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
    local e = { addr = nextAddr, tint = color(tint), params = params or {}, alive = true, running = true,
                goName = goName, path = path }
    function e:get_address() return self.addr end
    function e:call(m, v)
        if not self.alive then error("destroyed") end
        if m == "get_GameObject" then return self.goName and { call = function() return self.goName end } end
        if m == "get_Resource" then return self.path ~= "" and { ToString = function() return "Resource[" .. self.path .. "]" end } or nil end
        if m == "get_Running" then return self.running end
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
local hooked = {}
local pointers = {}
local function ptr(o)
    for i, x in ipairs(pointers) do if x == o then return i end end
    pointers[#pointers + 1] = o; return #pointers
end
sdk = {
    find_type_definition = function(n)
        return { get_method = function(_, sig) return n .. "::" .. sig end }
    end,
    hook = function(m, pre, post)
        hooked[m] = { pre = pre, post = post }
        if m == "via.effect.EffectPlayer::addExternParameter(via.effect.ExternParameter)" then addHook = pre end
    end,
    to_managed_object = function(p) return pointers[p] end,
    to_int64 = function(v) return v end,
    get_managed_singleton = function(n)
        return { getMasterPlayer = function() return { get_Character = function() return { call = function(_, m)
            if m == "get_WeaponHandling" then
                return { get_type_definition = function() return { get_full_name = function() return heldType end } end }
            end
            if m == "get_BaseActionController" then
                return { call = function(_, cm)
                    if cm == "get_CurrentAction" then
                        return { get_type_definition = function() return { get_full_name = function() return hunterAction end } end }
                    end
                end }
            end
        end } end } end }
    end,
    to_ptr = function(v) return v end,
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
local beforeRender
re = { on_frame = function(f) onFrame = f end, on_draw_ui = function(f) onDraw = f end,
       on_pre_application_entry = function(name, f) if name == "BeginRendering" then beforeRender = f end end }
local out, toggle = {}, {}
imgui = { tree_node = function() return true end, tree_pop = function() end, text = function(t) out[#out + 1] = t end,
          checkbox = function(l, v) if toggle[l] then toggle[l] = nil; return true, not v end return false, v end }
local savedCfg
json = { load_file = function() return nil end, dump_file = function(p, t) savedCfg = { p, t } end }
local clock = 0
os.clock = function() return clock end
heldType = "app.cHunterWp02Handling"
hunterAction = "app.Wp02Action.cIdle"

dofile(arg[1])
local function check(c, m) print((c and "PASS " or "FAIL ") .. m); if not c then os.exit(1) end end
local function rgb(c) return string.format("%02X%02X%02X", c.rgba & 0xFF, (c.rgba >> 8) & 0xFF, (c.rgba >> 16) & 0xFF) end
local function hue_is_gold(c)
    local r, g, b = c.rgba & 0xFF, (c.rgba >> 8) & 0xFF, (c.rgba >> 16) & 0xFF
    return r > g and g > b and g > r * 0.5
end

check(addHook ~= nil, "spawn hook installed")
check(hooked["via.effect.script.EffectCustomExternParameter::set_Color(via.Color)"]
      and hooked["via.effect.EffectPlayer::getExternParameter(System.String)"].post, "parameter hooks installed")
-- The game fetches a new trail's Color parameter and sets it red: changed on the way in.
local newTrail = effect("11_it02_001", "", hex(0xFF, 0xFF, 0xFF), { Color = param("Color", hex(0xFF, 0xFF, 0xFF)) })
local get = hooked["via.effect.EffectPlayer::getExternParameter(System.String)"]
local setColor = hooked["via.effect.script.EffectCustomExternParameter::set_Color(via.Color)"]
local function game_sets(ep, name, rgba)
    get.pre({ 0, ptr(ep), name })
    local p = ep.params[name]
    get.post(ptr(p))
    local args = { 0, ptr(p), rgba }
    setColor.pre(args)
    p.c = color(args[3])
    return p.c
end
local c0 = game_sets(newTrail, "Color", hex(0xFF, 0x2E, 0x2E, 0xC0))
check(hue_is_gold(c0) and (c0.rgba >> 24) == 0xC0, "game's red set on a trail parameter arrives gold (" .. rgb(c0) .. ")")
local c1 = game_sets(monster, "Color", hex(0xFF, 0x20, 0x20))
check(rgb(c1) == "FF2020", "other effects' colour sets pass through")
-- New effects: the game adds their parameters (hook) and gives the trail a red Color.
local trail = effect("11_it02_001", "", hex(0xFF, 0xFF, 0xFF), { Color = param("Color", hex(0xFF, 0x2E, 0x2E, 0xC0)) })
local late = effect(nil, "", hex(0xFF, 0xFF, 0xFF), { Color = param("Color", hex(0xFF, 0x2E, 0x2E)) })   -- named a frame later
local spark = effect("ef_spark", "", RED, { Color = param("Color", hex(0xFF, 0x20, 0x20)) })
addHook({ 0, ptr(trail), ptr({}) })
addHook({ 0, ptr(late), ptr({}) })
addHook({ 0, ptr(spark), ptr({}) })
clock = 0.1; onFrame()
local c = trail.params.Color.c
check(hue_is_gold(c) and (c.rgba >> 24) == 0xC0, "new trail gold on the next frame, alpha kept (" .. rgb(c) .. ")")
check(rgb(spark.params.Color.c) == "FF2020" and spark.tint.rgba == RED, "other new effects untouched")
check(rgb(late.params.Color.c) == "FF2E2E", "effect not set up yet: waits")
late.goName = "11_it02_001"
onFrame()
check(hue_is_gold(late.params.Color.c), "picked up once it has its name")
out = {}; onDraw()
check(table.concat(out):match("1 intercepted, 2 at spawn"), "intercepted and spawn recolours counted")
-- A finished trail is dropped.
trail.running = false
onFrame()
out = {}; onDraw()
trail.params.Color.c = color(hex(0xFF, 0x2E, 0x2E))
onFrame()
check(rgb(trail.params.Color.c) == "FF2E2E", "finished trail no longer tracked")
late.running = false; onFrame()
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
check(table.concat(out):match("Tracking 3 effects"), "destroyed and finished effects dropped (the three buff/heal effects stay watched)")
-- Switch the buff hiding off.
toggle["Hide attack-up / defense-up glow"] = true; onDraw()
check(savedCfg and savedCfg[2].hideBuffs == false, "setting saved")
defenseUp.tint = color(ORANGE)
onFrame(); clock = 1; onFrame()
check(defenseUp.tint.rgba == ORANGE, "with hiding off the glow stays")
-- A buff effect already black (e.g. after a script reload) is still watched: the game's
-- next replay sets the tint again and it is hidden before rendering.
toggle["Hide attack-up / defense-up glow"] = true; onDraw()
local reloaded = effect("11_pl_heal", "Art/VFX/EffectEditor/Player/pl_cm/pl_state/11_pl_heal.efx", 0)
playing = { reloaded }
clock = 2; onFrame()
reloaded.tint = color(ORANGE)
beforeRender()
check(reloaded.tint.rgba == 0, "replayed buff tint hidden in the before-rendering pass")
-- A new trail in the scene that no hook saw: recoloured in the same pass that finds it.
local fresh = effect("11_it02_001", "Art/VFX/EffectEditor/Weapon/it02/11_it02_001.efx", hex(0xFF, 0xFF, 0xFF),
    { Color = param("Color", hex(0xFF, 0x2E, 0x2E)) })
playing = { reloaded, fresh }
beforeRender()
check(hue_is_gold(fresh.params.Color.c), "new trail found by the per-frame search is gold before its first frame is drawn")
out = {}; onDraw()
check(tonumber(table.concat(out):match("(%d+) when found")) >= 1, "counted as recoloured when found")
check(table.concat(out):match("Cost: [%d.]+ ms per frame %(dual blades: searching every frame%)"), "cost and search rate shown")
-- Great sword in hand: its effects are tinted gold (white parts too), others left alone.
heldType = "app.cHunterWp00Handling"
clock = clock + 2
local WHITE = hex(0xFF, 0xFF, 0xFF, 0x80)
local gsGlow = effect("11_it00_020", "", WHITE, {})
local gsCharge = effect("11_it00_002", "", WHITE, {})
local other = effect("ef_dust", "", WHITE, {})
playing = { gsGlow, gsCharge, other }
beforeRender(); clock = clock + 0.05; beforeRender()
check(hue_is_gold(gsGlow.tint) and (gsGlow.tint.rgba >> 24) == 0x80, "great sword: white effect tinted gold, alpha kept (" .. rgb(gsGlow.tint) .. ")")
check(gsGlow.tint.rgba ~= hex(0xFF, 0xFF, 0xFF, 0x80) and rgb(gsGlow.tint) ~= "FFFFFF", "great sword: not left white")
check(other.tint.rgba == WHITE, "great sword: effects of nobody's weapon untouched")
out = {}; onDraw()
check(table.concat(out):match("great sword: searching every frame"), "great sword: searched every frame while held")
-- Hide the game's charge effects (the blade shows the charge).
toggle["Great sword: hide the game's charge effects (blade glow only)"] = true; onDraw()
clock = clock + 0.05; beforeRender()
check(gsCharge.tint.rgba == 0, "great sword: charge effect hidden when asked")
check(hue_is_gold(gsGlow.tint), "great sword: other great sword effects stay gold")
-- Light bowgun: ground dust (jimen) is not tinted.
heldType = "app.cHunterWp13Handling"
clock = clock + 2
local muzzle = effect("11_it13_102", "", WHITE, {})
local dust = effect("11_it13_102_jimen", "", WHITE, {})
playing = { muzzle, dust }
beforeRender(); clock = clock + 0.05; beforeRender()
check(hue_is_gold(muzzle.tint), "light bowgun: effect tinted gold")
check(dust.tint.rgba == WHITE, "light bowgun: ground dust left as is")
-- Insect glaive: searched 4 times a second (the flying kinsect), but every frame while the hunter
-- attacks: its trails are white in the files and the game tints them red as they start (user,
-- 2026-10-03: the rising spin showed red first, then gold).
heldType, hunterAction = "app.cHunterWp10Handling", "app.Wp10Action.cIdle"
clock = clock + 2
playing = {}
beforeRender()
local idleTrail = effect("11_it10_004", "", RED, {})
playing = { idleTrail }
clock = clock + 0.02; beforeRender()
check(idleTrail.tint.rgba == RED, "insect glaive: not attacking, a new effect waits for the next search (4 a second)")
out = {}; onDraw()
check(table.concat(out):match("insect glaive: 4 times a second, every frame while attacking"), "insect glaive: menu shows the search rate")
hunterAction = "app.Wp10Action.cBatonUpSlashSuper"
local spinTrail = effect("11_it10_001", "", RED, {})
playing = { idleTrail, spinTrail }
clock = clock + 0.02; beforeRender()
check(hue_is_gold(spinTrail.tint), "insect glaive: attacking, a new trail is gold before its first frame (" .. rgb(spinTrail.tint) .. ")")
out = {}; onDraw()
check(table.concat(out):match("insect glaive: searching every frame"), "insect glaive: every frame while attacking")
local smoke = effect("11_it10_010", "", RED, {})
playing = { smoke }
clock = clock + 0.02; beforeRender()
check(smoke.tint.rgba == RED, "insect glaive: smoke and dust left as they are")
print("ALL PASS")
