"""Shared building blocks for the Miquella light weapons.

Every weapon in the set is built from the same few motifs, so they read as one family:
- light: blades and edges made of gold light (no metal)
- ivory strands: woven grips and shafts; bundles that twist and split into three (the
  circlet's trident)
- floating halo rings: single rings, stacked pairs, and rails of rings along an axis
- droplets: glowing teardrops (pommels, cores, phials)
- energy membranes: faint sheets of light inside a halo (shields, striking faces)

All functions take positions in world space and return lists of new objects.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Vector

import common as c
import blades


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def V(*a):
    return Vector(a)


# ------------------------------------------------------------------ materials

def materials():
    return {
        "ivory": c.make_material("Ivory", c.PALETTE["ivory"], roughness=0.32, coat=0.3,
                                 emission=c.PALETTE["glow"], strength=0.05, subsurface=0.15),
        "light": c.make_material("Light", c.PALETTE["glow"], roughness=0.1, coat=0.5,
                                 emission=c.PALETTE["glow"], strength=1.0),
        "blade": blades.blade_material("Blade_Light", 0.35),
        "core": c.make_material("Blade_Core", c.PALETTE["blade_core"], roughness=0.1,
                                emission=c.PALETTE["blade_core"], strength=0.8),
        "membrane": membrane_material("Membrane", 0.3, 0.6),
    }


def glow_mode(mats):
    """Strengths for the dark 'glow' renders."""
    c.set_emission_strength(mats["light"], 2.5)
    c.set_emission_strength(mats["blade"], 2.2)
    c.set_emission_strength(mats["core"], 3.0)
    for m in mats.values():
        if "Membrane_Emission" in m.node_tree.nodes:
            m.node_tree.nodes["Membrane_Emission"].inputs["Strength"].default_value *= 2.0


def membrane_material(name, radius, strength, rim=0.32, center=0.03):
    """Mostly transparent sheet of gold light, brighter toward its rim (object space,
    so the object's origin must be at the sheet's center)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    emission = nodes.new("ShaderNodeEmission")
    emission.name = "Membrane_Emission"
    emission.inputs["Color"].default_value = c.hex_to_linear(c.PALETTE["glow"])
    emission.inputs["Strength"].default_value = strength
    coords = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / radius, 1 / radius, 1 / radius)
    gradient = nodes.new("ShaderNodeTexGradient")
    gradient.gradient_type = "SPHERICAL"
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (rim, rim, rim, 1)
    ramp.color_ramp.elements[1].position = 0.38
    ramp.color_ramp.elements[1].color = (center, center, center, 1)
    links.new(coords.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], gradient.inputs["Vector"])
    links.new(gradient.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def veil_material(name, opacity, strength):
    """Evenly faint, see-through light (the hollow interior of an openwork blade)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = opacity
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    emission = nodes.new("ShaderNodeEmission")
    emission.name = "Membrane_Emission"
    emission.inputs["Color"].default_value = c.hex_to_linear(c.PALETTE["glow"])
    emission.inputs["Strength"].default_value = strength
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def flat_fill(name, outline, mat, center_origin=False):
    """Flat polygon filling a closed outline (points in order), e.g. a blade's veil. With
    center_origin the object's origin sits at the outline's centroid."""
    bm = bmesh.new()
    ctr = sum((Vector(p) for p in outline), Vector()) / len(outline) if center_origin else Vector()
    verts = [bm.verts.new(Vector(p) - ctr) for p in outline]
    bm.faces.new(verts)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = c.link(bpy.data.objects.new(name, mesh))
    obj.location = ctr
    obj.data.materials.append(mat)
    return [obj]


# ------------------------------------------------------------------ geometry helpers

def basis(axis):
    """Orthonormal (u, v, w) with w along axis."""
    w = Vector(axis).normalized()
    ref = V(0, 0, 1) if abs(w.z) < 0.9 else V(1, 0, 0)
    u = ref.cross(w).normalized()
    return u, w.cross(u), w


def resample(points, n):
    """n points evenly spaced by arc length along a polyline."""
    pts = [Vector(p) for p in points]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seg)
    out, i, acc = [], 0, 0.0
    for k in range(n):
        s = total * k / (n - 1)
        while i < len(seg) - 1 and acc + seg[i] < s:
            acc += seg[i]
            i += 1
        t = 0.0 if seg[i] == 0 else (s - acc) / seg[i]
        out.append(pts[i].lerp(pts[i + 1], min(1.0, max(0.0, t))))
    return out


def catmull(points, n):
    pts = [Vector(p) for p in points]
    pts = [pts[0]] + pts + [pts[-1]]
    out = []
    segs = len(pts) - 3
    for i in range(n):
        t = i / (n - 1) * segs
        k = min(int(t), segs - 1)
        u = t - k
        p0, p1, p2, p3 = pts[k], pts[k + 1], pts[k + 2], pts[k + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u))
    return out


def arc_length(points):
    return sum((points[i + 1] - points[i]).length for i in range(len(points) - 1))


def frames(points):
    """Tangents and a twist-free (parallel transported) normal frame along a path."""
    n = len(points)
    tans = []
    for i in range(n):
        t = points[min(i + 1, n - 1)] - points[max(i - 1, 0)]
        tans.append(t.normalized() if t.length > 1e-9 else V(0, 0, 1))
    u0, v0, _ = basis(tans[0])
    us, vs = [u0], [v0]
    for i in range(1, n):
        u = tans[i - 1].rotation_difference(tans[i]) @ us[-1]
        u = (u - tans[i] * u.dot(tans[i])).normalized()
        us.append(u)
        vs.append(tans[i].cross(u))
    return tans, us, vs


def smooth_obj(obj, mat):
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def mesh_obj(name, bm, mat, subsurf=0):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = c.link(bpy.data.objects.new(name, mesh))
    if subsurf:
        sub = obj.modifiers.new("smooth", "SUBSURF")
        sub.levels = sub.render_levels = subsurf
    return smooth_obj(obj, mat)


# ------------------------------------------------------------------ halos

def halo(name, center, radius, minor, axis, mat, tilt_deg=0.0, tilt_axis=None):
    """A floating ring of light whose plane is perpendicular to `axis`."""
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=minor,
                                     major_segments=max(48, int(radius * 600)), minor_segments=12,
                                     location=Vector(center))
    ring = bpy.context.active_object
    ring.name = name
    ring.rotation_mode = "QUATERNION"
    q = V(0, 0, 1).rotation_difference(Vector(axis).normalized())
    if tilt_deg:
        ta = Vector(tilt_axis) if tilt_axis is not None else basis(axis)[0]
        from mathutils import Quaternion
        q = Quaternion(ta.normalized(), math.radians(tilt_deg)) @ q
    ring.rotation_quaternion = q
    ring.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return [ring]


def halo_rail(name, p0, p1, n, r0, r1, mat, minor0=0.0045, minor1=None, tilt=4.0):
    """Rings along the line p0 -> p1, shrinking from r0 to r1, alternately tilted."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    minor1 = minor0 * 0.75 if minor1 is None else minor1
    objs = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.0
        objs += halo(f"{name}_{i}", p0.lerp(p1, t), r0 + (r1 - r0) * t,
                     minor0 + (minor1 - minor0) * t, axis, mat, tilt_deg=tilt if i % 2 == 0 else -tilt)
    return objs


def membrane_disc(name, center, radius, axis, mat, scale=(1.0, 1.0)):
    """Single-sided disc of membrane light (origin at its center, see membrane_material)."""
    bpy.ops.mesh.primitive_circle_add(radius=radius, vertices=128, fill_type="NGON", location=Vector(center))
    disc = bpy.context.active_object
    disc.name = name
    disc.rotation_mode = "QUATERNION"
    disc.rotation_quaternion = V(0, 0, 1).rotation_difference(Vector(axis).normalized())
    disc.scale = (scale[0], scale[1], 1.0)
    disc.data.materials.append(mat)
    return [disc]


# ------------------------------------------------------------------ strands

def woven_tube(name, path, radius, mat, rng, pitch=0.85, core=True, n=None, radius_fn=None):
    """Ivory strands crossing in a weave around a path (grips and shafts), with a solid
    core underneath so no gaps show. radius_fn(u) scales the radius along the path."""
    path = [Vector(p) for p in path]
    length = arc_length(path)
    bevel = max(0.0018, radius * 0.17)
    if n is None:
        n = max(16, int(2 * math.pi * radius / (2 * bevel) * 1.5))
    turns = length * pitch / (2 * math.pi * radius)
    samples = max(40, int(turns * 22))
    pts = resample(path, samples)
    tans, us, vs = frames(pts)
    objs = []
    if core:
        objs.append(c.curve_tube(f"{name}_Core", pts,
                                 [(radius_fn(i / (samples - 1)) if radius_fn else 1.0) for i in range(samples)],
                                 mat, bevel=radius * 0.84, resolution=4))
    s_acc = [0.0]
    for i in range(1, samples):
        s_acc.append(s_acc[-1] + (pts[i] - pts[i - 1]).length)
    for k in range(n):
        phi = 2 * math.pi * k / n + rng.uniform(-0.15, 0.15)
        sign = 1 if k % 2 == 0 else -1
        strand = []
        for i in range(samples):
            u = i / (samples - 1)
            r = radius * (radius_fn(u) if radius_fn else 1.0) * rng.uniform(0.985, 1.015)
            a = phi + sign * s_acc[i] * pitch / radius
            strand.append(pts[i] + (us[i] * math.cos(a) + vs[i] * math.sin(a)) * r)
        objs.append(c.curve_tube(f"{name}_{k}", strand, [1.0] * samples, mat, bevel=bevel, resolution=2))
    return objs


def strand_bundle(name, path, radius, mat, rng, n=18, twist=7.0, split_at=None, fan=None,
                  sub_radius=None, bevel=0.0032, tip_taper=0.18, radius_fn=None, samples=90,
                  spread=(0.25, 1.0)):
    """A bundle of strands twisting around a center path. If split_at is given, from that
    point on the strands part into three sub-bundles moving toward `fan` offsets (three
    vectors reached at the tip): the circlet's trident."""
    pts = resample([Vector(p) for p in path], samples)
    tans, us, vs = frames(pts)
    sub_radius = radius * 0.45 if sub_radius is None else sub_radius
    objs = []
    for k in range(n):
        phi = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(*spread) ** 0.5     # (1, 1) keeps every strand on the surface
        om = twist * rng.uniform(0.8, 1.2) * (1 if rng.random() < 0.8 else -1)
        grp = k % 3
        strand, radii = [], []
        for i in range(samples):
            u = i / (samples - 1)
            f = smoothstep((u - split_at) / (1 - split_at)) if split_at is not None else 0.0
            base_r = radius * (radius_fn(u) if radius_fn else 1.0)
            r = base_r * (1 - f) + sub_radius * f
            ctr = pts[i] + (Vector(fan[grp]) * f ** 1.3 if fan else V(0, 0, 0))
            a = phi + om * u
            strand.append(ctr + (us[i] * math.cos(a) + vs[i] * math.sin(a)) * r * rr)
            radii.append(1.0 - 0.85 * smoothstep((u - (1 - tip_taper)) / tip_taper))
        objs.append(c.curve_tube(f"{name}_{k}", strand, radii, mat, bevel=bevel, resolution=2))
    return objs


def droplet(name, center, radius, direction, mat, stretch=1.0):
    """Glowing teardrop pointing along `direction`."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=32, ring_count=16, location=(0, 0, 0))
    drop = bpy.context.active_object
    drop.name = name
    for v in drop.data.vertices:
        if v.co.z > 0:
            f = v.co.z / radius
            v.co.x *= 1 - 0.72 * f
            v.co.y *= 1 - 0.72 * f
            v.co.z *= 1 + stretch * f
    drop.rotation_mode = "QUATERNION"
    drop.rotation_quaternion = V(0, 0, 1).rotation_difference(Vector(direction).normalized())
    drop.location = Vector(center)
    drop.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return [drop]


# ------------------------------------------------------------------ tendrils (luxury scrollwork)

def plane_mapper(origin, ex, ey):
    """Map 2D (x, y) to 3D on the plane through `origin` spanned by ex and ey."""
    o, ex, ey = Vector(origin), Vector(ex).normalized(), Vector(ey).normalized()
    return lambda x, y: o + ex * x + ey * y


def cylinder_mapper(axis_origin, radius, axis=(0, 0, 1)):
    """Map 2D (x, y) onto a cylinder: x runs along the axis, y is arc length around it,
    so a tendril laid out at an angle becomes a vine spiralling around a shaft."""
    o = Vector(axis_origin)
    u, v, w = basis(axis)
    return lambda x, y: o + w * x + (u * math.cos(y / radius) + v * math.sin(y / radius)) * radius


def volute(length, turns, curl_start=0.4, bend=0.0, n=160, tight=0.86):
    """2D centerline starting at the origin heading +x: a stem that bends gently (`bend`
    radians in total), then a scroll whose radius of curvature shrinks steadily, so it
    rolls into a generous spiral that tightens toward the centre (`turns` revolutions,
    positive = counter-clockwise). Returns points and headings."""
    ls = length * curl_start
    lc = length - ls
    sign = 1.0 if turns >= 0 else -1.0
    rho0 = lc * (-math.log(1 - tight) / tight) / (abs(turns) * 2 * math.pi) if turns else None
    ramp = 0.08 * length
    ds = length / (n - 1)
    x = y = th = 0.0
    pts, ths = [(0.0, 0.0)], [0.0]
    for i in range(1, n):
        s = i * ds
        k_stem = bend / ls if ls > 0 else 0.0
        if rho0 is None:
            k = k_stem
        elif s < ls:
            f = smoothstep((s - (ls - ramp)) / ramp)
            k = k_stem * (1 - f) + sign / rho0 * f * 0.6
        else:
            k = sign / (rho0 * (1 - tight * (s - ls) / lc))
        th += k * ds
        x += math.cos(th) * ds
        y += math.sin(th) * ds
        pts.append((x, y))
        ths.append(th)
    return pts, ths


def rope(name, center, radius, mats, strands=3, gold=True, taper=0.85, merge=0.82):
    """Ivory strands twisted around each other along `center` (a cord), thick to thin,
    merging into one near the end, with a thread of gold light wound between them."""
    n = len(center)
    tans, us, vs = frames(center)
    s_acc = [0.0]
    for i in range(1, n):
        s_acc.append(s_acc[-1] + (center[i] - center[i - 1]).length)
    twist = 1.0 / (radius * 6.5)                      # turns per metre: a visible rope lay
    objs = []

    def r_at(u):
        return radius * max(1 - taper * u ** 1.2, 0.07)

    for k in range(strands + (1 if gold else 0)):
        is_gold = k == strands
        pts, radii = [], []
        for i in range(n):
            u = i / (n - 1)
            r = r_at(u)
            conv = 1 - smoothstep((u - merge) / (1 - merge))
            base = (k + 0.5) if is_gold else k
            a = 2 * math.pi * base / strands + 2 * math.pi * twist * s_acc[i]
            off = r * (0.72 if is_gold else 0.55) * conv
            pts.append(center[i] + (us[i] * math.cos(a) + vs[i] * math.sin(a)) * off)
            radii.append(max(r / radius, 0.07) * (0.42 if is_gold else 1.0) * (1 - 0.6 * (1 - conv) if is_gold else 1))
        mat = mats["light"] if is_gold else mats["ivory"]
        objs.append(c.curve_tube(f"{name}_{'gold' if is_gold else k}", pts, radii, mat,
                                 bevel=radius * 0.5, resolution=2))
    return objs


def tendril(name, mapper, origin2d, heading_deg, length, turns, radius, mats, strands=3, gold=True,
            offshoots=(), curl_start=0.4, bend=0.0):
    """A cord that leaves `origin2d` at `heading_deg` (in the mapper's 2D space), thins out
    and rolls into a tightening volute. offshoots: (u, side, length_scale, turns) side
    branches peeling off at fraction u, each curling on its own."""
    pts, ths = volute(length, turns, curl_start, bend)
    h = math.radians(heading_deg)
    ch, sh = math.cos(h), math.sin(h)
    p2 = [(origin2d[0] + x * ch - y * sh, origin2d[1] + x * sh + y * ch) for x, y in pts]
    th2 = [h + t for t in ths]
    center = [mapper(x, y) for x, y in p2]
    objs = rope(name, center, radius, mats, strands=strands, gold=gold)
    for k, (u, side, scale, t_c) in enumerate(offshoots):
        i = int(u * (len(p2) - 1))
        r_here = radius * max(1 - 0.85 * u ** 1.2, 0.07)
        objs += tendril(f"{name}_b{k}", mapper, p2[i], math.degrees(th2[i]) + side * 40, length * scale, t_c,
                        r_here * 0.85, mats, strands=2, gold=True, curl_start=0.3, bend=side * 0.25)
    return objs


# ------------------------------------------------------------------ blades

def path_blade(name, path, plane_normal, width_fn, thick_fn, mat, offset_fn=None, n_sec=12,
               samples=90, subsurf=1):
    """A blade of light lofted along a path. The width lies in the plane whose normal is
    `plane_normal`; width_fn(t) / thick_fn(t) give full width and thickness, and
    offset_fn(t) shifts the section sideways (for single-edged or crescent shapes)."""
    pts = resample(catmull(path, max(len(path) * 8, 16)), samples) if len(path) > 2 else resample(path, samples)
    n_plane = Vector(plane_normal).normalized()
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        t = i / (samples - 1)
        tan = (pts[min(i + 1, samples - 1)] - pts[max(i - 1, 0)]).normalized()
        side = n_plane.cross(tan).normalized()
        w = max(width_fn(t), 0.0004)
        th = max(thick_fn(t), 0.0003)
        ctr = p + side * (offset_fn(t) if offset_fn else 0.0)
        ring = []
        for j in range(n_sec):
            a = 2 * math.pi * j / n_sec
            x = w / 2 * math.cos(a)
            y = th / 2 * math.sin(a) * (1 - abs(math.cos(a)) ** 3) ** 0.5
            ring.append(bm.verts.new(ctr + side * x + n_plane * y))
        rings.append(ring)
    for i in range(samples - 1):
        for j in range(n_sec):
            k = (j + 1) % n_sec
            bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return [mesh_obj(name, bm, mat, subsurf=subsurf)]


def interp1d(knots, t):
    """Smooth (Catmull-Rom) interpolation through (t, value) knots sorted by t."""
    ts = [k[0] for k in knots]
    vs = [k[1] for k in knots]
    t = min(max(t, ts[0]), ts[-1])
    i = max(0, min(len(ts) - 2, next((j for j in range(len(ts) - 1) if t <= ts[j + 1]), len(ts) - 2)))
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    p0 = vs[max(i - 1, 0)]
    p1, p2 = vs[i], vs[i + 1]
    p3 = vs[min(i + 2, len(vs) - 1)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u)


def wedge_blade(name, spine_pts, edge_pts, thick_fn, mat, n_u=9, plane_normal=(0, 1, 0), subsurf=1):
    """Single-edged blade lofted between a spine curve and an edge curve (same sample count):
    thick along the spine, tapering to a sharp edge (a wedge, not a flat plate)."""
    n_plane = Vector(plane_normal).normalized()
    count = len(spine_pts)
    bm = bmesh.new()
    rings = []
    for i in range(count):
        t = i / (count - 1)
        s, e = Vector(spine_pts[i]), Vector(edge_pts[i])
        th = max(thick_fn(t), 0.0004)
        top, bottom = [], []
        for j in range(n_u):
            u = (j / (n_u - 1)) ** 1.15
            h = th / 2 * (1 - u) ** 0.85
            p = s.lerp(e, u)
            top.append(p + n_plane * h)
            bottom.append(p - n_plane * h)
        ring = [bm.verts.new(p) for p in top] + [bm.verts.new(p) for p in reversed(bottom[:-1])]
        rings.append(ring)
    k = len(rings[0])
    for i in range(count - 1):
        for j in range(k):
            jj = (j + 1) % k
            bm.faces.new((rings[i][j], rings[i][jj], rings[i + 1][jj], rings[i + 1][j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return [mesh_obj(name, bm, mat, subsurf=subsurf)]


def core_lines(name, path, plane_normal, thick_fn, mat, reach=0.82, bevel=0.0016):
    """Bright fuller lines along both faces of a blade."""
    pts = resample(catmull(path, 32) if len(path) > 2 else path, 40)
    n_plane = Vector(plane_normal).normalized()
    objs = []
    for face in (-1, 1):
        line, radii = [], []
        for i in range(40):
            t = i / 39 * reach
            k = int(t * 39)
            line.append(pts[k] + n_plane * face * thick_fn(t) / 2 * 0.92)
            radii.append(1.0 - 0.8 * t)
        objs.append(c.curve_tube(f"{name}_{face}", line, radii, mat, bevel=bevel, resolution=2))
    return objs


# ------------------------------------------------------------------ assembly and render

def group(name, objs, location=(0, 0, 0), rotation=(0, 0, 0)):
    root = c.link(bpy.data.objects.new(name, None))
    for o in objs:
        if o.parent is None:
            o.parent = root
    root.location = location
    root.rotation_euler = rotation
    return root


def render_sheets(out, stem, mats, target, distance, views, glow_views=None, res=(900, 700),
                  lens=50, cols=None, backdrop=False, extra=None):
    """Studio sheet + blend + dark glow sheet, with lights scaled to the camera distance.
    extra: list of (label, target, distance, views) close-ups rendered in the glow pass."""
    os.makedirs(out, exist_ok=True)
    k = distance / 2.0
    tgt = Vector(target)
    c.setup_render(samples=32, res=res, world_hex="#2E2E33", world_strength=0.5)
    c.add_light("key", "AREA", tgt + V(1.0, -0.6, 1.0) * k, 110 * k * k, size=1.0 * k, target=tgt)
    c.add_light("fill", "AREA", tgt + V(-1.0, 0.2, 0.4) * k, 38 * k * k, size=1.0 * k, target=tgt)
    c.add_light("rim", "AREA", tgt + V(0.0, 1.4, 0.9) * k, 65 * k * k, size=0.8 * k, target=tgt)
    studio = c.render_views(out, "studio", target, distance, views, lens=lens)
    c.contact_sheet(studio, os.path.join(out, f"{stem}_sheet.png"), cols=cols or min(3, len(studio)))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(out, f"{stem}.blend")))

    glow_mode(mats)
    c.setup_render(samples=32, res=res, world_hex="#0E0E12", world_strength=0.25, glare=True)
    glow = c.render_views(out, "glow", target, distance, glow_views or views[:2], lens=lens)
    for label, t2, d2, v2 in (extra or []):
        glow += c.render_views(out, f"glow_{label}", t2, d2, v2, lens=lens)
    c.contact_sheet(glow, os.path.join(out, f"{stem}_glow_sheet.png"), cols=min(3, len(glow)))
    print("DONE", studio + glow, flush=True)
    return studio, glow
