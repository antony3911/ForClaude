"""診斷：(1) profiler 量到的 kernel 時間為什麼會比整個 block 的時間長？
         (2) TriMul 裡哪些 kernel 用不滿頻寬？

(1) 在 profiler 跑的同一批 forward 外面也包 CUDA event，比較同一批的 kernel 總和與總時間；
    並記錄這段時間 Windows 的 GPU 共用記憶體（借用系統 RAM）有沒有增加。
(2) 單獨跑一個 tri_mul_out，列出每個 aten 運算的 kernel 時間與達到的頻寬。

用法：python diagnose.py --L 1024 --dtype fp16 --chunk 64
"""
import argparse
import collections
import subprocess

import torch
from torch.profiler import ProfilerActivity, profile

from count_ops import DTYPES
from profile_block import attach_ranges, kernel_seconds, load_block

torch.backends.cuda.matmul.allow_tf32 = False


def shared_gb():
    ps = ("(Get-Counter '\\GPU Process Memory(pid_%d*)\\Shared Usage').CounterSamples | "
          "Measure-Object CookedValue -Sum | ForEach-Object { $_.Sum / 1GB }") % __import__("os").getpid()
    r = subprocess.run(["powershell", "-NoProfile", "-c", ps], capture_output=True, text=True)
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, default=1024)
    ap.add_argument("--dtype", default="fp16")
    ap.add_argument("--chunk", default="64")
    ap.add_argument("--mem-gb", type=float, default=6.5)
    args = ap.parse_args()
    torch.cuda.set_per_process_memory_fraction(args.mem_gb * 1e9 / torch.cuda.get_device_properties(0).total_memory)
    dt = DTYPES[args.dtype]
    chunk = None if args.chunk == "none" else int(args.chunk)
    L = args.L

    block = load_block(dt)
    attach_ranges(block)
    s = torch.randn(1, L, 1024, device="cuda", dtype=dt)
    z = torch.randn(1, L, L, 128, device="cuda", dtype=dt)
    mask = torch.ones(1, L, device="cuda", dtype=dt)

    def ev():
        return torch.cuda.Event(enable_timing=True)

    with torch.no_grad():
        block(s, z, mask=mask, chunk_size=chunk)
        torch.cuda.synchronize()
        print("共用記憶體（GB）暖機後：", shared_gb())
        # (1) 不開 profiler 的 3 次
        a, b = ev(), ev()
        a.record()
        for _ in range(3):
            block(s, z, mask=mask, chunk_size=chunk)
        b.record()
        torch.cuda.synchronize()
        plain = a.elapsed_time(b) / 3
        # 開 profiler 的 3 次，外面也包 CUDA event
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
            a, b = ev(), ev()
            a.record()
            for _ in range(3):
                block(s, z, mask=mask, chunk_size=chunk)
            b.record()
            torch.cuda.synchronize()
        profiled = a.elapsed_time(b) / 3
        ksum = sum(kernel_seconds(prof, 3).values()) * 1e3
        print(f"每次 block：不開 profiler {plain:.1f} ms；開 profiler {profiled:.1f} ms；同一批的 kernel 總和 {ksum:.1f} ms")
        print("共用記憶體（GB）結束時：", shared_gb())
        # 換一個算法：直接看 GPU 端的 kernel 事件（每個 kernel 只出現一次），並算區間聯集（扣掉重疊）
        spans = sorted((e.time_range.start, e.time_range.end) for e in prof.events()
                       if e.device_type == torch.autograd.DeviceType.CUDA)
        total = sum(b - a for a, b in spans)
        union, cur_a, cur_b = 0, None, None
        for a, b in spans:
            if cur_b is None or a > cur_b:
                union += (cur_b - cur_a) if cur_b is not None else 0
                cur_a, cur_b = a, b
            else:
                cur_b = max(cur_b, b)
        union += cur_b - cur_a
        print(f"GPU 端 kernel 事件：{len(spans)/3:.0f} 個/次，加總 {total/3e3:.1f} ms，聯集（扣重疊）{union/3e3:.1f} ms")

        # (2) tri_mul_out 裡每個 aten 運算的 kernel 時間
        x = z
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as p2:
            for _ in range(3):
                block.tri_mul_out(x, mask=mask.unsqueeze(2) * mask.unsqueeze(1))
            torch.cuda.synchronize()
    t = collections.Counter()
    n = collections.Counter()
    for e in p2.events():
        if e.kernels:
            t[e.name] += sum(k.duration for k in e.kernels) / 3 / 1e3
            n[e.name] += len(e.kernels) / 3
    tot = sum(t.values())
    pair_mb = L * L * 128 * torch.finfo(dt).bits / 8 / 1e6
    print(f"\ntri_mul_out 每次 {tot:.1f} ms（一個 L×L×128 張量 = {pair_mb:.0f} MB）")
    for name, ms in t.most_common(12):
        print(f"  {name:28s} {ms:8.2f} ms  {100*ms/tot:5.1f}%  kernels {n[name]:.0f}")


if __name__ == "__main__":
    main()
