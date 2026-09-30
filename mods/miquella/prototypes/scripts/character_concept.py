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


def hair_volume(hair_mat):
    """Base sheet of hair: hugs the back of the head, then falls behind the shoulders to
    below the waist with soft vertical waves. Gives the loose strands their volume."""
    bm = bmesh.new()
    n_u, n_v = 56, 60
    rows = []
    for i in range(n_v + 1):
        t = i / n_v
        z = 1.6 - (1.6 - 0.9) * t
        row = []
        for j in range(n_u + 1):
            phi = math.radians(-78 + 156 * j / n_u)        # 0 = straight behind
            # On the head: follow the scalp. Below the nape: fall behind shoulders and back.
            zl = z - HEAD_Z
            on_head = head_surface(180 - math.degrees(phi), max(zl, -0.09), 0.02)
            fall = Vector((math.sin(phi) * 0.195 * (1 + 0.12 * t),
                           0.05 + math.cos(phi) * 0.1 + 0.03 * t, z))
            w = smoothstep((1.5 - z) / 0.12)
            p = on_head * (1 - w) + fall * w
            wave = 0.012 * math.sin(phi * 13 + z * 4) * w
            p += Vector((math.sin(phi), math.cos(phi), 0)) * wave
            row.append(bm.verts.new(p))
        rows.append(row)
    for i in range(n_v):
        for j in range(n_u):
            bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
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


def build_hair(hair_mat, rng):
    objs = []
    # Scalp cap with a smooth hairline: lower at the back, higher at the forehead.
    bm = bmesh.new()
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
    for i in range(n_r - 1):
        for j in range(n_t):
            k = (j + 1) % n_t
            bm.faces.new((rows[i][j], rows[i][k], rows[i + 1][k], rows[i + 1][j]))
    for j in range(n_t):
        bm.faces.new((rows[-1][j], rows[-1][(j + 1) % n_t], pole))
    me = bpy.data.meshes.new("hair_cap")
    bm.to_mesh(me)
    bm.free()
    cap = c.link(bpy.data.objects.new("Hair_Cap", me))
    cap.data.materials.append(hair_mat)
    solid = cap.modifiers.new("thick", "SOLIDIFY")
    solid.thickness = 0.004
    for p in cap.data.polygons:
        p.use_smooth = True
    objs.append(cap)

    # Two side braids from the front beside the center part, wrapping back almost level,
    # meeting at the back of the head.
    back_meet = head_surface(180, 0.03, 0.02)
    for s in (1, -1):
        ctrl = [head_surface(s * th, zl, 0.018) for th, zl in
                ((5, 0.098), (28, 0.104), (65, 0.097), (105, 0.08), (145, 0.055))] + [back_meet]
        path = catmull(ctrl, 60)
        objs += braid(f"SideBraid_{s}", path, 0.02, hair_mat, taper=0.1)

    # One thick braid from where they meet, hanging down the back.
    ctrl = [back_meet, back_meet + Vector((0, 0.02, -0.08)), Vector((0, 0.12, 1.42)),
            Vector((0, 0.14, 1.25)), Vector((0, 0.15, 1.05)), Vector((0, 0.16, 0.9))]
    objs += braid("MainBraid", catmull(ctrl, 90), 0.036, hair_mat, taper=0.55)

    objs.append(hair_volume(hair_mat))

    # Long wavy loose hair falling over the back to the hips.
    for i in range(320):
        th = rng.uniform(65, 295)
        zl = rng.uniform(-0.03, 0.07)
        root = head_surface(th, zl, 0.012)
        side = math.sin(math.radians(th))
        fall_x = side * rng.uniform(0.1, 0.19)
        mid = Vector((fall_x, max(root.y, 0.05) + 0.07, 1.42))
        low = Vector((fall_x * 1.25, 0.14 + rng.uniform(0, 0.04), rng.uniform(0.86, 1.0)))
        path = catmull([root, root + Vector((0, 0.02, -0.05)), mid, low], 40)
        ph = rng.uniform(0, 2 * math.pi)
        wavy = [p + Vector((0.012 * math.sin(p.z * 22 + ph), 0.006 * math.cos(p.z * 18 + ph), 0))
                * smoothstep((1.5 - p.z) / 0.2) for p in path]
        objs.append(c.curve_tube(f"Loose_{i}", wavy, [1 - 0.6 * (j / 39) for j in range(40)],
                                 hair_mat, bevel=0.0065, resolution=2))

    # Several small braids hidden among the loose hair.
    for k, th in enumerate((125, 150, 205, 232, 140, 220)):
        root = head_surface(th, rng.uniform(-0.01, 0.03), 0.02)
        side = math.sin(math.radians(th))
        end = Vector((side * 0.17, 0.17, rng.uniform(1.0, 1.12)))
        path = catmull([root, Vector((side * 0.11, 0.12, 1.43)), end], 50)
        objs += braid(f"SmallBraid_{k}", path, 0.011, hair_mat, taper=0.4)
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

    body, head = build_body(skin)
    build_robe(body, robe, gold)
    build_hair(hair, rng)

    c.setup_render(samples=40, res=(700, 1000), world_hex="#34343A", world_strength=0.6)
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
    c.set_emission_strength(hair, 0.12)
    c.setup_render(samples=40, res=(700, 1000), world_hex="#101014", world_strength=0.3, glare=True)
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.data.energy *= 0.35
    glow = c.render_views(OUT, "glow", body_target, 3.1, [views[0], views[1], views[4]], lens=50)
    glow_head = c.render_views(OUT, "glow_head", (0, 0.03, HEAD_Z - 0.04), 1.0, [("head_front", 10, 5)], lens=50)
    c.contact_sheet(glow + glow_head, os.path.join(OUT, "character_glow_sheet.png"), cols=4)
    print("DONE", full + head_views + glow + glow_head)


if __name__ == "__main__":
    main()
