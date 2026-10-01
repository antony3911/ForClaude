"""Recolour Monster Hunter Wilds .efx files to Miquella's palette: red -> gold, blue -> silver.

For the dual blades (user, 2026-10-01): demon mode's red body glow, flames and the
archdemon attack trail become gold; the blue state (perfect evade in demon mode) with its
blue body glow and trail becomes silver.

Only colour fields whose meaning is known are touched (kagenocookie's REE-EFX-Unified
template, the struct variants Wilds uses), plus colour expression parameters (their
default values). Within one effect entry that has any blue colour, red colours become
silver too (that entry belongs to the blue state). Saturation, brightness and alpha are kept
for gold; silver is the same brightness with almost no colour.

The output is a modified game file: build it from the user's own game files, install it in
a patch pak, and do not commit it to the repo. If a game update changes the effect, rebuild.

Usage: python recolor_efx.py <in.efx.5571972> <out.efx.5571972>
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
}
TYPE_NAMES = {38: "TypeRibbonParticle", 78: "TypeNoDraw", 242: "RgbCommon"}
GOLD_HUE = 38.0                 # a deep gold, so strong glow blooms gold rather than white
SILVER_HUE, SILVER_SAT, SILVER_VALUE = 220.0, 0.08, 0.9


def classify(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    deg = h * 360
    if s < 0.3 or v < 0.2:
        return None
    if deg < 25 or deg > 320:
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


def recolor(data, log=print):
    data = bytearray(data)
    efx = Efx(bytes(data))
    changed = 0

    def patch(offset, label, blue_entry=False):
        nonlocal changed
        r, g, b, a = data[offset:offset + 4]
        kind = classify(r, g, b)
        if not kind:
            return
        new = to_silver(r, g, b) if kind == "blue" or blue_entry else to_gold(r, g, b)
        data[offset:offset + 3] = bytes(new)
        log(f"  {label}: {r:02X}{g:02X}{b:02X}{a:02X} -> {new[0]:02X}{new[1]:02X}{new[2]:02X}{a:02X}")
        changed += 1

    for e in efx.expressions:
        if e["type"] == 1:                       # colour expression parameter (default value)
            patch(e["value_offset"], f"expression '{e['name']}'")
    fields = [(a, name, off) for a in efx.attrs for name, off in COLOR_FIELDS.get(a.type, {}).items()
              if off + 4 <= a.size]
    blue_entries = {a.owner for a, _, off in fields
                    if classify(*data[a.data_start + off:a.data_start + off + 3]) == "blue"}
    for a, name, off in fields:
        patch(a.data_start + off, f"{a.owner} {TYPE_NAMES[a.type]}.{name}", a.owner in blue_entries)
    Efx(bytes(data))                             # still walks cleanly
    return bytes(data), changed


def main():
    src, dst = sys.argv[1], sys.argv[2]
    out, n = recolor(open(src, "rb").read())
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst, "wb").write(out)
    print(f"{n} colours changed -> {dst}")


if __name__ == "__main__":
    main()
