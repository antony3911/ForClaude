"""Build the weapons' recoloured effect paks (MiquellaLight_<Weapon>FX.pak) from the user's
own game files: every weapon's attack trails and glows in layers of gold (user, 2026-10-02
night: the long sword's red-spirit trail, then "other weapons have trails too").

The table below is the record of what each pak does. Effects that already had their own
treatment keep it (dual blades: red -> gold, blue -> silver, approved by the user; light
bowgun; the insect glaive's extract colours on the body). The modified game files stay out of
the repo; rebuild after a game update.

Usage (Blender 4.5's Python, for make_patch_pak):
    python fx_paks.py <extracted root> <work dir> [weapon ...]
Each weapon's files go to <work>/<folder>/natives/STM/Art/VFX/EffectEditor/Weapon/<it>/, the
pak to <work>/MiquellaLight_<name>.pak and a copy to <work>/install/pak_mods/.
"""
import glob
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from recolor_efx import recolor

SKIP_PARAMS = ("Blood", "Smoke", "Head", "Cartridge", "Hit")     # blood, smoke, ammo colours
SKIP_ENTRIES = ("jimen", "land", "blood", "dirt")
GROUND = ("_jimen", "_land_")                                    # ground dust files: left as they are

# weapon: (pak name, work folder, {file stem or "*": options}, files kept from the old pak)
#   options: hide = entries made transparent; only_hide = no recolouring
WEAPONS = {
    # Great sword, hammer: the charge only on the weapon (their body glow hidden), as before;
    # now layers of gold instead of reds only (guard / parry sparks were left pale red).
    "it00": ("GreatSwordFX", "gsfx", {"*": {"hide": ("PLE_Body", "PLE_IMP")}}, ()),
    "it04": ("HammerFX", "hmfx", {"*": {"hide": ("PLE_Body", "PLE_IMP")}}, ()),
    "it01": ("SwordShieldFX", "snsfx", {"*": {}}, ()),
    # Long sword: the spirit levels' blade and body glow hidden (2026-10-02), the rest gold.
    "it03": ("LongSwordFX", "lsfx", {"11_it03_000": {"hide": ("PLE_wep",), "only_hide": True},
                                     "11_it03_004": {"hide": ("PLE_Body", "GPUP"), "only_hide": True},
                                     "*": {}}, ()),
    "it05": ("HuntingHornFX", "hhfx", {"*": {}}, ()),
    # Lance: the charge's body glow hidden (2026-10-02); it had not been recoloured at all.
    "it06": ("LanceFX", "lnfx", {"*": {"hide": ("PLE_Body", "PLE_IMP", "PLE_Leg", "=PLE", "=0_PLE")}}, ()),
    "it07": ("GunlanceFX", "glfx", {"*": {}}, ()),
    "it08": ("SwitchAxeFX", "safx", {"*": {}}, ()),
    "it09": ("ChargeBladeFX", "cbfx", {"*": {}}, ()),
    # Insect glaive: its pak's files stay (warm -> gold, extract colours hidden); the purple
    # 052 / 198 are added.
    "it10": ("InsectGlaiveFX", "igfx", {"11_it10_052": {}, "11_it10_198": {}}, "keep"),
    # Bow: the charge (030) stays as it was; the arrows' trails are added.
    "it11": ("BowFX", "bowfx", {"11_it11_030": None, "*": {}}, "keep"),
    "it12": ("HeavyBowgunFX", "hbgfx", {"*": {}}, ()),
    # Light bowgun: was warm -> gold only (its blue sparks and the wyvernblast's blue core
    # stayed); now layers. Its ground files stay as they were in the old pak.
    "it13": ("LightBowgunFX", "lbgfx", {"*": {}}, "keep"),
}


def build(root, work, it):
    name, folder, rules, keep = WEAPONS[it]
    rel = f"natives/STM/Art/VFX/EffectEditor/Weapon/{it}"
    dst_dir = os.path.join(work, folder, rel)
    if keep != "keep" and os.path.isdir(os.path.join(work, folder)):
        shutil.rmtree(os.path.join(work, folder))
    os.makedirs(dst_dir, exist_ok=True)
    total = 0
    for src in sorted(glob.glob(os.path.join(root, f"natives/stm/art/vfx/effecteditor/weapon/{it}/*.efx.*"))):
        base = os.path.basename(src)
        stem = base.split(".")[0]
        if any(g in stem for g in GROUND):
            continue
        opts = rules.get(stem, rules.get("*"))
        if opts is None:                         # not handled here (kept from the old pak, if any)
            continue
        out, n = recolor(open(src, "rb").read(), log=lambda s: None, layers=not opts.get("only_hide"),
                         hide=opts.get("hide", ()), only_hide=opts.get("only_hide", False),
                         skip_params=SKIP_PARAMS, skip_entries=SKIP_ENTRIES)
        if n:
            open(os.path.join(dst_dir, base), "wb").write(out)
            total += 1
    pak = os.path.join(work, f"MiquellaLight_{name}.pak")
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "make_patch_pak.py"),
                        os.path.join(work, folder), pak, os.path.join(os.path.dirname(os.path.abspath(work)), "addons")],
                       capture_output=True, text=True)
    verified = [ln for ln in r.stdout.splitlines() if "verified" in ln]
    if not verified:                             # (Blender's Python may exit non-zero after finishing)
        sys.exit(f"{name}: pak failed\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    os.makedirs(os.path.join(work, "install", "pak_mods"), exist_ok=True)
    shutil.copy2(pak, os.path.join(work, "install", "pak_mods"))
    files = len(glob.glob(os.path.join(dst_dir, "*.efx.*")))
    print(f"{it} {name}: {total} files recoloured now, {files} in the pak; {verified[0]}", flush=True)


def main():
    root, work = sys.argv[1], sys.argv[2]
    for it in sys.argv[3:] or WEAPONS:
        build(root, work, it)


if __name__ == "__main__":
    main()
