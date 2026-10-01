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
    # Realistic, not glowing (user's call): the texture matters more than the light here.
    bsdf.inputs["Emission Strength"].default_value = 0.0
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


def fuzz_material():
    """The mould's fuzz: pale pink, whitening toward the tips."""
    mat = bpy.data.materials.new("FX_mould_fuzz")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.7
    bsdf.inputs["Subsurface Weight"].default_value = 0.4
    info = nodes.new("ShaderNodeHairInfo")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = c.hex_to_linear("#B8706A")
    ramp.color_ramp.elements[1].color = c.hex_to_linear("#F2CFC8")
    links.new(info.outputs["Intercept"], ramp.inputs["Fac"])
    # Some strands brown and dead, in patches.
    pick = nodes.new("ShaderNodeValToRGB")
    pick.color_ramp.elements[0].position = 0.78
    pick.color_ramp.elements[1].position = 0.8
    links.new(info.outputs["Random"], pick.inputs["Fac"])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = c.hex_to_linear("#5A2E26")
    links.new(pick.outputs["Color"], mix.inputs["Factor"])
    links.new(ramp.outputs["Color"], mix.inputs["A"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return mat


def mould_ball(name, center, radius, mat):
    """A cluster of mouldy balls (like the rot-cure moss balls), each lumpy and fuzzy."""
    center = Vector(center)
    objs = []
    lumps = [(V(0, 0, 0), 0.68), (V(0.78, -0.1, 0.12), 0.58), (V(-0.72, -0.05, 0.22), 0.56),
             (V(0.08, -0.3, 0.72), 0.52), (V(0.05, 0.35, -0.45), 0.5)]
    fuzz_mat = fuzz_material()
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
        ball.data.materials.append(fuzz_mat)
        bpy.ops.object.shade_smooth()
        # Dense fuzz all over, like mould.
        fuzz = ball.modifiers.new("fuzz", "PARTICLE_SYSTEM").particle_system.settings
        fuzz.type = "HAIR"
        fuzz.count = int(9000 * scale)
        fuzz.hair_length = radius * 0.22
        fuzz.root_radius = 1.0
        fuzz.tip_radius = 0.05
        fuzz.radius_scale = radius * 0.008
        fuzz.material = 2
        fuzz.use_rotations = True
        fuzz.rotation_factor_random = 0.6
        objs.append(ball)
    return objs


BUTTERFLY_FORE = [(0.0, 0.004), (0.03, 0.03), (0.07, 0.06), (0.11, 0.08), (0.13, 0.07), (0.12, 0.04),
                  (0.1, 0.012), (0.07, -0.004), (0.03, -0.01)]
BUTTERFLY_HIND = [(0.0, -0.006), (0.04, -0.03), (0.08, -0.06), (0.09, -0.085), (0.07, -0.1),
                  (0.04, -0.09), (0.015, -0.05)]
# root (near the body), middle, outer, decayed edge band, vein colour
BUTTERFLY_COLOURS = {
    "scarlet": ("#120203", "#4E060E", "#9E1A12", "#C9786A", "#0A0202"),
    "violet": ("#08040E", "#241448", "#4A3C9E", "#A898CC", "#050309"),
    "white": ("#2A2424", "#9A948E", "#D8D2CA", "#E6E0D8", "#2A2222"),
}


def wing_material(key, span):
    """Real butterfly wing, not a sheet of light: dark at the body, scarlet outward, a pale
    decayed band at the edge, dark veins radiating from the body and cross veins, mottled
    dusty scales, a little translucency. Object space: the body is at the origin and the
    wings lie roughly in the XY plane; `span` is the wing length."""
    root, mid, outer, edge, vein = BUTTERFLY_COLOURS[key]
    mat = bpy.data.materials.new(f"Wing_{key}")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.8
    bsdf.inputs["Sheen Weight"].default_value = 0.15         # a little dust on the scales
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    coords = nodes.new("ShaderNodeTexCoord")
    xy = nodes.new("ShaderNodeVectorMath")
    xy.operation = "MULTIPLY"
    xy.inputs[1].default_value = (1 / span, 1 / span, 0)
    links.new(coords.outputs["Object"], xy.inputs[0])
    dist = nodes.new("ShaderNodeVectorMath")
    dist.operation = "LENGTH"
    links.new(xy.outputs["Vector"], dist.inputs[0])
    # Mottling: shift the distance a little with noise so the bands are not clean.
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 18.0
    noise.inputs["Detail"].default_value = 6.0
    links.new(xy.outputs["Vector"], noise.inputs["Vector"])
    wobble = nodes.new("ShaderNodeMath")
    wobble.operation = "MULTIPLY_ADD"
    wobble.inputs[1].default_value = 0.25
    links.new(noise.outputs["Fac"], wobble.inputs[0])
    links.new(dist.outputs["Value"], wobble.inputs[2])
    tone = nodes.new("ShaderNodeValToRGB")
    els = tone.color_ramp.elements
    els[0].position, els[0].color = 0.1, c.hex_to_linear(root)
    els[1].position, els[1].color = 1.05, c.hex_to_linear(edge)
    e = els.new(0.45)
    e.color = c.hex_to_linear(mid)
    e = els.new(0.85)
    e.color = c.hex_to_linear(outer)
    links.new(wobble.outputs["Value"], tone.inputs["Fac"])
    # Veins: thin dark lines radiating from the body, plus a few cross veins.
    radial = nodes.new("ShaderNodeTexGradient")
    radial.gradient_type = "RADIAL"
    links.new(coords.outputs["Object"], radial.inputs["Vector"])
    spokes = nodes.new("ShaderNodeMath")
    spokes.operation = "MULTIPLY"
    spokes.inputs[1].default_value = 2 * math.pi * 26
    links.new(radial.outputs["Fac"], spokes.inputs[0])
    wave = nodes.new("ShaderNodeMath")
    wave.operation = "SINE"
    links.new(spokes.outputs["Value"], wave.inputs[0])
    rings = nodes.new("ShaderNodeMath")
    rings.operation = "MULTIPLY"
    rings.inputs[1].default_value = 2 * math.pi * 3.2
    links.new(dist.outputs["Value"], rings.inputs[0])
    wave2 = nodes.new("ShaderNodeMath")
    wave2.operation = "SINE"
    links.new(rings.outputs["Value"], wave2.inputs[0])
    both = nodes.new("ShaderNodeMath")
    both.operation = "MAXIMUM"
    links.new(wave.outputs["Value"], both.inputs[0])
    links.new(wave2.outputs["Value"], both.inputs[1])
    lines = nodes.new("ShaderNodeValToRGB")
    lines.color_ramp.elements[0].position = 0.9
    lines.color_ramp.elements[0].color = (0, 0, 0, 1)
    lines.color_ramp.elements[1].position = 0.985
    lines.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(both.outputs["Value"], lines.inputs["Fac"])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = c.hex_to_linear(vein)
    links.new(lines.outputs["Color"], mix.inputs["Factor"])
    links.new(tone.outputs["Color"], mix.inputs["A"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    # Only a trace of light, so they still read in the dark.
    links.new(mix.outputs["Result"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.12
    return mat


def body_material():
    mat = c.make_material("Fly_Body", "#140806", roughness=0.9)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Sheen Weight"].default_value = 0.25
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    return mat


def butterfly_materials(span=0.02):
    body = body_material()
    return {key: (wing_material(key, span), body) for key in BUTTERFLY_COLOURS}


def ragged(outline, rng, notches=2):
    """Tattered wing edge: the outline wobbles and has a couple of bites taken out."""
    pts = m.catmull([V(x, z, 0) for x, z in outline] + [V(outline[0][0], outline[0][1], 0)], 70)[:-1]
    bites = [rng.randrange(10, len(pts) - 10) for _ in range(notches)]
    out = []
    for i, p in enumerate(pts):
        f = 1.0 + 0.05 * math.sin(i * 1.7 + rng.random()) * (p.length > 0.03)
        for b in bites:
            d = abs(i - b)
            if d < 4:
                f *= 1 - 0.18 * (1 - d / 4)
        out.append(p * f)
    return out


def butterfly(name, center, size, yaw_deg, open_deg, pitch_deg, mats, seed=0):
    """A small, realistic butterfly: one object with four ragged wings around the body at
    its origin (so the wing pattern is centred on the body), a segmented fuzzy body and two
    thin antennae with clubbed tips. size: wing length; open_deg: how far the wings are
    raised; yaw/pitch: heading."""
    import bmesh
    import random
    rng = random.Random(seed)
    wing_mat, body_mat = mats
    k = size / 0.13
    lift = math.radians(open_deg)
    bm = bmesh.new()
    for s in (-1, 1):
        for outline in (BUTTERFLY_FORE, BUTTERFLY_HIND):
            loop = ragged(outline, rng)
            verts = [bm.verts.new(V(s * p.x * k * math.cos(lift), p.y * k, p.x * k * math.sin(lift))) for p in loop]
            edges = [bm.edges.new((verts[i], verts[(i + 1) % len(verts)])) for i in range(len(verts))]
            bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = c.link(bpy.data.objects.new(name, mesh))
    obj.data.materials.append(wing_mat)
    obj.location = Vector(center)
    obj.rotation_euler = (math.radians(pitch_deg), 0, math.radians(yaw_deg))
    objs = [obj]
    # Body: thorax and a tapering abdomen of small segments, then antennae.
    parts = [(0.012, 0.016), (-0.004, 0.012), (-0.018, 0.0105), (-0.032, 0.009), (-0.046, 0.0075), (-0.058, 0.006)]
    for j, (y, r) in enumerate(parts):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r * k, segments=12, ring_count=8, location=(0, y * k, 0))
        seg = bpy.context.active_object
        seg.name = f"{name}_Body_{j}"
        seg.scale = (0.8, 1.3, 0.8)
        seg.data.materials.append(body_mat)
        seg.parent = obj
        seg.matrix_parent_inverse.identity()
        objs.append(seg)
    for s in (-1, 1):
        ant = [V(s * 0.004 * k, 0.026 * k, 0.004 * k), V(s * 0.02 * k, 0.07 * k, 0.02 * k),
               V(s * 0.03 * k, 0.1 * k, 0.03 * k)]
        a = c.curve_tube(f"{name}_Antenna_{s}", m.catmull(ant, 16), [1.0] * 16, body_mat, bevel=0.0012 * k,
                         resolution=1)
        a.parent = obj
        a.matrix_parent_inverse.identity()
        objs.append(a)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0035 * k, segments=8, ring_count=6, location=ant[-1])
        club = bpy.context.active_object
        club.name = f"{name}_Club_{s}"
        club.data.materials.append(body_mat)
        club.parent = obj
        club.matrix_parent_inverse.identity()
        objs.append(club)
    return objs


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
        objs += butterfly(f"{prefix}_Fly_{i}", pos, 0.019 * (1.0 - 0.35 * t), 25 * i - 40, 10 + 30 * (i % 3),
                          -55 + 25 * (i % 2), fly_mats[colours[i % len(colours)]], seed=i)
    return objs
