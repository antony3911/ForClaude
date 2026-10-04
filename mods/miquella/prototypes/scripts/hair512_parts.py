"""Step 1 of 2 for hair512_braids.py. Import hairstyle 512, split the hair into loose parts, report parts weighted to the braid
(Mituami) bones, save a .blend for later steps."""
import os, sys
import bpy, bmesh
from collections import Counter

ROOT = "C:/Users/anton/MiquellaTools/extracted/natives/stm/art/model/character"
OUT = "C:/Users/anton/MiquellaTools/work/hair512"
os.makedirs(OUT, exist_ok=True)
OPTS = {"clearScene": True, "createCollections": True, "loadMaterials": False,
        "loadMDFData": False, "loadShellFur": False, "loadUnusedTextures": False,
        "loadUnusedProps": False, "useBackfaceCulling": False, "reloadCachedTextures": False,
        "mdfPath": "", "importAllLODs": False, "importBlendShapes": False, "rotate90": True,
        "mergeArmature": "", "importArmatureOnly": False, "mergeGroups": False,
        "importShadowMeshes": False, "importOcclusionMeshes": False, "importBoundingBoxes": False}


def main():
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile
    # MIQUELLA_HAIR_SEX=f: the female hunter's 512 (ch01_001_0512; the user's hunter is female)
    sex = "001" if os.environ.get("MIQUELLA_HAIR_SEX") == "f" else "000"
    importREMeshFile(f"{ROOT}/ch01/{sex}/0/512/ch01_{sex}_0512.mesh.241111606", OPTS)
    for o in bpy.data.objects:
        print("OBJ", o.name, o.type, len(o.data.vertices) if o.type == "MESH" else "",
              [m.name for m in o.data.materials] if o.type == "MESH" else "")
    hair = next(o for o in bpy.data.objects if o.type == "MESH" and "hair" in o.name.lower()
                and len(o.data.vertices) > 10000)
    names = {g.index: g.name for g in hair.vertex_groups}
    bm = bmesh.new()
    bm.from_mesh(hair.data)
    dl = bm.verts.layers.deform.active
    seen = set()
    parts = []
    for v in bm.verts:
        if v in seen:
            continue
        stack, comp = [v], []
        seen.add(v)
        while stack:
            x = stack.pop()
            comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        w = Counter()
        for x in comp:
            for gi, wt in x[dl].items():
                w[names[gi].rsplit("_CH", 1)[0] if "_CH" in names[gi] else names[gi]] += wt
        top = w.most_common(1)[0][0]
        ys = [x.co.z for x in comp]
        parts.append((top, len(comp), min(ys), max(ys), comp))
    print("parts", len(parts))
    c = Counter(p[0] for p in parts)
    print("dominant bone groups:", c.most_common(40))
    mit = [p for p in parts if "Mituami" in p[0]]
    for p in sorted(mit, key=lambda p: -p[1])[:40]:
        print("MIT verts", p[1], "z %.3f..%.3f" % (p[2], p[3]))
    # Tag braid parts with a vertex group for later use
    vg = hair.vertex_groups.new(name="BRAID_PART")
    idx = [x.index for p in mit for x in p[4]]
    bm.free()
    vg.add(idx, 1.0, "REPLACE")
    bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/hair512{'_f' if sex == '001' else ''}.blend")
    print("saved", len(idx), "braid verts", flush=True)


try:
    main()
finally:
    sys.stdout.flush()
    os._exit(0)
