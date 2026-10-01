"""Fit the dual light blade to a game original and rebuild its material file from it.

First in-game test (2026-10-01) showed two problems, both fixed here:
- Placement: Wilds weapons point along +Z (file space) with the hand on the origin and a
  root / Base / VFX_Attack skeleton, every vertex on Base. Our kit pointed along +Y with
  the origin at the pommel and had no skeleton, so the blade floated off the hand.
- No glow: RE Mesh Editor's Wilds "Weapon Emissive" preset predates a game update and
  has 176 parameters; the current shader has 180 (AnimEmit_Blend, Use_Basecolor_Mask,
  Basecolor_Mask_Min/Max). The game reads the parameter block by position, so every value
  after the gap was misread. Now each material is a copy of the original weapon's
  material (current layout), keeping our textures and values by name.

Source geometry is the kit's dual_blade_kit.blend (unchanged), so this can be re-run.

Usage: python fit_dual_blades.py <kit dir> <original it02 *_0.mesh.241111606> <original *_0.mdf2.45>
Requires bpy 4.5 with RE Mesh Editor in the user addons dir. The originals are only read.
"""
import copy
import math
import os
import sys

import bpy
from mathutils import Matrix

KIT, ORIG_MESH, ORIG_MDF = (os.path.abspath(a) for a in sys.argv[1:4])
NAME = "wp_miquella_db"
REL_DIR = "Art/Model/MiquellaLight/DualBlades"
MESH_EXT, MDF_EXT = ".241111606", ".45"
# Kit grip runs z 0.012..0.154; originals run about -0.04..0.13 with the hand near 0.
GRIP_SHIFT = -0.05
# Blender +Z (kit "up") -> Blender -Y, which RE Mesh Editor writes as file +Z.
TO_WEAPON_AXIS = Matrix.Rotation(math.radians(90.0), 4, "X") @ Matrix.Translation((0, 0, GRIP_SHIFT))


def log(msg):
    print(f"[fit] {msg}", flush=True)


def import_options():
    return {"clearScene": False, "createCollections": True, "loadMaterials": False,
            "loadMDFData": False, "loadShellFur": False, "loadUnusedTextures": False,
            "loadUnusedProps": False, "useBackfaceCulling": False, "reloadCachedTextures": False,
            "mdfPath": "", "importAllLODs": False, "importBlendShapes": False, "rotate90": True,
            "mergeArmature": "", "importArmatureOnly": False, "mergeGroups": False,
            "importShadowMeshes": False, "importOcclusionMeshes": False, "importBoundingBoxes": False}


def fit_mesh(natives):
    # Call the addon's functions directly: its operators toggle the system console,
    # which crashes headless Blender on Windows.
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile, exportREMeshFile

    bpy.ops.wm.open_mainfile(filepath=os.path.join(KIT, "dual_blade_kit.blend"))
    import addon_utils
    addon_utils.enable("re_mesh_editor", default_set=True)
    ours = bpy.data.collections[f"{NAME}.mesh"]
    parts = [o for o in ours.objects if o.type == "MESH"]

    before = set(bpy.data.objects)
    importREMeshFile(ORIG_MESH, import_options())
    new = [o for o in bpy.data.objects if o not in before]
    armature = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        if o is not armature:
            bpy.data.objects.remove(o, do_unlink=True)
    for col in list(armature.users_collection):
        col.objects.unlink(armature)
    ours.objects.link(armature)
    log(f"skeleton from original: {[b.name for b in armature.data.bones]}")

    for o in parts:
        o.data.transform(TO_WEAPON_AXIS @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.vertex_groups.clear()
        group = o.vertex_groups.new(name="Base")
        group.add(range(len(o.data.vertices)), 1.0, "REPLACE")
        o.modifiers.clear()
        o.modifiers.new("Armature", "ARMATURE").object = armature
        o.parent = armature
        ys = [v.co.y for v in o.data.vertices]
        log(f"{o.name}: length axis -Y {max(ys):+.3f} .. {min(ys):+.3f}")

    os.makedirs(natives, exist_ok=True)
    path = os.path.join(natives, f"{NAME}.mesh{MESH_EXT}")
    ok = exportREMeshFile(path, {"targetCollection": ours.name, "selectedOnly": False,
                                 "exportAllLODs": False, "exportBlendShapes": False, "rotate90": True,
                                 "useBlenderMaterialName": False, "preserveBoneMatrices": True,
                                 "exportBoundingBoxes": False, "autoSolveRepeatedUVs": True,
                                 "preserveSharpEdges": False})
    log(f"export mesh: {ok} -> {path} ({os.path.getsize(path)} bytes)")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(KIT, "dual_blade_kit_fitted.blend"))


def rebuild_mdf(natives):
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    path = os.path.join(natives, f"{NAME}.mdf2{MDF_EXT}")
    old = readMDF(path)                       # our values, outdated layout
    template = readMDF(ORIG_MDF)              # the game's current layout
    base = template.materialList[0]
    materials = []
    for mat in old.materialList:
        new = copy.deepcopy(base)
        new.materialName = mat.materialName
        ours_tex = {t.textureType: t.texturePath for t in mat.textureList}
        for t in new.textureList:
            if t.textureType in ours_tex:
                t.texturePath = ours_tex[t.textureType]
        ours_prop = {p.propName: p.propValue for p in mat.propertyList}
        kept, added = 0, []
        for p in new.propertyList:
            if p.propName in ours_prop:
                p.propValue = list(ours_prop[p.propName])
                kept += 1
            else:
                added.append(f"{p.propName}={p.propValue}")
        # Steady glow: the new animated-emission blend stays off.
        for p in new.propertyList:
            if p.propName == "AnimEmit_Blend":
                p.propValue = [0.0]
        materials.append(new)
        log(f"{new.materialName}: {kept} values kept, from original: {added}")
    template.materialList = materials
    writeMDF(template, path)
    check = readMDF(path)
    names = [p.propName for p in check.materialList[0].propertyList]
    log(f"wrote {path}: {len(check.materialList)} materials, {len(names)} params, "
        f"layout matches original: {names == [p.propName for p in base.propertyList]}")


def main():
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)
    natives = os.path.join(KIT, "natives", "STM", *REL_DIR.split("/"))
    rebuild_mdf(natives)
    fit_mesh(natives)


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.flush()
        os._exit(0)     # the addon leaves a thread running
