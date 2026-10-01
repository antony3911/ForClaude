"""Build a game kit (.mesh + .mdf2) for a Miquella light weapon from its prototype.

Weapons: see WEAPONS (shields and the kinsect are kits of their own). Same result as the dual blades pipeline
(build_game_kit.py + fit_dual_blades.py) in one pass, on Windows:
- builds the prototype geometry, lowers its resolution and joins it per game material;
- places it the way the game's originals are placed (file space, measured from the
  originals, see the kit READMEs): great sword along +Z with the hand just below the guard
  and the edge toward -X; light bowgun along +Z with up = +Y and the bore 0.19 below the origin;
- takes the skeleton from an original and moves its effect bones (blade tip, muzzle) onto
  our model, every vertex on Base except the floating rings: each has its own bone (MQ_*,
  pivot at the ring's center) that the weapons script moves every frame;
- copies the materials from the dual blades kit .mdf2 (current game layout, our textures),
  so the textures are the dual blades' (Art/Model/MiquellaLight/DualBlades/tex).

Usage: python build_weapon_kit.py <weapon, see WEAPONS> <kit dir> <original *_0.mesh.241111606> <dual blades .mdf2.45>
Requires bpy 4.5 with RE Mesh Editor in the user addons dir. The originals are only read.
"""
import copy
import json
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
MESH_EXT, MDF_EXT = ".241111606", ".45"
# File space -> Blender space as RE Mesh Editor writes it (rotate90): (x, y, z) -> (x, -z, y).
FILE_TO_BLENDER = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def log(msg):
    print(f"[kit] {msg}", flush=True)


# ------------------------------------------------------------------ weapons

def great_sword():
    """Grip lengthened from 0.36 to 0.48 so both hands fit (the originals' handles reach
    about 0.8 m below the hand); scaled 1.6x so the blade is ~1.9 m like the originals
    (2.0-2.2 m) but stays slender; turned 180 degrees about Z: the originals' single edges
    and the long sword's curve put the edge on -X, ours was on +X."""
    import arsenal
    gt, k = 0.48, 1.6
    objs, mats, tip = arsenal.great_sword(gt=gt, render=False)
    hand = Vector((0, 0, gt - 0.04))
    to_file = Matrix.Scale(k, 4) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation(-hand)
    return {
        "name": "wp_miquella_gs", "rel": "Art/Model/MiquellaLight/GreatSword",
        "objects": objs, "to_file": to_file,
        "bones": {"VFX_Attack": to_file @ Vector(tip)},
        "materials": {"Blade_Light": "MiquellaBlade", "Light": "MiquellaGlow", "Ivory": "MiquellaIvory",
                      "Blade_Core": "MiquellaTemper", "Membrane": "MiquellaGlow"},
        "by_name": {},
        # The rings floating on the spine swing like loose rings, the big ring around the
        # blade hovers like the bowgun's (weapons script).
        "floaters": {**{f"Spine_Ring_{i}": f"MQ_Ring{i}" for i in range(3)}, "Blade_Halo": "MQ_BladeHalo"},
    }


LS_BANDS = 8


def split_bands(subs, mat, prefix, n):
    """The sub-mesh on `mat` cut into n pieces along file +Z (by face centre), materials
    prefix1..n; the subs renumbered."""
    import bmesh
    src = next((o for o in subs if o.name.split("__", 1)[1] == mat), None)
    if src is None:
        log(f"  bands: no {mat}")
        return subs
    inv = FILE_TO_BLENDER.inverted()
    zs = [(inv @ v.co).z for v in src.data.vertices]
    z0, z1 = min(zs), max(zs)
    out = [o for o in subs if o is not src]
    for k in range(n):
        o = src.copy()
        o.data = src.data.copy()
        for col in src.users_collection:
            col.objects.link(o)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        lo, hi = k / n, (k + 1) / n
        kill = []
        for f in bm.faces:
            u = ((inv @ f.calc_center_median()).z - z0) / max(z1 - z0, 1e-6)
            if not (lo <= u < hi or (k == n - 1 and u >= hi)):
                kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(o.data)
        bm.free()
        name = f"{prefix}{k + 1}"
        o.data.materials.clear()
        o.data.materials.append(bpy.data.materials.get(name) or bpy.data.materials.new(name))
        o.name = f"Band_tmp_{k}__{name}"
        log(f"  band {name}: {tris(o)} tris")
        out.append(o)
    bpy.data.objects.remove(src, do_unlink=True)
    for i, o in enumerate(out):
        o.name = f"tmp_{i}__{o.name.split('__', 1)[1]}"
    for i, o in enumerate(out):
        o.name = f"Group_0_Sub_{i}__{o.name.split('__', 1)[1]}"
    return out


def light_bowgun():
    """Prototype axes: +Y muzzle, +Z up. Scaled 1.6x (originals are ~1.5 m long, ours
    0.93 m); bore placed 0.19 below the origin (the originals' muzzle bones sit at y -0.16
    to -0.23; their origin is on top of the receiver); moved back 0.1 so the pistol grip
    sits where the originals' grips do, about 0.3 behind the origin. The three lit drops
    over the barrel get their own materials, to work as the rapid-fire gauge later."""
    import light_bowgun as lb
    import bowgun as hb
    lb.build()
    k, bore_y, back = 1.6, -0.19, -0.10
    axes = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))      # x->-x, z->y, y->z
    to_file = (Matrix.Translation((0, bore_y, back)) @ Matrix.Scale(k, 4) @ axes
               @ Matrix.Translation((0, 0, -hb.CONDUIT_Z)))
    muzzle = to_file @ Vector((0, hb.MUZZLE + 0.01, hb.CONDUIT_Z))
    by_name = {}
    for i in range(3):
        by_name[f"Barrel_Phial_{i}"] = f"MiquellaGauge{i + 1}"
        by_name[f"Barrel_Phial_Halo_{i}"] = f"MiquellaGauge{i + 1}"
    return {
        "name": "wp_miquella_lbg", "rel": "Art/Model/MiquellaLight/LightBowgun",
        "objects": [o for o in bpy.data.objects if o.type in ("MESH", "CURVE")], "to_file": to_file,
        "bones": {"VFX_Fire": muzzle, "VFX_FireLong": muzzle, "VFX_FireSuppressor": muzzle},
        "materials": {"Ivory": "MiquellaIvory", "Light": "MiquellaGlow", "Beam": "MiquellaBlade"},
        "by_name": by_name,
        # The rings along the beam hover as if held by magnetism (weapons script).
        "floaters": {**{f"Rail_Halo_{i}": f"MQ_Halo{i}" for i in range(4)}, "Muzzle_Halo": "MQ_Halo4"},
    }


def long_sword():
    """Handle lengthened from 0.34 to 0.42 and scaled 1.9x: the originals' blades reach
    2.17-2.2 m above the hand and their handles 0.76 m below it (ours: 2.13 and 0.77);
    hand just below the collar; turned 180 degrees about Z so the edge is on -X and the
    tip curves toward +X like the originals' (VFX_Attack x +0.07 to +0.13)."""
    import long_sword as ls
    ls.HANDLE_LEN = 0.42
    k = 1.9
    objs, mats, tip = ls.build()
    hand = Vector((0, 0, -0.04))
    to_file = Matrix.Scale(k, 4) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation(-hand)
    return {
        "name": "wp_miquella_ls", "rel": "Art/Model/MiquellaLight/LongSword",
        "objects": objs, "to_file": to_file,
        "bones": {"VFX_Attack": to_file @ Vector(tip)},
        "materials": {"Blade_Light": "MiquellaBlade", "Light": "MiquellaGlow", "Ivory": "MiquellaIvory",
                      "Hamon": "MiquellaTemper"},
        "by_name": {},
        # The two rings in place of a tsuba hover like the bowgun's (weapons script).
        "floaters": {"Tsuba_Halo": "MQ_Tsuba0", "Tsuba_Halo_Inner": "MQ_Tsuba1"},
        # The temper line in 8 pieces root -> tip, a material each (MiquellaBand1-8): the weapons
        # script runs the band of light along them (the material's own moving glow, MoveEmit,
        # showed nothing in the game, user 2026-10-02).
        "bands": ("MiquellaTemper", "MiquellaBand", LS_BANDS),
    }


# ---- prototypes from arsenal.py, sword_shield.py and bowgun.py

# Our material names -> game materials, shared by these prototypes. Faint membranes (energy
# shields, the charge blade's axe sheet) are left out: the game's weapon shaders only cut out,
# so they would be solid gold plates; the open-work look stays (DESIGN: light, airy).
ARSENAL_MATERIALS = {"Ivory": "MiquellaIvory", "Light": "MiquellaGlow", "Blade_Light": "MiquellaBlade",
                     "Blade_Core": "MiquellaTemper", "Sun": "MiquellaGlow", "Face_Membrane": "MiquellaGlow",
                     "Sigil_Light": "MiquellaGlow", "Droplet": "MiquellaGlow", "Phial_Lit": "MiquellaGlow",
                     "Wing_Membrane": "MiquellaBlade", "Unalloyed_Gold": "MiquellaGold"}
SKIP_MATERIALS = {"Membrane", "Shield_Membrane", "Axe_Membrane"}
# Our shields face -Y; the originals' fronts face +Y: their grips are narrow parts on -Y, the
# plates widest at y +0.05..+0.15 (measured per depth). Ours sit at the plates' depth, off the arm.
SHIELD_TURN = 180.0


def capture(fn, *args, **kw):
    """Run a prototype builder without its renders and backdrop; returns every part it made."""
    import motifs
    import sword_shield
    saved = motifs.render_sheets, sword_shield.add_backdrop
    motifs.render_sheets = lambda *a, **k: None
    sword_shield.add_backdrop = lambda *a, **k: None
    try:
        fn(*args, **kw)
    finally:
        motifs.render_sheets, sword_shield.add_backdrop = saved
    # Parents moved or scaled after their children were linked: update world matrices first.
    bpy.context.view_layer.update()
    return [o for o in bpy.data.objects if o.type in ("MESH", "CURVE")]


def subtree(root_name):
    root = bpy.data.objects[root_name]
    return [o for o in [root] + list(root.children_recursive) if o.type in ("MESH", "CURVE")]


def top_z(objs):
    return max((o.matrix_world @ Vector(b)).z for o in objs for b in o.bound_box)


def placed(name, rel, objs, to_file, bones, **extra):
    spec = {"name": name, "rel": rel, "objects": objs, "to_file": to_file, "bones": bones,
            "materials": ARSENAL_MATERIALS, "skip_materials": SKIP_MATERIALS, "by_name": {}, "floaters": {}}
    spec.update(extra)
    return spec


def upright(k, hand, turn=0.0):
    """Blade or shaft along +Z like the originals: hand at the origin, scaled k, turned about Z."""
    return Matrix.Scale(k, 4) @ Matrix.Rotation(math.radians(turn), 4, "Z") @ Matrix.Translation(-Vector(hand))


def shield_place(root_name, k, center_file, turn=SHIELD_TURN):
    """An energy shield on its own (the sub weapon file, _1), its center at center_file."""
    center = bpy.data.objects[root_name].matrix_world.translation.copy()
    return (Matrix.Translation(center_file) @ Matrix.Scale(k, 4) @ Matrix.Rotation(math.radians(turn), 4, "Z")
            @ Matrix.Translation(-center))


def sns_sword():
    """Sword & shield, the sword (it01 _0): the dual blades' sword with sword_shield.py's 0.72
    blade, scaled 1.25 so the tip is ~1.0 m above the hand like the originals (VFX_Attack 0.98)."""
    import blades
    import common as c
    ivory = c.make_material("Ivory", c.PALETTE["ivory"], roughness=0.32, coat=0.3,
                            emission=c.PALETTE["glow"], strength=0.05, subsurface=0.15)
    drop = c.make_material("Droplet", c.PALETTE["glow"], roughness=0.08, coat=0.6,
                           emission=c.PALETTE["glow"], strength=1.5)
    blade = blades.blade_material("Blade_Light", 0.35)
    core = c.make_material("Blade_Core", c.PALETTE["blade_core"], roughness=0.1,
                           emission=c.PALETTE["blade_core"], strength=0.8)
    blades.BLADE_LEN = 0.72
    blades.build_sword("Sword", ivory, drop, blade, core, seed=4)
    to_file = upright(1.25, (0, 0, (blades.GRIP_BOTTOM + blades.GUARD_Z) / 2))
    tip = Vector((0, 0, blades.GUARD_Z + blades.BLADE_LEN))
    return placed("wp_miquella_sns", "Art/Model/MiquellaLight/SwordShield", subtree("Sword"), to_file,
                  {"VFX_Attack": to_file @ tip})


def sns_shield():
    """Sword & shield, the shield (it01 _1): the tree-sigil energy shield, 0.6 m across like the
    originals (0.58), centered where theirs is (z -0.07); halo, sigil and pods, no membrane."""
    import common as c
    import sword_shield as ss
    ivory = c.make_material("Ivory", c.PALETTE["ivory"], roughness=0.32, coat=0.3,
                            emission=c.PALETTE["glow"], strength=0.05, subsurface=0.15)
    glow = c.make_material("Sigil_Light", c.PALETTE["blade_core"], roughness=0.1,
                           emission=c.PALETTE["blade_core"], strength=1.2)
    ss.shield(glow, ss.membrane_material(0.6), ivory)
    bpy.context.view_layer.update()
    to_file = shield_place("EnergyShield", 1.1, (0, 0.14, -0.07))
    return placed("wp_miquella_sns_shield", "Art/Model/MiquellaLight/SwordShield", subtree("EnergyShield"),
                  to_file, {})


def sns_shield_membrane(variant):
    """The sword & shield's shield with its film of light back, on a translucent game material
    (MEMBRANES): looks A, B, C to compare in the game."""
    spec = sns_shield()
    spec["name"] = f"wp_miquella_sns_shield_{variant}"
    spec["membrane"] = variant
    spec["materials"] = dict(ARSENAL_MATERIALS, Membrane="MiquellaMembrane", Shield_Membrane="MiquellaMembrane")
    spec["skip_materials"] = SKIP_MATERIALS - {"Membrane", "Shield_Membrane"}
    return spec


# Film D (2026-10-02, after A-C: A, B invisible, C hard-edged in patches): our own glowing
# material, made see-through by a partial Dissolve (scattered pixels the game's anti-aliasing
# blends, as when the dual blades' side blades fade in), in concentric bands that thin out
# toward the rim so the edge softens away: (inner, outer radius as a fraction, Dissolve).
FILM_BANDS = [(0.0, 0.35, 0.42), (0.35, 0.6, 0.36), (0.6, 0.78, 0.28), (0.78, 0.9, 0.18), (0.9, 1.0, 0.08)]


def film_bands(name, radius, mat_prefix, n_seg=96):
    """Flat annuli in the local XY plane, both sides (two layers 0.002 apart, the back flipped)."""
    import bmesh
    objs = []
    for k, (f0, f1, _) in enumerate(FILM_BANDS):
        bm = bmesh.new()
        for z, flip in ((0.001, False), (-0.001, True)):
            inner, outer = [], []
            for i in range(n_seg):
                a = 2 * math.pi * i / n_seg
                d = Vector((math.cos(a), math.sin(a), 0))
                inner.append(bm.verts.new(d * radius * max(f0, 0.004) + Vector((0, 0, z))))
                outer.append(bm.verts.new(d * radius * f1 + Vector((0, 0, z))))
            for i in range(n_seg):
                j = (i + 1) % n_seg
                quad = (inner[i], outer[i], outer[j], inner[j])
                bm.faces.new(tuple(reversed(quad)) if flip else quad)
        me = bpy.data.meshes.new(f"{name}_{k}")
        bm.to_mesh(me)
        bm.free()
        me.uv_layers.new(name="UVMap")
        o = bpy.data.objects.new(f"{name}_{k}", me)
        bpy.context.scene.collection.objects.link(o)
        mat = bpy.data.materials.get(f"{mat_prefix}{k + 1}") or bpy.data.materials.new(f"{mat_prefix}{k + 1}")
        me.materials.append(mat)
        objs.append(o)
    return objs


def sns_shield_film():
    """The sword & shield's shield with film D in place of its membrane disc."""
    spec = sns_shield()
    disc = bpy.data.objects["Shield_Membrane"]
    radius = max(Vector(v.co.xy).length for v in disc.data.vertices)
    for o in film_bands("Shield_Film", radius, "Film_"):
        o.parent = disc.parent
        o.matrix_world = disc.matrix_world.copy()
    bpy.data.objects.remove(disc, do_unlink=True)
    bpy.context.view_layer.update()
    spec["objects"] = subtree("EnergyShield")
    spec["name"] = "wp_miquella_sns_shield_film"
    spec["materials"] = dict(ARSENAL_MATERIALS, **{f"Film_{k + 1}": f"MiquellaFilm{k + 1}" for k in range(len(FILM_BANDS))})
    return spec


def hammer():
    """Hand 0.1 above the pommel; scaled 1.4: the head's center 1.32 m above the hand, the
    striking faces 0.58 apart (originals: head up to 1.65, 1.1 wide; ours stays slender)."""
    import arsenal
    import motifs
    objs = capture(lambda: (arsenal.hammer(), arsenal.hammer_charge_rings(motifs.materials())))
    to_file = upright(1.4, (0, 0, 0.1))
    # The charge rings: one material per level, hidden until the weapons script fades them in.
    by_name = {f"Charge_Ring_{i}_{side}": f"MiquellaCharge{level}"
               for i, (level, _, _) in enumerate(arsenal.HAMMER_CHARGE) for side in "LR"}
    return placed("wp_miquella_hm", "Art/Model/MiquellaLight/Hammer", objs, to_file,
                  {"VFX_Attack": to_file @ Vector((0, 0, 1.04 + 0.14))},
                  floaters={"Belt_Halo": "MQ_BeltHalo"}, by_name=by_name)


def hunting_horn():
    """Hand 0.1 above the pommel; scaled 1.9: the lyre's top halo near the originals'
    VFX_Sound (2.07)."""
    import arsenal
    # The sound rings in front of the crown are the playing effect, not part of the weapon.
    objs = [o for o in capture(arsenal.hunting_horn) if not o.name.startswith("Sound_Ring")]
    to_file = upright(1.9, (0, 0, 0.1))
    top = to_file @ Vector((0, 0, 0.62 + 0.42))
    return placed("wp_miquella_hh", "Art/Model/MiquellaLight/HuntingHorn", objs, to_file,
                  {"VFX_Sound": top, "VFX_Attack": top})


def lance():
    """Hand mid-grip; scaled 1.7: the point 3.05 m above the hand (originals 3.08). The energy
    shield is lance_shield."""
    import arsenal
    import motifs
    objs = capture(lambda: (arsenal.lance(), arsenal.lance_charge_parts(motifs.materials())))
    shield = set(subtree("EnergyShield"))
    to_file = upright(1.7, (0, 0, 0.17))
    # Charge: the cone of rings a level at a time, the point's longer blade at full charge.
    levels = arsenal.LANCE_CHARGE[5]
    by_name = {f"Charge_Ring_{k}": f"MiquellaCharge{lv}" for k, lv in enumerate(levels)}
    by_name.update({"Point_Flare_A": "MiquellaChargeTip", "Point_Flare_B": "MiquellaChargeTip"})
    return placed("wp_miquella_ln", "Art/Model/MiquellaLight/Lance", [o for o in objs if o not in shield],
                  to_file, {}, by_name=by_name)


def lance_shield():
    """The lance's tall energy shield (it06 _1), same scale as the lance: 1.1 x 1.3 m
    (originals 0.85 x 1.4), centered like theirs."""
    import arsenal
    capture(arsenal.lance)
    to_file = shield_place("EnergyShield", 1.7, (0.08, 0.08, 0.04))
    return placed("wp_miquella_ln_shield", "Art/Model/MiquellaLight/Lance", subtree("EnergyShield"), to_file, {})


def gunlance():
    """Hand mid-grip; scaled 1.3: muzzle 2.04 m above the hand (originals: VFX_Fire 1.66, the
    bayonet up to 2.27). Shells come out of our muzzle (VFX_Fire moved there)."""
    import arsenal
    objs = capture(arsenal.gunlance)
    shield = set(subtree("EnergyShield"))
    to_file = upright(1.3, (0, 0, 0.17))
    muzzle = to_file @ Vector((0, 0, arsenal.GUNLANCE_TIP + 0.03))
    # The ivory spring: its top on a bone of its own, every vertex weighted by its height between
    # Base (the bottom stays) and MQ_SpringTop, so moving that bone down compresses it evenly
    # (reload, charged shelling, Wyvern's Fire: weapons script). The energy core has its own material.
    z0 = (to_file @ Vector((0, 0, arsenal.GUNLANCE_BASE + 0.1))).z
    top = (to_file @ Vector((0, 0, arsenal.SPRING_TOP))).z
    log(f"  spring from file z {z0:+.4f} to {top:+.4f}")

    def spring_weights(o, co):
        if not o.name.startswith("Binding"):
            return None
        w = min(1.0, max(0.0, (co.z - z0) / (top - z0)))
        return [("MQ_SpringTop", w), ("Base", 1.0 - w)]
    # The wyrmstake (and the heat effects) start at the originals' VFX_Pile / VFX_Heat, 0.11-0.19
    # off the axis where their barrels are; ours is on the axis: on it, at the same heights (user,
    # 2026-10-02: the needle showed beside the spring, not in it).
    return placed("wp_miquella_gl", "Art/Model/MiquellaLight/Gunlance", [o for o in objs if o not in shield],
                  to_file, {"VFX_Fire": muzzle, "VFX_Pile": Vector((0, 0, 0.530)), "VFX_Heat": Vector((0, 0, 1.153))},
                  floaters={"Barrel_Halo_0": "MQ_Halo0", "Barrel_Halo_1": "MQ_Halo1"},
                  pivots={"MQ_SpringTop": (0, 0, arsenal.SPRING_TOP)}, weight_fn=spring_weights,
                  by_name={"Energy_Core": "MiquellaCore"})


def gunlance_shield():
    import arsenal
    capture(arsenal.gunlance)
    to_file = shield_place("EnergyShield", 1.3, (0, 0.10, -0.03))
    return placed("wp_miquella_gl_shield", "Art/Model/MiquellaLight/Gunlance", subtree("EnergyShield"), to_file, {})


# The switch axe's morph: each axe blade turns into the fin of the same name on the sword's back.
SA_PAIRS = (("Blade_Upper", "Fin_Upper"), ("Blade_Middle", "Fin_Middle"), ("Blade_Lower", "Fin_Lower"))


def switch_axe():
    """Both modes in one model (user, 2026-10-02: swapping models flashed from one to the other;
    wanted the weapon to morph). Axe mode is the base, sword mode A the other. Parts of one mode
    only are sets with their own materials (faded by Dissolve), the moving parts have bones, and
    the weapons script moves them in about half a second (MORPHS in the script, written from
    `morph`): the long blade grows out of the shaft (its vertices weighted between Base and
    MQ_SwordTip, which starts pushed down to the blade's root); each axe blade swings up and
    over onto the sword's back, fading into its fin (the fins start where the blades are: the
    rigid fit of blade onto fin); the spike fades as the blade passes it; the head halo slides
    down to the blade's root. Hand 0.38 above the pommel so the shaft runs 0.72 m below it like
    the originals' long handles (-0.83); scaled 1.9: the head's top ~1.7 m above the hand
    (originals 1.96). Turned 180 about Z: the originals' axe blades reach out on -X, ours on +X."""
    import arsenal
    import motifs

    def build():
        mats = motifs.materials()
        arsenal.switch_axe_common(mats, random.Random(81))
        arsenal.switch_axe_axe_head(mats)
        arsenal.switch_axe_sword_head(mats, "a")
    objs = capture(build)
    to_file = upright(1.9, (0, 0, 0.38), turn=180)

    def F(p):
        return to_file @ Vector(p)
    # The head halo moves to where sword mode's root halo is; that one is not kept.
    root_halo = bpy.data.objects["Sword_Root_Halo"]
    halo_to = F(root_halo.matrix_world.translation)
    objs.remove(root_halo)
    bpy.data.objects.remove(root_halo, do_unlink=True)
    names = [o.name for o in objs]
    sets = {"Axe": {n for n in names if n.startswith(tuple(b for b, _ in SA_PAIRS))},
            "Spike": {n for n in names if n.startswith("Top_Spike")},
            "Sword": {n for n in names if n.startswith("Sword_Blade")},
            "Fin": {n for n in names if n.startswith("Fin_")}}
    joints, bone_prefix = [], [("Top_Halo", "MQ_HeadHalo")]
    for k, (blade, fin) in enumerate(SA_PAIRS):
        sb, eb = arsenal.SICKLES[blade]
        sf, ef = arsenal.SICKLES[fin]
        R, t = rigid_fit([F(p) for p in sb + eb], [F(p) for p in sf + ef])
        pa = F(sb[0])
        pf = R @ pa + t
        # Blade: from its place (bind) to the fin's; fin: from the blade's place to its own.
        joints.append({"name": f"MQ_Blade{k}", "pivot": pa, "alt": (pf, R), "win": (0.1, 0.9)})
        joints.append({"name": f"MQ_Fin{k}", "pivot": pf, "base": (pa, R.transposed()), "win": (0.1, 0.9)})
        bone_prefix += [(blade, f"MQ_Blade{k}"), (fin, f"MQ_Fin{k}")]
    # The long blade: root on Base, tip on MQ_SwordTip, between them by height; in axe mode the
    # tip sits on the root (the blade flattened to nothing, and faded out).
    zs = [(o.matrix_world @ Vector(b)) for o in objs if o.name == "Sword_Blade" for b in o.bound_box]
    z0, z1 = min(F(p).z for p in zs), max(F(p).z for p in zs)
    tip = F(max(zs, key=lambda p: p.z))
    joints.append({"name": "MQ_SwordTip", "pivot": tip, "base": (tip - Vector((0, 0, z1 - z0)), Matrix.Identity(3)),
                   "win": (0.0, 0.7)})
    head = F(bpy.data.objects["Top_Halo"].matrix_world.translation)
    joints.append({"name": "MQ_HeadHalo", "pivot": head, "alt": (halo_to, Matrix.Identity(3)), "win": (0.0, 0.6)})

    def weights(o, co):
        if not o.name.startswith("Sword_Blade"):
            return None
        w = min(1.0, max(0.0, (co.z - z0) / (z1 - z0)))
        return [("MQ_SwordTip", w), ("Base", 1.0 - w)]

    def bone(o, center):
        return next((b for prefix, b in bone_prefix if o.name.startswith(prefix)), None)
    axe_top = top_z([o for o in objs if o.name not in sets["Sword"] | sets["Fin"]])
    morph = {"seconds": 0.45, "joints": joints,
             "fades": [("Sword", "alt", (0.0, 0.25)), ("Spike", "base", (0.0, 0.35)),
                       ("Axe", "base", (0.45, 0.8)), ("Fin", "alt", (0.35, 0.7))]}
    return placed("wp_miquella_sa", "Art/Model/MiquellaLight/SwitchAxe", objs, to_file,
                  {"VFX_Attack_A": to_file @ Vector((0, 0, axe_top))}, by_name=phial_gauges("Phial"),
                  sets=sets, morph=morph, weight_fn=weights, bone_fn=bone,
                  file_pivots={j["name"]: j["pivot"] for j in joints})


def rigid_fit(src, dst):
    """Rotation R (3x3) and translation t with R @ s + t closest to d (least squares, no scale)."""
    import numpy as np
    a, b = np.array([list(p) for p in src]), np.array([list(p) for p in dst])
    ca, cb = a.mean(0), b.mean(0)
    u, _, vt = np.linalg.svd((a - ca).T @ (b - cb))
    d = np.sign(np.linalg.det(vt.T @ u.T))
    r = vt.T @ np.diag([1.0, 1.0, d]) @ u.T
    return Matrix(r.tolist()), Vector((cb - r @ ca).tolist())


def phial_gauges(prefix, n=5, halos=True):
    """Each floating phial (and its halo) on a material of its own, MiquellaGauge1-n, so the
    weapons script can light them one by one as a gauge (user, 2026-10-02)."""
    out = {}
    for k in range(n):
        out[f"{prefix}_{k}"] = f"MiquellaGauge{k + 1}"
        if halos:
            out[f"{prefix}_Halo_{k}"] = f"MiquellaGauge{k + 1}"
    return out


def charge_blade_scene(blade_len, fn=None):
    """A charge blade prototype (sword & shield, or `fn`) with a longer sword blade (set inside
    build_sword, which the prototype calls after setting its own length)."""
    import arsenal
    import blades
    orig = blades.build_sword

    def build(*a, **k):
        blades.BLADE_LEN = blade_len
        return orig(*a, **k)
    blades.build_sword = build
    try:
        return capture(fn or arsenal.charge_blade)
    finally:
        blades.build_sword = orig


# The charge blade's morph: bones along the axe head's outline (they draw the shield's oval in
# sword mode); the shield's halo, 0.27 x 1.05 across and 1.18 times as tall (arsenal.charge_blade).
CB_RIM_BONES = 24
CB_SHIELD_RADII = (0.27 * 1.05, 0.27 * 1.05 * 1.18)


def charge_blade():
    """The sword (it09 _0) with axe mode's head in the same model (user, 2026-10-02: swapping
    models flashed; the shield should change into the axe). Sword & shield mode is the base, axe
    mode the other; the weapons script morphs between them (MORPHS, written from `morph`): the
    shield model fades out while an oval of light the shield's size appears on the sword and
    reshapes into the bardiche outline (its rim on 24 bones along the outline), the sword
    shortens into the haft and spine of the head (vertices between Base and MQ_SwordTip), the
    five lit phials fly from the ring above the guard to the head's back, then the cutting edge,
    the sigil, the scrollwork and the phials' halos fade in. The prototype's 0.8 blade made 1.3,
    the whole scaled 1.4: tip 1.93 m above the hand (originals 1.92); 0.8 in axe mode like the
    axe design. Turned 180 about Z: the axe's edge toward -X like the originals' single edges."""
    import arsenal
    import blades
    import motifs
    objs = charge_blade_scene(1.3, lambda: (arsenal.charge_blade_axe(),
                                            arsenal.sword_phial_ring(motifs.materials(), 0.0, ring=False)))
    mw = bpy.data.objects["CB_Sword"].matrix_world
    to_file = upright(1.4, mw @ Vector((0, 0, (blades.GRIP_BOTTOM + blades.GUARD_Z) / 2)), turn=180)
    lin = to_file.to_3x3()

    def F(p):
        return to_file @ Vector(p)

    def axis_of(o):
        return (lin @ (o.matrix_world.to_3x3() @ Vector((0, 0, 1)))).normalized()
    joints = []
    # Phials: the sword's five (bind: the ring) fly to the axe's column; the axe's own droplets go.
    for k in range(5):
        drop, slot = bpy.data.objects[f"Sword_Phial_{k}"], bpy.data.objects[f"Phial_{k}"]
        rot = axis_of(drop).rotation_difference(axis_of(slot)).to_matrix()
        joints.append({"name": f"MQ_Phial{k}", "pivot": F(drop.matrix_world.translation),
                       "alt": (F(slot.matrix_world.translation), rot), "win": (0.2, 0.8)})
        objs.remove(slot)
        bpy.data.objects.remove(slot, do_unlink=True)
    names = [o.name for o in objs]
    sets = {"Rim": {"Axe_Rim", "Axe_Rim_Inner"},
            "Edge": {n for n in names if n.startswith("Axe_Edge")},
            "Axe": {o.name for o in subtree("Axe_Sigil")} | {n for n in names if n.startswith(("Joint_", "Phial_Halo"))}}
    # The sword shortens from 1.3 to 0.8 (the blade and its core lines, by height).
    g0, g1 = F((0, 0, blades.GUARD_Z)), F((0, 0, blades.GUARD_Z + 1.3))
    sword_parts = {o.name for o in subtree("CB_Sword") if o.name.split(".")[0] in ("Blade", "Core_-1", "Core_1")}
    joints.append({"name": "MQ_SwordTip", "pivot": g1, "alt": (F((0, 0, blades.GUARD_Z + 0.8)), Matrix.Identity(3)),
                   "win": (0.1, 0.6)})
    # The rim: bones evenly along the outline (by length); sword mode puts them on an oval the
    # shield's size around the outline's centre, at the same share of the way round.
    loop = [F(p) for p in arsenal.CB_AXE_OUTLINE]
    if (loop[0] - loop[-1]).length < 1e-6:
        loop = loop[:-1]
    seg = [(loop[(i + 1) % len(loop)] - loop[i]).length for i in range(len(loop))]
    total = sum(seg)
    arc = [sum(seg[:i]) / total for i in range(len(loop))]
    centre = sum(loop, Vector()) / len(loop)
    area = sum(loop[i].x * loop[(i + 1) % len(loop)].z - loop[(i + 1) % len(loop)].x * loop[i].z
               for i in range(len(loop)))
    turn = 1.0 if area > 0 else -1.0
    a0 = math.atan2(loop[0].z - centre.z, loop[0].x - centre.x)
    rx, rz = (1.4 * r for r in CB_SHIELD_RADII)
    for b in range(CB_RIM_BONES):
        s_b = b / CB_RIM_BONES
        i = min(range(len(loop)), key=lambda i: abs(arc[i] - s_b))
        a = a0 + turn * 2 * math.pi * s_b
        oval = centre + Vector((rx * math.cos(a), 0, rz * math.sin(a)))
        joints.append({"name": f"MQ_Rim{b}", "pivot": loop[i], "base": (oval, Matrix.Identity(3)),
                       "win": (0.15, 0.85)})
    from mathutils.kdtree import KDTree
    tree = KDTree(len(loop))
    for i, p in enumerate(loop):
        tree.insert(p, i)
    tree.balance()
    follows_rim = sets["Rim"] | sets["Edge"]

    def weights(o, co):
        if o.name in sword_parts:
            w = min(1.0, max(0.0, (co.z - g0.z) / (g1.z - g0.z)))
            return [("MQ_SwordTip", w), ("Base", 1.0 - w)]
        if o.name in follows_rim:
            _, i, _ = tree.find(co)
            u = arc[i] * CB_RIM_BONES
            b, f = int(u) % CB_RIM_BONES, u - int(u)
            return [(f"MQ_Rim{b}", 1.0 - f), (f"MQ_Rim{(b + 1) % CB_RIM_BONES}", f)]
        return None

    def bone(o, center):
        k = o.name.split(".")[0]
        return f"MQ_Phial{k[-1]}" if k.startswith("Sword_Phial_") else None
    morph = {"seconds": 0.5, "joints": joints,
             "fades": [("Rim", "alt", (0.0, 0.2)), ("Edge", "alt", (0.45, 0.85)), ("Axe", "alt", (0.5, 0.95))],
             # the shield model (the sub weapon) fades out as the axe forms
             "second": (0.0, 0.4)}
    return placed("wp_miquella_cb", "Art/Model/MiquellaLight/ChargeBlade", objs, to_file,
                  {"VFX_Attack": g1}, by_name=phial_gauges("Sword_Phial", halos=False), sets=sets, morph=morph,
                  weight_fn=weights, bone_fn=bone, file_pivots={j["name"]: j["pivot"] for j in joints})


def charge_blade_shield():
    """The shield (it09 _1): energy shield with its five phials and the floating axe edge, same
    scale as the sword (1.4)."""
    objs = charge_blade_scene(1.3)
    shield = set(subtree("EnergyShield")) | {o for o in objs if o.name.startswith(("Shield_Phial", "Axe_Edge"))}
    to_file = shield_place("EnergyShield", 1.4, (0, 0.12, 0.0))
    # The originals' shields hang on Emblem (and its blades), none on Base: follow Emblem.
    return placed("wp_miquella_cb_shield", "Art/Model/MiquellaLight/ChargeBlade",
                  [o for o in objs if o in shield], to_file, {}, bone_fn=lambda o, center: "Emblem",
                  by_name=phial_gauges("Shield_Phial", halos=False))


def insect_glaive():
    """Hand mid-grip; scaled 1.6: the top blade's point 1.82 m above the hand, the bottom one
    1.56 below (originals +1.74 / -1.6). The kinsect is a kit of its own."""
    import arsenal
    real = arsenal.kinsect
    arsenal.kinsect = lambda *a, **k: []
    try:
        objs = capture(arsenal.insect_glaive)
    finally:
        arsenal.kinsect = real
    to_file = upright(1.6, (0, 0, (0.52 + 0.95) / 2))
    # The three extract orbs (hidden until their extract is lit; the weapons script moves their
    # bones around the top blade), one material each on a three-band texture.
    floaters = {"Top_Halo": "MQ_TopHalo", "Bottom_Halo": "MQ_BottomHalo"}
    by_name, pivots = {}, {}
    mats = arsenal.extract_materials()
    for i, kind in enumerate(("Red", "White", "Orange")):
        a = math.radians(90 + 120 * i)
        center = Vector((IG_ORBIT[1] * math.cos(a), IG_ORBIT[1] * math.sin(a), IG_ORBIT[0]))
        pivots[f"MQ_Orb{kind}"] = center
        for o in arsenal.extract_orb(kind, center, IG_ORB_RADIUS, mats[kind]):
            floaters[o.name] = f"MQ_Orb{kind}"
            by_name[o.name] = f"MiquellaExtract{kind}"
            objs.append(o)
    return placed("wp_miquella_ig", "Art/Model/MiquellaLight/InsectGlaive", objs, to_file,
                  {"VFX_Attack": to_file @ Vector((0, 0, 1.45 + 0.42))},
                  floaters=floaters, by_name=by_name, pivots=pivots, uv_band=EXTRACT_BANDS,
                  textures=extract_textures)


# Orbit of the extract orbs in the prototype's space (centre height, radius): around the middle
# of the top blade; ~0.035 m orbs (user: small balls).
IG_ORBIT = (1.62, 0.088)
IG_ORB_RADIUS = 0.022
EXTRACT_TEX_REL = "Art/Model/MiquellaLight/InsectGlaive/tex"
EXTRACT_BANDS = {"MiquellaExtractRed": 0, "MiquellaExtractWhite": 1, "MiquellaExtractOrange": 2}
# albedo, roughness, emissive colour (RGB 0-255): rot pink mould, frosted ice, glowing ember.
EXTRACT_TEXTURE = [("#D88AA0", 0.85, (40, 10, 18)), ("#CFE6FA", 0.25, (24, 34, 46)), ("#FF8A1A", 0.5, (255, 140, 30))]


def extract_textures(kit):
    """The orbs' 64 x 64 three-band textures (ALBD, NRRO, EMI), unless already made."""
    from build_device_kit import convert_textures, save_rgba
    import numpy as np
    tex_dir = os.path.join(kit, "natives", "STM", *EXTRACT_TEX_REL.split("/"))
    if os.path.exists(os.path.join(tex_dir, f"MiquellaExtract_ALBD.tex.241106027")):
        return
    src = os.path.join(kit, "texture_sources")
    os.makedirs(src, exist_ok=True)
    n = 64
    albd, nrro, emi = (np.zeros((n, n, 4), np.uint8) for _ in range(3))
    for i, (color, rough, glow) in enumerate(EXTRACT_TEXTURE):
        cols = slice(i * n // 3, (i + 1) * n // 3 if i < 2 else n)
        albd[:, cols] = [int(color[k:k + 2], 16) for k in (1, 3, 5)] + [255]
        nrro[:, cols] = [int(rough * 255), 128, 255, 128]
        emi[:, cols] = list(glow) + [255]
    for name, arr in (("ALBD", albd), ("NRRO", nrro), ("EMI", emi)):
        save_rgba(os.path.join(src, f"MiquellaExtract_{name}.png"), arr)
    convert_textures(src, os.path.join(kit, "dds"), tex_dir)


def kinsect():
    """The golden swallowtail of light (the kinsect models are it10/03/*): head +Z and back +Y
    like the originals (ours had its back to -Y: turned 180 about Z). Its swallow tails make it
    tall: wingspan 1.1 m and 1.2 m from antennae to tails (originals 1.85 x 0.94), raised 0.2
    so it sits around their center. Wings follow the originals' wing bones, the rest Body."""
    import arsenal
    import motifs as m
    arsenal.kinsect(m.materials(), (0, 0, 0), 1.0)
    bpy.context.view_layer.update()
    objs = [o for o in bpy.data.objects if o.type in ("MESH", "CURVE")]
    span = 2 * max(abs((o.matrix_world @ Vector(b)).x) for o in objs for b in o.bound_box)
    to_file = Matrix.Translation((0, 0, 0.2)) @ Matrix.Scale(1.1 / span, 4) @ Matrix.Rotation(math.pi, 4, "Z")

    # The wings: not on the originals' wing bones (they beat so fast that our big gold wings
    # flickered, user 2026-10-02) but on bones of our own, children of Body at the wings' roots,
    # which the weapons script swings slowly like a butterfly's ("flap").
    wings = [o for o in objs if o.name.startswith(("Fore", "Hind"))]
    pts = [to_file @ (o.matrix_world @ v.co) for o in wings if o.type == "MESH" for v in o.data.vertices]
    if not pts:
        pts = [to_file @ (o.matrix_world @ Vector(b)) for o in wings for b in o.bound_box]
    roots = sorted(pts, key=lambda p: abs(p.x))[:max(8, len(pts) // 20)]
    hinge = sum(roots, Vector()) / len(roots)
    log(f"  wing hinge at y {hinge.y:+.4f} z {hinge.z:+.4f}")
    pivots = {"MQ_WingL": Vector((0.0, hinge.y, hinge.z)), "MQ_WingR": Vector((0.0, hinge.y, hinge.z))}

    def wing_bone(o, file_center):
        if o.name.startswith(("Fore", "Hind")):
            return "MQ_WingL" if file_center.x > 0 else "MQ_WingR"
        return "Body"
    return placed("wp_miquella_kinsect", "Art/Model/MiquellaLight/Kinsect", objs, to_file, {},
                  bone_fn=wing_bone, file_pivots=pivots, bone_parents={"MQ_WingL": "Body", "MQ_WingR": "Body"})


def kinsect_outline():
    """Option B: open-work wings, only the gold edges and veins (no solid wing sheets)."""
    spec = kinsect()
    spec["name"] = "wp_miquella_kinsect_b"
    spec["skip_materials"] = SKIP_MATERIALS | {"Wing_Membrane"}
    return spec


def bow():
    """Our bow stands in XZ with the arrow toward -X and the archer on +X; the originals' limbs
    run along Y and the string is behind the grip on -Z (arrow toward +Z). Grip at the origin,
    scaled 1.8: limb tips at +-1.24 (originals up to +-1.4). The drawn arrow is left out (the
    game draws its own, see `arrow`); the string's middle follows the original String bone.
    The six rings ahead of the arrow each have a bone (they hover, and pack toward the bow
    while drawing, weapons script) and light up in pairs per charge level (Gauge1-3)."""
    import arsenal
    import motifs
    objs = capture(lambda: arsenal.build_bow(motifs.materials(), with_arrow=False))
    to_file = Matrix.Scale(BOW_SCALE, 4) @ BOW_AXES @ Matrix.Translation((0.14, 0, 0))
    half = BOW_SCALE * 0.69

    def string_weights(o, co):
        if o.name.split(".")[0] != "String":
            return None
        w = max(0.0, 1.0 - abs(co.y) / half)
        return [("String", w), ("Base", 1.0 - w)]
    floaters = {f"Arrow_Rail_{i}": f"MQ_Ring{i}" for i in range(arsenal.BOW_RAIL_N)}
    floaters["Rest_Halo"] = "MQ_RestHalo"
    by_name = {f"Arrow_Rail_{i}": f"MiquellaGauge{i // 2 + 1}" for i in range(arsenal.BOW_RAIL_N)}
    for x in arsenal.bow_rail_x(1.0)[:2]:
        log(f"  packed ring at file z {(to_file @ Vector((x, 0, 0))).z:+.4f}")
    return placed("wp_miquella_bow", "Art/Model/MiquellaLight/Bow", objs, to_file, {},
                  weight_fn=string_weights, floaters=floaters, by_name=by_name)


BOW_SCALE = 1.8
BOW_AXES = Matrix(((0, -1, 0, 0), (0, 0, 1, 0), (-1, 0, 0, 0), (0, 0, 0, 1)))  # x->-z, y->-x, z->y


def bow_quiver(variant):
    """The bow's second model (_1): the originals lie along X, the bottom at x +0.55 and the
    arrows' vanes out to -0.77 at the mouth end. Ours (built along +Z, bottom at 0) turned so
    +Z -> -X, scaled 1.9: the drop under the bottom at +0.55, the vanes at -0.76."""
    import arsenal
    import motifs
    objs = capture(lambda: arsenal.QUIVERS[variant](motifs.materials()))
    axes = Matrix(((0, 0, -1, 0), (1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 0, 1)))       # z->-x, x->y, y->-z
    to_file = Matrix.Translation((0.49, 0.0, -0.01)) @ Matrix.Scale(1.9, 4) @ axes
    floaters = {"Quiver_Drop_0": "MQ_QuiverDrop", "Quiver_Drop_Halo_0": "MQ_QuiverDrop"}
    if variant == "a":
        floaters["Quiver_Halo"] = "MQ_QuiverHalo"
    else:
        floaters.update({"Quiver_Halo_0": "MQ_QuiverHalo0", "Quiver_Halo_1": "MQ_QuiverHalo1"})
    return placed(f"wp_miquella_bow_quiver_{variant}", "Art/Model/MiquellaLight/Bow", objs, to_file, {},
                  floaters=floaters, budget={"MiquellaIvory": 12000, "MiquellaGlow": 8000, "MiquellaBlade": 3000})


# The game's arrows (it1199_0000_0, the one on the string): nock near the origin, point on +Z
# at 2.69, a long head (about half); ours goes over that file (patch pak), for every bow.
ARROW_NOCK, ARROW_TIP = -0.04, 2.688


def arrow():
    import arsenal
    import motifs
    objs = capture(lambda: arsenal.needle_arrow("Arrow", Vector((0, 0, ARROW_NOCK)), Vector((0, 0, ARROW_TIP)),
                                                motifs.materials()))
    # Many fly at once: about the original's size (1.6k vertices).
    return placed("it1199_0000_0", "Art/Model/Item/it11/99/0000", objs, Matrix.Identity(4), {},
                  budget={"MiquellaGold": 2400, "MiquellaGlow": 400})


def heavy_bowgun():
    """Like the light bowgun kit (+Y muzzle -> +Z, +Z up -> +Y, bore 0.19 below the origin,
    0.1 back); scaled 1.3: 1.7 m long like the originals (-0.74..0.96)."""
    import bowgun as hb
    hb.build()
    # The conduit rings are named by their height (Conduit_Halo_0.34 / _0.56): give them names
    # of their own, each gets a bone.
    for o in [o for o in bpy.data.objects if o.name.startswith("Conduit_Halo_")]:
        o.name = "Conduit_Halo_A" if "0.34" in o.name else "Conduit_Halo_B"
    k, bore_y, back = 1.3, -0.194, -0.10
    axes = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))      # x->-x, z->y, y->z
    to_file = (Matrix.Translation((0, bore_y, back)) @ Matrix.Scale(k, 4) @ axes
               @ Matrix.Translation((0, 0, -hb.CONDUIT_Z)))
    muzzle = to_file @ Vector((0, hb.MUZZLE + 0.01, hb.CONDUIT_Z))
    by_name = {}
    for i in range(3):
        by_name[f"Barrel_Phial_{i}"] = f"MiquellaGauge{i + 1}"
        by_name[f"Barrel_Phial_Halo_{i}"] = f"MiquellaGauge{i + 1}"
    return {
        "name": "wp_miquella_hbg", "rel": "Art/Model/MiquellaLight/HeavyBowgun",
        "objects": [o for o in bpy.data.objects if o.type in ("MESH", "CURVE")], "to_file": to_file,
        "bones": {"VFX_Fire": muzzle, "VFX_FirePower": muzzle + Vector((0, 0, 0.38))},
        "materials": {"Ivory": "MiquellaIvory", "Light": "MiquellaGlow"},
        # Rings and phials hover like the light bowgun's (user, 2026-10-02).
        "by_name": by_name,
        "floaters": {"Conduit_Halo_A": "MQ_Halo0", "Conduit_Halo_B": "MQ_Halo1", "Muzzle_Halo": "MQ_Halo2",
                     "Muzzle_Halo_Inner": "MQ_Halo3",
                     **{f"Barrel_Phial_{i}": f"MQ_Phial{i}" for i in range(3)},
                     **{f"Barrel_Phial_Halo_{i}": f"MQ_Phial{i}" for i in range(3)}},
    }


WEAPONS = {"great_sword": great_sword, "light_bowgun": light_bowgun, "long_sword": long_sword,
           "sns_sword": sns_sword, "sns_shield": sns_shield,
           "sns_shield_aura": lambda: sns_shield_membrane("aura"),
           "sns_shield_bubble": lambda: sns_shield_membrane("bubble"),
           "sns_shield_volume": lambda: sns_shield_membrane("volume"), "sns_shield_film": sns_shield_film, "hammer": hammer, "hunting_horn": hunting_horn,
           "lance": lance, "lance_shield": lance_shield, "gunlance": gunlance, "gunlance_shield": gunlance_shield,
           "switch_axe": switch_axe, "charge_blade": charge_blade, "charge_blade_shield": charge_blade_shield,
           "insect_glaive": insect_glaive, "kinsect": kinsect, "kinsect_outline": kinsect_outline, "bow": bow,
           "bow_quiver_a": lambda: bow_quiver("a"), "bow_quiver_b": lambda: bow_quiver("b"), "arrow": arrow, "heavy_bowgun": heavy_bowgun}


# Parts of one mode only (switch axe, charge blade): Miquella<Set><Blade|Glow|Ivory>, so the
# weapons script can fade each set by its Dissolve (temper lines go on the set's Glow).
MODE_SETS = ("Axe", "Sword", "Fin", "Spike", "Rim", "Edge")
SET_BUDGET = {"MiquellaBlade": 4000, "MiquellaGlow": 5000, "MiquellaIvory": 6000}


def base_material(name):
    """MiquellaAxeBlade -> MiquellaBlade; other names unchanged."""
    for s in MODE_SETS:
        rest = name[len("Miquella" + s):]
        if name.startswith("Miquella" + s) and rest[:1].isupper():
            return "Miquella" + rest
    return name


# Triangle budget per game material (the originals run 5k-60k triangles in all).
BUDGET = {"MiquellaBlade": 8000, "MiquellaGlow": 12000, "MiquellaIvory": 24000, "MiquellaTemper": 1500,
          "MiquellaMembrane": 2000, "MiquellaCharge1": 8000, "MiquellaCharge2": 8000, "MiquellaCharge3": 8000,
          "MiquellaChargeTip": 2000}
GAUGE_BUDGET = 1500

# Material copied from the dual blades kit for each of our game materials.
MDF_SOURCE = {"MiquellaBlade": "MiquellaBlade", "MiquellaGlow": "MiquellaGlow",
              "MiquellaIvory": "MiquellaIvory", "MiquellaTemper": "MiquellaGlow",
              "MiquellaGauge1": "MiquellaGlow", "MiquellaGauge2": "MiquellaGlow",
              "MiquellaGauge3": "MiquellaGlow", "MiquellaGauge4": "MiquellaGlow", "MiquellaGauge5": "MiquellaGlow",
              "MiquellaCharge1": "MiquellaGlow", "MiquellaCharge2": "MiquellaGlow", "MiquellaCharge3": "MiquellaGlow",
              "MiquellaChargeTip": "MiquellaBlade",
              "MiquellaExtractRed": "MiquellaGlow", "MiquellaExtractWhite": "MiquellaGlow",
              "MiquellaExtractOrange": "MiquellaGlow", "MiquellaCore": "MiquellaGlow", "MiquellaGold": "MiquellaGlow",
              **{f"MiquellaBand{k + 1}": "MiquellaGlow" for k in range(LS_BANDS)},
              **{f"MiquellaFilm{k + 1}": "MiquellaGlow" for k in range(len(FILM_BANDS))}}
# Gold metal with a faint warmth (the needle arrows): the devices' three-band texture, its gold band.
DEVICE_TEX_REL = "Art/Model/MiquellaLight/Devices/tex"
UV_BANDS = {"MiquellaGold": 0}
# Charge parts start hidden (Dissolve 0) so they stay hidden if the weapons script is not running.
HIDDEN_AT_START = ("MiquellaCharge", "MiquellaExtract")


# Translucent light films (test, 2026-10-02): our weapon shaders only cut out, but some
# effect meshes and weapons use translucent ones. MiquellaMembrane is copied from one of
# these game materials (read from the local extraction, see HANDOFF) with gold settings.
EXTRACTED = "C:/Users/anton/MiquellaTools/extracted/natives/stm"
GLOW_EMI = "Art/Model/MiquellaLight/DualBlades/tex/MiquellaGlow_EMI.tex"
MEMBRANES = {
    # A: the aura effect on a player's equipment (two-sided, colour gradient, opacity).
    "aura": ("art/vfx/mesh/pl/equip/11_ch00_069_0006.mdf2.45", None, {
        "ColorParam": [1.0, 0.8, 0.4, 1.0], "ColorA": [1.0, 0.62, 0.2, 1.0], "ColorB": [1.0, 0.86, 0.5, 1.0],
        "EmissiveIntensity": [2.0], "Opacity": [0.5]}, {}),
    # B: the bubble effect: rim glow, refraction; its rainbow sheen turned off, little wobble.
    "bubble": ("art/vfx/mesh/common/other/bubble/11_bubble_00.mdf2.45", None, {
        "ColorParam": [1.0, 0.82, 0.45, 1.0], "EmissiveParam": [1.0, 0.75, 0.3, 1.0],
        "RimEmissive_Color": [1.0, 0.8, 0.35, 1.0], "RimEmissiveIntensity": [3.0], "RimEmissivePower": [2.0],
        "EmissiveIntensityParam": [2.0],
        "IridescenceBlendRate": [0.0], "Displacement": [0.02]}, {}),
    # C: a weapon's own soft inner glow (fake volume light, fades at grazing angles, pulses).
    "volume": ("art/model/item/it00/10/0001/it0010_0001_0.mdf2.45", "lambert5_Mat__P_Fake_InnerEmit", {
        "Emissive_Color": [1.0, 0.72, 0.28, 1.0], "Emissive_Power": [3.0]}, {"EmissiveMap": GLOW_EMI}),
}


def membrane_material(variant):
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF
    path, mat_name, props, textures = MEMBRANES[variant]
    mdf = readMDF(os.path.join(EXTRACTED, *path.split("/")))
    mat = copy.deepcopy(next(m for m in mdf.materialList if mat_name in (None, m.materialName)))
    for p in mat.propertyList:
        if p.propName in props:
            p.propValue = list(props[p.propName])
    for t in mat.textureList:
        if t.textureType in textures:
            t.texturePath = textures[t.textureType]
    missing = set(props) - {p.propName for p in mat.propertyList}
    if missing:
        log(f"  membrane {variant}: no {sorted(missing)}")
    return mat


# ------------------------------------------------------------------ geometry

def select_only(objs, active=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def game_material(o, spec):
    for prefix, mat in spec["by_name"].items():
        if o.name == prefix or o.name.startswith(prefix + "."):
            return mat
    names = [s.material.name for s in o.material_slots if s.material]
    mat = None
    for n in names:
        base = n.split(".")[0]
        if base in spec["materials"]:
            mat = spec["materials"][base]
            break
    if mat is None:
        log(f"  unmapped material {names} on {o.name} -> MiquellaIvory")
        mat = "MiquellaIvory"
    for set_name, members in spec.get("sets", {}).items():
        if o.name in members:
            return "Miquella" + set_name + ("Glow" if mat == "MiquellaTemper" else mat[len("Miquella"):])
    return mat


def lower_resolution(objs):
    """Game budget: thin strands as 4- or 8-sided tubes, at most one subdivision level."""
    for o in objs:
        if o.type == "CURVE":
            o.data.bevel_resolution = 0 if o.data.bevel_depth < 0.003 else 1
            o.data.resolution_u = min(o.data.resolution_u, 4)
        for mod in o.modifiers:
            if mod.type == "SUBSURF":
                mod.levels = mod.render_levels = min(mod.render_levels, 1)


def length_uv(o):
    """V runs from the blade's root (0) to its tip (1) along the prototype's +Z, so the
    material's moving glow band (MoveEmit) can sweep along the temper line."""
    zs = [v.co.z for v in o.data.vertices]
    z0, z1 = min(zs), max(zs)
    uv = o.data.uv_layers.active.data
    for loop in o.data.loops:
        co = o.data.vertices[loop.vertex_index].co
        uv[loop.index].uv = (0.5 + 4.0 * co.y, (co.z - z0) / max(z1 - z0, 1e-6))


def build_parts(spec, mesh_col):
    bpy.context.view_layer.update()
    objs = [o for o in spec["objects"] if o.name in bpy.data.objects]
    skip = spec.get("skip_materials", set())
    dropped = [o for o in objs if any(sl.material and sl.material.name.split(".")[0] in skip
                                      for sl in o.material_slots)]
    if dropped:
        log(f"  left out (membranes): {sorted(o.name for o in dropped)}")
    objs = [o for o in objs if o not in dropped]
    # Unparent and bake transforms so every part shares one space.
    for o in objs:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    lower_resolution(objs)
    floaters = spec.get("floaters", {})
    bone_of, pivots = {}, {}
    for o in objs:
        name = o.name.split(".")[0]
        if name in floaters:
            bone_of[o.name] = floaters[name]
            pivots[floaters[name]] = spec["to_file"] @ o.matrix_world.translation
    # Bones whose pivot is not a part's origin (a cluster of parts), in the prototype's space,
    # or already in file space.
    for bone, point in spec.get("pivots", {}).items():
        pivots[bone] = spec["to_file"] @ Vector(point)
    for bone, point in spec.get("file_pivots", {}).items():
        pivots[bone] = Vector(point)
    missing = set(floaters) - {n.split(".")[0] for n in bone_of}
    if missing:
        log(f"  floaters not found: {sorted(missing)}")
    groups = {}
    for o in objs:
        groups.setdefault(game_material(o, spec), []).append(o)
    subs = []
    for i, (mat, members) in enumerate(sorted(groups.items())):
        select_only(members)
        bpy.ops.object.convert(target="MESH")
        members = [o for o in bpy.context.selected_objects]
        for m in members:
            to_file = spec["to_file"] @ m.matrix_world
            weights = spec.get("weight_fn")
            if weights and len(m.data.vertices) and weights(m, to_file @ m.data.vertices[0].co) is not None:
                for v in m.data.vertices:
                    for bone, w in weights(m, to_file @ v.co):
                        g = m.vertex_groups.get(bone) or m.vertex_groups.new(name=bone)
                        g.add([v.index], w, "REPLACE")
                continue
            bone = bone_of.get(m.name, "Base")
            if spec.get("bone_fn"):
                center = sum((v.co for v in m.data.vertices), Vector()) / max(len(m.data.vertices), 1)
                bone = spec["bone_fn"](m, to_file @ center) or bone
            g = m.vertex_groups.new(name=bone)
            g.add(range(len(m.data.vertices)), 1.0, "REPLACE")
        select_only(members)
        if len(members) > 1:
            bpy.ops.object.join()
        o = bpy.context.view_layer.objects.active
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        o.name = f"Group_0_Sub_{i}__{mat}"
        o.data.materials.clear()
        o.data.materials.append(bpy.data.materials.get(mat) or bpy.data.materials.new(mat))
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=0.0001)
        bpy.ops.mesh.delete_loose()
        bpy.ops.uv.smart_project(island_margin=0.02)
        bpy.ops.object.mode_set(mode="OBJECT")
        if mat == "MiquellaTemper":
            length_uv(o)
        bands = {**UV_BANDS, **spec.get("uv_band", {})}
        if mat in bands:
            u = (bands[mat] + 0.5) / 3
            for d in o.data.uv_layers.active.data:
                d.uv = (u, 0.5)
        before = tris(o)
        budget = {**BUDGET, **spec.get("budget", {})}
        limit = budget.get(mat) or (SET_BUDGET.get(base_material(mat)) if mat != base_material(mat) else None)
        ratio = min(1.0, (limit or GAUGE_BUDGET) / max(before, 1))
        if ratio < 1.0:
            dec = o.modifiers.new("decimate", "DECIMATE")
            dec.ratio = ratio
            bpy.ops.object.modifier_apply(modifier="decimate")
            # Decimation can leave loose vertices, which the exporter refuses.
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.delete_loose()
            bpy.ops.object.mode_set(mode="OBJECT")
        o.data.transform(FILE_TO_BLENDER @ spec["to_file"])
        for col in list(o.users_collection):
            col.objects.unlink(o)
        mesh_col.objects.link(o)
        subs.append(o)
        log(f"{o.name}: {len(members)} parts, {before} -> {tris(o)} tris")
    log(f"total: {sum(tris(o) for o in subs)} tris")
    return subs, pivots


def import_skeleton(orig_mesh, mesh_col, bones, new_bones, parents=None):
    from re_mesh_editor.modules.mesh.blender_re_mesh import importREMeshFile
    opts = {"clearScene": False, "createCollections": True, "loadMaterials": False,
            "loadMDFData": False, "loadShellFur": False, "loadUnusedTextures": False,
            "loadUnusedProps": False, "useBackfaceCulling": False, "reloadCachedTextures": False,
            "mdfPath": "", "importAllLODs": False, "importBlendShapes": False, "rotate90": True,
            "mergeArmature": "", "importArmatureOnly": False, "mergeGroups": False,
            "importShadowMeshes": False, "importOcclusionMeshes": False, "importBoundingBoxes": False}
    before = set(bpy.data.objects)
    importREMeshFile(orig_mesh, opts)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        if o is not arm:
            bpy.data.objects.remove(o, do_unlink=True)
    for col in list(arm.users_collection):
        col.objects.unlink(arm)
    mesh_col.objects.link(arm)
    # Effect bones are children of Base (identity at the origin): RE matrices are row-major
    # with the translation in the last row, in file space; export keeps these stored values.
    for name, pos in bones.items():
        b = arm.data.bones.get(name)
        if b is None or b.get("reMeshWorldMatrix") is None:
            log(f"  bone {name} not in original, skipped")
            continue
        # Under a parent other than Base (e.g. a gun's Hinge) the local translation is relative
        # to it; only done when the parent is not rotated.
        local = pos.copy()
        parent = b.parent
        if parent is not None and parent.get("reMeshWorldMatrix") is not None:
            pm = [list(r) for r in parent["reMeshWorldMatrix"]]
            if any(abs(pm[i][j] - (1.0 if i == j else 0.0)) > 1e-4 for i in range(3) for j in range(3)):
                log(f"  bone {name}: parent {parent.name} is rotated, not moved")
                continue
            local = pos - Vector((pm[3][0], pm[3][1], pm[3][2]))
        for key, sign, p in (("reMeshWorldMatrix", 1, pos), ("reMeshLocalMatrix", 1, local),
                             ("reMeshInverseMatrix", -1, pos)):
            m = [list(r) for r in b[key]]
            m[3][0], m[3][1], m[3][2] = (sign * p.x, sign * p.y, sign * p.z)
            b[key] = m
        log(f"  bone {name} -> ({pos.x:+.3f}, {pos.y:+.3f}, {pos.z:+.3f})")
    add_bones(arm, new_bones, parents)
    log(f"skeleton: {[b.name for b in arm.data.bones]}")
    return arm


def add_bones(arm, pivots, parents=None):
    """New children of Base (or of the bone named in `parents`, which must not be rotated) at
    the given file-space points, no rotation. Export uses the stored RE matrices (Base's
    identity with our translation; the local one relative to the parent); the Blender bones
    are only placeholders."""
    parents = parents or {}
    if not pivots:
        return
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    base = arm.data.edit_bones["Base"]
    for name in pivots:
        eb = arm.data.edit_bones.new(name)
        eb.head = base.head
        eb.tail = base.head + Vector((0, 0, 0.05))
        eb.parent = arm.data.edit_bones[parents.get(name, "Base")]
    bpy.ops.object.mode_set(mode="OBJECT")
    ref = arm.data.bones["Base"]
    for name, pos in pivots.items():
        b = arm.data.bones[name]
        pm = arm.data.bones[parents.get(name, "Base")]["reMeshWorldMatrix"]
        local = pos - Vector((pm[3][0], pm[3][1], pm[3][2]))
        for key, sign, p in (("reMeshWorldMatrix", 1, pos), ("reMeshLocalMatrix", 1, local),
                             ("reMeshInverseMatrix", -1, pos)):
            m = [list(r) for r in ref[key]]
            m[3][0], m[3][1], m[3][2] = (sign * p.x, sign * p.y, sign * p.z)
            b[key] = m
        log(f"  new bone {name} at ({pos.x:+.4f}, {pos.y:+.4f}, {pos.z:+.4f})")


def bind(subs, arm):
    """Vertex groups were set per part in build_parts (Base, or a floating ring's bone)."""
    for o in subs:
        o.modifiers.clear()
        o.modifiers.new("Armature", "ARMATURE").object = arm
        o.parent = arm


def file_bounds(subs):
    inv = FILE_TO_BLENDER.inverted()
    pts = [inv @ v.co for o in subs for v in o.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


# ------------------------------------------------------------------ mdf

def build_mdf(path, template_mdf, names, membrane=None, hidden=()):
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    template = readMDF(template_mdf)
    by_name = {m.materialName: m for m in template.materialList}
    materials = []
    for name in names:
        if name == "MiquellaMembrane":
            new = membrane_material(membrane)
        else:
            new = copy.deepcopy(by_name[MDF_SOURCE[base_material(name)]])
            if name.startswith(HIDDEN_AT_START) or name in hidden:
                for p in new.propertyList:
                    if p.propName == "Dissolve":
                        p.propValue = [0.0]
            if name == "MiquellaGold":
                for p in new.propertyList:
                    if p.propName == "Emissive_Intensity":
                        p.propValue = [0.6]
                for t in new.textureList:
                    for kind in ("ALBD", "NRRO", "EMI"):
                        if t.texturePath.upper().endswith(f"_{kind}.TEX"):
                            t.texturePath = f"{DEVICE_TEX_REL}/MiquellaDevice_{kind}.tex"
            if name.startswith("MiquellaFilm"):
                for p in new.propertyList:
                    if p.propName == "Dissolve":
                        p.propValue = [FILM_BANDS[int(name[len("MiquellaFilm"):]) - 1][2]]
                    elif p.propName == "Emissive_Intensity":
                        p.propValue = [0.9]
            if name.startswith("MiquellaExtract"):
                # Their own colours from the band texture: white emissive colour, our textures.
                for p in new.propertyList:
                    if p.propName == "Emissive_Color":
                        p.propValue = [1.0, 1.0, 1.0, 1.0]
                for t in new.textureList:
                    for kind in ("ALBD", "NRRO", "EMI"):
                        if t.texturePath.upper().endswith(f"_{kind}.TEX"):
                            t.texturePath = f"{EXTRACT_TEX_REL}/MiquellaExtract_{kind}.tex"
        new.materialName = name
        materials.append(new)
    template.materialList = materials
    writeMDF(template, path)
    check = readMDF(path)
    log(f"mdf: {[m.materialName for m in check.materialList]}")


# ------------------------------------------------------------------ morph

def set_materials(names, set_name):
    return [n for n in names if n.startswith("Miquella" + set_name) and n[len("Miquella" + set_name):][:1].isupper()]


def write_morph(kit, name, morph, names):
    """The morph for the weapons script (a Lua table to paste into MORPHS) and for
    preview_morph.py (json): joints with their pivot and their pose in each mode (missing: the
    bind pose), as file-space positions and xyzw quaternions; the windows are shares of the
    morph's progress (0 base mode, 1 the other)."""
    def pose(j, side):
        if side not in j:
            return None
        pos, rot = j[side]
        q = rot.to_quaternion()
        return {"pos": [round(c, 4) for c in pos], "rot": [round(c, 5) for c in (q.x, q.y, q.z, q.w)]}
    data = {"seconds": morph["seconds"], "second": list(morph["second"]) if morph.get("second") else None,
            "joints": [{"name": j["name"], "pivot": [round(c, 4) for c in j["pivot"]], "base": pose(j, "base"),
                        "alt": pose(j, "alt"), "win": list(j["win"])} for j in morph["joints"]],
            "fades": [{"set": s, "mats": set_materials(names, s), "show": show, "win": list(win)}
                      for s, show, win in morph["fades"]]}
    with open(os.path.join(kit, f"{name}_morph.json"), "w") as f:
        json.dump(data, f, indent=1)

    def lua(v):
        if isinstance(v, dict):
            return "{ " + ", ".join(f"{k} = {lua(x)}" for k, x in v.items() if x is not None) + " }"
        if isinstance(v, (list, tuple)):
            return "{ " + ", ".join(lua(x) for x in v) + " }"
        if isinstance(v, str):
            return f'"{v}"'
        return repr(v)
    lines = [f"    seconds = {data['seconds']},"]
    if data["second"]:
        lines.append(f"    second = {lua(data['second'])},")
    lines.append("    joints = {")
    lines += [f"        {lua(j)}," for j in data["joints"]]
    lines += ["    },", "    fades = {"]
    lines += [f"        {lua({k: v for k, v in fd.items() if k != 'set'})}," for fd in data["fades"]]
    lines.append("    },")
    with open(os.path.join(kit, f"{name}_morph.lua"), "w") as f:
        f.write("{\n" + "\n".join(lines) + "\n}\n")
    log(f"morph: {len(data['joints'])} joints, fades {[(fd['set'], len(fd['mats'])) for fd in data['fades']]}")


# ------------------------------------------------------------------ main

def enable_addon():
    """After the prototype is built: its factory reset unregisters add-ons, and the importer
    crashes without its registered properties."""
    import addon_utils
    sys.path.append(bpy.utils.user_resource("SCRIPTS", path="addons"))
    addon_utils.modules_refresh()
    addon_utils.enable("re_mesh_editor", default_set=True)


def main():
    weapon, kit, orig_mesh, template_mdf = sys.argv[1], *(os.path.abspath(a) for a in sys.argv[2:5])
    import common as c

    c.reset_scene()
    spec = WEAPONS[weapon]()
    enable_addon()
    from re_mesh_editor.modules.mesh.blender_re_mesh import exportREMeshFile
    mesh_col = bpy.data.collections.new(f"{spec['name']}.mesh")
    bpy.context.scene.collection.children.link(mesh_col)
    subs, pivots = build_parts(spec, mesh_col)
    if spec.get("bands"):
        subs = split_bands(subs, *spec["bands"])
    lo, hi = file_bounds(subs)
    log(f"file-space bounds min=({lo.x:+.3f}, {lo.y:+.3f}, {lo.z:+.3f}) max=({hi.x:+.3f}, {hi.y:+.3f}, {hi.z:+.3f})")
    arm = import_skeleton(orig_mesh, mesh_col, spec["bones"], pivots, spec.get("bone_parents"))
    bind(subs, arm)
    # Drop everything that is not part of the export.
    keep = set(subs) | {arm}
    for o in list(bpy.data.objects):
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)

    natives = os.path.join(kit, "natives", "STM", *spec["rel"].split("/"))
    os.makedirs(natives, exist_ok=True)
    path = os.path.join(natives, f"{spec['name']}.mesh{MESH_EXT}")
    ok = exportREMeshFile(path, {"targetCollection": mesh_col.name, "selectedOnly": False,
                                 "exportAllLODs": False, "exportBlendShapes": False, "rotate90": True,
                                 "useBlenderMaterialName": False, "preserveBoneMatrices": True,
                                 "exportBoundingBoxes": False, "autoSolveRepeatedUVs": True,
                                 "preserveSharpEdges": False})
    log(f"export mesh: {ok} -> {path} ({os.path.getsize(path)} bytes)")
    names = [o.name.split("__", 1)[1] for o in subs]
    morph = spec.get("morph")
    hidden = set()
    if morph:
        # Parts of the other mode start hidden: the base mode shows without the script.
        for set_name, show, _ in morph["fades"]:
            if show == "alt":
                hidden |= set(set_materials(names, set_name))
        write_morph(kit, spec["name"], morph, names)
    build_mdf(os.path.join(natives, f"{spec['name']}.mdf2{MDF_EXT}"), template_mdf, names, spec.get("membrane"),
              hidden)
    if spec.get("textures"):
        spec["textures"](kit)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(kit, f"{spec['name']}_kit.blend"))


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.flush()
        os._exit(0)     # the addon leaves a thread running
