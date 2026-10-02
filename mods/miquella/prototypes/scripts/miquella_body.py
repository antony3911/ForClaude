"""Miquella's body for the game (character, 2026-10-02).

The game has no bare body to start from (the hunter's "innerwear" is a full outfit; research
notes section 18), so the body is MakeHuman's base mesh (CC0, github.com/makehumancommunity):
- shaped with its macro targets (adult, slender, androgynous: flat chest and stomach, narrow
  hips, little muscle; DESIGN / two-account notes, "體型") and a few detail targets;
- fitted onto the hunter's skeleton in its bind pose (A pose): MakeHuman's own rig and weights
  pose the mesh so every mapped bone runs between the game's joints (Copy Location + Stretch To);
- cut at the neck (the game's face mesh goes down to y 1.43 and stays), a plain underwear
  region as its own material (no anatomy, never shown bare: the robe goes on top).

Usage (bpy 4.5 with RE Mesh Editor in the user add-ons):
  python miquella_body.py preview <MakeHuman data dir> <game ch02_002_0002 .mesh> <out dir> [game face .mesh [other innerwear .mesh ...]]
      the variants side by side (and the game's hunter body / face if given: such a render has
      game models in it and stays out of the repo)
Variants: VARIANTS below.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
FILE_TO_BLENDER = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def log(msg):
    print(f"[body] {msg}", flush=True)


# ------------------------------------------------------------------ shape

# Macro values as MakeHuman's sliders (0..1; age 0.5 = 25 years, muscle / weight 0.5 = average),
# plus detail targets (file under targets/, weight).
COMMON_DETAILS = [
    ("torso/torso-vshape-decr", 0.6),             # no V-shaped torso
    ("torso/torso-muscle-pectoral-decr", 0.8),    # flat chest
    ("breast/nipple-point-decr", 1.0),
    ("breast/nipple-size-decr", 1.0),
    ("stomach/stomach-pregnant-decr", 0.5),       # flat stomach
    ("hip/hip-scale-horiz-decr", 0.35),           # narrow (male) pelvis
    ("neck/neck-scale-horiz-decr", 0.5),          # slender neck
]
VARIANTS = {
    "A": {"label": "A 纖細中性", "gender": 0.62, "muscle": 0.28, "weight": 0.30, "details": []},
    "B": {"label": "B 少年感", "gender": 0.90, "muscle": 0.45, "weight": 0.34, "details": []},
    "C": {"label": "C 柔和", "gender": 0.66, "muscle": 0.22, "weight": 0.44,
          "details": [("torso/torso-scale-horiz-decr", 0.2)]},
}
AGE = 0.5          # 25 years: adult proportions only
RACES = {"african": 1 / 3, "asian": 1 / 3, "caucasian": 1 / 3}


def three_way(v):
    """MakeHuman's split of a 0..1 slider into min / average / max weights."""
    if v < 0.5:
        return {"min": 1 - 2 * v, "average": 2 * v, "max": 0.0}
    return {"min": 0.0, "average": 2 - 2 * v, "max": 2 * v - 1}


def macro_targets(p):
    gender = {"female": 1 - p["gender"], "male": p["gender"]}
    age = {"young": 1.0}        # AGE 0.5 exactly: no baby / child / old targets
    muscle = {k + "muscle": w for k, w in three_way(p["muscle"]).items()}
    weight = {k + "weight": w for k, w in three_way(p["weight"]).items()}
    out = {}
    for g, wg in gender.items():
        for a, wa in age.items():
            for m, wm in muscle.items():
                for w, ww in weight.items():
                    out[f"macrodetails/universal-{g}-{a}-{m}-{w}"] = wg * wa * wm * ww
            for r, wr in RACES.items():
                out[f"macrodetails/{r}-{g}-{a}"] = wr * wg * wa
    out.update({name: w for name, w in COMMON_DETAILS + p["details"]})
    return {k: w for k, w in out.items() if w > 1e-4}


_target_cache = {}


def load_target(data, name):
    if name not in _target_cache:
        offs = []
        with open(os.path.join(data, "targets", name + ".target"), encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) == 4 and not line.startswith("#"):
                    offs.append((int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])))
        _target_cache[name] = offs
    return _target_cache[name]


# ------------------------------------------------------------------ MakeHuman data

def load_base(data):
    verts, uvs, faces, cur = [], [], [], None
    with open(os.path.join(data, "3dobjs", "base.obj"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                verts.append([float(t) for t in line.split()[1:4]])
            elif line.startswith("vt "):
                uvs.append([float(t) for t in line.split()[1:3]])
            elif line.startswith("g "):
                cur = line.split()[1]
            elif line.startswith("f ") and cur == "body":
                corner = [t.split("/") for t in line.split()[1:]]
                faces.append(([int(c[0]) - 1 for c in corner], [int(c[1]) - 1 for c in corner]))
    with open(os.path.join(data, "rigs", "default.mhskel"), encoding="utf-8") as f:
        skel = json.load(f)
    with open(os.path.join(data, "rigs", "default_weights.mhw"), encoding="utf-8") as f:
        weights = json.load(f)["weights"]
    return verts, uvs, faces, skel, weights


def shaped(data, verts, params):
    v = [list(p) for p in verts]
    for name, w in macro_targets(params).items():
        for i, dx, dy, dz in load_target(data, name):
            v[i][0] += w * dx
            v[i][1] += w * dy
            v[i][2] += w * dz
    return v


def mh_to_blender(p):
    """MakeHuman (decimeters, +Y up, +Z front) -> Blender (meters, +Z up, -Y front), like the game's files."""
    return Vector((p[0] * 0.1, -p[2] * 0.1, p[1] * 0.1))


def joint_positions(skel, pts):
    """Joint name -> mean of its reference vertices (pts already in Blender space)."""
    return {name: sum((pts[i] for i in idx), Vector()) / len(idx) for name, idx in skel["joints"].items()}


def aligned(skel, pts, G):
    """Move and scale the MakeHuman figure so its hip joints' midpoint sits on the game's and its
    neck base is at the game's Neck_0 height (the limbs are fitted bone by bone afterwards)."""
    J = joint_positions(skel, pts)
    mh_mid = (J["upperleg01.L____head"] + J["upperleg01.R____head"]) / 2
    game_mid = (G["L_Thigh"] + G["R_Thigh"]) / 2
    k = (G["Neck_0"].z - game_mid.z) / (J["neck01____head"].z - mh_mid.z)
    log(f"  scale {k:.4f} to the game's hip-to-neck height")
    return [game_mid + (p - mh_mid) * k for p in pts]


# ------------------------------------------------------------------ game skeleton

def enable_addon():
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)


IMPORT_OPTS = {"clearScene": False, "createCollections": True, "loadMaterials": False, "loadMDFData": False,
               "loadShellFur": False, "loadUnusedTextures": False, "loadUnusedProps": False,
               "useBackfaceCulling": False, "reloadCachedTextures": False, "mdfPath": "", "importAllLODs": False,
               "importBlendShapes": False, "rotate90": True, "mergeArmature": "", "importArmatureOnly": False,
               "mergeGroups": False, "importShadowMeshes": False, "importOcclusionMeshes": False,
               "importBoundingBoxes": False}


def import_game(path, keep_meshes):
    """Objects of a game .mesh (Blender space). Returns (armature, meshes)."""
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile
    before = set(bpy.data.objects)
    importREMeshFile(path, IMPORT_OPTS)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next((o for o in new if o.type == "ARMATURE"), None)
    meshes = []
    for o in new:
        if o.type != "MESH":
            continue
        names = " ".join(m.name.lower() for m in o.data.materials if m)
        if keep_meshes and not any(k in names for k in ("eye", "mouth", "lash", "fakeao", "shadow", "cage")):
            meshes.append(o)
        else:
            bpy.data.objects.remove(o, do_unlink=True)
    return arm, meshes


def game_joints(arm):
    """Bone name -> position in Blender space (from the file's world matrices)."""
    out = {}
    for b in arm.data.bones:
        m = b.get("reMeshWorldMatrix")
        if m is None:
            continue
        out[b.name] = FILE_TO_BLENDER @ Vector((m[3][0], m[3][1], m[3][2]))
    return out


# ------------------------------------------------------------------ fitting

def lerp_polyline(points, t):
    """Point at share t (0..1) of a polyline's length."""
    lens = [(points[i + 1] - points[i]).length for i in range(len(points) - 1)]
    total = sum(lens)
    d = t * total
    for i, L in enumerate(lens):
        if d <= L or i == len(lens) - 1:
            return points[i].lerp(points[i + 1], min(1.0, d / L if L else 0.0))
        d -= L
    return points[-1]


def chain_targets(J, G, bones, game_points):
    """Heads (and the last tail) of MakeHuman bones `bones`, spread over the game polyline by
    their share of the chain's length. Returns {bone: (head, tail)}."""
    pts = [J[b + "____head"] for b in bones] + [J[bones[-1] + "____tail"]]
    lens = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total, acc, shares = sum(lens), 0.0, [0.0]
    for L in lens:
        acc += L
        shares.append(acc / total)
    gp = [G[n] if isinstance(n, str) else n for n in game_points]
    placed = [lerp_polyline(gp, s) for s in shares]
    return {b: (placed[i], placed[i + 1]) for i, b in enumerate(bones)}


def extend(a, b, ratio):
    return b + (b - a) * ratio


def fit_targets(J, G):
    """Where each mapped MakeHuman bone's head and tail go, from the game's joints."""
    T = {}
    T.update(chain_targets(J, G, ["spine05", "spine04", "spine03", "spine02", "spine01"],
                           ["Spine_0", "Spine_1", "Spine_2", "Neck_0"]))
    T.update(chain_targets(J, G, ["neck01", "neck02", "neck03"], ["Neck_0", "Neck_1", "Head"]))
    head_len = (J["head____tail"] - J["head____head"]).length
    T["head"] = (G["Head"], G["Head"] + Vector((0, 0, head_len)))
    for s, S in (("L", "L_"), ("R", "R_")):
        T.update(chain_targets(J, G, [f"clavicle.{s}", f"shoulder01.{s}"], [S + "Shoulder", S + "UpperArm"]))
        T.update(chain_targets(J, G, [f"upperarm01.{s}", f"upperarm02.{s}"], [S + "UpperArm", S + "Forearm"]))
        T.update(chain_targets(J, G, [f"lowerarm01.{s}", f"lowerarm02.{s}"], [S + "Forearm", S + "Hand"]))
        T[f"pelvis.{s}"] = (G["Hip"], G[S + "Thigh"])
        T.update(chain_targets(J, G, [f"upperleg01.{s}", f"upperleg02.{s}"], [S + "Thigh", S + "Knee"]))
        T.update(chain_targets(J, G, [f"lowerleg01.{s}", f"lowerleg02.{s}"], [S + "Knee", S + "Foot"]))
        T[f"foot.{s}"] = (G[S + "Foot"], G[S + "Instep"])
        # Hand: the wrist points at the middle knuckle; metacarpals end at the knuckles.
        mh_w = J[f"wrist.{s}____head"]
        ratio = (J[f"wrist.{s}____tail"] - mh_w).length / (J[f"finger3-1.{s}____head"] - mh_w).length
        T[f"wrist.{s}"] = (G[S + "Hand"], G[S + "Hand"].lerp(G[S + "MiddleF1"], ratio))
        fingers = [("finger1", S + "Thumb", ""), ("finger2", S + "Index", "F"), ("finger3", S + "Middle", "F"),
                   ("finger4", S + "Ring", "F"), ("finger5", S + "Pinky", "F")]
        for k, (mh, game, f) in enumerate(fingers):
            g = [G[f"{game}{f}{i}"] for i in (1, 2, 3)]
            mh3 = (J[f"{mh}-3.{s}____tail"] - J[f"{mh}-3.{s}____head"]).length
            mh2 = (J[f"{mh}-2.{s}____tail"] - J[f"{mh}-2.{s}____head"]).length
            tip = extend(g[1], g[2], mh3 / mh2)
            T[f"{mh}-1.{s}"] = (g[0], g[1])
            T[f"{mh}-2.{s}"] = (g[1], g[2])
            T[f"{mh}-3.{s}"] = (g[2], tip)
            if k > 0:
                T[f"metacarpal{k}.{s}"] = (None, g[0])      # head follows the wrist
    return T


def build_mesh(name, verts, uvs, faces, weights):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [f[0] for f in faces])
    uv = me.uv_layers.new(name="UV")
    loop = 0
    for _, fuv in faces:
        for t in fuv:
            uv.data[loop].uv = uvs[t]
            loop += 1
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    for bone, pairs in weights.items():
        g = obj.vertex_groups.new(name=bone)
        for i, w in pairs:
            g.add([i], w, "REPLACE")
    for p in me.polygons:
        p.use_smooth = True
    return obj


def build_rig(skel, J):
    arm_data = bpy.data.armatures.new("MH_rig")
    arm = bpy.data.objects.new("MH_rig", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for name, b in skel["bones"].items():
        eb = arm_data.edit_bones.new(name)
        eb.head, eb.tail = J[b["head"]], J[b["tail"]]
        if (eb.tail - eb.head).length < 1e-5:
            eb.tail = eb.head + Vector((0, 0, 0.01))
    for name, b in skel["bones"].items():
        if b.get("parent"):
            arm_data.edit_bones[name].parent = arm_data.edit_bones[b["parent"]]
            arm_data.edit_bones[name].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    for b in arm_data.bones:
        b.inherit_scale = "NONE"
    return arm


def pose_to(arm, targets):
    """Copy Location onto each mapped head, Stretch To each mapped tail (no volume change)."""
    for name, (head, tail) in targets.items():
        pb = arm.pose.bones.get(name)
        if pb is None:
            log(f"  no bone {name}")
            continue
        if head is not None:
            e = bpy.data.objects.new(f"H_{name}", None)
            bpy.context.scene.collection.objects.link(e)
            e.location = head
            c = pb.constraints.new("COPY_LOCATION")
            c.target = e
        e = bpy.data.objects.new(f"T_{name}", None)
        bpy.context.scene.collection.objects.link(e)
        e.location = tail
        c = pb.constraints.new("STRETCH_TO")
        c.target = e
        c.volume = "NO_VOLUME"
        c.rest_length = pb.bone.length
    bpy.context.view_layer.update()


def bake(obj, arm):
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)


# ------------------------------------------------------------------ cut, materials

# The game's face mesh covers the neck from a slanted edge (front 1.43, nape 1.51, measured on
# ch00_000_0000): per 15-degree sector around the neck axis (Neck_0 -> Neck_1) our neck goes up
# NECK_OVERLAP past that edge, inside the face's neck (NECK_INSIDE of its radius), and meets
# its radius at the edge over NECK_BLEND below it, so no step and no gap shows.
NECK_OVERLAP, NECK_INSIDE, NECK_BLEND, NECK_SECTORS = 0.035, 0.95, 0.03, 24
NECK_CUT = 1.47          # without the face mesh: a level cut
UNDERWEAR = (0.78, 0.99, 0.30)   # boxer-brief band: lowest, highest, |x| limit (the hands hang beside it)


def neck_center(G, z):
    a, b = G["Neck_0"], G["Neck_1"]
    return a + (b - a) * ((z - a.z) / (b.z - a.z))


def polar(G, p):
    c = neck_center(G, p.z)
    dx, dy = p.x - c.x, p.y - c.y
    return (math.degrees(math.atan2(dx, -dy)) % 360.0), math.hypot(dx, dy), c


class FaceNeck:
    """The face mesh's neck: lowest point and outer radius per sector and 5 mm height bin."""
    def __init__(self, G, pts):
        self.G = G
        self.edge = [9.9] * NECK_SECTORS
        self.r = {}
        step = 360.0 / NECK_SECTORS
        for p in pts:
            if p.z > 1.60:
                continue
            ang, r, _ = polar(G, p)
            s = int(ang // step) % NECK_SECTORS
            self.edge[s] = min(self.edge[s], p.z)
            key = (s, round(p.z / 0.005))
            self.r[key] = max(self.r.get(key, 0.0), r)

    def _sector(self, s, z, what):
        if what == "edge":
            return self.edge[s]
        zb = round(z / 0.005)
        for d in (0, 1, -1, 2, -2):
            if (s, zb + d) in self.r:
                return self.r[(s, zb + d)]
        return None

    def at(self, ang, z, what):
        """Between the two nearest sector centers."""
        step = 360.0 / NECK_SECTORS
        f = ang / step - 0.5
        s0 = int(math.floor(f)) % NECK_SECTORS
        s1 = (s0 + 1) % NECK_SECTORS
        t = f - math.floor(f)
        a, b = self._sector(s0, z, what), self._sector(s1, z, what)
        if a is None or b is None:
            return a if b is None else b
        return a + (b - a) * t


def fit_neck(me, G, neck):
    for v in me.vertices:
        if v.co.z < 1.36 or v.co.z > 1.60:
            continue
        ang, r, c = polar(G, v.co)
        edge = neck.at(ang, 0, "edge")
        if v.co.z >= edge:
            rf = neck.at(ang, v.co.z, "r")
            if rf is None:
                continue
            nr = min(r, NECK_INSIDE * rf)
        elif v.co.z > edge - NECK_BLEND:
            rf = neck.at(ang, edge + 0.004, "r")
            if rf is None:
                continue
            t = (v.co.z - (edge - NECK_BLEND)) / NECK_BLEND
            t = t * t * (3 - 2 * t)
            nr = r + (NECK_INSIDE * rf - r) * t
        else:
            continue
        if r > 1e-6:
            k = nr / r
            v.co.x = c.x + (v.co.x - c.x) * k
            v.co.y = c.y + (v.co.y - c.y) * k


def cut_height(G, neck, p):
    """Past the face's edge by NECK_OVERLAP; the edge's highest point within two sectors, so a
    dip in it (the nape's middle) leaves no notch."""
    if neck is None:
        return NECK_CUT
    ang, _, _ = polar(G, p)
    step = 360.0 / NECK_SECTORS
    return max(neck.at((ang + d * step) % 360.0, 0, "edge") for d in (-2, -1, 0, 1, 2)) + NECK_OVERLAP


# Smooth body, no anatomical detail (design rule): the chest is smoothed flat around MakeHuman's
# nipple points (joint breast.*____tail, one vertex each).
SMOOTH_SPOTS = ("breast.L____tail", "breast.R____tail")
SMOOTH_RADIUS, SMOOTH_STEPS = 0.035, 40


def smooth_spots(obj, points):
    me = obj.data
    nbr = [[] for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices
        nbr[a].append(b)
        nbr[b].append(a)
    weight = {}
    for v in me.vertices:
        d = min((v.co - p).length for p in points)
        if d < SMOOTH_RADIUS:
            t = 1 - d / SMOOTH_RADIUS
            weight[v.index] = t * t * (3 - 2 * t)
    co = [v.co.copy() for v in me.vertices]
    for _ in range(SMOOTH_STEPS):
        new = {}
        for i, w in weight.items():
            if nbr[i]:
                avg = sum((co[j] for j in nbr[i]), Vector()) / len(nbr[i])
                new[i] = co[i].lerp(avg, 0.5 * w)
        for i, c in new.items():
            co[i] = c
    for i in weight:
        me.vertices[i].co = co[i]


def cut_and_paint(obj, G, skin, cloth, face_pts=None):
    me = obj.data
    neck = FaceNeck(G, face_pts) if face_pts else None
    if neck:
        fit_neck(me, G, neck)
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    above = [f for f in bm.faces if f.calc_center_median().z > 1.36
             and f.calc_center_median().z > cut_height(G, neck, f.calc_center_median())]
    bmesh.ops.delete(bm, geom=above, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    # Clean horizontal edges for the underwear band.
    low, high, xlim = UNDERWEAR
    for z in (low, high):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1))
    bm.to_mesh(me)
    bm.free()
    me.materials.clear()
    me.materials.append(skin)
    me.materials.append(cloth)
    for p in me.polygons:
        c = p.center
        p.material_index = 1 if low < c.z < high and abs(c.x) < xlim else 0
    log(f"{obj.name}: {len(me.vertices)} verts, {len(me.polygons)} faces after the cut")


def make_body(data, base, params, G, name, skin, cloth, face_pts=None):
    verts, uvs, faces, skel, weights = base
    v = aligned(skel, [mh_to_blender(p) for p in shaped(data, verts, params)], G)
    J = joint_positions(skel, v)
    obj = build_mesh(name, v, uvs, faces, weights)
    arm = build_rig(skel, J)
    pose_to(arm, fit_targets(J, G))
    bake(obj, arm)
    spots = [obj.data.vertices[skel["joints"][n][0]].co.copy() for n in SMOOTH_SPOTS]
    smooth_spots(obj, spots)
    for o in [o for o in bpy.data.objects if o.type == "EMPTY" or o is arm]:
        bpy.data.objects.remove(o, do_unlink=True)
    cut_and_paint(obj, G, skin, cloth, face_pts)
    return obj


# ------------------------------------------------------------------ preview

def preview(data, game_body, out, face=None, extra=()):
    import common as c
    c.reset_scene()
    enable_addon()
    arm, hunter = import_game(game_body, keep_meshes=True)
    for path in extra:
        a2, more = import_game(path, keep_meshes=True)
        hunter += more
        if a2:
            bpy.data.objects.remove(a2, do_unlink=True)
    G = game_joints(arm)
    log(f"game joints: {len(G)}; Head at {tuple(round(x, 3) for x in G['Head'])}")
    base = load_base(data)
    skin = c.make_material("Skin", "#F2DCD0", roughness=0.55, subsurface=0.2)
    cloth = c.make_material("Underwear", "#B8A27E", roughness=0.85)
    grey = c.make_material("GameHunter", "#6E6E74", roughness=0.7)
    faces_mat = c.make_material("GameFace", "#D9C7BC", roughness=0.6)
    for o in hunter:
        o.data.materials.clear()
        o.data.materials.append(grey)
    shown = list(hunter)
    face_objs = []
    if face:
        _, face_objs = import_game(face, keep_meshes=True)
        for o in face_objs:
            o.data.materials.clear()
            o.data.materials.append(faces_mat)
    face_pts = [o.matrix_world @ v.co for o in face_objs for v in o.data.vertices]
    gap = 1.5
    for k, (key, params) in enumerate(VARIANTS.items()):
        body = make_body(data, base, params, G, f"Body_{key}", skin, cloth, face_pts)
        body.location.x = gap * (k + 1)
        shown.append(body)
        for o in face_objs:
            dup = o.copy()
            dup.data = o.data
            bpy.context.scene.collection.objects.link(dup)
            dup.parent = None
            dup.matrix_world = Matrix.Translation((gap * (k + 1), 0, 0)) @ o.matrix_world
    if arm:
        arm.hide_render = True
    c.setup_render(samples=24, res=(1800, 1000), world_hex="#1A1A1F", world_strength=0.45)
    mid = gap * len(VARIANTS) / 2
    c.add_light("key", "AREA", (mid + 1.5, -4.0, 3.2), 380, size=3.0, target=(mid, 0, 1.0))
    c.add_light("fill", "AREA", (mid - 3.0, -3.0, 1.8), 140, size=3.0, target=(mid, 0, 1.0))
    c.add_light("rim", "AREA", (mid, 3.0, 2.5), 200, size=3.0, target=(mid, 0, 1.2))
    shots = []
    for view, rot in (("front", 0.0), ("side", 90.0)):
        cam_data = bpy.data.cameras.new(view)
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = gap * (len(VARIANTS) + 1) + 0.2
        cam = bpy.data.objects.new(view, cam_data)
        bpy.context.scene.collection.objects.link(cam)
        bpy.context.scene.camera = cam
        if view == "front":
            cam.location = (mid, -8, 0.9)
            cam.rotation_euler = (math.radians(90), 0, 0)
        else:
            # Side: every figure turned 90 degrees about its own axis.
            for o in [o for o in bpy.data.objects if o.type == "MESH"]:
                pivot = Vector((round(o.matrix_world.translation.x / gap) * gap if o.parent is None else 0, 0, 0))
                o.matrix_world = (Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(90), 4, "Z")
                                  @ Matrix.Translation(-pivot) @ o.matrix_world)
            cam.location = (mid, -8, 0.9)
            cam.rotation_euler = (math.radians(90), 0, 0)
        path = os.path.join(out, f"body_variants_{view}.png")
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        shots.append(path)
        log(f"render {path}")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "body_variants.blend"))
    return shots


def main():
    cmd = sys.argv[1]
    if cmd == "preview":
        data, game_body, out = sys.argv[2:5]
        face = sys.argv[5] if len(sys.argv) > 5 else None
        extra = [os.path.abspath(a) for a in sys.argv[6:]]
        os.makedirs(out, exist_ok=True)
        preview(os.path.abspath(data), os.path.abspath(game_body), os.path.abspath(out), face and os.path.abspath(face),
                extra)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout.flush()
        os._exit(0)
