"""Render a game kit next to the game's original weapon, at game scale, to check placement.

The original is drawn in flat grey; ours with gold glow and ivory. The hand (file origin) is
marked with a small red sphere. Views are orthographic in file space (+Z up).

Usage: python preview_kit.py <kit .blend> <original .mesh> <out.png> <view: front|side|gun> [offset]
"gun" is a perspective view with the muzzle (+Z) to the right and +Y up, ours above the original.
Requires bpy 4.5 with RE Mesh Editor in the user addons dir.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(__file__))
import common as c

KIT_BLEND, ORIG, OUT = (os.path.abspath(a) for a in sys.argv[1:4])
VIEW = sys.argv[4]
OFFSET = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
# Blender space of RE Mesh Editor (file +Z = Blender -Y) -> file space.
TO_FILE = Matrix.Rotation(math.radians(-90), 4, "X")
# File space -> world for the "gun" view: muzzle +X, file +Y up, file X toward the camera.
GUN = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def main():
    bpy.ops.wm.open_mainfile(filepath=KIT_BLEND)
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile

    ours = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in bpy.data.objects:
        if o.type == "ARMATURE":
            bpy.data.objects.remove(o, do_unlink=True)
    before = set(bpy.data.objects)
    importREMeshFile(ORIG, {"clearScene": False, "createCollections": True, "loadMaterials": False,
                            "loadMDFData": False, "loadShellFur": False, "loadUnusedTextures": False,
                            "loadUnusedProps": False, "useBackfaceCulling": False, "reloadCachedTextures": False,
                            "mdfPath": "", "importAllLODs": False, "importBlendShapes": False, "rotate90": True,
                            "mergeArmature": "", "importArmatureOnly": False, "mergeGroups": False,
                            "importShadowMeshes": False, "importOcclusionMeshes": False,
                            "importBoundingBoxes": False})
    theirs = []
    for o in [o for o in bpy.data.objects if o not in before]:
        if o.type == "MESH" and "Group_0_" in o.name:
            theirs.append(o)
        else:
            bpy.data.objects.remove(o, do_unlink=True)

    grey = c.make_material("Original", "#6E6E74", roughness=0.6)
    ivory = c.make_material("PvIvory", c.PALETTE["ivory"], roughness=0.35, emission=c.PALETTE["glow"], strength=0.05)
    glow = c.make_material("PvGlow", c.PALETTE["glow"], emission=c.PALETTE["glow"], strength=2.5)
    blade = c.make_material("PvBlade", c.PALETTE["blade_core"], emission=c.PALETTE["blade_core"], strength=2.2)
    if VIEW == "gun":
        world, shift = GUN, Matrix.Translation((0, 0, OFFSET))
    else:
        world = Matrix.Identity(4)
        shift = Matrix.Translation((OFFSET, 0, 0) if VIEW == "front" else (0, OFFSET, 0))
    for o in theirs:
        o.modifiers.clear()
        o.parent = None
        o.data.transform(world @ TO_FILE @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.data.materials.clear()
        o.data.materials.append(grey)
    for o in ours:
        o.modifiers.clear()
        o.parent = None
        o.data.transform(shift @ world @ TO_FILE @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        name = o.name.split("__")[-1]
        mat = ivory if "Ivory" in name else blade if "Blade" in name else glow
        o.data.materials.clear()
        o.data.materials.append(mat)
    hand = c.make_material("Hand", "#FF2020", emission="#FF2020", strength=3.0)
    for x in (0.0, OFFSET):
        loc = (x, 0, 0) if VIEW == "front" else (0, 0, x) if VIEW == "gun" else (0, x, 0)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=loc)
        bpy.context.active_object.data.materials.append(hand)

    zs = [(o.matrix_world @ v.co).z for o in ours + theirs for v in o.data.vertices]
    lo, hi = min(zs), max(zs)
    c.setup_render(samples=24, res=(900, 1100), world_hex="#1A1A1F", world_strength=0.4, glare=True)
    c.add_light("key", "AREA", (1.5, -2.0, 2.0), 300, size=2.0, target=(OFFSET / 2, 0, (lo + hi) / 2))
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = (hi - lo) * 1.12
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    mid = OFFSET / 2
    if VIEW == "gun":
        cam_data.type = "PERSP"
        cam.location = (0.15, -3.6, OFFSET / 2 + 0.35)
        cam.rotation_euler = (math.radians(84), 0, math.radians(2))
    elif VIEW == "front":     # looking along +Y: file X right, Z up
        cam.location = (mid, -6, (lo + hi) / 2)
        cam.rotation_euler = (math.radians(90), 0, 0)
    else:                   # looking along -X: file Y right... shown with -Y (down for bowguns) at the bottom
        cam.location = (6, mid, (lo + hi) / 2)
        cam.rotation_euler = (math.radians(90), 0, math.radians(90))
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("WROTE", OUT, flush=True)


try:
    main()
finally:
    sys.stdout.flush()
    os._exit(0)
