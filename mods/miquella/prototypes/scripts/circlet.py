"""Glowing circlet ("halo") prototype.

Half ring from temple to temple, V point with a droplet pendant at the forehead,
raised filigree on the band, and twig tendrils sweeping back and up at both ends.
See DESIGN.md section 4.

Usage: python circlet.py <out_dir>
"""
import math
import random
import sys

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0, __import__("os").path.dirname(__file__))
import common as c

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"

# Head proxy dimensions (meters): half-width, half-depth, half-height.
HEAD = Vector((0.074, 0.094, 0.112))
BAND_Z = 0.032          # band center height above head center (forehead)
OFFSET = 0.004          # gap between head surface and band
ARC = 100               # band spans -ARC..+ARC degrees (0 = front)


def head_point(theta_deg, z, offset=OFFSET):
    """Point on an ellipse around the head at angle theta (0 = front, + = right)."""
    t = math.radians(theta_deg)
    # Shrink the ellipse with height so the band hugs the skull.
    k = math.sqrt(max(0.0, 1 - (z / HEAD.z) ** 2))
    return Vector(((HEAD.x * k + offset) * math.sin(t),
                   -(HEAD.y * k + offset) * math.cos(t),
                   z))


def band_edges(theta):
    """Top and bottom z of the band at angle theta."""
    a = abs(theta)
    v = max(0.0, 1 - a / 26) ** 1.6            # V dip near the center
    taper = max(0.0, (a - 70) / (ARC - 70))    # narrow toward the ends
    # Where the band unravels into strands it thins out so no flat end shows.
    fade = min(1.0, max(0.0, (a - (ARC - 16)) / 16))
    fade = fade * fade * (3 - 2 * fade)
    top = BAND_Z + 0.0065 - 0.004 * v - 0.002 * taper - 0.0045 * fade
    bottom = BAND_Z - 0.0055 - 0.019 * v + 0.004 * taper + 0.0045 * fade
    return top, bottom


def build_band(material):
    """Curved ribbon with thickness, following the forehead."""
    mesh = bpy.data.meshes.new("band")
    bm = bmesh.new()
    steps = 120
    rows = []
    for i in range(steps + 1):
        theta = -ARC + 2 * ARC * i / steps
        top, bottom = band_edges(theta)
        col = []
        for j in range(5):
            z = bottom + (top - bottom) * j / 4
            # Slight convex bulge across the band height.
            bulge = 0.0012 * math.sin(math.pi * j / 4)
            col.append(bm.verts.new(head_point(theta, z, OFFSET + bulge)))
        rows.append(col)
    for i in range(steps):
        for j in range(4):
            bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]))
    bm.to_mesh(mesh)
    bm.free()
    obj = c.link(bpy.data.objects.new("Circlet_Band", mesh))
    obj.data.materials.append(material)
    solid = obj.modifiers.new("thickness", "SOLIDIFY")
    solid.thickness = 0.0022
    solid.offset = 1.0
    sub = obj.modifiers.new("smooth", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 2
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    return obj


def filigree(material, side):
    """Raised vine lines wandering along the band surface."""
    objs = []
    for lane, phase in ((0.35, 0.0), (0.65, 1.7)):
        pts, radii = [], []
        for i in range(90):
            theta = side * (6 + (ARC - 16) * i / 89)
            top, bottom = band_edges(theta)
            wave = 0.18 * math.sin(math.radians(theta) * 9 + phase)
            z = bottom + (top - bottom) * min(0.9, max(0.1, lane + wave))
            pts.append(head_point(theta, z, OFFSET + 0.0028))
            radii.append(0.55 + 0.25 * math.sin(i * 0.4))
        objs.append(c.curve_tube(f"Filigree_{side}_{lane}", pts, radii, material, bevel=0.0009, resolution=2))
    # Scrolls flanking the center emblem (larger, the focal ornament).
    for k, (theta0, size, turns) in enumerate(((7, 0.0055, 0.8), (15, 0.0045, 0.7))):
        th = side * theta0
        top, bottom = band_edges(th)
        zc = bottom + (top - bottom) * 0.45
        pts, radii = [], []
        for i in range(40):
            u = i / 39
            a = u * turns * 2 * math.pi
            r = size * (1 - 0.75 * u)
            dtheta = math.degrees((r * math.cos(a)) / HEAD.x) * side
            pts.append(head_point(th + dtheta, zc + r * math.sin(a), OFFSET + 0.0028))
            radii.append(1.2 - 0.8 * u)
        objs.append(c.curve_tube(f"Scroll_{side}_{k}", pts, radii, material, bevel=0.0009, resolution=2))
    # Small curls along the band.
    for k in range(4):
        theta0 = side * (30 + k * 16)
        top, bottom = band_edges(theta0)
        zc = (top + bottom) / 2
        pts, radii = [], []
        for i in range(24):
            a = i / 23 * 2.2 * math.pi
            r = 0.0032 * (1 - i / 30)
            theta = theta0 + side * math.degrees(r * math.cos(a) / HEAD.x)
            pts.append(head_point(theta, zc + r * math.sin(a), OFFSET + 0.0026))
            radii.append(1.0 - i / 30)
        objs.append(c.curve_tube(f"Curl_{side}_{k}", pts, radii, material, bevel=0.0008, resolution=2))
    return objs


def pendant(material, glow_material):
    """Center emblem on the V point plus a hanging droplet."""
    top, bottom = band_edges(0)
    tip = head_point(0, bottom, OFFSET + 0.001)
    objs = []
    # Emblem: small raised teardrop on the band just above the tip.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0042, location=head_point(0, bottom + 0.008, OFFSET + 0.0025))
    emblem = bpy.context.active_object
    emblem.name = "Circlet_Emblem"
    emblem.scale = (0.8, 0.45, 1.25)
    emblem.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    objs.append(emblem)
    # Tiny connector ring.
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0016, minor_radius=0.0005,
                                     location=tip + Vector((0, -0.0005, -0.0012)),
                                     rotation=(0, math.pi / 2, 0))
    ring = bpy.context.active_object
    ring.name = "Circlet_Ring"
    ring.data.materials.append(material)
    objs.append(ring)
    # Droplet: sphere pulled into a teardrop pointing up.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0028, segments=32, ring_count=16,
                                         location=tip + Vector((0, -0.0008, -0.0062)))
    drop = bpy.context.active_object
    drop.name = "Circlet_Droplet"
    for v in drop.data.vertices:
        if v.co.z > 0:
            f = v.co.z / 0.0028
            v.co.x *= 1 - 0.75 * f
            v.co.y *= 1 - 0.75 * f
            v.co.z *= 1 + 0.9 * f
    drop.data.materials.append(glow_material)
    bpy.ops.object.shade_smooth()
    objs.append(drop)
    return objs


def main_path(side, s):
    """Main tendril: continues the band backward around the head, lifting off and rising."""
    theta = side * (ARC - 14 + 44 * s)
    top, bottom = band_edges(side * min(abs(theta), ARC))
    z = (top + bottom) / 2 + 0.046 * s ** 1.4
    lift = OFFSET + 0.0015 + 0.016 * s ** 2.0
    return head_point(theta, z, lift)


def frame_at(side, s, eps=0.004):
    """Tangent and two normals of the main path at s."""
    p0, p1 = main_path(side, max(0, s - eps)), main_path(side, min(1, s + eps))
    t = (p1 - p0).normalized()
    n1 = t.cross(Vector((0, 0, 1))).normalized()
    n2 = t.cross(n1).normalized()
    return t, n1, n2


def spiral_curl(start, direction, up, size, turns, steps=40):
    """Fiddlehead-like curl: moves along `direction` while turning toward `up`."""
    pts = []
    d = direction.normalized()
    axis = d.cross(up).normalized()
    p = start.copy()
    for i in range(steps):
        t = i / (steps - 1)
        angle = turns * 2 * math.pi * t ** 1.4
        # Rotate the heading around `axis`, shrinking the step for a tightening spiral.
        heading = d * math.cos(angle) + up.normalized() * math.sin(angle)
        p = p + heading * (size * (1 - 0.8 * t) / steps * 6)
        pts.append(p.copy())
    return pts


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


U_SPLIT = 0.34   # where the main bundle splits into three branches (earlier = longer branches)


def rotate(vec, axis, angle):
    """Rodrigues rotation of vec around a unit axis."""
    axis = axis.normalized()
    return (vec * math.cos(angle) + axis.cross(vec) * math.sin(angle)
            + axis * axis.dot(vec) * (1 - math.cos(angle)))


def branch_paths(side):
    """Three medium branches fanning out (trident-like) from the split point.

    Right after the split the three branches still wind around each other, then fan
    out and keep sweeping back with irregular, non-planar waves."""
    origin = main_path(side, U_SPLIT)
    t, n1, n2 = frame_at(side, U_SPLIT)
    paths = []
    specs = (  # fan deg, length, wave amps, wave freqs, phase, start angle around axis
        (30, 0.078, (0.006, 0.003), (1.1, 2.3), 0.0, 0.0),
        (4, 0.092, (0.007, 0.004), (0.9, 2.0), 1.9, 2.1),
        (-20, 0.070, (0.005, 0.004), (1.3, 2.7), 3.6, 4.2),
    )
    for fan, length, amps, freqs, phase, a0 in specs:
        target_dir = rotate(t, n1, math.radians(fan) * -side)
        n = 90
        p = origin.copy()
        pts = [origin.copy()]
        for i in range(1, n):
            v = i / (n - 1)
            blend = smoothstep(v / 0.3)
            d = (t * (1 - blend) + target_dir * blend).normalized()
            p = p + d * (length / (n - 1))
            # Winding around each other just after the split, unwinding as they fan out.
            wind_r = 0.002 * (1 - smoothstep(v / 0.3))
            wind_a = a0 + side * 9 * v
            wind = (n1 * math.cos(wind_a) + n2 * math.sin(wind_a)) * wind_r
            side_axis = n1.cross(d).normalized()
            wave = (side_axis * amps[0] * math.sin(2 * math.pi * freqs[0] * v + phase)
                    + n1 * amps[1] * math.sin(2 * math.pi * freqs[1] * v + phase * 1.7)) * smoothstep(v / 0.25)
            lift = n1 * 0.007 * v ** 1.5     # drift away from the head
            pts.append(p + wind + wave + lift)
        paths.append(pts)
    return paths


def sample(path, v):
    """Point and tangent on a polyline at parameter v in [0, 1]."""
    x = v * (len(path) - 1)
    i = min(int(x), len(path) - 2)
    f = x - i
    p = path[i] * (1 - f) + path[i + 1] * f
    return p, (path[i + 1] - path[i]).normalized()


def twigs(material, side, seed=7):
    """The band end unravels into thin strands that twist into a dense bundle, which then
    splits evenly into three medium branches (trident-like), each still made of strands."""
    rng = random.Random(seed)
    out = []
    branches = branch_paths(side)
    n_strands = 18
    top0, bottom0 = band_edges(side * (ARC - 14))
    band_h = top0 - bottom0
    for k in range(n_strands):
        st = {
            "v": -0.5 + k / (n_strands - 1),
            "phi": rng.uniform(0, 2 * math.pi),
            "rr": rng.uniform(0.3, 1.0),
            "omega": rng.uniform(3.0, 6.0) * (1 if rng.random() < 0.75 else -1),
            "wave_f": rng.uniform(1.5, 3.0),
            "wave_p": rng.uniform(0, 2 * math.pi),
            "branch": k % 3,
            "omega_b": rng.uniform(5, 9) * (1 if rng.random() < 0.85 else -1),
            "end": rng.uniform(0.82, 1.0),
            "size": rng.uniform(0.8, 1.15),
        }
        pts, radii = [], []
        # Part 1: band -> bundle, along the main path up to the split.
        n_main = 45
        for i in range(n_main):
            u = U_SPLIT * i / n_main
            t, n1, n2 = frame_at(side, u)
            band_off = n2 * (-st["v"] * band_h * 0.95)
            r = 0.0066 * (1 + 0.3 * math.sin(2 * math.pi * st["wave_f"] * u + st["wave_p"]))
            ang = st["phi"] + side * st["omega"] * u
            bundle_off = (n1 * math.cos(ang) + n2 * math.sin(ang)) * r * st["rr"]
            w = smoothstep(u / 0.2)
            pts.append(main_path(side, u) + band_off * (1 - w) + bundle_off * w)
            radii.append(st["size"])
        # Part 2: along the assigned branch, twisting around the branch center.
        path = branches[st["branch"]]
        n_br = 110
        for i in range(n_br):
            v = st["end"] * i / (n_br - 1)
            c_pt, tb = sample(path, v)
            nb1 = tb.cross(Vector((0, 0, 1))).normalized()
            nb2 = tb.cross(nb1).normalized()
            u = U_SPLIT + v * 0.66
            ang = st["phi"] + side * st["omega"] * U_SPLIT + side * st["omega_b"] * v
            # Radius shrinks from the bundle size to the branch size right after the split.
            r = 0.0066 * (1 - smoothstep(v / 0.2)) + 0.0034 * smoothstep(v / 0.2)
            r *= (1 + 0.25 * math.sin(2 * math.pi * st["wave_f"] * 1.6 * v + st["wave_p"])) * (1 - 0.35 * v)
            pts.append(c_pt + (nb1 * math.cos(ang) + nb2 * math.sin(ang)) * r * st["rr"])
            tip = smoothstep((v - (st["end"] - 0.14)) / 0.14)
            radii.append(st["size"] * (1 - 0.35 * v ** 2) * (1 - 0.9 * tip))
        # A few strands curl off at the branch tips.
        if k in (0, 7):
            # Curl from before the tip taper so the curl keeps some thickness.
            cut = len(pts) - 9
            pts, radii = pts[:cut], radii[:cut]
            d = (pts[-1] - pts[-2]).normalized()
            curl = spiral_curl(pts[-1], d, Vector((0, 0, 1)) + d * 0.3,
                               rng.uniform(0.005, 0.007), rng.uniform(0.55, 0.8), steps=22)
            pts += curl[1:]
            radii += [radii[-1] * (1 - 0.8 * (j / len(curl)) ** 1.5) for j in range(1, len(curl))]
        out.append((pts, radii, 0.0013))

    # Small buds (nubs) along the bundle and branches.
    bud_spots = [("main", 0.2), ("main", 0.3), (0, 0.35), (1, 0.5), (2, 0.3), (1, 0.75), (0, 0.7)]
    for where, pos in bud_spots:
        if where == "main":
            base_c = main_path(side, pos)
            t, n1, n2 = frame_at(side, pos)
            rad = 0.006
        else:
            base_c, t = sample(branches[where], pos)
            n1 = t.cross(Vector((0, 0, 1))).normalized()
            n2 = t.cross(n1).normalized()
            rad = 0.003
        ang = rng.uniform(0, 2 * math.pi)
        normal = n1 * math.cos(ang) + n2 * math.sin(ang)
        base = base_c + normal * rad * 0.7
        d = (t * 0.8 + normal * 0.7).normalized()
        pts = [base + d * (0.0042 * j / 10) for j in range(11)]
        radii = [0.55 + 0.45 * math.sin(math.pi * min(1.0, j / 10 * 1.25)) if j < 10 else 0.25 for j in range(11)]
        radii[-2] = 0.6
        out.append((pts, radii, 0.0017))

    objs = []
    for i, (pts, radii, bevel) in enumerate(out):
        objs.append(c.curve_tube(f"Twig_{side}_{i}", pts, radii, material, bevel=bevel, resolution=3))
    return objs


def build(glow_strength):
    c.reset_scene()
    ivory = c.make_material("Circlet_Ivory", c.PALETTE["ivory"], roughness=0.32, coat=0.3,
                            emission=c.PALETTE["glow"], strength=glow_strength, subsurface=0.15)
    drop_mat = c.make_material("Circlet_Droplet", c.PALETTE["glow"], roughness=0.08, coat=0.6,
                               emission=c.PALETTE["glow"], strength=glow_strength * 1.3)
    parts = [build_band(ivory)]
    for side in (-1, 1):
        parts += filigree(ivory, side)
        parts += twigs(ivory, side, seed=11)   # same seed -> mirrored twigs
    parts += pendant(ivory, drop_mat)
    return parts, ivory, drop_mat


def add_head_proxy():
    mat = c.make_material("Head_Proxy", c.PALETTE["proxy"], roughness=0.7)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32, location=(0, 0, 0))
    head = bpy.context.active_object
    head.name = "Head_Proxy"
    head.scale = HEAD
    head.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return head


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    target = (0, 0.01, BAND_Z + 0.015)
    views = [("front", 0, 8), ("three_quarter", 35, 15), ("side", 90, 10),
             ("back_three_quarter", 145, 25), ("top", 0, 70), ("low_front", -20, -10)]

    # Pass 1: studio look on a head proxy, gentle glow.
    parts, ivory, drop = build(glow_strength=0.08)
    add_head_proxy()
    c.setup_render(samples=32, res=(640, 640), world_hex="#3A3A3E", world_strength=0.5)
    c.add_light("key", "AREA", (0.35, -0.45, 0.35), 22, size=0.4, target=(0, 0, 0.03))
    c.add_light("fill", "AREA", (-0.45, -0.3, 0.1), 6, size=0.5, target=(0, 0, 0.03))
    c.add_light("rim", "AREA", (0.0, 0.5, 0.4), 14, size=0.4, target=(0, 0, 0.03))
    studio = c.render_views(OUT, "studio", target, 0.6, views)
    c.contact_sheet(studio, os.path.join(OUT, "circlet_studio_sheet.png"), cols=3)
    split = main_path(1, U_SPLIT)
    close = c.render_views(OUT, "closeup", tuple(split + Vector((0, 0.01, 0.012))), 0.2,
                           [("tendril_side", 100, 10), ("tendril_back", 150, 20)])
    c.contact_sheet(close, os.path.join(OUT, "circlet_closeup_sheet.png"), cols=2)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(OUT, "circlet.blend")))

    # Pass 2: in-game glow look, dark background, bloom.
    c.set_emission_strength(ivory, 4.0)
    c.set_emission_strength(drop, 6.0)
    c.setup_render(samples=32, res=(640, 640), world_hex="#101014", world_strength=0.3, glare=True)
    glow = c.render_views(OUT, "glow", target, 0.6, [views[0], views[1], views[3]])
    c.contact_sheet(glow, os.path.join(OUT, "circlet_glow_sheet.png"), cols=3)
    print("DONE", studio + glow)


main()
