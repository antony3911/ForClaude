"""Render game kits put together in the weapon's file space: a bowgun with its add-ons (drum,
magazine, guard), from the side, from behind over the shoulder (the player's view) and from
the front, as one sheet.

Usage: python preview_addons.py <out.png> <title> <mesh> [<mesh> ...]
A mesh path prefixed "ghost:" is drawn in flat translucent grey (an original, to compare
placement; such sheets hold the game's model and stay out of the repo). Meshes are read with
RE Mesh Editor (bpy 4.5); our materials are told apart by name (Ivory / Blade / the rest glow).
"""
import math
import os
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(__file__))
import common as c

OUT, TITLE, MESHES = os.path.abspath(sys.argv[1]), sys.argv[2], sys.argv[3:]
# Blender space of RE Mesh Editor -> file space -> world: muzzle (+Z) along world +X, file +Y
# up, file +X toward world +Y (so the -X side, where the add-ons hang, faces a camera at -Y).
TO_FILE = Matrix.Rotation(math.radians(-90), 4, "X")
GUN = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
VIEWS = (("side", (0.0, -3.2, 0.0), (90, 0, 0)),
         ("over the shoulder", (-2.4, -1.25, 0.55), (78, 0, -62)),
         ("front", (3.0, -1.0, 0.15), (88, 0, 71)))


def import_mesh(path):
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile
    before = set(bpy.data.objects)
    importREMeshFile(path, {"clearScene": False, "createCollections": True, "loadMaterials": False,
                            "loadMDFData": False, "loadShellFur": False, "loadUnusedTextures": False,
                            "loadUnusedProps": False, "useBackfaceCulling": False, "reloadCachedTextures": False,
                            "mdfPath": "", "importAllLODs": False, "importBlendShapes": False, "rotate90": True,
                            "mergeArmature": "", "importArmatureOnly": False, "mergeGroups": False,
                            "importShadowMeshes": False, "importOcclusionMeshes": False,
                            "importBoundingBoxes": False})
    out = []
    for o in [o for o in bpy.data.objects if o not in before]:
        if o.type == "MESH" and "Group_" in o.name:
            out.append(o)
        else:
            bpy.data.objects.remove(o, do_unlink=True)
    return out


def main():
    c.reset_scene()
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)
    ghost = c.make_material("Ghost", "#8A8A92", roughness=0.6)
    bsdf = ghost.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Alpha"].default_value = 0.35
    ivory = c.make_material("PvIvory", c.PALETTE["ivory"], roughness=0.35, emission=c.PALETTE["glow"], strength=0.05)
    glow = c.make_material("PvGlow", c.PALETTE["glow"], emission=c.PALETTE["glow"], strength=2.5)
    blade = c.make_material("PvBlade", c.PALETTE["blade_core"], emission=c.PALETTE["blade_core"], strength=2.2)
    allobjs = []
    for spec in MESHES:
        is_ghost = spec.startswith("ghost:")
        for o in import_mesh(spec[6:] if is_ghost else spec):
            o.modifiers.clear()
            o.parent = None
            o.data.transform(GUN @ TO_FILE @ o.matrix_world)
            o.matrix_world = Matrix.Identity(4)
            name = o.name.split("__")[-1]
            mat = ghost if is_ghost else ivory if "Ivory" in name else blade if "Blade" in name else glow
            o.data.materials.clear()
            o.data.materials.append(mat)
            allobjs.append(o)
    hand = c.make_material("Origin", "#FF2020", emission="#FF2020", strength=3.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.018, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(hand)
    xs = [(o.matrix_world @ v.co).x for o in allobjs for v in o.data.vertices]
    mid_x = (min(xs) + max(xs)) / 2
    c.setup_render(samples=24, res=(1100, 700), world_hex="#1A1A1F", world_strength=0.4, glare=True)
    c.add_light("key", "AREA", (mid_x - 1.0, -2.5, 2.0), 300, size=2.0, target=(mid_x, 0, -0.2))
    c.add_light("rim", "AREA", (mid_x + 1.5, 2.0, 1.0), 120, size=2.0, target=(mid_x, 0, -0.2))
    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    frames = []
    for k, (label, loc, rot) in enumerate(VIEWS):
        cam_data.type = "ORTHO" if k == 0 else "PERSP"
        cam_data.ortho_scale = (max(xs) - min(xs)) * 1.1
        cam_data.lens = 50
        cam.location = (mid_x + loc[0], loc[1], loc[2] - 0.2)
        cam.rotation_euler = tuple(math.radians(a) for a in rot)
        path = OUT.replace(".png", f"_{k}.png")
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        frames.append((label, path))
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(p) for _, p in frames]
    W, H = ims[0].size
    sheet = Image.new("RGB", (W * 2, H * 2 + 60), (20, 20, 24))
    font = None
    for f in (os.environ.get("MIQUELLA_FONT"), "C:/Windows/Fonts/msjh.ttc", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"):
        if f and os.path.exists(f):
            font = ImageFont.truetype(f, 34)
            break
    d = ImageDraw.Draw(sheet)
    d.text((20, 12), TITLE, fill=(240, 210, 140), font=font)
    for k, (im, (label, p)) in enumerate(zip(ims, frames)):
        x, y = (k % 2) * W, 60 + (k // 2) * H
        sheet.paste(im, (x, y))
        d.text((x + 16, y + 10), label, fill=(220, 220, 220), font=font)
        os.remove(p)
    sheet.save(OUT)
    print("WROTE", OUT, flush=True)


try:
    main()
finally:
    sys.stdout.flush()
    os._exit(0)
