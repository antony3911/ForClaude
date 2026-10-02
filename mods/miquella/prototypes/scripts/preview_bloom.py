"""Render the lily gunlance's charge (lily_rig.py, build_weapon_kit.py gunlance) the way the
weapons script plays it: the kit's mesh deformed by its bones (preview_morph's skinning), the
bones and fades from <kit>/wp_miquella_gl_bloom.json. A Wyvern's Fire: the charge builds over
CHARGE seconds (every drive follows it), the blast holds, then the parts of light fade where
they stand while the ivory lily eases back. Writes an animated GIF and a strip of the charge
at 0-100 %.

Usage: python preview_bloom.py <kit .blend> <bloom .json> <out stem> [view: full|head]
Requires bpy 4.5 (only reads the .blend).
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as c
import preview_morph as pm

CHARGE, HOLD, FPS = 2.4, 0.35, 15
GLOW_FADE, OPEN_BACK = 0.3, 0.35          # as the weapons script (LILY_GL)
STRIP = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)


def ramp(p, win):
    return max(0.0, min(1.0, (p - win[0]) / (win[1] - win[0])))


def drives_at(t):
    """{drive: progress}, the light parts' fade, at time t of a Wyvern's Fire."""
    if t <= CHARGE:
        p = t / CHARGE
        return {"open": p, "glow": p, "wyvern": p}, 1.0
    after = t - CHARGE - HOLD
    if after <= 0:
        return {"open": 1.0, "glow": 1.0, "wyvern": 1.0}, 1.0
    return ({"open": max(0.0, 1.0 - after / OPEN_BACK), "glow": 1.0, "wyvern": 1.0},
            max(0.0, 1.0 - after / GLOW_FADE))


def main():
    blend, bloom_path, stem = (os.path.abspath(a) for a in sys.argv[1:4])
    view = sys.argv[4] if len(sys.argv) > 4 else "full"
    bloom = json.load(open(bloom_path))
    c.reset_scene()
    parts = pm.load_parts(blend)
    mats = {}
    for part in parts:
        if part.game_mat not in mats:
            mats[part.game_mat] = pm.preview_material(part.game_mat)
        part.mesh.materials.clear()
        part.mesh.materials.append(mats[part.game_mat][0])
    fades = {fd["mats"][0]: fd for fd in bloom["fades"]}
    hidden_gauges = ()                       # all five shells loaded

    def frame(drv, light, path):
        poses = {}
        for j in bloom["joints"]:
            e = ramp(drv[j["drive"]], j["win"])
            a = Vector(j["base"] or j["pivot"])
            b = Vector(j["alt"] or j["pivot"])
            poses[j["name"]] = (np.array(a.lerp(b, e)), np.identity(3))
            poses[j["name"] + "@pivot"] = np.array(j["pivot"])
        for part in parts:
            part.deform(poses)
        for name, (mat, factor) in mats.items():
            fd = fades.get(name)
            a = 1.0
            if fd:
                x = ramp(drv[fd["drive"]], fd["win"])
                a = x * x * (3 - 2 * x) * (light if fd["drive"] in ("glow", "wyvern") else 1.0)
            if name in hidden_gauges:
                a = 0.15
            factor.default_value = a
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        return path

    pts = np.concatenate([p.co for p in parts])
    lo, hi = pts.min(0), pts.max(0)
    if view == "head":
        lo[2] = max(lo[2], 1.2)
    res = (520, 900)
    c.setup_render(samples=16, res=res, world_hex="#0E0E12", world_strength=0.25, glare=True)
    centre = Vector(((lo[0] + hi[0]) / 2, 0, (lo[2] + hi[2]) / 2))
    c.add_light("key", "AREA", centre + Vector((1.2, -2.0, 1.0)), 250, size=2.0, target=centre)
    c.add_light("fill", "AREA", centre + Vector((-1.5, -1.2, 0.2)), 80, size=2.0, target=centre)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(hi[2] - lo[2], (hi[0] - lo[0]) * res[1] / res[0]) * 1.06
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    az = math.radians(30)
    cam.location = centre + Vector((6 * math.sin(az), -6 * math.cos(az), 0.8))
    c.look_at(cam, centre)
    bpy.context.scene.camera = cam

    os.makedirs(os.path.dirname(stem), exist_ok=True)
    strip = [frame({"open": p, "glow": p, "wyvern": p}, 1.0, f"{stem}_{int(p * 100):03d}.png") for p in STRIP]
    c.contact_sheet(strip, f"{stem}_strip.png", cols=len(strip))
    from PIL import Image
    n = int((CHARGE + HOLD + max(GLOW_FADE, OPEN_BACK) + 0.25) * FPS)
    gif = []
    for i in range(n + 1):
        drv, light = drives_at(i / FPS)
        path = frame(drv, light, f"{stem}_gif_{i:03d}.png")
        gif.append(Image.open(path).convert("RGB").resize((res[0] * 2 // 3, res[1] * 2 // 3)))
        os.remove(path)
    seq = [gif[0]] * 4 + gif + [gif[-1]] * 6
    seq[0].save(f"{stem}.gif", save_all=True, append_images=seq[1:], duration=int(1000 / FPS), loop=0)
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
