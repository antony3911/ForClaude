"""最簡單版：整個 ESMFold 在 CPU 上跑完一次，用碼錶量每種運算花多少時間。

不做任何優化：FP32、不分塊、不暖機、只跑一次。
CPU 是同步執行（一個運算算完才往下走），所以在模組前後掐碼錶就是它真正花的時間。

用法：python run_cpu.py --L 76 256 --threads 16
     （76 = 泛素，會順便和 PDB 1UBQ 比 RMSD 確認結果正確；其他長度用隨機序列）
"""
import argparse
import collections
import os
import random
import resource
import time

import torch
from transformers import EsmForProteinFolding

from count_ops import BLOCK_PARTS
from profile_e2e import UBIQUITIN, ca_rmsd

RESULTS = os.path.join(os.path.dirname(__file__), "results")
times = collections.Counter()  # 類別 → 累計秒數
calls = collections.Counter()  # 類別 → 被呼叫幾次


def stopwatch(module, name):
    """在 module 前後各記一次時間，差值加到 times[name]。"""
    def before(m, args):
        m._t0 = time.perf_counter()

    def after(m, args, out):
        times[name] += time.perf_counter() - m._t0
        calls[name] += 1
    module.register_forward_pre_hook(before)
    module.register_forward_hook(after)


ap = argparse.ArgumentParser()
ap.add_argument("--L", type=int, nargs="+", default=[76])
ap.add_argument("--threads", type=int, default=8)
args = ap.parse_args()
torch.set_num_threads(args.threads)  # 共用 server，不要吃光所有核心

model = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1").float().eval()  # 全部 FP32、CPU
model.trunk.set_chunk_size(None)  # 不分塊

stopwatch(model.esm, "ESM-2")
stopwatch(model.trunk.structure_module, "structure_module")
for block in model.trunk.blocks:
    stopwatch(block, "block_total")
    for part in BLOCK_PARTS:
        stopwatch(getattr(block, part), part)

for L in args.L:
    random.seed(0)
    seq = UBIQUITIN if L == 76 else "".join(random.choice("ACDEFGHIKLMNPQRSTVWY") for _ in range(L))
    times.clear()
    calls.clear()

    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.infer(seq)
    total = time.perf_counter() - t0

    # 拆成互不重疊的類別，加起來剛好 = total
    parts = {p: times[p] for p in BLOCK_PARTS}
    parts["block 其他（residual 加法等）"] = times["block_total"] - sum(parts.values())
    parts["ESM-2"] = times["ESM-2"]
    parts["structure_module"] = times["structure_module"]
    parts["其他（embedding、recycling 等）"] = total - times["block_total"] - times["ESM-2"] - times["structure_module"]

    peak_gb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6  # Linux 單位是 KB
    print(f"\n=== L = {L}：總共 {total:.1f} s，block 被呼叫 {calls['block_total']} 次，"
          f"整個程式峰值記憶體 {peak_gb:.1f} GB ===")
    for name, t in sorted(parts.items(), key=lambda kv: -kv[1]):
        print(f"{name:32s} {t:9.2f} s  {100 * t / total:5.1f}%")
    if L == 76:
        ca = out["positions"][-1, 0, :, 1, :].numpy()  # atom14 的第 1 個是 CA
        print(f"泛素 CA RMSD = {ca_rmsd(ca, os.path.join(RESULTS, '1UBQ.pdb')):.2f} Å（筆電 GPU 版是 0.84）")

    with open(os.path.join(RESULTS, f"cpu_L{L}.csv"), "w") as fh:
        fh.write("part,seconds,percent\n")
        for name, t in parts.items():
            fh.write(f"{name},{t:.4f},{100 * t / total:.2f}\n")
