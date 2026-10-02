"""Step 2 of 2 (step 1: hair512_parts.py makes hair512.blend). Hairstyle 512 + 12 thin braids among the loose waves + the main braid lengthened (same width).
Variant A: one thick braid in front of each shoulder; B: all at the back.
Usage: bpy45 python hair512_braids.py <A|B> [out dir]   (renders contain Capcom models: keep out of the repo)"""
import math, os, random, sys
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = "C:/Users/anton/MiquellaTools/extracted/natives/stm/art/model/character"
BODY = ("C:/Users/anton/ForClaude/mods/miquella/mhws/MiquellaLight_Character_kit/natives/STM/Art/"
        "Model/MiquellaLight/Character/mq_body_a.mesh.241111606")
W512 = "C:/Users/anton/MiquellaTools/work/hair512/hair512.blend"
VARIANT = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "C:/Users/anton/MiquellaTools/work/previews/hair_mq"
os.makedirs(OUT, exist_ok=True)
HAIR_COL = (0.85, 0.68, 0.30, 1)
SKIN_COL = (0.50, 0.47, 0.46, 1)
TIE_COL = (1.0, 0.55, 0.08, 1)
OPTS = {"clearScene": False, "createCollections": True, "loadMaterials": False,
        "loadMDFData": False, "loadShellFur": False, "loadUnusedTextures": False,
        "loadUnusedProps": False, "useBackfaceCulling": False, "reloadCachedTextures": False,
        "mdfPath": "", "importAllLODs": False, "importBlendShapes": False, "rotate90": True,
        "mergeArmature": "", "importArmatureOnly": False, "mergeGroups": False,
        "importShadowMeshes": False, "importOcclusionMeshes": False, "importBoundingBoxes": False}

# Thin braids: (azimuth from the back, + = character's left (+X), start z, end z, width,
# azimuth factor at the end (hair narrows toward the back lower down)).
BACK = [(-88, 1.612, 1.38, 0.0095, 0.85, 1), (-80, 1.565, 1.22, 0.011, 0.75, 0),
        (-64, 1.60, 1.30, 0.010, 0.75, 1), (-45, 1.525, 1.13, 0.012, 0.7, 0),
        (-37, 1.585, 1.25, 0.0095, 0.75, 1), (-18, 1.495, 1.17, 0.011, 0.85, 0),
        (16, 1.52, 1.21, 0.0105, 0.85, 1), (33, 1.575, 1.12, 0.012, 0.75, 0),
        (50, 1.535, 1.24, 0.010, 0.7, 1), (57, 1.595, 1.15, 0.011, 0.7, 0),
        (78, 1.555, 1.30, 0.0105, 0.75, 0), (96, 1.615, 1.36, 0.009, 0.85, 1)]
# Start heights are staggered: some come out from under the side twists, some from the waves lower.
FRONT = [  # side (+1 left / -1 right), start azimuth, x on shoulder, end z, width
    # as thick as the two side twists that merge into the main braid (~3 cm)
    (1, 122, 0.112, 1.17, 0.030), (-1, 120, 0.115, 1.15, 0.030)]
THIN_SCALE = 1.5   # user 2026-10-03: the thin braids were too thin
ROOT_LEN, ROOT_LEN_FRONT = 0.04, 0.06   # braids gathered from the hair above their start
SINK = 1.2   # how deep (x width) the root tips go under the loose hair
FRONT_REPLACES = {0, 11}   # indices in BACK dropped in variant A


def flatten_new(before, color):
    objs = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in objs if o.type == "MESH"]
    for o in meshes:
        mw = o.matrix_world.copy()
        o.parent = None
        o.modifiers.clear()
        o.data.transform(mw)
        o.matrix_world = Matrix.Identity(4)
        o.color = color
    for o in objs:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    return meshes


def bvh_from(items):
    """items: (obj, set of polygon indices to skip or None)"""
    verts, polys = [], []
    for o, skip in items:
        off = len(verts)
        verts += [v.co.copy() for v in o.data.vertices]
        polys += [[off + i for i in p.vertices] for p in o.data.polygons
                  if not skip or p.index not in skip]
    return BVHTree.FromPolygons(verts, polys)


def smooth(pts, n=6, iters=4):
    for _ in range(iters):
        q = []
        for i in range(len(pts)):
            if i == 0 or i == len(pts) - 1:
                q.append(pts[i].copy())
                continue
            lo, hi = max(0, i - n), min(len(pts), i + n + 1)
            s = Vector()
            for p in pts[lo:hi]:
                s += p
            q.append(s / (hi - lo))
        pts = q
    return pts


def resample(pts, step):
    out = [pts[0].copy()]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = (b - a).length
        t = step - acc
        while t <= seg:
            out.append(a.lerp(b, t / seg))
            t += step
        acc = seg - (t - step)
    if (out[-1] - pts[-1]).length > step * 0.3:
        out.append(pts[-1].copy())
    return out


def catmull(ctrl, per=40):
    pts = []
    c = [ctrl[0]] + ctrl + [ctrl[-1]]
    for i in range(1, len(c) - 2):
        p0, p1, p2, p3 = c[i - 1], c[i], c[i + 1], c[i + 2]
        for k in range(per):
            t = k / per
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    pts.append(ctrl[-1].copy())
    return pts


class Builder:
    def __init__(self):
        self.v, self.f = [], []

    def ring_tube(self, rings):
        k = len(rings[0])
        for r in rings:
            self.v += r
        base = len(self.v) - k * len(rings)
        for j in range(len(rings) - 1):
            for i in range(k):
                a = base + j * k + i
                b = base + j * k + (i + 1) % k
                self.f.append((a, b, b + k, a + k))
        # caps
        self.f.append(tuple(base + i for i in range(k))[::-1])
        last = base + (len(rings) - 1) * k
        self.f.append(tuple(last + i for i in range(k)))

    def obj(self, name, color):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.color = color
        for p in me.polygons:
            p.use_smooth = True
        return ob


def frames(pts, outs):
    n = len(pts)
    T = []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        T.append((b - a).normalized())
    B, N = [], []
    for t, o in zip(T, outs):
        b = (o - t * o.dot(t)).normalized()
        B.append(b)
        N.append(t.cross(b))
    return T, B, N


def braid(name, pts, outs, W, color, tail_len=None, seed=0, tie=True, tail=True, ramp_in=True,
          root_len=0.0):
    """Three-strand braid along pts (top -> bottom, ~1 mm apart); flat side faces outs.
    The first root_len of the path is the root: the three strands fan out upward as flat locks
    that thin out and sink into the loose hair, so the braid is gathered from the hair instead
    of starting from nothing."""
    rnd = random.Random(seed)
    T, B, N = frames(pts, outs)
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + (b - a).length)
    L = s[-1]
    P = 2.3 * W
    amp, dep, maj, mnr = 0.24 * W, 0.15 * W, 0.27 * W, 0.135 * W
    ph0 = rnd.uniform(0, 2 * math.pi)
    K = 12
    bld = Builder()
    t0s = [ph0 + 2 * math.pi * i / 3 for i in range(3)]
    order = sorted(range(3), key=lambda i: math.sin(t0s[i]))
    spread = min(0.8 * W, 0.014)
    e0 = 0.4 if ramp_in else 1.0
    for i in range(3):
        side = (order.index(i) - 1) * (1.0 + rnd.uniform(-0.2, 0.2))
        centers, roots = [], []
        for j, sj in enumerate(s):
            if sj < root_len:
                u = (root_len - sj) / root_len          # 1 at the top of the root
                t0 = t0s[i]
                centers.append(pts[j] + N[j] * (amp * e0 * math.sin(t0) + spread * side * u ** 1.2)
                               + B[j] * (dep * e0 * math.sin(2 * t0) * (1 - u) - SINK * W * u ** 1.2))
                roots.append(u)
                continue
            sb = sj - root_len
            env = 1.0
            if ramp_in:
                env *= 0.4 + 0.6 * min(1.0, sb / (1.2 * P))
            env *= 0.35 + 0.65 * min(1.0, (L - sj) / (0.6 * P))
            t = 2 * math.pi * sb / P + t0s[i]
            centers.append(pts[j] + N[j] * (amp * env * math.sin(t))
                           + B[j] * (dep * env * math.sin(2 * t)))
            roots.append(0.0)
        rings = []
        for j, c in enumerate(centers):
            a, b = centers[max(0, j - 1)], centers[min(len(centers) - 1, j + 1)]
            ti = (b - a).normalized()
            bb = (B[j] - ti * B[j].dot(ti)).normalized()
            mm = bb.cross(ti)
            sj = s[j]
            thin = 0.55 + 0.45 * min(1.0, (L - sj) / (0.5 * P))
            u = roots[j]
            fw, ft = 1 - 0.75 * u, 1 - 0.75 * u     # root locks: taper to a point as they sink
            if ramp_in and u == 0.0:                # the braid tightens and thickens over 1.2 periods
                g = 0.7 + 0.3 * min(1.0, max(0.0, sj - root_len) / (1.2 * P))
                fw, ft = g, g
            ring = []
            for k in range(K):
                th = 2 * math.pi * k / K
                f = (1 + 0.07 * math.sin(7 * th + i)) * thin
                ring.append(c + mm * (maj * math.cos(th) * f * fw) + bb * (mnr * math.sin(th) * f * ft))
            rings.append(ring)
        bld.ring_tube(rings)
    objs = [bld.obj(name, color)]
    end, te, be, ne = pts[-1], T[-1], B[-1], N[-1]
    if tie:
        tb = Builder()
        rings = []
        for h in range(5):
            c = end + te * (-0.0035 * W / 0.01 + h * 0.0018 * W / 0.01)
            r = 0.30 * W * (1.0 + 0.12 * math.sin(math.pi * h / 4))
            rings.append([c + ne * (r * math.cos(2 * math.pi * k / 16)) + be * (r * math.sin(2 * math.pi * k / 16))
                          for k in range(16)])
        tb.ring_tube(rings)
        objs.append(tb.obj(name + "_tie", TIE_COL))
    if tail:
        # soft fan of flat locks (wavy, tapering), fuller on thick braids
        tl = tail_len or 3.0 * W
        kb = Builder()
        count = 9 if W < 0.02 else 14
        for m in range(count):
            ang = 2 * math.pi * m / count + rnd.uniform(-0.25, 0.25)
            spread = Vector(ne * math.cos(ang) + be * math.sin(ang) * 0.6)
            ln = tl * rnd.uniform(0.6, 1.0)
            wv, fq = rnd.uniform(0, 6.3), rnd.uniform(2.5, 4.0)
            cs = []
            for h in range(17):
                u = h / 16
                cs.append(end + te * (ln * u + 0.002) + spread * (0.10 * W + 0.30 * W * math.sin(u * 2.2))
                          + spread.cross(te).normalized() * (0.10 * W * math.sin(fq * u * 3.1416 + wv)))
            rings = []
            for h, c in enumerate(cs):
                u = h / 16
                w = 0.20 * W * (1 - 0.9 * u ** 1.5)
                side = spread.cross(te).normalized()
                rings.append([c + side * (w * math.cos(2 * math.pi * k / 8)) + spread * (0.22 * w * math.sin(2 * math.pi * k / 8))
                              for k in range(8)])
            kb.ring_tube(rings)
        objs.append(kb.obj(name + "_tail", color))
    return objs


def robe_proxy(body):
    """Ivory stand-in over the torso and arms (not the robe design): body pushed out 5 mm."""
    bm = bmesh.new()
    for o in body:
        bm.from_mesh(o.data)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 1.445 or abs(v.co.x) > 0.52
                               or v.co.z < 0.80], context="VERTS")
    for v in bm.verts:
        v.co += v.normal * 0.009
    for _ in range(25):
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5,
                              use_axis_x=True, use_axis_y=True, use_axis_z=True)
    # the stand-in hides the torso: drop the covered body so nothing pokes through
    for o in body:
        bb = bmesh.new()
        bb.from_mesh(o.data)
        bmesh.ops.delete(bb, geom=[v for v in bb.verts if v.co.z <= 1.43 and abs(v.co.x) <= 0.50
                                   and v.co.z >= 0.83], context="VERTS")
        bb.to_mesh(o.data)
    me = bpy.data.meshes.new("robe_proxy")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("robe_proxy", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.color = (0.93, 0.86, 0.66, 1)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def main():
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile

    bpy.ops.wm.open_mainfile(filepath=W512)
    flatten_new(set(), HAIR_COL)
    hair = bpy.data.objects["Group_1_Sub_1__hair"]
    acc = bpy.data.objects["Group_1_Sub_0__acc"]
    scalp = bpy.data.objects["Group_0_Sub_0__scalp"]
    before = set(bpy.data.objects)
    importREMeshFile(f"{ROOT}/ch00/000/0000/ch00_000_0000.mesh.241111606", OPTS)
    face = flatten_new(before, SKIN_COL)
    before = set(bpy.data.objects)
    importREMeshFile(BODY, OPTS)
    body = flatten_new(before, SKIN_COL)
    print("face", [o.name for o in face], "body", [o.name for o in body], flush=True)

    # --- braid parts of 512: the braided section and the tail below the tie
    gi = hair.vertex_groups["BRAID_PART"].index
    bv = {v.index for v in hair.data.vertices if any(g.group == gi for g in v.groups)}
    bm = bmesh.new()
    bm.from_mesh(hair.data)
    bm.verts.ensure_lookup_table()
    seen, tailv, braidv = set(), set(), set()
    for v in bm.verts:
        if v.index not in bv or v in seen:
            continue
        stack, comp = [v], []
        seen.add(v)
        while stack:
            x = stack.pop()
            comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        (tailv if max(x.co.z for x in comp) < 1.456 else braidv).update(x.index for x in comp)
    braid_polys = {p.index for p in hair.data.polygons if p.vertices[0] in bv}
    # split the tail off into its own object (to move it to the new end)
    bmt = bm.copy()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in tailv], context="VERTS")
    bm.to_mesh(hair.data)
    bmt.verts.ensure_lookup_table()
    bmesh.ops.delete(bmt, geom=[v for v in bmt.verts if v.index not in tailv], context="VERTS")
    me = bpy.data.meshes.new("tail512")
    bmt.to_mesh(me)
    tail512 = bpy.data.objects.new("tail512", me)
    bpy.context.scene.collection.objects.link(tail512)
    tail512.color = HAIR_COL
    acc.color = TIE_COL

    def slab(z0, z1):
        ps = [hair.data.vertices[i].co for i in braidv]
        ps = [p for p in [Vector(q) for q in ps] if z0 < p.z < z1]
        return ps

    # Recompute braid vertex indices after deletion: use coordinates instead
    braid_pts = [Vector(v.co) for v in bmt.verts]  # unused; keep for clarity
    bm2 = bmesh.new()
    bm2.from_mesh(hair.data)
    # BVH of the loose hair only (no braid lobes): drop polygons whose verts lie near the braid axis
    hair_bvh_items = [(hair, None)]
    HAIR = bvh_from(hair_bvh_items)
    BODYT = bvh_from([(o, None) for o in body + face])
    robe_proxy(body)

    # main braid metrics from original coordinates (taken before deletion via acc and lobes)
    lobes = []
    gidx = hair.vertex_groups["BRAID_PART"].index
    for v in hair.data.vertices:
        if any(g.group == gidx for g in v.groups):
            lobes.append(Vector(v.co))
    def centre(z0, z1):
        ps = [p for p in lobes if z0 < p.z < z1]
        xs, ys = [p.x for p in ps], [p.y for p in ps]
        return Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (z0 + z1) / 2)), max(xs) - min(xs), max(ys) - min(ys)
    c_hi, w_hi, d_hi = centre(1.545, 1.565)
    c_lo, w_lo, d_lo = centre(1.495, 1.515)
    print("main braid width %.4f depth %.4f at z1.50; %.4f at 1.555" % (w_lo, d_lo, w_hi), c_lo, c_hi, flush=True)
    tie_c = Vector()
    for v in acc.data.vertices:
        tie_c += v.co
    tie_c /= len(acc.data.vertices)

    # loose-hair BVH without the braid lobes
    HAIRL = bvh_from([(hair, {p.index for p in hair.data.polygons
                              if any(gidx in [g.group for g in hair.data.vertices[vi].groups] for vi in p.vertices[:1])})])

    def hair_hit(phi_deg, z, tree=HAIRL, yc=0.02, x0=None):
        ph = math.radians(phi_deg)
        d = Vector((math.sin(ph), math.cos(ph), 0))
        o = Vector((0 if x0 is None else x0, yc, z)) + d * 0.7
        loc, nrm, idx, dist = tree.ray_cast(o, -d, 0.75)
        return loc, d

    def hit_near(ph, z, side):
        for k in range(12):
            loc, d = hair_hit(ph - side * 5 * k, z)
            if loc is not None:
                return loc, d
        raise RuntimeError(f"no hair near {ph} {z}")

    def root_above(phi_deg, z0, w, length):
        """Hair-surface points from z0 + length down to just above z0 (top -> bottom)."""
        out, r_prev, z = [], None, z0 + 0.004
        while z <= z0 + length:
            loc, d = hair_hit(phi_deg, z)
            if loc is None:
                break
            r = (loc - Vector((0, 0.02, z))).length
            if r_prev is not None and r > r_prev + 0.002:
                r = r_prev + 0.002
            r_prev = r
            out.append((Vector((0, 0.02, z)) + d * (r + w * 0.25), d))
            z += 0.004
        return out[::-1]

    def root_length(pts, z0):
        acc = 0.0
        for a, b in zip(pts, pts[1:]):
            if b.z <= z0:
                return acc
            acc += (b - a).length
        return acc

    out_objs = []
    # --- main braid lengthened: same width, from inside the original lobes down to z 1.20
    W = w_lo * 0.92
    dirv = (c_lo - c_hi).normalized()
    ctrl, outs = [], []
    z = 1.53
    p = c_lo + dirv * ((c_lo.z - 1.53) / -dirv.z) if dirv.z < 0 else c_lo
    while z > 1.20:
        loc, d = hair_hit(0, z, x0=c_lo.x)
        straight = c_lo + dirv * ((z - c_lo.z) / dirv.z)
        if loc is not None:
            target = loc + Vector((0, 1, 0)) * (d_lo * 0.45)
            k = min(1.0, (1.53 - z) / 0.10)
            q = straight.lerp(target, k)
        else:
            q = straight
        ctrl.append(q)
        outs.append(Vector((0, 1, 0)))
        z -= 0.005
    ctrl = smooth(ctrl, n=5, iters=6)
    pts = resample(ctrl, 0.0015)
    outs = [Vector((0, 1, 0))] * len(pts)
    out_objs += braid("main_ext", pts, outs, W, HAIR_COL, seed=1, tie=False, tail=False, ramp_in=False)
    shift = pts[-1] - tie_c + (pts[-1] - pts[-2]).normalized() * 0.004
    for o in (acc, tail512):
        o.data.transform(Matrix.Translation(shift))

    # --- thin braids
    back = [b for i, b in enumerate(BACK) if not (VARIANT == "A" and i in FRONT_REPLACES)]
    for n, (phi, z0, z1, w, fac, tuck) in enumerate(back):
        w *= THIN_SCALE
        root = root_above(phi, z0, w, ROOT_LEN)
        ctrl, outs = [p for p, d in root], [d for p, d in root]
        z = z0
        while z > z1:
            u = (z0 - z) / max(1e-6, z0 - z1)
            ph = phi * (1 - (1 - fac) * u) + 3.0 * math.sin(z * 38 + n)
            loc, d = hair_hit(ph, z)
            if loc is None:
                if len(ctrl) > len(root):
                    break
                z -= 0.004
                continue
            off = 0.25
            if tuck and z < z0 - 0.06:
                off -= 1.1 * max(0.0, math.sin(2 * math.pi * (z0 - z) / 0.16 + n))
            ctrl.append(loc + d * (w * off))
            outs.append(d)
            z -= 0.004
        if len(ctrl) < len(root) + 10:
            print("skip braid", n, flush=True)
            continue
        ctrl = smooth(ctrl, n=4, iters=5)
        pts = resample(ctrl, 0.001)
        outs = [outs[min(len(outs) - 1, int(i * len(outs) / len(pts)))] for i in range(len(pts))]
        out_objs += braid(f"b{n}", pts, outs, w, HAIR_COL, seed=10 + n,
                          root_len=root_length(pts, z0) if root else 0.0)

    if VARIANT == "A":
        for n, (side, phi, xs, z1, w) in enumerate(FRONT):
            a0, d0 = hit_near(side * phi, 1.615, side)
            a1, d1 = hit_near(side * (phi + 8), 1.545, side)
            # shoulder top under the braid
            top = Vector((side * xs, 0.0, 2.0))
            hit = BODYT.ray_cast(top, Vector((0, 0, -1)), 1.0)[0]
            sh = hit + Vector((0, -0.012, w * 0.6 + 0.004))
            def front_at(z, x):
                h = BODYT.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)), 1.5)[0]
                return h + Vector((0, -(w * 0.6 + 0.003), 0))
            c1 = front_at(sh.z - 0.07, side * (xs - 0.012))
            c2 = front_at((sh.z - 0.07 + z1) / 2, side * (xs - 0.022))
            c3 = front_at(z1, side * (xs - 0.026))
            ctrl = [a0 + d0 * (w * 0.25), a1 + d1 * (w * 0.4), sh, c1, c2, c3]
            root = root_above(side * phi, 1.615, w, ROOT_LEN_FRONT)
            pts = [p for p, d in root] + catmull(ctrl, per=60)
            # keep clear of body and face
            for it in range(3):
                q = []
                for p in pts:
                    loc, nrm, idx, dist = BODYT.find_nearest(p)
                    if loc is not None and ((p - loc).dot(nrm) < 0 or dist < w * 0.6 + 0.002):
                        p = loc + nrm * (w * 0.6 + 0.003)
                    q.append(p)
                pts = smooth(q, n=3, iters=2)
            pts = resample(pts, 0.001)
            outs = []
            for p in pts:
                loc, nrm, idx, dist = BODYT.find_nearest(p)
                hd = Vector((p.x, p.y - 0.02, 0)).normalized()
                outs.append(nrm if p.z < sh.z + 0.02 else hd)
            outs = smooth(outs, n=10, iters=3)
            outs = [o.normalized() for o in outs]
            out_objs += braid(f"f{n}", pts, outs, w, HAIR_COL, seed=40 + n,
                              root_len=root_length(pts, 1.615) if root else 0.0)

    bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/hair_mq_{VARIANT}.blend")
    render(out_objs, [hair, acc, scalp, tail512] + face + body)


def render(braids, others):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "OBJECT"
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.curvature_ridge_factor = 1.5
    sc.display.render_aa = "16"
    sc.render.resolution_x, sc.render.resolution_y = 640, 960
    for o in bpy.data.objects:
        if o.type in ("LIGHT", "CAMERA"):
            bpy.data.objects.remove(o, do_unlink=True)
    cd = bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cd.ortho_scale = 0.82
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    mid = 1.40
    views = (("back", (0, 3, mid), (90, 0, 180)), ("back34", (2.3, 2.0, mid), (90, 0, 131)),
             ("side", (3, 0, mid), (90, 0, 90)), ("front34", (2.0, -2.3, mid), (90, 0, 41)),
             ("front", (0, -3, mid), (90, 0, 0)))
    for name, loc, rot in views:
        cam.location = loc
        cam.rotation_euler = [math.radians(a) for a in rot]
        sc.render.filepath = f"{OUT}/{VARIANT}_{name}.png"
        bpy.ops.render.render(write_still=True)
    # highlight: braids in rose so they can be told apart
    for o in braids:
        if not o.name.endswith("_tie"):
            o.color = (0.95, 0.45, 0.55, 1)
    for name, loc, rot in views[:2] + views[3:4]:
        cam.location = loc
        cam.rotation_euler = [math.radians(a) for a in rot]
        sc.render.filepath = f"{OUT}/{VARIANT}_{name}_hl.png"
        bpy.ops.render.render(write_still=True)
    print("RENDERED", flush=True)


try:
    main()
except Exception:
    import traceback
    traceback.print_exc()
finally:
    sys.stdout.flush()
    os._exit(0)
