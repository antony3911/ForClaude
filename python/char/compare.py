"""比對：roofline 預測 vs 筆電實測（V2），以及用同一個模型推 H100、對照論文 Fig. 3（V5）。

輸入：results/counts_block.csv（count_ops.py）、results/measured_block*.csv（profile_block.py）
輸出：results/compare_block.csv、results/share_vs_L.png，並印出摘要表
"""
import collections
import csv
import os

from count_ops import DTYPES, count_block, roofline_seconds

RESULTS = os.path.join(os.path.dirname(__file__), "results")

# 子模組 → 報告用的分組
GROUPS = {
    "tri_mul_out": "TriMul", "tri_mul_in": "TriMul",
    "tri_att_start": "TriAttn", "tri_att_end": "TriAttn",
    "mlp_pair": "Pair transition",
    "sequence_to_pair": "Seq<->pair", "pair_to_sequence": "Seq<->pair",
    "seq_attention": "Seq track", "mlp_seq": "Seq track", "layernorm_1": "Seq track",
    "glue": "Residual/glue",
}
ORDER = ["TriMul", "TriAttn", "Pair transition", "Seq<->pair", "Seq track", "Residual/glue"]

# 論文 Fig. 3（H100、不分塊，佔整個 ESMFold 的比例）→ 換算成「佔 Folding Block」的比例
PAPER = {77: dict(block=83.8, TriMul=36.1, TriAttn=29.0), 1410: dict(block=94.5, TriMul=14.5, TriAttn=75.9)}

# H100 規格（dense；論文沒寫是 SXM 還是 PCIe，兩個都算）
H100 = {
    "H100 SXM": dict(fp16_matmul_tflops=989, fp32_matmul_tflops=67, bandwidth_gbs=3350),
    "H100 PCIe": dict(fp16_matmul_tflops=756, fp32_matmul_tflops=51, bandwidth_gbs=2000),
}


def read(name):
    path = os.path.join(RESULTS, name)
    return list(csv.DictReader(open(path))) if os.path.exists(path) else []


def grouped(rows, value):
    """(L, dtype, chunk) -> {group: 數值}"""
    out = collections.defaultdict(collections.Counter)
    for r in rows:
        if r.get(value, "") in ("", "OOM"):
            continue
        out[(int(r["L"]), r["dtype"], r["chunk"])][GROUPS[r["module"]]] += float(r[value])
    return out


def shares(d):
    tot = sum(d.values())
    return {g: 100 * d.get(g, 0) / tot for g in ORDER}


def laptop_report():
    counts = read("counts_block.csv")
    meas = read("measured_block.csv")
    pred = grouped(counts, "roofline_s")
    flops = grouped(counts, "flops")
    nbytes = grouped(counts, "bytes")
    got = grouped(meas, "kernel_s")
    rows = []
    for key in sorted(got):
        L, dt, ch = key
        m, p = got[key], pred.get(key)
        if not p:
            continue
        ms, ps, fs, bs = shares(m), shares(p), shares(flops[key]), shares(nbytes[key])
        for g in ORDER:
            rows.append(dict(L=L, dtype=dt, chunk=ch, group=g,
                             measured_ms=1e3 * m.get(g, 0), roofline_ms=1e3 * p.get(g, 0),
                             measured_share=ms[g], roofline_share=ps[g], flop_share=fs[g], byte_share=bs[g]))
    if rows:
        with open(os.path.join(RESULTS, "compare_block.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    return rows


def print_laptop(rows):
    by = collections.defaultdict(dict)
    for r in rows:
        by[(r["dtype"], r["chunk"], r["L"])][r["group"]] = r
    print("\n=== 筆電：實測 vs roofline（一個 block） ===")
    print("設定           L    總實測ms  總預測ms  比值 | TriMul 實測/預測/FLOP/bytes % | TriAttn 實測/預測/FLOP/bytes %")
    for (dt, ch, L), g in sorted(by.items()):
        tm = sum(x["measured_ms"] for x in g.values())
        tp = sum(x["roofline_ms"] for x in g.values())
        a, b = g["TriMul"], g["TriAttn"]
        print(f"{dt}:{ch:>4} {L:>6} {tm:10.1f} {tp:9.1f} {tm/tp:5.2f} | "
              f"{a['measured_share']:5.1f} {a['roofline_share']:5.1f} {a['flop_share']:5.1f} {a['byte_share']:5.1f} | "
              f"{b['measured_share']:5.1f} {b['roofline_share']:5.1f} {b['flop_share']:5.1f} {b['byte_share']:5.1f}")


def calibration(rows, dtype, chunk, L):
    """筆電上 實測 ÷ 預測（每個分組各一個效率係數），找最接近的 L。"""
    cand = [r for r in rows if r["dtype"] == dtype and r["chunk"] == chunk]
    if not cand:
        return None
    best = min({r["L"] for r in cand}, key=lambda x: abs(x - L))
    return {r["group"]: r["measured_ms"] / r["roofline_ms"] for r in cand
            if r["L"] == best and r["roofline_ms"] > 0}, best


def h100_report(rows):
    print("\n=== V5：推 H100（不分塊），對照論文 Fig. 3（換算成佔 Folding Block 的 %）===")
    for L, paper in PAPER.items():
        pm = 100 * paper["TriMul"] / paper["block"]
        pa = 100 * paper["TriAttn"] / paper["block"]
        print(f"\nL = {L}：論文 TriMul {pm:.1f}%、TriAttn {pa:.1f}%")
        for dt in ("fp16", "fp32"):
            c = count_block(L, DTYPES[dt], None)
            cal = calibration(rows, dt, "64", L) if rows else None
            for name, spec in H100.items():
                t = roofline_seconds(c.ops, spec, dt)
                g = collections.Counter()
                for (mod, kind), sec in t.items():
                    g[GROUPS[mod]] += sec
                s = shares(g)
                line = f"  {dt} {name:9s} 純 roofline：TriMul {s['TriMul']:5.1f}%  TriAttn {s['TriAttn']:5.1f}%"
                if cal:
                    eff, Lc = cal
                    gc = collections.Counter({k: v * eff.get(k, 1) for k, v in g.items()})
                    sc = shares(gc)
                    line += f" | 用筆電 L={Lc} 的效率校正：TriMul {sc['TriMul']:5.1f}%  TriAttn {sc['TriAttn']:5.1f}%"
                print(line)


def plot(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cfgs = sorted({(r["dtype"], r["chunk"]) for r in rows})
    fig, axes = plt.subplots(1, len(cfgs), figsize=(4.2 * len(cfgs), 3.6), sharey=True)
    if len(cfgs) == 1:
        axes = [axes]
    colors = {"TriMul": "#c0392b", "TriAttn": "#2471a3", "Pair transition": "#7d8c2b",
              "Seq<->pair": "#8e44ad", "Seq track": "#d68910", "Residual/glue": "#7f8c8d"}
    for ax, (dt, ch) in zip(axes, cfgs):
        for g in ORDER:
            pts = sorted((r["L"], r["measured_share"], r["roofline_share"]) for r in rows
                         if r["dtype"] == dt and r["chunk"] == ch and r["group"] == g)
            if not pts:
                continue
            Ls = [p[0] for p in pts]
            ax.plot(Ls, [p[1] for p in pts], "-o", ms=3, color=colors[g], label=g)
            ax.plot(Ls, [p[2] for p in pts], "--", color=colors[g], alpha=0.6)
        ax.set_title(f"{dt}, chunk={ch}")
        ax.set_xlabel("L")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("share of block GPU time (%)\nsolid = measured, dashed = roofline")
    axes[-1].legend(fontsize=7)
    fig.tight_layout()
    out = os.path.join(RESULTS, "share_vs_L.png")
    fig.savefig(out, dpi=130)
    print("\n圖：", out)


def main():
    rows = laptop_report()
    if rows:
        print_laptop(rows)
        plot(rows)
    h100_report(rows)


if __name__ == "__main__":
    main()
