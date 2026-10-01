"""Action-state previews: how a weapon's own parts react to weapon actions (visual only).

Each set renders the same weapon in several states side by side with labels, to agree on
the look before building the in-game version (material parameters, parts shown/hidden or
faded with Dissolve, parts moved by bones; see mods/research/mhws_modding_notes.md).

Sets:
  great_sword_charge  normal (gold) / charge 1 (bright gold) / charge 2 (white light)
  dual_blades_demon   normal / splitting / demon mode (three blades) / archdemon (bright gold)
  hammer_charge       levels 0-3: more rings around the head, the caged sun brightens
  lance_charge        levels 0-3: a cone of large rings grows root to tip, brighter each level
  lance_full_variants full charge with the cone of light at different strengths
  gunlance_reload     rest / spring compressed (core charging) / spring rebounds
  long_sword_spirit   spirit levels: pale gold / gold / bright gold / white, light flowing on the hamon
  insect_glaive_extracts  extracts as scarlet rot / frost / frenzied flame, two layouts
  switch_axe_states   switch gauge on the phials, power axe, sword mode, amped

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
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
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


def labelled_strip(paths, labels, out_path, title):
    """Panels side by side, a label above each, a title on top."""
    from PIL import Image, ImageDraw, ImageFont
    imgs = [Image.open(p).convert("RGB") for p in paths]
    w, h = imgs[0].size
    band, head = 70, 80
    sheet = Image.new("RGB", (w * len(imgs), h + band + head), (14, 14, 18))
    draw = ImageDraw.Draw(sheet)
    f_title = ImageFont.truetype(FONT, 40)
    f_label = ImageFont.truetype(FONT, 32)
    tw = draw.textlength(title, font=f_title)
    draw.text(((sheet.width - tw) / 2, 18), title, font=f_title, fill=(240, 220, 170))
    for i, (img, text) in enumerate(zip(imgs, labels)):
        sheet.paste(img, (i * w, head + band))
        lw = draw.textlength(text, font=f_label)
        draw.text((i * w + (w - lw) / 2, head + 16), text, font=f_label, fill=(235, 235, 235))
        if i:
            draw.line([(i * w, head), (i * w, sheet.height)], fill=(60, 60, 66), width=2)
    sheet.save(out_path)
    return out_path


# ------------------------------------------------------------------ great sword charge

def great_sword_charge():
    import arsenal
    c.reset_scene()
    mats = capture_build(arsenal.great_sword)
    m.glow_mode(mats)
    target, distance = (0.04, 0, 0.8), 3.2
    stage_lights(target, distance)
    stages = [
        # label, blade core, blade edge, blade strength, light colour, light strength, core strength
        ("一般（金）", c.PALETTE["blade_core"], c.PALETTE["blade_edge"], 2.2, c.PALETTE["glow"], 2.5, 3.0),
        ("一段蓄力（亮金）", BRIGHT_BLADE[0], BRIGHT_BLADE[1], BRIGHT_BLADE[2], BRIGHT_LIGHT[0], BRIGHT_LIGHT[1],
         BRIGHT_CORE[1]),
        ("二段蓄力（白光）", "#FFFBF0", "#FFE7B0", 6.0, "#FFF2D6", 5.5, 7.0),
    ]
    paths = []
    for i, (label, core_hex, edge_hex, s_blade, light_hex, s_light, s_core) in enumerate(stages):
        set_blade(mats["blade"], core_hex, edge_hex, s_blade)
        set_glow(mats["light"], light_hex, s_light)
        set_glow(mats["core"], core_hex, s_core)
        paths += c.render_views(OUT, f"stage{i}", target, distance, [("front", 0, 4)], lens=50)
    labelled_strip(paths, [s[0] for s in stages], os.path.join(OUT, "great_sword_charge.png"),
                   "大劍蓄力：光刃從金 → 亮金 → 白光")


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

    # ---- layout B: three motes in a triangle around the single blade
    b_objs, b_fx, b_mats = [], {}, {}
    motes = {"rot": V(0, -0.025, top + 0.5), "flame": V(-0.095, -0.025, top + 0.12),
             "frost": V(0.095, -0.025, top + 0.12)}
    for kind, p in motes.items():
        mat = c.make_material(f"Mote_{kind}", c.PALETTE["glow"], roughness=0.1, emission=c.PALETTE["glow"],
                              strength=2.0)
        b_mats[kind] = mat
        b_objs += m.droplet(f"Mote_{kind}", p, 0.014, (0, 0, 1), mat, stretch=1.4)
        b_objs += m.halo(f"Mote_Halo_{kind}", p + V(0, 0, 0.004), 0.026, 0.0022, (0, 1, 0), mats["light"])
    tri = [motes["rot"], motes["flame"], motes["frost"], motes["rot"]]
    b_triangle = []
    for k in range(3):
        a, b = tri[k], tri[k + 1]
        u = (b - a).normalized()
        b_triangle.append(c.curve_tube(f"Triangle_{k}", [a + u * 0.03, b - u * 0.03], [1, 1], mats["light"],
                                       bevel=0.0018, resolution=2))
    p = motes["rot"]
    b_fx["rot_v1"] = fx.rot("B_Rot", [(p + V(-0.034, 0, 0.012), (0, -1, 0.2)), (p + V(0.034, 0, 0.004), (0, -1, 0.2)),
                                   (p + V(0.004, 0, 0.038), (0, -1, 0.2))],
                         [p + V(-0.014, 0, -0.032), p + V(0.016, 0, -0.042)], fx_mats["rot"], radius=0.016)
    # Second try at rot (user's references): the mote turns into a mould ball shedding butterflies.
    b_fx["rot"] = fx.rot_mote("B_Rot2", motes["rot"], 0.017)
    show(b_fx.pop("rot_v1"), False)
    rot_mote_drop = [bpy.data.objects["Mote_rot"]]
    p = motes["flame"]
    b_fx["flame"] = fx.flame("B_Flame", [p + V(-0.012, 0, 0.012), p + V(0.006, 0, 0.016), p + V(0.018, 0, 0.008)],
                             (0.08, 0.1, 0.065), fx_mats["flame"], width=0.016)
    p = motes["frost"]
    angles = (20, 70, 120, 165, -30, -80)
    b_fx["frost"] = fx.frost("B_Frost", [p] * len(angles),
                             [V(math.cos(math.radians(a)), 0, math.sin(math.radians(a))) for a in angles],
                             (0.05, 0.06, 0.045, 0.05, 0.04, 0.035), fx_mats["frost"], width=0.007)

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
                    color, strength = (fx.STATUS[kind][0], 4.0) if kind in lit else (c.PALETTE["glow"], 2.0)
                    set_glow(b_mats[kind], color, strength)
                    show(b_fx[kind], kind in lit)
                show(rot_mote_drop, "rot" not in lit)      # the droplet becomes the mould ball
                show(b_triangle, full)
            paths += c.render_views(OUT, f"{layout}_state{i}", target, distance, [("front", 12, 4)], lens=50)
        if layout == "B":
            # Close-ups of each lit mote (the last state has all three lit).
            close = []
            for kind, dist in (("rot", 0.3), ("flame", 0.42), ("frost", 0.42)):
                close += c.render_views(OUT, f"B_close_{kind}", motes[kind] + V(0, 0, 0.025), dist,
                                        [("front", 12, 6)], lens=50)
            labelled_strip(close, ["猩紅腐敗", "癲火", "冰凍"], os.path.join(OUT, "insect_glaive_extracts_B_close.png"),
                           "方案 B 特寫：三顆光粒點亮後的樣子")
        title = ("方案 A：光刃變三刃（中猩紅腐敗、左癲火、右冰凍）" if layout == "A"
                 else "方案 B：單刃＋三顆光粒圍成三角形（上猩紅腐敗、左癲火、右冰凍）")
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


SETS = {
    "great_sword_charge": great_sword_charge,
    "dual_blades_demon": dual_blades_demon,
    "hammer_charge": hammer_charge,
    "lance_charge": lance_charge,
    "lance_full_variants": lance_full_variants,
    "gunlance_reload": gunlance_reload,
    "long_sword_spirit": long_sword_spirit,
    "insect_glaive_extracts": insect_glaive_extracts,
    "switch_axe_states": switch_axe_states,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    SETS[SET]()
    print("DONE", flush=True)
