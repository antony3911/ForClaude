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
        glow = { MiquellaBlade = 1.2, MiquellaGlow = 1.2, MiquellaTemper = 1.2 },
        -- Rings on the spine: bone pivots in the model's space (build_weapon_kit.py log).
        floaters = { mode = "swing", joints = {
            { name = "MQ_Ring0", pos = { 0.0456, 0.0, 1.2189 } },
            { name = "MQ_Ring1", pos = { 0.0222, 0.0, 1.4818 } },
            { name = "MQ_Ring2", pos = { -0.0217, 0.0, 1.7585 } } } },
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
    },
}
local SIZE_NAMES = { "1.0", "1.2", "1.4", "1.6" }
local KIT_NAMES = { "(original)" }
for name in pairs(KITS) do KIT_NAMES[#KIT_NAMES + 1] = name end
table.sort(KIT_NAMES, function(a, b)
    if a == "(original)" then return true end
    if b == "(original)" then return false end
    return a < b
end)

local config = {
    enabled = true,
    hideSheathed = true,
    -- original .mesh path -> kit name
    assign = {},
    -- In-game tuning: glow multiplies the kit's Emissive_Intensity; size picks the model.
    glow = 1.0,
    size = "1.4",
    -- Floating rings (great sword spine, light bowgun beam): on/off and how lively.
    float = true,
    floatStrength = 1.0,
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
if type(config.swappedFrom) ~= "table" then config.swappedFrom = {} end
local function save_config() json.dump_file(CONFIG_PATH, config) end

local function try(fn, ...)
    local ok, result = pcall(fn, ...)
    if ok then return result end
    return nil
end

-- ------------------------------------------------------------------ resources

local holders = {}
local function holder(typeName, path)
    local key = typeName .. "|" .. path
    if holders[key] == nil then
        holders[key] = try(function()
            local res = sdk.create_resource(typeName, path):add_ref()
            return res:create_holder(typeName .. "Holder"):add_ref()
        end) or false
    end
    return holders[key] or nil
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
                    slots[#slots + 1] = { mat = i, var = j, base = base }
                end
            end
        end
    end
    return slots
end

local function kit_mesh(kit)
    return kit.sizes and kit.sizes[config.size] or kit.mesh
end

-- Apply the Glow slider to a swapped weapon.
local function apply_tuning(entry, mesh)
    entry.glowSlots = entry.glowSlots or glow_slots(mesh, entry.kit)
    for _, s in ipairs(entry.glowSlots) do
        try(function() mesh:setMaterialFloat(s.mat, s.var, s.base * config.glow) end)
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
    for path, kitName in pairs(config.assign) do
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
    if set_model(go, mesh, kit_mesh(kit), kit.mdf2, NULL_CHAIN) then
        swapped[go:get_address()] = { go = go, original = original, chain = originalChain,
                                      kit = kit, kitMesh = kit_mesh(kit) }
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

    local kitName = config.enabled and original and config.assign[original]
    local kit = kitName and KITS[kitName]
    if kit then
        -- Swap when the game shows its own model (first time, or it reloaded the weapon).
        -- (or the size changed: then `current` is our other size and `original` stays the game's).
        if current ~= kit_mesh(kit) then swap_in(go, mesh, original, kit, name) end
        if swapped[key] then apply_tuning(swapped[key], mesh) end
        -- Only our light weapons vanish; if the swap failed, leave the original alone.
        if config.hideSheathed and swapped[key] then
            try(function() go:set_DrawSelf(isWeaponDrawn) end)
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

local function update_states(chr)
    local now = os.clock()
    local dt = math.min(now - lastClock, 0.1)
    lastClock = now
    local target = demon_target(chr)
    local rate = dt / (target > demonProgress and DEMON_IN or DEMON_OUT)
    demonProgress = demonProgress + math.max(-rate, math.min(rate, target - demonProgress))
    for _, entry in pairs(swapped) do
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
        local s = f.joints[i] or { name = j.name, pivot = j.pos, off = { 0, 0, 0 }, vel = { 0, 0, 0 },
                                   phase = i * 1.7, pos = j.pos, rot = { 0, 0, 0, 1 } }
        s.joint = try(function() return tf:call("getJointByName", j.name) end)
        if s.joint then f.found = f.found + 1 end
        f.joints[i] = s
    end
    entry.float = f
    return f
end

local function step_ring(s, mode, R, P, dt, t, strength)
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
    s.rot = qmul(tilt, wobble)
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
        local f = config.enabled and config.float and float_joints(entry)
        if f then
            floatInfo.found = floatInfo.found + f.found
            floatInfo.total = floatInfo.total + #f.joints
            local mode = FLOAT_MODES[entry.kit.floaters.mode]
            local pos = try(function() return f.tf:call("get_Position") end)
            local rot = try(function() return f.tf:call("get_Rotation") end)
            if pos and rot then
                local P, R = { pos.x, pos.y, pos.z }, { rot.x, rot.y, rot.z, rot.w }
                for _, s in ipairs(f.joints) do
                    -- Drawing/sheathing teleports the weapon: start the springs over.
                    if reset then s.prevAnchor, s.prevVel = nil, nil end
                    step_ring(s, mode, R, P, reset and 0 or dt, now, config.floatStrength)
                end
            end
        end
    end
end

local function apply_floaters(phase)
    floatInfo.phases[phase] = true
    for _, entry in pairs(swapped) do
        local f = entry.float
        if f and config.enabled and config.float then
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

re.on_frame(function()
    frame = frame + 1
    local chr = player_character()
    if not chr then return end
    if config.enabled then update_states(chr) end
    if not floatHooked then step_floaters(); apply_floaters("frame") end
    -- Visibility follows draw/sheathe immediately; model checks run less often.
    if frame % CHECK_EVERY ~= 0 then
        if config.enabled and config.hideSheathed then
            for _, entry in pairs(swapped) do
                try(function() entry.go:set_DrawSelf(isWeaponDrawn) end)
            end
        end
        return
    end
    for addr, entry in pairs(swapped) do
        if not try(function() return entry.go:get_Valid() end) then swapped[addr] = nil end
    end
    update_slot("Weapon", try(function() return chr:get_Weapon() end))
    update_slot("SubWeapon", try(function() return chr:get_SubWeapon() end))
end)

-- ------------------------------------------------------------------ menu

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
    imgui.text("Weapon drawn: " .. tostring(isWeaponDrawn))

    if not (slots.Weapon and slots.Weapon.original) then
        imgui.text("Load your hunter and equip a weapon: a 'Look' list appears below")
        imgui.text("  Looks: " .. table.concat(KIT_NAMES, ", ", 2))
    end
    for _, name in ipairs({ "Weapon", "SubWeapon" }) do
        local s = slots[name]
        if s and s.original then
            imgui.text(name .. ": " .. s.original)
            local currentKit = config.assign[s.original]
            local idx = 1
            for i, k in ipairs(KIT_NAMES) do
                if k == currentKit then idx = i end
            end
            local c2, newIdx = imgui.combo("Look##" .. name, idx, KIT_NAMES)
            if c2 then
                config.assign[s.original] = (newIdx > 1) and KIT_NAMES[newIdx] or nil
                changed = true
            end
        else
            imgui.text(name .. ": (none)")
        end
    end

    if next(config.assign) and imgui.tree_node("Assigned weapons") then
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
