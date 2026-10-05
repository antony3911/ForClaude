"""量 server CPU 實際做得到的天花板（和 ceilings.py 對應，CPU 版）。

1. 矩陣乘法算力（FP32，4096×4096）
2. 連續複製的頻寬（1 GB 張量，y.copy_(x)：讀 1 GB ＋ 寫 1 GB）
3. TriMul 那種「permute 後的複製」：L×L×128 轉成 128×L×L，看比連續複製慢多少
4. 每次新配置記憶體的代價：寫進一塊剛 new 出來的大張量 vs 寫進已經用過的張量
   （PyTorch 在 CPU 上不重複利用大塊記憶體，每個運算的輸出都要向作業系統要新記憶體）

用法：python ceilings_cpu.py --threads 32
"""
import argparse
import statistics
import time

import torch


def best(fn, reps=5):
    fn()  # 暖機
    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


ap = argparse.ArgumentParser()
ap.add_argument("--threads", type=int, default=8)
ap.add_argument("--L", type=int, default=1024)
args = ap.parse_args()
torch.set_num_threads(args.threads)

n = 4096
a, b = torch.randn(n, n), torch.randn(n, n)
print(f"矩陣乘法 FP32：{2 * n**3 / best(lambda: a @ b) / 1e9:.0f} GFLOP/s")

x = torch.randn(1 << 28)  # 1 GB
y = torch.empty_like(x)
print(f"連續複製：{2 * x.nbytes / best(lambda: y.copy_(x)) / 1e9:.0f} GB/s")

L = args.L
z = torch.randn(1, L, L, 128)  # TriMul 的 a、b 原本的排列 [i][k][c]
zt = torch.empty(1, 128, L, L)
t = best(lambda: zt.copy_(z.permute(0, 3, 1, 2)))
print(f"permute 複製（L = {L}，{z.nbytes / 1e9:.2f} GB）：{2 * z.nbytes / t / 1e9:.0f} GB/s，每次 {t * 1e3:.0f} ms")

t_new = best(lambda: torch.empty_like(x).fill_(1.0))
t_old = best(lambda: y.fill_(1.0))
print(f"寫 1 GB：新配置的記憶體 {x.nbytes / t_new / 1e9:.0f} GB/s，已用過的記憶體 {x.nbytes / t_old / 1e9:.0f} GB/s")
