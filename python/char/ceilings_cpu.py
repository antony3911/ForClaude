"""量 server CPU 實際做得到的天花板（和 ceilings.py 對應，CPU 版）。

1. 矩陣乘法算力（FP32）：掃描 n = 1024～8192，取平穩值當上限
2. 頻寬（1 GB、4 GB），兩種運算 × 兩種記憶體擺放
   - 連續複製 y.copy_(x)：讀 1 份 ＋ 寫 1 份
   - 原地加法 y.add_(x)：讀 2 份 ＋ 寫 1 份（和 TriAttn 的 add_ 同一種運算）
   - 擺放：server 有 2 顆 CPU，各接自己的記憶體（NUMA）。Linux 把一頁記憶體放在「第一個寫它的
     執行緒」所在那顆 CPU 旁邊。torch.randn 在 CPU 上是單執行緒產生的 → 整個張量集中在一顆 CPU；
     先用多執行緒的 fill_ 寫一遍 → 分散在兩顆。ESMFold 裡的大張量都是多執行緒的運算產生的，屬於後者。
3. 和 TriMul einsum 同形狀、但資料已排好的 bmm（128 個 L×L×L）：分開「形狀造成的損失」和「排列造成的損失」
4. TriMul 那種「permute 後的複製」：L×L×128 轉成 128×L×L，看比連續複製慢多少
5. 每次新配置記憶體的代價：寫進一塊剛 new 出來的大張量 vs 寫進已經用過的張量
   （PyTorch 在 CPU 上不重複利用大塊記憶體，每個運算的輸出都要向作業系統要新記憶體）

用法：python ceilings_cpu.py --threads 32
注意：最大的測試要約 10 GB 記憶體，只在 server 上跑（16 GB 的筆電會卡死）。
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

print("1. 矩陣乘法 FP32（n×n 乘 n×n）")
for n in (1024, 2048, 4096, 8192, 16384):
    a, b = torch.randn(n, n), torch.randn(n, n)
    print(f"   n = {n:5d}：{2 * n**3 / best(lambda: a @ b) / 1e9:6.0f} GFLOP/s")
del a, b



def spread(*shape):
    """先用多執行緒寫一遍（決定每一頁放在哪顆 CPU 旁），再填亂數。"""
    t = torch.empty(*shape)
    t.fill_(0.0)
    return t.normal_()


print("2. 頻寬")
for mb in (1024, 4096):
    n = mb * (1 << 20) // 4
    for name, make in (("集中在一顆 CPU（randn）", torch.randn), ("分散在兩顆（先平行寫入）", spread)):
        x, y = make(n), make(n)
        cp = 2 * x.nbytes / best(lambda: y.copy_(x)) / 1e9
        ad = 3 * x.nbytes / best(lambda: y.add_(x)) / 1e9
        print(f"   {mb:5d} MB，{name}：連續複製 {cp:4.0f} GB/s，原地加法 {ad:4.0f} GB/s")
    del x, y

L = args.L
a, b = spread(128, L, L), spread(128, L, L)  # 已經排成 [c][i][k]，不用再轉
t = best(lambda: torch.bmm(a, b))
print(f"3. 和 TriMul einsum 同形狀的 bmm（128 個 {L}×{L}×{L}，資料已排好）："
      f"{2 * 128 * L**3 / t / 1e9:.0f} GFLOP/s，每次 {t * 1e3:.0f} ms")
del a, b

z = spread(1, L, L, 128)  # TriMul 的 a、b 原本的排列 [i][k][c]
zt = torch.empty(1, 128, L, L)
t = best(lambda: zt.copy_(z.permute(0, 3, 1, 2)))
print(f"4. permute 複製（L = {L}，{z.nbytes / 1e9:.2f} GB）：{2 * z.nbytes / t / 1e9:.0f} GB/s，每次 {t * 1e3:.0f} ms")

x = spread(1 << 28)  # 1 GB
y = torch.empty_like(x)
t_new = best(lambda: torch.empty_like(x).fill_(1.0))
t_old = best(lambda: y.fill_(1.0))
print(f"5. 寫 1 GB：新配置的記憶體 {x.nbytes / t_new / 1e9:.0f} GB/s，已用過的記憶體 {x.nbytes / t_old / 1e9:.0f} GB/s")
