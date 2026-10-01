"""Elden Ring status looks for the insect glaive's extracts, built as meshes so the preview
shows what can be done in game with ordinary parts that fade in (Dissolve) and recolour
(Emissive_Color); real particle effects would be a later step.

  red extract    -> scarlet rot: crimson blade, small aeonia flowers at the root, rot dripping
  orange extract -> frenzied flame: sickly yellow-orange blade, tongues of flame licking up
  white extract  -> frost: pale icy blade, ice crystals growing from the edges

The colours here are the one place the mod leaves gold, because the user asked for them.
"""
import math

import bpy
from mathutils import Vector

import common as c
import motifs as m

from motifs import V  # noqa: E402  (V(x, y, z) -> Vector)

# blade core, blade edge, blade strength, effect colour, effect strength
# Kept dimmer than the gold: strong emission washes saturated red and blue out to pastel.
STATUS = {
    "rot": ("#E8303F", "#8A0A1E", 1.7, "#C8102E", 1.6),
    "flame": ("#FFC400", "#FF5A00", 2.6, "#FF8A10", 3.0),
    "frost": ("#E6F6FF", "#5FB0FF", 2.2, "#BFE4FF", 1.4),
}


def effect_material(kind):
    core, edge, s_blade, color, strength = STATUS[kind]
    if kind == "flame":
        # Soft, see-through tongues.
        mat = m.veil_material("FX_flame", 0.85, strength)
        node = mat.node_tree.nodes["Membrane_Emission"]
        node.inputs["Color"].default_value = c.hex_to_linear(color)
        return mat
    if kind == "frost":
        return c.make_material("FX_frost", "#DDF1FF", roughness=0.05, coat=1.0, emission=color, strength=strength)
    return c.make_material("FX_rot", "#8A0F1E", roughness=0.35, emission=color, strength=strength)


def rot_flower(name, center, radius, facing, mat, petals=6, twist=0.0):
    """A small scarlet aeonia: a ring of pointed petals around a bead."""
    facing = Vector(facing).normalized()
    ex = facing.orthogonal().normalized()
    ey = facing.cross(ex)
    objs = []
    for k in range(petals):
        a = twist + 2 * math.pi * k / petals
        d = ex * math.cos(a) + ey * math.sin(a)
        tip = Vector(center) + d * radius + facing * radius * 0.25
        objs += m.path_blade(f"{name}_Petal_{k}", [Vector(center), tip], facing,
                             lambda t, r=radius: r * 0.75 * math.sin(math.pi * min(t, 0.999)) ** 0.7 + 0.0005,
                             lambda t: 0.0016, mat, samples=16, n_sec=8, subsurf=0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius * 0.28, segments=16, ring_count=8, location=Vector(center))
    bead = bpy.context.active_object
    bead.name = f"{name}_Bead"
    bead.data.materials.append(mat)
    objs.append(bead)
    return objs


def rot(prefix, anchors, drips, mat, radius=0.016):
    """Flowers at the anchor points (position, facing) and drops of rot hanging below
    the given points."""
    objs = []
    for k, (pos, facing) in enumerate(anchors):
        objs += rot_flower(f"{prefix}_Flower_{k}", pos, radius * (1 - 0.15 * (k % 3)), facing, mat, twist=0.4 * k)
    for k, pos in enumerate(drips):
        objs += m.droplet(f"{prefix}_Drip_{k}", pos, 0.0055 - 0.001 * (k % 2), (0, 0, -1), mat, stretch=1.8)
    return objs


def flame(prefix, roots, heights, mat, width=0.02, lean=(0, 0, 1)):
    """Tongues of flame rising from the root points, each wavering and tapering."""
    objs = []
    lean = Vector(lean).normalized()
    for k, (root, h) in enumerate(zip(roots, heights)):
        phase = 0.6 * k
        path = [Vector(root) + lean * h * i / 8 + V(0.012 * math.sin(2 * math.pi * (1.3 * i / 8) + phase) * i / 8, 0, 0)
                for i in range(9)]
        objs += m.path_blade(f"{prefix}_Tongue_{k}", path, (0, 1, 0),
                             lambda t, w=width: w * math.sin(math.pi * min(t / 0.25, 1) * 0.5) * (1 - t) ** 1.2 + 0.0006,
                             lambda t: 0.004 * (1 - t), mat, samples=40, subsurf=0)
    return objs


def frost(prefix, roots, directions, lengths, mat, width=0.009):
    """Ice crystals: tapered six-sided shards growing from the root points."""
    objs = []
    for k, (root, d, length) in enumerate(zip(roots, directions, lengths)):
        d = Vector(d).normalized()
        objs += m.path_blade(f"{prefix}_Shard_{k}", [Vector(root), Vector(root) + d * length], d.orthogonal(),
                             lambda t, w=width: w * (1 - t) ** 0.9 + 0.0004,
                             lambda t, w=width: w * 0.9 * (1 - t) ** 0.9 + 0.0004, mat, n_sec=6, samples=12,
                             subsurf=0)
    return objs


# ------------------------------------------------------------------ scarlet rot, second try
# From the user's references: rot is a pink, mouldy, fuzzy texture (Elden Ring's rot-cure
# moss balls), and Malenia's wings shed small butterflies (mostly scarlet, a few violet-blue
# and white). So the red mote becomes a mould ball and tiny rot butterflies drift out of it.

def mould_material():
    """Pink, fuzzy and blotched with dark specks (the rot-cure moss balls), with a faint red
    glow from inside."""
    mat = bpy.data.materials.new("FX_mould")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Sheen Weight"].default_value = 1.0
    bsdf.inputs["Sheen Roughness"].default_value = 0.3
    bsdf.inputs["Sheen Tint"].default_value = c.hex_to_linear("#FFE3E0")
    bsdf.inputs["Subsurface Weight"].default_value = 0.3
    bsdf.inputs["Emission Color"].default_value = c.hex_to_linear("#FF3048")
    bsdf.inputs["Emission Strength"].default_value = 0.25
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 90.0
    noise.inputs["Detail"].default_value = 10.0
    tone = nodes.new("ShaderNodeValToRGB")                 # blotchy pinks
    tone.color_ramp.elements[0].position = 0.35
    tone.color_ramp.elements[0].color = c.hex_to_linear("#F3BFB6")
    tone.color_ramp.elements[1].position = 0.65
    tone.color_ramp.elements[1].color = c.hex_to_linear("#C9786E")
    links.new(noise.outputs["Fac"], tone.inputs["Fac"])
    cells = nodes.new("ShaderNodeTexVoronoi")              # dark specks
    cells.inputs["Scale"].default_value = 260.0
    specks = nodes.new("ShaderNodeValToRGB")
    specks.color_ramp.elements[0].position = 0.06
    specks.color_ramp.elements[0].color = (1, 1, 1, 1)
    specks.color_ramp.elements[1].position = 0.12
    specks.color_ramp.elements[1].color = (0, 0, 0, 1)
    links.new(cells.outputs["Distance"], specks.inputs["Fac"])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = c.hex_to_linear("#4A2A22")
    links.new(specks.outputs["Color"], mix.inputs["Factor"])
    links.new(tone.outputs["Color"], mix.inputs["A"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.8
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def mould_ball(name, center, radius, mat):
    """A lumpy ball: one main sphere with a few smaller ones grown onto it, all roughened."""
    center = Vector(center)
    objs = []
    lumps = [(V(0, 0, 0), 1.0), (V(0.55, -0.2, 0.45), 0.55), (V(-0.6, -0.15, 0.3), 0.5), (V(0.1, -0.3, -0.62), 0.48)]
    tex = bpy.data.textures.new(f"{name}_Lumps", "CLOUDS")
    tex.noise_scale = 0.25
    for k, (off, scale) in enumerate(lumps):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius * scale, segments=48, ring_count=24,
                                             location=center + off * radius)
        ball = bpy.context.active_object
        ball.name = f"{name}_{k}"
        disp = ball.modifiers.new("lumps", "DISPLACE")
        disp.texture = tex
        disp.strength = radius * 0.18
        disp.mid_level = 0.5
        ball.data.materials.append(mat)
        bpy.ops.object.shade_smooth()
        # Short fuzz all over, like mould.
        fuzz = ball.modifiers.new("fuzz", "PARTICLE_SYSTEM").particle_system.settings
        fuzz.type = "HAIR"
        fuzz.count = int(3000 * scale)
        fuzz.hair_length = radius * 0.16
        fuzz.root_radius = 1.0
        fuzz.tip_radius = 0.1
        fuzz.radius_scale = radius * 0.012
        fuzz.use_rotations = True
        fuzz.rotation_factor_random = 0.6
        objs.append(ball)
    return objs


BUTTERFLY_FORE = [(0.0, 0.004), (0.03, 0.03), (0.07, 0.06), (0.11, 0.08), (0.13, 0.07), (0.12, 0.04),
                  (0.1, 0.012), (0.07, -0.004), (0.03, -0.01)]
BUTTERFLY_HIND = [(0.0, -0.006), (0.04, -0.03), (0.08, -0.06), (0.09, -0.085), (0.07, -0.1),
                  (0.04, -0.09), (0.015, -0.05)]
BUTTERFLY_COLOURS = {"scarlet": ("#C8102E", "#FF6A2A"), "violet": ("#5A3CC8", "#B49CFF"),
                     "white": ("#F2EEF8", "#FFFFFF")}


def butterfly_materials():
    """Wings dark and see-through toward the root, glowing toward the edge (like the rot
    butterflies around Malenia's wings), with a brighter rim line."""
    mats = {}
    for key, (wing, edge) in BUTTERFLY_COLOURS.items():
        w = bpy.data.materials.new(f"Fly_{key}")
        w.use_nodes = True
        nodes, links = w.node_tree.nodes, w.node_tree.links
        for nd in list(nodes):
            nodes.remove(nd)
        out = nodes.new("ShaderNodeOutputMaterial")
        mix = nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = 0.85
        transparent = nodes.new("ShaderNodeBsdfTransparent")
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Strength"].default_value = 1.4
        coords = nodes.new("ShaderNodeTexCoord")
        gradient = nodes.new("ShaderNodeTexGradient")
        gradient.gradient_type = "SPHERICAL"
        mapping = nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (60, 60, 60)      # object space: wing ~1/60 m
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = c.hex_to_linear(edge)
        ramp.color_ramp.elements[1].position = 0.7
        ramp.color_ramp.elements[1].color = c.hex_to_linear(wing)
        links.new(coords.outputs["Object"], mapping.inputs["Vector"])
        links.new(mapping.outputs["Vector"], gradient.inputs["Vector"])
        links.new(gradient.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], emission.inputs["Color"])
        links.new(transparent.outputs["BSDF"], mix.inputs[1])
        links.new(emission.outputs["Emission"], mix.inputs[2])
        links.new(mix.outputs["Shader"], out.inputs["Surface"])
        e = c.make_material(f"Fly_{key}_Edge", edge, roughness=0.3, emission=edge, strength=2.5)
        body = c.make_material(f"Fly_{key}_Body", "#2A1014", roughness=0.6, emission=wing, strength=0.3)
        mats[key] = (w, e, body)
    return mats


def butterfly(name, center, size, yaw_deg, open_deg, pitch_deg, mats):
    """A tiny butterfly; size is the wing length, open_deg how far the wings are raised
    (0 = flat, 80 = nearly closed), yaw/pitch its heading."""
    wing_mat, edge_mat, body_mat = mats
    center = Vector(center)
    k = size / 0.13
    yaw, pitch, lift = math.radians(yaw_deg), math.radians(pitch_deg), math.radians(open_deg)
    rot = mathutils_matrix(yaw, pitch)
    objs = []
    for s in (-1, 1):
        for wname, outline in (("Fore", BUTTERFLY_FORE), ("Hind", BUTTERFLY_HIND)):
            loop = m.catmull([V(x, z, 0) for x, z in outline] + [V(outline[0][0], outline[0][1], 0)], 40)
            pts = [center + rot @ V(s * p.x * k * math.cos(lift), p.x * k * math.sin(lift), p.y * k) for p in loop]
            objs += m.flat_fill(f"{name}_{wname}_{s}", pts[:-1], wing_mat, center_origin=True)
            objs.append(c.curve_tube(f"{name}_{wname}_Edge_{s}", pts, [1.0] * len(pts), edge_mat,
                                     bevel=0.00035 * k, resolution=1))
    body = [center + rot @ V(0, 0, z * k) for z in (0.03, -0.075)]
    objs.append(c.curve_tube(f"{name}_Body", body, [1.0, 0.5], body_mat, bevel=0.0012 * k, resolution=2))
    return objs


def mathutils_matrix(yaw, pitch):
    from mathutils import Matrix
    return Matrix.Rotation(yaw, 3, "Z") @ Matrix.Rotation(pitch, 3, "X")


def rot_mote(prefix, center, radius, count=9, spread=0.075):
    """The red mote as a mould ball with tiny rot butterflies drifting out of it in a loose
    rising spiral, mostly scarlet with a violet and a white one, smaller as they leave."""
    center = Vector(center)
    objs = mould_ball(f"{prefix}_Mould", center, radius, mould_material())
    fly_mats = butterfly_materials()
    colours = ["scarlet", "scarlet", "violet", "scarlet", "white", "scarlet", "scarlet", "violet"]
    for i in range(count):
        t = (i + 1) / count
        a = math.radians(40 + 75 * i)
        pos = center + V(math.cos(a) * spread * (0.35 + 0.65 * t), -0.02 - 0.03 * t * math.sin(a) ** 2,
                         0.004 + 0.045 * t + 0.012 * math.sin(3 * a))
        objs += butterfly(f"{prefix}_Fly_{i}", pos, 0.016 * (1.0 - 0.4 * t), 25 * i - 40, 15 + 50 * (i % 3) / 2,
                          -60 + 25 * (i % 2), fly_mats[colours[i % len(colours)]])
    return objs
