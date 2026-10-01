"""Print what matters for fitting a replacement Wilds .mesh: skeleton bones (rest
positions), materials, per-material vertex bounds (LOD 0), and which bones the vertices
are weighted to.

Uses RE Mesh Editor's file parser directly (its Blender import operator crashes headless).
Coordinates are the file's own: Y up, metres.

Usage: python inspect_wilds_mesh.py <file.mesh.241111606> [...]
Requires bpy 4.3.2+ (4.5 here) with RE Mesh Editor in the user addons dir.
"""
import sys

import bpy
import numpy as np

sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))


def fmt(v):
    return "(" + ", ".join(f"{x:+.3f}" for x in v) + ")"


def inspect(path):
    from re_mesh_editor.modules.mesh.file_re_mesh import readREMesh
    from re_mesh_editor.modules.mesh.re_mesh_parse import ParsedREMesh
    parsed = ParsedREMesh()
    parsed.ParseREMesh(readREMesh(path, 0), {"importAllLOD": False, "importShadowMesh": False,
                                            "importOcclusionMesh": False, "importBlendShapes": False})
    print(f"\n=== {path.replace(chr(92), '/').split('/')[-1]}")
    print(f"materials: {parsed.materialNameList}")
    bones = parsed.skeleton.boneList if parsed.skeleton else []
    weighted = parsed.skeleton.weightedBones if parsed.skeleton else []
    print(f"bones: {len(bones)}  weighted: {weighted}")
    for b in bones:
        m = np.array(b.worldMatrix.matrix)
        parent = bones[b.parentIndex].boneName if 0 <= b.parentIndex < len(bones) and b.parentIndex != b.boneIndex else "-"
        # RE matrices are row-major with translation in the last row.
        print(f"  {b.boneName:28s} parent={parent:20s} pos={fmt(m[3][:3])}"
              f" x={fmt(m[0][:3])} y={fmt(m[1][:3])} z={fmt(m[2][:3])}")
    allpts = []
    for lod in parsed.mainMeshLODList[:1]:
        for group in lod.visconGroupList:
            for sub in group.subMeshList:
                pts = np.array(sub.vertexPosList, dtype=float).reshape(-1, 3)
                if not len(pts):
                    continue
                allpts.append(pts)
                used = {}
                for idx, w in zip(sub.weightIndicesList, sub.weightList):
                    for i, wt in zip(idx, w):
                        if wt > 0.01:
                            name = weighted[i] if i < len(weighted) else f"#{i}"
                            used[name] = used.get(name, 0) + 1
                mat = parsed.materialNameList[sub.materialIndex]
                print(f"  group {group.visconGroupNum} sub {sub.subMeshIndex} [{mat}] verts={len(pts)}"
                      f" min={fmt(pts.min(0))} max={fmt(pts.max(0))} weights={used}")
    if allpts:
        pts = np.concatenate(allpts)
        print(f"  TOTAL min={fmt(pts.min(0))} max={fmt(pts.max(0))} size={fmt(pts.max(0) - pts.min(0))}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        inspect(p)
    sys.stdout.flush()
    import os
    os._exit(0)
