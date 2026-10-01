"""Action-state previews: how a weapon's own parts react to weapon actions (visual only).

Each set renders the same weapon in several states side by side with labels, to agree on
the look before building the in-game version (material parameters, parts shown/hidden or
faded with Dissolve, parts moved by bones; see mods/research/mhws_modding_notes.md).

Sets:
  great_sword_charge  normal (gold) / charge 1 (bright gold) / 2 (brighter gold) / 3 (white light)
  dual_blades_demon   normal / splitting / demon mode (three blades) / archdemon (bright gold)
  dual_blades_split_point  demon pose: side blades branching further up the blade, a bit shorter
  hammer_charge       levels 0-3: more rings around the head, the caged sun brightens
  lance_charge        levels 0-3: a cone of large rings grows root to tip, brighter each level
  lance_full_variants full charge with the cone of light at different strengths
  gunlance_reload     rest / spring compressed (core charging) / spring rebounds
  long_sword_spirit   spirit levels: pale gold / gold / bright gold / white, light flowing on the hamon
  insect_glaive_extracts  extracts as scarlet rot / frost / frenzied flame, two layouts
  switch_axe_states   switch gauge on the phials, power axe, sword mode, amped
  charge_blade_states phials, shield charge, sword boost, axe boost
  bow_charge          charge levels light the rings ahead of the arrow
  bowgun_gauges       ignition / rapid fire gauge on the floating phials
  hunting_horn_notes  notes light the strings, playing spreads the sound rings
  shield_guard        guard and perfect guard flash on the energy shield

Usage: python states.py <set> <out_dir>
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import common as c
import motifs as m
from motifs import V

SET = sys.argv[1] if len(sys.argv) > 1 else "great_sword_charge"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join("out", SET)
def _cjk_font():
    """A font with Chinese glyphs for the labels: Linux (WenQuanYi) or Windows (Microsoft
    JhengHei / MingLiU); set MIQUELLA_FONT to use another."""
    for path in (os.environ.get("MIQUELLA_FONT", ""), "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                 r"C:\Windows\Fonts\msjh.ttc", r"C:\Windows\Fonts\msjhbd.ttc", r"C:\Windows\Fonts\mingliu.ttc",
                 "/System/Library/Fonts/PingFang.ttc"):
        if path and os.path.exists(path):
            return path
    raise FileNotFoundError("No CJK font found; set MIQUELLA_FONT to a .ttc/.ttf with Chinese glyphs")


FONT = _cjk_font()
# "Bright gold" used by every powered-up state that is not the great sword's white stage.
# Stronger and more saturated than the normal gold, so the bloom grows into a gold aura
# instead of washing out toward white.
BRIGHT_BLADE = ("#FF9E18", "#FF7A00", 12.0)     # blade core, blade edge, strength
BRIGHT_LIGHT = ("#FF9A10", 12.0)                # rings, halos, droplets
BRIGHT_CORE = ("#FFB030", 14.0)                 # core lines


# ------------------------------------------------------------------ helpers

def capture_build(builder):
    """Run an arsenal builder without its render step and return its materials."""
    captured = {}
    original = m.render_sheets

    def keep(out, stem, mats, *args, **kwargs):
        captured["mats"] = mats

    m.render_sheets = keep
    try:
        builder()
    finally:
        m.render_sheets = original
    return captured["mats"]


def ramp_node(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "VALTORGB")


def set_blade(mat, core_hex, edge_hex, strength):
    """Blade material: emission ramp from the facing core colour to the edge colour."""
    ramp = ramp_node(mat)
    ramp.color_ramp.elements[0].color = c.hex_to_linear(core_hex)
    ramp.color_ramp.elements[1].color = c.hex_to_linear(edge_hex)
    c.set_emission_strength(mat, strength)


def set_glow(mat, hex_color, strength):
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission Color"].default_value = c.hex_to_linear(hex_color)
    bsdf.inputs["Base Color"].default_value = c.hex_to_linear(hex_color)
    bsdf.inputs["Emission Strength"].default_value = strength


def brighten(mats):
    set_blade(mats["blade"], *BRIGHT_BLADE)
    set_glow(mats["light"], *BRIGHT_LIGHT)
    set_glow(mats["core"], *BRIGHT_CORE)


def show(objs, visible):
    for o in objs:
        o.hide_render = not visible
        show(o.children, visible)


def stage_lights(target, distance, res=(600, 1000)):
    k = distance / 2.0
    tgt = Vector(target)
    c.setup_render(samples=32, res=res, world_hex="#0E0E12", world_strength=0.25, glare=True)
    c.add_light("key", "AREA", tgt + Vector((1.0, -0.6, 1.0)) * k, 110 * k * k, size=1.0 * k, target=tgt)
    c.add_light("fill", "AREA", tgt + Vector((-1.0, 0.2, 0.4)) * k, 38 * k * k, size=1.0 * k, target=tgt)
    c.add_light("rim", "AREA", tgt + Vector((0.0, 1.4, 0.9)) * k, 65 * k * k, size=0.8 * k, target=tgt)


def labelled_strip(paths, labels, out_path, title, cols=None):
    """Panels in a row (or a grid of `cols` columns), a label above each, a title on top."""
    from PIL import Image, ImageDraw, ImageFont
    imgs = [Image.open(p).convert("RGB") for p in paths]
    w, h = imgs[0].size
    cols = cols or len(imgs)
    rows = (len(imgs) + cols - 1) // cols
    band, head = 70, 80
    sheet = Image.new("RGB", (w * cols, head + rows * (h + band)), (14, 14, 18))
    draw = ImageDraw.Draw(sheet)
    f_title = ImageFont.truetype(FONT, 40)
    f_label = ImageFont.truetype(FONT, 32)
    tw = draw.textlength(title, font=f_title)
    draw.text(((sheet.width - tw) / 2, 18), title, font=f_title, fill=(240, 220, 170))
    for i, (img, text) in enumerate(zip(imgs, labels)):
        x, y = (i % cols) * w, head + (i // cols) * (h + band)
        sheet.paste(img, (x, y + band))
        lw = draw.textlength(text, font=f_label)
        draw.text((x + (w - lw) / 2, y + 16), text, font=f_label, fill=(235, 235, 235))
        if i % cols:
            draw.line([(x, y), (x, y + h + band)], fill=(60, 60, 66), width=2)
    sheet.save(out_path)
    return out_path


# ------------------------------------------------------------------ great sword charge

def blade_band(mat, centers, width, hex_color, amount):
    """Sweep bands of colour over a blade material's emission (its length is generated z),
    so the flowing light reads even on a white-hot blade."""
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    for nd in [nd for nd in nodes if nd.label == "bladeband"]:
        nodes.remove(nd)
    ramp = ramp_node(mat)
    links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    if not centers:
        return
    mix = nodes.new("ShaderNodeMix")
    mix.label = "bladeband"
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = c.hex_to_linear(hex_color)
    amt = nodes.new("ShaderNodeMath")
    amt.label = "bladeband"
    amt.operation = "MULTIPLY"
    amt.inputs[1].default_value = amount
    links.new(band_sum(nodes, links, centers, width, "bladeband"), amt.inputs[0])
    links.new(amt.outputs["Value"], mix.inputs["Factor"])
    links.new(ramp.outputs["Color"], mix.inputs["A"])
    links.new(mix.outputs["Result"], bsdf.inputs["Emission Color"])


def great_sword_charge():
    """Three charge levels (the game's): bright gold, brighter gold, white. At the third,
    two bands of gold light flow along the temper lines like the long sword's hamon (the
    user asked for it, only at level 3)."""
    import arsenal
    c.reset_scene()
    mats = capture_build(arsenal.great_sword)
    m.glow_mode(mats)
    flow = flow_material("Temper_Flow")
    for line in [o for o in bpy.data.objects if "_Temper_" in o.name]:
        ribbon = line.copy()
        ribbon.data = line.data.copy()
        ribbon.name = line.name.replace("_Temper_", "_Flow_")
        ribbon.data.bevel_depth = line.data.bevel_depth * 2.4
        ribbon.data.materials[0] = flow
        ribbon.location.y += 0.0008 * (-1 if line.name.endswith("-1") else 1)
        bpy.context.scene.collection.objects.link(ribbon)
    target, distance = (0.04, 0, 0.8), 3.2
    stage_lights(target, distance)
    stages = [
        # label, blade (core, edge, strength), light (colour, strength), core strength, flow
        ("一般（金）", (c.PALETTE["blade_core"], c.PALETTE["blade_edge"], 2.2), (c.PALETTE["glow"], 2.5), 3.0, None),
        ("一段蓄力（亮金）", BRIGHT_BLADE, BRIGHT_LIGHT, BRIGHT_CORE[1], None),
        ("二段蓄力（更亮的金）", ("#FFC860", "#FF9A20", 24.0), ("#FFB848", 20.0), 26.0, None),
        ("三段蓄力（白光）", ("#FFFBF0", "#FFE7B0", 4.5), ("#FFF2D6", 5.5), 7.0, ([0.25, 0.7], 0.1, "#FF9A10", 60.0)),
    ]

    def apply(stage, centers=None):
        label, blade, light, s_core, fl = stage
        set_blade(mats["blade"], *blade)
        set_glow(mats["light"], *light)
        set_glow(mats["core"], blade[0], s_core)
        if fl:
            bands = centers if centers is not None else fl[0]
            set_flow(flow, bands, fl[1], fl[2], fl[3])
            blade_band(mats["blade"], bands, fl[1], fl[2], 0.85)
        else:
            set_flow(flow, [], 0.1, "#FFFFFF", 0.0)
            blade_band(mats["blade"], [], 0.1, "#FFFFFF", 0.0)

    paths = []
    for i, stage in enumerate(stages):
        apply(stage)
        paths += c.render_views(OUT, f"stage{i}", target, distance, [("front", 0, 4)], lens=50)
    labelled_strip(paths, [st[0] for st in stages], os.path.join(OUT, "great_sword_charge.png"),
                   "大劍蓄力三段：亮金 → 更亮的金 → 白光，三段時刃紋上有光流過")
    top = stages[3]
    paths = []
    for i, shift in enumerate((0.0, 0.17, 0.34)):
        apply(top, [b + shift for b in top[4][0]])
        paths += c.render_views(OUT, f"flow{i}", (0.06, 0, 1.0), 1.9, [("front", 0, 4)], lens=50)
    labelled_strip(paths, ["流光 1", "流光 2", "流光 3"], os.path.join(OUT, "great_sword_flow.png"),
                   "大劍三段（白光）：刃紋上的光從刀根往刀尖流")


# ------------------------------------------------------------------ dual blades demon mode

def side_blade(blades, mat, side, name):
    """A copy of the dual blade's light blade pivoting at the guard, for the demon-mode
    three-bladed (kunai) form."""
    obj = blades.build_blade(mat)
    obj.name = name
    gz = blades.GUARD_Z
    for v in obj.data.vertices:
        v.co.z -= gz
    obj.location = (0, 0, gz)
    obj["side"] = side
    return obj


def pose_side(obj, length, angle_deg, spread):
    s = obj["side"]
    obj.scale = (0.72, 0.8, length)
    obj.rotation_euler = (0, math.radians(s * angle_deg), 0)
    obj.location = (s * spread, 0, obj.location.z)


def dual_blades_demon():
    import blades
    c.reset_scene()
    mats = m.materials()
    blades.build_sword("DualBlade", mats["ivory"], mats["light"], mats["blade"], mats["core"], seed=3)
    ghost = m.veil_material("Blade_Ghost", 0.18, 1.0)      # stands in for a Dissolve fade-in
    mats["ghost"] = ghost
    sides = [side_blade(blades, mats["blade"], s, f"Side_Blade_{s}") for s in (-1, 1)]
    m.glow_mode(mats)
    target, distance = (0, 0, 0.44), 1.75
    stage_lights(target, distance)
    states = [
        # label, visible, material, length, angle, spread, bright
        ("一般", False, "blade", 0.0, 0, 0.0, False),
        ("分裂中（淡入＋滑出）", True, "ghost", 0.45, 9, 0.004, False),
        ("鬼人化（三刃苦無）", True, "blade", 0.74, 22, 0.01, False),
        ("藍鬼人（亮金）", True, "blade", 0.74, 22, 0.01, True),
    ]
    paths = []
    for i, (label, visible, mat_key, length, angle, spread, bright) in enumerate(states):
        for obj in sides:
            obj.hide_render = not visible
            obj.data.materials[0] = mats[mat_key]
            if visible:
                pose_side(obj, length, angle, spread)
        if bright:
            brighten(mats)
        paths += c.render_views(OUT, f"state{i}", target, distance, [("front", 0, 4)], lens=50)
    labelled_strip(paths, [s[0] for s in states], os.path.join(OUT, "dual_blades_demon.png"),
                   "雙劍：一片光刃分裂成三刃苦無")


# Side blades of the in-game build (add_demon_blades.py): (forward offset of the branch point
# along the main blade, length scale of the side blade). The first is the first in-game version.
SPLIT_OPTIONS = (("目前（遊戲裡這版）", 0.0, 0.74), ("A：往前 4 公分、短一點", 0.04, 0.66),
                 ("B：往前 7 公分、再短一點", 0.07, 0.62))


def dual_blades_split_point():
    """User feedback on the first in-game demon mode: the side blades branch too close to
    the grip and look crowded; move the branch point a little toward the tip and make the
    side blades slightly shorter than now."""
    import blades
    c.reset_scene()
    mats = m.materials()
    blades.build_sword("DualBlade", mats["ivory"], mats["light"], mats["blade"], mats["core"], seed=3)
    sides = [side_blade(blades, mats["blade"], s, f"Side_Blade_{s}") for s in (-1, 1)]
    m.glow_mode(mats)
    target, distance = (0, 0, 0.44), 1.75
    stage_lights(target, distance)
    paths = []
    for i, (label, forward, length) in enumerate(SPLIT_OPTIONS):
        for obj in sides:
            pose_side(obj, length, 22, 0.01)
            obj.location.z = blades.GUARD_Z + forward
        paths += c.render_views(OUT, f"split{i}", target, distance, [("front", 0, 4)], lens=50)
    labelled_strip(paths, [o[0] for o in SPLIT_OPTIONS], os.path.join(OUT, "dual_blades_split_point.png"),
                   "雙劍鬼人化：側刃分岔點往刀尖移、側刃短一點")


# ------------------------------------------------------------------ hammer charge

def hammer_charge():
    """Each charge level adds a ring beyond each striking face, smaller each time, so the
    charge stacks outward from both faces; the caged sun grows brighter."""
    import arsenal
    c.reset_scene()
    mats = capture_build(arsenal.hammer)
    m.glow_mode(mats)
    sun = bpy.data.materials["Sun"]
    head_z = 1.04
    rings = {1: [], 2: [], 3: []}
    # (level, x, radius, minor): the first frames the face halo, then they shrink outward.
    for level, x, r, minor in ((1, 0.25, 0.15, 0.0042), (2, 0.3, 0.12, 0.0036), (3, 0.35, 0.085, 0.003)):
        for s in (-1, 1):
            rings[level] += m.halo(f"Charge_Ring_{level}_{s}", (s * x, 0, head_z), r, minor, (1, 0, 0),
                                   mats["light"], tilt_deg=5 if level % 2 else -5, tilt_axis=(0, 0, 1))
    target, distance = (0, 0, 0.98), 1.9
    stage_lights(target, distance, res=(700, 900))
    levels = [("一般", 4.0), ("蓄力 1", 5.0), ("蓄力 2", 6.2), ("蓄力 3（滿）", 7.5)]
    paths = []
    for i, (label, s_sun) in enumerate(levels):
        for level, objs in rings.items():
            show(objs, level <= i)
        set_glow(sun, c.PALETTE["glow"] if i < 3 else "#FFB840", s_sun)
        if i == 3:
            set_glow(mats["light"], *BRIGHT_LIGHT)
        paths += c.render_views(OUT, f"level{i}", target, distance, [("three_quarter", 25, 10)], lens=50)
    labelled_strip(paths, [lv[0] for lv in levels], os.path.join(OUT, "hammer_charge.png"),
                   "大槌蓄力：每一段兩端打擊面外各多一圈能量環，籠中的太陽越來越亮")


# ------------------------------------------------------------------ lance charge

def build_lance_charge():
    """The lance plus its charge parts: a cone of large rings from the vamplate toward the
    point, a faint cone of light inside them, and a longer flare around the point."""
    import arsenal
    c.reset_scene()
    mats = capture_build(arsenal.lance)
    m.glow_mode(mats)
    show([bpy.data.objects["EnergyShield"]], False)
    z0, z1, r0, r1, n = 0.56, 1.64, 0.125, 0.032, 8          # cone of rings, root -> point
    rings = []
    for k in range(n):
        t = k / (n - 1)
        rings.append(m.halo(f"Charge_Ring_{k}", (0, 0, z0 + (z1 - z0) * t), r0 + (r1 - r0) * t,
                            0.0052 - 0.0022 * t, (0, 0, 1), mats["light"], tilt_deg=-3 if k % 2 == 0 else 3))
    cone_mat = m.veil_material("Charge_Cone", 0.1, 1.2)
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=r0 - 0.004, radius2=r1 - 0.004, depth=z1 - z0,
                                    end_fill_type="NOTHING", location=(0, 0, (z0 + z1) / 2))
    cone = bpy.context.active_object
    cone.name = "Charge_Cone"
    cone.data.materials.append(cone_mat)
    bpy.ops.object.shade_smooth()
    flare_mat = m.veil_material("Point_Flare", 0.35, 2.0)
    tip = 1.98
    flare = []
    for name, normal in (("Point_Flare_A", (0, 1, 0)), ("Point_Flare_B", (1, 0, 0))):
        flare += m.path_blade(name, [V(0, 0, tip - 0.38), V(0, 0, tip + 0.22)], normal,
                              lambda t: 0.085 * (1 - t) ** 0.9 * (0.75 + 0.25 * math.sin(math.pi * min(t / 0.3, 1))),
                              lambda t: 0.02 * (1 - t), flare_mat)
    return mats, rings, cone, cone_mat, flare


def set_cone(mat, opacity, fade_to_tip=False):
    """Cone opacity; with fade_to_tip it is strongest at the root and gone at the point."""
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    mix = next(nd for nd in nodes if nd.type == "MIX_SHADER")
    for link in list(mix.inputs["Fac"].links):
        links.remove(link)
    mix.inputs["Fac"].default_value = opacity
    if fade_to_tip:
        coords = nodes.new("ShaderNodeTexCoord")
        split = nodes.new("ShaderNodeSeparateXYZ")
        fade = nodes.new("ShaderNodeMapRange")       # generated z: 0 at the root, 1 at the point
        fade.inputs["To Min"].default_value = opacity
        fade.inputs["To Max"].default_value = 0.0
        links.new(coords.outputs["Generated"], split.inputs["Vector"])
        links.new(split.outputs["Z"], fade.inputs["Value"])
        links.new(fade.outputs["Result"], mix.inputs["Fac"])


LANCE_VIEW = ((0, 0, 1.3), 2.75, [("three_quarter", 20, 6)])


def lance_charge():
    """Charging grows the cone of rings a few at a time, brighter each level; at full charge
    the faint cone and the point flare appear: the whole lance reads as a lance of light."""
    mats, rings, cone, cone_mat, flare = build_lance_charge()
    set_cone(cone_mat, 0.08, fade_to_tip=True)       # chosen by the user (lance_full_variants, no. 3)
    target, distance, views = LANCE_VIEW
    stage_lights(target, distance)
    # label, rings shown, light strength ("bright" = bright gold), cone and flare
    levels = [("一般", 0, None, False), ("蓄力 1", 3, 4.0, False), ("蓄力 2", 6, 6.0, False),
              ("蓄力 3（滿）", 8, "bright", True)]
    paths = []
    for i, (label, count, strength, full) in enumerate(levels):
        for k, objs in enumerate(rings):
            show(objs, k < count)
        show([cone] + flare, full)
        if strength == "bright":
            brighten(mats)
        elif strength:
            set_glow(mats["light"], c.PALETTE["glow"], strength)
            set_blade(mats["blade"], c.PALETTE["blade_core"], c.PALETTE["blade_edge"], 2.2 + 0.5 * i)
        paths += c.render_views(OUT, f"level{i}", target, distance, views, lens=50)
    labelled_strip(paths, [lv[0] for lv in levels], os.path.join(OUT, "lance_charge.png"),
                   "長槍蓄力：光環從槍根往槍尖一段段長出，滿蓄力時圍成一支光的騎槍")


def lance_full_variants():
    """Full charge only, with the cone of light at different strengths, to pick one."""
    mats, rings, cone, cone_mat, flare = build_lance_charge()
    brighten(mats)
    target, distance, views = LANCE_VIEW
    stage_lights(target, distance)
    variants = [("目前（光膜 10%）", 0.1, False, True), ("光膜調淡（4%）", 0.04, False, True),
                ("調淡＋往槍尖淡出", 0.08, True, True), ("拿掉光膜", 0.0, False, False)]
    paths = []
    for i, (label, opacity, fade, visible) in enumerate(variants):
        set_cone(cone_mat, opacity, fade)
        show([cone], visible)
        paths += c.render_views(OUT, f"variant{i}", target, distance, views, lens=50)
    labelled_strip(paths, [v[0] for v in variants], os.path.join(OUT, "lance_full_variants.png"),
                   "長槍滿蓄力：光膜的濃淡比較")


# ------------------------------------------------------------------ gunlance reload

def gunlance_reload():
    """The ivory spring around the ribs compresses toward the root while the energy core at
    the root charges, then springs back a little past its rest length before settling."""
    import arsenal
    c.reset_scene()
    mats = capture_build(arsenal.gunlance)
    m.glow_mode(mats)
    show([bpy.data.objects["EnergyShield"]], False)
    core_mat = mats["light"].copy()
    core_mat.name = "Energy_Core_Charge"
    cores = [o for o in bpy.data.objects if o.name.startswith("Energy_Core")]
    for o in cores:
        o.data.materials[0] = core_mat
    z0 = arsenal.GUNLANCE_BASE + 0.1
    rest = arsenal.SPRING_TOP - z0
    target, distance = (0, 0, 1.0), 1.9
    stage_lights(target, distance)
    states = [
        # label, spring length (x rest), core colour, core strength, core scale
        ("一般", 1.0, c.PALETTE["glow"], 5.0, 1.0),
        ("裝填：彈簧壓縮、核心充能", 0.45, "#FFB840", 9.0, 1.35),
        ("回彈（略伸過頭再復位）", 1.12, c.PALETTE["glow"], 6.0, 1.1),
    ]
    paths = []
    for i, (label, f, core_hex, s_core, scale) in enumerate(states):
        for o in [o for o in bpy.data.objects if o.name.startswith("Binding")]:
            bpy.data.objects.remove(o, do_unlink=True)
        arsenal.gunlance_spring(mats, top=z0 + rest * f)
        set_glow(core_mat, core_hex, s_core)
        for o in cores:
            o.scale = (scale, scale, scale)
        paths += c.render_views(OUT, f"state{i}", target, distance, [("three_quarter", 25, 8)], lens=50)
    labelled_strip(paths, [st[0] for st in states], os.path.join(OUT, "gunlance_reload.png"),
                   "銃槍填彈：彈簧往槍根壓縮一次再彈回")


# ------------------------------------------------------------------ long sword spirit levels

def band_sum(nodes, links, centers, width, label):
    """Sum of soft bands along the object's length (generated z: 0 at one end, 1 at the
    other), centred on `centers`; returns the output socket (0 outside the bands)."""
    def node(kind, op=None, value=None):
        nd = nodes.new(kind)
        nd.label = label
        if op:
            nd.operation = op
        if value is not None:
            nd.inputs[1].default_value = value
        return nd

    coords = node("ShaderNodeTexCoord")
    split = node("ShaderNodeSeparateXYZ")
    links.new(coords.outputs["Generated"], split.inputs["Vector"])
    total = None
    for ctr in centers:
        d = node("ShaderNodeMath", "SUBTRACT", ctr)
        links.new(split.outputs["Z"], d.inputs[0])
        q = node("ShaderNodeMath", "DIVIDE", width)
        links.new(d.outputs[0], q.inputs[0])
        sq = node("ShaderNodeMath", "POWER", 2.0)
        links.new(q.outputs[0], sq.inputs[0])
        bump = node("ShaderNodeMath", "SUBTRACT")
        bump.inputs[0].default_value = 1.0
        links.new(sq.outputs[0], bump.inputs[1])
        pos = node("ShaderNodeMath", "MAXIMUM", 0.0)
        links.new(bump.outputs[0], pos.inputs[0])
        if total is None:
            total = pos
        else:
            add = node("ShaderNodeMath", "ADD")
            links.new(total.outputs[0], add.inputs[0])
            links.new(pos.outputs[0], add.inputs[1])
            total = add
    clamp = node("ShaderNodeMath", "MINIMUM", 1.0)
    links.new(total.outputs[0], clamp.inputs[0])
    return clamp.outputs[0]


def flow_material(name):
    """See-through except inside the bands: the travelling light on the hamon. In game this
    is the emissive band that moves along the mesh (Use_MoveEmit / MoveEmit)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    for nd in list(nodes):
        nodes.remove(nd)
    out = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    emission = nodes.new("ShaderNodeEmission")
    mat.node_tree.links.new(transparent.outputs["BSDF"], mix.inputs[1])
    mat.node_tree.links.new(emission.outputs["Emission"], mix.inputs[2])
    mat.node_tree.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def set_flow(mat, centers, width, hex_color, strength):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for nd in [nd for nd in nodes if nd.label == "band"]:
        nodes.remove(nd)
    mix = next(nd for nd in nodes if nd.type == "MIX_SHADER")
    emission = next(nd for nd in nodes if nd.type == "EMISSION")
    emission.inputs["Color"].default_value = c.hex_to_linear(hex_color)
    emission.inputs["Strength"].default_value = strength
    for link in list(mix.inputs["Fac"].links):
        links.remove(link)
    if centers:
        links.new(band_sum(nodes, links, centers, width, "band"), mix.inputs["Fac"])
    else:
        mix.inputs["Fac"].default_value = 0.0


def flow_ribbon(material):
    """A slightly wider tube over the hamon line on both faces, carrying the moving light."""
    import long_sword as ls
    objs = []
    for face in (-1, 1):
        pts, radii = [], []
        for i in range(120):
            s = 0.02 + 0.9 * i / 119
            ctr = ls.blade_center(s)
            w, t = ls.blade_profile(s)
            inset = 0.2 * w + 0.05 * w * math.sin(s * 40)
            pts.append(Vector((ctr.x + w - inset, face * t * 0.32, ctr.z)))
            radii.append(1.0 - 0.5 * s)
        objs.append(c.curve_tube(f"Hamon_Flow_{face}", pts, radii, material, bevel=0.0034, resolution=2))
    return objs


def build_long_sword():
    import blades
    import long_sword as ls
    import random
    c.reset_scene()
    rng = random.Random(8)
    ivory = c.make_material("Ivory", c.PALETTE["ivory"], roughness=0.32, coat=0.3,
                            emission=c.PALETTE["glow"], strength=0.05, subsurface=0.15)
    glow = c.make_material("Light", c.PALETTE["glow"], roughness=0.1, coat=0.5,
                           emission=c.PALETTE["glow"], strength=2.5)
    blade = blades.blade_material("Blade_Light", 2.2)
    hamon = c.make_material("Hamon", c.PALETTE["blade_core"], roughness=0.1,
                            emission=c.PALETTE["blade_core"], strength=3.0)
    parts = [ls.build_blade(blade)] + ls.hamon_line(hamon) + ls.handle(ivory, glow, rng)
    parts += ls.tsuba_halo(glow, ivory, rng) + ls.blade_wrap(ivory, rng)
    flow = flow_material("Hamon_Flow")
    parts += flow_ribbon(flow)
    root = c.link(bpy.data.objects.new("LongSword", None))
    for part in parts:
        part.parent = root
    root.rotation_euler = (0, math.radians(-8), 0)
    return {"blade": blade, "hamon": hamon, "light": glow, "flow": flow}


# Spirit levels: the game's none / white / yellow / red, here pale gold / gold / bright gold / white.
# From the yellow level a band of light travels along the hamon, in the next level's colour.
SPIRIT_LEVELS = [
    # label, blade (core, edge, strength), light (colour, strength), flow (centres, width, colour, strength)
    ("一般（淡金）", ("#FFDDA0", "#EDB868", 1.4), ("#F2C47E", 1.8), None),
    ("白刃 → 金", (c.PALETTE["blade_core"], c.PALETTE["blade_edge"], 2.2), (c.PALETTE["glow"], 2.5), None),
    ("黃刃 → 亮金", BRIGHT_BLADE, BRIGHT_LIGHT, ([0.5], 0.14, "#FFF4DC", 30.0)),
    ("紅刃 → 白光", ("#FFFBF0", "#FFE7B0", 5.0), ("#FFF2D6", 5.5), ([0.25, 0.7], 0.11, "#FF9A10", 45.0)),
]


def apply_spirit(mats, level, centers=None):
    label, blade, light, flow = level
    set_blade(mats["blade"], *blade)
    set_glow(mats["light"], *light)
    set_glow(mats["hamon"], blade[0], 3.0 * blade[2] / 2.2)
    if flow:
        set_flow(mats["flow"], centers if centers is not None else flow[0], flow[1], flow[2], flow[3])
    else:
        set_flow(mats["flow"], [], 0.1, "#FFFFFF", 0.0)


def long_sword_spirit():
    """Spirit levels light the blade up in four steps; from the third, light flows along the
    hamon line (the game's moving emissive band), faster and in two bands at the top."""
    mats = build_long_sword()
    target, distance = (0.0, 0, 0.5), 1.9
    stage_lights(target, distance, res=(560, 1000))
    paths = []
    for i, level in enumerate(SPIRIT_LEVELS):
        apply_spirit(mats, level)
        paths += c.render_views(OUT, f"level{i}", target, distance, [("flat", 0, 4)], lens=50)
    labelled_strip(paths, [lv[0] for lv in SPIRIT_LEVELS], os.path.join(OUT, "long_sword_spirit.png"),
                   "太刀練氣：淡金 → 金 → 亮金 → 白光，高段時刃紋上有光流過")
    # The flowing light, three moments of the top level.
    paths = []
    top = SPIRIT_LEVELS[3]
    for i, shift in enumerate((0.0, 0.17, 0.34)):
        apply_spirit(mats, top, [b + shift for b in top[3][0]])
        paths += c.render_views(OUT, f"flow{i}", target, distance, [("flat", 0, 4)], lens=50)
    labelled_strip(paths, ["流光 1", "流光 2", "流光 3"], os.path.join(OUT, "long_sword_flow.png"),
                   "太刀紅刃（白光）：刃紋上的光從刀根往刀尖流")


# ------------------------------------------------------------------ insect glaive extracts

LAYOUTS = ("B",)      # the user went with B (motes around the blade); A kept for reference


def insect_glaive_extracts():
    """Red, white and orange extracts as Elden Ring's scarlet rot, frost and frenzied flame
    (user's idea), in two layouts. A: the top blade becomes three blades (rot in the middle,
    flame on the left, frost on the right) and each takes on its status when that extract is
    lit. B: the single blade with three motes floating in a triangle around it (rot at the
    apex, flame lower left, frost lower right); a lit mote shows its status, and with all
    three a line of light joins them and the blade turns bright gold."""
    import arsenal
    import status_fx as fx
    c.reset_scene()
    mats = capture_build(arsenal.insect_glaive)
    m.glow_mode(mats)
    top = 1.45
    fx_mats = {kind: fx.effect_material(kind) for kind in fx.STATUS}
    gold = (c.PALETTE["blade_core"], c.PALETTE["blade_edge"], 2.2)

    def blade_copy(name):
        mat = mats["blade"].copy()
        mat.name = name
        return mat

    center = bpy.data.objects["Blade_Top"]
    center_mat = blade_copy("Blade_Center")
    center.data.materials[0] = center_mat

    def leaf(wmax):
        return lambda t: wmax * (0.8 + 0.3 * math.sin(math.pi * min(t / 0.45, 1) * 0.5)) * (1 - t ** 2.6)

    # ---- layout A: three blades
    a_objs, a_fx, a_mats = [], {}, {"rot": center_mat}
    root = V(0, 0, top + 0.02)
    dirs = {"flame": V(-math.sin(math.radians(30)), 0, math.cos(math.radians(30))),
            "frost": V(math.sin(math.radians(30)), 0, math.cos(math.radians(30)))}
    for kind, d in dirs.items():
        mat = blade_copy(f"Blade_{kind}")
        a_mats[kind] = mat
        a_objs += m.path_blade(f"Side_Blade_{kind}", [root, root + d * 0.3], (0, 1, 0), leaf(0.052),
                               lambda t: 0.01 * (1 - t ** 2), mat)
    a_fx["rot"] = fx.rot("A_Rot", [(V(-0.014, -0.014, top + 0.08), (0, -1, 0.15)),
                                   (V(0.016, -0.014, top + 0.16), (0, -1, 0.1)),
                                   (V(-0.008, -0.013, top + 0.25), (0, -1, 0.1))],
                         [V(0.036, -0.004, top + 0.16), V(-0.036, -0.004, top + 0.22), V(0.03, -0.004, top + 0.3),
                          V(-0.026, -0.004, top + 0.33)],
                         fx_mats["rot"], radius=0.02)
    d = dirs["flame"]
    out = V(-d.z, 0, d.x)                     # the left blade's outer side
    a_fx["flame"] = fx.flame("A_Flame", [root + d * (0.3 * u) + out * 0.022 for u in (0.08, 0.3, 0.52, 0.72)],
                             (0.15, 0.19, 0.16, 0.11), fx_mats["flame"], width=0.03, lean=(-0.45, 0, 1))
    d = dirs["frost"]
    out = V(d.z, 0, -d.x)                     # the right blade's outer side
    roots = [root + d * (0.3 * u) + out * 0.016 for u in (0.2, 0.38, 0.55, 0.72)]
    a_fx["frost"] = fx.frost("A_Frost", roots, [out + d * k for k in (-0.2, 0.3, 0.6, 1.0)],
                             (0.07, 0.085, 0.065, 0.05), fx_mats["frost"], width=0.012)
    a_fx["frost"] += fx.frost("A_Frost_Inner", [root + d * 0.12 - out * 0.012, root + d * 0.26 - out * 0.01],
                              [-out + d * 0.8, -out + d * 1.3], (0.025, 0.02), fx_mats["frost"], width=0.006)

    # ---- layout B (the user's): balls that appear only when their extract is lit and circle
    # the blade; no halos. Rot: a mould cluster shedding rot butterflies; frenzied flame: a
    # ball of curling fire; frost: a ball of ice (placeholder until the user's reference).
    b_objs, b_fx, b_mats = [], {}, {}
    orbit_c, orbit_r, orbit_z = V(0, 0, 0), 0.085, top + 0.2
    angles = {"rot": -100, "flame": 140, "frost": 20}           # degrees around the blade
    pos = {k: V(orbit_r * math.cos(math.radians(a)), orbit_r * math.sin(math.radians(a)), orbit_z)
           for k, a in angles.items()}
    motes = pos
    b_fx["rot"] = fx.rot_mote("B_Rot2", pos["rot"], 0.017)
    import particle_fx as pfx

    def trailing(kind):                     # behind the ball as it circles counter-clockwise
        a = math.radians(angles[kind])
        return (math.sin(a), -math.cos(a), -0.3)

    b_fx["flame"] = pfx.fire_strands("B_Frenzy", pos["flame"], 0.02)
    b_fx["frost"] = fx.frost_ball("B_Frost2", pos["frost"], 0.016, drift=trailing("frost"))
    b_triangle = []
    rot_mote_drop = []

    target, distance = (0, 0, top + 0.24), 1.05
    stage_lights(target, distance, res=(480, 800))
    states = [("一般", ()), ("紅：猩紅腐敗", ("rot",)), ("白：冰凍", ("frost",)), ("橘：癲火", ("flame",)),
              ("三燈齊", ("rot", "frost", "flame"))]

    def blade_state(mat, kind, lit):
        core, edge, strength = fx.STATUS[kind][:3] if lit else gold
        set_blade(mat, core, edge, strength)

    for layout in LAYOUTS:
        show(a_objs + sum(a_fx.values(), []), layout == "A")
        show(b_objs + sum(b_fx.values(), []) + b_triangle, layout == "B")
        paths = []
        for i, (label, lit) in enumerate(states):
            if layout == "A":
                for kind in fx.STATUS:
                    blade_state(a_mats[kind], kind, kind in lit)
                    show(a_fx[kind], kind in lit)
            else:
                full = len(lit) == 3
                set_blade(center_mat, *(BRIGHT_BLADE if full else gold))
                for kind in fx.STATUS:
                    show(b_fx[kind], kind in lit)
            paths += c.render_views(OUT, f"{layout}_state{i}", target, distance, [("front", 12, 4)], lens=50)
        if layout == "B":
            # Close-ups of each lit mote (the last state has all three lit).
            # Close-ups of each ball alone, seen from outside its orbit (the blade off to one side).
            close = []
            for kind in ("rot", "flame", "frost"):
                for other in fx.STATUS:
                    show(b_fx[other], other == kind)
                close += c.render_views(OUT, f"B_close_{kind}", motes[kind] + V(0, 0, 0.012),
                                        0.38 if kind == "frost" else 0.3,
                                        [("out", angles[kind] + 90 + 28, 8)], lens=50)
            for other in fx.STATUS:
                show(b_fx[other], True)
            # From above: the three balls around the blade (they circle it in game).
            close += c.render_views(OUT, "B_top", V(0, 0, orbit_z), 0.55, [("top", 0, 80)], lens=50)
            labelled_strip(close, ["猩紅腐敗", "癲火", "冰凍", "俯視：三顆球繞著光刃轉"],
                           os.path.join(OUT, "insect_glaive_extracts_B_close.png"), "特寫：三顆球")
        title = ("方案 A：光刃變三刃（中猩紅腐敗、左癲火、右冰凍）" if layout == "A"
                 else "操蟲棍精華：點燈後出現的球繞著光刃轉（腐敗、癲火、冰凍）")
        labelled_strip(paths, [st[0] for st in states], os.path.join(OUT, f"insect_glaive_extracts_{layout}.png"),
                       title)


# ------------------------------------------------------------------ switch axe

def switch_axe_states():
    """Axe mode: the floating phials show the switch gauge (dark when empty, lit one by one;
    from three the axe can morph); power axe mode brightens the three axe blades. Sword
    mode (design A, chosen by the user): amped state turns the sword and its fins bright
    gold with light flowing along the blade."""
    import arsenal
    import random
    c.reset_scene()
    mats = m.materials()
    common = arsenal.switch_axe_common(mats, random.Random(81))
    axe_mats = dict(mats, blade=mats["blade"].copy(), light=mats["light"].copy())
    axe = arsenal.switch_axe_axe_head(axe_mats)
    sword_mats = dict(mats, blade=mats["blade"].copy(), light=mats["light"].copy(), core=mats["core"].copy())
    sword = arsenal.switch_axe_sword_head(sword_mats, "a")
    m.glow_mode(mats)
    for mm in (axe_mats, sword_mats):
        set_blade(mm["blade"], c.PALETTE["blade_core"], c.PALETTE["blade_edge"], 2.2)
        set_glow(mm["light"], c.PALETTE["glow"], 2.5)
    set_glow(sword_mats["core"], c.PALETTE["glow"], 3.0)
    phials = sorted([o for o in bpy.data.objects if o.name.startswith("Phial_") and "Halo" not in o.name],
                    key=lambda o: o.location.z)
    phial_mats, halo_mats = [], []
    for k, o in enumerate(phials):
        mat = o.data.materials[0].copy()
        mat.name = f"Phial_Lit_{k}"
        o.data.materials[0] = mat
        phial_mats.append(mat)
        halo = bpy.data.objects[o.name.replace("Phial_", "Phial_Halo_")]
        hmat = halo.data.materials[0].copy()
        halo.data.materials[0] = hmat
        halo_mats.append(hmat)
    target, distance = (0.05, 0, 0.95), 2.6
    stage_lights(target, distance, res=(500, 1000))
    states = [
        # label, mode, phials lit, power axe, amped
        ("斧：量表空", "axe", 0, False, False),
        ("斧：量表 3 格（可變形）", "axe", 3, False, False),
        ("斧：量表滿", "axe", 5, False, False),
        ("強化斧模式", "axe", 5, True, False),
        ("劍模式", "sword", 3, False, False),
        ("劍模式：覺醒", "sword", 3, False, True),
    ]
    paths = []
    for i, (label, mode, lit, power, amped) in enumerate(states):
        show(axe, mode == "axe")
        show(sword, mode == "sword")
        for k, (mat, hmat) in enumerate(zip(phial_mats, halo_mats)):
            set_glow(mat, c.PALETTE["glow"] if k < lit else "#4A3E2A", 3.0 if k < lit else 0.05)
            set_glow(hmat, c.PALETTE["glow"] if k < lit else "#8A7450", 2.5 if k < lit else 0.15)
        if power:
            set_blade(axe_mats["blade"], *BRIGHT_BLADE)
            set_glow(axe_mats["light"], *BRIGHT_LIGHT)
        if amped:
            set_blade(sword_mats["blade"], *BRIGHT_BLADE)
            set_glow(sword_mats["light"], *BRIGHT_LIGHT)
            set_glow(sword_mats["core"], *BRIGHT_CORE)
        paths += c.render_views(OUT, f"state{i}", target, distance, [("front", 15, 5)], lens=50)
    labelled_strip(paths, [st[0] for st in states], os.path.join(OUT, "switch_axe_states.png"),
                   "斬擊斧：光點＝變形量表，強化斧讓三片光刃變亮，劍模式覺醒變亮金")


# ------------------------------------------------------------------ helpers for the rest

def objs_named(prefix, exclude=()):
    return sorted([o for o in bpy.data.objects if o.name.startswith(prefix)
                   and not any(x in o.name for x in exclude)], key=lambda o: o.name)


def own_material(objs, name):
    """Give these objects one shared copy of their (first) material so it can change alone."""
    objs = [o for o in objs if getattr(o.data, "materials", None)]
    mat = objs[0].data.materials[0].copy()
    mat.name = name
    for o in objs:
        o.data.materials[0] = mat
    return mat


def descendants(root):
    out = []
    for ch in root.children:
        out.append(ch)
        out += descendants(ch)
    return out


DIM = ("#4A3E2A", 0.05)       # an unlit phial / note


# ------------------------------------------------------------------ charge blade

def charge_blade_states():
    """Sword hits fill the sword's phial ring (gold, then bright gold when full); loading
    lights the shield's phials; shield charge turns the shield's halo and sigil bright gold;
    sword boost brightens the sword; axe boost the axe edge."""
    import arsenal
    c.reset_scene()
    mats = capture_build(arsenal.charge_blade)
    m.glow_mode(mats)
    show(objs_named("Backdrop"), False)
    sword_ph = own_material(objs_named("Sword_Phial_", exclude=("Ring",)), "Sword_Phials")
    shield_ph = [own_material([o], f"Shield_Phial_{k}") for k, o in enumerate(objs_named("Shield_Phial_"))]
    shield_parts = [o for o in descendants(bpy.data.objects["EnergyShield"])
                    if getattr(o.data, "materials", None) and o.data.materials[0] == mats["light"]]
    shield_light = own_material(shield_parts, "Shield_Light")
    sword_blade = own_material([o for o in descendants(bpy.data.objects["CB_Sword"])
                                if getattr(o.data, "materials", None) and o.data.materials[0] == mats["blade"]],
                               "CB_Sword_Blade")
    axe_edge = own_material(objs_named("Axe_Edge", exclude=("Temper", "Afterimage")), "CB_Axe_Edge")
    membrane = mats["shield_membrane"].node_tree.nodes["Membrane_Emission"]
    base_membrane = membrane.inputs["Strength"].default_value
    gold_blade = (c.PALETTE["blade_core"], c.PALETTE["blade_edge"], 2.2)
    target, distance = (-0.05, 0, 0.5), 2.3
    stage_lights(target, distance, res=(700, 630))
    states = [
        # label, sword phials, shield phials lit, shield, sword boost, axe boost
        ("一般", "dim", 0, False, False, False),
        ("劍攻擊累積（劍上光點亮）", "gold", 0, False, False, False),
        ("累積滿（亮金）", "bright", 0, False, False, False),
        ("裝填瓶子（盾上光點亮）", "dim", 5, False, False, False),
        ("盾強化（紅盾）", "dim", 5, True, False, False),
        ("劍強化", "dim", 3, True, True, False),
        ("斧強化（斧刃變亮）", "dim", 2, True, False, True),
    ]
    paths = []
    for i, (label, sp, lit, shield, sword_boost, axe_boost) in enumerate(states):
        set_glow(sword_ph, *{"dim": DIM, "gold": (c.PALETTE["glow"], 3.0), "bright": BRIGHT_LIGHT}[sp])
        for k, mat in enumerate(shield_ph):
            set_glow(mat, *((c.PALETTE["glow"], 3.0) if k < lit else DIM))
        set_glow(shield_light, *(BRIGHT_LIGHT if shield else (c.PALETTE["glow"], 2.5)))
        membrane.inputs["Strength"].default_value = base_membrane * (2.5 if shield else 1.0)
        set_blade(sword_blade, *(BRIGHT_BLADE if sword_boost else gold_blade))
        set_blade(axe_edge, *(BRIGHT_BLADE if axe_boost else gold_blade))
        paths += c.render_views(OUT, f"state{i}", target, distance, [("front", 0, 4)], lens=50)
    labelled_strip(paths, [st[0] for st in states], os.path.join(OUT, "charge_blade_states.png"),
                   "充能斧：光點＝瓶子，盾、劍、斧強化各自變亮金", cols=4)


# ------------------------------------------------------------------ bow

def bow_charge():
    """Each charge level lights one more ring ahead of the arrow in bright gold; at the
    third the whole rail and the arrowhead blaze."""
    import arsenal
    c.reset_scene()
    mats = capture_build(arsenal.bow)
    m.glow_mode(mats)
    rail = [own_material([o], f"Rail_{k}") for k, o in enumerate(objs_named("Arrow_Rail_"))]
    head = own_material(objs_named("Arrow_Head"), "Arrow_Head_Mat")
    shaft = own_material(objs_named("Arrow_Shaft"), "Arrow_Shaft_Mat")
    target, distance = (-0.3, 0, 0.0), 2.4
    stage_lights(target, distance, res=(900, 640))
    levels = [("拉弓（未蓄力）", 0), ("蓄力 1", 1), ("蓄力 2", 2), ("蓄力 3", 4)]
    paths = []
    for i, (label, n) in enumerate(levels):
        for k, mat in enumerate(rail):
            set_glow(mat, *(BRIGHT_LIGHT if k < n else ("#B8862E", 0.5)))     # unlit rings stay dim
        set_blade(head, *(BRIGHT_BLADE if n == 4 else (c.PALETTE["blade_core"], c.PALETTE["blade_edge"], 2.2)))
        set_glow(shaft, *(BRIGHT_CORE if n == 4 else (c.PALETTE["blade_core"], 3.0)))
        paths += c.render_views(OUT, f"level{i}", target, distance, [("front", 0, 4)], lens=50)
    labelled_strip(paths, [lv[0] for lv in levels], os.path.join(OUT, "bow_charge.png"),
                   "弓蓄力：箭前方的光環一段段亮起，三段時整條光環和箭頭全亮", cols=2)


# ------------------------------------------------------------------ bowguns

def bowgun_gauges():
    """The three floating phials are the gauge (heavy: ignition, light: rapid fire); while
    the special fire runs the barrel's rings blaze and the phials drain."""
    import bowgun as hb
    c.reset_scene()
    ivory, glow = hb.build()
    set_glow(glow, c.PALETTE["blade_core"], 2.5)
    phials = [own_material([o], f"HB_Phial_{k}") for k, o in enumerate(objs_named("Barrel_Phial_", ("Halo",)))]
    halos = [own_material([o], f"HB_Phial_Halo_{k}") for k, o in enumerate(objs_named("Barrel_Phial_Halo_"))]
    fire = own_material(objs_named("Muzzle_Halo") + objs_named("Conduit_Halo_"), "HB_Fire_Rings")
    target, distance = (0, 0.2, 0.02), 2.4
    stage_lights(target, distance, res=(800, 540))

    def gauge(n, mats, hmats):
        for k, (mat, hmat) in enumerate(zip(mats, hmats)):
            set_glow(mat, *((c.PALETTE["glow"], 3.0) if k < n else DIM))
            set_glow(hmat, *((c.PALETTE["glow"], 2.5) if k < n else ("#8A7450", 0.15)))

    states = [("點火量表 0", 0, False), ("1", 1, False), ("2", 2, False), ("滿（可點火）", 3, False),
              ("龍熱點火連射中（量表消耗）", 1, True)]
    paths = []
    for i, (label, n, firing) in enumerate(states):
        gauge(n, phials, halos)
        set_glow(fire, *(BRIGHT_LIGHT if firing else (c.PALETTE["blade_core"], 2.5)))
        paths += c.render_views(OUT, f"heavy{i}", target, distance, [("side", 90, 4)], lens=50)
    labelled_strip(paths, [st[0] for st in states], os.path.join(OUT, "heavy_bowgun_ignition.png"),
                   "重弩：三顆光點＝點火量表，點火連射時槍管光環全亮", cols=3)

    import light_bowgun as lb
    ivory, glow, beam = lb.build()
    set_glow(glow, c.PALETTE["glow"], 2.5)
    set_glow(beam, c.PALETTE["blade_core"], 3.0)
    phials = [own_material([o], f"LB_Phial_{k}") for k, o in enumerate(objs_named("Barrel_Phial_", ("Halo",)))]
    halos = [own_material([o], f"LB_Phial_Halo_{k}") for k, o in enumerate(objs_named("Barrel_Phial_Halo_"))]
    rails = [own_material([o], f"LB_Rail_{k}") for k, o in enumerate(objs_named("Rail_Halo_"))]
    target, distance = (0, 0.12, 0.01), 1.6
    stage_lights(target, distance, res=(800, 540))
    states = [("速射量表 0", 0, None), ("1", 1, None), ("2", 2, None), ("滿", 3, None),
              ("速射中：光環一圈圈往前閃", 2, 1)]
    paths = []
    for i, (label, n, flash) in enumerate(states):
        gauge(n, phials, halos)
        for k, mat in enumerate(rails):
            set_glow(mat, *(BRIGHT_LIGHT if flash is not None and k in (flash, flash + 2) else (c.PALETTE["glow"], 2.5)))
        paths += c.render_views(OUT, f"light{i}", target, distance, [("side", 90, 4)], lens=50)
    labelled_strip(paths, [st[0] for st in states], os.path.join(OUT, "light_bowgun_rapid.png"),
                   "輕弩：三顆光點＝速射量表，速射時光環隧道一圈圈往前閃", cols=3)


# ------------------------------------------------------------------ hunting horn

def hunting_horn_notes():
    """Each note lights one more string bright gold; with a full song the crown flares and,
    when played, the sound rings blaze and spread wider."""
    import arsenal
    c.reset_scene()
    mats = capture_build(arsenal.hunting_horn)
    m.glow_mode(mats)
    strings = [own_material([o], f"String_Mat_{k}") for k, o in enumerate(objs_named("String_"))]
    rings = objs_named("Sound_Ring_")
    ring_mat = own_material(rings, "Sound_Rings")
    crown = own_material(objs_named("Crown_Halo"), "Crown_Mat")
    base_scale = [tuple(o.scale) for o in rings]
    target, distance = (0, -0.06, 0.82), 1.3
    stage_lights(target, distance, res=(600, 760))
    order = [2, 1, 3, 0, 4]                       # middle string first, then outward
    states = [("一般", 0, False), ("音符 1", 1, False), ("音符 3", 3, False), ("音符滿", 5, False),
              ("演奏", 5, True)]
    paths = []
    for i, (label, n, play) in enumerate(states):
        for rank, k in enumerate(order):
            set_glow(strings[k], *(BRIGHT_CORE if rank < n else (c.PALETTE["blade_core"], 3.0)))
        set_glow(crown, *(BRIGHT_LIGHT if n == 5 else (c.PALETTE["glow"], 2.5)))
        set_glow(ring_mat, *(BRIGHT_LIGHT if play else (c.PALETTE["glow"], 2.5)))
        for o, sc in zip(rings, base_scale):
            f = 1.25 if play else 1.0
            o.scale = (sc[0] * f, sc[1] * f, sc[2] * f)
        paths += c.render_views(OUT, f"state{i}", target, distance, [("three_quarter", 30, 8)], lens=50)
    labelled_strip(paths, [st[0] for st in states], os.path.join(OUT, "hunting_horn_notes.png"),
                   "狩獵笛：每個音符點亮一條光弦，演奏時聲波環變亮擴大")


# ------------------------------------------------------------------ guard flash

def shield_guard():
    """Every energy shield (sword & shield, lance, gunlance, charge blade): blocking lights
    the membrane and the sigil; a perfect guard flashes bright gold with rings of light
    rippling out from the rim."""
    import arsenal
    c.reset_scene()
    mats = m.materials()
    root = arsenal.energy_shield(mats, (0, 0, 0.5), 1.0)
    m.glow_mode(mats)
    membrane = mats["shield_membrane"].node_tree.nodes["Membrane_Emission"]
    base = membrane.inputs["Strength"].default_value
    import sword_shield as ss
    R = ss.R
    ripple = []
    for k, (f, minor) in enumerate(((1.12, 0.004), (1.28, 0.0028), (1.46, 0.0018))):
        ripple += m.halo(f"Guard_Ripple_{k}", (0, -0.01, 0.5), R * f, minor, (0, 1, 0), mats["light"])
    for o in ripple:
        o.scale = (1.0, 1.0, 1.18)               # the shield is drawn taller
    target, distance = (0, 0, 0.5), 1.25
    stage_lights(target, distance, res=(600, 700))
    states = [("一般", 1.0, None, False), ("防禦（擋下攻擊）", 3.0, (c.PALETTE["glow"], 4.0), False),
              ("完美防禦（閃光＋光環擴散）", 5.0, BRIGHT_LIGHT, True)]
    paths = []
    for i, (label, f, light, rip) in enumerate(states):
        membrane.inputs["Strength"].default_value = base * f
        set_glow(mats["light"], *(light or (c.PALETTE["glow"], 2.5)))
        show(ripple, rip)
        paths += c.render_views(OUT, f"state{i}", target, distance, [("front", 0, 2)], lens=50)
    labelled_strip(paths, [st[0] for st in states], os.path.join(OUT, "shield_guard.png"),
                   "能量盾（片手劍、長槍、銃槍、充能斧共用）：擋下攻擊時光膜和樹紋亮起")


SETS = {
    "great_sword_charge": great_sword_charge,
    "dual_blades_demon": dual_blades_demon,
    "dual_blades_split_point": dual_blades_split_point,
    "hammer_charge": hammer_charge,
    "lance_charge": lance_charge,
    "lance_full_variants": lance_full_variants,
    "gunlance_reload": gunlance_reload,
    "long_sword_spirit": long_sword_spirit,
    "insect_glaive_extracts": insect_glaive_extracts,
    "switch_axe_states": switch_axe_states,
    "charge_blade_states": charge_blade_states,
    "bow_charge": bow_charge,
    "bowgun_gauges": bowgun_gauges,
    "hunting_horn_notes": hunting_horn_notes,
    "shield_guard": shield_guard,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    SETS[SET]()
    print("DONE", flush=True)
