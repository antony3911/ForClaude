"""The lily gunlance for the game (user's picks, 2026-10-03): the lily (gunlance_designs B) and,
growing with the charge, the lily of light at the muzzle (gunlance_lily_charge C), the leaves of
light (gunlance_lily_body C1) and the buds opening into lilies of light (C2); no vines. "Like the
other weapons' charges: an animation, not stepped models" -> every charge part is modelled once,
at its full size (the bind pose), and drawn by bones between a small pose and that one as the
charge builds; the ivory tepals and stamens are modelled at rest and bones throw them back.

build(mats) makes the objects and returns the rig: bones (bind point, small/thrown point, what
drives them, window) and the weights of every part's vertices (by object name: how far along the
part and how far across it a vertex is, between the bones of its stations). All in the
prototype's space (the kit maps it to file space).

Drives (the weapons script): "open" the ivory lily (follows the charge, eases back after it),
"glow" the parts of light (keep their size while they fade after the shot), "wyvern" the rings
of Wyvern's Fire.
"""
import math

import bpy
from mathutils import Quaternion, Vector

import gunlance_designs as gd
import gunlance_lily_body as lb
import gunlance_lily_charge as lc
import motifs as m
from motifs import V, smoothstep

S_LIGHT = (1.2, 2.6)            # lily of light: size at the start of the charge and at full
B_LIGHT = (0.2, 1.0)            #   its bloom (the ivory lily's profile it is drawn from)
K_LEAF = (1.15, 2.3)            # leaves of light
K_SHEATH = (1.1, 1.9)           # the sheath leaves' light
TILT_LEAF = (0.0, 18.0)         # degrees, opening outward
S_BUD = (0.22, 0.4)             # the buds' lilies of light
B_BUD = (0.0, 1.0)
TEPAL_T = (0.3, 0.55, 0.8, 1.0)  # stations along an ivory tepal
LIGHT_T = (0.33, 0.66)           # stations along a tepal of light (both rims; one more bone at the tip)
LEAF_T = (0.5,)                  # stations along a leaf of light (both rims; and the tip)
HALO_BONES = 8
THROAT_R = (0.014, 0.024, 0.036)
FIRE_HALOS = ((0.12, 0.10), (0.22, 0.13), (0.32, 0.16))


# ------------------------------------------------------------------ the shapes, by parameters

def light_tepal(k, s, bloom):
    """Centre line, rims and width of tepal k of the lily of light (as gunlance_lily_charge.option_c)."""
    prof = [(r * s, 1.36 + (z - 1.36) * s) for r, z in gd.lily_profile(False, max(bloom, 0.2))]
    radial, circ = gd.ring_frame(2 * math.pi * (k + 0.5) / 6)
    wmax = 0.062 * s

    def wfn(t):
        return wmax * math.sin(math.pi * min(t / 0.985, 1) ** 0.85) ** 0.6 * (0.35 + 0.65 * smoothstep(t / 0.35))

    center = gd.smooth_path([V(0, 0, z) + radial * r for r, z in prof], 60)
    return center, rims_of(center, circ, wfn), wfn, circ


def rims_of(center, side, wfn, cup=0.1):
    n = len(center)
    left, right = [], []
    for i, p in enumerate(center):
        tan = (center[min(i + 1, n - 1)] - center[max(i - 1, 0)]).normalized()
        nrm = side.cross(tan).normalized()
        w = wfn(i / (n - 1))
        left.append(p - side * (w / 2) + nrm * (cup * w))
        right.append(p + side * (w / 2) + nrm * (cup * w))
    return left, right


def light_stamen(k, s):
    radial, circ = gd.ring_frame(2 * math.pi * k / 6)
    r_end, z_end = 0.056 * s * 1.1, 1.36 + (1.722 - 1.36) * s * 0.92
    return gd.smooth_path([V(0, 0, 1.42) + radial * 0.01, V(0, 0, 1.36 + 0.2 * s) + radial * (0.022 * s),
                           V(0, 0, z_end - 0.04) + radial * (r_end * 0.8), V(0, 0, z_end) + radial * r_end], 30)


def light_halo(s, bloom):
    prof = [(r * s, 1.36 + (z - 1.36) * s) for r, z in gd.lily_profile(False, max(bloom, 0.2))]
    return V(0, 0, prof[5][1] - 0.01), prof[5][0] * 1.12


def halo_point(center, radius, a, tilt=6.0):
    return center + Quaternion(V(1, 0, 0), math.radians(tilt)) @ V(radius * math.cos(a), radius * math.sin(a), 0)


def leaf_path(i, k, tilt):
    """Leaf of light i (0-3 on the stem, 4-6 the sheath), its centre line and width."""
    if i < 4:
        z, a = lb.LEAVES[i]
        radial, circ = gd.ring_frame(a)
        length = 0.25 - 0.022 * i
        base = V(0, 0, z) + radial * 0.012
        path = [base, V(0, 0, z + 0.35 * length) + radial * 0.05, V(0, 0, z + 0.7 * length) + radial * 0.083,
                V(0, 0, z + length) + radial * 0.098]

        def wfn(t, k=k):
            return 0.026 * k * math.sin(math.pi * min(t / 0.98, 1) ** 0.6) ** 0.8
    else:
        radial, circ = gd.ring_frame(2 * math.pi * (i - 4) / 3 + 0.5)
        base = V(0, 0, lb.SHEATH[0][1]) + radial * lb.SHEATH[0][0]
        path = [V(0, 0, zz) + radial * r for r, zz in lb.SHEATH]

        def wfn(t, k=k):
            return 0.055 * k * math.sin(math.pi * min(t / 0.97, 1) ** 0.75) ** 0.7
    q = Quaternion(circ, math.radians(tilt))
    path = [base + q @ ((p - base) * k) for p in path]
    return path, wfn, circ


def bud_frame(i):
    z = 1.05 + 0.055 * i
    radial, _ = gd.ring_frame(0.3 + lb.GOLDEN * i)
    reach = 0.066 - 0.006 * i
    d = (radial * 0.38 + V(0, 0, 1)).normalized()
    return V(0, 0, z + 0.05) + radial * reach + d * 0.004, d


def bud_tepal(i, k, s, bloom):
    base, d = bud_frame(i)
    prof = [(r * s, (zz - 1.36) * s) for r, zz in gd.lily_profile(False, bloom)]
    q = V(0, 0, 1).rotation_difference(d)
    radial, _ = gd.ring_frame(0.3 * i + 2 * math.pi * k / 6)
    return gd.smooth_path([base + q @ (radial * r + V(0, 0, h)) for r, h in prof], 50)


def ivory_tepal(k, bloom):
    radial, _ = gd.ring_frame(2 * math.pi * k / 6)
    sc = 0.93 if k % 2 else 1.0
    return gd.smooth_path([V(0, 0, z) + radial * (r * sc) for r, z in gd.lily_profile(False, bloom)], 60)


def ivory_stamen(k, b):
    radial, _ = gd.ring_frame(2 * math.pi * (k + 0.5) / 6)
    r_end, z_end = 0.056 + 0.034 * b, 1.722 + 0.023 * b
    return gd.smooth_path([V(0, 0, 1.40) + radial * 0.008, V(0, 0, 1.53) + radial * 0.022,
                           V(0, 0, 1.65) + radial * (r_end * 0.75), V(0, 0, z_end) + radial * r_end], 30)


def at(pts, t):
    return pts[min(len(pts) - 1, max(0, round(t * (len(pts) - 1))))]


# ------------------------------------------------------------------ weights

def project(pts, co):
    """(t along the polyline, the nearest point) for a point."""
    best, bt, bp = None, 0.0, pts[0]
    total = sum((pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)) or 1.0
    acc = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        L = ab.length
        u = 0.0 if L < 1e-9 else max(0.0, min(1.0, (co - a).dot(ab) / (L * L)))
        p = a + ab * u
        d = (co - p).length
        if best is None or d < best:
            best, bt, bp = d, (acc + u * L) / total, p
        acc += L
    return bt, bp


def hat(stations, t):
    """Linear weights of t between stations (sorted, the first one 0 = the part's fixed root)."""
    out = [0.0] * len(stations)
    if t >= stations[-1]:
        out[-1] = 1.0
        return out
    for i in range(len(stations) - 1):
        a, b = stations[i], stations[i + 1]
        if a <= t <= b:
            f = (t - a) / (b - a)
            out[i], out[i + 1] = 1 - f, f
            return out
    out[0] = 1.0
    return out


def merged(pairs):
    acc = {}
    for bone, w in pairs:
        if w > 1e-4:
            acc[bone] = acc.get(bone, 0.0) + w
    total = sum(acc.values()) or 1.0
    return [(b, w / total) for b, w in acc.items()]


# ------------------------------------------------------------------ build

def build(mats):
    """The lily at rest and the charge parts at full size; returns (objects, rig)."""
    rng = __import__("random").Random(7)
    objs = []
    before = set(bpy.data.objects)
    gd.design_b(mats, rng, False)
    lc.option_c(mats, 3, B_LIGHT[1])
    lb.leaves_of_light(mats, 3)
    lb.bud_lilies(mats, 3)
    for j, r in enumerate(THROAT_R):
        gd.sphere(f"Throat_{j + 1}", (0, 0, lc.THROAT), r, mats["phial_lit"])
    for j, (dz, r) in enumerate(FIRE_HALOS):
        m.halo(f"Fire_Halo_{j}", (0, 0, 1.60 + dz), r, 0.0048 - 0.0008 * j, (0, 0, 1), mats["light"],
               tilt_deg=6 * (-1) ** j, tilt_axis=(1, 0, 0))
    objs = [o for o in bpy.data.objects if o not in before and o.type in ("MESH", "CURVE")]
    rig = Rig()
    rig.setup()
    return objs, rig


class Rig:
    """Bones: name -> dict(bind, base (small pose) or alt (thrown pose), drive, win). Weights
    by object name."""

    def __init__(self):
        self.bones = {}
        self.parts = {}                  # object name prefix -> weight function (co -> pairs)

    def bone(self, name, bind, other, side, drive, win=(0.0, 1.0)):
        self.bones[name] = {"bind": bind, side: other, "drive": drive, "win": win}
        return name

    def setup(self):
        s0, s1 = S_LIGHT
        # Ivory tepals: stations along each, thrown back (alt).
        for k in range(6):
            rest, thrown = ivory_tepal(k, 0.0), ivory_tepal(k, 1.0)
            names = [self.bone(f"MQ_Tepal{k}_{j + 1}", at(rest, t), at(thrown, t), "alt", "open")
                     for j, t in enumerate(TEPAL_T)]
            stations = (0.0,) + TEPAL_T

            def wf(co, rest=rest, names=names, stations=stations):
                t, _ = project(rest, co)
                return merged(zip(["Base"] + names, hat(stations, t)))
            for prefix in (f"B_Tepal_{k}", f"B_Tepal_Rim_{k}_", f"B_Tepal_Mid_{k}"):
                self.parts[prefix] = wf
            # its stamen
            fr, ft = ivory_stamen(k, 0.0), ivory_stamen(k, 1.0)
            bn = self.bone(f"MQ_Stamen{k}", fr[-1], ft[-1], "alt", "open")
            self.parts[f"B_Stamen_{k}"] = lambda co, fr=fr, bn=bn: merged(
                [("Base", 1 - project(fr, co)[0]), (bn, project(fr, co)[0])])
            self.parts[f"B_Anther_{k}"] = lambda co, bn=bn: [(bn, 1.0)]
        self.bone("MQ_Mouth", V(0, 0, 1.655), V(0, 0, 1.586), "alt", "open")
        self.parts["B_Mouth_Halo"] = lambda co: [("MQ_Mouth", 1.0)]
        # The lily of light: both rims at two stations, the tip; small pose = base.
        for k in range(6):
            c1, (l1, r1), w1, circ = light_tepal(k, s1, B_LIGHT[1])
            c0, (l0, r0), _, _ = light_tepal(k, s0, B_LIGHT[0])
            names = []
            for j, t in enumerate(LIGHT_T):
                names.append((self.bone(f"MQ_LL{k}_{j + 1}L", at(l1, t), at(l0, t), "base", "glow"),
                              self.bone(f"MQ_LL{k}_{j + 1}R", at(r1, t), at(r0, t), "base", "glow")))
            tip = self.bone(f"MQ_LL{k}_T", c1[-1], c0[-1], "base", "glow")

            def wf(co, c1=c1, w1=w1, circ=circ, names=names, tip=tip):
                t, p = project(c1, co)
                half = max(w1(t) / 2, 1e-4)
                u = max(-1.0, min(1.0, (co - p).dot(circ) / half))
                h = hat((0.0,) + LIGHT_T + (1.0,), t)
                pairs = [("Base", h[0]), (tip, h[-1])]
                for j, (nl, nr) in enumerate(names):
                    pairs += [(nl, h[j + 1] * (1 - u) / 2), (nr, h[j + 1] * (1 + u) / 2)]
                return merged(pairs)
            for prefix in (f"C_Rim_{k}_", f"C_Mid_{k}", f"C_Vein_{k}_"):
                self.parts[prefix] = wf
            f1, f0 = light_stamen(k, s1), light_stamen(k, s0)
            bn = self.bone(f"MQ_LLS{k}", f1[-1], f0[-1], "base", "glow")
            self.parts[f"C_Stamen_{k}"] = lambda co, f1=f1, bn=bn: merged(
                [("Base", 1 - project(f1, co)[0]), (bn, project(f1, co)[0])])
            self.parts[f"C_Anther_{k}"] = lambda co, bn=bn: [(bn, 1.0)]
        hc1, hr1 = light_halo(s1, B_LIGHT[1])
        hc0, hr0 = light_halo(s0, B_LIGHT[0])
        hnames = [self.bone(f"MQ_LLH{i}", halo_point(hc1, hr1, 2 * math.pi * i / HALO_BONES),
                            halo_point(hc0, hr0, 2 * math.pi * i / HALO_BONES), "base", "glow")
                  for i in range(HALO_BONES)]

        def halo_wf(co):
            local = Quaternion(V(1, 0, 0), math.radians(-6.0)) @ (co - hc1)
            a = math.atan2(local.y, local.x) % (2 * math.pi)
            f = a / (2 * math.pi / HALO_BONES)
            i = int(f) % HALO_BONES
            g = f - int(f)
            return merged([(hnames[i], 1 - g), (hnames[(i + 1) % HALO_BONES], g)])
        self.parts["C_Halo"] = halo_wf
        # Leaves of light: both rims halfway, the tip; their root stays on the stem.
        for i in range(7):
            k1, k0 = (K_LEAF if i < 4 else K_SHEATH)
            p1, w1, circ = leaf_path(i, k1, TILT_LEAF[1])
            p0, _, _ = leaf_path(i, k0, TILT_LEAF[0])
            c1, c0 = gd.smooth_path(p1, 50), gd.smooth_path(p0, 50)
            (l1, r1), (l0, r0) = rims_of(c1, circ, w1), rims_of(c0, circ, leaf_path(i, k0, 0.0)[1])
            names = [(self.bone(f"MQ_LF{i}_{j + 1}L", at(l1, t), at(l0, t), "base", "glow"),
                      self.bone(f"MQ_LF{i}_{j + 1}R", at(r1, t), at(r0, t), "base", "glow"))
                     for j, t in enumerate(LEAF_T)]
            tip = self.bone(f"MQ_LF{i}_T", c1[-1], c0[-1], "base", "glow")

            def wf(co, c1=c1, w1=w1, circ=circ, names=names, tip=tip):
                t, p = project(c1, co)
                half = max(w1(t) / 2, 1e-4)
                u = max(-1.0, min(1.0, (co - p).dot(circ) / half))
                h = hat((0.0,) + LEAF_T + (1.0,), t)
                pairs = [("Base", h[0]), (tip, h[-1])]
                for j, (nl, nr) in enumerate(names):
                    pairs += [(nl, h[j + 1] * (1 - u) / 2), (nr, h[j + 1] * (1 + u) / 2)]
                return merged(pairs)
            self.parts[f"C1_Leaf_{i}_" if i < 4 else f"C1_Sheath_{i - 4}_"] = wf
        # The buds' lilies of light: a bone at each tepal's tip (their width stays).
        for i in range(5):
            for k in range(6):
                t1, t0 = bud_tepal(i, k, S_BUD[1], B_BUD[1]), bud_tepal(i, k, S_BUD[0], B_BUD[0])
                bn = self.bone(f"MQ_BL{i}_{k}", t1[-1], t0[-1], "base", "glow")
                wf = (lambda co, t1=t1, bn=bn: merged([("Base", 1 - project(t1, co)[0]), (bn, project(t1, co)[0])]))
                self.parts[f"C2_Lily_{i}_{k}_"] = wf
                self.parts[f"C2_Lily_{i}_Stamen_{k}"] = wf
                self.parts[f"C2_Lily_{i}_Anther_{k}"] = lambda co, bn=bn: [(bn, 1.0)]

    def part_fn(self, name):
        """The weight function of object `name` (co in prototype space -> [(bone, w)]), or None:
        the object stays on Base."""
        base = name.split(".")[0]
        best = None
        for prefix, wf in self.parts.items():
            if base == prefix or (prefix.endswith("_") and base.startswith(prefix)):
                if best is None or len(prefix) > len(best[0]):
                    best = (prefix, wf)
        return best[1] if best else None


def material_of(name):
    """Game material of the lily's parts by object name (None: by its Blender material)."""
    base = name.split(".")[0]
    if base.startswith(("C_Rim_", "C_Mid_", "C_Vein_", "C_Stamen_", "C_Anther_", "C_Halo")):
        return "MiquellaLilyLight"
    if base.startswith(("C1_Leaf_", "C1_Sheath_")):
        return "MiquellaLeafLight"
    if base.startswith("C2_Lily_"):
        return "MiquellaBudLight"
    if base.startswith("Throat_"):
        return f"MiquellaThroat{base.split('_')[1]}"
    if base.startswith("Fire_Halo_"):
        return "MiquellaFireHalo"
    if base.startswith("B_Shell_"):
        return f"MiquellaGauge{int(base.split('_')[2]) + 1}"
    return None


# Windows of the charge (its progress 0-1) in which the parts of light fade in; the throat's
# light grows by three spheres; Wyvern's Fire's rings come at the very end of its wind-up.
FADES = (("MiquellaLilyLight", "glow", (0.0, 0.12)), ("MiquellaBudLight", "glow", (0.0, 0.15)),
         ("MiquellaLeafLight", "glow", (0.04, 0.2)), ("MiquellaThroat1", "glow", (0.0, 0.1)),
         ("MiquellaThroat2", "glow", (0.3, 0.55)), ("MiquellaThroat3", "glow", (0.6, 0.85)),
         ("MiquellaFireHalo", "wyvern", (0.75, 0.95)))
