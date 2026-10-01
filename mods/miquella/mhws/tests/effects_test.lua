-- Offline test for MiquellaLight_Effects.lua with a mocked REFramework API.
-- Run: python run_lua.py effects_test.lua ../MiquellaLight_Effects/reframework/autorun/MiquellaLight_Effects.lua

local function color(rgba)
    local c = { rgba = rgba }
    function c:get_field(n) if n == "rgba" then return self.rgba end end
    function c:set_field(n, v) if n == "rgba" then self.rgba = v end end
    return c
end
local function hex(r, g, b, a) return r | (g << 8) | (b << 16) | ((a or 0xFF) << 24) end

local function param(name, rgba)
    local p = { name = name, c = color(rgba) }
    function p:call(m, v)
        if m == "get_Name" then return self.name end
        if m == "get_Color" then return color(self.c.rgba) end
        if m == "set_Color(via.Color)" then self.c = color(v.rgba) end
    end
    return p
end

local nextAddr = 0x100
local function effect(goName, path, tint, params)
    nextAddr = nextAddr + 0x10
    local e = { addr = nextAddr, tint = color(tint), params = params or {}, alive = true }
    function e:get_address() return self.addr end
    function e:call(m, v)
        if not self.alive then error("destroyed") end
        if m == "get_GameObject" then return { call = function() return goName end } end
        if m == "get_Resource" then return { ToString = function() return "Resource[" .. path .. "]" end } end
        if m == "get_Color" then return color(self.tint.rgba) end
        if m == "set_Color(via.Color)" then self.tint = color(v.rgba) end
        if m == "getExternParameter(System.String)" then return self.params[v] end
    end
    return e
end

local RED, ORANGE, BLUE, GREEN = hex(0xFF, 0x33, 0x33), hex(0xFF, 0x80, 0x40), hex(0x40, 0x60, 0xFF), hex(0x40, 0xFF, 0x60)
local glow = effect("11_it02_002", "Art/VFX/EffectEditor/Weapon/it02/11_it02_002.efx", hex(0xFF, 0xFF, 0xFF),
    { ColorA = param("ColorA", hex(0xFF, 0x22, 0x22)), ColorB = param("ColorB", BLUE), ColorC = param("ColorC", hex(0xFF, 0x99, 0x99)) })
local attackUp = effect("11_pl_heal", "Art/VFX/EffectEditor/Player/pl_cm/pl_state/11_pl_heal.efx", RED)
local defenseUp = effect("11_pl_heal", "Art/VFX/EffectEditor/Player/pl_cm/pl_state/11_pl_heal.efx", ORANGE)
local heal = effect("11_pl_heal", "Art/VFX/EffectEditor/Player/pl_cm/pl_state/11_pl_heal.efx", GREEN)
local monster = effect("ef_fire", "Art/VFX/EffectEditor/Enemy/em0001/fire.efx", RED,
    { Color = param("Color", hex(0xFF, 0x20, 0x20)) })
local playing = { glow, attackUp, defenseUp, heal, monster }

local addHook
local pointers = {}
local function ptr(o) pointers[#pointers + 1] = o; return #pointers end
sdk = {
    find_type_definition = function(n)
        return { get_method = function(_, sig) return sig end }
    end,
    hook = function(m, pre, post) if m == "addExternParameter(via.effect.ExternParameter)" then addHook = pre end end,
    to_managed_object = function(p) return pointers[p] end,
    typeof = function(n) return n end,
    get_native_singleton = function() return {} end,
    call_native_func = function() return { call = function(_, m, t)
        if m == "findComponents(System.Type)" and t == "via.effect.EffectPlayer" then
            return { get_elements = function() return playing end }
        end
    end } end,
}
ValueType = { new = function() return color(0) end }
local onFrame, onDraw
re = { on_frame = function(f) onFrame = f end, on_draw_ui = function(f) onDraw = f end }
local out, toggle = {}, {}
imgui = { tree_node = function() return true end, tree_pop = function() end, text = function(t) out[#out + 1] = t end,
          checkbox = function(l, v) if toggle[l] then toggle[l] = nil; return true, not v end return false, v end }
local savedCfg
json = { load_file = function() return nil end, dump_file = function(p, t) savedCfg = { p, t } end }
local clock = 0
os.clock = function() return clock end

dofile(arg[1])
local function check(c, m) print((c and "PASS " or "FAIL ") .. m); if not c then os.exit(1) end end
local function rgb(c) return string.format("%02X%02X%02X", c.rgba & 0xFF, (c.rgba >> 8) & 0xFF, (c.rgba >> 16) & 0xFF) end
local function hue_is_gold(c)
    local r, g, b = c.rgba & 0xFF, (c.rgba >> 8) & 0xFF, (c.rgba >> 16) & 0xFF
    return r > g and g > b and g > r * 0.5
end

check(addHook ~= nil, "spawn hook installed")
-- A new trail: the game fills its shared parameter object with red and adds it.
local trail = effect("11_it02_001", "", hex(0xFF, 0xFF, 0xFF))
local shared = param("Color", hex(0xFF, 0x2E, 0x2E, 0xC0))
addHook({ 0, ptr(trail), ptr(shared) })
check(hue_is_gold(shared.c) and (shared.c.rgba >> 24) == 0xC0, "trail colour turned gold at spawn, alpha kept (" .. rgb(shared.c) .. ")")
local monsterParam = param("Color", hex(0xFF, 0x20, 0x20))
addHook({ 0, ptr(monster), ptr(monsterParam) })
check(rgb(monsterParam.c) == "FF2020", "other effects' parameters untouched at spawn")
local flag = param("IsKijin", hex(0xFF, 0x00, 0x00))
addHook({ 0, ptr(trail), ptr(flag) })
check(rgb(flag.c) == "FF0000", "non-colour parameter names untouched")

onFrame()
check(hue_is_gold(glow.params.ColorA.c) and hue_is_gold(glow.params.ColorC.c), "playing archdemon glow: ColorA / ColorC gold")
local b = glow.params.ColorB.c
local br, bg, bb = b.rgba & 0xFF, (b.rgba >> 8) & 0xFF, (b.rgba >> 16) & 0xFF
check(math.max(br, bg, bb) - math.min(br, bg, bb) < 40, "blue-state ColorB turned silver (" .. rgb(b) .. ")")
check(attackUp.tint.rgba == 0 and defenseUp.tint.rgba == 0, "attack-up and defense-up glows hidden")
check(heal.tint.rgba == GREEN, "healing glow left alone")
check(monster.tint.rgba == RED and rgb(monster.params.Color.c) == "FF2020", "monster effects untouched")
-- The game sets red again on the playing effect: put back next frame.
glow.params.ColorA.c = color(hex(0xFF, 0x22, 0x22))
attackUp.tint = color(RED)
onFrame()
check(hue_is_gold(glow.params.ColorA.c) and attackUp.tint.rgba == 0, "runtime red undone every frame")
-- The buff effect is reused for healing: no longer hidden.
attackUp.tint = color(GREEN)
onFrame(); onFrame()
check(attackUp.tint.rgba == GREEN, "a hidden effect reused for healing shows again")
-- Destroyed effects are dropped without errors.
glow.alive = false
onFrame()
out = {}; onDraw()
check(table.concat(out):match("Tracking 1%."), "destroyed effect dropped (only the hidden defense-up glow tracked)")
-- Switch the buff hiding off.
toggle["Hide attack-up / defense-up glow"] = true; onDraw()
check(savedCfg and savedCfg[2].hideBuffs == false, "setting saved")
defenseUp.tint = color(ORANGE)
onFrame(); clock = 1; onFrame()
check(defenseUp.tint.rgba == ORANGE, "with hiding off the glow stays")
print("ALL PASS")
