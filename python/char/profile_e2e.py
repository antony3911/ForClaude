"""端到端：整個 ESMFold 的時間分布（ESM-2 / trunk 的 192 次 block / structure module / 其他），
並檢查「單一 block × 192」是否等於 trunk 實測（V3），以及預測結構對不對（與 PDB 實驗結構比 RMSD）。

顯示記憶體放不下全部權重，所以分兩段：
  1. ESM-2（FP16，5.7 GB）放 GPU 算出 embedding，計時；算完移回 CPU
  2. trunk 與其他部分（FP32，從原檔填回權重）放 GPU，跑完整的 infer（共 4 輪：HF 預設 max_recycles = 4，不另外加 1），用 profiler 分段
時間和數值無關，所以長度掃描用隨機序列；正確性用泛素（ubiquitin，76 aa，PDB 1UBQ）。

用法：python profile_e2e.py [--L 256 512] [--chunk 64]
"""
import argparse
import collections
import csv
import glob
import os
import random
import statistics
import time
import urllib.request

import numpy as np
import torch
from torch.profiler import ProfilerActivity, profile, record_function

torch.backends.cuda.matmul.allow_tf32 = False
RESULTS = os.path.join(os.path.dirname(__file__), "results")
UBIQUITIN = "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"
CKPT_GLOB = "~/.cache/huggingface/hub/models--facebook--esmfold_v1/snapshots/*/pytorch_model.bin"


def load_model():
    from transformers import EsmForProteinFolding
    m = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1", torch_dtype=torch.float16, low_cpu_mem_usage=True)
    for name, child in m.named_children():
        if name != "esm":
            child.cuda().float()
    m.esm_s_combine.data = m.esm_s_combine.data.cuda().float()
    sd = torch.load(glob.glob(os.path.expanduser(CKPT_GLOB))[0], map_location="cpu", mmap=True, weights_only=True)
    missing, _ = m.load_state_dict({k: v for k, v in sd.items() if not k.startswith("esm.")}, strict=False)
    assert not [k for k in missing if not k.startswith("esm.")], "trunk 權重沒填完整"
    return m.eval()


def non_esm_children(m):
    return [c for n, c in m.named_children() if n != "esm"]


def esm_on_gpu(m, seq):
    """trunk 暫時移到 CPU，ESM-2 移上 GPU 算 embedding；回傳 (embedding, GPU 時間 s)。"""
    for c in non_esm_children(m):
        c.cpu()
    torch.cuda.empty_cache()
    m.esm.cuda()
    captured = {}
    orig = m.compute_language_model_representations

    def run(esmaa):
        esmaa = esmaa.cuda()
        orig(esmaa)  # 暖機
        torch.cuda.synchronize()
        times = []
        for _ in range(3):
            a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            a.record()
            out = orig(esmaa)
            b.record()
            torch.cuda.synchronize()
            times.append(a.elapsed_time(b) / 1e3)
        captured["t"] = statistics.median(times)
        captured["s"] = out.cpu()
        raise StopIteration  # 只要 embedding，不往下跑

    m.compute_language_model_representations = run
    m.esm_s_combine.data = m.esm_s_combine.data.cpu()
    try:
        with torch.no_grad():
            m.infer(seq)
    except StopIteration:
        pass
    m.compute_language_model_representations = orig
    m.esm.cpu()
    m.esm_s_combine.data = m.esm_s_combine.data.cuda()
    for c in non_esm_children(m):
        c.cuda()
    torch.cuda.empty_cache()
    return captured["s"], captured["t"]


def annotate(m):
    """trunk 的每個 block、structure module 各包一個 record_function。"""
    def wrap(mod, name):
        def pre(_m, _a):
            rf = record_function(name)
            rf.__enter__()
            _m._rf = rf

        def post(_m, _a, _o):
            _m._rf.__exit__(None, None, None)
        mod.register_forward_pre_hook(pre)
        mod.register_forward_hook(post)

    for blk in m.trunk.blocks:
        wrap(blk, "block")
    wrap(m.trunk.structure_module, "structure_module")


def gpu_breakdown(prof, reps):
    """GPU 時間軸上，每個 kernel 依開始時間歸到包住它的區段（block / structure_module / 其他）。"""
    cuda = [e for e in prof.events() if e.device_type == torch.autograd.DeviceType.CUDA]
    names = {"block", "structure_module"}
    spans = sorted((e.time_range.start, e.time_range.end, e.name) for e in cuda if e.name in names)
    t = collections.Counter()
    i = 0
    for e in sorted((e for e in cuda if e.name not in names), key=lambda e: e.time_range.start):
        ks, ke = e.time_range.start, e.time_range.end
        while i < len(spans) and spans[i][1] <= ks:
            i += 1
        part = "other"
        if i < len(spans) and spans[i][0] <= ks < spans[i][1]:
            part = spans[i][2]
        t[part] += (ke - ks) / 1e6 / reps
    return t


def run_trunk(m, seq, esm_s, chunk, reps=1):
    m.trunk.set_chunk_size(chunk)
    cached = esm_s.cuda()
    m.compute_language_model_representations = lambda esmaa: cached
    with torch.no_grad():
        out = m.infer(seq)  # 暖機
        torch.cuda.synchronize()
        base = torch.cuda.memory_allocated()
        torch.cuda.reset_peak_memory_stats()
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
            a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            a.record()
            for _ in range(reps):
                out = m.infer(seq)
            b.record()
            torch.cuda.synchronize()
        wall = a.elapsed_time(b) / 1e3 / reps
        peak = torch.cuda.max_memory_allocated() - base
    del m.compute_language_model_representations  # 還原成 class 上的方法
    return out, wall, gpu_breakdown(prof, reps), peak


def ca_rmsd(pred_ca, pdb_path):
    """Kabsch 對齊後的 CA RMSD（Å）。"""
    ref = []
    for line in open(pdb_path):
        if line.startswith("ATOM") and line[12:16].strip() == "CA" and line[21] == "A":
            ref.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    ref = np.array(ref[: len(pred_ca)])
    p = pred_ca - pred_ca.mean(0)
    q = ref - ref.mean(0)
    u, _, vt = np.linalg.svd(p.T @ q)
    d = np.sign(np.linalg.det(u @ vt))
    rot = u @ np.diag([1, 1, d]) @ vt
    return float(np.sqrt(((p @ rot - q) ** 2).sum(1).mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, nargs="*", default=[256, 512])
    ap.add_argument("--chunk", type=int, default=64)
    ap.add_argument("--mem-gb", type=float, default=6.5)
    args = ap.parse_args()
    torch.cuda.set_per_process_memory_fraction(args.mem_gb * 1e9 / torch.cuda.get_device_properties(0).total_memory)
    os.makedirs(RESULTS, exist_ok=True)

    m = load_model()
    annotate(m)
    jobs = [("ubiquitin", UBIQUITIN)]
    random.seed(0)
    jobs += [(f"random{L}", "".join(random.choice("ACDEFGHIKLMNPQRSTVWY") for _ in range(L))) for L in args.L]

    rows = []
    for name, seq in jobs:
        L = len(seq)
        esm_s, t_esm = esm_on_gpu(m, seq)
        try:
            out, wall, parts, peak = run_trunk(m, seq, esm_s, args.chunk)
        except torch.OutOfMemoryError:
            print(f"{name} L={L}: OOM")
            torch.cuda.empty_cache()
            continue
        nblk = 48 * 4  # 48 個 block × 4 輪（之前誤寫成 5 輪，run_cpu.py 的探針實測 192 次）
        row = dict(name=name, L=L, chunk=args.chunk, esm_s=t_esm, trunk_wall_s=wall,
                   blocks_s=parts["block"], per_block_s=parts["block"] / nblk,
                   structure_s=parts["structure_module"], other_s=parts["other"], peak_bytes=peak,
                   plddt=float(out["plddt"].mean()))
        if name == "ubiquitin":
            pdb = os.path.join(RESULTS, "1UBQ.pdb")
            if not os.path.exists(pdb):
                urllib.request.urlretrieve("https://files.rcsb.org/download/1UBQ.pdb", pdb)
            ca = out["positions"][-1, 0, :, 1, :].float().cpu().numpy()  # atom14 的第 1 個是 CA
            row["ca_rmsd_A"] = ca_rmsd(ca, pdb)
        rows.append(row)
        tot = t_esm + wall
        print(f"{name} L={L}: ESM-2 {t_esm*1e3:.0f} ms（{100*t_esm/tot:.1f}%）、trunk＋SM {wall*1e3:.0f} ms；"
              f"其中 192 個 block {parts['block']*1e3:.0f} ms（{100*parts['block']/tot:.1f}%，平均 {row['per_block_s']*1e3:.2f} ms）、"
              f"structure module {parts['structure_module']*1e3:.0f} ms（{100*parts['structure_module']/tot:.1f}%）、"
              f"其他 {parts['other']*1e3:.0f} ms；峰值 +{peak/1e9:.2f} GB；pLDDT {row['plddt']:.3f}"
              + (f"；CA RMSD {row['ca_rmsd_A']:.2f} Å" if "ca_rmsd_A" in row else ""), flush=True)

    with open(os.path.join(RESULTS, "measured_e2e.csv"), "w", newline="") as fh:
        keys = list(dict.fromkeys(k for r in rows for k in r))
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
