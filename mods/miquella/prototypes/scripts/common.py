"""Shared scene, material, and render helpers for the prototype scripts.

Run the prototype scripts with a Python that has the `bpy` module (Blender 4.2+).
"""
import math
import os

import bpy
from mathutils import Vector

# Palette from DESIGN.md (section 2), as linear-ish sRGB hex.
PALETTE = {
    "ivory": "#EFE8D2",
    "circlet": "#EED9A6",     # pale gold, a little lighter than the hair (user spec)
    "ivory_shadow": "#D9C9A0",
    "glow": "#FFA526",        # bright gold (not white): halo, rings, droplets
    "hair": "#DCC08A",
    "skin": "#F3D6BE",
    "robe": "#E8E0CC",
    "gold": "#946E1C",
    "gold_hi": "#B8933D",
    "blade_core": "#FFB445",  # pale bright gold
    "blade_edge": "#FF9A1A",  # deeper gold at glancing edges
    "proxy": "#8A8A8A",
}


def hex_to_linear(hex_color):
    """Convert an sRGB hex string to a linear RGBA tuple for Blender."""
    h = hex_color.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]

    def to_linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return (*[to_linear(c) for c in srgb], 1.0)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    return scene


def make_material(name, base, roughness=0.45, emission=None, strength=0.0,
                  metallic=0.0, coat=0.0, subsurface=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_to_linear(base)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Subsurface Weight"].default_value = subsurface
    if emission:
        bsdf.inputs["Emission Color"].default_value = hex_to_linear(emission)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def set_emission_strength(mat, strength):
    mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = strength


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def add_light(name, kind, location, energy, color="#FFFFFF", size=1.0, target=(0, 0, 0)):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = hex_to_linear(color)[:3]
    if kind == "AREA":
        data.size = size
    obj = link(bpy.data.objects.new(name, data))
    obj.location = location
    look_at(obj, target)
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_camera(name, location, target, lens=85):
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam = link(bpy.data.objects.new(name, cam_data))
    cam.location = location
    look_at(cam, target)
    return cam


def orbit_location(target, distance, azimuth_deg, elevation_deg):
    """Camera position around `target`. Azimuth 0 = front (-Y), 90 = right side (+X)."""
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    t = Vector(target)
    return (
        t.x + distance * math.cos(el) * math.sin(az),
        t.y - distance * math.cos(el) * math.cos(az),
        t.z + distance * math.sin(el),
    )


def setup_render(samples=64, res=(900, 900), world_hex="#2B2B2E", world_strength=0.6, glare=False):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.film_transparent = False
    # Filmic keeps bright emission golden; AgX washes it out toward white.
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = hex_to_linear(world_hex)
    bg.inputs["Strength"].default_value = world_strength
    scene.world = world

    scene.use_nodes = True
    tree = scene.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    rl = tree.nodes.new("CompositorNodeRLayers")
    comp = tree.nodes.new("CompositorNodeComposite")
    if glare:
        g = tree.nodes.new("CompositorNodeGlare")
        g.glare_type = "FOG_GLOW"
        g.quality = "HIGH"
        g.threshold = 0.6
        g.size = 8
        g.mix = 0.0
        tree.links.new(rl.outputs["Image"], g.inputs["Image"])
        tree.links.new(g.outputs["Image"], comp.inputs["Image"])
    else:
        tree.links.new(rl.outputs["Image"], comp.inputs["Image"])
    return scene


def render_views(out_dir, prefix, target, distance, views, lens=85):
    """Render each (label, azimuth, elevation) view and return the file paths."""
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    paths = []
    for label, az, el in views:
        cam = add_camera(f"cam_{label}", orbit_location(target, distance, az, el), target, lens)
        scene.camera = cam
        path = os.path.join(out_dir, f"{prefix}_{label}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        paths.append(path)
    return paths


def contact_sheet(paths, out_path, cols=3, label_height=0):
    """Tile rendered images into one sheet for quick review."""
    from PIL import Image

    images = [Image.open(p).convert("RGB") for p in paths]
    w, h = images[0].size
    rows = math.ceil(len(images) / cols)
    sheet = Image.new("RGB", (cols * w, rows * h), (20, 20, 22))
    for i, im in enumerate(images):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(out_path)
    return out_path


def curve_tube(name, points, radii, material, bevel=1.0, resolution=4):
    """Build a tapered tube along 3D points. `radii` scale the bevel per point."""
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = bevel
    data.bevel_resolution = resolution
    data.use_fill_caps = True
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co, r in zip(spline.points, points, radii):
        p.co = (co[0], co[1], co[2], 1.0)
        p.radius = r
    obj = link(bpy.data.objects.new(name, data))
    obj.data.materials.append(material)
    return obj


def to_mesh(objs, name):
    """Convert curve objects to meshes and join them into one object."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = name
    return joined
