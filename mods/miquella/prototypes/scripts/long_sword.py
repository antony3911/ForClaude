"""Long sword (tachi) prototype.

A long, gently curved single-edged blade of golden light with a brighter line along the
edge, a floating halo ring in place of a physical tsuba, a woven ivory handle, and a
glowing droplet at the pommel. See DESIGN.md section 5.

Blade runs along +Z; the edge faces +X and the blade curves back toward the spine (-X).

Usage: python long_sword.py <out_dir>
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
import blades

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"

HANDLE_LEN = 0.34
COLLAR = 0.03
BLADE_LEN = 1.05
SORI = 0.034          # maximum curvature offset of the blade
WIDTH = 0.034         # edge-to-spine width at the base
THICK = 0.0075


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def blade_center(s):
    """Spine-side curve: the blade bows back toward -X, strongest near the middle-top."""
    z = COLLAR + BLADE_LEN * s
    x = -SORI * (s ** 1.6)
    return Vector((x, 0, z))


def blade_profile(s):
    """Width and thickness along the blade; the kissaki narrows the width to a point."""
    w = WIDTH * (1 - 0.3 * s)
    t = THICK * (1 - 0.35 * s)
    if s > 0.92:
        k = (s - 0.92) / 0.08
        w *= (1 - k ** 1.6)
        t *= (1 - 0.8 * k)
    return max(w, 0.0005), max(t, 0.0004)


def build_blade(material):
    """Single-edged wedge section: flat spine, ridge line near the spine, sharp edge."""
    mesh = bpy.data.meshes.new("tachi_blade")
    bm = bmesh.new()
    rings = []
    n_len = 140
    for i in range(n_len + 1):
        s = i / n_len
        ctr = blade_center(s)
        w, t = blade_profile(s)
        spine = ctr.x
        ridge = spine + 0.3 * w
        edge = spine + w
        section = [(spine, 0.4 * t), (ridge, 0.5 * t), (edge, 0.0), (ridge, -0.5 * t), (spine, -0.4 * t)]
        rings.append([bm.verts.new((x, y, ctr.z)) for x, y in section])
    n_sec = 5
    for i in range(n_len):
        for j in range(n_sec):
            k = (j + 1) % n_sec
            bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.to_mesh(mesh)
    bm.free()
    obj = c.link(bpy.data.objects.new("Tachi_Blade", mesh))
    obj.data.materials.append(material)
    return obj


def hamon_line(material):
    """Brighter line of light running just inside the cutting edge."""
    objs = []
    for face in (-1, 1):
        pts, radii = [], []
        for i in range(80):
            s = 0.02 + 0.9 * i / 79
            ctr = blade_center(s)
            w, t = blade_profile(s)
            # Gentle wave like a hamon.
            inset = 0.2 * w + 0.05 * w * math.sin(s * 40)
            pts.append(Vector((ctr.x + w - inset, face * t * 0.18, ctr.z)))
            radii.append(1.0 - 0.6 * s)
        objs.append(c.curve_tube(f"Hamon_{face}", pts, radii, material, bevel=0.0014, resolution=2))
    return objs


def handle(ivory, drop_material, rng):
    """Woven ivory handle with a collar and a glowing droplet pommel."""
    objs = []
    r = 0.016
    bpy.ops.mesh.primitive_cylinder_add(radius=r * 0.82, depth=HANDLE_LEN, location=(0, 0, -HANDLE_LEN / 2))
    core = bpy.context.active_object
    core.name = "Handle_Core"
    core.data.materials.append(ivory)
    objs.append(core)
    for k in range(18):
        phi = 2 * math.pi * k / 18
        omega = rng.uniform(14, 17) * (1 if k % 2 == 0 else -1)
        pts = []
        for i in range(90):
            u = i / 89
            z = -HANDLE_LEN + 0.01 + (HANDLE_LEN - 0.01) * u
            rr = r * (1.02 + 0.06 * math.sin(math.pi * u))
            a = phi + omega * u
            pts.append(Vector((rr * math.cos(a) * 1.1, rr * math.sin(a) * 0.9, z)))
        objs.append(c.curve_tube(f"HandleStrand_{k}", pts, [1.0] * len(pts), ivory, bevel=0.0024, resolution=2))
    # Collar (habaki) where the blade meets the handle.
    bpy.ops.mesh.primitive_cylinder_add(radius=r * 1.25, depth=COLLAR, location=(-0.004, 0, COLLAR / 2))
    collar = bpy.context.active_object
    collar.name = "Collar"
    collar.scale = (1.2, 0.7, 1)
    collar.data.materials.append(ivory)
    bev = collar.modifiers.new("bevel", "BEVEL")
    bev.width = 0.003
    bev.segments = 3
    objs.append(collar)
    # Pommel cap and droplet.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 1.2, location=(0, 0, -HANDLE_LEN))
    cap = bpy.context.active_object
    cap.name = "Pommel"
    cap.scale = (1.1, 0.9, 0.6)
    cap.data.materials.append(ivory)
    bpy.ops.object.shade_smooth()
    objs.append(cap)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.009, segments=32, ring_count=16,
                                         location=(0, 0, -HANDLE_LEN - 0.022))
    drop = bpy.context.active_object
    drop.name = "Pommel_Droplet"
    for v in drop.data.vertices:
        if v.co.z > 0:
            f = v.co.z / 0.009
            v.co.x *= 1 - 0.75 * f
            v.co.y *= 1 - 0.75 * f
            v.co.z *= 1 + 0.9 * f
    drop.data.materials.append(drop_material)
    bpy.ops.object.shade_smooth()
    objs.append(drop)
    return objs


def blade_wrap(ivory, rng):
    """Strands continue from the handle over the collar and hug the blade base,
    splitting into three short tendrils (the trident motif)."""
    objs = []
    for k in range(9):
        phi = 2 * math.pi * k / 9
        prong = k % 3
        pts, radii = [], []
        for i in range(60):
            u = i / 59
            z = -0.02 + 0.11 * u
            s = max(0.0, (z - COLLAR) / BLADE_LEN)
            ctr = blade_center(s) if z > COLLAR else Vector((-0.004, 0, z))
            w, t = blade_profile(s)
            # Wrap tightly around the blade section, spiralling upward.
            a = phi + 5.5 * u
            rx = (w / 2 + 0.004) * (1 - 0.35 * u)
            ry = (t / 2 + 0.004) * (1 - 0.35 * u)
            p = Vector((ctr.x + w / 2 + rx * math.cos(a), ry * math.sin(a), z))
            # Near the top the three prongs peel away slightly.
            peel = smoothstep((u - 0.65) / 0.35)
            p += Vector(((prong - 1) * 0.01 * peel, 0, 0.004 * peel))
            pts.append(p)
            radii.append(1.0 - 0.85 * smoothstep((u - 0.7) / 0.3))
        objs.append(c.curve_tube(f"BladeWrap_{k}", pts, radii, ivory, bevel=0.0024, resolution=2))
    return objs


def tsuba_halo(glow_material, ivory, rng):
    """Floating halo rings in place of a tsuba, with small strand curls inside."""
    objs = []
    z = COLLAR + 0.03
    for name, r, minor, dz in (("Tsuba_Halo", 0.058, 0.0045, 0.0), ("Tsuba_Halo_Inner", 0.044, 0.0018, 0.008)):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=minor, major_segments=96,
                                         minor_segments=12, location=(-0.008, 0, z + dz))
        ring = bpy.context.active_object
        ring.name = name
        ring.data.materials.append(glow_material)
        bpy.ops.object.shade_smooth()
        objs.append(ring)
    return objs


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(8)
    c.reset_scene()
    ivory = c.make_material("Ivory", c.PALETTE["ivory"], roughness=0.32, coat=0.3,
                            emission=c.PALETTE["glow"], strength=0.05, subsurface=0.15)
    glow = c.make_material("Light", c.PALETTE["glow"], roughness=0.1, coat=0.5,
                           emission=c.PALETTE["glow"], strength=1.0)
    blade = blades.blade_material("Blade_Light", 0.5)
    hamon = c.make_material("Hamon", c.PALETTE["blade_core"], roughness=0.1,
                            emission=c.PALETTE["blade_core"], strength=1.2)
    parts = [build_blade(blade)] + hamon_line(hamon) + handle(ivory, glow, rng) + tsuba_halo(glow, ivory, rng)
    parts += blade_wrap(ivory, rng)
    root = c.link(bpy.data.objects.new("LongSword", None))
    for p in parts:
        p.parent = root
    root.rotation_euler = (0, math.radians(-8), 0)

    c.setup_render(samples=32, res=(700, 1000), world_hex="#2E2E33", world_strength=0.5)
    c.add_light("key", "AREA", (0.8, -1.0, 1.0), 80, size=1.0, target=(0, 0, 0.4))
    c.add_light("fill", "AREA", (-1.0, -0.6, 0.4), 30, size=1.0, target=(0, 0, 0.4))
    c.add_light("rim", "AREA", (0.0, 1.0, 1.2), 50, size=0.8, target=(0, 0, 0.4))
    target = (0, 0, 0.36)
    views = [("flat", 0, 4), ("three_quarter", 35, 10), ("edge", 90, 4)]
    studio = c.render_views(OUT, "studio", target, 2.2, views, lens=55)
    close = c.render_views(OUT, "closeup", (-0.02, 0, 0.02), 0.55,
                           [("tsuba", 20, 15), ("tip", 0, 0)], lens=55)
    # The tip close-up re-aims at the kissaki.
    c.contact_sheet(studio + close[:1], os.path.join(OUT, "long_sword_sheet.png"), cols=4)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, "long_sword.blend")))

    c.set_emission_strength(blade, 2.2)
    c.set_emission_strength(hamon, 3.0)
    c.set_emission_strength(glow, 2.5)
    c.setup_render(samples=32, res=(700, 1000), world_hex="#0E0E12", world_strength=0.25, glare=True)
    glow_paths = c.render_views(OUT, "glow", target, 2.2, views[:2], lens=55)
    glow_close = c.render_views(OUT, "glow_closeup", (-0.02, 0, 0.02), 0.55, [("tsuba", 20, 15)], lens=55)
    c.contact_sheet(glow_paths + glow_close, os.path.join(OUT, "long_sword_glow_sheet.png"), cols=3)
    print("DONE", studio + close + glow_paths + glow_close)


if __name__ == "__main__":
    main()
