-- MiquellaLight Effects
--
-- 1. Dual blades effects: red -> gold, blue -> silver at runtime. The recoloured effect
--    files are not enough: the game hands some effects their colours while it runs, as
--    extern parameters (Color on the attack trail 11_it02_001, ColorA/B/C on the archdemon
--    body glow and forearm flames 11_it02_002; found with the FX probe). Every new effect
--    is caught as the game adds its parameters (hook) and checked on the next frame, so a
--    red trail shows for one frame at most; the effects found then are re-checked every
--    frame while they play (parameters and the effect's tint), and a slower scan of all
--    effects catches anything the hook missed.
-- 2. Hide the attack-up / defense-up glow: pl_state/11_pl_heal, which the game tints red
--    (attack up) or orange (defense up) and replays every ~2 s. Its tint is set to
--    transparent black; the same effect with other tints (healing) is left alone.
--
-- Both can be switched off in the REFramework menu (Script Generated UI -> MiquellaLight
-- Effects); the choice is saved in reframework/data/MiquellaLight/Effects.json.
-- Untested in game; every call is wrapped in pcall.

local MOD = "MiquellaLight Effects"
local CONFIG_PATH = "MiquellaLight/Effects.json"
local EP = "via.effect.EffectPlayer"
local SCAN_EVERY = 0.25                 -- seconds between searches for new effects
local RECOLOR_MATCH = "it02"            -- dual blades effect files / objects (11_it02_*)
local COLOR_PARAMS = { "Color", "ColorA", "ColorB", "ColorC" }
local BUFF_MATCH = "11_pl_heal"
local BUFF_TINTS = { [0xFF3333] = "attack up", [0xFF8040] = "defense up" }   -- tint RGB as 0xRRGGBB
local GOLD_HUE, SILVER_HUE, SILVER_SAT, SILVER_VALUE = 38, 220, 0.08, 0.9   -- as recolor_efx.py

local config = { recolor = true, hideBuffs = true }
local saved = json.load_file(CONFIG_PATH)
if type(saved) == "table" then
    for k, v in pairs(saved) do config[k] = v end
end

local stats = { spawn = 0, playing = 0, buffs = 0 }
local tracked = {}                      -- address -> { ep, kind = "recolor" | "buff", ran, born }
local pending = {}                      -- effects just created: { ep, frames }
local MAX_PENDING = 128
local PENDING_FRAMES = 10               -- frames to wait for a new effect's name / resource
local IDLE_DROP = 3                     -- seconds a recoloured effect may sit idle before it is dropped
local nextScan = 0
local hookOk = false

local function try(fn, ...)
    local ok, result = pcall(fn, ...)
    if ok then return result end
    return nil
end

-- ------------------------------------------------------------------ colours

-- via.Color packs R in the low byte: rgba = R | G<<8 | B<<16 | A<<24.
local function unpack_rgba(v)
    return v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF, (v >> 24) & 0xFF
end

local function rgb_of(v)
    local r, g, b = unpack_rgba(v)
    return (r << 16) | (g << 8) | b
end

local function to_hsv(r, g, b)
    local mx, mn = math.max(r, g, b), math.min(r, g, b)
    local d = mx - mn
    local h = 0
    if d > 0 then
        if mx == r then h = ((g - b) / d) % 6
        elseif mx == g then h = (b - r) / d + 2
        else h = (r - g) / d + 4 end
    end
    return h * 60, mx > 0 and d / mx or 0, mx
end

local function from_hsv(h, s, v)
    local c = v * s
    local x = c * (1 - math.abs((h / 60) % 2 - 1))
    local r, g, b
    if h < 60 then r, g, b = c, x, 0
    elseif h < 120 then r, g, b = x, c, 0
    elseif h < 180 then r, g, b = 0, c, x
    elseif h < 240 then r, g, b = 0, x, c
    elseif h < 300 then r, g, b = x, 0, c
    else r, g, b = c, 0, x end
    local m = v - c
    return r + m, g + m, b + m
end

-- Red -> gold, blue -> silver (brightness, saturation and alpha kept); nil if unchanged.
local function recolor(rgba)
    local r, g, b, a = unpack_rgba(rgba)
    local h, s, v = to_hsv(r / 255, g / 255, b / 255)
    if s < 0.3 or v < 0.2 then return nil end
    local nr, ng, nb
    if h < 25 or h > 320 then
        nr, ng, nb = from_hsv(GOLD_HUE, s, v)
    elseif h > 190 and h < 265 then
        nr, ng, nb = from_hsv(SILVER_HUE, SILVER_SAT * s, SILVER_VALUE * v)
    else
        return nil
    end
    local function byte(x) return math.floor(x * 255 + 0.5) end
    return byte(nr) | (byte(ng) << 8) | (byte(nb) << 16) | (a << 24)
end

local colorTd = sdk.find_type_definition("via.Color")

local function make_color(rgba)
    local c = ValueType.new(colorTd)
    if not pcall(function() c:set_field("rgba", rgba) end) then c.rgba = rgba end
    return c
end

local function rgba_of(c)
    local v = c and try(function() return c:get_field("rgba") end)
    return type(v) == "number" and (math.tointeger(v) or 0) & 0xFFFFFFFF or nil
end

-- Recolour one colour extern parameter object; true if it changed.
local function recolor_param(p)
    local rgba = rgba_of(try(function() return p:call("get_Color") end))
    local new = rgba and recolor(rgba)
    if not new then return false end
    return pcall(function() p:call("set_Color(via.Color)", make_color(new)) end)
end

-- ------------------------------------------------------------------ new effects (hook)

local function effect_name(ep)
    local go = try(function() return ep:call("get_GameObject") end)
    local name = go and try(function() return go:call("get_Name") end)
    if name then return name end
    local res = try(function() return ep:call("get_Resource") end)
    return res and try(function() return res:ToString() end) or ""
end

-- Every new effect gets its parameters added (the parameter itself is a fixed native object,
-- not something a script can recolour), so this is where new effects are noticed. They are
-- looked at on the next frame, when their name and colours are in place.
local function on_add_param(args)
    if not config.recolor or #pending >= MAX_PENDING then return end
    local ep = sdk.to_managed_object(args[2])
    if ep then pending[#pending + 1] = { ep = ep, frames = 0 } end
end

hookOk = pcall(function()
    sdk.hook(sdk.find_type_definition(EP):get_method("addExternParameter(via.effect.ExternParameter)"),
        function(args) pcall(on_add_param, args) end,
        function(retval) return retval end)
end)

-- ------------------------------------------------------------------ playing effects

local function current_scene()
    return try(function()
        return sdk.call_native_func(sdk.get_native_singleton("via.SceneManager"),
            sdk.find_type_definition("via.SceneManager"), "get_CurrentScene()")
    end)
end

local function scan()
    local scene = current_scene()
    local arr = scene and try(function() return scene:call("findComponents(System.Type)", sdk.typeof(EP)) end)
    for _, ep in ipairs(arr and try(function() return arr:get_elements() end) or {}) do
        local key = try(function() return ep:get_address() end)
        if key and not tracked[key] then
            local name = effect_name(ep)
            if config.recolor and name:find(RECOLOR_MATCH, 1, true) then
                tracked[key] = { ep = ep, kind = "recolor" }
            elseif config.hideBuffs and name:find(BUFF_MATCH, 1, true) then
                local tint = rgba_of(try(function() return ep:call("get_Color") end))
                if tint and BUFF_TINTS[rgb_of(tint)] then tracked[key] = { ep = ep, kind = "buff" } end
            end
        end
    end
end

local TRANSPARENT = 0

-- Recolour an effect's colour parameters and tint; the number of colours changed.
local function recolor_effect(ep, tint)
    local n = 0
    for _, name in ipairs(COLOR_PARAMS) do
        local p = try(function() return ep:call("getExternParameter(System.String)", name) end)
        if p and recolor_param(p) then n = n + 1 end
    end
    local new = recolor(tint)
    if new and pcall(function() ep:call("set_Color(via.Color)", make_color(new)) end) then n = n + 1 end
    return n
end

local function update(key, t)
    local ep = t.ep
    local tint = rgba_of(try(function() return ep:call("get_Color") end))
    if not tint then tracked[key] = nil; return end          -- gone
    if t.kind == "recolor" then
        if not config.recolor then tracked[key] = nil; return end
        stats.playing = stats.playing + recolor_effect(ep, tint)
        -- Drop effects that have finished playing (trails are new objects for every attack).
        if try(function() return ep:call("get_Running") end) then
            t.ran, t.idle = true, nil
        else
            t.idle = t.idle or os.clock()
            if t.ran or os.clock() - t.idle > IDLE_DROP then tracked[key] = nil end
        end
    else
        if not config.hideBuffs then
            tracked[key] = nil
        elseif BUFF_TINTS[rgb_of(tint)] then
            if pcall(function() ep:call("set_Color(via.Color)", make_color(TRANSPARENT)) end) then
                stats.buffs = stats.buffs + 1
            end
        elseif tint ~= TRANSPARENT then
            tracked[key] = nil                                 -- reused for something else (healing)
        end
    end
end

-- New effects from the hook: dual blades ones are recoloured right away and tracked.
local function take_pending()
    local still = {}
    for _, item in ipairs(pending) do
        local ep = item.ep
        local key = try(function() return ep:get_address() end)
        local name = key and effect_name(ep) or ""
        if name:find(RECOLOR_MATCH, 1, true) then
            if not tracked[key] then
                tracked[key] = { ep = ep, kind = "recolor" }
                local tint = rgba_of(try(function() return ep:call("get_Color") end))
                if tint then stats.spawn = stats.spawn + recolor_effect(ep, tint) end
            end
        elseif key and name == "" and item.frames < PENDING_FRAMES then
            item.frames = item.frames + 1
            still[#still + 1] = item                     -- not set up yet: look again next frame
        end
    end
    pending = still
end

re.on_frame(function()
    if not (config.recolor or config.hideBuffs) then return end
    if #pending > 0 then pcall(take_pending) end
    if os.clock() >= nextScan then
        nextScan = os.clock() + SCAN_EVERY
        pcall(scan)
    end
    for key, t in pairs(tracked) do
        pcall(update, key, t)
    end
end)

re.on_draw_ui(function()
    if not imgui.tree_node(MOD) then return end
    local changed
    changed, config.recolor = imgui.checkbox("Dual blades effects: red -> gold, blue -> silver", config.recolor)
    if changed then json.dump_file(CONFIG_PATH, config) end
    changed, config.hideBuffs = imgui.checkbox("Hide attack-up / defense-up glow", config.hideBuffs)
    if changed then json.dump_file(CONFIG_PATH, config) end
    local n = 0
    for _ in pairs(tracked) do n = n + 1 end
    imgui.text(string.format("Recoloured: %d at spawn, %d on playing effects. Buff glows hidden: %d. Tracking %d.%s",
        stats.spawn, stats.playing, stats.buffs, n, hookOk and "" or " (spawn hook unavailable)"))
    imgui.tree_pop()
end)
