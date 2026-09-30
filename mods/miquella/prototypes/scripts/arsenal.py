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


def trident_arms(mats, rng, z, reach, n=24, radius=0.016, lift=0.02, name="Arm"):
    """Two strand arms reaching sideways from the grip top, each parting into three
    (up / straight / down): the balanced guard of the dual blades, scaled."""
    objs = []
    for s in (-1, 1):
        path = [V(0, 0, z), V(s * reach * 0.35, 0, z + lift * 0.6), V(s * reach, 0, z + lift)]
        fan = [V(-s * reach * 0.05, 0, reach * 0.34), V(s * reach * 0.2, 0, reach * 0.04),
               V(-s * reach * 0.04, 0, -reach * 0.3)]
        objs += m.strand_bundle(f"{name}_{s}", path, radius, mats["ivory"], rng, n=n, split_at=0.45,
                                fan=fan, sub_radius=radius * 0.4, bevel=radius * 0.2, twist=6)
    return objs


# ------------------------------------------------------------------ great sword

def great_sword():
    """Asymmetric, single-edged and openwork. The back is a straight ivory trunk from guard
    to point, threaded with small floating rings; the one edge is a slim blade of light that
    swells out in a long convex sweep and returns to meet the trunk at the point. Between
    them a see-through veil, crossed by leafy branches growing from the trunk toward the
    edge like a feather's barbs. The guard is one-sided too: a trident arm on the back, a
    steeply tilted halo on the edge side. Long reach, little mass."""
    mats = m.materials()
    rng = random.Random(31)
    gt = 0.36
    base, tip = gt + 0.03, 1.58
    objs = m.woven_tube("Grip", [V(0, 0, 0), V(0, 0, gt)], 0.017, mats["ivory"], rng)
    objs += pommel(mats, -0.01, 0.017)
    objs += collar(mats, gt - 0.005, 0.019)
    # Back (-X): the trunk, straight, leaning slightly toward the point.
    spine = [V(-0.03, 0, base - 0.02).lerp(V(-0.004, 0, tip), i / 49) for i in range(50)]
    objs += m.strand_bundle("Spine", [V(0, 0, gt - 0.01)] + spine, 0.016, mats["ivory"], rng, n=18,
                            bevel=0.0028, twist=10, tip_taper=0.12, radius_fn=lambda u: 1 - 0.55 * u, samples=140)
    # Edge (+X): one long convex sweep of light from the base to the point.
    edge = m.catmull([V(0.045, 0, base), V(0.14, 0, base + 0.22), V(0.2, 0, base + 0.5), V(0.215, 0, base + 0.72),
                      V(0.17, 0, base + 0.95), V(0.08, 0, tip - 0.08), V(-0.004, 0, tip)], 80)
    objs += m.path_blade("Edge", edge, (0, 1, 0), lambda t: 0.022 * (1 - 0.6 * t ** 2) + 0.002,
                         lambda t: 0.0065 * (1 - 0.5 * t), mats["blade"], offset_fn=lambda t: 0.004, samples=140)
    objs += m.strand_bundle("Base_Bar", [V(-0.03, 0, base - 0.01), V(0.045, 0, base)], 0.008, mats["ivory"], rng,
                            n=8, bevel=0.0022, twist=6, samples=30, tip_taper=0.05)
    mats["veil"] = m.veil_material("Blade_Veil", 0.08, 0.7)
    objs += m.flat_fill("Blade_Veil", spine[1:] + list(reversed(edge))[1:-1], mats["veil"])

    # Branches from the trunk, rising diagonally toward the edge.
    def edge_x(z):
        best = min(edge, key=lambda p: abs(p.z - z))
        return best.x

    branches = []
    # Irregular on purpose: spacing, rise, reach and bend all vary, like a real branch.
    for z0, rise, reach, bend in ((base + 0.07, 0.13, 0.85, 0.035), (base + 0.3, 0.24, 1.0, 0.02),
                                  (base + 0.46, 0.15, 0.75, 0.045), (base + 0.7, 0.22, 1.0, 0.015),
                                  (base + 0.9, 0.12, 0.8, 0.03)):
        x0 = -0.03 + 0.026 * (z0 - base) / (tip - base)
        z1 = z0 + rise
        x1 = x0 + (edge_x(z1) - 0.018 - x0) * reach
        mid = V((x0 + x1) / 2, 0, (z0 + z1) / 2 + bend)
        branches.append(m.catmull([V(x0, 0, z0), mid, V(x1, 0, z1)], 36))
    for i, path in enumerate(branches):
        objs += m.strand_bundle(f"Branch_{i}", path, 0.0065, mats["ivory"], rng, n=7, bevel=0.002, twist=7,
                                tip_taper=0.3, radius_fn=lambda u: 1 - 0.4 * u)
    objs += leaf_pairs(branches, mats["light"], every=7, length=0.024, width=0.0095)
    # Small rings threaded on the trunk, shrinking toward the point.
    for k, (z, r) in enumerate(((base + 0.58, 0.046), (base + 0.78, 0.038), (base + 0.98, 0.031))):
        x = -0.03 + 0.026 * (z - base) / (tip - base)
        objs += m.halo(f"Spine_Ring_{k}", (x, 0, z), r, 0.0036, (0.022, 0, 1), mats["light"], tilt_deg=10 - 10 * k)
    # One-sided guard: a trident arm on the back, a tilted halo on the edge side.
    arm = [V(-0.01, 0, gt + 0.01), V(-0.08, 0, gt + 0.03), V(-0.17, 0, gt + 0.05)]
    fan = [V(0.01, 0, 0.07), V(-0.05, 0, 0.012), V(0.012, 0, -0.06)]
    objs += m.strand_bundle("Guard_Arm", arm, 0.017, mats["ivory"], rng, n=22, split_at=0.45, fan=fan,
                            sub_radius=0.006, bevel=0.0032, twist=6)
    objs += m.halo("Guard_Halo", (0.06, 0, gt + 0.08), 0.1, 0.004, (0, 0, 1), mats["light"], tilt_deg=32,
                   tilt_axis=(0, 1, 0))
    objs += m.halo("Guard_Halo_Inner", (0.07, 0, gt + 0.1), 0.075, 0.0022, (0, 0, 1), mats["light"], tilt_deg=38,
                   tilt_axis=(0, 1, 0))
    target = (0.05, 0, 0.74)
    views = [("front", 0, 4), ("three_quarter", 35, 10), ("back", 180, 4)]
    m.render_sheets(OUT, "great_sword", mats, target, 3.4, views, res=(700, 1000),
                    extra=[("blade", (0.08, 0, 0.95), 1.4, [("blade", 12, 5)])])


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
    objs += m.strand_bundle("Cage", barrel, 0.14, mats["ivory"], rng, n=18, twist=5.5,
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
    membrane = m.membrane_material("Shield_Membrane", R, 0.5, rim=0.2, center=0.015)
    mats["shield_membrane"] = membrane
    objs = m.halo("Shield_Halo", (0, 0, 0), R, 0.0055, (0, 1, 0), mats["light"])
    objs += m.halo("Shield_Halo_Inner", (0, -0.002, 0), R - 0.02, 0.0022, (0, 1, 0), mats["light"])
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
    objs.append(c.curve_tube("Conduit", [V(0, 0, base), V(0, 0, tip)], [1, 0.8], mats["core"],
                             bevel=0.0055, resolution=4))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        radial = V(math.cos(a), math.sin(a), 0)
        path = [V(0, 0, base + 0.06) + radial * 0.04, V(0, 0, 1.1) + radial * 0.068,
                V(0, 0, tip + 0.16) + radial * 0.012]
        objs += m.path_blade(f"Rib_{k}", path, radial, lambda t: 0.026 * (1 - t) ** 0.6 + 0.002,
                             lambda t: 0.007 * (1 - t) ** 0.6, mats["blade"])
    objs += double_helix("Binding", base + 0.1, 1.45, 0.07, 0.06, 3.0, mats["ivory"], 0.0026, phase=0.3)
    objs += m.droplet("Energy_Core", (0, 0, base + 0.03), 0.028, (0, 0, 1), mats["light"], stretch=1.4)
    for k, z in enumerate((0.95, 1.32)):
        objs += m.halo(f"Barrel_Halo_{k}", (0, 0, z), 0.085, 0.0035, (0, 0, 1), mats["light"], tilt_deg=5 - 10 * k)
    objs += m.halo("Muzzle_Halo", (0, 0, tip + 0.03), 0.06, 0.005, (0, 0, 1), mats["light"])
    objs += m.halo("Muzzle_Halo_Inner", (0, 0, tip - 0.01), 0.045, 0.0025, (0, 0, 1), mats["light"])
    energy_shield(mats, (0.46, -0.05, 0.92), 1.2)
    views = [("front", 0, 5), ("three_quarter", 30, 10), ("back_three_quarter", 150, 10)]
    m.render_sheets(OUT, "gunlance", mats, (0.2, 0, 0.95), 3.4, views, res=(900, 1000),
                    extra=[("muzzle", (0, 0, 1.45), 1.2, [("muzzle", 25, 30)])])


# ------------------------------------------------------------------ switch axe

def leaf_pairs(paths, mat, every=7, length=0.026, width=0.01, y=0.0):
    """Leaves of light in pairs along branch paths lying in the XZ plane (the sigil's leaves)."""
    import sword_shield as ss
    ss.FRONT = y
    leaves = ss.LeafBuilder()
    for path in paths:
        for k in range(every + 1, len(path) - 4, every):
            d = path[k + 1] - path[k - 1]
            ang = math.atan2(d.z, d.x)
            for side in (-1, 1):
                leaves.add(path[k].x, path[k].z, ang + side * math.radians(50), length=length, width=width)
    return [leaves.finish(mat)]


def switch_axe():
    """Axe mode, openwork: a bearded axe head drawn by a cutting edge of light and slim light
    outlines around a see-through veil; the shaft's strands part into three and grow through
    the veil as leafy tracery out to the edge. The phial is a droplet vial between two rings."""
    mats = m.materials()
    rng = random.Random(81)
    top = 1.1
    objs = m.woven_tube("Shaft", [V(0, 0, 0), V(0, 0, top)], 0.019, mats["ivory"], rng)
    objs += pommel(mats, -0.01, 0.019)
    # Head outline: upper edge -> cutting arc -> beard, closing along the shaft.
    ac, ar = V(0.02, 0, 0.94), 0.28
    arc = [ac + V(ar * math.cos(math.radians(a)), 0, ar * math.sin(math.radians(a))) for a in range(50, -62, -4)]
    upper = m.catmull([V(0.018, 0, 1.05), V(0.1, 0, 1.1), arc[0]], 20)
    lower = m.catmull([arc[-1], V(0.1, 0, 0.8), V(0.018, 0, 0.87)], 20)
    objs += m.path_blade("Cutting_Edge", arc, (0, 1, 0), lambda t: 0.018 * (0.6 + 0.4 * math.sin(math.pi * t)),
                         lambda t: 0.006, mats["blade"], offset_fn=lambda t: -0.004)
    for name, path in (("Upper_Edge", upper), ("Beard_Edge", lower)):
        objs += m.path_blade(name, path, (0, 1, 0), lambda t: 0.008, lambda t: 0.004, mats["blade"])
    mats["veil"] = m.veil_material("Axe_Veil", 0.16, 0.8)
    objs += m.flat_fill("Axe_Veil", upper + arc[1:-1] + lower, mats["veil"])
    # Tracery: three branches from the shaft to the edge, with leaves.
    root = V(0.015, 0, 0.955)
    branches = []
    for a, bend in ((32, 0.03), (0, 0.0), (-38, -0.03)):
        end = ac + V((ar - 0.012) * math.cos(math.radians(a)), 0, (ar - 0.012) * math.sin(math.radians(a)))
        mid = root.lerp(end, 0.5) + V(0, 0, bend)
        branches.append(m.catmull([root, mid, end], 36))
    for i, path in enumerate(branches):
        objs += m.strand_bundle(f"Tracery_{i}", path, 0.008, mats["ivory"], rng, n=8, bevel=0.0022, twist=7,
                                tip_taper=0.25, radius_fn=lambda u: 1 - 0.45 * u)
    objs += leaf_pairs(branches, mats["light"], every=8, length=0.022, width=0.0085)
    objs += collar(mats, 0.955, 0.021, "Head_Collar")
    # Back: a trident of small curls.
    for k, dz in enumerate((0.5, 0.0, -0.5)):
        objs += m.curl(f"Back_Curl_{k}", (-0.018, 0, 0.955 + dz * 0.07), (-1, 0, dz * 0.6), 0.09,
                       mats["ivory"], side=(0, 0, 1 if dz >= 0 else -1), bevel=0.004)
    objs += m.path_blade("Top_Spike", [V(0, 0, top - 0.02), V(0, 0, top + 0.16)], (0, 1, 0),
                         lambda t: 0.034 * (1 - t), lambda t: 0.01 * (1 - t), mats["blade"])
    objs += m.halo("Top_Halo", (0, 0, top + 0.01), 0.045, 0.0032, (0, 0, 1), mats["light"], tilt_deg=8)
    # Phial: a droplet vial of light behind the shaft, between two floating rings.
    px, pz = -0.05, 0.64
    objs += m.droplet("Phial", (px, 0, pz - 0.02), 0.02, (0, 0, 1), mats["light"], stretch=2.2)
    for k, z in enumerate((pz - 0.05, pz + 0.05)):
        objs += m.halo(f"Phial_Ring_{k}", (px, 0, z), 0.03, 0.0025, (0, 0, 1), mats["light"], tilt_deg=6 * (1 - 2 * k))
    views = [("front", 0, 5), ("three_quarter", 35, 12), ("back_three_quarter", 145, 12)]
    m.render_sheets(OUT, "switch_axe", mats, (0.08, 0, 0.6), 2.7, views, res=(800, 1000),
                    extra=[("head", (0.12, 0, 0.94), 1.0, [("head", 20, 8)])])


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
    # Axe edge: a slim edge of light running along the lower-left rim (the axe blade in axe
    # mode), tied to the halo by three short ivory strands.
    def rim(a_deg, off):
        a = math.radians(a_deg)
        return V(0.2 + (rad + off) * math.cos(a), -0.005, 0.55 + (rad + off) * 1.18 * math.sin(a))

    arc = [rim(140 + 125 * i / 29, 0.035) for i in range(30)]
    m.path_blade("Axe_Edge", arc, (0, 1, 0), lambda t: 0.034 * math.sin(math.pi * t) ** 0.6 + 0.003,
                 lambda t: 0.008 * math.sin(math.pi * t) ** 0.5 + 0.002, mats["blade"],
                 offset_fn=lambda t: 0.008 * math.sin(math.pi * t))
    for k, a in enumerate((165, 202, 240)):
        m.strand_bundle(f"Edge_Tie_{k}", [rim(a, 0.008), rim(a + 4, 0.022), rim(a, 0.034)], 0.006,
                        mats["ivory"], rng, n=6, bevel=0.0018, twist=6, samples=30)
    import sword_shield as ss
    ss.add_backdrop()
    views = [("front", 0, 4), ("three_quarter", 30, 10)]
    m.render_sheets(OUT, "charge_blade", mats, (-0.05, 0, 0.5), 2.3, views, res=(1000, 900), cols=2,
                    extra=[("shield", (0.2, 0, 0.55), 1.1, [("shield", 15, 5)])])


# ------------------------------------------------------------------ insect glaive

def butterfly(mats, center, scale):
    """The kinsect: a butterfly of light with ivory-veined wings."""
    objs = []
    cx, cy, cz = center
    # Wing discs are unit discs scaled into ellipses, so their object space spans +-1.
    wing_mat = m.membrane_material("Wing_Membrane", 1.0, 1.1, rim=0.5, center=0.08)
    mats["wing"] = wing_mat
    objs += m.droplet("Kinsect_Body", (cx, cy, cz - 0.02 * scale), 0.012 * scale, (0, 0, 1), mats["light"],
                      stretch=3.0)
    for s in (-1, 1):
        for k, (w, h, ang, dz) in enumerate(((0.1, 0.065, 35, 0.02), (0.07, 0.045, -30, -0.035))):
            wc = V(cx + s * w * 0.62 * scale * math.cos(math.radians(ang)) * 1.1, cy,
                   cz + dz * scale + s * 0 + w * 0.5 * scale * math.sin(math.radians(ang)))
            disc = m.membrane_disc(f"Wing_{s}_{k}", wc, 1.0, (0, 1, 0), wing_mat,
                                   scale=(w * scale * 0.62, h * scale * 0.62))[0]
            disc.rotation_mode = "XYZ"
            disc.rotation_euler = (math.pi / 2, math.radians(-s * ang), 0)
            objs.append(disc)
            outline = []
            for i in range(49):
                t = 2 * math.pi * i / 48
                lx, lz = w * scale * 0.62 * math.cos(t), h * scale * 0.62 * math.sin(t)
                ca, sa = math.cos(math.radians(s * ang)), math.sin(math.radians(s * ang))
                outline.append(wc + V(lx * ca - lz * sa, -0.001, lx * sa + lz * ca))
            objs.append(c.curve_tube(f"Wing_Edge_{s}_{k}", outline, [1] * 49, mats["ivory"], bevel=0.0018 * scale,
                                     resolution=2))
            # Veins from the body into the wing.
            for j in (-1, 0, 1):
                tipv = wc + V(s * w * 0.45 * scale * math.cos(math.radians(ang + j * 25)), -0.001,
                              w * 0.45 * scale * math.sin(math.radians(ang + j * 25)) * (1 if s > 0 else 1))
                objs.append(c.curve_tube(f"Vein_{s}_{k}_{j}", [V(cx, cy - 0.001, cz), tipv], [1, 0.4],
                                         mats["ivory"], bevel=0.0012 * scale, resolution=2))
    for s in (-1, 1):
        objs += m.curl(f"Antenna_{s}", (cx, cy - 0.004, cz + 0.02 * scale), (s * 0.5, 0, 1), 0.1 * scale,
                       mats["ivory"], side=(s, 0, 0), bevel=0.0012 * scale, turns=0.6)
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
    butterfly(mats, (0.34, -0.06, 1.18), 1.3)
    views = [("front", 0, 5), ("three_quarter", 30, 10), ("side", 90, 5)]
    m.render_sheets(OUT, "insect_glaive", mats, (0.1, 0, 0.82), 3.5, views, res=(800, 1000),
                    extra=[("kinsect", (0.34, -0.06, 1.18), 0.6, [("kinsect", 10, 10)])])


# ------------------------------------------------------------------ bow

def bow():
    """Recurve limbs of twisting strands ending in trident tips, a string of light, and a
    light arrow drawn through a rail of shrinking rings (the light bowgun's signature).
    The bow stands in the XZ plane; the arrow points to -X, the archer is on +X."""
    mats = m.materials()
    rng = random.Random(111)
    grip_x = -0.14
    objs = m.woven_tube("Riser", [V(grip_x + 0.01, 0, -0.13), V(grip_x - 0.005, 0, 0), V(grip_x + 0.01, 0, 0.13)],
                        0.018, mats["ivory"], rng)
    tips = []
    for s in (1, -1):
        limb = [V(grip_x + 0.01, 0, s * 0.12), V(grip_x - 0.05, 0, s * 0.33), V(grip_x + 0.0, 0, s * 0.53),
                V(grip_x + 0.12, 0, s * 0.65), V(grip_x + 0.2, 0, s * 0.69)]
        tips.append(limb[-1])
        fan = [V(0.05, 0, s * 0.05), V(0.075, 0, -s * 0.005), V(0.035, 0, -s * 0.05)]
        objs += m.strand_bundle(f"Limb_{s}", m.catmull(limb, 40), 0.017, mats["ivory"], rng, n=18, twist=12,
                                split_at=0.86, fan=fan, sub_radius=0.006, bevel=0.003,
                                radius_fn=lambda u: 1.0 - 0.45 * u, tip_taper=0.1)
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
