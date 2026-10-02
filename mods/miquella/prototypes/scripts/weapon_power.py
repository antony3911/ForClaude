"""More force in the other weapons' charges (user, 2026-10-02 night). For each weapon: its
current full charge, then two additions. Additions are parts the game version can fade in
(Dissolve) and move or spin with bones; drawn in bright gold so they read against a
white-hot level 3. Used by power_states.py (set weapons_power)."""
import math
import random

import bpy
from mathutils import Vector

import common as c
import motifs as m
from motifs import V
import states as st

ADD_GOLD = ("#FFB43A", 14.0)


def gold(name, scale=1.0):
    return c.make_material(name, ADD_GOLD[0], roughness=0.1, emission=ADD_GOLD[0], strength=ADD_GOLD[1] * scale)


def tube(name, pts, radii, mat, bevel):
    return c.curve_tube(name, pts, radii, mat, bevel=bevel, resolution=3)


def strands_around(prefix, center_fn, radius_fn, n_str, turns, mat, bevel, n=260):
    """Strands of light spiralling around a curve (center_fn(t), radius_fn(t), t 0..1)."""
    objs = []
    for k in range(n_str):
        pts, radii = [], []
        for i in range(n):
            t = i / (n - 1)
            a = 2 * math.pi * k / n_str + 2 * math.pi * turns * t
            r = radius_fn(t)
            pts.append(center_fn(t) + V(r * math.cos(a), r * math.sin(a) * 0.55, 0))
            radii.append((1 - 0.6 * t) * min(1, t * 12))
        objs.append(tube(f"{prefix}_{k}", pts, radii, mat, bevel))
    return objs


def sunburst(prefix, center, axis, r_in, r_out, n, mat, bevel=0.0032):
    """A ring with rays of two lengths around `axis`."""
    axis = Vector(axis).normalized()
    u = axis.orthogonal().normalized()
    w = axis.cross(u)
    objs = m.halo(f"{prefix}_Ring", center, r_in, bevel * 1.4, axis, mat)
    for k in range(n):
        a = 2 * math.pi * k / n
        d = u * math.cos(a) + w * math.sin(a)
        r1 = r_out if k % 2 == 0 else r_in + (r_out - r_in) * 0.55
        objs.append(tube(f"{prefix}_Ray_{k}", [Vector(center) + d * r_in * 1.05, Vector(center) + d * r1],
                         [1.0, 0.12], mat, bevel if k % 2 == 0 else bevel * 0.7))
    return objs


# ---------------------------------------------------------------- great sword

GS_Z0, GS_LEN = 0.46, 1.2
GS_WIDTH = [(0.0, 0.012), (0.1, 0.055), (0.24, 0.085), (0.42, 0.165), (0.6, 0.23), (0.76, 0.2), (0.88, 0.11),
            (0.96, 0.038), (1.0, 0.0)]


def gs_center(t):
    spine_x = -0.035 * math.sin(math.pi * t) + 0.075 * t ** 3
    return V(spine_x + 0.5 * m.interp1d(GS_WIDTH, t), 0, GS_Z0 + GS_LEN * t)


def gs_base():
    import arsenal
    c.reset_scene()
    mats = st.capture_build(arsenal.great_sword)
    m.glow_mode(mats)
    st.set_blade(mats["blade"], "#FFFBF0", "#FFE7B0", 4.5)
    st.set_glow(mats["light"], "#FFF2D6", 5.5)
    st.set_glow(mats["core"], "#FFFBF0", 7.0)
    return mats


def gs_strands(mats):
    g = gold("GS_Strand")
    objs = strands_around("GS_Strand", gs_center, lambda t: 0.5 * m.interp1d(GS_WIDTH, t) + 0.035, 3, 3.2, g, 0.0035)
    rng = random.Random(5)
    for k in range(9):
        t = rng.uniform(0.25, 0.9)
        p = gs_center(t) + V(0.5 * m.interp1d(GS_WIDTH, t) + rng.uniform(0.05, 0.14), rng.uniform(-0.03, 0.03),
                             rng.uniform(-0.03, 0.03))
        objs += m.droplet(f"GS_Spark_{k}", p, rng.uniform(0.006, 0.01), (1, 0, 0.6), g, stretch=2.5)
    return objs


def gs_rings(mats):
    g = gold("GS_Ring")
    objs = []
    for k, (t, r, tilt) in enumerate(((0.12, 0.17, 20), (0.32, 0.21, -14), (0.52, 0.24, 10), (0.7, 0.21, -18),
                                      (0.86, 0.15, 12))):
        objs += m.halo(f"GS_Ring_{k}", gs_center(t), r, 0.0045, (0, 0, 1), g, tilt_deg=tilt,
                       tilt_axis=(1, 0, 0) if k % 2 == 0 else (0, 1, 0))
    tip = V(0.075 - 0.0, 0, GS_Z0 + GS_LEN)
    for k, normal in enumerate(((0, 1, 0), (1, 0, 0))):
        objs += m.path_blade(f"GS_Beam_{k}", [tip - V(0, 0, 0.08), tip + V(0.03, 0, 0.5)], normal,
                             lambda t: 0.03 * (1 - t) ** 0.8 + 0.001, lambda t: 0.006 * (1 - t) + 0.0005, g)
    return objs


# ---------------------------------------------------------------- hammer

HM_Z, HM_HALF = 1.04, 0.2


def hm_base():
    import arsenal
    c.reset_scene()
    mats = st.capture_build(arsenal.hammer)
    m.glow_mode(mats)
    arsenal.hammer_charge_rings(mats)
    st.set_glow(bpy.data.materials["Sun"], "#FFF0DC", 9.0)
    st.set_glow(mats["light"], "#FFF0DC", 16.0)
    return mats


def hm_corona(mats):
    """Rays of the caged sun bursting out between the strands."""
    g = gold("HM_Corona")
    objs = []
    rng = random.Random(9)
    n = 34
    for k in range(n):
        z = 1 - 2 * (k + 0.5) / n
        a = k * math.pi * (3 - math.sqrt(5))
        d = V(math.sqrt(1 - z * z) * math.cos(a) * 0.55, math.sqrt(1 - z * z) * math.sin(a), z)
        d.normalize()
        length = rng.uniform(0.42, 0.58) if k % 2 == 0 else rng.uniform(0.26, 0.34)
        objs.append(tube(f"HM_Ray_{k}", [V(0, 0, HM_Z) + d * 0.1, V(0, 0, HM_Z) + d * length], [1.0, 0.06], g,
                         0.009 if k % 2 == 0 else 0.006))
    return objs


def hm_shock(mats):
    """A sunburst wheel beyond each striking face, as if the blow were already ringing out."""
    g = gold("HM_Shock")
    objs = []
    for s in (1, -1):
        objs += sunburst(f"HM_Shock_{s}", V(s * 0.52, 0, HM_Z), (1, 0, 0), 0.17, 0.3, 20, g)
        objs += m.halo(f"HM_Shock_Out_{s}", V(s * 0.58, 0, HM_Z), 0.32, 0.0025, (1, 0, 0), g)
    return objs


# ---------------------------------------------------------------- gunlance

def gl_base():
    import arsenal
    c.reset_scene()
    mats = st.capture_build(arsenal.gunlance)
    m.glow_mode(mats)
    st.show([bpy.data.objects["EnergyShield"]], False)
    z0 = arsenal.GUNLANCE_BASE + 0.1
    for o in [o for o in bpy.data.objects if o.name.startswith("Binding")]:
        bpy.data.objects.remove(o, do_unlink=True)
    arsenal.gunlance_spring(mats, top=z0 + (arsenal.SPRING_TOP - z0) * 0.45)
    core = c.make_material("GL_Core", "#FFE2AC", roughness=0.1, emission="#FFE2AC", strength=14.0)
    for o in [o for o in bpy.data.objects if o.name.startswith("Energy_Core")]:
        o.data.materials[0] = core
        o.scale = (1.35, 1.35, 1.35)
    st.set_glow(mats["light"], "#FFE2AC", 10.0)
    st.set_blade(mats["blade"], "#FFE2AC", "#FFB43A", 6.0)
    return mats


def gl_muzzle(mats):
    """The muzzle opens like a flower of light, rings stacked ahead of it."""
    import arsenal
    g = gold("GL_Petal")
    tip = arsenal.GUNLANCE_TIP
    objs = []
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        d = V(math.cos(a), math.sin(a), 0)
        p0 = V(0, 0, tip) + d * 0.05
        objs += m.path_blade(f"GL_Petal_{k}", [p0, p0 + d * 0.07 + V(0, 0, 0.1), p0 + d * 0.13 + V(0, 0, 0.14)],
                             d, lambda t: 0.05 * math.sin(math.pi * min(1, 0.1 + t)) ** 0.7 + 0.001,
                             lambda t: 0.004, g, samples=30)
    for k, (dz, r) in enumerate(((0.2, 0.09), (0.3, 0.07), (0.38, 0.05))):
        objs += m.halo(f"GL_Ahead_{k}", (0, 0, tip + dz), r, 0.004, (0, 0, 1), g)
    return objs


def gl_rail(mats):
    """Rings stacked along the barrel, tighter and brighter toward the muzzle (about to fire)."""
    import arsenal
    g = gold("GL_Rail")
    tip = arsenal.GUNLANCE_TIP
    objs = []
    n = 9
    for k in range(n):
        t = k / (n - 1)
        z = 0.9 + (tip - 0.05 - 0.9) * (1 - (1 - t) ** 1.6)
        objs += m.halo(f"GL_Rail_{k}", (0, 0, z), 0.13 - 0.06 * t, 0.003 + 0.002 * t, (0, 0, 1), g,
                       tilt_deg=4 if k % 2 else -4)
    return objs


# ---------------------------------------------------------------- long sword

def ls_base():
    mats = st.build_long_sword()
    st.apply_spirit(mats, st.SPIRIT_LEVELS[3])
    return mats


def ls_parent(objs):
    root = bpy.data.objects["LongSword"]
    for o in objs:
        o.parent = root
    return objs


def ls_rings(mats):
    """The tsuba's two rings multiply up the blade at the red level (they can spin there)."""
    import long_sword as ls
    g = gold("LS_Ring")
    objs = []
    for k, s in enumerate((0.12, 0.3, 0.48, 0.66, 0.82)):
        p = ls.blade_center(s) + V(ls.blade_profile(s)[0] * 0.5, 0, 0)
        objs += m.halo(f"LS_Ring_{k}", p, 0.07 - 0.03 * s, 0.0035, (0, 0, 1), g, tilt_deg=12 if k % 2 else -12)
    return ls_parent(objs)


def ls_strands(mats):
    import long_sword as ls
    g = gold("LS_Strand")

    def center(t):
        s = 0.03 + 0.9 * t
        return ls.blade_center(s) + V(ls.blade_profile(s)[0] * 0.5, 0, 0)
    return ls_parent(strands_around("LS_Strand", center, lambda t: 0.04 - 0.02 * t, 2, 3.5, g, 0.0025))


WEAPONS = [
    ("大劍", gs_base, [("A 光絲纏繞", gs_strands), ("B 光環擴張＋光柱", gs_rings)],
     ((0.06, 0, 1.1), 3.3, ("front", 0, 4), (620, 1000))),
    ("大錘", hm_base, [("A 日冕放射", hm_corona), ("B 衝擊光輪", hm_shock)],
     ((0, 0, 1.0), 2.7, ("three_quarter", 38, 12), (760, 760))),
    ("銃槍", gl_base, [("A 槍口綻放", gl_muzzle), ("B 光環疊排", gl_rail)],
     ((0, 0, 1.38), 2.45, ("three_quarter", 25, 8), (620, 1000))),
    ("太刀", ls_base, [("A 光環沿刀身", ls_rings), ("B 光絲纏繞", ls_strands)],
     ((0.0, 0, 0.55), 2.0, ("flat", 0, 4), (560, 1000))),
]
