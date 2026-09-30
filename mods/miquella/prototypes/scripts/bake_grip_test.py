"""Game-ready test: bake the high-poly woven grip onto a low-poly cylinder.

The woven ivory strands make the dual blade far too heavy for a game weapon (tens of
thousands of vertices). This bakes their surface detail into a normal map on a simple
cylinder, then renders the low-poly version next to the high-poly one for comparison.

Usage: python bake_grip_test.py <dual_blades.blend> <out_dir>
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(__file__))
import common as c
import blades

BLEND, OUT = sys.argv[1], sys.argv[2]
RES = 1024


def count(objs):
    v = f = 0
    deps = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        m = o.evaluated_get(deps).to_mesh()
        v += len(m.vertices)
        f += sum(len(p.vertices) - 2 for p in m.polygons)
        o.evaluated_get(deps).to_mesh_clear()
    return v, f


def main():
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    root = bpy.data.objects["DualBlade_R"]
    grip_parts = [o for o in root.children_recursive
                  if o.name.startswith(("Strand_", "Grip_Core"))]
    # Work in world space, unparented.
    for o in grip_parts:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    # Hide everything else.
    for o in bpy.data.objects:
        if o not in grip_parts and o.type in {"MESH", "CURVE"}:
            o.hide_render = True
            o.hide_set(True)

    bpy.ops.object.select_all(action="DESELECT")
    for o in grip_parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = grip_parts[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    high = bpy.context.view_layer.objects.active
    high.name = "Grip_HighPoly"
    hv, hf = count([high])

    # Low-poly cage: a plain cylinder around the grip, UV unwrapped as a tube.
    bb = [high.matrix_world @ v.co for v in high.data.vertices]
    zmin = min(p.z for p in bb)
    zmax = min(max(p.z for p in bb), blades.GUARD_Z)
    cx = sum(p.x for p in bb) / len(bb)
    cy = sum(p.y for p in bb) / len(bb)
    # Estimate the grip radius from its middle only: the guard's downward prongs reach
    # below the guard height and would inflate it.
    mid = [p for p in bb if zmin + 0.03 < p.z < blades.GUARD_Z - 0.04]
    cx = sum(p.x for p in mid) / len(mid)
    cy = sum(p.y for p in mid) / len(mid)
    radius = max(math.hypot(p.x - cx, p.y - cy) for p in mid) * 0.86
    zmax = blades.GUARD_Z - 0.012
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=zmax - zmin - 0.004,
                                        location=(cx, cy, (zmin + zmax) / 2), end_fill_type="NOTHING")
    low = bpy.context.active_object
    low.name = "Grip_LowPoly"
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cylinder_project(direction="ALIGN_TO_OBJECT", scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()
    lv, lf = count([low])

    # Bake target image and material on the low-poly mesh.
    img = bpy.data.images.new("Grip_Normal", RES, RES, float_buffer=False)
    img.colorspace_settings.name = "Non-Color"
    mat = bpy.data.materials.new("Grip_Baked")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = c.hex_to_linear(c.PALETTE["ivory"])
    bsdf.inputs["Roughness"].default_value = 0.35
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    nodes.active = tex
    low.data.materials.append(mat)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 8
    bpy.ops.object.select_all(action="DESELECT")
    high.hide_set(False)
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.bake(type="NORMAL", use_selected_to_active=True, cage_extrusion=0.006,
                        max_ray_distance=0.02, normal_space="TANGENT", margin=8)
    img.filepath_raw = os.path.join(OUT, "grip_normal.png")
    img.file_format = "PNG"
    img.save()

    # Hook the baked normal map up for the comparison render.
    nmap = nodes.new("ShaderNodeNormalMap")
    links.new(tex.outputs["Color"], nmap.inputs["Color"])
    links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    # Side by side: high poly on the left, low poly with baked normals on the right.
    low.location.x += 0.05
    high.hide_render = False
    low.hide_render = False
    c.setup_render(samples=32, res=(700, 900), world_hex="#2E2E33", world_strength=0.5)
    for o in list(bpy.data.objects):
        if o.type == "CAMERA":
            bpy.data.objects.remove(o)
    target = (cx + 0.025, cy, (zmin + zmax) / 2)
    paths = c.render_views(OUT, "grip_compare", target, 0.32, [("front", 0, 5)], lens=55)
    print(f"[bake] high poly: {hv} verts / {hf} tris; low poly: {lv} verts / {lf} tris", flush=True)
    print("DONE", paths, flush=True)


if __name__ == "__main__":
    main()
