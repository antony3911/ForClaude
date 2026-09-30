"""Dual light-blade prototype.

Ivory grip made of intertwined strands (same language as the circlet), a guard where
the strands split trident-like and curl toward the blade, a glowing droplet pommel, and
an emissive white-gold blade with a brighter core line. See DESIGN.md section 5.

Usage: python blades.py <out_dir>
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as c

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"

GRIP_BOTTOM = 0.0
GUARD_Z = 0.16
BLADE_LEN = 0.62
BLADE_W = 0.056     # max width
BLADE_T = 0.009     # max thickness


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def blade_material(name, strength):
    """Emissive blade: bright core facing the viewer, warmer gold toward glancing edges."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = c.hex_to_linear(c.PALETTE["blade_core"])
    bsdf.inputs["Roughness"].default_value = 0.15
    bsdf.inputs["Coat Weight"].default_value = 0.5
    lw = nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = c.hex_to_linear(c.PALETTE["blade_core"])
    ramp.color_ramp.elements[1].color = c.hex_to_linear(c.PALETTE["blade_edge"])
    links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def build_blade(material):
    """Leaf-like straight blade with a lens cross-section, lofted along +Z."""
    mesh = bpy.data.meshes.new("blade")
    bm = bmesh.new()
    rings = []
    n_len, n_sec = 80, 12
    for i in range(n_len + 1):
        u = i / n_len
        z = GUARD_Z + 0.004 + BLADE_LEN * u
        # Slight swell at a third of the length, long elegant taper to the point.
        width = BLADE_W * (0.85 + 0.25 * math.sin(math.pi * min(u / 0.5, 1.0) * 0.5)) * (1 - u ** 3.2)
        width = max(width, 0.0004)
        thick = BLADE_T * (1 - 0.6 * u) * (1 - u ** 3)
        thick = max(thick, 0.0003)
        ring = []
        for j in range(n_sec):
            a = 2 * math.pi * j / n_sec
            x = width / 2 * math.cos(a)
            # Lens profile: thickest at the center line, sharp edges.
            y = thick / 2 * math.sin(a) * (1 - abs(math.cos(a)) ** 3) ** 0.5
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    for i in range(n_len):
        for j in range(n_sec):
            k = (j + 1) % n_sec
            bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.to_mesh(mesh)
    bm.free()
    obj = c.link(bpy.data.objects.new("Blade", mesh))
    obj.data.materials.append(material)
    sub = obj.modifiers.new("smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def core_line(material):
    """Brighter fuller line running up both faces of the blade."""
    objs = []
    for face in (-1, 1):
        pts, radii = [], []
        for i in range(40):
            u = i / 39 * 0.82
            z = GUARD_Z + 0.01 + BLADE_LEN * u
            thick = BLADE_T * (1 - 0.6 * u) * (1 - u ** 3)
            pts.append(Vector((0, face * thick / 2 * 0.92, z)))
            radii.append(1.0 - 0.8 * u)
        objs.append(c.curve_tube(f"Core_{face}", pts, radii, material, bevel=0.0016, resolution=2))
    return objs


def grip_and_guard(material, drop_material, rng):
    """Strand-wrapped grip; at the guard the strands split into three curling prongs."""
    objs = []
    n_strands = 16
    grip_r = 0.0135
    prongs = (  # direction in XZ plane (deg from +Z toward +X), length, curl sign
        (72, 0.075, 1), (0, 0.09, 0), (-72, 0.075, -1))
    # Solid core so the woven strands never show gaps.
    bpy.ops.mesh.primitive_cylinder_add(radius=grip_r * 0.82, depth=GUARD_Z - 0.01,
                                        location=(0, 0, (GUARD_Z + 0.01) / 2))
    core_cyl = bpy.context.active_object
    core_cyl.name = "Grip_Core"
    core_cyl.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    objs.append(core_cyl)
    for k in range(n_strands):
        phi = 2 * math.pi * k / n_strands + rng.uniform(-0.2, 0.2)
        omega = rng.uniform(8, 11) * (1 if k % 2 == 0 else -1)   # weave
        prong = k % 3
        pts, radii = [], []
        # Grip: helix from pommel to guard.
        for i in range(50):
            u = i / 49
            z = GRIP_BOTTOM + 0.012 + (GUARD_Z - 0.012) * u
            r = grip_r * (1.08 - 0.12 * math.sin(math.pi * u)) * rng.uniform(0.97, 1.03)
            a = phi + omega * u
            pts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
            radii.append(1.0)
        # Guard: strands gather into their prong and sweep out/up with a curl.
        ang_deg, length, curl = prongs[prong]
        d = Vector((math.sin(math.radians(ang_deg)), 0, math.cos(math.radians(ang_deg))))
        start = pts[-1].copy()
        a_end = phi + omega
        for i in range(1, 46):
            v = i / 45
            center = Vector((0, 0, GUARD_Z)) + d * (length * v)
            # Center prong wraps the blade base instead of leaving it.
            if prong == 1:
                center = Vector((0, 0, GUARD_Z + length * v))
            # Curl the side prongs back toward the blade near their tips.
            if curl:
                bend = smoothstep((v - 0.45) / 0.55)
                center += Vector((-curl * 0.03 * bend, 0, 0.022 * bend))
            a = a_end + 7 * v
            spread = 0.0045 * (1 - 0.6 * v) if prong != 1 else (BLADE_W * 0.45 + 0.002) * (1 - 0.7 * v)
            y_scale = 1.0 if prong != 1 else 0.3
            offset = Vector((spread * math.cos(a), spread * y_scale * math.sin(a), 0))
            w = smoothstep(v / 0.25)
            p = start * (1 - w) + (center + offset) * w
            pts.append(p)
            radii.append(1.0 - 0.85 * smoothstep((v - 0.6) / 0.4))
        objs.append(c.curve_tube(f"Strand_{k}", pts, radii, material, bevel=0.0028, resolution=3))
    # Collar where the strands gather under the guard.
    bpy.ops.mesh.primitive_torus_add(major_radius=grip_r + 0.002, minor_radius=0.0032,
                                     location=(0, 0, GUARD_Z - 0.006))
    collar = bpy.context.active_object
    collar.name = "Guard_Collar"
    collar.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    objs.append(collar)
    # Pommel: a small cap and a glowing droplet hanging below, echoing the circlet.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=grip_r * 1.25, location=(0, 0, GRIP_BOTTOM + 0.006))
    cap = bpy.context.active_object
    cap.name = "Pommel_Cap"
    cap.scale = (1, 1, 0.55)
    cap.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    objs.append(cap)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0085, segments=32, ring_count=16,
                                         location=(0, 0, GRIP_BOTTOM - 0.016))
    drop = bpy.context.active_object
    drop.name = "Pommel_Droplet"
    for v in drop.data.vertices:
        if v.co.z > 0:
            f = v.co.z / 0.0085
            v.co.x *= 1 - 0.75 * f
            v.co.y *= 1 - 0.75 * f
            v.co.z *= 1 + 0.9 * f
    drop.data.materials.append(drop_material)
    bpy.ops.object.shade_smooth()
    objs.append(drop)
    return objs


def build_sword(name, ivory, drop_mat, blade_mat, core_mat, seed):
    rng = random.Random(seed)
    parts = [build_blade(blade_mat)] + core_line(core_mat) + grip_and_guard(ivory, drop_mat, rng)
    root = c.link(bpy.data.objects.new(name, None))
    for p in parts:
        p.parent = root
    return root


def main():
    os.makedirs(OUT, exist_ok=True)
    c.reset_scene()
    ivory = c.make_material("Ivory", c.PALETTE["ivory"], roughness=0.32, coat=0.3,
                            emission=c.PALETTE["glow"], strength=0.05, subsurface=0.15)
    drop = c.make_material("Droplet", c.PALETTE["glow"], roughness=0.08, coat=0.6,
                           emission=c.PALETTE["glow"], strength=1.5)
    blade = blade_material("Blade_Light", 0.35)
    core = c.make_material("Blade_Core", c.PALETTE["blade_core"], roughness=0.1,
                           emission=c.PALETTE["blade_core"], strength=0.8)

    left = build_sword("DualBlade_L", ivory, drop, blade, core, seed=3)
    right = build_sword("DualBlade_R", ivory, drop, blade, core, seed=3)
    # Mirror the right sword so the pair is symmetric.
    right.scale = (-1, 1, 1)
    left.location = (-0.07, 0, 0)
    right.location = (0.07, 0, 0)
    left.rotation_euler = (0, math.radians(-4), 0)
    right.rotation_euler = (0, math.radians(4), 0)

    # Ground-ish backdrop so the glow reads.
    c.setup_render(samples=32, res=(640, 900), world_hex="#2E2E33", world_strength=0.5)
    c.add_light("key", "AREA", (0.6, -0.8, 0.8), 60, size=0.8, target=(0, 0, 0.4))
    c.add_light("fill", "AREA", (-0.8, -0.5, 0.3), 20, size=0.8, target=(0, 0, 0.4))
    c.add_light("rim", "AREA", (0.0, 0.8, 0.9), 40, size=0.6, target=(0, 0, 0.4))
    target = (0, 0, 0.38)
    views = [("pair_front", 0, 5), ("pair_three_quarter", 35, 12), ("pair_edge", 90, 5)]
    studio = c.render_views(OUT, "studio", target, 1.55, views, lens=60)
    # Close-up of the grip and guard.
    close = c.render_views(OUT, "closeup", (0.07, 0, 0.13), 0.42,
                           [("guard_front", 10, 8), ("guard_three_quarter", 45, 20)], lens=60)
    c.contact_sheet(studio + close, os.path.join(OUT, "blades_studio_sheet.png"), cols=5)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, "dual_blades.blend")))

    # Glow look.
    c.set_emission_strength(blade, 3.0)
    c.set_emission_strength(core, 7.0)
    c.set_emission_strength(drop, 5.0)
    c.setup_render(samples=32, res=(640, 900), world_hex="#0E0E12", world_strength=0.25, glare=True)
    glow = c.render_views(OUT, "glow", target, 1.55, [views[0], views[1]], lens=60)
    c.contact_sheet(glow, os.path.join(OUT, "blades_glow_sheet.png"), cols=2)
    print("DONE", studio + close + glow)


main()
