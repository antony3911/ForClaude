"""Where the bowguns' stocks and grips are: the side silhouettes of every extracted original light /
heavy bowgun stacked (grey: how many cover a pixel; blue: 80 % or more of them), our gun's outline in
gold on top, the weapon origin in red (2026-10-03, the user: "the hunter never takes hold of the
stocks"). The sheet holds the game's models: keep it in MiquellaTools\work\previews, out of the repo.

Usage (bpy 4.5 with RE Mesh Editor): python bowgun_stock_overlay.py <out.png>
"""
import sys, os, glob, bpy, numpy as np
sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
from re_mesh_editor.modules.mesh.file_re_mesh import readREMesh
from re_mesh_editor.modules.mesh.re_mesh_parse import ParsedREMesh
from PIL import Image, ImageDraw, ImageFont, ImageFilter
PX = 520
Z0, Z1, Y0, Y1 = -1.15, 1.55, -0.75, 0.40
W, H = int((Z1 - Z0) * PX), int((Y1 - Y0) * PX)
def mask(path, groups=(0,)):
    p = ParsedREMesh(); p.ParseREMesh(readREMesh(path, 0), {"importAllLOD": False, "importShadowMesh": False, "importOcclusionMesh": False, "importBlendShapes": False})
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for g in p.mainMeshLODList[0].visconGroupList:
        if g.visconGroupNum not in groups: continue
        for s in g.subMeshList:
            v = np.array(s.vertexPosList, float).reshape(-1, 3)
            f = np.array(s.faceList, int).reshape(-1, 3)
            xs = (v[:, 2] - Z0) * PX; ys = (Y1 - v[:, 1]) * PX
            for a, b, c in f:
                d.polygon([(xs[a], ys[a]), (xs[b], ys[b]), (xs[c], ys[c])], fill=255)
    return np.array(im) > 0
def panel(title, originals, ours):
    stack = np.zeros((H, W), float)
    for o in originals: stack += mask(o)
    frac = stack / len(originals)
    rgb = np.zeros((H, W, 3), np.uint8)
    rgb[...] = (18, 18, 22)
    grey = (frac * 150 + 40 * (frac > 0)).astype(np.uint8)
    for i in range(3): rgb[..., i] = np.maximum(rgb[..., i], grey)
    common = frac >= 0.8
    rgb[common] = (60, 170, 200)
    m = mask(ours)
    im = Image.fromarray(m.astype(np.uint8) * 255)
    edge = (np.array(im.filter(ImageFilter.MaxFilter(5))) > 0) & ~(np.array(im.filter(ImageFilter.MinFilter(3))) > 0)
    rgb[edge] = (255, 196, 60)
    out = Image.fromarray(rgb); d = ImageDraw.Draw(out)
    font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 30); small = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 22)
    ox, oy = (0 - Z0) * PX, (Y1 - 0) * PX
    d.ellipse((ox - 7, oy - 7, ox + 7, oy + 7), fill=(255, 40, 40))
    for z in np.arange(-1.0, 1.51, 0.25):
        x = (z - Z0) * PX; d.line((x, H - 18, x, H - 8), fill=(120, 120, 120)); d.text((x + 3, H - 42), f"{z:+.2f}", fill=(130, 130, 130), font=small)
    d.text((14, 10), title, fill=(240, 210, 140), font=font)
    d.text((14, 50), f"灰：{len(originals)} 把原版疊起來（越亮越多把有）　藍：八成以上的原版都有　金線：我們的　紅點：武器原點　（槍口朝右）", fill=(200, 200, 200), font=small)
    return out
E = "C:/Users/anton/MiquellaTools/extracted/natives/stm/art/model/item"
M = "C:/Users/anton/ForClaude/mods/miquella/mhws"
lbg = sorted(glob.glob(f"{E}/it13/[01]0/*/it13*_0.mesh.241111606"))
hbg = sorted(glob.glob(f"{E}/it12/[01]*/*/it12*_0.mesh.241111606"))
a = panel("輕弩：原版槍托、握把的位置 vs 我們的", lbg, f"{M}/MiquellaLight_LightBowgun_kit/natives/STM/Art/Model/MiquellaLight/LightBowgun/wp_miquella_lbg.mesh.241111606")
b = panel("重弩：原版槍托、握把的位置 vs 我們的", hbg, f"{M}/MiquellaLight_HeavyBowgun_kit/natives/STM/Art/Model/MiquellaLight/HeavyBowgun/wp_miquella_hbg.mesh.241111606")
sheet = Image.new("RGB", (W, H * 2 + 10), (40, 40, 40)); sheet.paste(a, (0, 0)); sheet.paste(b, (0, H + 10))
sheet.save(sys.argv[1]); print("WROTE", sys.argv[1], len(lbg), len(hbg))
sys.stdout.flush(); os._exit(0)
