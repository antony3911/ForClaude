"""The hunting horn's echo bubbles in gold (DESIGN: floating gold film bubbles).

The horn's echo effects (11_it05_000-042) show one shared sphere as their MESH:
Art/VFX/Mesh/Common/Other/bubble/11_bubble_00 (radius 0.5, one material on the effect's
VFX_Transparent_Bubble shader). Ours, over that file (patch pak):
- the shell: a sphere of the same size on the game's bubble material, in gold without its
  rainbow sheen (the effect keeps driving it, so it still appears and fades as before);
- three thin rings of gold light around it at different tilts, on our glowing weapon material
  (MiquellaRing, the dual blades kit's MiquellaGlow), which the effect cannot dim.
The horn's sound-wave spheres use the same mesh and grow: they become growing gold bubbles.

The material file is a modified game file: build it from the user's own extracted files, keep it
out of the repo.

Usage: python gold_bubble.py <extracted 11_bubble_00.mdf2.45> <out folder holding natives/>
Requires bpy 4.5 with RE Mesh Editor in the user addons dir.
"""
import copy
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(__file__))
from build_weapon_kit import FILE_TO_BLENDER, MDF_EXT, MEMBRANES, MESH_EXT, enable_addon, log, select_only, tris

REL = "Art/VFX/Mesh/Common/Other/bubble"
GLOW_TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "..", "mhws", "MiquellaLight_DualBlades_kit", "natives",
                             "STM", "Art", "Model", "MiquellaLight", "DualBlades", "wp_miquella_db.mdf2.45")
# Rings around the shell: (tilt about X, tilt about Y, radius, thickness), in the file's units.
# A third of the first version's thickness, dimmer (user, 2026-10-02: the lines were too thick).
RINGS = [(12, 0, 0.515, 0.0016), (72, 25, 0.522, 0.0013), (-48, -60, 0.528, 0.0011)]
RING_GLOW = 1.4


def build_mesh(mesh_col):
    import math
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=32, ring_count=16)
    shell = bpy.context.active_object
    shell.name = "Group_0_Sub_0__lambert1"
    bpy.ops.object.shade_smooth()
    shell.data.materials.append(bpy.data.materials.new("lambert1"))
    light = bpy.data.materials.new("MiquellaRing")
    rings = []
    for k, (tx, ty, r, minor) in enumerate(RINGS):
        # Light on polygons: the effect may show several bubbles at once.
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=minor, major_segments=96, minor_segments=8,
                                         rotation=(math.radians(tx), math.radians(ty), 0))
        o = bpy.context.active_object
        o.name = f"Ring_{k}"
        o.data.materials.append(light)
        bpy.ops.object.shade_smooth()
        rings.append(o)
    bpy.context.view_layer.update()
    for o in [shell] + rings:
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
    select_only(rings, rings[0])
    bpy.ops.object.join()
    ring = bpy.context.view_layer.objects.active
    ring.name = "Group_0_Sub_1__MiquellaRing"
    ring.data.materials.clear()
    ring.data.materials.append(light)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    for o in (shell, ring):
        o.data.transform(FILE_TO_BLENDER)        # file space = the sphere's own space
        for col in list(o.users_collection):
            col.objects.unlink(o)
        mesh_col.objects.link(o)
        log(f"{o.name}: {tris(o)} tris")
    return shell, ring


def build_mdf(src, dst):
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    mdf = readMDF(src)
    props = MEMBRANES["bubble"][2]
    for mat in mdf.materialList:
        for p in mat.propertyList:
            if p.propName in props:
                log(f"  {mat.materialName}.{p.propName}: {p.propValue} -> {props[p.propName]}")
                p.propValue = list(props[p.propName])
    glow = copy.deepcopy(next(m for m in readMDF(GLOW_TEMPLATE).materialList if m.materialName == "MiquellaGlow"))
    glow.materialName = "MiquellaRing"
    for p in glow.propertyList:
        if p.propName == "Emissive_Intensity":
            p.propValue = [RING_GLOW]
    mdf.materialList.append(glow)
    writeMDF(mdf, dst)
    log(f"mdf: {[m.materialName for m in readMDF(dst).materialList]}")


def main():
    src, out = sys.argv[1], os.path.abspath(sys.argv[2])
    import common as c
    c.reset_scene()
    enable_addon()
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile
    mesh_col = bpy.data.collections.new("11_bubble_00.mesh")
    bpy.context.scene.collection.children.link(mesh_col)
    build_mesh(mesh_col)
    out_dir = os.path.join(out, "natives", "STM", *REL.split("/"))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"11_bubble_00.mesh{MESH_EXT}")
    ok = exportREMeshFile(path, {"targetCollection": mesh_col.name, "selectedOnly": False,
                                 "exportAllLODs": False, "exportBlendShapes": False, "rotate90": True,
                                 "useBlenderMaterialName": False, "preserveBoneMatrices": False,
                                 "exportBoundingBoxes": False, "autoSolveRepeatedUVs": True,
                                 "preserveSharpEdges": False})
    log(f"export mesh: {ok} -> {path}")
    build_mdf(src, os.path.join(out_dir, f"11_bubble_00.mdf2{MDF_EXT}"))


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.flush()
        os._exit(0)
