"""server CPU 量測（run_cpu.py）的分析：時間佔比、每個運算達到的算力與頻寬、隨 L 的成長次方。

輸入：results/measured_cpu.csv（從 server 的 run_cpu.py log 抄錄，秒，為 192 次 block 呼叫的總和）
運算量與搬運量用 count_ops.count_block 現算（meta tensor，不需要 GPU）。

用法：python analyze_cpu.py
"""
import collections
import csv
import math
import os

import torch

from count_ops import count_block

CALLS = 48 * 4  # 48 個 block × 4 輪 recycling（run_cpu.py 的探針實際數到 192 次）
SHOW = ["tri_mul_out", "tri_mul_in", "tri_att_start", "tri_att_end", "mlp_pair"]

t = collections.defaultdict(dict)
for r in csv.DictReader(open(os.path.join(os.path.dirname(__file__), "results", "measured_cpu.csv"))):
    t[int(r["L"])][r["part"]] = float(r["seconds"])
Ls = sorted(t)

work = {}  # (L, module) -> (FLOPs, bytes)，一個 block 一次
for L in Ls:
    c = count_block(L, torch.float32, None)
    for (mod, kind), (n, f, b) in c.rec.items():
        F, B = work.get((L, mod), (0, 0))
        work[(L, mod)] = (F + f, B + b)


def trimul(L):
    return t[L]["tri_mul_out"] + t[L]["tri_mul_in"]


def triatt(L):
    return t[L]["tri_att_start"] + t[L]["tri_att_end"]


print("L      總時間   三角運算  TriMul  TriAttn  block 合計")
for L in Ls:
    blk = sum(v for k, v in t[L].items() if k not in ("esm2", "structure_module", "other", "total"))
    tot = t[L]["total"]
    print(f"{L:5d} {tot:8.1f} s {100*(trimul(L)+triatt(L))/tot:7.1f}% {100*trimul(L)/tot:6.1f}% "
          f"{100*triatt(L)/tot:7.1f}% {100*blk/tot:8.1f}%")

print("\nL     運算             FLOP/byte  達到 GFLOP/s  達到 GB/s（名目）")
for L in Ls:
    for mod in SHOW:
        F, B = work[(L, mod)]
        s = t[L][mod]
        print(f"{L:5d} {mod:15s} {F/B:9.1f} {F*CALLS/s/1e9:12.0f} {B*CALLS/s/1e9:12.1f}")

print("\n成長次方（時間 ∝ L^p）")
for a, b in zip(Ls, Ls[1:]):
    p = lambda f: math.log(f(b) / f(a)) / math.log(b / a)
    print(f"{a:5d}→{b:<5d} 總時間 {p(lambda L: t[L]['total']):.2f}｜TriMul 時間 {p(trimul):.2f}、"
          f"FLOPs {p(lambda L: work[(L, 'tri_mul_out')][0]):.2f}｜TriAttn 時間 {p(triatt):.2f}、"
          f"FLOPs {p(lambda L: work[(L, 'tri_att_start')][0]):.2f}、bytes {p(lambda L: work[(L, 'tri_att_start')][1]):.2f}")
