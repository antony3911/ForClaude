"""Sword & shield prototype: a light sword and an energy shield.

The shield is not a physical object: a floating halo ring frames a faint membrane of
light, and on it glows the tree sigil from Miquella's incantation (reference image 5):
a double-helix trunk with looped knots at the top and bottom, leafy branches spreading
into a rounded crown, and two oval pods at the upper left and right.

The sword reuses the dual blade design with a longer blade.

Shield faces -Y (toward the front camera); x is horizontal, z is vertical.

Usage: python sword_shield.py <out_dir>
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

R = 0.27          # halo radius
FRONT = -0.004    # sigil sits just in front of the membrane
LINE = 0.0021     # sigil line thickness


def p2(x, z, y=FRONT):
    return Vector((x, y, z))


def line(name, pts2d, mat, width=1.0, taper_end=False):
    pts = [p2(x, z) for x, z in pts2d]
    n = len(pts)
    radii = [width * (1 - 0.7 * (i / (n - 1)) ** 2 if taper_end else width) for i in range(n)]
    return c.curve_tube(name, pts, radii, mat, bevel=LINE, resolution=2)


def circle_pts(cx, cz, rx, rz, n=48, start=0.0, sweep=2 * math.pi):
    return [(cx + rx * math.cos(start + sweep * i / (n - 1)), cz + rz * math.sin(start + sweep * i / (n - 1)))
            for i in range(n)]


def knot(name, cx, cz, r, mat):
    """Looped knot: a ring with two bowed strands crossing inside."""
    objs = [line(f"{name}_ring", circle_pts(cx, cz, r, r), mat)]
    for sgn in (-1, 1):
        pts = []
        for i in range(30):
            t = i / 29
            d = 2 * t - 1                     # -1 .. 1 along the diagonal
            bow = 0.18 * r * math.cos(math.pi * d / 2)
            pts.append((cx + sgn * 0.68 * r * d - sgn * bow, cz + 0.68 * r * d + bow))
        objs.append(line(f"{name}_x{sgn}", pts, mat, 0.8))
    return objs


def trunk(mat):
    """Two strands braided into a chain of lens-shaped loops from bottom knot to top knot."""
    objs = []
    z0, z1 = -0.175, 0.15
    for sgn in (-1, 1):
        pts = []
        for i in range(160):
            t = i / 159
            z = z0 + (z1 - z0) * t
            # Wider elongated loop in the middle of the trunk.
            amp = 0.011 + 0.008 * math.exp(-((z - 0.0) / 0.035) ** 2)
            pts.append((sgn * amp * math.sin(2 * math.pi * 3.5 * t), z))
        objs.append(line(f"Trunk_{sgn}", pts, mat, 1.15))
    objs += knot("KnotTop", 0.0, 0.18, 0.03, mat)
    objs += knot("KnotBottom", 0.0, -0.205, 0.028, mat)
    # A smaller loop pair just above the bottom knot, like a figure eight.
    objs.append(line("LoopLow", circle_pts(0.0, -0.155, 0.014, 0.02), mat, 0.9))
    return objs


class LeafBuilder:
    """Collects many small leaf shapes into one glowing mesh."""

    def __init__(self):
        self.bm = bmesh.new()

    def add(self, x, z, angle, length=0.017, width=0.0065):
        n = 12
        verts = []
        for i in range(n):
            t = i / n * 2 * math.pi
            # Pointed leaf outline along its local +u axis.
            u = length / 2 * math.cos(t)
            v = width / 2 * math.sin(t) * (1 - 0.35 * math.cos(t))
            ca, sa = math.cos(angle), math.sin(angle)
            lx = x + (u + length / 2) * ca - v * sa
            lz = z + (u + length / 2) * sa + v * ca
            verts.append(self.bm.verts.new((lx, FRONT, lz)))
        self.bm.faces.new(verts)

    def finish(self, mat):
        mesh = bpy.data.meshes.new("leaves")
        self.bm.to_mesh(mesh)
        self.bm.free()
        obj = c.link(bpy.data.objects.new("Sigil_Leaves", mesh))
        obj.data.materials.append(mat)
        solid = obj.modifiers.new("thick", "SOLIDIFY")
        solid.thickness = 0.0012
        return obj


def branch(name, start, direction, length, curve, mat, leaves, rng, depth):
    """A twig that bends gently, sprouting leaf pairs and smaller twigs."""
    objs = []
    pts = []
    x, z = start
    ang = math.atan2(direction[1], direction[0])
    n = 26
    step = length / n
    for i in range(n + 1):
        pts.append((x, z))
        t = i / n
        ang += curve * step * 30
        x += step * math.cos(ang)
        z += step * math.sin(ang)
        # Leaf pairs along the twig.
        if i > 3 and i % 5 == 0:
            for side in (-1, 1):
                leaves.add(x, z, ang + side * math.radians(rng.uniform(35, 55)),
                           length=0.012 * (1 - 0.3 * t), width=0.0045 * (1 - 0.3 * t))
    objs.append(line(name, pts, mat, 1.0 if depth == 0 else 0.8, taper_end=True))
    # End leaf.
    leaves.add(x, z, ang, length=0.013, width=0.005)
    mirror = 1 if direction[0] >= 0 else -1
    if depth < 1:
        for frac, turn in ((0.45, mirror), (0.72, -mirror)):
            i = int(n * frac)
            bx, bz = pts[i]
            ba = math.atan2(pts[i + 1][1] - bz, pts[i + 1][0] - bx) + turn * math.radians(rng.uniform(30, 50))
            objs += branch(f"{name}_{i}", (bx, bz), (math.cos(ba), math.sin(ba)),
                           length * rng.uniform(0.38, 0.5), curve * 0.6 - turn * 0.02,
                           mat, leaves, rng, depth + 1)
    return objs


def crown(mat, leaves, rng):
    """Branches leaving the trunk on both sides, forming a rounded crown."""
    objs = []
    specs = (  # height, angle (deg from horizontal), length, curvature (droop)
        (0.06, 62, 0.13, -0.16),
        (0.025, 42, 0.16, -0.14),
        (-0.015, 22, 0.16, -0.13),
        (-0.055, 5, 0.12, -0.12),
    )
    for sgn in (-1, 1):
        for k, (z, deg, length, curve) in enumerate(specs):
            a = math.radians(deg)
            d = (sgn * math.cos(a), math.sin(a))
            objs += branch(f"Branch_{sgn}_{k}", (sgn * 0.01, z), d, length, curve * sgn,
                           mat, leaves, rng, 0)
    return objs


def pods(mat):
    """Oval pods with a criss-cross inside, at the upper left and right."""
    objs = []
    for sgn in (-1, 1):
        cx, cz = sgn * 0.125, 0.145
        objs.append(line(f"Pod_{sgn}", circle_pts(cx, cz, 0.018, 0.028), mat))
        for k in (-1, 1):
            pts = [(cx + k * 0.012 * math.sin(math.pi * t) * (1 - 2 * t) + 0.0, cz - 0.026 + 0.052 * t)
                   for t in [i / 19 for i in range(20)]]
            objs.append(line(f"Pod_{sgn}_x{k}", pts, mat, 0.7))
        # Stem joining the pod to the crown.
        stem = [(sgn * (0.07 + 0.05 * t), 0.09 + 0.03 * t + 0.01 * math.sin(math.pi * t)) for t in [i / 15 for i in range(16)]]
        objs.append(line(f"PodStem_{sgn}", stem, mat, 0.8))
    return objs


def shield(glow_mat, membrane_mat, ivory):
    objs = []
    rng = random.Random(9)
    # Halo ring and a thinner inner ring.
    for name, r, minor, y in (("Shield_Halo", R, 0.009, 0.0), ("Shield_Halo_Inner", R - 0.022, 0.0028, -0.002)):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=minor, major_segments=128,
                                         minor_segments=16, location=(0, y, 0), rotation=(math.pi / 2, 0, 0))
        ring = bpy.context.active_object
        ring.name = name
        ring.data.materials.append(glow_mat)
        bpy.ops.object.shade_smooth()
        objs.append(ring)
    # Faint membrane of light.
    bpy.ops.mesh.primitive_cylinder_add(radius=R - 0.004, depth=0.002, vertices=128,
                                        location=(0, 0.001, 0), rotation=(math.pi / 2, 0, 0))
    disc = bpy.context.active_object
    disc.name = "Shield_Membrane"
    disc.data.materials.append(membrane_mat)
    objs.append(disc)
    # Sigil.
    leaves = LeafBuilder()
    objs += trunk(glow_mat)
    objs += crown(glow_mat, leaves, rng)
    objs += pods(glow_mat)
    objs.append(leaves.finish(glow_mat))
    root = c.link(bpy.data.objects.new("EnergyShield", None))
    for o in objs:
        o.parent = root
    return root


def membrane_material(strength):
    """Energy membrane: mostly transparent, glowing gold, brighter toward the rim."""
    mat = bpy.data.materials.new("Membrane")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    emission = nodes.new("ShaderNodeEmission")
    emission.name = "Membrane_Emission"
    emission.inputs["Color"].default_value = c.hex_to_linear(c.PALETTE["glow"])
    emission.inputs["Strength"].default_value = strength
    # Radial falloff: distance from the shield center in object space.
    coords = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / R, 1 / R, 1 / R)
    gradient = nodes.new("ShaderNodeTexGradient")
    gradient.gradient_type = "SPHERICAL"
    ramp = nodes.new("ShaderNodeValToRGB")
    # Spherical gradient is 1 at the center, 0 at the rim: faint center, stronger rim.
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.3, 0.3, 0.3, 1)
    ramp.color_ramp.elements[1].position = 0.38
    ramp.color_ramp.elements[1].color = (0.03, 0.03, 0.03, 1)
    links.new(coords.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], gradient.inputs["Vector"])
    links.new(gradient.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def set_membrane_strength(mat, strength):
    mat.node_tree.nodes["Membrane_Emission"].inputs["Strength"].default_value = strength


def add_backdrop():
    """Textured wall behind the set so the shield's transparency reads."""
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0.7, 0.4), rotation=(math.pi / 2, 0, 0))
    wall = bpy.context.active_object
    wall.name = "Backdrop"
    mat = bpy.data.materials.new("Backdrop")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    brick = nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 6
    brick.inputs["Color1"].default_value = c.hex_to_linear("#5A5650")
    brick.inputs["Color2"].default_value = c.hex_to_linear("#46423D")
    brick.inputs["Mortar"].default_value = c.hex_to_linear("#2A2826")
    links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
    wall.data.materials.append(mat)
    return wall


def main():
    os.makedirs(OUT, exist_ok=True)
    c.reset_scene()
    ivory = c.make_material("Ivory", c.PALETTE["ivory"], roughness=0.32, coat=0.3,
                            emission=c.PALETTE["glow"], strength=0.05, subsurface=0.15)
    glow = c.make_material("Sigil_Light", c.PALETTE["blade_core"], roughness=0.1,
                           emission=c.PALETTE["blade_core"], strength=1.2)
    membrane = membrane_material(0.6)
    shield_root = shield(glow, membrane, ivory)
    shield_root.location = (0.2, 0, 0.45)
    add_backdrop()

    # Sword: the dual blade design with a longer blade.
    blades.BLADE_LEN = 0.72
    blade_mat = blades.blade_material("Blade_Light", 0.35)
    core = c.make_material("Blade_Core", c.PALETTE["blade_core"], roughness=0.1,
                           emission=c.PALETTE["blade_core"], strength=0.8)
    drop = c.make_material("Droplet", c.PALETTE["glow"], roughness=0.08, coat=0.6,
                           emission=c.PALETTE["glow"], strength=1.5)
    sword = blades.build_sword("Sword", ivory, drop, blade_mat, core, seed=4)
    sword.location = (-0.28, 0, 0.0)
    sword.rotation_euler = (0, math.radians(-6), 0)

    c.setup_render(samples=40, res=(1000, 900), world_hex="#2E2E33", world_strength=0.5)
    c.add_light("key", "AREA", (0.8, -1.0, 1.0), 70, size=1.0, target=(0, 0, 0.4))
    c.add_light("fill", "AREA", (-1.0, -0.6, 0.4), 25, size=1.0, target=(0, 0, 0.4))
    c.add_light("rim", "AREA", (0.0, 1.0, 1.0), 40, size=0.8, target=(0, 0, 0.4))
    studio = c.render_views(OUT, "studio", (0, 0, 0.42), 1.9, [("set_front", 0, 4), ("set_three_quarter", 30, 10)], lens=55)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, "sword_shield.blend")))

    # Glow look, with a close-up of the shield sigil.
    c.set_emission_strength(glow, 2.5)
    set_membrane_strength(membrane, 1.2)
    c.set_emission_strength(blade_mat, 2.2)
    c.set_emission_strength(core, 3.0)
    c.set_emission_strength(drop, 3.0)
    c.setup_render(samples=40, res=(1000, 900), world_hex="#0E0E12", world_strength=0.25, glare=True)
    glow_paths = c.render_views(OUT, "glow", (0, 0, 0.42), 1.9, [("set_front", 0, 4), ("set_three_quarter", 30, 10)], lens=55)
    sigil = c.render_views(OUT, "glow", (0.2, 0, 0.45), 0.85, [("shield_close", 0, 0), ("shield_angle", 40, 12)], lens=55)
    c.contact_sheet(studio + glow_paths, os.path.join(OUT, "sns_sheet.png"), cols=2)
    c.contact_sheet(sigil, os.path.join(OUT, "shield_sigil_sheet.png"), cols=2)
    print("DONE", studio + glow_paths + sigil)


if __name__ == "__main__":
    main()
