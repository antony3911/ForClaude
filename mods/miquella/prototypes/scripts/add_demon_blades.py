"""Add the demon-mode side blades to the fitted dual light blade (see DESIGN.md: one light
blade splits into a three-bladed kunai; the side blades fade in at the blade root and
slide outward, short first, then long).

The weapon has no bones we can animate, so the slide is three fixed stages, each its own
material (MiquellaDemon1..3) holding a left and a right side blade:
  stage 1: 37.7 % length,  9 deg   stage 2: 50.3 %, 15 deg   stage 3: 62 %, 22 deg (final pose)
They branch 7 cm up the main blade from the guard, so the halo at the guard stays visible.
(First in-game version: at the guard, 45 / 60 / 74 %; the user found it crowded near the
grip and the side blades a bit long, and picked option B of states.py dual_blades_split_point.)
They are hidden by default (Dissolve 0). MiquellaLight_Weapons.lua cross-fades them with the
game's demon-mode value (app.cHunterWp02Handling._KijinExtern, 0 -> 1).

Run after fit_dual_blades.py (reads dual_blade_kit_fitted.blend; safe to re-run).
Usage: python add_demon_blades.py <kit dir>
Requires bpy 4.5 with RE Mesh Editor in the user addons dir.
"""
import copy
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(__file__))
import blades
from fit_dual_blades import MDF_EXT, MESH_EXT, NAME, REL_DIR, TO_WEAPON_AXIS

# (length scale, splay angle, sideways offset) per stage, from states.py's preview.
STAGES = ((0.377, 9.0, 0.004), (0.503, 15.0, 0.007), (0.62, 22.0, 0.010))
BRANCH_FORWARD = 0.07     # metres from the guard toward the tip where the side blades branch
SIDE_SCALE_X, SIDE_SCALE_Y = 0.72, 0.8


def log(msg):
    print(f"[demon] {msg}", flush=True)


def side_pair(stage, length, angle, spread, armature, collection):
    mat_name = f"MiquellaDemon{stage}"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    objs = []
    for s in (-1, 1):
        o = blades.build_blade(mat)
        o.modifiers.clear()                                    # no subdivision in game
        pose = (Matrix.Translation((s * spread, 0, blades.GUARD_Z + BRANCH_FORWARD))
                @ Matrix.Rotation(math.radians(s * angle), 4, "Y")
                @ Matrix.Diagonal((SIDE_SCALE_X, SIDE_SCALE_Y, length, 1))
                @ Matrix.Translation((0, 0, -blades.GUARD_Z)))  # pivot at the guard
        o.data.transform(TO_WEAPON_AXIS @ pose)
        objs.append(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = f"Group_0_Sub_{3 + stage}__{mat_name}"
    o.data.materials.clear()
    o.data.materials.append(mat)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    for col in list(o.users_collection):
        col.objects.unlink(o)
    collection.objects.link(o)
    group = o.vertex_groups.new(name="Base")
    group.add(range(len(o.data.vertices)), 1.0, "REPLACE")
    o.modifiers.new("Armature", "ARMATURE").object = armature
    o.parent = armature
    ys = [v.co.y for v in o.data.vertices]
    log(f"{o.name}: {len(o.data.vertices)} verts, tip at {-min(ys):.3f} m")
    return o


def add_materials(path):
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    mdf = readMDF(path)
    mats = [m for m in mdf.materialList if not m.materialName.startswith("MiquellaDemon")]
    blade = next(m for m in mats if m.materialName == "MiquellaBlade")
    for stage in range(1, len(STAGES) + 1):
        m = copy.deepcopy(blade)
        m.materialName = f"MiquellaDemon{stage}"
        for p in m.propertyList:
            if p.propName == "Dissolve":
                p.propValue = [0.0]                            # hidden until demon mode
        mats.append(m)
    mdf.materialList = mats
    writeMDF(mdf, path)
    log(f"materials: {[m.materialName for m in readMDF(path).materialList]}")


def main():
    kit = os.path.abspath(sys.argv[1])
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile

    bpy.ops.wm.open_mainfile(filepath=os.path.join(kit, "dual_blade_kit_fitted.blend"))
    addon_utils.enable("re_mesh_editor", default_set=True)
    collection = bpy.data.collections[f"{NAME}.mesh"]
    armature = next(o for o in collection.objects if o.type == "ARMATURE")
    for o in list(collection.objects):
        if "MiquellaDemon" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
    for stage, (length, angle, spread) in enumerate(STAGES, 1):
        side_pair(stage, length, angle, spread, armature, collection)

    natives = os.path.join(kit, "natives", "STM", *REL_DIR.split("/"))
    add_materials(os.path.join(natives, f"{NAME}.mdf2{MDF_EXT}"))
    path = os.path.join(natives, f"{NAME}.mesh{MESH_EXT}")
    ok = exportREMeshFile(path, {"targetCollection": collection.name, "selectedOnly": False,
                                 "exportAllLODs": False, "exportBlendShapes": False, "rotate90": True,
                                 "useBlenderMaterialName": False, "preserveBoneMatrices": True,
                                 "exportBoundingBoxes": False, "autoSolveRepeatedUVs": True,
                                 "preserveSharpEdges": False})
    log(f"export mesh: {ok} ({os.path.getsize(path)} bytes)")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(kit, "dual_blade_kit_demon.blend"))


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.flush()
        os._exit(0)     # the addon leaves a thread running
