"""Robe, game version (2026-10-04): the robe of robe_designs.py as a Wilds .mesh on the hunter's
skeleton, spawned by MiquellaLight_Character.lua like the body (SameJointsConstraint).

- shape: robe_designs.Fit / build_skirt on the body kit's own mesh (mq_body_c / mq_body_c_f), the
  same cloth the previews showed;
- the fitted part (bodice, sleeves) takes the body's weights (nearest point on the body, its
  triangle's weights interpolated: the face blend at the neck, the game's helper joints on the legs);
- the skirt swings on the skirt chains of a game leg armor, ch03_025_0015 (12 chains of 6 joints
  around the hips, from HipJiggle_CH_00 on Hip_HJ_00): its bones are merged into our skeleton under
  their own names, the twelve skirt chains moved onto our skirt (CH_00 at the skirt's top, the
  rest evenly down to the hem), and the character script gives the object a via.motion.Chain2 with
  the game's own ch03_025_0015.chain2 (loaded by its path: nothing of Capcom's in our pak). The
  chain2 names its chains by their end joints (*_CH_end, murmur3 hashes); its other chains (belt,
  waist plates, bag, knife) find their bones too and move nothing. The male version of that armor
  has no chain2: both sexes use the female one (it only needs the joint names);
- the skirt's weights: the two chains around each column (by angle), the two joints along them
  (by row; the top segment mostly on CH_00), blended from the body's weights over the top
  TOP_BLEND (the hips);
- two-sided (the armor skirt materials' BaseTwoSideEnable): the inside shows when it swings;
- a woven ivory cloth tiled at TILE, UVs per part (torso and skirt around the body's axis, sleeves
  around the arm's) shifted by whole tiles in blocks: the UVs are half floats in the file.

Usage: bpy45 python robe_kit.py <smooth|lines|drape|cinch> <female|male> [preview <out dir>]
The drapes (drape: sash loose on the hips, cinch: at the waist) carry the gold of version D and the
broad collar (robe_designs.gold_work, collar "strands") as a second sub-mesh, MiquellaRobeGold.
Writes mq_robe_<fit>_c[_f].mesh, mq_robe.mdf2 (cloth + gold, the drapes) and mq_robe_cloth.mdf2 (the fitted
robes: a mesh only links an mdf2 of its own materials) (+ tex) into MiquellaLight_Character_kit.
`robe_kit.py mdf` writes only the materials.
"""
import math
import os
import random
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import miquella_body as mb  # noqa: E402
import robe_designs as rd  # noqa: E402

EXTRACTED = "C:/Users/anton/MiquellaTools/extracted/natives/stm/art/model/character"
KIT = "C:/Users/anton/ForClaude/mods/miquella/mhws/MiquellaLight_Character_kit"
NATIVES = os.path.join(KIT, "natives", "STM", *mb.REL.split("/"))
TEMPLATE_MDF = ("C:/Users/anton/ForClaude/mods/miquella/mhws/MiquellaLight_DualBlades_kit/natives/STM/Art/"
                "Model/MiquellaLight/DualBlades/wp_miquella_db.mdf2.45")
SKIRT_ARMOR = EXTRACTED + "/ch03/025/001/5/ch03_025_0015.mesh.241111606"
CHAINS = ["L_F_Skirt", "L_SF_Skirt1", "L_SF_Skirt2", "L_SB_Skirt1", "L_SB_Skirt2", "L_B_Skirt",
          "R_B_Skirt", "R_SB_Skirt2", "R_SB_Skirt1", "R_SF_Skirt2", "R_SF_Skirt1", "R_F_Skirt"]
TOP_BLEND = 0.06      # m below the skirt's top: the body's weights hand over to the chains
TILE = 0.024          # m of cloth per texture tile (16 threads: 1.5 mm threads)
TEX = 512             # px
THREADS = 16
UV_BLOCK = 8          # tiles: UVs shifted by whole multiples of this per face (half-float precision)
TORSO_TILES = 39      # tiles around the torso (u = angle * radius), ~0.149 m radius
ARM_TILES = 12        # tiles around a sleeve, ~0.046 m radius
ARM_REACH = 0.085     # m from the arm's bones: sleeve (UV mapped around the arm)
ROBE_RGB = (230, 221, 199)   # sRGB ivory ("米白")
ROBE_ROUGH = 0.82
MATERIAL = "MiquellaRobe"
GOLD = "MiquellaRobeGold"          # the drapes' jewellery: gold metal (ALBD alpha 0, as the devices' gold)
GOLD_RGB = (226, 176, 74)          # sRGB, the devices' gold
GOLD_ROUGH = 0.27
GOLD_FACES = 60000                 # triangles at most (the collar's strands are many tubes)
DRAPES = ("drape", "cinch")
GOLD_EMISSIVE_MAP = "systems/rendering/NullWhite.tex"
SOURCE_MATERIAL = "MiquellaGrip"   # the dual blades' weapon shader, as the briefs (proven in game)


def log(*a):
    print("[robe]", *a, flush=True)


# ------------------------------------------------------------------ the game's side

def import_body(path):
    """The body kit mesh with its skeleton: (armature, meshes baked to world space, weights kept)."""
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile
    before = set(bpy.data.objects)
    importREMeshFile(path, mb.IMPORT_OPTS)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    meshes = [o for o in new if o.type == "MESH"]
    for o in meshes:
        mw = o.matrix_world.copy()
        o.parent = None
        o.modifiers.clear()
        o.data.transform(mw)
        o.matrix_world = Matrix.Identity(4)
    log("body:", [o.name for o in meshes], "bones", len(arm.data.bones), "armature at",
        tuple(round(x, 3) for x in arm.matrix_world.to_euler()))
    return arm, meshes


def merge_skirt_bones(arm):
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile
    assert arm.name == arm.data.name, (arm.name, arm.data.name)   # the importer looks it up both ways
    n0 = len(arm.data.bones)
    before = set(bpy.data.objects)
    importREMeshFile(SKIRT_ARMOR, dict(mb.IMPORT_OPTS, mergeArmature=arm.data.name))
    for o in [o for o in bpy.data.objects if o not in before]:
        bpy.data.objects.remove(o, do_unlink=True)
    log(f"skirt armor bones merged: {n0} -> {len(arm.data.bones)}")


def chain_bones(arm, name):
    """The chain's joint names, root first. Names, not bpy Bone references: those go stale (and
    then point at other bones) whenever the armature goes through edit mode."""
    out = [arm.data.bones[f"{name}_CH_00"]]
    while True:
        kids = [c for c in out[-1].children if c.name.startswith(name + "_CH_")]
        if not kids:
            return [b.name for b in out]
        out.append(kids[0])


def file_matrix(bone, key="reMeshWorldMatrix"):
    return np.array([list(r) for r in bone[key]], dtype=float)


def to_file(p):
    """Blender space (z up, -y front) -> the file's (y up, +z front)."""
    return np.array([p.x, p.z, -p.y])


def rotation_between(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v, c = np.cross(a, b), float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k * (1 / (1 + c))


def move_chain(arm, names, points):
    """Set the chain's joints at points (Blender space): the file's world matrices (row-major,
    translation in the last row) moved there, each turned by the turn of its segment (the joint's
    own axes keep their relation to the segment); local and inverse matrices to match."""
    bones = [arm.data.bones[n] for n in names]
    old = [file_matrix(b) for b in bones]
    new_pos = [to_file(p) for p in points]
    news = []
    for k, b in enumerate(bones):
        j = min(k, len(bones) - 2)
        R = rotation_between(old[j + 1][3, :3] - old[j][3, :3], new_pos[j + 1] - new_pos[j])
        W = old[k].copy()
        W[:3, :3] = old[k][:3, :3] @ R.T
        W[3, :3] = new_pos[k]
        news.append(W)
    for k, b in enumerate(bones):
        parent_w = news[k - 1] if k else file_matrix(b.parent)
        b["reMeshWorldMatrix"] = news[k].tolist()
        b["reMeshLocalMatrix"] = (news[k] @ np.linalg.inv(parent_w)).tolist()
        b["reMeshInverseMatrix"] = np.linalg.inv(news[k]).tolist()
    # Blender's own bones the same way (the exporter writes the matrices above; this is for the
    # previews, which pose the armature)
    olds = [b.head_local.copy() for b in bones]
    mats = []
    for k, b in enumerate(bones):
        j = min(k, len(bones) - 2)
        q = (olds[j + 1] - olds[j]).rotation_difference(points[j + 1] - points[j])
        mats.append(Matrix.Translation(points[k]) @ (q.to_matrix() @ b.matrix_local.to_3x3()).to_4x4())
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for n, m in zip(names, mats):
        arm.data.edit_bones[n].matrix = m
    bpy.ops.object.mode_set(mode="OBJECT")


def check_matrix_convention(arm):
    """The stored local matrices should be world @ inverse(parent world) (row vectors)."""
    worst = 0.0
    for name in ("L_F_Skirt_CH_01", "Spine_1", "L_Forearm"):
        b = arm.data.bones[name]
        L = file_matrix(b, "reMeshLocalMatrix")
        guess = file_matrix(b) @ np.linalg.inv(file_matrix(b.parent))
        worst = max(worst, float(np.abs(L - guess).max()))
    log(f"local = world @ inv(parent world): worst difference {worst:.2e}")
    assert worst < 1e-3, "matrix convention"


# ------------------------------------------------------------------ weights

def body_weight_source(body_objs, arm):
    from mathutils.interpolate import poly_3d_calc
    bvh, verts, polys, ws = mb.leg_weights(body_objs, arm)

    def at(co):
        loc, _, fi, _ = bvh.find_nearest(co)
        corners = polys[fi]
        bary = poly_3d_calc([verts[i] for i in corners], loc)
        acc = {}
        for k, i in zip(bary, corners):
            for b, x in ws[i].items():
                acc[b] = acc.get(b, 0.0) + k * x
        return acc
    return at


def top_weights(acc):
    top = sorted(acc.items(), key=lambda kv: -kv[1])[:mb.MAX_WEIGHTS]
    total = sum(x for _, x in top) or 1.0
    return [(b, x / total) for b, x in top if x > 1e-4]


def mix(a, b, t):
    out = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0.0) + v * t
    return out


# ------------------------------------------------------------------ the cloth's texture

def weave_images():
    """A plain weave, THREADS x THREADS per tile, tileable: ALBD (ivory, threads a little uneven,
    darker between them) and NRRO (roughness, normal Y, AO, normal X, as the body's)."""
    n, p = TEX, TEX // THREADS
    rng = np.random.default_rng(5)
    y, x = np.mgrid[0:n, 0:n].astype(float)
    i, a = np.floor(x / p).astype(int), (x % p + 0.5) / p      # warp thread (along v) and across it
    j, b = np.floor(y / p).astype(int), (y % p + 0.5) / p      # weft thread (along u)
    over = np.where((i + j) % 2 == 0, 1.0, -1.0)               # warp over weft here
    prof_w, prof_f = np.sin(np.pi * a) ** 0.6, np.sin(np.pi * b) ** 0.6
    lift_w = 0.6 + 0.4 * over * np.sin(np.pi * b)               # the warp rising over / dipping under
    lift_f = 0.6 - 0.4 * over * np.sin(np.pi * a)
    tw = rng.uniform(0.9, 1.1, THREADS)[i % THREADS]          # thread thickness, per thread
    tf = rng.uniform(0.9, 1.1, THREADS)[j % THREADS]
    hw, hf = prof_w * lift_w * tw, prof_f * lift_f * tf
    h = np.maximum(hw, hf)
    shade_w = rng.uniform(0.96, 1.04, THREADS)[i % THREADS]
    shade_f = rng.uniform(0.96, 1.04, THREADS)[j % THREADS]
    shade = np.where(hw >= hf, shade_w, shade_f) * (0.86 + 0.14 * np.clip(h, 0, 1))
    albd = np.zeros((n, n, 4), dtype=np.uint8)
    for c in range(3):
        albd[..., c] = np.clip(ROBE_RGB[c] * shade, 0, 255).astype(np.uint8)
    albd[..., 3] = 255
    k = 0.9   # slope scale: threads tilt up to ~35 degrees
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * p / 2
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * p / 2
    nx, ny, nz = -dx * k, -dy * k, np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nrro = np.zeros((n, n, 4), dtype=np.uint8)
    nrro[..., 0] = np.clip(255 * (ROBE_ROUGH + 0.06 * (1 - h)), 0, 255).astype(np.uint8)
    nrro[..., 1] = np.clip(127.5 + 127.5 * ny / ln, 0, 255).astype(np.uint8)
    nrro[..., 2] = np.clip(255 * (0.75 + 0.25 * np.clip(h, 0, 1)), 0, 255).astype(np.uint8)
    nrro[..., 3] = np.clip(127.5 + 127.5 * nx / ln, 0, 255).astype(np.uint8)
    return [(MATERIAL, "ALBD", albd), (MATERIAL, "NRRO", nrro)]


def gold_images():
    """Flat gold metal: ALBD alpha 0 = metal (the devices' gold zone reads so), polished."""
    albd = np.zeros((64, 64, 4), dtype=np.uint8)
    albd[..., :3] = GOLD_RGB
    nrro = np.full((64, 64, 4), [round(GOLD_ROUGH * 255), 128, 255, 128], dtype=np.uint8)
    return [(GOLD, "ALBD", albd), (GOLD, "NRRO", nrro)]


def name_of(fit_name, female):
    return f"mq_robe_{fit_name}_c{'_f' if female else ''}"


def gold_object(objs, bm, per_vert, name):
    """robe_designs' gold work (curves and meshes) as one triangulated mesh, decimated to
    GOLD_FACES, each vertex on the weights of the nearest vertex of the cloth (the collar follows
    the chest, the cords and drops the skirt's front), UVs all in the middle (a flat texture)."""
    from mathutils import kdtree
    dg = bpy.context.evaluated_depsgraph_get()
    gb = bmesh.new()
    for o in objs:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        me.transform(o.matrix_world)
        gb.from_mesh(me)
        bpy.data.meshes.remove(me)
        bpy.data.objects.remove(o, do_unlink=True)
    bmesh.ops.triangulate(gb, faces=gb.faces[:])
    n0 = len(gb.faces)
    me = bpy.data.meshes.new(name + "_gold")
    gb.to_mesh(me)
    gb.free()
    ob = bpy.data.objects.new(name + "_gold", me)
    bpy.context.scene.collection.objects.link(ob)
    if n0 > GOLD_FACES:
        mod = ob.modifiers.new("Decimate", "DECIMATE")
        mod.ratio = GOLD_FACES / n0
        dg = bpy.context.evaluated_depsgraph_get()
        dec = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.remove(mod)
        ob.data = dec
        me = dec
        tb = bmesh.new()
        tb.from_mesh(me)
        bmesh.ops.triangulate(tb, faces=tb.faces[:])
        tb.to_mesh(me)
        tb.free()
    for p in me.polygons:
        p.use_smooth = True
    uv = me.uv_layers.new(name="UV")
    for lp in uv.data:
        lp.uv = (0.5, 0.5)
    me.materials.clear()
    me.materials.append(bpy.data.materials.get(GOLD) or bpy.data.materials.new(GOLD))
    verts = list(bm.verts)
    kd = kdtree.KDTree(len(verts))
    for i, v in enumerate(verts):
        kd.insert(v.co, i)
    kd.balance()
    groups = {}
    for v in me.vertices:
        _, i, _ = kd.find(v.co)
        for b, w in per_vert[verts[i]]:
            if b not in groups:
                groups[b] = ob.vertex_groups.new(name=b)
            groups[b].add([v.index], w, "REPLACE")
    ob.color = (0.85, 0.6, 0.15, 1)
    log(f"gold: {len(objs)} pieces, {n0} -> {len(me.polygons)} triangles, {len(me.vertices)} verts")
    return ob


def write_robe_mdf(path, textures):
    import copy
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    template = readMDF(TEMPLATE_MDF)
    src = next(m for m in template.materialList if m.materialName == SOURCE_MATERIAL)
    new = copy.deepcopy(src)
    new.materialName = MATERIAL
    for t in new.textureList:
        if t.textureType in textures[MATERIAL]:
            t.texturePath = textures[MATERIAL][t.textureType]
    new.flags.flagValues.BaseTwoSideEnable = 1
    gold = copy.deepcopy(src)
    gold.materialName = GOLD
    for t in gold.textureList:
        if t.textureType in textures[GOLD]:
            t.texturePath = textures[GOLD][t.textureType]
        elif t.textureType == "EmissiveMap":
            # white: the script tints the emission gold and sets how much (metal alone reads brown
            # in game, 2026-10-04); the source's black map would keep it off whatever the values
            t.texturePath = GOLD_EMISSIVE_MAP
    # The fitted robes have no gold: an mdf2 with materials their mesh lacks does not link (the
    # mesh's get_MaterialLinked fails) and the cloth renders black (2026-10-04, in game)
    for out, materials in ((path, [new, gold]), (path.replace("mq_robe.", "mq_robe_cloth."), [new])):
        template.materialList = materials
        writeMDF(template, out)
        for back in readMDF(out).materialList:
            log("mdf:", os.path.basename(out), back.materialName, "two-sided",
                bool(back.flags.flagValues.BaseTwoSideEnable),
                [t.texturePath for t in back.textureList if "MiquellaLight" in t.texturePath or t.textureType == "EmissiveMap"])


# ------------------------------------------------------------------ UVs

class Mapper:
    def __init__(self, fit, J):
        self.fit = fit
        self.arms = {s: (J[f"{s}_UpperArm"], J[f"{s}_Forearm"], J[f"{s}_Hand"]) for s in "LR"}
        self.r_torso = TORSO_TILES * TILE / (2 * math.pi)
        self.r_arm = ARM_TILES * TILE / (2 * math.pi)

    def arm_side(self, co):
        """L / R on the sleeve: past the shoulder joint along the arm and close to the arm's bones
        (the torso under the armpit is past that plane too)."""
        s = "L" if co.x > 0 else "R"
        a, b, c = self.arms[s]
        if (co - a).dot((b - a).normalized()) <= 0.03:
            return None
        near = min((co - (p + (q - p) * max(0.0, min(1.0, (co - p).dot(q - p) / (q - p).length_squared)))).length
                   for p, q in ((a, b), (b, c)))
        return s if near < ARM_REACH else None

    def torso(self, co):
        th = self.fit.theta(co)
        return [th * self.r_torso / TILE, co.z / TILE, th]

    def sleeve(self, s, co):
        a, b, c = self.arms[s]
        best = None
        acc = 0.0
        for p, q in ((a, b), (b, c)):
            d = q - p
            t = max(0.0, min(1.0, (co - p).dot(d) / d.length_squared))
            r = (co - (p + d * t)).length
            if best is None or r < best[0]:
                best = (r, p + d * t, d.normalized(), acc + d.length * t)
            acc += d.length
        _, foot, axis, along = best
        up = Vector((0, 0, 1))
        ref = (up - axis * axis.dot(up)).normalized()
        side = axis.cross(ref)
        w = co - foot
        phi = math.atan2(w.dot(side), w.dot(ref))       # +-pi under the arm: the seam
        return [phi * self.r_arm / TILE, along / TILE, phi]


def unwrap(bm, mapper, skirt_rc, grid, ang):
    # The robe is a copy of the body (fit.build) and came with the body's UVs: left first, they were
    # the ones exported, the weave spread over the body's UV islands (2026-10-04, in game: threads
    # centimetres wide, the arms and torso in blocks). Only ours.
    for old in list(bm.loops.layers.uv):
        bm.loops.layers.uv.remove(old)
    uv = bm.loops.layers.uv.new("UV")
    cols = len(grid[0])
    # skirt: around by the row's own circumference (whole tiles), down by the column's length
    per_row = []
    for row in grid:
        per = sum((row[k].co - row[(k + 1) % cols].co).length for k in range(cols))
        per_row.append(max(1, round(per / TILE)))
    down = [[0.0] * cols for _ in grid]
    for j in range(cols):
        for i in range(1, len(grid)):
            down[i][j] = down[i - 1][j] + (grid[i][j].co - grid[i - 1][j].co).length
    kinds = {}
    for f in bm.faces:
        rcs = [skirt_rc.get(v) for v in f.verts]
        if all(rcs):
            js = [j for _, j in rcs]
            wrap = max(js) - min(js) > cols / 2
            pts = [[(cols if wrap and j == 0 else j) / cols * per_row[i], down[i][j] / TILE, 0.0] for i, j in rcs]
            kind = "skirt"
        else:
            sides = [mapper.arm_side(v.co) for v in f.verts]
            s = max(set(sides), key=sides.count)
            if s:
                pts = [mapper.sleeve(s, v.co) for v in f.verts]
                r = mapper.r_arm
            else:
                pts = [mapper.torso(v.co) for v in f.verts]
                r = mapper.r_torso
            kind = "sleeve" if s else "torso"
            if max(p[2] for p in pts) - min(p[2] for p in pts) > math.pi:   # across the seam
                for p in pts:
                    if p[2] < 0:
                        p[0] += 2 * math.pi * r / TILE
        kinds[kind] = kinds.get(kind, 0) + 1
        mu = sum(p[0] for p in pts) / len(pts)
        mv = sum(p[1] for p in pts) / len(pts)
        ou, ov = UV_BLOCK * math.floor(mu / UV_BLOCK), UV_BLOCK * math.floor(mv / UV_BLOCK)
        for lp, p in zip(f.loops, pts):
            lp[uv].uv = (p[0] - ou, 1.0 - (p[1] - ov))
    log("uv faces:", kinds)


def split_by_uv(obj):
    """Triangles, loose vertices gone, one vertex per (vertex, UV): the exporter takes one UV per
    vertex (and reworks the mesh, losing our normals, if it has to split it itself:
    miquella_body.prepare_for_export). Normals smoothed over the seams first."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    normals = [Vector() for _ in me.vertices]
    for p in me.polygons:
        for vi in p.vertices:
            normals[vi] += p.normal * p.area
    uvl = me.uv_layers.active.data
    group_names = [g.name for g in obj.vertex_groups]
    groups = [[(g.group, g.weight) for g in v.groups] for v in me.vertices]
    index, src, uvs, faces = {}, [], [], []
    for p in me.polygons:
        f = []
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            u, v = uvl[li].uv
            key = (vi, round(u, 5), round(v, 5))
            if key not in index:
                index[key] = len(src)
                src.append(vi)
                uvs.append((u, v))
            f.append(index[key])
        faces.append(f)
    new = bpy.data.meshes.new(me.name)
    new.from_pydata([me.vertices[i].co.copy() for i in src], [], faces)
    layer = new.uv_layers.new(name="UV")
    for p in new.polygons:
        p.use_smooth = True
        for li in p.loop_indices:
            layer.data[li].uv = uvs[new.loops[li].vertex_index]
    for m in me.materials:
        new.materials.append(m)
    obj.data = new          # vertex group names live on the mesh: made again
    vg = [obj.vertex_groups.get(n) or obj.vertex_groups.new(name=n) for n in group_names]
    for k, vi in enumerate(src):
        for g, w in groups[vi]:
            vg[g].add([k], w, "REPLACE")
    new.normals_split_custom_set_from_vertices([normals[i].normalized() for i in src])
    log(f"split by UV: {len(me.vertices)} -> {len(new.vertices)} verts ({len(loose)} loose removed)")


# ------------------------------------------------------------------ build

def build(fit_name, female, preview_dir=None):
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable("re_mesh_editor", default_set=True)
    suffix = "_f" if female else ""
    arm, body = import_body(os.path.join(NATIVES, f"mq_body_c{suffix}.mesh{mb.MESH_EXT}"))
    global J_BASE
    J_BASE = [b.name for b in arm.data.bones]
    merge_skirt_bones(arm)
    check_matrix_convention(arm)
    J = mb.game_joints(arm)
    fit = rd.Fit(body, J)
    bm = fit.build(fit_name)
    # The cloth was copied from the body's bmesh, deform layer and all: its group indices (the
    # body object's) would land on our groups by number and mix leg weights into the shoulders.
    # (Removed now: removing a layer remakes the BMVerts, keys of the tables below.)
    for layer in list(bm.verts.layers.deform.values()):
        bm.verts.layers.deform.remove(layer)
    style = fit_name if fit_name in DRAPES else "hip"
    grid, ang, center = rd.build_skirt(bm, fit, random.Random(7), style=style)
    if fit_name != "lines":
        rd.soften_waist(bm, fit)
    if style != "hip":
        # as the previews: the clearance search's 2 mm steps left ripples across the hanging cloth
        skirt = [v for row in grid[1:-1] for v in row]
        for _ in range(2):
            rd.taubin(skirt, 25)
            fit.push_out(skirt, rd.GAP)
        bm.normal_update()
    # the drapes' gold (before the winding is settled below: gold_work recalculates the normals)
    gold_objs = rd.gold_work("D", bm, grid, fit, collar_kind="strands") if style != "hip" else []
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    out = sum((f.normal.to_2d().dot((f.calc_center_median() - center).to_2d()) for f in bm.faces
               if {v for v in f.verts} <= set(grid[len(grid) // 2])) or [0.0])
    if out < 0:   # inward: flip all (recalc picks a side on an open mesh)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    skirt_rc = {v: (i, j) for i, row in enumerate(grid) for j, v in enumerate(row)}
    rows, cols = len(grid) - 1, len(grid[0])
    log(f"robe: {len(bm.verts)} verts, {len(bm.faces)} faces; skirt {rows + 1} x {cols}")
    # Where the chains start, per column: the skirt's top on the fitted robes; on the drapes the
    # hanging cloth starts at the chest, and down to the hips (the fitted robes' skirt line) it
    # follows the torso on the body's weights, the chains taking over below
    def chain_top(j):
        if style == "hip":
            return 0
        z = rd.angle_blend(ang[j], *rd.SKIRT_TOP)
        return min(range(rows + 1), key=lambda i: abs(grid[i][j].co.z - z))
    top_row = [chain_top(j) for j in range(cols)]

    # the skirt chains onto our skirt
    chains = []
    for name in CHAINS:
        bones = chain_bones(arm, name)
        p0 = J[bones[0]]
        a = math.atan2(p0.x - center.x, -(p0.y - center.y)) % (2 * math.pi)
        j = min(range(cols), key=lambda k: abs(math.remainder(ang[k] - a, 2 * math.pi)))
        r0 = top_row[j]
        jr = [r0 + round(k * (rows - r0) / (len(bones) - 1)) for k in range(len(bones))]
        move_chain(arm, bones, [grid[r][j].co for r in jr])
        chains.append((a, name, bones, jr, j))
    chains.sort()
    log("chains (angle, column, joints):", [(round(math.degrees(a)), j, len(b)) for a, _, b, _, j in chains])

    # weights
    body_w = body_weight_source(body, arm)
    per_vert = {}
    for v in bm.verts:
        rc = skirt_rc.get(v)
        if not rc:
            per_vert[v] = top_weights(body_w(v.co))
            continue
        i, j = rc
        a = ang[j]
        n = len(chains)
        k = next((k for k in range(n) if chains[k][0] <= a < chains[(k + 1) % n][0] + (2 * math.pi if k == n - 1 else 0)),
                 n - 1)
        a0, a1 = chains[k][0], chains[(k + 1) % n][0]
        span = (a1 - a0) % (2 * math.pi)
        t = ((a - a0) % (2 * math.pi)) / span if span else 0.0
        acc = {}
        for c, wc in ((chains[k], 1 - t), (chains[(k + 1) % n], t)):
            _, _, bones, jr, _ = c
            if i <= jr[0]:
                seg, s = 0, 0.0
            else:
                seg = max(s for s in range(len(jr) - 1) if jr[s] <= i)
                s = (i - jr[seg]) / (jr[seg + 1] - jr[seg])
            if seg == 0:
                # the top segment hugs the hips: rows above CH_01 turn about it (inward when the
                # skirt swings out, into the hips, 13 mm at 20 degrees on straight lerp): kept
                # mostly on CH_00 (5 mm)
                s = s ** 3
            for bone, w in ((bones[seg], 1 - s), (bones[seg + 1], s)):
                acc[bone] = acc.get(bone, 0.0) + wc * w
        dz = grid[top_row[j]][j].co.z - v.co.z
        beta = 1 - mb.smoothstep(0.0, TOP_BLEND, dz)
        if beta > 0:
            acc = mix(acc, body_w(v.co), beta)
        per_vert[v] = top_weights(acc)

    gold = None
    if style != "hip":
        gold = gold_object(gold_objs, bm, per_vert, name_of(fit_name, female))
    mapper = Mapper(fit, J)
    unwrap(bm, mapper, skirt_rc, grid, ang)
    bm.verts.index_update()
    name = name_of(fit_name, female)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    robe = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(robe)
    for p in me.polygons:
        p.use_smooth = True
    groups = {}
    for v in bm.verts:
        for b, w in per_vert[v]:
            if b not in groups:
                groups[b] = robe.vertex_groups.new(name=b)
            groups[b].add([v.index], w, "REPLACE")
    base_bones = set(J_BASE)
    odd = {}
    for v in bm.verts:
        if v.co.z > 1.0:
            for b, w in per_vert[v]:
                if b not in base_bones and w > 0.01:
                    odd[b] = odd.get(b, 0) + 1
    log("verts above 1 m on the skirt armor's bones:", odd)
    legs = set()
    for side in "LR":
        stack = [arm.data.bones[f"{side}_Thigh"]]
        while stack:
            b = stack.pop()
            legs.add(b.name)
            stack.extend(b.children)
    high = {}
    for v in bm.verts:
        if v.co.z > 1.2:
            for b, w in per_vert[v]:
                if b in legs and w > 0.01:
                    high[b] = high.get(b, 0) + 1
    log("verts above 1.2 m on the leg bones:", high)
    missing = [g for g in groups if g not in arm.data.bones]
    log(f"weights on {len(groups)} bones; not in the skeleton: {missing}")
    assert not missing
    mat = bpy.data.materials.new(MATERIAL)
    me.materials.append(mat)

    if preview_dir:
        global DEBUG_PER_VERT
        DEBUG_PER_VERT = [per_vert[v] for v in bm.verts]
        preview(robe, body, arm, chains, preview_dir, name, gold)

    # export
    for o in body:
        bpy.data.objects.remove(o, do_unlink=True)
    mesh_col = bpy.data.collections.new(f"{name}.mesh")
    bpy.context.scene.collection.children.link(mesh_col)
    for col in list(arm.users_collection):
        col.objects.unlink(arm)
    mesh_col.objects.link(arm)
    robe.name = f"Group_0_Sub_0__{MATERIAL}"
    for col in list(robe.users_collection):
        col.objects.unlink(robe)
    mesh_col.objects.link(robe)
    split_by_uv(robe)
    mb.position_colors(robe.data)
    robe.modifiers.new("Armature", "ARMATURE").object = arm
    robe.parent = arm
    if gold:
        gold.name = f"Group_0_Sub_1__{GOLD}"
        for col in list(gold.users_collection):
            col.objects.unlink(gold)
        mesh_col.objects.link(gold)
        for m in list(gold.modifiers):
            gold.modifiers.remove(m)
        split_by_uv(gold)
        mb.position_colors(gold.data)
        gold.modifiers.new("Armature", "ARMATURE").object = arm
        gold.parent = arm
    path = os.path.join(NATIVES, f"{name}.mesh{mb.MESH_EXT}")
    ok = exportREMeshFile(path, {"targetCollection": mesh_col.name, "selectedOnly": False,
                                 "exportAllLODs": False, "exportBlendShapes": False, "rotate90": True,
                                 "useBlenderMaterialName": False, "preserveBoneMatrices": True,
                                 "exportBoundingBoxes": False, "autoSolveRepeatedUVs": True,
                                 "preserveSharpEdges": False})
    log(f"export {name}: {ok} ({os.path.getsize(path)} bytes), {len(robe.data.vertices)} verts"
        + (f" + gold {len(gold.data.vertices)}" if gold else ""))
    textures = mb.images_to_tex(KIT, weave_images() + gold_images())
    write_robe_mdf(os.path.join(NATIVES, f"mq_robe.mdf2{mb.MDF_EXT}"), textures)
    verify(path, chains)


def verify(path, chains):
    """Read the file back: the skirt joints where we put them, the weights on them."""
    from re_mesh_editor.modules.mesh.file_re_mesh import readREMesh
    from re_mesh_editor.modules.mesh.re_mesh_parse import ParsedREMesh
    parsed = ParsedREMesh()
    parsed.ParseREMesh(readREMesh(path, 0), {"importAllLOD": False, "importShadowMesh": False,
                                             "importOcclusionMesh": False, "importBlendShapes": False})
    bones = {b.boneName: b for b in parsed.skeleton.boneList}
    names = [b.boneName for b in parsed.skeleton.boneList]
    weighted = parsed.skeleton.weightedBones
    used = {}
    nverts = 0
    for lod in parsed.mainMeshLODList[:1]:
        for g in lod.visconGroupList:
            for sub in g.subMeshList:
                nverts += len(sub.vertexPosList)
                for idx, w in zip(sub.weightIndicesList, sub.weightList):
                    for i, x in zip(idx, w):
                        if x > 0.01:
                            used[weighted[i]] = used.get(weighted[i], 0) + 1
    log(f"read back: {len(names)} bones, {nverts} verts, weighted to {len(used)} bones")
    for _, name, bs, _, _ in chains[:2]:
        for n in bs:
            fb = bones[n]
            m = np.array(fb.worldMatrix.matrix)
            parent = names[fb.parentIndex] if fb.parentIndex >= 0 else "-"
            log(f"  {n:20s} parent {parent:20s} at {np.round(m[3][:3], 3)} verts {used.get(n, 0)}")
    for need in ("HipJiggle_CH_00", "Hip_HJ_00", "Hip", "Spine_2", "L_Forearm"):
        log(f"  {need}: in skeleton {need in bones}, verts {used.get(need, 0)}")


# ------------------------------------------------------------------ preview

def preview(robe, body, arm, chains, out, name, gold=None):
    """Workbench renders: rest pose, and the skirt chains swung (CH_01 turned 25 degrees outward,
    the back ones forward) to see the weights carry the cloth."""
    os.makedirs(out, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "OBJECT"
    scene.render.resolution_x, scene.render.resolution_y = 700, 1000
    robe.color = (0.88, 0.81, 0.64, 1)
    for o in body:
        o.color = (0.80, 0.52, 0.42, 1)
    mod = robe.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    if gold:
        gold.modifiers.new("Armature", "ARMATURE").object = arm
    for o in body:
        m = o.modifiers.new("Armature", "ARMATURE")
        m.object = arm
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 1.9
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    paths = []

    def shoot(tag, deg):
        a = math.radians(deg)
        cam.location = (math.sin(a) * 4, -math.cos(a) * 4, 0.9)
        cam.rotation_euler = (math.radians(90), 0, a)
        scene.render.filepath = os.path.join(out, f"{name}_{tag}_{deg}.png")
        bpy.ops.render.render(write_still=True)
        paths.append(scene.render.filepath)

    for deg in (0, 90, 180):
        shoot("rest", deg)
    # swing: pose mode rotations on the chains' second joints
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    for a, _, bones, _, _ in chains:
        pb = arm.pose.bones[bones[1]]
        pb.rotation_mode = "XYZ"
        # turn about the horizontal axis tangent to the skirt: outward
        tangent = Vector((math.cos(a), math.sin(a), 0))
        local = pb.bone.matrix_local.to_3x3().inverted() @ tangent
        pb.rotation_mode = "AXIS_ANGLE"
        pb.rotation_axis_angle = (math.radians(-20), *local)   # tangent x down = inward: negative turns out
    bpy.ops.object.mode_set(mode="OBJECT")
    for deg in (0, 90):
        shoot("swing", deg)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.rotation_axis_angle = (0, 0, 1, 0)
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
    # a step: left thigh forward 35 degrees, right back 15
    for side, deg in (("L", -35), ("R", 15)):
        pb = arm.pose.bones[f"{side}_Thigh"]
        pb.rotation_mode = "AXIS_ANGLE"
        axis = pb.bone.matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))
        pb.rotation_axis_angle = (math.radians(deg), *axis)
    bpy.ops.object.mode_set(mode="OBJECT")
    for deg in (90, 0, 180):
        shoot("step", deg)
    # which vertices moved far in the step, and their bones (a debug of 2026-10-04)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = robe.evaluated_get(dg).to_mesh()
    far = [v.index for v, e in zip(robe.data.vertices, ev.vertices) if v.co.z > 1.05 and (e.co - v.co).length > 0.05]
    names = {g.index: g.name for g in robe.vertex_groups}
    tally = {}
    for i in far:
        for g in robe.data.vertices[i].groups:
            if g.weight > 0.05:
                tally[names[g.group]] = tally.get(names[g.group], 0) + 1
    for i in sorted(far, key=lambda i: -robe.data.vertices[i].co.z)[:4] + far[:2]:
        v = robe.data.vertices[i]
        log(f"  v{i} at {tuple(round(x, 3) for x in v.co)} moved {tuple(round(x, 3) for x in ev.vertices[i].co)}; "
            f"mesh {[(names[g.group], round(g.weight, 2)) for g in v.groups]}; table {[(b, round(w, 2)) for b, w in DEBUG_PER_VERT[i]]}")
    robe.evaluated_get(dg).to_mesh_clear()
    log(f"step: {len(far)} verts above 1.05 m moved > 5 cm; their bones:",
        sorted(tally.items(), key=lambda kv: -kv[1])[:15])
    for b in sorted(tally, key=lambda k: -tally[k])[:6]:
        chain, x = [], arm.data.bones[b]
        while x:
            chain.append(x.name)
            x = x.parent
        log(f"  {b}: parents {chain[1:8]}")
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
    robe.modifiers.remove(mod)
    log("preview:", paths)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if args[0] == "mdf":   # only the materials (and their textures), no meshes
        textures = mb.images_to_tex(KIT, weave_images() + gold_images())
        write_robe_mdf(os.path.join(NATIVES, f"mq_robe.mdf2{mb.MDF_EXT}"), textures)
        return
    fit_name, sex = args[0], args[1]
    preview_dir = args[args.index("preview") + 1] if "preview" in args else None
    build(fit_name, sex == "female", preview_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout.flush()
        os._exit(0)
