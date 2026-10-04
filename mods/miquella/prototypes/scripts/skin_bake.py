"""The body's skin textures (2026-10-04, plan C): the game's own female body skin baked onto our
body (A), our own where the two shapes differ (B).

Our body (MakeHuman, miquella_body.py) had a flat albedo and a flat normal: lit, it read as a
statue next to the face (ruddiness, fine shadows, fine lines). The game's skin material
(innerwear "skin", SkinEdit) uses one body texture set for the whole female body,
Art/Model/Character/ch03/CommonTextures/skin/f_body_base_{ALBD,NRRO}.tex, on one UV layout, but
no single game mesh carries all of that skin: every armour part keeps only the skin it shows (the
innerwear's legs have none). So the source is the union of the skin submeshes of many female
parts (SOURCE_PARTS, picked by `survey` for how much of the texture each one covers); they are all
cut from the same body on the same skeleton in the same bind pose as ours.

A (where the shapes agree): every texel of our UV -> its point on our body -> the nearest point
on the game skin -> that point's game UV -> the game texel. The normal map is moved between the
two tangent frames (only the turn about the normal: the game's own surface tilt is not copied,
our shape stays ours).
B (where they do not: the game breasts' shading over our flat chest, both navels, the groin,
places far from any game skin, our neck tube whose UVs are degenerate): A's colour and roughness
filled in smoothly over our mesh from around, plus A's own detail finer than DETAIL_R texels (the
skin's grain without the game body's features), a faint 3D noise where even that is wrong
(navels, neck tube), our own occlusion from our mesh.
The game's NRRO normal is decoded as RE Mesh Editor does (signed squares, turned 45 degrees);
checked 2026-10-04 that this reads as the slope of a height field in Blender's tangent frames
(curl / divergence 0.2-0.4, mirrored 0.7-0.9), so the transfer keeps the game's convention.

The output is a derivative of Capcom's textures: it stays out of the repo (MiquellaTools work
folder); the pak gets it from there. Whether it can ship is the user's call at release time.

Usage (bpy45 python, RE Mesh Editor in the user add-ons; the game files from extract_game_files.py:
the ch03 .mdf2 files, the parts' .mesh with their streaming/ copies, the two skin textures):
  python skin_bake.py survey <extracted natives/stm> <out.json>
      every female part whose material uses the body skin: how much of the texture its skin covers
  python skin_bake.py bake <extracted natives/stm> <our mq_body_c_f.mesh> <out dir> [size]
      MiquellaSkin_{ALBD,NRRO}.png (2048 by default) + mask_A.png, normal_preview.png in <out dir>
  python skin_bake.py preview <extracted natives/stm> <our mq_body_c_f.mesh> <bake dir> <out dir>
      the game's bare body with its textures / ours flat / ours baked, front, torso, back
  python skin_bake.py stage <bake dir> <character kit dir> <stage dir>
      the kit's natives + the baked skin as .tex in <stage dir> -> make_patch_pak.py <stage dir> ...
One texture for every body (A/B/C, male and female: the same MakeHuman UVs), baked on C female
(the user's); A and B differ a little in shape, the male only at the neck and shoulders.
"""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(__file__))
import miquella_body as mb

CHAR = "art/model/character"
SKIN_TEX = f"{CHAR}/ch03/commontextures/skin/f_body_base_%s.tex.241106027"
MESH_EXT = ".mesh.241111606"


def log(msg):
    print(msg, flush=True)


def part_path(stm, name):
    """ch03_025_0014 -> <stm>/art/model/character/ch03/025/001/4/ch03_025_0014.mesh..."""
    _, a, b = name.split("_")
    return os.path.join(stm, *CHAR.split("/"), "ch03", a, b[:3], b[3], name + MESH_EXT)


def skin_objects(path):
    """The skin submeshes of a game part (Blender space), others deleted."""
    _, objs = mb.import_game(path, keep_meshes=True)
    keep = []
    for o in objs:
        names = [m.name.split(".")[0].lower() for m in o.data.materials if m]
        if names and all(n == "skin" for n in names):
            keep.append(o)
        else:
            bpy.data.objects.remove(o, do_unlink=True)
    for o in list(bpy.data.objects):
        if o.type == "ARMATURE":
            bpy.data.objects.remove(o, do_unlink=True)
    return keep


def uv_mask(objs, w=256, h=512):
    """Which texels of the game skin texture these objects' faces cover (numpy bool h x w)."""
    import numpy as np
    from PIL import Image, ImageDraw
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for o in objs:
        me = o.data
        uv = me.uv_layers.active.data
        for p in me.polygons:
            pts = [(uv[li].uv.x * w, (1 - uv[li].uv.y) * h) for li in p.loop_indices]
            d.polygon(pts, fill=255)
    return np.array(im) > 0


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)
    for d in list(bpy.data.collections):
        bpy.data.collections.remove(d)


def survey(stm, out):
    import glob
    import numpy as np
    import common as c
    c.reset_scene()
    mb.enable_addon()
    key = "f_body_base_ALBD".encode("utf-16-le")
    names = sorted(os.path.basename(p).split(".")[0]
                   for p in glob.glob(os.path.join(stm, *CHAR.split("/"), "ch03", "**", "*.mdf2.45"), recursive=True)
                   if key in open(p, "rb").read())
    res = {}
    masks = {}
    for n in names:
        path = part_path(stm, n)
        if not os.path.exists(path):
            continue
        clear()
        objs = skin_objects(path)
        if not objs:
            continue
        m = uv_mask(objs)
        masks[n] = m
        res[n] = {"texels": int(m.sum()), "faces": sum(len(o.data.polygons) for o in objs)}
        log(f"{n}: {res[n]}")
    # greedy cover: the part adding the most new texels each round
    covered = np.zeros_like(next(iter(masks.values())))
    order = []
    while True:
        best = max(masks, key=lambda n: (masks[n] & ~covered).sum())
        gain = int((masks[best] & ~covered).sum())
        if gain < 200:
            break
        covered |= masks[best]
        order.append((best, gain))
    log(f"greedy: {order}; covered {covered.mean():.3f} of the texture")
    from PIL import Image
    Image.fromarray((covered * 255).astype("uint8")).save(os.path.splitext(out)[0] + "_covered.png")
    json.dump({"parts": res, "greedy": order}, open(out, "w"), indent=1)


# ------------------------------------------------------------------ bake

# The female parts whose skin together covers 77% of the texture (`survey`, greedy; the rest of
# the texture is padding): the bare body's torso and legs (armour 000), the innerwear's arms and
# hands, a little more of the arm from 042.
SOURCE_PARTS = ("ch03_000_0002", "ch03_000_0004", "ch03_002_0001", "ch03_042_0012")
OUR_SKIN = ("miquellaskin", "miquellaskinchest", "miquellaskinwaist")
# Where A gives way to B (metres, our surface to the game skin's nearest point along our normal)
MATCH = {"near": 0.030, "far": 0.060,           # |offset| within near: A; beyond far: B (the game
                                                # body is curvier: hips, thighs 2-4 cm wider; a projection that far still lands;
                                                # the breasts and navels have masks of their own)
         "cos_near": 0.85, "cos_far": 0.6,      # the two surfaces' normals agree
         "grow": 3, "soften": 4}                # mask grown, then softened (graph steps ~7 mm)
NAVEL_R = (0.018, 0.030)                        # m: B inside the first, blending out by the second
CHEST_BAND = (1.22, 1.42)                       # m high (file space): the game breasts' shading
CHEST_GROW = 4                                  # extra steps over the chest: the crease under them
AO = {"rays": 24, "dist": 0.025, "strength": 0.4}   # our own occlusion, in the B parts only
GROIN_R = (0.05, 0.09)                          # m from the crotch: the game body's groin shading
NECK_GROW = 3                                   # steps around our neck tube (its UVs are degenerate)
# m: how far the nearest game point lies off our normal (sideways). Past the game skin's open
# edges (our neck base stands 3 cm above the game's, NECK_LIFT) every point lands on the same edge
# and its texels smear out in streaks like wood grain (2026-10-04, in game): B there, no A detail
# (only round the neck and shoulders, SLIDE_ABOVE up: elsewhere the game body's other curves
# shift the nearest point sideways too, harmlessly)
SLIDE = (0.006, 0.015)
SLIDE_ABOVE = 1.25
DETAIL_R = 3                                    # texels: B keeps A's detail finer than this
PORES = {"scale": 0.0012, "albedo": 0.02, "normal": 0.10}    # 3D noise where A's detail is no good
FILL_STEPS = 300


def smoothstep(e0, e1, x):
    import numpy as np
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def tri_arrays(objs, tangents=True):
    """Triangles of objects in file-ish Blender space: dict of numpy arrays per triangle corner
    (pos, uv, nor, tan, bit: T x 3 x n) and the vertex index per corner (into the stacked
    vertex positions `verts`)."""
    import numpy as np
    out = {k: [] for k in ("pos", "uv", "nor", "tan", "bit", "vid")}
    verts, base = [], 0
    for o in objs:
        me = o.data
        M = np.array(o.matrix_world)
        R = M[:3, :3]
        me.calc_loop_triangles()
        if tangents:
            me.calc_tangents(uvmap=me.uv_layers.active.name)
        nl, nv, nt = len(me.loops), len(me.vertices), len(me.loop_triangles)
        co = np.empty(nv * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3) @ R.T + M[:3, 3]
        lt = np.empty(nt * 3, np.int32)
        me.loop_triangles.foreach_get("loops", lt)
        lt = lt.reshape(-1, 3)
        lv = np.empty(nl, np.int32)
        me.loops.foreach_get("vertex_index", lv)
        uv = np.empty(nl * 2, np.float32)
        me.uv_layers.active.data.foreach_get("uv", uv)
        nor = np.array([v.vector for v in me.corner_normals], np.float32) @ R.T
        out["pos"].append(co[lv[lt]])
        out["uv"].append(uv.reshape(-1, 2)[lt])
        out["nor"].append(nor[lt])
        out["vid"].append(lv[lt] + base)
        if tangents:
            tan = np.empty(nl * 3, np.float32)
            me.loops.foreach_get("tangent", tan)
            bit = np.empty(nl * 3, np.float32)
            me.loops.foreach_get("bitangent", bit)
            out["tan"].append(tan.reshape(-1, 3)[lt] @ R.T)
            out["bit"].append(bit.reshape(-1, 3)[lt] @ R.T)
        verts.append(co)
        base += nv
    res = {k: np.concatenate(v) for k, v in out.items() if v}
    res["verts"] = np.concatenate(verts)
    return res


def frame(nor, tan, bit):
    """Orthonormal tangent frame from interpolated corner vectors, keeping the handedness."""
    import numpy as np
    n = nor / np.linalg.norm(nor, axis=-1, keepdims=True)
    t = tan - n * (tan * n).sum(-1, keepdims=True)
    t /= np.maximum(np.linalg.norm(t, axis=-1, keepdims=True), 1e-9)
    b = np.cross(n, t)
    b *= np.sign((b * bit).sum(-1, keepdims=True) + 1e-12)
    return n, t, b


def rasterize(uv, size):
    """Texels of a size x size image whose centres fall in the UV triangles (T x 3 x 2, v up).
    Returns (row, col, triangle, barycentric 3)."""
    import numpy as np
    P = uv.astype(np.float64) * size - 0.5                     # texel centre i sits at i
    lo = np.clip(np.ceil(P.min(1)), 0, size - 1).astype(np.int64)
    hi = np.clip(np.floor(P.max(1)), 0, size - 1).astype(np.int64)
    w = np.maximum(hi[:, 0] - lo[:, 0] + 1, 0)
    h = np.maximum(hi[:, 1] - lo[:, 1] + 1, 0)
    n = w * h
    tri = np.repeat(np.arange(len(uv)), n)
    k = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
    x = lo[tri, 0] + k % w[tri]
    y = lo[tri, 1] + k // w[tri]
    a, b, c = P[tri, 0], P[tri, 1], P[tri, 2]
    v0, v1, v2 = b - a, c - a, np.stack([x, y], 1) - a
    d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1)
    d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    ok = np.abs(den) > 1e-12
    den = np.where(ok, den, 1)
    l1 = (d11 * d20 - d01 * d21) / den
    l2 = (d00 * d21 - d01 * d20) / den
    l0 = 1 - l1 - l2
    inside = ok & (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
    idx = y * size + x
    sel = np.flatnonzero(inside)
    _, first = np.unique(idx[sel], return_index=True)
    sel = sel[first]
    bary = np.stack([l0[sel], l1[sel], l2[sel]], 1)
    return size - 1 - y[sel], x[sel], tri[sel], bary


def interp(arr, tri, bary):
    return (arr[tri] * bary[:, :, None]).sum(1)


def bary_on(P, tri_pos):
    """Barycentric coordinates of points P (N x 3) on triangles (N x 3 x 3), clamped inside."""
    import numpy as np
    a, b, c = tri_pos[:, 0], tri_pos[:, 1], tri_pos[:, 2]
    v0, v1, v2 = b - a, c - a, P - a
    d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1)
    d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
    den = np.where(np.abs(d00 * d11 - d01 * d01) > 1e-18, d00 * d11 - d01 * d01, 1)
    l1 = (d11 * d20 - d01 * d21) / den
    l2 = (d00 * d21 - d01 * d20) / den
    bary = np.clip(np.stack([1 - l1 - l2, l1, l2], 1), 0, 1)
    return bary / bary.sum(1, keepdims=True)


def nearest(bvh, P):
    """Nearest point on the BVH for each row of P: (location N x 3, triangle index N)."""
    import numpy as np
    loc = np.empty((len(P), 3))
    idx = np.empty(len(P), np.int64)
    fn = bvh.find_nearest
    for i, p in enumerate(P.tolist()):
        l, _, k, _ = fn(p)
        loc[i] = l
        idx[i] = k
    return loc, idx


def sample(img, uv):
    """Bilinear sample of an image (H x W x C float, row 0 = top) at UVs (v up)."""
    import numpy as np
    H, W = img.shape[:2]
    x = np.clip(uv[:, 0] * W - 0.5, 0, W - 1)
    y = np.clip((1 - uv[:, 1]) * H - 0.5, 0, H - 1)
    x0 = np.minimum(np.floor(x).astype(int), W - 2); y0 = np.minimum(np.floor(y).astype(int), H - 2)
    fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


# The game's NRRO normal (as RE Mesh Editor decodes it for Blender's tangent frames): G and A
# hold the signed square roots of two components of the normal turned 45 degrees about Z. Only
# a mirror error would matter here (a turn cancels out between decoding and encoding again).
C45 = math.sqrt(0.5)


def nrro_decode(g, a):
    import numpy as np
    gy = 2 * g - 1
    ax = 1 - 2 * a
    x0, y0 = gy * np.abs(gy), ax * np.abs(ax)
    z = np.sqrt(np.clip(1 - x0 * x0 - y0 * y0, 0, 1))
    return np.stack([x0 * C45 - y0 * C45, x0 * C45 + y0 * C45, z], -1)


def nrro_encode(v):
    import numpy as np
    v = v / np.linalg.norm(v, axis=-1, keepdims=True)
    x0 = v[..., 0] * C45 + v[..., 1] * C45
    y0 = -v[..., 0] * C45 + v[..., 1] * C45
    gy = np.sign(x0) * np.sqrt(np.abs(x0))
    ax = np.sign(y0) * np.sqrt(np.abs(y0))
    return (gy + 1) / 2, (1 - ax) / 2


def weld(verts, eps=1e-5):
    """Vertex -> welded id by position (our export split the mesh along its UV seams)."""
    import numpy as np
    key = np.round(verts / eps).astype(np.int64)
    _, wid, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    return inv.ravel(), verts[wid]


class Graph:
    """Neighbour averaging on the welded mesh (smoothing and filling masks, colours)."""

    def __init__(self, tri_vid, n):
        import numpy as np
        e = np.concatenate([tri_vid[:, [0, 1]], tri_vid[:, [1, 2]], tri_vid[:, [2, 0]]])
        e = np.unique(np.sort(e, 1), axis=0)
        e = e[e[:, 0] != e[:, 1]]
        self.a = np.concatenate([e[:, 0], e[:, 1]])
        self.b = np.concatenate([e[:, 1], e[:, 0]])
        self.deg = np.maximum(np.bincount(self.a, minlength=n), 1).astype(np.float64)
        self.n = n

    def mean(self, x):
        import numpy as np
        s = np.zeros((self.n,) + x.shape[1:])
        np.add.at(s, self.a, x[self.b])
        return s / self.deg.reshape((-1,) + (1,) * (x.ndim - 1))

    def max(self, x):
        import numpy as np
        s = x.copy()
        np.maximum.at(s, self.a, x[self.b])
        return s


def value_noise(P, scale, seed=0):
    """Smooth 3D value noise (-1..1) at points P (N x 3), cell size `scale` metres."""
    import numpy as np
    q = P / scale
    i = np.floor(q).astype(np.int64)
    f = q - i
    f = f * f * (3 - 2 * f)

    def h(ix, iy, iz):
        v = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
        v = (v ^ (v >> 13)) * 1274126177
        return ((v ^ (v >> 16)) & 0xFFFF) / 32767.5 - 1.0

    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * h(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz)
    return out


def pores(P):
    s = PORES["scale"]
    return 0.6 * value_noise(P, s, 1) + 0.3 * value_noise(P, s * 0.5, 2) + 0.25 * value_noise(P, s * 3.0, 3)


def pushpull(img, known):
    """Fill the texels outside `known` (H x W bool) from the nearest known ones, coarse to fine
    (the texture's padding around the UV islands, so mips and filtering do not pull in black)."""
    import numpy as np
    levels = [(img * known[..., None], known.astype(np.float64))]
    while min(levels[-1][1].shape) > 1:
        c, w = levels[-1]
        H, W = w.shape
        c = c[:H // 2 * 2, :W // 2 * 2].reshape(H // 2, 2, W // 2, 2, -1).sum((1, 3))
        w = w[:H // 2 * 2, :W // 2 * 2].reshape(H // 2, 2, W // 2, 2).sum((1, 3))
        levels.append((c, w))
    c, w = levels[-1]
    fill = c / np.maximum(w, 1e-9)[..., None]
    for c, w in reversed(levels[:-1]):
        H, W = w.shape
        up = np.repeat(np.repeat(fill, 2, 0), 2, 1)
        up = np.pad(up, ((0, H - up.shape[0]), (0, W - up.shape[1]), (0, 0)), mode="edge")
        mine = c / np.maximum(w, 1e-9)[..., None]
        fill = np.where((w > 0)[..., None], mine, up)
    return np.where(known[..., None], img, fill)


def load_png(path):
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGBA"), np.float64) / 255


def bake(stm, our_mesh, out, size="2048"):
    import numpy as np
    from mathutils.bvhtree import BVHTree
    from PIL import Image
    import common as c
    import decode_wilds_tex as dwt
    size = int(size)
    os.makedirs(out, exist_ok=True)
    c.reset_scene()
    mb.enable_addon()

    # --- the game skin (A's source)
    src_objs = []
    for n in SOURCE_PARTS:
        src_objs += skin_objects(part_path(stm, n))
    S = tri_arrays(src_objs)
    log(f"game skin: {len(S['pos'])} triangles from {SOURCE_PARTS}")
    tex = {}
    for kind in ("albd", "nrro"):
        im, _, _ = dwt.to_image(os.path.join(stm, "streaming", *(SKIN_TEX % kind).split("/")))
        tex[kind] = np.asarray(im.convert("RGBA"), np.float64) / 255
    bvh = BVHTree.FromPolygons(S["pos"].reshape(-1, 3).tolist(),
                               np.arange(len(S["pos"]) * 3).reshape(-1, 3).tolist(), all_triangles=True)

    # --- our body
    _, ours = mb.import_game(our_mesh, keep_meshes=True)
    is_skin = lambda o: o.data.materials and o.data.materials[0].name.split(".")[0].lower() in OUR_SKIN
    briefs = [o for o in ours if not is_skin(o)]
    bco = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in briefs])
    crotch = bco[np.argmin(np.where(np.abs(bco[:, 0]) < 0.02, bco[:, 2], 9))]
    ours = [o for o in ours if is_skin(o)]
    O = tri_arrays(ours)
    log(f"our skin: {len(O['pos'])} triangles, objects {[o.name for o in ours]}")
    wid, wverts = weld(O["verts"])
    tri_w = wid[O["vid"]]
    graph = Graph(tri_w, len(wverts))
    vnor = np.zeros_like(wverts)
    np.add.at(vnor, tri_w.ravel(), O["nor"].reshape(-1, 3))
    vnor /= np.maximum(np.linalg.norm(vnor, axis=1, keepdims=True), 1e-9)

    # --- per welded vertex: how well the two surfaces agree (the masks), our own occlusion
    vloc, vidx = nearest(bvh, wverts)
    off = ((vloc - wverts) * vnor).sum(1)
    gb = bary_on(vloc, S["pos"][vidx])
    gnor = interp(S["nor"], vidx, gb)
    gnor /= np.linalg.norm(gnor, axis=1, keepdims=True)
    cosn = (gnor * vnor).sum(1)
    slide = np.linalg.norm((vloc - wverts) - off[:, None] * vnor, axis=1)
    slide_v = smoothstep(SLIDE[0], SLIDE[1], slide) * (wverts[:, 2] > SLIDE_ABOVE)
    up = wverts[:, 2] > SLIDE_ABOVE
    log("slide (mm) p50/p90/p99: neck and shoulders " + "/".join(f"{np.percentile(slide[up], q) * 1000:.1f}" for q in (50, 90, 99))
        + ", below " + "/".join(f"{np.percentile(slide[~up], q) * 1000:.1f}" for q in (50, 90, 99)))
    bad = np.maximum.reduce([smoothstep(MATCH["near"], MATCH["far"], np.abs(off)),
                             smoothstep(MATCH["cos_near"], MATCH["cos_far"], cosn), slide_v])
    y = wverts[:, 2]                                       # Blender z = file y (up)
    chest = (y > CHEST_BAND[0]) & (y < CHEST_BAND[1]) & (wverts[:, 1] < 0)   # front: Blender -y
    for _ in range(MATCH["grow"]):
        bad = graph.max(bad)
    extra = np.where(chest, bad, 0)
    for _ in range(CHEST_GROW):
        extra = np.where(chest, graph.max(extra), 0)
    bad = np.maximum(bad, extra)
    # the navels: ours (the deepest dent on the belly) and the game's (where its texture's navel
    # lands on our body), B around both
    lap = graph.mean(wverts)
    for _ in range(3):
        lap = graph.mean(lap)
    cav = ((lap - wverts) * vnor).sum(1)                  # > 0: a dent
    belly = (np.abs(wverts[:, 0]) < 0.02) & (y > 0.95) & (y < 1.20) & (wverts[:, 1] < 0)
    navel = wverts[np.flatnonzero(belly)[np.argmax(cav[belly])]]
    gnavel = game_navel(S, tex["albd"])
    dn = np.minimum(np.linalg.norm(wverts - navel, axis=1), np.linalg.norm(wverts - gnavel, axis=1))
    navel_v = smoothstep(NAVEL_R[1], NAVEL_R[0], dn)
    groin_v = smoothstep(GROIN_R[1], GROIN_R[0], np.linalg.norm(wverts - crotch, axis=1))
    # our neck tube: every column of it has one UV (miquella_body.neck_tube), its triangles have
    # no UV area -> whatever lies along that UV line streaks up it: no detail there at all
    e1, e2 = O["pos"][:, 1] - O["pos"][:, 0], O["pos"][:, 2] - O["pos"][:, 0]
    area3 = np.linalg.norm(np.cross(e1, e2), axis=1)
    u1, u2 = O["uv"][:, 1] - O["uv"][:, 0], O["uv"][:, 2] - O["uv"][:, 0]
    area_uv = np.abs(u1[:, 0] * u2[:, 1] - u1[:, 1] * u2[:, 0])
    ratio = area_uv / np.maximum(area3, 1e-12)
    neck_v = np.zeros(len(wverts))
    neck_v[tri_w[ratio < 0.02 * np.median(ratio)].ravel()] = 1
    for _ in range(NECK_GROW):
        neck_v = graph.max(neck_v)
    for _ in range(MATCH["grow"]):
        slide_v = graph.max(slide_v)
    for _ in range(MATCH["soften"]):
        bad = 0.5 * bad + 0.5 * graph.mean(bad)
        navel_v = 0.5 * navel_v + 0.5 * graph.mean(navel_v)
        neck_v = 0.5 * neck_v + 0.5 * graph.mean(neck_v)
        slide_v = 0.5 * slide_v + 0.5 * graph.mean(slide_v)
    neck_v = np.maximum(neck_v, slide_v)
    # softening must not let the game's navel back in (2026-10-04: a faint slit 3 cm above ours)
    navel_v = np.maximum(navel_v, smoothstep(NAVEL_R[0], NAVEL_R[0] * 0.6, dn))
    wA_v = (1 - bad) * (1 - navel_v) * (1 - neck_v) * (1 - groin_v)
    plain_v = np.maximum.reduce([navel_v, neck_v, groin_v])    # no A detail at all: our pores instead
    # ...but not round the neck: each column of the neck tube reads one texel by the cut, so any
    # grain there runs up the tube and out over the shoulders as streaks (2026-10-04, in game):
    # smooth colour and a flat normal only
    pores_v = plain_v * (1 - neck_v)
    detail_v = 1 - plain_v
    log(f"navel ours {np.round(navel, 3)}, game's {np.round(gnavel, 3)}; crotch {np.round(crotch, 3)}; "
        f"neck tube {int((ratio < 0.02 * np.median(ratio)).sum())} triangles; projection slid off on {np.mean(slide_v > 0.5):.3f}; A on {np.mean(wA_v > 0.5):.2f} of the vertices")
    ao = occlusion(wverts, vnor, tri_w)

    # --- per texel
    row, col, tri, bary = rasterize(O["uv"], size)
    P = interp(O["pos"], tri, bary)
    n_o, t_o, b_o = frame(interp(O["nor"], tri, bary), interp(O["tan"], tri, bary), interp(O["bit"], tri, bary))
    log(f"{len(P)} texels covered ({len(P) / size / size:.2f})")
    loc, sidx = nearest(bvh, P)
    sb = bary_on(loc, S["pos"][sidx])
    suv = interp(S["uv"], sidx, sb)
    n_g, t_g, b_g = frame(interp(S["nor"], sidx, sb), interp(S["tan"], sidx, sb), interp(S["bit"], sidx, sb))
    alb = sample(tex["albd"], suv)
    nr = sample(tex["nrro"], suv)
    # the game's normal detail, turned from its tangent frame into ours about the normal
    v = nrro_decode(nr[:, 1], nr[:, 3])
    d = v[:, :1] * t_g + v[:, 1:2] * b_g + v[:, 2:] * n_g
    d = rotate_onto(d, n_g, n_o)
    vA = np.stack([(d * t_o).sum(1), (d * b_o).sum(1), (d * n_o).sum(1)], 1)

    def tex_of(vals):
        v = vals[tri_w][tri]
        return (v * bary).sum(1) if v.ndim == 2 else (v * bary[:, :, None]).sum(1)

    wA = np.clip(tex_of(wA_v), 0, 1)[:, None]
    detail = np.clip(tex_of(detail_v), 0, 1)[:, None]
    plain = np.clip(tex_of(pores_v), 0, 1)[:, None]
    known = np.zeros((size, size), bool)
    known[row, col] = True
    # B = A's colour and roughness from around (per vertex, filled into the B parts over the
    # mesh) + A's own fine detail (finer than DETAIL_R texels: the skin's grain, not the game
    # body's features) + our pores where even that is wrong (navels, neck tube) + our occlusion
    vb = bary_on(vloc, S["pos"][vidx])
    low_src = sample(blur_image(np.concatenate([tex["albd"][..., :3], tex["nrro"][..., :1]], 2)), interp(S["uv"], vidx, vb))
    fill = low_src.copy()
    for _ in range(FILL_STEPS):
        fill = wA_v[:, None] * low_src + (1 - wA_v[:, None]) * graph.mean(fill)
    fill = tex_of(fill)
    a_vals = np.concatenate([alb[:, :3], vA[:, :2], nr[:, :1]], 1)
    grid = np.zeros((size, size, a_vals.shape[1]))
    grid[row, col] = a_vals
    wgrid = blur_image(known[..., None].astype(np.float64), DETAIL_R)
    low = (blur_image(grid, DETAIL_R) / np.maximum(wgrid, 1e-6))[row, col]
    high = (a_vals - low) * detail
    noise = pores(P)
    eps = PORES["scale"] * 0.25
    dh_t = (pores(P + t_o * eps) - noise) / eps
    dh_b = (pores(P + b_o * eps) - noise) / eps
    k = PORES["normal"] * PORES["scale"] * plain
    albB = fill[:, :3] + high[:, :3] + (PORES["albedo"] * noise[:, None] * plain) * fill[:, :3]
    vB = np.concatenate([high[:, 3:5] - k * np.stack([dh_t, dh_b], 1), np.ones((len(P), 1))], 1)
    vB /= np.linalg.norm(vB, axis=1, keepdims=True)
    occl = 1 - AO["strength"] * (1 - tex_of(ao))[:, None] * (1 - wA)

    albedo = (wA * alb[:, :3] + (1 - wA) * albB) * occl
    vn = wA * vA + (1 - wA) * vB
    vn /= np.linalg.norm(vn, axis=1, keepdims=True)
    rough = wA[:, 0] * nr[:, 0] + (1 - wA[:, 0]) * (fill[:, 3] + high[:, 5])
    g, a = nrro_encode(vn)

    def image(cols):
        img = np.zeros((size, size, cols.shape[1]))
        img[row, col] = cols
        return np.clip(pushpull(img, known), 0, 1)

    albd_img = image(np.concatenate([albedo, np.ones((len(P), 1))], 1))
    nrro_img = image(np.stack([rough, g, np.ones(len(P)), a], 1))
    save = lambda arr, name: Image.fromarray((arr * 255 + 0.5).astype(np.uint8)).save(os.path.join(out, name))
    save(albd_img, "MiquellaSkin_ALBD.png")
    save(nrro_img, "MiquellaSkin_NRRO.png")
    # previews / checks: the mask, a Blender-style normal map (our tangent frames, OpenGL)
    save(image(np.repeat(wA, 3, 1)), "mask_A.png")
    save(image(vn * 0.5 + 0.5), "normal_preview.png")
    log(f"wrote {out}")


def rotate_onto(d, a, b):
    """Rotate vectors d by the shortest turn taking unit vectors a onto b (row-wise)."""
    import numpy as np
    axis = np.cross(a, b)
    s = np.linalg.norm(axis, axis=1, keepdims=True)
    cth = (a * b).sum(1, keepdims=True)
    k = axis / np.maximum(s, 1e-12)
    return d * cth + np.cross(k, d) * s + k * (k * d).sum(1, keepdims=True) * (1 - cth)


def blur_image(img, r=6):
    """A box-blurred copy (low-frequency colour for the fill)."""
    import numpy as np
    out = img.copy()
    for axis in (0, 1):
        cs = np.cumsum(np.pad(out, [(r + 1, r) if i == axis else (0, 0) for i in range(3)], mode="edge"), axis)
        out = (np.take(cs, range(2 * r + 1, cs.shape[axis]), axis) - np.take(cs, range(0, cs.shape[axis] - 2 * r - 1), axis)) / (2 * r + 1)
    return out


def game_navel(S, albd):
    """The game body's navel in 3D: the darkest spot of its torso-front texture, found on the
    triangle that holds that UV."""
    import numpy as np
    H, W = albd.shape[:2]
    lum = blur_image(albd, 3)[..., :3].mean(2)
    u0, u1, v0, v1 = 0.25, 0.42, 0.60, 0.78                  # torso front, around the belly
    sub = lum[int((1 - v1) * H):int((1 - v0) * H), int(u0 * W):int(u1 * W)]
    r, cc = np.unravel_index(np.argmin(sub), sub.shape)
    uv = np.array([(int(u0 * W) + cc + 0.5) / W, 1 - (int((1 - v1) * H) + r + 0.5) / H])
    a, b, c = S["uv"][:, 0], S["uv"][:, 1], S["uv"][:, 2]
    v0_, v1_, v2_ = b - a, c - a, uv - a
    den = v0_[:, 0] * v1_[:, 1] - v1_[:, 0] * v0_[:, 1]
    den = np.where(np.abs(den) > 1e-12, den, 1)
    l1 = (v2_[:, 0] * v1_[:, 1] - v1_[:, 0] * v2_[:, 1]) / den
    l2 = (v0_[:, 0] * v2_[:, 1] - v2_[:, 0] * v0_[:, 1]) / den
    inside = np.flatnonzero((l1 >= 0) & (l2 >= 0) & (l1 + l2 <= 1))
    t = inside[0]
    bary = np.array([1 - l1[t] - l2[t], l1[t], l2[t]])
    return (S["pos"][t] * bary[:, None]).sum(0)


def occlusion(verts, nor, tri):
    """Ambient occlusion per welded vertex from our own mesh (cosine-weighted hemisphere)."""
    import numpy as np
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromPolygons(verts.tolist(), tri.tolist(), all_triangles=True)
    rng = np.random.default_rng(7)
    n = AO["rays"]
    u1, u2 = rng.random(n), rng.random(n)
    local = np.stack([np.sqrt(u1) * np.cos(2 * np.pi * u2), np.sqrt(u1) * np.sin(2 * np.pi * u2), np.sqrt(1 - u1)], 1)
    up = np.where(np.abs(nor[:, 2:3]) < 0.9, [[0, 0, 1]], [[1, 0, 0]])
    t = np.cross(up, nor)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    b = np.cross(nor, t)
    ao = np.empty(len(verts))
    dist = AO["dist"]
    for i in range(len(verts)):
        o = Vector(verts[i] + nor[i] * 5e-4)
        dirs = local[:, :1] * t[i] + local[:, 1:2] * b[i] + local[:, 2:] * nor[i]
        hit = 0
        for dvec in dirs:
            if bvh.ray_cast(o, Vector(dvec), dist)[0] is not None:
                hit += 1
        ao[i] = 1 - hit / n
    log(f"occlusion: mean {ao.mean():.3f}, min {ao.min():.3f}")
    return ao


# ------------------------------------------------------------------ preview

PREVIEW_TINT = (1.0, 0.80, 0.70)      # the SkinEdit shader tints the grey albedo from the SkinMap
FLAT = (161, 179, 181)                # our albedo before (BODY_TEXTURES in miquella_body.py)


def skin_material(name, albedo=None, normal=None, rough=None):
    """Principled skin for the previews: albedo x PREVIEW_TINT, a Blender tangent normal map,
    roughness from NRRO red (images are file paths or None for flat)."""
    import common as c
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Subsurface Weight"].default_value = 0.15
    bsdf.inputs["Subsurface Radius"].default_value = (0.004, 0.002, 0.0015)
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    mul.inputs["B"].default_value = (*PREVIEW_TINT, 1)
    if albedo:
        im = nt.nodes.new("ShaderNodeTexImage")
        im.image = bpy.data.images.load(albedo)
        nt.links.new(im.outputs["Color"], mul.inputs["A"])
    else:
        mul.inputs["A"].default_value = (*[c.hex_to_linear("#%02X%02X%02X" % FLAT)[i] for i in range(3)], 1)
    nt.links.new(mul.outputs["Result"], bsdf.inputs["Base Color"])
    if normal:
        im = nt.nodes.new("ShaderNodeTexImage")
        im.image = bpy.data.images.load(normal)
        im.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(im.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if rough:
        im = nt.nodes.new("ShaderNodeTexImage")
        im.image = bpy.data.images.load(rough)
        im.image.colorspace_settings.name = "Non-Color"
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(im.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Red"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = 0.6
    return mat


def preview(stm, our_mesh, bake_dir, out):
    """Three figures: the game's bare body with its own textures, ours flat (before), ours baked
    (after); a full front and a torso close-up. Has Capcom models in it: stays out of the repo."""
    import numpy as np
    from mathutils import Matrix
    from PIL import Image
    import common as c
    import decode_wilds_tex as dwt
    c.reset_scene()
    mb.enable_addon()
    os.makedirs(out, exist_ok=True)
    # the game's textures as Blender images (its normal decoded to a plain tangent normal map)
    gt = {}
    for kind in ("albd", "nrro"):
        im, _, _ = dwt.to_image(os.path.join(stm, "streaming", *(SKIN_TEX % kind).split("/")))
        gt[kind] = np.asarray(im.convert("RGBA"), np.float64) / 255
    paths = {"albd": os.path.join(out, "game_albd.png"), "nrm": os.path.join(out, "game_nrm.png"),
             "nrro": os.path.join(out, "game_nrro.png")}
    Image.fromarray((gt["albd"] * 255).astype(np.uint8)).save(paths["albd"])
    Image.fromarray((gt["nrro"] * 255).astype(np.uint8)).save(paths["nrro"])
    v = nrro_decode(gt["nrro"][..., 1], gt["nrro"][..., 3])
    Image.fromarray(((v * 0.5 + 0.5) * 255).astype(np.uint8)).save(paths["nrm"])
    game_mat = skin_material("game", paths["albd"], paths["nrm"], paths["nrro"])
    flat_mat = skin_material("flat")
    baked_mat = skin_material("baked", os.path.join(bake_dir, "MiquellaSkin_ALBD.png"),
                              os.path.join(bake_dir, "normal_preview.png"), os.path.join(bake_dir, "MiquellaSkin_NRRO.png"))
    cloth = c.make_material("cloth", "#E2DAC8", roughness=0.8)
    game = []
    for n in SOURCE_PARTS[:3]:
        game += skin_objects(part_path(stm, n))
    for o in game:
        o.data.materials.clear()
        o.data.materials.append(game_mat)
    figures = [game]
    for k, mat in enumerate((flat_mat, baked_mat)):
        _, ours = mb.import_game(our_mesh, keep_meshes=True)
        for o in ours:
            skin = o.data.materials[0].name.split(".")[0].lower() in OUR_SKIN
            o.data.materials.clear()
            o.data.materials.append(mat if skin else cloth)
            o.matrix_world = Matrix.Translation((0.85 * (k + 1), 0, 0)) @ o.matrix_world
        figures.append(ours)
    for o in list(bpy.data.objects):
        if o.type == "ARMATURE":
            o.hide_render = True
    c.setup_render(samples=48, res=(1500, 1100), world_hex="#1A1A1F", world_strength=0.5)
    c.add_light("key", "AREA", (2.0, -3.5, 2.8), 300, size=2.5, target=(0.85, 0, 1.1))
    c.add_light("fill", "AREA", (-1.5, -3.0, 1.6), 90, size=3.0, target=(0.85, 0, 1.0))
    c.add_light("rim", "AREA", (0.85, 3.0, 2.4), 160, size=3.0, target=(0.85, 0, 1.2))
    cd = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    shots = []
    for view, loc, rot, ortho in (("full", (0.85, -8, 0.9), (90, 0, 0), 2.6),
                                  ("torso", (1.275, -8, 1.2), (90, 0, 0), 1.6),
                                  ("back", (1.275, 8, 1.2), (90, 0, 180), 1.6),
                                  ("hand", None, (90, 0, 0), 0.45),       # the baked one's left hand
                                  ("feet", (1.275, -8, 0.07), (90, 0, 0), 1.2)):
        if loc is None:                   # its fingertip: the furthest point along +x
            tip = max((o.matrix_world @ v.co for o in figures[2] for v in o.data.vertices), key=lambda p: p.x)
            loc = (tip.x - 0.08, -8, tip.z + 0.06)
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
        cam.location = loc
        cam.rotation_euler = [math.radians(a) for a in rot]
        if view != "full":
            bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 1800, 900
        path = os.path.join(out, f"skin_{view}.png")
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        shots.append(path)
        log(f"render {path}")
    return shots


TONE_REF = (164, 179, 180)   # the baked albedo by the neck seam (SKIN_MATCH was measured on it)
TONE_KEEP = 0.25             # share of the game albedo's own hue left in (2026-10-04, in game: belly
                             # and thighs olive, chest and shoulders red under the strong SKIN_MATCH tint)


def even_tone(rgba):
    """Every texel the neck's hue, keeping its own lightness: the game's grey-cyan albedo drifts
    green, blue and purple over the body (the SkinEdit shader evens that out; our ColorParam
    tint only multiplies, so it turns the drift into olive and red patches)."""
    import numpy as np
    srgb = rgba[..., :3].astype(float) / 255
    lin = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    ref = np.array(TONE_REF, float) / 255
    ref = ((ref + 0.055) / 1.055) ** 2.4
    w = np.array((0.2126, 0.7152, 0.0722))
    even = ref * ((lin @ w) / (ref @ w))[..., None]
    lin = even + TONE_KEEP * (lin - even)
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.clip(lin, 0, None) ** (1 / 2.4) - 0.055)
    out = rgba.copy()
    out[..., :3] = np.clip(srgb * 255 + 0.5, 0, 255).astype(np.uint8)
    return out


def stage(bake_dir, kit_dir, stage_dir):
    """The character kit's natives with the baked skin over our flat one, ready for
    make_patch_pak.py (the baked textures never go into the kit in the repo)."""
    import shutil
    import numpy as np
    from PIL import Image
    mb.enable_addon()
    dst = os.path.join(stage_dir, "natives")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(kit_dir, "natives"), dst)
    images = [("MiquellaSkin", kind, np.asarray(Image.open(os.path.join(bake_dir, f"MiquellaSkin_{kind}.png")).convert("RGBA")))
              for kind in ("ALBD", "NRRO")]
    images[0] = images[0][:2] + (even_tone(images[0][2]),)
    log(mb.images_to_tex(stage_dir, images))


def main():
    cmd, *args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if cmd == "stage":
        return stage(*args)
    if cmd == "survey":
        survey(*args)
    elif cmd == "bake":
        bake(*args)
    elif cmd == "preview":
        preview(*args)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
