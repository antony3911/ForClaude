"""Render a game kit's morph (switch axe, charge blade) the way the weapons script plays it.

The kit's mesh is deformed with the same bone math as the game (linear blend skinning: each
vertex follows its bones' pose, pos + rot @ (v - pivot)), the joint poses and the fades come
from the kit's <name>_morph.json (build_weapon_kit.py), with the script's easing. Writes a
strip of frames (progress 0 -> 1) and an animated GIF (there and back).

Usage: python preview_morph.py <kit .blend> <morph .json> <out stem> [second kit .blend x y z]
The optional second kit (the charge blade's shield) is drawn moved by (x, y, z) in file space
and fades out by the morph's `second` window. Requires bpy 4.5 (only reads the .blend files).
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as c

# Blender space of RE Mesh Editor (file +Z = Blender -Y) -> file space.
TO_FILE = Matrix.Rotation(math.radians(-90), 4, "X")
STRIP = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
GIF_STEPS = 12


def ease(p, win):
    """The weapons script's window: progress p across win, smoothstepped."""
    x = max(0.0, min(1.0, (p - win[0]) / (win[1] - win[0])))
    return x * x * (3 - 2 * x)


def pose(j, p):
    e = ease(p, j["win"])
    rest = {"pos": j["pivot"], "rot": [0, 0, 0, 1]}
    a, b = j.get("base") or rest, j.get("alt") or rest
    pos = Vector(a["pos"]).lerp(Vector(b["pos"]), e)
    qa = Quaternion((a["rot"][3], *a["rot"][:3]))
    qb = Quaternion((b["rot"][3], *b["rot"][:3]))
    if qa.dot(qb) < 0:                       # shortest way, as in the script
        qb.negate()
    return np.array(pos), np.array(qa.slerp(qb, e).to_matrix())


class Part:
    """One sub-mesh: file-space rest positions, per-bone weights, a preview material."""

    def __init__(self, o, shift=Vector()):
        o.modifiers.clear()
        o.parent = None
        o.data.transform(Matrix.Translation(shift) @ TO_FILE @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        self.obj, self.mesh = o, o.data
        n = len(o.data.vertices)
        self.co = np.empty(n * 3)
        o.data.vertices.foreach_get("co", self.co)
        self.co = self.co.reshape(n, 3)
        names = {g.index: g.name for g in o.vertex_groups}
        self.weights = {}
        for v in o.data.vertices:
            for g in v.groups:
                if g.weight > 0:
                    self.weights.setdefault(names[g.group], np.zeros(n))[v.index] = g.weight
        self.game_mat = o.name.split("__")[-1]

    def deform(self, poses):
        total = np.zeros(len(self.co))
        out = np.zeros_like(self.co)
        for bone, w in self.weights.items():
            total += w
            if bone in poses:
                pos, rot = poses[bone]
                moved = pos + (self.co - poses[bone + "@pivot"]) @ rot.T
            else:
                moved = self.co
            out += w[:, None] * moved
        rest = np.clip(1.0 - total, 0.0, None)
        out = (out + rest[:, None] * self.co) / np.maximum(total + rest, 1e-9)[:, None]
        self.mesh.vertices.foreach_set("co", out.ravel())
        self.mesh.update()


def preview_material(game_mat):
    """Gold light, or ivory, mixed with transparency (its factor is the fade)."""
    m = bpy.data.materials.new(f"Pv_{game_mat}")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    if "Ivory" in game_mat:
        body = nt.nodes.new("ShaderNodeBsdfPrincipled")
        body.inputs["Base Color"].default_value = c.hex_to_linear(c.PALETTE["ivory"])
        body.inputs["Roughness"].default_value = 0.35
    else:
        body = nt.nodes.new("ShaderNodeEmission")
        hexc = c.PALETTE["blade_core"] if "Blade" in game_mat else c.PALETTE["glow"]
        body.inputs["Color"].default_value = c.hex_to_linear(hexc)
        body.inputs["Strength"].default_value = 2.2 if "Blade" in game_mat else 2.5
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(body.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m, mix.inputs[0]


def load_parts(blend, shift=Vector()):
    with bpy.data.libraries.load(blend) as (src, dst):
        dst.objects = [n for n in src.objects if "Group_0_Sub" in n]
    parts = []
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
        parts.append(Part(o, shift))
    return parts


def main():
    import json
    blend, morph_path, stem = (os.path.abspath(a) for a in sys.argv[1:4])
    morph = json.load(open(morph_path))
    c.reset_scene()
    parts = load_parts(blend)
    second = []
    if len(sys.argv) > 4:
        second = load_parts(os.path.abspath(sys.argv[4]), Vector([float(x) for x in sys.argv[5:8]]))
    fades = {m: fd for fd in morph["fades"] for m in fd["mats"]}
    mats = {}
    # (the second kit's materials are its own: it fades as a whole)
    for part in parts + second:
        key = ("2:" if part in second else "") + part.game_mat
        if key not in mats:
            mats[key] = preview_material(part.game_mat)
        part.mesh.materials.clear()
        part.mesh.materials.append(mats[key][0])

    def frame(p, path):
        poses = {}
        for j in morph["joints"]:
            poses[j["name"]] = pose(j, p)
            poses[j["name"] + "@pivot"] = np.array(j["pivot"])
        for part in parts:
            part.deform(poses)
        for name, (mat, factor) in mats.items():
            fd = fades.get(name)
            a = 1.0
            if fd:
                a = ease(p, fd["win"])
                a = a if fd["show"] == "alt" else 1.0 - a
            factor.default_value = a
        if second and morph.get("second"):
            a = 1.0 - ease(p, morph["second"])
            for part in second:
                mats["2:" + part.game_mat][1].default_value = a
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        return path

    # Frame: the union of the rest pose and the other mode, front view (file X right, Z up).
    pts = np.concatenate([p.co for p in parts + second])
    for p in (1.0,):
        poses = {j["name"]: pose(j, p) for j in morph["joints"]}
        poses.update({j["name"] + "@pivot": np.array(j["pivot"]) for j in morph["joints"]})
        for part in parts:
            part.deform(poses)
        pts = np.concatenate([pts] + [np.array([v.co for v in part.mesh.vertices]) for part in parts])
    lo, hi = pts.min(0), pts.max(0)
    lo[2] = max(lo[2], 0.3)                  # the head, not the whole haft
    res = (520, 900)
    c.setup_render(samples=16, res=res, world_hex="#16161B", world_strength=0.35, glare=True)
    centre = Vector(((lo[0] + hi[0]) / 2, 0, (lo[2] + hi[2]) / 2))
    c.add_light("key", "AREA", centre + Vector((1.2, -2.0, 1.0)), 250, size=2.0, target=centre)
    c.add_light("fill", "AREA", centre + Vector((-1.5, -1.2, 0.2)), 80, size=2.0, target=centre)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(hi[2] - lo[2], (hi[0] - lo[0]) * res[1] / res[0]) * 1.08
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    az = math.radians(22)                    # a little turned, so swings out of the plane show
    cam.location = centre + Vector((6 * math.sin(az), -6 * math.cos(az), 0.4))
    c.look_at(cam, centre)
    bpy.context.scene.camera = cam

    out_dir = os.path.dirname(stem)
    os.makedirs(out_dir, exist_ok=True)
    strip = [frame(p, f"{stem}_{int(p * 100):03d}.png") for p in STRIP]
    c.contact_sheet(strip, f"{stem}_strip.png", cols=len(strip))
    from PIL import Image
    gif = []
    for i in range(GIF_STEPS + 1):
        gif.append(Image.open(frame(i / GIF_STEPS, f"{stem}_gif_{i:02d}.png")).convert("RGB"))
    seq = [gif[0]] * 4 + gif + [gif[-1]] * 6 + gif[::-1] + [gif[0]] * 2
    seq = [im.resize((im.width * 2 // 3, im.height * 2 // 3)) for im in seq]
    seq[0].save(f"{stem}.gif", save_all=True, append_images=seq[1:], duration=60, loop=0)
    for i in range(GIF_STEPS + 1):
        os.remove(f"{stem}_gif_{i:02d}.png")
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
