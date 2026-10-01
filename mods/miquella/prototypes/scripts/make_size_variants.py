"""Export the dual light blade at several sizes, as separate .mesh files sharing one .mdf2.

Scaling the weapon's transform at run time does not work in Wilds (the game resets it: the
first try flickered between sizes, the second had no effect), so each size is its own model
and the Weapons script picks one.

Size F scales the whole weapon's length by F, but the grip and pommel stay hand-sized:
everything above the grip (guard, halo, blade, demon side blades) is scaled about the top
of the grip, lengthwise by k so that the total length is F times the original, and across
by sqrt(k) so the blade stays slender.

Run after add_demon_blades.py (reads dual_blade_kit_demon.blend).
Usage: python make_size_variants.py <kit dir> [sizes, default 1.2 1.4 1.6]
Writes wp_miquella_db_s12.mesh... next to wp_miquella_db.mesh (size 1.0).
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(__file__))
from fit_dual_blades import MESH_EXT, NAME, REL_DIR

GRIP_TOP = 0.098      # weapon space (Blender -Y is the blade direction); grip and pommel are below
THRESHOLD = 0.0       # vertices further along than this belong to the guard / blade side


def log(msg):
    print(f"[size] {msg}", flush=True)


def variant_name(size):
    return f"{NAME}_s{round(size * 10):d}"


def scale_part(obj, k, w, lengthwise):
    """Blender space: the blade runs along -Y, width X, thickness Z."""
    for v in obj.data.vertices:
        along = -v.co.y
        if along <= THRESHOLD:
            continue
        f = k if lengthwise else w
        v.co.y = -(GRIP_TOP + (along - GRIP_TOP) * f)
        v.co.x *= w
        v.co.z *= w


def main():
    kit = os.path.abspath(sys.argv[1])
    sizes = [float(s) for s in sys.argv[2:]] or [1.2, 1.4, 1.6]
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile

    natives = os.path.join(kit, "natives", "STM", *REL_DIR.split("/"))
    for size in sizes:
        bpy.ops.wm.open_mainfile(filepath=os.path.join(kit, "dual_blade_kit_demon.blend"))
        addon_utils.enable("re_mesh_editor", default_set=True)
        collection = bpy.data.collections[f"{NAME}.mesh"]
        parts = [o for o in collection.objects if o.type == "MESH"]
        ys = [v.co.y for o in parts for v in o.data.vertices]
        start, tip = -max(ys), -min(ys)                     # pommel end, blade tip
        k = ((tip - start) * size - (GRIP_TOP - start)) / (tip - GRIP_TOP)
        w = math.sqrt(k)
        for o in parts:
            if "MiquellaGrip" in o.name:
                continue                                    # the hand holds this: keep it
            lengthwise = "MiquellaBlade" in o.name or "MiquellaDemon" in o.name
            scale_part(o, k, w, lengthwise)
        new_tip = -min(v.co.y for o in parts for v in o.data.vertices)
        collection.name = f"{variant_name(size)}.mesh"
        path = os.path.join(natives, f"{variant_name(size)}.mesh{MESH_EXT}")
        ok = exportREMeshFile(path, {"targetCollection": collection.name, "selectedOnly": False,
                                     "exportAllLODs": False, "exportBlendShapes": False, "rotate90": True,
                                     "useBlenderMaterialName": False, "preserveBoneMatrices": True,
                                     "exportBoundingBoxes": False, "autoSolveRepeatedUVs": True,
                                     "preserveSharpEdges": False})
        log(f"size {size}: length x{k:.3f}, width x{w:.3f}, total {new_tip - start:.3f} m "
            f"(was {tip - start:.3f}) -> {os.path.basename(path)} {ok}")


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.flush()
        os._exit(0)     # the addon leaves a thread running
