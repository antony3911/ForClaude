"""實測：一個 Folding Block（真實權重 = trunk 的第 0 個 block、隨機輸入）在 GPU 上的時間與記憶體。

- 每個子模組的時間 = profiler 量到、屬於它的 kernel 在 GPU 上的執行時間總和
  （不是碼錶時間，所以 CPU 被別的程式拖慢不會影響）
- 也用 CUDA event 量整個 block 的時間（含 kernel 之間 GPU 空等的時間），兩者對照
- 峰值記憶體 = forward 過程中比開始時多用的部分（不含權重與輸入）

時間和記憶體跟數值無關（沒有依資料走不同分支），所以輸入用隨機數即可。

用法：python profile_block.py [--L 64 128 ...] [--configs fp32:none fp32:64 fp16:none fp16:64]
"""
import argparse
import collections
import csv
import glob
import os
import statistics
import subprocess

import torch
from torch.profiler import ProfilerActivity, profile, record_function

from count_ops import BLOCK_PARTS, DTYPES, trunk_config

torch.backends.cuda.matmul.allow_tf32 = False
MATMUL_OPS = {"aten::mm", "aten::addmm", "aten::bmm", "aten::baddbmm"}
RESULTS = os.path.join(os.path.dirname(__file__), "results")


def load_block(dtype):
    from transformers.models.esm.modeling_esmfold import EsmFoldTriangularSelfAttentionBlock
    ckpt = glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/models--facebook--esmfold_v1/snapshots/*/pytorch_model.bin"))[0]
    sd = torch.load(ckpt, map_location="cpu", mmap=True, weights_only=True)
    prefix = "trunk.blocks.0."
    block = EsmFoldTriangularSelfAttentionBlock(trunk_config())
    block.load_state_dict({k[len(prefix):]: v for k, v in sd.items() if k.startswith(prefix)}, strict=True)
    return block.to(dtype).cuda().eval()


def attach_ranges(block):
    """每個子模組包一個 record_function，profiler 才知道 kernel 屬於誰。"""
    stack = []

    def enter(name):
        def hook(m, a):
            rf = record_function(name)
            rf.__enter__()
            stack.append(rf)
        return hook

    def leave(m, a, o):
        stack.pop().__exit__(None, None, None)

    for part in BLOCK_PARTS:
        sub = getattr(block, part)
        sub.register_forward_pre_hook(enter(part))
        sub.register_forward_hook(leave)


def kernel_seconds(prof, reps):
    """用 GPU 端的時間軸歸屬 kernel：每個 kernel 依開始時間，歸到包住它的子模組區段
    （record_function 在 GPU 上也會留下一段區段）。每個 kernel 只算一次。
    （舊做法沿著 CPU 端的父子關係找，長 L 加分塊時會重複算到約 20%，已棄用。）"""
    parts = set(BLOCK_PARTS)
    cuda = [e for e in prof.events() if e.device_type == torch.autograd.DeviceType.CUDA]
    spans = sorted((e.time_range.start, e.time_range.end, e.name) for e in cuda if e.name in parts)
    kernels = sorted((e.time_range.start, e.time_range.end, e) for e in cuda if e.name not in parts)
    # 每個 kernel 對應的 CPU 運算名稱（判斷是不是矩陣乘法）
    is_mm = collections.defaultdict(bool)
    for e in prof.events():
        for k in e.kernels:
            is_mm[k.name] |= e.name in MATMUL_OPS
    t = collections.Counter()
    i = 0
    for ks, ke, k in kernels:
        while i < len(spans) and spans[i][1] <= ks:
            i += 1
        part = "glue"
        for ss, se, name in spans[i:i + 3]:
            if ss <= ks < se:
                part = name
                break
        kind = "matmul" if is_mm[k.name] else "other"
        t[(part, kind)] += (ke - ks) / 1e6 / reps
    return t


def clocks():
    q = "clocks.sm,power.draw,temperature.gpu"
    r = subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader"], capture_output=True, text=True)
    return r.stdout.strip()


def measure(block, L, dtype, chunk, reps):
    s = torch.randn(1, L, 1024, device="cuda", dtype=dtype)
    z = torch.randn(1, L, L, 128, device="cuda", dtype=dtype)
    mask = torch.ones(1, L, device="cuda", dtype=dtype)

    def f():
        block(s, z, mask=mask, chunk_size=chunk)

    with torch.no_grad():
        f()  # 暖機
        torch.cuda.synchronize()
        base = torch.cuda.memory_allocated()
        torch.cuda.reset_peak_memory_stats()
        walls = []
        for _ in range(reps):
            a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            a.record()
            f()
            b.record()
            torch.cuda.synchronize()
            walls.append(a.elapsed_time(b) / 1e3)
        peak = torch.cuda.max_memory_allocated() - base
        clk = clocks()
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
            for _ in range(reps):
                f()
            torch.cuda.synchronize()
    return statistics.median(walls), peak, kernel_seconds(prof, reps), clk


def save(detail, summary, tag):
    """每量完一個點就整個重寫一次，中途停掉也不會白跑。"""
    for name, rows in (("measured_block", detail), ("measured_block_summary", summary)):
        if not rows:
            continue
        keys = list(dict.fromkeys(k for r in rows for k in r))
        with open(os.path.join(RESULTS, f"{name}{tag}.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, nargs="+", default=[64, 128, 256, 384, 512, 768, 1024, 1410])
    ap.add_argument("--configs", nargs="+", default=["fp32:none", "fp32:64", "fp16:none", "fp16:64"])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--tag", default="")
    ap.add_argument("--mem-gb", type=float, default=6.5,
                    help="PyTorch 可用的顯示記憶體上限。Windows 驅動在顯示記憶體不夠時會偷借系統 RAM"
                         "（不報錯、慢幾十倍），所以要設上限讓它直接 OOM")
    args = ap.parse_args()
    os.makedirs(RESULTS, exist_ok=True)
    total = torch.cuda.get_device_properties(0).total_memory
    torch.cuda.set_per_process_memory_fraction(args.mem_gb * 1e9 / total)

    detail, summary = [], []
    for cfg in args.configs:
        dt, ch = cfg.split(":")
        chunk = None if ch == "none" else int(ch)
        block = load_block(DTYPES[dt])
        attach_ranges(block)
        for L in args.L:
            try:
                wall, peak, kt, clk = measure(block, L, DTYPES[dt], chunk, args.reps)
            except torch.OutOfMemoryError:
                print(f"{dt} chunk={ch:>4} L={L:>5}: OOM（之後更長的 L 跳過）")
                summary.append(dict(L=L, dtype=dt, chunk=ch, wall_s="OOM", kernel_s="", peak_bytes="", clocks=""))
                torch.cuda.empty_cache()
                save(detail, summary, args.tag)
                break
            ktot = sum(kt.values())
            print(f"{dt} chunk={ch:>4} L={L:>5}: block {wall*1e3:9.1f} ms（kernel {ktot*1e3:9.1f} ms），"
                  f"峰值 +{peak/1e9:6.2f} GB  [{clk}]", flush=True)
            summary.append(dict(L=L, dtype=dt, chunk=ch, wall_s=wall, kernel_s=ktot, peak_bytes=peak, clocks=clk))
            for (mod, kind), sec in sorted(kt.items()):
                detail.append(dict(L=L, dtype=dt, chunk=ch, module=mod, kind=kind, kernel_s=sec))
            save(detail, summary, args.tag)
            torch.cuda.empty_cache()
        del block
        torch.cuda.empty_cache()

    save(detail, summary, args.tag)
    print("完成")


if __name__ == "__main__":
    main()
