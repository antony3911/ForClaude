"""把 docs/report/ 的技術摘要（英文、中文）排成 PDF，沿用手冊的排版與 Chromium 列印。

用法：
    python3 docs/report/build_report.py        # 產生 summary_en.pdf、summary_zh.pdf
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "manual"))
import build_pdf as bp  # noqa: E402

EXTRA_CSS = r"""
@page :first { @bottom-center { content: counter(page); font-size: 9pt; color: #888; } }
html { font-size: 11pt; }
h1 { font-size: 17pt; }
h2:not(:first-of-type) { break-before: page; page-break-before: always; }
"""

EN_FONT = r"""
body { font-family: "DejaVu Sans", "WenQuanYi Zen Hei", sans-serif; }
"""

DOCS = [
    ("summary_en.md", "summary_en", "en", "LightNobel and FPGA TriMul Kernels"),
    ("summary_zh.md", "summary_zh", "zh-Hant", "LightNobel 與 FPGA TriMul Kernel"),
]


def build(src, out, lang, title):
    body, _ = bp.render_chapter(1, os.path.join(HERE, src))
    css = bp.CSS + EXTRA_CSS + (EN_FONT if lang == "en" else "")
    doc = (f'<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">'
           f"<title>{title}</title><style>{css}</style></head><body>{body}</body></html>")
    html_path = os.path.join(HERE, out + ".html")
    pdf_path = os.path.join(HERE, out + ".pdf")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(doc)
    chrome = bp.find_chrome()
    if not chrome:
        sys.exit("找不到 Chrome/Chromium")
    r = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf_path}", "file://" + html_path], capture_output=True, text=True,
                       timeout=180)
    if r.returncode != 0 or not os.path.exists(pdf_path):
        sys.exit(r.stderr[-2000:])
    os.remove(html_path)
    print(f"已產生 {pdf_path}")


if __name__ == "__main__":
    for d in DOCS:
        if os.path.exists(os.path.join(HERE, d[0])):
            build(*d)
