"""Second round of charge proposals (user, 2026-10-02 evening): the gunlance's two did not have
the right feel ("try a charging gold filament stretching inside it"); the hammer's left the
user cold; the sword & shield's Perfect Rush (attack when the hunter lights up for more damage)
and Charged Chop should change the blade too.

Usage: python power_round2.py <gunlance|hammer|sns> <out_dir>
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as c
import motifs as m
from motifs import V
import states as st

SET = sys.argv[1] if len(sys.argv) > 1 else "gunlance"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join("out", SET)

LOOK = {1: ("#FF9A10", 6.0), 2: ("#FFA21C", 9.0), 3: ("#FFB43A", 13.0)}


def glow(name, level=2, scale=1.0, hex_color=None):
    col, s = LOOK[level]
    col = hex_color or col
    return c.make_material(name, col, roughness=0.1, emission=col, strength=s * scale)


def tube(name, pts, radii, mat, bevel):
    return c.curve_tube(name, pts, radii, mat, bevel=bevel, resolution=3)


def render_grid(rows, build_base, target, distance, view, res, title, out_name):
    paths, labels = [], []
    for name, build in rows:
        for level in (1, 2, 3):
            mats = build_base(level)
            build(mats, level)
            st.stage_lights(target, distance, res=res)
            stem = f"{SET}_{name.split()[0]}_{level}"
            paths += c.render_views(OUT, stem, target, distance, [view], lens=50)
            labels.append(f"{name}・{('蓄力 1', '蓄力 2', '滿蓄力')[level - 1]}" if SET != "sns" else
                          f"{name}・{LEVEL_NAMES_SNS[name.split()[0]][level - 1]}")
            print("rendered", stem, flush=True)
    st.labelled_strip(paths, labels, os.path.join(OUT, out_name), title, cols=3)


# ---------------------------------------------------------------- gunlance: a gold filament stretching

GL_ROOT = 0.5


def gl_base(level):
    import arsenal
    c.reset_scene()
    mats = st.capture_build(arsenal.gunlance)
    m.glow_mode(mats)
    st.show([bpy.data.objects["EnergyShield"]], False)
    st.show([bpy.data.objects["Conduit"]], False)              # the filament takes its place
    z0 = arsenal.GUNLANCE_BASE + 0.1
    for o in [o for o in bpy.data.objects if o.name.startswith("Binding")]:
        bpy.data.objects.remove(o, do_unlink=True)
    arsenal.gunlance_spring(mats, top=z0 + (arsenal.SPRING_TOP - z0) * (0.8, 0.62, 0.45)[level - 1])
    core = c.make_material("GL_Core", LOOK[level][0], roughness=0.1, emission=LOOK[level][0],
                           strength=6.0 + 3 * level)
    for o in [o for o in bpy.data.objects if o.name.startswith("Energy_Core")]:
        o.data.materials[0] = core
    return mats


def gl_top(level):
    import arsenal
    return GL_ROOT + (arsenal.GUNLANCE_TIP - 0.02 - GL_ROOT) * (0.38, 0.68, 1.0)[level - 1]


def filament_coil(mats, level):
    """A tight coil of gold wire from the core, drawn out toward the muzzle: the same number of
    turns over a longer reach, so the coil opens up and thins as it stretches."""
    g = glow("Coil", level, 1.0)
    top = gl_top(level)
    turns, n = 30, 900
    r = (0.022, 0.016, 0.011)[level - 1]
    pts = [V(r * math.cos(2 * math.pi * turns * t), r * math.sin(2 * math.pi * turns * t), GL_ROOT + (top - GL_ROOT) * t)
           for t in [i / (n - 1) for i in range(n)]]
    objs = [tube("Coil", pts, [1.0] * n, g, 0.003)]
    objs += m.droplet("Coil_Tip", V(0, 0, top + 0.012), 0.008 + 0.002 * level, (0, 0, 1), glow("Coil_Drop", level, 1.6),
                      stretch=1.5)
    return objs


def filament_beads(mats, level):
    """A straight gold thread drawn out of the core, beads of light strung along it."""
    g = glow("Thread", level, 1.1)
    top = gl_top(level)
    objs = [tube("Thread", [V(0, 0, GL_ROOT), V(0, 0, top)], [1.0, 0.6], g, 0.0035 + 0.0008 * level)]
    bead = glow("Bead", level, 1.6)
    n = 2 * level + 1
    for k in range(n):
        z = GL_ROOT + (top - GL_ROOT) * (k + 1) / (n + 0.5)
        objs += m.droplet(f"Bead_{k}", V(0, 0, z), 0.012, (0, 0, 1), bead, stretch=0.9)
        objs += m.halo(f"Bead_Halo_{k}", V(0, 0, z + 0.004), 0.026, 0.002, (0, 0, 1), g)
    objs += m.droplet("Thread_Tip", V(0, 0, top + 0.01), 0.011, (0, 0, 1), bead, stretch=1.6)
    return objs


def filament_braid(mats, level):
    """Two gold threads twisted together (the unalloyed gold needle's eye), drawn out: the same
    twists over a longer reach loosen; an eye of twisted gold at the drawn end."""
    g = glow("Braid", level, 1.0)
    top = gl_top(level)
    twists, n = 9, 500
    r = (0.011, 0.0085, 0.006)[level - 1]
    objs = []
    for k in range(2):
        pts = [V(r * math.cos(k * math.pi + 2 * math.pi * twists * t), r * math.sin(k * math.pi + 2 * math.pi * twists * t),
                 GL_ROOT + (top - GL_ROOT) * t) for t in [i / (n - 1) for i in range(n)]]
        objs.append(tube(f"Braid_{k}", pts, [1.0] * n, g, 0.0028))
    # The eye: two strands parting into an oval loop and meeting again.
    eye_h, eye_w = 0.07, 0.024
    for k, s in enumerate((1, -1)):
        pts = [V(s * eye_w * math.sin(math.pi * t), 0, top + eye_h * t) for t in [i / 30 for i in range(31)]]
        objs.append(tube(f"Braid_Eye_{k}", pts, [1.0] * 31, g, 0.0028))
    objs += m.droplet("Braid_Drop", V(0, 0, top + eye_h * 0.5), 0.007 + 0.002 * level, (0, 0, 1),
                      glow("Braid_Drop", level, 1.8), stretch=0.6)
    return objs


GUNLANCE_ROWS = [("G1 金線圈拉伸", filament_coil), ("G2 光珠金線", filament_beads), ("G3 絞絲針眼", filament_braid)]


def gunlance():
    render_grid(GUNLANCE_ROWS, gl_base, (0, 0, 1.2), 2.35, ("three_quarter", 25, 8), (560, 900),
                "銃槍蓄力：槍身裡一條充能金絲往槍口拉伸（外面象牙彈簧同時往槍根壓）", "gunlance_filament.png")


# ---------------------------------------------------------------- hammer

HM_Z, HM_HALF = 1.04, 0.2


def hm_base(level):
    import arsenal
    c.reset_scene()
    mats = st.capture_build(arsenal.hammer)
    m.glow_mode(mats)
    rings = arsenal.hammer_charge_rings(mats)
    for lv, objs in rings.items():
        st.show(objs, lv <= level)
    col, s = (("#FF9A10", 12.0), ("#FFB43A", 14.0), ("#FFF0DC", 16.0))[level - 1]
    st.set_glow(mats["light"], col, s)
    st.set_glow(bpy.data.materials["Sun"], col, 6.0 + 1.5 * level)
    return mats


def hm_cage_open(mats, level):
    """The sun swells and pushes the cage open: its strands bow outward and part."""
    for o in st.objs_named("Cage"):
        o.hide_render = True
    orb = bpy.data.objects["Sun_Orb"]
    k = (1.15, 1.35, 1.6)[level - 1]
    orb.scale = (k, k, k)
    objs = []
    n = 12
    bulge = (0.17, 0.22, 0.28)[level - 1]
    gap = (0.0, 0.25, 0.5)[level - 1]            # the ribs part in the middle as the sun pushes out
    for j in range(n):
        phi = 2 * math.pi * j / n
        for side in (-1, 1):
            pts, radii = [], []
            for i in range(40):
                u = i / 39                       # face -> middle
                x = side * HM_HALF * (1 - u * (1 - gap * 0.5))
                r = 0.13 + (bulge - 0.13) * math.sin(math.pi * u / 2) ** 1.2
                a = phi + side * 0.12 * u
                pts.append(V(x, r * math.cos(a), HM_Z + r * math.sin(a)))
                radii.append(1.0 - 0.75 * u ** 2 if gap else 1.0)
            objs.append(tube(f"Open_Rib_{j}_{side}", pts, radii, mats["ivory"], 0.0045))
    for side in (-1, 1):
        objs += m.halo(f"Open_Face_{side}", (side * HM_HALF, 0, HM_Z), 0.135, 0.005, (1, 0, 0), mats["light"])
    return objs


def hm_planets(mats, level):
    """Small suns on tilted orbits around the head, more of them and closer each level."""
    g = glow("Planet", level, 1.3)
    line = glow("Orbit", level, 0.35)
    orbits = [(0.3, 18, 0.0), (0.26, -32, 1.3), (0.34, 60, 2.4)][:level]
    objs = []
    for k, (r, tilt, phase) in enumerate(orbits):
        axis = Vector((math.sin(math.radians(tilt)), 0, math.cos(math.radians(tilt)))).normalized()
        objs += m.halo(f"Orbit_{k}", (0, 0, HM_Z), r, 0.0012, axis, line)
        u = axis.orthogonal().normalized()
        w = axis.cross(u)
        for j in range(2):
            a = phase + math.pi * j
            p = V(0, 0, HM_Z) + (u * math.cos(a) + w * math.sin(a)) * r
            objs += m.droplet(f"Planet_{k}_{j}", p, 0.018 - 0.003 * j, (0, 0, 1), g, stretch=0.0)
            objs += m.halo(f"Planet_Halo_{k}_{j}", p, 0.03 - 0.005 * j, 0.0018, axis, g)
    return objs


def hm_scrolls(mats, level):
    """Gold scrollwork growing out of the faces and curling round the head, longer each level."""
    objs = []
    length = (0.14, 0.24, 0.34)[level - 1]
    for side in (-1, 1):
        for j in range(4):
            phi = math.pi / 4 + math.pi / 2 * j
            # A plane through the hammer's axis at angle phi: 2D x along the axis, y outward.
            out = V(0, math.cos(phi), math.sin(phi))
            mapper = m.plane_mapper(V(side * HM_HALF, 0, HM_Z), (side, 0, 0), tuple(out))
            objs += m.tendril(f"Scroll_{side}_{j}", mapper, (0.0, 0.13), 120, length, 1.4 * (1 if j % 2 else -1),
                              0.008, mats, strands=3, strand_mat="light",
                              offshoots=[(0.4, 1, 0.45, -1.2)] if level >= 2 else ())
    return objs


HAMMER_ROWS = [("H1 撐開籠子", hm_cage_open), ("H2 日輪行星", hm_planets), ("H3 卷草滋長", hm_scrolls)]


def hammer():
    render_grid(HAMMER_ROWS, hm_base, (0, 0, 1.0), 2.3, ("three_quarter", 30, 12), (700, 700),
                "大錘蓄力・第二輪：三個方向", "hammer_round2.png")


# ---------------------------------------------------------------- sword & shield

LEVEL_NAMES_SNS = {"S1": ("完美 1 次", "完美 2 次", "完美 4 次（滿）"),
                   "S2": ("時機將到", "完美時機", "打出完美"),
                   "S3": ("蓄力中", "蓄力將滿", "蓄力斬命中弱點")}
SNS_TIP = 0.16 + 0.72


def sns_base(level):
    import blades
    c.reset_scene()
    mats = m.materials()
    blades.BLADE_LEN = 0.72
    drop = c.make_material("Droplet", c.PALETTE["glow"], roughness=0.08, emission=c.PALETTE["glow"], strength=3.0)
    blades.build_sword("Sword", mats["ivory"], drop, mats["blade"], mats["core"], seed=4)
    m.glow_mode(mats)
    return mats


def leaf(name, center, size, mat, lean):
    """A small leaf of light (the shield sigil's leaves), its point up and leaning out."""
    d = V(math.sin(lean), 0, math.cos(lean))
    return m.path_blade(name, [center, center + d * size], (0, 1, 0),
                        lambda t: size * 0.42 * math.sin(math.pi * min(1, t * 1.05)) ** 0.7 + 0.0004,
                        lambda t: 0.003, mat, samples=20)


def sns_perfect_stack(mats, level):
    """Each Perfect lights one pair of leaves up the blade; the fourth turns it bright gold."""
    count = (1, 2, 4)[level - 1]
    g = glow("Leaf", 3 if level == 3 else 2, 1.0)
    objs = []
    for k in range(count):
        z = 0.24 + 0.14 * k
        for s in (1, -1):
            objs += leaf(f"Leaf_{k}_{s}", V(s * 0.03, -0.004, z), 0.07 - 0.008 * k, g, s * math.radians(38))
    if level == 3:
        st.brighten(mats)
        objs += m.halo("Perfect_Crown", (0, 0, SNS_TIP + 0.03), 0.04, 0.0025, (0, 0, 1), g)
    return objs


def sns_timing(mats, level):
    """A ring slides down the blade to the guard as the timing comes; on a Perfect it bursts."""
    g = glow("Timing", 3, 1.0)
    objs = []
    if level == 1:
        objs += m.halo("Timing_Ring", (0, 0, 0.7), 0.05, 0.003, (0, 0, 1), g)
        objs += m.halo("Timing_Ring_2", (0, 0, 0.78), 0.035, 0.002, (0, 0, 1), g)
    elif level == 2:
        objs += m.halo("Timing_Ring", (0, 0, 0.2), 0.07, 0.004, (0, 0, 1), g)
        st.set_blade(mats["blade"], "#FFC35A", "#FF9A10", 6.0)
    else:
        st.brighten(mats)
        for k, (z, r) in enumerate(((0.2, 0.1), (0.3, 0.14), (0.42, 0.18))):
            objs += m.halo(f"Burst_{k}", (0, 0, z), r, 0.004 - 0.001 * k, (0, 0, 1), g)
        for k in range(12):
            a = 2 * math.pi * k / 12
            d = V(math.cos(a), math.sin(a), 0.25)
            objs.append(tube(f"Burst_Ray_{k}", [V(0, 0, 0.2) + d * 0.08, V(0, 0, 0.2) + d * 0.2], [1, 0.1], g, 0.0025))
    return objs


def sns_charged_chop(mats, level):
    """Holding the chop grows a longer blade of light around the sword; hitting a weak spot
    splits it into a second, outer blade for the follow-up slice."""
    import blades
    g = glow("Chop", min(3, level + 1), 0.8)
    ext = (0.12, 0.25, 0.32)[level - 1]
    objs = []
    for k, normal in enumerate(((0, 1, 0), (1, 0, 0))):
        objs += m.path_blade(f"Chop_Ext_{k}", [V(0, 0, 0.5), V(0, 0, SNS_TIP + ext)], normal,
                             lambda t: blades.BLADE_W * 0.9 * (1 - t) ** 0.7 + 0.001, lambda t: 0.004 * (1 - t) + 0.0005,
                             g if k == 0 else mats["blade"])
    if level == 3:
        st.brighten(mats)
        for s in (1, -1):
            objs += m.path_blade(f"Chop_Side_{s}", [V(s * 0.045, 0, 0.3), V(s * 0.07, 0, 0.62), V(s * 0.03, 0, SNS_TIP + 0.12)],
                                 (0, 1, 0), lambda t: 0.018 * math.sin(math.pi * min(1, 0.1 + t)) ** 0.7 + 0.0005,
                                 lambda t: 0.003, g)
    return objs


SNS_ROWS = [("S1 完美連擊光葉", sns_perfect_stack), ("S2 時機光環", sns_timing), ("S3 蓄力斬伸長", sns_charged_chop)]


def sns():
    render_grid(SNS_ROWS, sns_base, (0, 0, 0.66), 1.62, ("front", 10, 4), (520, 800),
                "片手劍：完美突進（亮起時出手）與蓄力斬的刀身變化", "sns_perfect.png")


# ---------------------------------------------------------------- hammer, third round

def hm_base3(level):
    """As hm_base, the white of the top level a little softer so additions stay readable."""
    mats = hm_base(level)
    if level == 3:
        st.set_glow(mats["light"], "#FFE9C8", 9.0)
    return mats


def hm_armillary(mats, level):
    """An armillary sphere around the caged sun: great rings on tilted axes (each can spin on
    its own bone, faster each level), beads of light set along them."""
    g = glow("Armillary", level, 0.9)
    bead = glow("Armillary_Bead", level, 1.6)
    rings = [((0.0, 1.0, 0.35), 0.31), ((0.0, -0.45, 1.0), 0.34), ((0.55, 0.0, 1.0), 0.28)][:level]
    objs = []
    for k, (axis, r) in enumerate(rings):
        axis = Vector(axis).normalized()
        objs += m.halo(f"Armillary_{k}", (0, 0, HM_Z), r, 0.0055, axis, g)
        objs += m.halo(f"Armillary_In_{k}", (0, 0, HM_Z), r - 0.012, 0.0018, axis, g)
        u = axis.orthogonal().normalized()
        w = axis.cross(u)
        for j in range(6):
            a = 2 * math.pi * j / 6 + k
            p = V(0, 0, HM_Z) + (u * math.cos(a) + w * math.sin(a)) * r
            objs += m.droplet(f"Armillary_Bead_{k}_{j}", p, 0.009, axis, bead, stretch=0.0)
    return objs


def hm_seal(mats, level):
    """The Haligtree sigil forming at the end of each cone of rings: the head strikes like a seal."""
    import arsenal
    objs = []
    x_end = (0.3, 0.37, 0.48)[level - 1]
    sm = glow("Seal", level, 0.9)
    for sgn in (-1, 1):
        root = arsenal.energy_shield(mats, (0, 0, 0), (0.3, 0.36, 0.42)[level - 1], stretch=1.0)
        root.location = (sgn * x_end, 0, HM_Z)
        root.rotation_euler = (0, 0, math.radians(90 * sgn))
        for o in st.descendants(root):
            if o.name.startswith("Shield_Membrane"):
                o.hide_render = True
            elif o.type in ("MESH", "CURVE") and o.data.materials:
                o.data.materials[0] = sm
                if level == 1 and not o.name.startswith("Shield_Halo"):
                    o.hide_render = True
    if level == 3:
        for sgn in (-1, 1):
            for k in range(16):
                a = 2 * math.pi * k / 16
                d = V(0, math.cos(a), math.sin(a))
                r0, r1 = 0.12, (0.2 if k % 2 == 0 else 0.16)
                objs.append(tube(f"Seal_Ray_{sgn}_{k}", [V(sgn * 0.48, 0, HM_Z) + d * r0, V(sgn * 0.49, 0, HM_Z) + d * r1],
                                 [1, 0.1], sm, 0.003))
    return objs


def hm_implode(mats, level):
    """The opposite of growing: the cones pull in tight against the faces and the sun shrinks
    to a hard white star; everything is loaded for the blow."""
    f = (0.7, 0.45, 0.2)[level - 1]
    for o in bpy.data.objects:
        if o.name.startswith("Charge_Ring_"):
            x = o.location.x
            o.location.x = math.copysign(HM_HALF + 0.03 + (abs(x) - HM_HALF - 0.03) * f, x)
    orb = bpy.data.objects["Sun_Orb"]
    k = (0.8, 0.6, 0.42)[level - 1]
    orb.scale = (k, k, k)
    st.set_glow(bpy.data.materials["Sun"], "#FFF6E8", 10.0 + 6 * level)
    objs = []
    if level >= 2:
        g = glow("Star", 3, 1.4)
        for j, axis in enumerate(((0, 1, 0), (0, 0, 1), (0, 0.7, 0.7), (0, 0.7, -0.7))):
            a = Vector(axis).normalized()
            ln = (0.16 if j < 2 else 0.1) * (1 if level == 3 else 0.6)
            objs += m.path_blade(f"Star_{j}", [V(0, 0, HM_Z) - a * ln, V(0, 0, HM_Z) + a * ln], (1, 0, 0),
                                 lambda t: 0.012 * math.sin(math.pi * t) ** 3 + 0.0005, lambda t: 0.004, g)
    return objs


HAMMER3_ROWS = [("H4 渾天儀", hm_armillary), ("H5 聖印錘面", hm_seal), ("H6 坍縮蓄能", hm_implode)]


def hammer3():
    render_grid(HAMMER3_ROWS, hm_base3, (0, 0, 1.0), 2.1, ("three_quarter", 32, 12), (700, 640),
                "大錘蓄力・第三輪：渾天儀／聖印錘面／坍縮蓄能", "hammer_round3.png")


SETS = {"gunlance": gunlance, "hammer": hammer, "sns": sns, "hammer3": hammer3}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    SETS[SET]()
    print("DONE", flush=True)
