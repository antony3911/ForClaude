"""Weapon devices: things a weapon leaves on or around the monster, redesigned in the
Miquella style (the user asked: "this device has to change too").

  wyrmstake   gunlance Wyrmstake Cannon -> Miquella's Unalloyed Gold Needle: a slender
              needle of pure gold whose eye is a loop of twisted gold wire with small
              scrolls, light glowing inside. Drilled into the monster, it cracks the hide
              with gold light, bursts in rings and flares along its shaft, then blows.

Usage: python devices.py <set> <out_dir>
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as c
import motifs as m
from motifs import V

SET = sys.argv[1] if len(sys.argv) > 1 else "wyrmstake"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join("out", SET)
sys.argv = ["states.py", SET, OUT]          # states reads its own argv on import
import particle_fx as pf                     # noqa: E402
import states as st                          # noqa: E402


def gold_material(name="Unalloyed_Gold"):
    """Pure gold metal with a faint warmth from inside."""
    mat = c.make_material(name, "#E8B84E", roughness=0.22, metallic=1.0, emission="#FFB445", strength=0.08)
    return mat


def needle(mats, length=0.5, base=V(0, 0, 0), direction=V(0, 0, 1)):
    """The Unalloyed Gold Needle, point at `base`, eye at the far end along `direction`."""
    d = direction.normalized()
    side = d.orthogonal().normalized()
    gold = mats["gold"]
    objs = []
    # Shaft: round, swelling slightly toward the eye, a fine point.
    pts = [base + d * length * (i / 60) for i in range(61)]
    radii = [max(0.06, (i / 60) ** 0.45) for i in range(61)]
    objs.append(c.curve_tube("Needle_Shaft", pts[:52], radii[:52], gold, bevel=0.007, resolution=6))
    # Eye: two strands of gold wire twisted into an oval loop at the top.
    top = base + d * length * 0.86
    eye_h, eye_w = length * 0.13, length * 0.035
    for k in range(2):
        loop = []
        for i in range(121):
            t = i / 120
            a = 2 * math.pi * t
            twist = 0.0025 * math.sin(2 * math.pi * 9 * t + k * math.pi)
            loop.append(top + d * (eye_h / 2 * (1 - math.cos(a))) + side * ((eye_w + twist) * math.sin(a))
                        + d.cross(side) * twist)
        objs.append(c.curve_tube(f"Needle_Eye_{k}", loop, [1.0] * len(loop), gold, bevel=0.0026, resolution=4))
    # Light inside the eye, and small scrolls of gold wire curling off its shoulders.
    objs += m.droplet("Needle_Light", top + d * eye_h * 0.5, 0.009, d, mats["light"], stretch=1.6)
    plane = m.plane_mapper(top + d * eye_h * 0.15, side, d)
    for s in (-1, 1):
        objs += m.tendril(f"Needle_Scroll_{s}", plane, (s * eye_w * 0.9, 0), 90 - s * 70, length * 0.07,
                          s * -1.4, 0.0018, {"ivory": gold, "light": mats["light"]}, strands=2, gold=False,
                          strand_mat="ivory", curl_start=0.3)
    # A collar where the shaft meets the eye.
    objs += m.halo("Needle_Collar", top - d * 0.004, 0.0105, 0.0022, d, gold)
    return objs


def hide_block():
    """A slab of monster hide to show the needle driven in: dark, scaled, rough."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.0, -0.2))
    block = bpy.context.active_object
    block.name = "Hide"
    block.scale = (0.9, 0.5, 0.4)
    mat = bpy.data.materials.new("Hide_Mat")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.7
    cells = nodes.new("ShaderNodeTexVoronoi")
    cells.inputs["Scale"].default_value = 26.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = c.hex_to_linear("#1A1210")
    ramp.color_ramp.elements[1].color = c.hex_to_linear("#4A3428")
    links.new(cells.outputs["Distance"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    links.new(cells.outputs["Distance"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    block.data.materials.append(mat)
    return block


def wyrmstake():
    c.reset_scene()
    mats = m.materials()
    mats["gold"] = gold_material()
    m.glow_mode(mats)
    target_free, dist_free = V(0, 0, 0.28), 0.9
    # 1. The needle itself.
    nd = needle(mats, 0.5, V(0, 0, 0.03), V(0, 0, 1))
    st.stage_lights((0, 0, 0.2), 1.2, res=(600, 900))
    paths = c.render_views(OUT, "needle", target_free, dist_free, [("front", 20, 8)], lens=50)
    close = c.render_views(OUT, "needle_eye", V(0, 0, 0.5), 0.3, [("eye", 25, 10)], lens=50)
    for o in nd:
        bpy.data.objects.remove(o, do_unlink=True)
    # 2-4. Driven into the hide at an angle; then bursts.
    hide = hide_block()
    entry = V(0.0, 0.0, 0.0)
    tilt = V(0.35, 0.0, 1.0).normalized()
    nd = needle(mats, 0.5, entry - tilt * 0.17, tilt)
    glow = c.make_material("Crack_Light", c.PALETTE["glow"], roughness=0.2, emission=c.PALETTE["glow"], strength=6.0)
    # Hairline cracks of gold light on the hide's top face (z = 0), running out from the wound.
    rng = random.Random(4)
    crack_objs = []
    for k in range(10):
        heading = rng.uniform(0, 2 * math.pi)
        p = entry.copy()
        pts = [p.copy()]
        for i in range(12):
            heading += rng.uniform(-0.45, 0.45)
            p = p + V(math.cos(heading), math.sin(heading), 0) * 0.011
            pts.append(p.copy())
        crack_objs.append(c.curve_tube(f"Crack_{k}", pts, [1 - 0.9 * i / 12 for i in range(13)], glow,
                                       bevel=0.0016, resolution=1))
    rings = []
    for k, (u, r) in enumerate(((0.12, 0.035), (0.22, 0.05), (0.32, 0.065))):
        rings += m.halo(f"Burst_Ring_{k}", entry + tilt * (u - 0.17), r, 0.0028, tilt, mats["light"])
    small_burst = pf.burst_strands("Burst_Small", entry + V(0, 0, 0.02), 0.03, count=140, strength=1.3)
    big_burst = pf.burst_strands("Burst_Big", entry + V(0, 0, 0.05), 0.08, count=260, strength=1.5, seed=9)
    shock = []
    for k, (r, minor) in enumerate(((0.16, 0.004), (0.22, 0.003), (0.29, 0.002))):
        shock += m.halo(f"Shock_{k}", entry + V(0, 0, 0.004), r, minor, (0, 0, 1), mats["light"])
    target, distance = V(0.02, 0, 0.12), 1.0
    states = [("刺入：皮上裂出金光", True, False, False, False), ("連續爆裂：光環和光焰", True, True, True, False),
              ("最後爆炸", False, False, False, True)]
    for i, (label, cr, rg, small, big) in enumerate(states):
        st.show(crack_objs, cr)
        st.show(rings, rg)
        st.show(small_burst, small)
        st.show(big_burst + shock, big)
        st.show(nd, not big)
        paths += c.render_views(OUT, f"state{i}", target, distance, [("front", 15, 18)], lens=50)
    st.labelled_strip(paths, ["龍杭＝未鍛金之針"] + [s[0] for s in states], os.path.join(OUT, "wyrmstake.png"),
                      "銃槍龍杭砲：杭改成米凱拉的未鍛金之針")
    st.labelled_strip(close, ["針眼特寫"], os.path.join(OUT, "wyrmstake_eye.png"), "未鍛金之針：針眼")


SETS = {"wyrmstake": wyrmstake}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    SETS[SET]()
    print("DONE", flush=True)
