"""Weapon devices: things a weapon leaves on or around the monster, redesigned in the
Miquella style (the user asked: "this device has to change too").

  wyrmstake   gunlance Wyrmstake Cannon -> Miquella's Unalloyed Gold Needle: a slender
              needle of pure gold whose eye is a loop of twisted gold wire with small
              scrolls, light glowing inside. Drilled into the monster, it cracks the hide
              with gold light, bursts in rings and flares along its shaft, then blows.

  wyvernpiercer  heavy bowgun -> a small gold thorn that buries itself, light leaking from
                 the wound, then bursting out of it
  wyvernblast    light bowgun mine -> an ivory flower bud holding a light; struck, its
                 petals open and it bursts
  tracer         bow tracer arrow -> where it sticks, a small tree-sigil ring floats up and
                 the other arrows of light curve in toward it; enough hits and it bursts
  echo_bubble    hunting horn -> a ring of light on the ground and a gilded bubble floating
                 above it, which pulses out rings when an attack lands inside

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


# ------------------------------------------------------------------ heavy bowgun: wyvernpiercer

def thorn(mats, length, tip, direction, name="Thorn"):
    """A gold thorn round: a slim cone with spiral grooves of light, three small gold
    scrolls at its tail like fletching, and a drop of light in the tail."""
    d = direction.normalized()
    side = d.orthogonal().normalized()
    up = d.cross(side)
    objs = []
    pts = [tip - d * length * (i / 40) for i in range(41)]
    radii = [0.08 + 0.92 * (i / 40) ** 0.7 for i in range(41)]
    objs.append(c.curve_tube(f"{name}_Body", pts, radii, mats["gold"], bevel=length * 0.06, resolution=6))
    groove = []
    for i in range(80):
        t = i / 79
        r = length * 0.06 * (0.08 + 0.92 * t ** 0.7) + 0.0006
        a = 2 * math.pi * 2.5 * t
        groove.append(tip - d * length * t * 0.92 + (side * math.cos(a) + up * math.sin(a)) * r)
    objs.append(c.curve_tube(f"{name}_Groove", groove, [1.0] * 80, mats["light"], bevel=0.0009, resolution=2))
    tail = tip - d * length
    for k in range(3):
        a = 2 * math.pi * k / 3
        out = side * math.cos(a) + up * math.sin(a)
        plane = m.plane_mapper(tail + d * length * 0.12, -d, out)
        objs += m.tendril(f"{name}_Fin_{k}", plane, (0, length * 0.05), 70, length * 0.22, -1.2, 0.0016,
                          {"ivory": mats["gold"], "light": mats["light"]}, strands=2, gold=False, curl_start=0.35)
    objs += m.droplet(f"{name}_Light", tail - d * 0.004, 0.0065, -d, mats["light"], stretch=1.2)
    return objs


def wound_glow(name, center, radius, strength=6.0):
    """Light seeping up through the hide around a buried round: a soft glowing disc."""
    mat = m.membrane_material(f"{name}_Mat", radius, strength, rim=0.0, center=0.9)
    node = mat.node_tree.nodes["Membrane_Emission"]
    node.inputs["Color"].default_value = c.hex_to_linear("#FFB43A")
    ramp = next(n for n in mat.node_tree.nodes if n.type == "VALTORGB")
    ramp.color_ramp.elements[0].color = (0.75, 0.75, 0.75, 1)
    ramp.color_ramp.elements[1].position = 0.9
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    return m.membrane_disc(name, center, radius, (0, 0, 1), mat)


def gold_cracks(prefix, center, count, length, mat, seed=4):
    rng = random.Random(seed)
    objs = []
    for k in range(count):
        heading = rng.uniform(0, 2 * math.pi)
        p = Vector(center)
        pts = [p.copy()]
        for i in range(12):
            heading += rng.uniform(-0.45, 0.45)
            p = p + V(math.cos(heading), math.sin(heading), 0) * (length / 12)
            pts.append(p.copy())
        objs.append(c.curve_tube(f"{prefix}_{k}", pts, [1 - 0.9 * i / 12 for i in range(13)], mat,
                                 bevel=0.0016, resolution=1))
    return objs


def wyvernpiercer():
    c.reset_scene()
    mats = m.materials()
    mats["gold"] = gold_material()
    m.glow_mode(mats)
    # The round alone.
    rnd = thorn(mats, 0.16, V(0.08, 0, 0.12), V(1, 0, 0.0))
    st.stage_lights((0, 0, 0.12), 0.6, res=(700, 600))
    paths = c.render_views(OUT, "round", V(0, 0, 0.12), 0.42, [("side", 10, 10)], lens=50)
    for o in rnd:
        bpy.data.objects.remove(o, do_unlink=True)
    # Buried in the hide: only the tail shows, light leaks through the wound, then it bursts.
    hide_block()
    entry = V(0, 0, 0)
    d = V(-0.6, 0, -1).normalized()                     # flying down into the hide
    tail_out = thorn(mats, 0.16, entry + d * 0.09, d, "Buried")
    glow = c.make_material("Crack_Light", c.PALETTE["glow"], roughness=0.2, emission=c.PALETTE["glow"], strength=6.0)
    cracks = gold_cracks("Wound_Crack", entry, 7, 0.07, glow)
    seep = wound_glow("Wound_Glow", entry + V(0, 0, 0.001), 0.045, strength=1.6)
    bursts = []
    for k, (off, r) in enumerate(((V(0, 0, 0.0), 0.05), (V(0.05, 0.03, 0.0), 0.035), (V(-0.04, -0.03, 0.0), 0.03))):
        bursts += pf.burst_strands(f"Inner_Burst_{k}", entry + off, r, count=120, strength=1.4, seed=11 + k, lift=1.4)
    shock = m.halo("Inner_Shock", entry + V(0, 0, 0.003), 0.14, 0.003, (0, 0, 1), mats["light"])
    states = [("射入：尾端露出、傷口透光", True, False), ("從體內爆開", False, True)]
    target, distance = V(0.0, 0, 0.04), 0.75
    for i, (label, buried, burst) in enumerate(states):
        st.show(tail_out, buried)
        st.show(cracks + seep, True)
        st.show(bursts + shock, burst)
        paths += c.render_views(OUT, f"state{i}", target, distance, [("front", 15, 24)], lens=50)
    st.labelled_strip(paths, ["龍穿彈＝金荊棘"] + [s[0] for s in states], os.path.join(OUT, "wyvernpiercer.png"),
                      "重弩龍穿點火：彈頭改成金荊棘，打進去後從體內爆開")


# ------------------------------------------------------------------ light bowgun: wyvernblast

def petal(name, base, out_dir, open_deg, length, width, mat, curl=0.25):
    """One ivory petal rising from `base`: its tilt from vertical is open_deg, it cups
    inward slightly (curl), widest at two thirds."""
    up = V(0, 0, 1)
    out = Vector(out_dir).normalized()
    a = math.radians(open_deg)
    pts = []
    for i in range(24):
        t = i / 23
        tilt = a + curl * t * t * (-1 if open_deg < 40 else 0.4)
        pts.append(Vector(base) + (up * math.cos(tilt) + out * math.sin(tilt)) * length * t)
    side = up.cross(out).normalized()
    return m.path_blade(name, pts, out.cross(side) * -1 if False else side.cross(up).normalized(),
                        lambda t: width * math.sin(math.pi * min(t, 0.999) ** 0.8) * (1 - 0.3 * t) + 0.0008,
                        lambda t: 0.003 * (1 - t) + 0.0006, mat, samples=40)


def bud(mats, center, open_deg, prefix="Bud"):
    """The flower-bud mine: six ivory petals veined with gold around a light, on a nest of
    small scroll roots."""
    C = Vector(center)
    objs = []
    for k in range(6):
        a = 2 * math.pi * k / 6 + (0.25 if k % 2 else 0)
        out = V(math.cos(a), math.sin(a), 0)
        L = 0.075 if k % 2 == 0 else 0.068
        objs += petal(f"{prefix}_Petal_{k}", C + out * 0.006, out, open_deg + (6 if k % 2 else 0), L, 0.042,
                      mats["ivory"])
        # A gold vein down the middle of each petal.
        tilt = math.radians(open_deg + (6 if k % 2 else 0))
        vein = [C + out * 0.006 + (V(0, 0, 1) * math.cos(tilt) + out * math.sin(tilt)) * L * t * 0.85
                + out * 0.0022 for t in [i / 15 for i in range(16)]]
        objs.append(c.curve_tube(f"{prefix}_Vein_{k}", vein, [1 - 0.7 * i / 15 for i in range(16)], mats["light"],
                                 bevel=0.0011, resolution=1))
    objs += m.droplet(f"{prefix}_Light", C + V(0, 0, 0.022), 0.016, (0, 0, 1), mats["light"], stretch=1.1)
    ground = m.plane_mapper(C, (1, 0, 0), (0, 1, 0))
    for k in range(5):
        a = 360 * k / 5 + 20
        objs += m.tendril(f"{prefix}_Root_{k}", ground, (0.006 * math.cos(math.radians(a)), 0.006 * math.sin(math.radians(a))),
                          a, 0.05, 1.2 if k % 2 else -1.2, 0.0026, mats, strands=2, curl_start=0.4)
    return objs


def wyvernblast():
    c.reset_scene()
    mats = m.materials()
    m.glow_mode(mats)
    bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0, 0, -0.001))
    ground = bpy.context.active_object
    ground.name = "Ground"
    gmat = c.make_material("Ground_Mat", "#2A2620", roughness=0.9)
    ground.data.materials.append(gmat)
    closed = bud(mats, V(0, 0, 0), 8, "Closed")
    opened = bud(mats, V(0, 0, 0), 62, "Open")
    burst = pf.burst_strands("Bud_Burst", V(0, 0, 0.035), 0.042, count=220, strength=1.4, seed=5, lift=1.0)
    shock = m.halo("Bud_Shock", V(0, 0, 0.004), 0.13, 0.003, (0, 0, 1), mats["light"])
    st.stage_lights((0, 0, 0.04), 0.6, res=(640, 640))
    states = [("放置：花苞包著光", "closed"), ("被打到：花瓣綻開", "open"), ("爆炸", "burst")]
    paths = []
    for i, (label, mode) in enumerate(states):
        st.show(closed, mode == "closed")
        st.show(opened, mode == "open")
        st.show(burst + [o for o in shock], mode == "burst")
        if mode == "burst":
            st.show([o for o in opened if "Root" in o.name], True)
        paths += c.render_views(OUT, f"state{i}", V(0, 0, 0.045), 0.42, [("front", 20, 22)], lens=50)
    st.labelled_strip(paths, [s[0] for s in states], os.path.join(OUT, "wyvernblast.png"),
                      "輕弩地雷彈：一朵包著光的象牙花苞，被打到時綻開爆炸")


# ------------------------------------------------------------------ bow: tracer arrow

def light_arrow(mats, tip, direction, length=0.42, name="Arrow"):
    d = direction.normalized()
    objs = [c.curve_tube(f"{name}_Shaft", [tip - d * length, tip - d * 0.03], [1, 1], mats["core"], bevel=0.0028,
                         resolution=2)]
    objs += m.path_blade(f"{name}_Head", [tip - d * 0.06, tip], d.orthogonal(),
                         lambda t: 0.026 * (1 - t) ** 0.9, lambda t: 0.005 * (1 - t), mats["blade"], samples=20)
    return objs


def small_sigil(mats, center, scale, facing=(0, -1, 0)):
    """The shield's tree sigil in its halo, small, floating and facing the camera side."""
    import sword_shield as ss
    ss.FRONT = 0.0
    rng = random.Random(9)
    objs = m.halo("Sigil_Halo", (0, 0, 0), ss.R, 0.006, (0, 1, 0), mats["light"])
    leaves = ss.LeafBuilder()
    objs += ss.trunk(mats["light"])
    objs += ss.crown(mats["light"], leaves, rng)
    objs += ss.pods(mats["light"])
    objs.append(leaves.finish(mats["light"]))
    root = m.group("Tracer_Sigil", objs, center)
    root.scale = (scale, scale, scale)
    return [root] + st.descendants(root)


def tracer():
    c.reset_scene()
    mats = m.materials()
    m.glow_mode(mats)
    hide_block()
    entry = V(0, 0, 0)
    d = V(0.5, 0.2, -1).normalized()
    stuck = light_arrow(mats, entry + d * 0.05, d, name="Tracer")
    glow = c.make_material("Crack_Light", c.PALETTE["glow"], roughness=0.2, emission=c.PALETTE["glow"], strength=6.0)
    mark = gold_cracks("Tracer_Mark", entry, 6, 0.035, glow, seed=8)
    sigil = small_sigil(mats, entry + V(0, -0.02, 0.2), 0.22)
    # Other arrows curving in toward the sigil, each with a fading trail.
    homing = []
    trail_mat = m.veil_material("Homing_Trail", 0.35, 1.5)
    for k, (start, bend) in enumerate(((V(-0.55, -0.1, 0.45), V(0, 0, 0.25)), (V(-0.5, 0.2, 0.15), V(0.05, 0, 0.3)),
                                       (V(-0.6, -0.25, 0.3), V(0, -0.1, 0.1)))):
        aim = entry + V(0, 0, 0.03)
        path = m.catmull([start, start.lerp(aim, 0.5) + bend, aim.lerp(start, 0.18)], 40)
        tip = path[-1]
        d2 = (path[-1] - path[-4]).normalized()
        homing += light_arrow(mats, tip, d2, length=0.3, name=f"Homing_{k}")
        homing.append(c.curve_tube(f"Homing_Trail_{k}", path[:-6], [0.2 + 0.8 * i / 33 for i in range(34)], trail_mat,
                                   bevel=0.004, resolution=2))
    burst = pf.burst_strands("Tracer_Burst", entry + V(0, 0, 0.04), 0.07, count=220, strength=1.5, seed=13, lift=1.0)
    st.stage_lights((0, 0, 0.1), 1.0, res=(700, 640))
    states = [("插上：浮出樹紋光環", True, False, False), ("其他光箭轉彎追過來", True, True, False),
              ("打夠了：爆開", False, False, True)]
    paths = []
    for i, (label, sig, hom, bst) in enumerate(states):
        st.show(stuck + mark, not bst)
        st.show(sigil, sig)
        st.show(homing, hom)
        st.show(burst, bst)
        paths += c.render_views(OUT, f"state{i}", V(-0.12, 0, 0.12), 1.15, [("front", 10, 12)], lens=50)
    st.labelled_strip(paths, [s[0] for s in states], os.path.join(OUT, "tracer.png"),
                      "弓追蹤箭：插箭處浮出小小的樹紋光環，其他光箭追著它飛")


# ------------------------------------------------------------------ hunting horn: echo bubble

def bubble_material(name):
    """A real bubble: clear, a thin gilded film that catches the light at its edges (no
    rainbow film: that turned pink and violet, off the gold palette)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = c.hex_to_linear("#FFE7B0")
    bsdf.inputs["Roughness"].default_value = 0.02
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["IOR"].default_value = 1.05
    bsdf.inputs["Emission Color"].default_value = c.hex_to_linear("#FFB445")
    bsdf.inputs["Emission Strength"].default_value = 0.08
    return mat


def echo_bubble():
    c.reset_scene()
    mats = m.materials()
    m.glow_mode(mats)
    bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0, 0, -0.001))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.data.materials.append(c.make_material("Ground_Mat", "#2A2620", roughness=0.9))
    R = 0.9
    ring = m.halo("Echo_Ground_Ring", (0, 0, 0.01), R, 0.008, (0, 0, 1), mats["light"])
    ring += m.halo("Echo_Ground_Ring_Inner", (0, 0, 0.01), R * 0.86, 0.003, (0, 0, 1), mats["light"])
    # A faint film of light on the ground inside the ring.
    film = m.membrane_material("Echo_Film", R, 0.5, rim=0.25, center=0.02)
    ring += m.membrane_disc("Echo_Film", (0, 0, 0.006), R * 0.98, (0, 0, 1), film)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, segments=64, ring_count=32, location=(0, 0, 1.0))
    bub = bpy.context.active_object
    bub.name = "Echo_Bubble"
    bub.data.materials.append(bubble_material("Echo_Bubble_Mat"))
    bpy.ops.object.shade_smooth()
    core = m.droplet("Echo_Core", (0, 0, 1.0), 0.035, (0, 0, 1), mats["light"], stretch=1.2)
    core += m.halo("Echo_Core_Halo", (0, 0, 1.0), 0.07, 0.003, (0, 1, 0), mats["light"], tilt_deg=12)
    pulse = []
    for k, (r, minor) in enumerate(((0.32, 0.005), (0.46, 0.0035), (0.62, 0.0022))):
        pulse += m.halo(f"Echo_Pulse_{k}", (0, 0, 1.0), r, minor, (0, 1, 0.15), mats["light"])
    for k, (r, minor) in enumerate(((1.1, 0.006), (1.35, 0.004))):
        pulse += m.halo(f"Echo_Ground_Pulse_{k}", (0, 0, 0.01), r, minor, (0, 0, 1), mats["light"])
    st.stage_lights((0, 0, 0.6), 3.2, res=(760, 640))
    states = [("放置：地上光環、上方浮著光泡", False), ("在範圍內攻擊：共鳴脈動", True)]
    paths = []
    for i, (label, pul) in enumerate(states):
        st.show(pulse, pul)
        st.set_glow(mats["light"], *(st.BRIGHT_LIGHT if pul else (c.PALETTE["glow"], 2.5)))
        paths += c.render_views(OUT, f"state{i}", V(0, 0, 0.55), 3.2, [("front", 15, 16)], lens=50)
    st.labelled_strip(paths, [s[0] for s in states], os.path.join(OUT, "echo_bubble.png"),
                      "狩獵笛響玉：地上的光環＋浮空的金膜泡泡，攻擊時共鳴")


SETS = {"wyrmstake": wyrmstake, "wyvernpiercer": wyvernpiercer, "wyvernblast": wyvernblast, "tracer": tracer,
        "echo_bubble": echo_bubble}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    SETS[SET]()
    print("DONE", flush=True)
