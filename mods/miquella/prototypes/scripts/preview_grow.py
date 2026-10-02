"""Render a game kit's charge growth (spirals, the bow's flowers) the way the weapons script plays it.

The kit's growth bands (MiquellaGrow1..n, build_weapon_kit.py) fade in by the share of the charge
the script computes from the game's charge timer: the level reached by the level thresholds plus
the share of the way to the next, over the top level (the bow: two flowers a level's time from
level 1, the rest one after another over `post` seconds at the top). Parts shown at full charge
(sparks, spin trails, the lance point's blade) come in at the top level; the lance's drill turns
on MQ_Drill, faster as it grows. Writes a strip of frames and an animated GIF in real time.

Usage: python preview_grow.py <kit .blend> <great_sword|lance|long_sword|bow> <out stem>
Requires bpy 4.5 (only reads the .blend).
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as c
from preview_morph import Part, preview_material

# How each weapon grows (the weapons script's KITS grow tables): levels base..top and the timer's
# value when each is reached; full: parts that come at the top level; view: turns file space so
# the weapon stands up facing the camera; spin: the drill's bone, pivot and speed per level.
WEAPONS = {
    "great_sword": {"times": [0.0, 0.8, 1.55, 2.3], "bands": 24, "full": ["MiquellaCharge3"], "z0": 0.0},
    "lance": {"times": [0.0, 0.8, 2.0, 3.6], "bands": 24, "full": ["MiquellaCharge3", "MiquellaChargeTip"], "z0": 0.3,
              "spin": ("MQ_Drill", (0.0, 0.0, 1.751), [0, 90, 200, 420])},
    "long_sword": {"times": [0.0, 0.8, 1.6, 2.9], "bands": 24, "full": [], "z0": 0.0},
    "bow": {"times": [0.0, 1.0, 2.0], "base": 1, "bands": 21, "flowers": 7, "post": 0.6, "full": [],
            # file +X (where the flowers face) toward the camera, the limbs (file Y) up
            "view": Matrix(((0, 0, -1, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))},
}
FPS, HOLD, RELEASE = 10, 0.6, 0.3


def growth(w, t):
    """(share 0..1 of the growth, level progress) at `t` seconds of the charge timer."""
    times, base = w["times"], w.get("base", 0)
    top = base + len(times) - 1
    lp = top
    for k in range(len(times) - 1):
        if t < times[k + 1]:
            lp = base + k + (t - times[k]) / (times[k + 1] - times[k])
            break
    else:
        if w.get("post"):
            lp = top + min(1.0, (t - times[-1]) / w["post"])
    if w.get("flowers"):
        n = w["flowers"]
        tau = (2 * (min(lp, top) - base) + max(0.0, lp - top) * (n - 2 * (top - base))) / n
    else:
        tau = (lp - base) / (top - base)
    return max(0.0, min(1.0, tau)), lp


def main():
    blend, kind, stem = os.path.abspath(sys.argv[1]), sys.argv[2], os.path.abspath(sys.argv[3])
    w = WEAPONS[kind]
    c.reset_scene()
    with bpy.data.libraries.load(blend) as (src, dst):
        dst.objects = [n for n in src.objects if "Group_0_Sub" in n]
    parts = []
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
        parts.append(Part(o))
    view = w.get("view")
    if view is not None:
        for p in parts:
            p.co = p.co @ np.array(view.to_3x3()).T
            p.mesh.vertices.foreach_set("co", p.co.ravel())
            p.mesh.update()
    mats = {}
    for p in parts:
        if p.game_mat not in mats:
            mats[p.game_mat] = preview_material(p.game_mat)
        p.mesh.materials.clear()
        p.mesh.materials.append(mats[p.game_mat][0])
    top_t = w["times"][-1] + w.get("post", 0.0)
    spin_angle = [0.0]

    def frame(t, path, dt=0.0, fade=1.0):
        tau, lp = growth(w, t)
        for name, (mat, factor) in mats.items():
            if name.startswith("MiquellaGrow"):
                k = int(name[len("MiquellaGrow"):])
                factor.default_value = max(0.0, min(1.0, tau * w["bands"] - (k - 1))) * fade
            elif name in w["full"]:
                factor.default_value = max(0.0, min(1.0, (t - w["times"][-1]) / 0.12)) * fade
        if w.get("spin"):
            bone, pivot, dps = w["spin"]
            lv = min(len(dps) - 1, lp * fade)
            lo = int(lv)
            speed = dps[lo] + (dps[min(len(dps) - 1, lo + 1)] - dps[lo]) * (lv - lo)
            spin_angle[0] += speed * dt
            a = math.radians(spin_angle[0])
            rot = np.array(((math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0), (0, 0, 1)))
            poses = {bone: (np.array(pivot), rot), bone + "@pivot": np.array(pivot)}
            for p in parts:
                if bone in p.weights:
                    p.deform(poses)
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        return path

    # Frame the growing parts and the blade around them, front view a little turned.
    grow = [p for p in parts if p.game_mat.startswith("MiquellaGrow")]
    pts = np.concatenate([p.co for p in grow])
    lo, hi = pts.min(0), pts.max(0)
    allp = np.concatenate([p.co for p in parts])
    lo[2], hi[2] = max(min(lo[2], allp[:, 2].min()), w.get("z0", -10)), max(hi[2], allp[:, 2].max())
    lo[0], hi[0] = min(lo[0], -0.2), max(hi[0], 0.2)
    res = (480, 900)
    c.setup_render(samples=12, res=res, world_hex="#16161B", world_strength=0.35, glare=True)
    centre = Vector(((lo[0] + hi[0]) / 2, 0, (lo[2] + hi[2]) / 2))
    c.add_light("key", "AREA", centre + Vector((1.2, -2.0, 1.0)), 250, size=2.0, target=centre)
    c.add_light("fill", "AREA", centre + Vector((-1.5, -1.2, 0.2)), 80, size=2.0, target=centre)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(hi[2] - lo[2], (hi[0] - lo[0]) * res[1] / res[0]) * 1.06
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    az = math.radians(18)
    cam.location = centre + Vector((6 * math.sin(az), -6 * math.cos(az), 0.4))
    c.look_at(cam, centre)
    bpy.context.scene.camera = cam

    os.makedirs(os.path.dirname(stem), exist_ok=True)
    marks = [top_t * i / 5 for i in range(6)]
    strip = [frame(t, f"{stem}_{i}.png") for i, t in enumerate(marks)]
    c.contact_sheet(strip, f"{stem}_strip.png", cols=len(strip))
    from PIL import Image, ImageDraw
    spin_angle[0] = 0.0
    seq, n = [], int(round((top_t + HOLD) * FPS))
    for i in range(n + 1):
        t = i / FPS
        im = Image.open(frame(t, f"{stem}_gif.png", 1 / FPS)).convert("RGB")
        ImageDraw.Draw(im).text((12, 12), f"{min(t, top_t):.1f} s", fill=(235, 220, 180))
        seq.append(im)
    for i in range(1, int(RELEASE * FPS) + 1):
        seq.append(Image.open(frame(top_t, f"{stem}_gif.png", 1 / FPS, 1 - i / (RELEASE * FPS))).convert("RGB"))
    seq += [seq[-1]] * 4
    seq = [im.resize((im.width * 2 // 3, im.height * 2 // 3)) for im in seq]
    seq[0].save(f"{stem}.gif", save_all=True, append_images=seq[1:], duration=int(1000 / FPS), loop=0)
    os.remove(f"{stem}_gif.png")
    print("WROTE", f"{stem}_strip.png", f"{stem}.gif", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout.flush()
        os._exit(0)
