"""Pack a mod's natives folder into a Wilds patch pak, then verify it by reading it back.

Wilds only loads our textures from a patch pak. This runs RE Asset Library's own
createPakPatch (the code behind its "Create Pak Patch" button) without Blender's UI,
packing only the natives folder (no READMEs, previews or .blend files), and then looks
every file up by its lower-case path, the way the game does, and compares the bytes.

Usage: python make_patch_pak.py <folder containing natives/> <out.pak> <dir holding a
       re_asset_library package (RE-Asset-Library checkout or symlink)>
"""
import filecmp
import os
import shutil
import sys
import tempfile


def main():
    src, out_pak, lib_parent = sys.argv[1:4]
    sys.path.insert(0, lib_parent)
    from re_asset_library.modules.pak.re_pak_utils import createPakPatch, extractFileList

    natives = os.path.join(src, "natives")
    if not os.path.isdir(natives):
        sys.exit(f"No natives folder in {src}")
    work = tempfile.mkdtemp(prefix="pak_")
    try:
        stage = os.path.join(work, "stage")
        shutil.copytree(natives, os.path.join(stage, "natives"))
        createPakPatch(stage, out_pak)

        files = []
        for root, _, names in os.walk(stage):
            for n in names:
                files.append(os.path.relpath(os.path.join(root, n), stage).replace(os.sep, "/"))
        check = os.path.join(work, "check")
        extractFileList([f.lower() for f in files], out_pak, check)
        bad = [f for f in files
               if not (os.path.isfile(os.path.join(check, f.lower()))
                       and filecmp.cmp(os.path.join(stage, f), os.path.join(check, f.lower()), shallow=False))]
        print(f"\nverified {len(files) - len(bad)}/{len(files)} files by lower-case path lookup")
        for f in bad:
            print("MISMATCH", f)
        return 1 if bad else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)      # RE Asset Library can leave threads behind; don't wait for them
