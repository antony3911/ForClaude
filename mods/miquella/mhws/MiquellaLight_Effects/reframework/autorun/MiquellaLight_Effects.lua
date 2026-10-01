-- MiquellaLight Effects
--
-- 1. Dual blades effects: red -> gold, blue -> silver at runtime. The recoloured effect
--    files are not enough: the game hands some effects their colours while it runs, as
--    extern parameters (Color on the attack trail 11_it02_001, ColorA/B/C on the archdemon
--    body glow and forearm flames 11_it02_002; found with the FX probe). Trails are emitted
--    piece by piece and each piece keeps the colour it was emitted with, so the colour has
--    to be right before the first piece: the parameter objects of dual blades effects are
--    noted when they are fetched (hook on getExternParameter) and the game's own set_Color
--    on them is changed on the way in (hook). In game those hooks never fired (v3: 0
--    intercepted), so all effects are also searched every frame, before rendering: a new
--    dual blades effect is recoloured the frame it is found ("when found") and re-checked
--    every frame while it plays ("later": the game setting red again).
-- 2. Hide the attack-up / defense-up glow: pl_state/11_pl_heal, which the game tints red
--    (attack up) or orange (defense up) and replays every ~2 s, setting the tint again each
--    time. Every instance of that effect is watched for its whole life and the two buff tints
--    are made transparent black before rendering; other tints (healing) are left alone.
--
-- 3. Great sword and light bowgun (2026-10-02): their effect files are recoloured in the
--    patch paks (warm -> gold; the great sword's body glow PLE_Body / PLE_IMP removed, the
--    user wants the charge shown on the blade only); here every one of their effects is also
--    tinted gold (the white parts take the tint), and the great sword's remaining charge
--    effects can be hidden altogether.
--
-- The effects of the weapon in hand are searched every frame; otherwise 4 times a second.
-- All can be switched off in the REFramework menu (Script Generated UI -> MiquellaLight
-- Effects); the choice is saved in reframework/data/MiquellaLight/Effects.json.
-- Untested in game; every call is wrapped in pcall.

local MOD = "MiquellaLight Effects"
local CONFIG_PATH = "MiquellaLight/Effects.json"
local EP = "via.effect.EffectPlayer"
local SCAN_FAST, SCAN_SLOW = 0, 0.25    -- every frame with dual blades (a new trail must be found
                                        -- before it is drawn), otherwise 4 times a second
-- Per weapon held: which effects are ours and what is done to them. "recolor": red -> gold,
-- blue -> silver on colour parameters and tint (dual blades); "gold": tint gold.
local RULES = {
    ["app.cHunterWp02Handling"] = { match = "it02", kind = "recolor", label = "dual blades" },
    ["app.cHunterWp00Handling"] = { match = "it00", kind = "gold", label = "great sword",
                                    charge = { "11_it00_00", "11_it00_01" } },    -- charge levels, true charge
    ["app.cHunterWp13Handling"] = { match = "it13", kind = "gold", label = "light bowgun",
                                    skip = { "jimen", "land" } },                 -- ground dust stays as is
    -- Insect glaive (user, 2026-10-02: the red charge glow should be gold): its smoke, poison
    -- and hit dust (010-012, 100) and the GPU modules (9xx) stay as they are. Searched 4 times
    -- a second, not every frame (slow): its charge glow lasts, and the flying kinsect brings
    -- many effects (the user saw memory climb with every-frame searches).
    -- Bow (user, 2026-10-02: the charge shows a red aura): only its charge effect (11_it11_030).
    ["app.cHunterWp11Handling"] = { match = "11_it11_030", kind = "gold", label = "bow", slow = true },
    ["app.cHunterWp10Handling"] = { match = "it10", kind = "gold", label = "insect glaive", slow = true,
                                    skip = { "11_it10_01", "11_it10_100", "11_it10_9" } },
}
local TINT_SAT = 0.6                    -- white parts of gold-tinted effects: a bright gold, not white
local COLOR_PARAMS = { "Color", "ColorA", "ColorB", "ColorC" }
local BUFF_MATCH = "11_pl_heal"
local BUFF_TINTS = { [0xFF3333] = "attack up", [0xFF8040] = "defense up" }   -- tint RGB as 0xRRGGBB
local GOLD_HUE, SILVER_HUE, SILVER_SAT, SILVER_VALUE = 38, 220, 0.08, 0.9   -- as recolor_efx.py

local config = { recolor = true, hideBuffs = true, hideGsCharge = false }
local saved = json.load_file(CONFIG_PATH)
if type(saved) == "table" then
    for k, v in pairs(saved) do config[k] = v end
end

local stats = { spawn = 0, found = 0, playing = 0, buffs = 0, intercepted = 0 }
local paramOwned = {}                   -- address of a dual blades colour parameter object -> true
local nParams = 0
local it02Cache = {}                    -- effect player address -> true when it belongs to the held weapon
local getCtx = nil                      -- effect player whose parameter is being fetched (hook pre -> post)
local tickedAt = -1
local CACHE_LIFE, cacheReset = 5, 0
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

-- Gold tint for an effect: white / warm -> gold (brightness and alpha kept); nil if unchanged.
local function gold_tint(rgba)
    local r, g, b, a = unpack_rgba(rgba)
    if a == 0 then return nil end
    local h, s, v = to_hsv(r / 255, g / 255, b / 255)
    if v < 0.05 or (s >= 0.3 and h > 70 and h < 320) then return nil end
    local nr, ng, nb = from_hsv(GOLD_HUE, s < 0.3 and TINT_SAT or s, v)
    local function byte(x) return math.floor(x * 255 + 0.5) end
    local new = byte(nr) | (byte(ng) << 8) | (byte(nb) << 16) | (a << 24)
    return new ~= rgba and new or nil
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

-- The rule for the weapon in hand (checked once a second), nil for other weapons.
local rule, ruleCheck = nil, -1
local function held_rule()
    if os.clock() < ruleCheck then return rule end
    ruleCheck = os.clock() + 1
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local h = chr and try(function() return chr:call("get_WeaponHandling") end)
    local name = h and try(function() return h:get_type_definition():get_full_name() end)
    local new = name and RULES[name] or nil
    if new ~= rule then it02Cache = {} end
    rule = new
    return rule
end

-- Whether an effect name belongs to the held weapon's rule.
local function ours(name, r)
    if not (r and name:find(r.match, 1, true)) then return false end
    for _, k in ipairs(r.skip or {}) do
        if name:find(k, 1, true) then return false end
    end
    return true
end

-- Cached per effect player (the game fetches parameters often); the cache is emptied every
-- few seconds in case an address is reused by another effect.
local function is_it02(key, ep)
    local known = it02Cache[key]
    if known ~= nil then return known end
    local name = ep and effect_name(ep) or ""
    local yes = ours(name, RULES["app.cHunterWp02Handling"])    -- parameter colours: dual blades only
    if yes or name ~= "" then it02Cache[key] = yes end      -- not set up yet: ask again next time
    return yes
end

-- The game fetches a dual blades effect's colour parameter: remember that parameter object.
local function on_get_param_pre(args)
    getCtx = nil
    if not config.recolor then return end
    local key = sdk.to_int64(args[2])
    if is_it02(key, sdk.to_managed_object(args[2])) then getCtx = key end
end

local function on_get_param_post(retval)
    if not getCtx then return end
    getCtx = nil
    local p = sdk.to_managed_object(retval)
    local name = p and try(function() return p:call("get_Name") end)
    if not (name == "Color" or name == "ColorA" or name == "ColorB" or name == "ColorC") then return end
    local key = sdk.to_int64(retval)
    if not paramOwned[key] then
        if nParams > 4000 then paramOwned, nParams = {}, 0 end
        paramOwned[key], nParams = true, nParams + 1
    end
end

-- The game sets a colour on one of those parameters: recolour it on the way in.
local function on_set_color_pre(args)
    if not (config.recolor and paramOwned[sdk.to_int64(args[2])]) then return end
    local v = sdk.to_int64(args[3])
    if v < 0 or v > 0xFFFFFFFF then return end           -- not a colour passed by value
    local new = recolor(v)
    if new then
        args[3] = sdk.to_ptr(new)
        stats.intercepted = stats.intercepted + 1
    end
end

local hooks = {
    { EP, "addExternParameter(via.effect.ExternParameter)", function(args) pcall(on_add_param, args) end },
    { EP, "getExternParameter(System.String)", function(args) pcall(on_get_param_pre, args) end,
      function(retval) pcall(on_get_param_post, retval); return retval end },
    { EP, "getExternParameters(System.UInt64)", function(args) pcall(on_get_param_pre, args) end,
      function(retval) pcall(on_get_param_post, retval); return retval end },
    { "via.effect.script.EffectCustomExternParameter", "set_Color(via.Color)",
      function(args) pcall(on_set_color_pre, args) end },
}
local nHooks = 0
for _, h in ipairs(hooks) do
    if pcall(function()
        sdk.hook(sdk.find_type_definition(h[1]):get_method(h[2]), h[3], h[4] or function(retval) return retval end)
    end) then nHooks = nHooks + 1 end
end
hookOk = nHooks == #hooks

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
            if config.recolor and ours(name, rule) then
                tracked[key] = { ep = ep, kind = "recolor", fresh = true, rule = rule, name = name }
            elseif config.hideBuffs and name:find(BUFF_MATCH, 1, true) then
                tracked[key] = { ep = ep, kind = "buff" }        -- watched for its whole life
            end
        end
    end
end

local TRANSPARENT = 0

-- Recolour an effect's colour parameters and tint; the number of colours changed.
local function hidden_charge(t)
    if not (config.hideGsCharge and t.rule and t.rule.charge) then return false end
    for _, k in ipairs(t.rule.charge) do
        if (t.name or ""):find(k, 1, true) then return true end
    end
    return false
end

local function recolor_effect(ep, tint, t)
    local n = 0
    if t and t.rule and t.rule.kind == "gold" then
        local new
        if hidden_charge(t) then
            new = tint ~= TRANSPARENT and TRANSPARENT or nil
        else
            new = gold_tint(tint)
        end
        if new and pcall(function() ep:call("set_Color(via.Color)", make_color(new)) end) then n = n + 1 end
        return n
    end
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
        local n = recolor_effect(ep, tint, t)
        if t.fresh then
            stats.found, t.fresh = stats.found + n, nil
        else
            stats.playing = stats.playing + n
        end
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
        end                                                    -- other tints (healing): left alone
    end
end

-- New effects from the hook: dual blades ones are recoloured right away and tracked.
local function take_pending()
    local still = {}
    for _, item in ipairs(pending) do
        local ep = item.ep
        local key = try(function() return ep:get_address() end)
        local name = key and effect_name(ep) or ""
        if ours(name, rule) then
            if not tracked[key] then
                tracked[key] = { ep = ep, kind = "recolor", rule = rule, name = name }
                local tint = rgba_of(try(function() return ep:call("get_Color") end))
                if tint then stats.spawn = stats.spawn + recolor_effect(ep, tint, tracked[key]) end
            end
        elseif key and name == "" and item.frames < PENDING_FRAMES then
            item.frames = item.frames + 1
            still[#still + 1] = item                     -- not set up yet: look again next frame
        end
    end
    pending = still
end

local cost = { total = 0, frames = 0, shown = 0 }   -- time spent per frame, averaged over a second

local function tick()
    if not (config.recolor or config.hideBuffs) then return end
    local t0 = os.clock()
    if config.recolor then held_rule() end          -- once a second; new effects need it
    if #pending > 0 then pcall(take_pending) end
    if os.clock() >= nextScan then
        local held = config.recolor and held_rule()
        nextScan = os.clock() + ((held and not held.slow) and SCAN_FAST or SCAN_SLOW)
        pcall(scan)
    end
    if os.clock() >= cacheReset then
        cacheReset = os.clock() + CACHE_LIFE
        it02Cache = {}
    end
    for key, t in pairs(tracked) do
        pcall(update, key, t)
    end
    cost.total, cost.frames = cost.total + (os.clock() - t0), cost.frames + 1
    if cost.frames >= 60 then
        cost.shown, cost.total, cost.frames = cost.total / cost.frames * 1000, 0, 0
    end
end

-- Before rendering, after the game's own update set this frame's colours. If that entry
-- point does not exist, fall back to once per frame.
local entryOk = pcall(function()
    re.on_pre_application_entry("BeginRendering", function()
        tickedAt = os.clock()
        tick()
    end)
end)
re.on_frame(function()
    if not entryOk or os.clock() - tickedAt > 0.1 then tick() end
end)

re.on_draw_ui(function()
    if not imgui.tree_node(MOD) then return end
    local changed
    changed, config.recolor = imgui.checkbox("Weapon effects to gold (dual blades, great sword, light bowgun)",
                                             config.recolor)
    if changed then json.dump_file(CONFIG_PATH, config) end
    changed, config.hideGsCharge = imgui.checkbox("Great sword: hide the game's charge effects (blade glow only)",
                                                  config.hideGsCharge)
    if changed then json.dump_file(CONFIG_PATH, config) end
    changed, config.hideBuffs = imgui.checkbox("Hide attack-up / defense-up glow", config.hideBuffs)
    if changed then json.dump_file(CONFIG_PATH, config) end
    local n = 0
    for _ in pairs(tracked) do n = n + 1 end
    imgui.text(string.format("Recoloured: %d intercepted, %d at spawn, %d when found, %d later. Buff glows hidden: %d.",
        stats.intercepted, stats.spawn, stats.found, stats.playing, stats.buffs))
    imgui.text(string.format("Tracking %d effects, %d colour parameters. Hooks %d/%d. %s", n, nParams, nHooks, #hooks,
        (entryOk and os.clock() - tickedAt < 0.5) and "Before rendering." or "Once per frame."))
    imgui.text(string.format("Cost: %.2f ms per frame (%s).", cost.shown,
        rule and (rule.label .. ": searching every frame") or "searching 4 times a second"))
    imgui.tree_pop()
end)
