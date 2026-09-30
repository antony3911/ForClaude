-- MiquellaLight: Hide Sheathed Weapons (Monster Hunter Wilds, REFramework)
--
-- The light weapons have no scabbard: they appear when drawn and vanish when sheathed.
-- This script hides the player's weapon (and sub weapon, e.g. the Sword & Shield energy
-- shield) while it is sheathed, and only for the weapons listed in the config, so other
-- weapons are left alone.
--
-- STATUS: untested draft, written before the game was available. The method names come
-- from the open-source MDF-XL script (SilverEzredes/MDF-XL), which uses the same calls.
-- Verify in game before relying on it.
--
-- Visual only: this changes whether the weapon is drawn on screen, nothing else.

local CONFIG_PATH = "MiquellaLight/HideSheathed.json"

local config = {
    enabled = true,
    applyToAll = false,
    hideSubWeapon = true,
    -- GameObject names of the weapons this mod replaces. Use "Add current weapon" in the
    -- REFramework menu while holding the weapon to fill this in.
    weaponNames = {},
}

local saved = json.load_file(CONFIG_PATH)
if saved then
    for k, v in pairs(saved) do
        config[k] = v
    end
end

local function save_config()
    json.dump_file(CONFIG_PATH, config)
end

local playerManager = nil
local isWeaponDrawn = false
local currentWeaponName = ""
-- GameObjects this script has hidden, so they can be restored when they stop matching.
local hiddenByUs = {}

local function get_player_character()
    if playerManager == nil then
        playerManager = sdk.get_managed_singleton("app.PlayerManager")
    end
    if playerManager == nil then return nil end
    local master = playerManager:getMasterPlayer()
    if master == nil or not master:get_Valid() then return nil end
    return master:get_Character()
end

-- Track whether the local player's weapon is drawn.
sdk.hook(sdk.find_type_definition("app.HunterCharacter"):get_method("checkWeaponOn()"),
    function(args)
        local hunter = sdk.to_managed_object(args[2])
        if hunter ~= nil and hunter:ToString():match("MasterPlayer") then
            isWeaponDrawn = hunter._IsWeaponOn
        end
    end,
    function(retval)
        return retval
    end
)

local function is_target(name)
    if config.applyToAll then return true end
    for _, n in ipairs(config.weaponNames) do
        if n == name then return true end
    end
    return false
end

local function update_visibility(component)
    if component == nil then return end
    local go = component:get_GameObject()
    if go == nil then return end
    local name = go:get_Name()
    local key = go:get_address()

    if config.enabled and is_target(name) then
        local visible = isWeaponDrawn
        go:set_DrawSelf(visible)
        hiddenByUs[key] = (not visible) and go or nil
    elseif hiddenByUs[key] ~= nil then
        -- No longer a target (setting changed): restore it once.
        go:set_DrawSelf(true)
        hiddenByUs[key] = nil
    end
end

re.on_frame(function()
    local chr = get_player_character()
    if chr == nil then return end

    local weapon = chr:get_Weapon()
    if weapon ~= nil then
        local go = weapon:get_GameObject()
        currentWeaponName = go and go:get_Name() or ""
    end

    update_visibility(weapon)
    if config.hideSubWeapon then
        update_visibility(chr:get_SubWeapon())
    end
end)

re.on_draw_ui(function()
    if imgui.tree_node("MiquellaLight: Hide Sheathed Weapons") then
        local changed = false
        local c1, c2, c3
        c1, config.enabled = imgui.checkbox("Enabled", config.enabled)
        c2, config.applyToAll = imgui.checkbox("Apply to every weapon", config.applyToAll)
        c3, config.hideSubWeapon = imgui.checkbox("Also hide sub weapon (shield)", config.hideSubWeapon)
        changed = c1 or c2 or c3

        imgui.text("Current weapon: " .. currentWeaponName)
        imgui.text("Drawn: " .. tostring(isWeaponDrawn))
        if currentWeaponName ~= "" and not is_target(currentWeaponName) then
            if imgui.button("Add current weapon") then
                table.insert(config.weaponNames, currentWeaponName)
                changed = true
            end
        end

        for i, n in ipairs(config.weaponNames) do
            if imgui.button("Remove##" .. i) then
                table.remove(config.weaponNames, i)
                changed = true
                break
            end
            imgui.same_line()
            imgui.text(n)
        end

        if changed then save_config() end
        imgui.tree_pop()
    end
end)
