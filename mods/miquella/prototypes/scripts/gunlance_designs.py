"""Gunlance redesign proposals (user, 2026-10-03): the first gunlance (three ribs of light bound
by an ivory spring) "looks crude, has no design to it, and is hard to put effects on" -> start
over. Keep the golden needle (the Wyrmstake: Miquella's Unalloyed Gold Needle, devices.py).

Four directions. Each one is built so the gunlance's actions have big, readable parts to drive
in the game (lit parts = one material each, moving parts = bones, like the switch axe morph):
  A needle reliquary  a Gothic reliquary of flat ivory ribs with pointed-arch windows framed
                      in gold, the golden needle floating inside; Wyvern's Fire opens its front
                      half into eight arched petals and the needle slides out through the muzzle
  B lily              a braided stem with long lily leaves, a cluster of buds under the flower
                      (the shells) and a trumpet lily as the muzzle, stamens round the spear
                      point; Wyvern's Fire throws the petals back
  C Haligtree         the shield sigil's trunk: three ivory strands twisted round a core of
                      light, two eyelets, roots on the grip, five twigs with small needle eyes
                      holding the shells, a trident crown of scroll branches at the muzzle;
                      Wyvern's Fire spreads the crown
  D wings             two folded wings (ivory arm, coverts, ivory secondaries, primaries of
                      light with a light drop at the tips: the shells) along a conduit of light;
                      Wyvern's Fire spreads the wings
Rows of the sheet: at rest (whole weapon), the barrel close up, Wyvern's Fire charging.

Usage: python gunlance_designs.py <out_dir> [test] [A B C D]
"""
import math
import os
import random
import sys

import bpy
import bmesh  # noqa: E402  (after bpy)
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join("out", "gunlance_designs")
FLAGS = sys.argv[2:]
TEST = "test" in FLAGS
PICK = [f for f in FLAGS if f in ("A", "B", "C", "D")] or ["A", "B", "C", "D"]

import common as c                       # noqa: E402
import motifs as m                       # noqa: E402
from motifs import V, smoothstep         # noqa: E402
import devices                           # noqa: E402  (rewrites sys.argv for states)
import states as st                      # noqa: E402
import arsenal                           # noqa: E402

TIP = 1.98                               # point of the spear (the old gunlance's length)


# ------------------------------------------------------------------ helpers

def rot_about(p, hinge, axis, angle):
    return hinge + Quaternion(axis.normalized(), angle) @ (p - hinge)


def ring_frame(phi):
    """Radial and circumferential unit vectors at angle phi round the weapon's axis."""
    return V(math.cos(phi), math.sin(phi), 0), V(-math.sin(phi), math.cos(phi), 0)


def tube(name, pts, mat, bevel, taper=(1.0, 1.0), bulge=False):
    n = len(pts)
    if bulge:                            # thin at both ends, full in the middle
        radii = [0.3 + 0.7 * math.sin(math.pi * i / (n - 1)) for i in range(n)]
    else:
        radii = [taper[0] + (taper[1] - taper[0]) * i / (n - 1) for i in range(n)]
    return [c.curve_tube(name, pts, radii, mat, bevel=bevel, resolution=2)]


def smooth_path(pts, n=30):
    return m.resample(m.catmull(pts, max(len(pts) * 12, 24)), n)


def capsule(name, center, radius, length, direction, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=24, ring_count=12, location=Vector(center))
    o = bpy.context.active_object
    o.name = name
    o.scale = (radius, radius, length / 2)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = V(0, 0, 1).rotation_difference(Vector(direction).normalized())
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return [o]


def sphere(name, center, radius, mat):
    return capsule(name, center, radius, 2 * radius, (0, 0, 1), mat)


def sheet(name, center, side, width_fn, mat, cup=0.12, thick=0.0025, n_u=9, samples=60):
    """A thin petal or leaf lofted along `center` with its width along the fixed `side` vector
    (the path stays perpendicular to it), cupped along its normal, made solid. Returns the
    objects and the two rim lines and the outer midline (for light edges and ribs)."""
    pts = smooth_path(center, samples)
    side = Vector(side).normalized()
    bm = bmesh.new()
    rows, left, right, mid = [], [], [], []
    for i, p in enumerate(pts):
        t = i / (samples - 1)
        tan = (pts[min(i + 1, samples - 1)] - pts[max(i - 1, 0)]).normalized()
        nrm = side.cross(tan).normalized()
        w = max(width_fn(t), 0.0005)
        row = []
        for j in range(n_u):
            u = 2 * j / (n_u - 1) - 1
            row.append(bm.verts.new(p + side * (u * w / 2) + nrm * (cup * w * u * u)))
        rows.append(row)
        left.append(p - side * (w / 2) + nrm * (cup * w))
        right.append(p + side * (w / 2) + nrm * (cup * w))
        mid.append(p + nrm * (thick / 2 + 0.0006))
    for i in range(samples - 1):
        for j in range(n_u - 1):
            bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
    obj = m.mesh_obj(name, bm, mat, subsurf=0)
    sol = obj.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = thick
    sol.offset = 0.0
    sub = obj.modifiers.new("smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    return [obj], (left, right), mid


def grip(mats, rng):
    objs = m.woven_tube("Grip", [V(0, 0, 0), V(0, 0, 0.34)], 0.019, mats["ivory"], rng)
    objs += arsenal.pommel(mats, -0.01, 0.019)
    objs += arsenal.collar(mats, 0.335, 0.022, "Grip_Collar")
    return objs


def leaf_point(name, z0, z1, width, mats, thick=0.009):
    """The spear point: a leaf of light (narrow root, full belly, long point), crossed by a
    narrower one, bright fuller lines on its faces."""
    def w(t):
        return width * math.sin(math.pi * min(t / 0.97, 1.0) ** 0.62) ** 0.9

    def th(t):
        return thick * (1 - t) ** 0.7 + 0.0008

    objs = m.path_blade(f"{name}_A", [V(0, 0, z0), V(0, 0, z1)], (0, 1, 0), w, th, mats["blade"])
    objs += m.path_blade(f"{name}_B", [V(0, 0, z0), V(0, 0, z1 - 0.05)], (1, 0, 0), lambda t: 0.5 * w(t), th,
                         mats["blade"])
    objs += m.core_lines(f"{name}_Core", [V(0, 0, z0 + 0.02), V(0, 0, z1 - 0.04)], (0, 1, 0), th, mats["core"])
    return objs


def scroll_crown(prefix, mats, z, n, length, turns, radius, r0=0.022, heading=-30.0, phase=0.0,
                 strand_mat="ivory"):
    """n scrolls round the axis at height z, each curling in the plane of its own radius."""
    objs = []
    for k in range(n):
        radial, _ = ring_frame(phase + 2 * math.pi * k / n)
        plane = m.plane_mapper(V(0, 0, z) + radial * r0, radial, V(0, 0, 1))
        objs += m.tendril(f"{prefix}_{k}", plane, (0, 0), heading, length, turns, radius, mats, strands=2,
                          gold=strand_mat == "ivory", strand_mat=strand_mat, curl_start=0.35)
    return objs


def lyre(prefix, mapper, base, length, turns, radius, mats, spread=22.0, heading=0.0, strand_mat="light"):
    """Two scrolls leaving one point back to back and curling outward (a filigree lyre),
    each with a small inner curl."""
    objs = []
    for s in (-1, 1):
        objs += m.tendril(f"{prefix}_{'L' if s < 0 else 'R'}", mapper, base, heading + s * spread, length,
                          s * turns, radius, mats, strands=2, gold=False, strand_mat=strand_mat, curl_start=0.3,
                          offshoots=[(0.42, -s, 0.4, -s * 1.0)])
    return objs


def charge_glow(mats, z, orb=0.032, halos=((0.10, 0.10), (0.19, 0.13), (0.28, 0.16))):
    """Wyvern's Fire gathering at the muzzle: an orb of light and rings stacking forward."""
    objs = sphere("Charge_Orb", (0, 0, z), orb, mats["phial_lit"])
    for k, (dz, r) in enumerate(halos):
        objs += m.halo(f"Charge_Halo_{k}", (0, 0, z + dz), r, 0.0048 - 0.0008 * k, (0, 0, 1), mats["light"],
                       tilt_deg=6 * (-1) ** k, tilt_axis=(1, 0, 0))
    return objs


# ------------------------------------------------------------------ A needle reliquary

A_Z0, A_Z1, A_HINGE = 0.47, 1.56, 1.05      # cage root, muzzle end, ring where the front opens
A_TIERS = ((0.56, 0.80), (0.80, 1.05), (1.05, 1.30), (1.30, 1.49))
A_RIBS = 8


def a_radius(z):
    t = min(max((z - A_Z0) / (A_Z1 - A_Z0), 0.0), 1.0)
    return 0.02 + 0.075 * math.sin(math.pi * t ** 0.8) ** 0.85


def a_surf(phi, z, lift=0.0):
    radial, _ = ring_frame(phi)
    return V(0, 0, z) + radial * (a_radius(z) + lift)


def lancet(phi_c, z_lo, z_hi, margin=0.0095):
    """Outline of a pointed (equilateral) arch window on the cage between two ribs."""
    z_sill, z_apex = z_lo + 0.014, z_hi - 0.014
    z_s = z_sill + 0.55 * (z_apex - z_sill)
    pts = [(-1.0, z_sill + (z_s - z_sill) * i / 11) for i in range(12)]
    for i in range(1, 25):
        th = math.radians(180 - 60 * i / 24)
        pts.append((1 + 2 * math.cos(th), z_s + 2 * math.sin(th) / math.sqrt(3) * (z_apex - z_s)))
    for i in range(1, 25):
        th = math.radians(60 - 60 * i / 24)
        pts.append((-1 + 2 * math.cos(th), z_s + 2 * math.sin(th) / math.sqrt(3) * (z_apex - z_s)))
    pts += [(1.0, z_s - (z_s - z_sill) * i / 11) for i in range(1, 12)]
    pts += [(1.0 - 2.0 * i / 11, z_sill) for i in range(1, 12)]
    return [a_surf(phi_c + x * (math.pi / A_RIBS - margin / a_radius(z)), z, 0.003) for x, z in pts]


def rib_ribbon(name, path, side, mats, width):
    """A flat ivory rib with a gold line inlaid along its outer face."""
    rib, _, mid = sheet(name, path, side, lambda t: width, mats["ivory"], cup=-0.08, thick=0.0034, n_u=5,
                        samples=max(len(path) * 2, 24))
    return rib + tube(name + "_Gold", mid, mats["light"], 0.0011)


def design_a(mats, rng, fire):
    """Needle reliquary: a Gothic reliquary of flat ivory ribs and rings with pointed-arch
    windows framed in gold (filigree lyres in the lower ones); through them the golden needle
    floats on the axis, its eye glowing in the bulb. Wyvern's Fire: the front half splits
    into eight arched petals that open, the needle slides out through the muzzle."""
    objs = grip(mats, rng)
    objs += scroll_crown("A_Guard", mats, 0.395, 6, 0.08, 1.25, 0.0042, heading=-28, phase=0.26)
    objs += m.halo("A_Guard_Halo", (0, 0, 0.45), 0.075, 0.003, (0, 0, 1), mats["light"])
    open_rad = math.radians(42) if fire else 0.0

    def petal_xf(phi_c):
        if not open_rad:
            return (lambda p: p), (lambda v: v)
        hinge = a_surf(phi_c, A_HINGE)
        q = Quaternion(ring_frame(phi_c)[1], open_rad)
        return (lambda p: hinge + q @ (p - hinge)), (lambda v: q @ v)

    for k in range(A_RIBS):              # lower half: whole ribs
        phi = 2 * math.pi * k / A_RIBS
        rear = [a_surf(phi, A_Z0 + (A_HINGE - A_Z0) * i / 29) for i in range(30)]
        objs += rib_ribbon(f"A_Rib_{k}", rear, ring_frame(phi)[1], mats, 0.011)
    for k in range(A_RIBS):              # upper half: eight petals, each with half a rib on both edges
        phi_c = 2 * math.pi * (k + 0.5) / A_RIBS
        xf, vf = petal_xf(phi_c)
        for sgn in (-1, 1):
            phi_e = phi_c + sgn * math.pi / A_RIBS
            path = [a_surf(phi_e - sgn * 0.00275 / a_radius(z), z) for z in
                    (A_HINGE + (A_Z1 - 0.012 - A_HINGE) * i / 23 for i in range(24))]
            objs += rib_ribbon(f"A_Petal_{k}_{sgn}", [xf(p) for p in path], vf(ring_frame(phi_e)[1]), mats, 0.0055)
        for z in (1.30, 1.49):
            arc = [a_surf(phi_c + (j / 15 - 0.5) * 2 * math.pi / A_RIBS, z, 0.002) for j in range(16)]
            objs += tube(f"A_Arc_{k}_{z}", [xf(p) for p in arc], mats["ivory"], 0.0042)
        tip = xf(a_surf(phi_c, A_Z1 - 0.02, 0.004))
        objs += m.droplet(f"A_Petal_Bud_{k}", tip, 0.0042, (xf(a_surf(phi_c, A_Z1)) - xf(a_surf(phi_c, 1.45)))
                          .normalized(), mats["light"], stretch=1.4)
    for z in (0.56, 0.80):
        objs += m.halo(f"A_Band_{z}", (0, 0, z), a_radius(z) + 0.002, 0.0042, (0, 0, 1), mats["ivory"])
    objs += m.halo("A_Hinge_Band", (0, 0, A_HINGE), a_radius(A_HINGE) + 0.003, 0.0056, (0, 0, 1), mats["ivory"])
    objs += m.halo("A_Hinge_Gold", (0, 0, A_HINGE - 0.014), a_radius(A_HINGE - 0.014) + 0.002, 0.0017, (0, 0, 1),
                   mats["light"])
    objs += m.halo("A_Waist_Halo", (0, 0, A_HINGE + 0.03), a_radius(A_HINGE) + 0.05, 0.0036, (0, 0, 1),
                   mats["light"], tilt_deg=9, tilt_axis=(1, 0, 0))
    objs += m.halo("A_Root_Band", (0, 0, A_Z0 + 0.025), a_radius(A_Z0 + 0.025) + 0.003, 0.0038, (0, 0, 1),
                   mats["ivory"])
    for tier, (z_lo, z_hi) in enumerate(A_TIERS):
        front = z_lo >= A_HINGE - 1e-6
        for k in range(A_RIBS):
            phi_c = 2 * math.pi * (k + 0.5) / A_RIBS
            xf, _ = petal_xf(phi_c) if front else ((lambda p: p), None)
            objs += tube(f"A_Window_{tier}_{k}", [xf(p) for p in lancet(phi_c, z_lo, z_hi)], mats["light"], 0.0012)
            z_apex = z_hi - 0.014
            objs += sphere(f"A_Apex_{tier}_{k}", xf(a_surf(phi_c, z_apex - 0.016, 0.003)), 0.0034, mats["light"])
            if not front:                # filigree lyre in each lower window

                def wmap(x, y, phi_c=phi_c):
                    return a_surf(phi_c + y / a_radius(x), x, 0.003)

                z_sill = z_lo + 0.014
                objs += lyre(f"A_Lyre_{tier}_{k}", wmap, (z_sill + 0.01, 0.0), 0.4 * (z_apex - z_sill), 1.25, 0.0017,
                             mats, spread=9)
    slide = 0.15 if fire else 0.0
    c.set_emission_strength(mats["gold"], 1.4)
    objs += devices.needle(mats, length=1.0, base=V(0, 0, 1.555 + slide), direction=V(0, 0, -1))
    for k in range(8):                   # calyx at the muzzle
        radial, circ = ring_frame(2 * math.pi * k / 8)
        bend = math.radians(24 + (40 if fire else 0))
        d0 = V(0, 0, 1) * math.cos(bend) + radial * math.sin(bend)
        base = V(0, 0, 1.54) + radial * 0.018
        sep, _, mid = sheet(f"A_Sepal_{k}", [base, base + d0 * 0.05, base + d0 * 0.09 + radial * 0.008], circ,
                            lambda t: 0.022 * math.sin(math.pi * min(t / 0.98, 1) ** 0.7) ** 0.8, mats["ivory"],
                            cup=-0.15, thick=0.003, samples=24)
        objs += sep + tube(f"A_Sepal_Rib_{k}", mid[2:-3], mats["light"], 0.0011, (1.0, 0.4))
    objs += m.halo("A_Muzzle_Halo", (0, 0, 1.635), 0.066, 0.0036, (0, 0, 1), mats["light"])
    objs += m.halo("A_Muzzle_Inner", (0, 0, 1.605), 0.042, 0.0022, (0, 0, 1), mats["light"])
    objs += leaf_point("A_Point", 1.58, TIP, 0.05, mats)
    objs += m.floating_phials("A_Shell", [V(0.17, 0, z) for z in (0.585, 0.665, 0.745, 0.825, 0.905)], (0, 0, 1),
                              (0, 0, 1), mats, size=0.0095)
    if fire:
        objs += charge_glow(mats, 1.66, orb=0.03, halos=((0.08, 0.10), (0.16, 0.13), (0.24, 0.16)))
    return objs


# ------------------------------------------------------------------ B lily

B_THROAT = 1.36


def lily_profile(fire, bloom=None):
    """(radius, height) along a tepal: up the trumpet, flaring, the tip rolled back. bloom
    goes from the flower at rest (0) to thrown back for Wyvern's Fire (1)."""
    rest = [(0.016, 1.36), (0.026, 1.45), (0.045, 1.53), (0.075, 1.595), (0.112, 1.632), (0.142, 1.645),
            (0.158, 1.632)]
    thrown = [(0.016, 1.36), (0.028, 1.44), (0.052, 1.51), (0.094, 1.553), (0.138, 1.566), (0.172, 1.546),
              (0.186, 1.514)]
    b = (1.0 if fire else 0.0) if bloom is None else bloom
    return [(r0 + (r1 - r0) * b, z0 + (z1 - z0) * b) for (r0, z0), (r1, z1) in zip(rest, thrown)]


def design_b(mats, rng, fire, bloom=None):
    """Lily: a braided ivory stem wound with a gold vine and four long lily leaves; under the
    flower a cluster of five buds holds the shells (light at their tips); the muzzle is a
    trumpet lily with light-rimmed tepals and six stamens round the spear point (the pistil)."""
    objs = grip(mats, rng)
    objs += m.halo("B_Guard_Halo", (0, 0, 0.36), 0.042, 0.0028, (0, 0, 1), mats["light"])
    for k in range(3):                   # a sheath of three leaves above the grip
        radial, circ = ring_frame(2 * math.pi * k / 3 + 0.5)
        prof = [(0.016, 0.345), (0.036, 0.41), (0.056, 0.48), (0.066, 0.55), (0.06, 0.615)]
        leaf, _, mid = sheet(f"B_Sheath_{k}", [V(0, 0, z) + radial * r for r, z in prof], circ,
                             lambda t: 0.055 * math.sin(math.pi * min(t / 0.97, 1) ** 0.75) ** 0.7,
                             mats["ivory"], cup=-0.12, thick=0.003)
        objs += leaf + tube(f"B_Sheath_Rib_{k}", mid[3:-6], mats["light"], 0.0013, (1.0, 0.3))
    stem = [V(0, 0, 0.34 + (B_THROAT + 0.03 - 0.34) * i / 59) for i in range(60)]
    objs += m.rope("B_Stem", stem, 0.0125, mats, strands=3, gold=True, taper=0.3, merge=0.999)
    objs += m.wound_cord("B_Vine", [V(0, 0, 0.42), V(0, 0, 1.30)], 0.0175, 3.2, 0.0022, mats, strand_mat="light",
                         taper=0.5)
    for i, (z, a) in enumerate(((0.62, -0.5), (0.74, 2.3), (0.86, 4.1), (0.97, 0.9))):   # leaves
        radial, circ = ring_frame(a)
        length = 0.25 - 0.022 * i
        path = [V(0, 0, z) + radial * 0.012, V(0, 0, z + 0.35 * length) + radial * 0.05,
                V(0, 0, z + 0.7 * length) + radial * 0.083, V(0, 0, z + length) + radial * 0.098]
        leaf, rims, mid = sheet(f"B_Leaf_{i}", path, circ,
                                lambda t: 0.026 * math.sin(math.pi * min(t / 0.98, 1) ** 0.6) ** 0.8,
                                mats["ivory"], cup=-0.22, thick=0.0024)
        objs += leaf + tube(f"B_Leaf_Rib_{i}", mid[2:-6], mats["light"], 0.0012, (1.0, 0.3))
        for e, rim in enumerate(rims):
            objs += tube(f"B_Leaf_Rim_{i}_{e}", rim[3:-2], mats["light"], 0.0008, bulge=True)
    golden = math.radians(137.5)
    for i in range(5):                   # the buds = the shells, clustered under the flower
        z = 1.05 + 0.055 * i
        radial, _ = ring_frame(0.3 + golden * i)
        reach = 0.066 - 0.006 * i
        ped = [V(0, 0, z) + radial * 0.012, V(0, 0, z + 0.022) + radial * (0.6 * reach),
               V(0, 0, z + 0.05) + radial * reach]
        objs += tube(f"B_Pedicel_{i}", smooth_path(ped, 24), mats["ivory"], 0.0034, (1.0, 0.7))
        d = (radial * 0.38 + V(0, 0, 1)).normalized()
        objs += m.droplet(f"B_Bud_{i}", ped[-1] + d * 0.013, 0.0165, d, mats["ivory"], stretch=2.5)
        for j in range(3):               # gold seams of the closed tepals
            a = 2 * math.pi * j / 3 + 0.4
            u, v, _ = m.basis(d)
            off = u * math.cos(a) + v * math.sin(a)
            seam = [ped[-1] + d * (0.013 + 0.058 * f) + off * (0.0168 * math.sin(math.pi * (0.5 + 0.5 * f)) ** 0.9)
                    for f in (x / 16 for x in range(17))]
            objs += tube(f"B_Bud_Seam_{i}_{j}", seam, mats["light"], 0.0009, (1.0, 0.3))
        objs += m.floating_phials(f"B_Shell_{i}", [ped[-1] + d * 0.082], d, d, mats, size=0.0062)
    for k in range(6):                   # the trumpet
        radial, circ = ring_frame(2 * math.pi * k / 6)
        sc, wmax = (0.93, 0.054) if k % 2 else (1.0, 0.062)
        path = [V(0, 0, z) + radial * (r * sc) for r, z in lily_profile(fire, bloom)]
        petal, rims, mid = sheet(
            f"B_Tepal_{k}", path, circ,
            lambda t, wmax=wmax: wmax * math.sin(math.pi * min(t / 0.985, 1) ** 0.85) ** 0.6
            * (0.35 + 0.65 * smoothstep(t / 0.35)), mats["ivory"], cup=0.1, thick=0.0026)
        objs += petal
        for e, rim in enumerate(rims):
            objs += tube(f"B_Tepal_Rim_{k}_{e}", rim[4:], mats["light"], 0.0013, bulge=True)
        objs += tube(f"B_Tepal_Mid_{k}", mid[2:-8], mats["light"], 0.0012, (1.0, 0.3))
    for k in range(6):                   # stamens
        radial, circ = ring_frame(2 * math.pi * (k + 0.5) / 6)
        b = (1.0 if fire else 0.0) if bloom is None else bloom
        r_end, z_end = 0.056 + 0.034 * b, 1.722 + 0.023 * b
        fil = smooth_path([V(0, 0, 1.40) + radial * 0.008, V(0, 0, 1.53) + radial * 0.022,
                           V(0, 0, 1.65) + radial * (r_end * 0.75), V(0, 0, z_end) + radial * r_end], 30)
        objs += tube(f"B_Stamen_{k}", fil, mats["light"], 0.0016, (1.0, 0.6))
        objs += capsule(f"B_Anther_{k}", fil[-1] + radial * 0.002, 0.004, 0.017, circ, mats["phial_lit"])
    objs += leaf_point("B_Pistil", 1.44, TIP, 0.04, mats)
    b = (1.0 if fire else 0.0) if bloom is None else bloom
    objs += m.halo("B_Mouth_Halo", (0, 0, 1.655 - 0.069 * b), 0.19 + 0.025 * b, 0.0038, (0, 0, 1),
                   mats["light"], tilt_deg=5, tilt_axis=(1, 0, 0))
    if fire:
        objs += charge_glow(mats, 1.60, orb=0.036, halos=((0.12, 0.10), (0.22, 0.13), (0.32, 0.16)))
    return objs


# ------------------------------------------------------------------ C Haligtree

C_SPLIT = 1.40
C_EYES = (0.74, 1.12)


def braid(k, z0, z1, n=200, r0=0.0125, turns_per_m=3.2, extra=0.0):
    """One strand of the trunk's three-strand twist, bulging open round the two eyelets."""
    pts = []
    for i in range(n):
        z = z0 + (z1 - z0) * i / (n - 1)
        bulge = sum(0.026 * math.exp(-((z - ze) / 0.05) ** 2) for ze in C_EYES)
        a = 2 * math.pi * (k / 3 + turns_per_m * (z - z0))
        r = r0 + bulge + extra
        pts.append(V(r * math.cos(a), r * math.sin(a), z))
    return pts


def pod(prefix, z, phi, mats):
    """A shell: a twig off the trunk ending in an eyelet of twisted ivory and gold wire
    (the needle's eye, small) holding a drop of light."""
    radial, circ = ring_frame(phi)
    twig = smooth_path([V(0, 0, z) + radial * 0.014, V(0, 0, z + 0.012) + radial * 0.036,
                        V(0, 0, z + 0.03) + radial * 0.052], 20)
    objs = tube(f"{prefix}_Twig", twig, mats["ivory"], 0.0032, (1.0, 0.7))
    d = (twig[-1] - twig[-4]).normalized()
    top, eye_h, eye_w = twig[-1], 0.044, 0.012
    for k in range(2):
        loop = []
        for i in range(81):
            t = i / 80
            a = 2 * math.pi * t
            tw = 0.0016 * math.sin(2 * math.pi * 7 * t + k * math.pi)
            loop.append(top + d * (eye_h / 2 * (1 - math.cos(a))) + circ * ((eye_w + tw) * math.sin(a))
                        + d.cross(circ) * tw)
        objs += tube(f"{prefix}_Eye_{k}", loop, mats["ivory"] if k == 0 else mats["light"], 0.0018)
    objs += m.droplet(f"{prefix}_Drop", top + d * eye_h * 0.42, 0.0075, d, mats["phial_lit"], stretch=1.4)
    return objs


def design_c(mats, rng, fire):
    """Haligtree: the barrel is the shield sigil's trunk, three ivory strands twisted round a
    core of light, opening into two eyelets with a light inside; roots grip the grip; five
    twigs carry the shells in small needle eyes; at the muzzle the trunk parts into a
    trident crown of scroll branches with paired light leaves round a fruit of light."""
    objs = grip(mats, rng)
    objs += scroll_crown("C_Root", mats, 0.405, 6, 0.085, 1.4, 0.0045, heading=-55, phase=0.2)
    objs += tube("C_Core", [V(0, 0, 0.40), V(0, 0, C_SPLIT + 0.02)], mats["light"], 0.0045)
    for k in range(3):
        strand = braid(k, 0.40, C_SPLIT + 0.02)
        objs += tube(f"C_Strand_{k}", strand, mats["ivory"], 0.0068, (1.0, 0.85))
        gold = braid(k + 0.5, 0.42, C_SPLIT, extra=0.0055)
        objs += tube(f"C_Thread_{k}", gold, mats["light"], 0.0015)
    for i, ze in enumerate(C_EYES):      # the eyelets of the trunk
        objs += m.droplet(f"C_Eye_Light_{i}", (0, 0, ze - 0.014), 0.012, (0, 0, 1), mats["phial_lit"], stretch=1.3)
        objs += m.halo(f"C_Eye_Halo_{i}", (0, 0, ze), 0.06, 0.0028, (0, 0, 1), mats["light"], tilt_deg=12,
                       tilt_axis=(1, 0, 0))
    for i, (z, phi) in enumerate(((0.52, -0.4), (0.60, 2.0), (0.90, 4.4), (0.98, 0.5), (1.27, 2.9))):
        objs += pod(f"C_Pod_{i}", z, phi, mats)
    for k in range(3):                   # the crown
        radial, circ = ring_frame(2 * math.pi * k / 3 + 0.35)
        plane = m.plane_mapper(V(0, 0, C_SPLIT) + radial * 0.012, radial, V(0, 0, 1))
        heading = 18 if fire else 62
        length, turns, curl, bend = 0.37, -1.3, 0.55, -0.25
        objs += m.tendril(f"C_Branch_{k}", plane, (0, 0), heading, length, turns, 0.0088, mats, strands=3,
                          gold=True, offshoots=[(0.33, 1, 0.34, 1.2), (0.52, -1, 0.3, -1.1)], curl_start=curl,
                          bend=bend)
        pts, ths = m.volute(length, turns, curl, bend)
        h = math.radians(heading)
        center = [plane(x * math.cos(h) - y * math.sin(h), x * math.sin(h) + y * math.cos(h)) for x, y in pts]
        for j, u in enumerate((0.16, 0.27, 0.40, 0.62)):     # paired light leaves
            i = int(u * (len(center) - 1))
            tan = (center[i + 1] - center[i - 1]).normalized()
            for s in (-1, 1):
                objs += m.droplet(f"C_Leaf_{k}_{j}_{s}", center[i], 0.0062, (tan * 0.55 + circ * s * 0.85),
                                  mats["light"], stretch=2.0)
    objs += sphere("C_Fruit", (0, 0, C_SPLIT + 0.17), 0.04 if fire else 0.026, mats["phial_lit"])
    objs += m.halo("C_Crown_Halo", (0, 0, C_SPLIT + 0.2), 0.12, 0.0038, (0, 0, 1), mats["light"], tilt_deg=8,
                   tilt_axis=(1, 0, 0))
    objs += m.halo("C_Crown_Halo_Small", (0, 0, C_SPLIT + 0.245), 0.052, 0.0024, (0, 0, 1), mats["light"])
    objs += leaf_point("C_Point", C_SPLIT + 0.19, TIP, 0.046, mats)
    if fire:
        objs += charge_glow(mats, C_SPLIT + 0.19, orb=0.001, halos=((0.11, 0.12), (0.21, 0.15), (0.31, 0.18)))
    return objs


# ------------------------------------------------------------------ D wings

def wing(s, mats, fire):
    """One wing: an ivory arm wound with gold, rows of small ivory coverts on it, inner
    secondaries of ivory and long primaries of light (a light drop at the tip of each of
    the five longest: the shells). It sits at the head of the spear, folded back along the
    barrel like the wings on a herald's staff."""
    side = "L" if s < 0 else "R"
    if fire:
        ctrl = [V(s * 0.025, 0, D_ROOT), V(s * 0.10, 0, D_ROOT + 0.02), V(s * 0.19, 0, D_ROOT + 0.06),
                V(s * 0.25, 0, D_ROOT + 0.11)]
    else:
        ctrl = [V(s * 0.025, 0, D_ROOT), V(s * 0.06, 0, D_ROOT - 0.04), V(s * 0.074, 0, D_ROOT - 0.14),
                V(s * 0.068, 0, D_ROOT - 0.26)]
    arm = smooth_path(ctrl, 60)
    objs = [c.curve_tube(f"D_Arm_{side}", arm, [1 - 0.55 * i / 59 for i in range(60)], mats["ivory"], bevel=0.0085,
                         resolution=3)]
    objs += m.wound_cord(f"D_Arm_Vine_{side}", arm, 0.0095, 4.0, 0.0016, mats, strand_mat="light", taper=0.5)

    def fdir(u):                         # angle from straight back (-z) toward the wing's side
        a = math.radians(55 + 60 * u) if fire else math.radians(4 + 9 * u)
        return V(s * math.sin(a), 0, -math.cos(a)), a

    feathers = [(0.5 + 0.1 * i, 0.30 + 0.06 * i, True, i) for i in range(6)]
    feathers += [(0.08 + 0.09 * i, 0.20 + 0.035 * i, False, i) for i in range(5)]
    for u, length, primary, i in feathers:
        p0 = arm[min(int(u * 59), 59)]
        d, a = fdir(u)
        perp = V(s * math.cos(a), 0, math.sin(a))
        p0 = p0 + V(0, (-0.004 * (i + 1)) if primary else 0.004 * (i + 1), 0)
        path = [p0, p0 + d * (0.5 * length) + perp * 0.015, p0 + d * length + perp * 0.008]
        width = (0.034 + 0.002 * i) if primary else 0.03

        def w(t, width=width):
            return width * math.sin(math.pi * min(t / 0.985, 1) ** 0.5) ** 0.75

        name = f"D_{'Primary' if primary else 'Secondary'}_{side}_{i}"
        objs += m.path_blade(name, path, (0, 1, 0), w, lambda t: 0.004 * (1 - 0.7 * t),
                             mats["blade"] if primary else mats["ivory"], offset_fn=lambda t, w=w: s * 0.22 * w(t))
        rach = [p + V(0, -0.0032, 0) for p in smooth_path(path, 30)]
        objs += tube(name + "_Rachis", rach[:27], mats["core"] if primary else mats["light"], 0.0014, (1.0, 0.3))
        if primary and i >= 1:
            objs += m.floating_phials(f"D_Shell_{side}_{i}", [path[-1] + d * 0.024], d, d, mats, size=0.0066)
    for j in range(13):                  # coverts
        u = 0.05 + 0.07 * j
        d, _ = fdir(u)
        p = arm[min(int(u * 59), 59)]
        for row, (dy, dl) in enumerate(((-0.006, 0.012), (0.005, 0.03))):
            objs += m.droplet(f"D_Covert_{side}_{j}_{row}", p + d * dl + V(0, dy, 0), 0.0085 - 0.002 * row, d,
                              mats["ivory"], stretch=1.9)
    return objs


D_ROOT = 1.45                            # where the wings leave the barrel


def design_d(mats, rng, fire):
    """Wings: a conduit of light sheathed in ivory at the root; at the head of the spear a
    heart of light where two wings leave it and fold back along the barrel. Wyvern's Fire
    spreads them."""
    objs = grip(mats, rng)
    objs += scroll_crown("D_Guard", mats, 0.395, 6, 0.07, 1.3, 0.004, heading=-28, phase=0.5)
    objs += tube("D_Conduit", [V(0, 0, 0.40), V(0, 0, 1.63)], mats["light"], 0.0055, (1.0, 0.6))
    objs += m.woven_tube("D_Sheath", [V(0, 0, 0.36), V(0, 0, 0.60)], 0.02, mats["ivory"], rng,
                         radius_fn=lambda u: 1 - 0.25 * u)
    objs += m.halo("D_Sheath_Band", (0, 0, 0.605), 0.019, 0.0055, (0, 0, 1), mats["ivory"])
    objs += m.halo("D_Heart_Ring", (0, 0, D_ROOT), 0.03, 0.0062, (0, 0, 1), mats["ivory"])
    objs += m.halo("D_Heart_Gold", (0, 0, D_ROOT + 0.016), 0.026, 0.002, (0, 0, 1), mats["light"])
    objs += m.droplet("D_Heart", (0, 0, D_ROOT - 0.014), 0.016, (0, 0, 1), mats["phial_lit"], stretch=1.5)
    for k, (z, r) in enumerate(((0.72, 0.042), (0.98, 0.038), (1.55, 0.034))):
        objs += m.halo(f"D_Halo_{k}", (0, 0, z), r, 0.003, (0, 0, 1), mats["light"], tilt_deg=10 * (-1) ** k,
                       tilt_axis=(1, 0, 0))
    for s in (-1, 1):
        objs += wing(s, mats, fire)
    objs += scroll_crown("D_Muzzle", mats, 1.595, 3, 0.05, -1.2, 0.003, heading=50, phase=0.3)
    objs += m.halo("D_Muzzle_Halo", (0, 0, 1.645), 0.046, 0.0034, (0, 0, 1), mats["light"])
    objs += leaf_point("D_Point", 1.625, TIP, 0.048, mats)
    if fire:
        objs += charge_glow(mats, 1.665, orb=0.03)
    return objs


# ------------------------------------------------------------------ render

DESIGNS = {
    "A": ("A 金針聖匣", design_a, 3.3),
    "B": ("B 聖百合", design_b, 3.3),
    "C": ("C 聖樹", design_c, 3.3),
    "D": ("D 聖翼", design_d, 4.4),
}
ROWS = [(False, "full", "{}"), (False, "detail", "{}・槍身近看"), (True, "full", "{}・龍擊砲蓄能")]


def render_one(key, fire, frame):
    c.reset_scene()
    mats = m.materials()
    mats["gold"] = devices.gold_material()
    c.set_emission_strength(mats["gold"], 0.6)
    mats["phial_lit"] = c.make_material("Phial_Lit", c.PALETTE["glow"], roughness=0.1,
                                        emission=c.PALETTE["glow"], strength=3.0)
    m.glow_mode(mats)
    if fire:
        st.set_glow(mats["light"], "#FF9A10", 8.0)
        st.set_blade(mats["blade"], "#FFA828", "#FF8000", 8.0)
        st.set_glow(mats["core"], "#FFB030", 9.0)
        c.set_emission_strength(mats["phial_lit"], 9.0)
    _, build, fire_dist = DESIGNS[key]
    build(mats, random.Random(7), fire)
    if frame == "full":
        target, dist, el = (0, 0, 1.0), (fire_dist if fire else 3.3), 8
    else:
        target, dist, el = (0, 0, 1.33), 1.9, 10
    st.stage_lights(target, dist, res=(300, 500) if TEST else (600, 1000))
    if TEST:
        bpy.context.scene.cycles.samples = 8
    stem = f"gl_{key}_{'fire' if fire else 'rest'}_{frame}"
    return c.render_views(OUT, stem, target, dist, [("tq", 30, el)], lens=50)[0]


def main():
    grid = {}
    for key in PICK:
        for fire, frame, _ in ROWS:
            grid[(key, fire, frame)] = render_one(key, fire, frame)
            print("rendered", key, "fire" if fire else "rest", frame, flush=True)
    paths, labels = [], []
    for fire, frame, fmt in ROWS:
        for key in PICK:
            paths.append(grid[(key, fire, frame)])
            labels.append(fmt.format(DESIGNS[key][0]))
    out = os.path.join(OUT, "gunlance_redesign_test.png" if TEST else "gunlance_redesign.png")
    st.labelled_strip(paths, labels, out, "銃槍重新設計：四個方向（上：平時　中：槍身近看　下：龍擊砲蓄能）",
                      cols=len(PICK))
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
