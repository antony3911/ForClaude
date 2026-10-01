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
