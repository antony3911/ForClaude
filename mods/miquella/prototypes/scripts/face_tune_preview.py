"""Face tuning by the face's own joints (2026-10-04): what offsets on the game's facial joints do to
the female face (ch00_001_0000), for the user's direction (DESIGN.md "臉": droopy, half-lidded,
haughty and toying eyes, a one-sided smile). The same offsets (head space, mm / degrees) are what
a script would add on top of the hunter's character edit and expressions in game.

Joints (the face's rig, 393 bones): outer eye corners L/R_OuterEyeJ_LOD02 (children Up/Lo),
upper / lower lids L/R_UpEyeLidJ_LOD02 / LoEyeLidJ_LOD02 (at the eye's centre: turning them about
the head's left axis, + lowers, - raises), mouth corners L/R_cornerLip_LOD02, brows L/R_EyeBrow_A/B/C_LOD01 (inner, middle, outer).

Usage: bpy45 python face_tune_preview.py <out dir>
Renders contain Capcom's face: keep them out of the repo."""
import math
import os
import sys

import bpy
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FACE = ("C:/Users/anton/MiquellaTools/extracted/natives/stm/art/model/character/ch00/001/0000/"
        "ch00_001_0000.mesh.241111606")
DROP = ("eyelens", "eyeshadow", "shadow", "fakeao", "cage")

# Offsets in the head's space: x the hunter's left, y up, z the face's front; mm and degrees.
# For the right side x is mirrored. "rot": (axis, degrees) about the joint itself.
TWEAKS = {
    "droop": [   # outer eye corners down and a touch back: a droopy eye
        ("{s}_OuterEyeJ_LOD02", (0.0, -2.2, -0.6), None),
        ("{s}_UpEyeLid_B_LOD00", (0.0, -0.6, 0.0), None),
    ],
    "lids": [    # upper lids lowered over the iris: half-lidded
        ("{s}_UpEyeLidJ_LOD02", (0.0, 0.0, 0.0), ((1, 0, 0), 11.0)),
    ],
    "smirk": [   # one mouth corner up and back (the hunter's left), the other a little; lower lids
                 # pushed up a touch (the amused eye a smile makes)
        ("L_cornerLip_LOD02", (0.9, 2.6, -1.4), None),
        ("R_cornerLip_LOD02", (0.3, 0.7, -0.4), None),
        ("{s}_LoEyeLidJ_LOD02", (0.0, 0.0, 0.0), ((1, 0, 0), -5.0)),
    ],
    "brow": [    # brows at ease, the left outer end lifted: amused
        ("L_EyeBrow_C_LOD01", (0.0, 1.6, 0.0), None),
        ("L_EyeBrow_B_LOD01", (0.0, 0.8, 0.0), None),
        ("{s}_EyeBrow_A_LOD01", (0.0, -0.5, 0.0), None),
    ],
}
VARIANTS = [("base", []), ("A droop+lids", ["droop", "lids"]), ("B +smirk", ["droop", "lids", "smirk"]),
            ("C +brow", ["droop", "lids", "smirk", "brow"])]


def log(*a):
    print("[face]", *a, flush=True)


def head_to_blender(v):
    """Head/file space (x left, y up, z front) -> Blender (x, -z, y)."""
    return Vector((v[0], -v[2], v[1]))


def import_face():
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable("re_mesh_editor", default_set=True)
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile
    import miquella_body as mb
    importREMeshFile(FACE, mb.IMPORT_OPTS)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    meshes = []
    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        names = " ".join(m.name.lower() for m in o.data.materials if m)
        if any(k in names for k in DROP):
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        if not any(m.type == "ARMATURE" for m in o.modifiers):
            o.modifiers.new("Armature", "ARMATURE").object = arm
        meshes.append(o)
    return arm, meshes


def paint(meshes, arm):
    """Colour attributes: skin, dark lashes and liner, eyes white with a gold iris and dark pupil."""
    for o in meshes:
        names = " ".join(m.name.lower() for m in o.data.materials if m)
        me = o.data
        for a in list(me.color_attributes):     # the importer's (the game's vertex colours)
            me.color_attributes.remove(a)
        col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        me.color_attributes.active_color = col
        me.color_attributes.render_color_index = 0
        mw = o.matrix_world
        if "eye_" in names:
            side = "L" if any(m.name.lower().startswith("eye_l") for m in me.materials) else "R"
            centre = arm.matrix_world @ arm.data.bones[f"{side}_EyeJ_LOD02"].head_local
            front = max((mw @ v.co for v in me.vertices), key=lambda p: -p.y)
            axis = (front - centre).normalized()
            for v in me.vertices:
                d = ((mw @ v.co) - centre).normalized()
                a = math.degrees(math.acos(max(-1.0, min(1.0, d.dot(axis)))))
                c = (0.02, 0.015, 0.01, 1) if a < 10 else (0.85, 0.55, 0.12, 1) if a < 26 else (0.92, 0.9, 0.88, 1)
                col.data[v.index].color = c
            continue
        c = (0.06, 0.04, 0.03, 1) if ("lash" in names or "eyeline" in names) else \
            (0.75, 0.35, 0.33, 1) if "mouth" in names else (0.93, 0.78, 0.70, 1)
        for v in me.vertices:
            col.data[v.index].color = c


def set_pose(arm, keys):
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
    for key in keys:
        for name, move, rot in TWEAKS[key]:
            for side, sx in (("L", 1), ("R", -1)):
                if "{s}" not in name and side == "R":
                    continue
                bone_name = name.format(s=side)
                pb = arm.pose.bones.get(bone_name)
                if pb is None:
                    log("no joint", bone_name)
                    continue
                m3 = (arm.matrix_world.to_3x3() @ pb.bone.matrix_local.to_3x3()).inverted()
                world = head_to_blender((move[0] * sx / 1000, move[1] / 1000, move[2] / 1000))
                pb.location = Vector(pb.location) + m3 @ world
                if rot:
                    # mirrored to the right side: a turn about x stays as it is, about y or z reverses
                    ax = head_to_blender(rot[0])
                    deg = rot[1] * (1 if abs(rot[0][0]) == 1 else sx)
                    q = (m3 @ ax).normalized()
                    from mathutils import Quaternion
                    pb.rotation_quaternion = Quaternion(q, math.radians(deg)) @ pb.rotation_quaternion
    bpy.context.view_layer.update()


def render_all(arm, out):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "VERTEX"
    scene.display.shading.show_cavity = True
    scene.render.resolution_x, scene.render.resolution_y = 520, 620
    scene.view_settings.view_transform = "Standard"
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 0.205
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    target = Vector((0, 0, 1.605))
    paths = []
    for label, keys in VARIANTS:
        set_pose(arm, keys)
        for view, deg in (("front", 0), ("q", 32)):
            a = math.radians(deg)
            cam.location = target + Vector((math.sin(a), -math.cos(a), 0.02)) * 1.0
            cam.rotation_euler = (math.radians(89), 0, a)
            path = os.path.join(out, f"face_{label.split()[0]}_{view}.png")
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            paths.append((label, view, path))
    return paths


def sheet(paths, out):
    from PIL import Image, ImageDraw, ImageFont
    labels = [v[0] for v in VARIANTS]
    ims = {(l, v): Image.open(p).convert("RGB") for l, v, p in paths}
    w, h = next(iter(ims.values())).size
    s = Image.new("RGB", (w * len(labels), h * 2 + 40), "white")
    d = ImageDraw.Draw(s)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 26)
    except OSError:
        font = None
    for i, l in enumerate(labels):
        d.text((i * w + 12, 6), l, fill="black", font=font)
        for j, v in enumerate(("front", "q")):
            s.paste(ims[(l, v)], (i * w, 40 + j * h))
    path = os.path.join(out, "face_tune_sheet.png")
    s.save(path)
    return path


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = os.path.abspath(args[0])
    os.makedirs(out, exist_ok=True)
    arm, meshes = import_face()
    log("face objects:", [o.name for o in meshes], "bones", len(arm.data.bones))
    paint(meshes, arm)
    paths = render_all(arm, out)
    log("sheet:", sheet(paths, out))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout.flush()
        os._exit(0)
