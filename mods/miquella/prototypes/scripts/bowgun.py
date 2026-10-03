"""Heavy bowgun concept blockout: a holy light cannon.

Stock and receiver are woven from ivory strands; in front of the receiver the strands
split into three branches (the circlet's trident motif) that spiral around a glowing
light conduit instead of a metal barrel. A glowing halo ring floats at the muzzle and a
glowing droplet sits on the receiver as the energy core. See DESIGN.md section 5.

Axes: +Y is the muzzle direction, +Z is up.

Usage: python bowgun.py <out_dir>
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

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"

STOCK_END = -0.48
WRIST = -0.14
RECEIVER_END = 0.10
MUZZLE = 0.82
CONDUIT_R = 0.046
CONDUIT_Z = 0.03


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def body_section(y):
    """Center (x, z) and half-sizes (rx, rz) of the stock/receiver body at y."""
    if y < WRIST:
        u = (y - STOCK_END) / (WRIST - STOCK_END)          # 0 at butt, 1 at wrist
        cz = -0.05 * (1 - u) ** 1.3
        rz = 0.105 * (1 - u) + 0.05 * u
        rx = 0.04 + 0.006 * (1 - u)
    else:
        u = (y - WRIST) / (RECEIVER_END - WRIST)           # 0 at wrist, 1 at receiver front
        cz = 0.015 * math.sin(math.pi * u)
        rz = 0.05 + 0.045 * math.sin(math.pi * min(1.0, u * 1.3))
        rx = 0.046 + 0.034 * math.sin(math.pi * min(1.0, u * 1.2))
    return Vector((0, y, cz)), rx, rz


def loft_body(material):
    """Smooth solid under the strands so the weave never shows holes."""
    mesh = bpy.data.meshes.new("body")
    bm = bmesh.new()
    rings = []
    n_y, n_s = 90, 24
    for i in range(n_y + 1):
        y = STOCK_END + (RECEIVER_END - STOCK_END) * i / n_y
        ctr, rx, rz = body_section(y)
        # Round off both ends.
        end = min(1.0, (y - STOCK_END) / 0.03, (RECEIVER_END - y) / 0.03 + 0.2)
        k = math.sqrt(max(0.05, min(1.0, end)))
        rings.append([bm.verts.new(ctr + Vector((rx * k * 0.85 * math.cos(2 * math.pi * j / n_s), 0,
                                                 rz * k * 0.85 * math.sin(2 * math.pi * j / n_s))))
                      for j in range(n_s)])
    for i in range(n_y):
        for j in range(n_s):
            k = (j + 1) % n_s
            bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bm.to_mesh(mesh)
    bm.free()
    obj = c.link(bpy.data.objects.new("Body_Core", mesh))
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    sub = obj.modifiers.new("smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    return obj


def branch_center(b, v):
    """Center line of branch b (0..2) spiraling around the conduit, v in [0, 1]."""
    base_angle = math.radians(90 + 120 * b)
    angle = base_angle + math.radians(140) * v
    r = CONDUIT_R + 0.02 + 0.006 * math.sin(math.pi * v)
    y = RECEIVER_END - 0.02 + (MUZZLE - 0.05 - RECEIVER_END) * v
    return Vector((r * math.cos(angle), y, CONDUIT_Z + r * math.sin(angle)))


def woven_strands(material, rng):
    """Strands running over the body, then gathering into three branches around the conduit."""
    objs = []
    n = 36
    for k in range(n):
        phi = 2 * math.pi * k / n
        twist = rng.uniform(1.2, 2.0) * (1 if k % 2 == 0 else -1)
        branch = k % 3
        b_phase = rng.uniform(0, 2 * math.pi)
        b_omega = rng.uniform(10, 16) * (1 if rng.random() < 0.8 else -1)
        pts, radii = [], []
        # Over the body.
        n_body = 90
        for i in range(n_body):
            y = STOCK_END + 0.02 + (RECEIVER_END - 0.02 - STOCK_END - 0.02) * i / (n_body - 1)
            ctr, rx, rz = body_section(y)
            a = phi + twist * (y - STOCK_END)
            close = smoothstep((y - STOCK_END) / 0.06)
            pts.append(ctr + Vector((rx * 0.92 * close * math.cos(a), 0, rz * 0.92 * close * math.sin(a))))
            radii.append(0.6 + 0.4 * close)
        # Gather into the branch and spiral toward the muzzle.
        start = pts[-1].copy()
        n_br = 110
        end_v = rng.uniform(0.86, 1.0)
        for i in range(1, n_br):
            v = end_v * i / (n_br - 1)
            ctr = branch_center(branch, v)
            r = 0.014 * (1 - 0.35 * v)
            a = b_phase + b_omega * v
            # Local frame around the branch: radial from the conduit axis, and along Y.
            radial = Vector((ctr.x, 0, ctr.z - CONDUIT_Z)).normalized()
            around = Vector((0, 1, 0)).cross(radial).normalized()
            p = ctr + (radial * math.cos(a) + around * math.sin(a)) * r
            w = smoothstep(v / 0.15)
            pts.append(start * (1 - w) + p * w)
            radii.append(1.0 - 0.8 * smoothstep((v - (end_v - 0.12)) / 0.12))
        objs.append(c.curve_tube(f"Strand_{k}", pts, radii, material, bevel=0.0042, resolution=3))
    return objs


def pistol_grip(material, rng):
    """Woven grip under the receiver, raked back."""
    objs = []
    top = Vector((0, -0.08, -0.03))
    bottom = Vector((0, -0.15, -0.17))
    axis = (bottom - top).normalized()
    side = Vector((1, 0, 0))
    fwd = axis.cross(side).normalized()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=(bottom - top).length,
                                        location=(top + bottom) / 2)
    core = bpy.context.active_object
    core.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()
    core.name = "Grip_Core"
    core.data.materials.append(material)
    objs.append(core)
    for k in range(12):
        phi = 2 * math.pi * k / 12
        omega = rng.uniform(8, 11) * (1 if k % 2 == 0 else -1)
        pts = []
        for i in range(40):
            u = i / 39
            p = top + (bottom - top) * u
            a = phi + omega * u
            pts.append(p + (side * math.cos(a) + fwd * math.sin(a)) * 0.019)
        objs.append(c.curve_tube(f"GripStrand_{k}", pts, [1.0] * len(pts), material, bevel=0.0028, resolution=2))
    return objs


def conduit(glow_mat):
    """Glowing light conduit in place of a metal barrel."""
    length = MUZZLE - RECEIVER_END + 0.04
    bpy.ops.mesh.primitive_cylinder_add(radius=CONDUIT_R, depth=length, vertices=48,
                                        location=(0, RECEIVER_END - 0.04 + length / 2, CONDUIT_Z),
                                        rotation=(math.pi / 2, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Light_Conduit"
    obj.data.materials.append(glow_mat)
    bev = obj.modifiers.new("bevel", "BEVEL")
    bev.width = 0.01
    bev.segments = 4
    bpy.ops.object.shade_smooth()
    return [obj]


def muzzle_halo(glow_mat, ivory, rng):
    """Floating halo ring at the muzzle, with small strand curls anchoring it."""
    objs = []
    bpy.ops.mesh.primitive_torus_add(major_radius=0.105, minor_radius=0.008,
                                     major_segments=96, minor_segments=16,
                                     location=(0, MUZZLE + 0.06, CONDUIT_Z),
                                     rotation=(math.pi / 2, 0, 0))
    ring = bpy.context.active_object
    ring.name = "Muzzle_Halo"
    ring.data.materials.append(glow_mat)
    bpy.ops.object.shade_smooth()
    objs.append(ring)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.078, minor_radius=0.003,
                                     major_segments=96, minor_segments=12,
                                     location=(0, MUZZLE + 0.03, CONDUIT_Z),
                                     rotation=(math.pi / 2, 0, 0))
    inner = bpy.context.active_object
    inner.name = "Muzzle_Halo_Inner"
    inner.data.materials.append(glow_mat)
    bpy.ops.object.shade_smooth()
    objs.append(inner)
    return objs


def energy_core(glow_mat, ivory):
    """Glowing droplet cradled on top of the receiver."""
    objs = []
    center = Vector((0, -0.01, 0.112))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, segments=32, ring_count=16, location=center)
    drop = bpy.context.active_object
    drop.name = "Energy_Core"
    for v in drop.data.vertices:
        if v.co.y > 0:   # teardrop pointing forward
            f = v.co.y / 0.04
            v.co.x *= 1 - 0.7 * f
            v.co.z *= 1 - 0.7 * f
            v.co.y *= 1 + 1.0 * f
    drop.data.materials.append(glow_mat)
    bpy.ops.object.shade_smooth()
    objs.append(drop)
    # Cradle: four strand arcs from the receiver hugging the droplet.
    for k in range(2):
        a = k * math.pi
        pts = []
        for i in range(30):
            u = i / 29
            ang = math.pi * u
            r = 0.044
            p = Vector((r * math.cos(a) * math.sin(ang), -0.06 + 0.12 * u, 0.085 + 0.03 * math.sin(ang)))
            pts.append(p)
        objs.append(c.curve_tube(f"Cradle_{k}", pts, [1.0 - 0.5 * abs(0.5 - i / 29) for i in range(30)],
                                 ivory, bevel=0.0035, resolution=2))
    return objs


def side_wings(material, rng):
    """Dense strand bundles sweeping back and up from the receiver sides, splitting into
    three sub-bundles (the circlet's trident motif)."""
    objs = []
    for side in (-1, 1):
        root = Vector((side * 0.075, 0.05, 0.035))
        for k in range(32):
            phi = rng.uniform(0, 2 * math.pi)
            rr = rng.uniform(0.35, 1.0)
            omega = rng.uniform(4, 7) * (1 if rng.random() < 0.8 else -1)
            split = k % 3
            pts, radii = [], []
            for i in range(90):
                u = i / 89
                ctr = root + Vector((side * 0.045 * u ** 1.3, -0.27 * u, 0.075 * u ** 1.5))
                f = smoothstep((u - 0.45) / 0.55)
                fan = (split - 1) * 0.04 * f
                ctr += Vector((side * abs(fan) * 0.35, -0.02 * abs(split - 1) * f, fan))
                r = 0.018 * (1 - 0.3 * u) * (1 - f) + 0.008 * f
                a = phi + omega * u
                p = ctr + Vector((side * r * math.cos(a) * 0.7, r * 0.35 * math.sin(a), r * math.sin(a))) * rr
                pts.append(p)
                radii.append(1.0 - 0.85 * smoothstep((u - 0.82) / 0.18))
            objs.append(c.curve_tube(f"Wing_{side}_{k}", pts, radii, material, bevel=0.0038, resolution=2))
    return objs


def conduit_rings(glow_mat):
    """Floating halo rings along the conduit, like accelerator rings."""
    objs = []
    for y, r, minor in ((0.34, 0.1, 0.0042), (0.56, 0.094, 0.0038)):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=minor,
                                         major_segments=96, minor_segments=12,
                                         location=(0, y, CONDUIT_Z), rotation=(math.pi / 2, 0, 0))
        ring = bpy.context.active_object
        ring.name = f"Conduit_Halo_{y}"
        ring.data.materials.append(glow_mat)
        bpy.ops.object.shade_smooth()
        objs.append(ring)
    return objs


# Stock and grip in one piece (user's pick 2026-10-03, A3; the hunter never holds the pistol grip,
# and a grip and a stock read as two things): behind the wrist the stock and the grip are one woven
# ring round a thumbhole (bowgun_onepiece.py), its grain running round the hole, with gold wound round
# it both ways. False: the old stock and pistol grip.
ONE_PIECE = True


def stock_and_body(ivory, gold, rng, gun="hbg", weave_bevel=0.0042):
    """The body and its strands (from the wrist on, the strands then reach along the barrel), and
    behind the wrist the one-piece stock (or the old stock and grip)."""
    global STOCK_END, body_section
    if not ONE_PIECE:
        return [loft_body(ivory)] + woven_strands(ivory, rng) + pistol_grip(ivory, rng)
    import bowgun_onepiece as op
    full_end, section = STOCK_END, body_section
    ctr_w, rx_w, rz_w = section(WRIST)
    STOCK_END = WRIST - 0.03
    body_section = lambda y: section(y) if y >= WRIST else (Vector((0, y, ctr_w.z)), rx_w, rz_w)
    try:
        parts = [loft_body(ivory)] + woven_strands(ivory, rng)
    finally:
        STOCK_END, body_section = full_end, section
    fr = op.ring_frames(gun, wrist=WRIST, stock_len=WRIST - full_end)
    parts.append(op.ring_core("Stock_Core", fr, ivory))
    parts += op.ring_strands("Stock_Weave", fr, ivory, 40, 2.2, weave_bevel, rng=rng)
    lift = weave_bevel + 0.0035
    parts += op.ring_strands("Stock_Gold", fr, gold, 3, 9.0, 0.0021, cross=True, phase=math.pi / 3, lift=lift)
    parts += op.ring_strands("Stock_Gold2", fr, gold, 3, 9.0, 0.0021, cross=False, phase=2 * math.pi / 3, lift=lift)
    return parts


def barrel_phials(mats, ys, z, size):
    """Three lit droplets floating in a row above the barrel, forward of the shooter (not
    over the stock, which felt crowding), each in a small halo that faces the side."""
    import motifs
    pts = [Vector((0, y, z)) for y in ys]
    return motifs.floating_phials("Barrel_Phial", pts, (0, -0.15, 1), (1, 0, 0.25), mats, size=size)


def build():
    """The whole heavy bowgun; returns the ivory and light materials."""
    rng = random.Random(5)
    c.reset_scene()
    ivory = c.make_material("Ivory", c.PALETTE["ivory"], roughness=0.32, coat=0.3,
                            emission=c.PALETTE["glow"], strength=0.05, subsurface=0.15)
    glow = c.make_material("Light", c.PALETTE["blade_core"], roughness=0.1, coat=0.5,
                           emission=c.PALETTE["blade_core"], strength=0.6)
    parts = stock_and_body(ivory, glow, rng, "hbg", 0.0042)
    parts += conduit(glow)
    parts += muzzle_halo(glow, ivory, rng)
    parts += energy_core(glow, ivory)
    parts += side_wings(ivory, rng)
    parts += conduit_rings(glow)
    parts += barrel_phials({"light": glow}, ys=(0.2, 0.32, 0.44), z=CONDUIT_Z + 0.15, size=0.018)
    return ivory, glow


def main():
    os.makedirs(OUT, exist_ok=True)
    ivory, glow = build()

    c.setup_render(samples=32, res=(900, 600), world_hex="#2E2E33", world_strength=0.5)
    c.add_light("key", "AREA", (1.0, -0.6, 1.0), 120, size=1.0, target=(0, 0.1, 0))
    c.add_light("fill", "AREA", (-1.0, 0.2, 0.4), 40, size=1.0, target=(0, 0.1, 0))
    c.add_light("rim", "AREA", (0.0, 1.4, 0.9), 70, size=0.8, target=(0, 0.1, 0))
    target = (0, 0.2, 0.02)
    views = [("side", 90, 4), ("front_three_quarter", 140, 18), ("back_three_quarter", 45, 20),
             ("top", 90, 75), ("muzzle", 175, 8), ("low_side", 70, -12)]
    studio = c.render_views(OUT, "studio", target, 2.6, views, lens=50)
    c.contact_sheet(studio, os.path.join(OUT, "bowgun_studio_sheet.png"), cols=3)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, "heavy_bowgun.blend")))

    c.set_emission_strength(glow, 2.5)
    c.setup_render(samples=32, res=(900, 600), world_hex="#0E0E12", world_strength=0.25, glare=True)
    glow_paths = c.render_views(OUT, "glow", target, 2.6, [views[0], views[1]], lens=50)
    c.contact_sheet(glow_paths, os.path.join(OUT, "bowgun_glow_sheet.png"), cols=2)
    print("DONE", studio + glow_paths)


if __name__ == "__main__":
    main()
