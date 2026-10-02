"""Charging power for the lily gunlance (user, 2026-10-03: "聖百合非常好看，但蓄力的力量感不足，
有沒有辦法加點蓄力的力量感元素" and "別砍掉原有的元素…只加"). The lily stays exactly as proposed
(gunlance_designs.design_b; at full charge its Wyvern's Fire look: tepals thrown back, stamens
out, orb and rings); each direction only adds to it. Shown at the three steps of a charge (in
the game everything here grows continuously with the charge timer, like the great sword's
strands, so there are no jumps):
  A gold spiral    three strands of light spiral up from the root of the stem, round the
                   trumpet, and on past the mouth into a cone of light round the spear point
  B petal whorls   whorls of light tepals open in front of the flower one after another, each
                   larger, counter-rotating, with trails behind their tips
  C lily of light  a lily drawn in light opens round the ivory one and grows to two and a half
                   times its size, stamens of light reaching out
  D light vortex   streaks of light spiral in from all round into the flower's throat, more
                   and tighter at each step
Usage: python gunlance_lily_charge.py <out_dir> [test]
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join("out", "lily_charge")
TEST = "test" in sys.argv[2:]

import gunlance_designs as gd            # noqa: E402  (imports devices and states)
import common as c                       # noqa: E402
import motifs as m                       # noqa: E402
from motifs import V, smoothstep         # noqa: E402
import states as st                      # noqa: E402

GLOW = {1: 3.5, 2: 5.0, 3: 6.5}          # bright gold at every step, never white
BLOOM = {1: 0.3, 2: 0.65}                # step 3 is the lily's own Wyvern's Fire look
THROAT = 1.585


def trumpet_r(z, bloom):
    prof = gd.lily_profile(False, bloom)[:5]
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return prof[0][0] if z < prof[0][1] else prof[-1][0]


# ------------------------------------------------------------------ A gold spiral

def option_a(mats, step, bloom):
    """Three strands of light spiral up the stem from its root, round the trumpet and on
    into a cone round the spear point; a bright bead leads each strand."""
    z_end = {1: 0.98, 2: 1.62, 3: 1.965}[step]
    knots = ((0.40, 0.0), (1.36, 3.5), (1.60, 4.1), (1.965, 6.4))

    def turns_at(z):
        for (z0, t0), (z1, t1) in zip(knots, knots[1:]):
            if z <= z1:
                return t0 + (t1 - t0) * (z - z0) / (z1 - z0)
        return knots[-1][1]

    r_mouth = trumpet_r(1.60, bloom) + 0.016

    def radius_at(z):
        if z <= 1.36:
            return 0.032
        if z <= 1.60:
            return trumpet_r(z, bloom) + 0.016
        return r_mouth * (1 - (z - 1.60) / 0.365) ** 1.25 + 0.004

    objs = []
    n = 420
    for k in range(3):
        pts, radii = [], []
        for i in range(n):
            z = 0.40 + (z_end - 0.40) * i / (n - 1)
            a = 2 * math.pi * (k / 3 + turns_at(z))
            r = radius_at(z)
            pts.append(V(r * math.cos(a), r * math.sin(a), z))
            u = i / (n - 1)
            radii.append((0.5 + 0.5 * smoothstep(u * 4)) * (1 - 0.6 * smoothstep((u - 0.96) / 0.04)))
        objs.append(c.curve_tube(f"A_Spiral_{k}", pts, radii, mats["light"], bevel=0.0026 + 0.0006 * step,
                                 resolution=2))
        objs += m.droplet(f"A_Lead_{k}", pts[-1], 0.0055 + 0.0015 * step, (pts[-1] - pts[-5]).normalized(),
                          mats["phial_lit"], stretch=2.2)
    return objs


# ------------------------------------------------------------------ B petal whorls

def option_b(mats, step, bloom):
    """Whorls of light tepals in front of the flower, each step adding a larger one further
    forward; neighbouring whorls turn opposite ways, trails of light behind the tips."""
    objs = []
    whorls = [(1.665, 0.17, 0.0), (1.775, 0.25, 30.0), (1.885, 0.33, 10.0)]
    for wi in range(step):
        z, length, phase = whorls[wi]
        spin = 1 if wi % 2 == 0 else -1
        objs += m.halo(f"B_Hub_{wi}", (0, 0, z), 0.026, 0.0022, (0, 0, 1), mats["light"])
        for k in range(6):
            phi = math.radians(phase) + 2 * math.pi * k / 6
            radial, circ = gd.ring_frame(phi)
            gamma = math.radians(26)
            d = radial * math.cos(gamma) + V(0, 0, 1) * math.sin(gamma)
            pitch = math.radians(38) * spin
            wdir = circ * math.cos(pitch) + d.cross(circ) * math.sin(pitch)
            normal = d.cross(wdir).normalized()
            base = V(0, 0, z) + radial * 0.024
            path = [base, base + d * (0.5 * length) - circ * (spin * 0.012),
                    base + d * length - circ * (spin * 0.034)]
            width = 0.3 * length
            objs += m.path_blade(f"B_Whorl_{wi}_{k}", path, normal,
                                 lambda t, width=width: width * math.sin(math.pi * min(t / 0.98, 1) ** 0.8) ** 0.7,
                                 lambda t: 0.003 * (1 - 0.6 * t), mats["blade"])
            tip = path[-1]
            r_tip = math.hypot(tip.x, tip.y)
            a_tip = math.atan2(tip.y, tip.x)
            trail = [V(r_tip * math.cos(a_tip - spin * math.radians(40) * j / 20),
                       r_tip * math.sin(a_tip - spin * math.radians(40) * j / 20), tip.z - 0.004 * j / 20)
                     for j in range(21)]
            objs += gd.tube(f"B_Trail_{wi}_{k}", trail, mats["light"], 0.0026, (1.0, 0.05))
    return objs


# ------------------------------------------------------------------ C lily of light

def option_c(mats, step, bloom):
    """A lily drawn in light round the ivory one (rims, midribs and veins of light, open
    between them so the ivory lily shows), scaled about the throat; stamens of light."""
    s = {1: 1.5, 2: 2.0, 3: 2.6}[step]
    prof = [(r * s, 1.36 + (z - 1.36) * s) for r, z in gd.lily_profile(False, max(bloom, 0.2))]
    objs = []
    for k in range(6):
        radial, circ = gd.ring_frame(2 * math.pi * (k + 0.5) / 6)
        path = [V(0, 0, z) + radial * r for r, z in prof]
        wmax = 0.062 * s

        def wfn(t, wmax=wmax):
            return wmax * math.sin(math.pi * min(t / 0.985, 1) ** 0.85) ** 0.6 * (0.35 + 0.65 * smoothstep(t / 0.35))

        center = gd.smooth_path(path, 60)
        rims = ([], [])
        for i, p in enumerate(center):
            t = i / 59
            tan = (center[min(i + 1, 59)] - center[max(i - 1, 0)]).normalized()
            nrm = circ.cross(tan).normalized()
            w = wfn(t)
            rims[0].append(p - circ * (w / 2) + nrm * (0.1 * w))
            rims[1].append(p + circ * (w / 2) + nrm * (0.1 * w))
        for e, rim in enumerate(rims):
            objs += gd.tube(f"C_Rim_{k}_{e}", rim[3:], mats["light"], 0.0024, bulge=True)
        objs += gd.tube(f"C_Mid_{k}", center[2:-6], mats["light"], 0.0018, (1.0, 0.3))
        for j, u in enumerate((0.3, 0.45, 0.6, 0.75)):     # veins from the midrib to the rims
            i = int(u * 59)
            for e in range(2):
                vein = gd.smooth_path([center[i], center[i].lerp(rims[e][min(i + 5, 59)], 0.6),
                                       rims[e][min(i + 8, 59)]], 12)
                objs += gd.tube(f"C_Vein_{k}_{j}_{e}", vein, mats["light"], 0.0011, (1.0, 0.4))
    for k in range(6):                   # stamens of light
        radial, circ = gd.ring_frame(2 * math.pi * k / 6)
        r_end, z_end = 0.056 * s * 1.1, 1.36 + (1.722 - 1.36) * s * 0.92
        fil = gd.smooth_path([V(0, 0, 1.42) + radial * 0.01, V(0, 0, 1.36 + 0.2 * s) + radial * (0.022 * s),
                              V(0, 0, z_end - 0.04) + radial * (r_end * 0.8), V(0, 0, z_end) + radial * r_end], 30)
        objs += gd.tube(f"C_Stamen_{k}", fil, mats["light"], 0.0018, (1.0, 0.6))
        objs += gd.capsule(f"C_Anther_{k}", fil[-1], 0.005, 0.024, circ, mats["phial_lit"])
    objs += m.halo("C_Halo", (0, 0, prof[5][1] - 0.01), prof[5][0] * 1.12, 0.0042, (0, 0, 1), mats["light"],
                   tilt_deg=6, tilt_axis=(1, 0, 0))
    return objs


# ------------------------------------------------------------------ D light vortex

def option_d(mats, step, bloom):
    """Arms of light spiralling in from a wide funnel round the flower into its throat (thin
    where they start, thick as they arrive), more arms and a tighter funnel at each step,
    sparks along them."""
    rng = random.Random(5)
    n = {1: 6, 2: 9, 3: 12}[step]
    objs = []
    for layer, (z_start, r_scale) in enumerate(((1.30, 1.0), (1.86, 0.8))[: 1 if step == 1 else 2]):
      for k in range(n):
        phi0 = 2 * math.pi * (k + 0.5 * layer) / n
        r0 = (0.34 - 0.04 * (step - 1)) * r_scale
        z0 = z_start
        turns = 0.85
        pts, radii = [], []
        for i in range(60):
            u = i / 59
            r = r0 * (1 - u) ** 1.6 + 0.016 * u
            z = z0 + (THROAT - z0) * u ** 0.8
            a = phi0 + 2 * math.pi * turns * u ** 1.3
            pts.append(V(r * math.cos(a), r * math.sin(a), z))
            radii.append(0.12 + 0.88 * u ** 1.5)
        objs.append(c.curve_tube(f"D_Streak_{layer}_{k}", pts, radii, mats["light"], bevel=0.003, resolution=2))
        for j in range(2):
            i = rng.randint(10, 40)
            objs += gd.sphere(f"D_Spark_{layer}_{k}_{j}", pts[i], 0.003 + 0.001 * step, mats["phial_lit"])
    return objs


# ------------------------------------------------------------------ render

OPTIONS = [("A 金藤螺旋", option_a), ("B 光瓣旋輪", option_b), ("C 光之百合", option_c), ("D 聚光旋渦", option_d)]
STEP_NAMES = {1: "一段", 2: "二段", 3: "滿（龍擊砲）"}


def render_one(index, step):
    name, build = OPTIONS[index]
    c.reset_scene()
    mats = m.materials()
    mats["gold"] = gd.devices.gold_material()
    mats["phial_lit"] = c.make_material("Phial_Lit", c.PALETTE["glow"], roughness=0.1,
                                        emission=c.PALETTE["glow"], strength=3.0)
    m.glow_mode(mats)
    st.set_glow(mats["light"], "#FF9A10", GLOW[step])
    st.set_blade(mats["blade"], "#FFA828", "#FF8000", GLOW[step])
    st.set_glow(mats["core"], "#FFB030", GLOW[step] + 1.0)
    c.set_emission_strength(mats["phial_lit"], 3.0 + 2.0 * step)
    rng = random.Random(7)
    if step == 3:                        # the lily exactly as proposed, at Wyvern's Fire
        gd.design_b(mats, rng, True)
        bloom = 1.0
    else:
        bloom = BLOOM[step]
        gd.design_b(mats, rng, False, bloom=bloom)
        gd.sphere("Throat_Orb", (0, 0, THROAT), 0.012 + 0.01 * step, mats["phial_lit"])
    build(mats, step, bloom)
    target, dist = (0, 0, 1.5), 2.4
    st.stage_lights(target, dist, res=(300, 430) if TEST else (600, 860))
    if TEST:
        bpy.context.scene.cycles.samples = 8
    stem = f"lily_{name.split()[0]}_{step}"
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
            labels.append(f"{name}・{STEP_NAMES[step]}")
    out = os.path.join(OUT, "lily_charge_test.png" if TEST else "gunlance_lily_charge.png")
    st.labelled_strip(paths, labels, out, "聖百合銃槍：蓄力的力量感（原本的全部保留，只加；上：一段　中：二段　下：滿）",
                      cols=len(OPTIONS))
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
