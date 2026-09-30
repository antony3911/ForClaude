"""The rest of the Miquella light arsenal, built from the shared motifs (motifs.py).

Weapons: great_sword, hammer, hunting_horn, lance, gunlance, switch_axe, charge_blade,
insect_glaive, bow. Visual concepts only; see DESIGN.md section 5.

Melee weapons stand along +Z with the grip at the origin; blades face +-Y.

Usage: python arsenal.py <weapon> <out_dir>
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
from motifs import V, smoothstep

WEAPON = sys.argv[1] if len(sys.argv) > 1 else "great_sword"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join("out", WEAPON)


# ------------------------------------------------------------------ shared pieces

def pommel(mats, z, radius):
    """Ivory cap with a glowing droplet hanging below it (as on every blade)."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius * 1.25, location=(0, 0, z))
    cap = bpy.context.active_object
    cap.name = "Pommel_Cap"
    cap.scale = (1, 1, 0.55)
    cap.data.materials.append(mats["ivory"])
    bpy.ops.object.shade_smooth()
    return [cap] + m.droplet("Pommel_Droplet", (0, 0, z - radius * 1.3), radius * 0.62, (0, 0, 1),
                             mats["light"], stretch=0.9)


def collar(mats, z, radius, name="Collar"):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=radius * 0.24, location=(0, 0, z))
    ring = bpy.context.active_object
    ring.name = name
    ring.data.materials.append(mats["ivory"])
    bpy.ops.object.shade_smooth()
    return [ring]


# ------------------------------------------------------------------ great sword

def blade_dressing(prefix, spine, edge, thick, mats, trail=(0.28, 0.84), temper_u=0.32):
    """Temper line on both faces of a wedge blade and a faint afterimage of light trailing
    its edge, detached from it."""
    n = len(spine)
    objs = []
    for face in (-1, 1):
        line = []
        for i in range(int(0.07 * n), int(0.9 * n), 2):
            t = i / (n - 1)
            h = thick(t) / 2 * (1 - temper_u ** 1.15) ** 0.85
            line.append(spine[i].lerp(edge[i], temper_u ** 1.15) + V(0, face * (h + 0.0006), 0))
        objs.append(c.curve_tube(f"{prefix}_Temper_{face}", line,
                                 [1 - 0.7 * (k / (len(line) - 1)) ** 2 for k in range(len(line))],
                                 mats["core"], bevel=0.0014, resolution=2))
    i0, i1 = int(trail[0] * n), int(trail[1] * n)
    pts = []
    for i in range(i0, i1):
        out = (edge[i] - spine[i]).normalized()
        pts.append(edge[i] + out * (0.016 + 0.012 * math.sin(math.pi * (i - i0) / (i1 - i0))))
    objs += m.path_blade(f"{prefix}_Afterimage", pts, (0, 1, 0), lambda t: 0.006 * math.sin(math.pi * t) + 0.0008,
                         lambda t: 0.0016, mats["light"], samples=90)
    return objs


def great_sword():
    """Asymmetric single-edged great sword whose blade of light floats above the hilt.

    The blade is a sculpted wedge (thick spine, sharp edge) with a sinuous edge: narrow
    shard-like root, a slight inward curve, a full belly, then a clipped return to the point,
    all on a gently curving spine. It hovers a hand's width above the guard, held in a
    levitation ring and cradled, without contact, by three ivory prongs that grow from the
    grip. A thin temper line runs along both faces and a faint afterimage of light trails the
    edge. The guard is one-sided: scrollwork on the back, a tilted halo around the blade."""
    mats = m.materials()
    rng = random.Random(31)
    gt = 0.36
    z0, length = gt + 0.1, 1.2
    objs = m.woven_tube("Grip", [V(0, 0, 0), V(0, 0, gt)], 0.017, mats["ivory"], rng)
    objs += pommel(mats, -0.01, 0.017)
    objs += collar(mats, gt - 0.005, 0.019)

    # Blade geometry: spine curve, its in-plane normal, and the edge offset along it.
    n = 140
    ts = [i / (n - 1) for i in range(n)]
    spine = [V(-0.035 * math.sin(math.pi * t) + 0.075 * t ** 3, 0, z0 + length * t) for t in ts]
    width_knots = [(0.0, 0.012), (0.1, 0.055), (0.24, 0.085), (0.42, 0.165), (0.6, 0.23),
                   (0.76, 0.2), (0.88, 0.11), (0.96, 0.038), (1.0, 0.0)]
    edge, normals = [], []
    for i, t in enumerate(ts):
        d = spine[min(i + 1, n - 1)] - spine[max(i - 1, 0)]
        tan = d.normalized()
        nrm = V(tan.z, 0, -tan.x)
        normals.append(nrm)
        edge.append(spine[i] + nrm * m.interp1d(width_knots, t))

    def thick(t):
        return 0.024 * (1 - 0.45 * t) * smoothstep(t / 0.06) * (1 - t ** 8) + 0.001

    objs += m.wedge_blade("Blade", spine, edge, thick, mats["blade"])
    objs += blade_dressing("Blade", spine, edge, thick, mats, trail=(0.29, 0.83))

    # Levitation ring between guard and blade, and the ivory cradle (no contact).
    objs += m.halo("Levitation_Halo", (0, 0, gt + 0.055), 0.032, 0.003, (0, 0, 1), mats["light"])
    objs += m.halo("Levitation_Halo_Inner", (0, 0, gt + 0.075), 0.022, 0.0018, (0, 0, 1), mats["light"], tilt_deg=10)
    xz = m.plane_mapper((0, 0, 0), (1, 0, 0), (0, 0, 1))
    front = m.plane_mapper((0, 0, 0), (0, -1, 0), (0, 0, 1))
    # Cradle: a twisted cord rises from the grip and parts into three scrolls of different
    # size and turn, curling away from the floating blade without touching it.
    objs += m.tendril("Cradle_Stem", xz, (0, gt - 0.012), 90, 0.045, 0.0, 0.011, mats, curl_start=0.99)
    base2 = (0, gt + 0.03)
    objs += m.tendril("Cradle_Back", xz, base2, 116, 0.36, 1.3, 0.0095, mats,
                      offshoots=[(0.3, -1, 0.35, -1.2), (0.52, 1, 0.22, 1.0)])
    objs += m.tendril("Cradle_Edge", xz, base2, 56, 0.31, -1.15, 0.0088, mats, offshoots=[(0.42, 1, 0.33, 1.1)])
    objs += m.tendril("Cradle_Front", front, base2, 76, 0.2, 1.5, 0.007, mats, offshoots=[(0.4, -1, 0.35, -1.0)])
    # One-sided guard: on the back a cord runs out from the grip and parts into three
    # scrolls (up, out, down), each different, with side curls.
    objs += m.tendril("Guard_Cord", xz, (-0.005, gt + 0.005), 172, 0.07, 0.0, 0.012, mats, curl_start=0.99, bend=0.05)
    gp = (-0.074, gt + 0.015)
    objs += m.tendril("Guard_Up", xz, gp, 118, 0.17, -1.3, 0.009, mats, offshoots=[(0.4, 1, 0.4, 1.1)])
    objs += m.tendril("Guard_Out", xz, gp, 178, 0.24, 1.45, 0.0105, mats,
                      offshoots=[(0.3, -1, 0.35, -1.2), (0.55, 1, 0.25, 1.0)])
    objs += m.tendril("Guard_Down", xz, gp, 232, 0.14, 1.1, 0.008, mats)
    i_h = int(0.24 * (n - 1))
    objs += m.halo("Blade_Halo", spine[i_h].lerp(edge[i_h], 0.45), 0.13, 0.0042, (0, 0, 1), mats["light"],
                   tilt_deg=28, tilt_axis=(0, 1, 0))
    # Small rings floating on the spine, shrinking toward the point.
    for k, t in enumerate((0.52, 0.66, 0.8)):
        i = int(t * (n - 1))
        d = (spine[i + 1] - spine[i - 1]).normalized()
        # Steeply tilted so they read as rings, not ticks, from the side of the blade.
        objs += m.halo(f"Spine_Ring_{k}", spine[i] - normals[i] * 0.004, 0.034 - 0.005 * k, 0.003, d,
                       mats["light"], tilt_deg=38 if k % 2 == 0 else -34, tilt_axis=(1, 0, 0))
    target = (0.04, 0, 0.78)
    views = [("front", 0, 4), ("three_quarter", 35, 10), ("back", 180, 4)]
    m.render_sheets(OUT, "great_sword", mats, target, 3.3, views, res=(700, 1000),
                    extra=[("float", (0.02, 0, gt + 0.2), 0.9, [("float", 25, 10)])])


# ------------------------------------------------------------------ hammer

def hammer():
    """A sun of light caged in woven ivory: the barrel-shaped head is a lantern of strands
    around a glowing orb, both striking faces are halos filled with light."""
    mats = m.materials()
    rng = random.Random(41)
    head_z, half = 1.04, 0.2
    objs = m.woven_tube("Shaft", [V(0, 0, 0), V(0, 0, head_z - 0.13)], 0.019, mats["ivory"], rng)
    objs += pommel(mats, -0.01, 0.019)
    # Orb and cage.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.095, segments=48, ring_count=24, location=(0, 0, head_z))
    orb = bpy.context.active_object
    orb.name = "Sun_Orb"
    # Brighter than the other light so it shines out between the strands.
    sun = c.make_material("Sun", c.PALETTE["glow"], roughness=0.1, emission=c.PALETTE["glow"], strength=4.0)
    orb.data.materials.append(sun)
    bpy.ops.object.shade_smooth()
    objs.append(orb)
    barrel = [V(x, 0, head_z) for x in (-half, 0, half)]
    objs += m.strand_bundle("Cage", barrel, 0.14, mats["ivory"], rng, n=24, twist=5.5,
                            radius_fn=lambda u: 0.78 + 0.22 * math.sin(math.pi * u), spread=(1, 1),
                            bevel=0.0042, tip_taper=0.02)
    # Striking faces: thick halos filled with membrane light, a thinner ring inside.
    face = m.membrane_material("Face_Membrane", 0.11, 0.7)
    mats["face"] = face
    for s in (-1, 1):
        x = s * (half + 0.004)
        objs += m.halo(f"Face_Halo_{s}", (x, 0, head_z), 0.112, 0.009, (1, 0, 0), mats["light"])
        objs += m.halo(f"Face_Halo_Inner_{s}", (x + s * 0.012, 0, head_z), 0.072, 0.004, (1, 0, 0), mats["light"])
        objs += m.membrane_disc(f"Face_Light_{s}", (x, 0, head_z), 0.105, (1, 0, 0), face)
    # More coverage, and richer: a gold-threaded cord hoop near each face, and scrollwork
    # lying on the lantern's surface between them (the sun still shows through).
    def barrel_radius(x):
        u = min(max((x + half) / (2 * half), 0.0), 1.0)
        return 0.14 * (0.78 + 0.22 * math.sin(math.pi * u))

    for s in (-1, 1):
        x = s * 0.155
        r = barrel_radius(x) + 0.007
        ring = [V(x, r * math.cos(a), head_z + r * math.sin(a)) for a in [2 * math.pi * i / 120 for i in range(121)]]
        objs += m.rope(f"Hoop_{s}", ring, 0.008, mats, strands=3, gold=True, taper=0.0, merge=0.999)

    def barrel_map(x, v):
        r = barrel_radius(x) + 0.006
        a = v / 0.14
        return V(x, r * math.cos(a), head_z + r * math.sin(a))

    for k in range(6):
        v0 = (2 * math.pi * k / 6 + 0.45) * 0.14
        sgn = 1 if k % 2 == 0 else -1
        # Gold filigree laid over the ivory cage.
        objs += m.tendril(f"Scroll_{k}", barrel_map, (-0.12, v0), 8 * sgn, 0.2, 1.3 * sgn, 0.005, mats, strands=2,
                          gold=False, strand_mat="light", offshoots=[(0.45, -sgn, 0.38, -1.1 * sgn)])
    # Floating belt ring around the middle of the head.
    objs += m.halo("Belt_Halo", (0, 0, head_z), 0.2, 0.0042, (1, 0, 0), mats["light"], tilt_deg=14,
                   tilt_axis=(0, 0, 1))
    # Neck: the shaft's strands part into three and grip the underside of the head.
    neck = [V(0, 0, head_z - 0.2), V(0, 0, head_z - 0.15)]
    fan = [V(-0.13, 0, 0.06), V(0, -0.035, 0.035), V(0.13, 0, 0.06)]
    objs += m.strand_bundle("Neck", neck, 0.022, mats["ivory"], rng, n=20, split_at=0.15, fan=fan,
                            sub_radius=0.008, bevel=0.0036, twist=6)
    views = [("front", 0, 6), ("three_quarter", 35, 14), ("face_on", 90, 8)]
    m.render_sheets(OUT, "hammer", mats, (0, 0, 0.62), 2.6, views, res=(800, 1000),
                    extra=[("head", (0, 0, head_z), 1.0, [("head", 30, 18)])])


# ------------------------------------------------------------------ hunting horn

def hunting_horn():
    """A lyre of light: two twisting strand arms rise from a yoke and hold a halo at the
    top; strings of light run between; rings ripple out in front like sound."""
    mats = m.materials()
    rng = random.Random(51)
    yoke_z = 0.62
    objs = m.woven_tube("Shaft", [V(0, 0, 0), V(0, 0, yoke_z - 0.02)], 0.018, mats["ivory"], rng)
    objs += pommel(mats, -0.01, 0.018)
    # Yoke: a shallow U of strands carrying the arms.
    yoke = [V(-0.14, 0, yoke_z + 0.05), V(-0.07, 0, yoke_z + 0.005), V(0, 0, yoke_z),
            V(0.07, 0, yoke_z + 0.005), V(0.14, 0, yoke_z + 0.05)]
    objs += m.strand_bundle("Yoke", m.catmull(yoke, 30), 0.018, mats["ivory"], rng, n=20, twist=8,
                            bevel=0.003, tip_taper=0.05)
    top_z, ring_r = yoke_z + 0.42, 0.09
    # Arms: open lyre horns rising from the yoke, flaring outward at the top.
    for s in (-1, 1):
        arm = [V(s * 0.14, 0, yoke_z + 0.05), V(s * 0.19, 0, yoke_z + 0.17), V(s * 0.15, 0, yoke_z + 0.32),
               V(s * 0.155, 0, yoke_z + 0.45), V(s * 0.23, 0, yoke_z + 0.54)]
        fan = [V(s * 0.06, 0, 0.06), V(s * 0.075, 0, -0.01), V(s * 0.01, 0, 0.08)]
        objs += m.strand_bundle(f"Arm_{s}", m.catmull(arm, 40), 0.02, mats["ivory"], rng, n=24,
                                split_at=0.8, fan=fan, sub_radius=0.0065, bevel=0.0032, twist=9,
                                radius_fn=lambda u: 1.0 - 0.35 * u, tip_taper=0.12)
    # The crossbar is a halo floating between the arms.
    objs += m.halo("Crown_Halo", (0, 0, top_z), ring_r, 0.0075, (0, 1, 0), mats["light"])
    objs += m.halo("Crown_Halo_Inner", (0, -0.004, top_z), ring_r - 0.02, 0.0028, (0, 1, 0), mats["light"])
    # Strings of light from the yoke up to the halo.
    for i, x in enumerate((-0.06, -0.03, 0.0, 0.03, 0.06)):
        z_top = top_z - math.sqrt(max(ring_r ** 2 - x ** 2, 0)) + 0.004
        objs.append(c.curve_tube(f"String_{i}", [V(x, 0, yoke_z + 0.02 + 0.03 * abs(x) / 0.075), V(x, 0, z_top)],
                                 [1, 1], mats["core"], bevel=0.0016, resolution=2))
    objs += m.droplet("Resonance_Core", (0, 0, yoke_z + 0.035), 0.02, (0, 0, 1), mats["light"], stretch=1.2)
    # Sound: rings rippling forward out of the crown halo, each wider and fainter.
    for i in range(3):
        objs += m.halo(f"Sound_Ring_{i}", (0, -0.05 * (i + 1), top_z), ring_r + 0.022 * (i + 1),
                       0.0034 - 0.0008 * i, (0, 1, 0), mats["light"])
    views = [("front", 0, 5), ("three_quarter", 35, 12), ("side", 90, 6)]
    m.render_sheets(OUT, "hunting_horn", mats, (0, 0, 0.6), 2.3, views, res=(800, 1000),
                    extra=[("lyre", (0, -0.05, 0.86), 1.0, [("lyre", 25, 8)])])


# ------------------------------------------------------------------ lance and gunlance

def lance_grip(mats, rng):
    """Slim woven grip and an openwork vamplate: eight petal outlines flaring forward with
    open space between them, rimmed by a thin halo."""
    objs = m.woven_tube("Grip", [V(0, 0, 0), V(0, 0, 0.34)], 0.019, mats["ivory"], rng)
    objs += pommel(mats, -0.01, 0.019)
    objs += collar(mats, 0.335, 0.022, "Grip_Collar")
    n_petals = 8
    for k in range(n_petals):
        phi = 2 * math.pi * k / n_petals
        side_pts = {-1: [], 1: []}
        rib = []
        for i in range(40):
            t = i / 39
            r = 0.022 + 0.11 * t ** 1.2
            z = 0.33 + 0.15 * t - 0.02 * smoothstep((t - 0.8) / 0.2)
            w = 0.2 * math.sin(math.pi * t) ** 0.8
            for s in (-1, 1):
                a = phi + s * w
                side_pts[s].append(V(r * math.cos(a), r * math.sin(a), z))
            if t < 0.75:
                rib.append(V(r * math.cos(phi), r * math.sin(phi), z))
        outline = side_pts[-1] + list(reversed(side_pts[1]))
        objs.append(c.curve_tube(f"Petal_{k}", outline, [1.0] * len(outline), mats["ivory"], bevel=0.0028,
                                 resolution=2))
        objs.append(c.curve_tube(f"Petal_Rib_{k}", rib, [1 - 0.6 * i / (len(rib) - 1) for i in range(len(rib))],
                                 mats["ivory"], bevel=0.002, resolution=2))
    objs += m.halo("Vamplate_Halo", (0, 0, 0.475), 0.14, 0.0045, (0, 0, 1), mats["light"])
    return objs


def energy_shield(mats, location, scale, stretch=1.18):
    """The tree-sigil energy shield, drawn light: a slim halo, a faint single membrane and
    the sigil (from sword_shield), made taller than the sword & shield's."""
    import sword_shield as ss
    ss.FRONT = -0.004
    rng = random.Random(9)
    R = ss.R
    membrane = m.membrane_material("Shield_Membrane", R, 0.45, rim=0.1, center=0.008)
    mats["shield_membrane"] = membrane
    objs = m.halo("Shield_Halo", (0, 0, 0), R, 0.0048, (0, 1, 0), mats["light"])
    objs += m.membrane_disc("Shield_Membrane", (0, 0.001, 0), R - 0.004, (0, 1, 0), membrane)
    leaves = ss.LeafBuilder()
    objs += ss.trunk(mats["light"])
    objs += ss.crown(mats["light"], leaves, rng)
    objs += ss.pods(mats["light"])
    objs.append(leaves.finish(mats["light"]))
    root = m.group("EnergyShield", objs, location)
    root.scale = (scale, scale, scale * stretch)
    return root


def double_helix(name, z0, z1, r0, r1, turns, mat, bevel, phase=0.0, n=160):
    """Two strands spiralling around the axis, like the sigil's braided trunk."""
    objs = []
    for k in range(2):
        pts, radii = [], []
        for i in range(n):
            t = i / (n - 1)
            r = r0 + (r1 - r0) * t
            a = phase + k * math.pi + 2 * math.pi * turns * t
            pts.append(V(r * math.cos(a), r * math.sin(a), z0 + (z1 - z0) * t))
            radii.append(1 - 0.5 * t)
        objs.append(c.curve_tube(f"{name}_{k}", pts, radii, mat, bevel=bevel, resolution=2))
    return objs


def lance():
    """Openwork lance: the shaft of the spear is a double helix of light around a thin core,
    only the point is a solid blade; rings shrink toward the point; a tall energy shield."""
    mats = m.materials()
    rng = random.Random(61)
    objs = lance_grip(mats, rng)
    tip = 1.98
    objs.append(c.curve_tube("Spear_Core", [V(0, 0, 0.4), V(0, 0, tip - 0.3)], [1, 0.6], mats["core"],
                             bevel=0.0038, resolution=3))
    objs += double_helix("Spear_Helix", 0.42, tip - 0.3, 0.034, 0.008, 4.5, mats["light"], 0.0036)

    def width(t):
        return 0.05 * (1 - t) ** 0.8 * (0.8 + 0.2 * math.sin(math.pi * min(t / 0.35, 1)))

    for name, normal in (("Point_A", (0, 1, 0)), ("Point_B", (1, 0, 0))):
        objs += m.path_blade(name, [V(0, 0, tip - 0.36), V(0, 0, tip)], normal, width,
                             lambda t: 0.009 * (1 - t) ** 0.8, mats["blade"])
    objs += m.halo_rail("Spear_Rail", (0, 0, 0.72), (0, 0, 1.5), 4, 0.07, 0.03, mats["light"], minor0=0.0038)
    energy_shield(mats, (0.46, -0.05, 0.92), 1.2)
    views = [("front", 0, 5), ("three_quarter", 30, 10), ("back_three_quarter", 150, 10)]
    m.render_sheets(OUT, "lance", mats, (0.2, 0, 0.95), 3.4, views, res=(900, 1000),
                    extra=[("spear", (0, 0, 1.1), 1.4, [("spear", 25, 20)])])


def gunlance():
    """Openwork gunlance: three slim ribs of light around a thin glowing conduit (the
    trident as a gun barrel), bound by an ivory spiral; a small energy core at the root
    and light muzzle halos at the tip for shelling."""
    mats = m.materials()
    rng = random.Random(71)
    objs = lance_grip(mats, rng)
    base, tip = 0.46, 1.74
    objs.append(c.curve_tube("Conduit", [V(0, 0, base), V(0, 0, tip)], [1, 0.8], mats["light"],
                             bevel=0.004, resolution=4))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        radial = V(math.cos(a), math.sin(a), 0)
        path = [V(0, 0, base + 0.06) + radial * 0.045, V(0, 0, 1.05) + radial * 0.095,
                V(0, 0, tip + 0.16) + radial * 0.016]
        objs += m.path_blade(f"Rib_{k}", path, radial, lambda t: 0.016 * (1 - t) ** 0.6 + 0.002,
                             lambda t: 0.007 * (1 - t) ** 0.6, mats["blade"])
    objs += double_helix("Binding", base + 0.1, 1.45, 0.098, 0.07, 3.0, mats["ivory"], 0.0026, phase=0.3)
    objs += m.droplet("Energy_Core", (0, 0, base + 0.03), 0.028, (0, 0, 1), mats["light"], stretch=1.4)
    for k, z in enumerate((0.95, 1.32)):
        objs += m.halo(f"Barrel_Halo_{k}", (0, 0, z), 0.12, 0.0035, (0, 0, 1), mats["light"], tilt_deg=5 - 10 * k)
    objs += m.halo("Muzzle_Halo", (0, 0, tip + 0.03), 0.06, 0.005, (0, 0, 1), mats["light"])
    objs += m.halo("Muzzle_Halo_Inner", (0, 0, tip - 0.01), 0.045, 0.0025, (0, 0, 1), mats["light"])
    energy_shield(mats, (0.46, -0.05, 0.92), 1.2)
    views = [("front", 0, 5), ("three_quarter", 30, 10), ("back_three_quarter", 150, 10)]
    m.render_sheets(OUT, "gunlance", mats, (0.2, 0, 0.95), 3.4, views, res=(900, 1000),
                    extra=[("muzzle", (0, 0, 1.45), 1.2, [("muzzle", 25, 30)])])


# ------------------------------------------------------------------ switch axe

def sickle_blade(name, ctrl, wmax, thick_max, mats, side=1, n=80):
    """A slim curved single-edged wedge of light along a control path; the edge lies on the
    `side` of the path (turning right when side=1)."""
    spine = m.resample(m.catmull(ctrl, 40), n)
    knots = [(0.0, 0.005), (0.22, 0.55 * wmax), (0.58, wmax), (0.84, 0.6 * wmax), (1.0, 0.0)]
    edge = []
    for i in range(n):
        tan = (spine[min(i + 1, n - 1)] - spine[max(i - 1, 0)]).normalized()
        edge.append(spine[i] + V(tan.z, 0, -tan.x) * side * m.interp1d(knots, i / (n - 1)))

    def thick(t):
        return thick_max * (0.4 + 0.6 * math.sin(math.pi * min(t / 0.6, 1.0) * 0.5 + 0.0)) * (1 - t ** 6) + 0.0008

    objs = m.wedge_blade(name, spine, edge, thick, mats["blade"])
    objs += blade_dressing(name, spine, edge, thick, mats, trail=(0.3, 0.9), temper_u=0.35)
    return objs, spine


def switch_axe():
    """Axe mode. The head is Miquella's trident made of light: three slim curved blades
    floating in a fan beside the shaft (the upper one sweeping up, the middle one reaching
    out, the lower one hanging as the beard), edges all turned the same way like a
    pinwheel. Their outer ends draw the axe's silhouette. Three ivory prongs reach from the
    shaft toward the blade roots and curl short of them; floating collars mark the head.
    Three curls on the back, a light spike on top, the phial as a droplet vial in two rings."""
    mats = m.materials()
    rng = random.Random(81)
    top = 1.1
    objs = m.woven_tube("Shaft", [V(0, 0, 0), V(0, 0, top)], 0.019, mats["ivory"], rng)
    objs += pommel(mats, -0.01, 0.019)
    specs = [
        ("Blade_Upper", [V(0.05, 0, 1.0), V(0.13, 0, 1.04), V(0.22, 0, 1.11), V(0.27, 0, 1.2)], 0.055),
        ("Blade_Middle", [V(0.05, 0, 0.94), V(0.16, 0, 0.955), V(0.26, 0, 0.945), V(0.33, 0, 0.92)], 0.065),
        ("Blade_Lower", [V(0.05, 0, 0.88), V(0.13, 0, 0.84), V(0.2, 0, 0.76), V(0.23, 0, 0.66)], 0.06),
    ]
    roots = []
    for name, ctrl, w in specs:
        o, spine = sickle_blade(name, ctrl, w, 0.011, mats)
        objs += o
        roots.append(spine[0])
    xz = m.plane_mapper((0, 0, 0), (1, 0, 0), (0, 0, 1))
    # Scrolls reaching out beneath each blade root, curling short of it.
    for k, (r, turns, head) in enumerate(zip(roots, (1.3, -1.2, -1.4), (14, -4, -18))):
        objs += m.tendril(f"Prong_{k}", xz, (0.012, r.z), head, 0.085, turns, 0.0055, mats, curl_start=0.45)
    # A gold-threaded cord winding up the shaft like a vine, ending in a scroll.
    vine = m.cylinder_mapper((0, 0, 0.46), 0.027)
    # Gold, so it reads against the ivory shaft.
    objs += m.tendril("Shaft_Vine", vine, (0, 0), 32, 0.56, 1.1, 0.0068, mats, curl_start=0.8, gold=False,
                      strand_mat="light", offshoots=[(0.3, 1, 0.25, 1.1), (0.55, -1, 0.22, -1.0)])
    for k, z in enumerate((0.84, 1.05)):
        objs += m.halo(f"Float_Collar_{k}", (0, 0, z), 0.03, 0.0026, (0, 0, 1), mats["light"], tilt_deg=8 * (1 - 2 * k))
    # Back: a cord leaving the shaft parts into three scrolls of different size.
    objs += m.tendril("Back_Cord", xz, (-0.012, 0.95), 182, 0.06, 0.0, 0.012, mats, curl_start=0.99)
    bp = (-0.072, 0.948)
    objs += m.tendril("Back_Up", xz, bp, 122, 0.22, 1.35, 0.0092, mats, offshoots=[(0.38, -1, 0.4, -1.2)])
    objs += m.tendril("Back_Out", xz, bp, 186, 0.29, -1.55, 0.0105, mats,
                      offshoots=[(0.3, 1, 0.35, 1.2), (0.52, -1, 0.25, -1.0)])
    objs += m.tendril("Back_Down", xz, bp, 240, 0.18, -1.2, 0.0082, mats, offshoots=[(0.45, 1, 0.35, 1.0)])
    objs += m.path_blade("Top_Spike", [V(0, 0, top - 0.02), V(0, 0, top + 0.16)], (0, 1, 0),
                         lambda t: 0.034 * (1 - t), lambda t: 0.01 * (1 - t), mats["blade"])
    objs += m.halo("Top_Halo", (0, 0, top + 0.01), 0.045, 0.0032, (0, 0, 1), mats["light"], tilt_deg=8)
    # Phial: a droplet vial of light behind the shaft, between two floating rings.
    px, pz = -0.05, 0.36     # low on the shaft, clear of the vine
    objs += m.droplet("Phial", (px, 0, pz - 0.02), 0.02, (0, 0, 1), mats["light"], stretch=2.2)
    for k, z in enumerate((pz - 0.05, pz + 0.05)):
        objs += m.halo(f"Phial_Ring_{k}", (px, 0, z), 0.03, 0.0025, (0, 0, 1), mats["light"], tilt_deg=6 * (1 - 2 * k))
    views = [("front", 0, 5), ("three_quarter", 35, 12), ("back_three_quarter", 145, 12)]
    m.render_sheets(OUT, "switch_axe", mats, (0.08, 0, 0.6), 2.7, views, res=(800, 1000),
                    extra=[("head", (0.15, 0, 0.93), 0.9, [("head", 25, 8)])])


# ------------------------------------------------------------------ charge blade

def charge_blade():
    """Sword and shield. The shield is the tree-sigil energy shield with five phials of
    light set into its rim and a crescent edge that becomes the axe blade."""
    import blades
    mats = m.materials()
    rng = random.Random(91)
    blades.BLADE_LEN = 0.8
    sword = blades.build_sword("CB_Sword", mats["ivory"], mats["light"], mats["blade"], mats["core"], seed=9)
    sword.location = (-0.38, 0, 0.0)
    # Phial ring on the sword: five droplets orbiting a halo above the guard.
    gz = blades.GUARD_Z + 0.13
    ring = m.halo("Sword_Phial_Ring", (-0.38, 0, gz), 0.06, 0.0028, (0, 0, 1), mats["light"], tilt_deg=10)
    for k in range(5):
        a = 2 * math.pi * k / 5
        pos = V(-0.38 + 0.06 * math.cos(a), 0.06 * math.sin(a), gz)
        m.droplet(f"Sword_Phial_{k}", pos, 0.009, (-math.sin(a), math.cos(a), 0), mats["light"], stretch=1.1)
    root = energy_shield(mats, (0.2, 0, 0.55), 1.05)
    rad = 0.27 * 1.05
    # Phials: five droplets along the upper rim, pointing outward.
    for k in range(5):
        a = math.radians(55 + 17.5 * k)
        pos = V(0.2 + (rad + 0.03) * math.cos(a), -0.01, 0.55 + (rad + 0.03) * 1.18 * math.sin(a))
        m.droplet(f"Shield_Phial_{k}", pos, 0.012, (math.cos(a), 0, math.sin(a)), mats["light"], stretch=1.3)
    # Axe edge (the axe blade in axe mode): a floating single-edged wedge beside the lower-left
    # rim, like the great sword's blade: narrow at the top, a full belly low down, a sinuous
    # return to a point that sweeps past the rim. Not a crescent hugging the circle.
    def rim(a_deg, off):
        a = math.radians(a_deg)
        return V(0.2 + (rad + off) * math.cos(a), -0.005, 0.55 + (rad + off) * 1.18 * math.sin(a))

    n_e = 90
    spine, edge = [], []
    knots = [(0.0, 0.004), (0.15, 0.02), (0.4, 0.045), (0.62, 0.07), (0.8, 0.06), (0.93, 0.03), (1.0, 0.0)]
    for i in range(n_e):
        t = i / (n_e - 1)
        a = 150 + 108 * t
        s = rim(a, 0.024 + 0.05 * t ** 3)               # leaves the rim toward the point
        out = (s - V(0.2, -0.005, 0.55)).normalized()
        spine.append(s)
        edge.append(s + out * m.interp1d(knots, t))

    def thick(t):
        return 0.012 * (0.5 + 0.5 * math.sin(math.pi * t)) + 0.001

    m.wedge_blade("Axe_Edge", spine, edge, thick, mats["blade"])
    blade_dressing("Axe_Edge", spine, edge, thick, mats, trail=(0.35, 0.9), temper_u=0.35)
    import sword_shield as ss
    ss.add_backdrop()
    views = [("front", 0, 4), ("three_quarter", 30, 10)]
    m.render_sheets(OUT, "charge_blade", mats, (-0.05, 0, 0.5), 2.3, views, res=(1000, 900), cols=2,
                    extra=[("shield", (0.2, 0, 0.55), 1.1, [("shield", 15, 5)])])


# ------------------------------------------------------------------ insect glaive

def bead(name, loc, radius, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=24, ring_count=12, location=Vector(loc))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return [obj]


def kinsect(mats, center, scale):
    """The kinsect as a slender butterfly of light: true wing shapes (pointed forewings,
    swallow-tailed hindwings whose tails roll into scrolls), fine curved veins and edges of
    gold light on faint membranes, wings raised in a shallow V; a beaded ivory body and long
    antennae ending in scrolls."""
    C = Vector(center)
    k = scale
    wing_mat = m.membrane_material("Wing_Membrane", 0.06 * k, 1.0, rim=0.45, center=0.06)
    mats["wing"] = wing_mat
    fore = [(0.0, 0.004), (0.03, 0.028), (0.065, 0.055), (0.1, 0.078), (0.128, 0.084), (0.126, 0.064),
            (0.116, 0.036), (0.1, 0.012), (0.08, -0.004), (0.05, -0.012), (0.02, -0.01)]
    hind = [(0.0, -0.006), (0.03, -0.02), (0.064, -0.036), (0.09, -0.058), (0.094, -0.078),
            (0.08, -0.09), (0.066, -0.094), (0.062, -0.13), (0.056, -0.158), (0.05, -0.13),
            (0.042, -0.1), (0.024, -0.07), (0.008, -0.03)]
    fore_veins = [(0.122, 0.078), (0.124, 0.05), (0.106, 0.018), (0.076, -0.004)]
    hind_veins = [(0.088, -0.066), (0.07, -0.088), (0.058, -0.14)]
    dihedral = math.radians(20)
    objs = []
    for s in (-1, 1):
        def to3(x, z, s=s):
            return C + V(s * x * k * math.cos(dihedral), -x * k * math.sin(dihedral), z * k)

        for wname, outline, veins, lift in (("Fore", fore, fore_veins, 0.01), ("Hind", hind, hind_veins, -0.012)):
            loop = m.catmull([V(x, z, 0) for x, z in outline] + [V(outline[0][0], outline[0][1], 0)], 90)
            pts3 = [to3(p.x, p.y) for p in loop]
            objs += m.flat_fill(f"{wname}_{s}", pts3[:-1], wing_mat, center_origin=True)
            objs.append(c.curve_tube(f"{wname}_Edge_{s}", pts3, [1.0] * len(pts3), mats["light"],
                                     bevel=0.0008 * k, resolution=2))
            for j, (ex, ez) in enumerate(veins):
                ctrl = [V(0.004, 0.0, 0), V(ex * 0.45, ez * 0.3 + lift, 0), V(ex * 0.97, ez * 0.97, 0)]
                vp = [to3(p.x, p.y) for p in m.catmull(ctrl, 24)]
                objs.append(c.curve_tube(f"{wname}_Vein_{s}_{j}", vp, [1 - 0.7 * i / 23 for i in range(24)],
                                         mats["light"], bevel=0.0006 * k, resolution=2))
        objs += m.tendril(f"Tail_{s}", to3, (0.056, -0.158), -95, 0.05, 1.3, 0.0022 * k, mats, strands=2,
                          gold=False, curl_start=0.3)
        objs += m.tendril(f"Shoulder_{s}", to3, (0.004, 0.006), 72, 0.04, -1.2, 0.0024 * k, mats, strands=2,
                          gold=False, curl_start=0.3)
        head = C + V(0, 0, 0.022 * k)
        objs += m.tendril(f"Antenna_{s}", m.plane_mapper(head, (s, 0, 0), (0, 0, 1)), (0, 0), 70, 0.08 * k, -1.3,
                          0.0015 * k, mats, strands=2, gold=False, curl_start=0.6)
    # Body: head, a droplet of light for the thorax, a tapering chain of ivory beads.
    objs += bead("Kinsect_Head", C + V(0, 0, 0.022 * k), 0.0055 * k, mats["ivory"])
    objs += m.droplet("Kinsect_Thorax", C + V(0, 0, 0.004 * k), 0.0075 * k, (0, 0, 1), mats["light"], stretch=1.2)
    for i in range(6):
        objs += bead(f"Kinsect_Abdomen_{i}", C + V(0, 0, -(0.008 + 0.0105 * i) * k), (0.0056 - 0.0006 * i) * k,
                     mats["ivory"], scale=(1, 1, 1.25))
    return objs


def insect_glaive():
    """A staff with light blades at both ends, halos at each blade root, a trident guard at
    each end of the grip, and a butterfly of light as the kinsect."""
    mats = m.materials()
    rng = random.Random(101)
    bottom, top = 0.0, 1.45
    # Only the middle is a woven grip; above and below, the staff opens into a double helix
    # of ivory around a thin core of light, with floating rings.
    g0, g1 = 0.52, 0.95
    objs = m.woven_tube("Grip", [V(0, 0, g0), V(0, 0, g1)], 0.017, mats["ivory"], rng, pitch=0.7)
    for z in (g0, g1):
        objs += collar(mats, z, 0.02, f"Grip_Collar_{z}")
    for name, z0, z1 in (("Upper", g1, top), ("Lower", g0, bottom)):
        objs.append(c.curve_tube(f"{name}_Core", [V(0, 0, z0), V(0, 0, z1)], [1, 1], mats["core"],
                                 bevel=0.0042, resolution=3))
        objs += double_helix(f"{name}_Helix", z0, z1, 0.016, 0.012, 3.0, mats["ivory"], 0.0036,
                             phase=0.5 if name == "Upper" else 2.0)
        for k in (1, 2):
            z = z0 + (z1 - z0) * k / 3
            objs += m.halo(f"{name}_Ring_{k}", (0, 0, z), 0.03, 0.0025, (0, 0, 1), mats["light"], tilt_deg=7 * (1 - 2 * (k % 2)))
    leaf = lambda wmax: (lambda t: wmax * (0.8 + 0.3 * math.sin(math.pi * min(t / 0.45, 1) * 0.5)) * (1 - t ** 2.6))
    objs += m.path_blade("Blade_Top", [V(0, 0, top), V(0, 0, top + 0.42)], (0, 1, 0), leaf(0.075),
                         lambda t: 0.012 * (1 - t ** 2), mats["blade"])
    objs += m.path_blade("Blade_Bottom", [V(0, 0, bottom), V(0, 0, bottom - 0.24)], (0, 1, 0), leaf(0.05),
                         lambda t: 0.01 * (1 - t ** 2), mats["blade"])
    for name, z, zdir in (("Top", top, 1), ("Bottom", bottom, -1)):
        objs += m.halo(f"{name}_Halo", (0, 0, z + zdir * 0.07), 0.065, 0.004, (0, 0, 1), mats["light"], tilt_deg=8)
        for s in (-1, 1):
            path = [V(0, 0, z - zdir * 0.02), V(s * 0.05, 0, z + zdir * 0.01), V(s * 0.09, 0, z + zdir * 0.02)]
            fan = [V(s * 0.0, 0, zdir * 0.05), V(s * 0.04, 0, zdir * 0.0), V(s * 0.0, 0, -zdir * 0.035)]
            objs += m.strand_bundle(f"{name}_Guard_{s}", path, 0.012, mats["ivory"], rng, n=16, split_at=0.4,
                                    fan=fan, sub_radius=0.004, bevel=0.0022, twist=6)
    kinsect(mats, (0.36, -0.08, 1.2), 1.4)
    views = [("front", 0, 5), ("three_quarter", 30, 10), ("side", 90, 5)]
    m.render_sheets(OUT, "insect_glaive", mats, (0.1, 0, 0.82), 3.5, views, res=(800, 1000),
                    extra=[("kinsect", (0.36, -0.08, 1.15), 0.85, [("kinsect", 10, 12)])])


# ------------------------------------------------------------------ bow

def bow():
    """Recurve limbs of twisting strands ending in scrollwork tips, a string of light, and a
    light arrow drawn through a rail of shrinking rings (the light bowgun's signature).
    The bow stands in the XZ plane; the arrow points to -X, the archer is on +X."""
    mats = m.materials()
    rng = random.Random(111)
    grip_x = -0.14
    objs = m.woven_tube("Riser", [V(grip_x + 0.01, 0, -0.13), V(grip_x - 0.005, 0, 0), V(grip_x + 0.01, 0, 0.13)],
                        0.018, mats["ivory"], rng)
    tips = []
    xz = m.plane_mapper((0, 0, 0), (1, 0, 0), (0, 0, 1))
    for s in (1, -1):
        limb = [V(grip_x + 0.01, 0, s * 0.12), V(grip_x - 0.05, 0, s * 0.33), V(grip_x + 0.0, 0, s * 0.53),
                V(grip_x + 0.12, 0, s * 0.65), V(grip_x + 0.2, 0, s * 0.69)]
        tips.append(limb[-1])
        path = m.catmull(limb, 40)
        objs += m.strand_bundle(f"Limb_{s}", path, 0.017, mats["ivory"], rng, n=18, twist=12, bevel=0.003,
                                radius_fn=lambda u: 1.0 - 0.35 * u, tip_taper=0.04)
        # Tip: three scrolls of different size; the long one rolls back toward the string.
        d = path[-1] - path[-2]
        h = math.degrees(math.atan2(d.z, d.x))
        tp = (path[-1].x, path[-1].z)
        objs += m.tendril(f"Tip_Long_{s}", xz, tp, h + s * 5, 0.24, -s * 1.4, 0.0095, mats,
                          offshoots=[(0.35, s, 0.4, s * 1.2), (0.55, -s, 0.25, -s * 1.0)])
        objs += m.tendril(f"Tip_Up_{s}", xz, tp, h + s * 62, 0.15, s * 1.25, 0.0078, mats,
                          offshoots=[(0.45, -s, 0.35, -s * 1.0)])
        objs += m.tendril(f"Tip_Back_{s}", xz, tp, h - s * 58, 0.12, -s * 1.1, 0.0068, mats)
        # A gold-threaded cord winding along the limb out to the scrolls.
        objs += m.wound_cord(f"Limb_Vine_{s}", path, 0.021, 4.5, 0.0045, mats, phase=1.0 + s, strand_mat="light")
        # Scrolls at the end of the grip, curling forward.
        objs += m.tendril(f"Riser_Scroll_{s}", xz, (grip_x - 0.012, s * 0.125), 180 - s * 32, 0.13, s * 1.25, 0.0072,
                          mats, offshoots=[(0.4, -s, 0.35, -s * 1.1)])
    string_x = grip_x + 0.2
    objs.append(c.curve_tube("String", [V(string_x, 0, 0.69), V(string_x, 0, -0.69)], [1, 1], mats["core"],
                             bevel=0.0022, resolution=2))
    # Arrow of light from the string, over the arrow rest, through the rings.
    az = 0.02
    nock, point = string_x, -0.78
    objs.append(c.curve_tube("Arrow_Shaft", [V(nock, 0, az), V(point + 0.05, 0, az)], [1, 1], mats["core"],
                             bevel=0.0035, resolution=3))
    objs += m.path_blade("Arrow_Head", [V(point + 0.06, 0, az), V(point - 0.05, 0, az)], (0, 1, 0),
                         lambda t: 0.03 * (1 - t) ** 0.9, lambda t: 0.006 * (1 - t), mats["blade"])
    for k in range(3):
        a = math.radians(90 + 120 * k)
        normal = V(0, math.cos(a), math.sin(a))
        objs += m.path_blade(f"Fletch_{k}", [V(nock - 0.02, 0, az), V(nock - 0.1, 0, az)], normal.cross(V(1, 0, 0)),
                             lambda t: 0.03 * math.sin(math.pi * (0.2 + 0.8 * t)) ** 0.8,
                             lambda t: 0.002, mats["light"], offset_fn=lambda t: 0.012)
    objs += m.halo_rail("Arrow_Rail", (grip_x - 0.18, 0, az), (point + 0.08, 0, az), 4, 0.075, 0.035,
                        mats["light"], minor0=0.0045)
    objs += m.halo("Rest_Halo", (grip_x - 0.03, 0, az), 0.04, 0.003, (1, 0, 0), mats["light"])
    views = [("profile", 0, 4), ("three_quarter", 35, 12), ("archer_view", 75, 6)]
    m.render_sheets(OUT, "bow", mats, (-0.2, 0, 0.0), 2.4, views, res=(1000, 900),
                    extra=[("rail", (-0.4, 0, 0.02), 1.1, [("rail", 60, 10)])])


WEAPONS = {
    "great_sword": great_sword,
    "hammer": hammer,
    "hunting_horn": hunting_horn,
    "lance": lance,
    "gunlance": gunlance,
    "switch_axe": switch_axe,
    "charge_blade": charge_blade,
    "insect_glaive": insect_glaive,
    "bow": bow,
}

if __name__ == "__main__":
    c.reset_scene()
    WEAPONS[WEAPON]()
