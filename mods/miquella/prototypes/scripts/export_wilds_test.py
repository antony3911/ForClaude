"""Pipeline test: export a prototype weapon to the Monster Hunter Wilds .mesh format with
RE Mesh Editor, headless.

This only proves the export step can be scripted. A real mod must start from the
original weapon mesh (its bones, position, and materials), which needs the game files.

Usage: python export_wilds_test.py <prototype.blend> <root object name> <out_dir>
Requires Blender 4.3.2+ (bpy 4.5 here) with the RE Mesh Editor addon in the user addons dir.
"""
import os
import sys

import bpy

BLEND, ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ADDONS = bpy.utils.user_resource("SCRIPTS", path="addons")
MESH_NAME = "wp_miquella_test"
WILDS_EXT = ".241111606"


def log(msg):
    print(f"[export] {msg}", flush=True)


def main():
    import addon_utils
    sys.path.append(ADDONS)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    addon_utils.modules_refresh()
    mod = addon_utils.enable("re_mesh_editor", default_set=True)
    log(f"RE Mesh Editor enabled: {mod is not None}")
    root = bpy.data.objects[ROOT]
    parts = [o for o in root.children_recursive if o.type in {"MESH", "CURVE"}]
    log(f"{len(parts)} parts under {ROOT}")

    # Bake curves and modifiers into plain meshes in world space.
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target="MESH")
    for o in parts:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # One sub mesh per material, named Group_X_Sub_Y__MaterialName.
    by_material = {}
    for o in parts:
        mat = o.data.materials[0].name if o.data.materials else "Default"
        by_material.setdefault(mat, []).append(o)
    collection = bpy.data.collections.new(f"{MESH_NAME}.mesh")
    bpy.context.scene.collection.children.link(collection)
    for sub, (mat, objs) in enumerate(sorted(by_material.items())):
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        joined = bpy.context.view_layer.objects.active
        joined.name = f"Group_0_Sub_{sub}__{mat.replace('.', '_')}"
        # Exporter rules: no loose vertices, and every sub mesh needs a UV map.
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.delete_loose()
        if not joined.data.uv_layers:
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(island_margin=0.02)
        bpy.ops.object.mode_set(mode="OBJECT")
        for c in list(joined.users_collection):
            c.objects.unlink(joined)
        collection.objects.link(joined)
        log(f"sub mesh {joined.name}: {len(joined.data.vertices)} verts")

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{MESH_NAME}.mesh{WILDS_EXT}")
    result = bpy.ops.re_mesh.exportfile(filepath=path, targetCollection=collection.name,
                                        filename_ext=WILDS_EXT)
    log(f"export result: {result}")
    if os.path.exists(path):
        log(f"wrote {path} ({os.path.getsize(path)} bytes)")


try:
    main()
finally:
    # The addon leaves a thread running that keeps the interpreter alive; exit explicitly.
    sys.stdout.flush()
    os._exit(0)
