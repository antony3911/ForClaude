"""Bowgun grip options (user, 2026-10-03: the hunter never takes hold of the light / heavy
bowguns' grips -> "make it look right without being held; give me some options").

The woven pistol grip under the receiver reads as a handle, so an empty hand next to it looks
wrong. Each option replaces it with something that is plainly not a handle:

  O  now: the woven pistol grip, raked back (for comparison)
  A  scroll pendant: an ivory cord with a gold thread drops from under the receiver and rolls
     back into a volute, a smaller side branch curling the other way
  B  light drop: no handle; a short ivory stem under the receiver ends in a small halo holding
     a lit drop that floats below it (the floating-drop motif)
  C  gold filigree: no grip at all; two thin gold-wire scrolls of different sizes hug the
     underside of the receiver, a small drop of light between them
  D  braid pendant: a short three-strand braid (Miquella's braids) hangs from under the
     receiver, swaying back, a gold band and a drop of light at its end

Prototype axes: +Y muzzle, +Z up (the grip ran from (0, -0.08, -0.03) down to (0, -0.15, -0.17)).
Renders the heavy and light bowgun from the side and from behind over the shoulder (the
player's view), the options side by side; only our model.

Second set, `loop` (user: "or a grip that curves back and joins the stock?"): the grip stays,
its foot runs on back and joins the stock's underside, closing a thumbhole frame, so it reads as
part of the stock's openwork rather than a lone handle:

  A  woven loop: one woven tube, down the grip and back up into the stock, thinning
  B  scroll bridge: the woven grip, an ivory cord with a gold thread back to the stock, a gold
     scroll curling into the opening
  C  trident: the woven grip's foot splits into three strands fanning back to the stock (the
     circlet's trident)
  D  arc of light: the woven grip, a gold arc of light back to the stock, a drop of light in a
     halo floating in the opening

Third set, `frame` (user: "don't build on the old grip, design one that runs back"): no pistol
grip at all; one designed frame leaves the receiver's underside, sweeps down and back and joins
the stock's underside, enclosing an opening:

  A  scroll frame: an ivory cord with a gold thread, thick in front, thinning back; a volute
     curls into the opening off its lower back, a small gold scroll off its front
  B  branches: three slender twisting strand bundles that part in the middle (an openwork
     lattice, like branches) and meet again at both ends, a gold thread wound round the middle one
  C  harp: a smooth ivory arm with a gold inlay, five strings of light from it up to the body
     (the hunting horn's harp)
  D  braid: a three-strand braid makes the loop, gold bands at both joints, a drop of light
     hanging from its lowest point

Usage: python grip_options.py <out_dir> [test] [loop|frame] [O A B C D]
"""
import math
import os
import random
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "out/grip"
FLAGS = sys.argv[2:]
TEST = "test" in FLAGS
LOOP = "loop" in FLAGS
FRAME = "frame" in FLAGS
PICK = [f for f in FLAGS if f in ("O", "A", "B", "C", "D")] or ["O", "A", "B", "C", "D"]

import bpy                               # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
sys.argv = [sys.argv[0], OUT]
import common as c                       # noqa: E402
import motifs as m                       # noqa: E402
from motifs import V                     # noqa: E402
from motifs import smoothstep            # noqa: E402
import bowgun as hb                      # noqa: E402

PI = math.pi
NAMES = {"O": "現在（編織握把）", "A": "A 卷草垂飾", "B": "B 光滴垂飾", "C": "C 金絲卷草（無握把）", "D": "D 編髮垂飾"}
if LOOP:
    NAMES = {"O": "現在（編織握把）", "A": "A 編織環", "B": "B 卷草橋", "C": "C 三叉回流", "D": "D 光弧"}
if FRAME:
    NAMES = {"O": "現在（編織握把）", "A": "A 卷草框", "B": "B 枝條框", "C": "C 豎琴框", "D": "D 編髮框"}
TOP = V(0, -0.08, -0.03)                 # where the grip met the receiver
_KEYS = ("STOCK_END", "WRIST", "RECEIVER_END", "MUZZLE", "CONDUIT_R", "CONDUIT_Z")
HBG = {k: getattr(hb, k) for k in _KEYS}
HBG["section"], HBG["branch"] = hb.body_section, hb.branch_center
ORIGINAL_GRIP = hb.pistol_grip
import light_bowgun as lb                # noqa: E402  (sets the bowgun module to its slim frame)
LBG = {k: getattr(hb, k) for k in _KEYS}
LBG["section"], LBG["branch"] = hb.body_section, hb.branch_center


def use(frame):
    for k in _KEYS:
        setattr(hb, k, frame[k])
    hb.body_section, hb.branch_center = frame["section"], frame["branch"]


def materials(ivory):
    """The prototype's own ivory and light (made before the grip in hb.build), a lit drop."""
    light = bpy.data.materials.get("Light")
    lit = bpy.data.materials.get("Phial_Lit") or c.make_material(
        "Phial_Lit", c.PALETTE["glow"], roughness=0.1, emission=c.PALETTE["glow"], strength=3.0)
    return {"ivory": ivory, "light": light, "phial_lit": lit}


def under(body_top=None):
    """The receiver's underside just above the old grip's top (the body's lowest point there)."""
    ctr, _, rz = hb.body_section(TOP.y)
    return V(0, TOP.y, ctr.z - rz * 0.8) if body_top is None else body_top


def scroll_pendant(k, mats):
    root = under()
    side = m.plane_mapper(root, (0, 0, -1), (0, -1, 0))        # 2D x: down, y: back
    objs = m.tendril("GA_Scroll", side, (0, 0), 14, 0.17 * k, 1.35, 0.012 * k, mats,
                     offshoots=((0.4, -1, 0.42, -1.3),))
    objs += m.halo("GA_Band", root + V(0, 0, -0.012 * k), 0.012 * k, 0.0022 * k, (0, 0, 1), mats["light"])
    return objs


def light_drop(k, mats):
    root = under()
    tip = root + V(0, -0.012, -0.05) * k
    objs = [c.curve_tube("GB_Stem", [root + V(0, 0, 0.01), root + V(0, -0.004, -0.025) * k, tip],
                         [1.0, 0.8, 0.5], mats["ivory"], bevel=0.0065 * k, resolution=3)]
    drop = tip + V(0, -0.006, -0.05) * k
    objs += m.halo("GB_Halo", drop + V(0, 0, 0.004 * k), 0.022 * k, 0.0024 * k, (0, 1, 0.25), mats["light"])
    objs += m.droplet("GB_Drop", drop, 0.014 * k, (0, 0, -1), mats["phial_lit"], stretch=1.6)
    for s in (-1, 1):
        cur = m.plane_mapper(root + V(s * 0.006 * k, 0, -0.004), (0, 0, -1), (0, -s, 0))
        objs += m.tendril(f"GB_Curl_{s}", cur, (0, 0), 50, 0.04 * k, 1.5, 0.0035 * k, mats, strands=2,
                          strand_mat="light", gold=False)
    return objs


def gold_filigree(k, mats):
    root = under()
    objs = []
    for s, (length, turns) in ((1, (0.09, 1.4)), (-1, (0.065, 1.6))):
        plane = m.plane_mapper(root + V(0, s * 0.012 * k, -0.002), (0, s, 0), (0, 0, -1))   # along the belly
        objs += m.tendril(f"GC_Wire_{s}", plane, (0, 0), 12, length * k, -turns, 0.0042 * k, mats, strands=2,
                          strand_mat="light", gold=False, offshoots=((0.45, 1, 0.4, turns * 0.9),))
    objs += m.droplet("GC_Drop", root + V(0, 0, -0.012 * k), 0.008 * k, (0, 0, -1), mats["phial_lit"], stretch=1.4)
    return objs


def braid_pendant(k, mats):
    root = under()
    pts = [root + V(0, 0, 0.01), root + V(0, -0.012, -0.05) * k, root + V(0, -0.04, -0.1) * k,
           root + V(0, -0.075, -0.135) * k]
    center = m.resample(m.catmull(pts, 120), 100)
    objs = m.rope("GD_Braid", center, 0.011 * k, mats, strands=3, gold=True, taper=0.45, merge=0.97)
    tan = (center[-6] - center[-12]).normalized()
    objs += m.halo("GD_Band", center[-10], 0.0085 * k, 0.0019 * k, tan, mats["light"])
    objs += m.droplet("GD_Drop", center[-1] + tan * 0.01 * k, 0.0095 * k, tan, mats["phial_lit"], stretch=1.5)
    return objs


def loop_line():
    """The grip's foot on back to the stock's underside, a quarter of the way from the butt."""
    j_y = hb.STOCK_END + 0.25 * (hb.WRIST - hb.STOCK_END)
    ctr, _, rz = hb.body_section(j_y)
    J = V(0, j_y, ctr.z - rz * 0.7)
    B = V(0, -0.15, -0.17)                   # the grip's foot
    up = B + (TOP - B) * 0.15                # leaves the grip a little above its foot, rounding the corner
    back = m.resample(m.catmull([up, B + V(0, -0.025, -0.022), B + V(0, -0.075, -0.04), (B + J) / 2 + V(0, 0, -0.045),
                                 J + V(0, 0.035, -0.035), J], 140), 90)
    return B, J, back


def woven_loop(k, mats, rng):
    B, J, back = loop_line()
    path = [TOP + (back[0] - TOP) * (i / 10) for i in range(10)] + back
    return m.woven_tube("LA_Loop", path, 0.018, mats["ivory"], rng,
                        radius_fn=lambda u: 1.0 - 0.3 * smoothstep((u - 0.3) / 0.6))


def scroll_loop(k, mats, rng):
    objs = ORIGINAL_GRIP(mats["ivory"], rng)
    B, J, back = loop_line()
    objs += m.rope("LB_Cord", back, 0.012, mats, strands=3, gold=True, taper=0.3, merge=0.99)
    mid = back[len(back) // 2]
    plane = m.plane_mapper(mid + V(0, 0, 0.008), (0, 0, 1), (0, 1, 0))     # 2D x: up into the opening
    objs += m.tendril("LB_Scroll", plane, (0, 0), 8, 0.11, 1.5, 0.0062, mats, strands=2, strand_mat="light",
                      gold=False, offshoots=((0.4, -1, 0.5, -1.4),))
    return objs


def trident_loop(k, mats, rng):
    objs = ORIGINAL_GRIP(mats["ivory"], rng)
    B = V(0, -0.15, -0.17)
    for j, f in enumerate((0.12, 0.25, 0.4)):
        y = hb.STOCK_END + f * (hb.WRIST - hb.STOCK_END)
        ctr, _, rz = hb.body_section(y)
        J = V(0, y, ctr.z - rz * 0.7)
        pts = m.resample(m.catmull([B + V(0, -0.005, 0.006), B + V(0, -0.05, -0.022 + 0.01 * j),
                                    (B + J) / 2 + V(0, 0, -0.04 + 0.014 * j), J + V(0, 0.025, -0.02), J], 100), 70)
        objs.append(c.curve_tube(f"LC_Strand_{j}", pts, [1 - 0.45 * (i / 69) for i in range(70)], mats["ivory"],
                                 bevel=0.0068 - 0.0012 * j, resolution=3))
        if j == 1:
            objs += m.wound_cord("LC_Gold", pts, 0.0072, 5, 0.0016, mats, strand_mat="light")
    return objs


def light_loop(k, mats, rng):
    objs = ORIGINAL_GRIP(mats["ivory"], rng)
    B, J, back = loop_line()
    objs.append(c.curve_tube("LD_Arc", back, [1.0] * len(back), mats["light"], bevel=0.0045, resolution=3))
    low = back[len(back) // 2]
    hole = V(0, (B.y + J.y) / 2 + 0.012, (J.z + low.z) / 2 + 0.012)
    objs += m.halo("LD_Halo", hole, 0.021, 0.0022, (1, 0, 0), mats["light"])
    objs += m.droplet("LD_Drop", hole, 0.012, (0, 0, -1), mats["phial_lit"], stretch=1.5)
    return objs


def body_bottom(y, inset=0.7):
    ctr, _, rz = hb.body_section(y)
    return V(0, y, ctr.z - rz * inset)


def frame_line():
    """From the receiver's underside down and back to the stock's underside (a quarter of the
    way from the butt): the frame's centre line, front to back."""
    F = body_bottom(-0.05)
    J = body_bottom(hb.STOCK_END + 0.25 * (hb.WRIST - hb.STOCK_END))
    pts = [F, F + V(0, -0.025, -0.07), V(0, -0.145, -0.185), V(0, (-0.145 + J.y) / 2 - 0.02, -0.2),
           J + V(0, 0.04, -0.045), J]
    return F, J, m.resample(m.catmull(pts, 160), 120)


def in_plane_normal(path, i):
    """The normal in the side (YZ) plane, pointing into the opening (up)."""
    t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
    n = V(0, -t.z, t.y)
    return n if n.z > 0 else -n


def scroll_frame(k, mats, rng):
    F, J, path = frame_line()
    objs = m.rope("FA_Frame", path, 0.015, mats, strands=3, gold=True, taper=0.4, merge=0.99)
    p = path[78]
    plane = m.plane_mapper(p, in_plane_normal(path, 78), (0, 1, 0))     # 2D x: into the opening
    objs += m.tendril("FA_Volute", plane, (0, 0), 25, 0.12, 1.45, 0.0085, mats,
                      offshoots=((0.38, -1, 0.42, -1.4),))
    q = path[26]
    plane = m.plane_mapper(q, in_plane_normal(path, 26), (0, -1, 0))
    objs += m.tendril("FA_Front", plane, (0, 0), 20, 0.06, 1.6, 0.0045, mats, strands=2, strand_mat="light", gold=False)
    return objs


def branch_frame(k, mats, rng):
    F, J, path = frame_line()
    objs = []
    for j, s in enumerate((-1, 0, 1)):
        pts = [p + in_plane_normal(path, i) * (s * 0.028 * math.sin(math.pi * i / (len(path) - 1)) ** 1.2)
               for i, p in enumerate(path)]
        objs += m.strand_bundle(f"FB_Branch_{j}", pts, 0.0078, mats["ivory"], rng, n=7, twist=9.0,
                                radius_fn=lambda u: 0.75 + 0.35 * math.sin(math.pi * u), bevel=0.0026, tip_taper=0.05)
        if s == 0:
            objs += m.wound_cord("FB_Gold", pts, 0.0095, 7, 0.0016, mats, strand_mat="light")
    return objs


def harp_frame(k, mats, rng):
    F, J, path = frame_line()
    n = len(path)
    radii = [0.75 + 0.45 * math.sin(math.pi * i / (n - 1)) ** 0.8 for i in range(n)]
    objs = [c.curve_tube("FC_Arm", path, radii, mats["ivory"], bevel=0.0115, resolution=4)]
    inlay = [p - in_plane_normal(path, i) * 0.0105 * radii[i] for i, p in enumerate(path)]
    objs.append(c.curve_tube("FC_Inlay", inlay[6:-6], [1.0] * (n - 12), mats["light"], bevel=0.0018, resolution=2))
    for j in range(5):
        i = int((0.2 + 0.15 * j) * (n - 1))
        p = path[i]
        top = body_bottom(p.y, 0.6)
        objs.append(c.curve_tube(f"FC_String_{j}", [p + V(0, 0, 0.008), top], [1.0, 1.0], mats["light"],
                                 bevel=0.0016, resolution=2))
    return objs


def braid_frame(k, mats, rng):
    F, J, path = frame_line()
    objs = m.rope("FD_Braid", path, 0.016, mats, strands=3, gold=True, taper=0.25, merge=0.99)
    for name, i in (("FD_Band_F", 10), ("FD_Band_B", len(path) - 12)):
        t = (path[i + 2] - path[i - 2]).normalized()
        objs += m.halo(name, path[i], 0.0165, 0.0026, t, mats["light"])
    low = min(range(len(path)), key=lambda i: path[i].z)
    objs += m.halo("FD_Drop_Halo", path[low] + V(0, 0, -0.03), 0.013, 0.0018, (1, 0, 0), mats["light"])
    objs += m.droplet("FD_Drop", path[low] + V(0, 0, -0.032), 0.01, (0, 0, -1), mats["phial_lit"], stretch=1.5)
    objs.append(c.curve_tube("FD_Thread", [path[low] + V(0, 0, -0.012), path[low] + V(0, 0, -0.02)], [1, 1],
                             mats["light"], bevel=0.0012, resolution=2))
    return objs


OPTIONS = {"A": scroll_pendant, "B": light_drop, "C": gold_filigree, "D": braid_pendant}
SIZE = {"A": 1.7, "B": 1.5, "C": 1.9, "D": 1.35}        # each option about the old grip's size
LOOPS = {"A": woven_loop, "B": scroll_loop, "C": trident_loop, "D": light_loop}
FRAMES = {"A": scroll_frame, "B": branch_frame, "C": harp_frame, "D": braid_frame}


def build(gun, opt):
    use(HBG if gun == "hbg" else LBG)
    k = 1.0 if gun == "hbg" else 0.85
    if opt == "O":
        hb.pistol_grip = ORIGINAL_GRIP
    else:
        if FRAME:
            hb.pistol_grip = lambda material, rng: FRAMES[opt](k, materials(material), rng)
        elif LOOP:
            hb.pistol_grip = lambda material, rng: LOOPS[opt](k, materials(material), rng)
        else:
            hb.pistol_grip = lambda material, rng: OPTIONS[opt](k * SIZE[opt], materials(material))
    if gun == "hbg":
        _, glow = hb.build()
    else:
        _, glow, _ = lb.build()
    c.set_emission_strength(glow, 2.5)
    for name in ("Phial_Lit",):
        if bpy.data.materials.get(name):
            c.set_emission_strength(bpy.data.materials[name], 4.0)


def main():
    os.makedirs(OUT, exist_ok=True)
    res = (420, 300) if TEST else (760, 520)
    tiles = {}
    for gun in ("hbg", "lbg"):
        for opt in PICK:
            build(gun, opt)
            c.setup_render(samples=8 if TEST else 28, res=res, world_hex="#0E0E12", world_strength=0.3, glare=True)
            c.add_light("key", "AREA", (1.0, -0.6, 1.0), 120, size=1.0, target=(0, -0.1, -0.05))
            c.add_light("fill", "AREA", (-1.0, 0.2, 0.4), 40, size=1.0, target=(0, -0.1, -0.05))
            c.add_light("rim", "AREA", (0.0, 1.4, 0.9), 70, size=0.8, target=(0, -0.1, -0.05))
            dist = 1.35 if gun == "hbg" else 1.1
            paths = c.render_views(OUT, f"{gun}_{opt}", (0, -0.02, -0.07), dist,
                                   [("side", 90, 4), ("back", 28, 12)], lens=50)
            tiles[(gun, opt)] = paths
    from PIL import Image, ImageDraw, ImageFont
    font = None
    for f in (os.environ.get("MIQUELLA_FONT"), "C:/Windows/Fonts/msjh.ttc", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"):
        if f and os.path.exists(f):
            font = ImageFont.truetype(f, 26 if not TEST else 16)
            break
    W, H = res
    head = 96 if not TEST else 60
    rows = [("hbg", 0, "重弩・側面"), ("hbg", 1, "重弩・背後（玩家視角）"), ("lbg", 0, "輕弩・側面"),
            ("lbg", 1, "輕弩・背後（玩家視角）")]
    sheet = Image.new("RGB", (W * len(PICK), head + H * len(rows)), (20, 20, 24))
    d = ImageDraw.Draw(sheet)
    title = ("輕弩、重弩握把：重新設計一個從機匣繞回槍托的框（不用原本的握把）" if FRAME else
             "輕弩、重弩握把：底部繞回去跟槍托合體（像拇指孔槍托）" if LOOP else
             "輕弩、重弩握把：人物不會去握，換成不像把手的東西")
    d.text((14, 8), title, fill=(240, 210, 140), font=font)
    for ci, opt in enumerate(PICK):
        d.text((ci * W + 14, head - (40 if not TEST else 24)), NAMES[opt], fill=(255, 225, 150), font=font)
        for ri, (gun, vi, label) in enumerate(rows):
            sheet.paste(Image.open(tiles[(gun, opt)][vi]), (ci * W, head + ri * H))
            if ci == 0:
                d.text((10, head + ri * H + 8), label, fill=(200, 200, 200), font=font)
    out = os.path.join(OUT, "grip_frame_options.png" if FRAME else "grip_loop_options.png" if LOOP else "grip_options.png")
    sheet.save(out)
    print("WROTE", out, flush=True)


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.flush()
        os._exit(0)
