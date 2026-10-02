"""The lily gunlance's charge with option C (a lily of light opening round the flower, the user's
pick, 2026-10-03) and the body changing too (user: "只有槍尖有變化的話有點空虛，槍身我也希望有點
改變"). Nothing of the lily is taken away (user: "別砍，只加"); everything is drawn in light, the
language of the big lily of light, and grows with the charge:
  C1 leaves of light   every ivory leaf grows a larger leaf drawn in light round it, opening out
  C2 lilies of light   the five buds (the shells) open into small lilies of light
  C3 vines of light    tendrils of light sprout up the stem and curl, a thread of light winds up
  C4 all three
Rows: the three steps of the charge (step 3 = the lily's Wyvern's Fire look).
Usage: python gunlance_lily_body.py <out_dir> [test]
"""
import math
import os
import random
import sys

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join("out", "lily_body")
TEST = "test" in sys.argv[2:]

import gunlance_lily_charge as lc        # noqa: E402  (imports gunlance_designs, devices, states)
import common as c                       # noqa: E402
import motifs as m                       # noqa: E402
from motifs import V                     # noqa: E402
import states as st                      # noqa: E402

gd = lc.gd
LEAVES = ((0.62, -0.5), (0.74, 2.3), (0.86, 4.1), (0.97, 0.9))      # design_b's lily leaves (height, angle)
SHEATH = ((0.016, 0.345), (0.036, 0.41), (0.056, 0.48), (0.066, 0.55), (0.06, 0.615))
GOLDEN = math.radians(137.5)


def light_outline(prefix, center, side, width_fn, mats, veins=4, rim=0.0022, mid=0.0016, vein=0.001, cup=0.1):
    """A tepal or leaf drawn in light: both rims, the midrib and pairs of veins."""
    pts = gd.smooth_path(center, 50)
    n = len(pts)
    rims = ([], [])
    for i, p in enumerate(pts):
        t = i / (n - 1)
        tan = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        nrm = side.cross(tan).normalized()
        w = width_fn(t)
        rims[0].append(p - side * (w / 2) + nrm * (cup * w))
        rims[1].append(p + side * (w / 2) + nrm * (cup * w))
    objs = []
    for e, r in enumerate(rims):
        objs += gd.tube(f"{prefix}_Rim_{e}", r[2:], mats["light"], rim, bulge=True)
    objs += gd.tube(f"{prefix}_Mid", pts[2:-4], mats["light"], mid, (1.0, 0.3))
    for j in range(veins):
        i = int((0.25 + 0.5 * j / max(veins - 1, 1)) * (n - 1))
        for e in range(2):
            v = gd.smooth_path([pts[i], pts[i].lerp(rims[e][min(i + 6, n - 1)], 0.6), rims[e][min(i + 9, n - 1)]], 10)
            objs += gd.tube(f"{prefix}_Vein_{j}_{e}", v, mats["light"], vein, (1.0, 0.4))
    return objs


def leaves_of_light(mats, step):
    """C1: a larger leaf drawn in light round every ivory leaf (and the sheath leaves),
    growing and opening outward with the charge."""
    k = {1: 1.4, 2: 1.8, 3: 2.3}[step]
    tilt = math.radians(6 * step)
    objs = []
    for i, (z, a) in enumerate(LEAVES):
        radial, circ = gd.ring_frame(a)
        length = 0.25 - 0.022 * i
        base = V(0, 0, z) + radial * 0.012
        path = [base, V(0, 0, z + 0.35 * length) + radial * 0.05, V(0, 0, z + 0.7 * length) + radial * 0.083,
                V(0, 0, z + length) + radial * 0.098]
        q = Quaternion(circ, tilt)
        path = [base + q @ ((p - base) * k) for p in path]
        objs += light_outline(f"C1_Leaf_{i}", path, circ,
                              lambda t, k=k: 0.026 * k * math.sin(math.pi * min(t / 0.98, 1) ** 0.6) ** 0.8, mats)
    ks = 1.0 + 0.3 * step
    for j in range(3):
        radial, circ = gd.ring_frame(2 * math.pi * j / 3 + 0.5)
        base = V(0, 0, SHEATH[0][1]) + radial * SHEATH[0][0]
        q = Quaternion(circ, tilt)
        path = [base + q @ ((V(0, 0, zz) + radial * r - base) * ks) for r, zz in SHEATH]
        objs += light_outline(f"C1_Sheath_{j}", path, circ,
                              lambda t: 0.055 * ks * math.sin(math.pi * min(t / 0.97, 1) ** 0.75) ** 0.7, mats, veins=3)
    return objs


def small_light_lily(prefix, base, axis, s, bloom, mats, rot=0.0):
    """A lily drawn in light, `s` times the size of the ivory one, opening along `axis`."""
    prof = [(r * s, (zz - 1.36) * s) for r, zz in gd.lily_profile(False, bloom)]
    q = V(0, 0, 1).rotation_difference(axis)
    objs = []
    for k in range(6):
        radial, circ = gd.ring_frame(rot + 2 * math.pi * k / 6)
        path = [base + q @ (radial * r + V(0, 0, h)) for r, h in prof]
        wmax = 0.062 * s
        objs += light_outline(f"{prefix}_{k}", path, q @ circ,
                              lambda t, wmax=wmax: wmax * math.sin(math.pi * min(t / 0.985, 1) ** 0.85) ** 0.6,
                              mats, veins=0, rim=0.0014, mid=0.001)
        tip = base + q @ (radial * (0.05 * s * (1 + bloom)) + V(0, 0, 0.3 * s))
        fil = gd.smooth_path([base, base + q @ (radial * (0.012 * s) + V(0, 0, 0.16 * s)), tip], 12)
        objs += gd.tube(f"{prefix}_Stamen_{k}", fil, mats["light"], 0.0009, (1.0, 0.6))
        objs += gd.sphere(f"{prefix}_Anther_{k}", tip, 0.0026, mats["phial_lit"])
    return objs


def bud_lilies(mats, step):
    """C2: the five buds (the shells) open into small lilies of light round them."""
    s = {1: 0.2, 2: 0.3, 3: 0.4}[step]
    bloom = {1: 0.0, 2: 0.5, 3: 1.0}[step]
    objs = []
    for i in range(5):
        z = 1.05 + 0.055 * i
        radial, _ = gd.ring_frame(0.3 + GOLDEN * i)
        reach = 0.066 - 0.006 * i
        d = (radial * 0.38 + V(0, 0, 1)).normalized()
        base = V(0, 0, z + 0.05) + radial * reach + d * 0.004
        objs += small_light_lily(f"C2_Lily_{i}", base, d, s, bloom, mats, rot=0.3 * i)
    return objs


def vines_of_light(mats, step):
    """C3: tendrils of light sprouting up the stem, longer at every step, and a thread of
    light winding up it the other way round from the vine, a bead of light leading it."""
    length = {1: 0.1, 2: 0.18, 3: 0.26}[step]
    sprouts = ((0.46, 0.2), (0.57, 2.6), (0.69, 4.9), (0.81, 1.0), (0.93, 3.4), (1.04, 5.7), (1.18, 1.9))
    objs = []
    for i, (z, a) in enumerate(sprouts):
        radial, _ = gd.ring_frame(a)
        plane = m.plane_mapper(V(0, 0, z) + radial * 0.014, radial, V(0, 0, 1))
        sgn = 1 if i % 2 == 0 else -1
        objs += m.tendril(f"C3_Vine_{i}", plane, (0, 0), 48, length, sgn * 1.3, 0.0034, mats, strands=2, gold=False,
                          strand_mat="light", offshoots=[(0.45, -sgn, 0.4, -sgn * 1.1)], curl_start=0.45)
    z_end = {1: 0.75, 2: 1.05, 3: 1.36}[step]
    pts = []
    for j in range(240):
        zz = 0.40 + (z_end - 0.40) * j / 239
        aa = -2 * math.pi * 3.0 * (zz - 0.40)
        pts.append(V(0.021 * math.cos(aa), 0.021 * math.sin(aa), zz))
    objs += gd.tube("C3_Sap", pts, mats["light"], 0.0019, (0.6, 1.0))
    objs += m.droplet("C3_Sap_Lead", pts[-1], 0.0055, (pts[-1] - pts[-4]).normalized(), mats["phial_lit"], stretch=2.0)
    return objs


def all_three(mats, step):
    return leaves_of_light(mats, step) + bud_lilies(mats, step) + vines_of_light(mats, step)


OPTIONS = [("C1 光葉", leaves_of_light), ("C2 光花", bud_lilies), ("C3 光藤", vines_of_light), ("C4 三者全加", all_three)]


def render_one(index, step):
    name, build = OPTIONS[index]
    c.reset_scene()
    mats = m.materials()
    mats["gold"] = gd.devices.gold_material()
    mats["phial_lit"] = c.make_material("Phial_Lit", c.PALETTE["glow"], roughness=0.1,
                                        emission=c.PALETTE["glow"], strength=3.0)
    m.glow_mode(mats)
    st.set_glow(mats["light"], "#FF9A10", lc.GLOW[step])
    st.set_blade(mats["blade"], "#FFA828", "#FF8000", lc.GLOW[step])
    st.set_glow(mats["core"], "#FFB030", lc.GLOW[step] + 1.0)
    c.set_emission_strength(mats["phial_lit"], 3.0 + 2.0 * step)
    rng = random.Random(7)
    if step == 3:                        # the lily exactly as proposed, at Wyvern's Fire
        gd.design_b(mats, rng, True)
        bloom = 1.0
    else:
        bloom = lc.BLOOM[step]
        gd.design_b(mats, rng, False, bloom=bloom)
        gd.sphere("Throat_Orb", (0, 0, lc.THROAT), 0.012 + 0.01 * step, mats["phial_lit"])
    lc.option_c(mats, step, bloom)       # the big lily of light at the muzzle
    build(mats, step)
    target, dist = (0, 0, 1.18), 3.45
    st.stage_lights(target, dist, res=(300, 500) if TEST else (600, 1000))
    if TEST:
        bpy.context.scene.cycles.samples = 8
    stem = f"body_{name.split()[0]}_{step}"
    return c.render_views(OUT, stem, target, dist, [("tq", 30, 8)], lens=50)[0]


def main():
    grid = {}
    for i in range(len(OPTIONS)):
        for step in (1, 2, 3):
            grid[(i, step)] = render_one(i, step)
            print("rendered", OPTIONS[i][0], step, flush=True)
    paths, labels = [], []
    for step in (1, 2, 3):
        for i, (name, _) in enumerate(OPTIONS):
            paths.append(grid[(i, step)])
            labels.append(f"{name}・{lc.STEP_NAMES[step]}")
    out = os.path.join(OUT, "lily_body_test.png" if TEST else "gunlance_lily_body.png")
    st.labelled_strip(paths, labels, out,
                      "聖百合 C 光之百合＋槍身也變化（原本的全部保留，只加；上：一段　中：二段　下：滿）", cols=len(OPTIONS))
    print("WROTE", out, flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout.flush()
        os._exit(0)
