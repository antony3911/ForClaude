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
import math
import os
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
    }


# ---- prototypes from arsenal.py, sword_shield.py and bowgun.py

# Our material names -> game materials, shared by these prototypes. Faint membranes (energy
# shields, the charge blade's axe sheet) are left out: the game's weapon shaders only cut out,
# so they would be solid gold plates; the open-work look stays (DESIGN: light, airy).
ARSENAL_MATERIALS = {"Ivory": "MiquellaIvory", "Light": "MiquellaGlow", "Blade_Light": "MiquellaBlade",
                     "Blade_Core": "MiquellaTemper", "Sun": "MiquellaGlow", "Face_Membrane": "MiquellaGlow",
                     "Sigil_Light": "MiquellaGlow", "Droplet": "MiquellaGlow", "Phial_Lit": "MiquellaGlow",
                     "Wing_Membrane": "MiquellaBlade"}
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


def hammer():
    """Hand 0.1 above the pommel; scaled 1.4: the head's center 1.32 m above the hand, the
    striking faces 0.58 apart (originals: head up to 1.65, 1.1 wide; ours stays slender)."""
    import arsenal
    objs = capture(arsenal.hammer)
    to_file = upright(1.4, (0, 0, 0.1))
    return placed("wp_miquella_hm", "Art/Model/MiquellaLight/Hammer", objs, to_file,
                  {"VFX_Attack": to_file @ Vector((0, 0, 1.04 + 0.14))},
                  floaters={"Belt_Halo": "MQ_BeltHalo"})


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
    objs = capture(arsenal.lance)
    shield = set(subtree("EnergyShield"))
    to_file = upright(1.7, (0, 0, 0.17))
    return placed("wp_miquella_ln", "Art/Model/MiquellaLight/Lance", [o for o in objs if o not in shield],
                  to_file, {})


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
    return placed("wp_miquella_gl", "Art/Model/MiquellaLight/Gunlance", [o for o in objs if o not in shield],
                  to_file, {"VFX_Fire": muzzle},
                  floaters={"Barrel_Halo_0": "MQ_Halo0", "Barrel_Halo_1": "MQ_Halo1"})


def gunlance_shield():
    import arsenal
    capture(arsenal.gunlance)
    to_file = shield_place("EnergyShield", 1.3, (0, 0.10, -0.03))
    return placed("wp_miquella_gl_shield", "Art/Model/MiquellaLight/Gunlance", subtree("EnergyShield"), to_file, {})


def switch_axe():
    """Axe mode only for now (the sword mode needs the game's mode field). Hand 0.38 above the
    pommel so the shaft runs 0.72 m below it like the originals' long handles (-0.83); scaled
    1.9: the head's top ~1.7 m above the hand (originals 1.96). Turned 180 about Z: the
    originals' axe blades reach out on -X, ours on +X."""
    import arsenal
    objs = capture(arsenal.switch_axe)
    to_file = upright(1.9, (0, 0, 0.38), turn=180)
    return placed("wp_miquella_sa", "Art/Model/MiquellaLight/SwitchAxe", objs, to_file,
                  {"VFX_Attack_A": to_file @ Vector((0, 0, top_z(objs)))})


def charge_blade_scene(blade_len):
    """The charge blade prototype with a longer sword blade (set inside build_sword, which the
    prototype calls after setting its own length)."""
    import arsenal
    import blades
    orig = blades.build_sword

    def build(*a, **k):
        blades.BLADE_LEN = blade_len
        return orig(*a, **k)
    blades.build_sword = build
    try:
        return capture(arsenal.charge_blade)
    finally:
        blades.build_sword = orig


def charge_blade():
    """The sword (it09 _0): the prototype's 0.8 blade made 1.3, the whole scaled 1.4: tip
    1.93 m above the hand (originals 1.92)."""
    import blades
    objs = charge_blade_scene(1.3)
    sword = set(subtree("CB_Sword")) | {o for o in objs if o.name.startswith("Sword_Phial")}
    mw = bpy.data.objects["CB_Sword"].matrix_world
    to_file = upright(1.4, mw @ Vector((0, 0, (blades.GRIP_BOTTOM + blades.GUARD_Z) / 2)))
    tip = mw @ Vector((0, 0, blades.GUARD_Z + 1.3))
    return placed("wp_miquella_cb", "Art/Model/MiquellaLight/ChargeBlade", [o for o in objs if o in sword],
                  to_file, {"VFX_Attack": to_file @ tip})


def charge_blade_shield():
    """The shield (it09 _1): energy shield with its five phials and the floating axe edge, same
    scale as the sword (1.4)."""
    objs = charge_blade_scene(1.3)
    shield = set(subtree("EnergyShield")) | {o for o in objs if o.name.startswith(("Shield_Phial", "Axe_Edge"))}
    to_file = shield_place("EnergyShield", 1.4, (0, 0.12, 0.0))
    # The originals' shields hang on Emblem (and its blades), none on Base: follow Emblem.
    return placed("wp_miquella_cb_shield", "Art/Model/MiquellaLight/ChargeBlade",
                  [o for o in objs if o in shield], to_file, {}, bone_fn=lambda o, center: "Emblem")


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
    return placed("wp_miquella_ig", "Art/Model/MiquellaLight/InsectGlaive", objs, to_file,
                  {"VFX_Attack": to_file @ Vector((0, 0, 1.45 + 0.42))},
                  floaters={"Top_Halo": "MQ_TopHalo", "Bottom_Halo": "MQ_BottomHalo"})


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

    def wing_bone(o, file_center):
        if o.name.startswith(("Fore", "Hind")):
            return "L_Wing" if file_center.x > 0 else "R_Wing"
        return "Body"
    return placed("wp_miquella_kinsect", "Art/Model/MiquellaLight/Kinsect", objs, to_file, {},
                  bone_fn=wing_bone)


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
    game draws its own); the string's middle follows the original String bone."""
    import arsenal
    objs = capture(arsenal.bow)
    objs = [o for o in objs if not o.name.startswith(("Arrow_Shaft", "Arrow_Head", "Fletch_"))]
    axes = Matrix(((0, -1, 0, 0), (0, 0, 1, 0), (-1, 0, 0, 0), (0, 0, 0, 1)))  # x->-z, y->-x, z->y
    to_file = Matrix.Scale(1.8, 4) @ axes @ Matrix.Translation((0.14, 0, 0))
    half = 1.8 * 0.69

    def string_weights(o, co):
        if o.name.split(".")[0] != "String":
            return None
        w = max(0.0, 1.0 - abs(co.y) / half)
        return [("String", w), ("Base", 1.0 - w)]
    return placed("wp_miquella_bow", "Art/Model/MiquellaLight/Bow", objs, to_file, {},
                  weight_fn=string_weights)


def heavy_bowgun():
    """Like the light bowgun kit (+Y muzzle -> +Z, +Z up -> +Y, bore 0.19 below the origin,
    0.1 back); scaled 1.3: 1.7 m long like the originals (-0.74..0.96)."""
    import bowgun as hb
    hb.build()
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
        "by_name": by_name, "floaters": {},
    }


WEAPONS = {"great_sword": great_sword, "light_bowgun": light_bowgun, "long_sword": long_sword,
           "sns_sword": sns_sword, "sns_shield": sns_shield, "hammer": hammer, "hunting_horn": hunting_horn,
           "lance": lance, "lance_shield": lance_shield, "gunlance": gunlance, "gunlance_shield": gunlance_shield,
           "switch_axe": switch_axe, "charge_blade": charge_blade, "charge_blade_shield": charge_blade_shield,
           "insect_glaive": insect_glaive, "kinsect": kinsect, "kinsect_outline": kinsect_outline, "bow": bow, "heavy_bowgun": heavy_bowgun}


# Triangle budget per game material (the originals run 5k-60k triangles in all).
BUDGET = {"MiquellaBlade": 8000, "MiquellaGlow": 12000, "MiquellaIvory": 24000, "MiquellaTemper": 1500}
GAUGE_BUDGET = 1500

# Material copied from the dual blades kit for each of our game materials.
MDF_SOURCE = {"MiquellaBlade": "MiquellaBlade", "MiquellaGlow": "MiquellaGlow",
              "MiquellaIvory": "MiquellaIvory", "MiquellaTemper": "MiquellaGlow",
              "MiquellaGauge1": "MiquellaGlow", "MiquellaGauge2": "MiquellaGlow",
              "MiquellaGauge3": "MiquellaGlow"}


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
    for n in names:
        base = n.split(".")[0]
        if base in spec["materials"]:
            return spec["materials"][base]
    log(f"  unmapped material {names} on {o.name} -> MiquellaIvory")
    return "MiquellaIvory"


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
        before = tris(o)
        ratio = min(1.0, BUDGET.get(mat, GAUGE_BUDGET) / max(before, 1))
        if ratio < 1.0:
            dec = o.modifiers.new("decimate", "DECIMATE")
            dec.ratio = ratio
            bpy.ops.object.modifier_apply(modifier="decimate")
        o.data.transform(FILE_TO_BLENDER @ spec["to_file"])
        for col in list(o.users_collection):
            col.objects.unlink(o)
        mesh_col.objects.link(o)
        subs.append(o)
        log(f"{o.name}: {len(members)} parts, {before} -> {tris(o)} tris")
    log(f"total: {sum(tris(o) for o in subs)} tris")
    return subs, pivots


def import_skeleton(orig_mesh, mesh_col, bones, new_bones):
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
    add_bones(arm, new_bones)
    log(f"skeleton: {[b.name for b in arm.data.bones]}")
    return arm


def add_bones(arm, pivots):
    """New children of Base at the given file-space points, no rotation. Export uses the
    stored RE matrices (Base's identity with our translation); the Blender bones are only
    placeholders."""
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
        eb.parent = base
    bpy.ops.object.mode_set(mode="OBJECT")
    ref = arm.data.bones["Base"]
    for name, pos in pivots.items():
        b = arm.data.bones[name]
        for key, sign in (("reMeshWorldMatrix", 1), ("reMeshLocalMatrix", 1), ("reMeshInverseMatrix", -1)):
            m = [list(r) for r in ref[key]]
            m[3][0], m[3][1], m[3][2] = (sign * pos.x, sign * pos.y, sign * pos.z)
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

def build_mdf(path, template_mdf, names):
    from re_mesh_editor.modules.mdf.file_re_mdf import readMDF, writeMDF
    template = readMDF(template_mdf)
    by_name = {m.materialName: m for m in template.materialList}
    materials = []
    for name in names:
        new = copy.deepcopy(by_name[MDF_SOURCE[name]])
        new.materialName = name
        materials.append(new)
    template.materialList = materials
    writeMDF(template, path)
    check = readMDF(path)
    log(f"mdf: {[m.materialName for m in check.materialList]}")


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
    lo, hi = file_bounds(subs)
    log(f"file-space bounds min=({lo.x:+.3f}, {lo.y:+.3f}, {lo.z:+.3f}) max=({hi.x:+.3f}, {hi.y:+.3f}, {hi.z:+.3f})")
    arm = import_skeleton(orig_mesh, mesh_col, spec["bones"], pivots)
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
    build_mdf(os.path.join(natives, f"{spec['name']}.mdf2{MDF_EXT}"), template_mdf, names)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(kit, f"{spec['name']}_kit.blend"))


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.flush()
        os._exit(0)     # the addon leaves a thread running
