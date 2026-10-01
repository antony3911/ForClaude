"""Dump Wilds .mdf2 materials: shader (mmtr), flags, textures and parameters.

Usage: python inspect_wilds_mdf.py [--all-params] <file.mdf2.45> [...]
Without --all-params only parameters whose names hint at emission, colour, dissolve or
alpha are printed. Requires bpy 4.5 with RE Mesh Editor in the user addons dir.
"""
import re
import sys

import bpy

sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
INTERESTING = re.compile(r"emi|emis|color|colour|dissolve|alpha|glow|light|intens|fx", re.I)


def dump(path, all_params):
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF
    mdf = readMDF(path)
    print(f"\n=== {path.replace(chr(92), '/').split('/')[-1]}")
    for m in mdf.materialList:
        flags = m.flags.flagValues
        on = [n for n, *_ in type(flags)._fields_ if getattr(flags, n) and n not in ("TessFactor", "PhongFactor")]
        print(f"[{m.materialName}] mmtr={m.mmtrPath} shaderType={m.shaderType}")
        print(f"  flags: {on}")
        for t in m.textureList:
            print(f"  tex {t.textureType:36s} {t.texturePath}")
        for p in m.propertyList:
            if all_params or INTERESTING.search(p.propName):
                print(f"  prop {p.propName:36s} {p.propValue}")


if __name__ == "__main__":
    args = sys.argv[1:]
    all_params = "--all-params" in args
    for p in (a for a in args if a != "--all-params"):
        dump(p, all_params)
    sys.stdout.flush()
    import os
    os._exit(0)
