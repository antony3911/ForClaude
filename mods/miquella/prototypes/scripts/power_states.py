"""Charges with more force (user, 2026-10-02 night): the lance's charge lacks power and
character; the bow's charge could carry more ornamental light; the insect glaive's triple
extract orbs are not settled; every weapon's charge could feel more powerful.

Design proposals only, not in the game yet. Each set renders several directions side by side
so the user can pick. Everything is something the game version can do with our tools: extra
parts faded in (Dissolve), parts moved or turned by bones (the floating rings already are),
brighter or deeper gold emission. No effects (fire, smoke) are drawn as models (DESIGN).

Sets:
  lance_power    four directions for the lance's charge, levels 1-3
  bow_power      ornamental light for the bow's charge
  extract_orbs   the insect glaive's three extract orbs, several styles
  weapons_power  more force for the other weapons' charges

Usage: python power_states.py <set> <out_dir>
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector, Quaternion

sys.path.insert(0, os.path.dirname(__file__))
import common as c
import motifs as m
from motifs import V, smoothstep
import states as st

SET = sys.argv[1] if len(sys.argv) > 1 else "lance_power"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join("out", SET)

# Charge looks (DESIGN: bright gold = more saturated and much stronger, never white).
LEVEL_LOOK = {1: ("#FF9A10", 5.0), 2: ("#FFA21C", 8.0), 3: ("#FFB43A", 12.0)}


def glow_mat(name, hex_color=None, strength=3.0):
    hex_color = hex_color or c.PALETTE["glow"]
    return c.make_material(name, hex_color, roughness=0.1, emission=hex_color, strength=strength)


def look(mat, level, scale=1.0):
    col, s = LEVEL_LOOK[level]
    st.set_glow(mat, col, s * scale)


def tube(name, pts, radii, mat, bevel):
    return c.curve_tube(name, pts, radii, mat, bevel=bevel, resolution=3)


def arc(name, center, radius, a0, a1, z_fn, mat, bevel, n=90, taper=True):
    """A partial circle around the Z axis (a motion trail): thick at a1, fading to a point at a0."""
    pts, radii = [], []
    for i in range(n):
        t = i / (n - 1)
        a = a0 + (a1 - a0) * t
        pts.append(Vector(center) + V(radius * math.cos(a), radius * math.sin(a), z_fn(t)))
        radii.append(max(0.05, t ** 0.8) if taper else 1.0)
    return [tube(name, pts, radii, mat, bevel)]


def lance_base():
    """The lance prototype in its glow look, shield hidden; returns its materials."""
    import arsenal
    c.reset_scene()
    mats = st.capture_build(arsenal.lance)
    m.glow_mode(mats)
    st.show([bpy.data.objects["EnergyShield"]], False)
    return mats


def lance_shaft(mats, level):
    """The lance's own parts per level: a little brighter each level, bright gold at full."""
    if level >= 3:
        st.brighten(mats)
    else:
        st.set_glow(mats["light"], c.PALETTE["glow"], 3.0 + 1.5 * level)
        st.set_blade(mats["blade"], c.PALETTE["blade_core"], c.PALETTE["blade_edge"], 2.4 + 0.5 * level)


LANCE_TIP = 1.98


def point_flare(name, mat, length, width=0.085):
    """A longer blade of light around the point (two crossed blades)."""
    objs = []
    for k, normal in enumerate(((0, 1, 0), (1, 0, 0))):
        objs += m.path_blade(f"{name}_{k}", [V(0, 0, LANCE_TIP - 0.38), V(0, 0, LANCE_TIP + length)], normal,
                             lambda t: width * (1 - t) ** 0.9 * (0.75 + 0.25 * math.sin(math.pi * min(t / 0.3, 1))),
                             lambda t: 0.02 * (1 - t), mat)
    return objs


# ---------------------------------------------------------------- A: spiral drill

def drill_strands(prefix, mat, reach, n_str, phase, r_root=0.16, turns=2.2, bevel=0.0042):
    """Strands from the vamplate's rim spiralling in toward the point, against the shaft's own
    helix; `reach` (0..1) is how far up they have grown (their growing ends taper off)."""
    z0, z1 = 0.47, 1.93
    zt = z0 + (z1 - z0) * reach
    objs = []
    for k in range(n_str):
        pts, radii = [], []
        n = 240
        for i in range(n):
            t = i / (n - 1)
            z = z0 + (zt - z0) * t
            u = (z - z0) / (z1 - z0)
            r = r_root * (1 - u) ** 1.2 + 0.012
            a = phase + 2 * math.pi * k / n_str - 2 * math.pi * turns * u
            pts.append(V(r * math.cos(a), r * math.sin(a), z))
            radii.append((1 - 0.65 * u) * (1 - 0.85 * smoothstep((t - 0.82) / 0.18)))
        objs.append(tube(f"{prefix}_{k}", pts, radii, mat, bevel))
    return objs


def lance_drill(mats, level):
    main = glow_mat("Drill_Main")
    fine = glow_mat("Drill_Fine")
    look(main, level, 1.0)
    look(fine, level, 0.7)
    objs = drill_strands("Drill_A", main, (0.4, 0.75, 1.0)[level - 1], 3, 0.0)
    if level >= 2:
        objs += drill_strands("Drill_B", fine, (0.5, 0.85)[level - 2], 3, math.pi / 3, r_root=0.2,
                              turns=2.2, bevel=0.0024)
    if level >= 3:
        # Spin trails at the root: the drill turning.
        for k in range(3):
            a0 = 2 * math.pi * k / 3
            objs += arc(f"Drill_Spin_{k}", (0, 0, 0.52), 0.205, a0, a0 + math.radians(100),
                        lambda t: 0.04 * t, fine, 0.003)
        objs += point_flare("Drill_Point", mats["blade"], 0.42)
    return objs


# ---------------------------------------------------------------- B: corolla and aureole

def petal(name, phi, length, spread, mat, width=0.05, lift=0.62):
    """A blade petal from the vamplate rim, opening outward and forward (its face toward the axis)."""
    r0, z0 = 0.13, 0.47
    path = []
    for i in range(9):
        t = i / 8
        r = r0 + length * spread * math.sin(t * math.pi / 2)
        z = z0 + length * lift * t + length * 0.25 * t * t
        path.append(V(r * math.cos(phi), r * math.sin(phi), z))
    radial = V(math.cos(phi), math.sin(phi), 0)
    return m.path_blade(name, path, radial, lambda t: width * math.sin(math.pi * min(1, t * 1.1)) ** 0.7 + 0.002,
                        lambda t: 0.006 * (1 - t) + 0.001, mat, samples=40)


def aureole(prefix, z, radius, mat, rays_mat, n_rays=24):
    """Miquella's halo behind the guard: a large ring with rays of two lengths."""
    objs = m.halo(f"{prefix}_Ring", (0, 0, z), radius, 0.0055, (0, 0, 1), mat)
    objs += m.halo(f"{prefix}_Ring_In", (0, 0, z + 0.005), radius * 0.62, 0.003, (0, 0, 1), rays_mat)
    for k in range(n_rays):
        a = 2 * math.pi * k / n_rays
        r_in, r_out = radius * 0.66, radius * (1.18 if k % 2 == 0 else 0.92)
        d = V(math.cos(a), math.sin(a), 0)
        pts = [d * r_in + V(0, 0, z), d * r_out + V(0, 0, z - 0.02)]
        objs.append(tube(f"{prefix}_Ray_{k}", pts, [1.0, 0.15], rays_mat, 0.0032 if k % 2 == 0 else 0.0022))
    return objs


def lance_corolla(mats, level):
    pm = glow_mat("Corolla_Petal")
    look(pm, level, 0.8)
    objs = []
    length = (0.16, 0.28, 0.4)[level - 1]
    for k in range(8):
        objs += petal(f"Corolla_{k}", 2 * math.pi * k / 8, length, 0.55, mats["blade"])
    if level >= 2:
        for k in range(8):
            objs += petal(f"Corolla_In_{k}", 2 * math.pi * (k + 0.5) / 8, length * 0.7, 0.3, pm, width=0.03)
    if level >= 3:
        am = glow_mat("Aureole")
        look(am, 3, 0.9)
        objs += aureole("Aureole", 0.4, 0.36, am, pm)
        objs += point_flare("Corolla_Point", mats["blade"], 0.3)
    return objs


# ---------------------------------------------------------------- C: light feathers

def feather(name, at_z, phi, size, mat):
    """A floating blade of light swept back like fletching (points away from the point)."""
    d = V(math.cos(phi), math.sin(phi), 0)
    p0 = d * 0.045 + V(0, 0, at_z)
    p1 = d * (0.045 + 0.55 * size) + V(0, 0, at_z - 0.85 * size)
    p2 = d * (0.045 + 0.75 * size) + V(0, 0, at_z - 1.35 * size)
    tangent_normal = V(-math.sin(phi), math.cos(phi), 0)
    return m.path_blade(name, [p0, p1, p2], tangent_normal,
                        lambda t: 0.36 * size * math.sin(math.pi * min(1, 0.15 + t)) ** 0.6 * (1 - t) ** 0.4 + 0.002,
                        lambda t: 0.006 * (1 - t) + 0.001, mat, samples=40)


def lance_feathers(mats, level):
    fm = glow_mat("Feather")
    look(fm, level, 0.8)
    tiers = [(0.78, 0.15, 0.0), (1.12, 0.12, math.pi / 3), (1.42, 0.095, 0.0), (1.68, 0.075, math.pi / 3)]
    shown = (1, 2, 4)[level - 1]
    objs = []
    for i, (z, size, phase) in enumerate(tiers[:shown]):
        for k in range(3):
            objs += feather(f"Feather_{i}_{k}", z, phase + 2 * math.pi * k / 3, size, mats["blade"])
        objs += m.halo(f"Feather_Collar_{i}", (0, 0, z + 0.004), 0.05 - 0.006 * i, 0.003, (0, 0, 1), fm)
    if level >= 3:
        objs += point_flare("Feather_Point", mats["blade"], 0.38)
    return objs


# ---------------------------------------------------------------- D: compression

def lance_compress(mats, level):
    rm = glow_mat("Compress_Ring")
    look(rm, level, 1.0)
    n = 8
    # Rings slide toward the point and close up level by level; the shaft dims as the light gathers.
    span = {1: (0.6, 1.62, 0.15, 0.04), 2: (0.98, 1.68, 0.12, 0.035), 3: (1.42, 1.74, 0.085, 0.03)}[level]
    z0, z1, r0, r1 = span
    objs = []
    for k in range(n):
        t = k / (n - 1)
        objs += m.halo(f"Compress_{k}", (0, 0, z0 + (z1 - z0) * t), r0 + (r1 - r0) * t,
                       0.005 + 0.002 * (level - 1) - 0.002 * t, (0, 0, 1), rm, tilt_deg=-3 if k % 2 == 0 else 3)
    st.set_glow(mats["light"], c.PALETTE["glow"], (3.2, 2.2, 1.2)[level - 1])
    if level >= 2:
        objs += point_flare("Compress_Point", mats["blade"], (0.18, 0.5)[level - 2], width=(0.07, 0.1)[level - 2])
    if level >= 3:
        star = glow_mat("Compress_Star")
        look(star, 3, 1.2)
        for k, normal in enumerate(((1, 0, 0), (0, 1, 0))):
            axis = V(0, 1, 0) if k == 0 else V(1, 0, 0)
            objs += m.path_blade(f"Compress_Spike_{k}", [V(0, 0, LANCE_TIP) - axis * 0.16, V(0, 0, LANCE_TIP) + axis * 0.16],
                                 normal, lambda t: 0.022 * math.sin(math.pi * t) ** 3 + 0.001,
                                 lambda t: 0.006 * math.sin(math.pi * t) + 0.001, star)
        objs += m.halo("Compress_Wave", (0, 0, LANCE_TIP + 0.1), 0.2, 0.0035, (0, 0, 1), star)
        objs += m.halo("Compress_Wave_2", (0, 0, LANCE_TIP + 0.2), 0.12, 0.0025, (0, 0, 1), star)
    return objs


LANCE_DIRECTIONS = [
    ("A 光旋", lance_drill, "槍身外長出反向的光絲，越蓄越長、越密，滿蓄力像旋轉的光鑽（遊戲裡光絲綁骨頭繞軸轉）"),
    ("B 光冠", lance_corolla, "護手綻放光的花瓣，一段比一段長；滿蓄力背後浮出米凱拉的光輪"),
    ("C 光羽", lance_feathers, "一層層往後掠的浮空光羽，從槍根往槍尖長出，像要往前射出去"),
    ("D 收束", lance_compress, "光環往槍尖滑、越收越緊，槍身變暗、光全部壓到槍尖，滿蓄力槍尖爆出星芒和衝擊環"),
]


def lance_power():
    target, distance = (0, 0, 1.22), 3.35
    paths, labels = [], []
    for name, build, _ in LANCE_DIRECTIONS:
        for level in (1, 2, 3):
            mats = lance_base()
            lance_shaft(mats, level)
            build(mats, level)
            st.stage_lights(target, distance, res=(540, 900))
            stem = f"lance_{name.split()[0]}_{level}"
            paths += c.render_views(OUT, stem, target, distance, [("tq", 20, 6)], lens=50)
            labels.append(f"{name}・蓄力 {level}" if level < 3 else f"{name}・滿蓄力")
            print("rendered", stem, flush=True)
    st.labelled_strip(paths, labels, os.path.join(OUT, "lance_power.png"),
                      "長槍蓄力：四個加強力量感的方向（每列一個方向，蓄力 1 → 2 → 滿）", cols=3)


# ---------------------------------------------------------------- bow: ornamental light

BOW_LEVELS = {1: (0.55, 2, "#FF9A10", 12.0), 2: (0.8, 4, "#FFB43A", 14.0), 3: (1.0, 6, "#FFE2AC", 16.0)}
BOW_GRIP_X = -0.14


def bow_base(level):
    """The bow drawn at a charge level, as in states.bow_charge (rings packed, two lit per level)."""
    import arsenal
    c.reset_scene()
    mats = m.materials()
    arsenal.build_bow(mats)
    m.glow_mode(mats)
    pack, lit, color, strength = BOW_LEVELS[level]
    rings = st.objs_named("Arrow_Rail_")
    for k, (o, x) in enumerate(zip(rings, arsenal.bow_rail_x(pack))):
        o.location.x = x
        mat = st.own_material([o], f"Rail_{k}")
        st.set_glow(mat, *((color, strength) if k < lit else ("#B8862E", 0.5)))
    st.set_glow(mats["light"], color, strength * 0.6)
    st.set_glow(mats["core"], color, strength)
    st.set_blade(mats["blade"], color, color, strength * 0.8)
    return mats, color, strength


def limb_path(s):
    g = BOW_GRIP_X
    limb = [V(g + 0.01, 0, s * 0.12), V(g - 0.05, 0, s * 0.33), V(g + 0.0, 0, s * 0.53),
            V(g + 0.12, 0, s * 0.65), V(g + 0.2, 0, s * 0.69)]
    return m.resample(m.catmull(limb, 40), 100)


def blossom(name, center, normal, size, mat, core_mat, petals=5, twist=0.0):
    """A small flower of light facing `normal`: pointed petals and a droplet heart."""
    n = Vector(normal).normalized()
    u = n.orthogonal().normalized()
    w = n.cross(u)
    objs = []
    for k in range(petals):
        a = twist + 2 * math.pi * k / petals
        d = u * math.cos(a) + w * math.sin(a)
        p0 = Vector(center) + d * size * 0.15
        p1 = Vector(center) + d * size * 0.7 + n * size * 0.18
        p2 = Vector(center) + d * size + n * size * 0.1
        objs += m.path_blade(f"{name}_P{k}", [p0, p1, p2], n.cross(d),
                             lambda t: size * 0.55 * math.sin(math.pi * min(1, t * 1.05)) ** 0.8 + 0.0004,
                             lambda t: size * 0.06 + 0.0004, mat, samples=16, subsurf=0)
    objs += m.droplet(f"{name}_Heart", center + n * size * 0.08, size * 0.2, n, core_mat, stretch=0.6)
    return objs


def bow_vine_blossoms(mats, level, color, strength):
    pm = glow_mat("Blossom", color, strength * 0.55)
    hm = glow_mat("Blossom_Heart", "#FFE2AC", strength * 0.9)
    stops = {1: (0.12, 0.3), 2: (0.12, 0.3, 0.48, 0.64), 3: (0.12, 0.3, 0.48, 0.64, 0.8, 0.93)}[level]
    objs = []
    for s in (1, -1):
        path = limb_path(s)
        for i, u in enumerate(stops):
            p = path[int(u * (len(path) - 1))]
            size = 0.06 - 0.02 * u + (0.012 if level == 3 else 0.0)
            objs += blossom(f"Blossom_{s}_{i}", p + V(-0.012, -0.035, 0), (-0.25, -1, 0.15 * s), size, pm, hm,
                            twist=i * 0.7)
    if level == 3:
        for s in (1, -1):
            tip = limb_path(s)[-1]
            objs += blossom(f"Blossom_Tip_{s}", tip + V(0.0, -0.045, s * 0.03), (-0.2, -1, 0.2 * s), 0.1, pm, hm, petals=7)
    return objs


def bow_sigil(mats, level, color, strength):
    """The Haligtree sigil (as on the energy shields) forming in front of the arrow."""
    import arsenal
    sm = glow_mat("Sigil", color, strength * (0.45, 0.6, 0.8)[level - 1])
    root = arsenal.energy_shield(mats, (0, 0, 0), 0.58, stretch=1.0)
    root.location = (-0.6, 0, 0.02)
    root.rotation_euler = (0, 0, math.radians(90))
    for o in st.descendants(root):
        if o.name.startswith("Shield_Membrane"):
            o.hide_render = True
            continue
        if o.type in ("MESH", "CURVE") and o.data.materials:
            o.data.materials[0] = sm
        if level == 1 and not o.name.startswith("Shield_Halo"):
            o.hide_render = True
    objs = []
    if level == 3:
        rm = glow_mat("Sigil_Rays", color, strength * 0.7)
        R = 0.27 * 0.58
        for k in range(16):
            a = 2 * math.pi * k / 16
            d = V(0, math.cos(a), math.sin(a))
            r1 = R * (1.45 if k % 2 == 0 else 1.22)
            objs.append(tube(f"Sigil_Ray_{k}", [V(-0.6, 0, 0.02) + d * R * 1.06, V(-0.62, 0, 0.02) + d * r1],
                             [1.0, 0.1], rm, 0.0028))
        objs += m.halo("Sigil_Outer", (-0.62, 0, 0.02), R * 1.3, 0.0025, (1, 0, 0), rm)
    return objs


def bow_orbit_phials(mats, level, color, strength):
    """Floating lit droplets in their halos circling the arrow's point: two per level."""
    pm = {"light": glow_mat("Orbit_Halo", color, strength * 0.6)}
    pm["phial_lit"] = glow_mat("Orbit_Drop", "#FFD58A" if level == 3 else color, strength * 0.9)
    n = 2 * level
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n + 0.3
        x = -0.68 + 0.06 * math.sin(2 * a)
        pts.append(V(x, 0.11 * math.cos(a), 0.02 + 0.11 * math.sin(a)))
    objs = m.floating_phials("Orbit", pts, (-1, 0, 0), (1, 0, 0), pm, size=0.02)
    objs += m.halo("Orbit_Path", (-0.68, 0, 0.02), 0.11, 0.0014, (1, 0, 0), pm["light"])
    if level == 3:
        objs += m.halo("Orbit_Ring", (-0.80, 0, 0.02), 0.06, 0.0022, (1, 0, 0), pm["light"])
        objs += m.halo("Orbit_Ring_2", (-0.86, 0, 0.02), 0.035, 0.0018, (1, 0, 0), pm["light"])
    return objs


def bow_wings(mats, level, color, strength):
    """Feathers of light spreading back from each limb, more and longer each level."""
    fm = glow_mat("Wing", color, strength * 0.5)
    count = (2, 4, 6)[level - 1]
    objs = []
    for s in (1, -1):
        path = limb_path(s)
        for i in range(count):
            u = 0.42 + 0.5 * i / 5
            root = path[int(u * (len(path) - 1))]
            length = (0.22 + 0.1 * (i % 2)) * (0.7 + 0.3 * level / 3) * (1.0 - 0.3 * i / 5)
            ang = math.radians(40 + 11 * i)
            d = V(-math.cos(ang), 0, s * math.sin(ang))
            mid = root + d * length * 0.55 + V(0, 0.01, s * length * 0.08)
            objs += m.path_blade(f"Wing_{s}_{i}", [root, mid, root + d * length + V(0, 0.02, s * length * 0.12)],
                                 (0, 1, 0), lambda t, L=length: L * 0.16 * math.sin(math.pi * min(1, 0.1 + t)) ** 0.7
                                 * (1 - t) ** 0.3 + 0.0006, lambda t: 0.003 * (1 - t) + 0.0005, fm, samples=30)
            objs.append(tube(f"Wing_Quill_{s}_{i}", [root, mid, root + d * length * 0.9], [1.0, 0.7, 0.1],
                             mats["light"], 0.0016))
    return objs


BOW_DIRECTIONS = [
    ("A 藤蔓綻放", bow_vine_blossoms, "弓臂上的金藤一段段開出光花，從握把開到弓尖，滿蓄力弓尖開大花"),
    ("B 聖樹光陣", bow_sigil, "箭前方浮出盾牌上的聖樹紋章光陣，箭從正中間穿過；一段只有外環、二段紋章、三段放射光芒"),
    ("C 光點環繞", bow_orbit_phials, "懸浮光點繞著箭頭轉，每段多兩顆（兼當段數），滿蓄力再套兩圈細光環"),
    ("D 光翼", bow_wings, "弓臂往後展開光的羽毛，越蓄越多越長，滿蓄力像一對光翼"),
]


def bow_power():
    target, distance = (-0.3, 0, 0.0), 2.05
    paths, labels = [], []
    for name, build, _ in BOW_DIRECTIONS:
        for level in (1, 2, 3):
            mats, color, strength = bow_base(level)
            build(mats, level, color, strength)
            st.stage_lights(target, distance, res=(720, 760))
            stem = f"bow_{name.split()[0]}_{level}"
            paths += c.render_views(OUT, stem, target, distance, [("tq", 28, 8)], lens=50)
            labels.append(f"{name}・蓄力 {level}")
            print("rendered", stem, flush=True)
    st.labelled_strip(paths, labels, os.path.join(OUT, "bow_power.png"),
                      "弓蓄力的裝飾光效：四個方向（每列一個方向，蓄力 1 → 2 → 3）", cols=3)


# ---------------------------------------------------------------- insect glaive: extract orbs

def extract_orbs():
    import orb_styles as ob
    target, distance = (0, 0, 0), 0.62
    paths, labels = [], []
    for name, build, _ in ob.STYLES:
        c.reset_scene()
        lm = m.materials()
        m.glow_mode(lm)
        for i, (kind, _) in enumerate(ob.KINDS):
            build(V(0.13 * (i - 1), 0, 0), kind, 0.04, lm)
        st.stage_lights(target, distance, res=(1100, 460))
        stem = f"orbs_{name.split()[0]}"
        paths += c.render_views(OUT, stem, target, distance, [("front", 18, 14)], lens=60)
        labels.append(f"{name}：腐敗・冰凍・癲火")
        print("rendered", stem, flush=True)
    st.labelled_strip(paths, labels, os.path.join(OUT, "extract_orbs.png"),
                      "操蟲棍三燈精華球：四種造型", cols=1)


# ---------------------------------------------------------------- other weapons

def weapons_power():
    import weapon_power as wp
    only = sys.argv[3:]                  # weapon names to render (default: all)
    for i, (name, base, additions, (target, distance, view, res)) in enumerate(wp.WEAPONS):
        if only and name not in only:
            continue
        paths, labels = [], []
        for label, add in [("現在的滿蓄力", None)] + additions:
            mats = base()
            if add:
                add(mats)
            st.stage_lights(target, distance, res=res)
            stem = f"wp_{i}_{len(paths)}"
            paths += c.render_views(OUT, stem, target, distance, [view], lens=50)
            labels.append(f"{name}・{label}")
            print("rendered", stem, name, label, flush=True)
        # Each weapon on its own sheet (their panel sizes differ).
        st.labelled_strip(paths, labels, os.path.join(OUT, f"power_{i + 1}.png"),
                          f"{name}蓄力的力量感：現在 vs 兩個加強方向", cols=3)


# ---------------------------------------------------------------- animations

def save_gif(frames, out, ms=70):
    from PIL import Image
    imgs = [Image.open(f).convert("RGB") for f in frames]
    imgs = [im.resize((im.width // 2, im.height // 2), Image.LANCZOS) for im in imgs]
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=ms, loop=0, optimize=True)
    return out


def compress_rings(mats, p, rm):
    """lance_compress at a continuous progress p (0 spread out .. 1 packed at the point)."""
    spans = [(0.6, 1.62, 0.15, 0.04), (0.98, 1.68, 0.12, 0.035), (1.42, 1.74, 0.085, 0.03)]
    x = min(1.999, p * 2)
    a, b = spans[int(x)], spans[int(x) + 1]
    f = x - int(x)
    z0, z1, r0, r1 = [u + (v - u) * f for u, v in zip(a, b)]
    objs = []
    for k in range(8):
        t = k / 7
        objs += m.halo(f"Compress_{k}", (0, 0, z0 + (z1 - z0) * t), r0 + (r1 - r0) * t, 0.005 + 0.004 * p - 0.002 * t,
                       (0, 0, 1), rm, tilt_deg=-3 if k % 2 == 0 else 3)
    return objs


def lance_anim():
    """A: the drill strands turning; D: the rings packing toward the point, then released."""
    target, distance = (0, 0, 1.22), 3.35
    # A: spin the full-charge drill (in the game: its strands on a bone turning about the axis).
    frames = []
    mats = lance_base()
    lance_shaft(mats, 3)
    lance_drill(mats, 3)
    pivot = c.link(bpy.data.objects.new("Drill_Pivot", None))
    for o in [o for o in bpy.data.objects if o.name.startswith("Drill_") and o is not pivot]:
        o.parent = pivot
    st.stage_lights(target, distance, res=(540, 900))
    for f in range(12):
        pivot.rotation_euler = (0, 0, -2 * math.pi / 3 * f / 12)   # three strands: a third of a turn loops
        frames += c.render_views(OUT, f"animA_{f:02d}", target, distance, [("tq", 20, 6)], lens=50)
    save_gif(frames, os.path.join(OUT, "lance_A_spin.gif"), ms=60)
    # D: charge (rings slide and pack, shaft dims, point grows), hold, release.
    frames = []
    seq = [i / 11 for i in range(12)] + [1.0] * 3 + [0.6, 0.25, 0.0]
    for f, p in enumerate(seq):
        mats = lance_base()
        lance_shaft(mats, 1 + int(p * 2.01))
        rm = glow_mat("Compress_Ring")
        col, strength = LEVEL_LOOK[min(3, 1 + int(p * 3))]
        st.set_glow(rm, col, strength)
        compress_rings(mats, p, rm)
        st.set_glow(mats["light"], c.PALETTE["glow"], 3.2 - 2.0 * p)
        if p > 0.4:
            point_flare("Compress_Point", mats["blade"], 0.5 * (p - 0.4) / 0.6, width=0.07 + 0.03 * p)
        if p >= 1.0:
            star = glow_mat("Compress_Star")
            look(star, 3, 1.2)
            m.halo("Compress_Wave", (0, 0, LANCE_TIP + 0.1), 0.2, 0.0035, (0, 0, 1), star)
            m.halo("Compress_Wave_2", (0, 0, LANCE_TIP + 0.2), 0.12, 0.0025, (0, 0, 1), star)
        st.stage_lights(target, distance, res=(540, 900))
        frames += c.render_views(OUT, f"animD_{f:02d}", target, distance, [("tq", 20, 6)], lens=50)
        print("frame", f, flush=True)
    save_gif(frames, os.path.join(OUT, "lance_D_compress.gif"), ms=90)


def extract_on_glaive():
    """The four orb styles circling the glaive's top blade with all three extracts lit (the
    blade bright gold), to judge their size on the weapon."""
    import arsenal
    import orb_styles as ob
    target, distance = (0.0, 0, 1.64), 0.95
    angles = {"rot": -100, "frenzy": 140, "frost": 20}
    heights = {"rot": 1.72, "frenzy": 1.62, "frost": 1.66}
    paths, labels = [], []
    for name, build, _ in ob.STYLES:
        c.reset_scene()
        mats = st.capture_build(arsenal.insect_glaive)
        m.glow_mode(mats)
        st.brighten(mats)
        for kind, a in angles.items():
            p = V(0.1 * math.cos(math.radians(a)), 0.1 * math.sin(math.radians(a)), heights[kind])
            build(p, kind, 0.026, mats)
        st.stage_lights(target, distance, res=(640, 820))
        stem = f"glaive_{name.split()[0]}"
        paths += c.render_views(OUT, stem, target, distance, [("tq", 20, 10)], lens=50)
        labels.append(name)
        print("rendered", stem, flush=True)
    st.labelled_strip(paths, labels, os.path.join(OUT, "extract_on_glaive.png"),
                      "操蟲棍三燈齊：四種精華球繞著光刃（光刃亮金）", cols=4)


SETS = {"lance_power": lance_power, "bow_power": bow_power, "extract_orbs": extract_orbs,
        "weapons_power": weapons_power, "lance_anim": lance_anim,
        "extract_on_glaive": extract_on_glaive}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    SETS[SET]()
    print("DONE", flush=True)
