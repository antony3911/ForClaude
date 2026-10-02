"""The insect glaive's three extract orbs in four styles (user, 2026-10-02 night: the orbs are
not settled, look for more designs). Scarlet rot, frost and frenzied flame (DESIGN: the only
colours off gold). The game cannot draw fire, mist or see-through glass on a weapon model, so
these are solid objects that read at a glance; fire and cold breath can come from borrowed
game effects later.

References (Elden Ring): scarlet rot blooms as the Scarlet Aeonia flower (its petals twist and
tighten, then burst) and sprouts buds and fungus; the frenzied flame is a yellow flame that
blazes from the eyes; frost belongs to Miquella's Haligtree in the Consecrated Snowfield.

Each style is build(center, kind, r, light_mats) -> objects, kind in rot / frost / frenzy.
"""
import math
import random

import bpy
from mathutils import Vector

import common as c
import motifs as m
from motifs import V, smoothstep

ESSENCE = {
    "rot": {"base": "#8E0A1E", "glow": "#D0203A", "strength": 0.9, "dark": "#2E040C"},
    "frost": {"base": "#D8EEFF", "glow": "#BFE2FF", "strength": 1.4, "dark": "#5C86B0"},
    "frenzy": {"base": "#FF9A00", "glow": "#FFB21A", "strength": 3.0, "dark": "#2A1000"},
}


def tube(name, pts, radii, mat, bevel):
    return c.curve_tube(name, pts, radii, mat, bevel=bevel, resolution=3)


def ess_mats(kind):
    e = ESSENCE[kind]
    return {"main": c.make_material(f"{kind}_Main", e["base"], roughness=0.25, emission=e["glow"],
                                    strength=e["strength"]),
            "dark": c.make_material(f"{kind}_Dark", e["dark"], roughness=0.5),
            "hot": c.make_material(f"{kind}_Hot", e["glow"], roughness=0.2, emission=e["glow"],
                                   strength=e["strength"] * 2.2)}


def sphere(name, center, r, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=center)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def petal_blade(name, center, d, n, length, width, cup, mat, curl=0.0, wave=0.0, samples=24):
    """A petal leaving `center` along d, cupped toward n, its tip curling by `curl`."""
    n = Vector(n).normalized()
    p0 = center + d * length * 0.05
    p1 = center + d * length * 0.55 + n * length * cup
    p2 = center + d * length * (0.95 - 0.3 * curl) + n * length * (cup * 1.4 + curl * 0.5)
    side = n.cross(d).normalized()
    plane = d.cross(side).normalized()
    return m.path_blade(name, [p0, p1, p2], plane,
                        lambda t: width * (math.sin(math.pi * min(1, 0.08 + t)) ** 0.7)
                        * (1 + wave * math.sin(t * 18)) + 0.0005,
                        lambda t: width * 0.08 + 0.0004, mat, samples=samples, subsurf=1)


def ring_dirs(n, up, phase=0.0, tilt=0.0):
    """n directions around `up`, tilted toward it by `tilt` (radians)."""
    up = Vector(up).normalized()
    u = up.orthogonal().normalized()
    w = up.cross(u)
    out = []
    for k in range(n):
        a = phase + 2 * math.pi * k / n
        out.append(((u * math.cos(a) + w * math.sin(a)) * math.cos(tilt) + up * math.sin(tilt)).normalized())
    return out


def crystal(name, base, d, length, radius, mat):
    """A hexagonal ice prism with a pointed end."""
    d = Vector(d).normalized()
    return m.path_blade(name, [base, base + d * length], d.orthogonal(),
                        lambda t: radius * 2 * (1 - smoothstep((t - 0.72) / 0.28)) + 0.0004,
                        lambda t: radius * 1.75 * (1 - smoothstep((t - 0.72) / 0.28)) + 0.0004,
                        mat, n_sec=6, samples=14, subsurf=0)


# ------------------------------------------------------------------ 1: reliquary cages

def cage(prefix, center, r, lm):
    """An ivory openwork cage: six meridian ribs, a gold equator, droplet finials."""
    objs = []
    ts = [i / 30 for i in range(31)]
    for k in range(6):
        a = 2 * math.pi * k / 6
        pts = [center + V(r * math.sin(math.pi * t) * math.cos(a), r * math.sin(math.pi * t) * math.sin(a),
                          r * 1.15 * math.cos(math.pi * t)) for t in ts]
        objs.append(tube(f"{prefix}_Rib_{k}", pts, [0.7 + 0.3 * math.sin(math.pi * t) for t in ts], lm["ivory"],
                         r * 0.045))
    objs += m.halo(f"{prefix}_Equator", center, r * 1.01, r * 0.035, (0, 0, 1), lm["light"])
    objs += m.halo(f"{prefix}_Top", center + V(0, 0, r * 1.15), r * 0.22, r * 0.04, (0, 0, 1), lm["light"])
    objs += m.droplet(f"{prefix}_Finial", center + V(0, 0, r * 1.32), r * 0.12, (0, 0, 1), lm["light"], stretch=1.2)
    objs += m.droplet(f"{prefix}_Drop", center - V(0, 0, r * 1.3), r * 0.1, (0, 0, -1), lm["light"], stretch=1.6)
    return objs


def rot_bud(prefix, center, r, em):
    objs = []
    for k, d in enumerate(ring_dirs(6, (0, 0, 1), 0.3, math.radians(62))):
        objs += petal_blade(f"{prefix}_{k}", center - V(0, 0, r * 0.5), d, V(0, 0, 1) - d * 0.3, r * 1.25,
                            r * 0.55, 0.12, em["main"], curl=0.25)
    objs += m.droplet(f"{prefix}_Heart", center, r * 0.32, (0, 0, 1), em["hot"], stretch=0.8)
    return objs


def frost_cluster(prefix, center, r, em):
    objs = []
    rng = random.Random(4)
    for k in range(7):
        d = V(0, 0, 1) if k == 0 else Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.4, 1))).normalized()
        objs += crystal(f"{prefix}_{k}", center - d * r * 0.2, d, r * rng.uniform(0.9, 1.35) * (1.3 if k == 0 else 1),
                        r * rng.uniform(0.13, 0.2), em["main"])
    return objs


def frenzy_flame(prefix, center, r, em):
    objs = m.droplet(f"{prefix}_Core", center - V(0, 0, r * 0.25), r * 0.42, (0, 0, 1), em["hot"], stretch=2.2)
    for k, d in enumerate(ring_dirs(3, (0, 0, 1), 0.5, 0.0)):
        base = center - V(0, 0, r * 0.45) + d * r * 0.25
        path = [base, base + d * r * 0.35 + V(0, 0, r * 0.5), base + d * r * 0.15 + V(0, 0, r * 1.05),
                base - d * r * 0.12 + V(0, 0, r * 1.25)]
        objs += m.path_blade(f"{prefix}_Tongue_{k}", path, d.cross(V(0, 0, 1)),
                             lambda t: r * 0.32 * math.sin(math.pi * min(1, 0.15 + t)) ** 0.8 + 0.0004,
                             lambda t: r * 0.06 + 0.0004, em["main"], samples=24)
    return objs


def style_cages(center, kind, r, lm):
    em = ess_mats(kind)
    inner = {"rot": rot_bud, "frost": frost_cluster, "frenzy": frenzy_flame}[kind]
    return cage(f"Cage_{kind}", center, r, lm) + inner(f"In_{kind}", center, r * 0.8, em)


# ------------------------------------------------------------------ 2: flowers

def aeonia(prefix, center, r, em):
    """Scarlet rot's flower: broad cupped petals in two rows, a dark heart of buds."""
    up = V(0, -1, 0.25).normalized()
    objs = []
    for layer, (n, tilt, scale) in enumerate([(6, 18, 1.0), (5, 45, 0.7)]):
        for k, d in enumerate(ring_dirs(n, up, layer * 0.5, math.radians(tilt))):
            objs += petal_blade(f"{prefix}_{layer}_{k}", center, d, up, r * scale, r * 0.62 * scale, 0.18,
                                em["main"], curl=-0.15, wave=0.05)
    for k in range(7):
        a = 2 * math.pi * k / 7
        objs.append(sphere(f"{prefix}_Bud_{k}", center + V(r * 0.13 * math.cos(a), -r * 0.12, r * 0.13 * math.sin(a)),
                           r * 0.075, em["dark"]))
    objs += m.droplet(f"{prefix}_Heart", center + V(0, -r * 0.1, 0), r * 0.1, (0, -1, 0), em["hot"])
    return objs


def frost_lily(prefix, center, r, em):
    up = V(0, -1, 0.3).normalized()
    objs = []
    for k, d in enumerate(ring_dirs(6, up, 0.0, math.radians(52))):
        objs += petal_blade(f"{prefix}_{k}", center, d, d * -0.2 + up, r * 1.2, r * 0.28, 0.2, em["main"], curl=-0.7)
    for k, d in enumerate(ring_dirs(6, up, 0.5, math.radians(62))):
        objs += crystal(f"{prefix}_Stamen_{k}", center, d, r * 0.55, r * 0.035, em["hot"])
    return objs


def frenzy_flower(prefix, center, r, em):
    """Petals like flame tongues around a burning eye (the frenzied flame blazes from the eyes)."""
    up = V(0, -1, 0.15).normalized()
    objs = []
    for k, d in enumerate(ring_dirs(7, up, 0.2, math.radians(32))):
        objs += petal_blade(f"{prefix}_{k}", center, d, up, r * (1.15 if k % 2 == 0 else 0.9), r * 0.3, 0.1,
                            em["main"], curl=0.95, wave=0.25)
    objs.append(sphere(f"{prefix}_Eye", center + V(0, -r * 0.05, 0), r * 0.36, em["hot"], (1.0, 0.45, 0.62)))
    objs.append(sphere(f"{prefix}_Pupil", center + V(0, -r * 0.2, 0), r * 0.13, em["dark"], (0.32, 0.3, 1.25)))
    return objs


def style_flowers(center, kind, r, lm):
    em = ess_mats(kind)
    build = {"rot": aeonia, "frost": frost_lily, "frenzy": frenzy_flower}[kind]
    return build(f"Flower_{kind}", center, r, em) + m.halo(f"Flower_{kind}_Halo", center + V(0, 0.01, 0), r * 1.25,
                                                             r * 0.025, (0, 1, 0), lm["light"])


# ------------------------------------------------------------------ 3: gems in gold settings

def gem_mesh(name, center, r, kind, mat):
    if kind == "frost":
        # A brilliant cut: a deep pavilion and a short crown, eight facets, table toward the viewer.
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=r, radius2=0, depth=r * 1.4,
                                        location=center + V(0, r * 0.7, 0))
        lower = bpy.context.active_object
        lower.rotation_euler = (math.radians(-90), 0, 0)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=r, radius2=r * 0.55, depth=r * 0.42,
                                        location=center - V(0, r * 0.21, 0))
        upper = bpy.context.active_object
        upper.rotation_euler = (math.radians(90), 0, 0)
        objs = [lower, upper]
    else:
        bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=1, location=center)
        o = bpy.context.active_object
        o.scale = (1.0, 0.62, 1.25) if kind == "rot" else (1.0, 0.7, 1.0)
        objs = [o]
    for i, o in enumerate(objs):
        o.name = f"{name}_{i}"
        o.data.materials.append(mat)
    return objs


def setting(prefix, center, r, lm, prongs=6):
    """A gold claw setting with a filigree collar behind the stone and scrolls either side."""
    objs = m.halo(f"{prefix}_Collar", center + V(0, r * 0.25, 0), r * 1.08, r * 0.07, (0, 1, 0), lm["light"])
    objs += m.halo(f"{prefix}_Collar2", center + V(0, r * 0.45, 0), r * 0.8, r * 0.05, (0, 1, 0), lm["light"])
    for k, d in enumerate(ring_dirs(prongs, (0, 1, 0), 0.26)):
        base = center + V(0, r * 0.3, 0) + d * r * 1.05
        tip = center + V(0, -r * 0.45, 0) + d * r * 0.78
        objs.append(tube(f"{prefix}_Prong_{k}", [base, center + d * r * 1.12, tip], [1.0, 0.9, 0.6], lm["light"],
                         r * 0.07))
    xz = m.plane_mapper(center + V(0, r * 0.35, 0), (1, 0, 0), (0, 0, 1))
    for s in (1, -1):
        objs += m.tendril(f"{prefix}_Scroll_{s}", xz, (s * r * 1.05, -r * 0.3), 90 - s * 70, r * 1.6, s * 1.3,
                          r * 0.1, lm, strands=2, strand_mat="light")
    return objs


def style_gems(center, kind, r, lm):
    em = ess_mats(kind)
    objs = gem_mesh(f"Gem_{kind}", center, r * 0.78, kind, em["main"])
    if kind == "frenzy":
        objs += m.droplet("Gem_frenzy_Flame", center + V(0, -r * 0.52, -r * 0.18), r * 0.2, (0, 0, 1), em["hot"],
                          stretch=2.0)
    return objs + setting(f"Set_{kind}", center, r * 0.78, lm)


# ------------------------------------------------------------------ 4: sigil medallions

def butterfly(prefix, center, r, em):
    """A kindred-of-rot butterfly: scarlet wings with dark edges and veins."""
    objs = []
    for s in (1, -1):
        fore = [(0, 0), (s * 0.35, 0.55), (s * 0.95, 0.75), (s * 1.0, 0.45), (s * 0.7, 0.1), (s * 0.1, -0.02)]
        hind = [(0, -0.05), (s * 0.55, -0.15), (s * 0.75, -0.55), (s * 0.45, -0.8), (s * 0.15, -0.45)]
        for tag, outline in (("Fore", fore), ("Hind", hind)):
            smooth = m.catmull([V(x, z, 0) for x, z in outline], 50)
            objs += m.flat_fill(f"{prefix}_{tag}_{s}", [center + V(p.x * r, -0.004, p.y * r) for p in smooth], em["main"])
            edge = [center + V(p.x * r, -0.006, p.y * r) for p in smooth] + [center + V(smooth[0].x * r, -0.006, smooth[0].y * r)]
            objs.append(tube(f"{prefix}_{tag}_Edge_{s}", edge, [1] * len(edge), em["dark"], r * 0.03))
            for k in range(3):
                q = smooth[int((k + 1) * len(smooth) / 4)]
                objs.append(tube(f"{prefix}_{tag}_Vein_{s}_{k}", [center + V(0, -0.006, 0),
                                                                   center + V(q.x * r * 0.85, -0.006, q.y * r * 0.85)],
                                 [1, 0.4], em["dark"], r * 0.018))
    objs.append(tube(f"{prefix}_Body", [center + V(0, -0.008, r * 0.35), center + V(0, -0.008, -r * 0.5)], [1, 0.5],
                     em["dark"], r * 0.06))
    return objs


def snowflake(prefix, center, r, em):
    objs = []
    for k, d in enumerate(ring_dirs(6, (0, 1, 0), 0.0)):
        objs += crystal(f"{prefix}_Arm_{k}", center, d, r * 1.0, r * 0.06, em["main"])
        side = d.cross(V(0, 1, 0))
        for j, (u, ln) in enumerate(((0.45, 0.35), (0.7, 0.22))):
            for sgn in (1, -1):
                objs += crystal(f"{prefix}_Br_{k}_{j}_{sgn}", center + d * r * u, d + side * sgn * 1.2, r * ln,
                                r * 0.04, em["main"])
    objs += m.droplet(f"{prefix}_Heart", center, r * 0.14, (0, -1, 0), em["hot"], stretch=0.3)
    return objs


def flame_eye(prefix, center, r, em):
    eye = [V(-1, 0, 0), V(-0.5, 0.42, 0), V(0, 0.55, 0), V(0.5, 0.42, 0), V(1, 0, 0), V(0.5, -0.42, 0),
           V(0, -0.55, 0), V(-0.5, -0.42, 0)]
    smooth = m.catmull(eye + [eye[0]], 80)
    objs = [tube(f"{prefix}_Lid", [center + V(p.x * r * 0.75, -0.004, p.y * r * 0.75) for p in smooth],
                 [1] * len(smooth), em["main"], r * 0.06)]
    objs.append(sphere(f"{prefix}_Iris", center, r * 0.3, em["hot"], (1, 0.3, 1)))
    objs.append(sphere(f"{prefix}_Pupil", center + V(0, -r * 0.08, 0), r * 0.12, em["dark"], (0.4, 0.3, 1.3)))
    for k, (x, h) in enumerate(((-0.45, 0.75), (0.0, 1.0), (0.45, 0.7))):
        base = center + V(x * r, -0.004, r * 0.35)
        path = [base, base + V(x * r * 0.2 + r * 0.12, 0, r * h * 0.45), base + V(-r * 0.1, 0, r * h * 0.85),
                base + V(r * 0.08, 0, r * h)]
        objs += m.path_blade(f"{prefix}_Flame_{k}", path, (0, 1, 0),
                             lambda t: r * 0.22 * math.sin(math.pi * min(1, 0.1 + t)) ** 0.8 + 0.0004,
                             lambda t: r * 0.05 + 0.0004, em["main"], samples=24)
    return objs


def style_sigils(center, kind, r, lm):
    em = ess_mats(kind)
    build = {"rot": butterfly, "frost": snowflake, "frenzy": flame_eye}[kind]
    objs = build(f"Sigil_{kind}", center, r * 0.85, em)
    objs += m.halo(f"Sigil_{kind}_Ring", center, r * 1.12, r * 0.04, (0, 1, 0), lm["light"])
    objs += m.halo(f"Sigil_{kind}_Ring2", center + V(0, 0.002, 0), r * 1.2, r * 0.018, (0, 1, 0), lm["light"])
    return objs


STYLES = [
    ("1 聖骸燈籠", style_cages, "象牙鏤空籠封著精華：腐敗花苞、冰晶簇、癲火火苗（同大錘燈籠一系列）"),
    ("2 三朵花", style_flowers, "猩紅腐敗之花、霜百合、癲火之花（花心是燃燒的眼睛）；點燈時綻開"),
    ("3 寶石", style_gems, "石榴石帶暗紅脈、八面冰晶、黃水晶裡一簇火，金爪鑲座＋卷草"),
    ("4 紋章", style_sigils, "腐敗蝶、六角冰星、火焰之眼，套在金環裡，一眼認得出是哪一盞"),
]
KINDS = [("rot", "腐敗"), ("frost", "冰凍"), ("frenzy", "癲火")]
