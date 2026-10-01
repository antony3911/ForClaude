"""Recolour the red parts of a Monster Hunter Wilds .efx to Miquella gold.

Only colour fields whose meaning is known (kagenocookie's REE-EFX-Unified template, the
struct variants Wilds uses) are touched, and only when they are red: the hue is moved to
gold, saturation, brightness and alpha are kept. Other colours (e.g. the blue variants in
the same file) stay as they are.

The output is a modified game file: build it from the user's own game files, install it in
a patch pak, and do not commit it to the repo. If a game update changes the effect, rebuild.

Usage: python recolor_efx.py <in.efx.5571972> <out.efx.5571972> [gold hue in degrees, default 38]
"""
import colorsys
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
from efx_walk import Efx

# Wilds attribute type id -> {field name: offset of an RGBA8 colour after itemType/itemSize}
COLOR_FIELDS = {
    38: {"color1": 8, "color2": 12, "ukn22": 92, "ukn23": 96, "ukn24": 100},   # TypeRibbonParticle (DD2 layout)
    242: {"greenChColor": 8, "greenChColorRange": 12, "redChColor": 28, "redChColorRange": 32},  # RgbCommon (RE4 layout)
}
TYPE_NAMES = {38: "TypeRibbonParticle", 242: "RgbCommon"}


def is_red(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    deg = h * 360
    return s > 0.45 and v > 0.2 and (deg < 25 or deg > 330)


def to_gold(r, g, b, hue):
    _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    nr, ng, nb = colorsys.hsv_to_rgb(hue / 360, s, v)
    return round(nr * 255), round(ng * 255), round(nb * 255)


def recolor(data, hue=38.0, log=print):
    data = bytearray(data)
    efx = Efx(bytes(data))
    changed = 0

    def patch(offset, label):
        nonlocal changed
        r, g, b, a = data[offset:offset + 4]
        if is_red(r, g, b):
            nr, ng, nb = to_gold(r, g, b, hue)
            data[offset:offset + 3] = bytes((nr, ng, nb))
            log(f"  {label}: {r:02X}{g:02X}{b:02X}{a:02X} -> {nr:02X}{ng:02X}{nb:02X}{a:02X}")
            changed += 1

    for e in efx.expressions:
        if e["type"] == 1:                       # colour expression parameter (default value)
            patch(e["value_offset"], f"expression '{e['name']}'")
    for attr in efx.attrs:
        for name, off in COLOR_FIELDS.get(attr.type, {}).items():
            if off + 4 <= attr.size:
                patch(attr.data_start + off, f"{attr.owner} {TYPE_NAMES[attr.type]}.{name}")
    Efx(bytes(data))                             # still walks cleanly
    return bytes(data), changed


def main():
    src, dst = sys.argv[1], sys.argv[2]
    hue = float(sys.argv[3]) if len(sys.argv) > 3 else 38.0
    out, n = recolor(open(src, "rb").read(), hue)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst, "wb").write(out)
    print(f"{n} colours changed -> {dst}")


if __name__ == "__main__":
    main()
