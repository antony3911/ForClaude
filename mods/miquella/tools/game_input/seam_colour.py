# Mean colour of small patches either side of the neck seam in a zoom screenshot (computer-use zoom
# with save_to_disk). Args: image, then x,y,dx,dy per pair: face patch at (x,y), body at (x+dx,y+dy).
# Prints the linear face/body ratio per channel: multiply ColorParam by it (2026-10-04 skin match).
import sys
from PIL import Image
import numpy as np
img = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(float)
print("size", img.shape)
def lin(c): return ((c / 255.0 + 0.055) / 1.055) ** 2.4
pairs = [tuple(map(int, a.split(","))) for a in sys.argv[2:]]   # x,y,dx,dy: face patch at (x,y), body at (x+dx, y+dy)
r = 7
fs, bs = [], []
for x, y, dx, dy in pairs:
    f = img[y - r:y + r, x - r:x + r].reshape(-1, 3).mean(0)
    b = img[y + dy - r:y + dy + r, x + dx - r:x + dx + r].reshape(-1, 3).mean(0)
    fs.append(f); bs.append(b)
    print(f"face {f.round(1)} body {b.round(1)} linear ratio face/body {(lin(f) / lin(b)).round(3)}")
F, B = np.mean(fs, 0), np.mean(bs, 0)
print("MEAN face", F.round(1), "body", B.round(1), "ratio", (lin(F) / lin(B)).round(3))
