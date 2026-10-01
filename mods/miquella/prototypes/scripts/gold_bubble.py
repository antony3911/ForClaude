"""The hunting horn's echo bubbles in gold: a copy of the game's bubble material
(Art/VFX/Mesh/Common/Other/bubble/11_bubble_00.mdf2, the sphere the horn's echo effects
11_it05_000-042 show as their MESH) with gold colours and no rainbow sheen (DESIGN: floating gold
film bubbles). The shape stays the game's; the material goes over the game's file (patch pak).

The output is a modified game file: build it from the user's own extracted files, keep it out of
the repo.

Usage: python gold_bubble.py <extracted 11_bubble_00.mdf2.45> <out .mdf2.45>
Requires bpy 4.5 with RE Mesh Editor in the user addons dir.
"""
import os
import sys

import bpy  # noqa: F401  (RE Mesh Editor's modules expect Blender)

sys.path.insert(0, os.path.dirname(__file__))
from build_weapon_kit import MEMBRANES, enable_addon, log


def main():
    src, dst = sys.argv[1], sys.argv[2]
    enable_addon()
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    mdf = readMDF(src)
    props = MEMBRANES["bubble"][2]
    for mat in mdf.materialList:
        for p in mat.propertyList:
            if p.propName in props:
                log(f"  {mat.materialName}.{p.propName}: {p.propValue} -> {props[p.propName]}")
                p.propValue = list(props[p.propName])
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    writeMDF(mdf, dst)
    log(f"wrote {dst}")


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.flush()
        os._exit(0)
