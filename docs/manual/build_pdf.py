"""把 docs/manual/ 的各章 Markdown 合併成一份排版好的 HTML 與 PDF。

用法：
    pip install markdown
    python3 docs/manual/build_pdf.py            # 產生 manual.html 與 manual.pdf

PDF 由 Chromium / Chrome 的 headless 列印功能產生。找不到瀏覽器時只輸出 HTML，
可以用瀏覽器打開 manual.html，再用「列印 → 另存為 PDF」。
可用環境變數 CHROME 指定瀏覽器路徑。
"""

import datetime
import glob
import html
import os
import re
import shutil
import subprocess
import sys

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
# (檔案, 從這章開始的「部」標題；None 表示同一部)
CHAPTERS = [
    ("00_guide.md", None),
    ("01_why.md", "第一部　背景與理論"),
    ("02_why_it_works.md", None),
    ("03_tools.md", "第二部　工具與實作"),
    ("04_workflow.md", None),
    ("05_commands.md", "第三部　動手操作"),
    ("06_strategy.md", "第四部　專題策略"),
    ("07_research_method.md", "第五部　研究方法"),
    ("A_glossary.md", "附錄"),
    ("B_answers.md", None),
]

CSS = r"""
/* 等寬區塊：英文、框線用 DejaVu Sans Mono（寬 0.602em）；中文放大到剛好 2 個英文字寬，
   讓含中文的 ASCII 圖能對齊 */
@font-face {
  font-family: "CJKMono2x";
  src: local("WenQuanYi Zen Hei Mono"), local("WenQuanYi Zen Hei"),
       local("Noto Sans Mono CJK TC"), local("Microsoft JhengHei"), local("MingLiU");
  size-adjust: 120.4%;
  unicode-range: U+1100-11FF, U+2E80-2FFF, U+3000-303F, U+3040-9FFF, U+AC00-D7AF, U+F900-FAFF, U+FE30-FE4F, U+FF00-FF60, U+FFE0-FFE6;
}
@page {
  size: A4;
  margin: 18mm 16mm 20mm 16mm;
  @bottom-center { content: counter(page); font-size: 9pt; color: #888; }
}
@page :first { @bottom-center { content: none; } }
:root {
  --ink: #1f2328; --muted: #57606a; --line: #d0d7de; --accent: #0b5cad;
  --code-bg: #f6f8fa; --quote-bg: #eef5ff; --th-bg: #f0f3f6;
}
html { font-size: 10.5pt; }
body {
  font-family: "WenQuanYi Zen Hei", "Noto Sans CJK TC", "Microsoft JhengHei", "PingFang TC", sans-serif;
  color: var(--ink); line-height: 1.7; margin: 0;
}
h1, h2, h3, h4 { line-height: 1.35; page-break-after: avoid; break-after: avoid; }
h1 {
  font-size: 20pt; color: var(--accent); border-bottom: 3px solid var(--accent);
  padding-bottom: 6px; margin: 0 0 14px;
}
h2 { font-size: 14.5pt; border-bottom: 1px solid var(--line); padding-bottom: 4px; margin: 26px 0 10px; }
h3 { font-size: 12pt; margin: 20px 0 8px; }
h4 { font-size: 11pt; margin: 16px 0 6px; }
p { margin: 6px 0; }
a { color: var(--accent); text-decoration: none; }
strong { color: #000; }
code {
  font-family: "DejaVu Sans Mono", "CJKMono2x", monospace;
  font-size: 0.88em; background: var(--code-bg); padding: 1px 4px; border-radius: 4px;
}
pre {
  font-family: "DejaVu Sans Mono", "CJKMono2x", monospace;
  background: var(--code-bg); border: 1px solid var(--line); border-radius: 6px;
  padding: 10px 12px; font-size: 8.6pt; line-height: 1.45;
  white-space: pre-wrap; word-break: break-word; page-break-inside: avoid; break-inside: avoid;
}
pre code { background: none; padding: 0; font-size: inherit; font-family: inherit; }
blockquote {
  margin: 10px 0; padding: 8px 14px; background: var(--quote-bg);
  border-left: 4px solid var(--accent); border-radius: 0 6px 6px 0;
}
blockquote p { margin: 4px 0; }
table {
  border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.2pt;
  page-break-inside: auto;
}
tr { page-break-inside: avoid; break-inside: avoid; }
th, td { border: 1px solid var(--line); padding: 5px 7px; vertical-align: top; text-align: left; }
th { background: var(--th-bg); font-weight: bold; }
tbody tr:nth-child(even) td { background: #fafbfc; }
ul, ol { padding-left: 22px; margin: 6px 0; }
li { margin: 2px 0; }
hr { border: none; border-top: 1px solid var(--line); margin: 18px 0; }
.chapter { page-break-before: always; break-before: page; }
.part {
  display: inline-block; font-size: 10pt; color: #fff; background: var(--accent);
  padding: 3px 12px; border-radius: 12px; margin-bottom: 10px; letter-spacing: 1px;
}
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: center; }
.cover .title { font-size: 28pt; font-weight: bold; color: var(--accent); line-height: 1.3; }
.cover .subtitle { font-size: 14pt; color: var(--muted); margin-top: 12px; }
.cover .meta { margin-top: 40px; font-size: 10.5pt; color: var(--muted); line-height: 1.9; }
.toc h1 { border: none; }
.toc ol { list-style: none; padding-left: 0; }
.toc > ol > li { margin: 10px 0 4px; font-weight: bold; font-size: 11.5pt; }
.toc ol ol { padding-left: 18px; }
.toc ol ol li { font-weight: normal; font-size: 10pt; margin: 1px 0; }
"""


def slug_prefix(n):
    return f"ch{n}-"


LIST_RE = re.compile(r"^((?:> ?)*)(\s*)([-*+]|\d+\.)\s")


def add_blank_before_lists(text):
    """Python-Markdown 要求清單前有空行（GitHub 不需要）；在需要的地方自動補上。"""
    out, prev = [], ""
    in_code = False
    for line in text.split("\n"):
        if line.lstrip("> ").startswith("```"):
            in_code = not in_code
        m = LIST_RE.match(line)
        if m and not in_code:
            prefix = m.group(1)
            pm = LIST_RE.match(prev)
            prev_body = prev[len(prefix):].strip() if prev.startswith(prefix) else prev.strip()
            if prev_body and not pm and not prev_body.startswith("|"):
                out.append(prefix.rstrip())
        out.append(line)
        prev = line
    return "\n".join(out)


def render_chapter(n, path):
    text = add_blank_before_lists(open(path, encoding="utf-8").read())
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": lambda v, sep: slug_prefix(n) + re.sub(r"\W+", "-", v).strip("-")}},
    )
    body = md.convert(text)
    return body, md.toc_tokens


def build_toc(entries):
    out = ['<div class="toc chapter"><h1>目錄</h1><ol>']
    for tokens in entries:
        for h1 in tokens:
            out.append(f'<li><a href="#{h1["id"]}">{html.escape(h1["name"])}</a>')
            subs = [c for c in h1.get("children", []) if c["level"] == 2]
            if subs:
                out.append("<ol>")
                for h2 in subs:
                    out.append(f'<li><a href="#{h2["id"]}">{html.escape(h2["name"])}</a></li>')
                out.append("</ol>")
            out.append("</li>")
    out.append("</ol></div>")
    return "\n".join(out)


def find_chrome():
    cands = [os.environ.get("CHROME")]
    cands += sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"), reverse=True)
    for name in ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"]:
        cands.append(shutil.which(name))
    cands += [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


def main():
    bodies, tocs = [], []
    for n, (name, part) in enumerate(CHAPTERS, 1):
        body, toc = render_chapter(n, os.path.join(HERE, name))
        label = f'<div class="part">{part}</div>\n' if part else ""
        bodies.append(f'<section class="chapter">\n{label}{body}\n</section>')
        tocs.append(toc)

    today = datetime.date.today().isoformat()
    cover = f"""
<div class="cover">
  <div class="title">從 LightNobel 到 FPGA<br>記憶體優化教學手冊</div>
  <div class="subtitle">蛋白質結構預測模型的 memory-bound 問題，以及在 AMD Alveo U55C 上的常見解法</div>
  <div class="meta">
    專題 reference：LightNobel (ISCA 2025)<br>
    程式碼：github.com/antony3911/ForClaude（分支 claude/lightnobel-memory-optimization-yhokyc）<br>
    產生日期：{today}
  </div>
</div>"""

    doc = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<title>LightNobel 到 FPGA：記憶體優化教學手冊</title>
<style>{CSS}</style></head>
<body>
{cover}
{build_toc(tocs)}
{''.join(bodies)}
</body></html>"""

    html_path = os.path.join(HERE, "manual.html")
    pdf_path = os.path.join(HERE, "manual.pdf")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"已產生 {html_path}")

    chrome = find_chrome()
    if not chrome:
        print("找不到 Chrome/Chromium：請用瀏覽器打開 manual.html，列印 → 另存為 PDF")
        return
    cmd = [
        chrome, "--headless", "--no-sandbox", "--disable-gpu",
        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
        "file://" + html_path.replace(os.sep, "/"),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or not os.path.exists(pdf_path):
        print(r.stderr[-2000:])
        sys.exit("PDF 產生失敗")
    print(f"已產生 {pdf_path}（{os.path.getsize(pdf_path) / 1e6:.1f} MB）")


if __name__ == "__main__":
    main()
