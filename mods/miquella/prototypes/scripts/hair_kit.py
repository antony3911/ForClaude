"""Hair, game version (2026-10-04): hairstyle 512 as the female hunter wears it (ch01_001_0512;
the user's hunter is female) with Miquella's braids (hair512_braids.py variant A, the design the
user settled on 2026-10-03: 10 thin braids among the waves, a thick braid in front of each
shoulder, the main braid lengthened with 512's own tie and tail moved to its new end).

The character script spawns it in place of the hunter's own 512 (hidden), on the hunter's
skeleton, swinging by 512's own chain2 (Chain2 + ChildSecondary, as the robe; a spawned copy of
512 swings like the real one, research notes section 15). It holds a copy of Capcom's 512 mesh,
moved and added to: a grey area for release, like the recoloured effects (the user decides then).

  - 512's own parts keep their weights; everything new or moved (the braids, their gold ties and
    tails, 512's tail and tie at the new end) copies the weights and vertex colours of 512's
    nearest vertices (the original, before the braid was cut), smoothed along each strand: the
    thin braids swing with the back_hair chains they lie in, the lengthened braid with the hair
    around it
  - the braids are thinned for the game: a ring every RING_STEP and RING_K points round each
    strand (built at 1 mm and 12)
  - strand UVs: v along the strand (mirrored every V_SPAN, so it never ends in a tip), u a narrow
    band round it, in 512's own hair texture (the dense strands at its left)
  - materials: scalp, acc, hair (512's, the game's textures) and MiquellaRobeGold (the robe's
    gold) for the thin braids' ties

Usage (bpy45):
  MIQUELLA_HAIR_SEX=f python hair512_parts.py
  MIQUELLA_HAIR_SEX=f python hair512_braids.py A <MiquellaTools>/work/previews/hair_mq
  python hair_kit.py <extracted natives/stm> <hair_mq_A_f.blend> <MiquellaTools>/work/hair_kit <character kit dir>
The mesh holds Capcom's 512 and the mdf2 copies its materials: both go OUTSIDE the repo
(work/hair_kit, beside the character kit's natives), copied into work/stage_Character for the pak
like the baked skin. The kit dir is read for the robe's gold material.
"""
import math
import os
import re
import sys

import bpy
import bmesh
from mathutils import Vector, kdtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import miquella_body as mb  # noqa: E402

GAME = "art/model/character/ch01/001/0/512/ch01_001_0512"
MESH_OUT = "mq_hair512_f"
MDF_OUT = "mq_hair512"
GOLD = "MiquellaRobeGold"
RING_STEP = 3          # keep every 3rd ring (1 mm apart as built)
RING_K = 2             # and every 2nd point round each ring (12 -> 6)
U0, U_SPAN, DU = 0.02, 0.24, 0.05     # strand u: a DU-wide band starting in [U0, U0 + U_SPAN]
V0, V1, V_SPAN = 0.04, 0.96, 0.12     # strand v: V_SPAN m of strand per pass over [V0, V1]
NEAREST = 4
SMOOTH_PASSES = 4
NEW = re.compile(r"^(main_ext|b\d+|f\d+)(_tie|_tail)?$")


def log(*a):
    print("[hair]", *a, flush=True)


# ------------------------------------------------------------------ the built tubes

def tubes(me):
    """Builder.ring_tube's tubes in a mesh: (first vertex, ring size k, rings), read off the faces
    (each tube's quads, then its two caps: the first ring reversed, the last ring)."""
    out = []
    for p in me.polygons:
        if len(p.vertices) <= 4:
            continue
        vs = list(p.vertices)
        if out and out[-1][3] is None and min(vs) > out[-1][0]:
            first, k, _, _ = out[-1]
            out[-1] = (first, k, (min(vs) - first) // k + 1, True)
        else:
            out.append((min(vs), len(vs), None, None))
    return [(a, k, n) for a, k, n, _ in out if n]


def thin(obj, step=RING_STEP, every=RING_K, keep_k=None):
    """Rebuild the object's tubes with every `step`-th ring (and the last) and every `every`-th
    point round them; UVs per strand; returns the new mesh's per-vertex strand data."""
    me = obj.data
    co = [v.co.copy() for v in me.vertices]
    verts, faces, uvs = [], [], []
    rnd = (hash(obj.name) % 997) / 997.0
    for t, (first, k, n) in enumerate(tubes(me)):
        rings = list(range(0, n, step))
        if rings[-1] != n - 1:
            rings.append(n - 1)
        kk = keep_k or max(4, k // every)
        idx = [round(i * k / kk) % k for i in range(kk)]
        base = len(verts)
        centres = [sum((co[first + j * k + i] for i in range(k)), Vector()) / k for j in rings]
        s = [0.0]
        for a, b in zip(centres, centres[1:]):
            s.append(s[-1] + (b - a).length)
        u0 = U0 + ((rnd + 0.37 * t) % 1.0) * U_SPAN
        for jj, j in enumerate(rings):
            for i in idx:
                verts.append(co[first + j * k + i])
        for jj in range(len(rings) - 1):
            for ii in range(kk):
                a = base + jj * kk + ii
                b = base + jj * kk + (ii + 1) % kk
                faces.append((a, b, b + kk, a + kk))
                tv = []
                for r, q in ((jj, ii), (jj, ii + 1), (jj + 1, ii + 1), (jj + 1, ii)):
                    f = (s[r] / V_SPAN) % 2.0
                    f = f if f < 1.0 else 2.0 - f
                    tv.append((u0 + DU * q / kk, V0 + (V1 - V0) * f))
                uvs.append(tv)
        for cap in (list(range(base, base + kk))[::-1],
                    list(range(base + (len(rings) - 1) * kk, base + len(rings) * kk))):
            faces.append(tuple(cap))
            uvs.append([(u0 + DU * 0.5, V0)] * kk)
    new = bpy.data.meshes.new(obj.name + "_game")
    new.from_pydata(verts, [], faces)
    new.update()
    uvl = new.uv_layers.new(name="UVMap0")
    for poly, tv in zip(new.polygons, uvs):
        for li, uv in zip(poly.loop_indices, tv):
            uvl.data[li].uv = uv
    for p in new.polygons:
        p.use_smooth = True
    old = obj.data
    obj.data = new
    bpy.data.meshes.remove(old)
    return obj


# ------------------------------------------------------------------ weights and colours

class Source:
    """512 as the game ships it: its vertices (world), weights (bone name -> weight) and colours."""
    def __init__(self, path):
        arm, objs = mb.import_game(path, keep_meshes=True)
        self.arm = arm
        hair = next(o for o in objs if "hair" in o.name)
        self.objs = objs
        me = hair.data
        names = {g.index: g.name for g in hair.vertex_groups}
        self.co = [hair.matrix_world @ v.co for v in me.vertices]
        self.w = [{names[g.group]: g.weight for g in v.groups if g.weight > 0} for v in me.vertices]
        col = me.color_attributes.get("Col") or (me.color_attributes[0] if me.color_attributes else None)
        self.col = [None] * len(me.vertices)
        if col is not None:
            for li, lp in enumerate(me.loops):
                if col.domain == "CORNER":
                    self.col[lp.vertex_index] = tuple(col.data[li].color)
            if col.domain == "POINT":
                self.col = [tuple(d.color) for d in col.data]
        self.kd = kdtree.KDTree(len(self.co))
        for i, p in enumerate(self.co):
            self.kd.insert(p, i)
        self.kd.balance()

    def at(self, p):
        near = self.kd.find_n(p, NEAREST)
        acc, colour, tot = {}, Vector((0, 0, 0, 0)), 0.0
        for _, i, d in near:
            k = 1.0 / max(d, 1e-4)
            tot += k
            for b, x in self.w[i].items():
                acc[b] = acc.get(b, 0.0) + x * k
            if self.col[i] is not None:
                colour += Vector(self.col[i]) * k
        top = sorted(acc.items(), key=lambda t: -t[1])[:mb.MAX_WEIGHTS]
        s = sum(x for _, x in top) or 1.0
        return {b: x / s for b, x in top}, tuple(colour / tot) if tot else (1, 1, 1, 1)


def copy_from(obj, src, smooth=True):
    """Weights and colours from 512's nearest vertices, smoothed over the mesh's edges."""
    me = obj.data
    ws, cs = [], []
    for v in me.vertices:
        w, c = src.at(obj.matrix_world @ v.co)
        ws.append(w)
        cs.append(c)
    if smooth:
        nb = [[] for _ in me.vertices]
        for e in me.edges:
            a, b = e.vertices
            nb[a].append(b)
            nb[b].append(a)
        for _ in range(SMOOTH_PASSES):
            new = []
            for i, w in enumerate(ws):
                acc = dict((b, x * 2) for b, x in w.items())
                for j in nb[i]:
                    for b, x in ws[j].items():
                        acc[b] = acc.get(b, 0.0) + x
                top = sorted(acc.items(), key=lambda t: -t[1])[:mb.MAX_WEIGHTS]
                s = sum(x for _, x in top) or 1.0
                new.append({b: x / s for b, x in top})
            ws = new
    obj.vertex_groups.clear()
    groups = {}
    for i, w in enumerate(ws):
        for b, x in w.items():
            if b not in groups:
                groups[b] = obj.vertex_groups.new(name=b)
            groups[b].add([i], x, "REPLACE")
    col = me.color_attributes.get("Col") or me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    for li, lp in enumerate(me.loops):
        col.data[li].color = cs[lp.vertex_index]


# ------------------------------------------------------------------ mdf2

def write_mdf(path, stm, robe_mdf):
    import copy
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    game = readMDF(os.path.join(stm, *(GAME + ".mdf2.45").split("/")))
    robe = readMDF(robe_mdf)
    gold = copy.deepcopy(next(m for m in robe.materialList if m.materialName == GOLD))
    keep = [copy.deepcopy(m) for m in game.materialList if m.materialName in ("scalp", "acc", "hair")]
    game.materialList = keep + [gold]
    writeMDF(game, path)
    log("mdf2", os.path.basename(path), [m.materialName for m in readMDF(path).materialList])


# ------------------------------------------------------------------ main

def main():
    stm, blend, out_dir, kit = sys.argv[1:5]
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile
    bpy.ops.wm.open_mainfile(filepath=blend)
    mb.enable_addon()
    keep = {"Group_1_Sub_1__hair": "hair", "Group_1_Sub_0__acc": "acc", "Group_0_Sub_0__scalp": "scalp",
            "tail512": "hair"}
    parts, new = {}, []
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o.name in keep:
            parts[o.name] = o
        elif o.type == "MESH" and NEW.match(o.name):
            new.append(o)
        else:
            bpy.data.objects.remove(o, do_unlink=True)
    log("512 parts", sorted(parts), "new", len(new))
    src = Source(os.path.join(stm, *(GAME + ".mesh.241111606").split("/")))
    arm = src.arm
    for o in src.objs:
        bpy.data.objects.remove(o, do_unlink=True)

    for o in new:
        if o.name.endswith("_tie"):
            thin(o, step=1, keep_k=8)
        elif o.name.endswith("_tail"):
            thin(o, step=2, keep_k=4)
        else:
            thin(o)
        copy_from(o, src)
    # moved with the lengthened braid: 512's tail and tie, weighted where they now hang
    for name in ("tail512", "Group_1_Sub_0__acc"):
        copy_from(parts[name], src)
    # tail512 came from the hair's own mesh: its UVs and colours are 512's already (copy_from
    # overwrote the colours with the ones around its new place, which is what the shader wants)

    # one object per material, named as RE Mesh Editor reads them
    def join(objs, name):
        objs = [o for o in objs if o]
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        objs[0].name = name
        return objs[0]

    tie_objs = [o for o in new if o.name.endswith("_tie")]
    strand_objs = [o for o in new if not o.name.endswith("_tie")]
    ties = join(tie_objs, f"Group_1_Sub_2__{GOLD}")
    hair = join([parts["Group_1_Sub_1__hair"], parts["tail512"]] + strand_objs, "Group_1_Sub_1__hair")
    out = [parts["Group_0_Sub_0__scalp"], parts["Group_1_Sub_0__acc"], hair, ties]
    mats = {o.name: o.name.split("__")[1] for o in out}
    col = bpy.data.collections.new(f"{MESH_OUT}.mesh")
    bpy.context.scene.collection.children.link(col)
    for o in [arm] + out:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    for o in out:
        o.data.materials.clear()
        m = bpy.data.materials.get(mats[o.name]) or bpy.data.materials.new(mats[o.name])
        o.data.materials.append(m)
        mb.prepare_for_export(o.data)
        o.modifiers.clear()
        o.modifiers.new("Armature", "ARMATURE").object = arm
        o.parent = arm
        log(f"  {o.name}: {len(o.data.vertices)} verts, {len(o.vertex_groups)} groups")
    natives = os.path.join(out_dir, "natives", "STM", *mb.REL.split("/"))
    os.makedirs(natives, exist_ok=True)
    kit_natives = os.path.join(kit, "natives", "STM", *mb.REL.split("/"))
    path = os.path.join(natives, f"{MESH_OUT}.mesh{mb.MESH_EXT}")
    ok = exportREMeshFile(path, {"targetCollection": col.name, "selectedOnly": False,
                                 "exportAllLODs": False, "exportBlendShapes": False, "rotate90": True,
                                 "useBlenderMaterialName": False, "preserveBoneMatrices": True,
                                 "exportBoundingBoxes": False, "autoSolveRepeatedUVs": True,
                                 "preserveSharpEdges": False})
    log("export", ok, path, os.path.getsize(path))
    write_mdf(os.path.join(natives, f"{MDF_OUT}.mdf2{mb.MDF_EXT}"), stm,
              os.path.join(kit_natives, f"mq_robe.mdf2{mb.MDF_EXT}"))


if __name__ == "__main__":
    main()
