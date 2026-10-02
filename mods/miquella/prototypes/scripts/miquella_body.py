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
  python miquella_body.py kit <MakeHuman data dir> <game ch02_002_0002 .mesh> <game face .mesh> <kit dir> <dual blades .mdf2>
      every variant as Art/Model/MiquellaLight/Character/mq_body_<a|b|c>.mesh (+ mq_body.mdf2), on
      the game's skeleton (from the given body mesh), weighted to its main bones
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
    ("buttocks/buttocks-volume-incr", 0.75),      # round buttocks (user 2026-10-02: they read square)
]
VARIANTS = {
    "A": {"label": "A 纖細中性", "gender": 0.62, "muscle": 0.28, "weight": 0.30, "details": []},
    "B": {"label": "B 少年感", "gender": 0.90, "muscle": 0.45, "weight": 0.34, "details": []},
    "C": {"label": "C 柔和", "gender": 0.66, "muscle": 0.22, "weight": 0.44,
          "details": [("torso/torso-scale-horiz-decr", 0.2)]},
}
# The belly (user 2026-10-02: the first bodies read as a beer belly; wants a slim waist with
# lines, 人魚線 / 馬甲線). Options shown side by side (preview abs); grooves are carved into the
# surface after one subdivision: (front-view polyline of (x, z) in m, depth, half-width).
FLAT_BELLY = [("stomach/stomach-pregnant-decr", 1.0)]
TONE = [("stomach/stomach-tone-incr", 0.7)]
GROOVES = {
    # 馬甲線: the outer edges of the abdominal wall, ribs to lower belly, and a faint midline above the navel.
    "vertical": [([(0.072, 1.24), (0.066, 1.14), (0.056, 1.04)], 0.0028, 0.011),
                 ([(-0.072, 1.24), (-0.066, 1.14), (-0.056, 1.04)], 0.0028, 0.011),
                 ([(0.0, 1.25), (0.0, 1.11)], 0.0016, 0.009)],
    # 人魚線: from the front hip bones down and in toward the groin (into the underwear).
    "v": [([(0.112, 1.065), (0.085, 1.005), (0.052, 0.955)], 0.0032, 0.012),
          ([(-0.112, 1.065), (-0.085, 1.005), (-0.052, 0.955)], 0.0032, 0.012)],
    # The groin (inguinal) fold where thigh and pelvis meet (user 2026-10-02: thigh and crotch are
    # separate forms, a V runs from the crotch up to the hip, shaded even under the underwear):
    # from beside the crotch up and out past the front of the hip joint to the hip bone, a narrow
    # soft line (user: a 15 mm wide valley is wider than real ones; 6.5 mm cut like a knife and
    # left a spike). Side-facing surface too (the fold turns in between the legs).
    "crease": [([(s * 0.020, 0.818), (s * 0.040, 0.852), (s * 0.074, 0.912), (s * 0.112, 0.982)],
                0.0045, 0.010, 0.35) for s in (1, -1)],
    # The first version of it (15 mm wide, starting 6 cm apart), for the before / after sheets.
    "crease_wide": [([(s * 0.030, 0.815), (s * 0.048, 0.852), (s * 0.078, 0.912), (s * 0.118, 0.985)],
                     0.0065, 0.015, 0.35) for s in (1, -1)],
    # The fold under each buttock (user 2026-10-02: the buttocks read square): from beside the
    # crotch down a little, then out and up along the bottom of the cheek, carved on the back.
    "gluteal": [([(s * 0.022, 0.836), (s * 0.045, 0.823), (s * 0.072, 0.824), (s * 0.100, 0.838),
                  (s * 0.128, 0.866)], 0.006, 0.012, 0.35, True) for s in (1, -1)],
}
BASE_GROOVES = ["crease", "gluteal"]     # every body shape has these
BUTT = "buttocks/buttocks-volume-incr"
# Before / after the 2026-10-02 hips round (narrow groin line, cone thighs, round buttocks with
# the fold under them, the cleft spanned by the underwear), and the buttocks rounder or less.
SHAPE_OPTIONS = [
    ("1 修改前", {"base_grooves": ["crease_wide"], "cleft": 0, "taper": 0, "soft": 0, "details": [(BUTT, 0.0)]}),
    ("2 修改後", {}),
    ("3 屁股少圓一點", {"details": [(BUTT, 0.4)]}),
    ("4 屁股再圓一點", {"details": [(BUTT, 1.0)]}),
]
BELLY_OPTIONS = [
    ("0 原本", {}),
    ("1 收小腹", {"details": FLAT_BELLY, "weight": 0.26}),
    ("2 收小腹＋緊實", {"details": FLAT_BELLY + TONE, "weight": 0.26}),
    ("3 收小腹＋馬甲線", {"details": FLAT_BELLY, "weight": 0.26, "grooves": ["vertical"]}),
    ("4 收小腹＋人魚線", {"details": FLAT_BELLY, "weight": 0.26, "grooves": ["v"]}),
    ("5 收小腹＋兩種", {"details": FLAT_BELLY, "weight": 0.26, "grooves": ["vertical", "v"]}),
]
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
    # The torso keeps MakeHuman's own anatomy (only moved and scaled by `aligned`): the game's
    # Hip / Spine_0 pivots sit 11 cm above its hip joints, and pulling MakeHuman's lower spine and
    # pelvis onto them lifted the crotch to hip-joint height and merged thighs and pelvis (user,
    # 2026-10-02: the groin had no structure). Limbs, neck, hands and feet are fitted.
    T = {}
    T.update(chain_targets(J, G, ["neck01", "neck02", "neck03"], ["Neck_0", "Neck_1", "Head"]))
    head_len = (J["head____tail"] - J["head____head"]).length
    T["head"] = (G["Head"], G["Head"] + Vector((0, 0, head_len)))
    for s, S in (("L", "L_"), ("R", "R_")):
        T.update(chain_targets(J, G, [f"clavicle.{s}", f"shoulder01.{s}"], [S + "Shoulder", S + "UpperArm"]))
        T.update(chain_targets(J, G, [f"upperarm01.{s}", f"upperarm02.{s}"], [S + "UpperArm", S + "Forearm"]))
        T.update(chain_targets(J, G, [f"lowerarm01.{s}", f"lowerarm02.{s}"], [S + "Forearm", S + "Hand"]))
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


def smooth_where(obj, weight_of, steps, keep_volume=False):
    """Laplacian smoothing of the vertices `weight_of(co, normal)` gives a weight (0..1) to;
    `keep_volume` alternates an inflating pass (Taubin) so bumps go but the form doesn't shrink."""
    me = obj.data
    me.update()
    weight = {}
    for v in me.vertices:
        w = weight_of(v.co, v.normal)
        if w > 0:
            weight[v.index] = w
    nbr = {i: [] for i in weight}
    for e in me.edges:
        a, b = e.vertices
        if a in nbr:
            nbr[a].append(b)
        if b in nbr:
            nbr[b].append(a)
    co = {i: me.vertices[i].co.copy() for i in weight}
    for i in weight:
        for j in nbr[i]:
            co.setdefault(j, me.vertices[j].co.copy())
    passes = (0.5, -0.53) if keep_volume else (0.5,)
    for _ in range(steps):
        for k in passes:
            new = {}
            for i, w in weight.items():
                if nbr[i]:
                    avg = sum((co[j] for j in nbr[i]), Vector()) / len(nbr[i])
                    new[i] = co[i] + (avg - co[i]) * (k * w)
            co.update(new)
    for i in weight:
        me.vertices[i].co = co[i]
    return len(weight)


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def smooth_groin(obj, reach=0.035, steps=12):
    """Linear skinning pinches small folds where the fitted thighs meet the pelvis: smooth the
    surface within `reach` (front view) of the groin fold before anything is carved there."""
    lines = [g[0] for g in GROOVES["crease"]]

    def weight_of(c, n):
        if not 0.79 < c.z < 1.02 or n.y > 0.5:
            return 0.0
        d = min(seg_dist(c.x, c.z, a, b)[0] for pts in lines for a, b in zip(pts, pts[1:]))
        return smoothstep(0.0, 1.0, 1 - d / reach)
    smooth_where(obj, weight_of, steps)


# The cleft between the buttocks (user 2026-10-02 asked how the back is designed): the underwear is
# only a material on the skin, so MakeHuman's deep cleft showed through it. Cloth spans the cleft:
# at each height it is filled out to a line from one cheek's crest to the other's, sagging `sag`
# in the middle, fading out above the waistband and toward the crotch. Only the cleft moves
# (smoothing it shallow instead pulled the cheeks in and left a hard vertical line on each).
CLEFT = {"z": (0.845, 0.875, 0.95, 0.985), "sag": 0.004, "amount": 1.0}


def bridge_cleft(obj, amount=1):
    me = obj.data
    z0, z1, z2, z3 = CLEFT["z"]
    used = {i for p in me.polygons for i in p.vertices}
    back = [v for v in me.vertices if v.index in used and v.co.y > 0.0 and z0 - 0.01 < v.co.z < z3 + 0.01
            and abs(v.co.x) < 0.12]
    zs = [z0 + i * 0.005 for i in range(int((z3 - z0) / 0.005) + 1)]
    crest = []
    for zc in zs:       # the mesh is ~1 cm apart here: the crest within 1 cm of each height
        sl = [v.co for v in back if abs(v.co.z - zc) < 0.01 and 0.02 < abs(v.co.x) < 0.10]
        top = max(sl, key=lambda c: c.y)
        crest.append((abs(top.x), top.y))
    moved = {}
    for v in back:
        z = v.co.z
        w = smoothstep(z0, z1, z) * (1 - smoothstep(z2, z3, z)) * amount
        if w <= 0:
            continue
        xc, yc = crest[min(range(len(zs)), key=lambda i: abs(zs[i] - z))]
        t = abs(v.co.x) / xc
        if t >= 1:
            continue
        lift = yc - CLEFT["sag"] * (1 - t * t) - v.co.y
        if lift > 0:
            v.co.y += lift * w
            moved[v.index] = 1.0
    # Relax the filled wall (its vertices were pressed together sideways).
    me.update()
    nbr = {i: [] for i in moved}
    for e in me.edges:
        a, b = e.vertices
        if a in nbr:
            nbr[a].append(b)
        if b in nbr:
            nbr[b].append(a)
    for _ in range(12):     # a deeper cleft (rounder buttocks) needs more, or a seam shows
        for i in moved:
            if nbr[i]:
                avg = sum((me.vertices[j].co for j in nbr[i]), Vector()) / len(nbr[i])
                me.vertices[i].co = me.vertices[i].co.lerp(avg, 0.5)
    log(f"  filled the cleft: {len(moved)} vertices")


# The buttocks under a robe that is fitted down to the thighs (user 2026-10-02: a firm, sculpted
# shape would look odd): MakeHuman's muscle shapes there are smoothed away, keeping the volume.
SOFT_BUTT = {"x": 0.17, "z": (0.80, 0.83, 0.97, 1.01), "steps": 25}


def soften_buttocks(obj, steps):
    z0, z1, z2, z3 = SOFT_BUTT["z"]

    def weight_of(c, n):
        if c.y < 0.0 or n.y < -0.2:
            return 0.0
        return (smoothstep(z0, z1, c.z) * (1 - smoothstep(z2, z3, c.z))
                * (1 - smoothstep(SOFT_BUTT["x"] - 0.04, SOFT_BUTT["x"], abs(c.x))))
    n = smooth_where(obj, weight_of, steps, keep_volume=True)
    log(f"  softened the buttocks: {n} vertices, {steps} steps")


# The thighs in profile (user 2026-10-02, with a reference drawing of slim legs from the side):
# a cone narrowing straight from under the buttock to the knee, not an arc. MakeHuman's thigh keeps
# its depth to mid-thigh and then curves in. Per leg, each height's front-most and back-most points
# are moved onto straight lines between the ends, and the rest of the slice is scaled with them.
THIGH_TAPER = (0.53, 0.80)        # knee, under the buttock (z, m)


def taper_thighs(obj, G, amount=1.0):
    me = obj.data
    lo, hi = THIGH_TAPER
    # MakeHuman's helper geometry (tights, skirt...) is still here as loose vertices: skip it.
    used = {i for p in me.polygons for i in p.vertices}
    for s in (1, -1):
        S = "L_" if s > 0 else "R_"
        top, knee = G[S + "Thigh"], G[S + "Knee"]

        def axis_x(z):
            t = (top.z - z) / (top.z - knee.z)
            return top.x + (knee.x - top.x) * t
        leg = [v for v in me.vertices if lo - 0.02 < v.co.z < hi + 0.02 and s * v.co.x > 0.02
               and abs(v.co.x - axis_x(v.co.z)) < 0.12 and v.index in used]
        zs = [lo + i * 0.01 for i in range(int(round((hi - lo) / 0.01)) + 1)]
        front, back = [], []
        for zc in zs:
            sl = [v.co.y for v in leg if abs(v.co.z - zc) < 0.008]
            front.append(min(sl))
            back.append(max(sl))

        def at(vals, z):
            t = max(0.0, min(len(zs) - 1.0, (z - lo) / 0.01))
            i = min(int(t), len(zs) - 2)
            return vals[i] + (vals[i + 1] - vals[i]) * (t - i)

        def line(vals, z):
            t = (z - lo) / (hi - lo)
            return vals[0] + (vals[-1] - vals[0]) * t
        for v in leg:
            z = v.co.z
            if not lo <= z <= hi:
                continue
            f, b = at(front, z), at(back, z)
            ft = f + (line(front, z) - f) * amount
            bt = b + (line(back, z) - b) * amount
            if b - f > 1e-4:
                v.co.y = ft + (v.co.y - f) * (bt - ft) / (b - f)


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


# Briefs: leg openings along the groin fold in front, along the buttock fold behind.
BRIEF_TOP = 0.975
BRIEF_FRONT = [(0.0, 0.80), (0.036, 0.858), (0.076, 0.908), (0.118, 0.975)]
BRIEF_BACK = [(0.0, 0.79), (0.07, 0.81), (0.12, 0.86), (0.15, 0.94)]


def line_z(pts, x):
    x = abs(x)
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        if x <= x1:
            return z0 + (z1 - z0) * (x - x0) / max(x1 - x0, 1e-6)
    return pts[-1][1]


def in_brief(c, n):
    if abs(c.x) > 0.2 or c.z > BRIEF_TOP or c.z < 0.76:
        return False
    if abs(c.x) > BRIEF_FRONT[-1][0] and n.y < 0:
        return c.z > BRIEF_FRONT[-1][1] - 0.002     # the side band at the hip
    return c.z > line_z(BRIEF_FRONT if c.y < 0 else BRIEF_BACK, c.x)


def cut_and_paint(obj, G, skin, cloth, face_pts=None, style="boxer"):
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
        if style == "brief":
            p.material_index = 1 if in_brief(c, p.normal) else 0
        else:
            p.material_index = 1 if low < c.z < high and abs(c.x) < xlim else 0
    log(f"{obj.name}: {len(me.vertices)} verts, {len(me.polygons)} faces after the cut")


# The lower belly stuck out in profile like a beer belly (user 2026-10-02, side view): from below
# the ribs to the pubic bone the front of the belly may not come past a straight line, and dips a
# little behind it in the middle (BELLY_DIP), so the profile runs slim and slightly hollow.
BELLY_SPAN = (0.92, 1.21)    # m: pubic bone .. below the ribs
BELLY_DIP = 0.006            # m behind the line at its middle
BELLY_HALF = 0.15            # m: |x| beyond which nothing moves


def flatten_belly(obj):
    me = obj.data
    lo, hi = BELLY_SPAN
    torso = [v for v in me.vertices if abs(v.co.x) < BELLY_HALF and lo - 0.02 < v.co.z < hi + 0.02]

    def front(z):
        s = [v.co.y for v in torso if abs(v.co.x) < 0.03 and abs(v.co.z - z) < 0.006]
        return min(s) if s else None
    y_lo, y_hi = front(lo), front(hi)
    if y_lo is None or y_hi is None:
        log("  belly: profile not found, left as is")
        return
    slabs = {}
    for v in torso:
        slabs.setdefault(round(v.co.z / 0.01), []).append(v)
    worst = 0.0
    for zb, vs in slabs.items():
        z = zb * 0.01
        if not lo < z < hi:
            continue
        t = (z - lo) / (hi - lo)
        target = y_lo + (y_hi - y_lo) * t + BELLY_DIP * math.sin(math.pi * t)
        fy = min(v.co.y for v in vs if abs(v.co.x) < 0.03) if any(abs(v.co.x) < 0.03 for v in vs) else None
        if fy is None:
            continue
        push = target - fy              # > 0: the front sticks out past the line by this much
        if push <= 0:
            continue
        worst = max(worst, push)
        back = max(v.co.y for v in vs)
        center = (fy + back) / 2
        hw = max(abs(v.co.x) for v in vs if v.co.y < center) if any(v.co.y < center for v in vs) else BELLY_HALF
        edge = min(1.0, (z - lo) / 0.03, (hi - z) / 0.03)
        for v in vs:
            if v.co.y >= center:
                continue
            wx = max(0.0, 1 - (v.co.x / (hw * 0.95)) ** 2)
            wy = min(1.0, (center - v.co.y) / max(center - fy, 1e-4))
            v.co.y += push * wx * wy * edge
    log(f"  belly: flattened up to {worst * 100:.1f} cm")
    # Smooth the moved area a little so slab steps do not show.
    nbr = {}
    ids = {v.index for v in torso}
    for e in me.edges:
        a, b = e.vertices
        if a in ids and b in ids:
            nbr.setdefault(a, []).append(b)
            nbr.setdefault(b, []).append(a)
    for _ in range(4):
        co = {i: me.vertices[i].co.copy() for i in ids}
        for i in ids:
            v = me.vertices[i]
            if lo < v.co.z < hi and abs(v.co.x) < BELLY_HALF * 0.9 and i in nbr:
                avg = sum((co[j] for j in nbr[i]), Vector()) / len(nbr[i])
                v.co = co[i].lerp(avg, 0.3)


def subdivide(obj):
    """One Catmull-Clark level (vertex groups carry over), so thin grooves have vertices to sit on."""
    mod = obj.modifiers.new("Subdiv", "SUBSURF")
    mod.levels = mod.render_levels = 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)


def seg_dist(px, pz, a, b):
    """Distance in the front view (x, z) from a point to segment ab, and the share along it."""
    ax, az = a
    bx, bz = b
    dx, dz = bx - ax, bz - az
    L2 = dx * dx + dz * dz
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L2)) if L2 else 0.0
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz)), t


def carve(obj, grooves):
    """Soft grooves on the front of the body: each vertex near a polyline (front view) moves in
    along its normal by depth * a Gaussian of its distance, tapered at the line's ends."""
    me = obj.data
    me.update()
    moves = {}
    for v in me.vertices:
        for g in grooves:
            pts, depth, width = g[:3]
            facing = g[3] if len(g) > 3 else -0.25
            back = len(g) > 4 and g[4]
            if (-v.normal.y if back else v.normal.y) > facing:     # front-facing only (front is -Y), or back
                continue
            lens = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
            total, acc, best = sum(lens), 0.0, (9.9, 0.0)
            for i in range(len(pts) - 1):
                d, t = seg_dist(v.co.x, v.co.z, pts[i], pts[i + 1])
                if d < best[0]:
                    best = (d, (acc + t * lens[i]) / total)
                acc += lens[i]
            d, u = best
            if d > 3 * width:
                continue
            taper = min(1.0, u / 0.2, (1 - u) / 0.2)
            taper = taper * taper * (3 - 2 * taper)
            amount = depth * math.exp(-(d / width) ** 2) * taper
            moves[v.index] = moves.get(v.index, 0.0) + amount
    for i, a in moves.items():
        v = me.vertices[i]
        v.co -= v.normal * a
    log(f"  carved {len(grooves)} grooves over {len(moves)} vertices")


def ground_feet(obj, G):
    """The game's ankle joint is lower than MakeHuman's: below the ankles the feet are squashed
    so the soles stand on the ground (z 0) instead of sinking into it."""
    ankle = (G["L_Foot"].z + G["R_Foot"].z) / 2
    vs = [v for v in obj.data.vertices if v.co.z < ankle and abs(v.co.x) < 0.4]
    sole = min(v.co.z for v in vs)
    if sole < 0:
        k = ankle / (ankle - sole)
        for v in vs:
            v.co.z = ankle + (v.co.z - ankle) * k
        log(f"  feet: sole {sole:+.3f} -> 0 (below the ankle at {ankle:.3f})")


def make_body(data, base, params, G, name, skin, cloth, face_pts=None):
    verts, uvs, faces, skel, weights = base
    v = aligned(skel, [mh_to_blender(p) for p in shaped(data, verts, params)], G)
    J = joint_positions(skel, v)
    obj = build_mesh(name, v, uvs, faces, weights)
    arm = build_rig(skel, J)
    targets = fit_targets(J, G)
    # Where each bone ends up (fitted, or MakeHuman's own after alignment): bone_map reads it.
    fit = {b: [list(J[v["head"]]), list(J[v["tail"]])] for b, v in skel["bones"].items()}
    fit.update({b: [list(t) if h is None else list(h), list(t)] for b, (h, t) in targets.items()})
    obj["fit"] = fit
    pose_to(arm, targets)
    bake(obj, arm)
    ground_feet(obj, G)
    if params.get("flat", False):     # not needed since the torso keeps its own anatomy
        flatten_belly(obj)
    spots = [obj.data.vertices[skel["joints"][n][0]].co.copy() for n in SMOOTH_SPOTS]
    smooth_spots(obj, spots)
    smooth_groin(obj)
    if params.get("soft", SOFT_BUTT["steps"]):
        soften_buttocks(obj, params.get("soft", SOFT_BUTT["steps"]))
    if params.get("taper", 1.0):
        taper_thighs(obj, G, params.get("taper", 1.0))
    grooves = list(params.get("base_grooves", BASE_GROOVES)) + list(params.get("grooves", []))
    if grooves:
        subdivide(obj)
    if params.get("cleft", CLEFT["amount"]):    # needs the subdivided mesh (2 cm apart before)
        bridge_cleft(obj, params.get("cleft", CLEFT["amount"]))
    if grooves:
        carve(obj, [g for key in grooves for g in GROOVES[key]])
    for o in [o for o in bpy.data.objects if o.type == "EMPTY" or o is arm]:
        bpy.data.objects.remove(o, do_unlink=True)
    cut_and_paint(obj, G, skin, cloth, face_pts, params.get("underwear", "boxer"))
    return obj


# ------------------------------------------------------------------ game kit

def segment_bone(z, chain, G):
    """The game bone of a chain whose segment holds height z (the last one covers above)."""
    out = chain[0]
    for name in chain:
        if G[name].z <= z + 1e-4:
            out = name
    return out


def bone_map(skel, fit, G):
    """MakeHuman bone -> game bone (main bones only: the game's *_HJ_* helpers are left out)."""
    m = {"root": "Hip", "head": "Head"}

    def mid(b):
        return (Vector(fit[b][0]) + Vector(fit[b][1])) / 2
    for b in ("spine05", "spine04", "spine03", "spine02", "spine01"):
        m[b] = segment_bone(mid(b).z, ["Spine_0", "Spine_1", "Spine_2"], G)
    for b in ("neck01", "neck02", "neck03"):
        m[b] = segment_bone(mid(b).z, ["Neck_0", "Neck_1"], G)
    for s, S in (("L", "L_"), ("R", "R_")):
        m.update({f"pelvis.{s}": "Hip", f"breast.{s}": "Spine_2",
                  f"clavicle.{s}": S + "Shoulder", f"shoulder01.{s}": S + "Shoulder",
                  f"upperarm01.{s}": S + "UpperArm", f"upperarm02.{s}": S + "UpperArm",
                  f"lowerarm01.{s}": S + "Forearm", f"lowerarm02.{s}": S + "Forearm",
                  f"wrist.{s}": S + "Hand", f"metacarpal1.{s}": S + "Hand", f"metacarpal2.{s}": S + "Hand",
                  f"metacarpal3.{s}": S + "Palm", f"metacarpal4.{s}": S + "Palm",
                  f"upperleg01.{s}": S + "Thigh", f"upperleg02.{s}": S + "Thigh",
                  f"lowerleg01.{s}": S + "Shin", f"lowerleg02.{s}": S + "Shin", f"foot.{s}": S + "Foot"})
        for k, (game, f) in enumerate([("Thumb", ""), ("Index", "F"), ("Middle", "F"), ("Ring", "F"), ("Pinky", "F")]):
            for i in (1, 2, 3):
                m[f"finger{k + 1}-{i}.{s}"] = f"{S}{game}{f}{i}"
        for b in skel["bones"]:
            if b.startswith("toe") and b.endswith("." + s):
                m[b] = S + "Toe"
    # Anything else (face, tongue, eyes...): its nearest mapped ancestor's.
    for b in skel["bones"]:
        a = b
        while a not in m and skel["bones"][a].get("parent"):
            a = skel["bones"][a]["parent"]
        m.setdefault(b, m.get(a, "Head"))
    return m


MAX_WEIGHTS = 6


def game_weights(obj, skel, G):
    """MakeHuman's vertex groups -> game bone groups (summed, the top MAX_WEIGHTS, normalized)."""
    fit = obj["fit"].to_dict()
    m = bone_map(skel, fit, G)
    names = {g.index: g.name for g in obj.vertex_groups}
    per_vertex = []
    for v in obj.data.vertices:
        acc = {}
        for ge in v.groups:
            if ge.weight > 0:
                gb = m.get(names[ge.group], "Hip")
                acc[gb] = acc.get(gb, 0.0) + ge.weight
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:MAX_WEIGHTS]
        total = sum(w for _, w in top) or 1.0
        per_vertex.append([(b, w / total) for b, w in top] or [("Hip", 1.0)])
    obj.vertex_groups.clear()
    groups = {}
    for i, ws in enumerate(per_vertex):
        for b, w in ws:
            if b not in groups:
                groups[b] = obj.vertex_groups.new(name=b)
            groups[b].add([i], w, "REPLACE")
    log(f"  weights on {len(groups)} game bones")


MESH_EXT, MDF_EXT = ".241111606", ".45"
REL = "Art/Model/MiquellaLight/Character"
# Our material -> (game material name, dual blades material it is copied from).
GAME_MATERIALS = {"Skin": ("MiquellaSkin", "MiquellaIvory"), "Underwear": ("MiquellaCloth", "MiquellaGrip")}


def split_for_export(obj, mesh_col):
    """One object per material, named the way RE Mesh Editor reads them (Group_0_Sub_i__Material)."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.mesh.separate(type="MATERIAL")
    out = []
    for o in list(bpy.context.selected_objects):
        used = {p.material_index for p in o.data.polygons}
        mat = o.data.materials[used.pop()].name.split(".")[0] if len(used) == 1 else None
        if mat not in GAME_MATERIALS:
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        out.append((GAME_MATERIALS[mat][0], o))
    out.sort(key=lambda t: t[0])
    for i, (game_mat, o) in enumerate(out):
        o.name = f"Group_0_Sub_{i}__{game_mat}"
        o.data.materials.clear()
        o.data.materials.append(bpy.data.materials.get(game_mat) or bpy.data.materials.new(game_mat))
        for col in list(o.users_collection):
            col.objects.unlink(o)
        mesh_col.objects.link(o)
    return [o for _, o in out]


def write_mdf(path, template_mdf):
    import copy
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    template = readMDF(template_mdf)
    by_name = {m.materialName: m for m in template.materialList}
    mats = []
    for game_mat, source in GAME_MATERIALS.values():
        new = copy.deepcopy(by_name[source])
        new.materialName = game_mat
        mats.append(new)
    template.materialList = mats
    writeMDF(template, path)
    log(f"mdf: {[m.materialName for m in readMDF(path).materialList]}")


def kit(data, game_body, face, kit_dir, template_mdf):
    import common as c
    c.reset_scene()
    enable_addon()
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile
    arm, _ = import_game(game_body, keep_meshes=False)
    G = game_joints(arm)
    _, face_objs = import_game(face, keep_meshes=True)
    face_pts = [o.matrix_world @ v.co for o in face_objs for v in o.data.vertices]
    for o in list(bpy.data.objects):
        if o.type == "ARMATURE" and o is not arm or o in face_objs:
            bpy.data.objects.remove(o, do_unlink=True)
    base = load_base(data)
    skin = bpy.data.materials.new("Skin")
    cloth = bpy.data.materials.new("Underwear")
    natives = os.path.join(kit_dir, "natives", "STM", *REL.split("/"))
    os.makedirs(natives, exist_ok=True)
    for key, params in VARIANTS.items():
        name = f"mq_body_{key.lower()}"
        body = make_body(data, base, params, G, name, skin, cloth, face_pts)
        game_weights(body, base[3], G)
        mesh_col = bpy.data.collections.new(f"{name}.mesh")
        bpy.context.scene.collection.children.link(mesh_col)
        for col in list(arm.users_collection):
            col.objects.unlink(arm)
        mesh_col.objects.link(arm)
        subs = split_for_export(body, mesh_col)
        for o in subs:
            o.modifiers.clear()
            o.modifiers.new("Armature", "ARMATURE").object = arm
            o.parent = arm
        path = os.path.join(natives, f"{name}.mesh{MESH_EXT}")
        ok = exportREMeshFile(path, {"targetCollection": mesh_col.name, "selectedOnly": False,
                                     "exportAllLODs": False, "exportBlendShapes": False, "rotate90": True,
                                     "useBlenderMaterialName": False, "preserveBoneMatrices": True,
                                     "exportBoundingBoxes": False, "autoSolveRepeatedUVs": True,
                                     "preserveSharpEdges": False})
        log(f"export {name}: {ok} ({os.path.getsize(path)} bytes), {[o.name for o in subs]}, "
            f"{sum(len(o.data.vertices) for o in subs)} verts")
        for o in subs:
            bpy.data.objects.remove(o, do_unlink=True)
    write_mdf(os.path.join(natives, f"mq_body.mdf2{MDF_EXT}"), template_mdf)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(kit_dir, "mq_body_kit.blend"))


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


VIEWS = (("front", 0), ("quarter", 30), ("side", 90))
BACK_VIEWS = (("back", 180), ("backquarter", 150), ("side", 90))


def preview_abs(data, game_body, out, base_key="A", options=None, center_z=1.10, scale=0.52, prefix="belly",
                views=VIEWS):
    """Options (on one body shape unless an option names its own `base`), close-ups from each of
    `views` in a row."""
    options = options or BELLY_OPTIONS
    import common as c
    c.reset_scene()
    enable_addon()
    arm, _ = import_game(game_body, keep_meshes=False)
    G = game_joints(arm)
    base = load_base(data)
    skin = c.make_material("Skin", "#F2DCD0", roughness=0.5, subsurface=0.15)
    cloth = c.make_material("Underwear", "#B8A27E", roughness=0.85)
    gap = 0.9
    for k, (label, opt) in enumerate(options):
        params = dict(VARIANTS[opt.get("base", base_key)])
        params["details"] = list(params["details"]) + list(opt.get("details", []))
        for key in ("weight", "muscle", "grooves", "base_grooves", "flat", "underwear", "cleft", "taper", "soft"):
            if key in opt:
                params[key] = opt[key]
        body = make_body(data, base, params, G, f"Belly_{k}", skin, cloth)
        body.location.x = gap * k
    if arm:
        bpy.data.objects.remove(arm, do_unlink=True)
    c.setup_render(samples=32, res=(600, 700), world_hex="#141418", world_strength=0.25)
    shots = []
    n = len(options)
    for view, az in views:
        for o in [o for o in bpy.data.objects if o.type == "LIGHT"]:
            bpy.data.objects.remove(o, do_unlink=True)
        for k in range(n):
            x0 = gap * k
            ang = math.radians(az)
            cam_dir = Vector((math.sin(ang), -math.cos(ang), 0))
            # Raking key light from above and to the side shows the grooves.
            side = Vector((math.cos(ang), math.sin(ang), 0))
            c.add_light(f"key{k}", "AREA", tuple(Vector((x0, 0, center_z + 0.35)) + cam_dir * 0.5 + side * 0.55), 6,
                        size=0.25, target=(x0, 0, center_z - 0.02))
            c.add_light(f"fill{k}", "AREA", tuple(Vector((x0, 0, center_z)) + cam_dir * 0.9 - side * 0.5), 1.5,
                        size=0.6, target=(x0, 0, center_z))
        for k, (label, _) in enumerate(options):
            x0 = gap * k
            ang = math.radians(az)
            cam_data = bpy.data.cameras.new(f"{view}{k}")
            cam_data.type = "ORTHO"
            cam_data.ortho_scale = scale
            cam = bpy.data.objects.new(f"{view}{k}", cam_data)
            bpy.context.scene.collection.objects.link(cam)
            cam.location = (x0 + math.sin(ang) * 2.0, -math.cos(ang) * 2.0, center_z)
            cam.rotation_euler = (math.radians(90), 0, ang)
            if view in ("side", "profile"):
                # Clip off the near arm (it hangs in front of the belly in profile); for the whole
                # leg ("profile") clip further out so the near thigh stays whole.
                cam_data.clip_start, cam_data.clip_end = 2.0 - (0.2 if view == "side" else 0.27), 3.0
            bpy.context.scene.camera = cam
            for o in bpy.data.objects:
                if o.type == "MESH":
                    o.hide_render = o.name != f"Belly_{k}"
            path = os.path.join(out, f"{prefix}_{view}_{k}.png")
            bpy.context.scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            shots.append(path)
    c.contact_sheet(shots, os.path.join(out, f"{prefix}_options.png"), cols=n)


def main():
    cmd = sys.argv[1]
    if cmd == "back":
        # The back of the three shapes: hips close-ups (back, back three-quarter, side) and whole bodies.
        data, game_body, out = (os.path.abspath(a) for a in sys.argv[2:5])
        os.makedirs(out, exist_ok=True)
        shapes = [(VARIANTS[k]["label"], {"base": k}) for k in VARIANTS]
        preview_abs(data, game_body, out, options=shapes, center_z=0.90, scale=0.44, prefix="back",
                    views=BACK_VIEWS)
        preview_abs(data, game_body, out, options=shapes, center_z=0.92, scale=1.95, prefix="back_full",
                    views=(("back", 180),))
    if cmd == "hips":
        # Before / after sheets of the hips: front, back, and the legs in profile.
        data, game_body, out = (os.path.abspath(a) for a in sys.argv[2:5])
        os.makedirs(out, exist_ok=True)
        preview_abs(data, game_body, out, options=SHAPE_OPTIONS, center_z=0.90, scale=0.40, prefix="hips_front")
        preview_abs(data, game_body, out, options=SHAPE_OPTIONS, center_z=0.90, scale=0.40, prefix="hips_back",
                    views=BACK_VIEWS)
        preview_abs(data, game_body, out, options=SHAPE_OPTIONS, center_z=0.74, scale=0.72, prefix="hips_legs",
                    views=(("profile", 90), ("back", 180)))
    if cmd == "abs":
        data, game_body, out = (os.path.abspath(a) for a in sys.argv[2:5])
        os.makedirs(out, exist_ok=True)
        preview_abs(data, game_body, out)
    if cmd == "kit":
        data, game_body, face, kit_dir, template = (os.path.abspath(a) for a in sys.argv[2:7])
        kit(data, game_body, face, kit_dir, template)
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
