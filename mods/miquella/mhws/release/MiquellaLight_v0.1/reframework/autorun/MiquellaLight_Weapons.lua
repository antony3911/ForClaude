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
local KITS = {
    DualBlades = {
        label = "Miquella light blade (dual blades)",
        mesh = "Art/Model/MiquellaLight/DualBlades/wp_miquella_db.mesh",
        mdf2 = "Art/Model/MiquellaLight/DualBlades/wp_miquella_db.mdf2",
    },
}
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
}
local saved = json.load_file(CONFIG_PATH)
if saved then
    for k, v in pairs(saved) do config[k] = v end
end
-- An empty table is saved as JSON null; don't let that replace the assignment table.
if type(config.assign) ~= "table" then config.assign = {} end
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

local function swap_in(go, mesh, original, kit)
    local chain = component(go, CHAIN2)
    local originalChain = chain and resource_path(try(function() return chain:get_ChainAsset() end))
    -- Remember each original model's physics chain. If the game restored only its model,
    -- the chain on the object is still ours, so use the one remembered earlier.
    if originalChain and originalChain ~= NULL_CHAIN then
        chainOf[original] = originalChain
    else
        originalChain = chainOf[original]
    end
    if set_model(go, mesh, kit.mesh, kit.mdf2, NULL_CHAIN) then
        swapped[go:get_address()] = { go = go, original = original, chain = originalChain, kitMesh = kit.mesh }
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
        if current ~= kit.mesh then swap_in(go, mesh, current, kit) end
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

re.on_frame(function()
    frame = frame + 1
    local chr = player_character()
    if not chr then return end
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
    imgui.text("Weapon drawn: " .. tostring(isWeaponDrawn))

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
