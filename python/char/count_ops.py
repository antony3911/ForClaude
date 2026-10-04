"""計數：用 meta tensor 執行 HF ESMFold 的模組，記錄每個 aten 運算的 FLOPs 與搬運 bytes。

meta tensor 只有形狀、不配置記憶體，所以任何 L 都能算，數到的是 HF 實作真正執行的運算。

搬運量的規則（每個 aten 運算 ≈ 一個 kernel，沒有融合）：
- view 類運算（permute、transpose、view、expand…）不搬資料 → 0
- 其他運算：讀所有輸入 + 寫所有輸出；broadcast（stride 0）的輸入只算實際不同的元素
- in-place（add_ 等）：讀 self 與其他輸入、寫 self
- copy_：讀 src、寫 dst
FLOPs 只算矩陣乘法類（mm、addmm、bmm、baddbmm），一次乘加算 2。

用法：python count_ops.py --L 77 256 512 1410 --dtype fp32 --chunk none 64 --out counts.csv
"""
import argparse
import collections
import csv
import json
import os
import sys

import torch
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_flatten

MATMUL = {"mm", "addmm", "bmm", "baddbmm"}
NO_TRAFFIC = {"empty", "empty_strided", "empty_like", "detach", "lift_fresh", "_local_scalar_dense"}
DTYPES = {"fp32": torch.float32, "fp16": torch.float16}

# 一個 Folding Block 裡我們關心的子模組（順序同 forward）
BLOCK_PARTS = ["pair_to_sequence", "layernorm_1", "seq_attention", "mlp_seq", "sequence_to_pair",
               "tri_mul_out", "tri_mul_in", "tri_att_start", "tri_att_end", "mlp_pair"]


def unique_bytes(t):
    """實際不同元素的 bytes：broadcast（stride 0）的維度只算一份。"""
    n = 1
    for size, stride in zip(t.shape, t.stride()):
        if stride != 0:
            n *= size
    return n * t.element_size()


def matmul_flops(name, args):
    a, b = (args[0], args[1]) if name in ("mm", "bmm") else (args[1], args[2])
    if name in ("mm", "addmm"):
        m, k = a.shape
        n = b.shape[1]
        return 2 * m * k * n
    bsz, m, k = a.shape
    n = b.shape[2]
    return 2 * bsz * m * k * n


class Counter(TorchDispatchMode):
    def __init__(self):
        super().__init__()
        self.stack = ["glue"]
        # (module, kind) -> [ops, flops, bytes]；kind = "matmul" 或 "other"
        self.rec = collections.defaultdict(lambda: [0, 0, 0])
        self.ops = []  # 逐個運算：(module, op, flops, bytes)，給 roofline 逐 kernel 預測

    def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        kwargs = kwargs or {}
        out = func(*args, **kwargs)
        name = func.overloadpacket.__name__
        rets = func._schema.returns
        if rets and rets[0].alias_info is not None and not rets[0].alias_info.is_write:
            return out  # view
        if name in NO_TRAFFIC:
            return out
        ins = [a for a in tree_flatten((args, kwargs))[0] if isinstance(a, torch.Tensor)]
        outs = [o for o in tree_flatten(out)[0] if isinstance(o, torch.Tensor)]
        if name == "copy_":
            nbytes = unique_bytes(args[0]) + unique_bytes(args[1])
        else:
            nbytes = sum(unique_bytes(t) for t in ins) + sum(unique_bytes(t) for t in outs)
        flops = matmul_flops(name, args) if name in MATMUL else 0
        kind = "matmul" if name in MATMUL else "other"
        r = self.rec[(self.stack[-1], kind)]
        r[0] += 1
        r[1] += flops
        r[2] += nbytes
        self.ops.append((self.stack[-1], name, flops, nbytes))
        return out


def attach(counter, module, parts):
    """進入子模組時把名字推進 stack、離開時彈出（hook 必須回傳 None，否則會蓋掉輸出）。"""
    def enter(name):
        def hook(m, a):
            counter.stack.append(name)
        return hook

    def leave(m, a, o):
        counter.stack.pop()

    for part in parts:
        sub = getattr(module, part)
        sub.register_forward_pre_hook(enter(part))
        sub.register_forward_hook(leave)


def trunk_config():
    from transformers import EsmConfig
    cfg = EsmConfig.from_pretrained("facebook/esmfold_v1")
    return cfg.esmfold_config.trunk


def patch_autocast_check():
    """HF 的 TriMul 會問「autocast 有沒有開成 fp16」；meta 裝置不支援這個查詢。
    我們不用 autocast，在 GPU 上的答案是 False，meta 上照這個答案回。"""
    import transformers.models.esm.modeling_esmfold as mf
    if getattr(mf, "_char_patched", False):
        return
    orig = mf.is_fp16_enabled
    mf.is_fp16_enabled = lambda device_type: False if device_type == "meta" else orig(device_type)
    mf._char_patched = True


def count_block(L, dtype, chunk):
    from transformers.models.esm.modeling_esmfold import EsmFoldTriangularSelfAttentionBlock
    patch_autocast_check()
    tc = trunk_config()
    block = EsmFoldTriangularSelfAttentionBlock(tc).eval().to(dtype).to("meta")
    c = Counter()
    attach(c, block, BLOCK_PARTS)
    s = torch.empty(1, L, tc.sequence_state_dim, device="meta", dtype=dtype)
    z = torch.empty(1, L, L, tc.pairwise_state_dim, device="meta", dtype=dtype)
    mask = torch.ones(1, L, device="meta", dtype=dtype)
    with torch.no_grad(), c:
        block(s, z, mask=mask, chunk_size=chunk)
    return c


def load_ceilings():
    path = os.path.join(os.path.dirname(__file__), "results", "ceilings.json")
    return json.load(open(path)) if os.path.exists(path) else None


def roofline_seconds(ops, ceil, dtype_name):
    """每個運算各自取 max(運算量 ÷ 算力, 搬運量 ÷ 頻寬)，再按模組加總。"""
    peak = ceil[f"{dtype_name}_matmul_tflops"] * 1e12
    bw = ceil["bandwidth_gbs"] * 1e9
    t = collections.Counter()
    for mod, name, flops, nbytes in ops:
        kind = "matmul" if name in MATMUL else "other"
        t[(mod, kind)] += max(flops / peak, nbytes / bw)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, nargs="+", default=[77, 256, 512, 1024, 1410])
    ap.add_argument("--dtype", nargs="+", default=["fp32", "fp16"])
    ap.add_argument("--chunk", nargs="+", default=["none", "64"])
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "results", "counts_block.csv"))
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    ceil = load_ceilings()
    rows = []
    for dt in args.dtype:
        for ch in args.chunk:
            chunk = None if ch == "none" else int(ch)
            for L in args.L:
                c = count_block(L, DTYPES[dt], chunk)
                pred = roofline_seconds(c.ops, ceil, dt) if ceil else {}
                for (mod, kind), (n, f, b) in sorted(c.rec.items()):
                    rows.append(dict(L=L, dtype=dt, chunk=ch, module=mod, kind=kind, ops=n, flops=f, bytes=b,
                                     roofline_s=pred.get((mod, kind), "")))
                tot_f = sum(v[1] for v in c.rec.values())
                tot_b = sum(v[2] for v in c.rec.values())
                print(f"{dt} chunk={ch:>4} L={L:>5}: {tot_f/1e9:9.1f} GFLOP, {tot_b/1e9:8.2f} GB moved, {len(c.ops)} ops")
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("寫入", args.out)


if __name__ == "__main__":
    sys.exit(main())
