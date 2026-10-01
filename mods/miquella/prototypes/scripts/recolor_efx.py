"""Recolour Monster Hunter Wilds .efx files to Miquella's palette: red -> gold, blue -> silver.

For the dual blades (user, 2026-10-01): demon mode's red body glow, flames and the
archdemon attack trail become gold; the blue state (perfect evade in demon mode) with its
blue body glow and trail becomes silver.

Only colour fields whose meaning is known are touched (kagenocookie's REE-EFX-Unified
template, the struct variants Wilds uses: player glow, ribbons, billboards, GPU particles,
channel colours), plus colour expression parameters (their default values). Within one effect entry that has any blue colour, red colours become
silver too (that entry belongs to the blue state). Saturation, brightness and alpha are kept
for gold; silver is the same brightness with almost no colour.

The output is a modified game file: build it from the user's own game files, install it in
a patch pak, and do not commit it to the repo. If a game update changes the effect, rebuild.

Usage: python recolor_efx.py [options] <in.efx.5571972> <out.efx.5571972>
  --warm            red, orange and yellow -> gold (default: red only)
  --no-silver       leave blue alone (default: blue -> silver)
  --hide A,B        entries whose name contains A or B: every colour set to transparent black
                    (great sword: PLE_Body,PLE_IMP = the glow the game puts on the hunter's body)
  --skip-param A    colour parameters whose name contains A are left alone (e.g. Blood)
Great sword / light bowgun (2026-10-02): --warm --no-silver, and for the great sword
--hide PLE_Body,PLE_IMP --skip-param Blood (the user wants the charge shown on the blade only).
"""
import colorsys
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from efx_walk import Efx

# Wilds attribute type id -> {field name: offset of an RGBA8 colour after itemType/itemSize}
COLOR_FIELDS = {
    38: {"color1": 8, "color2": 12, "ukn22": 92, "ukn23": 96, "ukn24": 100},   # TypeRibbonParticle (DD2 layout)
    78: {"color": 8, "colorRange": 12},                                        # TypeNoDraw (RE7 layout; player glow)
    242: {"greenChColor": 8, "greenChColorRange": 12, "redChColor": 28, "redChColorRange": 32},  # RgbCommon (RE4)
    # uniqueId, blendFlags, then color / colorRange in all of these (template layouts for Wilds)
    25: {"color": 8, "colorRange": 12},          # TypeBillboard3D: glows, flames
    33: {"color": 8, "colorRange": 12},          # TypeRibbonFollow: trails
    34: {"color": 8, "colorRange": 12},          # TypeRibbonLength: flame streaks
    258: {"color": 8, "colorRange": 12},         # TypeGpuBillboard: GPU particles
    264: {"color": 8, "colorRange": 12},         # TypeGpuRibbonLength: GPU sparks
}
TYPE_NAMES = {38: "TypeRibbonParticle", 78: "TypeNoDraw", 242: "RgbCommon", 25: "TypeBillboard3D",
              33: "TypeRibbonFollow", 34: "TypeRibbonLength", 258: "TypeGpuBillboard", 264: "TypeGpuRibbonLength"}
GOLD_HUE = 38.0                 # a deep gold, so strong glow blooms gold rather than white
SILVER_HUE, SILVER_SAT, SILVER_VALUE = 220.0, 0.08, 0.9


def classify(r, g, b, warm=False):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    deg = h * 360
    if s < 0.3 or v < 0.2:
        return None
    if deg < (70 if warm else 25) or deg > 320:
        return "red"
    if 190 < deg < 265:
        return "blue"
    return None


def to_gold(r, g, b):
    _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(GOLD_HUE / 360, s, v))


def to_silver(r, g, b):
    _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(SILVER_HUE / 360, SILVER_SAT * s, SILVER_VALUE * v))


def recolor(data, log=print, warm=False, silver=True, hide=(), skip_params=()):
    data = bytearray(data)
    efx = Efx(bytes(data))
    changed = 0

    def patch(offset, label, blue_entry=False):
        nonlocal changed
        r, g, b, a = data[offset:offset + 4]
        kind = classify(r, g, b, warm)
        if not kind or (kind == "blue" and not silver):
            return
        new = to_silver(r, g, b) if silver and (kind == "blue" or blue_entry) else to_gold(r, g, b)
        data[offset:offset + 3] = bytes(new)
        log(f"  {label}: {r:02X}{g:02X}{b:02X}{a:02X} -> {new[0]:02X}{new[1]:02X}{new[2]:02X}{a:02X}")
        changed += 1

    for e in efx.expressions:
        if e["type"] == 1 and not any(k in e["name"] for k in skip_params):   # colour parameter default
            patch(e["value_offset"], f"expression '{e['name']}'")
    fields = [(a, name, off) for a in efx.attrs for name, off in COLOR_FIELDS.get(a.type, {}).items()
              if off + 4 <= a.size]
    hidden = [(a, name, off) for a, name, off in fields if any(k in a.owner for k in hide)]
    for a, name, off in hidden:
        at = a.data_start + off
        log(f"  hide {a.owner} {TYPE_NAMES[a.type]}.{name}: {data[at:at + 4].hex()} -> 00000000")
        data[at:at + 4] = bytes(4)
        changed += 1
    fields = [f for f in fields if f not in hidden]
    blue_entries = {a.owner for a, _, off in fields
                    if silver and classify(*data[a.data_start + off:a.data_start + off + 3]) == "blue"}
    for a, name, off in fields:
        patch(a.data_start + off, f"{a.owner} {TYPE_NAMES[a.type]}.{name}", a.owner in blue_entries)
    Efx(bytes(data))                             # still walks cleanly
    return bytes(data), changed


def main():
    args, opts = sys.argv[1:], {}
    while args and args[0].startswith("--"):
        flag = args.pop(0)
        if flag == "--warm":
            opts["warm"] = True
        elif flag == "--no-silver":
            opts["silver"] = False
        elif flag == "--hide":
            opts["hide"] = tuple(args.pop(0).split(","))
        elif flag == "--skip-param":
            opts["skip_params"] = tuple(args.pop(0).split(","))
        else:
            sys.exit(f"unknown option {flag}")
    src, dst = args
    out, n = recolor(open(src, "rb").read(), log=lambda m: None, **opts)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst, "wb").write(out)
    print(f"{n} colours changed -> {dst}")


if __name__ == "__main__":
    main()
