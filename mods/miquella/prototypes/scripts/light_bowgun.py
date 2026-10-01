"""Light bowgun prototype: no physical barrel, only a thin beam of light running through
a rail of floating halo rings that shrink toward the muzzle.

Reuses the heavy bowgun's woven body with slimmer proportions. See DESIGN.md section 5.

Axes: +Y is the muzzle direction, +Z is up.

Usage: python light_bowgun.py <out_dir>
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as c
import bowgun as hb

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"

# Slimmer, shorter frame than the heavy bowgun.
hb.STOCK_END = -0.40
hb.WRIST = -0.13
hb.RECEIVER_END = 0.06
hb.MUZZLE = 0.52
hb.CONDUIT_R = 0.011
hb.CONDUIT_Z = 0.022


def slim_section(y):
    """Center and half-sizes of the light bowgun body at y."""
    if y < hb.WRIST:
        u = (y - hb.STOCK_END) / (hb.WRIST - hb.STOCK_END)
        cz = -0.04 * (1 - u) ** 1.3
        rz = 0.07 * (1 - u) + 0.03 * u
        rx = 0.024 + 0.004 * (1 - u)
    else:
        u = (y - hb.WRIST) / (hb.RECEIVER_END - hb.WRIST)
        cz = 0.01 * math.sin(math.pi * u)
        rz = 0.03 + 0.022 * math.sin(math.pi * min(1.0, u * 1.3))
        rx = 0.026 + 0.014 * math.sin(math.pi * min(1.0, u * 1.2))
    return Vector((0, y, cz)), rx, rz


hb.body_section = slim_section


def branch_center_slim(b, v):
    """Three thin strand branches reaching only part-way along the beam."""
    base_angle = math.radians(90 + 120 * b)
    angle = base_angle + math.radians(100) * v
    r = hb.CONDUIT_R + 0.012 + 0.004 * math.sin(math.pi * v)
    y = hb.RECEIVER_END - 0.02 + 0.22 * v
    return Vector((r * math.cos(angle), y, hb.CONDUIT_Z + r * math.sin(angle)))


hb.branch_center = branch_center_slim


def halo_rail(glow_mat):
    """Floating rings along the beam, shrinking toward the muzzle, gently tilted."""
    objs = []
    start = hb.RECEIVER_END + 0.24
    n = 4
    for i in range(n):
        t = i / (n - 1)
        y = start + (hb.MUZZLE - 0.04 - start) * t
        r = 0.07 - 0.022 * t
        tilt = math.radians(4 if i % 2 == 0 else -4)
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.0042 - 0.001 * t,
                                         major_segments=96, minor_segments=12,
                                         location=(0, y, hb.CONDUIT_Z),
                                         rotation=(math.pi / 2 + tilt, 0, tilt * 0.6))
        ring = bpy.context.active_object
        ring.name = f"Rail_Halo_{i}"
        ring.data.materials.append(glow_mat)
        bpy.ops.object.shade_smooth()
        objs.append(ring)
    # Double halo at the muzzle.
    bpy.ops.mesh.primitive_torus_add(major_radius=0.062, minor_radius=0.0055, major_segments=96,
                                     minor_segments=12, location=(0, hb.MUZZLE + 0.01, hb.CONDUIT_Z),
                                     rotation=(math.pi / 2, 0, 0))
    muzzle = bpy.context.active_object
    muzzle.name = "Muzzle_Halo"
    muzzle.data.materials.append(glow_mat)
    bpy.ops.object.shade_smooth()
    objs.append(muzzle)
    return objs


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(12)
    c.reset_scene()
    ivory = c.make_material("Ivory", c.PALETTE["ivory"], roughness=0.32, coat=0.3,
                            emission=c.PALETTE["glow"], strength=0.05, subsurface=0.15)
    glow = c.make_material("Light", c.PALETTE["glow"], roughness=0.1, coat=0.5,
                           emission=c.PALETTE["glow"], strength=1.0)
    beam = c.make_material("Beam", c.PALETTE["blade_core"], roughness=0.1,
                           emission=c.PALETTE["blade_core"], strength=1.2)
    parts = [hb.loft_body(ivory)]
    parts += hb.woven_strands(ivory, rng)
    parts += hb.pistol_grip(ivory, rng)
    parts += hb.conduit(beam)
    parts += hb.energy_core(glow, ivory)
    parts += halo_rail(glow)
    parts += hb.barrel_phials({"light": glow}, ys=(0.1, 0.17, 0.24), z=hb.CONDUIT_Z + 0.075, size=0.013)
    # Adapt heavy-bowgun parts to the slimmer frame.
    for obj in parts:
        if obj.name == "Light_Conduit":
            obj.modifiers["bevel"].width = 0.003
        if obj.name == "Energy_Core" or obj.name.startswith("Cradle_"):
            obj.scale = (0.75, 0.75, 0.75)
            obj.location = (obj.location.x * 0.75, obj.location.y * 0.75 + 0.01, obj.location.z * 0.75 - 0.012)

    c.setup_render(samples=32, res=(900, 600), world_hex="#2E2E33", world_strength=0.5)
    c.add_light("key", "AREA", (1.0, -0.6, 1.0), 100, size=1.0, target=(0, 0.1, 0))
    c.add_light("fill", "AREA", (-1.0, 0.2, 0.4), 35, size=1.0, target=(0, 0.1, 0))
    c.add_light("rim", "AREA", (0.0, 1.4, 0.9), 60, size=0.8, target=(0, 0.1, 0))
    target = (0, 0.12, 0.01)
    views = [("side", 90, 4), ("front_three_quarter", 140, 18), ("back_three_quarter", 45, 20),
             ("muzzle", 172, 6)]
    studio = c.render_views(OUT, "studio", target, 1.75, views, lens=50)
    c.contact_sheet(studio, os.path.join(OUT, "light_bowgun_sheet.png"), cols=2)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, "light_bowgun.blend")))

    c.set_emission_strength(glow, 2.5)
    c.set_emission_strength(beam, 3.0)
    c.setup_render(samples=32, res=(900, 600), world_hex="#0E0E12", world_strength=0.25, glare=True)
    glow_paths = c.render_views(OUT, "glow", target, 1.75, [views[0], views[1]], lens=50)
    c.contact_sheet(glow_paths, os.path.join(OUT, "light_bowgun_glow_sheet.png"), cols=2)
    print("DONE", studio + glow_paths)


if __name__ == "__main__":
    main()
