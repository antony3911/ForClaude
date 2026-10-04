"""Option B for the face's pale lower neck (2026-10-04): a gold choker over the seam where our
body meets the face's neck. The user's own idea (2026-10-03, DESIGN.md "服裝" -> 項圈) and
correction (2026-10-04): a ring that fits round the neck like a 地雷系 choker, not a necklace
hanging on the chest; made of gold. Three versions, all gold metal, light where they can be
(HANDOFF section 5), each with a small ring at the front holding the circlet's drop:
  C1 a plain gold band with rolled edges
  C2 an open band: two fine rails, 卷草 scrollwork between them
  C3 three twisted gold cords, one above the other
The band's lower edge follows the face's neck rim (a V in front, eased), a little below it, so it
covers the seam and most of the face's pale lower neck; it sits CLEAR off the skin.

Usage: bpy45 python neck_collar_designs.py <out dir> [C1 C2 C3] [tall] [test]
(`tall`: on the tall-neck body, option A; the renders hold Capcom's face and hair: keep them
outside the repo.)
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import robe_designs as rd  # noqa: E402
import miquella_body as mb  # noqa: E402

HEIGHT = 0.018      # m, the band
# Its lower edge follows the face's neck rim, BELOW under it. The rim is a deep V: front 1.419,
# 45 deg 1.448, 60 deg 1.474, sides 1.500, nape 1.510 (measured); under it at the sides there is
# no neck, only the shoulders (our neck base is raised, NECK_LIFT): a level ring, or an eased V,
# lay out over the chest and shoulders. So the band is V-shaped in front, like the circlet's point.
BELOW = 0.002
EASE_PASSES = 3
CLEAR = 0.0018      # m off the skin
STEP = 2.5          # degrees between columns
ROWS = 8
EDGE = 0.0009       # C1's rolled edges
RAIL = 0.0008       # C2's rails
CORD = 0.00048      # C3's strands
TWIST = 0.010       # m per turn of C3's strands
DROP = 0.0085       # the drop's size (the circlet's drop, smaller)


class Neck:
    """The neck's surface (the face's and our body's together), sampled by angle and height."""
    def __init__(self, face_objs, body_objs, G):
        self.G = G
        face = mb.face_geometry(face_objs)
        self.rim = mb.FaceNeck(G, face)
        bm = bmesh.new()
        for o in list(mb.face_outer(face_objs)) + list(body_objs):
            t = bmesh.new()
            t.from_mesh(o.data)
            t.transform(o.matrix_world)
            me = bpy.data.meshes.new("tmp")
            t.to_mesh(me)
            bm.from_mesh(me)
            t.free()
        self.bvh = BVHTree.FromBMesh(bm)
        low = [self.rim.edge(i * STEP) - BELOW for i in range(int(360 / STEP))]
        n = len(low)
        for _ in range(EASE_PASSES):
            low = [(low[i - 1] + 2 * low[i] + low[(i + 1) % n]) / 4 for i in range(n)]
        self.low = low

    def at(self, ang, z, clear=CLEAR):
        hit = mb.ray_hit(self.bvh, self.G, ang, z)
        d = Vector((math.sin(math.radians(ang)), -math.cos(math.radians(ang)), 0.0))
        if not hit:
            return self.rim.to_world(ang, 0.05, z), d
        r, (tr, tz) = hit
        nrm = (d * tz - Vector((0, 0, 1)) * tr).normalized()
        return self.rim.to_world(ang, r, z) + nrm * clear, nrm

    def low_at(self, ang):
        f = (ang % 360) / STEP
        i = int(f)
        t = f - i
        return self.low[i % len(self.low)] * (1 - t) + self.low[(i + 1) % len(self.low)] * t

    def row(self, v, clear=CLEAR, step=STEP):
        """(point, normal) round the neck at height v above the lower edge (a closed loop)."""
        out = []
        a = 0.0
        while a < 360.0 - 1e-6:
            out.append(self.at(a, self.low_at(a) + v, clear))
            a += step
        return out


def front_drop(neck, name):
    """A small ring under the band's front and the circlet's drop hanging from it."""
    p, nrm = neck.at(0.0, neck.low_at(0.0) + 0.001, CLEAR + 0.0015)
    c = p + Vector((0, 0, -0.0058)) + nrm * 0.001
    objs = [rd.ring(f"{name}_ring", c, 0.0055, nrm, 0.0009, rd.COL["gold"])]
    objs.append(rd.droplet(f"{name}_drop", c + Vector((0, 0, -0.0055 - DROP * 0.9)) + nrm * 0.0015, DROP * 0.62, rd.COL["gold"]))
    return objs


def c1(neck):
    rows = [neck.row(HEIGHT * k / ROWS) for k in range(ROWS + 1)]
    bm = bmesh.new()
    grid = [[bm.verts.new(p) for p, _ in row] for row in rows]
    n = len(grid[0])
    for k in range(ROWS):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((grid[k][i], grid[k][j], grid[k + 1][j], grid[k + 1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    band = rd.mesh_object("C1_band", bm, rd.COL["gold"])
    sol = band.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = 0.0007
    objs = [band]
    for k, v in ((0, 0.0), (1, HEIGHT)):
        objs.append(rd.tube(f"C1_edge{k}", [p for p, _ in neck.row(v, CLEAR + 0.0003)], EDGE, rd.COL["gold"], closed=True))
    return objs + front_drop(neck, "C1")


def c2(neck):
    objs = [rd.tube("C2_rail_lo", [p for p, _ in neck.row(0.0)], RAIL, rd.COL["gold"], closed=True),
            rd.tube("C2_rail_hi", [p for p, _ in neck.row(HEIGHT)], RAIL, rd.COL["gold"], closed=True)]
    # the circumference along the lower rail, to lay the scrolls out by length
    fine = 0.5
    base = [p for p, _ in neck.row(0.0, step=fine)]
    run = [0.0]
    for i in range(1, len(base)):
        run.append(run[-1] + (base[i] - base[i - 1]).length)
    L = run[-1] + (base[0] - base[-1]).length

    def pt(sv, v):
        sv %= L
        i = next((k for k in range(len(run) - 1) if run[k + 1] >= sv), len(run) - 2)
        t = (sv - run[i]) / max(run[i + 1] - run[i], 1e-9)
        ang = (i + t) * fine
        return neck.at(ang, neck.low_at(ang) + v)[0]

    lam = 0.026
    reps = max(2, round(L / lam))
    lam = L / reps
    mid, amp = HEIGHT / 2, HEIGHT * 0.12
    N = reps * 24
    objs.append(rd.tube("C2_stem", [pt(L * k / N, mid + amp * math.sin(2 * math.pi * k / 24)) for k in range(N)],
                        RAIL * 0.85, rd.COL["gold"], closed=True))
    vpts, _ = rd.volute(lam * 0.62, 1.7, curl_start=0.22, n=60)
    for m in range(reps * 2):
        sgn = 1 if m % 2 == 0 else -1
        s0 = lam * m / 2
        h = math.radians(55) * sgn
        size = 1.0 if m % 3 else 0.8          # not every curl alike
        pts, radii = [], []
        for q, (x, y) in enumerate(vpts):
            yy0 = -y * sgn
            xx = (x * math.cos(h) - yy0 * math.sin(h)) * size
            yy = (x * math.sin(h) + yy0 * math.cos(h)) * size
            vv = min(max(mid + yy, RAIL * 1.5), HEIGHT - RAIL * 1.5)
            pts.append(pt(s0 + xx, vv))
            radii.append(1.0 - 0.55 * q / len(vpts))
        objs.append(rd.tube(f"C2_c{m}", pts, RAIL * 0.8, rd.COL["gold"], radii=radii))
    return objs + front_drop(neck, "C2")


def c3(neck):
    objs = []
    for c, v in enumerate((HEIGHT * 0.12, HEIGHT * 0.5, HEIGHT * 0.88)):
        core = neck.row(v, CLEAR + CORD * 1.6, step=0.5)
        n = len(core)
        run, acc = [0.0], 0.0
        for i in range(1, n):
            acc += (core[i][0] - core[i - 1][0]).length
            run.append(acc)
        for k in range(3):
            pts = []
            for i, ((p, nrm), sv) in enumerate(zip(core, run)):
                t = (core[(i + 1) % n][0] - core[i - 1][0]).normalized()
                b = t.cross(nrm).normalized()
                a = 2 * math.pi * sv / TWIST + k * 2 * math.pi / 3 + c
                pts.append(p + (nrm * math.cos(a) + b * math.sin(a)) * CORD * 1.6)
            objs.append(rd.tube(f"C3_cord{c}_{k}", pts, CORD, rd.COL["gold"], closed=True))
    return objs + front_drop(neck, "C3")


def render_close(out, stem, test, scale=0.19):
    """robe_designs.render_collar's lights and materials, the camera on the neck (the band is a
    few millimetres thick), the lights at half power (the skin washed out)."""
    sc = bpy.context.scene
    mats = rd.cycles_materials()
    for o in bpy.data.objects:
        if o.type not in ("MESH", "CURVE"):
            continue
        key = min(rd.COL, key=lambda k: sum((a - b) ** 2 for a, b in zip(rd.COL[k], o.color)))
        key = {"light": "gold"}.get(key, key)
        o.data.materials.clear()
        o.data.materials.append(mats[key])
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 24 if test else 96
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Filmic"
    sc.view_settings.look = "Medium High Contrast"
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.30, 0.28, 0.26, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    sc.world = world
    lights = []
    for name, loc, e, size in (("key", (-1.2, -2.2, 2.4), 70, 1.5), ("fill", (1.8, -1.6, 1.4), 22, 2.0),
                               ("rim", (0.5, 2.5, 2.2), 50, 1.5)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size = e, size
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 1.42)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        lights.append(lo)
    s = 360 if test else 900
    sc.render.resolution_x = sc.render.resolution_y = s
    cd = bpy.data.cameras.new("cc")
    cd.type = "ORTHO"
    cd.ortho_scale = scale
    cam = bpy.data.objects.new("cc", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    paths = []
    for name, az, z in (("front", 0, 1.43), ("front34", 35, 1.44), ("side", 80, 1.46)):
        a = math.radians(az)
        cam.location = (4 * math.sin(a), -4 * math.cos(a), z + 0.06)
        cam.rotation_euler = (math.radians(89.1), 0, a)
        p = os.path.join(out, f"{stem}_{name}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    for o in lights + [cam]:
        bpy.data.objects.remove(o, do_unlink=True)
    return paths


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out = os.path.abspath(args[0])
    test = "test" in args
    tall = "tall" in args
    versions = [a for a in args[1:] if a in ("C1", "C2", "C3")] or ["C1", "C2", "C3"]
    os.makedirs(out, exist_ok=True)
    mb.enable_addon()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mb.enable_addon()
    rd.scene_setup(test)
    body_path = rd.BODY.replace("_c_f.mesh", "_c_f_tall.mesh") if tall else rd.BODY
    body, J = rd.import_mesh(body_path, rd.COL["skin"])
    face_objs, _ = rd.import_mesh(rd.FACE, rd.COL["skin"], drop=("eye", "mouth", "lash", "fakeao", "shadow", "cage", "brow"))
    rd.import_mesh(rd.HAIR, rd.COL["hair"])
    circ, _ = rd.import_mesh(rd.CIRCLET, rd.COL["circlet"])
    pivot = Vector((0, 0, 0.128))
    for o in circ:
        o.data.transform(Matrix.Translation(J["Head"] + pivot) @ Matrix.Scale(0.85, 4) @ Matrix.Translation(-pivot))
    neck = Neck(face_objs, body, J)
    stem = "choker" + ("_tall" if tall else "")
    paths = render_close(out, stem + "_none", test)
    for v in versions:
        objs = {"C1": c1, "C2": c2, "C3": c3}[v](neck)
        paths += render_close(out, f"{stem}_{v}", test)
        for o in objs:
            bpy.data.objects.remove(o, do_unlink=True)
    print("rendered", paths)


if __name__ == "__main__":
    main()
