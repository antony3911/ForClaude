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
    # (no slender neck: it has to meet the game face's neck, which is a man's)
    ("buttocks/buttocks-volume-incr", 0.75),      # round buttocks (user 2026-10-02: they read square)
    ("measure/measure-waist-circ-decr", 0.6),     # a waist, curving out to the hips (LINE_OPTIONS)
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
# The spine's groove down the back (slim and toned), carved on the back.
GROOVES["spine"] = [([(0.0, 1.33), (0.0, 1.17), (0.0, 1.02)], 0.003, 0.010, -0.25, True)]
BASE_GROOVES = ["crease", "gluteal", "vertical", "spine"]     # every body shape has these
# Lines of a slim young man keeping a slender, softly feminine figure (user 2026-10-02: "add the
# ones you think of; a friend says 馬甲線"): a narrower waist (waist to hips curve), 馬甲線, the
# spine's groove. Compared side by side (preview lines); all three went in (user: "add them").
# Not 人魚線 ("v"): the groin fold already draws that V.
WAIST = "measure/measure-waist-circ-decr"
LINE_OPTIONS = [      # option 4 is what every shape now has (COMMON_DETAILS, BASE_GROOVES)
    ("1 現在", {"base_grooves": ["crease", "gluteal"], "details": [(WAIST, 0.0)]}),
    ("2 收腰", {"base_grooves": ["crease", "gluteal"]}),
    ("3 收腰＋馬甲線", {"base_grooves": ["crease", "gluteal", "vertical"]}),
    ("4 收腰＋馬甲線＋背溝", {}),
]
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


NECK_SHIFT = (Vector((0, 0.015, 0)), Vector((0, 0.025, 0)))     # at Neck_0, at Neck_1 and Head
UPPER_BACK_SHARE = 0.35


def fit_targets(J, G):
    """Where each mapped MakeHuman bone's head and tail go, from the game's joints."""
    # The torso keeps MakeHuman's own anatomy (only moved and scaled by `aligned`): the game's
    # Hip / Spine_0 pivots sit 11 cm above its hip joints, and pulling MakeHuman's lower spine and
    # pelvis onto them lifted the crotch to hip-joint height and merged thighs and pelvis (user,
    # 2026-10-02: the groin had no structure). Limbs, neck, hands and feet are fitted.
    T = {}
    # The neck goes NECK_SHIFT behind the game's neck joints: placed on them, MakeHuman's neck
    # stood 2.3 cm in front of the game face's neck (whose rim it has to meet), and the two bent
    # into an S at the seam (user 2026-10-02: "the neck is twisted").
    neck_pts = [G["Neck_0"] + NECK_SHIFT[0], G["Neck_1"] + NECK_SHIFT[1], G["Head"] + NECK_SHIFT[1]]
    T.update(chain_targets(J, G, ["neck01", "neck02", "neck03"], neck_pts))
    # The upper back turns to meet that neck base (the lower spine and pelvis stay MakeHuman's):
    # left alone, MakeHuman's upper spine leans forward where the game's leans back, the neck
    # came off it 3 cm behind and the nape stood out like a spur under the face's rim (user
    # 2026-10-02). The turn is shared, UPPER_BACK_SHARE by spine02 and the rest by spine01.
    off = neck_pts[0] - J["spine01____tail"]
    mid = J["spine02____tail"] + off * UPPER_BACK_SHARE
    T["spine02"] = (None, mid)
    T["spine01"] = (mid, neck_pts[0])
    head_len = (J["head____tail"] - J["head____head"]).length
    T["head"] = (neck_pts[2], neck_pts[2] + Vector((0, 0, head_len)))
    for s, S in (("L", "L_"), ("R", "R_")):
        T.update(chain_targets(J, G, [f"clavicle.{s}", f"shoulder01.{s}"], [S + "Shoulder", S + "UpperArm"]))
        T.update(chain_targets(J, G, [f"upperarm01.{s}", f"upperarm02.{s}"], [S + "UpperArm", S + "Forearm"]))
        T.update(chain_targets(J, G, [f"lowerarm01.{s}", f"lowerarm02.{s}"], [S + "Forearm", S + "Hand"]))
        T.update(chain_targets(J, G, [f"upperleg01.{s}", f"upperleg02.{s}"], [S + "Thigh", S + "Knee"]))
        T.update(chain_targets(J, G, [f"lowerleg01.{s}", f"lowerleg02.{s}"], [S + "Knee", S + "Foot"]))
        # The foot keeps MakeHuman's own angle and length, moved onto the game's ankle: aimed at
        # the game's Instep it pointed down, sank 5 cm into the ground and was squashed to 63 %
        # height to stand on it (user 2026-10-03: long, flat feet). shorten_feet sets the length.
        T[f"foot.{s}"] = (G[S + "Foot"], G[S + "Foot"] + (J[f"foot.{s}____tail"] - J[f"foot.{s}____head"]))
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

# The game's face mesh (ch00_000_0000) covers the whole neck down to an open rim (front 1.43,
# nape 1.53), lined inside by a narrow band (its Group_7). The game's own innerwear (ch02_002_0002,
# its skin) starts right there, measured 2026-10-03: its top edge IS the face's rim, the same 48
# vertices (0.000 mm apart), with the face's normals (0 degrees apart) and weights (identical)
# on them, so the seam never opens and shows no shading line, and the face's neck keeps its
# shape. Our neck does the same (user 2026-10-03: covering the face's neck from outside made "a
# big ring bulging out"; a seam may show, a jewel can cover it, the shape may not change): the
# face stays untouched, our body's top edge is the face's rim.
# Below the rim: MakeHuman's neck is ~2 cm thinner than the face's (a man's) and its trapezius
# starts ~6 cm lower, so a curve from the rim to MakeHuman's surface a few cm below had to tuck in
# (a fold at the sides; user: "obvious deformation", and the neck looked long). So from each rim
# vertex the profile aims NECK_DEPTH down and out at NECK_SLOPE (the neck-to-shoulder line: up
# the trapezius at the sides, which shortens the neck; the upper chest; the upper back, under the
# bulge MakeHuman's upper back makes behind the neck) and meets MakeHuman's body at its surface
# nearest that point; the profile from there up to the rim (radius-height plane) is a cubic
# Hermite leaving the body along its surface and reaching the rim along the face's (the plane of
# the face's normal there), so the face's neck carries on into ours without a kink. Below the rim
# the game's innerwear is no guide: its skin stands up there like a collar's lining. MakeHuman is
# cut cleanly where the profiles meet it (`contour_cut`), everything from there up is built new
# (`neck_tube`).
NECK_SLOPE = (30.0, 50.0, -5.0)   # degrees out from straight down, the rim to the body: front, sides, back
NECK_DEPTH = (0.05, 0.07, 0.09)   # how far below the rim the profiles meet the body: front, sides, back
                                  # (back: under MakeHuman's upper back, which bulges up behind the neck)
NECK_ROWS = 12                     # rows from the cut up to the rim
NECK_SMOOTH = 4                    # passes smoothing the profiles around (not at their ends)
NECK_SAMPLES = 64                  # points along each profile
NECK_CUT = 1.47          # without the face mesh: a level cut
UNDERWEAR = (0.78, 0.99, 0.30)   # boxer-brief band: lowest, highest, |x| limit (the hands hang beside it)


def face_outer(face_objs):
    """The face's outer surface: everything but the band lining the inside of its neck rim."""
    return [o for o in face_objs if not o.name.startswith("Group_7_")]


def face_geometry(face_objs):
    """What fitting the neck needs from the face: its outer surface (world-space vertices and
    polygons) and its neck rim (the lowest open boundary): each rim vertex's position and the
    face's own (custom) normal there, as the file has it."""
    import bmesh
    from mathutils import kdtree
    verts, normals, polys, loops = [], [], [], []
    for o in face_outer(face_objs):
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in o.data.vertices]
        rot = o.matrix_world.to_3x3()
        me = o.data
        acc = [Vector() for _ in me.vertices]
        for li, lp in enumerate(me.loops):          # the file's normals (custom, per corner)
            acc[lp.vertex_index] += Vector(me.corner_normals[li].vector)
        normals += [(rot @ n).normalized() for n in acc]
        polys += [[base + i for i in p.vertices] for p in me.polygons]
        bm = bmesh.new()
        bm.from_mesh(me)
        # The face is split along its UV seams (front and back of the neck): welded, those don't
        # count as edges.
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        seen = set()
        for e in bm.edges:              # boundary loops (neck rim, mouth, eyes...)
            if not e.is_boundary or e in seen:
                continue
            stack, vs = [e], set()
            while stack:
                x = stack.pop()
                if x in seen:
                    continue
                seen.add(x)
                vs.update(x.verts)
                stack += [y for v in x.verts for y in v.link_edges if y.is_boundary and y not in seen]
            loops.append([o.matrix_world @ v.co for v in vs])
        bm.free()
    rim = min(loops, key=lambda L: min(p.z for p in L))     # the lowest loop: the neck rim
    kd = kdtree.KDTree(len(verts))
    for i, p in enumerate(verts):
        kd.insert(p, i)
    kd.balance()
    rim = [(p, normals[kd.find(p)[1]]) for p in rim]
    return {"pts": verts, "normals": normals, "polys": polys, "rim": rim}


def neck_center(G, z):
    """On the line through Neck_0 and Neck_1, held at Neck_0 below it: the neck leans forward,
    and carried on down that line the center ended up behind the upper back, which then counted
    as the front of the neck and was pulled in (a pit between the shoulder blades)."""
    a, b = G["Neck_0"], G["Neck_1"]
    return a + (b - a) * max(0.0, (z - a.z) / (b.z - a.z))


def polar(G, p):
    c = neck_center(G, p.z)
    dx, dy = p.x - c.x, p.y - c.y
    return (math.degrees(math.atan2(dx, -dy)) % 360.0), math.hypot(dx, dy), c


def around(ang, front, sides, back=None):
    """`front` at 0 degrees, `sides` at 90 / 270, `back` (else `sides`) at 180, smooth between."""
    a = abs((ang + 180.0) % 360.0 - 180.0)
    back = sides if back is None else back
    if a <= 90.0:
        return front + (sides - front) * smoothstep(0.0, 90.0, a)
    return sides + (back - sides) * smoothstep(90.0, 180.0, a)


def ray_hit(bvh, G, ang, z):
    """Where a level ray from the neck axis at height z, direction `ang`, first meets a surface:
    (radius, the surface's tangent going up in the radius-height plane), or None."""
    c = neck_center(G, z)
    d = Vector((math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0.0))
    loc, nrm, _, dist = bvh.ray_cast(Vector((c.x, c.y, z)), d, 0.4)
    if loc is None:
        return None
    nr, nz = nrm.dot(d), nrm.z
    if nr < 0:
        nr, nz = -nr, -nz
    k = math.hypot(nr, nz) or 1.0
    return dist, (-nz / k, nr / k)


def hermite(A, TA, B, TB, n):
    """n + 1 points of the cubic Hermite curve from A to B (unit tangents scaled by the chord)."""
    L = (B - A).length
    out = []
    for i in range(n + 1):
        t = i / n
        h00, h10 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t
        h01, h11 = -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
        out.append(A * h00 + TA * (L * h10) + B * h01 + TB * (L * h11))
    return out


def resample(pts, n):
    """n + 1 points evenly spaced along polyline pts."""
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + (b - a).length)
    out, j = [], 0
    for i in range(n + 1):
        d = acc[-1] * i / n
        while j < len(pts) - 2 and acc[j + 1] < d:
            j += 1
        seg = acc[j + 1] - acc[j]
        out.append(pts[j].lerp(pts[j + 1], (d - acc[j]) / seg if seg > 0 else 0.0))
    return out


class FaceNeck:
    """The face's neck: its rim (every vertex in order around: angle, position, the face's normal
    there) and its surface (for rays). One profile per rim vertex once built."""
    def __init__(self, G, face):
        from mathutils.bvhtree import BVHTree
        self.G = G
        self.rim = sorted(((polar(G, p)[0], p, n) for p, n in face["rim"]), key=lambda t: t[0])
        self.angles = [a for a, _, _ in self.rim]
        self.bvh = BVHTree.FromPolygons(face["pts"], face["polys"])
        self.curves = None

    def to_world(self, ang, r, z):
        c = neck_center(self.G, z)
        a = math.radians(ang)
        return Vector((c.x + r * math.sin(a), c.y - r * math.cos(a), z))

    @staticmethod
    def up_tangent(ang, n):
        """A surface normal -> the surface's tangent going up, in the radius-height plane at ang."""
        d = Vector((math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0.0))
        nr, nz = n.dot(d), n.z
        if nr < 0:
            nr, nz = -nr, -nz
        k = math.hypot(nr, nz) or 1.0
        return Vector((-nz / k, nr / k))

    def bracket(self, ang):
        """The rim vertices either side of angle ang, and the share of the way between them."""
        import bisect
        A, n = self.angles, len(self.angles)
        ang %= 360.0
        i = bisect.bisect_right(A, ang)
        k0, k1 = (i - 1) % n, i % n
        a0 = A[k0] - (360.0 if i == 0 else 0.0)
        a1 = A[k1] + (360.0 if i == n else 0.0)
        return k0, k1, (ang - a0) / max(a1 - a0, 1e-9)

    def edge(self, ang):
        """The rim's height at angle ang."""
        k0, k1, t = self.bracket(ang)
        return self.rim[k0][1].z + (self.rim[k1][1].z - self.rim[k0][1].z) * t

    def face_r(self, ang, z):
        h = ray_hit(self.bvh, self.G, ang, z)
        return h[0] if h else None

    def build(self, body_bvh):
        """One profile per rim vertex (radius-height plane), from where it meets the body (A) up
        to that vertex (B), a Hermite curve leaving the body along its surface and reaching the
        rim along the face's (the plane of the face's normal there). A: the body's surface
        nearest the point NECK_DEPTH below B along a line NECK_SLOPE out from straight down (so
        the feet go round smoothly: trapezius at the sides, upper chest, upper back under
        MakeHuman's bulge behind the neck, which goes)."""
        G, n = self.G, len(self.rim)
        cols = []
        for ang, p, nrm in self.rim:
            B, TB = Vector((polar(G, p)[1], p.z)), self.up_tangent(ang, nrm)
            depth = around(ang, *NECK_DEPTH)
            aim = self.to_world(ang, B.x + depth * math.tan(math.radians(around(ang, *NECK_SLOPE))), p.z - depth)
            cols.append((ang, p, B, TB, aim))
        self.curves = []
        for ang, p, B, TB, aim in cols:
            loc, nrm = body_bvh.find_nearest(aim)[:2]
            if os.environ.get("NECK_DEBUG"):
                log(f"  foot {ang:5.1f}: r {polar(G, loc)[1] * 100:.1f} cm, {(loc.z - p.z) * 100:+.1f} cm, "
                    f"{(loc - aim).length * 100:.1f} cm off the aim")
            A, TA = Vector((polar(G, loc)[1], loc.z)), self.up_tangent(ang, nrm)
            chord = (B - A).normalized()
            while TA.y < 0.25:                  # leave the body rising, never dipping first
                TA = (TA + chord * 0.25).normalized()
            self.curves.append(resample(hermite(A, TA, B, TB, NECK_SAMPLES * 2), NECK_SAMPLES))
        log("  neck: profiles meet the body at " + ", ".join(
            f"{ang:.0f}deg r {c[0].x * 100:.1f} {(c[0].y - B.y) * 100:+.1f}cm"
            for (ang, _, B, _, _), c in list(zip(cols, self.curves))[::6]))
        # And the profiles between their ends (they stay on the body and on the rim).
        keep = [1.0 - smoothstep(0.0, 0.15, i / NECK_SAMPLES) * (1.0 - smoothstep(0.75, 0.95, i / NECK_SAMPLES))
                for i in range(NECK_SAMPLES + 1)]
        for _ in range(NECK_SMOOTH):
            self.curves = [[(self.curves[(k - 1) % n][i] + self.curves[k][i] * 2 + self.curves[(k + 1) % n][i]) / 4
                            * (1 - keep[i]) + self.curves[k][i] * keep[i]
                            for i in range(NECK_SAMPLES + 1)] for k in range(n)]
        # A profile never dips below where it has been (neighbours meeting the body far lower
        # pull its middle down): everything under a dip would count as past its foot.
        for c in self.curves:
            for i in range(1, len(c)):
                c[i].y = max(c[i].y, c[i - 1].y)

    def curve(self, ang):
        k0, k1, t = self.bracket(ang)
        return [p.lerp(q, t) for p, q in zip(self.curves[k0], self.curves[k1])]

    def past_foot(self, co):
        """Which side of its direction's foot point co lies, along the chord from the foot up to
        the rim (m): positive toward the rim (MakeHuman's there goes), negative on the body.
        Only near the feet does it matter (`contour_cut` takes the side the head is on)."""
        ang, r, _ = polar(self.G, co)
        if r > 0.25 or co.z < 1.2:
            return -1.0
        c = self.curve(ang)
        return (Vector((r, co.z)) - c[0]).dot((c[-1] - c[0]).normalized())


def curve_at(curve, t):
    f = max(0.0, min(1.0, t)) * (len(curve) - 1)
    i = min(int(f), len(curve) - 2)
    return curve[i].lerp(curve[i + 1], f - i)


def contour_cut(bm, s_of):
    """Cut the mesh along the zero line of a scalar on its vertices (edges crossing it are split
    where it crosses, faces split between those points) and delete the positive side the topmost
    face is on, and anything left hanging loose: a clean edge instead of a row of whole faces'
    teeth, and the scalar only has to be right near the cut."""
    import bmesh
    s = {v: s_of(v.co) for v in bm.verts}
    zero = set()
    for e in list(bm.edges):
        a, b = e.verts
        sa, sb = s[a], s[b]
        if sa * sb < 0:
            _, nv = bmesh.utils.edge_split(e, a, sa / (sa - sb))
            s[nv] = 0.0
            zero.add(nv)
    for f in list(bm.faces):
        vs = [v for v in f.verts if v in zero]
        if len(vs) == 2 and not any(vs[1] in (lp.link_loop_next.vert, lp.link_loop_prev.vert)
                                    for lp in f.loops if lp.vert is vs[0]):
            bmesh.utils.face_split(f, vs[0], vs[1])
    positive = {f for f in bm.faces if max(s[v] for v in f.verts) > 0 and min(s[v] for v in f.verts) >= 0}

    def spread(start, inside):
        seen, stack = {start}, [start]
        while stack:
            f = stack.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g not in seen and inside(g):
                        seen.add(g)
                        stack.append(g)
        return seen
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    bmesh.ops.delete(bm, geom=list(spread(top, lambda g: g in positive)), context="FACES")
    parts, left = [], set(bm.faces)
    while left:
        part = spread(next(iter(left)), lambda g: True)
        parts.append(part)
        left -= part
    parts.sort(key=len)
    bmesh.ops.delete(bm, geom=[f for part in parts[:-1] for f in part], context="FACES")
    log(f"  neck: cut along the profiles' feet; {len(parts) - 1} loose pieces "
        f"({sum(len(p) for p in parts[:-1])} faces) dropped")


def zip_rings(bm, lower, lower_ang, upper, upper_ang):
    """Triangles between two closed rings of vertices (each in order of growing angle around the
    neck, with its angles), walking round both by angle: always on along the ring whose next
    vertex comes first."""
    def from_ref(ring, angs, ref):
        s = min(range(len(ring)), key=lambda i: (angs[i] - ref) % 360.0)
        ring, angs = ring[s:] + ring[:s], angs[s:] + angs[:s]
        out = []
        for a in angs:
            u = ref + (a - ref) % 360.0
            out.append(u if not out or u >= out[-1] else u + 360.0)
        return ring, out
    ref = lower_ang[0]
    lower, la = from_ref(lower, lower_ang, ref)
    upper, ua = from_ref(upper, upper_ang, ref)
    n, m = len(lower), len(upper)
    i = j = 0
    faces = []
    while i < n or j < m:
        a_next = la[i + 1] if i + 1 < n else la[0] + 360.0
        b_next = ua[j + 1] if j + 1 < m else ua[0] + 360.0
        if j >= m or (i < n and a_next <= b_next):
            faces.append(bm.faces.new((lower[i % n], lower[(i + 1) % n], upper[j % m])))
            i += 1
        else:
            faces.append(bm.faces.new((lower[i % n], upper[(j + 1) % m], upper[j % m])))
            j += 1
    return faces


def neck_tube(bm, G, neck):
    """Our neck from the cut (where the profiles start) up to the face's rim, built new: two
    columns per rim vertex (one on it, one halfway to the next), NECK_ROWS rows along the
    profiles; the top row is the face's rim itself, one vertex per rim vertex, at exactly its
    position (as the game's innerwear meets the face). The cut (MakeHuman's vertices, set onto
    the profiles' start) zips onto the first row. Weights and UVs come from the nearest vertex of
    the cut."""
    deform = bm.verts.layers.deform.verify()
    uv = bm.loops.layers.uv.active
    edges = [e for e in bm.edges if e.is_boundary and min(v.co.z for v in e.verts) > 1.30
             and max(polar(G, v.co)[1] for v in e.verts) < 0.22]
    adj = {}
    for e in edges:
        a, b = e.verts
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    loops, seen = [], set()
    for start in adj:               # the cut's loops; the neck's is the longest
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [v for v in adj[cur] if v is not prev and (v not in seen or v is start)]
            if not nxt or nxt[0] is start:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        loops.append(loop)
    if os.environ.get("NECK_DEBUG"):
        for lp in sorted(loops, key=len, reverse=True)[:6]:
            log(f"  cut loop: {len(lp)} verts, z {min(v.co.z for v in lp):.3f}..{max(v.co.z for v in lp):.3f}, "
                f"r {min(polar(G, v.co)[1] for v in lp) * 100:.1f}..{max(polar(G, v.co)[1] for v in lp) * 100:.1f} cm")
    loop = max(loops, key=len)
    n = len(loop)
    angs = [polar(G, v.co)[0] for v in loop]
    steps = [((angs[(i + 1) % n] - angs[i] + 180.0) % 360.0) - 180.0 for i in range(n)]
    if sum(steps) < 0:              # go round with growing angles
        loop.reverse()
        angs.reverse()
        steps = [((angs[(i + 1) % n] - angs[i] + 180.0) % 360.0) - 180.0 for i in range(n)]
    steps = [max(d, 0.05) for d in steps]            # no column steps back (teeth of the cut)
    k = 360.0 / sum(steps)
    col_ang = [angs[0]]
    for d in steps[:-1]:
        col_ang.append(col_ang[-1] + d * k)

    def place(ang, t):
        p = curve_at(neck.curve(ang % 360.0), t)
        c = neck_center(G, p.y)
        a = math.radians(ang)
        return Vector((c.x + p.x * math.sin(a), c.y - p.x * math.cos(a), p.y))

    def nearest_cut(ang):
        return min(range(n), key=lambda i: abs((col_ang[i] - ang + 180.0) % 360.0 - 180.0))

    for v in loop:                  # (on the profiles' start already, give or take the cut's chords)
        v.co = place(polar(G, v.co)[0], 0.0)
    cut_w = [dict(v[deform]) for v in loop]
    cut_uv = [v.link_loops[0][uv].uv.copy() if uv and v.link_loops else None for v in loop]
    vert_uv = {v: u for v, u in zip(loop, cut_uv)}

    def new_vert(co, ang):
        nv = bm.verts.new(co)
        i = nearest_cut(ang)
        for g, x in cut_w[i].items():
            nv[deform][g] = x
        vert_uv[nv] = cut_uv[i]
        return nv

    m = len(neck.rim)
    angs = []
    for k in range(m):
        a0, a1 = neck.angles[k], neck.angles[(k + 1) % m]
        angs += [a0, a0 + ((a1 - a0) % 360.0) / 2]
    rows = [[new_vert(place(a, row / NECK_ROWS), a) for a in angs] for row in range(1, NECK_ROWS)]
    rim = [new_vert(p.copy(), a) for a, p, _ in neck.rim]
    bm.verts.ensure_lookup_table()
    made = zip_rings(bm, loop, col_ang, rows[0], angs)
    for low, up in zip(rows, rows[1:]):
        for i in range(2 * m):
            j = (i + 1) % (2 * m)
            made.append(bm.faces.new((low[i], low[j], up[j], up[i])))
    top = rows[-1]
    for k in range(m):
        a, b, c = top[2 * k], top[2 * k + 1], top[(2 * k + 2) % (2 * m)]
        made += [bm.faces.new((a, b, rim[k])), bm.faces.new((b, rim[(k + 1) % m], rim[k])),
                 bm.faces.new((b, c, rim[(k + 1) % m]))]
    if uv:
        for f in made:
            for lp in f.loops:
                u = vert_uv.get(lp.vert)
                if u is not None:
                    lp[uv].uv = u
    # Facing out?
    votes = 0
    for f in made:
        f.normal_update()
        ang, _, _ = polar(G, f.calc_center_median())
        out = Vector((math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0.0))
        votes += 1 if f.normal.dot(out) > 0 else -1
    if votes < 0:
        for f in made:
            f.normal_flip()
    log(f"  neck: the cut ({n} vertices) zipped onto {2 * m} columns x {NECK_ROWS - 1} rows, up to the "
        f"face's rim ({m} vertices)")


def rim_lookup(neck):
    """KD tree over the face's rim vertices (index into neck.rim)."""
    from mathutils import kdtree
    kd = kdtree.KDTree(len(neck.rim))
    for i, (_, p, _) in enumerate(neck.rim):
        kd.insert(p, i)
    kd.balance()
    return kd


def match_face_normals(obj, G, neck, face):
    """Shading across the seam: on the rim our vertices take the face's own normals there (custom
    normals, which the exporter writes), as the game's innerwear does, so no line shows."""
    me = obj.data
    me.update()
    kd = rim_lookup(neck)
    out, n = [], 0
    for v in me.vertices:
        normal = v.normal.copy()
        _, i, d = kd.find(v.co)
        if d < 1e-6:
            normal = neck.rim[i][2].copy()
            n += 1
        out.append(normal)
    me.normals_split_custom_set_from_vertices(out)
    log(f"  neck: {n} rim normals are the face's")


def face_neck_weights(face_objs, arm):
    """The face's skin weights around its neck (KD tree, weights per vertex), bone names the
    body's skeleton has (else the name without its _HJ_ helper suffix)."""
    from mathutils import kdtree
    pts = []
    for o in face_outer(face_objs):
        names = {g.index: g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            p = o.matrix_world @ v.co
            if p.z > 1.62:                 # the rim and a little above it, the nape included
                continue
            ws = {}
            for ge in v.groups:
                if ge.weight <= 0:
                    continue
                b = names[ge.group]
                if b not in arm.data.bones:
                    b = b.split("_HJ_")[0]
                if b in arm.data.bones:
                    ws[b] = ws.get(b, 0.0) + ge.weight
            if ws:
                pts.append((p, ws))
    tree = kdtree.KDTree(len(pts))
    for i, (p, _) in enumerate(pts):
        tree.insert(p, i)
    tree.balance()
    log(f"  face neck weights: {len(pts)} vertices, bones {sorted({b for _, ws in pts for b in ws})}")
    return tree, [ws for _, ws in pts]


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
        from mathutils.bvhtree import BVHTree
        neck.build(BVHTree.FromPolygons([v.co for v in me.vertices], [list(p.vertices) for p in me.polygons]))
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    if neck:
        contour_cut(bm, neck.past_foot)
    else:
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z > NECK_CUT], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    if neck:
        neck_tube(bm, G, neck)
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
    return neck


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
    """Below the ankles the feet are scaled in height so the soles stand on the ground (z 0):
    since the feet keep MakeHuman's angle that is under a centimetre either way."""
    ankle = (G["L_Foot"].z + G["R_Foot"].z) / 2
    vs = [v for v in obj.data.vertices if v.co.z < ankle and abs(v.co.x) < 0.4]
    sole = min(v.co.z for v in vs)
    if abs(sole) > 0.002:
        k = ankle / (ankle - sole)
        for v in vs:
            v.co.z = ankle + (v.co.z - ankle) * k
        log(f"  feet: sole {sole:+.3f} -> 0 (below the ankle at {ankle:.3f})")


# Feet, in cm along the foot from the ankle joint (user 2026-10-03: "the feet are too long"). Aimed
# at the game's Instep and squashed onto the ground they were 29 cm, longer than the hunter's boot
# (28); at MakeHuman's own angle they are ~25.6 (heel -5.6, tip 20.0), scaled to ~24.5 here.
FOOT = {"tip": 19.0, "heel": -5.5}


def shorten_feet(obj, G):
    """Scale each foot along its length (front and back of the ankle separately) to FOOT; full
    below the ankle, fading out just above it."""
    ankle = (G["L_Foot"].z + G["R_Foot"].z) / 2
    e1, h1 = FOOT["tip"] / 100, FOOT["heel"] / 100
    for S, s in (("L_", "L"), ("R_", "R")):
        o = G[S + "Foot"]
        d = G[S + "Toe"] - o
        d.z = 0
        d.normalize()
        vs = [v for v in obj.data.vertices if v.co.z < ankle + 0.03 and (v.co.x > 0) == (s == "L")
              and abs(v.co.x) < 0.4]
        f = {v.index: (v.co - o).dot(d) for v in vs}
        e0, h0 = max(f.values()), min(f.values())
        for v in vs:
            x = f[v.index]
            g = x * (e1 / e0 if x > 0 else h1 / h0)
            w = min(1.0, max(0.0, (ankle + 0.03 - v.co.z) / 0.06))
            v.co += d * ((g - x) * w)
        log(f"  {s} foot: heel {h0 * 100:.1f} -> {h1 * 100:.1f}, tip {e0 * 100:.1f} -> {e1 * 100:.1f} cm")


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
    shorten_feet(obj, G)
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
    neck = cut_and_paint(obj, G, skin, cloth, face_pts, params.get("underwear", "boxer"))
    if neck:
        match_face_normals(obj, G, neck, face_pts)
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


# Near the face's rim the body takes the face's weights (the rim is skinned to the game's helper
# joints, Neck_0_HJ_00, Spine_2_HJ_00, the traps and shoulders'): fully from NECK_W[1] below the
# rim up, fading out by NECK_W[0] below it, so the seam doesn't open when the head moves.
NECK_W = (0.035, 0.005)


def blend_face_weights(obj, G, neck, tree, face_ws):
    me = obj.data
    groups = {g.name: g for g in obj.vertex_groups}
    names = {g.index: g.name for g in obj.vertex_groups}
    n = 0
    for v in me.vertices:
        if v.co.z < 1.36 or v.co.z > 1.75:
            continue
        ang, _, _ = polar(G, v.co)
        edge = neck.edge(ang)
        w = smoothstep(edge - NECK_W[0], edge - NECK_W[1], v.co.z)
        if w <= 0:
            continue
        near = tree.find_n(v.co, 4)
        if near and near[0][2] < 1e-6:          # on the rim: exactly the face's weights there
            near, w = near[:1], 1.0
        inv = [(1.0 / max(d, 1e-4), i) for _, i, d in near]
        tot = sum(k for k, _ in inv)
        acc = {}
        for k, i in inv:
            for b, x in face_ws[i].items():
                acc[b] = acc.get(b, 0.0) + w * x * k / tot
        for ge in v.groups:
            acc[names[ge.group]] = acc.get(names[ge.group], 0.0) + (1 - w) * ge.weight
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:MAX_WEIGHTS]
        total = sum(x for _, x in top) or 1.0
        for ge in list(v.groups):
            groups[names[ge.group]].remove([v.index])
        for b, x in top:
            if b not in groups:
                groups[b] = obj.vertex_groups.new(name=b)
                names[groups[b].index] = b
            groups[b].add([v.index], x / total, "REPLACE")
        n += 1
    log(f"  face weights blended into {n} neck vertices")


MESH_EXT, MDF_EXT = ".241111606", ".45"
REL = "Art/Model/MiquellaLight/Character"
# Our material -> (game material name, dual blades material it is copied from).
GAME_MATERIALS = {"Skin": ("MiquellaSkin", "MiquellaIvory"), "Underwear": ("MiquellaCloth", "MiquellaGrip")}
# Our own flat textures (sRGB albedo; roughness 0..1). The dual blades' textures these materials
# started from have broken NRRO (2026-10-03: converted in the cloud they read roughness 0.03,
# normal Y -0.9, AO 0.22 = dark, mirror-like), so the body no longer uses them.
# NRRO = roughness, normal Y, AO, normal X (as the game's face: R varies, G 127, B 255, A 126).
BODY_TEXTURES = {"MiquellaSkin": ((234, 199, 172), 0.55), "MiquellaCloth": ((226, 218, 200), 0.8)}


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


def prepare_for_export(me):
    """RE Mesh Editor reworks a mesh that has quads (bmesh triangulation) or vertices with more
    than one UV (split along the UV islands, normals carried over from a copy by nearest surface)
    and both lose our custom normals (the rim's, `match_face_normals`: they read back up to 24
    degrees off). Done here first, the normals put back per vertex by position, so the exporter
    leaves the mesh alone."""
    import bmesh
    from mathutils import kdtree
    normals = [Vector() for _ in me.vertices]
    for li, lp in enumerate(me.loops):
        normals[lp.vertex_index] += Vector(me.corner_normals[li].vector)
    kd = kdtree.KDTree(len(me.vertices))
    for v in me.vertices:
        kd.insert(v.co, v.index)
    kd.balance()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    uv = bm.loops.layers.uv.active
    if uv:
        def uv_at(f, v):
            return next(lp[uv].uv for lp in f.loops if lp.vert is v)
        seams = [e for e in bm.edges if len(e.link_faces) == 2 and any(
            (uv_at(e.link_faces[0], v) - uv_at(e.link_faces[1], v)).length > 1e-6 for v in e.verts)]
        bmesh.ops.split_edges(bm, edges=seams)
    bm.to_mesh(me)
    bm.free()
    me.normals_split_custom_set_from_vertices([normals[kd.find(v.co)[1]].normalized() for v in me.vertices])


def make_textures(kit_dir):
    """Flat ALBD and NRRO per body material: PNG (texture_sources) -> DDS (BC7) -> Wilds .tex in
    natives/.../Character/tex. Returns {material: {texture type: path in the game}}."""
    import ctypes
    import numpy as np
    from PIL import Image
    if os.name == "nt":                 # texconv reads PNGs through WIC (COM)
        ctypes.windll.ole32.CoInitializeEx(None, 0)
    from re_mesh_editor.modules.ddsconv.directx.texconv import Texconv, unload_texconv
    from re_mesh_editor.modules.tex.blender_re_tex import convertTexDDSList
    src = os.path.join(kit_dir, "texture_sources")
    dds = os.path.join(kit_dir, "dds")
    tex = os.path.join(kit_dir, "natives", "STM", *REL.split("/"), "tex")
    for d in (src, dds, tex):
        os.makedirs(d, exist_ok=True)
    conv = Texconv()
    paths = {}
    for mat, (rgb, rough) in BODY_TEXTURES.items():
        for kind, rgba, fmt in (("ALBD", list(rgb) + [255], "BC7_UNORM_SRGB"),
                                ("NRRO", [round(rough * 255), 128, 255, 128], "BC7_UNORM")):
            png = os.path.join(src, f"{mat}_{kind}.png")
            Image.fromarray(np.full((256, 256, 4), rgba, dtype=np.uint8), "RGBA").save(png)
            conv.convert_to_dds(file=png, dds_fmt=fmt, out=dds, no_mip=False, verbose=False,
                                allow_slow_codec=True)
            kind_name = "BaseDielectricMap" if kind == "ALBD" else "NormalRoughnessOcclusionMap"
            paths.setdefault(mat, {})[kind_name] = f"{REL}/tex/{mat}_{kind}.tex"
    unload_texconv()
    names = [f for f in os.listdir(dds) if f.endswith(".dds")]
    ok, failed = convertTexDDSList(names, dds, tex, "MHWILDS")
    log(f"textures: {len(names)} dds -> {ok} tex ({failed} failed)")
    return paths


def write_mdf(path, template_mdf, textures=None):
    import copy
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    template = readMDF(template_mdf)
    by_name = {m.materialName: m for m in template.materialList}
    mats = []
    for game_mat, source in GAME_MATERIALS.values():
        new = copy.deepcopy(by_name[source])
        new.materialName = game_mat
        for t in new.textureList:
            if textures and t.textureType in textures.get(game_mat, {}):
                t.texturePath = textures[game_mat][t.textureType]
        mats.append(new)
    template.materialList = mats
    writeMDF(template, path)
    log(f"mdf: {[(m.materialName, [t.texturePath for t in m.textureList if 'Art/' in t.texturePath]) for m in readMDF(path).materialList]}")


def kit(data, game_body, face, kit_dir, template_mdf):
    import common as c
    c.reset_scene()
    enable_addon()
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile
    arm, _ = import_game(game_body, keep_meshes=False)
    G = game_joints(arm)
    _, face_objs = import_game(face, keep_meshes=True)
    face_pts = face_geometry(face_objs)
    neck = FaceNeck(G, face_pts)
    tree, face_ws = face_neck_weights(face_objs, arm)
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
        blend_face_weights(body, G, neck, tree, face_ws)
        mesh_col = bpy.data.collections.new(f"{name}.mesh")
        bpy.context.scene.collection.children.link(mesh_col)
        for col in list(arm.users_collection):
            col.objects.unlink(arm)
        mesh_col.objects.link(arm)
        subs = split_for_export(body, mesh_col)
        for o in subs:
            prepare_for_export(o.data)
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
    write_mdf(os.path.join(natives, f"mq_body.mdf2{MDF_EXT}"), template_mdf, make_textures(kit_dir))
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
    face_pts = face_geometry(face_objs) if face_objs else None
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
    if cmd == "lines":
        data, game_body, out = (os.path.abspath(a) for a in sys.argv[2:5])
        os.makedirs(out, exist_ok=True)
        preview_abs(data, game_body, out, options=LINE_OPTIONS, center_z=1.13, scale=0.62, prefix="lines",
                    views=(("front", 0), ("quarter", 35), ("back", 180)))
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
