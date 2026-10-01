-- Offline test for MiquellaLight_FxProbe.lua with a mocked REFramework API.
-- Run: lua5.4 fxprobe_test.lua ../MiquellaLight_FxProbe/reframework/autorun/MiquellaLight_FxProbe.lua
--  or: python run_lua.py fxprobe_test.lua ../MiquellaLight_FxProbe/reframework/autorun/MiquellaLight_FxProbe.lua

local function tname(n) return { get_full_name = function() return n end } end
local function method(name, params, ret)
    local ps = {}
    for i, p in ipairs(params) do ps[i] = tname(p) end
    return { get_name = function() return name end, get_param_types = function() return ps end,
             get_return_type = function() return tname(ret or "System.Void") end }
end
local componentTd = { get_full_name = function() return "via.Component" end, get_methods = function() return { method("get_GameObject", {}) } end }
local epTd = {
    get_full_name = function() return "via.effect.EffectPlayer" end,
    get_parent_type = function() return componentTd end,
    get_methods = function() return {
        method("get_Resource", {}, "via.effect.EffectResourceHolder"),
        method("setExternParameterColor", { "System.String", "via.Color" }),
        method("setExternParameterFloat", { "System.String", "System.Single" }),
        method("getExternParameter", { "System.String" }, "via.effect.ExternParameter"),
        method("set_Color", { "via.Color" }),
        method("play", {}),
    } end,
}

-- Effect players in the scene.
-- An extern parameter object: name and colour fields (via.Color has a packed rgba field).
local function externParam(name, rgba)
    local fields = {
        { get_name = function() return "_Name" end, is_static = function() return false end, get_data = function() return name end,
          get_type = function() return tname("System.String") end },
        { get_name = function() return "_Color" end, is_static = function() return false end,
          get_data = function() return { get_field = function(_, f) if f == "rgba" then return rgba end end } end,
          get_type = function() return tname("via.Color") end },
    }
    local td = { get_full_name = function() return "via.effect.script.EffectCustomExternParameter" end,
                 get_fields = function() return fields end, get_methods = function() return { method("set_Color", { "via.Color" }) } end }
    return { get_type_definition = function() return td end }
end
local function effect(path, goName, values, addr)
    local e = { path = path, running = true, tint = 0xFFFFFFFF }
    e.get_address = function() return addr or 0 end
    e.call = function(self, m, arg)
        if m == "get_Resource" then return { ToString = function() return "Resource[" .. path .. "]" end } end
        if m == "get_GameObject" then return { call = function() return goName end } end
        if m == "get_Running" then return e.running end
        if m == "get_Color" then return { get_field = function(_, f) if f == "rgba" then return e.tint end end } end
        if m == "getExternParameter(System.String)" and values and values[arg] then return externParam(arg, values[arg]) end
    end
    return e
end
local trail = effect("Art/VFX/EffectEditor/Weapon/it02/11_it02_001.efx", "Wp02Effect", { Color = 0xFF2E7AE6 }, 0xA0)
local swordtrail = effect("Art/VFX/EffectEditor/Player/pl_cm/pl_etc/11_pl_swordtrail_000.efx", "trail", nil, 0xB0)
local flames = effect("Art/VFX/EffectEditor/Weapon/it02/11_it02_002.efx", "Wp02Effect", {})
local grass = effect("Art/VFX/EffectEditor/Stage/st101/grass.efx", "Env")
local playing = { trail, grass, swordtrail }

local hooks = {}
local pointers, nextPtr = {}, 0x1000
local function ptr(obj)
    for p, o in pairs(pointers) do if o == obj then return p end end
    nextPtr = nextPtr + 0x10; pointers[nextPtr] = obj; return nextPtr
end
local flag = { name = "_IsKijinOn", value = false }
local handling = { get_type_definition = function() return {
    get_fields = function() return {
        { get_name = function() return flag.name end, is_static = function() return false end, get_data = function() return flag.value end },
        { get_name = function() return "_KijinExtern" end, is_static = function() return false end, get_data = function() return 0.5 end },
    } end } end }
local master = { get_Character = function() return { call = function(self, m) if m == "get_WeaponHandling" then return handling end end } end }

sdk = {
    typeof = function(n) return { name = n } end,
    find_type_definition = function(n) if n == "via.effect.EffectPlayer" then return epTd end return tname(n) end,
    hook = function(m, pre, post) hooks[m:get_name()] = pre end,
    get_native_singleton = function() return {} end,
    call_native_func = function() return { call = function(self, m, t)
        if m == "findComponents(System.Type)" and t.name == "via.effect.EffectPlayer" then
            return { get_elements = function() return playing end }
        end
    end } end,
    get_managed_singleton = function() return { getMasterPlayer = function() return master end } end,
    to_int64 = function(v) return type(v) == "table" and ptr(v) or v end,
    to_float = function(v) return v end,
    to_managed_object = function(p) if type(p) == "table" then return p.obj or p end return pointers[p] end,
}
local onDraw, onFrame
re = { on_draw_ui = function(f) onDraw = f end, on_frame = function(f) onFrame = f end }
local press, out = {}, {}
imgui = { tree_node = function(l) return true end, tree_pop = function() end,
          button = function(l) return press[l] end, text = function(t) out[#out + 1] = t end }
local dumped
json = { dump_file = function(p, t) dumped = { p, t } end }
local clock = 0
os.clock = function() return clock end

dofile(arg[1])
local function check(c, m) print((c and "PASS " or "FAIL ") .. m); if not c then os.exit(1) end end
local function click(label) press[label] = true; out = {}; onDraw(); press[label] = nil; return table.concat(out, "\n") end

local s = click("Start recording")
check(s:match("6 methods, 3 setters hooked, 1 weapon flags"), "methods listed, extern setters and set_Color hooked, flag found")
check(hooks.setExternParameterColor and hooks.setExternParameterFloat and hooks.set_Color and not hooks.getExternParameter, "only setters hooked")

onFrame()                                         -- first scan: trail + grass playing
clock = 1.0
local str = { obj = { call = function(self, m) return "ColorA" end } }
hooks.setExternParameterColor({ 0, ptr(flames), str, 0xFF2244FF })      -- red, game sets ColorA
hooks.setExternParameterColor({ 0, ptr(flames), str, 0xFF2244FF })
hooks.setExternParameterFloat({ 0, ptr(flames), { obj = { call = function() return "IsKijin" end } }, 1.0 })
hooks.set_Color({ 0, ptr(swordtrail), 0xFF1020E0 })
swordtrail.tint = 0xFF1020E0
playing = { flames, swordtrail }; flag.value = true
clock = 1.5; onFrame()
clock = 2.0
s = click("Stop and save")
check(s:match("Saved 4 effect files"), "saved")
local r = dumped[2]
check(dumped[1] == "MiquellaLight/fx.json", "report path")
local params = table.concat(r.params, "\n")
check(params:match('setExternParameterColor%("ColorA", #FF4422FF%)  on  Art/VFX/EffectEditor/Weapon/it02/11_it02_002.efx   x2'),
      "colour call decoded (RGBA byte order) with effect file and count")
check(params:match('setExternParameterFloat%("IsKijin", 1.000%)'), "float call decoded")
local tl = table.concat(r.timeline, "\n")
check(tl:match("start Art/VFX/EffectEditor/Weapon/it02/11_it02_001.efx") and not tl:match("start Art/VFX/EffectEditor/Stage"),
      "timeline shows focused effects only")
check(tl:match("stop  Art/VFX/EffectEditor/Weapon/it02/11_it02_001.efx"), "effect stop logged")
check(tl:match("_IsKijinOn: false %-> true"), "weapon flag change logged")
check(tl:match("value Art/VFX/EffectEditor/Weapon/it02/11_it02_001.efx @A0 getExternParameter Color = _Name=Color _Color=#E67A2EFF"),
      "parameter object's fields read back, colour as #RRGGBBAA")
check(r.extern and r.extern.type == "via.effect.script.EffectCustomExternParameter" and #r.extern.fields == 2
      and r.extern.methods[1]:match("set_Color"), "parameter object's type described")
check(tl:match("state Art/VFX/EffectEditor/Player/pl_cm/pl_etc/11_pl_swordtrail_000.efx @B0 running=true tint=#FFFFFFFF")
      and tl:match("11_pl_swordtrail_000.efx @B0 running=true tint=#E02010FF"), "watched effect's tint change logged")
check(params:match("set_Color%(#E02010FF%)  on  Art/VFX/EffectEditor/Player/pl_cm/pl_etc/11_pl_swordtrail_000.efx"), "set_Color call recorded")
local effects = table.concat(r.effects, "\n")
check(effects:match("grass.efx") and effects:match("(Wp02Effect)"), "all effects listed with their object")
check(#r.methods == 6 and r.hooked[1]:match("setExternParameterColor%(System.String, via.Color%)"), "method signatures saved")
-- Stopped: hooks no longer record.
hooks.setExternParameterColor({ 0, ptr(flames), str, 0xFF0000FF })
s = click("Start recording")
check(s:match("Recording"), "second recording starts without hooking again")
print("ALL PASS")
