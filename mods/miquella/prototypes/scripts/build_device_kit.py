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
import math
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
    2.35 m like the original, the eye at the back.

    Which groups (the stake effects' mesh elements, read from the .efx, 2026-10-02): 104 fires
    (groups 4+5, then 7 in flight, 4+5 on impact), 105 drills (4+5), 105_pile the stake left in
    (9), 004 the final blast (7, and 0-3: the pieces flying off). Group 5 is the drill: the
    effect spawns many copies of it turning around the axis, so a whole needle there showed as
    a bundle of needles (user). The needle goes in 4, 7 and 9 only; 0-3 get small gold shards."""
    import devices
    import motifs as m
    mats = m.materials()
    mats["gold"] = devices.gold_material()
    to_file = Matrix.Translation((0, 0, 1.55)) @ Matrix.Scale(4.7, 4)
    parts = {}
    for g in (4, 7, 9):
        before = set(bpy.data.objects)
        devices.needle(mats, 0.5, Vector((0, 0, 0)), Vector((0, 0, -1)))
        parts[g] = [o for o in bpy.data.objects if o not in before and o.type in ("MESH", "CURVE")]
    # Shards: slivers of gold, a little under the original pieces' size (0.6-1.2 m in the file).
    for g, (length, width) in enumerate(((0.12, 0.012), (0.1, 0.01), (0.09, 0.011), (0.05, 0.008))):
        parts[g] = m.path_blade(f"Shard_{g}", [Vector((0, 0, -0.33 - length / 2)), Vector((0, 0, -0.33 + length / 2))],
                                (1, 0.3, 0), lambda t, w=width: w * math.sin(math.pi * t) ** 0.6 + 0.0005,
                                lambda t, w=width: w * 0.5 * math.sin(math.pi * t) ** 0.6 + 0.0004, mats["gold"],
                                n_sec=6, samples=12, subsurf=0)
    return {"name": "11_it07_000", "rel": "Art/VFX/Mesh/Weapon/it07", "objects": parts[7], "to_file": to_file,
            "parts": parts, "budget": 3500, "glow_material": True}


def wyvernblast():
    """The closed bud (petals at 8 degrees), +Y up like the original mine (its dome symmetric
    about Y, x and z +-0.25). Ours: prototype +Z up -> +Y, scaled 5 (0.39 high like the original).
    The ground is at the effect's origin, not at the dome's bottom (-0.13) as first assumed: the
    original's landed disc lies at y -0.05..+0.06, and with the bud's base at -0.13 the user saw
    more than 80 % of the open flower under the ground, only the top of its light (2026-10-03).
    So the base sits at +0.02: the open flower's lowest petal tips just above the ground."""
    import devices
    import motifs as m
    mats = m.materials()
    closed = devices.bud(mats, Vector((0, 0, 0)), 8, "Closed")
    opened = devices.bud(mats, Vector((0, 0, 0)), 62, "Open")
    axes = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))     # z -> y, y -> -z
    to_file = Matrix.Translation((0, 0.02, 0)) @ Matrix.Scale(5.0, 4) @ axes
    # The game's effect (11_it13_106) shows groups 0+1 while the shell flies and 0+2 once it has
    # landed (its mesh elements' group ranges): 0 the light inside, 1 the closed bud, 2 the open
    # flower on its scroll roots, so the bud opens as it lands (user, 2026-10-02: it never opened).
    light = [o for o in closed if "_Light" in o.name]
    parts = {0: light,
             1: [o for o in closed if o not in light and "_Root_" not in o.name],
             2: [o for o in opened if "_Light" not in o.name]}
    for o in [o for o in opened if "_Light" in o.name] + [o for o in closed if "_Root_" in o.name]:
        bpy.data.objects.remove(o, do_unlink=True)
    return {"name": "11_setbombshell_000", "rel": "Art/VFX/Mesh/Weapon/it13", "objects": light, "to_file": to_file,
            "parts": parts, "budget": 6000, "glow_material": True}


def shot_arrow(name, groups):
    """The bow's arrows in flight (Art/VFX/Mesh/common/shell/arrow/11_arrow_0x): the same
    arrow as the one on the string (it1199_0000_0) moved back 1.1 (nock -1.14, point on +Z
    at 1.588 like the originals). 02 has two groups (the head part separately): whole arrow in both."""
    import arsenal
    import motifs as m
    from build_weapon_kit import ARROW_NOCK, ARROW_TIP
    mats = m.materials()
    objs = arsenal.needle_arrow("Arrow", Vector((0, 0, ARROW_NOCK - 1.1)), Vector((0, 0, ARROW_TIP - 1.1)), mats)
    return {"name": name, "rel": "Art/VFX/Mesh/common/shell/arrow", "objects": objs, "to_file": Matrix.Identity(4),
            "groups": groups, "budget": 3000, "glow_material": True, "glow_intensity": 0.6}


def shellcase():
    """The gunlance's spent shells (Art/VFX/Mesh/Common/Shell/shellcase/11_shellcase_02, 0.035 x
    0.095 along Z, effect 11_it07_199 on reload): the user saw machine parts flying out. Ours:
    a small drop of light in a ring, the same size."""
    import motifs as m
    mats = m.materials()
    objs = m.droplet("Spent_Drop", (0, 0, -0.01), 0.013, (0, 0, 1), mats["light"], stretch=1.6)
    objs += m.halo("Spent_Halo", (0, 0, 0.0), 0.017, 0.0022, (0, 0, 1), mats["light"])
    return {"name": "11_shellcase_02", "rel": "Art/VFX/Mesh/Common/Shell/shellcase", "objects": objs,
            "to_file": Matrix.Identity(4), "groups": 1, "budget": 1200, "glow_material": True}


DEVICES = {"wyrmstake": wyrmstake, "wyvernblast": wyvernblast, "shellcase": shellcase,
           "arrow_00": lambda: shot_arrow("11_arrow_00", 1), "arrow_01": lambda: shot_arrow("11_arrow_01", 1),
           "arrow_02": lambda: shot_arrow("11_arrow_02", 2)}


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


# Our weapons' glowing material (dual blades kit): the effect cannot drive its parameters, so
# it keeps glowing gold (on the effect material the needle came out dark metal, user 2026-10-02).
GLOW_TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "..", "mhws", "MiquellaLight_DualBlades_kit", "natives",
                             "STM", "Art", "Model", "MiquellaLight", "DualBlades", "wp_miquella_db.mdf2.45")


def build_mdf(path, template_mdf, glow=False, intensity=2.5):
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    if glow:
        mdf = readMDF(GLOW_TEMPLATE)
        mat = copy.deepcopy(next(m for m in mdf.materialList if m.materialName == "MiquellaGlow"))
        mat.materialName = "lambert1"
        for t in mat.textureList:
            for kind in ("ALBD", "NRRO", "EMI"):
                if t.texturePath.upper().endswith(f"_{kind}.TEX"):
                    t.texturePath = f"{TEX_REL}/MiquellaDevice_{kind}.tex"
        for p in mat.propertyList:
            if p.propName == "Emissive_Intensity":
                p.propValue = [intensity]
        mdf.materialList = [mat]
        writeMDF(mdf, path)
        log(f"mdf (glow): {[(m.materialName, m.mmtrPath if hasattr(m, 'mmtrPath') else '') for m in readMDF(path).materialList]}")
        return
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
    if spec.get("parts"):
        # A different part in each group (built one after another, objects of the others kept).
        built = []
        for g, objs in sorted(spec["parts"].items()):
            part = build_mesh({**spec, "objects": objs}, mesh_col)
            part.name = f"Group_{g}_Sub_0__lambert1"
            built.append(part)
        for o in list(bpy.data.objects):
            if o not in built:
                bpy.data.objects.remove(o, do_unlink=True)
        log(f"groups: {sorted(spec['parts'])} (one part each)")
    else:
        export_groups(spec, build_mesh(spec, mesh_col), mesh_col)
    finish(spec, kit, template_mdf, mesh_col)


def export_groups(spec, obj, mesh_col):
    for o in list(bpy.data.objects):
        if o is not obj:
            bpy.data.objects.remove(o, do_unlink=True)
    groups = spec["groups"] if isinstance(spec["groups"], list) else list(range(spec["groups"]))
    obj.name = f"Group_{groups[0]}_Sub_0__lambert1"
    for g in groups[1:]:
        copy_obj = obj.copy()
        copy_obj.data = obj.data.copy()
        copy_obj.name = f"Group_{g}_Sub_0__lambert1"
        mesh_col.objects.link(copy_obj)
    log(f"groups: {groups} (the whole model in each)")


def finish(spec, kit, template_mdf, mesh_col):
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile
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
    build_mdf(os.path.join(out_dir, f"{spec['name']}.mdf2{MDF_EXT}"), template_mdf, spec.get("glow_material", False),
              spec.get("glow_intensity", 2.5))
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
