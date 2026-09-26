"""Triangle Multiplication kernel 的分析模型（architectural model）。

用途：
  1. 預測 v0～v4 在任意 L、tile 大小下的 cycle 數、GFLOP/s、算術強度（roofline 用）
  2. 粗估硬體資源（DSP、BRAM）
  3. 計算 HBM 容量限制下可處理的最大序列長度 L（含「融合＋INT8」的預估）
  4. 若有 HLS 報告（hls_prj/*/sol/syn/report/csynth.xml），自動比對預測誤差
  5. 設計空間探索（DSE）：掃過 tile 大小，列出 Pareto 最佳設定

用法（在 fpga/trimul 目錄下）：
    python3 scripts/perf_model.py                 # 全部輸出
    python3 scripts/perf_model.py --csv model.csv # 另外把 DSE 結果存成 CSV
    make model

模型常數的來源：
  - 已校正（CALIBRATED）：v2 的 HLS 報告（Vitis 2025.2，L=256，8x8 tile，2026-09-26）
      load_a/load_b = 141 cycles（64 個 512-bit word + 77 overhead）
      mac = 526（512 + 14 pipeline depth）、store = 586、init = 514、loop_k 每輪額外 4
  - 假設值（ASSUMED）：其他版本的 overhead 與 pipeline depth、DSP 用量。
    拿到 v0/v1/v3/v4 的報告後，比對誤差並更新下面的常數。
"""

import argparse
import glob
import math
import os
import xml.etree.ElementTree as ET

C = 128
FREQ_HZ = 300e6
L_TRIP = 256  # 必須和 kernels/trimul.h 的 L_TRIP 一致

# ---------------- 模型常數 ----------------
# 校正值（來自 v2 報告）
MAXI_OVH = 77      # 一次 burst 載入的固定 overhead（HBM 延遲 + 迴圈啟動）
MAC_DEPTH = 14     # 16 lane 浮點 MAC pipeline 深度
STORE_OVH = 74     # 寫回的固定 overhead
INIT_OVH = 2
KITER_OVH = 4      # loop_k 每輪的額外 cycle
TILE_OVH = 4       # 每個 tile 的額外 cycle
# 假設值（待校正）
FADD_II = 4        # v0：浮點累加的跨迭代相依 → II ≈ fadd latency（ASSUMED）
V0_LOOP_OVH = 80   # v0：每個 (i,j,c) 的 k 迴圈啟動成本（ASSUMED，含 m_axi 延遲）
V1_MAC_DEPTH = 10  # v1：純量 MAC 的 pipeline 深度（ASSUMED）
V4_MAC_DEPTH = 20  # v4：int8 乘法 + 轉浮點 + 縮放 + 累加（ASSUMED）
SCALE_LOAD = 2     # v4：每個 scale 讀取約 2 cycle（ASSUMED）

# DSP 估計（Vitis 預設：fmul ≈ 3 DSP、fadd ≈ 2 DSP；ASSUMED）
DSP_FMUL, DSP_FADD = 3, 2
U55C = {"DSP": 9024, "BRAM_18K": 4032, "HBM_GB": 16, "PORT_GB": 4}


# ---------------- 各版本的 cycle 模型 ----------------
def cycles(version, L, TI=8, TJ=8):
    """回傳 (總 cycle, 每輪 loop_k 的 cycle, 拆解 dict)。"""
    tiles = (L // TI) * (L // TJ)
    if version == "v0":
        per = L * FADD_II + V0_LOOP_OVH
        total = L * L * C * per
        return total, None, {"per_output": per}

    if version == "v1":
        load = max(TI, TJ) * C + MAXI_OVH          # 32-bit port：每 cycle 1 個 float
        mac = TI * TJ * C + V1_MAC_DEPTH
        kiter = load + mac + KITER_OVH
        init, store = TI * TJ * C + INIT_OVH, TI * TJ * C + STORE_OVH
    elif version in ("v2", "v3"):
        CW = C // 16
        load = max(TI, TJ) * CW + MAXI_OVH
        mac = TI * TJ * CW + MAC_DEPTH
        if version == "v2":
            kiter = load + mac + KITER_OVH
        else:  # v3：載入和計算重疊
            kiter = max(load, mac) + KITER_OVH
        init, store = TI * TJ * CW + INIT_OVH, TI * TJ * CW + STORE_OVH
        if version == "v3":
            init += load  # 第一批要先載入
    elif version == "v4":
        QW = C // 64
        load = max(TI, TJ) * QW + MAXI_OVH
        load += (TI + TJ) * SCALE_LOAD            # per-token scale
        mac = TI * TJ * QW + V4_MAC_DEPTH
        kiter = load + mac + KITER_OVH
        init = TI * TJ * QW + INIT_OVH
        store = TI * TJ * QW * 4 + STORE_OVH      # 64 個 float → 4 個 512-bit word
    else:
        raise ValueError(version)
    per_tile = init + L * kiter + store + TILE_OVH
    total = tiles * per_tile
    return total, kiter, {"load": load, "mac": mac, "init": init, "store": store}


def arithmetic_intensity(version, TI=8, TJ=8):
    """FLOP / off-chip byte（讀取部分，L 大時寫回可忽略）。"""
    if version == "v0":
        return 2 / 8
    reuse = 1 / TI + 1 / TJ
    if version == "v4":
        return 2 * C / (reuse * (C + 4))
    return 2 / (4 * reuse)


def peak_gflops(version):
    lanes = {"v0": 1, "v1": 1, "v2": 16, "v3": 16, "v4": 64}[version]
    return 2 * lanes * FREQ_HZ / 1e9


def resources(version, TI=8, TJ=8):
    """粗估 DSP 與 BRAM_18K（ASSUMED，僅供趨勢比較）。"""
    lanes = {"v0": 1, "v1": 1, "v2": 16, "v3": 16, "v4": 64}[version]
    dsp = lanes * (DSP_FMUL + DSP_FADD)
    if version == "v4":
        dsp += lanes * (1 + DSP_FMUL)  # int8 乘法 + 乘 scale
    if version == "v0":
        bram = 0
    else:
        acc_words = TI * TJ * C // lanes          # 每個 lane 的深度
        bram = lanes * math.ceil(acc_words / 512)  # 18Kb ≈ 512 x 36bit
        buf_banks = 2 if version == "v3" else 1
        bram += buf_banks * 2 * lanes * math.ceil(max(TI, TJ) * C / lanes / 512)
    return dsp, bram


# ---------------- 容量模型 ----------------
FOOTPRINT = {  # 每個 L² 需要的 bytes（C=128）
    # 完整的 Triangle Multiplication 一步（含 LayerNorm、投影、gating 的中間值）
    "[完整一步] 典型實作（約 7 份 FP32）": 7 * C * 4,
    "[完整一步] 融合 + INT8 中間值（方向 A）": 2 * C * 4 + 2 * (C + 4),
    # 只有 einsum 核心（目前 v0～v4 實作的範圍）
    "[只算 einsum] v2（a、b、z，FP32）": 3 * C * 4,
    "[只算 einsum] v4（a、b INT8，z FP32）": 2 * (C + 4) + C * 4,
}


def max_L(bytes_per_L2, budget_gb):
    return int(math.sqrt(budget_gb * 2**30 / bytes_per_L2))


# ---------------- 讀取 HLS 報告 ----------------
def read_reports(prj="hls_prj"):
    out = {}
    for x in glob.glob(os.path.join(prj, "*", "sol", "syn", "report", "csynth.xml")):
        name = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(x)))))
        try:
            r = ET.parse(x).getroot()
            lat = r.find("PerformanceEstimates/SummaryOfOverallLatency/Worst-caseLatency")
            out[name] = int(lat.text)
        except Exception:
            pass
    return out


def parse_name(name):
    """trimul_v2 → (v2, 8, 8)；trimul_v2_t16 → (v2, 16, 16)"""
    parts = name.split("_")
    v = next((p for p in parts if p.startswith("v") and p[1:].isdigit()), None)
    t = next((int(p[1:]) for p in parts if p.startswith("t") and p[1:].isdigit()), 8)
    return v, t, t


def fmt(n):
    return f"{n:,.0f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", type=int, default=L_TRIP)
    ap.add_argument("--prj", default="hls_prj")
    ap.add_argument("--csv")
    a = ap.parse_args()
    L = a.L
    flops = 2 * L**3 * C

    print(f"=== 1. 各版本預測（L = {L}，tile 8x8，{FREQ_HZ/1e6:.0f} MHz）===")
    print(f"{'版本':<6}{'cycles':>16}{'時間(s)':>10}{'GFLOP/s':>9}{'峰值':>7}{'AI':>7}{'loop_k':>8}{'DSP':>6}{'BRAM':>6}")
    for v in ["v0", "v1", "v2", "v3", "v4"]:
        cyc, kiter, _ = cycles(v, L)
        sec = cyc / FREQ_HZ
        dsp, bram = resources(v)
        print(f"{v:<6}{fmt(cyc):>16}{sec:>10.4g}{flops/sec/1e9:>9.3g}{peak_gflops(v):>7.3g}"
              f"{arithmetic_intensity(v):>7.2f}{(kiter or 0):>8}{dsp:>6}{bram:>6}")

    reps = read_reports(a.prj)
    if reps:
        print("\n=== 2. 模型 vs HLS 報告 ===")
        print(f"{'專案':<20}{'HLS cycles':>16}{'模型 cycles':>16}{'誤差':>9}")
        for name in sorted(reps):
            v, ti, tj = parse_name(name)
            if not v:
                continue
            pred, _, _ = cycles(v, L_TRIP, ti, tj)
            err = (pred - reps[name]) / reps[name] * 100
            print(f"{name:<20}{fmt(reps[name]):>16}{fmt(pred):>16}{err:>8.1f}%")
        print("（誤差大的版本：回頭檢查該版本報告中各迴圈的 cycle 數，更新本檔上方的常數）")
    else:
        print(f"\n（找不到 {a.prj}/*/sol/syn/report/csynth.xml，略過模型驗證）")

    print(f"\n=== 3. 設計空間探索（L = {L}）===")
    rows = []
    for v in ["v2", "v3", "v4"]:
        for t in [4, 8, 16, 32]:
            if L % t:
                continue
            cyc, kiter, br = cycles(v, L, t, t)
            dsp, bram = resources(v, t, t)
            ok = dsp <= U55C["DSP"] and bram <= U55C["BRAM_18K"]
            rows.append(dict(version=v, tile=t, cycles=cyc, gflops=flops / (cyc / FREQ_HZ) / 1e9,
                             ai=arithmetic_intensity(v, t, t),
                             # 未被隱藏的等待比例：v3 的載入與計算重疊，只有超出計算的部分算等待
                             mem_frac=(max(0, br["load"] - br["mac"]) if v == "v3" else br["load"]) / kiter,
                             dsp=dsp, bram=bram, fits=ok))
    print(f"{'版本':<6}{'tile':>6}{'cycles':>16}{'GFLOP/s':>9}{'AI':>7}{'等記憶體':>10}{'DSP':>6}{'BRAM':>6}{'放得下':>7}")
    for r in rows:
        print(f"{r['version']:<6}{r['tile']:>6}{fmt(r['cycles']):>16}{r['gflops']:>9.3g}{r['ai']:>7.2f}"
              f"{r['mem_frac']*100:>9.0f}%{r['dsp']:>6}{r['bram']:>6}{'是' if r['fits'] else '否':>7}")
    pareto = [r for r in rows if r["fits"] and not any(
        o["fits"] and o["cycles"] <= r["cycles"] and o["bram"] <= r["bram"] and o is not r
        and (o["cycles"] < r["cycles"] or o["bram"] < r["bram"]) for o in rows)]
    print("Pareto 最佳（cycles 與 BRAM 無法同時更好）：",
          ", ".join(f"{r['version']}@{r['tile']}x{r['tile']}" for r in pareto))

    print("\n=== 4. 容量模型：U55C 16 GB HBM 可處理的最大序列長度 ===")
    print(f"{'配置':<42}{'bytes/L²':>10}{'最大 L（16 GB）':>16}{'相對':>7}")
    base = None
    for k, b in FOOTPRINT.items():
        m = max_L(b, U55C["HBM_GB"])
        base = base or m
        print(f"{k:<42}{b:>10}{m:>16,}{m/base:>6.2f}x")
    print("（相對值以第一列為基準；只計 pair 張量，未計其他層、權重與 HBM 分區限制）")

    if a.csv:
        with open(a.csv, "w") as f:
            f.write("version,tile,cycles,gflops,ai,mem_frac,dsp,bram,fits\n")
            for r in rows:
                f.write(f"{r['version']},{r['tile']},{r['cycles']},{r['gflops']:.4f},{r['ai']:.4f},"
                        f"{r['mem_frac']:.4f},{r['dsp']},{r['bram']},{int(r['fits'])}\n")
        print(f"\n已寫入 {a.csv}")


if __name__ == "__main__":
    main()
