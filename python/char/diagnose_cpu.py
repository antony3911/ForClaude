"""CPU 版診斷：TriMul 和 TriAttn 裡面，時間花在哪些 aten 運算？

GPU 上 tri_mul_out 有 57% 時間在 copy_（permute 後的轉置複製），einsum（bmm）只佔 6%。
這支程式在 CPU 上做同樣的拆解，看是不是同一回事；也比較 tri_att_start 和 tri_att_end
（server 上 L = 1024 時 end 比 start 慢 25%）。

做法：真實權重（trunk 的第 0 個 block）、隨機輸入、FP32、不分塊。每個子模組先跑 1 次暖機，
再用 profiler 量 3 次。CPU 是同步執行，每個 aten 運算的 self 時間就是它實際花的時間。

用法：python diagnose_cpu.py --L 512 1024 --threads 32
"""
import argparse
import glob
import os

import torch
from torch.profiler import ProfilerActivity, profile

from count_ops import trunk_config

PARTS = ["tri_mul_out", "tri_mul_in", "tri_att_start", "tri_att_end"]
REPS = 3


def load_block():
    from transformers.models.esm.modeling_esmfold import EsmFoldTriangularSelfAttentionBlock
    ckpt = glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/models--facebook--esmfold_v1/snapshots/*/pytorch_model.bin"))[0]
    sd = torch.load(ckpt, map_location="cpu", mmap=True, weights_only=True)
    prefix = "trunk.blocks.0."
    block = EsmFoldTriangularSelfAttentionBlock(trunk_config())
    block.load_state_dict({k[len(prefix):]: v for k, v in sd.items() if k.startswith(prefix)}, strict=True)
    return block.float().eval()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, nargs="+", default=[512])
    ap.add_argument("--threads", type=int, default=8)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    block = load_block()

    for L in args.L:
        torch.manual_seed(0)
        z = torch.randn(1, L, L, 128)
        tri_mask = torch.ones(1, L, L)
        pair_mb = L * L * 128 * 4 / 1e6
        print(f"\n######## L = {L}（一個 L×L×128 張量 = {pair_mb:.0f} MB）########")
        for part in PARTS:
            mod = getattr(block, part)
            kw = {} if part.startswith("tri_mul") else {"chunk_size": None}
            with torch.no_grad():
                mod(z, mask=tri_mask, **kw)  # 暖機
                with profile(activities=[ProfilerActivity.CPU]) as prof:
                    for _ in range(REPS):
                        mod(z, mask=tri_mask, **kw)
            # self 時間：扣掉子運算之後，這個運算自己花的時間（避免 linear 和它裡面的 addmm 重複計算）
            rows = [(e.key, e.self_cpu_time_total / REPS / 1e3, e.count / REPS) for e in prof.key_averages()]
            rows = [r for r in rows if r[1] > 0]
            total = sum(r[1] for r in rows)
            print(f"\n{part}：每次 {total:.0f} ms")
            for name, ms, n in sorted(rows, key=lambda r: -r[1])[:10]:
                print(f"  {name:32s} {ms:9.1f} ms  {100 * ms / total:5.1f}%  呼叫 {n:.0f} 次")


if __name__ == "__main__":
    main()
