"""Build a game-ready kit for the dual light blade (Monster Hunter Wilds).

Produces everything that can be made without the game files:
- a low-poly sword (grip detail baked into a normal map instead of geometry)
- textures in RE Engine layouts (ALBD, NRRO, EMI) converted to Wilds .tex
- an .mdf2 built from RE Mesh Editor's Wilds "Weapon" / "Weapon Emissive" presets,
  with a bright gold Emissive_Color
- the .mesh exported for Wilds

Still needs the game (see the kit README): the path and name of the weapon being replaced,
its bones and position, and packing into a patch pak.

Usage: python build_game_kit.py <kit_dir> <work_dir>
Requires bpy 4.5 with RE Mesh Editor in the user addons dir.
"""
import math
import os
import shutil
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import common as c
import blades

KIT, WORK = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
NAME = "wp_miquella_db"
# Placeholder location; must become the replaced weapon's path once it is chosen in game.
REL_DIR = "Art/Model/MiquellaLight/DualBlades"
TEX_REL = f"{REL_DIR}/tex"
MESH_EXT, MDF_EXT = ".241111606", ".45"
GOLD_EMISSIVE = (1.0, 0.647, 0.149, 1.0)      # #FFA526


def log(msg):
    print(f"[kit] {msg}", flush=True)


def enable_addon():
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)


def select_only(objs, active=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def tri_count(objs):
    deps = bpy.context.evaluated_depsgraph_get()
    n = 0
    for o in objs:
        m = o.evaluated_get(deps).to_mesh()
        n += sum(len(p.vertices) - 2 for p in m.polygons)
        o.evaluated_get(deps).to_mesh_clear()
    return n


# ------------------------------------------------------------------ geometry

def build_geometry():
    c.reset_scene()
    enable_addon()
    ivory = c.make_material("MiquellaIvory", c.PALETTE["ivory"], roughness=0.4)
    drop = c.make_material("MiquellaGlow", c.PALETTE["glow"], emission=c.PALETTE["glow"], strength=1.0)
    blade = c.make_material("MiquellaBlade", c.PALETTE["blade_core"], emission=c.PALETTE["blade_core"], strength=1.0)
    core = c.make_material("Core", c.PALETTE["blade_core"])

    high = blades.build_sword("High", ivory, drop, blade, core, seed=3)
    low = blades.build_sword("Low", ivory, drop, blade, core, seed=3)
    high_grip = [o for o in high.children if o.name.startswith(("Strand_", "Grip_Core"))]
    for o in high.children:
        if o not in high_grip:
            bpy.data.objects.remove(o, do_unlink=True)

    parts = list(low.children)
    for o in parts:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    # Bake object transforms so every part shares one coordinate space.
    select_only(parts)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    by = {"blade": [], "ivory": [], "glow": []}
    for o in parts:
        if o.name.startswith(("Core_", "Grip_Core")):
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        if o.name.startswith(("Blade_Halo", "Pommel_Droplet")):
            by["glow"].append(o)
        elif o.name.startswith("Blade"):
            o.modifiers.clear()                      # drop the subdivision
            by["blade"].append(o)
        else:
            if o.type == "CURVE":
                o.data.bevel_resolution = 0          # 4-sided strands
            by["ivory"].append(o)

    # Ivory: bake curves to mesh, drop the grip section (replaced by the baked cylinder),
    # then decimate the guard strands.
    select_only(by["ivory"])
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    ivory_obj = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in ivory_obj.data.vertices:
        v.select = 0.02 < v.co.z < blades.GUARD_Z - 0.012
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    dec = ivory_obj.modifiers.new("decimate", "DECIMATE")
    dec.ratio = 0.5
    bpy.ops.object.modifier_apply(modifier="decimate")

    # Low-poly grip cylinder.
    r = 0.0135 * 1.02
    z0, z1 = 0.012, blades.GUARD_Z - 0.006
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=z1 - z0,
                                        location=(0, 0, (z0 + z1) / 2), end_fill_type="NOTHING")
    grip = bpy.context.active_object
    grip.name = "Grip"
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cylinder_project(direction="ALIGN_TO_OBJECT", scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()

    # Join per material and name the sub meshes the RE Engine way.
    mesh_col = bpy.data.collections.new(f"{NAME}.mesh")
    bpy.context.scene.collection.children.link(mesh_col)
    subs = []
    for sub, (mat_name, objs) in enumerate((("MiquellaBlade", by["blade"]), ("MiquellaIvory", [ivory_obj]),
                                            ("MiquellaGrip", [grip]), ("MiquellaGlow", by["glow"]))):
        select_only(objs)
        bpy.ops.object.convert(target="MESH")
        if len(objs) > 1:
            bpy.ops.object.join()
        o = bpy.context.view_layer.objects.active
        o.name = f"Group_0_Sub_{sub}__{mat_name}"
        o.data.materials.clear()
        o.data.materials.append(bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name))
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.delete_loose()
        if mat_name != "MiquellaGrip":
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(island_margin=0.02)
        bpy.ops.object.mode_set(mode="OBJECT")
        for col in list(o.users_collection):
            col.objects.unlink(o)
        mesh_col.objects.link(o)
        subs.append(o)
        log(f"{o.name}: {tri_count([o])} tris")
    log(f"total low poly: {tri_count(subs)} tris")
    return subs, grip_of(subs), high_grip, mesh_col


def grip_of(subs):
    return next(o for o in subs if o.name.endswith("MiquellaGrip"))


# ------------------------------------------------------------------ bake + textures

def bake_grip_normal(grip, high_grip, path):
    select_only(high_grip)
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    high = bpy.context.view_layer.objects.active
    img = bpy.data.images.new("GripNormal", 1024, 1024)
    img.colorspace_settings.name = "Non-Color"
    mat = grip.data.materials[0]
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    mat.node_tree.nodes.active = tex
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 8
    select_only([high, grip], active=grip)
    bpy.ops.object.bake(type="NORMAL", use_selected_to_active=True, cage_extrusion=0.006,
                        max_ray_distance=0.02, normal_space="TANGENT", margin=8)
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.objects.remove(high, do_unlink=True)
    mat.node_tree.nodes.remove(tex)
    log(f"baked {path}")


def hex_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def save_rgba(path, arr):
    """Save an HxWx4 uint8 array as PNG through Blender (top row first)."""
    h, w, _ = arr.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=True)
    img.pixels.foreach_set((np.flipud(arr).astype(np.float32) / 255.0).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def flat(size, rgba):
    return np.tile(np.array(rgba, dtype=np.uint8), (size, size, 1))


def make_textures(src_dir, grip_normal_png):
    """RE layouts: ALBD = albedo + dielectric (white = non-metal),
    NRRO = roughness, normal Y (DirectX), AO, normal X; EMI = emissive mask."""
    os.makedirs(src_dir, exist_ok=True)
    out = {}

    def flat_nrro(size, rough):
        return flat(size, [int(rough * 255), 128, 255, 128])

    specs = {
        "MiquellaBlade": ("#F6D99A", 0.25, True),
        "MiquellaIvory": (c.PALETTE["ivory"], 0.4, False),
        "MiquellaGrip": (c.PALETTE["ivory"], 0.4, False),
        "MiquellaGlow": ("#FFC75A", 0.2, True),
    }
    for mat, (color, rough, emissive) in specs.items():
        size = 1024 if mat == "MiquellaGrip" else 256
        albd = flat(size, hex_rgb(color) + [255])
        save_rgba(os.path.join(src_dir, f"{mat}_ALBD.png"), albd)
        if mat == "MiquellaGrip":
            img = bpy.data.images.load(grip_normal_png)
            px = (np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4) * 255).astype(np.uint8)
            px = np.flipud(px)
            nrro = np.zeros_like(px)
            nrro[..., 0] = int(rough * 255)
            nrro[..., 1] = 255 - px[..., 1]            # OpenGL -> DirectX: flip green
            nrro[..., 2] = 255
            nrro[..., 3] = px[..., 0]                  # normal X lives in alpha
        else:
            nrro = flat_nrro(size, rough)
        save_rgba(os.path.join(src_dir, f"{mat}_NRRO.png"), nrro)
        if emissive:
            save_rgba(os.path.join(src_dir, f"{mat}_EMI.png"), flat(size, [255, 255, 255, 255]))
        out[mat] = emissive
    return out


def convert_textures(src_dir, dds_dir, tex_dir):
    from re_mesh_editor.modules.ddsconv.directx.texconv import Texconv, unload_texconv
    from re_mesh_editor.modules.tex.blender_re_tex import convertTexDDSList
    os.makedirs(dds_dir, exist_ok=True)
    conv = Texconv()
    jobs = sorted(os.listdir(src_dir))
    for f in jobs:
        fmt = "BC7_UNORM_SRGB" if f.endswith("_ALBD.png") else "BC7_UNORM"
        # BC7 on Linux needs the (slow) software encoder.
        conv.convert_to_dds(file=os.path.join(src_dir, f), dds_fmt=fmt, out=dds_dir,
                            no_mip=False, verbose=False, allow_slow_codec=True)
    unload_texconv()
    names = [f for f in os.listdir(dds_dir) if f.endswith(".dds")]
    ok, failed = convertTexDDSList(names, dds_dir, tex_dir, "MHWILDS")
    log(f"textures: {len(jobs)} png -> {len(names)} dds -> {ok} tex ({failed} failed)")


# ------------------------------------------------------------------ mdf

def build_mdf(emissive_map):
    from re_mesh_editor.modules.mdf.blender_re_mdf import createMDFCollection
    from re_mesh_editor.modules.mdf.re_mdf_presets import readPresetJSON
    preset_dir = os.path.join(bpy.utils.user_resource("SCRIPTS", path="addons"),
                              "re_mesh_editor", "Presets", "MHWILDS")
    col = createMDFCollection(f"{NAME}.mdf2")
    for mat in ("MiquellaBlade", "MiquellaIvory", "MiquellaGrip", "MiquellaGlow"):
        preset = "Weapon Emissive.json" if emissive_map[mat] else "Weapon.json"
        readPresetJSON(os.path.join(preset_dir, preset), col)
        obj = bpy.context.view_layer.objects.active
        m = obj.re_mdf_material
        m.materialName = mat
        for p in m.propertyList_items:
            if p.prop_name == "Emissive_Color" and emissive_map[mat]:
                p.color_value = GOLD_EMISSIVE
            elif p.prop_name == "Emissive_Intensity" and emissive_map[mat]:
                p.float_value = 1.2
        for b in m.textureBindingList_items:
            if b.textureType == "BaseDielectricMap":
                b.path = f"{TEX_REL}/{mat}_ALBD.tex"
            elif b.textureType == "NormalRoughnessOcclusionMap":
                b.path = f"{TEX_REL}/{mat}_NRRO.tex"
            elif b.textureType == "EmissiveMap" and emissive_map[mat]:
                b.path = f"{TEX_REL}/{mat}_EMI.tex"
        log(f"mdf material {mat} from {preset}")
    return col


# ------------------------------------------------------------------ main

def main():
    subs, grip, high_grip, mesh_col = build_geometry()
    os.makedirs(WORK, exist_ok=True)
    normal_png = os.path.join(WORK, "grip_normal_gl.png")
    bake_grip_normal(grip, high_grip, normal_png)
    emissive = make_textures(os.path.join(WORK, "tex_src"), normal_png)

    natives = os.path.join(KIT, "natives", "STM", *REL_DIR.split("/"))
    convert_textures(os.path.join(WORK, "tex_src"), os.path.join(WORK, "dds"),
                     os.path.join(KIT, "natives", "STM", *TEX_REL.split("/")))
    mdf_col = build_mdf(emissive)
    os.makedirs(natives, exist_ok=True)
    r1 = bpy.ops.re_mesh.exportfile(filepath=os.path.join(natives, f"{NAME}.mesh{MESH_EXT}"),
                                    targetCollection=mesh_col.name, filename_ext=MESH_EXT)
    r2 = bpy.ops.re_mdf.exportfile(filepath=os.path.join(natives, f"{NAME}.mdf2{MDF_EXT}"),
                                   targetCollection=mdf_col.name, filename_ext=MDF_EXT)
    log(f"export mesh {r1}, mdf {r2}")
    for root, _, files in os.walk(KIT):
        for f in files:
            p = os.path.join(root, f)
            log(f"  {os.path.relpath(p, KIT)} ({os.path.getsize(p)} bytes)")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, "dual_blade_kit.blend"))


try:
    main()
finally:
    sys.stdout.flush()
    os._exit(0)
