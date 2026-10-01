-- MiquellaLight FX Probe (read-only)
--
-- Finds out which effect files (.efx) play while you fight and which effect parameters the
-- game sets on them at runtime (colours such as ColorA / Color, values such as IsKijin).
-- Some dual blades effects stayed red after their files were recoloured red -> gold, so the
-- game must be handing them colours while it runs; this shows which ones and when.
--
-- "Start recording", do the actions, "Stop and save" -> reframework/data/MiquellaLight/fx.json:
--   methods   the effect player's methods and parameter types (what can be hooked / read)
--   hooked    the parameter setters that were hooked
--   effects   every effect file seen playing, with first / last time (seconds) and scan count
--   params    every distinct parameter call: method, effect file, arguments, count
--   values    the dual blades effects' parameter values read back (when a getter exists)
--   timeline  effect files starting / stopping, weapon true-false flags changing, first calls
--
-- Nothing in the game is changed (the hooks only record). Untested in game; every call is
-- wrapped in pcall.

local MOD = "MiquellaLight FX Probe"
local OUT = "MiquellaLight/fx.json"
local EP = "via.effect.EffectPlayer"
local POLL = 0.25                 -- seconds between scans of the playing effects
local MAX_TIMELINE = 800
local MAX_PARAMS = 500
local MAX_EFFECTS = 500
local FOCUS = { "it02", "player/", "Player" }   -- effect paths shown on the timeline
local VALUE_FOCUS = "it02"                      -- effects whose parameters are read back
local PARAM_NAMES = { "Color", "ColorA", "ColorB", "ColorC", "IsKijin", "IsBuff" }
local HANDLING_METHODS = { "get_WeaponHandling", "get_WpHandling", "get_WeaponHandle" }

local rec = nil
local status = ""
local methods = nil               -- { {name, sig, params, ret, def} }
local resGetters = nil            -- getter names that may return the effect resource
local valueGetters = nil          -- getters taking one string (parameter name)
local hooked = nil                -- names of the hooked setters
local pathCache = {}

local function try(fn, ...)
    local ok, result = pcall(fn, ...)
    if ok then return result end
    return nil
end

local function resource_path(res)
    local s = res and try(function() return res:ToString() end)
    if not s or not s:match("^Resource%[") then return nil end
    return (s:gsub("^Resource%[", ""):gsub("%]$", ""))
end

local function elapsed() return os.clock() - rec.t0 end

local function log(text)
    if rec and #rec.timeline < MAX_TIMELINE then
        rec.timeline[#rec.timeline + 1] = string.format("%.2fs %s", elapsed(), text)
    end
end

local function focused(path)
    for _, f in ipairs(FOCUS) do
        if path:find(f, 1, true) then return true end
    end
    return false
end

-- ------------------------------------------------------------------ effect player methods

local function describe_methods()
    local list = {}
    local td = sdk.find_type_definition(EP)
    while td do
        local owner = try(function() return td:get_full_name() end) or "?"
        if owner == "via.Component" or owner:match("^System%.") then break end
        for _, m in ipairs(try(function() return td:get_methods() end) or {}) do
            local params = {}
            for _, p in ipairs(try(function() return m:get_param_types() end) or {}) do
                params[#params + 1] = try(function() return p:get_full_name() end) or "?"
            end
            local name = try(function() return m:get_name() end) or "?"
            list[#list + 1] = {
                name = name, owner = owner, params = params, def = m,
                sig = name .. "(" .. table.concat(params, ", ") .. ")",
                ret = try(function() return m:get_return_type():get_full_name() end) or "?",
            }
        end
        td = try(function() return td:get_parent_type() end)
    end
    return list
end

local function effect_path(ep)
    for _, g in ipairs(resGetters) do
        local p = resource_path(try(function() return ep:call(g) end))
        if p then return p end
    end
    return nil
end

-- ------------------------------------------------------------------ hooks on parameter setters

local function arg_text(ptype, raw)
    if ptype == "System.String" then
        local s = try(function() return sdk.to_managed_object(raw):call("ToString()") end)
        return s and ('"' .. s .. '"') or "string?"
    elseif ptype == "System.Single" then
        return string.format("%.3f", sdk.to_float(raw))
    elseif ptype == "System.Boolean" then
        return tostring((sdk.to_int64(raw) & 0xFF) ~= 0)
    elseif ptype == "via.Color" then
        local v = sdk.to_int64(raw)
        if v < 0 or v > 0xFFFFFFFF then return string.format("color@0x%X", v) end
        return string.format("#%02X%02X%02X%02X", v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF, (v >> 24) & 0xFF)
    end
    return string.format("0x%X", sdk.to_int64(raw))
end

local function record_call(m, args)
    local key = sdk.to_int64(args[2])
    local path = pathCache[key]
    if path == nil then
        path = effect_path(sdk.to_managed_object(args[2])) or "?"
        pathCache[key] = path
    end
    local parts = {}
    for i, p in ipairs(m.params) do
        parts[#parts + 1] = try(arg_text, p, args[i + 2]) or "?"
    end
    local text = m.name .. "(" .. table.concat(parts, ", ") .. ")  on  " .. path
    local entry = rec.params[text]
    if entry then
        entry.count = entry.count + 1
        entry.last = elapsed()
    elseif rec.nparams < MAX_PARAMS then
        rec.params[text] = { count = 1, first = elapsed(), last = elapsed() }
        rec.nparams = rec.nparams + 1
        log("call " .. text)
    end
end

local function install_hooks()
    hooked = {}
    for _, m in ipairs(methods) do
        if m.name:find("xtern") and not m.name:match("^get") then
            local ok = pcall(sdk.hook, m.def, function(args)
                if rec then pcall(record_call, m, args) end
            end, function(retval) return retval end)
            if ok then hooked[#hooked + 1] = m.sig end
        end
    end
end

-- ------------------------------------------------------------------ scanning playing effects

local function current_scene()
    return try(function()
        return sdk.call_native_func(sdk.get_native_singleton("via.SceneManager"),
            sdk.find_type_definition("via.SceneManager"), "get_CurrentScene()")
    end)
end

local function read_values(ep, path)
    for _, g in ipairs(valueGetters) do
        for _, name in ipairs(PARAM_NAMES) do
            local v = try(function() return ep:call(g.sig, name) end)
            if v ~= nil then
                local text = type(v) == "userdata" and (try(function() return v:ToString() end) or tostring(v)) or tostring(v)
                local key = path .. " " .. g.name .. " " .. name
                if rec.values[key] ~= text then
                    rec.values[key] = text
                    log("value " .. key .. " = " .. text)
                end
            end
        end
    end
end

local function scan_effects()
    local scene = current_scene()
    local arr = scene and try(function() return scene:call("findComponents(System.Type)", sdk.typeof(EP)) end)
    local now, playing = elapsed(), {}
    for _, ep in ipairs(arr and try(function() return arr:get_elements() end) or {}) do
        local path = effect_path(ep)
        if path then
            playing[path] = true
            local e = rec.effects[path]
            if not e and rec.neffects < MAX_EFFECTS then
                local go = try(function() return ep:call("get_GameObject") end)
                e = { first = now, scans = 0, object = go and try(function() return go:call("get_Name") end) or "?" }
                rec.effects[path] = e
                rec.neffects = rec.neffects + 1
            end
            if e then
                e.scans, e.last = e.scans + 1, now
            end
            if path:find(VALUE_FOCUS, 1, true) and #valueGetters > 0 then read_values(ep, path) end
        end
    end
    for path in pairs(playing) do
        if not rec.playing[path] and focused(path) then log("start " .. path) end
    end
    for path in pairs(rec.playing) do
        if not playing[path] and focused(path) then log("stop  " .. path) end
    end
    rec.playing = playing
end

-- ------------------------------------------------------------------ weapon flags

local function find_handling()
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local character = master and try(function() return master:get_Character() end)
    if not character then return nil end
    for _, m in ipairs(HANDLING_METHODS) do
        local h = try(function() return character:call(m) end)
        if h then return h end
    end
    return nil
end

local function flag_fields(obj)
    local list = {}
    local td = try(function() return obj:get_type_definition() end)
    while td do
        for _, f in ipairs(try(function() return td:get_fields() end) or {}) do
            if not try(function() return f:is_static() end) then
                local v = try(function() return f:get_data(obj) end)
                if type(v) == "boolean" then
                    list[#list + 1] = { field = f, name = f:get_name(), last = v }
                end
            end
        end
        td = try(function() return td:get_parent_type() end)
    end
    return list
end

local function update_flags()
    for _, w in ipairs(rec.flags) do
        local v = try(function() return w.field:get_data(rec.handling) end)
        if v ~= nil and v ~= w.last then
            log(w.name .. ": " .. tostring(w.last) .. " -> " .. tostring(v))
            w.last = v
        end
    end
end

-- ------------------------------------------------------------------ start / stop

local function start()
    if not methods then
        methods = describe_methods()
        resGetters, valueGetters = {}, {}
        for _, m in ipairs(methods) do
            if m.name:match("^get_.*Resource") and #m.params == 0 then
                table.insert(resGetters, m.name == "get_Resource" and 1 or #resGetters + 1, m.name)
            elseif m.name:match("^get.*xtern") and #m.params == 1 and m.params[1] == "System.String" then
                valueGetters[#valueGetters + 1] = m
            end
        end
        if #resGetters == 0 then resGetters = { "get_Resource" } end
    end
    if #methods == 0 then return EP .. " not found." end
    if not hooked then install_hooks() end
    local handling = find_handling()
    rec = { t0 = os.clock(), next = 0, effects = {}, neffects = 0, params = {}, nparams = 0, values = {},
            playing = {}, timeline = {}, handling = handling, flags = handling and flag_fields(handling) or {} }
    return string.format("Recording. %d methods, %d setters hooked, %d weapon flags. Do the actions now.",
        #methods, #hooked, #rec.flags)
end

local function report()
    local ms = {}
    for _, m in ipairs(methods) do ms[#ms + 1] = m.owner .. "  " .. m.ret .. " " .. m.sig end
    local effects = {}
    for path, e in pairs(rec.effects) do
        effects[#effects + 1] = string.format("%-90s %7.2f .. %7.2f  x%d  (%s)", path, e.first, e.last, e.scans, e.object)
    end
    table.sort(effects)
    local params = {}
    for text, p in pairs(rec.params) do
        params[#params + 1] = string.format("%s   x%d  %.2f .. %.2f", text, p.count, p.first, p.last)
    end
    table.sort(params)
    return { methods = ms, hooked = hooked, resource_getters = resGetters, effects = effects, params = params,
             values = rec.values, timeline = rec.timeline, seconds = elapsed() }
end

local function stop_and_save()
    json.dump_file(OUT, report())
    local n = rec.neffects
    rec = nil
    return "Saved " .. n .. " effect files to reframework/data/" .. OUT
end

re.on_frame(function()
    if not rec then return end
    pcall(update_flags)
    if os.clock() >= rec.next then
        rec.next = os.clock() + POLL
        pcall(scan_effects)
    end
end)

re.on_draw_ui(function()
    if not imgui.tree_node(MOD) then return end
    if imgui.button(rec and "Stop and save" or "Start recording") then
        status = rec and stop_and_save() or start()
    end
    imgui.text(status)
    if rec then
        imgui.text(string.format("%.0f s: %d effect files, %d distinct parameter calls, %d timeline lines",
            elapsed(), rec.neffects, rec.nparams, #rec.timeline))
    end
    imgui.tree_pop()
end)
