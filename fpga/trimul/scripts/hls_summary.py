"""把各版本的 HLS 合成報告整理成一張比較表。

用法（在 fpga/trimul 目錄下，先跑過 make hls KERNEL=...）：
    python3 scripts/hls_summary.py            # 印出表格
    python3 scripts/hls_summary.py --csv out.csv

讀取 hls_prj/<kernel>/sol/syn/report/csynth.xml。
Latency 是 HLS 在 L = L_TRIP（kernels/trimul.h，預設 256）時的估計值。
"""
import argparse
import glob
import os
import xml.etree.ElementTree as ET

C = 128


def text(root, path, default=None):
    node = root.find(path)
    return node.text.strip() if node is not None and node.text else default


def to_int(s):
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


def parse(xml_path, L):
    r = ET.parse(xml_path).getroot()
    # 用專案資料夾名稱（例如 trimul_v2_t16），才分得出同一個 kernel 的不同設定
    name = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(xml_path)))))
    target = float(text(r, "UserAssignments/TargetClockPeriod", "3.33"))
    est = float(text(r, "PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod", "nan"))
    lat = to_int(text(r, "PerformanceEstimates/SummaryOfOverallLatency/Worst-caseLatency"))
    res = {}
    for k in ["BRAM_18K", "URAM", "DSP", "FF", "LUT"]:
        used = to_int(text(r, f"AreaEstimates/Resources/{k}"))
        avail = to_int(text(r, f"AreaEstimates/AvailableResources/{k}"))
        res[k] = (used, avail)
    sec = lat * target * 1e-9 if lat is not None else None  # 以目標時脈（300 MHz）計算
    gflops = 2.0 * L**3 * C / sec / 1e9 if sec else None
    return {"kernel": name, "cycles": lat, "sec": sec, "gflops": gflops,
            "target_ns": target, "est_ns": est, "res": res}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prj", default="hls_prj")
    p.add_argument("--L", type=int, default=256, help="須與 kernels/trimul.h 的 L_TRIP 相同")
    p.add_argument("--csv")
    args = p.parse_args()

    rows = []
    for x in sorted(glob.glob(os.path.join(args.prj, "*", "sol", "syn", "report", "csynth.xml"))):
        try:
            rows.append(parse(x, args.L))
        except Exception as e:  # 單一報告壞掉不影響其他
            print(f"無法解析 {x}: {e}")
    if not rows:
        print("找不到任何報告，請先執行 make hls KERNEL=trimul_vN")
        return

    base = next((r for r in rows if r["kernel"] == "trimul_v0" and r["cycles"]), None)

    def pct(u, a):
        return f"{u} ({100 * u / a:.1f}%)" if u is not None and a else str(u)

    hdr = ["kernel", "cycles", "time(s)", "GFLOP/s", "speedup", "clock(ns)", "BRAM_18K", "URAM", "DSP", "LUT", "FF"]
    table = []
    for r in rows:
        sp = f"{base['cycles'] / r['cycles']:.1f}x" if base and r["cycles"] else "-"
        table.append([
            r["kernel"],
            f"{r['cycles']:,}" if r["cycles"] is not None else "?",
            f"{r['sec']:.4g}" if r["sec"] else "?",
            f"{r['gflops']:.3g}" if r["gflops"] else "?",
            sp,
            f"{r['est_ns']:.2f}/{r['target_ns']:.2f}",
            *[pct(*r["res"][k]) for k in ["BRAM_18K", "URAM", "DSP", "LUT", "FF"]],
        ])
    w = [max(len(h), *(len(t[i]) for t in table)) for i, h in enumerate(hdr)]
    print(f"HLS 估計（L = {args.L}，C = {C}，以目標時脈計算時間）")
    print("  ".join(h.ljust(w[i]) for i, h in enumerate(hdr)))
    for t in table:
        print("  ".join(c.ljust(w[i]) for i, c in enumerate(t)))
    if not base:
        print("\n（沒有 trimul_v0 的報告，所以 speedup 欄位空白）")

    if args.csv:
        with open(args.csv, "w") as f:
            f.write(",".join(hdr) + "\n")
            for t in table:
                f.write(",".join(c.replace(",", "") for c in t) + "\n")
        print(f"\n已寫入 {args.csv}")


if __name__ == "__main__":
    main()
