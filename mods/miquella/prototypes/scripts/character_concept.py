"""Character concept prototype on a stand-in mannequin.

Validates the approach from DESIGN.md section 4 before the Wilds body is available:
- slim, androgynous, normal-height body (narrow shoulders and hips, flat chest)
- one long robe: fitted upper body grown from the body surface, loose skirt to the ankles,
  gold trim at the collar, cuffs and hem, gold armband near the elbow
- pale gold long hair: two side braids that wrap back and merge into one thick braid,
  several small braids, and long wavy loose hair covering the back
- the glowing circlet

The mannequin is only a stand-in; in game the body comes from the Wilds hunter model.

Character faces -Y. Usage: python character_concept.py <out_dir>
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as c
import circlet as cl

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"

HEAD_Z = 1.58            # head center height (character is about 1.70 m tall)
H = cl.HEAD              # head half-sizes shared with the circlet


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def catmull(points, n):
    """Smooth path through control points (Catmull-Rom), n samples."""
    pts = [Vector(p) for p in points]
    pts = [pts[0]] + pts + [pts[-1]]
    out = []
    segs = len(pts) - 3
    for i in range(n):
        t = i / (n - 1) * segs
        k = min(int(t), segs - 1)
        u = t - k
        p0, p1, p2, p3 = pts[k], pts[k + 1], pts[k + 2], pts[k + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u))
    return out


def head_surface(theta_deg, z_local, offset):
    """Point on the head ellipsoid (theta 0 = front, +90 = character's left... +X side)."""
    p = cl.head_point(theta_deg, z_local, offset)
    return Vector((p.x, p.y, p.z + HEAD_Z))


# ---------------------------------------------------------------- body

def build_body(skin_mat):
    """Mannequin from a skin-modifier skeleton: slim, narrow hips, flat chest."""
    joints = {
        "pelvis": ((0, 0, 0.95), (0.135, 0.09)),
        "waist": ((0, 0, 1.07), (0.11, 0.08)),
        "chest": ((0, 0, 1.25), (0.135, 0.09)),
        "neckbase": ((0, 0.005, 1.40), (0.11, 0.075)),
        "neck": ((0, 0.01, 1.47), (0.045, 0.05)),
        "shoulder_l": ((0.165, 0.01, 1.385), (0.048, 0.048)),
        "elbow_l": ((0.2, 0.02, 1.12), (0.037, 0.037)),
        "wrist_l": ((0.215, 0.0, 0.89), (0.027, 0.024)),
        "hand_l": ((0.22, -0.01, 0.8), (0.033, 0.017)),
        "hip_l": ((0.085, 0, 0.92), (0.075, 0.075)),
        "knee_l": ((0.09, 0.0, 0.5), (0.048, 0.05)),
        "ankle_l": ((0.09, 0.015, 0.08), (0.032, 0.034)),
        "toe_l": ((0.09, -0.1, 0.025), (0.035, 0.022)),
    }
    for name in list(joints):
        if name.endswith("_l"):
            (x, y, z), r = joints[name]
            joints[name[:-2] + "_r"] = ((-x, y, z), r)
    chains = [["pelvis", "waist", "chest", "neckbase", "neck"]]
    for s in ("_l", "_r"):
        chains.append(["neckbase", "shoulder" + s, "elbow" + s, "wrist" + s, "hand" + s])
        chains.append(["pelvis", "hip" + s, "knee" + s, "ankle" + s, "toe" + s])
    names = list(joints)
    mesh = bpy.data.meshes.new("body")
    edges = []
    for ch in chains:
        for a, b in zip(ch, ch[1:]):
            edges.append((names.index(a), names.index(b)))
    mesh.from_pydata([joints[n][0] for n in names], edges, [])
    obj = c.link(bpy.data.objects.new("Mannequin", mesh))
    skin = obj.modifiers.new("skin", "SKIN")
    for i, n in enumerate(names):
        obj.data.skin_vertices[0].data[i].radius = joints[n][1]
    obj.data.skin_vertices[0].data[names.index("pelvis")].use_root = True
    sub = obj.modifiers.new("smooth", "SUBSURF")
    sub.levels = sub.render_levels = 2
    obj.data.materials.append(skin_mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    # Head: the same ellipsoid the circlet was designed around.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32, location=(0, 0, HEAD_Z))
    head = bpy.context.active_object
    head.name = "Head"
    head.scale = H
    head.data.materials.append(skin_mat)
    bpy.ops.object.shade_smooth()
    return obj, head


# ---------------------------------------------------------------- robe

def build_robe(body, robe_mat, gold_mat):
    objs = []
    # Upper robe: the body surface itself, pushed outward (guarantees a close fit).
    deps = bpy.context.evaluated_depsgraph_get()
    src = body.evaluated_get(deps).to_mesh()
    bm = bmesh.new()
    bm.from_mesh(src)
    body.evaluated_get(deps).to_mesh_clear()
    drop = [v for v in bm.verts
            if (v.co.z < 1.02 and abs(v.co.x) < 0.155)        # skirt takes over below the waist
            or v.co.z > 1.435                                 # round neckline
            or (abs(v.co.x) > 0.19 and v.co.z < 0.9)]         # sleeves end at the wrist
    bmesh.ops.delete(bm, geom=drop, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * 0.009
    mesh = bpy.data.meshes.new("robe_upper")
    bm.to_mesh(mesh)
    bm.free()
    upper = c.link(bpy.data.objects.new("Robe_Upper", mesh))
    upper.data.materials.append(robe_mat)
    solid = upper.modifiers.new("thick", "SOLIDIFY")
    solid.thickness = 0.003
    for p in upper.data.polygons:
        p.use_smooth = True
    objs.append(upper)

    # Skirt: from the waist, flaring to the ankles, with folds deepening toward the hem.
    bm = bmesh.new()
    rings = []
    n_z, n_a = 40, 96
    for i in range(n_z + 1):
        t = i / n_z
        z = 1.06 - (1.06 - 0.06) * t
        rx = 0.125 + (0.34 - 0.125) * t ** 1.3
        ry = 0.095 + (0.29 - 0.095) * t ** 1.3
        ring = []
        for j in range(n_a):
            a = 2 * math.pi * j / n_a
            fold = 1 + (0.02 + 0.07 * t) * math.sin(11 * a + 0.6) + 0.03 * t * math.sin(5 * a + 2.1)
            ring.append(bm.verts.new((rx * fold * math.sin(a), -ry * fold * math.cos(a), z)))
        rings.append(ring)
    for i in range(n_z):
        for j in range(n_a):
            k = (j + 1) % n_a
            bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
    hem = [Vector(v.co) for v in rings[-1]]
    mesh = bpy.data.meshes.new("robe_skirt")
    bm.to_mesh(mesh)
    bm.free()
    skirt = c.link(bpy.data.objects.new("Robe_Skirt", mesh))
    skirt.data.materials.append(robe_mat)
    solid = skirt.modifiers.new("thick", "SOLIDIFY")
    solid.thickness = 0.004
    sub = skirt.modifiers.new("smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    for p in skirt.data.polygons:
        p.use_smooth = True
    objs.append(skirt)

    # Gold trims fitted to the robe's actual edges: collar, cuffs, hem, armband.
    verts = [upper.matrix_world @ v.co for v in upper.data.vertices]
    top_z = max(v.z for v in verts if abs(v.x) < 0.12)
    neck = [v for v in verts if v.z > top_z - 0.012 and abs(v.x) < 0.13]
    nx = max(abs(v.x) for v in neck) + 0.004
    ny0, ny1 = min(v.y for v in neck) - 0.004, max(v.y for v in neck) + 0.004
    nz = sum(v.z for v in neck) / len(neck)
    collar = [Vector((nx * math.sin(a), (ny0 + ny1) / 2 - (ny1 - ny0) / 2 * math.cos(a), nz - 0.004))
              for a in [2 * math.pi * i / 64 for i in range(65)]]
    objs.append(flat_band("Trim_Collar", collar, gold_mat, 0.022, 0.004))
    for s in (1, -1):
        arm = [v for v in verts if s * v.x > 0.15 and v.z < 1.0]
        lowest = min(v.z for v in arm)
        wrist = [v for v in arm if v.z < lowest + 0.02]
        wx = sum(v.x for v in wrist) / len(wrist)
        wy = sum(v.y for v in wrist) / len(wrist)
        wr = max(math.hypot(v.x - wx, v.y - wy) for v in wrist) + 0.003
        wz = min(v.z for v in wrist) + 0.006
        cuff = [Vector((wx + wr * math.sin(a), wy - wr * math.cos(a), wz))
                for a in [2 * math.pi * i / 48 for i in range(49)]]
        objs.append(flat_band(f"Trim_Cuff_{s}", cuff, gold_mat, 0.008, 0.003))
        arm = [Vector((s * 0.197 + 0.05 * math.sin(a), 0.02 - 0.05 * math.cos(a), 1.175))
               for a in [2 * math.pi * i / 48 for i in range(49)]]
        objs.append(flat_band(f"Armband_{s}", arm, gold_mat, 0.012, 0.004))
    hem.append(hem[0])
    objs.append(flat_band("Trim_Hem", hem, gold_mat, 0.018, 0.004, offset_z=0.012))
    return objs


def rings_to_coords(ring):
    return [v for v in ring]


def flat_band(name, pts, mat, height, thickness, offset_z=0.0):
    """A ribbon band along a closed loop (used for trims)."""
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_mode = "PROFILE"
    data.bevel_depth = 0.5
    data.use_fill_caps = True
    spline = data.splines.new("POLY")
    spline.points.add(len(pts) - 1)
    for p, co in zip(spline.points, pts):
        p.co = (co.x, co.y, co.z + offset_z, 1.0)
    data.bevel_mode = "OBJECT"
    # Rectangular profile.
    prof = bpy.data.curves.new(name + "_profile", "CURVE")
    prof.dimensions = "2D"
    ps = prof.splines.new("POLY")
    ps.points.add(3)
    for p, (x, y) in zip(ps.points, ((-thickness / 2, -height / 2), (thickness / 2, -height / 2),
                                    (thickness / 2, height / 2), (-thickness / 2, height / 2))):
        p.co = (x, y, 0, 1)
    ps.use_cyclic_u = True
    prof_obj = c.link(bpy.data.objects.new(name + "_profile", prof))
    prof_obj.hide_render = True
    data.bevel_object = prof_obj
    obj = c.link(bpy.data.objects.new(name, data))
    obj.data.materials.append(mat)
    return obj


# ---------------------------------------------------------------- hair

def braid(name, path, width, mat, taper=0.35, strand_scale=0.42, twists=None):
    """Three-strand braid along a path."""
    n = len(path)
    length = sum((path[i + 1] - path[i]).length for i in range(n - 1))
    twists = twists or length / (width * 1.6)
    objs = []
    up = Vector((0, 0, 1))
    for k in range(3):
        pts, radii = [], []
        ph = 2 * math.pi * k / 3
        for i in range(n):
            t = i / (n - 1)
            tan = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
            side = tan.cross(up)
            if side.length < 1e-4:
                side = Vector((1, 0, 0))
            side.normalize()
            nrm = side.cross(tan).normalized()
            w = width * (1 - taper * t)
            a = 2 * math.pi * twists * t + ph
            off = side * (w * 0.5 * math.sin(a)) + nrm * (w * 0.22 * math.sin(2 * a))
            pts.append(path[i] + off)
            radii.append(1 - taper * t)
        objs.append(c.curve_tube(f"{name}_{k}", pts, radii, mat, bevel=width * strand_scale, resolution=3))
    return objs


def fall_point(phi, z, offset):
    """Point on the curved surface the long hair falls along, behind the shoulders and
    down the back (phi 0 = straight behind, +-90 = beside the shoulders). `offset` pushes
    it outward, so the base sheet, the card layers and the braids stack in order."""
    t = min(1.0, max(0.0, (1.5 - z) / 0.6))
    rx = 0.195 * (1 + 0.1 * t - 0.16 * t * t) + offset
    ry = 0.08 + 0.02 * t + offset
    return Vector((math.sin(phi) * rx, 0.05 + math.cos(phi) * ry, z))


def theta_to_phi(theta_deg):
    """Head angle (0 = front) to fall angle (0 = behind), both signed toward +X."""
    return math.radians(((180 - theta_deg + 180) % 360) - 180)


def scalp_dir(theta_deg, z_local):
    p = head_surface(theta_deg, z_local, 0.0) - Vector((0, 0, HEAD_Z))
    return Vector((p.x / H.x, p.y / H.y, p.z / H.z)).normalized()


def scalp_point(direction, offset):
    d = direction.normalized()
    return Vector((d.x * (H.x + offset), d.y * (H.y + offset), d.z * (H.z + offset) + HEAD_Z))


def strand_texture(path, size=(512, 1024), seed=7):
    """Hair-card texture in the RE Engine ALBA layout (RGB = colour, A = coverage).
    Strands run along V (roots at v = 0, tips toward v = 1), gather into clumps toward
    the tips and tile horizontally, so any horizontal slice of it can go on a card."""
    import numpy as np
    from PIL import Image
    w, h = size
    rs = np.random.RandomState(seed)
    v = np.linspace(0.0, 1.0, h)
    base = np.array([int(c.PALETTE["hair"][i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    pale = np.array([0xF4, 0xE6, 0xC0]) / 255.0
    trans = np.ones((h, w))
    col = np.zeros((h, w, 3))
    wsum = np.zeros((h, w))
    n_clumps = 18
    cx = (np.arange(n_clumps) + rs.uniform(-0.3, 0.3, n_clumps)) * w / n_clumps
    c_amp = rs.uniform(2, 7, n_clumps)
    c_freq = rs.uniform(0.8, 1.8, n_clumps)
    c_ph = rs.uniform(0, 2 * np.pi, n_clumps)
    xs = np.arange(-6, 7)
    rows = np.repeat(np.arange(h)[:, None], len(xs), axis=1)
    grad = (0.86 + 0.2 * v)[:, None, None]          # slightly deeper at the roots
    for _ in range(900):
        k = rs.randint(n_clumps)
        x0 = cx[k] + rs.normal(0, w / n_clumps * 0.5)
        conv = rs.uniform(0.3, 0.85)
        sigma = rs.uniform(0.55, 1.3)
        v0, v1 = rs.uniform(0.0, 0.04), rs.uniform(0.55, 1.0)
        xc = (x0 + (cx[k] - x0) * conv * v ** 1.4
              + c_amp[k] * np.sin(2 * np.pi * c_freq[k] * v + c_ph[k])
              + rs.uniform(0.3, 1.5) * np.sin(2 * np.pi * rs.uniform(2, 5) * v + rs.uniform(0, 2 * np.pi)))
        cols = np.floor(xc).astype(int)[:, None] + xs[None, :]
        a = np.exp(-0.5 * ((cols + 0.5 - xc[:, None]) / sigma) ** 2) * rs.uniform(0.55, 0.95)
        a *= (np.clip((v1 - v) / 0.15, 0, 1) ** 1.5 * np.clip((v - v0) / 0.02, 0, 1))[:, None]
        cols %= w
        strand = (pale if rs.uniform() < 0.12 else base) * rs.uniform(0.82, 1.1)
        trans[rows, cols] *= 1 - a
        col[rows, cols] += a[..., None] * strand[None, None, :] * grad
        wsum[rows, cols] += a
    rgb = np.where(wsum[..., None] > 1e-4, col / np.maximum(wsum, 1e-4)[..., None], base)
    img = np.flipud(np.dstack([np.clip(rgb, 0, 1), 1 - trans]))   # image rows start at the top
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").save(path)
    return path


def hair_materials(tex_path):
    """Three materials sharing the strand texture:
    cards  - colour + alpha straight from the texture (like the game's alpha-tested cards)
    base   - opaque; gaps between strands read as shadowed hair (scalp cap)
    volume - opaque, but the tips of the texture cut a ragged hem at the bottom"""
    img = bpy.data.images.load(os.path.abspath(tex_path))
    img.pack()
    dark = c.hex_to_linear("#9C7E48")
    mats = []
    for name, mode in (("Hair_Cards", "card"), ("Hair_Base", "base"), ("Hair_VolumeMat", "volume")):
        mat = c.make_material(name, c.PALETTE["hair"], roughness=0.45, coat=0.2,
                              emission=c.PALETTE["hair"], strength=0.0)
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes["Principled BSDF"]
        uv = nodes.new("ShaderNodeUVMap")
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.extension = "REPEAT"
        links.new(uv.outputs["UV"], tex.inputs["Vector"])
        if mode == "card":
            colour = tex.outputs["Color"]
            # Fade toward the card's long edges so no straight cut shows.
            edge = nodes.new("ShaderNodeAttribute")
            edge.attribute_name = "edge"
            fade = nodes.new("ShaderNodeMapRange")
            fade.interpolation_type = "SMOOTHSTEP"
            fade.inputs["From Min"].default_value = 0.0
            fade.inputs["From Max"].default_value = 0.5
            links.new(edge.outputs["Fac"], fade.inputs["Value"])
            mul = nodes.new("ShaderNodeMath")
            mul.operation = "MULTIPLY"
            links.new(tex.outputs["Alpha"], mul.inputs[0])
            links.new(fade.outputs["Result"], mul.inputs[1])
            # ...and fade in at the root, so roots blend into the hair below them.
            sep = nodes.new("ShaderNodeSeparateXYZ")
            links.new(uv.outputs["UV"], sep.inputs["Vector"])
            root = nodes.new("ShaderNodeMapRange")
            root.interpolation_type = "SMOOTHSTEP"
            root.inputs["From Min"].default_value = 0.0
            root.inputs["From Max"].default_value = 0.1
            links.new(sep.outputs["Y"], root.inputs["Value"])
            mul2 = nodes.new("ShaderNodeMath")
            mul2.operation = "MULTIPLY"
            links.new(mul.outputs["Value"], mul2.inputs[0])
            links.new(root.outputs["Result"], mul2.inputs[1])
            links.new(mul2.outputs["Value"], bsdf.inputs["Alpha"])
        else:
            mix = nodes.new("ShaderNodeMixRGB")
            mix.inputs["Color1"].default_value = dark
            links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
            links.new(tex.outputs["Color"], mix.inputs["Color2"])
            colour = mix.outputs["Color"]
        if mode == "volume":
            sep = nodes.new("ShaderNodeSeparateXYZ")
            links.new(uv.outputs["UV"], sep.inputs["Vector"])
            solid = nodes.new("ShaderNodeMapRange")
            solid.inputs["From Min"].default_value = 0.8
            solid.inputs["From Max"].default_value = 0.96
            solid.inputs["To Min"].default_value = 1.0
            solid.inputs["To Max"].default_value = 0.0
            links.new(sep.outputs["Y"], solid.inputs["Value"])
            mx = nodes.new("ShaderNodeMath")
            mx.operation = "MAXIMUM"
            links.new(solid.outputs["Result"], mx.inputs[0])
            links.new(tex.outputs["Alpha"], mx.inputs[1])
            links.new(mx.outputs["Value"], bsdf.inputs["Alpha"])
        links.new(colour, bsdf.inputs["Base Color"])
        links.new(colour, bsdf.inputs["Emission Color"])
        mats.append(mat)
    return mats


def hem_z(phi):
    """Where the long hair ends: longest at the center of the back, rising toward the
    sides so the ends form a soft curve."""
    return 0.88 + 0.14 * (abs(phi) / 1.36) ** 1.5


def set_face_uvs(face, layer, uvs):
    for loop, co in zip(face.loops, uvs):
        loop[layer].uv = co


def hair_volume(hair_mat):
    """Base sheet of hair: hugs the back of the head, then falls behind the shoulders to
    below the waist with soft vertical waves. Everything else is layered on top of it."""
    bm = bmesh.new()
    layer = bm.loops.layers.uv.new("UVMap")
    n_u, n_v = 56, 60
    rows = []
    for i in range(n_v + 1):
        t = i / n_v
        row = []
        for j in range(n_u + 1):
            phi = math.radians(-78 + 156 * j / n_u)        # 0 = straight behind
            z = 1.6 - (1.6 - hem_z(phi)) * t
            # On the head: follow the scalp. Below the nape: fall behind shoulders and back.
            zl = z - HEAD_Z
            on_head = head_surface(180 - math.degrees(phi), max(zl, -0.09), 0.009)
            w = smoothstep((1.5 - z) / 0.12)
            p = on_head * (1 - w) + fall_point(phi, z, 0.0) * w
            wave = 0.012 * math.sin(phi * 13 + z * 4) * w
            p += Vector((math.sin(phi), math.cos(phi), 0)) * wave
            row.append(bm.verts.new(p))
        rows.append(row)
    for i in range(n_v):
        for j in range(n_u):
            f = bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
            u0, u1 = 3 * j / n_u, 3 * (j + 1) / n_u
            v0, v1 = i / n_v, (i + 1) / n_v
            set_face_uvs(f, layer, ((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
    mesh = bpy.data.meshes.new("hair_volume")
    bm.to_mesh(mesh)
    bm.free()
    obj = c.link(bpy.data.objects.new("Hair_Volume", mesh))
    obj.data.materials.append(hair_mat)
    solid = obj.modifiers.new("thick", "SOLIDIFY")
    solid.thickness = 0.012
    sub = obj.modifiers.new("smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def add_card(bm, layer, edge_layer, path, width, rng, tilt):
    """One hair card: a strip three vertices wide along the path, bowed slightly outward,
    facing away from the head / body axis. U runs across a random slice of the texture,
    V from root (0) to tip (1)."""
    n = len(path)
    u0, uw = rng.uniform(0, 1), rng.uniform(0.3, 0.5)
    prev = None
    for i, p in enumerate(path):
        t = i / (n - 1)
        tan = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        wf = smoothstep((1.5 - p.z) / 0.12)
        out = p - Vector((0, 0.05 * wf, min(p.z, HEAD_Z)))
        side = tan.cross(out)
        if side.length < 1e-6:
            side = Vector((1, 0, 0))
        side.normalize()
        nrm = side.cross(tan).normalized()
        if nrm.dot(out) < 0:
            nrm = -nrm
        side, nrm = side * math.cos(tilt) + nrm * math.sin(tilt), nrm * math.cos(tilt) - side * math.sin(tilt)
        w = width * (0.7 + 0.5 * math.sin(math.pi * t * 0.85)) * (1 - 0.45 * t * t)
        row = [bm.verts.new(p + side * (w * k) + nrm * (0.12 * w if k == 0 else 0.0))
               for k in (-0.5, 0.0, 0.5)]
        for vert, e in zip(row, (0.0, 1.0, 0.0)):
            vert[edge_layer] = e
        if prev:
            tp = (i - 1) / (n - 1)
            for k in range(2):
                f = bm.faces.new((prev[k], prev[k + 1], row[k + 1], row[k]))
                ua, ub = u0 + uw * k / 2, u0 + uw * (k + 1) / 2
                set_face_uvs(f, layer, ((ua, tp), (ub, tp), (ub, t), (ua, t)))
        prev = row


def loose_path(d_root, theta_leave, zl_leave, z_extra, off_head, off_fall, ph):
    """Root on the scalp -> along the scalp to where the hair leaves the head -> down the
    back along the fall surface, with a soft wave that grows toward the tips."""
    d_leave = scalp_dir(theta_leave, zl_leave)
    ctrl = [scalp_point(d_root.lerp(d_leave, f), off_head + 0.003 * f) for f in (0, 0.33, 0.66, 1.0)]
    phi = max(-1.36, min(1.36, theta_to_phi(theta_leave) * 0.72))
    z_end = hem_z(phi) + z_extra
    ctrl += [fall_point(phi, 1.4, off_fall), fall_point(phi, (1.4 + z_end) / 2, off_fall),
             fall_point(phi * 0.98, z_end, off_fall)]
    path = catmull(ctrl, 44)
    return [p + Vector((0.012 * math.sin(p.z * 22 + ph), 0.006 * math.cos(p.z * 18 + ph), 0))
            * smoothstep((1.5 - p.z) / 0.2) for p in path]


def build_hair(card_mat, base_mat, volume_mat, braid_mat, rng):
    objs = []
    # Scalp cap with a smooth hairline: lower at the back, higher at the forehead.
    # Textured so strands run from the crown down to the hairline.
    bm = bmesh.new()
    layer = bm.loops.layers.uv.new("UVMap")
    n_t, n_r = 96, 24
    top_z = H.z * 0.985
    rows = []
    for i in range(n_r):
        row = []
        for j in range(n_t):
            th = 360 * j / n_t
            front = math.cos(math.radians(th))           # 1 at the forehead, -1 at the back
            hairline = 0.02 + 0.055 * max(0.0, front) - 0.07 * max(0.0, -front)
            zl = hairline + (top_z - hairline) * (i / (n_r - 1)) ** 0.8
            row.append(bm.verts.new(head_surface(th, zl, 0.007)))
        rows.append(row)
    pole = bm.verts.new((0, 0, HEAD_Z + H.z + 0.007))
    cap_v = lambda i: 0.06 + 0.54 * (1 - i / (n_r - 1))
    for i in range(n_r - 1):
        for j in range(n_t):
            k = (j + 1) % n_t
            f = bm.faces.new((rows[i][j], rows[i][k], rows[i + 1][k], rows[i + 1][j]))
            u0, u1 = 6 * j / n_t, 6 * (j + 1) / n_t
            set_face_uvs(f, layer, ((u0, cap_v(i)), (u1, cap_v(i)), (u1, cap_v(i + 1)), (u0, cap_v(i + 1))))
    for j in range(n_t):
        f = bm.faces.new((rows[-1][j], rows[-1][(j + 1) % n_t], pole))
        u0, u1 = 6 * j / n_t, 6 * (j + 1) / n_t
        set_face_uvs(f, layer, ((u0, cap_v(n_r - 1)), (u1, cap_v(n_r - 1)), ((u0 + u1) / 2, 0.06)))
    me = bpy.data.meshes.new("hair_cap")
    bm.to_mesh(me)
    bm.free()
    cap = c.link(bpy.data.objects.new("Hair_Cap", me))
    cap.data.materials.append(base_mat)
    solid = cap.modifiers.new("thick", "SOLIDIFY")
    solid.thickness = 0.004
    for p in cap.data.polygons:
        p.use_smooth = True
    objs.append(cap)

    # Two side braids from the front beside the center part, wrapping back almost level,
    # meeting at the back of the head.
    back_meet = scalp_point(scalp_dir(180, 0.03), 0.022)
    for s in (1, -1):
        ctrl = [scalp_point(scalp_dir(s * th, zl), 0.021) for th, zl in
                ((5, 0.098), (28, 0.104), (65, 0.097), (105, 0.08), (145, 0.055))] + [back_meet]
        path = catmull(ctrl, 60)
        objs += braid(f"SideBraid_{s}", path, 0.02, braid_mat, taper=0.1)

    # One thick braid from where they meet, lying on top of the loose hair down the back.
    ctrl = [back_meet, back_meet + Vector((0, 0.025, -0.07)), fall_point(0, 1.38, 0.05),
            fall_point(0, 1.2, 0.05), fall_point(0, 1.02, 0.05), fall_point(0, 0.88, 0.05)]
    objs += braid("MainBraid", catmull(ctrl, 90), 0.036, braid_mat, taper=0.55)

    objs.append(hair_volume(volume_mat))

    # Long wavy loose hair as layered cards (the way game hair is built): one mesh,
    # each card a strip carrying a slice of the strand texture.
    bm = bmesh.new()
    layer = bm.loops.layers.uv.new("UVMap")
    edge_layer = bm.verts.layers.float.new("edge")
    layers = ((0.012, 0.010), (0.024, 0.012), (0.036, 0.014))     # (fall offset, scalp offset)
    count = 0

    def card(d_root, theta_leave, zl_leave):
        nonlocal count
        li = rng.choices((0, 1, 2), weights=(4, 3.5, 2.5))[0]
        off_fall, off_head = layers[li]
        z_extra = rng.uniform(-0.03, 0.08) + 0.02 * li
        path = loose_path(d_root, theta_leave, zl_leave, z_extra, off_head, off_fall,
                          rng.uniform(0, 2 * math.pi))
        # Wider than they look: the edges fade out.
        width = rng.uniform(0.04, 0.065) if li < 2 else rng.uniform(0.032, 0.05)
        add_card(bm, layer, edge_layer, path, width, rng, math.radians(rng.uniform(-12, 12)))
        count += 1

    # From the center part, swept to the sides and back, leaving the head behind the ears
    # (front of the part) or at the back (crown).
    for s in (1, -1):
        for k in range(40):
            a = (k + rng.uniform(0, 1)) / 40
            ang = math.radians(-46 + 86 * a)
            d_root = Vector((s * 0.04, math.sin(ang), math.cos(ang)))
            card(d_root, s * (78 + 95 * a + rng.uniform(-8, 8)), rng.uniform(-0.055, -0.02))
    # Fill for the back of the head below the crown.
    for k in range(60):
        th = rng.uniform(100, 260)
        card(scalp_dir(th, rng.uniform(0.02, 0.09)), 180 + (th - 180) * 0.9, rng.uniform(-0.06, -0.03))

    me = bpy.data.meshes.new("hair_cards")
    bm.to_mesh(me)
    bm.free()
    cards = c.link(bpy.data.objects.new("Hair_Cards", me))
    cards.data.materials.append(card_mat)
    for p in cards.data.polygons:
        p.use_smooth = True
    objs.append(cards)
    print(f"[hair] {count} cards, {len(me.polygons)} faces", flush=True)

    # Several small braids lying among the loose hair.
    for k, th in enumerate((125, 150, 205, 232, 140, 220)):
        root = head_surface(th, rng.uniform(-0.01, 0.03), 0.02)
        phi = theta_to_phi(th) * 0.8
        end = fall_point(phi * 1.05, rng.uniform(1.0, 1.12), 0.042)
        path = catmull([root, fall_point(phi, 1.43, 0.04), end], 50)
        objs += braid(f"SmallBraid_{k}", path, 0.011, braid_mat, taper=0.4)
    return objs


# ---------------------------------------------------------------- scene

def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(21)
    # The circlet builds (and resets) the scene first, around a head centred at the origin.
    parts, circ_mat, drop_mat = cl.build(glow_strength=0.1)
    holder = c.link(bpy.data.objects.new("Circlet", None))
    for p in parts:
        p.parent = holder
    holder.location = (0, 0, HEAD_Z)
    holder.scale = (1.12, 1.1, 1.06)   # sits on top of the hair, not the bare scalp
    c.set_emission_strength(circ_mat, 0.1)

    skin = c.make_material("Skin", c.PALETTE["skin"], roughness=0.55, subsurface=0.2)
    robe = c.make_material("Robe", c.PALETTE["robe"], roughness=0.75)
    gold = c.make_material("Gold_Trim", c.PALETTE["gold_hi"], roughness=0.35, metallic=0.9)
    hair = c.make_material("Hair", c.PALETTE["hair"], roughness=0.45, coat=0.2,
                           emission=c.PALETTE["hair"], strength=0.0)
    tex_path = strand_texture(os.path.join(OUT, "hair_strands_ALBA.png"))
    hair_mats = hair_materials(tex_path)

    body, head = build_body(skin)
    build_robe(body, robe, gold)
    build_hair(*hair_mats, hair, rng)

    c.setup_render(samples=40, res=(700, 1000), world_hex="#34343A", world_strength=0.6)
    bpy.context.scene.cycles.transparent_max_bounces = 48   # layered alpha cards
    c.add_light("key", "AREA", (1.6, -2.2, 2.6), 260, size=2.0, target=(0, 0, 1.1))
    c.add_light("fill", "AREA", (-2.2, -1.2, 1.4), 90, size=2.0, target=(0, 0, 1.0))
    c.add_light("rim", "AREA", (0.0, 2.4, 2.6), 220, size=1.6, target=(0, 0, 1.2))
    body_target = (0, 0, 0.88)
    views = [("front", 0, 5), ("three_quarter", 35, 8), ("side", 90, 5), ("back", 180, 8),
             ("back_three_quarter", 145, 12)]
    full = c.render_views(OUT, "full", body_target, 3.1, views, lens=50)
    head_views = c.render_views(OUT, "head", (0, 0.03, HEAD_Z - 0.04), 1.0,
                                [("head_front", 10, 5), ("head_back", 170, 20), ("head_side", 100, 8)], lens=50)
    c.contact_sheet(full, os.path.join(OUT, "character_sheet.png"), cols=5)
    c.contact_sheet(head_views, os.path.join(OUT, "character_head_sheet.png"), cols=3)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, "character_concept.blend")))

    # Glow: golden circlet, faint glow in the hair.
    c.set_emission_strength(circ_mat, 1.3)
    c.set_emission_strength(drop_mat, 2.0)
    for m in [hair] + hair_mats:
        c.set_emission_strength(m, 0.12)
    c.setup_render(samples=40, res=(700, 1000), world_hex="#101014", world_strength=0.3, glare=True)
    bpy.context.scene.cycles.transparent_max_bounces = 48
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.data.energy *= 0.35
    glow = c.render_views(OUT, "glow", body_target, 3.1, [views[0], views[1], views[4]], lens=50)
    glow_head = c.render_views(OUT, "glow_head", (0, 0.03, HEAD_Z - 0.04), 1.0, [("head_front", 10, 5)], lens=50)
    c.contact_sheet(glow + glow_head, os.path.join(OUT, "character_glow_sheet.png"), cols=4)
    print("DONE", full + head_views + glow + glow_head)


if __name__ == "__main__":
    main()
