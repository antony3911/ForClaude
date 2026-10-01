"""Build a game kit (.mesh + .mdf2) for a Miquella light weapon from its prototype.

Weapons: great_sword, light_bowgun. Same result as the dual blades pipeline
(build_game_kit.py + fit_dual_blades.py) in one pass, on Windows:
- builds the prototype geometry, lowers its resolution and joins it per game material;
- places it the way the game's originals are placed (file space, measured from the
  originals, see the kit READMEs): great sword along +Z with the hand just below the guard
  and the edge toward -X; light bowgun along +Z with up = +Y and the bore 0.19 below the origin;
- takes the skeleton from an original and moves its effect bones (blade tip, muzzle) onto
  our model, every vertex on Base;
- copies the materials from the dual blades kit .mdf2 (current game layout, our textures),
  so the textures are the dual blades' (Art/Model/MiquellaLight/DualBlades/tex).

Usage: python build_weapon_kit.py <weapon> <kit dir> <original *_0.mesh.241111606> <dual blades .mdf2.45>
Requires bpy 4.5 with RE Mesh Editor in the user addons dir. The originals are only read.
"""
import copy
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
MESH_EXT, MDF_EXT = ".241111606", ".45"
# File space -> Blender space as RE Mesh Editor writes it (rotate90): (x, y, z) -> (x, -z, y).
FILE_TO_BLENDER = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def log(msg):
    print(f"[kit] {msg}", flush=True)


# ------------------------------------------------------------------ weapons

def great_sword():
    """Grip lengthened from 0.36 to 0.48 so both hands fit (the originals' handles reach
    about 0.8 m below the hand); scaled 1.6x so the blade is ~1.9 m like the originals
    (2.0-2.2 m) but stays slender; turned 180 degrees about Z: the originals' single edges
    and the long sword's curve put the edge on -X, ours was on +X."""
    import arsenal
    gt, k = 0.48, 1.6
    objs, mats, tip = arsenal.great_sword(gt=gt, render=False)
    hand = Vector((0, 0, gt - 0.04))
    to_file = Matrix.Scale(k, 4) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation(-hand)
    return {
        "name": "wp_miquella_gs", "rel": "Art/Model/MiquellaLight/GreatSword",
        "objects": objs, "to_file": to_file,
        "bones": {"VFX_Attack": to_file @ Vector(tip)},
        "materials": {"Blade_Light": "MiquellaBlade", "Light": "MiquellaGlow", "Ivory": "MiquellaIvory",
                      "Blade_Core": "MiquellaTemper", "Membrane": "MiquellaGlow"},
        "by_name": {},
    }


def light_bowgun():
    """Prototype axes: +Y muzzle, +Z up. Scaled 1.6x (originals are ~1.5 m long, ours
    0.93 m); bore placed 0.19 below the origin (the originals' muzzle bones sit at y -0.16
    to -0.23; their origin is on top of the receiver); moved back 0.1 so the pistol grip
    sits where the originals' grips do, about 0.3 behind the origin. The three lit drops
    over the barrel get their own materials, to work as the rapid-fire gauge later."""
    import light_bowgun as lb
    import bowgun as hb
    lb.build()
    k, bore_y, back = 1.6, -0.19, -0.10
    axes = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))      # x->-x, z->y, y->z
    to_file = (Matrix.Translation((0, bore_y, back)) @ Matrix.Scale(k, 4) @ axes
               @ Matrix.Translation((0, 0, -hb.CONDUIT_Z)))
    muzzle = to_file @ Vector((0, hb.MUZZLE + 0.01, hb.CONDUIT_Z))
    by_name = {}
    for i in range(3):
        by_name[f"Barrel_Phial_{i}"] = f"MiquellaGauge{i + 1}"
        by_name[f"Barrel_Phial_Halo_{i}"] = f"MiquellaGauge{i + 1}"
    return {
        "name": "wp_miquella_lbg", "rel": "Art/Model/MiquellaLight/LightBowgun",
        "objects": [o for o in bpy.data.objects if o.type in ("MESH", "CURVE")], "to_file": to_file,
        "bones": {"VFX_Fire": muzzle, "VFX_FireLong": muzzle, "VFX_FireSuppressor": muzzle},
        "materials": {"Ivory": "MiquellaIvory", "Light": "MiquellaGlow", "Beam": "MiquellaBlade"},
        "by_name": by_name,
    }


WEAPONS = {"great_sword": great_sword, "light_bowgun": light_bowgun}

# Triangle budget per game material (the originals run 5k-60k triangles in all).
BUDGET = {"MiquellaBlade": 8000, "MiquellaGlow": 12000, "MiquellaIvory": 24000, "MiquellaTemper": 1500}
GAUGE_BUDGET = 1500

# Material copied from the dual blades kit for each of our game materials.
MDF_SOURCE = {"MiquellaBlade": "MiquellaBlade", "MiquellaGlow": "MiquellaGlow",
              "MiquellaIvory": "MiquellaIvory", "MiquellaTemper": "MiquellaGlow",
              "MiquellaGauge1": "MiquellaGlow", "MiquellaGauge2": "MiquellaGlow",
              "MiquellaGauge3": "MiquellaGlow"}


# ------------------------------------------------------------------ geometry

def select_only(objs, active=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def game_material(o, spec):
    for prefix, mat in spec["by_name"].items():
        if o.name == prefix or o.name.startswith(prefix + "."):
            return mat
    names = [s.material.name for s in o.material_slots if s.material]
    for n in names:
        base = n.split(".")[0]
        if base in spec["materials"]:
            return spec["materials"][base]
    log(f"  unmapped material {names} on {o.name} -> MiquellaIvory")
    return "MiquellaIvory"


def lower_resolution(objs):
    """Game budget: thin strands as 4- or 8-sided tubes, at most one subdivision level."""
    for o in objs:
        if o.type == "CURVE":
            o.data.bevel_resolution = 0 if o.data.bevel_depth < 0.003 else 1
            o.data.resolution_u = min(o.data.resolution_u, 4)
        for mod in o.modifiers:
            if mod.type == "SUBSURF":
                mod.levels = mod.render_levels = min(mod.render_levels, 1)


def build_parts(spec, mesh_col):
    objs = [o for o in spec["objects"] if o.name in bpy.data.objects]
    # Unparent and bake transforms so every part shares one space.
    for o in objs:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    lower_resolution(objs)
    groups = {}
    for o in objs:
        groups.setdefault(game_material(o, spec), []).append(o)
    subs = []
    for i, (mat, members) in enumerate(sorted(groups.items())):
        select_only(members)
        bpy.ops.object.convert(target="MESH")
        members = [o for o in bpy.context.selected_objects]
        select_only(members)
        if len(members) > 1:
            bpy.ops.object.join()
        o = bpy.context.view_layer.objects.active
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.name = f"Group_0_Sub_{i}__{mat}"
        o.data.materials.clear()
        o.data.materials.append(bpy.data.materials.get(mat) or bpy.data.materials.new(mat))
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        bpy.ops.mesh.delete_loose()
        bpy.ops.uv.smart_project(island_margin=0.02)
        bpy.ops.object.mode_set(mode="OBJECT")
        before = tris(o)
        ratio = min(1.0, BUDGET.get(mat, GAUGE_BUDGET) / max(before, 1))
        if ratio < 1.0:
            dec = o.modifiers.new("decimate", "DECIMATE")
            dec.ratio = ratio
            bpy.ops.object.modifier_apply(modifier="decimate")
        o.data.transform(FILE_TO_BLENDER @ spec["to_file"])
        for col in list(o.users_collection):
            col.objects.unlink(o)
        mesh_col.objects.link(o)
        subs.append(o)
        log(f"{o.name}: {len(members)} parts, {before} -> {tris(o)} tris")
    log(f"total: {sum(tris(o) for o in subs)} tris")
    return subs


def import_skeleton(orig_mesh, mesh_col, bones):
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile
    opts = {"clearScene": False, "createCollections": True, "loadMaterials": False,
            "loadMDFData": False, "loadShellFur": False, "loadUnusedTextures": False,
            "loadUnusedProps": False, "useBackfaceCulling": False, "reloadCachedTextures": False,
            "mdfPath": "", "importAllLODs": False, "importBlendShapes": False, "rotate90": True,
            "mergeArmature": "", "importArmatureOnly": False, "mergeGroups": False,
            "importShadowMeshes": False, "importOcclusionMeshes": False, "importBoundingBoxes": False}
    before = set(bpy.data.objects)
    importREMeshFile(orig_mesh, opts)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        if o is not arm:
            bpy.data.objects.remove(o, do_unlink=True)
    for col in list(arm.users_collection):
        col.objects.unlink(arm)
    mesh_col.objects.link(arm)
    # Effect bones are children of Base (identity at the origin): RE matrices are row-major
    # with the translation in the last row, in file space; export keeps these stored values.
    for name, pos in bones.items():
        b = arm.data.bones.get(name)
        if b is None or b.get("reMeshWorldMatrix") is None:
            log(f"  bone {name} not in original, skipped")
            continue
        for key, sign in (("reMeshWorldMatrix", 1), ("reMeshLocalMatrix", 1), ("reMeshInverseMatrix", -1)):
            m = [list(r) for r in b[key]]
            m[3][0], m[3][1], m[3][2] = (sign * pos.x, sign * pos.y, sign * pos.z)
            b[key] = m
        log(f"  bone {name} -> ({pos.x:+.3f}, {pos.y:+.3f}, {pos.z:+.3f})")
    log(f"skeleton: {[b.name for b in arm.data.bones]}")
    return arm


def bind(subs, arm):
    for o in subs:
        o.vertex_groups.clear()
        g = o.vertex_groups.new(name="Base")
        g.add(range(len(o.data.vertices)), 1.0, "REPLACE")
        o.modifiers.clear()
        o.modifiers.new("Armature", "ARMATURE").object = arm
        o.parent = arm


def file_bounds(subs):
    inv = FILE_TO_BLENDER.inverted()
    pts = [inv @ v.co for o in subs for v in o.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


# ------------------------------------------------------------------ mdf

def build_mdf(path, template_mdf, names):
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    template = readMDF(template_mdf)
    by_name = {m.materialName: m for m in template.materialList}
    materials = []
    for name in names:
        new = copy.deepcopy(by_name[MDF_SOURCE[name]])
        new.materialName = name
        materials.append(new)
    template.materialList = materials
    writeMDF(template, path)
    check = readMDF(path)
    log(f"mdf: {[m.materialName for m in check.materialList]}")


# ------------------------------------------------------------------ main

def enable_addon():
    """After the prototype is built: its factory reset unregisters add-ons, and the importer
    crashes without its registered properties."""
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)


def main():
    weapon, kit, orig_mesh, template_mdf = sys.argv[1], *(os.path.abspath(a) for a in sys.argv[2:5])
    import common as c

    c.reset_scene()
    spec = WEAPONS[weapon]()
    enable_addon()
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile
    mesh_col = bpy.data.collections.new(f"{spec['name']}.mesh")
    bpy.context.scene.collection.children.link(mesh_col)
    subs = build_parts(spec, mesh_col)
    lo, hi = file_bounds(subs)
    log(f"file-space bounds min=({lo.x:+.3f}, {lo.y:+.3f}, {lo.z:+.3f}) max=({hi.x:+.3f}, {hi.y:+.3f}, {hi.z:+.3f})")
    arm = import_skeleton(orig_mesh, mesh_col, spec["bones"])
    bind(subs, arm)
    # Drop everything that is not part of the export.
    keep = set(subs) | {arm}
    for o in list(bpy.data.objects):
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)

    natives = os.path.join(kit, "natives", "STM", *spec["rel"].split("/"))
    os.makedirs(natives, exist_ok=True)
    path = os.path.join(natives, f"{spec['name']}.mesh{MESH_EXT}")
    ok = exportREMeshFile(path, {"targetCollection": mesh_col.name, "selectedOnly": False,
                                 "exportAllLODs": False, "exportBlendShapes": False, "rotate90": True,
                                 "useBlenderMaterialName": False, "preserveBoneMatrices": True,
                                 "exportBoundingBoxes": False, "autoSolveRepeatedUVs": True,
                                 "preserveSharpEdges": False})
    log(f"export mesh: {ok} -> {path} ({os.path.getsize(path)} bytes)")
    names = [o.name.split("__", 1)[1] for o in subs]
    build_mdf(os.path.join(natives, f"{spec['name']}.mdf2{MDF_EXT}"), template_mdf, names)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(kit, f"{spec['name']}_kit.blend"))


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.flush()
        os._exit(0)     # the addon leaves a thread running
