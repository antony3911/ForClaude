"""The insect glaive's triple-up charge (user, 2026-10-03: "with all three extracts lit the glaive
also has a charged attack, look it up and think of a design"). In Wilds, with the three extracts
lit, holding the attack charges two levels (the game's cHoldAttackSuper, <ChargeLv> 0-2,
_ChargeTimer) and letting go throws the hunter up in a Rising Spiral Slash (cBatonUpSlashSuper).
Today the blade only turns gold -> bright gold -> white gold.

Four directions, each at charge level 1 and 2 (the spiral slash is the release). Design rules
(DESIGN, HANDOFF 5): bright gold not white, light and open, the extract flowers are the one
place off gold (rot crimson, frost white, frenzy orange), spirals and growth the user likes.
Everything maps onto what the game kit can do: parts that fade in or grow with the charge
(growth bands and bones), the flowers' orbit bones moved by the charge.

Usage: python glaive_charge.py <out_dir>
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
import orb_styles as ob
import states as st

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join("out", "glaive_charge")
TOP, TIP = 1.45, 1.87                       # the top blade's root and point (arsenal.insect_glaive)
SLOTS = {"rot": -100, "frenzy": 140, "frost": 20}          # the extract flowers round the blade
HEIGHTS = {"rot": 1.72, "frenzy": 1.62, "frost": 1.66}
ORBIT_R, FLOWER_R = 0.1, 0.026
GOLD = "#FFB43A"
BLADE_LOOK = {1: ("#FF9E18", "#FF7A00", 12.0), 2: ("#FFD27A", "#FFAA30", 16.0)}   # bright gold, white gold


def gold(name, strength=12.0):
    return c.make_material(name, GOLD, roughness=0.1, emission=GOLD, strength=strength)


def tube(name, pts, radii, mat, bevel):
    return c.curve_tube(name, pts, radii, mat, bevel=bevel, resolution=3)


def orbit_point(angle_deg, z, r=ORBIT_R):
    a = math.radians(angle_deg)
    return V(r * math.cos(a), r * math.sin(a), z)


def flowers(mats, places, r=FLOWER_R):
    objs = []
    for kind, p in places.items():
        objs += ob.style_flowers(p, kind, r, mats)
    return objs


def spiral(name, a0, a1, z0, z1, r0, r1, mat, bevel, n=120, taper=(0.25, 1.0)):
    pts, radii = [], []
    for i in range(n):
        t = i / (n - 1)
        a = math.radians(a0 + (a1 - a0) * t)
        r = r0 + (r1 - r0) * t
        pts.append(V(r * math.cos(a), r * math.sin(a), z0 + (z1 - z0) * t))
        radii.append(taper[0] + (taper[1] - taper[0]) * t)
    return tube(name, pts, radii, mat, bevel)


# ------------------------------------------------------------------ A: the three flowers converge

def a_converge(mats, level):
    """Level 1: the flowers leave their circle and spiral up the blade, closer and faster (their
    paths drawn in gold); level 2: they meet at the point and open as one flower of the three
    extracts, a gold halo of rays behind it."""
    g = gold("A_Trail")
    objs = []
    if level == 1:
        to = {k: (SLOTS[k] + 70, HEIGHTS[k] + 0.1, 0.068) for k in SLOTS}
        objs += flowers(mats, {k: orbit_point(a, z, r) for k, (a, z, r) in to.items()})
        for k, (a, z, r) in to.items():
            objs.append(spiral(f"A_Trail_{k}", a - 300, a - 12, HEIGHTS[k] - 0.05, z - 0.006, ORBIT_R, r, g, 0.0028))
        return objs
    tip = V(0, -0.004, TIP + 0.075)
    r = 0.05
    # The three gathered round the point, a gold heart where they meet.
    for kind, a in (("rot", 90), ("frost", 210), ("frenzy", 330)):
        em = ob.ess_mats(kind)
        build = {"rot": ob.aeonia, "frost": ob.frost_lily, "frenzy": ob.frenzy_flower}[kind]
        off = V(math.cos(math.radians(a)), 0, math.sin(math.radians(a))) * r * 0.66
        objs += build(f"A_Bloom_{kind}", tip + off + V(0, -0.006, 0), r * 0.7, em)
    objs += m.droplet("A_Heart", tip + V(0, -0.016, 0), 0.01, (0, -1, 0), gold("A_Heart", 20))
    objs += m.halo("A_Halo", tip + V(0, 0.012, 0), r * 1.45, 0.0022, (0, 1, 0), g)
    for k in range(16):
        a = 2 * math.pi * k / 16
        d = V(math.cos(a), 0, math.sin(a))
        objs.append(tube(f"A_Ray_{k}", [tip + V(0, 0.014, 0) + d * r * 1.55, tip + V(0, 0.014, 0) + d * r * (2.0 + 0.35 * (k % 2))],
                         [1.0, 0.1], g, 0.0018))
    for k, kind in enumerate(SLOTS):
        a1 = SLOTS[kind] + 70
        objs.append(spiral(f"A_Join_{kind}", a1 - 420, a1, HEIGHTS[kind] - 0.02, TIP + 0.05, 0.09, 0.012, g, 0.0028))
    return objs


# ------------------------------------------------------------------ B: a spiral spike of petals

def b_inflorescence(mats, level):
    """Petals of light set round the blade on a rising spiral (the golden angle, like a flower
    spike), growing petal by petal up the blade; level 2 reaches the point and crowns it with a
    small flower; the spike turns."""
    g = gold("B_Petal", 11.0)
    vine = gold("B_Vine", 8.0)
    objs = flowers(mats, {k: orbit_point(SLOTS[k], HEIGHTS[k]) for k in SLOTS})
    z0, z1, turns = TOP + 0.07, TIP - 0.01, 2.5
    reach = 0.5 if level == 1 else 1.0

    def at(t):
        a = 2 * math.pi * turns * t
        r = 0.058 * (1 - 0.6 * t) + 0.01
        return V(r * math.cos(a), r * math.sin(a) * 0.8, z0 + (z1 - z0) * t), V(math.cos(a), math.sin(a) * 0.8, 0)
    n = 160
    pts = [at(reach * i / (n - 1))[0] for i in range(n)]
    objs.append(tube("B_Vine", pts, [max(0.2, min(1.0, i / 8)) * (1 - 0.5 * i / n) for i in range(n)], vine, 0.0022))
    count = int(22 * reach)
    for i in range(count):
        t = (i + 0.5) / 22
        p, rad = at(t)
        length = 0.05 + 0.025 * math.sin(math.pi * t)
        d = (rad.normalized() * 0.8 + V(0, 0, 0.6)).normalized()
        objs += ob.petal_blade(f"B_Petal_{i}", p, d, V(0, 0, 1), length, 0.02, 0.25, g, curl=0.2, samples=16)
    if level == 2:
        import arsenal
        objs += arsenal.light_blossom("B_Crown", V(0, -0.01, TIP + 0.03), (0, -1, 0.35), 0.06, g, petals=7)
    return objs


# ------------------------------------------------------------------ C: wings of gold filigree

WING_FORE = [(0.0, 0.004), (0.03, 0.028), (0.065, 0.055), (0.1, 0.078), (0.128, 0.084), (0.126, 0.064),
             (0.116, 0.036), (0.1, 0.012), (0.08, -0.004), (0.05, -0.012), (0.02, -0.01)]
WING_HIND = [(0.0, -0.006), (0.03, -0.02), (0.064, -0.036), (0.09, -0.058), (0.094, -0.078),
             (0.08, -0.09), (0.066, -0.094), (0.062, -0.13), (0.056, -0.158), (0.05, -0.13),
             (0.04, -0.1), (0.02, -0.06), (0.005, -0.02)]          # (as the kinsect's, arsenal.kinsect)


def c_wings(mats, level):
    """A golden swallowtail like the kinsect opens at the blade's root: open filigree, no
    membranes (DESIGN: light and open) — veins and edges of gold, drops of light at the tips.
    Level 1 the forewings, level 2 the hindwings with their long tails."""
    g = gold("C_Wing", 10.0)
    fine = gold("C_Vein", 7.0)
    objs = flowers(mats, {k: orbit_point(SLOTS[k], HEIGHTS[k]) for k in SLOTS})
    root = V(0, 0.012, TOP + 0.075)
    k = 2.0
    # (the hindwings smaller and swept out, their tails clear of the guard)
    wings = [("Fore", WING_FORE, 0.18, k)] + ([("Hind", WING_HIND, 0.95, k * 0.72)] if level == 2 else [])
    for name, outline, tilt, kk in wings:
        for s in (-1, 1):
            def to3(p, s=s, tilt=tilt, kk=kk):
                x, y = p
                return root + V(s * x * kk, 0.03 * x * kk, y * kk + abs(x) * kk * tilt)
            pts = [to3(p) for p in outline] + [to3(outline[0])]
            pts = m.resample(m.catmull(pts, 16), 80)
            objs.append(tube(f"C_{name}_Edge_{s}", pts, [1.0] * len(pts), g, 0.0024))
            n = len(outline)
            for j, idx in enumerate((n // 4, n // 2, 3 * n // 4)):
                tip = to3(outline[idx])
                vein = [root + (tip - root) * (i / 20) + V(0, 0, 0.012 * math.sin(math.pi * i / 20)) for i in range(21)]
                objs.append(tube(f"C_{name}_Vein_{s}_{j}", vein, [1 - 0.6 * i / 20 for i in range(21)], fine, 0.0015))
            far = max(outline, key=lambda p: p[0] * p[0] + p[1] * p[1])
            objs += m.droplet(f"C_{name}_Drop_{s}", to3(far), 0.007, (s, 0, 0), gold("C_Drop", 18.0))
            # a scroll curling in from the wing's far edge (DESIGN: rich scrollwork)
            c0 = to3(far)
            curl = [c0 + V(s * 0.03 * math.cos(1.4 * math.pi * i / 30) * (1 - i / 40), 0,
                           0.03 * math.sin(1.4 * math.pi * i / 30) * (1 - i / 40)) - V(s * 0.03, 0, 0) for i in range(31)]
            objs.append(tube(f"C_{name}_Scroll_{s}", curl, [1 - 0.7 * i / 30 for i in range(31)], g, 0.0018))
    return objs


# ------------------------------------------------------------------ D: three-coloured spiral

def d_braid(mats, level):
    """The three extracts' colours as three strands of light braiding up the blade from its
    root, growing with the charge (like the lance's drill); level 2 they close to a point past
    the blade's tip and the flowers have gone into them."""
    objs = []
    if level == 1:
        objs += flowers(mats, {k: orbit_point(SLOTS[k], HEIGHTS[k]) for k in SLOTS})
    reach = 0.45 if level == 1 else 1.0
    z0, z1 = TOP + 0.05, TIP + 0.13
    looks = {"rot": ("#E01848", 9.0), "frost": ("#CFEAFF", 7.0), "frenzy": ("#FF6A00", 10.0)}
    for k, kind in enumerate(("rot", "frost", "frenzy")):
        mat = c.make_material(f"D_{kind}", looks[kind][0], roughness=0.15, emission=looks[kind][0],
                              strength=looks[kind][1])
        pts, radii = [], []
        n = int(200 * reach) + 2
        for i in range(n):
            t = reach * i / (n - 1)
            a = 2 * math.pi * k / 3 + 2 * math.pi * 2.6 * t
            r = 0.062 * (1 - t) ** 0.85 + 0.004
            pts.append(V(r * math.cos(a), r * math.sin(a) * 0.8, z0 + (z1 - z0) * t))
            radii.append(max(0.15, min(1.0, t * 14)) * (1 - 0.5 * t))
        objs.append(tube(f"D_Strand_{kind}", pts, radii, mat, 0.0042))
    if level == 2:
        g = gold("D_Point", 16.0)
        objs += m.droplet("D_Point", V(0, 0, z1), 0.009, (0, 0, 1), g, stretch=2.2)
        objs += m.halo("D_Point_Halo", (0, 0, z1 - 0.03), 0.022, 0.0016, (0, 0, 1), g)
    return objs


OPTIONS = [("A 三花聚頂", a_converge, "三朵精華花離開軌道、沿著刀刃螺旋往上；二段在刀尖合成一朵三色大花，背後金色光芒"),
           ("B 螺旋花序", b_inflorescence, "金色花瓣照黃金角沿刀刃螺旋排列，一片一片往上長；二段長到刀尖、頂端開小花，整串旋轉"),
           ("C 金絲蝶翼", c_wings, "刀根展開金絲鏤空的燕尾蝶翅（呼應獵蟲）：一段前翅、二段後翅和長燕尾"),
           ("D 三色光旋", d_braid, "三朵花化成紅白橘三股光絲，從刀根螺旋編上去；二段收成刀尖外的一點光")]


def main():
    import arsenal
    paths, labels = [], []
    for name, build, _ in OPTIONS:
        for level in (1, 2):
            c.reset_scene()
            mats = st.capture_build(arsenal.insect_glaive)
            m.glow_mode(mats)
            st.set_blade(mats["blade"], *BLADE_LOOK[level])
            st.set_glow(mats["light"], "#FF9A10", 12.0)
            st.set_glow(mats["core"], "#FFB030", 14.0)
            # (the kinsect beside the glaive is out of this picture)
            for o in bpy.data.objects:
                if o.type in ("MESH", "CURVE") and (o.matrix_world.translation.x > 0.22 or o.name.startswith("Kinsect")):
                    o.hide_render = True
            build(mats, level)
            target = (0.0, 0, 1.73)
            st.stage_lights(target, 1.15, res=(600, 860))
            stem = f"glaive_{name.split()[0]}_{level}"
            paths += c.render_views(OUT, stem, target, 1.15, [("tq", 22, 8)], lens=50)
            labels.append(f"{name}・{'一' if level == 1 else '二'}段")
            print("rendered", stem, flush=True)
    order = [paths[2 * i] for i in range(4)] + [paths[2 * i + 1] for i in range(4)]
    lab = [labels[2 * i] for i in range(4)] + [labels[2 * i + 1] for i in range(4)]
    st.labelled_strip(order, lab, os.path.join(OUT, "glaive_charge.png"),
                      "操蟲棍三燈蓄力（上升螺旋斬）：四個方向，上排一段、下排二段", cols=4)
    print("WROTE", os.path.join(OUT, "glaive_charge.png"), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout.flush()
        os._exit(0)
