"""Extract files from the installed Monster Hunter Wilds paks by path, newest patch first.

Uses RE Asset Library's own pak reader (TOC, decryption, zstd/deflate), without Blender's UI.
Paths come from a file list such as REE.PAK.Tool's MHWs_STM_Release.list; each line is
matched against the given regular expressions. Files from later paks (patches) win.

Extracted files are Capcom's: keep the output folder OUTSIDE this repo, never commit it.

Usage: python extract_game_files.py <game dir> <file list> <out dir> <dir holding a
       re_asset_library package> <regex> [<regex> ...]
Example regex: "art/model/item/it02/00/0002/[^/]*\\.(mesh|mdf2)\\."
"""
import os
import re
import sys
import zlib


def main():
    game_dir, list_path, out_dir, lib_parent, *patterns = sys.argv[1:]
    if not patterns:
        sys.exit(__doc__)
    sys.path.insert(0, lib_parent)
    import zstandard
    from re_asset_library.modules.pak.file_re_pak import ReadPakTOC
    from re_asset_library.modules.pak.re_pak_utils import (CompressionTypes, concatInt,
                                                           pathToPakHash, scanForPakFiles)
    from re_asset_library.modules.encryption.re_pak_encryption import decryptResource

    regexes = [re.compile(p, re.I) for p in patterns]
    with open(list_path, encoding="utf-8") as f:
        wanted = sorted({line.strip() for line in f
                         if line.strip() and any(r.search(line) for r in regexes)})
    print(f"{len(wanted)} paths match")
    if not wanted:
        return 1

    hashes = {pathToPakHash(p): p for p in wanted}
    found = {}                                   # path -> (pak, entry); later paks override
    for pak in scanForPakFiles(game_dir):
        for entry in ReadPakTOC(pak):
            path = hashes.get(concatInt(entry.hashNameLower, entry.hashNameUpper))
            if path:
                found[path] = (pak, entry)

    zstd = zstandard.ZstdDecompressor()
    for path in wanted:
        if path not in found:
            print("NOT IN PAKS", path)
            continue
        pak, entry = found[path]
        with open(pak, "rb") as s:
            s.seek(entry.offset)
            data = s.read(entry.compressedSize or entry.decompressedSize)
        if entry.encryptionType > 0:
            data = decryptResource(data)
        if entry.compressionType == CompressionTypes.COMPRESSION_TYPE_DEFLATE:
            data = zlib.decompress(data, wbits=-zlib.MAX_WBITS)
        elif entry.compressionType == CompressionTypes.COMPRESSION_TYPE_ZSTD:
            data = zstd.decompress(data, max_output_size=entry.decompressedSize)
        out = os.path.join(out_dir, *path.split("/"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(data)
        print(f"{os.path.basename(pak)}: {path} ({len(data)} bytes)")
    print(f"extracted {sum(p in found for p in wanted)}/{len(wanted)}")
    return 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)      # RE Asset Library can leave threads behind; don't wait for them
