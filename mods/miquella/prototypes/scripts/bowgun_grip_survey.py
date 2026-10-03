"""Where the original bowguns have grips: each extracted original light / heavy bowgun's side
silhouette around the grip (z -0.80..0.45, y -0.72..0.15), our gun's outline in gold, the origin in red, and
each one's lowest point under the receiver (2026-10-03, the user: "the hunter never takes hold of the
grip"). The sheets hold the game's models: they stay in MiquellaTools\work\previews\grip, out of the repo.

Usage (bpy 4.5 with RE Mesh Editor): python bowgun_grip_survey.py
"""
import sys, os, glob, bpy, numpy as np
sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
from re_mesh_editor.modules.mesh.file_re_mesh import readREMesh
from re_mesh_editor.modules.mesh.re_mesh_parse import ParsedREMesh
from PIL import Image, ImageDraw, ImageFont, ImageFilter
PX = 560
Z0, Z1, Y0, Y1 = -0.80, 0.45, -0.72, 0.15
W, H = int((Z1 - Z0) * PX), int((Y1 - Y0) * PX)
def load(path, groups=(0,)):
    p = ParsedREMesh(); p.ParseREMesh(readREMesh(path, 0), {"importAllLOD": False, "importShadowMesh": False, "importOcclusionMesh": False, "importBlendShapes": False})
    tris = []
    for g in p.mainMeshLODList[0].visconGroupList:
        if g.visconGroupNum not in groups: continue
        for s in g.subMeshList:
            v = np.array(s.vertexPosList, float).reshape(-1, 3); f = np.array(s.faceList, int).reshape(-1, 3)
            tris.append(v[f])
    return np.concatenate(tris)
def raster(tris):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    xs = (tris[..., 2] - Z0) * PX; ys = (Y1 - tris[..., 1]) * PX
    for t in range(len(tris)):
        d.polygon([(xs[t, 0], ys[t, 0]), (xs[t, 1], ys[t, 1]), (xs[t, 2], ys[t, 2])], fill=255)
    return np.array(im) > 0
def edge(mask):
    im = Image.fromarray(mask.astype(np.uint8) * 255)
    return (np.array(im.filter(ImageFilter.MaxFilter(3))) > 0) & ~(np.array(im.filter(ImageFilter.MinFilter(3))) > 0)
E = "C:/Users/anton/MiquellaTools/extracted/natives/stm/art/model/item"
M = "C:/Users/anton/ForClaude/mods/miquella/mhws"
font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 24)
out = {}
for gun, pattern, ours in (("lbg", f"{E}/it13/[01]0/*/it13*_0.mesh.241111606", f"{M}/MiquellaLight_LightBowgun_kit/natives/STM/Art/Model/MiquellaLight/LightBowgun/wp_miquella_lbg.mesh.241111606"),
                           ("hbg", f"{E}/it12/[01]*/*/it12*_0.mesh.241111606", f"{M}/MiquellaLight_HeavyBowgun_kit/natives/STM/Art/Model/MiquellaLight/HeavyBowgun/wp_miquella_hbg.mesh.241111606")):
    our = raster(load(ours)); our_edge = edge(our)
    tiles = []
    for path in sorted(glob.glob(pattern)):
        name = os.path.basename(path).split(".")[0]
        tr = load(path)
        mk = raster(tr)
        rgb = np.zeros((H, W, 3), np.uint8); rgb[...] = (18, 18, 22)
        rgb[mk] = (150, 150, 158)
        rgb[our_edge] = (255, 196, 60)
        im = Image.fromarray(rgb); d = ImageDraw.Draw(im)
        ox, oy = (0 - Z0) * PX, (Y1 - 0) * PX
        d.ellipse((ox - 5, oy - 5, ox + 5, oy + 5), fill=(255, 40, 40))
        # lowest point under the receiver: per 2 cm slice of z in [-0.6, 0.4], the min y
        v = tr.reshape(-1, 3)
        prof = []
        for z in np.arange(-0.6, 0.4, 0.02):
            s = v[(v[:, 2] >= z) & (v[:, 2] < z + 0.02)]
            prof.append((z + 0.01, s[:, 1].min() if len(s) else np.nan))
        zz, yy = min(prof, key=lambda p: p[1] if p[1] == p[1] else 9)
        d.text((8, 6), f"{name}  最低點 z {zz:+.2f}, y {yy:+.2f}", fill=(230, 230, 230), font=font)
        out.setdefault(gun, []).append((name, zz, yy, prof))
        tiles.append(im)
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (W * cols, H * rows), (40, 40, 40))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * W, (i // cols) * H))
    sheet.save(f"C:/Users/anton/MiquellaTools/work/previews/grip/zoom_{gun}.png")
    print(gun, [(n, round(z, 2), round(y, 2)) for n, z, y, _ in out[gun]])
import json
json.dump({g: [(n, z, y, [(a, None if b != b else b) for a, b in pr]) for n, z, y, pr in v] for g, v in out.items()},
          open("C:/Users/anton/MiquellaTools/work/previews/grip/survey.json", "w"))
sys.stdout.flush(); os._exit(0)
