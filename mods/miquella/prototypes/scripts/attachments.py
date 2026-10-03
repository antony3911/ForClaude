"""Add-ons the game still shows in its own style (user, 2026-10-03: "find every add-on we haven't
done; four versions each for me to review"). Things the game clips onto a weapon or fires out of
it, beyond the devices already in the game (the Wyrmstake needle, the Wyvernblast bud):

  lbg_drum    light bowgun Rapid Fire Mode: the hunter clips an ammo drum under the gun, like a
              tommy gun (the game's own drum still shows on our light bowgun)
  hbg_mag     heavy bowgun magazine (a Nexus mod hides "the light and heavy bowgun magazines",
              so the heavy bowgun shows one too; when exactly is to be checked in the game)
  hbg_shield  heavy bowgun guard: every heavy bowgun in Wilds carries a shield that unfolds to
              guard (auto-guard from the front); ours has none
  tracer      bow Tracer arrow: stuck in the monster, the next arrows home in on it, then it
              bursts (the earlier single proposal is version A)
  piercer     heavy bowgun Wyvernpiercer Ignition: a round that drills through the monster (the
              earlier gold thorn is version A)

Each item renders four versions (A-D) side by side in two rows: mounted / close up for the
drum and magazine, folded / guarding for the shield, stuck / charged for the tracer, the round /
breaking out of the hide for the piercer. Built from the same motifs as the weapons (ivory
strands, gold light, halos, scrolls, floating light drops); every part is solid (the game has no
see-through weapon material).

Usage: python attachments.py <item> <out_dir> [test] [A B C D]
"""
import math
import os
import random
import sys

ITEM = sys.argv[1] if len(sys.argv) > 1 else "lbg_drum"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join("out", ITEM)
FLAGS = sys.argv[3:]
TEST = "test" in FLAGS
PICK = [f for f in FLAGS if f in ("A", "B", "C", "D")] or ["A", "B", "C", "D"]

import bpy                               # noqa: E402
from mathutils import Vector             # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
sys.argv = [sys.argv[0], ITEM, OUT]      # devices and states read argv on import
import common as c                       # noqa: E402
import motifs as m                       # noqa: E402
from motifs import V, smoothstep         # noqa: E402
import devices                           # noqa: E402
import states as st                      # noqa: E402
import particle_fx as pf                 # noqa: E402
import gunlance_designs as gd            # noqa: E402

PI = math.pi


def materials():
    mats = m.materials()
    mats["gold"] = devices.gold_material()
    c.set_emission_strength(mats["gold"], 0.6)
    mats["phial_lit"] = c.make_material("Phial_Lit", c.PALETTE["glow"], roughness=0.1,
                                        emission=c.PALETTE["glow"], strength=3.0)
    mats["phial_dim"] = c.make_material("Phial_Dim", "#C9B78E", roughness=0.25,
                                        emission=c.PALETTE["glow"], strength=0.15)
    m.glow_mode(mats)
    return mats


def charge_up(mats):
    """Brighter gold for a charged / guarding state (same as the gunlance proposals)."""
    st.set_glow(mats["light"], "#FF9A10", 7.0)
    st.set_blade(mats["blade"], "#FFA828", "#FF8000", 7.0)
    st.set_glow(mats["core"], "#FFB030", 8.0)
    c.set_emission_strength(mats["phial_lit"], 8.0)


def polar(axis_pt, axis, phi, r):
    """Point at angle phi, radius r round an axis through axis_pt (axis = 'x' or 'y')."""
    if axis == "x":
        return axis_pt + V(0, r * math.cos(phi), r * math.sin(phi))
    return axis_pt + V(r * math.cos(phi), 0, r * math.sin(phi))


def light_bowgun():
    import light_bowgun as lb
    _, glow, beam = lb.build()
    c.set_emission_strength(glow, 2.5)
    c.set_emission_strength(beam, 3.0)


def heavy_bowgun():
    import bowgun as hb
    _, glow = hb.build()
    c.set_emission_strength(glow, 2.5)


# ================================================================== light bowgun: rapid fire drum
# Prototype axes: muzzle +Y, up +Z. The drum hangs under the receiver in front of the grip,
# its faces to the sides (axis X).

DRUM_C = V(0, 0.035, -0.12)
DRUM_R = 0.064
DRUM_W = 0.023
NECK_TOP = V(0, 0.035, -0.02)


def dpt(phi, r, x=0.0):
    return polar(DRUM_C + V(x, 0, 0), "x", phi, r)


def drum_neck(mats, rng, bottom_z):
    objs = m.woven_tube("Drum_Neck", [NECK_TOP, V(0, NECK_TOP.y, bottom_z)], 0.0105, mats["ivory"], rng)
    objs += m.halo("Drum_Neck_Band", NECK_TOP + V(0, 0, -0.01), 0.0122, 0.0022, (0, 0, 1), mats["light"])
    return objs


def drum_a(mats, rng):
    """Lantern: an openwork cage of ivory ribs between two rims, gold filigree lyres on each
    face round a lit hub, the rounds (light drops) standing round the inside."""
    objs = drum_neck(mats, rng, DRUM_C.z + DRUM_R + 0.002)
    for s in (-1, 1):
        x = s * DRUM_W
        objs += m.halo(f"A_Rim_{s}", DRUM_C + V(x, 0, 0), DRUM_R, 0.0034, (1, 0, 0), mats["ivory"])
        objs += m.halo(f"A_Rim_Gold_{s}", DRUM_C + V(x * 1.12, 0, 0), DRUM_R * 0.92, 0.0012, (1, 0, 0), mats["light"])
        plane = m.plane_mapper(DRUM_C + V(x * 1.14, 0, 0), (0, 1, 0), (0, 0, 1))
        for k in range(4):
            ang = 45 + 90 * k
            base = (0.011 * math.cos(math.radians(ang)), 0.011 * math.sin(math.radians(ang)))
            objs += gd.lyre(f"A_Lyre_{s}_{k}", plane, base, 0.034, 1.1, 0.0015, mats, spread=26, heading=ang)
        objs += m.halo(f"A_Hub_Halo_{s}", DRUM_C + V(x * 1.16, 0, 0), 0.0105, 0.0015, (1, 0, 0), mats["light"])
        objs += m.droplet(f"A_Hub_{s}", DRUM_C + V(x * 1.02, 0, 0), 0.0068, (s, 0, 0), mats["phial_lit"], stretch=0.9)
    for k in range(12):                  # the cage: ribs leaning a little, bulging out
        a0 = 2 * PI * k / 12
        pts = [dpt(a0 + 0.35 * (u - 0.5), DRUM_R * (1 + 0.08 * math.sin(PI * u)), -DRUM_W + 2 * DRUM_W * u)
               for u in (i / 16 for i in range(17))]
        objs.append(c.curve_tube(f"A_Rib_{k}", pts, [0.65 + 0.35 * math.sin(PI * i / 16) for i in range(17)],
                                 mats["ivory"], bevel=0.0024, resolution=2))
    girdle = [dpt(2 * PI * i / 95, DRUM_R * 1.085, 0.0026 * math.sin(2 * PI * 6 * i / 95)) for i in range(96)]
    objs.append(c.curve_tube("A_Girdle", girdle, [1.0] * 96, mats["light"], bevel=0.0011, resolution=2))
    for k in range(10):                  # the rounds
        a = 2 * PI * k / 10 + 0.3
        objs += m.droplet(f"A_Round_{k}", dpt(a, DRUM_R * 0.66), 0.0074, V(0, math.cos(a), math.sin(a)),
                          mats["phial_lit"], stretch=1.6)
    return objs


def drum_b(mats, rng):
    """Orrery: no drum at all, three rings of light round an ivory axle, the rounds floating
    between them as lit drops in their own small halos (they wheel round while firing)."""
    objs = gd.capsule("B_Axle", DRUM_C, 0.0105, 2 * DRUM_W + 0.016, (1, 0, 0), mats["ivory"])
    for s in (-1, 1):
        objs += m.halo(f"B_Rim_{s}", DRUM_C + V(s * DRUM_W, 0, 0), DRUM_R, 0.0032, (1, 0, 0), mats["light"],
                       tilt_deg=7 * s, tilt_axis=(0, 0, 1))
        plane = m.plane_mapper(DRUM_C + V(s * (DRUM_W + 0.0085), 0, 0), (0, 1, 0), (0, 0, 1))
        for k in range(5):
            ang = 72 * k + 12
            o = (0.0075 * math.cos(math.radians(ang)), 0.0075 * math.sin(math.radians(ang)))
            objs += m.tendril(f"B_Cap_{s}_{k}", plane, o, ang, 0.024, 1.2, 0.0017, mats, strands=2, curl_start=0.35)
    objs += m.halo("B_Equator", DRUM_C, DRUM_R * 1.07, 0.0042, (1, 0, 0), mats["light"])
    for k in range(8):
        a = 2 * PI * k / 8 + 0.2
        tangent = V(0, -math.sin(a), math.cos(a))
        objs += m.floating_phials(f"B_Round_{k}", [dpt(a, DRUM_R * 0.7)], tangent, tangent, mats, size=0.0078)
        spoke = [dpt(a, 0.012 + (DRUM_R * 0.7 - 0.024) * i / 11) for i in range(12)]
        objs.append(c.curve_tube(f"B_Spoke_{k}", spoke, [1 - 0.6 * i / 11 for i in range(12)], mats["light"],
                                 bevel=0.0009, resolution=1))
    stem = gd.smooth_path([NECK_TOP, V(-0.016, 0.034, -0.04), V(-0.034, 0.036, -0.075), V(-0.036, 0.035, -0.1),
                           V(-0.031, 0.035, DRUM_C.z)], 60)
    objs += m.rope("B_Stem", stem, 0.0072, mats, strands=3, gold=True, taper=0.35, merge=0.999)
    return objs


def drum_c(mats, rng):
    """Double lily: two six-tepal lilies back to back, a round of light cradled in every tepal,
    stamens and a lit pistil at the heart, a ring of light framing them."""
    objs = []
    for s, scale in ((1, 1.0), (-1, 0.84)):
        for k in range(6):
            a = 2 * PI * k / 6 + PI / 2 + (PI / 6 if s < 0 else 0)
            radial, circ = V(0, math.cos(a), math.sin(a)), V(0, -math.sin(a), math.cos(a))
            sc = scale * (1.0 if k % 2 == 0 else 0.9)
            prof = [(0.008, 0.002), (0.02, 0.008), (0.036, 0.013), (0.05, 0.0135), (0.061, 0.009)]
            path = [DRUM_C + radial * (r * sc) + V(s * xf, 0, 0) for r, xf in prof]
            wmax = 0.031 * sc
            petal, rims, mid = gd.sheet(
                f"C_Tepal_{s}_{k}", path, circ,
                lambda t, wmax=wmax: wmax * math.sin(PI * min(t / 0.985, 1) ** 0.85) ** 0.6
                * (0.35 + 0.65 * smoothstep(t / 0.35)), mats["ivory"], cup=0.12 * s, thick=0.0022, samples=40)
            objs += petal
            for e, rim in enumerate(rims):
                objs += gd.tube(f"C_Tepal_Rim_{s}_{k}_{e}", rim[3:], mats["light"], 0.0009, bulge=True)
            objs += gd.tube(f"C_Tepal_Mid_{s}_{k}", mid[2:-6], mats["light"], 0.0008, (1.0, 0.3))
            if s > 0:
                objs += m.droplet(f"C_Round_{k}", DRUM_C + radial * 0.034 + V(0.016, 0, 0), 0.0058, radial,
                                  mats["phial_lit"], stretch=1.5)
    for k in range(6):                   # stamens
        a = 2 * PI * (k + 0.5) / 6 + PI / 2
        radial, circ = V(0, math.cos(a), math.sin(a)), V(0, -math.sin(a), math.cos(a))
        fil = gd.smooth_path([DRUM_C + V(0.004, 0, 0), DRUM_C + radial * 0.009 + V(0.016, 0, 0),
                              DRUM_C + radial * 0.019 + V(0.027, 0, 0)], 16)
        objs += gd.tube(f"C_Stamen_{k}", fil, mats["light"], 0.0010, (1.0, 0.6))
        objs += gd.capsule(f"C_Anther_{k}", fil[-1], 0.0022, 0.008, circ, mats["phial_lit"])
    objs += m.droplet("C_Pistil", DRUM_C + V(0.012, 0, 0), 0.0066, (1, 0, 0), mats["phial_lit"], stretch=1.4)
    objs += m.halo("C_Calyx", DRUM_C, 0.012, 0.0045, (1, 0, 0), mats["ivory"])
    objs += m.halo("C_Frame", DRUM_C + V(0.004, 0, 0), DRUM_R * 1.1, 0.0028, (1, 0, 0), mats["light"],
                   tilt_deg=5, tilt_axis=(0, 0, 1))
    stem = gd.smooth_path([NECK_TOP, V(-0.004, 0.034, -0.05), V(-0.012, 0.036, -0.085), V(-0.008, 0.035, DRUM_C.z)],
                          50)
    objs += m.rope("C_Stem", stem, 0.0075, mats, strands=3, gold=True, taper=0.3, merge=0.999)
    return objs


def drum_d(mats, rng):
    """Scroll: a cord of ivory wound with gold coiled like a watch spring between two rims,
    the rounds strung along it like a belt (big outside, small toward the curl at the heart)."""
    objs = drum_neck(mats, rng, DRUM_C.z + DRUM_R + 0.002)
    for s in (-1, 1):
        objs += m.halo(f"D_Rim_{s}", DRUM_C + V(s * DRUM_W, 0, 0), DRUM_R, 0.0034, (1, 0, 0), mats["ivory"])
        objs += m.halo(f"D_Rim_Gold_{s}", DRUM_C + V(s * DRUM_W * 1.12, 0, 0), DRUM_R * 0.95, 0.0012, (1, 0, 0),
                       mats["light"])
    n = 260
    spiral = []
    for i in range(n):
        u = i / (n - 1)
        spiral.append(dpt(PI / 2 + 2 * PI * 2.4 * u, DRUM_R * (0.97 - 0.82 * u ** 0.9)))
    objs += m.rope("D_Spring", spiral, 0.0046, mats, strands=3, gold=True, taper=0.65, merge=0.999)
    for j in range(13):
        u = 0.06 + 0.86 * j / 12
        p = spiral[int(u * (n - 1))]
        for s in (-1, 1):
            objs += gd.sphere(f"D_Round_{j}_{s}", p + V(s * 0.0072, 0, 0), 0.0058 * (1 - 0.45 * u), mats["phial_lit"])
    for k in range(3):                   # three ivory spokes holding the spring to the rims
        a = PI / 2 + 2 * PI * k / 3 + 0.5
        for s in (-1, 1):
            spoke = [dpt(a, DRUM_R * f, s * DRUM_W * (0.4 + 0.6 * f)) for f in (x / 9 for x in range(10))]
            objs.append(c.curve_tube(f"D_Spoke_{k}_{s}", spoke, [0.6 + 0.4 * i / 9 for i in range(10)],
                                     mats["ivory"], bevel=0.0019, resolution=1))
    objs += m.droplet("D_Heart", DRUM_C, 0.0072, (1, 0, 0), mats["phial_lit"], stretch=0.5)
    return objs


# ================================================================== heavy bowgun: magazine
# Hangs under the receiver in front of the grip, raked forward.

MAG_TOP = V(0, 0.025, -0.055)


def mag_path(n=40, length=0.2):
    return gd.smooth_path([MAG_TOP, MAG_TOP + V(0, 0.012, -0.065 * length / 0.2),
                           MAG_TOP + V(0, 0.032, -0.13 * length / 0.2), MAG_TOP + V(0, 0.06, -length)], n)


def mag_a(mats, rng):
    """Woven: a curved magazine of woven ivory like the stock, gold bands, a lit drop at the
    foot under a crown of scrolls, and the rounds left floating in a row along its front."""
    path = mag_path()
    objs = m.woven_tube("A_Mag", path, 0.029, mats["ivory"], rng, radius_fn=lambda u: 1 - 0.12 * u)
    tans, _, _ = m.frames(path)
    for k, u in enumerate((0.12, 0.5, 0.88)):
        i = int(u * (len(path) - 1))
        objs += m.halo(f"A_Band_{k}", path[i], 0.031 * (1 - 0.12 * u), 0.0026, tans[i], mats["light"])
    foot = path[-1]
    objs += gd.capsule("A_Foot", foot + tans[-1] * 0.004, 0.027, 0.014, tans[-1], mats["ivory"])
    fu, fv, _ = m.basis(tans[-1])
    for k in range(6):
        a = 2 * PI * k / 6
        plane = m.plane_mapper(foot + tans[-1] * 0.01, fu * math.cos(a) + fv * math.sin(a), tans[-1])
        objs += m.tendril(f"A_Foot_Scroll_{k}", plane, (0.02, 0), 30, 0.03, 1.2, 0.0022, mats, strands=2,
                          curl_start=0.35)
    objs += m.droplet("A_Foot_Light", foot + tans[-1] * 0.03, 0.0095, tans[-1], mats["phial_lit"], stretch=1.4)
    pts = [path[int(u * (len(path) - 1))] + V(0, 0.05, 0) for u in (0.12, 0.3, 0.48, 0.66, 0.84)]
    objs += m.floating_phials("A_Count", pts, (0, 0, -1), (0, 1, 0), mats, size=0.0085)
    return objs


def mag_b(mats, rng):
    """Column of light: the rounds as a stack of lit discs, three ivory strands twisting
    round them and closing into a point at the foot, halo collars top and bottom."""
    axis = V(0, 0.28, -1).normalized()
    top = MAG_TOP + axis * 0.012
    length = 0.19
    objs = []
    for k in range(8):
        objs += gd.capsule(f"B_Disc_{k}", top + axis * (0.016 + 0.021 * k), 0.027 - 0.0009 * k, 0.011, axis,
                           mats["phial_lit"])
    u0, v0, _ = m.basis(axis)
    for j in range(3):
        pts, radii = [], []
        for i in range(120):
            t = i / 119
            r = 0.036 * (1 - smoothstep((t - 0.78) / 0.22) * 0.97)
            a = 2 * PI * j / 3 + 2 * PI * 0.75 * t
            pts.append(top + axis * (length * t) + (u0 * math.cos(a) + v0 * math.sin(a)) * r)
            radii.append(1.0 - 0.6 * t)
        objs += m.rope(f"B_Strand_{j}", pts, 0.0046, mats, strands=2, gold=(j == 0), taper=0.5, merge=0.999)
    for k, (t, r) in enumerate(((0.0, 0.041), (0.78, 0.034))):
        objs += m.halo(f"B_Collar_{k}", top + axis * (length * t), r, 0.0028, axis, mats["light"],
                       tilt_deg=6 * (-1) ** k, tilt_axis=(1, 0, 0))
    objs += m.droplet("B_Point", top + axis * (length + 0.012), 0.0085, axis, mats["phial_lit"], stretch=1.8)
    return objs


def mag_c(mats, rng):
    """Reliquary: a small Gothic casket of ivory pillars with pointed arch windows framed in
    gold light, a big drop of light hanging inside, an inverted spire of scrolls at the foot."""
    axis = V(0, 0.2, -1).normalized()
    side_y = V(0, 1, 0.2).normalized()
    top = MAG_TOP + axis * 0.005
    h, wx, wy = 0.15, 0.024, 0.034
    objs = []
    corners = [(sx, sy) for sx in (-1, 1) for sy in (-1, 1)]
    for sx, sy in corners:
        p0 = top + V(sx * wx, 0, 0) + side_y * (sy * wy)
        objs.append(c.curve_tube(f"C_Pillar_{sx}_{sy}", [p0, p0 + axis * h], [1, 1], mats["ivory"], bevel=0.0042,
                                 resolution=3))
    for k, t in enumerate((0.0, 1.0)):   # plinths top and foot
        ctr = top + axis * (h * t)
        for sx in (-1, 1):
            objs.append(c.curve_tube(f"C_BarX_{k}_{sx}", [ctr + V(sx * wx, 0, 0) - side_y * wy,
                                                          ctr + V(sx * wx, 0, 0) + side_y * wy],
                                     [1, 1], mats["ivory"], bevel=0.0036, resolution=2))
        for sy in (-1, 1):
            objs.append(c.curve_tube(f"C_BarY_{k}_{sy}", [ctr - V(wx, 0, 0) + side_y * (sy * wy),
                                                          ctr + V(wx, 0, 0) + side_y * (sy * wy)],
                                     [1, 1], mats["ivory"], bevel=0.0036, resolution=2))
    for face, (normal, across, half) in enumerate(((V(1, 0, 0), side_y, wy), (V(-1, 0, 0), side_y, wy),
                                                   (side_y, V(1, 0, 0), wx), (-side_y, V(1, 0, 0), wx))):
        off = normal * (wx if face < 2 else wy) * 1.04
        w = half * 0.7
        z_lo, z_hi = 0.025, 0.125      # the arch points down (the casket hangs upside down)
        left = [top + off + axis * (z_lo + (z_hi - z_lo) * 0.35 * f) + across * (-w) for f in (i / 20 for i in range(21))]
        right = [top + off + axis * (z_lo + (z_hi - z_lo) * 0.35 * f) + across * w for f in (i / 20 for i in range(21))]
        tip = top + off + axis * z_hi
        arc_l = gd.smooth_path([left[-1], left[-1] + axis * 0.04 + across * (w * 0.15), tip], 24)
        arc_r = gd.smooth_path([right[-1], right[-1] + axis * 0.04 - across * (w * 0.15), tip], 24)
        objs += gd.tube(f"C_Arch_L_{face}", left + arc_l[1:], mats["light"], 0.0014)
        objs += gd.tube(f"C_Arch_R_{face}", right + arc_r[1:], mats["light"], 0.0014)
        objs += gd.tube(f"C_Arch_Top_{face}", [left[0], right[0]], mats["light"], 0.0012)
    objs += m.droplet("C_Relic", top + axis * 0.085, 0.016, axis, mats["phial_lit"], stretch=1.6)
    objs += m.halo("C_Relic_Halo", top + axis * 0.07, 0.019, 0.0018, axis, mats["light"])
    foot = top + axis * h
    for k in range(4):                   # inverted spire of scrolls
        a = PI / 4 + PI / 2 * k
        out = (V(math.cos(a), 0, 0) + side_y * math.sin(a)).normalized()
        plane = m.plane_mapper(foot + out * 0.02, axis, out)
        objs += m.tendril(f"C_Spire_{k}", plane, (0, 0), 25, 0.05, -1.3, 0.0026, mats, strands=2, curl_start=0.4)
    objs.append(c.curve_tube("C_Finial", [foot, foot + axis * 0.05], [1.0, 0.1], mats["ivory"], bevel=0.0045,
                             resolution=3))
    objs += m.droplet("C_Finial_Light", foot + axis * 0.055, 0.006, axis, mats["phial_lit"], stretch=1.4)
    return objs


def mag_d(mats, rng):
    """Floating rounds: no magazine, a chain of lit drops in their own halos hanging in an arc
    under the gun, strung on a vine of gold light from a scroll bracket (spent drops go out)."""
    arc = gd.smooth_path([MAG_TOP + V(0, 0, 0.01), MAG_TOP + V(0, 0.01, -0.07), MAG_TOP + V(0, 0.045, -0.15),
                          MAG_TOP + V(0, 0.11, -0.2), MAG_TOP + V(0, 0.18, -0.205)], 80)
    tans, _, _ = m.frames(arc)
    objs = m.rope("D_Vine", arc, 0.0024, mats, strands=2, gold=False, taper=0.4, merge=0.999, strand_mat="light")
    plane = m.plane_mapper(MAG_TOP + V(0, 0, 0.004), (0, 1, 0), (0, 0, 1))
    objs += gd.lyre("D_Bracket", plane, (0, 0), 0.05, 1.2, 0.0034, {**mats}, spread=55, heading=-90,
                    strand_mat="ivory")
    for k in range(6):
        u = 0.16 + 0.16 * k
        i = int(u * (len(arc) - 1))
        size = 0.0125 - 0.0011 * k
        mat_key = "phial_lit" if k < 4 else "phial_dim"
        objs += m.droplet(f"D_Round_{k}", arc[i], size, tans[i], mats[mat_key], stretch=1.4)
        objs += m.halo(f"D_Round_Halo_{k}", arc[i] + tans[i] * (size / 3), size * 1.85, size * 0.15, tans[i],
                       mats["light"])
    return objs


# ================================================================== heavy bowgun: guard shield
# Hinged round the conduit (axis +Y at z 0.03) behind the second accelerator ring; folded along
# the barrel when not guarding, open across the front to guard.

HY = 0.47
AX = V(0, HY, 0.03)


def shield_collar(mats):
    objs = m.halo("Shield_Collar", AX, 0.054, 0.007, (0, 1, 0), mats["ivory"])
    objs += m.halo("Shield_Collar_Gold", AX + V(0, 0.008, 0), 0.056, 0.0018, (0, 1, 0), mats["light"])
    return objs


def rib(name, phi, open_, mats, length=0.23, r0=0.055, scroll=True):
    """An ivory rib hinged on the collar: folded forward along the barrel, or swung out across
    the front (a little cupped forward); a scroll curls at its end."""
    radial = polar(V(0, 0, 0), "y", phi, 1.0)
    root = AX + radial * r0
    if open_:
        tip_dir, bow = (radial + V(0, 0.12, 0)).normalized(), V(0, 0.03, 0)
    else:
        tip_dir, bow = (V(0, 1, 0) + radial * 0.05).normalized(), radial * 0.012
    path = gd.smooth_path([root, root + tip_dir * (length * 0.5) + bow, root + tip_dir * length], 40)
    objs = [c.curve_tube(name, path, [1 - 0.45 * i / 39 for i in range(40)], mats["ivory"], bevel=0.0048,
                         resolution=2)]
    objs += m.wound_cord(name + "_Vine", path, 0.0052, 2.5, 0.0011, mats, strand_mat="light", taper=0.4)
    if scroll:
        normal = radial.cross(V(0, 1, 0)).normalized()
        plane = m.plane_mapper(path[-1], tip_dir, tip_dir.cross(normal).normalized())
        objs += m.tendril(name + "_Scroll", plane, (0, 0), 20, 0.045, -1.3, 0.0034, mats, strands=2,
                          curl_start=0.35)
    return objs, path


def shield_a(mats, rng, open_):
    """Sigil: six ivory ribs swing out like an umbrella and the shield's tree sigil of light
    grows across them (folded, the sigil shrinks to a drop of light at the collar)."""
    objs = shield_collar(mats)
    for k in range(6):
        objs += rib(f"A_Rib_{k}", PI / 2 + 2 * PI * k / 6, open_, mats, length=0.24)[0]
    if open_:
        objs += devices.small_sigil(mats, AX + V(0, 0.035, 0), 0.95)
    else:
        objs += m.droplet("A_Seed", AX + V(0, 0.016, 0.06), 0.008, (0, 1, 0), mats["phial_lit"], stretch=1.2)
        objs += m.halo("A_Seed_Halo", AX + V(0, 0.022, 0.06), 0.014, 0.0017, (0, 1, 0), mats["light"])
    return objs


def shield_b(mats, rng, open_):
    """Wings: two ivory wings folded back along the sides of the barrel; guarding, they swing
    out across the front and fan their feathers of light up and down into a round guard,
    a light drop at the tip of every other feather."""
    objs = shield_collar(mats)
    for s in (-1, 1):
        side = "L" if s < 0 else "R"
        if open_:
            ctrl = [AX + V(s * 0.05, 0.012, 0.0), AX + V(s * 0.09, 0.02, 0.028), AX + V(s * 0.13, 0.026, 0.026),
                    AX + V(s * 0.16, 0.03, 0.0)]
        else:
            ctrl = [AX + V(s * 0.05, 0.0, 0.0), AX + V(s * 0.064, -0.05, 0.014), AX + V(s * 0.068, -0.1, 0.014),
                    AX + V(s * 0.066, -0.15, 0.004)]
        arm = gd.smooth_path(ctrl, 50)
        objs.append(c.curve_tube(f"B_Arm_{side}", arm, [1 - 0.5 * i / 49 for i in range(50)], mats["ivory"],
                                 bevel=0.0075, resolution=3))
        objs += m.wound_cord(f"B_Arm_Vine_{side}", arm, 0.0083, 3.0, 0.0013, mats, strand_mat="light", taper=0.5)
        n = 7
        for i in range(n):
            f = i / (n - 1)
            p0 = arm[int((0.3 + 0.7 * (1 - abs(2 * f - 1))) * 49)]
            length = 0.11 + 0.08 * math.sin(PI * f) ** 0.6
            if open_:
                th = math.radians(78 - 156 * f)         # fanned from straight up to straight down
                d = V(s * math.cos(th), 0.1, math.sin(th)).normalized()
                normal = V(0, 1, 0)
                bow = V(0, 0.012, 0)
            else:
                d = V(s * 0.08, -1, 0.05 * (f - 0.5)).normalized()
                normal = V(s, 0, 0)
                bow = V(s * 0.006, 0, 0)
                p0 = p0 + V(s * 0.003 * i, 0, 0)
            path = [p0, p0 + d * (0.5 * length) + bow, p0 + d * length]
            width = 0.036

            def w(t, width=width):
                return width * math.sin(PI * min(t / 0.985, 1) ** 0.5) ** 0.75

            name = f"B_Feather_{side}_{i}"
            objs += m.path_blade(name, path, normal, w, lambda t: 0.004 * (1 - 0.7 * t), mats["blade"])
            rach = gd.smooth_path(path, 30)
            objs += gd.tube(name + "_Rachis", rach[:27], mats["core"], 0.0014, (1.0, 0.3))
            if open_ and i % 2 == 0:
                objs += m.floating_phials(f"B_Drop_{side}_{i}", [path[-1] + d * 0.02], d, (0, 1, 0), mats,
                                          size=0.0085)
        for j in range(9):               # ivory coverts along the arm
            p = arm[int((0.15 + 0.09 * j) * 49)]
            d = (V(0, 0.02, 1) if open_ else V(0, -1, 0.15)).normalized()
            objs += m.droplet(f"B_Covert_{side}_{j}", p + d * 0.006, 0.0075, d, mats["ivory"], stretch=1.8)
    objs += m.droplet("B_Heart", AX + V(0, 0.03, 0.06), 0.011, (0, 1, 0), mats["phial_lit"], stretch=1.2)
    objs += m.halo("B_Heart_Halo", AX + V(0, 0.036, 0.06), 0.02, 0.0022, (0, 1, 0), mats["light"])
    return objs


def shield_c(mats, rng, open_):
    """Lily: six ivory tepals closed into a long bud round the barrel; guarding, they open into
    a lily facing the monster, gold light along the rims, stamens round the conduit."""
    objs = shield_collar(mats)
    if open_:
        prof = [(0.052, 0.0), (0.085, 0.03), (0.14, 0.05), (0.2, 0.05), (0.245, 0.033), (0.26, 0.012)]
        wmax = 0.13
    else:
        prof = [(0.052, 0.0), (0.064, 0.05), (0.07, 0.11), (0.066, 0.17), (0.055, 0.21), (0.05, 0.23)]
        wmax = 0.068
    for k in range(6):
        phi = PI / 2 + 2 * PI * k / 6
        radial, circ = polar(V(0, 0, 0), "y", phi, 1.0), polar(V(0, 0, 0), "y", phi + PI / 2, 1.0)
        sc = 1.0 if k % 2 == 0 else 0.92
        path = [AX + radial * (r * (sc if open_ else 1.0)) + V(0, dy, 0) for r, dy in prof]
        w = wmax * (sc if open_ else 1.0)
        petal, rims, mid = gd.sheet(
            f"C_Tepal_{k}", path, circ,
            lambda t, w=w: w * math.sin(PI * min(t / 0.985, 1) ** 0.85) ** 0.6 * (0.35 + 0.65 * smoothstep(t / 0.3)),
            mats["ivory"], cup=0.1, thick=0.003)
        objs += petal
        for e, rim in enumerate(rims):
            objs += gd.tube(f"C_Tepal_Rim_{k}_{e}", rim[4:], mats["light"], 0.0016, bulge=True)
        objs += gd.tube(f"C_Tepal_Mid_{k}", mid[2:-8], mats["light"], 0.0014, (1.0, 0.3))
    if open_:
        for k in range(6):
            phi = PI / 2 + 2 * PI * (k + 0.5) / 6
            radial, circ = polar(V(0, 0, 0), "y", phi, 1.0), polar(V(0, 0, 0), "y", phi + PI / 2, 1.0)
            fil = gd.smooth_path([AX + radial * 0.05, AX + radial * 0.07 + V(0, 0.05, 0),
                                  AX + radial * 0.1 + V(0, 0.08, 0)], 24)
            objs += gd.tube(f"C_Stamen_{k}", fil, mats["light"], 0.0022, (1.0, 0.6))
            objs += gd.capsule(f"C_Anther_{k}", fil[-1], 0.005, 0.02, circ, mats["phial_lit"])
        objs += m.halo("C_Halo", AX + V(0, 0.02, 0), 0.285, 0.0042, (0, 1, 0), mats["light"], tilt_deg=4,
                       tilt_axis=(1, 0, 0))
    return objs


def shield_d(mats, rng, open_):
    """Rose window: eight ivory spokes and three rings of light; folded, the rings sit stacked
    round the barrel and the spokes lie along it; guarding, the rings spread into a wheel,
    scrolls of light fill the gaps and a lit drop floats at each spoke's end."""
    objs = shield_collar(mats)
    tips = []
    for k in range(8):
        parts, path = rib(f"D_Spoke_{k}", PI / 8 + 2 * PI * k / 8, open_, mats, length=0.22, scroll=False)
        objs += parts
        tips.append(path[-1])
    if open_:
        for k, r in enumerate((0.11, 0.18, 0.255)):
            objs += m.halo(f"D_Ring_{k}", AX + V(0, 0.012 + 0.012 * k, 0), r, 0.0036 + 0.0008 * k, (0, 1, 0),
                           mats["light"])
        for k in range(8):
            phi = PI / 8 + 2 * PI * (k + 0.5) / 8
            radial = polar(V(0, 0, 0), "y", phi, 1.0)
            plane = m.plane_mapper(AX + V(0, 0.026, 0), radial, radial.cross(V(0, 1, 0)).normalized())
            objs += gd.lyre(f"D_Lyre_{k}", plane, (0.19, 0), 0.05, 1.1, 0.0022, mats, spread=26, heading=0)
            objs += gd.lyre(f"D_Lyre_In_{k}", plane, (0.115, 0), 0.04, 1.0, 0.0018, mats, spread=30, heading=0)
        for k, p in enumerate(tips):
            radial = (p - AX - V(0, p.y - AX.y, 0)).normalized()
            objs += m.floating_phials(f"D_Phial_{k}", [p + radial * 0.022], radial, (0, 1, 0), mats, size=0.0105)
    else:
        for k, (dy, r) in enumerate(((0.05, 0.068), (0.1, 0.07), (0.15, 0.072))):
            objs += m.halo(f"D_Ring_{k}", AX + V(0, dy, 0), r, 0.0034, (0, 1, 0), mats["light"])
    return objs


# ================================================================== bow: tracer arrow
# The hide's top face is z 0; the arrow went in at the origin.

T_DIR = V(0.5, 0.2, -1).normalized()


def tracer_arrow(mats):
    objs = devices.light_arrow(mats, T_DIR * 0.05, T_DIR, name="Tracer")
    nock = T_DIR * (0.05 - 0.42)
    objs += m.droplet("Tracer_Nock", nock, 0.0085, -T_DIR, mats["phial_lit"], stretch=1.2)
    objs += m.halo("Tracer_Collar", nock + T_DIR * 0.05, 0.016, 0.0018, T_DIR, mats["light"])
    return objs


def surface_plane(z=0.0015):
    return m.plane_mapper(V(0, 0, z), (1, 0, 0), (0, 1, 0))


def tracer_a(mats, rng, charged):
    """Sigil (the earlier proposal): gold cracks round the arrow and a small tree sigil
    floating above it; charged, three rings stack up under the sigil."""
    glow = c.make_material("A_Crack_Light", c.PALETTE["glow"], roughness=0.2, emission=c.PALETTE["glow"],
                           strength=6.0)
    objs = devices.gold_cracks("A_Crack", V(0, 0, 0.001), 9 if charged else 6, 0.05 if charged else 0.035, glow, seed=8)
    objs += devices.small_sigil(mats, V(0, -0.02, 0.2), 0.22)
    if charged:
        for k in range(3):
            objs += m.halo(f"A_Stack_{k}", V(0, -0.02, 0.06 + 0.035 * k), 0.035 + 0.012 * k, 0.0022, (0, 0, 1),
                           mats["light"])
    return objs


def tracer_b(mats, rng, charged):
    """Bloom: an ivory flower opens on the hide round the arrow, rimmed in gold light;
    charged, it lies wide open, a pistil of light rises and a ring floats over it."""
    objs = []
    open_deg = 78 if charged else 42
    for k in range(5):
        phi = 2 * PI * k / 5 + 0.3
        radial = V(math.cos(phi), math.sin(phi), 0)
        circ = V(-math.sin(phi), math.cos(phi), 0)
        a = math.radians(open_deg)
        out = radial * math.sin(a) + V(0, 0, 1) * math.cos(a)
        base = radial * 0.012 + V(0, 0, 0.002)
        path = [base + out * (0.09 * f) + V(0, 0, 0.014 * math.sin(PI * f)) for f in (0, 0.25, 0.5, 0.75, 1.0)]
        petal, rims, mid = gd.sheet(f"B_Petal_{k}", path, circ,
                                    lambda t: 0.055 * math.sin(PI * min(t / 0.98, 1) ** 0.7) ** 0.7,
                                    mats["ivory"], cup=0.15, thick=0.002, samples=40)
        objs += petal
        for e, rim in enumerate(rims):
            objs += gd.tube(f"B_Petal_Rim_{k}_{e}", rim[3:], mats["light"], 0.0011, bulge=True)
        objs += gd.tube(f"B_Petal_Mid_{k}", mid[2:-6], mats["light"], 0.001, (1.0, 0.3))
    if charged:
        objs += gd.tube("B_Pistil", [V(0, 0, 0.0), V(0, 0, 0.09)], mats["light"], 0.0035, (1.0, 0.4))
        objs += m.droplet("B_Pistil_Light", V(0, 0, 0.1), 0.011, (0, 0, 1), mats["phial_lit"], stretch=1.3)
        objs += m.halo("B_Halo", V(0, 0, 0.12), 0.045, 0.0025, (0, 0, 1), mats["light"])
    else:
        objs += m.droplet("B_Heart", V(0, 0, 0.012), 0.009, (0, 0, 1), mats["phial_lit"], stretch=1.0)
    return objs


def tracer_c(mats, rng, charged):
    """Reticle: three rings of light turning round the arrow like a gyroscope, five drops
    circling it; each hit lights one (stuck: two lit; charged: all five)."""
    ctr = V(0.012, 0.005, 0.07)
    objs = []
    for k, (r, tilt, ax) in enumerate(((0.06, 0, (1, 0, 0)), (0.05, 55, (1, 0, 0)), (0.04, 55, (0, 1, 0)))):
        objs += m.halo(f"C_Ring_{k}", ctr, r, 0.0025, (0, 0, 1), mats["light"], tilt_deg=tilt, tilt_axis=ax)
    lit = 5 if charged else 2
    for k in range(5):
        a = 2 * PI * k / 5 + 0.4
        p = ctr + V(0.085 * math.cos(a), 0.085 * math.sin(a), 0.01 * math.sin(3 * a))
        tangent = V(-math.sin(a), math.cos(a), 0)
        if k < lit:
            objs += m.floating_phials(f"C_Count_{k}", [p], tangent, tangent, mats, size=0.0085)
        else:
            objs += m.droplet(f"C_Count_{k}", p, 0.0085, tangent, mats["phial_dim"], stretch=1.4)
            objs += m.halo(f"C_Count_Halo_{k}", p + tangent * 0.003, 0.0157, 0.0013, tangent, mats["ivory"])
    if charged:
        objs += m.halo("C_Ground", V(0, 0, 0.003), 0.1, 0.003, (0, 0, 1), mats["light"])
    return objs


def tracer_d(mats, rng, charged):
    """Gold vines: scrolls of gold light spread over the hide from the arrow like roots; each
    hit grows them; charged, they reach out and buds of light swell at their ends."""
    plane = surface_plane()
    objs = []
    reach = 0.17 if charged else 0.1
    for k in range(6):
        heading = 60 * k + rng.uniform(-12, 12)
        o = (0.01 * math.cos(math.radians(heading)), 0.01 * math.sin(math.radians(heading)))
        turns = 1.3 * (1 if k % 2 else -1)
        objs += m.tendril(f"D_Vine_{k}", plane, o, heading, reach * rng.uniform(0.85, 1.15), turns, 0.0042, mats,
                          strands=2, gold=False, strand_mat="light", curl_start=0.55,
                          offshoots=[(0.35, 1 if k % 2 else -1, 0.45, -turns * 0.8)])
        if charged:
            h = math.radians(heading)
            tip = V(math.cos(h), math.sin(h), 0) * (reach * 0.62) + V(0, 0, 0.012)
            objs += m.floating_phials(f"D_Bud_{k}", [tip], (0, 0, 1), (0, 0, 1), mats, size=0.0075)
    objs += m.halo("D_Root", V(0, 0, 0.003), 0.016, 0.0028, (0, 0, 1), mats["light"])
    return objs


# ================================================================== heavy bowgun: Wyvernpiercer

def piercer_a(mats, length, tip, d, name):
    """Gold thorn (the earlier proposal)."""
    return devices.thorn(mats, length, tip, d, name)


def piercer_b(mats, length, tip, d, name):
    """Lance of light: a leaf-shaped point of light crossed by a narrower one, a braided ivory
    tail through three rings of light, a drop of light at the end."""
    side = d.orthogonal().normalized()
    up = d.cross(side).normalized()
    head0 = tip - d * length * 0.5

    def w(t):
        return length * 0.17 * math.sin(PI * min(t / 0.97, 1) ** 0.62) ** 0.9

    def th(t):
        return length * 0.035 * (1 - t) ** 0.7 + 0.0006

    objs = m.path_blade(f"{name}_Head_A", [head0, tip], up, w, th, mats["blade"])
    objs += m.path_blade(f"{name}_Head_B", [head0, tip - d * 0.01], side, lambda t: 0.55 * w(t), th, mats["blade"])
    tail = [head0 + d * 0.01 - d * (length * 0.5 * i / 39) for i in range(40)]
    objs += m.rope(f"{name}_Tail", tail, length * 0.035, mats, strands=3, gold=True, taper=0.6, merge=0.999)
    for k in range(3):
        objs += m.halo(f"{name}_Ring_{k}", head0 - d * (length * (0.08 + 0.13 * k)), length * (0.13 - 0.025 * k),
                       0.0016, d, mats["light"], tilt_deg=8 * (-1) ** k)
    objs += m.droplet(f"{name}_Light", tip - d * (length * 1.02), length * 0.04, -d, mats["phial_lit"], stretch=1.3)
    return objs


def piercer_c(mats, length, tip, d, name):
    """Feather dart: a slim ivory body with a point of light, three long swept-back feathers
    of light at its tail and a ring of light at its waist."""
    side = d.orthogonal().normalized()
    up = d.cross(side).normalized()
    objs = gd.capsule(f"{name}_Body", tip - d * (length * 0.52), length * 0.045, length * 0.72, d, mats["ivory"])
    objs += m.path_blade(f"{name}_Point", [tip - d * (length * 0.2), tip], up,
                         lambda t: length * 0.09 * (1 - t) ** 0.8, lambda t: length * 0.03 * (1 - t) + 0.0005,
                         mats["blade"])
    for k in range(3):
        a = 2 * PI * k / 3 + PI / 2
        out = side * math.cos(a) + up * math.sin(a)
        normal = d.cross(out)
        root = tip - d * (length * 0.62)
        path = [root, root - d * (length * 0.22) + out * (length * 0.06), root - d * (length * 0.45) + out * (length * 0.1)]
        objs += m.path_blade(f"{name}_Feather_{k}", path, normal,
                             lambda t: length * 0.11 * math.sin(PI * min(t / 0.98, 1) ** 0.55) ** 0.8,
                             lambda t: 0.0012, mats["blade"], offset_fn=lambda t: length * 0.03 * t)
        rach = gd.smooth_path(path, 20)
        objs += gd.tube(f"{name}_Rachis_{k}", rach[:18], mats["core"], 0.0008, (1.0, 0.3))
    objs += m.halo(f"{name}_Waist", tip - d * (length * 0.32), length * 0.085, 0.0016, d, mats["light"])
    objs += m.droplet(f"{name}_Light", tip - d * (length * 0.9), length * 0.035, -d, mats["phial_lit"], stretch=1.2)
    return objs


def piercer_d(mats, length, tip, d, name):
    """Scroll drill: three ivory strands twisted tight into a point round a core of light,
    a gold thread in the twist, three scrolls curling back at the tail."""
    side = d.orthogonal().normalized()
    up = d.cross(side).normalized()
    def twist(phase, scale):
        pts = []
        for i in range(90):
            t = i / 89                   # 0 at the tail, 1 at the point
            r = length * scale * (1 - t ** 1.6) + 0.0004
            a = phase + 2 * PI * 2.2 * t
            pts.append(tip - d * (length * (1 - t)) + (side * math.cos(a) + up * math.sin(a)) * r)
        return pts

    objs = []
    for j in range(3):
        objs.append(c.curve_tube(f"{name}_Strand_{j}", twist(2 * PI * j / 3, 0.075),
                                 [1 - 0.85 * (i / 89) ** 1.5 for i in range(90)], mats["ivory"],
                                 bevel=length * 0.03, resolution=2))
    objs.append(c.curve_tube(f"{name}_Gold", twist(PI / 3, 0.085), [1 - 0.8 * i / 89 for i in range(90)],
                             mats["light"], bevel=0.0012, resolution=1))
    objs += gd.capsule(f"{name}_Core", tip - d * (length * 0.55), length * 0.045, length * 0.8, d, mats["phial_lit"])
    tail = tip - d * length
    for k in range(3):
        a = 2 * PI * k / 3 + PI / 3
        out = side * math.cos(a) + up * math.sin(a)
        plane = m.plane_mapper(tail + d * (length * 0.06), -d, out)
        objs += m.tendril(f"{name}_Scroll_{k}", plane, (0, length * 0.05), 55, length * 0.3, -1.3, length * 0.022,
                          mats, strands=2, curl_start=0.35)
    return objs


# ================================================================== items and render

ITEMS = {
    # name: (title, versions {key: (label, builder)}, rows [(row label, state)], scene, camera(state))
    "lbg_drum": ("輕弩速射彈鼓：四個版本（上：裝在輕弩上　下：近看）",
                 {"A": ("A 象牙燈籠", drum_a), "B": ("B 光環輪", drum_b), "C": ("C 雙面百合", drum_c),
                  "D": ("D 金藤卷軸", drum_d)},
                 [("", "mounted"), ("・近看", "close")]),
    "hbg_mag": ("重弩彈匣：四個版本（上：裝在重弩上　下：近看）",
                {"A": ("A 編織彈倉", mag_a), "B": ("B 光柱", mag_b), "C": ("C 聖匣", mag_c),
                 "D": ("D 浮空光點串", mag_d)},
                [("", "mounted"), ("・近看", "close")]),
    "hbg_shield": ("重弩防禦盾：四個版本（上：平時收合　下：防禦展開）",
                   {"A": ("A 聖樹紋章", shield_a), "B": ("B 光翼", shield_b), "C": ("C 百合", shield_c),
                    "D": ("D 玫瑰窗", shield_d)},
                   [("・平時", "folded"), ("・防禦", "open")]),
    "tracer": ("弓追蹤箭：四個版本（上：剛插上　下：打夠了、快爆開）",
               {"A": ("A 樹紋光環", tracer_a), "B": ("B 光花綻放", tracer_b), "C": ("C 光環準星", tracer_c),
                "D": ("D 金藤蔓生", tracer_d)},
               [("・插上", "stuck"), ("・快爆", "charged")]),
    "piercer": ("重弩龍穿點火：四個版本（上：彈頭　下：從魔物身上貫穿而出）",
                {"A": ("A 金荊棘", piercer_a), "B": ("B 光之長矛", piercer_b), "C": ("C 光羽鏢", piercer_c),
                 "D": ("D 卷草鑽", piercer_d)},
                [("", "round"), ("・貫穿", "through")]),
}


def build_scene(key, state):
    """Builds one version in one state; returns (target, distance, azimuth, elevation, res)."""
    rng = random.Random(7)
    builder = ITEMS[ITEM][1][key][1]
    if ITEM == "lbg_drum":
        light_bowgun()
        mats = materials()
        builder(mats, rng)
        if state == "mounted":
            return (0, 0.06, -0.03), 1.1, 74, 4, (640, 480)
        return tuple(DRUM_C + V(0, 0, 0.004)), 0.4, 68, 8, (640, 480)
    if ITEM == "hbg_mag":
        heavy_bowgun()
        mats = materials()
        builder(mats, rng)
        if state == "mounted":
            return (0, 0.16, -0.06), 1.6, 72, 4, (640, 480)
        return tuple(MAG_TOP + V(0, 0.05, -0.115)), 0.62, 66, 6, (640, 480)
    if ITEM == "hbg_shield":
        heavy_bowgun()
        mats = materials()
        if state == "open":
            charge_up(mats)
        builder(mats, rng, state == "open")
        if state == "open":
            return (0, 0.3, 0.03), 1.55, 142, 12, (640, 520)
        return (0, 0.32, 0.03), 1.3, 104, 16, (640, 520)
    if ITEM == "tracer":
        c.reset_scene()
        mats = materials()
        if state == "charged":
            charge_up(mats)
        devices.hide_block()
        tracer_arrow(mats)
        builder(mats, rng, state == "charged")
        return (0.0, 0.0, 0.07), 0.62, 8, 26, (640, 520)
    if ITEM == "piercer":
        c.reset_scene()
        mats = materials()
        if state == "round":
            builder(mats, 0.16, V(0.08, 0, 0.12), V(1, 0, 0), "Round")
            return (0, 0, 0.12), 0.36, 12, 10, (640, 400)
        charge_up(mats)
        devices.hide_block()
        d = V(0.55, -0.1, 1).normalized()
        builder(mats, 0.16, d * 0.22, d, "Round")
        glow = c.make_material("Crack_Light", c.PALETTE["glow"], roughness=0.2, emission=c.PALETTE["glow"],
                               strength=6.0)
        devices.gold_cracks("Exit_Crack", V(0, 0, 0.001), 8, 0.06, glow, seed=5)
        devices.wound_glow("Exit_Glow", V(0, 0, 0.0012), 0.05, strength=1.6)
        m.halo("Exit_Ring", V(0, 0, 0.004), 0.06, 0.0025, (0, 0, 1), mats["light"])
        for k in range(2):               # rings left in its wake as it breaks out
            m.halo(f"Exit_Wake_{k}", d * (0.012 + 0.022 * k), 0.034 - 0.008 * k, 0.0018, d, mats["light"])
        pf.burst_strands("Exit_Burst", V(0, 0, 0.004), 0.03, count=40, strength=0.9, seed=11, lift=0.5)
        return (0.07, -0.01, 0.1), 0.6, 14, 14, (640, 400)
    raise SystemExit(f"unknown item {ITEM}")


def render_one(key, state):
    target, dist, az, el, res = build_scene(key, state)
    if TEST:
        res = (res[0] // 2, res[1] // 2)
    st.stage_lights(target, dist, res=res)
    if TEST:
        bpy.context.scene.cycles.samples = 8
    return c.render_views(OUT, f"{ITEM}_{key}_{state}", target, dist, [("v", az, el)], lens=50)[0]


def main():
    os.makedirs(OUT, exist_ok=True)
    title, versions, rows = ITEMS[ITEM]
    paths, labels = [], []
    for row_label, state in rows:
        for key in PICK:
            paths.append(render_one(key, state))
            labels.append(versions[key][0] + row_label)
            print("rendered", key, state, flush=True)
    out = os.path.join(OUT, f"{ITEM}{'_test' if TEST else ''}.png")
    st.labelled_strip(paths, labels, out, title, cols=len(PICK))
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
