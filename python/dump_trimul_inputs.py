"""用 ESMFold 跑真實蛋白質，擷取 Triangle Multiplication (outgoing) 的輸入 a, b。

擷取到的 a, b 就是 fpga/trimul kernel 要算的東西：
    z[i][j][c] = sum_k a[i][k][c] * b[j][k][c]
存成 float32 raw binary，排列 [i][k][c]，可直接給 host.exe / tb 讀取。

只需要跑到指定的 trunk block 就停止（後面的 structure module 不用跑），
所以比完整預測結構省時間和記憶體。

範例：
    # UniProt ID（自動下載序列）
    python dump_trimul_inputs.py --uniprot P0DTC2 --out ../data/spike
    # PDB ID
    python dump_trimul_inputs.py --pdb 6VXX --out ../data/6vxx
    # 自己的 FASTA
    python dump_trimul_inputs.py --fasta my.fasta --out ../data/my
    # 太長的話截斷
    python dump_trimul_inputs.py --uniprot P11532 --max-len 2048 --out ../data/dmd2048

輸出目錄內容：
    a.bin, b.bin   float32, shape [L_pad, L_pad, 128]
    meta.json      序列名稱、原始長度、padding 後長度、各種統計
"""

import argparse
import json
import math
import os
import time
import urllib.request

import torch

C = 128


def fetch_sequence(args):
    if args.seq:
        return "custom", args.seq
    if args.fasta:
        text = open(args.fasta).read()
    elif args.uniprot:
        url = f"https://rest.uniprot.org/uniprotkb/{args.uniprot}.fasta"
        text = urllib.request.urlopen(url, timeout=60).read().decode()
    elif args.pdb:
        url = f"https://www.rcsb.org/fasta/entry/{args.pdb}"
        text = urllib.request.urlopen(url, timeout=60).read().decode()
    else:
        raise SystemExit("請指定 --seq / --fasta / --uniprot / --pdb 其中一個")
    # 只取第一條鏈
    lines = text.strip().splitlines()
    name = lines[0][1:].split()[0] if lines[0].startswith(">") else "seq"
    seq = []
    for line in lines[1:]:
        if line.startswith(">"):
            break
        seq.append(line.strip())
    return name, "".join(seq).upper()


class StopCapture(Exception):
    pass


def int8_quant(x, per_token):
    """對稱 INT8 量化再還原（fake quant），x: [L, L, C]"""
    if per_token:
        s = x.abs().amax(dim=-1, keepdim=True).clamp_min(1e-12) / 127.0
    else:
        s = x.abs().amax().clamp_min(1e-12) / 127.0
    return torch.clamp(torch.round(x / s), -127, 127) * s


def trimul_ref(a, b, channels):
    # z[i,j,c] = sum_k a[i,k,c] b[j,k,c]，只算部分 channel 以節省記憶體
    a = a[..., channels].permute(2, 0, 1).double()  # [c, i, k]
    b = b[..., channels].permute(2, 1, 0).double()  # [c, k, j]
    return torch.matmul(a, b)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seq")
    p.add_argument("--fasta")
    p.add_argument("--uniprot")
    p.add_argument("--pdb")
    p.add_argument("--out", required=True)
    p.add_argument("--block", type=int, default=0, help="擷取第幾個 trunk block（0~47）")
    p.add_argument("--max-len", type=int, default=0, help="序列超過此長度就截斷（0 = 不截斷）")
    p.add_argument("--pad", type=int, default=32, help="L 補零到此倍數（需為 kernel tile 大小的倍數）")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--chunk-size", type=int, default=64, help="trunk chunk size，越小越省記憶體")
    p.add_argument("--eval-channels", type=int, default=16, help="量化誤差評估用幾個 channel")
    p.add_argument("--model", default="facebook/esmfold_v1")
    args = p.parse_args()

    name, seq = fetch_sequence(args)
    if args.max_len and len(seq) > args.max_len:
        print(f"序列長度 {len(seq)} 截斷為 {args.max_len}")
        seq = seq[: args.max_len]
    L0 = len(seq)
    print(f"{name}: L = {L0}")

    from transformers import EsmForProteinFolding

    print(f"載入 {args.model}（第一次會下載約 8 GB 權重）...")
    # 語言模型 ESM-2 3B 用半精度以節省記憶體；trunk 維持 FP32
    lm_dtype = torch.float16 if args.device.startswith("cuda") else torch.bfloat16
    model = EsmForProteinFolding.from_pretrained(args.model, torch_dtype=lm_dtype, low_cpu_mem_usage=True)
    for child_name, child in model.named_children():
        if child_name != "esm":
            child.float()
    model.esm_s_combine.data = model.esm_s_combine.data.float()
    model.eval().to(args.device)
    model.trunk.set_chunk_size(args.chunk_size)

    captured = {}
    tm = model.trunk.blocks[args.block].tri_mul_out

    def capture(a, b, _inplace_chunk_size=None):
        captured["a"] = a[0].float().cpu()
        captured["b"] = b[0].float().cpu()
        raise StopCapture

    tm._combine_projections = capture

    t0 = time.time()
    with torch.no_grad():
        try:
            # infer() 會把胺基酸字母轉成 ESMFold 需要的編號（不要直接用 tokenizer）
            model.infer(seq)
        except StopCapture:
            pass
    if "a" not in captured:
        raise SystemExit("沒有擷取到資料，transformers 版本的內部結構可能不同")
    if args.device.startswith("cuda"):
        peak = torch.cuda.max_memory_allocated() / 2**30
        print(f"GPU peak memory: {peak:.2f} GiB")
    print(f"擷取完成，耗時 {time.time() - t0:.1f} s")

    a, b = captured["a"], captured["b"]
    assert a.shape == (L0, L0, C), a.shape

    # ---- 統計：outlier 程度與量化誤差（這些數字可以直接放進報告）----
    tok_max_a = a.abs().amax(dim=-1).flatten()
    stats = {
        "absmax": float(a.abs().max()),
        "token_absmax_median": float(tok_max_a.median()),
        "token_absmax_p99": float(tok_max_a.quantile(0.99)) if tok_max_a.numel() < 2**24 else None,
        "outlier_ratio_max_over_median": float(tok_max_a.max() / tok_max_a.median().clamp_min(1e-12)),
    }
    g = torch.Generator().manual_seed(0)
    ch = torch.randperm(C, generator=g)[: args.eval_channels]
    ref = trimul_ref(a, b, ch)
    for per_token, tag in [(True, "per_token"), (False, "per_tensor")]:
        z = trimul_ref(int8_quant(a, per_token), int8_quant(b, per_token), ch)
        stats[f"int8_{tag}_rel_l2"] = float((z - ref).norm() / ref.norm())
    print(json.dumps(stats, indent=2))

    # ---- 補零到 pad 的倍數（補的 token 全為 0，不影響結果）----
    L = int(math.ceil(L0 / args.pad) * args.pad)
    if L != L0:
        a = torch.nn.functional.pad(a, (0, 0, 0, L - L0, 0, L - L0))
        b = torch.nn.functional.pad(b, (0, 0, 0, L - L0, 0, L - L0))

    os.makedirs(args.out, exist_ok=True)
    a.contiguous().numpy().tofile(os.path.join(args.out, "a.bin"))
    b.contiguous().numpy().tofile(os.path.join(args.out, "b.bin"))
    meta = {"name": name, "L_orig": L0, "L": L, "C": C, "block": args.block, "seq": seq, "stats": stats}
    json.dump(meta, open(os.path.join(args.out, "meta.json"), "w"), indent=2)
    mb = a.numel() * 4 / 2**20
    print(f"已寫入 {args.out}/a.bin, b.bin（L={L}，每個 {mb:.1f} MiB）")


if __name__ == "__main__":
    main()
