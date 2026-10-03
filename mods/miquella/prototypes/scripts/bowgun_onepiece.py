"""One-piece stock and grip for the bowguns (user, 2026-10-03: the grip options all read as "a
stock and a grip, two different things"; "I'd rather have it one piece").

Behind the receiver the stock and the grip are one woven ring round a thumbhole: its band runs
from the receiver back along the top to the butt, down the butt, forward along the bottom and up
the front of the grip into the receiver again, and the weave runs round with it, so there is no
joint where a grip meets a stock. The ring is lofted between two matched closed contours in the
side (YZ) plane, the outline and the hole, with an elliptical section (across: half the band,
side to side: the stock's thickness).

Prototype axes as bowgun.py: +Y muzzle, +Z up; contours drawn for the heavy bowgun and mapped onto
the light bowgun's shorter, slimmer stock.
"""
import math

import bmesh
import bpy
from mathutils import Vector

import common as c

PI = math.pi
X = Vector((1, 0, 0))
# Outline and hole (y, z), matched point for point, starting inside the receiver and running back
# along the top, down the butt, forward along the bottom and up the front of the grip.
OUTER = [(-0.095, 0.045), (-0.17, 0.05), (-0.27, 0.055), (-0.37, 0.06), (-0.44, 0.058), (-0.478, 0.03),
         (-0.49, -0.04), (-0.48, -0.115), (-0.455, -0.16), (-0.38, -0.165), (-0.29, -0.175), (-0.21, -0.2),
         (-0.165, -0.222), (-0.125, -0.195), (-0.098, -0.12), (-0.08, -0.04)]
HOLE = [(-0.155, -0.012), (-0.2, -0.008), (-0.27, -0.008), (-0.33, -0.014), (-0.37, -0.03), (-0.385, -0.055),
        (-0.375, -0.08), (-0.345, -0.097), (-0.3, -0.108), (-0.255, -0.12), (-0.215, -0.14), (-0.19, -0.16),
        (-0.172, -0.148), (-0.156, -0.11), (-0.149, -0.07), (-0.149, -0.035)]
HBG_WRIST, HBG_STOCK = -0.14, 0.34                 # the heavy bowgun's wrist and stock length
THICK = {"hbg": 0.034, "lbg": 0.021}               # half the stock's thickness, side to side


def closed_resample(pts, n):
    pts = [Vector(p) for p in pts]
    segs = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    lens = [(b - a).length for a, b in segs]
    total = sum(lens)
    out, acc, k = [], 0.0, 0
    for i in range(n):
        target = total * i / n
        while acc + lens[k] < target:
            acc += lens[k]
            k += 1
        a, b = segs[k]
        out.append(a + (b - a) * ((target - acc) / lens[k]))
    return out


def smooth_closed(pts, n, passes=3):
    """Catmull-Rom through a closed polygon, then resampled evenly."""
    m = len(pts)
    dense = []
    for i in range(m):
        p0, p1, p2, p3 = (Vector(pts[(i + j) % m]) for j in (-1, 0, 1, 2))
        for s in range(12):
            t = s / 12
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    return closed_resample(dense, n)


def contours(gun, hole_scale=1.0, wrist=None, stock_len=None):
    """The outline and the hole for a gun, the hole optionally shrunk round its middle; the light
    bowgun's are fitted to its wrist and stock length."""
    hole = [Vector(p) for p in HOLE]
    if hole_scale != 1.0:
        mid = sum(hole, Vector((0, 0))) / len(hole)
        hole = [mid + (p - mid) * hole_scale for p in hole]
    outer = [Vector(p) for p in OUTER]
    if gun == "lbg":
        k = stock_len / HBG_STOCK
        fit = lambda p: Vector((wrist + (p.x - HBG_WRIST) * k, p.y * 0.66))
        outer, hole = [fit(p) for p in outer], [fit(p) for p in hole]
    return outer, hole


def ring_frames(gun, n=180, hole_scale=1.0, wrist=None, stock_len=None):
    """For n points round the ring: (centre, direction across the band toward the outline, half
    the band, half the thickness)."""
    outer, hole = contours(gun, hole_scale, wrist, stock_len)
    o, i = smooth_closed(outer, n), smooth_closed(hole, n)
    frames = []
    for po, pi in zip(o, i):
        mid = (po + pi) / 2
        d = po - pi
        frames.append((Vector((0, mid.x, mid.y)), Vector((0, d.x, d.y)).normalized(), d.length / 2, THICK[gun]))
    return frames


EXP = 3.2          # the band's section is a superellipse: flat faces like the old stock's, not a tube


def ring_point(f, theta, scale_a=1.0, scale_b=1.0):
    ctr, u, a, b = f
    cs, sn = math.cos(theta), math.sin(theta)
    cs = math.copysign(abs(cs) ** (2 / EXP), cs)
    sn = math.copysign(abs(sn) ** (2 / EXP), sn)
    return ctr + u * (a * scale_a * cs) + X * (b * scale_b * sn)


def ring_core(name, frames, mat, scale_a=0.97, scale_b=0.97, sides=24):
    bm = bmesh.new()
    rings = [[bm.verts.new(ring_point(f, 2 * PI * j / sides, scale_a, scale_b)) for j in range(sides)] for f in frames]
    n = len(rings)
    for i in range(n):
        for j in range(sides):
            a, b = rings[i][j], rings[i][(j + 1) % sides]
            bm.faces.new((a, b, rings[(i + 1) % n][(j + 1) % sides], rings[(i + 1) % n][j]))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = c.link(bpy.data.objects.new(name, mesh))
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    sub = obj.modifiers.new("smooth", "SUBSURF")
    sub.levels = sub.render_levels = 1
    return obj


def loop_length(frames):
    return sum((frames[(i + 1) % len(frames)][0] - frames[i][0]).length for i in range(len(frames)))


def ring_strands(name, frames, mat, count, per_m, bevel, scale=1.03, cross=True, rng=None, phase=0.0, radius=1.0,
                 lift=0.0):
    """Strands round the ring's section, turning per_m radians per metre along it (alternate
    strands the other way when cross: a weave), closed (whole turns round the loop)."""
    L = loop_length(frames)
    turns = round(per_m * L / (2 * PI))       # 0: the strands run straight round, like the stock's grain
    rate = 2 * PI * turns / L
    s_acc = [0.0]
    for i in range(1, len(frames)):
        s_acc.append(s_acc[-1] + (frames[i][0] - frames[i - 1][0]).length)
    objs = []
    for k in range(count):
        th0 = phase + 2 * PI * k / count + (rng.uniform(-0.1, 0.1) if rng else 0.0)
        sign = (1 if k % 2 == 0 else -1) if cross else 1
        pts = [ring_point(f, th0 + sign * rate * s, scale, scale) for f, s in zip(frames, s_acc)]
        if lift:                         # stand out of the weave by `lift` (gold wound over it)
            pts = [p + (p - f[0]).normalized() * lift for p, f in zip(pts, frames)]
        pts.append(pts[0])
        objs.append(c.curve_tube(f"{name}_{k}", pts, [radius] * len(pts), mat, bevel=bevel, resolution=2))
    return objs


def hole_inlay(name, frames, mat, spread=1.05, bevel=0.0022, lift=0.0095):
    """Gold lines round the thumbhole on both faces, standing just out of the weave."""
    objs = []
    for s in (-1, 1):
        pts = []
        for f in frames:
            p = ring_point(f, PI + s * spread)
            out = 1.0 if (p - f[0]).dot(X) > 0 else -1.0
            pts.append(p + X * (out * lift))
        pts.append(pts[0])
        objs.append(c.curve_tube(f"{name}_{s}", pts, [1.0] * len(pts), mat, bevel=bevel, resolution=2))
    return objs
