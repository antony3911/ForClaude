"""Robe design (2026-10-03/04) on Miquella's body for a female hunter (mq_body_c_f), with the game's
female face, hairstyle 512 and our circlet for context. Long sleeves to the wrist, a skirt to the
ankles. Decided with the user (DESIGN.md "服裝"):
  fits (all kept, as options): "lines" fitted, the body's lines showing; "smooth" fitted, no lines;
    "drape" hanging from the shoulders, pushed out only by the buttocks; "cinch" the drape with the
    sash pulling it in at the waist
  jewellery, all gold, on the drape only (the fitted ones plain, version N): D = gold-ring sash
    (loose on the hips on "drape", cinched at the waist on "cinch") with two hanging cords ending in
    gold drops, narrow gold hem and cuff bands, and the broad collar 丁 (collar:strands: the
    circlet's strands radiating over a gold plate, a fringe of gold drops)
  proposals not taken: A plain wide bands, B openwork scroll bands, C scroll vines; collars 甲
    beads, 乙 leaves, 丙 scrolls
Usage: bpy45 python robe_designs.py <out dir> [A B C D N] [lines smooth drape cinch] [collar:<kind>]
       [full] [test]
  e.g. "D drape cinch collar:strands full" (Cycles close-ups of the collar plus the full body),
       "N lines smooth"
Renders contain Capcom models (face, hair): keep them out of the repo."""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from miquella_body import split_along  # noqa: E402
from motifs import volute  # noqa: E402

ROOT = "C:/Users/anton/MiquellaTools/extracted/natives/stm/art/model/character"
KIT = ("C:/Users/anton/ForClaude/mods/miquella/mhws/MiquellaLight_Character_kit/natives/STM/Art/"
       "Model/MiquellaLight/Character/")
BODY = KIT + "mq_body_c_f.mesh.241111606"
CIRCLET = KIT + "mq_circlet.mesh.241111606"
FACE = ROOT + "/ch00/001/0000/ch00_001_0000.mesh.241111606"
HAIR = ROOT + "/ch01/001/0/512/ch01_001_0512.mesh.241111606"
OPTS = {"clearScene": False, "createCollections": True, "loadMaterials": False,
        "loadMDFData": False, "loadShellFur": False, "loadUnusedTextures": False,
        "loadUnusedProps": False, "useBackfaceCulling": False, "reloadCachedTextures": False,
        "mdfPath": "", "importAllLODs": False, "importBlendShapes": False, "rotate90": True,
        "mergeArmature": "", "importArmatureOnly": False, "mergeGroups": False,
        "importShadowMeshes": False, "importOcclusionMeshes": False, "importBoundingBoxes": False}

# object colours (workbench, linear: these come out lighter)
COL = {"skin": (0.80, 0.52, 0.42, 1), "hair": (0.85, 0.68, 0.30, 1), "robe": (0.88, 0.81, 0.64, 1),
       "gold": (0.78, 0.42, 0.06, 1), "circlet": (0.90, 0.70, 0.38, 1), "light": (1.0, 0.55, 0.05, 1)}

# --- the robe's shape (Blender space: +Z up, the face looks toward -Y, +X the hunter's left)
GAP = 0.004           # m between the body and the fitted cloth
# How the fitted part follows the body (user 2026-10-03: keep both):
#   "lines"  plain smoothing then pushed back out: the cloth shows the chest and belly lines (the user
#            picked this look from a test render: keep it as it was, waist corner not rounded off)
#   "smooth" Taubin smoothing (no shrinking): muscle lines, navel and grooves bridged; pushed out only
#            where it went into the body (pushing it back to GAP every round copied the nipples back)
#   "drape"  (user 2026-10-03: "no lines at all, hanging from the shoulders, the body's curve only
#            showing where the buttocks push it out a little") the "smooth" cloth over the shoulders
#            and the top of the chest only; from DRAPE_TOP down it falls straight, pushed out only
#            by what sticks out (buttocks, hips), then flares to the hem
#   "cinch"  (2026-10-04, the user liked D's sash and hem on the drape only) the drape with the sash
#            pulling the cloth in at the hips: a little blousing above, falling and flaring below.
#            "drape" with D has the sash resting loose on the hanging cloth, dipping in front
FITS = {"lines": (40, 3), "smooth": (60, 4), "drape": (60, 4), "cinch": (60, 4)}   # smoothing steps per round, rounds
BLOUSE = 0.008        # m: how far the cinched cloth puffs out between the chest and the sash
SASH_LOOSE = (0.835, 0.915, 0.885)   # m: a loose sash on the drape, front (dipping) / side (on the hips) / back
SMOOTH_GAP = 0.0015   # m: "smooth" / "drape" cloth pushed out only to here
# "smooth" in game (2026-10-04): the crotch and one side of the chest still showed through ("no
# lines" should show none): pushing the cloth back out of the body copies its bumps back. After
# that, smoothing that only ever moves the cloth out (never in) so it spans the hollows like
# stretched cloth: the groin's V, the dips round the chest.
INFLATE = {"smooth": 400}
DRAPE_TOP = (1.31, 1.27, 1.34)   # m: where the cloth leaves the body, front (chest) / side (armpit) / back (shoulder blades)
DRAPE_X = 0.22        # m: the drape cut only on the torso (the arms hang beyond this)
DRAPE_SOFT = 0.08     # m: profile smoothing (the cloth's stiffness) over the buttocks
COLLAR_DROP = (0.040, 0.034, 0.028)   # m below the top of the body (the face's neck edge): front, side, back
COLLAR_R = 0.115      # m from the neck's axis: the collar cut only reaches this far
CUFF_T = 0.96         # along forearm -> wrist joint, where the sleeve ends
# m: the skirt hangs from here, front / side / back: fitted over the hips above (the crotch is at ~0.83;
# low in front so the groin lines show, at the widest of the hips at the sides and the buttocks behind)
SKIRT_TOP = (0.86, 0.90, 0.88)
# "smooth" ("no lines"): the skirt from above the groin in front, so the crotch is under hanging
# cloth, not under the fitted part (its V showed in game, 2026-10-04)
SKIRT_TOP_SMOOTH = (0.93, 0.92, 0.88)
HEM_Z = 0.095         # m: hem at the ankles
HEM_R = (0.43, 0.35)  # m: hem half-widths (x, y) before the folds
BELL = 1.0            # share of the extra width (beyond the straight line that clears the legs) put in as a bell
FOLDS = 9             # main folds around
FOLD_AMP = 0.032      # m at the hem
LEG_CLEAR = 0.018     # m kept between the skirt and the legs (bind pose)
ROWS = 72             # skirt rows
SKIRT_COLS = 160      # skirt columns, at even angles
SEAM_DROP = 0.004     # m between the fitted part's lower edge and the skirt's first row
K_FROM = 0.05         # m below the top where the skirt's slope starts to count the legs


def log(*a):
    print(*a, flush=True)


def import_mesh(path, color, drop=()):
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile
    before = set(bpy.data.objects)
    importREMeshFile(path, OPTS)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next((o for o in new if o.type == "ARMATURE"), None)
    joints = {}
    if arm:
        for b in arm.data.bones:
            joints[b.name] = arm.matrix_world @ b.head_local
    meshes = []
    others = [o for o in new if o.type != "MESH"]
    for o in new:
        if o.type != "MESH":
            continue
        names = " ".join(m.name.lower() for m in o.data.materials if m)
        if any(k in names for k in drop):
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        mw = o.matrix_world.copy()
        o.parent = None
        o.modifiers.clear()
        o.data.transform(mw)
        o.matrix_world = Matrix.Identity(4)
        o.color = color
        o.data.materials.clear()
        for p in o.data.polygons:
            p.use_smooth = True
        meshes.append(o)
    for o in others:
        bpy.data.objects.remove(o, do_unlink=True)
    return meshes, joints


def body_bmesh(objs):
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    n0 = sum(f.normal.z for f in bm.faces if f.calc_center_median().z > 1.6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)   # the two parts (skin, briefs) wound alike
    bm.normal_update()
    log("body normals recalculated (neck faces' z sum before %.2f)" % n0)
    return bm


def mesh_object(name, bm, color, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.color = color
    for p in me.polygons:
        p.use_smooth = smooth
    return ob


def boundary_loops(bm):
    """Open edge loops of a mesh, each as an ordered list of verts."""
    edges = {e for e in bm.edges if e.is_boundary}
    loops = []
    while edges:
        e = edges.pop()
        loop = [e.verts[0], e.verts[1]]
        while True:
            v = loop[-1]
            nxt = next((x for x in v.link_edges if x in edges), None)
            if not nxt:
                break
            edges.discard(nxt)
            w = nxt.other_vert(v)
            if w is loop[0]:
                break
            loop.append(w)
        loops.append(loop)
    return loops


def keep_largest(bm):
    seen, comps = set(), []
    for v in bm.verts:
        if v in seen:
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
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    for comp in comps[1:]:
        bmesh.ops.delete(bm, geom=comp, context="VERTS")


def taubin(verts, passes, lam=0.5, mu=-0.53, weight=None):
    """Smooth without shrinking (Taubin's lambda/mu): muscle lines and the navel go, the volume stays.
    Boundary verts stay put; weight(v) in 0..1 scales the move per vert."""
    import numpy as np
    verts = [v for v in verts if v.is_valid]
    idx = {v: i for i, v in enumerate(verts)}
    P = np.array([v.co[:] for v in verts])
    a, b = [], []
    for v in verts:
        for e in v.link_edges:
            w = e.other_vert(v)
            if w in idx:
                a.append(idx[v])
                b.append(idx[w])
    a, b = np.array(a), np.array(b)
    deg = np.bincount(a, minlength=len(verts)).astype(float)
    free = np.array([0.0 if v.is_boundary else 1.0 for v in verts])
    if weight:
        free *= np.array([weight(v) for v in verts])
    free = free[:, None] * (deg > 0)[:, None]
    deg[deg == 0] = 1
    for _ in range(passes):
        for f in (lam, mu):
            avg = np.zeros_like(P)
            np.add.at(avg, a, P[b])
            P += f * free * (avg / deg[:, None] - P)
    for v, p in zip(verts, P):
        v.co = p


def angle_blend(theta, front, side, back):
    """theta 0 = front (-Y), pi = back; smooth front -> side -> back."""
    c = math.cos(theta)
    return side + (front - side) * max(c, 0) + (back - side) * max(-c, 0)


# ------------------------------------------------------------------ the fitted part (bodice and sleeves)

def flatten_dense(bm):
    """The nipples and the navel on the copy the cloth is made from: inside 2 cm of each, the
    surface set onto a quadric fitted to the ring 4.5 to 6.5 cm out (blended out by 4.5 cm);
    plain smoothing there shrank the patch by about the nipple's height and the cloth, pushed 4 mm
    out, came back on the nipple's own shape (2026-10-04)."""
    import numpy as np
    import statistics
    lens = {v: sum(e.calc_length() for e in v.link_edges) / max(len(v.link_edges), 1) for v in bm.verts}
    med = statistics.median(lens.values())
    dense = [v for v in bm.verts if lens[v] < 0.45 * med and v.co.y < 0 and 1.1 < v.co.z < 1.4 and abs(v.co.x) < 0.15]
    centres = []
    for side in (1, -1):
        pts = [v.co for v in dense if v.co.x * side > 0]
        if pts:
            centres.append(sum(pts, Vector()) / len(pts))
    mid = [v for v in bm.verts if abs(v.co.x) < 0.012 and 0.97 < v.co.z < 1.12 and v.co.y < 0]
    if mid:
        centres.append(max(mid, key=lambda v: v.co.y).co.copy())   # the navel: the deepest point of the belly's midline
    front = [v for v in bm.verts if v.co.y < 0.02]
    for c in centres:
        ring = [v for v in front if 0.045 < (v.co - c).length < 0.065]
        inner = [v for v in front if (v.co - c).length < 0.045]
        if len(ring) < 12 or not inner:
            continue
        n = sum((v.normal for v in ring), Vector()).normalized()
        u = n.cross(Vector((0, 0, 1))).normalized()
        w = n.cross(u)
        A = np.array([[1, (v.co - c).dot(u), (v.co - c).dot(w), (v.co - c).dot(u) ** 2,
                       (v.co - c).dot(u) * (v.co - c).dot(w), (v.co - c).dot(w) ** 2] for v in ring])
        h = np.array([(v.co - c).dot(n) for v in ring])
        coef = np.linalg.lstsq(A, h, rcond=None)[0]
        for v in inner:
            d = v.co - c
            x, y = d.dot(u), d.dot(w)
            target = float(np.dot(coef, [1, x, y, x * x, x * y, y * y]))
            t = min(max((d.length - 0.02) / 0.025, 0.0), 1.0)
            k = 1 - t * t * (3 - 2 * t)
            v.co += n * (target - d.dot(n)) * k
    bm.normal_update()
    return len(centres), len(dense)


class Fit:
    def __init__(self, body_objs, J):
        self.J = J
        self.bm_body = body_bmesh(body_objs)
        self.bm_real = self.bm_body.copy()
        self.bvh_real = BVHTree.FromBMesh(self.bm_real)
        log("nipples and navel flattened (patches, dense verts):", flatten_dense(self.bm_body))
        self.bvh_flat = BVHTree.FromBMesh(self.bm_body)
        self.bvh = self.bvh_flat
        self.top = SKIRT_TOP
        self.waist_z = self.measure_waist()
        rim = max(boundary_loops(self.bm_body), key=lambda lp: sum(v.co.z for v in lp) / len(lp))
        self.neck_c = sum((v.co for v in rim), Vector()) / len(rim)
        self.rim = [(self.theta(v.co), v.co.z) for v in rim]
        self.rim.sort()
        log("rim: %d points, z front %.3f back %.3f, center %s" % (
            len(rim), self.rim_z(0.0), self.rim_z(math.pi), tuple(round(x, 3) for x in self.neck_c)))

    def measure_waist(self):
        """Height of the narrowest part of the torso (the cinched sash sits there)."""
        best = None
        for k in range(48):
            z = 0.97 + k * 0.005
            xs = [abs(v.co.x) for v in self.bm_body.verts if abs(v.co.z - z) < 0.003 and abs(v.co.x) < 0.25]
            if xs:
                w = max(xs)
                if best is None or w < best[1]:
                    best = (z, w)
        log("waist: z %.3f, half width %.3f" % best)
        return best[0]

    def theta(self, co):
        d = co - self.neck_c
        return math.atan2(d.x, -d.y)   # 0 front, +pi/2 the hunter's left

    def rim_z(self, th):
        """The face's neck edge height at angle th, interpolated between its 48 points (taking the
        nearest point made the collar cut a staircase) and averaged with its neighbours."""
        if not hasattr(self, "_rim_smooth"):
            zs = [z for _, z in self.rim]
            n = len(zs)
            self._rim_smooth = [sum(zs[(i + k) % n] for k in range(-2, 3)) / 5 for i in range(n)]
        angs, zs = [a for a, _ in self.rim], self._rim_smooth
        n = len(angs)
        th = math.remainder(th, 2 * math.pi)
        for i in range(n):
            a0, a1 = angs[i], angs[(i + 1) % n] + (2 * math.pi if i == n - 1 else 0)
            t = th if th >= a0 else th + 2 * math.pi
            if a0 <= t <= a1:
                f = (t - a0) / (a1 - a0) if a1 > a0 else 0.0
                return zs[i] * (1 - f) + zs[(i + 1) % n] * f
        return zs[0]

    def collar_z(self, th):
        return self.rim_z(th) - angle_blend(th, *COLLAR_DROP)

    def s_collar(self, co):
        c = self.neck_c
        r = math.hypot(co.x - c.x, co.y - c.y)
        return min(co.z - self.collar_z(self.theta(co)), COLLAR_R - r)

    def s_cuff(self, side, co):
        a, b = self.J[f"{side}_Forearm"], self.J[f"{side}_Hand"]
        ab = b - a
        t = (co - a).dot(ab) / ab.length_squared
        near = (co - (a + ab * t)).length < 0.12
        return (t - CUFF_T) if near and t > 0.5 else -1.0

    def s_skirt(self, co):
        if self.top is DRAPE_TOP and abs(co.x) > DRAPE_X:
            return -1.0
        return self.skirt_z(co) - co.z

    def covered(self, co, margin=0.0):
        """Under the fitted part (hidden in the previews; a material of its own in the game)."""
        return (self.s_collar(co) < -margin and self.s_cuff("L", co) < -margin
                and self.s_cuff("R", co) < -margin and self.s_skirt(co) < -margin)

    def build(self, fit):
        self.top = (DRAPE_TOP if fit in ("drape", "cinch") else SKIRT_TOP_SMOOTH if fit == "smooth"
                    else SKIRT_TOP)
        self.style = fit
        # "lines" is made as the user saw it first: from the body itself; the others from the copy
        # with the nipples and navel flattened
        src = self.bm_real if fit == "lines" else self.bm_body
        self.bvh = self.bvh_real if fit == "lines" else self.bvh_flat
        bm = src.copy()
        cuts = [self.s_collar, lambda co: self.s_cuff("L", co), lambda co: self.s_cuff("R", co), self.s_skirt]
        for s_of in cuts:
            split_along(bm, s_of)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if s_of(v.co) > 1e-7], context="VERTS")
        keep_largest(bm)
        small = [e for lp in boundary_loops(bm) if len(lp) <= 4 for v in lp for e in v.link_edges if e.is_boundary]
        bmesh.ops.holes_fill(bm, edges=list(set(small)), sides=4)   # slivers the cuts left
        bm.normal_update()
        for v in bm.verts:
            v.co += v.normal * GAP
        steps, rounds = FITS[fit]
        inflate_passes = INFLATE.get(fit, 0)
        for _ in range(rounds):
            if fit != "lines":
                taubin(bm.verts, steps)
                self.push_out(bm.verts, SMOOTH_GAP)
                continue
            else:
                inner = [v for v in bm.verts if not v.is_boundary]
                for _ in range(steps):
                    bmesh.ops.smooth_vert(bm, verts=inner, factor=0.5, use_axis_x=True, use_axis_y=True,
                                          use_axis_z=True)
            self.push_out(bm.verts, GAP)
        bm.normal_update()
        if inflate_passes:
            inflate(bm, inflate_passes)
        return bm

    def skirt_z(self, co):
        th = math.atan2(co.x, -co.y)
        return angle_blend(th, *self.top)

    def push_out(self, verts, gap):
        for v in verts:
            loc, n, _, _ = self.bvh.find_nearest(v.co)
            if loc is None:
                continue
            d = (v.co - loc).dot(n)
            if d < gap:
                v.co += n * (gap - d)


# ------------------------------------------------------------------ the skirt

def inflate(bm, passes):
    """Smoothing that only moves vertices outward (along their normal): the cloth bridges hollows
    and never sinks into one; the edges (collar, cuffs, skirt top) stay put."""
    verts = [v for v in bm.verts if not v.is_boundary]
    moved = 0
    for k in range(passes):
        if k % 4 == 0:
            bm.normal_update()
        moves = []
        for v in verts:
            nb = [e.other_vert(v).co for e in v.link_edges]
            avg = sum(nb, Vector()) / len(nb)
            d = avg - v.co
            if d.dot(v.normal) > 1e-7:
                moves.append((v, avg))
        for v, a in moves:
            v.co = a
        moved = len(moves)
    bm.normal_update()
    log(f"inflate: {passes} passes, {moved} vertices still moving out at the end")


def drape_profile(need, zs):
    """Cloth falling straight down from the top, pushed out by whatever sticks out above (never back
    in), its bends softened over DRAPE_SOFT like a stiff cloth."""
    env, m = [], 0.0
    for r in need:
        m = max(m, r)
        env.append(m)
    dz = abs(zs[1] - zs[0])
    w = max(1, int(DRAPE_SOFT / dz))
    for _ in range(4):
        sm = []
        for i in range(len(env)):
            lo, hi = max(0, i - w), min(len(env), i + w + 1)
            sm.append(sum(env[lo:hi]) / (hi - lo))
        env = [max(a, b) for a, b in zip(sm, need)]
        env[0] = need[0]
    return env


def cinch_profile(fit, c, d, zs, zb, r0, rh):
    """One column of the cinched drape: from the chest to the sash at zb a straight run puffed out
    by BLOUSE, pulled in to the body at the sash, then a straight line clearing the legs and a bell
    out to the hem. Returns the radii and the fold amplitude (0..1) per row."""
    ib = min(range(len(zs)), key=lambda i: abs(zs[i] - zb))
    raw = []
    for i, z in enumerate(zs):
        below = max(zb - z, 0.0)
        clear = GAP + 0.003 + (LEG_CLEAR - GAP - 0.003) * min(below / 0.10, 1.0) ** 2
        raw.append(clear_radius(fit, c, d, z, r0 * 0.6, clear) if i else r0)
    rb = raw[ib]
    col, amp = [], []
    for i in range(ib + 1):
        sb = i / max(ib, 1)
        col.append(max(r0 + (rb - r0) * sb + BLOUSE * math.sin(math.pi * sb), raw[i]))
        amp.append(0.35 * sb * sb)
    # below the sash: over the hips, then falling straight (as the drape), then the bell to the hem
    # (a straight line from the sash that cleared the hips carried on into a huge cone, 2026-10-04)
    span = zb - HEM_Z
    below = [rb] + [raw[i] + FOLD_AMP * ((zb - zs[i]) / span) ** 1.5 for i in range(ib + 1, len(zs))]
    env = drape_profile(below, zs[ib:])
    extra = max(rh - env[-1], 0.0)
    for i in range(ib + 1, len(zs)):
        u = (zb - zs[i]) / span
        col.append(env[i - ib] + BELL * extra * u * u)
        amp.append(0.35 * (1 - u) ** 2 + u ** 1.5)
    return col, amp


def clear_radius(fit, c, d, z, r_min, clear):
    """Smallest distance from the axis along d at height z that is `clear` outside the body.
    A point counts as inside only within 10 cm of where the search started (a face turned the
    wrong way must not send the search out forever)."""
    r = r_min
    for k in range(120):
        p = Vector((c.x + d.x * r, c.y + d.y * r, z))
        loc, n, _, dist = fit.bvh.find_nearest(p)
        inside = loc is not None and (p - loc).dot(n) < 0 and k < 50
        if loc is None or (not inside and dist >= clear):
            return r
        r += 0.002
    return r


def build_skirt(bm, fit, rng, style="hip"):
    """Rows hanging from the bodice's bottom edge to the hem; returns the grid of verts (rows x cols)
    and per column the angle around the hips."""
    loops = boundary_loops(bm)
    def centre(lp):
        return sum((v.co for v in lp), Vector()) / len(lp)
    ring = min((lp for lp in loops if abs(centre(lp).x) < 0.1), key=lambda lp: centre(lp).z)   # not the cuffs
    c = centre(ring)
    # columns at even angles (the ring's own verts can double back, and columns from them crossed):
    # the skirt's top row sits SEAM_DROP under the ring, bridged to it
    top, ang = [], []
    pts = [v.co for v in ring]
    for k in range(SKIRT_COLS):
        a = 2 * math.pi * k / SKIRT_COLS
        d = Vector((math.sin(a), -math.cos(a), 0))
        best = None
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            # where the vertical plane through the axis at angle a cuts segment p-q, on the d side
            n = Vector((d.y, -d.x, 0))
            sp, sq = (p - c).dot(n), (q - c).dot(n)
            if sp * sq > 0 or sp == sq:
                continue
            x = p.lerp(q, sp / (sp - sq))
            r = (x - c).to_2d().dot(d.to_2d())
            if r > 0 and (best is None or r > best[0]):
                best = (r, x)
        x = best[1] if best else c + d * 0.15
        top.append(bm.verts.new((x.x, x.y, x.z - SEAM_DROP)))
        ang.append(a)
    for k in range(SKIRT_COLS):
        bm.edges.new((top[k], top[(k + 1) % SKIRT_COLS]))
    ring_edges = list({e for v in ring for e in v.link_edges if e.is_boundary})
    top_edges = [e for v in top for e in v.link_edges]
    try:
        bmesh.ops.bridge_loops(bm, edges=list(set(ring_edges + top_edges)))
    except Exception as e:
        log("bridge failed:", e)
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    log("skirt top: %d columns, center %s" % (len(top), tuple(round(x, 3) for x in c)))
    grid = [top]
    cols = len(top)
    R = []
    for j, v in enumerate(top):
        zs = [v.co.z + (HEM_Z - v.co.z) * i / ROWS for i in range(ROWS + 1)]   # this column's rows
        d = Vector((v.co.x - c.x, v.co.y - c.y, 0))
        r0 = d.length
        d.normalize()
        rh = 1 / math.sqrt((d.x / HEM_R[0]) ** 2 + (d.y / HEM_R[1]) ** 2)
        a = ang[j]
        fold = (math.sin(FOLDS * a + ph[0]) * 0.65 + math.sin(FOLDS * 1.9 * a + ph[1]) * 0.25
                + math.sin(FOLDS * 0.5 * a + ph[2]) * 0.10)
        if style == "cinch":
            zb = fit.waist_z   # at the waist (user 2026-10-04: nobody cinches at the buttocks)
            col, fold_amp = cinch_profile(fit, c, d, zs, zb, r0, rh)
            R.append((d, [x + FOLD_AMP * fold * f for x, f in zip(col, fold_amp)], fold, v.co.z))
            continue
        need = [r0]
        for i in range(1, ROWS + 1):
            t = i / ROWS
            clear = GAP + (LEG_CLEAR - GAP) * min(t / 0.2, 1.0) ** 2   # hugging the body at the top
            need.append(clear_radius(fit, c, d, zs[i], r0, clear) + FOLD_AMP * t ** 1.5)
        if style == "drape":
            base = drape_profile(need, zs)
        else:
            # the straight line from the top that clears the legs (bind pose), folds included
            # (rows within K_FROM of the top left out: there the 2 mm search steps over a ~1 cm
            # drop made steep slopes; the waist softening and push-out take care of those rows)
            k = max((need[i] - r0) / (v.co.z - zs[i]) for i in range(1, ROWS + 1) if v.co.z - zs[i] >= K_FROM)
            k = max(k, 0.0)
            base = [r0 + k * (v.co.z - z) for z in zs]
        extra = max(rh - base[-1], 0.0)
        col = []
        for i in range(ROWS + 1):
            t = i / ROWS
            col.append(base[i] + BELL * extra * t ** 2 + FOLD_AMP * fold * t ** 1.5)
        R.append((d, col, fold, v.co.z))
    # smooth the line slopes across columns (one column's thigh must not make a ridge)
    for _ in range(6):
        new = []
        for j in range(cols):
            a, b = R[j - 1][1], R[(j + 1) % cols][1]
            new.append([R[j][1][0]] + [max(R[j][1][i], 0.25 * a[i] + 0.5 * R[j][1][i] + 0.25 * b[i])
                                       for i in range(1, ROWS + 1)])
        R = [(R[j][0], new[j], R[j][2], R[j][3]) for j in range(cols)]
    for i in range(1, ROWS + 1):
        row = []
        for j in range(cols):
            d, col, fold, z0 = R[j]
            t = i / ROWS
            z = z0 + (HEM_Z - z0) * t + 0.006 * fold * t ** 2   # the hem lifts a little at the fold crests
            row.append(bm.verts.new((c.x + d.x * col[i], c.y + d.y * col[i], z)))
        grid.append(row)
    fit.push_out([v for row in grid[:int(ROWS * 0.15)] for v in row], GAP)
    for i in range(ROWS):
        a, b = grid[i], grid[i + 1]
        for j in range(cols):
            k = (j + 1) % cols
            try:
                bm.faces.new((a[j], a[k], b[k], b[j]))
            except ValueError:
                pass
    bm.normal_update()
    return grid, ang, c


def soften_waist(bm, fit):
    """Round off the corner where the fitted part meets the skirt (cloth bridges it)."""
    def w(v):
        if fit.top is DRAPE_TOP and abs(v.co.x) > DRAPE_X:
            return 0.0
        dz = v.co.z - fit.skirt_z(v.co)
        if dz > 0:
            return max(0.0, 1 - dz / 0.07)
        return max(0.0, 1 - (-dz) / 0.12)
    band = [v for v in bm.verts if w(v) > 0]
    for _ in range(3):
        taubin(band, 30, weight=w)
        fit.push_out(band, GAP)
    bm.normal_update()


# ------------------------------------------------------------------ gold work

BAND_W = {"collar": 0.032, "cuff": 0.026, "hem": 0.040}   # m (DESIGN.md: a wide gold band at the collar)
LIFT = 0.0012          # m the gold sits off the cloth
SCROLL = 0.046         # m: one wave of the scroll stem along a band


class Surface:
    """Snapping onto the robe, the normal turned away from the body."""
    def __init__(self, bm, fit):
        self.bvh = BVHTree.FromBMesh(bm)
        self.fit = fit

    def snap(self, p, lift=0.0):
        loc, n, _, _ = self.bvh.find_nearest(p)
        if loc is None:
            return p, Vector((0, 0, 1))
        q, _, _, _ = self.fit.bvh_real.find_nearest(loc)
        if q is not None and n.dot(loc - q) < 0:
            n = -n
        return loc + n * lift, n


def resample_closed(pts, step):
    pts = list(pts) + [pts[0]]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seg)
    n = max(8, int(total / step))
    out, acc, i = [], 0.0, 0
    for k in range(n):
        target = total * k / n
        while i < len(seg) - 1 and acc + seg[i] < target:
            acc += seg[i]
            i += 1
        f = (target - acc) / seg[i] if seg[i] else 0.0
        out.append(pts[i].lerp(pts[i + 1], f))
    return out, total


def smooth_closed(pts, iters):
    for _ in range(iters):
        n = len(pts)
        pts = [(pts[k - 1] + pts[k] * 2 + pts[(k + 1) % n]) / 4 for k in range(n)]
    return pts


class Band:
    """A strip on the robe along a closed edge: s runs along the edge (m), v away from it into the
    cloth (m), marched over the surface; pt(s, v, lift) is on the cloth."""
    def __init__(self, edge, inward, width, surf, step=0.004, reach=None, smooth=4):
        pts, self.L = resample_closed(edge, step)
        pts = [surf.snap(p)[0] for p in smooth_closed(pts, smooth)]
        self.n, self.W, self.surf = len(pts), width, surf
        reach = max(reach or width, width)
        self.dv = width / max(2, int(width / 0.004))
        self.K = int(round(reach / self.dv))
        rows = [pts]
        for k in range(self.K):
            row = []
            for p in rows[-1]:
                _, nrm = surf.snap(p)
                d = inward(p)
                d = (d - nrm * nrm.dot(d)).normalized()
                row.append(surf.snap(p + d * self.dv)[0])
            rows.append(row)
        self.rows = rows

    def raw(self, s, v):
        x = (s / self.L) * self.n
        i0 = int(math.floor(x)) % self.n
        i1, fx = (i0 + 1) % self.n, x - math.floor(x)
        y = min(max(v / self.dv, 0.0), self.K - 1e-6)
        k0 = int(y)
        fy = y - k0
        a = self.rows[k0][i0].lerp(self.rows[k0][i1], fx)
        b = self.rows[k0 + 1][i0].lerp(self.rows[k0 + 1][i1], fx)
        return a.lerp(b, fy)

    def pt(self, s, v, lift=LIFT):
        return self.surf.snap(self.raw(s, v), lift)[0]

    def s_at(self, test):
        """s of the edge point that maximises test(point)."""
        i = max(range(self.n), key=lambda i: test(self.rows[0][i]))
        return self.L * i / self.n


def tube(name, pts, r, color, closed=False, radii=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for k, (pt, co) in enumerate(zip(sp.points, pts)):
        pt.co = (co[0], co[1], co[2], 1.0)
        pt.radius = radii[k] if radii else 1.0
    sp.use_cyclic_u = closed
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.color = color
    return ob


def solid_band(name, band, v0, v1, lift=LIFT, thick=0.0016):
    bm = bmesh.new()
    K = max(2, int((v1 - v0) / 0.004))
    grid = [[bm.verts.new(band.pt(band.L * i / band.n, v0 + (v1 - v0) * k / K, lift)) for i in range(band.n)]
            for k in range(K + 1)]
    for k in range(K):
        for i in range(band.n):
            j = (i + 1) % band.n
            bm.faces.new((grid[k][i], grid[k][j], grid[k + 1][j], grid[k + 1][i]))
    ob = mesh_object(name, bm, COL["gold"])
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness = thick
    m.offset = 0.0
    return ob


def rail(name, band, v, r, lift=LIFT):
    pts = [band.pt(band.L * i / band.n, v, lift + r * 0.6) for i in range(band.n)]
    return tube(name, pts, r, COL["gold"], closed=True)


def scroll_run(name, band, v0, v1, r=0.0015, lam=SCROLL, lift=LIFT):
    """A wavy stem between v0 and v1 with a curl leaving it at every crossing (卷草), all round."""
    reps = max(2, round(band.L / lam))
    lam = band.L / reps
    mid, amp = (v0 + v1) / 2, (v1 - v0) * 0.30
    N = reps * 24
    stem = [band.pt(band.L * k / N, mid + amp * math.sin(2 * math.pi * k / 24), lift + r) for k in range(N)]
    objs = [tube(name + "_stem", stem, r, COL["gold"], closed=True)]
    vpts, _ = volute(lam * 0.62, 1.15, curl_start=0.35, n=40)
    for m in range(reps * 2):
        sgn = 1 if m % 2 == 0 else -1
        s0 = lam * m / 2
        h = math.radians(55) * sgn
        pts, radii = [], []
        for q, (x, y) in enumerate(vpts):
            yy0 = -y * sgn
            xx = x * math.cos(h) - yy0 * math.sin(h)
            yy = x * math.sin(h) + yy0 * math.cos(h)
            vv = min(max(mid + yy * 0.55, v0 + r), v1 - r)
            pts.append(band.pt(s0 + xx * 0.9, vv, lift + r))
            radii.append(1.0 - 0.55 * q / len(vpts))
        objs.append(tube(f"{name}_c{m}", pts, r, COL["gold"], radii=radii))
    return objs


def droplet(name, center, size, color):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=size)
    for v in bm.verts:
        if v.co.z > 0:
            v.co.z *= 1.6   # a drop hanging from its tip
        v.co += center
    return mesh_object(name, bm, color)


def ring(name, center, radius, axis, r, color):
    axis = axis.normalized()
    u = axis.orthogonal().normalized()
    w = axis.cross(u)
    pts = [center + (u * math.cos(a) + w * math.sin(a)) * radius for a in (2 * math.pi * k / 32 for k in range(32))]
    return tube(name, pts, r, color, closed=True)


def body_ring(surf, c, z_of, lift, n=160):
    """A closed path round the robe at height z_of(angle), on the cloth."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        d = Vector((math.sin(a), -math.cos(a), 0))
        z = z_of(a)
        o = Vector((c.x, c.y, z)) + d * 0.8
        hit = surf.bvh.ray_cast(o, -d)
        p = hit[0] if hit[0] is not None else Vector((c.x, c.y, z)) + d * 0.2
        pts.append(surf.snap(p, lift)[0])
    return pts


def vine(name, mapper, origin, heading, length, turns, r, side_curls):
    """A stem rolling into a volute, with side curls peeling off; mapper(x, y) -> 3D on the cloth."""
    pts2, ths = volute(length, turns, curl_start=0.55, bend=0.25 * (1 if turns > 0 else -1), n=90)
    h = math.radians(heading)
    P = [(origin[0] + x * math.cos(h) - y * math.sin(h), origin[1] + x * math.sin(h) + y * math.cos(h)) for x, y in pts2]
    objs = [tube(name, [mapper(x, y) for x, y in P], r, COL["gold"],
                 radii=[1.0 - 0.6 * q / len(P) for q in range(len(P))])]
    for k, (u, sgn, scale) in enumerate(side_curls):
        i = int(u * (len(P) - 1))
        hh = math.degrees(h + ths[i]) + sgn * 50
        objs += vine(f"{name}_s{k}", mapper, P[i], hh, length * scale, 1.1 * sgn, r * (1 - 0.5 * u), [])
    return objs


def vines(bands, surf, grid):
    """C: scroll vines embroidered up from the hem, up the forearms and down from the collar."""
    objs = []
    rows, cols = len(grid), len(grid[0])
    P = [[v.co.copy() for v in row] for row in grid]
    rowlen = (P[-2][0] - P[-1][0]).length

    def skirt_mapper(j0):
        def m(x, y):   # x around (m), y up from the hem band (m)
            i = rows - 1 - (BAND_W["hem"] + 0.012 + y) / rowlen
            i = min(max(i, 0.0), rows - 1.001)
            i0 = int(i)
            span = (P[i0][1] - P[i0][0]).length
            j = j0 + x / span
            ja = int(math.floor(j)) % cols
            jb, fj, fi = (ja + 1) % cols, j - math.floor(j), i - i0
            a = P[i0][ja].lerp(P[i0][jb], fj)
            b = P[i0 + 1][ja].lerp(P[i0 + 1][jb], fj)
            return surf.snap(a.lerp(b, fi), LIFT + 0.0012)[0]
        return m
    rng = random.Random(3)
    for k in range(10):
        j0 = cols * (k + rng.uniform(-0.15, 0.15)) / 10
        t = 1.15 if k % 2 else -1.15
        objs += vine(f"vine{k}", skirt_mapper(j0), (0.0, 0.0), 90 + rng.uniform(-12, 12), rng.uniform(0.26, 0.40), t,
                     0.0016, [(0.3, 1, 0.38), (0.55, -1, 0.32), (0.75, 1, 0.25)])
    for name, b in bands:
        if name.startswith("cuff"):
            for k in range(3):
                s0 = b.L * k / 3

                def m(x, y, b=b, s0=s0):
                    return b.surf.snap(b.raw(s0 + x, b.W + 0.008 + y), LIFT + 0.0012)[0]
                objs += vine(f"{name}_v{k}", m, (0.0, 0.0), 90, 0.11, 1.0 if k % 2 else -1.0, 0.0013, [(0.45, 1, 0.4)])
        if name == "collar":
            s_front = b.s_at(lambda p: -p.y - abs(p.x) * 3)
            for sgn in (1, -1):
                def m(x, y, b=b, sgn=sgn):
                    return b.surf.snap(b.raw(s_front + sgn * x, b.W + 0.006 + y), LIFT + 0.0012)[0]
                objs += vine(f"yoke{sgn}", m, (0.006, 0.0), 75, 0.13, -1.2, 0.0014, [(0.35, 1, 0.45), (0.6, -1, 0.35)])
                objs += vine(f"yokeb{sgn}", m, (0.05, 0.0), 80, 0.08, 1.1, 0.0012, [(0.5, -1, 0.4)])
    return objs


def belt(surf, grid, loose=False):
    """D (the user's idea, 2026-10-04): a sash of gold rings where the fitted part meets the skirt,
    so the gathering there reads as the sash's; two cords hang in front, each ending in a gold drop
    held in a small gold ring (the floating-phial motif, in gold: all the jewellery is gold)."""
    objs = []
    c = Vector((0.0, 0.009, 0.0))
    heights = SASH_LOOSE if loose else (surf.fit.waist_z,) * 3 if surf.fit.style == "cinch" else SKIRT_TOP
    path = body_ring(surf, c, lambda a: angle_blend(a, *heights) + 0.004, 0.0045)
    path = smooth_closed(path, 3)
    n = len(path)
    for k, ph in enumerate((0.0, math.pi)):   # two twisted cords
        pts, acc = [], 0.0
        for i in range(n):
            t = (path[(i + 1) % n] - path[i - 1]).normalized()
            out = surf.snap(path[i])[1]
            side = t.cross(out)
            a = ph + 2 * math.pi * acc / 0.028
            pts.append(path[i] + side * (math.cos(a) * 0.004) + out * (math.sin(a) * 0.0025))
            acc += (path[(i + 1) % n] - path[i]).length
        objs.append(tube(f"belt_cord{k}", pts, 0.0019, COL["gold"], closed=True))
    for i in range(0, n, 4):   # a small gold ring every ~4 cm
        t = (path[(i + 1) % n] - path[i - 1]).normalized()
        objs.append(ring(f"belt_ring{i}", path[i], 0.0085, t, 0.0013, COL["gold"]))
    front = min(range(n), key=lambda i: path[i].y + abs(path[i].x) * 4)
    for sgn, length in ((1, 0.30), (-1, 0.36)):
        start = path[(front + sgn * 3) % n]
        pts = []
        for q in range(40):
            f = q / 39
            p = start + Vector((sgn * 0.012 * math.sin(f * 2.2), 0, -length * f))
            pts.append(surf.snap(p, 0.006)[0])
        objs.append(tube(f"hang{sgn}_a", pts, 0.0016, COL["gold"]))
        objs.append(tube(f"hang{sgn}_b", [p + Vector((0.0025 * math.sin(q * 0.9), 0, 0)) for q, p in enumerate(pts)],
                         0.0012, COL["gold"]))
        end = pts[-1] + Vector((0, -0.004, -0.014))   # all the jewellery gold (user 2026-10-04)
        objs.append(droplet(f"drop{sgn}", end, 0.0075, COL["gold"]))
        objs.append(ring(f"halo{sgn}", end + Vector((0, 0, 0.002)), 0.016, Vector((0, 1, 0)), 0.0014, COL["gold"]))
    return objs


def gold_work(version, bm, grid, fit, collar_kind=None):
    if version == "N":   # plain: the fitted robes have no jewellery (user 2026-10-04)
        return []
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    surf = Surface(bm, fit)
    J = fit.J
    loops = boundary_loops(bm)

    def centre(lp):
        return sum((v.co for v in lp), Vector()) / len(lp)
    loops = [lp for lp in loops if len(lp) > 20]   # not the slivers the cuts left
    collar = max(loops, key=lambda lp: centre(lp).z)
    cuffs = [lp for lp in loops if abs(centre(lp).x) > 0.3 and len(lp) > 10]
    down, up = Vector((0, 0, -1)), Vector((0, 0, 1))
    sc = 0.6 if version == "D" else 1.0
    reach = {"collar": 0.20, "cuff": 0.16, "hem": 0.0} if version == "C" else {}
    bands = [("collar", Band([v.co for v in collar], lambda p: down, BAND_W["collar"] * sc, surf,
                             reach=reach.get("collar")))]
    for lp in cuffs:
        side = "L" if centre(lp).x > 0 else "R"
        back = (J[f"{side}_Forearm"] - J[f"{side}_Hand"]).normalized()
        bands.append(("cuff" + side, Band([v.co for v in lp], lambda p, back=back: back, BAND_W["cuff"] * sc, surf,
                                          reach=reach.get("cuff"))))
    bands.append(("hem", Band([v.co for v in grid[-1]], lambda p: up, BAND_W["hem"] * sc, surf)))
    objs = []
    if collar_kind:   # the broad collar replaces the collar band
        objs += broad_collar(collar_kind, bm, fit, surf)
        bands_drawn = [nb for nb in bands if nb[0] != "collar"]
    else:
        bands_drawn = bands
    for name, b in bands_drawn:
        if version in ("A", "D"):
            objs.append(solid_band(f"{name}_band", b, 0.0, b.W))
            objs.append(rail(f"{name}_edge", b, 0.0, 0.0024))
            objs.append(rail(f"{name}_inner", b, b.W, 0.0012))
        else:
            objs.append(rail(f"{name}_edge", b, 0.0, 0.0022))
            objs.append(rail(f"{name}_inner", b, b.W, 0.0014))
            objs += scroll_run(f"{name}_scroll", b, 0.004, b.W - 0.003)
    if version == "C":
        objs += vines(bands, surf, grid)
    if version == "D":
        objs += belt(surf, grid, loose=fit.style == "drape")
    return objs


# ------------------------------------------------------------------ broad collar (寬領)

# User 2026-10-04: the collar wants "a big piece of noble gold jewellery" that covers; reference an
# Egyptian broad collar (usekh: rows of beads, falcon-head terminals, a fringe of drops) "but all
# gold, not so many colours, the shape is good". So: rows of different gold textures instead of
# colours; worn as a whole ring round the neck (laid flat a usekh is a crescent, Ranni's sign);
# the outer fringe of drops answers the circlet's drop.
#   甲 beads   rows of radial gold tube beads between rails (closest to the reference)
#   乙 leaves  overlapping gold leaves in rows, like scales (the most covering)
#   丙 scrolls openwork gold scrolls between rails (lighter)
#   丁 strands the circlet's motif radiating: strands twisting into bundles that split in three
COLLARS = {"beads": "甲", "leaves": "乙", "scrolls": "丙", "strands": "丁"}
# m out from the neckline: front (down the chest) / shoulders / back (user 2026-10-04 on 丁: "smaller,
# not out toward the armpits" -> this; was 0.125 / 0.085 / 0.075. Tried 0.065 / 0.038 / 0.048 too
# ("covering part of the collarbones"), the user went back to this one: "this is good")
YOKE_W = (0.095, 0.055, 0.065)
YOKE_LIFT = 0.0025               # m the plate sits off the cloth


def yoke(bm, fit, surf):
    """The collar's own (s, f) space: s along the neckline (m), f 0 at the neckline to 1 at the outer
    edge, marched outward over the robe (round the neck and down)."""
    loops = [lp for lp in boundary_loops(bm) if len(lp) > 20]
    collar = max(loops, key=lambda lp: sum(v.co.z for v in lp) / len(lp))
    nc = fit.neck_c

    def outward(p):
        r = Vector((p.x - nc.x, p.y - nc.y, 0))
        if r.length < 1e-6:
            r = Vector((0, -1, 0))
        return r.normalized() + Vector((0, 0, -0.55))
    band = Band([v.co for v in collar], outward, 0.02, surf, reach=max(YOKE_W) + 0.035, smooth=14)

    def wmax(s):
        p = band.raw(s, 0.0)
        return angle_blend(fit.theta(p), *YOKE_W)

    def pt(s, f, lift=YOKE_LIFT):
        return band.pt(s, f * wmax(s), lift)

    def normal(s, f):
        return surf.snap(band.raw(s, f * wmax(s)))[1]
    band.wmax, band.fpt, band.fnormal = wmax, pt, normal
    return band


def plate(name, y, f0, f1, lift=YOKE_LIFT, thick=0.002):
    bm = bmesh.new()
    K = 14
    grid = [[bm.verts.new(y.fpt(y.L * i / y.n, f0 + (f1 - f0) * k / K, lift)) for i in range(y.n)] for k in range(K + 1)]
    for k in range(K):
        for i in range(y.n):
            j = (i + 1) % y.n
            bm.faces.new((grid[k][i], grid[k][j], grid[k + 1][j], grid[k + 1][i]))
    ob = mesh_object(name, bm, COL["gold"])
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness = thick
    m.offset = 0.0
    return ob


def yrail(name, y, f, r, lift=YOKE_LIFT):
    pts = [y.fpt(y.L * i / y.n, f, lift + r * 0.7) for i in range(y.n)]
    return tube(name, pts, r, COL["gold"], closed=True)


def cylinder_into(bm, a, b, r, seg=8):
    ax = (b - a)
    if ax.length < 1e-6:
        return
    ax.normalize()
    u = ax.orthogonal().normalized()
    w = ax.cross(u)
    ring_a = [bm.verts.new(a + (u * math.cos(t) + w * math.sin(t)) * r) for t in (2 * math.pi * k / seg for k in range(seg))]
    ring_b = [bm.verts.new(b + (u * math.cos(t) + w * math.sin(t)) * r) for t in (2 * math.pi * k / seg for k in range(seg))]
    for k in range(seg):
        bm.faces.new((ring_a[k], ring_a[(k + 1) % seg], ring_b[(k + 1) % seg], ring_b[k]))
    bm.faces.new(list(reversed(ring_a)))
    bm.faces.new(ring_b)


def bead_row(name, y, f0, f1, pitch, r, lift=YOKE_LIFT):
    """Gold tube beads lying radially between fractions f0 and f1, one every `pitch` m."""
    bm = bmesh.new()
    n = int(y.L / pitch)
    for k in range(n):
        s = y.L * k / n
        a, b = y.fpt(s, f0 + 0.04 * (f1 - f0), lift + r), y.fpt(s, f1 - 0.04 * (f1 - f0), lift + r)
        cylinder_into(bm, a, b, r)
    return mesh_object(name, bm, COL["gold"], smooth=False)


def drop_fringe(name, y, pitch, length, f=1.0, lift=YOKE_LIFT):
    """Gold drops hanging off the outer edge, tip up, pointing on outward and down the cloth."""
    bm = bmesh.new()
    n = int(y.L / pitch)
    for k in range(n):
        s = y.L * (k + 0.5) / n
        top = y.fpt(s, f, lift + 0.001)
        p2 = y.pt(s, min(y.wmax(s) + length, y.K * y.dv - 1e-4), lift + 0.0015)
        ax = (p2 - top)
        L = ax.length
        ax.normalize()
        nrm = y.fnormal(s, f)
        u = ax.cross(nrm).normalized()
        sb = bmesh.new()
        bmesh.ops.create_uvsphere(sb, u_segments=12, v_segments=8, radius=1.0)
        for v in sb.verts:   # x across, y along (0 = top .. 1 = round end), z off the cloth
            x, yy, z = v.co
            t = (1 - yy) / 2          # 0 at the top point, 1 at the round end
            width = L * 0.30 * math.sin(math.pi * min(t, 0.999) ** 0.75) if t < 0.999 else 0.0
            v.co = top + ax * (t * L) + u * (x * width) + nrm * (abs(z) * width * 0.55 + 0.0005)
        me = bpy.data.meshes.new("tmp")
        sb.to_mesh(me)
        sb.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    return mesh_object(name, bm, COL["gold"])


def leaf_rows(name, y, rows, lift=YOKE_LIFT):
    """Overlapping gold leaves, pointed outward; the inner rows lie over the outer ones."""
    objs = []
    for ri, (f0, f1, pitch) in enumerate(rows):
        bm = bmesh.new()
        n = int(y.L / pitch)
        layer = lift + 0.0012 * (len(rows) - ri)
        for k in range(n):
            s0 = y.L * (k + 0.5 * (ri % 2)) / n
            NU, NV = 6, 10
            grid = []
            for jv in range(NV + 1):
                t = jv / NV
                f = f0 + (f1 - f0) * t
                half = pitch * 0.40 * math.sin(math.pi * min(t * 0.92 + 0.08, 1.0)) ** 0.7   # gaps between leaves
                row = []
                for ju in range(NU + 1):
                    x = (ju / NU * 2 - 1) * half
                    bulge = 0.0012 * (1 - (ju / NU * 2 - 1) ** 2) * math.sin(math.pi * t)
                    row.append(bm.verts.new(y.fpt(s0 + x, f, layer + bulge + 0.0008 * t)))
                grid.append(row)
            for jv in range(NV):
                for ju in range(NU):
                    bm.faces.new((grid[jv][ju], grid[jv][ju + 1], grid[jv + 1][ju + 1], grid[jv + 1][ju]))
        ob = mesh_object(f"{name}{ri}", bm, COL["gold"])
        m = ob.modifiers.new("solid", "SOLIDIFY")
        m.thickness = 0.0009
        objs.append(ob)
        ribs = []
        for k in range(n):
            s0 = y.L * (k + 0.5 * (ri % 2)) / n
            ribs.append(tube(f"{name}{ri}_rib{k}", [y.fpt(s0, f0 + (f1 - f0) * t, layer + 0.0022) for t in (0.1, 0.4, 0.7, 0.92)],
                             0.0007, COL["gold"]))
        objs += ribs
    return objs


class FracBand:
    """A band between two fractions of the yoke, for scroll_run (s in m, v in m across)."""
    def __init__(self, y, f0, f1):
        self.y, self.f0, self.f1, self.L, self.n = y, f0, f1, y.L, y.n
        self.W = 0.02

    def pt(self, s, v, lift=LIFT):
        f = self.f0 + (self.f1 - self.f0) * min(max(v / self.W, 0.0), 1.0)
        return self.y.fpt(s, f, lift + YOKE_LIFT)


def strand_rays(name, y, n_rays=26, lift=YOKE_LIFT):
    """The circlet's motif: three strands twisting round each other out from the neckline, the
    bundle splitting into three prongs that end in buds."""
    objs = []
    for k in range(n_rays):
        s0 = y.L * k / n_rays
        span = y.L / n_rays
        for st in range(3):
            pts, radii = [], []
            for q in range(36):
                t = q / 35
                f = 0.06 + 0.62 * t
                tw = math.sin(2 * math.pi * (2.2 * t) + st * 2 * math.pi / 3) * span * 0.10
                pts.append(y.fpt(s0 + tw, f, lift + 0.0016 + 0.0008 * math.cos(2 * math.pi * 2.2 * t + st * 2.1)))
                radii.append(1.0 - 0.25 * t)
            for q in range(1, 16):   # the prong
                t = q / 15
                f = 0.68 + 0.24 * t
                fan = (st - 1) * span * 0.32 * math.sin(math.pi / 2 * t)
                curl = (st - 1) * span * 0.06 * math.sin(math.pi * t)
                pts.append(y.fpt(s0 + fan + curl, f, lift + 0.0016))
                radii.append(0.75 - 0.3 * t)
            objs.append(tube(f"{name}{k}_{st}", pts, 0.0016, COL["gold"], radii=radii))
            end = pts[-1]
            objs.append(droplet(f"{name}{k}_{st}_bud", end, 0.0028, COL["gold"]))
    return objs


def broad_collar(kind, bm, fit, surf):
    y = yoke(bm, fit, surf)
    objs = [yrail("yk_inner", y, 0.0, 0.0034)]   # the rolled inner edge covers the robe's neckline
    if kind == "beads":
        objs.append(plate("yk_plate", y, 0.0, 1.0))
        for i, (f0, f1) in enumerate(((0.06, 0.26), (0.30, 0.50), (0.54, 0.74), (0.78, 0.96))):
            objs.append(bead_row(f"yk_beads{i}", y, f0, f1, 0.0125 + 0.002 * i, 0.0024))   # spaced out (user: too dense)
        for i, f in enumerate((0.28, 0.52, 0.76)):
            objs.append(yrail(f"yk_rail{i}", y, f, 0.0016))
        objs.append(yrail("yk_outer", y, 0.985, 0.0022))
    elif kind == "leaves":
        objs.append(plate("yk_plate", y, 0.0, 0.5))
        objs += leaf_rows("yk_leaf", y, ((0.58, 1.0, 0.034), (0.30, 0.72, 0.027), (0.04, 0.44, 0.021)))   # fewer, spaced
    elif kind == "scrolls":
        for i, f in enumerate((0.33, 0.66)):
            objs.append(yrail(f"yk_rail{i}", y, f, 0.0018))
        objs.append(yrail("yk_outer", y, 0.985, 0.0024))
        for i, (f0, f1) in enumerate(((0.04, 0.31), (0.35, 0.64), (0.68, 0.96))):
            objs += scroll_run(f"yk_scroll{i}", FracBand(y, f0, f1), 0.001, 0.019, r=0.0016, lam=0.034 + 0.008 * i)
    elif kind == "strands":
        objs.append(plate("yk_plate", y, 0.0, 0.62))
        objs.append(yrail("yk_rail", y, 0.62, 0.0018))
        objs += strand_rays("yk_ray", y, n_rays=18)
    objs.append(drop_fringe("yk_drops", y, 0.0105, 0.016, f=0.99 if kind != "strands" else 0.93))
    return objs


def cycles_materials():
    """Gold that reads as metal, for the collar close-ups (workbench draws flat colours)."""
    mats = {}
    def mat(name, color, metallic, rough, sss=0.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = color
        b.inputs["Metallic"].default_value = metallic
        b.inputs["Roughness"].default_value = rough
        if sss:
            b.inputs["Subsurface Weight"].default_value = sss
        return m
    mats["gold"] = mat("Gold", (0.95, 0.66, 0.24, 1), 1.0, 0.26)
    mats["robe"] = mat("Robe", (0.80, 0.74, 0.62, 1), 0.0, 0.85)
    mats["skin"] = mat("Skin", (0.80, 0.58, 0.48, 1), 0.0, 0.5, 0.15)
    mats["hair"] = mat("Hair", (0.78, 0.58, 0.26, 1), 0.0, 0.45)
    mats["circlet"] = mat("Circlet", (0.95, 0.72, 0.36, 1), 0.7, 0.3)
    return mats


def render_collar(out, stem, test):
    """Cycles close-ups of the neck: front, three-quarter, back three-quarter."""
    sc = bpy.context.scene
    mats = cycles_materials()
    for o in bpy.data.objects:
        if o.type not in ("MESH", "CURVE"):
            continue
        key = min(COL, key=lambda k: sum((a - b) ** 2 for a, b in zip(COL[k], o.color)))
        key = {"light": "gold"}.get(key, key)
        o.data.materials.clear()
        o.data.materials.append(mats[key])
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 16 if test else 64
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Filmic"
    sc.view_settings.look = "Medium High Contrast"
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.30, 0.28, 0.26, 1)   # for the metal to reflect
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5
    sc.world = world
    lights = []
    for name, loc, e, size in (("key", (-1.2, -2.2, 2.4), 160, 1.5), ("fill", (1.8, -1.6, 1.4), 50, 2.0),
                               ("rim", (0.5, 2.5, 2.2), 90, 1.5), ("back", (-1.5, 2.0, 1.6), 40, 2.0)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size = e, size
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        d = Vector((0, 0, 1.35)) - Vector(loc)
        lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        lights.append(lo)
    s = 300 if test else 800
    sc.render.resolution_x = sc.render.resolution_y = s
    cd = bpy.data.cameras.new("cc")
    cd.type = "ORTHO"
    cd.ortho_scale = 0.56
    cam = bpy.data.objects.new("cc", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    paths = []
    for name, az, z in (("front", 0, 1.36), ("front34", 35, 1.37), ("back34", 150, 1.40)):
        a = math.radians(az)
        cam.location = (4 * math.sin(a), -4 * math.cos(a), z + 0.35)
        cam.rotation_euler = (math.radians(85), 0, a)
        p = os.path.join(out, f"{stem}_{name}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    for o in lights + [cam]:
        bpy.data.objects.remove(o, do_unlink=True)
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    return paths


# ------------------------------------------------------------------ main

def scene_setup(test):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "OBJECT"
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.curvature_ridge_factor = 1.0
    sh.show_shadows = False
    sc.display.render_aa = "8" if test else "16"
    sc.view_settings.view_transform = "Standard"
    return sc


def render(out, stem, test):
    sc = bpy.context.scene
    w, h = (300, 560) if test else (600, 1100)
    sc.render.resolution_x, sc.render.resolution_y = w, h
    cd = bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cd.ortho_scale = 1.95
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    mid = 0.93
    paths = []
    for name, az in (("front", 0), ("front34", 35), ("side", 90), ("back", 180)):
        a = math.radians(az)
        cam.location = (4 * math.sin(a), -4 * math.cos(a), mid)
        cam.rotation_euler = (math.radians(90), 0, a)
        p = os.path.join(out, f"{stem}_{name}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    # close-up of the upper body (collar, cuffs, the sash at the hips)
    sc.render.resolution_x, sc.render.resolution_y = (h // 2, h // 2) if test else (900, 900)
    cd.ortho_scale = 1.0
    a = math.radians(28)
    cam.location = (4 * math.sin(a) + 0.08, -4 * math.cos(a), 1.13)
    cam.rotation_euler = (math.radians(90), 0, a)
    p = os.path.join(out, f"{stem}_close.png")
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    paths.append(p)
    bpy.data.objects.remove(cam, do_unlink=True)
    return paths


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = os.path.abspath(args[0])
    test = "test" in args
    versions = [a for a in args[1:] if a in ("A", "B", "C", "D", "N")] or ["A", "B", "C", "D"]
    full = "full" in args   # with a collar: the full-body views too
    fits = [a for a in args[1:] if a in FITS] or ["drape"]
    collars = [a.split(":", 1)[1] for a in args[1:] if a.startswith("collar:")]
    os.makedirs(out, exist_ok=True)
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable("re_mesh_editor", default_set=True)
    scene_setup(test)
    body, J = import_mesh(BODY, COL["skin"])
    log("body objects", len(body), "joints", len(J))
    for k in ("Head", "Neck_0", "L_UpperArm", "L_Forearm", "L_Hand", "Hip", "L_Thigh", "L_Knee", "L_Foot"):
        if k in J:
            log(k, tuple(round(x, 3) for x in J[k]))
    import_mesh(FACE, COL["skin"], drop=("eye", "mouth", "lash", "fakeao", "shadow", "cage", "brow"))
    import_mesh(HAIR, COL["hair"])
    circ, _ = import_mesh(CIRCLET, COL["circlet"])
    pivot = Vector((0, 0, 0.128))   # the circlet's size pivot, Head joint space (MiquellaLight_Character.lua)
    for o in circ:
        o.data.transform(Matrix.Translation(J["Head"] + pivot) @ Matrix.Scale(0.85, 4) @ Matrix.Translation(-pivot))
    fit = Fit(body, J)
    for o in body:   # the body under the fitted part pokes through the 4 mm gap: hidden here
        bb = bmesh.new()
        bb.from_mesh(o.data)
        bmesh.ops.delete(bb, geom=[x for x in bb.verts if fit.covered(x.co, 0.01)], context="VERTS")
        bb.to_mesh(o.data)
        bb.free()
    for f in fits:
        for v in versions:
            rng = random.Random(7)
            bm = fit.build(f)
            grid, ang, center = build_skirt(bm, fit, rng, style=f if f in ("drape", "cinch") else "hip")
            if f != "lines":
                soften_waist(bm, fit)
            if f in ("drape", "cinch"):
                # the 2 mm steps of the clearance search left ripples across the hanging cloth
                skirt = [v for row in grid[1:-1] for v in row]
                for _ in range(2):
                    taubin(skirt, 25)
                    fit.push_out(skirt, GAP)
                bm.normal_update()
            # one winding all over (the skirt's faces were made in loop order): mixed windings drew
            # black seams in Cycles where the skirt meets the fitted part
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            robe = mesh_object(f"Robe_{v}", bm, COL["robe"])
            for kind in collars or [None]:
                objs = [robe] + gold_work(v, bm, grid, fit, collar_kind=kind)
                if kind:
                    paths = render_collar(out, f"robe_{f}_{v}_collar_{kind}", test)
                    if full:
                        paths += render(out, f"robe_{f}_{v}_collar_{kind}", test)
                else:
                    paths = render(out, f"robe_{f}_{v}", test)
                log("rendered", paths)
                for o in objs[1:]:
                    bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.objects.remove(robe, do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "robe_designs.blend"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout.flush()
        os._exit(0)
