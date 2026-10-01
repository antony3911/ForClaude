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


SETS = {
    "great_sword_charge": great_sword_charge,
    "dual_blades_demon": dual_blades_demon,
    "hammer_charge": hammer_charge,
    "lance_charge": lance_charge,
    "lance_full_variants": lance_full_variants,
    "gunlance_reload": gunlance_reload,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    SETS[SET]()
    print("DONE", flush=True)
