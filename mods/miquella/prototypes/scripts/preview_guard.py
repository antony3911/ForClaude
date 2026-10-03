"""Preview the heavy bowgun's guard (D, the radiant halo) the way the weapons script moves it:
the kit's own mesh and weights, its joints set as the script sets them (rings slide by dz and
widen from r0 to r1 on their rim joints, rays drawn out from root to tip, drops flown to the
rim), at a few points of the guard's progress, from the front and over the shoulder.

Usage: python preview_guard.py <kit .blend> <wp_miquella_hbg_guard.lua> <out.png> [gif]
Only our model is drawn (can go in the repo). bpy 4.5.
"""
import math
import os
import re
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as c

KIT, RIG, OUT = (os.path.abspath(a) for a in sys.argv[1:4])
GIF = "gif" in sys.argv[4:]
F2B = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))        # file -> RE Mesh Editor's Blender space
GUN = Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0)))          # file -> world: muzzle +X, up +Z
STEPS = (0.0, 0.3, 0.6, 1.0)
VIEWS = (("前方", (2.3, -1.3, 0.15), (88, 0, 60)), ("玩家視角（背後）", (-2.3, -1.15, 0.5), (78, 0, -62)))


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def motion(t):
    """attachments.ring_motion: the slide leads, the widening follows."""
    return smooth(t / 0.6), smooth((t - 0.35) / 0.65)


def read_rig(path):
    text = open(path, encoding="utf-8").read()
    num = r"(-?[\d.]+)"
    vec = r"\{ " + num + ", " + num + ", " + num + r" \}"
    rings = [dict(halo=int(m[0]), dz=float(m[1]), r0=float(m[2]), r1=float(m[3]))
             for m in re.findall(r'halo = "MQ_Halo(\d+)", dz = ' + num + ", r0 = " + num + ", r1 = " + num, text)]
    rays = [(m[0], Vector(map(float, m[1:4])), Vector(map(float, m[4:7])))
            for m in re.findall(r'name = "(MQ_Ray\d+)", root = ' + vec + ", tip = " + vec, text)]
    drops = {m[0]: Vector(map(float, m[1:4])) for m in re.findall(r"(MQ_Phial\d) = " + vec, text)}
    rim = int(re.search(r"rim = (\d+)", text).group(1))
    return rings, rays, drops, rim


def offsets(t, rings, rays, drops, rim, pivots):
    slide, grow = motion(t)
    off = {}
    for r in rings:
        dz = Vector((0, 0, r["dz"] * slide))
        off[f"MQ_Halo{r['halo']}"] = dz
        for j in range(rim):
            a = 2 * math.pi * j / rim
            off[f"MQ_G{r['halo']}_{j}"] = dz + Vector((math.cos(a), math.sin(a), 0)) * ((r["r1"] - r["r0"]) * grow)
    for name, root, tip in rays:
        off[name] = root.lerp(tip, grow) - tip
    for name, at in drops.items():
        off[name] = (at - pivots[name]) * slide
    return off, grow


def main():
    bpy.ops.wm.open_mainfile(filepath=KIT)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    pivots = {b.name: Vector([b["reMeshWorldMatrix"][3][i] for i in range(3)])
              for b in arm.data.bones if b.get("reMeshWorldMatrix") is not None}
    rings, rays, drops, rim = read_rig(RIG)
    ivory = c.make_material("PvIvory", c.PALETTE["ivory"], roughness=0.35, emission=c.PALETTE["glow"], strength=0.05)
    glow = c.make_material("PvGlow", c.PALETTE["glow"], emission=c.PALETTE["glow"], strength=2.5)
    blade = c.make_material("PvBlade", c.PALETTE["blade_core"], emission=c.PALETTE["blade_core"], strength=3.0)
    parts = []
    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        o.modifiers.clear()
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
        name = o.name.split("__")[-1]
        o.data.materials.clear()
        o.data.materials.append(ivory if "Ivory" in name else blade if ("Blade" in name or "Ray" in name) else glow)
        groups = {g.index: g.name for g in o.vertex_groups}
        base = [F2B.inverted() @ v.co for v in o.data.vertices]          # file space
        weights = [[(groups[g.group], g.weight) for g in v.groups] for v in o.data.vertices]
        parts.append((o, base, weights, "Ray" in name))
    bpy.data.objects.remove(arm, do_unlink=True)
    c.setup_render(samples=20, res=(900, 640), world_hex="#1A1A1F", world_strength=0.4, glare=True)
    c.add_light("key", "AREA", (0.0, -2.5, 2.0), 300, size=2.0, target=(0.2, 0, -0.2))
    c.add_light("back", "AREA", (-2.0, 1.0, 1.5), 150, size=2.0, target=(0.2, 0, -0.2))
    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam_data.lens = 45

    def pose(t):
        off, grow = offsets(t, rings, rays, drops, rim, pivots)
        for o, base, weights, is_ray in parts:
            for v, p, ws in zip(o.data.vertices, base, weights):
                d = Vector()
                for b, w in ws:
                    if b in off:
                        d += off[b] * w
                q = GUN @ (p + d)
                v.co = q
            o.hide_render = is_ray and grow < 0.02
            o.data.update()

    def shoot(path, view):
        _, loc, rot = view
        cam.location = (0.35 + loc[0], loc[1], loc[2] - 0.2)
        cam.rotation_euler = tuple(math.radians(a) for a in rot)
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)

    from PIL import Image, ImageDraw, ImageFont
    font = None
    for f in (os.environ.get("MIQUELLA_FONT"), "C:/Windows/Fonts/msjh.ttc", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"):
        if f and os.path.exists(f):
            font = ImageFont.truetype(f, 30)
            break
    tiles = []
    for vi, view in enumerate(VIEWS):
        for t in STEPS:
            pose(t)
            path = OUT.replace(".png", f"_{vi}_{t:.2f}.png")
            shoot(path, view)
            tiles.append((f"{view[0]}・{int(t * 100)}%", path))
    W, H = Image.open(tiles[0][1]).size
    sheet = Image.new("RGB", (W * len(STEPS), H * len(VIEWS) + 56), (20, 20, 24))
    d = ImageDraw.Draw(sheet)
    d.text((16, 10), "重弩防禦盾 D 光輪（遊戲版：照換裝腳本的骨頭算法，防禦 0 → 100%）", fill=(240, 210, 140), font=font)
    for k, (label, path) in enumerate(tiles):
        x, y = (k % len(STEPS)) * W, 56 + (k // len(STEPS)) * H
        sheet.paste(Image.open(path), (x, y))
        d.text((x + 12, y + 8), label, fill=(225, 225, 225), font=font)
        os.remove(path)
    sheet.save(OUT)
    print("WROTE", OUT, flush=True)
    if GIF:
        frames = []
        bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 560, 400
        seq = [i / 11 for i in range(12)] + [1.0] * 4 + [1 - i / 11 for i in range(12)] + [0.0] * 3
        for i, t in enumerate(seq[:16]):
            pose(t)
            path = OUT.replace(".png", f"_g{i}.png")
            shoot(path, VIEWS[1])
            frames.append(Image.open(path).convert("RGB"))
            os.remove(path)
        frames = frames + frames[::-1]
        frames[0].save(OUT.replace(".png", ".gif"), save_all=True, append_images=frames[1:], duration=70, loop=0)
        print("WROTE GIF", flush=True)


try:
    main()
finally:
    sys.stdout.flush()
    os._exit(0)
