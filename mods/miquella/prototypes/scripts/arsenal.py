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


def great_sword(gt=0.36, render=True):
    """Asymmetric single-edged great sword whose blade of light floats above the hilt.

    The blade is a sculpted wedge (thick spine, sharp edge) with a sinuous edge: narrow
    shard-like root, a slight inward curve, a full belly, then a clipped return to the point,
    all on a gently curving spine. It hovers a hand's width above the guard, held in a
    levitation ring and cradled, without contact, by three ivory prongs that grow from the
    grip. A thin temper line runs along both faces and a faint afterimage of light trails the
    edge. The guard is one-sided: scrollwork on the back, a tilted halo around the blade.

    gt is the grip length (the game kit uses a longer one, for two hands); render=False
    returns (objects, materials, blade tip) instead of rendering."""
    mats = m.materials()
    rng = random.Random(31)
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
    if not render:
        return objs, mats, spine[-1]
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
        r = barrel_radius(x) + 0.013             # lies on top of the cage strands
        a = v / 0.14
        return V(x, r * math.cos(a), head_z + r * math.sin(a))

    for k in range(6):
        v0 = (2 * math.pi * k / 6 + 0.45) * 0.14
        sgn = 1 if k % 2 == 0 else -1
        # Gold filigree laid over the ivory cage.
        objs += m.tendril(f"Scroll_{k}", barrel_map, (-0.12, v0), 8 * sgn, 0.21, 1.3 * sgn, 0.0072, mats, strands=2,
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
    xz = m.plane_mapper((0, 0, 0), (1, 0, 0), (0, 0, 1))
    for s in (-1, 1):
        arm = [V(s * 0.14, 0, yoke_z + 0.05), V(s * 0.19, 0, yoke_z + 0.17), V(s * 0.15, 0, yoke_z + 0.32),
               V(s * 0.155, 0, yoke_z + 0.45), V(s * 0.23, 0, yoke_z + 0.54)]
        path = m.catmull(arm, 40)
        objs += m.strand_bundle(f"Arm_{s}", path, 0.02, mats["ivory"], rng, n=24, bevel=0.0032, twist=9,
                                radius_fn=lambda u: 1.0 - 0.35 * u, tip_taper=0.04)
        # Horn tips: three scrolls of different size, the long one rolling outward and down
        # like a ram's horn, the others curling up and inward.
        d = path[-1] - path[-2]
        h = math.degrees(math.atan2(d.z, d.x))
        tp = (path[-1].x, path[-1].z)
        objs += m.tendril(f"Arm_Tip_Out_{s}", xz, tp, h - s * 8, 0.22, -s * 1.45, 0.0095, mats,
                          offshoots=[(0.35, s, 0.38, s * 1.2), (0.55, -s, 0.25, -s * 1.0)])
        objs += m.tendril(f"Arm_Tip_Up_{s}", xz, tp, h + s * 45, 0.15, s * 1.25, 0.0078, mats,
                          offshoots=[(0.45, -s, 0.35, -s * 1.0)])
        objs += m.tendril(f"Arm_Tip_In_{s}", xz, tp, h + s * 100, 0.1, s * 1.1, 0.0065, mats)
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


GUNLANCE_BASE, GUNLANCE_TIP = 0.46, 1.74
SPRING_TOP = 1.45        # top of the ivory spring at rest


def gunlance_rib_path(k):
    a = math.radians(90 + 120 * k)
    radial = V(math.cos(a), math.sin(a), 0)
    base, tip = GUNLANCE_BASE, GUNLANCE_TIP
    return radial, [V(0, 0, base + 0.06) + radial * 0.045, V(0, 0, 1.05) + radial * 0.095,
                    V(0, 0, tip + 0.16) + radial * 0.016]


def gunlance_spring(mats, top=SPRING_TOP, name="Binding"):
    """The ivory spring bound around the ribs (two strands, three turns). On reload it
    compresses toward the root and springs back (states.py), so `top` is its upper end;
    the bottom stays put and it always clears the ribs."""
    _, rib = gunlance_rib_path(0)
    prof = m.catmull(rib, 80)                           # rib centre line, height -> radius

    def rib_radius(z):
        for p, q in zip(prof, prof[1:]):
            if p.z <= z <= q.z:
                u = (z - p.z) / max(q.z - p.z, 1e-6)
                return math.hypot(p.x, p.y) * (1 - u) + math.hypot(q.x, q.y) * u
        return 0.0

    z0, n, turns = GUNLANCE_BASE + 0.1, 160, 3.0
    objs = []
    for k in range(2):
        pts, radii = [], []
        for i in range(n):
            t = i / (n - 1)
            z = z0 + (top - z0) * t
            r = max(0.098 - 0.028 * t, rib_radius(z) + 0.0075)
            a = 0.3 + k * math.pi + 2 * math.pi * turns * t
            pts.append(V(r * math.cos(a), r * math.sin(a), z))
            radii.append(1 - 0.5 * t)
        objs.append(c.curve_tube(f"{name}_{k}", pts, radii, mats["ivory"], bevel=0.0026, resolution=2))
    return objs


def gunlance():
    """Openwork gunlance: three slim ribs of light around a thin glowing conduit (the
    trident as a gun barrel), bound by an ivory spring; a small energy core at the root
    and light muzzle halos at the tip for shelling."""
    mats = m.materials()
    rng = random.Random(71)
    objs = lance_grip(mats, rng)
    base, tip = GUNLANCE_BASE, GUNLANCE_TIP
    objs.append(c.curve_tube("Conduit", [V(0, 0, base), V(0, 0, tip)], [1, 0.8], mats["light"],
                             bevel=0.004, resolution=4))
    for k in range(3):
        radial, path = gunlance_rib_path(k)
        objs += m.path_blade(f"Rib_{k}", path, radial, lambda t: 0.016 * (1 - t) ** 0.6 + 0.002,
                             lambda t: 0.007 * (1 - t) ** 0.6, mats["blade"])
    objs += gunlance_spring(mats)
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

def phial_column(prefix, x, z0, count, step, mats, size=0.012):
    """Phials as a column of lit droplets floating beside the weapon, each in a small halo."""
    return m.floating_phials(prefix, [V(x, 0, z0 + step * k) for k in range(count)], (-1, 0, 0.35), (1, 0, 0.3),
                             mats, size=size)


# Spine and edge points of each sickle blade made, by name (build_weapon_kit.py fits the switch
# axe's morph from them: each axe blade turns into a fin on the sword's back).
SICKLES = {}


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
    SICKLES[name] = (spine, edge)
    return objs, spine


SWITCH_AXE_TOP = 1.1


def switch_axe_common(mats, rng):
    """What both modes share: the shaft with its gold vine, the floating collars, the
    scrollwork on the back, the prongs reaching from the shaft, and the phial column."""
    top = SWITCH_AXE_TOP
    objs = m.woven_tube("Shaft", [V(0, 0, 0), V(0, 0, top)], 0.019, mats["ivory"], rng)
    objs += pommel(mats, -0.01, 0.019)
    xz = m.plane_mapper((0, 0, 0), (1, 0, 0), (0, 0, 1))
    # Scrolls reaching out beneath each axe blade root, curling short of it.
    for k, (z, turns, head) in enumerate(zip((1.0, 0.94, 0.88), (1.3, -1.2, -1.4), (14, -4, -18))):
        objs += m.tendril(f"Prong_{k}", xz, (0.012, z), head, 0.085, turns, 0.0055, mats, curl_start=0.45)
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
    # Phial: lit droplets floating in a column behind the shaft, each in a small halo.
    objs += phial_column("Phial", -0.078, 0.5, 5, 0.068, mats)
    return objs


def switch_axe_axe_head(mats):
    """Axe mode head: three slim curved blades of light in a fan beside the shaft, and the
    light spike on top."""
    top = SWITCH_AXE_TOP
    specs = [
        ("Blade_Upper", [V(0.05, 0, 1.0), V(0.13, 0, 1.04), V(0.22, 0, 1.11), V(0.27, 0, 1.2)], 0.055),
        ("Blade_Middle", [V(0.05, 0, 0.94), V(0.16, 0, 0.955), V(0.26, 0, 0.945), V(0.33, 0, 0.92)], 0.065),
        ("Blade_Lower", [V(0.05, 0, 0.88), V(0.13, 0, 0.84), V(0.2, 0, 0.76), V(0.23, 0, 0.66)], 0.06),
    ]
    objs = []
    for name, ctrl, w in specs:
        objs += sickle_blade(name, ctrl, w, 0.011, mats)[0]
    objs += m.path_blade("Top_Spike", [V(0, 0, top - 0.02), V(0, 0, top + 0.16)], (0, 1, 0),
                         lambda t: 0.034 * (1 - t), lambda t: 0.01 * (1 - t), mats["blade"])
    objs += m.halo("Top_Halo", (0, 0, top + 0.01), 0.045, 0.0032, (0, 0, 1), mats["light"], tilt_deg=8)
    return objs


def sword_blade(name, z0, length, wmax, mats, n=90):
    """A long single-edged blade of light rising from the shaft top: spine on the axis
    bowing slightly back, the edge toward +X with a gentle S rhythm (the great sword's
    language, slimmer)."""
    spine, edge = [], []
    knots = [(0.0, 0.3 * wmax), (0.12, 0.8 * wmax), (0.45, wmax), (0.7, 0.85 * wmax), (0.88, 0.5 * wmax),
             (0.97, 0.15 * wmax), (1.0, 0.0)]
    for i in range(n):
        t = i / (n - 1)
        sp = V(-0.025 * t ** 2, 0, z0 + length * t)
        spine.append(sp)
        edge.append(sp + V(m.interp1d(knots, t), 0, 0.02 * math.sin(math.pi * t)))

    def thick(t):
        return 0.016 * (1 - t ** 3) + 0.0008

    objs = m.wedge_blade(name, spine, edge, thick, mats["blade"])
    objs += blade_dressing(name, spine, edge, thick, mats, trail=(0.25, 0.9), temper_u=0.3)
    return objs, spine, edge


def switch_axe_sword_head(mats, variant):
    """Sword mode. A: a long blade rises from the shaft and the three axe blades fold up
    along its back like feathers, smaller toward the tip. B: the middle axe blade grows into
    the long sword, the upper and lower fold up beside its root like closed wings."""
    top = SWITCH_AXE_TOP
    objs, spine, edge = sword_blade("Sword_Blade", top - 0.08, 0.82, 0.075, mats)
    objs += m.halo("Sword_Root_Halo", (0.02, 0, top - 0.04), 0.05, 0.0034, (0, 0, 1), mats["light"], tilt_deg=10)
    if variant == "a":
        # Fins on the spine side, rooted at the back of the blade, sweeping up and back.
        for name, u, size in (("Fin_Lower", 0.08, 1.0), ("Fin_Middle", 0.33, 0.82), ("Fin_Upper", 0.56, 0.64)):
            i = int(u * (len(spine) - 1))
            r = spine[i] + V(-0.006, 0, 0)
            ctrl = [r, r + V(-0.05, 0, 0.07) * size, r + V(-0.085, 0, 0.17) * size, r + V(-0.09, 0, 0.27) * size]
            objs += sickle_blade(name, ctrl, 0.045 * size, 0.009, mats, side=-1)[0]
    else:
        # Wings: the upper blade folds up on the spine side, the lower on the edge side.
        r = V(-0.01, 0, top - 0.05)
        ctrl = [r, r + V(-0.06, 0, 0.06), r + V(-0.1, 0, 0.17), r + V(-0.1, 0, 0.3)]
        objs += sickle_blade("Wing_Back", ctrl, 0.05, 0.010, mats, side=-1)[0]
        r = V(0.03, 0, top - 0.07)
        ctrl = [r, r + V(0.07, 0, 0.03), r + V(0.12, 0, 0.11), r + V(0.13, 0, 0.21)]
        objs += sickle_blade("Wing_Edge", ctrl, 0.045, 0.010, mats, side=1)[0]
    return objs


def switch_axe():
    """Axe mode. The head is Miquella's trident made of light: three slim curved blades
    floating in a fan beside the shaft (the upper one sweeping up, the middle one reaching
    out, the lower one hanging as the beard), edges all turned the same way like a
    pinwheel. Their outer ends draw the axe's silhouette. Three ivory prongs reach from the
    shaft toward the blade roots and curl short of them; floating collars mark the head.
    Scrollwork on the back, a light spike on top, the phials as lit droplets floating in
    small halos behind the shaft."""
    mats = m.materials()
    rng = random.Random(81)
    objs = switch_axe_common(mats, rng) + switch_axe_axe_head(mats)
    views = [("front", 0, 5), ("three_quarter", 35, 12), ("back_three_quarter", 145, 12)]
    m.render_sheets(OUT, "switch_axe", mats, (0.08, 0, 0.6), 2.7, views, res=(800, 1000),
                    extra=[("head", (0.15, 0, 0.93), 0.9, [("head", 25, 8)])])


def switch_axe_sword(variant="a"):
    """Sword mode (see switch_axe_sword_head)."""
    mats = m.materials()
    rng = random.Random(81)
    objs = switch_axe_common(mats, rng) + switch_axe_sword_head(mats, variant)
    views = [("front", 0, 5), ("three_quarter", 35, 12), ("back_three_quarter", 145, 12)]
    m.render_sheets(OUT, f"switch_axe_sword_{variant}", mats, (0.02, 0, 0.92), 3.1, views, res=(800, 1100),
                    extra=[("head", (0.0, 0, 1.3), 1.2, [("head", 25, 8)])])


# ------------------------------------------------------------------ charge blade

def charge_blade():
    """Sword & shield mode. The shield is the tree-sigil energy shield with five phials of
    light set into its rim and a floating edge on its lower-left rim that becomes the axe's
    cutting edge. Axe mode (the shield reshaped around the sword) is charge_blade_axe."""
    import blades
    mats = m.materials()
    rng = random.Random(91)
    blades.BLADE_LEN = 0.8
    sword = blades.build_sword("CB_Sword", mats["ivory"], mats["light"], mats["blade"], mats["core"], seed=9)
    sword.location = (-0.38, 0, 0.0)
    sword_phial_ring(mats, -0.38)
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


CB_AXE_OUTLINE = []      # the axe head's outline, the last one built


def sword_phial_ring(mats, x, ring=True):
    """The charge blade sword's phial ring: five droplets orbiting a halo above the guard."""
    import blades
    gz = blades.GUARD_Z + 0.13
    objs = m.halo("Sword_Phial_Ring", (x, 0, gz), 0.06, 0.0028, (0, 0, 1), mats["light"], tilt_deg=10) if ring else []
    for k in range(5):
        a = 2 * math.pi * k / 5
        pos = V(x + 0.06 * math.cos(a), 0.06 * math.sin(a), gz)
        objs += m.droplet(f"Sword_Phial_{k}", pos, 0.009, (-math.sin(a), math.cos(a), 0), mats["light"], stretch=1.1)
    return objs


def charge_blade_axe():
    """Axe mode. The sword slides into the shield and becomes the haft and the spine of the
    head; because the shield is light, its halo does not stay round but reshapes into a
    bardiche outline: a pointed upper horn, a long convex cutting edge, a beard hanging
    below and a concave underside. The membrane and the tree sigil re-flow into the new
    shape (stretched), a floating wedge of light rides the cutting edge with its
    afterimage, the five phials line up along the back in small halos, all lit (charged),
    and scrollwork dresses the joint."""
    import blades
    import sword_shield as ss
    mats = m.materials()
    rng = random.Random(92)
    blades.BLADE_LEN = 0.8
    blades.build_sword("CB_Sword", mats["ivory"], mats["light"], mats["blade"], mats["core"], seed=9)
    gz = blades.GUARD_Z + 0.13
    m.halo("Sword_Phial_Ring", (0, 0, gz), 0.06, 0.0028, (0, 0, 1), mats["light"], tilt_deg=10)

    # Head outline (XZ plane), counter-clockwise from the top of the neck: a short, narrow
    # neck against the sword, concave flares above and below, a pointed upper horn, a long
    # convex edge and a hooked beard, so it reads as an axe rather than a stretched shield.
    horn, beard = V(0.1, 0, 1.3), V(0.09, 0, 0.34)
    ctrl = [V(-0.03, 0, 1.03), V(0.01, 0, 1.08), V(0.05, 0, 1.18), horn, V(0.17, 0, 1.24), V(0.26, 0, 1.12),
            V(0.31, 0, 0.96), V(0.315, 0, 0.8), V(0.28, 0, 0.64), V(0.2, 0, 0.48), beard, V(0.07, 0, 0.44),
            V(0.05, 0, 0.56), V(0.02, 0, 0.67), V(-0.03, 0, 0.73), V(-0.04, 0, 0.88)]
    loop = m.resample(m.catmull(ctrl + [ctrl[0]], 200), 240)
    centroid = sum(loop, V(0, 0, 0)) / len(loop)
    # (build_weapon_kit.py: the rim's bones sit along this outline for the morph)
    CB_AXE_OUTLINE[:] = loop
    # Rim of light (the halo, reshaped) and a thinner inner line.
    m.path_blade("Axe_Rim", loop, (0, 1, 0), lambda t: 0.009, lambda t: 0.009, mats["light"], samples=240, subsurf=0)
    inner = [centroid.lerp(p, 0.93) for p in loop]
    c.curve_tube("Axe_Rim_Inner", [p + V(0, -0.002, 0) for p in inner], [1.0] * len(inner), mats["light"],
                 bevel=0.0022, resolution=2)
    membrane = m.membrane_material("Axe_Membrane", 0.34, 0.5, rim=0.12, center=0.01)
    mats["axe_membrane"] = membrane
    m.flat_fill("Axe_Membrane", loop[:-1], membrane, center_origin=True)
    # The sigil, re-flowed (stretched) into the taller head.
    ss.FRONT = -0.004
    leaves = ss.LeafBuilder()
    sig = ss.trunk(mats["light"]) + ss.crown(mats["light"], leaves, random.Random(9)) + ss.pods(mats["light"])
    sig.append(leaves.finish(mats["light"]))
    holder = m.group("Axe_Sigil", sig, location=(0.16, 0, 0.85))
    holder.scale = (0.8, 1, 1.2)
    # Cutting edge: a floating single-edged wedge riding outside the convex side.
    i0 = min(range(len(loop)), key=lambda i: (loop[i] - horn).length)
    i1 = min(range(len(loop)), key=lambda i: (loop[i] - beard).length)
    seg = loop[i0:i1 + 1]
    spine, edge = [], []
    knots = [(0.0, 0.004), (0.12, 0.022), (0.4, 0.045), (0.62, 0.055), (0.82, 0.04), (0.94, 0.016), (1.0, 0.0)]
    for i, p in enumerate(seg):
        t = i / (len(seg) - 1)
        out = (p - centroid)
        out.y = 0
        out.normalize()
        s = p + out * (0.022 + 0.02 * t ** 2)
        spine.append(s)
        edge.append(s + out * m.interp1d(knots, t))

    def thick(t):
        return 0.013 * (0.5 + 0.5 * math.sin(math.pi * t)) + 0.001

    m.wedge_blade("Axe_Edge", spine, edge, thick, mats["blade"])
    blade_dressing("Axe_Edge", spine, edge, thick, mats, trail=(0.15, 0.92), temper_u=0.35)
    # Phials along the back, each in a small halo, all lit.
    phial_column("Phial", -0.09, 0.76, 5, 0.075, mats)
    # Scrollwork at the joint where the head meets the haft.
    xz = m.plane_mapper((0, 0, 0), (1, 0, 0), (0, 0, 1))
    m.tendril("Joint_Cord", xz, (-0.02, 0.71), 200, 0.05, 0.0, 0.01, mats, curl_start=0.99)
    jp = (-0.068, 0.693)
    m.tendril("Joint_Down", xz, jp, 250, 0.24, 1.3, 0.009, mats, offshoots=[(0.35, -1, 0.35, -1.2)])
    m.tendril("Joint_Out", xz, jp, 178, 0.17, -1.35, 0.008, mats, offshoots=[(0.45, 1, 0.3, 1.0)])
    m.tendril("Joint_Up", xz, (-0.03, 1.03), 112, 0.17, 1.3, 0.0075, mats, offshoots=[(0.4, -1, 0.3, -1.0)])
    ss.add_backdrop()
    views = [("front", 0, 4), ("three_quarter", 30, 10)]
    m.render_sheets(OUT, "charge_blade_axe", mats, (0.1, 0, 0.62), 2.3, views, res=(800, 1000), cols=2,
                    extra=[("head", (0.13, 0, 0.84), 1.05, [("head", 15, 6)])])


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

# The rail of rings ahead of the arrow: at rest spread over the arrow, packed toward the bow
# like a spring being wound while the bow is drawn (weapons script: packed = 1).
BOW_ARROW_Z = 0.02
BOW_RAIL_N = 6
BOW_RAIL_REST = (-0.29, -0.70)            # first and last ring (x)
BOW_RAIL_PACKED = (-0.255, -0.028)        # first ring, then this step


def bow_rail_x(pack=0.0):
    out = []
    for i in range(BOW_RAIL_N):
        rest = BOW_RAIL_REST[0] + (BOW_RAIL_REST[1] - BOW_RAIL_REST[0]) * i / (BOW_RAIL_N - 1)
        packed = BOW_RAIL_PACKED[0] + BOW_RAIL_PACKED[1] * i
        out.append(rest + (packed - rest) * pack)
    return out


def build_bow(mats, rail_pack=0.0, with_arrow=True):
    """Recurve limbs of twisting strands ending in scrollwork tips, a string of light, and a
    light arrow drawn through a rail of shrinking rings (the light bowgun's signature).
    The bow stands in the XZ plane; the arrow points to -X, the archer is on +X."""
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
    if with_arrow:
        objs += needle_arrow("Drawn_Arrow", V(string_x, 0, BOW_ARROW_Z), V(-0.78, 0, BOW_ARROW_Z), mats)
    for i, x in enumerate(bow_rail_x(rail_pack)):
        t = i / (BOW_RAIL_N - 1)
        objs += m.halo(f"Arrow_Rail_{i}", (x, 0, BOW_ARROW_Z), 0.075 + (0.035 - 0.075) * t, 0.0045 - 0.0011 * t,
                       (1, 0, 0), mats["light"], tilt_deg=4.0 if i % 2 == 0 else -4.0)
    objs += m.halo("Rest_Halo", (grip_x - 0.03, 0, BOW_ARROW_Z), 0.04, 0.003, (1, 0, 0), mats["light"])
    return objs


def bow():
    mats = m.materials()
    build_bow(mats)
    views = [("profile", 0, 4), ("three_quarter", 35, 12), ("archer_view", 75, 6)]
    m.render_sheets(OUT, "bow", mats, (-0.18, 0, 0.0), 2.8, views, res=(1000, 900),
                    extra=[("rail", (-0.4, 0, 0.02), 1.1, [("rail", 60, 10)])])


def light_arrow(prefix, nock, tip, mats, head=0.45, width=0.062):
    """An arrow of light: three gold vanes of light at the nock, a thin shaft of light, a ring
    collar and a long leaf-shaped head like the dual blades' (the game's arrows have long
    heads too: about half the arrow). Proportions scale with the length."""
    nock, tip = Vector(nock), Vector(tip)
    d = (tip - nock).normalized()
    L = (tip - nock).length
    up = V(0, 0, 1) if abs(d.z) < 0.9 else V(1, 0, 0)
    side = d.cross(up).normalized()
    up = side.cross(d).normalized()
    base = nock + d * (L * (1 - head))
    objs = [c.curve_tube(f"{prefix}_Shaft", [nock + d * (L * 0.01), base + d * (L * 0.04)], [1, 1], mats["core"],
                         bevel=0.0036 * L, resolution=2)]
    # Head: a leaf blade, widest a third of the way, with a brighter vein.
    objs += m.path_blade(f"{prefix}_Head", [base, tip], up,
                         lambda t: width * L * math.sin(math.pi * min(1.0, (t + 0.06) / 0.98)) ** 0.7 * (1 - t) ** 0.35,
                         lambda t: 0.011 * L * (1 - t) ** 0.8, mats["blade"])
    objs += m.path_blade(f"{prefix}_Vein", [base + d * (L * 0.01), base + d * (L * head * 0.8)], up,
                         lambda t: 0.006 * L * (1 - t), lambda t: 0.013 * L * (1 - t) ** 0.8, mats["core"])
    objs += m.halo(f"{prefix}_Collar", base, 0.013 * L, 0.0022 * L, d, mats["light"])
    # Vanes: slim swept feathers of light, tallest near the back, a long slope to the front.
    shaft_r = 0.0036 * L
    vane_h = 0.026 * L

    def vane_w(t):           # t: back (0) -> front (1)
        return vane_h * min(1.0, (t + 0.3) / 0.42) * (1 - t) ** 0.9

    for k in range(3):
        a = math.radians(90 + 120 * k)
        radial = up * math.cos(a) + side * math.sin(a)
        objs += m.path_blade(f"{prefix}_Fletch_{k}", [nock + d * (L * 0.015), nock + d * (L * 0.19)],
                             d.cross(radial), vane_w, lambda t: 0.0012 * L, mats["light"],
                             offset_fn=lambda t: shaft_r + vane_w(t) / 2, n_sec=8, samples=40)
    # Nock: an ivory bead with a drop of light.
    objs += m.halo(f"{prefix}_Nock", nock + d * (L * 0.006), 0.0045 * L, 0.0028 * L, d, mats["ivory"])
    return objs


def needle_arrow(prefix, nock, tip, mats, girth=0.45):
    """The arrows are Miquella's Unalloyed Gold Needle (user, 2026-10-02: the light arrow was too
    thick for the rings and read as an energy weapon): gold metal with a faint warmth, the point
    forward, the twisted gold eye with its drop of light at the nock. The wyrmstake's needle
    (devices.needle) stretched to the arrow's length and slimmed: `girth` scales its thickness."""
    import devices
    from mathutils import Matrix
    mats.setdefault("gold", devices.gold_material())
    before = set(bpy.data.objects)
    devices.needle(mats, 0.5, V(0, 0, 0), V(0, 0, -1))
    objs = [o for o in bpy.data.objects if o not in before]
    nock, tip = Vector(nock), Vector(tip)
    L = (tip - nock).length
    k = L / 0.5
    rot = V(0, 0, -1).rotation_difference((nock - tip).normalized()).to_matrix().to_4x4()
    M = Matrix.Translation(tip) @ rot @ Matrix.Diagonal((k * girth, k * girth, k, 1.0))
    bpy.context.view_layer.update()
    for o in objs:
        o.name = f"{prefix}_{o.name.split('.')[0]}"
        if o.parent is None:
            o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()
    return [o for o in objs if o.type in ("MESH", "CURVE")]


# Quivers (the bow's second model). Built along +Z: the bottom at z 0, the mouth at QUIVER_LEN,
# the arrows' vanes standing out above it.
QUIVER_LEN = 0.55


def quiver_arrows(prefix, mats, n, spread_top, spread_bottom, nock_z, tip_z, rng):
    objs = []
    for k in range(n):
        a = 2 * math.pi * k / n + 0.35
        top = V(spread_top * math.cos(a), spread_top * math.sin(a), nock_z + rng.uniform(-0.012, 0.012))
        bot = V(spread_bottom * math.cos(a + 0.4), spread_bottom * math.sin(a + 0.4), tip_z)
        objs += needle_arrow(f"{prefix}_{k}", top, bot, mats)
    return objs


def quiver_cage(mats):
    """A: a slender lantern of woven ivory strands (like the hammer's), narrow at the bottom,
    gold filigree laid over it, a gold-threaded hoop at the mouth and a halo floating above it;
    the arrows' heads glow through the openwork; a lit drop floats under the bottom."""
    rng = random.Random(113)
    L, R = QUIVER_LEN, 0.042

    def radius(u):
        return R * (0.5 + 0.5 * smoothstep(min(1.0, u * 1.25)) ** 0.7)

    objs = m.strand_bundle("Quiver_Cage", [V(0, 0, 0.02), V(0, 0, L)], R, mats["ivory"], rng, n=22, twist=4.5,
                           radius_fn=lambda u: radius(u) / R, spread=(1, 1), bevel=0.0028, tip_taper=0.02)
    # Bottom: the strands gather into an ivory cap; a drop of light floats below it.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R * 0.62, location=(0, 0, 0.022))
    cap = bpy.context.active_object
    cap.name = "Quiver_Cap"
    cap.scale = (1, 1, 0.6)
    cap.data.materials.append(mats["ivory"])
    bpy.ops.object.shade_smooth()
    objs.append(cap)
    objs += m.floating_phials("Quiver_Drop", [V(0, 0, -0.03)], (0, 0, 1), (0, 0, 1), mats, size=0.011)
    for z, name in ((L, "Quiver_Mouth"), (0.13, "Quiver_Band")):
        r = radius(z / L) + 0.005
        ring = [V(r * math.cos(a), r * math.sin(a), z) for a in [2 * math.pi * i / 96 for i in range(97)]]
        objs += m.rope(name, ring, 0.0065 if z == L else 0.005, mats, strands=3, gold=True, taper=0.0, merge=0.999)

    def cage_map(x, v):                       # x along the quiver, v arc length at the cage's radius
        r = radius(x / L) + 0.006
        a = v / R
        return V(r * math.cos(a), r * math.sin(a), x)

    for k in range(3):
        sgn = 1 if k % 2 == 0 else -1
        objs += m.tendril(f"Quiver_Scroll_{k}", cage_map, (0.17 + 0.03 * k, 2 * math.pi * k / 3 * R), 70 - 25 * k,
                          0.24 - 0.03 * k, 1.3 * sgn, 0.0062, mats, strands=2, gold=False, strand_mat="light",
                          offshoots=[(0.45, -sgn, 0.38, -1.1 * sgn)])
    objs += m.halo("Quiver_Halo", (0, 0, L + 0.03), R + 0.016, 0.0032, (0, 0, 1), mats["light"], tilt_deg=9,
                   tilt_axis=(1, 0, 0))
    objs += quiver_arrows("Quiver_Arrow", mats, 4, 0.02, 0.012, L + 0.11, 0.06, rng)
    return objs


def quiver_bundle(mats):
    """B: no quiver at all: a fan of light arrows held by two floating halos, cradled by one
    slender ivory stem with a gold vine, which curls over the vanes at the top and into a scroll
    at the bottom, where a lit drop floats."""
    rng = random.Random(117)
    L = QUIVER_LEN
    objs = quiver_arrows("Quiver_Arrow", mats, 5, 0.034, 0.008, L + 0.11, 0.03, rng)
    for i, (z, r) in enumerate(((0.17, 0.026), (0.40, 0.04))):
        objs += m.halo(f"Quiver_Halo_{i}", (0, 0, z), r, 0.0034, (0, 0, 1), mats["light"],
                       tilt_deg=8 if i == 0 else -10, tilt_axis=(1, 0, 0))
    stem = m.catmull([V(0, 0.048, 0.03), V(0, 0.040, 0.2), V(0, 0.052, 0.38), V(0, 0.058, L)], 30)
    objs += m.strand_bundle("Quiver_Stem", stem, 0.007, mats["ivory"], rng, n=8, twist=9, bevel=0.0024, tip_taper=0.1)
    objs += m.wound_cord("Quiver_Vine", stem, 0.009, 5.0, 0.0024, mats, phase=0.8, strand_mat="light")
    yz = m.plane_mapper((0, 0, 0), (0, 1, 0), (0, 0, 1))
    top = (stem[-1].y, stem[-1].z)
    objs += m.tendril("Quiver_Crown_Long", yz, top, 125, 0.16, 1.35, 0.0065, mats,
                      offshoots=[(0.4, -1, 0.4, -1.1)])
    objs += m.tendril("Quiver_Crown_Short", yz, top, 70, 0.09, -1.2, 0.005, mats)
    objs += m.tendril("Quiver_Foot", yz, (stem[0].y, stem[0].z), -110, 0.11, -1.3, 0.0055, mats,
                      offshoots=[(0.45, 1, 0.4, 1.0)])
    objs += m.floating_phials("Quiver_Drop", [V(0, 0, -0.015)], (0, 0, 1), (0, 0, 1), mats, size=0.011)
    return objs


QUIVERS = {"a": quiver_cage, "b": quiver_bundle}


def quiver(variant):
    mats = m.materials()
    QUIVERS[variant](mats)
    views = [("side", 0, 6), ("three_quarter", 40, 12), ("mouth", 70, 35)]
    m.render_sheets(OUT, f"quiver_{variant}", mats, (0, 0, 0.3), 1.5, views, res=(800, 1000))


def arrow():
    mats = m.materials()
    needle_arrow("Arrow", V(0, 0, -0.5), V(0, 0, 0.5), mats)
    views = [("side", 0, 4), ("three_quarter", 40, 18)]
    m.render_sheets(OUT, "arrow", mats, (0, 0, 0), 1.4, views, res=(700, 1000))



# ------------------------------------------------------------------ charge parts (game kits, states.py)

HAMMER_HEAD_Z = 1.04
# Rings beyond each striking face, per charge level: a cone from large (at the face) to small,
# more rings each level (user, 2026-10-02: "a flat stack looks careless").
HAMMER_CHARGE = [(lv, 0.238 + 0.036 * i, 0.13 - 0.015 * i) for i, lv in enumerate((1, 1, 2, 2, 3, 3, 3))]


def hammer_charge_rings(mats):
    """Returns {level: [objects]}; ring names Charge_Ring_<i>_<side>."""
    out = {1: [], 2: [], 3: []}
    n = len(HAMMER_CHARGE)
    for i, (level, x, r) in enumerate(HAMMER_CHARGE):
        minor = 0.0046 - 0.002 * i / (n - 1)
        for sgn in (-1, 1):
            out[level] += m.halo(f"Charge_Ring_{i}_{'L' if sgn < 0 else 'R'}", (sgn * x, 0, HAMMER_HEAD_Z), r, minor,
                                 (1, 0, 0), mats["light"], tilt_deg=4 if i % 2 == 0 else -4, tilt_axis=(0, 0, 1))
    return out


LANCE_TIP = 1.98
# Rings from the vamplate toward the point (DESIGN: the cone of a lance of light), levels 1-3.
LANCE_CHARGE = (0.56, 1.64, 0.125, 0.032, 8, (1, 1, 1, 2, 2, 2, 3, 3))


def lance_charge_parts(mats):
    """Returns ({level: [ring objects]}, [point flare objects]): Charge_Ring_<k>, Point_Flare_A/B
    (a longer blade of light around the point at full charge)."""
    z0, z1, r0, r1, n, levels = LANCE_CHARGE
    rings = {1: [], 2: [], 3: []}
    for k in range(n):
        t = k / (n - 1)
        rings[levels[k]] += m.halo(f"Charge_Ring_{k}", (0, 0, z0 + (z1 - z0) * t), r0 + (r1 - r0) * t,
                                   0.0052 - 0.0022 * t, (0, 0, 1), mats["light"], tilt_deg=-3 if k % 2 == 0 else 3)
    flare = []
    for name, normal in (("Point_Flare_A", (0, 1, 0)), ("Point_Flare_B", (1, 0, 0))):
        flare += m.path_blade(name, [V(0, 0, LANCE_TIP - 0.38), V(0, 0, LANCE_TIP + 0.22)], normal,
                              lambda t: 0.085 * (1 - t) ** 0.9 * (0.75 + 0.25 * math.sin(math.pi * min(t / 0.3, 1))),
                              lambda t: 0.02 * (1 - t), mats["blade"])
    return rings, flare


# ------------------------------------------------------------------ insect glaive extracts (game version)

# Elden Ring's scarlet rot, frost and frenzied flame for red, white and orange (DESIGN). The
# prototype ones (status_fx.py) use hair, volumes and glass that a game model cannot carry:
# these are plain meshes with a colour band each (the fire and cold breath come later as effects).
EXTRACT_COLOURS = {"Red": ("#D88AA0", 0.0), "White": ("#CFE6FA", 0.3), "Orange": ("#FF8A1A", 3.0)}


def extract_materials():
    return {k: c.make_material(f"Extract_{k}", col, roughness=0.6 if k == "Red" else 0.3,
                               emission=col, strength=st)
            for k, (col, st) in EXTRACT_COLOURS.items()}


def extract_orb(kind, center, radius, mat, seed=7):
    """Red: a cluster of lumpy mould balls (like the rot-cure moss balls); White: a craggy chunk
    of ice with crystals breaking out; Orange: a lumpy glowing ember (its flames are an effect).
    Object names Orb_<kind>_<n>."""
    rng = random.Random(seed)
    center = Vector(center)
    objs = []

    def lump(name, at, r, noise, strength, subdiv=3, flat=False):
        bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=subdiv, location=at)
        o = bpy.context.active_object
        o.name = name
        tex = bpy.data.textures.new(f"{name}_Noise", noise)
        tex.noise_scale = r * (0.5 if noise == "CLOUDS" else 0.9)
        d = o.modifiers.new("lumps", "DISPLACE")
        d.texture, d.texture_coords, d.strength = tex, "OBJECT", r * strength
        o.data.materials.append(mat)
        (bpy.ops.object.shade_flat if flat else bpy.ops.object.shade_smooth)()
        return o

    if kind == "Red":
        for k, (off, sc) in enumerate([((0, 0, 0), 0.68), ((0.78, -0.1, 0.12), 0.58), ((-0.72, -0.05, 0.22), 0.56),
                                       ((0.08, -0.3, 0.72), 0.52), ((0.05, 0.35, -0.45), 0.5)]):
            objs.append(lump(f"Orb_Red_{k}", center + Vector(off) * radius, radius * sc, "CLOUDS", 0.35))
    elif kind == "White":
        core = lump("Orb_White_0", center, radius * 0.75, "VORONOI", 0.45, subdiv=2, flat=True)
        core.scale = (1.0, 0.85, 1.2)
        objs.append(core)
        for k in range(6):
            z = rng.uniform(-0.6, 1.0)
            a = rng.uniform(0, 2 * math.pi)
            d = Vector((math.sqrt(1 - z * z) * math.cos(a), math.sqrt(1 - z * z) * math.sin(a), z))
            root = center + d * radius * 0.4
            length, w = radius * rng.uniform(0.9, 1.35), radius * rng.uniform(0.28, 0.4)
            objs += m.path_blade(f"Orb_White_{k + 1}", [root, root + d * length], d.orthogonal(),
                                 lambda t, w=w: w * (1 - t ** 4) + 0.0003, lambda t, w=w: w * 0.86 * (1 - t ** 4) + 0.0003,
                                 mat, n_sec=6, samples=10, subsurf=0)
    else:
        objs.append(lump("Orb_Orange_0", center, radius * 0.95, "CLOUDS", 0.3))
    return objs


def extracts_preview():
    mats = extract_materials()
    lm = m.materials()
    for i, kind in enumerate(("Red", "White", "Orange")):
        extract_orb(kind, (0.12 * (i - 1), 0, 0), 0.03, mats[kind])
    m.render_sheets(OUT, "extract_orbs", lm, (0, 0, 0), 0.6, [("front", 0, 8), ("three_quarter", 40, 20)],
                    res=(900, 500))

WEAPONS = {
    "great_sword": great_sword,
    "hammer": hammer,
    "hunting_horn": hunting_horn,
    "lance": lance,
    "gunlance": gunlance,
    "switch_axe": switch_axe,
    "switch_axe_sword_a": lambda: switch_axe_sword("a"),
    "switch_axe_sword_b": lambda: switch_axe_sword("b"),
    "charge_blade": charge_blade,
    "charge_blade_axe": charge_blade_axe,
    "insect_glaive": insect_glaive,
    "bow": bow,
    "quiver_a": lambda: quiver("a"),
    "quiver_b": lambda: quiver("b"),
    "arrow": arrow,
    "extract_orbs": extracts_preview,
}

if __name__ == "__main__":
    c.reset_scene()
    WEAPONS[WEAPON]()
