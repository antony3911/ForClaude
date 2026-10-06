"""把 server CPU 的 characterization 結果排成 PDF（中文、英文各一份）：時間佔比隨 L 的變化（整條流程）＋ 結論。

資料：python/char/results/measured_cpu.csv（run_cpu.py 的結果）
用法：python docs/report/build_char_summary.py
     → docs/report/characterization_summary.pdf、characterization_summary_en.pdf
"""
import csv
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def find_chrome():
    import shutil
    cands = [os.environ.get("CHROME"), shutil.which("chromium"), shutil.which("google-chrome"),
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
    return next((c for c in cands if c and os.path.exists(c)), None)


t = {}
for r in csv.DictReader(open(ROOT / "python/char/results/measured_cpu.csv", encoding="utf-8")):
    t.setdefault(int(r["L"]), {})[r["part"]] = float(r["seconds"])
LS = sorted(t)
PEAK = {76: 19.9, 256: 22.2, 512: 27.4, 1024: 60.7}

# 圖用的 7 組（顏色依固定順序，見 dataviz 的 categorical palette，已跑過驗證）
GROUP_PARTS = [
    (["tri_mul_out", "tri_mul_in"], "#2a78d6"),
    (["tri_att_start", "tri_att_end"], "#eb6834"),
    (["mlp_pair"], "#1baf7a"),
    (["seq_attention", "mlp_seq", "layernorm_1"], "#eda100"),
    (["sequence_to_pair", "pair_to_sequence"], "#e87ba4"),
    (["block_other"], "#008300"),
    (["esm2", "structure_module", "other"], "#4a3aa7"),
]
ROW_KEYS = ["tri_mul_out", "tri_mul_in", "tri_att_start", "tri_att_end", "mlp_pair", "seq_attention", "mlp_seq",
            "layernorm_1", "sequence_to_pair", "pair_to_sequence", "block_other", "esm2", "structure_module", "other"]

TXT = {
"zh": dict(
    lang="zh-Hant", out="characterization_summary.pdf",
    font='"Microsoft JhengHei", "Noto Sans TC", "PingFang TC", sans-serif',
    title="ESMFold 時間分布與結論（workload characterization）",
    groups=["TriMul（out＋in）", "TriAttn（start＋end）", "pair transition", "sequence track", "seq↔pair",
            "block 其他（residual 等）", "trunk 以外（ESM-2、structure module、其他）"],
    rows=["Triangle Multiplication（outgoing）", "Triangle Multiplication（incoming）",
          "Triangle Attention（starting node）", "Triangle Attention（ending node）", "pair transition（mlp_pair）",
          "sequence attention", "sequence transition（mlp_seq）", "LayerNorm（sequence）", "sequence → pair",
          "pair → sequence", "block 其他（residual 加法等）", "ESM-2（語言模型）", "structure module",
          "其他（embedding、recycling 等）"],
    total="總", sec="秒", col="類別", tot_row="總時間", peak_row="峰值記憶體（整個程式）",
    h1="1. 整條流程的時間佔比隨 L 的變化", h2="2. 結論", h3="3. 方法摘要", h4="4. 限制",
    note="一條橫條 = 一次完整推論（從胺基酸序列到 3D 結構）的總時間，切成互不重疊的 7 組；長度依序為 76（泛素）、256、512、1024。各組包含的細項與秒數見表 1。",
    box=["三角運算（藍＋橘）隨 L 越佔越多，L = 1024 達 90%。",
         "TriMul（藍）越來越小、TriAttn（橘）越來越大，在 L = 256～512 之間交叉。",
         "ESM-2 與 structure module（紫）在 L ≥ 256 時幾乎看不到。"],
    table_title="表 1　全部類別的時間與佔比（192 次 block 呼叫的總和）",
    conclusions="""
<div class="c"><h3>結論 1　整條流程的瓶頸是 pair 表示上的三角運算</h3>
<ul>
<li>L ≥ 256 時，TriMul ＋ TriAttn 佔整條流程 <b>82～90%</b>；48 個 block 合計 97～99%。</li>
<li>ESM-2 ＋ structure module：L ≥ 256 時不到 3%。ESM-2 佔全部參數的 80%，卻只佔不到 1% 的時間：參數量決定權重佔多少記憶體，時間則由中間資料（pair 表示 L²、三角運算 L³）決定。</li>
<li>與 LightNobel 只加速 trunk、不加速 ESM-2 與 structure module 的選擇一致。</li>
</ul></div>

<div class="c"><h3>結論 2　瓶頸隨長度轉移：短序列 TriMul 最大，長序列 TriAttn 最大</h3>
<ul>
<li>TriMul 佔比 57% → 52% → 35% → 22%；TriAttn 11% → 31% → 53% → 69%（L = 76 → 1024）。</li>
<li>兩者在 L = 256～512 之間交叉。</li>
<li>原因：兩者都有 L³ 運算，但 TriMul 的資料只有 L²（每筆資料被重複使用 L 次），TriAttn 會產生 L³ 大小的 logits（L = 1024 時 17 GB），搬運量跟著 L³ 成長。</li>
</ul></div>

<div class="c"><h3>結論 3　TriAttn：受記憶體頻寬限制，已貼近天花板</h3>
<p class="sub">現象</p>
<ul>
<li>tri_att_start（L = 1024）：<code>add_</code> 31% ＋ <code>softmax</code> 28% = 59% 在讀寫 logits；矩陣乘法只佔 27%。</li>
<li><code>add_</code> 的名目頻寬約 112 GB/s（計數的 68.7 GB ÷ 實測 0.616 s），機器上限約 100 GB/s（同種運算、同樣的記憶體擺放實測）→ 已用滿頻寬。roofline 達成率 58～88%。</li>
<li>L = 1024 峰值記憶體 60.7 GB，主要是不分塊的 logits（一份 17 GB）。</li>
<li>tri_att_end 在 L = 1024 時比 start 慢 583 ms，其中 578 ms（99%）來自 <code>add_</code>（1,194 vs 616 ms）；L = 512 時兩者相同。</li>
</ul>
<p class="sub">原因</p>
<ul>
<li>softmax 的依賴只需要「一列」（L = 1024 時 4 KB），17 GB 的搬運來自「一個運算處理完整個張量」的執行方式。</li>
</ul>
</div>

<div class="c"><h3>結論 4　TriMul：時間大半浪費在資料排列，不在計算；只修好排列，整體可省約 10～13%（L = 1024）、19～24%（L = 512）</h3>
<p class="sub">現象</p>
<ul>
<li><code>copy_</code>（permute 後的複製）佔 TriMul 的 <b>50～58%</b>；einsum 本身只佔 14～17%。</li>
<li>roofline 達成率只有 16～24%，三種運算中最低。</li>
<li>permute 複製只有 9 GB/s，連續複製 76～82 GB/s，慢約 9 倍。</li>
<li><b>對照實驗</b>：同形狀（128 個 1024×1024×1024）、資料已排好的矩陣乘法只要 <b>63 ms</b>（等於機器上限）；HF 的寫法是 einsum 149 ms ＋ copy 436 ms = <b>585 ms</b>，差 <b>9.3 倍</b>。形狀本身沒有問題，損失全在排列。</li>
</ul>
<p class="sub">原因</p>
<ul>
<li>bmm 要求 <code>[c][i][k]</code>，資料原本是 <code>[i][k][c]</code>。a、b 各轉一次、結果轉回一次，共 3 次。</li>
<li>同一 channel 的相鄰元素相隔 512 bytes，每抓一條 64 bytes 的 cache line 只用到 4 bytes。</li>
</ul>
<p class="sub">效益估算（只修好排列）</p>
<ul>
<li>一次 tri_mul_out（L = 1024，881 ms）＝ A 組（einsum ＋ copy）585 ms ＋ B 組（linear、gate、LayerNorm）296 ms。</li>
<li>保守情境（省掉進入前的 2 次 copy，結果仍要轉回 1 次）：A 組 63 ＋ 124 = 187 ms → TriMul 快 1.82 倍 → 整體省 <b>9.7%</b>。</li>
<li>理想情境（3 次 copy 全省）：A 組 63 ms → TriMul 快 2.45 倍 → 整體省 <b>12.8%</b>。</li>
<li>L = 512：理想 einsum 未實測，以效率範圍估算，整體省 19～24%。</li>
<li>假設 B 組不變；若再把 B 組融合（中間結果不寫回），還能更省 → 以上為保守估計。只優化 TriMul 的上限：L = 512 最多 1.54 倍、L = 1024 最多 1.28 倍。</li>
</ul></div>
""",
    method="""
<ul class="small">
<li><b>平台</b>：學校 server，2 × Intel Xeon Gold 6526Y（共 32 實體核），125 GB RAM，無 GPU；Python 3.9、torch 2.8.0+cpu、transformers 4.57.6。量測時負載為 0。</li>
<li><b>完整流程</b>（run_cpu.py）：HF ESMFold 全部 FP32 放 CPU、不分塊、32 執行緒，每個模組前後掐碼錶；類別互不重疊，加總等於總時間。48 個 block × 4 輪 recycling = 192 次呼叫（探針實測）。</li>
<li><b>正確性</b>：泛素預測結構與 PDB 1UBQ 的 CA RMSD = 0.83 Å。</li>
<li><b>拆解</b>（diagnose_cpu.py）：單一 block 的子模組，暖機後以 profiler 量 3 次；與完整流程的每次時間差 1.6%（TriMul）。</li>
<li><b>天花板</b>（ceilings_cpu.py）：矩陣乘法約 4,300 GFLOP/s（n = 16384，±5%）；頻寬約 100 GB/s（原地加法，記憶體分散在兩顆 CPU，與 ESMFold 的大張量相同；集中在一顆時只有一半）。</li>
<li><b>運算量、搬運量</b>：count_ops.py 以 meta tensor 計數；搬運量是「每個運算讀所有輸入、寫所有輸出」的名目值，不含快取效應，也不含 CPU 內部的逐 channel 複製。</li>
</ul>""",
    limits="""
<ul class="small">
<li>每個長度只跑一次；天花板同一點重複量測約 ±5%。</li>
<li>L = 512 的理想 einsum 未實測（以範圍估算）。</li>
<li>L &gt; 1024 只能依趨勢外推。只量推論、batch = 1。</li>
<li>單獨量的 TriAttn 比完整流程裡快 22～39%，原因只解釋一部分（新配置記憶體慢約 22%）；佔比以完整流程為準。</li>
<li>峰值記憶體是整個程式的最大值（含載入模型），短序列的數字主要反映載入時的用量。</li>
</ul>""",
),
"en": dict(
    lang="en", out="characterization_summary_en.pdf",
    font='"Segoe UI", "Helvetica Neue", Arial, sans-serif',
    title="ESMFold Time Breakdown and Findings (workload characterization)",
    groups=["TriMul (out + in)", "TriAttn (start + end)", "pair transition", "sequence track", "seq↔pair",
            "block other (residual etc.)", "outside the trunk (ESM-2, structure module, other)"],
    rows=["Triangle Multiplication (outgoing)", "Triangle Multiplication (incoming)",
          "Triangle Attention (starting node)", "Triangle Attention (ending node)", "pair transition (mlp_pair)",
          "sequence attention", "sequence transition (mlp_seq)", "LayerNorm (sequence)", "sequence → pair",
          "pair → sequence", "block other (residual additions etc.)", "ESM-2 (language model)",
          "structure module", "other (embedding, recycling etc.)"],
    total="total", sec="s", col="Category", tot_row="Total time", peak_row="Peak memory (whole process)",
    h1="1. Time share of the whole pipeline vs. sequence length L", h2="2. Findings", h3="3. Method summary",
    h4="4. Limitations",
    note="Each bar is the total time of one complete inference (amino-acid sequence in, 3D structure out), split into "
         "7 non-overlapping groups. Lengths: 76 (ubiquitin), 256, 512, 1024. Per-category seconds are in Table 1.",
    box=["The triangle operations (blue + orange) take a growing share as L increases, reaching 90% at L = 1024.",
         "TriMul (blue) shrinks while TriAttn (orange) grows; they cross between L = 256 and 512.",
         "ESM-2 and the structure module (purple) are barely visible for L ≥ 256."],
    table_title="Table 1　Time and share of every category (sum over 192 block calls)",
    conclusions="""
<div class="c"><h3>Finding 1　The bottleneck of the pipeline is the triangle operations on the pair representation</h3>
<ul>
<li>For L ≥ 256, TriMul + TriAttn take <b>82–90%</b> of the whole pipeline; the 48 blocks together take 97–99%.</li>
<li>ESM-2 + structure module: under 3% for L ≥ 256. ESM-2 holds 80% of all parameters but under 1% of the time: parameter count sets how much memory the weights need, while time is set by the intermediate data (pair representation L², triangle operations L³).</li>
<li>Consistent with LightNobel accelerating only the trunk, not ESM-2 or the structure module.</li>
</ul></div>

<div class="c"><h3>Finding 2　The bottleneck shifts with length: TriMul dominates short sequences, TriAttn dominates long ones</h3>
<ul>
<li>TriMul share 57% → 52% → 35% → 22%; TriAttn 11% → 31% → 53% → 69% (L = 76 → 1024).</li>
<li>The two cross between L = 256 and 512.</li>
<li>Reason: both perform L³ work, but TriMul's data is only L² (each element is reused L times), whereas TriAttn produces L³-sized logits (17 GB at L = 1024), so its data movement grows as L³.</li>
</ul></div>

<div class="c"><h3>Finding 3　TriAttn: memory-bandwidth bound, already close to the ceiling</h3>
<p class="sub">Observations</p>
<ul>
<li>tri_att_start (L = 1024): <code>add_</code> 31% + <code>softmax</code> 28% = 59% spent reading and writing logits; matrix multiplication takes only 27%.</li>
<li><code>add_</code> reaches a nominal bandwidth of about 112 GB/s (68.7 GB counted ÷ 0.616 s measured), against a machine ceiling of about 100 GB/s (same operation, same memory placement) → bandwidth is saturated. Roofline efficiency 58–88%.</li>
<li>Peak memory at L = 1024 is 60.7 GB, mostly the unchunked logits (17 GB per copy).</li>
<li>At L = 1024, tri_att_end is 583 ms slower than start; 578 ms of it (99%) comes from <code>add_</code> (1,194 vs 616 ms). At L = 512 the two are equal.</li>
</ul>
<p class="sub">Cause</p>
<ul>
<li>The softmax dependency needs only one row (4 KB at L = 1024); the 17 GB of traffic comes from executing each operation over the entire tensor before starting the next.</li>
</ul>
</div>

<div class="c"><h3>Finding 4　TriMul: most of its time is lost to data layout, not computation; fixing the layout alone saves about 10–13% of total time (L = 1024) and 19–24% (L = 512)</h3>
<p class="sub">Observations</p>
<ul>
<li><code>copy_</code> (copies after permute) takes <b>50–58%</b> of TriMul; the einsum itself only 14–17%.</li>
<li>Roofline efficiency is only 16–24%, the lowest of the three operations.</li>
<li>A permuted copy runs at only 9 GB/s versus 76–82 GB/s for a contiguous copy, about 9× slower.</li>
<li><b>Control experiment</b>: a matrix multiplication of the same shape (128 × 1024×1024×1024) with data already in the right layout takes only <b>63 ms</b> (the machine ceiling); the HF implementation takes einsum 149 ms + copy 436 ms = <b>585 ms</b>, a <b>9.3×</b> gap. The shape is not the problem; the entire loss is in the layout.</li>
</ul>
<p class="sub">Cause</p>
<ul>
<li>bmm requires <code>[c][i][k]</code>, but the data is stored as <code>[i][k][c]</code>. a and b are each transposed once and the result is transposed back once: 3 copies in total.</li>
<li>Adjacent elements of the same channel are 512 bytes apart, so each 64-byte cache line fetched yields only 4 useful bytes.</li>
</ul>
<p class="sub">Estimated benefit (fixing the layout only)</p>
<ul>
<li>One tri_mul_out call (L = 1024, 881 ms) = group A (einsum + copies) 585 ms + group B (linear, gating, LayerNorm) 296 ms.</li>
<li>Conservative case (remove the 2 copies before the einsum, still transpose the result back once): group A = 63 + 124 = 187 ms → TriMul 1.82× faster → total time reduced by <b>9.7%</b>.</li>
<li>Ideal case (all 3 copies removed): group A = 63 ms → TriMul 2.45× faster → total time reduced by <b>12.8%</b>.</li>
<li>L = 512: the ideal einsum was not measured; estimated from an efficiency range, total time reduced by 19–24%.</li>
<li>Group B is assumed unchanged; fusing group B as well (no intermediate write-back) would save more, so these are conservative estimates. Upper bound for optimizing TriMul alone: at most 1.54× at L = 512 and 1.28× at L = 1024.</li>
</ul></div>
""",
    method="""
<ul class="small">
<li><b>Platform</b>: lab server, 2 × Intel Xeon Gold 6526Y (32 physical cores), 125 GB RAM, no GPU; Python 3.9, torch 2.8.0+cpu, transformers 4.57.6. System load was zero during measurement.</li>
<li><b>Whole pipeline</b> (run_cpu.py): HF ESMFold entirely in FP32 on the CPU, no chunking, 32 threads; wall-clock timing around every module; categories do not overlap and sum to the total. 48 blocks × 4 recycling passes = 192 calls (counted by the hooks).</li>
<li><b>Correctness</b>: predicted ubiquitin structure vs. PDB 1UBQ, CA RMSD = 0.83 Å.</li>
<li><b>Breakdown</b> (diagnose_cpu.py): submodules of a single block, profiled 3 times after warm-up; per-call time within 1.6% of the whole-pipeline measurement (TriMul).</li>
<li><b>Ceilings</b> (ceilings_cpu.py): matrix multiplication about 4,300 GFLOP/s (n = 16384, ±5%); bandwidth about 100 GB/s (in-place add, memory spread across both CPUs as for ESMFold's large tensors; half that when placed on one CPU).</li>
<li><b>Operation and traffic counts</b>: count_ops.py, using meta tensors; traffic is the nominal "read all inputs, write all outputs" per operation, excluding cache effects and the CPU's internal per-channel copies.</li>
</ul>""",
    limits="""
<ul class="small">
<li>Each length was run once; repeated ceiling measurements vary by about ±5%.</li>
<li>The ideal einsum at L = 512 was not measured (estimated as a range).</li>
<li>L &gt; 1024 is extrapolated from the trend only. Inference only, batch size 1.</li>
<li>TriAttn measured in isolation is 22–39% faster than inside the whole pipeline; this is only partly explained (writing to newly allocated memory is about 22% slower). Shares are taken from the whole pipeline.</li>
<li>Peak memory is the maximum of the whole process (including model loading); for short sequences it mainly reflects loading.</li>
</ul>""",
),
}

CSS = """
@page { size: A4; margin: 16mm 15mm; }
body { font-family: FONT; color: #0b0b0b; background: #ffffff; font-size: 10pt; line-height: 1.5; }
h1 { font-size: 17pt; margin: 0 0 2px; }
h2 { font-size: 13pt; border-bottom: 1.5px solid #0b0b0b; padding-bottom: 2px; margin: 18px 0 8px; }
h3 { font-size: 11pt; margin: 0 0 4px; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 9pt; margin: 6px 0 8px; }
.lg i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px; vertical-align: -1px; }
table { border-collapse: collapse; width: 100%; font-size: 8.6pt; margin-top: 6px; }
th, td { border-bottom: 1px solid #e3e2dc; padding: 2.5px 5px; text-align: right; font-variant-numeric: tabular-nums; }
th { color: #52514e; font-weight: 600; text-align: center; }
td.l, th.l { text-align: left; }
tr.tot td { border-top: 1.5px solid #0b0b0b; font-weight: 600; }
.note { font-size: 8.6pt; color: #52514e; }
.c { border: 1px solid #d8d7d0; border-radius: 6px; padding: 8px 12px; margin: 0 0 8px; break-inside: avoid; }
.c ul { margin: 2px 0 0; padding-left: 18px; }
.c li { margin: 1px 0; }
code { font-family: Consolas, monospace; font-size: 8.8pt; }
.small { font-size: 8.8pt; }
.page { break-before: page; }
.sub { font-size: 9pt; font-weight: 600; color: #52514e; margin: 5px 0 0; }
.box ol { margin: 0; padding-left: 20px; }
.box { background: #f4f4f1; border-radius: 6px; padding: 8px 12px; margin: 8px 0; font-size: 9.5pt; }
"""


def text_color(hexcode):
    r, g, b = (int(hexcode[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lum = 0.2126 * r ** 2.2 + 0.7152 * g ** 2.2 + 0.0722 * b ** 2.2
    return "#0b0b0b" if lum > 0.3 else "#ffffff"


def chart(tx):
    W, x0, x1, row, gap, top = 700, 92, 690, 34, 16, 6
    h = top + len(LS) * (row + gap)
    out = [f'<svg viewBox="0 0 {W} {h}" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="inherit" role="img">']
    for n, L in enumerate(LS):
        y = top + n * (row + gap)
        tot = t[L]["total"]
        out.append(f'<clipPath id="c{L}"><rect x="{x0}" y="{y}" width="{x1 - x0}" height="{row}" rx="4"/></clipPath>')
        out.append(f'<text x="0" y="{y + 15}" font-size="12" font-weight="600" fill="#0b0b0b">L = {L}</text>')
        out.append(f'<text x="0" y="{y + 30}" font-size="10" fill="#52514e">{tx["total"]} {tot:,.1f} s</text>')
        out.append(f'<g clip-path="url(#c{L})">')
        x = x0
        for name, (parts, col) in zip(tx["groups"], GROUP_PARTS):
            share = sum(t[L][p] for p in parts) / tot
            w = share * (x1 - x0)
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w - 2, 0):.1f}" height="{row}" fill="{col}">'
                       f'<title>{name}: {100 * share:.1f}%</title></rect>')
            if w >= 34:
                out.append(f'<text x="{x + w / 2 - 1:.1f}" y="{y + row / 2 + 4}" font-size="11" text-anchor="middle" '
                           f'fill="{text_color(col)}">{100 * share:.0f}%</text>')
            x += w
        out.append("</g>")
    out.append("</svg>")
    return "".join(out)


def legend(tx):
    items = "".join(f'<span class="lg"><i style="background:{c}"></i>{n}</span>'
                    for n, (_, c) in zip(tx["groups"], GROUP_PARTS))
    return f'<div class="legend">{items}</div>'


def table(tx):
    head = "".join(f"<th colspan=2>L = {L}</th>" for L in LS)
    sub = "".join(f"<th>{tx['sec']}</th><th>%</th>" for _ in LS)
    body = []
    for key, label in zip(ROW_KEYS, tx["rows"]):
        cells = "".join(f"<td>{t[L][key]:,.2f}</td><td>{100 * t[L][key] / t[L]['total']:.1f}</td>" for L in LS)
        body.append(f"<tr><td class=l>{label}</td>{cells}</tr>")
    tot = "".join(f"<td>{t[L]['total']:,.1f}</td><td>100</td>" for L in LS)
    peak = "".join(f"<td colspan=2>{PEAK[L]} GB</td>" for L in LS)
    return (f'<table><thead><tr><th rowspan=2 class=l>{tx["col"]}</th>{head}</tr><tr>{sub}</tr></thead>'
            f'<tbody>{"".join(body)}<tr class=tot><td class=l>{tx["tot_row"]}</td>{tot}</tr>'
            f'<tr><td class=l>{tx["peak_row"]}</td>{peak}</tr></tbody></table>')


def build(tx):
    box = "".join(f"<li>{s}</li>" for s in tx["box"])
    html = f"""<!DOCTYPE html><html lang="{tx['lang']}"><head><meta charset="utf-8">
<title>{tx['title']}</title><style>{CSS.replace('FONT', tx['font'])}</style></head><body>
<h1>{tx['title']}</h1>
<h2>{tx['h1']}</h2>
{legend(tx)}
{chart(tx)}
<p class="note">{tx['note']}</p>
<div class="box"><ol>{box}</ol></div>
<h3 style="margin-top:12px">{tx['table_title']}</h3>
{table(tx)}
<h2 class="page">{tx['h2']}</h2>
{tx['conclusions']}
<h2 class="page">{tx['h3']}</h2>
{tx['method']}
<h2>{tx['h4']}</h2>
{tx['limits']}
</body></html>"""
    out_pdf = HERE / tx["out"]
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / "summary.html"
        src.write_text(html, encoding="utf-8")
        chrome = find_chrome()
        if not chrome:
            sys.exit("找不到 Chrome/Edge")
        r = subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                            f"--user-data-dir={tmp}/profile", f"--print-to-pdf={out_pdf}", src.as_uri()],
                           capture_output=True, text=True, timeout=180)
        if not out_pdf.exists():
            sys.exit(r.stderr[-2000:])
    print(f"已產生 {out_pdf}")


if __name__ == "__main__":
    for tx in TXT.values():
        build(tx)
