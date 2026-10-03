"""Decode Wilds .tex files (top mip) and print each channel's mean and range; with SAVE=<dir> also
write <name>_rgb.png and <name>_a.png. BC7 / BC1 (sRGB or not) through Pillow.
Usage: bpy45 python decode_wilds_tex.py <file.tex.241106027>...
Used 2026-10-03 to find the dual blades' broken NRRO (converted in the cloud: RGB times alpha, then
sRGB) and to read the game's skin textures. NRRO = roughness, normal Y, AO, normal X."""
import os, sys, struct, io
sys.path.insert(0, os.path.join(os.environ["APPDATA"], "Blender Foundation/Blender/4.5/scripts/addons"))
from re_mesh_editor.modules.tex.file_re_tex import Tex
from PIL import Image, ImageStat

FLAGS = 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000


def to_image(path):
    t = Tex()
    with open(path, "rb") as fh:
        t.read(fh)
    h = t.header
    fmt = h.format
    data = t.imageMipDataList[0][0].textureData
    w, hh = h.width, h.height
    zeros44 = bytes(44)
    if fmt in (71, 72):     # BC1: legacy DXT1 header
        pf = struct.pack("<II4sIIIII", 32, 0x4, b"DXT1", 0, 0, 0, 0, 0)
        hdr = struct.pack("<4sIIIIIII", b"DDS ", 124, FLAGS, hh, w, len(data), 0, 1) + zeros44 + pf \
            + struct.pack("<IIIII", 0x1000, 0, 0, 0, 0)
        return Image.open(io.BytesIO(hdr + data)), fmt, (w, hh)
    pf = struct.pack("<II4sIIIII", 32, 0x4, b"DX10", 0, 0, 0, 0, 0)
    hdr = struct.pack("<4sIIIIIII", b"DDS ", 124, FLAGS, hh, w, len(data), 0, 1) + zeros44 + pf \
        + struct.pack("<IIIII", 0x1000, 0, 0, 0, 0)
    dx10 = struct.pack("<IIIII", fmt, 3, 0, 1, 0)
    return Image.open(io.BytesIO(hdr + dx10 + data)), fmt, (w, hh)


for p in sys.argv[1:]:
    try:
        im, fmt, size = to_image(p)
        im = im.convert("RGBA")
        st = ImageStat.Stat(im)
        print(os.path.basename(p), "fmt", fmt, size, "mean RGBA", [round(x) for x in st.mean], "min/max", im.getextrema())
        if os.environ.get("SAVE"):
            base = os.path.join(os.environ["SAVE"], os.path.basename(p).split(".")[0])
            im.convert("RGB").save(base + "_rgb.png")
            im.getchannel("A").save(base + "_a.png")
    except Exception as e:
        print(os.path.basename(p), "ERR", e)
