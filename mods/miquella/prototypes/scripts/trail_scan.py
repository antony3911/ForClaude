"""List the attack trails in the game's weapon effects and their colours (user, 2026-10-02:
the long sword's red-spirit trail was red; other weapons may have coloured trails too).

A trail here is an entry drawn as a ribbon (TypeRibbonFollow / Length / Particle, GPU ribbon)
or named like one (trail, ribbon, kiseki). Each is listed with its colours, named by hue, and
whether a pak of ours already replaces the file (the work folders' natives).

Usage: python trail_scan.py <extracted natives root> <work dir> [out.md]
"""
import colorsys
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
from efx_walk import Efx
from recolor_efx import COLOR_FIELDS

RIBBONS = {33: "follow", 34: "length", 38: "particle", 264: "gpu ribbon"}
NAMED = ("trail", "ribbon", "kiseki", "tr_")


def hue_name(r, g, b, a):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if v < 0.12 or a == 0:
        return None
    if s < 0.18:
        return "white" if v > 0.6 else "grey"
    deg = h * 360
    for limit, name in ((15, "red"), (32, "orange"), (50, "gold"), (70, "yellow"), (160, "green"),
                        (190, "cyan"), (260, "blue"), (300, "purple"), (340, "pink"), (361, "red")):
        if deg < limit:
            return name


def scan(path):
    data = open(path, "rb").read()
    try:
        efx = Efx(data)
    except Exception as e:                       # noqa: BLE001 (a file the walker does not handle)
        return None, str(e)
    trails = {}
    owners_ribbon = {a.owner for a in efx.attrs if a.type in RIBBONS}
    for a in efx.attrs:
        named = any(k in a.owner.lower() for k in NAMED)
        if a.owner not in owners_ribbon and not named:
            continue
        for fname, off in COLOR_FIELDS.get(a.type, {}).items():
            if off + 4 > a.size:
                continue
            r, g, b, al = data[a.data_start + off:a.data_start + off + 4]
            name = hue_name(r, g, b, al)
            if name:
                trails.setdefault(a.owner, set()).add(f"{name} #{r:02X}{g:02X}{b:02X}")
    params = [e["name"] for e in efx.expressions if e["type"] == 1]
    return {"trails": trails, "params": params}, None


def main():
    root, work = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else None
    ours = {os.path.basename(p).split(".")[0]
            for p in glob.glob(os.path.join(work, "*", "natives", "**", "*.efx.*"), recursive=True)}
    files = sorted(glob.glob(os.path.join(root, "natives/stm/art/vfx/effecteditor/weapon/it*/*.efx.*"))
                   + glob.glob(os.path.join(root, "natives/stm/art/vfx/effecteditor/player/pl_cm/*/*trail*.efx.*")))
    lines = ["| file | in our pak | trail entries: colours | colour parameters |", "|---|---|---|---|"]
    for p in files:
        stem = os.path.basename(p).split(".")[0]
        res, err = scan(p)
        if err:
            lines.append(f"| {stem} | | (not read: {err[:40]}) | |")
            continue
        if not res["trails"]:
            continue
        desc = "; ".join(f"{k}: {', '.join(sorted(v))}" for k, v in sorted(res["trails"].items()))
        lines.append(f"| {stem} | {'yes' if stem in ours else ''} | {desc} | {', '.join(res['params'])} |")
    text = "\n".join(lines)
    if out:
        open(out, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
