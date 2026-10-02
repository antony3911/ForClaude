-- MiquellaLight: Light Weapons (Monster Hunter Wilds, REFramework)
--
-- Shows the Miquella light weapons on the hunter WITHOUT overwriting any game file:
-- while a chosen weapon is equipped, its model and material are swapped at runtime for
-- ours (the same technique as MDF-XL's weapon transmog). Pick the weapon in the
-- REFramework menu; the choice is remembered per original model path.
--
-- Also hides the light weapons while sheathed (they have no scabbard). Do not run this
-- together with MiquellaLight_HideSheathed: this script replaces it.
--
-- Our model files must be installed (patch pak) at the paths listed in KITS.
--
-- STATUS: untested draft, written before the game was available. Calls follow MDF-XL
-- (SilverEzredes/MDF-XL) and the REFramework docs. Every game call is wrapped in pcall.
-- Visual only: nothing about the weapon's stats or moves changes.

local CONFIG_PATH = "MiquellaLight/Weapons.json"
local MESH = "via.render.Mesh"
local CHAIN2 = "via.motion.Chain2"
-- An empty physics chain, used by MDF-XL when the new model has no physics.
local NULL_CHAIN = "Art/Model/Item/it00/99/it0099_0000_0.chain2"
local CHECK_EVERY = 20       -- frames between checks

-- Our models. Paths are relative to natives/STM/ without the numeric extension.
-- glow: materials whose Emissive_Intensity the Glow slider scales, with their mdf2 value.
-- demon: demon-mode side-blade materials and their stage (hidden outside demon mode).
-- Phial gauges (switch axe, charge blade): one material per floating phial.
local PHIALS = { "MiquellaGauge1", "MiquellaGauge2", "MiquellaGauge3", "MiquellaGauge4", "MiquellaGauge5" }
local BOTTLE_FIELDS = { "_ActionEnterBinNum", "_BottleNum" }
-- Charge parts that stay bright gold whatever the level's colour (strands on a white-hot blade).
local PART_GOLD = { 1.0, 0.62, 0.12 }
-- Charge level fields (candidates from the game's type names; the first found is used).
local CHARGE_FIELDS ={ "_ChargeLv", "_ChargeLevel", "_EffectChargeLevel", "_ChargeLvEffect" }

-- Mode morphs (switch axe, charge blade; user 2026-10-02: swapping models flashed, the weapon
-- should change shape): both modes are one model. Written by build_weapon_kit.py
-- (<kit>/<model>_morph.lua): joints with their pivot (bind pose) and their pose in the base
-- mode and the other (missing: the bind pose), file-space metres and xyzw quaternions; fades:
-- materials shown in one mode only; second: the sub weapon (the shield) fades out toward the
-- other mode. Windows are shares of the morph's progress (0 base mode, 1 the other), eased.
local MORPH_SA = {
    seconds = 0.45,
    joints = {
        { name = "MQ_Blade0", pivot = { -0.095, 0.0, 1.178 }, alt = { pos = { -0.0334, 0.0, 1.975 }, rot = { -0.26449, 0.0, 0.96439, 0.0 } }, win = { 0.1, 0.9 } },
        { name = "MQ_Fin0", pivot = { -0.0334, 0.0, 1.975 }, base = { pos = { -0.095, 0.0, 1.178 }, rot = { -0.26449, 0.0, 0.96439, 0.0 } }, win = { 0.1, 0.9 } },
        { name = "MQ_Blade1", pivot = { -0.095, 0.0, 1.064 }, alt = { pos = { 0.0445, -0.0, 1.6666 }, rot = { -0.61489, 0.0, 0.78862, 0.0 } }, win = { 0.1, 0.9 } },
        { name = "MQ_Fin1", pivot = { 0.0445, -0.0, 1.6666 }, base = { pos = { -0.095, 0.0, 1.064 }, rot = { -0.61489, 0.0, 0.78862, 0.0 } }, win = { 0.1, 0.9 } },
        { name = "MQ_Blade2", pivot = { -0.095, 0.0, 0.95 }, alt = { pos = { 0.0941, -0.0, 1.3135 }, rot = { 0.87964, -0.0, -0.47563, 0.0 } }, win = { 0.1, 0.9 } },
        { name = "MQ_Fin2", pivot = { 0.0941, -0.0, 1.3135 }, base = { pos = { -0.095, 0.0, 0.95 }, rot = { 0.87964, -0.0, -0.47563, 0.0 } }, win = { 0.1, 0.9 } },
        { name = "MQ_SwordTip", pivot = { 0.0475, 0.016, 2.774 }, base = { pos = { 0.0475, 0.016, 1.216 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.0, 0.7 } },
        { name = "MQ_HeadHalo", pivot = { 0.0, 0.0, 1.387 }, alt = { pos = { -0.038, 0.0, 1.292 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.0, 0.6 } },
    },
    fades = {
        { mats = { "MiquellaSwordBlade", "MiquellaSwordGlow" }, show = "alt", win = { 0.0, 0.25 } },
        { mats = { "MiquellaSpikeBlade" }, show = "base", win = { 0.0, 0.35 } },
        { mats = { "MiquellaAxeBlade", "MiquellaAxeGlow" }, show = "base", win = { 0.45, 0.8 } },
        { mats = { "MiquellaFinBlade", "MiquellaFinGlow" }, show = "alt", win = { 0.35, 0.7 } },
    },
}
local MORPH_CB = {
    seconds = 0.5,
    second = { 0.0, 0.4 },
    joints = {
        { name = "MQ_Phial0", pivot = { -0.084, 0.0, 0.294 }, alt = { pos = { 0.126, -0.0, 0.952 }, rot = { -0.23359, 0.0, 0.66741, 0.70711 } }, win = { 0.2, 0.8 } },
        { name = "MQ_Phial1", pivot = { -0.026, -0.0799, 0.294 }, alt = { pos = { 0.126, -0.0, 1.057 }, rot = { -0.0524, -0.16127, 0.14971, 0.97408 } }, win = { 0.2, 0.8 } },
        { name = "MQ_Phial2", pivot = { 0.068, -0.0494, 0.294 }, alt = { pos = { 0.126, -0.0, 1.162 }, rot = { 0.15156, -0.11011, -0.43303, 0.8817 } }, win = { 0.2, 0.8 } },
        { name = "MQ_Phial3", pivot = { 0.068, 0.0494, 0.294 }, alt = { pos = { 0.126, -0.0, 1.267 }, rot = { 0.28323, 0.20578, -0.80922, 0.47181 } }, win = { 0.2, 0.8 } },
        { name = "MQ_Phial4", pivot = { -0.026, 0.0799, 0.294 }, alt = { pos = { 0.126, -0.0, 1.372 }, rot = { -0.22564, 0.69446, 0.6447, 0.2262 } }, win = { 0.2, 0.8 } },
        { name = "MQ_SwordTip", pivot = { 0.0, 0.0, 1.932 }, alt = { pos = { 0.0, 0.0, 1.232 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.1, 0.6 } },
        { name = "MQ_Rim0", pivot = { 0.042, -0.0, 1.33 }, base = { pos = { 0.0604, 0.0, 1.4088 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim1", pivot = { -0.0285, 0.0, 1.4314 }, base = { pos = { -0.0282, 0.0, 1.4721 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim2", pivot = { -0.073, 0.0, 1.5478 }, base = { pos = { -0.1277, 0.0, 1.5062 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim3", pivot = { -0.1126, 0.0, 1.6659 }, base = { pos = { -0.2313, 0.0, 1.5088 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim4", pivot = { -0.1986, 0.0, 1.6719 }, base = { pos = { -0.3319, 0.0, 1.4796 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim5", pivot = { -0.2793, 0.0, 1.5771 }, base = { pos = { -0.4227, 0.0, 1.4207 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim6", pivot = { -0.3528, 0.0, 1.4767 }, base = { pos = { -0.4975, 0.0, 1.3361 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim7", pivot = { -0.4017, 0.0, 1.3623 }, base = { pos = { -0.5511, 0.0, 1.2315 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim8", pivot = { -0.4323, 0.0, 1.2416 }, base = { pos = { -0.58, 0.0, 1.1141 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim9", pivot = { -0.445, 0.0, 1.1178 }, base = { pos = { -0.5822, 0.0, 0.9918 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim10", pivot = { -0.4395, 0.0, 0.9934 }, base = { pos = { -0.5575, 0.0, 0.8731 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim11", pivot = { -0.4181, 0.0, 0.8708 }, base = { pos = { -0.5076, 0.0, 0.766 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim12", pivot = { -0.3844, 0.0, 0.7639 }, base = { pos = { -0.4358, 0.0, 0.6777 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim13", pivot = { -0.3325, 0.0, 0.6507 }, base = { pos = { -0.3472, 0.0, 0.6144 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim14", pivot = { -0.2694, 0.0, 0.5434 }, base = { pos = { -0.2477, 0.0, 0.5803 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim15", pivot = { -0.1988, 0.0, 0.4407 }, base = { pos = { -0.1441, 0.0, 0.5777 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim16", pivot = { -0.1116, 0.0, 0.3717 }, base = { pos = { -0.0435, 0.0, 0.6069 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim17", pivot = { -0.0993, 0.0, 0.4952 }, base = { pos = { 0.0473, 0.0, 0.6658 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim18", pivot = { -0.08, 0.0, 0.6183 }, base = { pos = { 0.1221, 0.0, 0.7504 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim19", pivot = { -0.055, 0.0, 0.7403 }, base = { pos = { 0.1757, 0.0, 0.855 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim20", pivot = { -0.0066, 0.0, 0.8528 }, base = { pos = { 0.2046, 0.0, 0.9724 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim21", pivot = { 0.0504, -0.0, 0.9569 }, base = { pos = { 0.2068, 0.0, 1.0947 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim22", pivot = { 0.0559, -0.0, 1.0813 }, base = { pos = { 0.1821, 0.0, 1.2134 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
        { name = "MQ_Rim23", pivot = { 0.0523, -0.0, 1.2058 }, base = { pos = { 0.1322, 0.0, 1.3205 }, rot = { 0.0, 0.0, 0.0, 1.0 } }, win = { 0.15, 0.85 } },
    },
    fades = {
        { mats = { "MiquellaRimGlow" }, show = "alt", win = { 0.0, 0.2 } },
        { mats = { "MiquellaEdgeBlade", "MiquellaEdgeGlow" }, show = "alt", win = { 0.45, 0.85 } },
        { mats = { "MiquellaAxeGlow", "MiquellaAxeIvory" }, show = "alt", win = { 0.5, 0.95 } },
    },
}

local KITS = {
    DualBlades = {
        label = "Miquella light blade (dual blades)",
        mesh = "Art/Model/MiquellaLight/DualBlades/wp_miquella_db.mesh",
        mdf2 = "Art/Model/MiquellaLight/DualBlades/wp_miquella_db.mdf2",
        -- Sizes are separate models (scaling the weapon's transform does not hold in Wilds).
        sizes = {
            ["1.0"] = "Art/Model/MiquellaLight/DualBlades/wp_miquella_db.mesh",
            ["1.2"] = "Art/Model/MiquellaLight/DualBlades/wp_miquella_db_s12.mesh",
            ["1.4"] = "Art/Model/MiquellaLight/DualBlades/wp_miquella_db_s14.mesh",
            ["1.6"] = "Art/Model/MiquellaLight/DualBlades/wp_miquella_db_s16.mesh",
        },
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2,
                 MiquellaDemon1 = 1.2, MiquellaDemon2 = 1.2, MiquellaDemon3 = 1.2 },
        demon = { MiquellaDemon1 = 1, MiquellaDemon2 = 2, MiquellaDemon3 = 3 },
    },
    -- One size each, matched to the game's originals (build_weapon_kit.py).
    GreatSword = {
        label = "Miquella light blade (great sword)",
        mesh = "Art/Model/MiquellaLight/GreatSword/wp_miquella_gs.mesh",
        mdf2 = "Art/Model/MiquellaLight/GreatSword/wp_miquella_gs.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2,
                 MiquellaCharge1 = 1.2, MiquellaCharge2 = 1.2, MiquellaCharge3 = 1.2 },
        -- Rings on the spine: bone pivots in the model's space (build_weapon_kit.py log).
        floaters = { mode = "swing", joints = {
            { name = "MQ_Ring0", pos = { 0.0456, 0.0, 1.2189 } },
            { name = "MQ_Ring1", pos = { 0.0222, 0.0, 1.4818 } },
            { name = "MQ_Ring2", pos = { -0.0217, 0.0, 1.7585 } },
            -- The big ring around the blade near the hilt hovers like the bowgun's rings.
            { name = "MQ_BladeHalo", pos = { -0.0240, 0.0, 0.6833 }, mode = "hover" } } },
        -- Charge level 0-3 (candidates from the game's type names; the first found is used).
        -- Strands of light round the blade grow a level at a time, sparks at full (user's pick
        -- 2026-10-02, "A"); they stay bright gold while the blade turns white.
        charge = { levels = 3, fields = CHARGE_FIELDS, band = true,
                   parts = { MiquellaCharge1 = 1, MiquellaCharge2 = 2, MiquellaCharge3 = 3 }, partColor = PART_GOLD },
    },
    LightBowgun = {
        label = "Miquella light bowgun",
        mesh = "Art/Model/MiquellaLight/LightBowgun/wp_miquella_lbg.mesh",
        mdf2 = "Art/Model/MiquellaLight/LightBowgun/wp_miquella_lbg.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2,
                 MiquellaGauge1 = 1.2, MiquellaGauge2 = 1.2, MiquellaGauge3 = 1.2 },
        -- Rings along the beam, muzzle ring last.
        floaters = { mode = "hover", joints = {
            { name = "MQ_Halo0", pos = { 0.0, -0.19, 0.380 } },
            { name = "MQ_Halo1", pos = { 0.0, -0.19, 0.476 } },
            { name = "MQ_Halo2", pos = { 0.0, -0.19, 0.572 } },
            { name = "MQ_Halo3", pos = { 0.0, -0.19, 0.668 } },
            { name = "MQ_Halo4", pos = { 0.0, -0.19, 0.748 } } } },
        -- Rapid-fire gauge on the three drops (Gauge1-3), brighter in rapid-fire mode.
        gauge = { dots = { "MiquellaGauge1", "MiquellaGauge2", "MiquellaGauge3" },
                  fields = { "_RapidAmmoGauge", "_RapidFireAmmo_Gauge", "_RapidFireTimer_Gauge", "_RapidModeTimer" },
                  mode = { "_IsRapidMode", "_IsRapidShotBoost" } },
    },
    LongSword = {
        label = "Miquella light blade (long sword)",
        mesh = "Art/Model/MiquellaLight/LongSword/wp_miquella_ls.mesh",
        mdf2 = "Art/Model/MiquellaLight/LongSword/wp_miquella_ls.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2, MiquellaBand1 = 1.2, MiquellaBand2 = 1.2,
                 MiquellaBand3 = 1.2, MiquellaBand4 = 1.2, MiquellaBand5 = 1.2, MiquellaBand6 = 1.2, MiquellaBand7 = 1.2,
                 MiquellaBand8 = 1.2, MiquellaBlade1 = 1.2, MiquellaBlade2 = 1.2, MiquellaBlade3 = 1.2,
                 MiquellaBlade4 = 1.2, MiquellaBlade5 = 1.2, MiquellaBlade6 = 1.2, MiquellaBlade7 = 1.2,
                 MiquellaBlade8 = 1.2, MiquellaCharge1 = 1.2, MiquellaCharge2 = 1.2, MiquellaCharge3 = 1.2 },
        -- The two rings in place of a tsuba hover.
        floaters = { mode = "hover", joints = {
            { name = "MQ_Tsuba0", pos = { 0.0152, 0.0, 0.1900 } },
            { name = "MQ_Tsuba1", pos = { 0.0152, 0.0, 0.2052 } } } },
        -- Spirit gauge levels (none / white / yellow / red): pale gold -> gold -> bright gold ->
        -- white light, the temper line's band of light running from yellow on (DESIGN). The game
        -- counts 1 none .. 4 red (recorded 2026-10-02: <AuraLevel>k__BackingField; the guess
        -- _AuraLevel did not exist). The band runs along the temper line's 8 pieces (MiquellaBand1-8,
        -- root -> tip; the material's own MoveEmit showed nothing in the game, user 2026-10-02) and,
        -- since the thin line alone did not show either (the blade already burns white at Glow 5),
        -- through the blade's matching pieces (MiquellaBlade1-8): a white pulse, the rest of the
        -- blade dimmed a little while it runs so the pulse stands out. MiquellaBlade: the older
        -- model (one blade), until the new pak is in.
        charge = { levels = 3, fields = { "<AuraLevel>k__BackingField", "_AuraLevel" }, offset = -1, look = "spirit",
                   band = true, bandFrom = 2, bandWidth = 0.16, bandBoost = 4.0, bandPeriod = 0.8, bandDim = 0.6,
                   bands = { "MiquellaBand1", "MiquellaBand2", "MiquellaBand3", "MiquellaBand4", "MiquellaBand5",
                             "MiquellaBand6", "MiquellaBand7", "MiquellaBand8" },
                   blades = { "MiquellaBlade1", "MiquellaBlade2", "MiquellaBlade3", "MiquellaBlade4", "MiquellaBlade5",
                              "MiquellaBlade6", "MiquellaBlade7", "MiquellaBlade8" },
                   weights = { MiquellaBlade = 1.0, MiquellaGlow = 0.4 },
                   -- Two strands of light round the blade, a third more each level from white on
                   -- (user's pick 2026-10-02, "B"), bright gold against the white red level.
                   parts = { MiquellaCharge1 = 1, MiquellaCharge2 = 2, MiquellaCharge3 = 3 }, partColor = PART_GOLD },
    },
    -- The other weapons (build_weapon_kit.py, 2026-10-02). Shields are looks of their own for
    -- the sub weapon (_1) model; `shield` names the look that goes with a weapon's shield.
    SwordShield = {
        label = "Miquella light blade (sword & shield)",
        mesh = "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns.mesh",
        mdf2 = "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2, MiquellaTiming = 1.2, MiquellaBurst = 1.2 },
        -- Perfect Rush (user's pick 2026-10-02, "S2"): in the game's cJustRush* actions a ring
        -- rides down the blade to the guard (MQ_TimingRing, built at the guard: slide lifts it by
        -- entry.slide) as each timed blow comes; a Perfect bursts into rings and rays. The window
        -- is the game's canJustRushCombo0-2 when they answer, else the ring falls in `fall` s;
        -- a Perfect is _IsJustRush turning true. Guessed from the game's type names: the events
        -- are logged (fields_app_cHunterWp01Handling.json, events / actions) to tune.
        floaters = { mode = "fixed", joints = { { name = "MQ_TimingRing", pos = { 0.0, 0.0, 0.1500 }, slide = true } } },
        timing = { actions = "JustRush", ring = "MiquellaTiming", burst = "MiquellaBurst", rise = 0.80, fall = 0.45,
                   checks = { "canJustRushCombo0", "canJustRushCombo1", "canJustRushCombo2" },
                   success = { "_IsJustRush" } },
        shield = "SwordShield_Shield",
    },
    SwordShield_Shield = {
        label = "Miquella energy shield (sword & shield)",
        mesh = "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns_shield.mesh",
        mdf2 = "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns_shield.mdf2",
        glow = { MiquellaGlow = 1.2 },
    },
    -- Test (2026-10-02): the shield with a film of light. A (aura effect) and B (bubble effect)
    -- showed nothing in the game, C (a weapon's inner glow) came out hard-edged in patches (user);
    -- D: our glowing material, see-through by a partial Dissolve in bands that thin toward the rim.
    SwordShield_ShieldC = {
        label = "Miquella energy shield (sword & shield) + translucent film C: soft inner glow",
        mesh = "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns_shield_volume.mesh",
        mdf2 = "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns_shield_volume.mdf2",
        glow = { MiquellaGlow = 1.2 },
    },
    SwordShield_ShieldD = {
        label = "Miquella energy shield (sword & shield) + film D: our glow, dithered, soft edge",
        mesh = "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns_shield_film.mesh",
        mdf2 = "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns_shield_film.mdf2",
        glow = { MiquellaGlow = 1.2 },
    },
    Hammer = {
        label = "Miquella sun lantern (hammer)",
        mesh = "Art/Model/MiquellaLight/Hammer/wp_miquella_hm.mesh",
        mdf2 = "Art/Model/MiquellaLight/Hammer/wp_miquella_hm.mdf2",
        glow = { MiquellaGlow = 1.2, MiquellaCharge1 = 1.2, MiquellaCharge2 = 1.2, MiquellaCharge3 = 1.2,
                 MiquellaArmillary1 = 1.2, MiquellaArmillary2 = 1.2, MiquellaArmillary3 = 1.2 },
        -- The armillary sphere round the sun (user's pick 2026-10-02, "H4"): a great ring more
        -- each level, each on its bone at the head's centre turning about its own axis (spin:
        -- the axis), faster each level, like a gyroscope.
        floaters = { mode = "hover", spin = { axis = { 0, 0, 1 }, dps = { 0, 70, 140, 260 } }, joints = {
            { name = "MQ_BeltHalo", pos = { 0.0, 0.0, 1.3160 } },
            { name = "MQ_Arm0", pos = { 0.0, 0.0, 1.3160 }, spin = { 0, 0, 1 } },
            { name = "MQ_Arm1", pos = { 0.0, 0.0, 1.3160 }, spin = { -1, 0, 0 } },
            { name = "MQ_Arm2", pos = { 0.0, 0.0, 1.3160 }, spin = { 0.3, 1, 0 } } } },
        -- Charge (user, 2026-10-02): a cone of rings beyond each face grows a level at a time, the
        -- light goes bright gold -> white; the game's glow on the hunter is gone (HammerFX pak).
        charge = { levels = 3, fields = { "<ChargeLv>k__BackingField", "<ChargeLvEffect>k__BackingField" },
                   weights = { MiquellaGlow = 1.0 }, colored = { "MiquellaGlow" },
                   parts = { MiquellaCharge1 = 1, MiquellaCharge2 = 2, MiquellaCharge3 = 3,
                             MiquellaArmillary1 = 1, MiquellaArmillary2 = 2, MiquellaArmillary3 = 3 } },
    },
    HuntingHorn = {
        label = "Miquella lyre of light (hunting horn)",
        mesh = "Art/Model/MiquellaLight/HuntingHorn/wp_miquella_hh.mesh",
        mdf2 = "Art/Model/MiquellaLight/HuntingHorn/wp_miquella_hh.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2 },
    },
    Lance = {
        label = "Miquella light lance",
        mesh = "Art/Model/MiquellaLight/Lance/wp_miquella_ln.mesh",
        mdf2 = "Art/Model/MiquellaLight/Lance/wp_miquella_ln.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2,
                 MiquellaCharge1 = 1.2, MiquellaCharge2 = 1.2, MiquellaCharge3 = 1.2, MiquellaChargeTip = 1.2 },
        -- Charge (user's pick 2026-10-02, "A, the spiral drill"): strands of light grow from the
        -- vamplate toward the point a level at a time, brighter each level, and turn about the
        -- lance's axis on their bone (MQ_Drill), faster each level; at full charge the point's
        -- longer blade. Only on the lance: the game's glow on the hunter is gone (LanceFX pak).
        floaters = { mode = "fixed", spin = { axis = { 0, 0, 1 }, dps = { 0, 90, 200, 420 } }, joints = {
            { name = "MQ_Drill", pos = { 0.0, 0.0, 1.7510 }, spin = true } } },
        charge = { levels = 3, fields = { "_FinishChargeLevel", "_FinishChargeLevelForAction" },
                   weights = { MiquellaBlade = 1.0, MiquellaGlow = 0.6, MiquellaTemper = 1.0 },
                   colored = { "MiquellaBlade", "MiquellaGlow" },
                   parts = { MiquellaCharge1 = 1, MiquellaCharge2 = 2, MiquellaCharge3 = 3, MiquellaChargeTip = 3 } },
        shield = "Lance_Shield",
    },
    Lance_Shield = {
        label = "Miquella energy shield (lance)",
        mesh = "Art/Model/MiquellaLight/Lance/wp_miquella_ln_shield.mesh",
        mdf2 = "Art/Model/MiquellaLight/Lance/wp_miquella_ln_shield.mdf2",
        glow = { MiquellaGlow = 1.2 },
    },
    Gunlance = {
        label = "Miquella light gunlance",
        mesh = "Art/Model/MiquellaLight/Gunlance/wp_miquella_gl.mesh",
        mdf2 = "Art/Model/MiquellaLight/Gunlance/wp_miquella_gl.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2, MiquellaCore = 1.2,
                 MiquellaFilament = 1.2 },
        -- MQ_SpringTop: the ivory spring's top; packing it moves it 0.636 toward the root
        -- (the spring at 45 % of its length). MQ_FilamentTop: the gold thread's eye (user's pick
        -- 2026-10-02, "G3"): drawn out from the core (stretch: its root's height) toward the
        -- muzzle as the charge builds, while the spring packs the other way.
        floaters = { mode = "hover", joints = {
            { name = "MQ_Halo0", pos = { 0.0, 0.0, 1.0140 } },
            { name = "MQ_Halo1", pos = { 0.0, 0.0, 1.4950 } },
            { name = "MQ_SpringTop", pos = { 0.0, 0.0, 1.6640 }, pack = -0.636, mode = "fixed" },
            { name = "MQ_FilamentTop", pos = { 0.0, 0.0, 2.0150 }, stretch = 0.4290, mode = "fixed" } } },
        -- Reload, charged shelling and Wyvern's Fire wind the spring (user, 2026-10-02); charged
        -- shelling's levels light it gold -> bright gold -> white gold. Fields guessed from the
        -- game's type names (menu: "Gunlance:").
        -- Recorded 2026-10-02: no Wyvern's Fire timer; its gauge (_RyuugekiGauge, 1..2) drops by
        -- one when it is used -> wind the spring for the wind-up; a shell fired lowers
        -- _ChargeShotBulletNum -> a short press.
        gunlance = { reload = { "_IsReload", "_IsContinueReload" }, chargeShot = { "_ChargeShotElapsedTimer" },
                     wyvern = { "_RyuugekiChargeTimer" }, wyvernGauge = { "_RyuugekiGauge" },
                     shells = { "_ChargeShotBulletNum" },
                     charge = { levels = 3, look = "whiteGold", colored = { "MiquellaBlade", "MiquellaGlow", "MiquellaCore" },
                                weights = { MiquellaBlade = 1.0, MiquellaGlow = 0.6, MiquellaCore = 1.5 },
                                parts = { MiquellaFilament = 1 } } },
        shield = "Gunlance_Shield",
    },
    Gunlance_Shield = {
        label = "Miquella energy shield (gunlance)",
        mesh = "Art/Model/MiquellaLight/Gunlance/wp_miquella_gl_shield.mesh",
        mdf2 = "Art/Model/MiquellaLight/Gunlance/wp_miquella_gl_shield.mdf2",
        glow = { MiquellaGlow = 1.2 },
    },
    SwitchAxe = {
        label = "Miquella trident axe (switch axe)",
        mesh = "Art/Model/MiquellaLight/SwitchAxe/wp_miquella_sa.mesh",
        mdf2 = "Art/Model/MiquellaLight/SwitchAxe/wp_miquella_sa.mdf2",
        glow = { MiquellaAxeBlade = 1.2, MiquellaAxeGlow = 1.2, MiquellaSpikeBlade = 1.2, MiquellaSwordBlade = 1.2,
                 MiquellaSwordGlow = 1.2, MiquellaFinBlade = 1.2, MiquellaFinGlow = 1.2, MiquellaGlow = 1.2,
                 MiquellaGauge1 = 1.2, MiquellaGauge2 = 1.2, MiquellaGauge3 = 1.2, MiquellaGauge4 = 1.2,
                 MiquellaGauge5 = 1.2 },
        -- The five floating phials are the switch gauge; amped (awakened) lights the sword, power
        -- axe the axe blades bright gold (DESIGN).
        gauges = { { key = "slash", dots = PHIALS, fields = { "_SlashGauge", "_SwitchGauge", "_Gauge" } } },
        boosts = { { key = "awake", fields = { "_SwordAwakeTimer" },
                     mats = { "MiquellaSwordBlade", "MiquellaSwordGlow", "MiquellaFinBlade" } },
                   { key = "axeEnh", fields = { "_AxeEnhancedTimer" }, mats = { "MiquellaAxeBlade", "MiquellaSpikeBlade" } } },
        -- _Mode 0 axe, 1 sword (recorded 2026-10-02; "Swap modes" if it reads the wrong way round):
        -- the axe blades swing onto the sword's back as it grows out of the shaft.
        mode = { fields = { "_Mode" }, names = { "axe", "sword" }, morph = MORPH_SA },
    },
    ChargeBlade = {
        label = "Miquella light blade (charge blade)",
        mesh = "Art/Model/MiquellaLight/ChargeBlade/wp_miquella_cb.mesh",
        mdf2 = "Art/Model/MiquellaLight/ChargeBlade/wp_miquella_cb.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2, MiquellaGauge1 = 1.2,
                 MiquellaGauge2 = 1.2, MiquellaGauge3 = 1.2, MiquellaGauge4 = 1.2, MiquellaGauge5 = 1.2,
                 MiquellaRimGlow = 1.2, MiquellaEdgeBlade = 1.2, MiquellaEdgeGlow = 1.2, MiquellaAxeGlow = 1.2,
                 MiquellaSawAGlow = 1.2, MiquellaSawBGlow = 1.2, MiquellaSawCGlow = 1.2 },
        shield = "ChargeBlade_Shield",
        -- Sword: the phial ring is the sword's energy (bright gold when full); axe: the phials on
        -- its back are the loaded phials. Sword / axe enhanced light the blade (DESIGN).
        gauges = { { key = "energy", dots = PHIALS, fields = { "_SwordEnergyState" }, max = 2,
                     fullBright = true, when = "base" },
                   { key = "bottles", dots = PHIALS, fields = BOTTLE_FIELDS, count = true, when = "alt" } },
        boosts = { { key = "swordEnh", fields = { "_SwordEnhancedTimer" }, mats = { "MiquellaBlade", "MiquellaTemper" } },
                   -- Savage axe (user's pick 2026-10-02, "A"): teeth of light outside the edge, their
                   -- three sets lit in turn so they run from the horn to the beard.
                   { key = "axeEnhCB", fields = { "_AxeEnhancedTimer" }, mats = { "MiquellaBlade", "MiquellaEdgeBlade" },
                     when = "alt", chase = { "MiquellaSawAGlow", "MiquellaSawBGlow", "MiquellaSawCGlow" }, chaseHz = 15 } },
        -- _Mode 0 sword & shield, 1 axe: the shield fades out while its light gathers on the sword
        -- as an oval and reshapes into the bardiche (user, 2026-10-02).
        mode = { fields = { "_Mode" }, names = { "sword & shield", "axe" }, morph = MORPH_CB },
    },
    ChargeBlade_Shield = {
        label = "Miquella energy shield (charge blade)",
        mesh = "Art/Model/MiquellaLight/ChargeBlade/wp_miquella_cb_shield.mesh",
        mdf2 = "Art/Model/MiquellaLight/ChargeBlade/wp_miquella_cb_shield.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2, MiquellaGauge1 = 1.2,
                 MiquellaGauge2 = 1.2, MiquellaGauge3 = 1.2, MiquellaGauge4 = 1.2, MiquellaGauge5 = 1.2 },
        -- The five phials on the rim are the loaded phials; shield enhanced (red shield): the halo
        -- and the tree sigil bright gold.
        gauges = { { key = "bottles", dots = PHIALS, fields = BOTTLE_FIELDS, count = true } },
        boosts = { { key = "shieldEnh", fields = { "_ShieldEnhancedTimer" }, mats = { "MiquellaGlow" } } },
    },
    InsectGlaive = {
        label = "Miquella light glaive (insect glaive)",
        mesh = "Art/Model/MiquellaLight/InsectGlaive/wp_miquella_ig.mesh",
        mdf2 = "Art/Model/MiquellaLight/InsectGlaive/wp_miquella_ig.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2 },
        -- The extracts (rot, frost, frenzied flame) circle the top blade (orbit: their slot); they
        -- are flowers (user's pick 2026-10-02, style 2), so they keep facing out while circling
        -- and turn slowly about their own centre (face, spin degrees a second).
        floaters = { mode = "hover", orbit = { center = { 0.0, 0.0, 1.4160 }, radius = 0.1408, hz = 0.4,
                                               face = true, spin = 25 },
                     joints = {
            { name = "MQ_TopHalo", pos = { 0.0, 0.0, 1.2560 } },
            { name = "MQ_BottomHalo", pos = { 0.0, 0.0, -1.2880 } },
            { name = "MQ_OrbRed", pos = { 0.0, 0.1408, 1.4160 }, orbit = 0 },
            { name = "MQ_OrbWhite", pos = { -0.1219, -0.0704, 1.4160 }, orbit = 1 },
            { name = "MQ_OrbOrange", pos = { 0.1219, -0.0704, 1.4160 }, orbit = 2 } } },
        -- Charge (user, 2026-10-02): gold -> bright gold -> white gold.
        charge = { levels = 2, fields = { "<ChargeLv>k__BackingField" }, look = "whiteGold2" },
        -- An orb shows while its extract is lit (the game's timers); all three: the blade bright gold.
        extracts = { orbs = { MiquellaExtractRed = "_ExtractTimerRed", MiquellaExtractWhite = "_ExtractTimerWhite",
                              MiquellaExtractOrange = "_ExtractTimerOrange" },
                     triple = "_ExtractTimerTripple" },
        kinsect = "Kinsect",
    },
    -- The kinsect: a golden swallowtail of light (A, solid gold wings). Not a weapon look: it goes
    -- on the insect glaive's kinsect (found through the weapon handling's _Insect).
    Kinsect = {
        label = "Miquella golden swallowtail (kinsect)",
        part = true,
        mesh = "Art/Model/MiquellaLight/Kinsect/wp_miquella_kinsect.mesh",
        mdf2 = "Art/Model/MiquellaLight/Kinsect/wp_miquella_kinsect.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2 },
        -- The wings on bones of our own (children of Body, at the wings' roots; local positions):
        -- a slow butterfly beat about the body's length (+Z), up toward the back (+Y). The game's
        -- own wing beat was so fast our gold wings flickered (user, 2026-10-02).
        floaters = { mode = "flap", flap = { hz = 1.6, base = 12, amp = 26 }, joints = {
            { name = "MQ_WingL", pos = { 0.0, 0.0023, 0.0027 }, flap = 1 },
            { name = "MQ_WingR", pos = { 0.0, 0.0023, 0.0027 }, flap = -1 } } },
    },
    Bow = {
        label = "Miquella light bow",
        mesh = "Art/Model/MiquellaLight/Bow/wp_miquella_bow.mesh",
        mdf2 = "Art/Model/MiquellaLight/Bow/wp_miquella_bow.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2,
                 MiquellaGauge1 = 1.2, MiquellaGauge2 = 1.2, MiquellaGauge3 = 1.2,
                 MiquellaCharge1 = 1.2, MiquellaCharge2 = 1.2, MiquellaCharge3 = 1.2 },
        -- The rings ahead of the arrow hover; while drawing they pack toward the bow like a
        -- spring being wound (pack: metres along +Z when fully packed, build_weapon_kit.py log).
        floaters = { mode = "hover", joints = {
            { name = "MQ_RestHalo", pos = { 0.0, 0.036, 0.0540 } },
            { name = "MQ_Ring0", pos = { 0.0, 0.036, 0.2700 }, pack = -0.0630 },
            { name = "MQ_Ring1", pos = { 0.0, 0.036, 0.4176 }, pack = -0.1602 },
            { name = "MQ_Ring2", pos = { 0.0, 0.036, 0.5652 }, pack = -0.2574 },
            { name = "MQ_Ring3", pos = { 0.0, 0.036, 0.7128 }, pack = -0.3546 },
            { name = "MQ_Ring4", pos = { 0.0, 0.036, 0.8604 }, pack = -0.4518 },
            { name = "MQ_Ring5", pos = { 0.0, 0.036, 1.0080 }, pack = -0.5490 } } },
        -- Charge level (bright gold -> white gold) and drawing; the ring pairs Gauge1-3 light
        -- one pair per level. Field names guessed from the game's type names, as for the great sword.
        -- (recorded 2026-10-02: the level rests at 1; drawing = the string held by the hand)
        -- The vine on the limbs opens flowers of light, two more a level, the tips' at full
        -- charge (user's pick 2026-10-02, "A"): parts = material -> level.
        bow = { levels = 3, rings = { "MiquellaGauge1", "MiquellaGauge2", "MiquellaGauge3" },
                fields = { "<ChargeLv>k__BackingField" }, draw = { "_IsBowStringConstToHand" },
                parts = { MiquellaCharge1 = 1, MiquellaCharge2 = 2, MiquellaCharge3 = 3 } },
        shield = "Bow_Quiver",
    },
    -- The bow's quiver (_1), two designs to pick from in the game (2026-10-02).
    Bow_Quiver = {
        label = "Miquella quiver A: woven ivory cage",
        mesh = "Art/Model/MiquellaLight/Bow/wp_miquella_bow_quiver_a.mesh",
        mdf2 = "Art/Model/MiquellaLight/Bow/wp_miquella_bow_quiver_a.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2 },
        floaters = { mode = "hover", joints = {
            { name = "MQ_QuiverHalo", pos = { -0.6120, 0.0, -0.0100 } },
            { name = "MQ_QuiverDrop", pos = { 0.5400, 0.0, -0.0100 } } } },
    },
    Bow_QuiverB = {
        label = "Miquella quiver B: floating bundle of arrows",
        mesh = "Art/Model/MiquellaLight/Bow/wp_miquella_bow_quiver_b.mesh",
        mdf2 = "Art/Model/MiquellaLight/Bow/wp_miquella_bow_quiver_b.mdf2",
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2 },
        floaters = { mode = "hover", joints = {
            { name = "MQ_QuiverHalo0", pos = { 0.1670, 0.0, -0.0100 } },
            { name = "MQ_QuiverHalo1", pos = { -0.2700, 0.0, -0.0100 } },
            { name = "MQ_QuiverDrop", pos = { 0.5115, 0.0, -0.0100 } } } },
    },
    HeavyBowgun = {
        label = "Miquella heavy bowgun",
        mesh = "Art/Model/MiquellaLight/HeavyBowgun/wp_miquella_hbg.mesh",
        mdf2 = "Art/Model/MiquellaLight/HeavyBowgun/wp_miquella_hbg.mdf2",
        glow = { MiquellaGlow = 1.2, MiquellaGauge1 = 1.2, MiquellaGauge2 = 1.2, MiquellaGauge3 = 1.2 },
        -- The conduit and muzzle rings and the three phials hover like the light bowgun's
        -- (user, 2026-10-02).
        floaters = { mode = "hover", joints = {
            { name = "MQ_Halo0", pos = { 0.0, -0.194, 0.3420 } },
            { name = "MQ_Halo1", pos = { 0.0, -0.194, 0.6280 } },
            { name = "MQ_Halo2", pos = { 0.0, -0.194, 1.0440 } },
            { name = "MQ_Halo3", pos = { 0.0, -0.194, 1.0050 } },
            { name = "MQ_Phial0", pos = { 0.0, 0.0087, 0.1588 } },
            { name = "MQ_Phial1", pos = { 0.0, 0.0087, 0.3148 } },
            { name = "MQ_Phial2", pos = { 0.0, 0.0087, 0.4708 } } } },
    },
}
-- Second-model looks (names with "_Shield" or "_Quiver") go on a weapon's shield or quiver
-- model, the others on the weapon.
local function is_shield_kit(name)
    return name:find("_Shield", 1, true) ~= nil or name:find("_Quiver", 1, true) ~= nil
end
local SIZE_NAMES = { "1.0", "1.2", "1.4", "1.6" }
local KIT_NAMES = { "(original)" }
for name in pairs(KITS) do KIT_NAMES[#KIT_NAMES + 1] = name end
local function by_name(a, b)
    if a == "(original)" then return true end
    if b == "(original)" then return false end
    return a < b
end
table.sort(KIT_NAMES, by_name)
local MAIN_NAMES = {}
for _, n in ipairs(KIT_NAMES) do
    if not is_shield_kit(n) and not (KITS[n] and KITS[n].part) then MAIN_NAMES[#MAIN_NAMES + 1] = n end
end

local config = {
    enabled = true,
    hideSheathed = true,
    -- weapon type (it02 = dual blades, it00 = great sword, it13 = light bowgun ...) -> kit name:
    -- one look for every weapon of that type (user, 2026-10-02)
    assignType = {},
    -- weapon type -> shield look for that type's shields (_1), or "(original)"; unset = the
    -- weapon look's own `shield`
    assignShield = {},
    -- original .mesh path -> kit name (older versions; moved into assignType on load)
    assign = {},
    -- the per-model choices that were moved, kept only to recognise our model after a reload
    migratedFrom = {},
    -- In-game tuning: glow multiplies the kit's Emissive_Intensity; size picks the model.
    glow = 1.0,
    size = "1.4",
    -- Floating rings (great sword spine, light bowgun beam): on/off and how lively.
    float = true,
    floatStrength = 1.0,
    -- The bow's charge field counts from 0 (level 1 = 0): set in the menu if the rings light late.
    bowFrom0 = false,
    -- While drawing, the bow's rings move onto the drawn arrow's line (found in the scene).
    bowFollowArrow = true,
    -- weapon type -> true: the mode field reads the other way round (switch axe, charge blade)
    modeInvert = {},
    -- Record the weapon handling's number / true-false fields while playing (for Claude to find
    -- the charge, draw, mode ... fields): reframework/data/MiquellaLight/fields_<type>.json
    recordFields = true,
    -- slot name -> { original = game's .mesh, chain = its physics chain } while swapped, so a
    -- script reload (REFramework "Reset scripts") can pick up a weapon that already shows our model.
    swappedFrom = {},
}
local saved = json.load_file(CONFIG_PATH)
if saved then
    for k, v in pairs(saved) do config[k] = v end
end
-- An empty table is saved as JSON null; don't let that replace the assignment table.
if type(config.assign) ~= "table" then config.assign = {} end
if type(config.assignType) ~= "table" then config.assignType = {} end
if type(config.assignShield) ~= "table" then config.assignShield = {} end
if type(config.migratedFrom) ~= "table" then config.migratedFrom = {} end
if type(config.modeInvert) ~= "table" then config.modeInvert = {} end
if type(config.swappedFrom) ~= "table" then config.swappedFrom = {} end
local function save_config() json.dump_file(CONFIG_PATH, config) end

-- Weapon type of a model path: Art/Model/Item/it13/00/0001/it1300_0001_0.mesh -> "it13".
local function weapon_type(path)
    return path and path:match("[Ii]tem/(it%d%d)/") or nil
end
local TYPE_LABELS = { it00 = "great swords", it01 = "swords", it02 = "dual blades", it03 = "long swords",
                      it04 = "hammers", it05 = "hunting horns", it06 = "lances", it07 = "gunlances",
                      it08 = "switch axes", it09 = "charge blades", it10 = "insect glaives", it11 = "bows",
                      it12 = "heavy bowguns", it13 = "light bowguns" }

-- Model number of a weapon path: ..._0.mesh is the weapon, ..._1.mesh the second model: the
-- dual blades' other blade, or a shield (sword & shield, lance, gunlance, charge blade), or the
-- bow's quiver, or the long sword's scabbard (which keeps its game look).
local function model_index(path) return path and path:match("_(%d+)%.mesh$") or nil end
local BOTH_HANDS = { it02 = true }        -- dual blades: both models take the weapon's look

-- Older configs chose a look per model: make it the look of that model's weapon type.
do
    local moved = false
    for path, kit in pairs(config.assign) do
        local t = weapon_type(path)
        if t then
            if model_index(path) == "1" and not BOTH_HANDS[t] then
                if is_shield_kit(kit) then config.assignShield[t] = config.assignShield[t] or kit end
            else
                config.assignType[t] = config.assignType[t] or kit
            end
            config.migratedFrom[path] = kit
            config.assign[path] = nil
            moved = true
        end
    end
    if moved then save_config() end
end

-- The look a game model gets (nil: leave it as the game made it).
local function assigned_kit(original)
    if config.assign[original] then return config.assign[original] end
    local t = weapon_type(original)
    local main = t and config.assignType[t]
    if not main then return nil end
    local idx = model_index(original)
    -- The insect glaive's kinsect (Item/it10/03/...): the look's kinsect.
    if original:match("[Ii]tem/it10/03/") then return KITS[main] and KITS[main].kinsect or nil end
    if idx == "0" or BOTH_HANDS[t] then return main end
    if idx ~= "1" then return nil end
    local pick = config.assignShield[t]
    if pick == "(original)" then return nil end
    if pick and KITS[pick] then return pick end
    return KITS[main] and KITS[main].shield or nil
end

-- Shield looks offered for a type: the ones named after its weapon look's shield.
local function shield_names(t)
    local main = config.assignType[t]
    local prefix = main and KITS[main] and KITS[main].shield
    local out = { "(original)" }
    for _, n in ipairs(KIT_NAMES) do
        if is_shield_kit(n) and (not prefix or n:sub(1, #prefix) == prefix) then out[#out + 1] = n end
    end
    return out
end

local function try(fn, ...)
    local ok, result = pcall(fn, ...)
    if ok then return result end
    return nil
end

-- ------------------------------------------------------------------ resources

local holders = {}
local retryAt = {}
local function holder(typeName, path)
    local key = typeName .. "|" .. path
    -- A failed load is tried again after a while (the pak may not have been mounted yet).
    if holders[key] == false and os.clock() >= (retryAt[key] or 0) then holders[key] = nil end
    if holders[key] == nil then
        retryAt[key] = os.clock() + 5
        holders[key] = try(function()
            local res = sdk.create_resource(typeName, path):add_ref()
            return res:create_holder(typeName .. "Holder"):add_ref()
        end) or false
    end
    return holders[key] or nil
end

-- Load every kit's model and material now: a resource created in the same frame as the swap
-- is not loaded yet, and the weapon showed nothing until it was equipped again (user).
for _, kit in pairs(KITS) do
    holder("via.render.MeshMaterialResource", kit.mdf2)
    holder("via.render.MeshResource", kit.mesh)
    for _, m in pairs(kit.sizes or {}) do holder("via.render.MeshResource", m) end
end

local function resource_path(res)
    local s = res and try(function() return res:ToString() end)
    if not s then return nil end
    return (s:gsub("^Resource%[", ""):gsub("%]$", ""))
end

local function component(go, typeName)
    return try(function() return go:call("getComponent(System.Type)", sdk.typeof(typeName)) end)
end

-- ------------------------------------------------------------------ state

local isWeaponDrawn = false
local frame = 0
local lastError = ""
-- Per weapon GameObject (by address) that we swapped: { go, original, chain }
local swapped = {}
-- original .mesh path -> its physics chain path, as first seen
local chainOf = {}
-- What the UI shows for each slot.
local slots = {}

-- If a game update renamed this method, keep the script running (weapons stay visible).
local hookOk = pcall(function()
    sdk.hook(sdk.find_type_definition("app.HunterCharacter"):get_method("checkWeaponOn()"),
    function(args)
        local hunter = sdk.to_managed_object(args[2])
        if hunter ~= nil and hunter:ToString():match("MasterPlayer") then
            isWeaponDrawn = hunter._IsWeaponOn
        end
    end,
    function(retval) return retval end
    )
end)
if not hookOk then isWeaponDrawn = true end

local function player_character()
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    if not (master and try(function() return master:get_Valid() end)) then return nil end
    return try(function() return master:get_Character() end)
end

-- The hunter's current actions: the type names of what its base and sub action controllers run
-- (e.g. app.Wp07Action.cRyuugekiStart; method and class names found in the game's type names,
-- 2026-10-02). Logged when they change (actionLog, saved with the field recorder's file).
local ACTION_CONTROLLERS = { "get_BaseActionController", "get_SubActionController" }
local actionNow, actionLog = "", {}
local actionObjs = {}                -- the current action objects, { name, obj } (the rush trace reads them)

local function current_actions(chr)
    local names = {}
    actionObjs = {}
    for _, getter in ipairs(ACTION_CONTROLLERS) do
        local ctl = try(function() return chr:call(getter) end)
        local act = ctl and try(function() return ctl:call("get_CurrentAction") end)
        local n = act and try(function() return act:get_type_definition():get_full_name() end)
        if n then
            names[#names + 1] = n
            actionObjs[#actionObjs + 1] = { name = n, obj = act }
        end
    end
    return table.concat(names, " + ")
end

local hunterChr = nil                -- the hunter character of this frame (the rush trace reads it)

local function update_actions(chr)
    hunterChr = chr
    local a = current_actions(chr)
    if a ~= actionNow then
        actionNow = a
        actionLog[#actionLog + 1] = string.format("%8.2f  %s", os.clock(), a ~= "" and a or "(none)")
        if #actionLog > 150 then table.remove(actionLog, 1) end
    end
end

local function set_model(go, mesh, meshPath, mdfPath, chainPath)
    local m = holder("via.render.MeshResource", meshPath)
    local d = holder("via.render.MeshMaterialResource", mdfPath)
    if not (m and d) then
        lastError = "Could not load " .. meshPath .. " (is the patch pak installed?)"
        return false
    end
    try(function() mesh:set_Enabled(false) end)
    try(function() mesh:setMesh(m) end)
    try(function() mesh:set_Material(d) end)
    try(function() mesh:set_Enabled(true) end)
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do try(function() mesh:setMaterialsEnable(i, true) end) end
    local chain = component(go, CHAIN2)
    local c = chainPath and holder("via.motion.Chain2Resource", chainPath)
    if chain and c then try(function() chain:set_ChainAsset(c) end) end
    return true
end

-- Material slots of the Emissive_Intensity parameter, found by name once per swap.
local function glow_slots(mesh, kit)
    local slots = {}
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        local base = kit.glow and kit.glow[try(function() return mesh:getMaterialName(i) end) or ""]
        if base then
            local vars = try(function() return mesh:getMaterialVariableNum(i) end) or 0
            for j = 0, vars - 1 do
                if try(function() return mesh:getMaterialVariableName(i, j) end) == "Emissive_Intensity" then
                    slots[#slots + 1] = { mat = i, var = j, base = base,
                                          name = try(function() return mesh:getMaterialName(i) end) }
                end
            end
        end
    end
    return slots
end

-- Kits whose game is in the other mode (switch axe sword mode, charge blade axe mode).
local modeOn = {}

local function kit_mesh(kit)
    return kit.sizes and kit.sizes[config.size] or kit.mesh
end

local function kit_mdf(kit)
    return kit.mdf2
end

-- Material variable index by material and variable name, found once per swap.
local function material_vars(mesh)
    local vars = {}
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        local mat = try(function() return mesh:getMaterialName(i) end)
        if mat then
            vars[mat] = { index = i }
            local count = try(function() return mesh:getMaterialVariableNum(i) end) or 0
            for j = 0, count - 1 do
                local name = try(function() return mesh:getMaterialVariableName(i, j) end)
                if name then vars[mat][name] = j end
            end
        end
    end
    return vars
end

-- Write a material value only when it changed (most of them stay put most frames).
local function set_float(entry, mesh, mat, var, value)
    entry.vars = entry.vars or material_vars(mesh)
    local m = entry.vars[mat]
    local j = m and m[var]
    if not j then return end
    entry.written = entry.written or {}
    local key = mat .. "." .. var
    if entry.written[key] == value then return end
    entry.written[key] = value
    try(function() mesh:setMaterialFloat(m.index, j, value) end)
end

local function set_color(entry, mesh, mat, rgb)
    entry.vars = entry.vars or material_vars(mesh)
    local m = entry.vars[mat]
    local j = m and m.Emissive_Color
    if not j then return end
    entry.written = entry.written or {}
    local key = mat .. ".Emissive_Color"
    local tag = string.format("%.3f %.3f %.3f", rgb[1], rgb[2], rgb[3])
    if entry.written[key] == tag then return end
    entry.written[key] = tag
    try(function() mesh:setMaterialFloat4(m.index, j, Vector4f.new(rgb[1], rgb[2], rgb[3], 1.0)) end)
end

-- Glow slider times the weapon state's multiplier (entry.mul, set by the state updates).
local function apply_tuning(entry, mesh)
    entry.glowSlots = entry.glowSlots or glow_slots(mesh, entry.kit)
    for _, s in ipairs(entry.glowSlots) do
        set_float(entry, mesh, s.name, "Emissive_Intensity", s.base * config.glow * ((entry.mul or {})[s.name] or 1))
    end
end

-- The kit a model path belongs to (any size), or nil if it is not one of ours.
local function kit_of_mesh(path)
    for _, kit in pairs(KITS) do
        if kit.mesh == path then return kit end
        for _, m in pairs(kit.sizes or {}) do
            if m == path then return kit end
        end
    end
    return nil
end

-- No record of what a slot held before our model (config from an older version): take an
-- assigned original of the same kit, the right-hand model (_1) for the main weapon slot.
local function guess_original(slotName, current)
    local kit, pick = kit_of_mesh(current), nil
    local known = {}
    for path, kitName in pairs(config.assign) do known[path] = kitName end
    for path, kitName in pairs(config.migratedFrom) do known[path] = kitName end
    for path, kitName in pairs(known) do               -- (only older configs have per-model entries)
        if KITS[kitName] == kit then
            local hand = path:match("_(%d)%.mesh$")
            if not pick or (hand == "1") == (slotName == "Weapon") then pick = path end
        end
    end
    return pick and { original = pick } or nil
end

local function swap_in(go, mesh, original, kit, slotName)
    local chain = component(go, CHAIN2)
    local originalChain = chain and resource_path(try(function() return chain:get_ChainAsset() end))
    -- Remember each original model's physics chain. If the game restored only its model,
    -- the chain on the object is still ours, so use the one remembered earlier.
    if originalChain and originalChain ~= NULL_CHAIN then
        chainOf[original] = originalChain
    else
        originalChain = chainOf[original]
    end
    if set_model(go, mesh, kit_mesh(kit), kit_mdf(kit), NULL_CHAIN) then
        swapped[go:get_address()] = { go = go, original = original, chain = originalChain,
                                      kit = kit, kitMesh = kit_mesh(kit), kitMdf = kit_mdf(kit), slot = slotName,
                                      -- set the model again a second later, and when next drawn
                                      refreshAt = os.clock() + 1.0, drawRefresh = not isWeaponDrawn,
                                      -- the kinsect is a creature, not a weapon: it stays when sheathed
                                      keep = slotName == "Kinsect" }
        local prev = config.swappedFrom[slotName]
        if not prev or prev.original ~= original or prev.chain ~= originalChain then
            config.swappedFrom[slotName] = { original = original, chain = originalChain }
            save_config()
        end
    end
end

local function swap_back(entry)
    local go = entry.go
    if not try(function() return go:get_Valid() end) then return end
    local mesh = component(go, MESH)
    if mesh then
        set_model(go, mesh, entry.original, entry.original:gsub("%.mesh$", ".mdf2"), entry.chain)
    end
    try(function() go:set_DrawSelf(true) end)
end

-- ------------------------------------------------------------------ per frame

-- Our weapons vanish when sheathed (not the kinsect); a shield also once it has faded into its
-- weapon's other mode (charge blade axe).
local function entry_visible(entry)
    if entry.hiddenByMode then return false end
    if entry.keep or not config.hideSheathed then return true end
    return isWeaponDrawn
end

local function update_slot(name, weapon)
    local go = weapon and try(function() return weapon:get_GameObject() end)
    if not go then slots[name] = nil; return end
    local mesh = component(go, MESH)
    if not mesh then slots[name] = nil; return end
    local key = go:get_address()
    local current = resource_path(try(function() return mesh:getMesh() end))
    local entry = swapped[key]
    local remembered = config.swappedFrom[name] or (not entry and kit_of_mesh(current) and guess_original(name, current))
    if not entry and remembered and kit_of_mesh(current) then
        -- Our model is already on the weapon (the scripts were reloaded): take it over again.
        entry = { go = go, original = remembered.original, chain = remembered.chain,
                  kit = kit_of_mesh(current), kitMesh = current }
        swapped[key] = entry
        chainOf[remembered.original] = chainOf[remembered.original] or remembered.chain
    end
    if entry and current ~= entry.original and current ~= entry.kitMesh then
        -- The game put a different weapon on this object: forget the old one.
        try(function() go:set_DrawSelf(true) end)
        swapped[key] = nil
        entry = nil
    end
    local original = entry and entry.original or current
    slots[name] = { go = go, original = original, current = current }

    local kitName = config.enabled and original and assigned_kit(original)
    local kit = kitName and KITS[kitName]
    if kit then
        -- Swap when the game shows its own model (first time, or it reloaded the weapon).
        -- (or the size changed: then `current` is our other size and `original` stays the game's).
        if current ~= kit_mesh(kit) then swap_in(go, mesh, original, kit, name) end
        if swapped[key] then apply_tuning(swapped[key], mesh) end
        -- Only our light weapons vanish; if the swap failed, leave the original alone.
        if swapped[key] then
            try(function() go:set_DrawSelf(entry_visible(swapped[key])) end)
        else
            try(function() go:set_DrawSelf(true) end)
        end
    elseif entry then
        swap_back(entry)
        swapped[key] = nil
    end
end

-- ------------------------------------------------------------------ weapon states

-- Demon mode (dual blades): the game's own 0 -> 1 value, read from the weapon handling
-- object (found with the scout script's Watch: app.cHunterWp02Handling._KijinExtern).
local function demon_target(chr)
    local h = try(function() return chr:call("get_WeaponHandling") end)
    if not h then return 0 end
    local v = try(function() return h:get_field("_KijinExtern") end)
    return type(v) == "number" and math.max(0, math.min(1, v)) or 0
end

local function ramp(p, a, b) return math.max(0, math.min(1, (p - a) / (b - a))) end
-- Side-blade stages cross-fade as the split progresses (0 = one blade, 1 = three blades):
-- short and narrow first, then longer and wider, so the blades seem to slide outward.
local function stage_alpha(stage, p)
    if stage == 1 then return math.min(ramp(p, 0.0, 0.3), 1 - ramp(p, 0.3, 0.6)) end
    if stage == 2 then return math.min(ramp(p, 0.3, 0.6), 1 - ramp(p, 0.6, 0.9)) end
    return ramp(p, 0.6, 1.0)
end

local demonProgress, lastClock = 0, os.clock()
local DEMON_IN, DEMON_OUT = 0.35, 0.2      -- seconds for the split / the merge

local function state_slots(mesh, kit)
    local slots = {}
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        local stage = kit.demon and kit.demon[try(function() return mesh:getMaterialName(i) end) or ""]
        if stage then
            local vars = try(function() return mesh:getMaterialVariableNum(i) end) or 0
            local dissolve
            for j = 0, vars - 1 do
                if try(function() return mesh:getMaterialVariableName(i, j) end) == "Dissolve" then dissolve = j end
            end
            slots[#slots + 1] = { mat = i, stage = stage, dissolve = dissolve }
        end
    end
    return slots
end

-- Game values read by name from the weapon handling object. The names were found in the
-- game's type database (strings in the exe), not yet confirmed per weapon: the first
-- candidate that exists is used, and the menu shows which one (or lists similar fields).
local GAUGE_SUBFIELDS = { "_Value", "_Current", "_Now", "_Point", "_Gauge", "Value" }
local function read_number(obj, name)
    local v = try(function() return obj:get_field(name) end)
    if type(v) == "number" then return v end
    if type(v) == "boolean" then return v and 1 or 0 end
    if type(v) == "userdata" then
        for _, sub in ipairs(GAUGE_SUBFIELDS) do
            local w = try(function() return v:get_field(sub) end)
            if type(w) == "number" then return w end
        end
    end
    return nil
end

local resolved = { type = nil, fields = {} }     -- per handling type: key -> { name } or { missing, at }
local stateInfo = {}                             -- what the menu shows
local function handling_type(h)
    return try(function() return h:get_type_definition():get_full_name() end) or "?"
end

local function resolve(h, key, candidates)
    local td = handling_type(h)
    if resolved.type ~= td then resolved = { type = td, fields = {} } end
    key = key .. "|" .. (candidates[1] or "")      -- kits may look for the same thing under other names
    local r = resolved.fields[key]
    if r and (r.name or os.clock() < r.at) then return r.name end
    for _, name in ipairs(candidates) do
        if read_number(h, name) ~= nil then
            resolved.fields[key] = { name = name }
            return name
        end
    end
    resolved.fields[key] = { missing = true, at = os.clock() + 3 }       -- look again later
    return nil
end

-- Fields of the handling object whose names contain `pattern` (for the menu, when none of
-- the candidates exist).
local function similar_fields(h, pattern)
    local out = {}
    local td = try(function() return h:get_type_definition() end)
    while td and #out < 12 do
        for _, f in ipairs(try(function() return td:get_fields() end) or {}) do
            local n = try(function() return f:get_name() end) or ""
            if n:find(pattern, 1, true) and #out < 12 then out[#out + 1] = n end
        end
        td = try(function() return td:get_parent_type() end)
    end
    return out
end

local function lerp(a, b, t) return a + (b - a) * t end
local function lerp3(a, b, t) return { lerp(a[1], b[1], t), lerp(a[2], b[2], t), lerp(a[3], b[3], t) } end
local function approach(cur, target, dt, up, down)
    local rate = dt / (target > cur and up or down)
    return cur + math.max(-rate, math.min(rate, target - cur))
end

-- Great sword charge (DESIGN.md: bright gold -> brighter gold -> white light; only at the
-- third level a gold band of light runs along the temper line). mul scales the glow.
-- The hammer and the lance use it too: their charge parts (spec.parts: material -> level,
-- hidden at Dissolve 0 in the mdf2) fade in at their level and take the level's light.
local GOLD = { 1.0, 0.647, 0.149 }
local CHARGE_LOOK = {
    [0] = { mul = 1.0, color = GOLD },
    [1] = { mul = 1.8, color = { 1.0, 0.56, 0.06 } },     -- more saturated, much stronger
    [2] = { mul = 2.8, color = { 1.0, 0.60, 0.09 } },
    [3] = { mul = 3.6, color = { 1.0, 0.94, 0.82 } },     -- white light
}
-- Insect glaive (user, 2026-10-02): gold -> bright gold -> white gold.
local CHARGE_LOOKS = {
    -- Insect glaive: two levels (recorded 2026-10-02), gold -> bright gold -> white gold.
    whiteGold2 = {
        [0] = { mul = 1.0, color = GOLD },
        [1] = { mul = 2.2, color = { 1.0, 0.56, 0.06 } },
        [2] = { mul = 3.2, color = { 1.0, 0.86, 0.58 } },
    },
    -- Long sword spirit levels.
    spirit = {
        [0] = { mul = 0.8, color = { 1.0, 0.78, 0.45 } },     -- pale gold
        [1] = { mul = 1.0, color = GOLD },
        [2] = { mul = 1.8, color = { 1.0, 0.56, 0.06 } },     -- bright gold
        [3] = { mul = 3.4, color = { 1.0, 0.94, 0.82 } },     -- white light
    },
    whiteGold = {
        [0] = { mul = 1.0, color = GOLD },
        [1] = { mul = 1.4, color = GOLD },
        [2] = { mul = 2.2, color = { 1.0, 0.56, 0.06 } },
        [3] = { mul = 3.2, color = { 1.0, 0.86, 0.58 } },
    },
}
local BAND_PERIOD, BAND_WIDTH = 0.9, 0.14
local BAND_WHITE = { 1.0, 0.97, 0.90 }     -- the pulse's colour at its peak
local CHARGE_WEIGHTS = { MiquellaBlade = 1.0, MiquellaGlow = 0.4, MiquellaTemper = 1.0 }

-- spec: the kit's charge table; level: given by the caller (the gunlance) or read from spec.fields.
local function update_charge(entry, mesh, h, dt, now, spec, level)
    spec = spec or entry.kit.charge
    if not level then
        local name = h and resolve(h, "charge", spec.fields)
        local raw = name and read_number(h, name) or 0
        level = math.max(0, math.min(spec.levels, math.floor(raw + (spec.offset or 0) + 0.5)))
        stateInfo.charge = name and string.format("%s = %s (level %d)", name, tostring(raw), level)
            or ("not found; fields with 'Charge': " .. table.concat(h and similar_fields(h, "Charge") or {}, ", "))
    end
    entry.chargeSmooth = approach(entry.chargeSmooth or 0, level, dt, 0.12, 0.35)
    local s = entry.chargeSmooth
    local lo = math.floor(s)
    local hi, t = math.min(spec.levels, lo + 1), s - lo
    local look = CHARGE_LOOKS[spec.look] or CHARGE_LOOK
    local a, b = look[lo], look[hi]
    local mul, color = lerp(a.mul, b.mul, t), lerp3(a.color, b.color, t)
    entry.mul = {}
    for mat, w in pairs(spec.weights or CHARGE_WEIGHTS) do entry.mul[mat] = 1 + (mul - 1) * w end
    for _, mat in ipairs(spec.colored or { "MiquellaBlade" }) do set_color(entry, mesh, mat, color) end
    entry.vars = entry.vars or material_vars(mesh)
    entry.partsOn = entry.partsOn or {}
    for mat, lv in pairs(spec.parts or {}) do
        local alpha = math.max(0, math.min(1, s - (lv - 1)))
        local m = entry.vars[mat]
        if m and entry.partsOn[mat] ~= (alpha > 0.001) then
            entry.partsOn[mat] = alpha > 0.001
            try(function() mesh:setMaterialsEnable(m.index, alpha > 0.001) end)
        end
        set_float(entry, mesh, mat, "Dissolve", alpha)
        entry.mul[mat] = mul
        set_color(entry, mesh, mat, spec.partColor or color)
    end
    if not spec.band then return end
    -- The band: on from the third level, sweeping root -> tip (the temper UVs run along it).
    local band = math.max(0, math.min(1, s - ((spec.bandFrom or spec.levels) - 1)))
    if spec.bands then
        -- Pieces of the temper line (and the blade's, `blades`) lit in turn: a pulse travelling
        -- root -> tip, then again, whiter where it is; the rest dims to bandDim while it runs.
        local n, w = #spec.bands, spec.bandWidth or BAND_WIDTH
        local front = ((now / (spec.bandPeriod or BAND_PERIOD)) % 1) * (1 + 2 * w) - w
        local base = mul * lerp(1, spec.bandDim or 1, band)
        for k, mat in ipairs(spec.bands) do
            local x = ((k - 0.5) / n - front) / w
            local g = band * math.exp(-x * x)
            local c = lerp3(color, BAND_WHITE, g)
            entry.mul[mat] = base * (1 + (spec.bandBoost or 1) * g)
            set_color(entry, mesh, mat, c)
            local blade = spec.blades and spec.blades[k]
            if blade then
                entry.mul[blade] = entry.mul[mat]
                set_color(entry, mesh, blade, c)
            end
        end
        return
    end
    set_float(entry, mesh, "MiquellaTemper", "Use_MoveEmit", band > 0.05 and 1.0 or 0.0)
    if band > 0.05 then
        set_float(entry, mesh, "MiquellaTemper", "MoveEmit", ((now / BAND_PERIOD) % 1) * 1.3 - 0.15)
        set_float(entry, mesh, "MiquellaTemper", "MoveEmit_Width", spec.bandWidth or BAND_WIDTH)
        entry.mul.MiquellaTemper = mul * (1 + band * (spec.bandBoost or 1))
    end
end

-- Light bowgun rapid-fire gauge on the three drops over the barrel: each drop is one third
-- of the gauge (dim when empty); in rapid-fire mode they burn brighter, deeper gold.
local DOT_DIM, RAPID_MUL, RAPID_COLOR = 0.35, 1.8, { 1.0, 0.56, 0.06 }

local function update_gauge(entry, mesh, h, dt)
    local spec = entry.kit.gauge
    local name = h and resolve(h, "gauge", spec.fields)
    local modeName = h and resolve(h, "rapid", spec.mode)
    local g = name and read_number(h, name)
    local rapid = modeName and (read_number(h, modeName) or 0) > 0
    local f = 1
    if g then
        entry.gaugeMax = math.max(entry.gaugeMax or 0, g, 1e-6)
        f = math.max(0, math.min(1, g / entry.gaugeMax))
    end
    stateInfo.gauge = (name and string.format("%s = %.2f (max seen %.2f)", name, g or 0, entry.gaugeMax or 0)
        or ("gauge not found; fields with 'Rapid': " .. table.concat(h and similar_fields(h, "Rapid") or {}, ", ")))
        .. (modeName and string.format("; %s = %s", modeName, tostring(rapid)) or "")
    entry.gaugeSmooth = approach(entry.gaugeSmooth or f, f, dt, 0.15, 0.15)
    entry.rapidSmooth = approach(entry.rapidSmooth or 0, rapid and 1 or 0, dt, 0.1, 0.3)
    entry.mul = {}
    for i, mat in ipairs(spec.dots) do
        local lit = math.max(0, math.min(1, entry.gaugeSmooth * #spec.dots - (i - 1)))
        entry.mul[mat] = lerp(DOT_DIM, 1, lit) * lerp(1, RAPID_MUL, entry.rapidSmooth)
        set_color(entry, mesh, mat, lerp3(GOLD, RAPID_COLOR, entry.rapidSmooth))
    end
end

-- Bow (user, 2026-10-02): the charge level runs the light from bright gold to white gold,
-- and lights the rings ahead of the arrow a pair per level (the unlit ones dim while drawing).
-- Drawing packs those rings toward the bow like a spring being wound, tighter each level
-- (entry.packTarget, 0..1; the floating-ring step springs them there and back).
local BOW_LOOK = {
    [0] = { mul = 1.0, color = GOLD },
    [1] = { mul = 1.8, color = { 1.0, 0.56, 0.06 } },     -- bright gold
    [2] = { mul = 2.6, color = { 1.0, 0.68, 0.20 } },     -- brighter gold
    [3] = { mul = 3.4, color = { 1.0, 0.86, 0.58 } },     -- white gold
    [4] = { mul = 4.0, color = { 1.0, 0.92, 0.74 } },     -- (a fourth level, if the game has one)
}
local PACK_DRAWN = 0.45          -- how packed the rings are as soon as the bow is drawn

local function update_bow(entry, mesh, h, dt)
    local spec = entry.kit.bow
    local name = h and resolve(h, "charge", spec.fields)
    local drawName = h and resolve(h, "draw", spec.draw)
    local raw = name and read_number(h, name) or 0
    local drawRaw = drawName and read_number(h, drawName) or 0
    local level = math.floor(raw + 0.5) + (config.bowFrom0 and 1 or 0)
    -- With a drawing field, only it says whether the bow is drawn (the level may stay set).
    local drawing = isWeaponDrawn and ((drawName and drawRaw > 0) or (not drawName and raw > 0))
    level = drawing and math.max(0, math.min(4, level)) or 0
    stateInfo.charge = name and string.format("%s = %s (level %d)", name, tostring(raw), level)
        or ("not found; fields with 'Charge': " .. table.concat(h and similar_fields(h, "Charge") or {}, ", "))
    stateInfo.draw = drawName and string.format("%s = %s (drawing: %s)", drawName, tostring(drawRaw), tostring(drawing))
        or ("not found (using the level); fields with 'Aim': " .. table.concat(h and similar_fields(h, "Aim") or {}, ", "))
    entry.drawSmooth = approach(entry.drawSmooth or 0, drawing and 1 or 0, dt, 0.12, 0.25)
    entry.chargeSmooth = approach(entry.chargeSmooth or 0, level, dt, 0.12, 0.25)
    local s = entry.chargeSmooth
    local lo = math.min(4, math.floor(s))
    local hi, t = math.min(4, lo + 1), s - lo
    local mul, color = lerp(BOW_LOOK[lo].mul, BOW_LOOK[hi].mul, t), lerp3(BOW_LOOK[lo].color, BOW_LOOK[hi].color, t)
    entry.mul = { MiquellaBlade = mul, MiquellaTemper = mul, MiquellaGlow = 1 + (mul - 1) * 0.5 }
    for _, mat in ipairs({ "MiquellaBlade", "MiquellaTemper", "MiquellaGlow" }) do set_color(entry, mesh, mat, color) end
    for i, mat in ipairs(spec.rings) do
        local lit = math.max(0, math.min(1, s - (i - 1)))
        entry.mul[mat] = lerp(lerp(1, DOT_DIM, entry.drawSmooth), mul, lit)
        set_color(entry, mesh, mat, lerp3(GOLD, color, lit))
    end
    -- Flowers opening level by level (Dissolve fade; switched off while gone).
    entry.vars = entry.vars or material_vars(mesh)
    entry.partsOn = entry.partsOn or {}
    for mat, lv in pairs(spec.parts or {}) do
        local alpha = math.max(0, math.min(1, s - (lv - 1)))
        local m = entry.vars[mat]
        if m and entry.partsOn[mat] ~= (alpha > 0.001) then
            entry.partsOn[mat] = alpha > 0.001
            try(function() mesh:setMaterialsEnable(m.index, alpha > 0.001) end)
        end
        set_float(entry, mesh, mat, "Dissolve", alpha)
        entry.mul[mat] = mul
        set_color(entry, mesh, mat, color)
    end
    entry.packTarget = drawing and (PACK_DRAWN + (1 - PACK_DRAWN) * math.min(level, spec.levels) / spec.levels) or 0
end

-- Insect glaive extracts: an orb fades in while its extract is lit and circles the top blade
-- (step_floaters); with all three the blade burns bright gold.
local EXTRACT_FADE, TRIPLE_MUL, TRIPLE_COLOR = 0.3, 1.8, { 1.0, 0.56, 0.06 }

local function update_extracts(entry, mesh, h, dt)
    local spec = entry.kit.extracts
    entry.vars = entry.vars or material_vars(mesh)
    entry.partsOn = entry.partsOn or {}
    entry.orbAlpha = entry.orbAlpha or {}
    local info = {}
    for mat, field in pairs(spec.orbs) do
        local v = h and read_number(h, field)
        info[#info + 1] = string.format("%s=%s", (field:gsub("_ExtractTimer", "")), v and string.format("%.0f", v) or "?")
        local a = approach(entry.orbAlpha[mat] or 0, (v or 0) > 0 and 1 or 0, dt, EXTRACT_FADE, EXTRACT_FADE)
        entry.orbAlpha[mat] = a
        local m = entry.vars[mat]
        if m and entry.partsOn[mat] ~= (a > 0.001) then
            entry.partsOn[mat] = a > 0.001
            try(function() mesh:setMaterialsEnable(m.index, a > 0.001) end)
        end
        set_float(entry, mesh, mat, "Dissolve", a)
    end
    table.sort(info)
    local t = h and read_number(h, spec.triple)
    entry.tripleSmooth = approach(entry.tripleSmooth or 0, (t or 0) > 0 and 1 or 0, dt, 0.2, 0.4)
    stateInfo.extract = table.concat(info, " ") .. string.format(" Tripple=%s", t and string.format("%.0f", t) or "?")
    -- On top of the charge light (only while not charging, so the charge stays readable).
    local k = entry.tripleSmooth * (1 - math.min(1, entry.chargeSmooth or 0))
    if k > 0.001 then
        entry.mul = entry.mul or {}
        entry.mul.MiquellaBlade = (entry.mul.MiquellaBlade or 1) * lerp(1, TRIPLE_MUL, k)
        set_color(entry, mesh, "MiquellaBlade", lerp3(GOLD, TRIPLE_COLOR, k))
    end
end

-- Gunlance (user, 2026-10-02): a reload winds the ivory spring toward the root and lets it
-- spring back; charged shelling winds it tighter each level and holds it until the shot;
-- Wyvern's Fire winds it all the way until it fires. The light follows the level.
local RELOAD_PULSE, GL_LEVEL_TIME = 0.35, 0.45
local SHELL_PULSE = 0.18             -- a shell fired: a short press
-- Wyvern's Fire: its gauge drops at the blast, too late for the wind-up (user, 2026-10-02), and
-- the original gunlance bones on our model do not move during it (traces of 2026-10-02: Hinge
-- 18 deg, Heat_Hinge 0 through the whole wind-up). Now the hunter's own action: the game's
-- Wyvern's Fire actions are cRyuugeki* (Start, Idle, AimIdle, ToAim, Shoot, Shot) -> wound
-- while one runs until the gauge drops (the blast), then it springs back and waits for them to end.
local GL_WYVERN_ACTION = "Ryuugeki"
local glEvents = {}

local function gl_event(text)
    glEvents[#glEvents + 1] = string.format("%8.2f  %s", os.clock(), text)
    if #glEvents > 100 then table.remove(glEvents, 1) end
end
local GL_CHARGE_STEP = 0.6           -- charged shelling: a level per 0.6 s of its timer (it reached 1.83)

local function first_number(h, names)
    for _, n in ipairs(names) do
        local v = read_number(h, n)
        if v ~= nil then return v, n end
    end
    return nil, nil
end

local function update_gunlance(entry, mesh, h, dt, now)
    local spec = entry.kit.gunlance
    local reload, rn = first_number(h, spec.reload)
    local shot, sn = first_number(h, spec.chargeShot)
    local wyv, wn = first_number(h, spec.wyvern)
    local gauge, gn = first_number(h, spec.wyvernGauge or {})
    local shells = first_number(h, spec.shells or {})
    if gauge and entry.lastWyvGauge and gauge < entry.lastWyvGauge - 0.5 then
        entry.blastAt = now
        gl_event(string.format("Wyvern's Fire gauge %.2f -> %.2f (the blast)", entry.lastWyvGauge, gauge))
    end
    entry.lastWyvGauge = gauge
    if shells and entry.lastShells and shells < entry.lastShells then
        entry.shellUntil = now + SHELL_PULSE
        gl_event(string.format("shells %s -> %s", tostring(entry.lastShells), tostring(shells)))
    end
    entry.lastShells = shells
    local wyvAction = actionNow:find(GL_WYVERN_ACTION, 1, true) ~= nil
    if wyvAction ~= (entry.wasWyvAction or false) then
        gl_event(string.format("Wyvern's Fire action %s (%s)", wyvAction and "starts" or "ends", actionNow))
    end
    entry.wasWyvAction = wyvAction
    local reloading = (reload or 0) > 0
    if reloading and not entry.wasReloading then
        entry.reloadUntil = now + RELOAD_PULSE
        gl_event("reload")
    end
    entry.wasReloading = reloading
    -- Charging while the timer counts up (it keeps its value after the shot).
    local counting = shot ~= nil and entry.lastShot ~= nil and shot > entry.lastShot + 1e-5 and shot > 0
    entry.lastShot = shot
    entry.countingAt = counting and now or entry.countingAt
    local charging = entry.countingAt ~= nil and now - entry.countingAt < 0.15
    -- After the blast the action may run on a while (the recoil): wait for it to end first.
    if entry.blastAt == now then entry.blastLatch = true end
    if not wyvAction then entry.blastLatch = nil end
    local winding = (wyv or 0) > 0 or (wyvAction and not entry.blastLatch and not reloading)
    entry.chargeSince = charging and (entry.chargeSince or now) or nil
    entry.windSince = winding and (entry.windSince or now) or nil
    local level, pack = 0, 0
    if entry.reloadUntil and now < entry.reloadUntil then level, pack = 1, 0.8 end
    if entry.shellUntil and now < entry.shellUntil then level, pack = math.max(level, 1), math.max(pack, 0.5) end
    if charging then
        local lv = math.min(3, 1 + math.floor((shot or (now - entry.chargeSince)) / GL_CHARGE_STEP))
        level, pack = math.max(level, lv), math.max(pack, 0.4 + 0.2 * lv)
    end
    if winding then
        level = math.max(level, math.min(3, 1 + math.floor((now - entry.windSince) / GL_LEVEL_TIME)))
        pack = 1.0
    end
    if not isWeaponDrawn then level, pack = 0, 0 end
    entry.packTarget = pack
    -- The gold thread: drawn out a third of the way per level (it shows from the first).
    entry.stretch = approach(entry.stretch or 0, level / 3, dt, 0.2, 0.15)
    local function show(n, v) return n and string.format("%s=%s", n, tostring(v)) or "?" end
    stateInfo.gunlance = string.format("%s %s %s %s shells=%s (level %d, spring %.2f)", show(rn, reload), show(sn, shot),
                                       show(wn, wyv), show(gn, gauge and string.format("%.2f", gauge)), tostring(shells),
                                       level, entry.pack or 0)
        .. "  action: " .. (actionNow ~= "" and actionNow or "not readable")
    update_charge(entry, mesh, h, dt, now, spec.charge, level)
end

-- Weapon modes: read the game's mode, put on the other mode's model when it changes.
-- A morph window: progress p across win = { from, to }, smoothstepped.
local function eased(p, win)
    local x = ramp(p, win[1], win[2])
    return x * x * (3 - 2 * x)
end

-- A material's visibility: Dissolve (dithered fade), switched off when fully gone.
local function set_alpha(entry, mesh, mat, a)
    entry.vars = entry.vars or material_vars(mesh)
    local m = entry.vars[mat]
    if not m then return end
    entry.fadeOn = entry.fadeOn or {}
    if entry.fadeOn[mat] ~= (a > 0.001) then
        entry.fadeOn[mat] = a > 0.001
        try(function() mesh:setMaterialsEnable(m.index, a > 0.001) end)
    end
    set_float(entry, mesh, mat, "Dissolve", a)
end

-- The game's mode drives the morph's progress (entry.morphP, 0 base mode .. 1 the other) over
-- morph.seconds; parts of one mode fade, the shield fades out toward the other mode. The
-- joints follow in apply_morph (with the floating rings, so they land after the game's motion).
local function update_mode(entry, mesh, h, dt)
    -- Only the weapon in the hand (an older weapon object may still be listed).
    if not (slots.Weapon and slots.Weapon.go == entry.go) then return end
    local spec = entry.kit.mode
    local name = h and resolve(h, "mode", spec.fields)
    local v = name and read_number(h, name) or 0
    local wtype = slots.Weapon and weapon_type(slots.Weapon.original)
    local on = (v > 0) ~= (config.modeInvert[wtype or ""] == true)
    modeOn[entry.kit] = on
    local m = spec.morph
    local target = on and 1 or 0
    -- A weapon just put on starts in the game's mode (no morph on drawing it).
    entry.morphP = approach(entry.morphP or target, target, dt, m.seconds, m.seconds)
    local p = entry.morphP
    stateInfo.mode = name and string.format("%s = %s (%s look, morph %.2f)", name, tostring(v), spec.names[on and 2 or 1], p)
        or ("not found; fields with 'Mode': " .. table.concat(h and similar_fields(h, "Mode") or {}, ", "))
    for _, f in ipairs(m.fades) do
        local a = eased(p, f.win)
        if f.show == "base" then a = 1 - a end
        for _, mat in ipairs(f.mats) do set_alpha(entry, mesh, mat, a) end
    end
    if not m.second then return end
    local a = 1 - eased(p, m.second)
    for _, other in pairs(swapped) do
        if other.slot == "SubWeapon" then
            local mesh2 = component(other.go, MESH)
            if mesh2 then
                other.vars = other.vars or material_vars(mesh2)
                for mat in pairs(other.vars) do set_float(other, mesh2, mat, "Dissolve", a) end
            end
            other.hiddenByMode = a < 0.001 or nil
        end
    end
end

-- Phial gauges and boosts (switch axe, charge blade): a gauge lights its phials one by one
-- (count: the value is a number of phials; otherwise a fraction of the largest value seen),
-- unlit ones dim; a boost (enhanced, amped) burns its materials bright gold. `when`: only in
-- the base or the other ("alt") mode of the weapon.
local GAUGE_DIM, BOOST_MUL, BOOST_COLOR = 0.25, 1.8, { 1.0, 0.56, 0.06 }

local function in_mode(entry, when)
    if not when then return true end
    return (when == "alt") == (modeOn[entry.kit] == true)
end

local function update_gauges(entry, mesh, h, dt)
    if not (entry.kit.charge or entry.kit.bow or entry.kit.gunlance) then entry.mul = {} end
    entry.mul = entry.mul or {}
    entry.gaugeState = entry.gaugeState or {}
    local info = {}
    for _, g in ipairs(entry.kit.gauges or {}) do
        if in_mode(entry, g.when) then
            local name = h and resolve(h, g.key, g.fields)
            local v = name and read_number(h, name)
            local st = entry.gaugeState[g.key] or {}
            entry.gaugeState[g.key] = st
            local f = 0
            if v then
                if g.count then
                    f = v / #g.dots
                else
                    -- The game's maximum when it has one, else the largest value seen.
                    local maxV = g.max or (g.maxFields and first_number(h, g.maxFields))
                    st.max = (maxV and maxV > 0) and maxV or math.max(st.max or 0, v, 1e-6)
                    f = v / st.max
                end
            end
            f = math.max(0, math.min(1, f))
            st.smooth = approach(st.smooth or f, f, dt, 0.15, 0.15)
            local full = g.fullBright and st.smooth > 0.995
            for i, mat in ipairs(g.dots) do
                local lit = math.max(0, math.min(1, st.smooth * #g.dots - (i - 1)))
                entry.mul[mat] = lerp(GAUGE_DIM, full and BOOST_MUL or 1, lit)
                set_color(entry, mesh, mat, full and BOOST_COLOR or GOLD)
            end
            info[#info + 1] = name and string.format("%s=%s", name, v and string.format("%.1f", v) or "?")
                or (g.key .. " not found")
        end
    end
    for _, b in ipairs(entry.kit.boosts or {}) do
        if in_mode(entry, b.when) then
            local name = h and resolve(h, b.key, b.fields)
            local v = name and read_number(h, name) or 0
            local st = entry.gaugeState[b.key] or {}
            entry.gaugeState[b.key] = st
            st.smooth = approach(st.smooth or 0, v > 0 and 1 or 0, dt, 0.15, 0.4)
            for _, mat in ipairs(b.mats) do
                entry.mul[mat] = (entry.mul[mat] or 1) * lerp(1, BOOST_MUL, st.smooth)
                set_color(entry, mesh, mat, lerp3(GOLD, BOOST_COLOR, st.smooth))
            end
            -- Chasing sets: one lit at a time, in turn (a light running along them).
            local step = b.chase and math.floor(os.clock() * (b.chaseHz or 10)) % #b.chase
            for i, mat in ipairs(b.chase or {}) do
                set_alpha(entry, mesh, mat, (i - 1 == step) and st.smooth or 0)
                entry.mul[mat] = BOOST_MUL
                set_color(entry, mesh, mat, BOOST_COLOR)
            end
            info[#info + 1] = name and string.format("%s=%s", name, tostring(v)) or (b.key .. " not found")
        else
            for _, mat in ipairs(b.chase or {}) do set_alpha(entry, mesh, mat, 0) end
        end
    end
    stateInfo.gauges = stateInfo.gauges or {}
    stateInfo.gauges[entry.kit] = table.concat(info, "  ")
end

-- Every field of an object (its type and parents), not static.
local function field_names(h)
    local out, seen = {}, {}
    local td = try(function() return h:get_type_definition() end)
    while td do
        for _, f in ipairs(try(function() return td:get_fields() end) or {}) do
            local n = try(function() return f:get_name() end)
            if n and not seen[n] and not try(function() return f:is_static() end) then
                seen[n] = true
                out[#out + 1] = n
            end
        end
        td = try(function() return td:get_parent_type() end)
    end
    return out
end

-- Perfect Rush trace, to time the ring from one test (2026-10-02): while a rush runs and 1 s
-- after it, every frame, the number / true-false fields of the hunter, the weapon handling (and
-- the objects it holds) and the current actions (and theirs). True-false and whole numbers are
-- logged on every change (at most 12 lines a field each rush), other numbers when they start or
-- stop (0 <-> not 0); a new action's true fields when it starts. Each line has the seconds since
-- the rush began; saved as `trace` in the field recorder's file (fields_app_cHunterWp01Handling.json).
local TRACE_LINES, TRACE_PER_FIELD, TRACE_AFTER, TRACE_SUB_FIELDS = 1500, 12, 1.0, 60
local rushTrace = { lines = {}, on = false, start = 0, untilT = 0, last = {}, count = {}, names = {}, n = 0 }

local function trace_line(text)
    local lines = rushTrace.lines
    lines[#lines + 1] = text
    if #lines > TRACE_LINES then table.remove(lines, 1) end
end

local function trace_note(text, now)
    if rushTrace.on then trace_line(string.format("%6.3f  %s", now - rushTrace.start, text)) end
end

local function trace_num(v)
    if v == math.floor(v) and math.abs(v) < 1e9 then return string.format("%d", v) end
    return string.format("%.3f", v)
end

local function trace_obj(obj, prefix, t, depth, seen, firstTrue, maxFields)
    local addr = try(function() return obj:get_address() end)
    if addr then
        if seen[addr] then return end
        seen[addr] = true
    end
    local tn = try(function() return obj:get_type_definition():get_full_name() end)
    if not tn then return end
    local names = rushTrace.names[tn]
    if not names then
        names = field_names(obj)
        rushTrace.names[tn] = names
    end
    for i, n in ipairs(names) do
        if maxFields and i > maxFields then break end
        local v = try(function() return obj:get_field(n) end)
        if type(v) == "userdata" then
            if depth > 0 then trace_obj(v, prefix .. n .. ".", t, depth - 1, seen, firstTrue, TRACE_SUB_FIELDS) end
        else
            local isBool = type(v) == "boolean"
            if isBool then v = v and 1 or 0 end
            if type(v) == "number" then
                local key = prefix .. n
                local old = rushTrace.last[key]
                rushTrace.last[key] = v
                local line = nil
                if old == nil then
                    if firstTrue and isBool and v == 1 then line = key .. " = true" end
                elseif old ~= v then
                    local whole = v == math.floor(v) and old == math.floor(old)
                    if whole or (old == 0) ~= (v == 0) then line = key .. " " .. trace_num(old) .. " -> " .. trace_num(v) end
                end
                if line then
                    local c = (rushTrace.count[key] or 0) + 1
                    rushTrace.count[key] = c
                    if c <= TRACE_PER_FIELD then
                        trace_line(string.format("%6.3f  %s", t, line))
                    elseif c == TRACE_PER_FIELD + 1 then
                        trace_line(string.format("%6.3f  %s (keeps changing)", t, key))
                    end
                end
            end
        end
    end
end

local function update_rush_trace(h, inRush, now)
    if not config.recordFields then return end
    if inRush and not rushTrace.on then
        rushTrace.on, rushTrace.start, rushTrace.last, rushTrace.count = true, now, {}, {}
        rushTrace.n, rushTrace.action = rushTrace.n + 1, actionNow
        trace_line(string.format("=== rush %d at %.2f: %s", rushTrace.n, now, actionNow))
    end
    if not rushTrace.on then return end
    if inRush then rushTrace.untilT = now + TRACE_AFTER end
    local t = now - rushTrace.start
    if now > rushTrace.untilT then
        rushTrace.on = false
        trace_line(string.format("%6.3f  === end", t))
        return
    end
    if actionNow ~= rushTrace.action then
        rushTrace.action = actionNow
        trace_line(string.format("%6.3f  action %s", t, actionNow ~= "" and actionNow or "(none)"))
    end
    local seen = {}
    if hunterChr then trace_obj(hunterChr, "hunter.", t, 0, seen, false) end
    if h then trace_obj(h, "", t, 1, seen, false) end
    for _, a in ipairs(actionObjs) do
        trace_obj(a.obj, (a.name:match("[^%.]+$") or a.name) .. ".", t, 1, seen, true)
    end
end

-- Sword & shield Perfect Rush (user's pick 2026-10-02, "S2"): see the kit's timing table.
local TIMING_BURST = 0.35

local function update_timing(entry, mesh, h, dt, now)
    local spec = entry.kit.timing
    local inRush = isWeaponDrawn and actionNow:find(spec.actions, 1, true) ~= nil
    if actionNow ~= entry.timingAction then
        entry.timingAction = actionNow
        if inRush then
            entry.timingStart = now
            gl_event("Perfect Rush action " .. actionNow)
        end
    end
    update_rush_trace(h, inRush, now)
    -- The game's own check for the window, when it answers (true / false) on the handling or the
    -- hunter; nil = not known.
    local window = nil
    if inRush then
        for _, owner in ipairs({ h or false, hunterChr or false }) do
            for _, m in ipairs(owner and spec.checks or {}) do
                local v = try(function() return owner:call(m) end)
                if type(v) == "boolean" then window = window or v end
            end
        end
    end
    if window ~= entry.timingWindow then
        entry.timingWindow = window
        if window ~= nil then
            gl_event("Perfect Rush window " .. tostring(window))
            trace_note("window " .. tostring(window), now)
        end
    end
    local p = 0
    if inRush then
        local t = (now - (entry.timingStart or now)) / spec.fall
        if window == nil then p = math.min(1, t) else p = window and 1 or math.min(0.9, t) end
    end
    if p >= 1 and (entry.timingP or 0) < 1 then trace_note("ring at the guard", now) end
    entry.timingP = p
    entry.slide = spec.rise * (1 - p)
    local ok = h and first_number(h, spec.success)
    local okOn = (ok or 0) > 0
    if okOn and not entry.timingOk then
        entry.burstAt = now
        gl_event("Perfect!")
        trace_note("Perfect! (" .. spec.success[1] .. ")", now)
    end
    entry.timingOk = okOn
    entry.mul = entry.mul or {}
    entry.ringA = approach(entry.ringA or 0, inRush and 1 or 0, dt, 0.06, 0.2)
    set_alpha(entry, mesh, spec.ring, entry.ringA)
    entry.mul[spec.ring] = p >= 1 and 3.0 or 1.4
    local b = entry.burstAt and math.max(0, 1 - (now - entry.burstAt) / TIMING_BURST) or 0
    set_alpha(entry, mesh, spec.burst, b)
    entry.mul[spec.burst] = 3.0
    stateInfo.timing = string.format("in rush: %s  window: %s  ring %.2f  %s = %s",
        tostring(inRush), tostring(window), p, spec.success[1], tostring(ok))
end

-- Field recorder: 4 times a second, every number / true-false field of the weapon handling
-- (its type and parents); per field the lowest, highest and last value and how often it
-- changed; saved every 5 s, one file per handling type.
local rec = { type = nil, names = nil, data = nil, nextRead = 0, nextSave = 0, samples = 0 }

local function record_fields(h, now)
    if not (config.recordFields and h) or now < rec.nextRead then return end
    rec.nextRead = now + 0.25
    local tn = handling_type(h)
    if rec.type ~= tn then
        rec = { type = tn, names = field_names(h), data = {}, nextRead = now + 0.25, nextSave = now + 5, samples = 0 }
    end
    rec.samples = rec.samples + 1
    local function note(n, v)
        if type(v) == "boolean" then v = v and 1 or 0 end
        if type(v) ~= "number" then return end
        local d = rec.data[n]
        if not d then
            rec.data[n] = { min = v, max = v, last = v, changes = 0 }
        else
            if v ~= d.last then d.changes = d.changes + 1 end
            d.min, d.max, d.last = math.min(d.min, v), math.max(d.max, v), v
        end
    end
    for _, n in ipairs(rec.names) do
        local v = try(function() return h:get_field(n) end)
        if type(v) == "userdata" then
            -- Objects held by the handling (gauges, timers): their own fields, once found.
            rec.objects = rec.objects or {}
            rec.objects[n] = rec.objects[n] or try(function() return v:get_type_definition():get_full_name() end) or "?"
            rec.sub = rec.sub or {}
            if rec.sub[n] == nil then rec.sub[n] = field_names(v) end
            for i, sn in ipairs(rec.sub[n]) do
                if i > 40 then break end
                note(n .. "." .. sn, try(function() return v:get_field(sn) end))
            end
            v = nil
        end
        if type(v) == "boolean" then v = v and 1 or 0 end
        if type(v) == "number" then
            local d = rec.data[n]
            if not d then
                rec.data[n] = { min = v, max = v, last = v, changes = 0 }
            else
                if v ~= d.last then d.changes = d.changes + 1 end
                d.min, d.max, d.last = math.min(d.min, v), math.max(d.max, v), v
            end
        end
    end
    if now >= rec.nextSave then
        rec.nextSave = now + 5
        local changed = {}
        for n, d in pairs(rec.data) do
            if d.changes > 0 then changed[n] = d end
        end
        local safe = rec.type:gsub("[^%w_]", "_")
        try(function() json.dump_file("MiquellaLight/fields_" .. safe .. ".json",
            { type = rec.type, samples = rec.samples, changed = changed, all = rec.data, objects = rec.objects,
              events = #glEvents > 0 and glEvents or nil, actions = #actionLog > 0 and actionLog or nil,
              trace = #rushTrace.lines > 0 and rushTrace.lines or nil }) end)
    end
end

local function update_states(chr)
    local now = os.clock()
    local dt = math.min(now - lastClock, 0.1)
    lastClock = now
    local target = demon_target(chr)
    local rate = dt / (target > demonProgress and DEMON_IN or DEMON_OUT)
    demonProgress = demonProgress + math.max(-rate, math.min(rate, target - demonProgress))
    local h = nil
    update_actions(chr)
    if config.recordFields then
        h = try(function() return chr:call("get_WeaponHandling") end)
        record_fields(h, now)
    end
    for _, entry in pairs(swapped) do
        if entry.kit.charge or entry.kit.gauge or entry.kit.bow or entry.kit.extracts or entry.kit.gunlance
            or entry.kit.mode or entry.kit.gauges or entry.kit.boosts or entry.kit.timing then
            local mesh = component(entry.go, MESH)
            h = h or try(function() return chr:call("get_WeaponHandling") end)
            if mesh then
                if entry.kit.charge then update_charge(entry, mesh, h, dt, now) end
                if entry.kit.gauge then update_gauge(entry, mesh, h, dt) end
                if entry.kit.bow then update_bow(entry, mesh, h, dt) end
                if entry.kit.extracts then update_extracts(entry, mesh, h, dt) end
                if entry.kit.gunlance then update_gunlance(entry, mesh, h, dt, now) end
                if entry.kit.mode then update_mode(entry, mesh, h, dt) end
                if entry.kit.gauges or entry.kit.boosts then update_gauges(entry, mesh, h, dt) end
                if entry.kit.timing then update_timing(entry, mesh, h, dt, now) end
                apply_tuning(entry, mesh)
            end
        end
        if entry.kit.demon then
            local mesh = component(entry.go, MESH)
            if mesh then
                entry.stateSlots = entry.stateSlots or state_slots(mesh, entry.kit)
                for _, s in ipairs(entry.stateSlots) do
                    local a = stage_alpha(s.stage, demonProgress)
                    if a ~= s.last then
                        try(function() mesh:setMaterialsEnable(s.mat, a > 0.001) end)
                        if s.dissolve then try(function() mesh:setMaterialFloat(s.mat, s.dissolve, a) end) end
                        s.last = a
                    end
                end
            end
        end
    end
end

-- ------------------------------------------------------------------ floating rings

-- Rings with their own bone (MQ_*, a child of Base with no rotation, see build_weapon_kit.py)
-- are moved every frame: a damped spring in the weapon's space, pushed by the weapon's
-- acceleration at the ring (so it lags and swings back), plus a slow drift and, for
-- "hover", a faint fast tremor. Offsets are soft-clamped to max metres; the ring tilts with
-- its offset. Units: metres, seconds, degrees.
local FLOAT_MODES = {
    swing = { hz = 3.2, damping = 0.22, gain = 0.12, max = 0.035, tilt = 28,
              drift = 0.0015, driftTilt = 2.5, driftHz = { 0.31, 0.43, 0.37 }, tremor = 0 },
    hover = { hz = 2.2, damping = 0.35, gain = 0.05, max = 0.012, tilt = 6,
              drift = 0.004, driftTilt = 3.0, driftHz = { 0.47, 0.71, 0.59 }, tremor = 0.0004 },
    -- does not float: only packs (the gunlance's spring)
    fixed = { hz = 1.0, damping = 1.0, gain = 0, max = 0.001, tilt = 0,
              drift = 0, driftTilt = 0, driftHz = { 0, 0, 0 }, tremor = 0 },
}
local MAX_ACCEL = 150.0

local function vadd(a, b) return { a[1] + b[1], a[2] + b[2], a[3] + b[3] } end
local function vsub(a, b) return { a[1] - b[1], a[2] - b[2], a[3] - b[3] } end
local function vscale(a, s) return { a[1] * s, a[2] * s, a[3] * s } end
local function vlen(a) return math.sqrt(a[1] * a[1] + a[2] * a[2] + a[3] * a[3]) end
-- Lua 5.4 (REFramework) dropped the hyperbolic functions.
local function tanh(x)
    if x > 20 then return 1 end
    local e = math.exp(2 * x)
    return (e - 1) / (e + 1)
end
local function cross(a, b)
    return { a[2] * b[3] - a[3] * b[2], a[3] * b[1] - a[1] * b[3], a[1] * b[2] - a[2] * b[1] }
end
-- Quaternions as { x, y, z, w }.
local function qrot(q, v)
    local u = { q[1], q[2], q[3] }
    local t = vscale(cross(u, v), 2)
    return vadd(vadd(v, vscale(t, q[4])), cross(u, t))
end
local function qconj(q) return { -q[1], -q[2], -q[3], q[4] } end
local function qaxis(axis, deg)
    local l = vlen(axis)
    if l < 1e-9 or deg == 0 then return { 0, 0, 0, 1 } end
    local h = math.rad(deg) / 2
    local s = math.sin(h) / l
    return { axis[1] * s, axis[2] * s, axis[3] * s, math.cos(h) }
end
local function qmul(a, b)
    return { a[4] * b[1] + a[1] * b[4] + a[2] * b[3] - a[3] * b[2],
             a[4] * b[2] - a[1] * b[3] + a[2] * b[4] + a[3] * b[1],
             a[4] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[4],
             a[4] * b[4] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3] }
end

-- REFramework's Quaternion.new takes (w, x, y, z) (glm); check once in case it changes.
local quatOrder = nil
local function to_quat(q)
    if quatOrder == nil then
        local probe = try(function() return Quaternion.new(0.5, 0.1, 0.2, 0.3) end)
        quatOrder = (probe and math.abs(probe.w - 0.5) < 1e-6) and "wxyz" or "xyzw"
    end
    if quatOrder == "wxyz" then return Quaternion.new(q[4], q[1], q[2], q[3]) end
    return Quaternion.new(q[1], q[2], q[3], q[4])
end

local floatInfo = { found = 0, total = 0, phases = {} }
local lastFloatClock = nil

local function float_joints(entry)
    local spec = entry.kit.floaters
    if not spec then return nil end
    local f = entry.float
    if f and f.found == #spec.joints then return f end
    local tf = try(function() return entry.go:call("get_Transform") end)
    if not tf then return f end
    f = f or { joints = {} }
    f.tf, f.found = tf, 0
    for i, j in ipairs(spec.joints) do
        local s = f.joints[i] or { name = j.name, mode = j.mode, pivot = j.pos, pack = j.pack, orbit = j.orbit, flap = j.flap,
                                   spin = j.spin, stretch = j.stretch, slide = j.slide, off = { 0, 0, 0 },
                                   vel = { 0, 0, 0 }, phase = i * 1.7, pos = j.pos, rot = { 0, 0, 0, 1 } }
        s.joint = try(function() return tf:call("getJointByName", j.name) end)
        if s.joint then f.found = f.found + 1 end
        f.joints[i] = s
    end
    entry.float = f
    return f
end

local function step_ring(s, mode, R, P, dt, t, strength, pack)
    local anchor = vadd(P, qrot(R, s.pivot))
    local accel = { 0, 0, 0 }
    if s.prevAnchor and dt > 0 then
        local v = vscale(vsub(anchor, s.prevAnchor), 1 / dt)
        if s.prevVel then
            accel = vscale(vsub(v, s.prevVel), 1 / dt)
            local a = vlen(accel)
            if a > MAX_ACCEL then accel = vscale(accel, MAX_ACCEL / a) end
        end
        s.prevVel = v
    end
    s.prevAnchor = anchor
    local accLocal = qrot(qconj(R), accel)
    local w = 2 * math.pi * mode.hz
    local k, c = w * w, 2 * mode.damping * w
    local steps = math.max(1, math.ceil(dt / (1 / 240)))
    local h = dt / steps
    for _ = 1, steps do
        local force = vsub(vscale(s.off, -k), vadd(vscale(s.vel, c), vscale(accLocal, mode.gain * strength)))
        s.vel = vadd(s.vel, vscale(force, h))
        s.off = vadd(s.off, vscale(s.vel, h))
    end
    -- Soft clamp, then drift and tremor on top.
    local len = vlen(s.off)
    local disp = len > 1e-9 and vscale(s.off, mode.max * tanh(len / mode.max) / len) or { 0, 0, 0 }
    local p, hz = s.phase, mode.driftHz
    local drift = { math.sin(2 * math.pi * hz[1] * t + p), math.sin(2 * math.pi * hz[2] * t + 2.1 * p),
                    0.5 * math.sin(2 * math.pi * hz[3] * t + 0.7 * p) }
    disp = vadd(disp, vscale(drift, mode.drift * strength))
    if mode.tremor > 0 then
        disp = vadd(disp, vscale({ math.sin(2 * math.pi * 7.3 * t + 3 * p), math.sin(2 * math.pi * 8.9 * t + p), 0 },
                                 mode.tremor * strength))
    end
    -- Tilt away from the offset (about the axis across it and the weapon's length), plus a
    -- slow wobble about the two cross axes.
    local tilt = qaxis(cross({ 0, 0, 1 }, disp), mode.tilt * math.min(1, vlen(disp) / mode.max))
    local wob = mode.driftTilt * strength
    local wobble = qmul(qaxis({ 1, 0, 0 }, wob * math.sin(2 * math.pi * hz[2] * 0.8 * t + p)),
                        qaxis({ 0, 1, 0 }, wob * math.sin(2 * math.pi * hz[1] * 0.9 * t + 2 * p)))
    s.pos = vadd(s.pivot, disp)
    if s.pack then s.pos[3] = s.pos[3] + s.pack * pack end
    s.rot = qmul(tilt, wobble)
end

-- The bow's rings packing toward entry.packTarget (0..1): smooth while winding up, one
-- springy bounce past their rest places when the arrow is loosed.
local PACK_HZ, PACK_BOUNCE = 2.6, 0.4

local function step_pack(entry, dt)
    local target, x, v = entry.packTarget or 0, entry.pack or 0, entry.packVel or 0
    local w = 2 * math.pi * PACK_HZ
    local zeta = target > x and 1.0 or PACK_BOUNCE
    local steps = math.max(1, math.ceil(dt / (1 / 240)))
    local h = dt / steps
    for _ = 1, steps do
        v = v + (w * w * (target - x) - 2 * zeta * w * v) * h
        x = x + v * h
    end
    entry.pack, entry.packVel = x, v
end

-- Rings move when floating is on, or when they pack (the bow) or orbit (the extract orbs),
-- which work without it.
local function rings_active(entry)
    return config.enabled and (config.float or entry.kit.bow ~= nil or entry.kit.gunlance ~= nil or entry.kit.timing ~= nil
                               or (entry.kit.floaters and (entry.kit.floaters.orbit or entry.kit.floaters.flap
                                                           or entry.kit.floaters.spin)) ~= nil)
end

-- An orb circling the blade: its place on the circle (slot 0-2, a third apart), a slow bob,
-- and a tumble about its own centre.
local function orbit_ring(s, spec, t)
    local a = 2 * math.pi * (spec.hz * t + s.orbit / 3) + math.pi / 2
    local c = spec.center
    s.pos = { c[1] + spec.radius * math.cos(a), c[2] + spec.radius * math.sin(a),
              c[3] + 0.03 * math.sin(2 * math.pi * 0.7 * t + s.orbit * 2.1) }
    if spec.face then
        -- Built facing out at their slot: turned with the orbit, spinning about that outward line.
        local bind = 2 * math.pi * s.orbit / 3 + math.pi / 2
        local out = { math.cos(bind), math.sin(bind), 0 }
        s.rot = qmul(qaxis({ 0, 0, 1 }, math.deg(a - bind) % 360), qaxis(out, (t * (spec.spin or 0)) % 360))
    else
        s.rot = qaxis({ 0.3, 1.0, 0.2 }, (t * 70 + s.orbit * 120) % 360)
    end
end

-- The bow's drawn arrow (user, 2026-10-02: the arrow left the rings around the middle one;
-- its line comes from the hunter's draw, not the bow): the game's arrow model, found by its
-- path among the scene's meshes (the nearest to the bow, looked for twice a second until
-- found), gives its line in the bow's frame; the rings slide across onto it and turn square
-- to it. Rings sit on the line where their own height (+Z) meets it.
local ARROW_MATCH, ARROW_LOOK, ARROW_NEAR = "it1199_0000_0", 0.5, 1.5
local ARROW_BLEND, ARROW_MAX_OFF = 0.12, 0.25
local arrowInfo = "not looked for"

local function current_scene()
    return try(function()
        return sdk.call_native_func(sdk.get_native_singleton("via.SceneManager"),
            sdk.find_type_definition("via.SceneManager"), "get_CurrentScene()")
    end)
end

local function vec_of(v) return v and { v.x, v.y, v.z } or nil end

local function find_arrow(P)
    local scene = current_scene()
    local arr = scene and try(function() return scene:call("findComponents(System.Type)", sdk.typeof(MESH)) end)
    local best, bestD = nil, ARROW_NEAR
    for _, m in ipairs(arr and try(function() return arr:get_elements() end) or {}) do
        local path = resource_path(try(function() return m:getMesh() end))
        if path and path:find(ARROW_MATCH, 1, true) then
            local go = try(function() return m:call("get_GameObject") end)
            local tf = go and try(function() return go:call("get_Transform") end)
            local p = tf and vec_of(try(function() return tf:call("get_Position") end))
            local d = p and vlen(vsub(p, P))
            if d and d < bestD then best, bestD = tf, d end
        end
    end
    return best
end

local function follow_arrow(entry, P, R, now)
    local drawing = (entry.packTarget or 0) > 0 and config.bowFollowArrow
    local line = nil
    if drawing then
        local tf = entry.arrowTf
        local ap = tf and vec_of(try(function() return tf:call("get_Position") end))
        if not ap or vlen(vsub(ap, P)) > ARROW_NEAR then
            tf, ap = nil, nil
            if now >= (entry.arrowLookAt or 0) then
                entry.arrowLookAt = now + ARROW_LOOK
                tf = find_arrow(P)
                ap = tf and vec_of(try(function() return tf:call("get_Position") end))
            end
        end
        entry.arrowTf = tf
        local ar = tf and try(function() return tf:call("get_Rotation") end)
        if ap and ar then
            local inv = qconj(R)
            local d = qrot(inv, qrot({ ar.x, ar.y, ar.z, ar.w }, { 0, 0, 1 }))
            if d[3] > 0.5 then line = { p = qrot(inv, vsub(ap, P)), d = d } end
        end
        arrowInfo = line and string.format("found, line off the bow's axis by (%.1f, %.1f) cm at the bow, (%.1f, %.1f) cm 1 m ahead",
            100 * (line.p[1] - line.d[1] * line.p[3] / line.d[3]), 100 * (line.p[2] - line.d[2] * line.p[3] / line.d[3]),
            100 * (line.p[1] + line.d[1] * (1 - line.p[3]) / line.d[3]), 100 * (line.p[2] + line.d[2] * (1 - line.p[3]) / line.d[3]))
            or "drawing, arrow not found"
    end
    if line then entry.arrowLine = line end
    entry.arrowBlend = approach(entry.arrowBlend or 0, line and 1 or 0, 1 / 60, ARROW_BLEND, ARROW_BLEND)
end

-- A ring onto the arrow's line at its height, square to it, by entry.arrowBlend.
local function ring_on_arrow(s, line, blend)
    local t = (s.pos[3] - line.p[3]) / line.d[3]
    local dx, dy = line.p[1] + line.d[1] * t - s.pivot[1], line.p[2] + line.d[2] * t - s.pivot[2]
    local l = math.sqrt(dx * dx + dy * dy)
    if l > ARROW_MAX_OFF then dx, dy = dx * ARROW_MAX_OFF / l, dy * ARROW_MAX_OFF / l end
    s.pos = { s.pos[1] + blend * dx, s.pos[2] + blend * dy, s.pos[3] }
    local angle = math.deg(math.acos(math.max(-1, math.min(1, line.d[3]))))
    s.rot = qmul(qaxis(cross({ 0, 0, 1 }, line.d), angle * blend), s.rot)
end

-- Run the springs once per frame (the first hook that fires), using the weapon's transform.
local function step_floaters()
    local now = os.clock()
    local dt = lastFloatClock and (now - lastFloatClock) or 0
    if lastFloatClock and dt < 0.002 then return end
    lastFloatClock = now
    local reset = dt > 0.1 or not isWeaponDrawn
    dt = math.min(dt, 0.1)
    floatInfo.found, floatInfo.total = 0, 0
    for _, entry in pairs(swapped) do
        local f = rings_active(entry) and float_joints(entry)
        if f then
            if entry.kit.bow or entry.kit.gunlance then step_pack(entry, dt) end
            local strength = config.float and config.floatStrength or 0
            floatInfo.found = floatInfo.found + f.found
            floatInfo.total = floatInfo.total + #f.joints
            local default = entry.kit.floaters.mode
            local pos = try(function() return f.tf:call("get_Position") end)
            local rot = try(function() return f.tf:call("get_Rotation") end)
            if pos and rot then
                local P, R = { pos.x, pos.y, pos.z }, { rot.x, rot.y, rot.z, rot.w }
                if entry.kit.bow then follow_arrow(entry, P, R, now) end
                local blend = entry.kit.bow and entry.arrowLine and (entry.arrowBlend or 0) or 0
                for _, s in ipairs(f.joints) do
                    -- Drawing/sheathing teleports the weapon: start the springs over.
                    if reset then s.prevAnchor, s.prevVel = nil, nil end
                    if s.spin then
                        -- Turning about the weapon's axis at the charge level's speed (the lance's drill).
                        local sp = entry.kit.floaters.spin
                        local lv = math.max(0, math.min(#sp.dps - 1, entry.chargeSmooth or 0))
                        local lo = math.floor(lv)
                        local dps = lerp(sp.dps[lo + 1], sp.dps[math.min(#sp.dps, lo + 2)], lv - lo)
                        s.angle = ((s.angle or 0) + dps * dt) % 360
                        s.pos = s.pivot
                        s.rot = qaxis(type(s.spin) == "table" and s.spin or sp.axis, s.angle)
                    elseif s.flap then
                        local w = entry.kit.floaters.flap
                        s.pos = s.pivot
                        s.rot = qaxis({ 0, 0, 1 }, s.flap * (w.base + w.amp * math.sin(2 * math.pi * w.hz * now)))
                    elseif s.orbit then
                        orbit_ring(s, entry.kit.floaters.orbit, now)
                    else
                        step_ring(s, FLOAT_MODES[s.mode or default], R, P, reset and 0 or dt, now, strength, entry.pack or 0)
                        -- Drawn out from its root (the gunlance's gold thread): at entry.stretch of its length.
                        if s.stretch then
                            s.pos[3] = s.stretch + (s.pivot[3] - s.stretch) * math.max(0.15, entry.stretch or 0)
                        end
                        -- Lifted along the weapon (the sword's timing ring).
                        if s.slide then s.pos[3] = s.pos[3] + (entry.slide or 0) end
                        if blend > 0.001 then ring_on_arrow(s, entry.arrowLine, blend) end
                    end
                end
            end
        end
    end
end

-- Quaternion slerp, the shorter way (as build_weapon_kit's preview does).
local function qslerp(a, b, t)
    local d = a[1] * b[1] + a[2] * b[2] + a[3] * b[3] + a[4] * b[4]
    if d < 0 then b, d = { -b[1], -b[2], -b[3], -b[4] }, -d end
    local wa, wb
    if d > 0.9995 then
        wa, wb = 1 - t, t
    else
        local th = math.acos(d)
        wa, wb = math.sin((1 - t) * th) / math.sin(th), math.sin(t * th) / math.sin(th)
    end
    local q = { wa * a[1] + wb * b[1], wa * a[2] + wb * b[2], wa * a[3] + wb * b[3], wa * a[4] + wb * b[4] }
    local l = math.sqrt(q[1] * q[1] + q[2] * q[2] + q[3] * q[3] + q[4] * q[4])
    return { q[1] / l, q[2] / l, q[3] / l, q[4] / l }
end

local IDENTITY = { 0, 0, 0, 1 }
local morphInfo = { found = 0, total = 0 }

-- The morph's joints at entry.morphP. A joint resting at its bind pose is set once (the game
-- may also put it back there); one away from it is set in every pass.
local function apply_morph(entry)
    local m = entry.kit.mode and entry.kit.mode.morph
    if not (m and entry.morphP and config.enabled) then return end
    local js = entry.morphJoints
    if not js then
        local tf = try(function() return entry.go:call("get_Transform") end)
        if not tf then return end
        js = {}
        for i, j in ipairs(m.joints) do
            js[i] = { joint = try(function() return tf:call("getJointByName", j.name) end) }
        end
        entry.morphJoints = js
    end
    morphInfo.found, morphInfo.total = 0, #m.joints
    local p = entry.morphP
    for i, j in ipairs(m.joints) do
        local s = js[i]
        if s.joint then
            morphInfo.found = morphInfo.found + 1
            local e = eased(p, j.win)
            local a, b = j.base or { pos = j.pivot, rot = IDENTITY }, j.alt or { pos = j.pivot, rot = IDENTITY }
            local atBind = (not j.base or e >= 1) and (not j.alt or e <= 0)
            if not (atBind and s.atBind) then
                local pos, rot = lerp3(a.pos, b.pos, e), qslerp(a.rot, b.rot, e)
                try(function() s.joint:call("set_LocalPosition", Vector3f.new(pos[1], pos[2], pos[3])) end)
                try(function() s.joint:call("set_LocalRotation", to_quat(rot)) end)
                s.atBind = atBind
            end
        end
    end
end

local function apply_floaters(phase)
    floatInfo.phases[phase] = true
    for _, entry in pairs(swapped) do apply_morph(entry) end
    for _, entry in pairs(swapped) do
        local f = entry.float
        if f and rings_active(entry) then
            for _, s in ipairs(f.joints) do
                if s.joint then
                    try(function() s.joint:call("set_LocalPosition", Vector3f.new(s.pos[1], s.pos[2], s.pos[3])) end)
                    try(function() s.joint:call("set_LocalRotation", to_quat(s.rot)) end)
                end
            end
        end
    end
end

-- Joint poses may be rewritten by the game's motion update, so set them after behaviour
-- updates and again just before rendering; whichever lands last wins.
local floatHooked = false
if re.on_application_entry then
    floatHooked = pcall(re.on_application_entry, "LateUpdateBehavior", function()
        step_floaters(); apply_floaters("LateUpdateBehavior")
    end) or floatHooked
end
if re.on_pre_application_entry then
    for _, phase in ipairs({ "PrepareRendering", "BeginRendering" }) do
        floatHooked = pcall(re.on_pre_application_entry, phase, function()
            step_floaters(); apply_floaters(phase)
        end) or floatHooked
    end
end

-- Set our model again on a weapon (same model and material): the first set can land before
-- the resource finished loading and then shows nothing.
local function refresh(entry)
    local mesh = component(entry.go, MESH)
    if not mesh then return end
    set_model(entry.go, mesh, entry.kitMesh, entry.kitMdf or entry.kit.mdf2, nil)
    entry.vars, entry.written, entry.glowSlots, entry.stateSlots, entry.float = nil, nil, nil, nil, nil
    entry.partsOn, entry.fadeOn, entry.morphJoints = nil, nil, nil
    apply_tuning(entry, mesh)
end

-- The insect glaive's kinsect: the hunter's get_Wp10Insect (like get_Weapon; found in the
-- game's type names), else the weapon handling's _Insect. A component or its GameObject.
local function kinsect_of(chr)
    local t = slots.Weapon and weapon_type(slots.Weapon.original)
    if t ~= "it10" then return nil end
    local ins = try(function() return chr:call("get_Wp10Insect") end)
    if not ins then
        local h = try(function() return chr:call("get_WeaponHandling") end)
        ins = h and try(function() return h:get_field("_Insect") end)
    end
    if not ins then return nil end
    local go = try(function() return ins:call("get_GameObject") end)
    if not go and try(function() return ins:get_type_definition():get_full_name() end) == "via.GameObject" then go = ins end
    return go and { get_GameObject = function() return go end } or nil
end

local wasDrawn = isWeaponDrawn
local function refresh_pass()
    local now = os.clock()
    for _, entry in pairs(swapped) do
        if entry.refreshAt and now >= entry.refreshAt then
            entry.refreshAt = nil
            refresh(entry)
        elseif entry.drawRefresh and isWeaponDrawn and not wasDrawn then
            entry.drawRefresh = nil
            refresh(entry)
        end
    end
    wasDrawn = isWeaponDrawn
end

re.on_frame(function()
    frame = frame + 1
    local chr = player_character()
    if not chr then return end
    -- Drop weapon objects the game destroyed (switching weapons) before touching them again:
    -- calls on them throw inside the game (REFramework logs each one).
    for addr, entry in pairs(swapped) do
        if not try(function() return entry.go:get_Valid() end) then swapped[addr] = nil end
    end
    if config.enabled then refresh_pass() end
    if config.enabled then update_states(chr) end
    if not floatHooked then step_floaters(); apply_floaters("frame") end
    -- Visibility follows draw/sheathe immediately; model checks run less often.
    if frame % CHECK_EVERY ~= 0 then
        if config.enabled then
            for _, entry in pairs(swapped) do
                try(function() entry.go:set_DrawSelf(entry_visible(entry)) end)
            end
        end
        return
    end
    update_slot("Weapon", try(function() return chr:get_Weapon() end))
    update_slot("SubWeapon", try(function() return chr:get_SubWeapon() end))
    update_slot("Kinsect", kinsect_of(chr))
end)

-- ------------------------------------------------------------------ menu
-- (kinsect_of is above the frame loop)

re.on_draw_ui(function()
    if not imgui.tree_node("MiquellaLight: Light Weapons") then return end
    local changed, c
    c, config.enabled = imgui.checkbox("Enabled", config.enabled)
    changed = c
    c, config.hideSheathed = imgui.checkbox("Hide while sheathed", config.hideSheathed)
    changed = changed or c
    c, config.glow = imgui.slider_float("Glow", config.glow, 0.0, 10.0, "%.2f")
    changed = changed or c
    local sizeIdx = 1
    for i, n in ipairs(SIZE_NAMES) do if n == config.size then sizeIdx = i end end
    local c3, newSize = imgui.combo("Size (dual blades)", sizeIdx, SIZE_NAMES)
    if c3 then config.size = SIZE_NAMES[newSize]; changed = true end
    c, config.recordFields = imgui.checkbox("Record weapon fields (for Claude)", config.recordFields)
    changed = changed or c
    if config.recordFields and rec.type then
        imgui.text(string.format("Recording %s: %d samples", rec.type, rec.samples))
    end
    c, config.float = imgui.checkbox("Floating rings", config.float)
    changed = changed or c
    c, config.floatStrength = imgui.slider_float("Ring motion", config.floatStrength, 0.0, 3.0, "%.2f")
    changed = changed or c
    if floatInfo.total > 0 then
        local phases = {}
        for p in pairs(floatInfo.phases) do phases[#phases + 1] = p end
        table.sort(phases)
        imgui.text(string.format("Rings found: %d/%d (set at %s)", floatInfo.found, floatInfo.total,
                                 #phases > 0 and table.concat(phases, ", ") or "-"))
    end
    for _, entry in pairs(swapped) do
        if (entry.kit.charge or entry.kit.bow) and stateInfo.charge then imgui.text("Charge: " .. stateInfo.charge) end
        if entry.kit.extracts and stateInfo.extract then imgui.text("Extracts: " .. stateInfo.extract) end
        if entry.kit.gunlance and stateInfo.gunlance then imgui.text("Gunlance: " .. stateInfo.gunlance) end
        if entry.kit.timing and stateInfo.timing then imgui.text("Perfect Rush: " .. stateInfo.timing) end
        if stateInfo.gauges and stateInfo.gauges[entry.kit] then imgui.text("Gauges: " .. stateInfo.gauges[entry.kit]) end
        if entry.kit.mode and stateInfo.mode then
            imgui.text("Mode: " .. stateInfo.mode)
            if morphInfo.total > 0 then
                imgui.text(string.format("Morph joints found: %d/%d", morphInfo.found, morphInfo.total))
            end
            local wtype = slots.Weapon and weapon_type(slots.Weapon.original)
            if wtype then
                local inv
                c, inv = imgui.checkbox("Swap modes##" .. wtype, config.modeInvert[wtype] == true)
                if c then config.modeInvert[wtype] = inv or nil; changed = true end
            end
        end
        if entry.kit.bow and stateInfo.draw then
            imgui.text("Draw: " .. stateInfo.draw)
            c, config.bowFrom0 = imgui.checkbox("Bow charge counts from 0", config.bowFrom0)
            changed = changed or c
            c, config.bowFollowArrow = imgui.checkbox("Rings follow the arrow", config.bowFollowArrow)
            imgui.text("Arrow: " .. arrowInfo)
            changed = changed or c
        end
        if entry.kit.gauge and stateInfo.gauge then imgui.text("Gauge: " .. stateInfo.gauge) end
    end
    imgui.text("Weapon drawn: " .. tostring(isWeaponDrawn))

    if not (slots.Weapon and slots.Weapon.original) then
        imgui.text("Load your hunter and equip a weapon: a 'Look' list appears below")
        imgui.text("  Looks: " .. table.concat(KIT_NAMES, ", ", 2))
    end
    if slots.Kinsect and slots.Kinsect.original then
        local k = assigned_kit(slots.Kinsect.original)
        imgui.text("Kinsect: " .. slots.Kinsect.original .. (k and ("  ->  " .. k) or ""))
    elseif slots.Weapon and weapon_type(slots.Weapon.original) == "it10" then
        imgui.text("Kinsect: not found (no get_Wp10Insect / _Insect)")
    end
    for _, name in ipairs({ "Weapon", "SubWeapon" }) do
        local s = slots[name]
        if s and s.original then
            imgui.text(name .. ": " .. s.original)
            local wtype = weapon_type(s.original)
            local typeName = wtype and (TYPE_LABELS[wtype] or wtype) or "this model"
            local second = model_index(s.original) == "1" and not (wtype and BOTH_HANDS[wtype])
            local main = wtype and config.assignType[wtype]
            if second and not (main and KITS[main] and KITS[main].shield) then
                -- Scabbard, quiver, or a shield whose weapon look has none: left as the game made it.
                imgui.text("  (keeps its game look" .. (main and "" or "; choose the weapon's look first") .. ")")
            else
                local list = second and shield_names(wtype) or MAIN_NAMES
                local currentKit = assigned_kit(s.original)
                local idx = 1
                for i, k in ipairs(list) do
                    if k == currentKit then idx = i end
                end
                local label = second and ((wtype == "it11" and "Quiver look (all " or "Shield look (all ") .. typeName .. ")")
                    or ("Look (all " .. typeName .. ")")
                local c2, newIdx = imgui.combo(label .. "##" .. name, idx, list)
                if c2 then
                    local kit = (newIdx > 1) and list[newIdx] or nil
                    if second then
                        config.assignShield[wtype] = kit or "(original)"
                    elseif wtype then
                        config.assignType[wtype] = kit
                    end
                    config.assign[s.original] = nil
                    if not wtype then config.assign[s.original] = kit end
                    changed = true
                end
            end
        else
            imgui.text(name .. ": (none)")
        end
    end

    if (next(config.assignType) or next(config.assign)) and imgui.tree_node("Assigned looks") then
        for wtype, kitName in pairs(config.assignType) do
            if imgui.button("Remove##" .. wtype) then
                config.assignType[wtype] = nil
                config.assignShield[wtype] = nil
                changed = true
                break
            end
            imgui.same_line()
            local shield = config.assignShield[wtype]
            imgui.text(kitName .. "  <-  all " .. (TYPE_LABELS[wtype] or wtype)
                .. (shield and ("  (shields: " .. shield .. ")") or ""))
        end
        for path, kitName in pairs(config.assign) do
            if imgui.button("Remove##" .. path) then
                config.assign[path] = nil
                changed = true
                break
            end
            imgui.same_line()
            imgui.text(kitName .. "  <-  " .. path)
        end
        imgui.tree_pop()
    end

    if lastError ~= "" then imgui.text_colored(lastError, 0xFF6060FF) end
    if changed then save_config() end
    imgui.tree_pop()
end)
