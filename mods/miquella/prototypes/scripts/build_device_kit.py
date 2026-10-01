"""Build a game kit for a Miquella weapon device: a model that replaces one of the game's
effect meshes at its own path (patch pak), so every one the game spawns is ours.

Devices: wyrmstake (gunlance: Art/VFX/Mesh/Weapon/it07/11_it07_000, the Unalloyed Gold
Needle) and wyvernblast (light bowgun: Art/VFX/Mesh/Weapon/it13/11_setbombshell_000, the
ivory flower bud). The originals have no skeleton and one material, lambert1, on the effect
shaders (the effect drives its ColorParam / IntensityParam), and several visibility groups
(stake: 10 overlapping parts, mine: 3) of which the effect shows some. Ours put the whole model
in each of those groups, so whichever is shown, the model appears. One lambert1,
copied from the sticky shell's emissive effect material (VFX_Standard_Simple_E), on a small
texture in three bands (gold metal, ivory, light) that each part's UVs point into.

Usage: python build_device_kit.py <device> <kit dir> <original .mesh> <11_stickyshell_000.mdf2.45>
Requires bpy 4.5 with RE Mesh Editor in the user addons dir. The originals are only read.
"""
import copy
import os
import sys

ARGS = sys.argv[1:]          # devices.py rewrites sys.argv when imported

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
from build_weapon_kit import FILE_TO_BLENDER, MDF_EXT, MESH_EXT, enable_addon, log, select_only, tris

TEX_REL = "Art/Model/MiquellaLight/Devices/tex"
TEX_EXT = ".241106027"
# Texture bands (u ranges), in the order gold, ivory, light: color, metal, roughness, emissive.
BANDS = [("#E2B04A", True, 0.28, 150), ("#F2E6D0", False, 0.4, 0), ("#FFC75A", False, 0.2, 255)]
BAND_OF = {"Unalloyed_Gold": 0, "Ivory": 1, "Light": 2, "Blade_Light": 2, "Blade_Core": 2}
# Gold light for the emissive band (the original's EmissiveParam is black: no glow of its own).
EMISSIVE = [3.0, 2.1, 0.8, 1.0]


def wyrmstake():
    """The needle with its point on +Z like the original stake's (which narrows to a point at
    z 1.6 and has its fins at the back, z -0.8): built 0.5 long point-first and scaled 4.7,
    2.35 m like the original, the eye at the back."""
    import devices
    import motifs as m
    mats = m.materials()
    mats["gold"] = devices.gold_material()
    objs = devices.needle(mats, 0.5, Vector((0, 0, 0)), Vector((0, 0, -1)))
    to_file = Matrix.Translation((0, 0, 1.55)) @ Matrix.Scale(4.7, 4)
    return {"name": "11_it07_000", "rel": "Art/VFX/Mesh/Weapon/it07", "objects": objs, "to_file": to_file,
            "groups": 10, "budget": 3500}


def wyvernblast():
    """The closed bud (petals at 8 degrees) placed like the original mine: its dome is
    symmetric about Y (x, z +-0.25) from y -0.13 to +0.24, so +Y is up and the ground at
    -0.13. Ours: prototype +Z up -> +Y, scaled 5 (0.39 high like the original)."""
    import devices
    import motifs as m
    mats = m.materials()
    objs = devices.bud(mats, Vector((0, 0, 0)), 8, "Closed")
    axes = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))     # z -> y, y -> -z
    to_file = Matrix.Translation((0, -0.13, 0)) @ Matrix.Scale(5.0, 4) @ axes
    return {"name": "11_setbombshell_000", "rel": "Art/VFX/Mesh/Weapon/it13", "objects": objs, "to_file": to_file,
            "groups": 3, "budget": 6000}


DEVICES = {"wyrmstake": wyrmstake, "wyvernblast": wyvernblast}


# ------------------------------------------------------------------ textures

def save_rgba(path, arr):
    h, w, _ = arr.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=True)
    img.pixels.foreach_set((np.flipud(arr).astype(np.float32) / 255.0).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()


def make_textures(src_dir):
    """64 x 64, three vertical bands. ALBD: albedo + dielectric in alpha (0 = metal);
    NRRO: roughness, normal Y, height/AO, normal X (flat); EMI: emissive mask."""
    os.makedirs(src_dir, exist_ok=True)
    n = 64
    albd, nrro, emi = (np.zeros((n, n, 4), np.uint8) for _ in range(3))
    for i, (color, metal, rough, glow) in enumerate(BANDS):
        cols = slice(i * n // 3, (i + 1) * n // 3 if i < 2 else n)
        rgb = [int(color[k:k + 2], 16) for k in (1, 3, 5)]
        albd[:, cols] = rgb + [0 if metal else 255]
        nrro[:, cols] = [int(rough * 255), 128, 255, 128]
        emi[:, cols] = [glow, glow, glow, 255]
    for name, arr in (("ALBD", albd), ("NRRO", nrro), ("EMI", emi)):
        save_rgba(os.path.join(src_dir, f"MiquellaDevice_{name}.png"), arr)


def convert_textures(src_dir, dds_dir, tex_dir):
    from re_mesh_editor.modules.ddsconv.directx.texconv import Texconv, unload_texconv
    from re_mesh_editor.modules.tex.blender_re_tex import convertTexDDSList
    os.makedirs(dds_dir, exist_ok=True)
    os.makedirs(tex_dir, exist_ok=True)
    if os.name == "nt":
        # texconv reads PNGs through WIC (COM): headless Blender has not initialized COM
        # (otherwise FAILED 80004002).
        import ctypes
        ctypes.windll.ole32.CoInitializeEx(None, 0)
    conv = Texconv()
    for f in sorted(os.listdir(src_dir)):
        fmt = "BC7_UNORM_SRGB" if f.endswith("_ALBD.png") else "BC7_UNORM"
        conv.convert_to_dds(file=os.path.join(src_dir, f), dds_fmt=fmt, out=dds_dir,
                            no_mip=False, verbose=False, allow_slow_codec=True)
    unload_texconv()
    names = [f for f in os.listdir(dds_dir) if f.endswith(".dds")]
    ok, failed = convertTexDDSList(names, dds_dir, tex_dir, "MHWILDS")
    log(f"textures: {len(names)} dds -> {ok} tex ({failed} failed)")


# ------------------------------------------------------------------ geometry

def band(o):
    for s in o.material_slots:
        if s.material and s.material.name.split(".")[0] in BAND_OF:
            return BAND_OF[s.material.name.split(".")[0]]
    log(f"  no band for {o.name} ({[s.material.name for s in o.material_slots if s.material]}) -> gold")
    return 0


def build_mesh(spec, mesh_col):
    bpy.context.view_layer.update()
    objs = [o for o in spec["objects"] if o.name in bpy.data.objects and o.type in ("MESH", "CURVE")]
    bands = {o.name: band(o) for o in objs}
    for o in objs:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    select_only(objs)
    bpy.ops.object.convert(target="MESH")
    parts = list(bpy.context.selected_objects)
    for o in parts:
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        uv = o.data.uv_layers.get("UVMap") or o.data.uv_layers.new(name="UVMap")
        u = (bands.get(o.name, 0) + 0.5) / 3
        for d in uv.data:
            d.uv = (u, 0.5)
        o.vertex_groups.clear()
    select_only(parts)
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = "Group_0_Sub_0__lambert1"
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials.new("lambert1"))
    before = tris(obj)
    if before > spec["budget"]:
        dec = obj.modifiers.new("decimate", "DECIMATE")
        dec.ratio = spec["budget"] / before
        bpy.ops.object.modifier_apply(modifier="decimate")
    # The exporter refuses loose vertices.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.delete_loose()
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.data.transform(FILE_TO_BLENDER @ spec["to_file"])
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    mesh_col.objects.link(obj)
    inv = FILE_TO_BLENDER.inverted()
    pts = [inv @ v.co for v in obj.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    log(f"{len(parts)} parts, {before} -> {tris(obj)} tris; file-space bounds "
        f"min=({lo[0]:+.3f}, {lo[1]:+.3f}, {lo[2]:+.3f}) max=({hi[0]:+.3f}, {hi[1]:+.3f}, {hi[2]:+.3f})")
    return obj


def build_mdf(path, template_mdf):
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    mdf = readMDF(template_mdf)
    mat = copy.deepcopy(mdf.materialList[0])
    mat.materialName = "lambert1"
    for t in mat.textureList:
        for kind in ("ALBD", "NRRO", "EMI"):
            if t.texturePath.upper().endswith(f"_{kind}.TEX"):
                t.texturePath = f"{TEX_REL}/MiquellaDevice_{kind}.tex"
    for p in mat.propertyList:
        if p.propName == "EmissiveParam":
            p.propValue = list(EMISSIVE)
    mdf.materialList = [mat]
    writeMDF(mdf, path)
    check = readMDF(path)
    log(f"mdf: {[(m.materialName, [t.texturePath for t in m.textureList]) for m in check.materialList]}")


def main():
    device, kit, orig_mesh, template_mdf = ARGS[0], *(os.path.abspath(a) for a in ARGS[1:4])
    import common as c
    c.reset_scene()
    spec = DEVICES[device]()
    enable_addon()
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile
    mesh_col = bpy.data.collections.new(f"{spec['name']}.mesh")
    bpy.context.scene.collection.children.link(mesh_col)
    obj = build_mesh(spec, mesh_col)
    for o in list(bpy.data.objects):
        if o is not obj:
            bpy.data.objects.remove(o, do_unlink=True)
    for g in range(1, spec["groups"]):
        copy_obj = obj.copy()
        copy_obj.data = obj.data.copy()
        copy_obj.name = f"Group_{g}_Sub_0__lambert1"
        mesh_col.objects.link(copy_obj)
    log(f"groups: {spec['groups']} (the whole model in each)")
    natives = os.path.join(kit, "natives", "STM")
    out_dir = os.path.join(natives, *spec["rel"].split("/"))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{spec['name']}.mesh{MESH_EXT}")
    ok = exportREMeshFile(path, {"targetCollection": mesh_col.name, "selectedOnly": False,
                                 "exportAllLODs": False, "exportBlendShapes": False, "rotate90": True,
                                 "useBlenderMaterialName": False, "preserveBoneMatrices": False,
                                 "exportBoundingBoxes": False, "autoSolveRepeatedUVs": True,
                                 "preserveSharpEdges": False})
    log(f"export mesh: {ok} -> {path} ({os.path.getsize(path)} bytes)")
    build_mdf(os.path.join(out_dir, f"{spec['name']}.mdf2{MDF_EXT}"), template_mdf)
    tex_dir = os.path.join(natives, *TEX_REL.split("/"))
    if not os.path.exists(os.path.join(tex_dir, f"MiquellaDevice_ALBD.tex{TEX_EXT}")):
        src = os.path.join(kit, "texture_sources")
        make_textures(src)
        convert_textures(src, os.path.join(kit, "dds"), tex_dir)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(kit, f"{spec['name']}_kit.blend"))


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.flush()
        os._exit(0)
