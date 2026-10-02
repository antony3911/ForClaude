-- Minimal stand-ins for the REFramework API, enough to drive MiquellaLight_Weapons.lua.
local failPaths = {}
local function resource(path) return { ToString = function() return "Resource[" .. path .. "]" end } end
-- A kit's growth bands (parts that grow with the charge): MiquellaGrow1..n.
local function withGrow(list, n)
  for k = 1, n do list[#list + 1] = "MiquellaGrow" .. k end
  return list
end
local function newMesh(meshPath)
  local m = { meshPath = meshPath, mdfPath = meshPath:gsub("%.mesh$", ".mdf2"), enabled = true }
  function m:getMesh() return resource(self.meshPath) end
  function m:get_Material() return resource(self.mdfPath) end
  m.setCount = 0
  function m:setMesh(h) self.meshPath = h.path; self.setCount = self.setCount + 1 end
  function m:set_Material(h) self.mdfPath = h.path end
  function m:set_Enabled(v) self.enabled = v end
  m.floats = {}
  local function mats(self)
    if self.mdfPath:match("wp_miquella_db") then
      return { "MiquellaBlade", "MiquellaIvory", "MiquellaGrip", "MiquellaGlow", "MiquellaDemon1", "MiquellaDemon2", "MiquellaDemon3" }
    end
    if self.mdfPath:match("wp_miquella_lbg") then
      return { "MiquellaBlade", "MiquellaGauge1", "MiquellaGauge2", "MiquellaGauge3", "MiquellaGlow", "MiquellaIvory" }
    end
    if self.mdfPath:match("wp_miquella_bow%.") then
      return withGrow({ "MiquellaGauge1", "MiquellaGauge2", "MiquellaGauge3", "MiquellaGlow", "MiquellaIvory", "MiquellaTemper" }, 21)
    end
    if self.mdfPath:match("wp_miquella_ls%.") then
      return withGrow({ "MiquellaGlow", "MiquellaIvory",
               "MiquellaBlade1", "MiquellaBlade2", "MiquellaBlade3", "MiquellaBlade4",
               "MiquellaBlade5", "MiquellaBlade6", "MiquellaBlade7", "MiquellaBlade8", "MiquellaBand1", "MiquellaBand2",
               "MiquellaBand3", "MiquellaBand4", "MiquellaBand5", "MiquellaBand6", "MiquellaBand7", "MiquellaBand8" }, 24)
    end
    if self.mdfPath:match("wp_miquella_sa%.") then
      return { "MiquellaAxeBlade", "MiquellaAxeGlow", "MiquellaFinBlade", "MiquellaFinGlow", "MiquellaGauge1",
               "MiquellaGauge2", "MiquellaGauge3", "MiquellaGauge4", "MiquellaGauge5", "MiquellaGlow", "MiquellaIvory",
               "MiquellaSpikeBlade", "MiquellaSwordBlade", "MiquellaSwordGlow" }
    end
    if self.mdfPath:match("wp_miquella_cb%.") then
      return { "MiquellaAxeGlow", "MiquellaAxeIvory", "MiquellaBlade", "MiquellaEdgeBlade", "MiquellaEdgeGlow",
               "MiquellaGauge1", "MiquellaGauge2", "MiquellaGauge3", "MiquellaGauge4", "MiquellaGauge5", "MiquellaGlow",
               "MiquellaIvory", "MiquellaRimGlow", "MiquellaTemper", "MiquellaSawAGlow", "MiquellaSawBGlow", "MiquellaSawCGlow" }
    end
    if self.mdfPath:match("wp_miquella_cb_shield") then
      return { "MiquellaBlade", "MiquellaGauge1", "MiquellaGauge2", "MiquellaGauge3", "MiquellaGauge4", "MiquellaGauge5",
               "MiquellaGlow", "MiquellaTemper" }
    end
    if self.mdfPath:match("wp_miquella_gl%.") then
      return { "MiquellaBlade", "MiquellaCore", "MiquellaGlow", "MiquellaIvory", "MiquellaFilament" }
    end
    if self.mdfPath:match("wp_miquella_ig%.") then
      return { "MiquellaBlade", "MiquellaExtractOrange", "MiquellaExtractRed", "MiquellaExtractWhite", "MiquellaGlow", "MiquellaIvory", "MiquellaTemper" }
    end
    if self.mdfPath:match("wp_miquella_sns%.") then
      return { "MiquellaBlade", "MiquellaGlow", "MiquellaIvory", "MiquellaTemper", "MiquellaTiming", "MiquellaBurst" }
    end
    if self.mdfPath:match("wp_miquella_ln%.") then
      return withGrow({ "MiquellaBlade", "MiquellaCharge3", "MiquellaChargeTip", "MiquellaGlow", "MiquellaIvory",
                        "MiquellaTemper" }, 24)
    end
    if self.mdfPath:match("wp_miquella_hm%.") then
      return { "MiquellaCharge1", "MiquellaCharge2", "MiquellaCharge3", "MiquellaGlow", "MiquellaIvory",
               "MiquellaArmillary1", "MiquellaArmillary2", "MiquellaArmillary3" }
    end
    if self.mdfPath:match("wp_miquella_gs") then
      return withGrow({ "MiquellaBlade", "MiquellaGlow", "MiquellaIvory", "MiquellaTemper", "MiquellaCharge3" }, 24)
    end
    return { "lambert" }
  end
  function m:get_MaterialNum() return #mats(self) end
  function m:getMaterialName(i) return mats(self)[i + 1] end
  local VARS = { "Emissive_Color", "Emissive_Intensity", "Dissolve", "Use_MoveEmit", "MoveEmit", "MoveEmit_Width" }
  function m:getMaterialVariableNum(i) return #VARS end
  function m:getMaterialVariableName(i, j) return VARS[j + 1] end
  function m:setMaterialFloat(i, j, v) self.floats[mats(self)[i + 1] .. "." .. j] = v end
  m.colors = {}
  function m:setMaterialFloat4(i, j, v) self.colors[mats(self)[i + 1]] = v end
  m.matEnabled = {}
  function m:setMaterialsEnable(i, v) self.matEnabled[mats(self)[i + 1]] = v end
  return m
end
local function newChain(path)
  local c = { path = path }
  function c:get_ChainAsset() return resource(self.path) end
  function c:set_ChainAsset(h) self.path = h.path end
  return c
end
local function newGO(name, addr, mesh, chain)
  local go = { name = name, addr = addr, draw = true, valid = true, comps = { ["via.render.Mesh"] = mesh, ["via.motion.Chain2"] = chain } }
  function go:get_Name() return self.name end
  function go:get_address() return self.addr end
  function go:get_Valid() return self.valid end
  function go:set_DrawSelf(v) self.draw = v end
  -- Weapon transform with named joints that record what the script sets.
  go.tf = { pos = { x = 0, y = 0, z = 0 }, rot = { x = 0, y = 0, z = 0, w = 1 }, joints = {} }
  function go.tf:call(m, a)
    if m == "get_Position" then return self.pos end
    if m == "get_Rotation" then return self.rot end
    if m == "getJointByName" then
      if not self.joints[a] then
        local j = { name = a }
        function j:call(jm, v)
          if jm == "set_LocalPosition" then self.lp = v elseif jm == "set_LocalRotation" then self.lr = v end
          if jm == "get_LocalRotation" then return self.lr or { x = 0, y = 0, z = 0, w = 1 } end
          if jm == "get_LocalPosition" then return self.lp or { x = 0, y = 0, z = 0 } end
        end
        self.joints[a] = j
      end
      return self.joints[a]
    end
  end
  function go:call(sig, t)
    if sig == "get_Transform" then return self.tf end
    return self.comps[t.name]
  end
  return go
end
local weaponMesh = newMesh("Art/Model/Item/it02/00/0002/it0200_0002_1.mesh")
local weaponChain = newChain("Art/Model/Item/it02/00/0002/it0200_0002_1.chain2")
local weaponGO = newGO("Wp02_R", 1001, weaponMesh, weaponChain)
local subMesh = newMesh("Art/Model/Item/it02/00/0002/it0200_0002_0.mesh")
local subGO = newGO("Wp02_L", 1002, subMesh, nil)
local chr = {}
local kijin = 0
local chargeLv = nil
local rapidGauge, rapidMode = nil, nil
local bowDraw = nil
local glStart, glKeep = nil, 0   -- gunlance charged shelling: its timer counts while charging, then keeps its value
local extract = {}               -- field -> value (insect glaive timers)
local insectGO = nil             -- the kinsect GameObject behind _Insect
local hunterAction = nil         -- type name of the hunter's current (base) action
local handlingFields = {}        -- field names the handling lists (the field recorder and rush trace read them)
local chargeT0 = nil             -- the game's charge timer (great sword, lance, long sword, bow) counts from here
function chr:call(m)
  if m == "get_BaseActionController" then
    return { call = function(_, cm)
      if cm == "get_CurrentAction" and hunterAction then
        return { get_type_definition = function() return { get_full_name = function() return hunterAction end } end }
      end
    end }
  end
  if m == "get_WeaponHandling" then
    -- One handling type per weapon object, like the game's (field lookups are cached per type).
    return { get_type_definition = function() return { get_full_name = function() return "Handling_" .. weaponGO.name end,
                                                       get_fields = function()
                                                         local out = {}
                                                         for _, fname in ipairs(handlingFields) do
                                                           out[#out + 1] = { get_name = function() return fname end, is_static = function() return false end }
                                                         end
                                                         return out
                                                       end,
                                                       get_parent_type = function() return nil end } end,
             get_field = function(_, n)
      if n == "_KijinExtern" then return kijin end
      if n == "_ChargeLv" or n == "<ChargeLv>k__BackingField" then return chargeLv end
      if n == "_ChargeShotElapsedTimer" then
        if glStart then glKeep = os.clock() - glStart end
        return glKeep
      end
      if n == "_ChargeTimer" or n == "_FinishChargeTimer" or n == "_KijinChargeTimer" then
        return chargeT0 and (os.clock() - chargeT0) or 0
      end
      if n == "_RapidAmmoGauge" then return rapidGauge end
      if n == "_IsRapidMode" then return rapidMode end
      if n == "_IsBowStringConstToHand" then return bowDraw end
      if extract[n] ~= nil then return extract[n] end
      if n == "_Insect" and insectGO then return { call = function(_, m) if m == "get_GameObject" then return insectGO end end } end
    end }
  end
end
local fakeTime = 0
os.clock = function() return fakeTime end
function chr:get_Weapon() return { get_GameObject = function() return weaponGO end } end
function chr:get_SubWeapon() return { get_GameObject = function() return subGO end } end
local master = { get_Valid = function() return true end, get_Character = function() return chr end }
local pm = { getMasterPlayer = function() return master end }

local hookPre
sdk = {
  typeof = function(n) return { name = n } end,
  get_managed_singleton = function(n) return n == "app.PlayerManager" and pm or nil end,
  find_type_definition = function(n) return { get_method = function(_, m) return { m = m } end } end,
  hook = function(method, pre, post) hookPre = pre end,
  to_managed_object = function(x) return x end,
  create_resource = function(t, path)
    if failPaths[path] then return nil end
    local r = {}
    function r:add_ref() return self end
    function r:create_holder(ht) local h = { path = path, type = ht }; function h:add_ref() return self end; return h end
    return r
  end,
}
local onFrame, onDraw
re = { on_frame = function(f) onFrame = f end, on_draw_ui = function(f) onDraw = f end }
Vector3f = { new = function(x, y, z) return { x = x, y = y, z = z } end }
Vector4f = { new = function(x, y, z, w) return { x = x, y = y, z = z, w = w } end }
Quaternion = { new = function(w, x, y, z) return { w = w, x = x, y = y, z = z } end }
local comboAnswer = nil
local comboPick = nil            -- { slot = "SubWeapon", name = "<look>" }: pick a look by name on that row
local sizeAnswer = nil
local sliderAnswer = {}
local texts = {}
local combos = {}                -- labels of the combo boxes drawn
imgui = {
  tree_node = function() return true end, tree_pop = function() end, same_line = function() end,
  checkbox = function(l, v) return false, v end, button = function() return false end,
  text = function(t) texts[#texts + 1] = t end, text_colored = function(t) texts[#texts + 1] = "!! " .. t end,
  combo = function(label, idx, list)
    combos[#combos + 1] = label
    if comboPick and label:match("##" .. comboPick.slot .. "$") then
      local want = comboPick.name; comboPick = nil
      for i, k in ipairs(list) do if k == want then return true, i end end
      return false, idx
    end
    if comboAnswer and label:match("##Weapon$") then
      -- Answers count in the first looks' order; find them by name (more looks sort in between).
      local a = comboAnswer; comboAnswer = nil
      local name = ({ "(original)", "DualBlades", "GreatSword", "LightBowgun" })[a]
      for i, k in ipairs(list) do if k == name then a = i end end
      return true, a
    end
    if sizeAnswer and label == "Size (dual blades)" then local a = sizeAnswer; sizeAnswer = nil; return true, a end
    return false, idx
  end,
  slider_float = function(label, v)
    if sliderAnswer[label] then local a = sliderAnswer[label]; sliderAnswer[label] = nil; return true, a end
    return false, v
  end,
}
local savedCfg
local savedFiles = {}
json = { load_file = function() return nil end, dump_file = function(p, t)
  savedFiles[p] = t
  if p == "MiquellaLight/Weapons.json" then savedCfg = t end
end }

if arg[2] == "missing" then
  failPaths["Art/Model/MiquellaLight/DualBlades/wp_miquella_db_s14.mesh"] = true
end
dofile(arg[1])
local function frames(n, dt)
  for _ = 1, n do
    fakeTime = fakeTime + (dt or 0)
    onFrame()
  end
end
local function anyText(pattern)
  for _, t in ipairs(texts) do if t:match(pattern) then return true end end
  return false
end
local function check(cond, msg) print((cond and "PASS " or "FAIL ") .. msg); if not cond then os.exit(1) end end

if arg[2] == "missing" then
  frames(20)
  comboAnswer = 2; onDraw()
  frames(40)
  texts = {}; onDraw()
  local sawError = false
  for _, t in ipairs(texts) do if t:match("^!! Could not load") then sawError = true end end
  check(sawError, "missing model shows an error in the menu")
  check(weaponMesh.meshPath:match("it0200_0002_1") and weaponGO.draw == true, "weapon left untouched")
  print("ALL PASS (missing pak)")
  os.exit(0)
end
frames(20)
texts = {}; onDraw()
check(anyText("it0200_0002_1%.mesh"), "menu shows the original main weapon path")
comboAnswer = 2; onDraw()
check(savedCfg and savedCfg.assignType["it02"] == "DualBlades", "assignment saved for all dual blades")
frames(20)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/DualBlades/wp_miquella_db_s14.mesh", "main weapon model swapped (default size 1.4)")
check(weaponMesh.mdfPath == "Art/Model/MiquellaLight/DualBlades/wp_miquella_db.mdf2", "main weapon material swapped")
check(weaponChain.path == "Art/Model/Item/it00/99/it0099_0000_0.chain2", "physics chain replaced with the empty one")
check(subMesh.meshPath:match("wp_miquella_db"), "sub weapon (same type) swapped too")
hookPre({ { } , { ToString = function() return "app.HunterCharacter[MasterPlayer]" end, _IsWeaponOn = false } })
-- args[2] is the hunter
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = false } })
frames(1)
check(weaponGO.draw == false, "hidden while sheathed")
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = true } })
frames(1)
check(weaponGO.draw == true, "shown while drawn")
-- Glow slider and Size choice.
check(math.abs((weaponMesh.floats["MiquellaBlade.1"] or 0) - 1.2) < 1e-6, "glow at default intensity on the blade")
sliderAnswer.Glow = 2.0; onDraw()
frames(20)
check(math.abs(weaponMesh.floats["MiquellaBlade.1"] - 2.4) < 1e-6 and math.abs(weaponMesh.floats["MiquellaGlow.1"] - 2.4) < 1e-6, "glow slider scales blade and droplet")
check(weaponMesh.floats["MiquellaIvory.1"] == nil, "ivory not made to glow")
sizeAnswer = 1; onDraw()            -- "1.0"
frames(20)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/DualBlades/wp_miquella_db.mesh", "size 1.0 picks the base model")
check(savedCfg.size == "1.0", "size choice saved")
sizeAnswer = 4; onDraw()            -- "1.6"
frames(20)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/DualBlades/wp_miquella_db_s16.mesh", "size 1.6 model")
check(weaponMesh.floats["MiquellaBlade.1"] and math.abs(weaponMesh.floats["MiquellaBlade.1"] - 2.4) < 1e-6, "glow kept on the new size")
check(subMesh.meshPath == "Art/Model/MiquellaLight/DualBlades/wp_miquella_db_s16.mesh", "sub weapon follows the size too")
sizeAnswer = 3; onDraw()            -- back to "1.4"
frames(20)
-- Demon mode: side blades hidden, then split out in stages, then merge back.
local function visible(name) return weaponMesh.matEnabled[name] == true end
local function dissolve(name) return weaponMesh.floats[name .. ".2"] or 0 end
check(not visible("MiquellaDemon1") and not visible("MiquellaDemon2") and not visible("MiquellaDemon3"),
      "side blades hidden outside demon mode")
check(visible("MiquellaBlade"), "main blade visible")
kijin = 1
frames(3, 0.05)          -- 0.15 s of 0.35 s: about 43 %
check(visible("MiquellaDemon1") and visible("MiquellaDemon2") and not visible("MiquellaDemon3"),
      "early in the split: short and middle stages showing")
check(dissolve("MiquellaDemon1") > 0 and dissolve("MiquellaDemon1") < 1, "stage 1 partly faded")
frames(6, 0.05)
check(not visible("MiquellaDemon1") and not visible("MiquellaDemon2") and visible("MiquellaDemon3")
      and dissolve("MiquellaDemon3") == 1, "demon mode: only the final three-blade pose, fully shown")
check(math.abs(weaponMesh.floats["MiquellaDemon3.1"] - 2.4) < 1e-6, "glow slider also brightens the side blades")
kijin = 0
frames(6, 0.05)
check(not visible("MiquellaDemon1") and not visible("MiquellaDemon2") and not visible("MiquellaDemon3"),
      "side blades gone after demon mode ends")
-- Game reloads its own model (e.g. after a loading screen): we swap again.
weaponMesh.meshPath = "Art/Model/Item/it02/00/0002/it0200_0002_1.mesh"
frames(20)
check(weaponMesh.meshPath:match("wp_miquella_db"), "re-swapped after the game restored its model")
-- The game equips a weapon of another type (unassigned: long sword) on the same object while sheathed.
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = false } })
frames(1)
weaponMesh.meshPath = "Art/Model/Item/it03/00/0005/it0300_0005_1.mesh"
frames(20)
check(weaponMesh.meshPath:match("it0300_0005_1") and weaponGO.draw == true, "different weapon left alone and visible")
-- Back to the assigned weapon: swapped again.
weaponMesh.meshPath = "Art/Model/Item/it02/00/0002/it0200_0002_1.mesh"
frames(20)
check(weaponMesh.meshPath:match("wp_miquella_db") and weaponChain.path:match("it0099"), "assigned weapon swapped again")
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = true } })
frames(1)
-- REFramework "Reset scripts": the script restarts while our model is already on the weapon.
check(savedCfg.swappedFrom and savedCfg.swappedFrom.Weapon.original == "Art/Model/Item/it02/00/0002/it0200_0002_1.mesh",
      "slot's original model remembered in the config")
json.load_file = function() return savedCfg end
weaponMesh.matEnabled = {}
dofile(arg[1])
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = true } })
frames(20)          -- model checks run every 20 frames
check(weaponMesh.meshPath:match("wp_miquella_db_s14"), "after a script reload the swapped weapon is kept")
kijin = 1
frames(10, 0.05)
check(visible("MiquellaDemon3") and dissolve("MiquellaDemon3") == 1, "after a script reload demon mode still splits the blade")
kijin = 0
frames(10, 0.05)
-- Un-assign: back to the original.
comboAnswer = 1; onDraw()
frames(20)
check(weaponMesh.meshPath == "Art/Model/Item/it02/00/0002/it0200_0002_1.mesh", "original model restored")
check(weaponMesh.mdfPath == "Art/Model/Item/it02/00/0002/it0200_0002_1.mdf2", "original material restored")
check(weaponChain.path == "Art/Model/Item/it02/00/0002/it0200_0002_1.chain2", "original physics restored")
check(weaponGO.draw == true, "visible again")
check(not weaponMesh.meshPath:match("wp_miquella"), "after size changes, un-assigning still restores the game's model")
-- A config from the older version (no record of the slots' original models), then a reload.
comboAnswer = 2; onDraw()
frames(20)
check(weaponMesh.meshPath:match("wp_miquella_db"), "assigned again")
-- (older versions chose a look per model and kept no record of the slots' originals)
savedCfg.swappedFrom, savedCfg.assignType, savedCfg.migratedFrom = nil, nil, nil
savedCfg.assign = { ["Art/Model/Item/it02/00/0002/it0200_0002_1.mesh"] = "DualBlades",
                    ["Art/Model/Item/it02/00/0002/it0200_0002_0.mesh"] = "DualBlades" }
weaponMesh.matEnabled = {}
dofile(arg[1])
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = true } })
frames(20)
kijin = 1
frames(10, 0.05)
check(visible("MiquellaDemon3"), "older config: the swapped weapon is still picked up after a reload")
check(savedCfg.assignType and savedCfg.assignType.it02 == "DualBlades" and next(savedCfg.assign) == nil,
      "older config: per-model choice moved to the weapon type")
kijin = 0
frames(10, 0.05)
comboAnswer = 1; onDraw()
frames(20)
check(weaponMesh.meshPath == "Art/Model/Item/it02/00/0002/it0200_0002_1.mesh", "older config: the right-hand model guessed and restored")
-- Another weapon type: a great sword (one model, no sub weapon, no demon mode).
weaponMesh = newMesh("Art/Model/Item/it00/00/0000/it0000_0000_0.mesh")
weaponChain = newChain("Art/Model/Item/it00/00/0000/it0000_0000_0.chain2")
weaponGO = newGO("Wp00", 2001, weaponMesh, weaponChain)
subGO = nil
frames(20)
texts = {}; onDraw()
check(anyText("it0000_0000_0%.mesh"), "great sword: menu shows its model path")
comboAnswer = 3; onDraw()
check(savedCfg.assignType["it00"] == "GreatSword", "great sword: assignment saved for all great swords")
frames(20)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/GreatSword/wp_miquella_gs.mesh", "great sword: model swapped (no size variants)")
check(weaponMesh.mdfPath == "Art/Model/MiquellaLight/GreatSword/wp_miquella_gs.mdf2", "great sword: material swapped")
check(math.abs((weaponMesh.floats["MiquellaTemper.1"] or 0) - 1.2 * savedCfg.glow) < 1e-6, "great sword: Glow slider reaches the temper line")
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = false } })
frames(1)
check(weaponGO.draw == false, "great sword: hidden while sheathed")
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = true } })
frames(1)
check(weaponGO.draw == true, "great sword: shown when drawn")
-- Floating rings: joints found, quiet at rest, flung by a swing, settle afterwards.
frames(5, 1 / 60)
texts = {}; onDraw()
local sawRings = false
for _, t in ipairs(texts) do if t:match("^Rings found: 4/4") then sawRings = true end end
check(sawRings, "great sword: menu reports the 4 ring joints")
local ring = weaponGO.tf.joints["MQ_Ring1"]
local pivot = { 0.0222, 0.0, 1.4818 }
local function ringOff()
  local p = ring.lp
  return math.sqrt((p.x - pivot[1]) ^ 2 + (p.y - pivot[2]) ^ 2 + (p.z - pivot[3]) ^ 2)
end
frames(60, 1 / 60)
check(ring.lp and ringOff() < 0.004, string.format("great sword: ring drifts only slightly at rest (%.4f m)", ringOff()))
local q = ring.lr
check(math.abs(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z - 1) < 1e-6, "great sword: ring rotation is a unit quaternion")
local peak = 0
for i = 1, 12 do          -- a fast swing: speeds up along X for 0.2 s
  weaponGO.tf.pos.x = weaponGO.tf.pos.x + 0.02 * i
  frames(1, 1 / 60)
  peak = math.max(peak, ringOff())
end
frames(6, 1 / 60)
check(peak > 0.01, string.format("great sword: a swing flings the ring (%.4f m)", peak))
check(peak < 0.035 + 0.004, "great sword: the fling stays within its range")
frames(120, 1 / 60)
check(ringOff() < 0.004, string.format("great sword: the ring settles back (%.4f m)", ringOff()))
sliderAnswer["Ring motion"] = 0.0; onDraw()
frames(30, 1 / 60)
check(ringOff() < 1e-3, "great sword: Ring motion 0 keeps the ring still")
-- Charge: the game's level brightens the blade; the third level turns it white and runs the band.
local glow = savedCfg.glow
chargeLv = 0
frames(200, 1 / 60)                  -- the field is looked for again after 3 s
texts = {}; onDraw()
local sawCharge = false
for _, t in ipairs(texts) do if t:match("^Charge: _ChargeLv = 0") then sawCharge = true end end
check(sawCharge, "great sword: menu shows the charge field it found")
check(math.abs(weaponMesh.floats["MiquellaBlade.1"] - 1.2 * glow) < 1e-6, "great sword: level 0 keeps the base glow")
chargeLv = 2
frames(30, 1 / 60)
check(math.abs(weaponMesh.floats["MiquellaBlade.1"] - 1.2 * glow * 2.8) < 1e-6, "great sword: level 2 glows 2.8x")
check(weaponMesh.floats["MiquellaTemper.3"] == 0.0, "great sword: no band before level 3")
check(weaponMesh.matEnabled["MiquellaCharge3"] ~= true, "great sword: no sparks before level 3")
chargeLv = 3
frames(30, 1 / 60)
local c = weaponMesh.colors["MiquellaBlade"]
check(c and c.z > 0.8, "great sword: level 3 turns the blade white")
check(weaponMesh.floats["MiquellaTemper.3"] == 1.0, "great sword: level 3 runs the band on the temper line")
local sc = weaponMesh.colors["MiquellaCharge3"]
check(weaponMesh.matEnabled["MiquellaCharge3"] == true and sc and sc.z < 0.3,
      "great sword: level 3 shows all the strands and sparks, bright gold on the white blade")
local band1 = weaponMesh.floats["MiquellaTemper.4"]
frames(10, 1 / 60)
check(weaponMesh.floats["MiquellaTemper.4"] ~= band1, "great sword: the band moves")
chargeLv = 0
frames(90, 1 / 60)                   -- 0.35 s per level on the way down
check(math.abs(weaponMesh.floats["MiquellaBlade.1"] - 1.2 * glow) < 1e-6 and weaponMesh.floats["MiquellaTemper.3"] == 0.0,
      "great sword: releasing the charge fades back")
-- The strands grow with the charge (user, 2026-10-03): the game's _ChargeTimer against the level
-- thresholds (0.8 / 1.55 / 2.3 s), not a level's piece at a time; where the game's level really
-- changes is learned for the next charges.
local function grown(n)              -- growth bands fully shown, and the front band's share
  local full, front = 0, 0
  for k = 1, n do
    local on, d = weaponMesh.matEnabled["MiquellaGrow" .. k] == true, weaponMesh.floats["MiquellaGrow" .. k .. ".2"] or 0
    if on and d >= 0.999 then full = full + 1 elseif on and d > 0.001 then front = d end
  end
  return full, front
end
check(grown(24) == 0, "great sword: no strands without a charge")
chargeT0 = fakeTime                  -- a charge: the timer counts, level 0
frames(24, 1 / 60)                   -- 0.4 s: half the way to level 1
local g1 = grown(24)
check(g1 >= 3 and g1 <= 5, string.format("great sword: the strands grow during the first level (%d of 24 bands)", g1))
-- The band growing is drawn out of a point by the strands' own bones (two a band, MQ_G<strand>_1-48):
-- the ones ahead of the front gather there, the front climbs every frame, the ones behind rest.
local function jp(n) local j = weaponGO.tf.joints[n]; return j and j.lp end
frames(2, 1 / 60)                    -- 0.43 s: the front in band 5 (strand bones 9, 10)
local a8, a9, a10 = jp("MQ_G0_8"), jp("MQ_G0_9"), jp("MQ_G0_10")
check(a8 and a9 and a10 and a9.x == a10.x and a9.y == a10.y and a9.z == a10.z and math.abs(a8.z - a9.z) > 1e-3,
      "great sword: the band growing has its bones gathered at the front, the one behind rests")
local z8, zf, rose = a8.z, a10.z, true
for _ = 1, 3 do
  frames(1, 1 / 60)
  if jp("MQ_G0_10").z <= zf then rose = false end
  zf = jp("MQ_G0_10").z
end
check(rose and jp("MQ_G0_8").z == z8, string.format("great sword: the front climbs every frame (%.4f), the bones behind stay", zf))
frames(7, 1 / 60)
local g2 = grown(24)
check(g2 > g1 and g2 <= 7, string.format("great sword: and keep growing (%d)", g2))
frames(6, 1 / 60)                    -- 0.7 s: the game's level comes early this time
chargeLv = 1
frames(15, 1 / 60)
local g3 = grown(24)
check(g3 >= 9 and g3 <= 11, string.format("great sword: level 1 = a third grown (%d)", g3))
frames(54, 1 / 60)                   -- 1.85 s (level 2 at 1.55)
check(grown(24) <= 17, string.format("great sword: still short of level 2's growth until the game says so (%d)", grown(24)))
chargeLv = 2
frames(27, 1 / 60)                   -- 2.3 s
chargeLv = 3
frames(12, 1 / 60)
check(grown(24) == 24 and weaponMesh.matEnabled["MiquellaCharge3"] == true, "great sword: full charge, the strands reach the point, sparks")
check(jp("MQ_G2_48") and math.abs(jp("MQ_G2_48").z - 2.144) < 2e-3, "great sword: and every bone is back where it was built")
local sg = weaponMesh.colors["MiquellaGrow24"]
check(sg and sg.z < 0.3 and weaponMesh.floats["MiquellaGrow24.1"] / (1.2 * glow) > 3.0,
      "great sword: the strands stay bright gold on the white blade")
chargeLv, chargeT0 = 0, nil
frames(6, 1 / 60)
local gf, gfront = grown(24)
check(gf == 0 and gfront > 0.2, "great sword: let go, the strands fade where they stand")
frames(20, 1 / 60)
check(grown(24) == 0 and select(2, grown(24)) == 0, "great sword: and are gone")
check(savedCfg.chargeTimes and savedCfg.chargeTimes.it00 and math.abs(savedCfg.chargeTimes.it00["1"] - 0.7) < 0.03,
      "great sword: the level the game reached early is learned and saved")
chargeT0 = fakeTime                  -- the next charge uses it: level 1's growth by 0.7 s
frames(39, 1 / 60)
local g4 = grown(24)
check(g4 >= 7 and g4 <= 9, string.format("great sword: the next charge grows by the learned time (%d at 0.65 s)", g4))
chargeT0 = nil
frames(40, 1 / 60)
texts = {}; onDraw()
check(anyText("^Growth: _ChargeLv") and anyText("^Growth bones found: 144/144"), "great sword: menu shows the growth and its bones")
comboAnswer = 1; onDraw()
frames(20)
check(weaponMesh.meshPath == "Art/Model/Item/it00/00/0000/it0000_0000_0.mesh", "great sword: original restored")
-- Light bowgun: the rapid-fire gauge lights the three drops, rapid-fire mode brightens them.
weaponMesh = newMesh("Art/Model/Item/it13/00/0001/it1300_0001_0.mesh")
weaponGO = newGO("Wp13", 3001, weaponMesh, newChain("Art/Model/Item/it13/00/0001/it1300_0001_0.chain2"))
rapidGauge, rapidMode = 100, false
frames(20, 1 / 60)
comboAnswer = 4; onDraw()
frames(260, 1 / 60)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/LightBowgun/wp_miquella_lbg.mesh", "light bowgun: model swapped")
local function dot(i) return weaponMesh.floats["MiquellaGauge" .. i .. ".1"] / (1.2 * glow) end
check(math.abs(dot(3) - 1) < 1e-3, "light bowgun: full gauge lights all three drops")
rapidGauge = 50
frames(60, 1 / 60)
check(math.abs(dot(1) - 1) < 1e-3 and dot(3) < 0.4, string.format("light bowgun: half gauge (%.2f %.2f %.2f)", dot(1), dot(2), dot(3)))
rapidMode = true
frames(60, 1 / 60)
check(dot(1) > 1.7, "light bowgun: rapid-fire mode brightens the drops")
texts = {}; onDraw()
local sawGauge = false
for _, t in ipairs(texts) do if t:match("^Gauge: _RapidAmmoGauge") then sawGauge = true end end
check(sawGauge, "light bowgun: menu shows the gauge field")
-- One look for every weapon of the type: another light bowgun takes it without the menu.
weaponMesh.meshPath = "Art/Model/Item/it13/00/0005/it1300_0005_0.mesh"
frames(40, 1 / 60)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/LightBowgun/wp_miquella_lbg.mesh", "another light bowgun takes the look too")
-- Swapped while sheathed: set again when drawn (the first set can land before the model loaded).
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = false } })
weaponMesh = newMesh("Art/Model/Item/it13/00/0006/it1300_0006_0.mesh")
weaponGO = newGO("Wp13b", 3002, weaponMesh, newChain("Art/Model/Item/it13/00/0006/it1300_0006_0.chain2"))
frames(30, 1 / 60)
local sets = weaponMesh.setCount
check(weaponMesh.meshPath:match("wp_miquella_lbg") and sets >= 1, "new weapon object swapped while sheathed")
frames(80, 1 / 60)
check(weaponMesh.setCount > sets, "model set again a second after the swap")
sets = weaponMesh.setCount
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = true } })
frames(2, 1 / 60)
check(weaponMesh.setCount > sets, "and once more when the weapon is drawn")
-- Sword & shield: the shield (_1) takes the look's shield; a film can be picked on its row.
weaponMesh = newMesh("Art/Model/Item/it01/00/0003/it0100_0003_0.mesh")
weaponGO = newGO("Wp01", 4001, weaponMesh, nil)
local shieldMesh = newMesh("Art/Model/Item/it01/00/0003/it0100_0003_1.mesh")
subGO = newGO("Wp01_Shield", 4002, shieldMesh, nil)
frames(20, 1 / 60)
comboPick = { slot = "Weapon", name = "SwordShield" }; onDraw()
frames(30, 1 / 60)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns.mesh", "sword & shield: sword takes the look")
check(shieldMesh.meshPath == "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns_shield.mesh", "sword & shield: shield takes the look's shield")
comboPick = { slot = "SubWeapon", name = "SwordShield_ShieldD" }; onDraw()
frames(30, 1 / 60)
check(shieldMesh.meshPath == "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns_shield_film.mesh", "sword & shield: film D picked for every shield")
check(savedCfg.assignShield.it01 == "SwordShield_ShieldD", "sword & shield: shield choice saved per type")
-- Perfect Rush (user's pick "S2"): in the game's cJustRush actions the ring rides down the blade
-- to the guard; a Perfect (_IsJustRush) bursts at the guard and fades.
local ringJ = weaponGO.tf.joints["MQ_TimingRing"]
local function shown(n) return weaponMesh.matEnabled[n] == true, weaponMesh.floats[n .. ".2"] or 0 end
check(not shown("MiquellaTiming") and not shown("MiquellaBurst"), "sword & shield: no timing ring outside Perfect Rush")
handlingFields = { "_IsJustRush", "_StepSlashCount" }
extract._IsJustRush, extract._StepSlashCount = false, 0
hunterAction = "app.Wp01Action.cJustRushCombo0"
frames(6, 1 / 60)
extract._StepSlashCount = 1
local zHigh = ringJ.lp.z
check(shown("MiquellaTiming") and zHigh > 0.7, string.format("sword & shield: Perfect Rush shows the ring high on the blade (%.3f)", zHigh))
frames(30, 1 / 60)
check(math.abs(ringJ.lp.z - 0.15) < 0.01, string.format("sword & shield: the ring comes down to the guard (%.3f)", ringJ.lp.z))
extract._IsJustRush = true
frames(3, 1 / 60)
check(shown("MiquellaBurst"), "sword & shield: a Perfect bursts at the guard")
frames(30, 1 / 60)
check(not shown("MiquellaBurst"), "sword & shield: the burst fades")
hunterAction, extract._IsJustRush = nil, false
frames(30, 1 / 60)
check(not shown("MiquellaTiming"), "sword & shield: the ring goes after the rush")
-- The rush trace (to time the ring from one test): every change during the rush, saved with the fields.
frames(400, 1 / 60)
local trace = nil
for p, t in pairs(savedFiles) do
  if p:find("MiquellaLight/fields_", 1, true) and t.trace then trace = table.concat(t.trace, " | ") end
end
check(trace ~= nil, "sword & shield: the rush trace is saved with the field record")
trace = trace or ""
check(trace:find("=== rush 1", 1, true) and trace:find("=== end", 1, true), "sword & shield: the trace marks the rush's start and end")
check(trace:find("_StepSlashCount 0 -> 1", 1, true) ~= nil, "sword & shield: the trace logs a field's change")
check(trace:find("_IsJustRush 0 -> 1", 1, true) and trace:find("Perfect!", 1, true), "sword & shield: the trace logs the Perfect")
check(trace:find("ring at the guard", 1, true) ~= nil, "sword & shield: the trace logs the ring reaching the guard")
handlingFields, extract._IsJustRush, extract._StepSlashCount = {}, nil, nil
-- Long sword: the scabbard (_1) keeps its game look.
weaponMesh = newMesh("Art/Model/Item/it03/00/0001/it0300_0001_0.mesh")
weaponGO = newGO("Wp03", 5001, weaponMesh, nil)
local scabbard = newMesh("Art/Model/Item/it03/00/0001/it0300_0001_1.mesh")
subGO = newGO("Wp03_Scabbard", 5002, scabbard, nil)
frames(20, 1 / 60)
comboPick = { slot = "Weapon", name = "LongSword" }; onDraw()
frames(30, 1 / 60)
check(weaponMesh.meshPath:match("MiquellaLight/LongSword"), "long sword: blade takes the look")
check(scabbard.meshPath == "Art/Model/Item/it03/00/0001/it0300_0001_1.mesh", "long sword: scabbard keeps its game look")
texts = {}; onDraw()
local sawKeep = false
for _, t in ipairs(texts) do if t:match("keeps its game look") then sawKeep = true end end
check(sawKeep, "long sword: menu says the scabbard keeps its look")
-- Bow: the quiver (_1) takes the look's quiver (B can be picked); drawing packs the rings ahead
-- of the arrow toward the bow, tighter per level, lights them a pair per level, gold -> white
-- gold; loosing the arrow springs them back past their places once.
weaponMesh = newMesh("Art/Model/Item/it11/00/0002/it1100_0002_0.mesh")
weaponGO = newGO("Wp11", 6001, weaponMesh, nil)
local quiverMesh = newMesh("Art/Model/Item/it11/00/0002/it1100_0002_1.mesh")
subGO = newGO("Wp11_Quiver", 6002, quiverMesh, nil)
chargeLv, bowDraw = 0, false
frames(20, 1 / 60)
comboPick = { slot = "Weapon", name = "Bow" }; onDraw()
frames(30, 1 / 60)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/Bow/wp_miquella_bow.mesh", "bow: model swapped")
check(quiverMesh.meshPath == "Art/Model/MiquellaLight/Bow/wp_miquella_bow_quiver_a.mesh", "bow: quiver takes quiver A")
combos = {}; onDraw()
local sawQuiver = false
for _, t in ipairs(combos) do if t:match("^Quiver look") then sawQuiver = true end end
check(sawQuiver, "bow: menu offers a quiver look")
comboPick = { slot = "SubWeapon", name = "Bow_QuiverB" }; onDraw()
frames(30, 1 / 60)
check(quiverMesh.meshPath == "Art/Model/MiquellaLight/Bow/wp_miquella_bow_quiver_b.mesh", "bow: quiver B picked")
frames(200, 1 / 60)                  -- the draw field is looked for again after 3 s
local front = weaponGO.tf.joints["MQ_Ring5"]
local REST, PACKED = 1.0080, 1.0080 - 0.5490
check(front.lp and math.abs(front.lp.z - REST) < 0.01, string.format("bow: rings spread at rest (front ring z %.3f)", front.lp.z))
local function gauge(i) return weaponMesh.floats["MiquellaGauge" .. i .. ".1"] / (1.2 * glow) end
check(math.abs(gauge(3) - 1) < 1e-3, "bow: rings at normal glow when not drawn")
check(grown(21) == 0, "bow: no flowers when not drawn")
-- The game's own level times (_ActionParam._ChargeTimeLv2 / 3: 1 and 2 s of _ChargeTimer); the
-- flowers open one at a time, each its heart then half its petals then the rest, two in a level's
-- time; at the top level the rest, the tips' last (user, 2026-10-03).
extract._ActionParam = { get_field = function(_, k)
  return ({ _ChargeTimeLv2 = 1.0, _ChargeTimeLv3 = 2.0, _ChargeTimeLv4 = 3.0 })[k]
end }
bowDraw, chargeLv, chargeT0 = true, 1, fakeTime
frames(15, 1 / 60)                   -- 0.25 s
local f1, f1front = grown(21)
check(f1 == 1 and f1front > 0.2, string.format("bow: the first flower opens first, heart then petals (%d, %.2f)", f1, f1front))
frames(15, 1 / 60)                   -- 0.5 s: half a level's time
check(grown(21) == 3, string.format("bow: the first flower open at half the level, the second not yet (%d)", grown(21)))
frames(30, 1 / 60)                   -- 1.0 s
local z1 = front.lp.z
check(z1 < REST - 0.2 and z1 > PACKED + 0.05, string.format("bow: drawing packs the rings part way (%.3f)", z1))
check(math.abs(gauge(1) - 1.8) < 0.05 and gauge(3) < 0.4, string.format("bow: level 1 lights the first pair (%.2f %.2f %.2f)", gauge(1), gauge(2), gauge(3)))
check(grown(21) >= 5 and grown(21) <= 6, string.format("bow: the second flower opening as level 2 comes (%d)", grown(21)))
chargeLv = 2
frames(30, 1 / 60)                   -- 1.5 s
check(grown(21) >= 8 and grown(21) <= 9, string.format("bow: level 2: the third flower (%d)", grown(21)))
frames(30, 1 / 60)                   -- 2.0 s
chargeLv = 3
frames(6, 1 / 60)
local f3 = grown(21)
check(f3 >= 12 and f3 <= 14, string.format("bow: level 3: four flowers, the rest opening (%d)", f3))
frames(40, 1 / 60)
check(math.abs(front.lp.z - PACKED) < 0.01, string.format("bow: level 3 packs them tight (%.3f)", front.lp.z))
check(gauge(3) > 3.3, "bow: level 3 lights every ring")
check(grown(21) == 21, "bow: and every flower is open, the tips' last")
local fc = weaponMesh.colors["MiquellaGrow21"]
check(fc and fc.z > 0.5, "bow: the flowers take the level's white gold")
local col = weaponMesh.colors["MiquellaGauge3"]
check(col and col.z > 0.5 and col.y > 0.8, "bow: level 3 turns them white gold")
texts = {}; onDraw()
local sawDraw = false
for _, t in ipairs(texts) do if t:match("^Draw: _IsBowStringConstToHand") then sawDraw = true end end
check(sawDraw, "bow: menu shows the draw field")
-- The drawn arrow in the scene (the game's arrow model, found by its path), off the rings'
-- axis and tilted 6 degrees toward +X: the rings move onto its line.
local arrowMesh = newMesh("Art/Model/Item/it11/99/0000/it1199_0000_0.mesh")
local arrowGO = newGO("Arrow", 9901, arrowMesh, nil)
arrowGO.tf.pos = { x = 0.05, y = 0.0, z = -0.3 }
arrowGO.tf.rot = { x = 0, y = math.sin(math.rad(3)), z = 0, w = math.cos(math.rad(3)) }
function arrowMesh:call(m) if m == "get_GameObject" then return arrowGO end end
sdk.get_native_singleton = function() return {} end
sdk.call_native_func = function()
  return { call = function() return { get_elements = function() return { arrowMesh } end } end }
end
frames(40, 1 / 60)
local want = 0.05 + math.tan(math.rad(6)) * (front.lp.z + 0.3)
check(math.abs(front.lp.x - want) < 0.015 and math.abs(front.lp.y) < 0.015 and math.abs(front.lr.y) > 0.03,
      string.format("bow: rings move onto the drawn arrow's line (x %.3f, want %.3f; y %.3f)", front.lp.x, want, front.lp.y))
texts = {}; onDraw()
check(anyText("^Arrow: found"), "bow: menu says the arrow was found")
sdk.call_native_func = nil
bowDraw, chargeLv, chargeT0 = false, 0, nil
local far = 0
for _ = 1, 90 do frames(1, 1 / 60); far = math.max(far, front.lp.z) end
check(far > REST + 0.03, string.format("bow: loosing springs the rings past their places (%.3f)", far))
frames(120, 1 / 60)
check(math.abs(front.lp.z - REST) < 0.01, "bow: and they settle back")
check(math.abs(gauge(3) - 1) < 1e-3, "bow: glow back to normal")
check(grown(21) == 0, "bow: the flowers close after the shot")
-- Hammer: the charge cones fade in a level at a time beyond both faces, bright gold -> white.
weaponMesh = newMesh("Art/Model/Item/it04/00/0001/it0400_0001_0.mesh")
weaponGO = newGO("Wp04", 7001, weaponMesh, nil)
subGO = nil
chargeLv = 0
frames(20, 1 / 60)
comboPick = { slot = "Weapon", name = "Hammer" }; onDraw()
frames(30, 1 / 60)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/Hammer/wp_miquella_hm.mesh", "hammer: model swapped")
local function part(name) return weaponMesh.matEnabled[name] == true, weaponMesh.floats[name .. ".2"] or 0 end
local on1 = part("MiquellaCharge1")
check(not on1 and not part("MiquellaCharge3"), "hammer: no charge rings at rest")
chargeLv = 1
frames(30, 1 / 60)
local on, d = part("MiquellaCharge1")
check(on and d == 1 and not part("MiquellaCharge2"), "hammer: level 1 shows the first rings")
check(math.abs(weaponMesh.floats["MiquellaGlow.1"] / (1.2 * glow) - 1.8) < 1e-3, "hammer: level 1 bright gold glow on the hammer")
chargeLv = 3
frames(40, 1 / 60)
check(part("MiquellaCharge3"), "hammer: level 3 shows every cone ring")
-- The armillary sphere (user's pick "H4"): every great ring shown and turning about its own axis.
local function qOf(n) local j = weaponGO.tf.joints[n]; return j and j.lr end
local q0, q1 = qOf("MQ_Arm0"), qOf("MQ_Arm1")
frames(10, 1 / 60)
local turned0 = q0 and math.abs(qOf("MQ_Arm0").z - q0.z) > 1e-3
local turned1 = q1 and math.abs(qOf("MQ_Arm1").x - q1.x) > 1e-3
check(part("MiquellaArmillary3") and turned0 and turned1 and math.abs(qOf("MQ_Arm0").x) < 1e-9,
      "hammer: level 3 shows the armillary rings, each turning about its own axis")
local hc = weaponMesh.colors["MiquellaCharge3"]
check(hc and hc.z > 0.8 and weaponMesh.colors["MiquellaGlow"].z > 0.8, "hammer: level 3 turns rings and hammer white")
chargeLv = 0
frames(90, 1 / 60)
check(not part("MiquellaCharge1") and not part("MiquellaCharge3"), "hammer: rings fade out after the swing")
-- Insect glaive: charge gold -> bright gold -> white gold; the extract orbs show while lit and
-- circle the blade; all three brighten the blade; the kinsect takes the swallowtail and stays
-- when sheathed.
weaponMesh = newMesh("Art/Model/Item/it10/00/0003/it1000_0003_0.mesh")
weaponGO = newGO("Wp10", 8001, weaponMesh, nil)
local kinsectMesh = newMesh("Art/Model/Item/it10/03/0002/it1003_0002_0.mesh")
insectGO = newGO("Wp10Insect", 8002, kinsectMesh, nil)
-- The game's ExtractTimer: an array of app.cValueHolderF (red, white, orange), TrippleUpTimer one more.
local extractValues = { 0, 0, 0 }
local function holderOf(get) return { get_field = function(_, k) if k == "_Value" then return get() end end } end
local triple = 0
extract = { ExtractTimer = { get_elements = function()
              return { holderOf(function() return extractValues[1] end), holderOf(function() return extractValues[2] end),
                       holderOf(function() return extractValues[3] end) }
            end },
            TrippleUpTimer = holderOf(function() return triple end),
            -- (the extracts' durations: not timers)
            _ActionParam = { get_field = function(_, k) return ({ _ExtractTimerRed = 90, _ExtractTimerWhite = 120 })[k] end } }
chargeLv = 0
frames(20, 1 / 60)
comboPick = { slot = "Weapon", name = "InsectGlaive" }; onDraw()
frames(40, 1 / 60)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/InsectGlaive/wp_miquella_ig.mesh", "insect glaive: model swapped")
check(kinsectMesh.meshPath == "Art/Model/MiquellaLight/Kinsect/wp_miquella_kinsect.mesh", "insect glaive: kinsect takes the swallowtail")
-- Its wings beat slowly on our own bones: mirrored, and changing over a fraction of a second.
local wl, wr = insectGO.tf.joints["MQ_WingL"], insectGO.tf.joints["MQ_WingR"]
local q0 = wl and wl.lr and wl.lr.z
frames(9, 1 / 60)
check(wl and wr and wl.lr and wr.lr and math.abs(wl.lr.z + wr.lr.z) < 1e-6 and math.abs(wl.lr.z - q0) > 0.01
      and math.abs(wl.lr.z) < 0.35, "insect glaive: kinsect wings flap slowly, mirrored")
local function orb(n) return weaponMesh.matEnabled["MiquellaExtract" .. n] == true end
check(not orb("Red") and not orb("White") and not orb("Orange"), "insect glaive: no orbs without extracts")
extractValues[1] = 30
frames(30, 1 / 60)
check(orb("Red") and not orb("White"), "insect glaive: red extract (ExtractTimer[0]) shows the rot orb")
local o = weaponGO.tf.joints["MQ_OrbRed"]
local p1 = { o.lp.x, o.lp.y }
frames(30, 1 / 60)
local moved = math.sqrt((o.lp.x - p1[1]) ^ 2 + (o.lp.y - p1[2]) ^ 2)
local r = math.sqrt(o.lp.x ^ 2 + o.lp.y ^ 2)
check(moved > 0.05 and math.abs(r - 0.1408) < 1e-3, string.format("insect glaive: the orb circles the blade (moved %.3f, r %.4f)", moved, r))
-- The flowers (user's pick, style 2) keep facing out from the blade while they circle: the
-- joint's turn carries the slot's outward line (built along +Y for the red one) onto the radius.
local function qrotv(q, v)
  local x, y, z, w = q.x, q.y, q.z, q.w
  local tx, ty, tz = 2 * (y * v[3] - z * v[2]), 2 * (z * v[1] - x * v[3]), 2 * (x * v[2] - y * v[1])
  return { v[1] + w * tx + (y * tz - z * ty), v[2] + w * ty + (z * tx - x * tz), v[3] + w * tz + (x * ty - y * tx) }
end
local face = qrotv(o.lr, { 0, 1, 0 })
local dot = (face[1] * o.lp.x + face[2] * o.lp.y) / r
check(dot > 0.99 and math.abs(face[3]) < 1e-3, string.format("insect glaive: the flower keeps facing out (%.3f)", dot))
extractValues[2], extractValues[3], triple = 30, 30, 30
frames(40, 1 / 60)
check(orb("White") and orb("Orange"), "insect glaive: all three orbs")
texts = {}; onDraw()
check(anyText("^Extracts: ExtractTimer %[30 30 30%]") and anyText("TrippleUpTimer=30"), "insect glaive: menu shows the timers")
check(weaponMesh.floats["MiquellaBlade.1"] / (1.2 * glow) > 1.7, "insect glaive: three extracts brighten the blade")
triple = 0
chargeLv = 2
frames(60, 1 / 60)
local ic = weaponMesh.colors["MiquellaBlade"]
check(ic and ic.y > 0.8 and ic.z > 0.5 and ic.z < 0.7, "insect glaive: level 2 (full) charge is white gold")
chargeLv = 0
extractValues[1] = 0
frames(60, 1 / 60)
check(not orb("Red") and orb("White"), "insect glaive: an extract running out hides its orb")
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = false } })
frames(2, 1 / 60)
check(weaponGO.draw == false and insectGO.draw == true, "insect glaive: sheathed glaive hidden, kinsect stays")
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = true } })
frames(2, 1 / 60)
-- Gunlance: a reload winds the spring and lets it go; charged shelling winds it tighter per
-- level and holds until the shot, gold -> white gold; Wyvern's Fire winds it all the way.
weaponMesh = newMesh("Art/Model/Item/it07/00/0004/it0700_0004_0.mesh")
weaponGO = newGO("Wp07", 9001, weaponMesh, nil)
subGO = newGO("Wp07_Shield", 9002, newMesh("Art/Model/Item/it07/00/0004/it0700_0004_1.mesh"), nil)
insectGO = nil
extract = { _IsReload = false, _RyuugekiChargeTimer = 0 }
frames(20, 1 / 60)
comboPick = { slot = "Weapon", name = "Gunlance" }; onDraw()
frames(40, 1 / 60)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/Gunlance/wp_miquella_gl.mesh", "gunlance: model swapped")
local top = weaponGO.tf.joints["MQ_SpringTop"]
local REST_TOP = 1.6640
check(top.lp and math.abs(top.lp.z - REST_TOP) < 1e-3, "gunlance: spring at rest")
extract._IsReload = true
local low = REST_TOP
for _ = 1, 30 do frames(1, 1 / 60); low = math.min(low, top.lp.z) end
check(low < REST_TOP - 0.35, string.format("gunlance: a reload winds the spring (top down to %.3f)", low))
extract._IsReload = false
frames(90, 1 / 60)
check(math.abs(top.lp.z - REST_TOP) < 0.01, "gunlance: and lets it spring back")
glStart = fakeTime
local thread = weaponGO.tf.joints["MQ_FilamentTop"]
frames(20, 1 / 60)
local z1 = top.lp.z
frames(16, 1 / 60)                   -- 0.6 s of 1.2: the gold thread half drawn out
local half = (thread.lp.z - 0.429) / (2.015 - 0.429)
check(half > 0.4 and half < 0.6, string.format("gunlance: the gold thread grows with the charge (%.2f of its length at 0.6 s)", half))
frames(54, 1 / 60)
local z3 = top.lp.z
check(z3 < z1 - 0.05, string.format("gunlance: charged shelling winds tighter per level (%.3f -> %.3f)", z1, z3))
local gc = weaponMesh.colors["MiquellaCore"]
check(gc and gc.y > 0.8 and gc.z > 0.5, "gunlance: full charge is white gold")
-- The gold thread (user's pick "G3"): drawn out to the muzzle at full charge, shown.
check(thread.lp and math.abs(thread.lp.z - 2.015) < 0.02 and weaponMesh.matEnabled["MiquellaFilament"] == true,
      string.format("gunlance: full charge draws the gold thread out to the muzzle (%.3f)", thread.lp and thread.lp.z or -1))
glStart = nil
local far = 0
for _ = 1, 60 do frames(1, 1 / 60); far = math.max(far, top.lp.z) end
check(far > REST_TOP + 0.02, string.format("gunlance: the shot lets the spring fly back past its place (%.3f)", far))
frames(40, 1 / 60)                   -- the charge light fades over a second
check(thread.lp.z < 0.429 + (2.015 - 0.429) * 0.2 and weaponMesh.matEnabled["MiquellaFilament"] ~= true,
      string.format("gunlance: after the shot the thread goes back into the core (%.3f)", thread.lp.z))
extract._RyuugekiChargeTimer = 1.0
frames(60, 1 / 60)
check(math.abs(top.lp.z - (REST_TOP - 0.636)) < 0.01, "gunlance: Wyvern's Fire winds it all the way")
extract._RyuugekiChargeTimer = 0
frames(120, 1 / 60)
check(math.abs(top.lp.z - REST_TOP) < 0.01, "gunlance: back after the blast")
-- Wyvern's Fire: the hunter runs the game's cRyuugeki* actions through its wind-up; its gauge
-- drops by one at the blast. A shell fired lowers the count.
extract._RyuugekiGauge, extract._ChargeShotBulletNum = 2.0, 5
hunterAction = "app.Wp07Action.cIdle"
frames(10, 1 / 60)
check(math.abs(top.lp.z - REST_TOP) < 0.01, "gunlance: other actions leave the spring alone")
hunterAction = "app.Wp07Action.cRyuugekiStart"
frames(60, 1 / 60)
check(math.abs(top.lp.z - (REST_TOP - 0.636)) < 0.01, "gunlance: Wyvern's Fire's wind-up (cRyuugekiStart) winds the spring")
hunterAction = "app.Wp07Action.cRyuugekiShoot"
frames(20, 1 / 60)
check(math.abs(top.lp.z - (REST_TOP - 0.636)) < 0.01, "gunlance: still wound into the shot until the blast")
extract._RyuugekiGauge = 1.0
frames(120, 1 / 60)
check(math.abs(top.lp.z - REST_TOP) < 0.01, "gunlance: released at the blast (gauge used), though the action still runs")
hunterAction = "app.Wp07Action.cIdle"
frames(30, 1 / 60)
extract._ChargeShotBulletNum = 4
frames(6, 1 / 60)
check(top.lp.z < REST_TOP - 0.05, string.format("gunlance: a shell fired presses the spring (%.3f)", top.lp.z))
frames(90, 1 / 60)
check(math.abs(top.lp.z - REST_TOP) < 0.01, "gunlance: back after the shell")
texts = {}; onDraw()
local sawGl = false
for _, t in ipairs(texts) do if t:match("^Gunlance: _IsReload") and t:match("action: app%.Wp07Action%.cIdle") then sawGl = true end end
check(sawGl, "gunlance: menu shows the fields and the hunter's action")
hunterAction = nil
-- Switch axe and charge blade: both modes are one model; the game's mode drives a morph (joints
-- move, parts of one mode fade by Dissolve), never a model swap. Charge blade: the shield fades
-- out toward axe mode and is hidden once gone.
local function jointAt(name, pos)
  local j = weaponGO.tf.joints[name]
  return j and j.lp and math.abs(j.lp.x - pos[1]) + math.abs(j.lp.y - pos[2]) + math.abs(j.lp.z - pos[3]) < 1e-3
end
weaponMesh = newMesh("Art/Model/Item/it08/00/0001/it0800_0001_0.mesh")
weaponGO = newGO("Wp08", 10001, weaponMesh, nil)
subGO = nil
extract = { _Mode = 0 }
frames(20, 1 / 60)
comboPick = { slot = "Weapon", name = "SwitchAxe" }; onDraw()
frames(40, 1 / 60)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/SwitchAxe/wp_miquella_sa.mesh", "switch axe: our model")
check(dissolve("MiquellaAxeBlade") == 1 and dissolve("MiquellaSwordBlade") == 0 and not visible("MiquellaSwordBlade")
      and dissolve("MiquellaFinBlade") == 0, "switch axe: axe mode shows the axe blades, not the sword")
frames(40, 1 / 60)                   -- (past the model's set-again a second after the swap)
local sets = weaponMesh.setCount
extract._Mode = 1
frames(12, 1 / 60)                   -- 0.2 s of the 0.45 s morph
local b0 = weaponGO.tf.joints["MQ_Blade0"]
check(dissolve("MiquellaSwordBlade") == 1 and dissolve("MiquellaAxeBlade") > 0 and b0 and b0.lp
      and not jointAt("MQ_Blade0", { -0.095, 0.0, 1.178 }) and math.abs(b0.lr.w) < 0.99,
      "switch axe: mid-morph the sword is out and the axe blades swing")
frames(30, 1 / 60)
check(dissolve("MiquellaAxeBlade") == 0 and not visible("MiquellaAxeBlade") and dissolve("MiquellaFinBlade") == 1
      and dissolve("MiquellaSpikeBlade") == 0 and jointAt("MQ_HeadHalo", { -0.038, 0.0, 1.292 })
      and jointAt("MQ_SwordTip", { 0.0475, 0.016, 2.774 }), "switch axe: sword mode (fins shown, halo at the blade's root)")
check(weaponMesh.setCount == sets and weaponMesh.meshPath:match("wp_miquella_sa%.mesh"), "switch axe: no model swap")
texts = {}; onDraw()
check(anyText("^Morph joints found: 8/8") and anyText("^Mode: _Mode = 1 %(sword look, morph 1%.00%)"),
      "switch axe: menu shows the morph")
extract._Mode = 0
frames(40, 1 / 60)
check(dissolve("MiquellaAxeBlade") == 1 and dissolve("MiquellaSwordBlade") == 0 and jointAt("MQ_Blade0", { -0.095, 0.0, 1.178 })
      and jointAt("MQ_SwordTip", { 0.0475, 0.016, 1.216 }), "switch axe: back to the axe")
weaponMesh = newMesh("Art/Model/Item/it09/00/0002/it0900_0002_0.mesh")
weaponGO = newGO("Wp09", 11001, weaponMesh, nil)
local cbShield = newMesh("Art/Model/Item/it09/00/0002/it0900_0002_1.mesh")
subGO = newGO("Wp09_Shield", 11002, cbShield, nil)
frames(20, 1 / 60)
comboPick = { slot = "Weapon", name = "ChargeBlade" }; onDraw()
frames(40, 1 / 60)
check(weaponMesh.meshPath:match("wp_miquella_cb%.mesh") and cbShield.meshPath:match("wp_miquella_cb_shield"), "charge blade: sword and shield")
check(subGO.draw == true and dissolve("MiquellaRimGlow") == 0 and not visible("MiquellaEdgeBlade"),
      "charge blade: shield shown in sword mode, the axe head hidden")
frames(40, 1 / 60)
sets = weaponMesh.setCount
extract._Mode = 1
frames(9, 1 / 60)                   -- 0.15 s of 0.5 s
local shieldA = cbShield.floats["MiquellaGlow.2"] or 1
check(shieldA > 0 and shieldA < 1 and subGO.draw == true and dissolve("MiquellaRimGlow") == 1,
      string.format("charge blade: mid-morph the shield fades (%.2f) as the axe's rim appears", shieldA))
frames(30, 1 / 60)
check(subGO.draw == false and (cbShield.floats["MiquellaGlow.2"] or 1) == 0, "charge blade: shield gone in axe mode")
check(dissolve("MiquellaEdgeBlade") == 1 and dissolve("MiquellaAxeGlow") == 1 and jointAt("MQ_Phial0", { 0.126, 0.0, 0.952 })
      and jointAt("MQ_SwordTip", { 0.0, 0.0, 1.232 }), "charge blade: axe mode (head shown, phials on its back, sword shortened)")
check(weaponMesh.setCount == sets, "charge blade: no model swap")
extract._Mode = 0
frames(40, 1 / 60)
check(weaponMesh.meshPath:match("wp_miquella_cb%.mesh") and subGO.draw == true and cbShield.floats["MiquellaGlow.2"] == 1
      and dissolve("MiquellaRimGlow") == 0, "charge blade: back to sword and shield")
-- Charge blade phials: the shield's rim phials count the loaded phials; the sword's ring is its
-- energy (bright gold when full); in axe mode the axe's phials count them; shield enhanced
-- lights the shield. Switch axe: the phials are the switch gauge, amped lights the blade.
local function dotOf(m, i) return (m.floats["MiquellaGauge" .. i .. ".1"] or 0) / (1.2 * glow) end
extract = { _Mode = 0, _ActionEnterBinNum = 3, _SwordEnergyState = 2, _ShieldEnhancedTimer = 0 }
frames(200, 1 / 60)                  -- fields missing earlier are looked for again after 3 s
extract._SwordEnergyState = 1
frames(60, 1 / 60)
check(dotOf(cbShield, 3) > 0.99 and dotOf(cbShield, 4) < 0.3, string.format("charge blade: shield phials show 3 loaded (%.2f %.2f)", dotOf(cbShield, 3), dotOf(cbShield, 4)))
check(dotOf(weaponMesh, 2) > 0.99 and dotOf(weaponMesh, 4) < 0.3, string.format("charge blade: sword ring shows its energy (%.2f %.2f)", dotOf(weaponMesh, 2), dotOf(weaponMesh, 4)))
extract._SwordEnergyState = 2
frames(60, 1 / 60)
check(dotOf(weaponMesh, 5) > 1.7, "charge blade: full energy burns bright gold")
extract._ShieldEnhancedTimer = 30
frames(40, 1 / 60)
check((cbShield.floats["MiquellaGlow.1"] or 0) / (1.2 * glow) > 1.7, "charge blade: shield enhanced lights the shield")
extract._Mode, extract._ActionEnterBinNum = 1, 5
frames(60, 1 / 60)
check(dissolve("MiquellaEdgeBlade") == 1 and dotOf(weaponMesh, 5) > 0.99, "charge blade: axe phials show the loaded phials")
extract._ActionEnterBinNum = 1
frames(60, 1 / 60)
check(dotOf(weaponMesh, 1) > 0.99 and dotOf(weaponMesh, 2) < 0.3, "charge blade: using phials dims them")
-- Savage axe (user's pick "A"): the saw teeth's three sets lit one at a time, in turn.
local saws = { "MiquellaSawAGlow", "MiquellaSawBGlow", "MiquellaSawCGlow" }
local function sawLit()
  local lit = {}
  for i, n in ipairs(saws) do if dissolve(n) > 0.5 then lit[#lit + 1] = i end end
  return lit
end
check(#sawLit() == 0, "charge blade: no saw teeth without the axe enhanced")
extract._AxeEnhancedTimer = 40
frames(210, 1 / 60)                  -- a field not found is looked for again after 3 s
local seen, single = {}, true
for _ = 1, 20 do
  frames(1, 1 / 60)
  local lit = sawLit()
  if #lit ~= 1 then single = false else seen[lit[1]] = true end
end
check(single and seen[1] and seen[2] and seen[3], "charge blade: enhanced axe runs its saw teeth (one set at a time, all in turn)")
extract._Mode = 0
frames(90, 1 / 60)
check(#sawLit() == 0, "charge blade: the saw teeth go with the axe")
extract._AxeEnhancedTimer = 0
extract._Mode = 0
weaponMesh = newMesh("Art/Model/Item/it08/00/0001/it0800_0001_0.mesh")
weaponGO = newGO("Wp08b", 12001, weaponMesh, nil)
subGO = nil
extract = { _Mode = 0, _SlashGauge = 100, _SwordAwakeTimer = 0 }
frames(200, 1 / 60)
extract._SlashGauge = 60
frames(60, 1 / 60)
check(dotOf(weaponMesh, 3) > 0.99 and dotOf(weaponMesh, 4) < 0.3, string.format("switch axe: phials show the switch gauge (%.2f %.2f)", dotOf(weaponMesh, 3), dotOf(weaponMesh, 4)))
extract._SwordAwakeTimer = 30
frames(40, 1 / 60)
check((weaponMesh.floats["MiquellaSwordBlade.1"] or 0) / (1.2 * glow) > 1.7, "switch axe: amped lights the blade bright gold")
texts = {}; onDraw()
local sawG = false
for _, t in ipairs(texts) do if t:match("^Gauges: _SlashGauge") then sawG = true end end
check(sawG, "switch axe: menu shows the gauge fields")
-- Long sword: spirit levels pale gold -> gold -> bright gold -> white, the band from yellow on.
weaponMesh = newMesh("Art/Model/Item/it03/00/0002/it0300_0002_0.mesh")
weaponGO = newGO("Wp03b", 13001, weaponMesh, nil)
subGO = nil
extract = { ["<AuraLevel>k__BackingField"] = 1 }      -- the game counts 1 (none) .. 4 (red)
frames(200, 1 / 60)
comboPick = { slot = "Weapon", name = "LongSword" }; onDraw()
frames(40, 1 / 60)
check(weaponMesh.meshPath:match("MiquellaLight/LongSword"), "long sword: model swapped")
local function ls(mat) return (weaponMesh.floats[mat .. ".1"] or 0) / (1.2 * glow) end
check(math.abs(ls("MiquellaBlade1") - 0.8) < 0.01 and math.abs(ls("MiquellaBlade8") - 0.8) < 0.01,
      string.format("long sword: no spirit = pale gold (%.2f)", ls("MiquellaBlade1")))
extract["<AuraLevel>k__BackingField"] = 3
frames(60, 1 / 60)
local function bandRange(prefix)
  local lo, hi = math.huge, 0
  for k = 1, 8 do local v = ls((prefix or "MiquellaBand") .. k); lo, hi = math.min(lo, v), math.max(hi, v) end
  return lo, hi
end
local blo, bhi = bandRange()
for _ = 1, 48 do                     -- (wait for the pulse to be on the blade: it runs once in 0.8 s)
  if bhi > 1.8 * 2.5 then break end
  frames(1, 1 / 60)
  blo, bhi = bandRange()
end
check(bhi > 1.8 * 2.5 and blo < 1.8,
      string.format("long sword: yellow = bright gold, the band runs along the pieces (%.2f .. %.2f)", blo, bhi))
local dlo, dhi = bandRange("MiquellaBlade")
check(math.abs(dlo - blo) < 1e-6 and math.abs(dhi - bhi) < 1e-6 and dlo < 1.8 * 0.8,
      string.format("long sword: the band runs through the blade's pieces too, the rest dimmed (%.2f .. %.2f)", dlo, dhi))
local hiColor = nil
for k = 1, 8 do if ls("MiquellaBlade" .. k) == dhi then hiColor = weaponMesh.colors["MiquellaBlade" .. k] end end
check(hiColor and hiColor.z > 0.5, "long sword: the pulse is white")
local firstHi = nil
for k = 1, 8 do if ls("MiquellaBand" .. k) == bhi then firstHi = k end end
frames(12, 1 / 60)
local nowHi = nil
blo, bhi = bandRange()
for k = 1, 8 do if ls("MiquellaBand" .. k) == bhi then nowHi = k end end
check(firstHi and nowHi and nowHi ~= firstHi, string.format("long sword: the band moves (piece %s -> %s)", tostring(firstHi), tostring(nowHi)))
extract["<AuraLevel>k__BackingField"] = 4
frames(60, 1 / 60)
local lc = weaponMesh.colors["MiquellaBlade1"]
check(lc and lc.z > 0.8, "long sword: red = white light")
check(grown(24) == 0, "long sword: the spirit gauge's colour no longer brings the strands")
extract["<AuraLevel>k__BackingField"] = 2
frames(90, 1 / 60)
blo, bhi = bandRange()
dlo, dhi = bandRange("MiquellaBlade")
check(math.abs(dlo - 1.0) < 0.01 and dhi - dlo < 0.01 and bhi - blo < 0.01, "long sword: white = gold, no band")
-- The Spirit Charge before a Spirit Roundslash (user, 2026-10-03): the strands grow with it (levels
-- at 0.8 / 1.6 / 2.9 s of _KijinChargeTimer), stay through the roundslash, fade after it.
extract._KijinChargeLv = 0
hunterAction = "app.Wp03Action.cKijinSlash1"
chargeT0 = fakeTime                  -- the timer may run on a held Spirit Blade: nothing grows there
frames(30, 1 / 60)
check(grown(24) == 0, "long sword: no strands outside the Spirit Charge")
hunterAction, chargeT0 = "app.Wp03Action.cKijinCharge", fakeTime
frames(24, 1 / 60)                   -- 0.4 s
local l1 = grown(24)
check(l1 >= 3 and l1 <= 5, string.format("long sword: the Spirit Charge grows the strands (%d of 24)", l1))
frames(2, 1 / 60)                    -- 0.43 s: strand 1's bones 9 and 10 at the front
check(jp("MQ_G1_9") and jp("MQ_G1_10") and jp("MQ_G1_9").z == jp("MQ_G1_10").z and jp("MQ_G1_10").z < 0.9,
      "long sword: the strands draw out on their bones")
frames(24, 1 / 60)
extract._KijinChargeLv = 1
frames(48, 1 / 60)                   -- 1.6 s
extract._KijinChargeLv = 2
frames(78, 1 / 60)                   -- 2.9 s
extract._KijinChargeLv = 3
frames(12, 1 / 60)
check(grown(24) == 24, "long sword: full Spirit Charge wraps the whole blade")
check(jp("MQ_G1_48") and math.abs(jp("MQ_G1_48").z - 1.9883) < 2e-3, "long sword: its strands' bones all back in place at full")
local lsc = weaponMesh.colors["MiquellaGrow24"]
check(lsc and lsc.z < 0.3 and weaponMesh.floats["MiquellaGrow24.1"] / (1.2 * glow) > 3.0, "long sword: bright gold strands")
hunterAction, chargeT0, extract._KijinChargeLv = "app.Wp03Action.cKijinSlashRound", nil, 0
frames(40, 1 / 60)
check(grown(24) == 24, "long sword: they stay through the Spirit Roundslash")
hunterAction = "app.Wp03Action.cIdle"
frames(30, 1 / 60)
check(grown(24) == 0 and select(2, grown(24)) == 0, "long sword: and fade after it")
hunterAction = nil
-- Lance (user's pick "A, the spiral drill"): the strands' bone turns about the lance's axis
-- while charging, faster each level, and stays on its pivot.
weaponMesh = newMesh("Art/Model/Item/it06/00/0001/it0600_0001_0.mesh")
weaponGO = newGO("Wp06", 14001, weaponMesh, nil)
subGO = nil
extract = { _FinishChargeLevel = 0 }
frames(200, 1 / 60)
comboPick = { slot = "Weapon", name = "Lance" }; onDraw()
frames(40, 1 / 60)
check(weaponMesh.meshPath:match("MiquellaLight/Lance/wp_miquella_ln%.mesh"), "lance: model swapped")
local function drillAngle()
  local q = weaponGO.tf.joints["MQ_Drill"] and weaponGO.tf.joints["MQ_Drill"].lr
  return q and math.deg(2 * math.atan(q.z, q.w)) % 360 or nil
end
local a0 = drillAngle()
frames(30, 1 / 60)
check(a0 ~= nil and math.abs(drillAngle() - a0) < 1e-6 and grown(24) == 0, "lance: the drill rests without a charge")
-- The strands grow with _FinishChargeTimer (levels at 0.8 / 2.0 / 3.6 s), the drill turning faster.
chargeT0 = fakeTime
frames(24, 1 / 60)                   -- 0.4 s
local n1 = grown(24)
check(n1 >= 3 and n1 <= 5, string.format("lance: the drill grows from the start of the charge (%d of 24)", n1))
frames(2, 1 / 60)                    -- 0.43 s: the front in band 5: its end bone (MQ_Grow10) on the axis, moved down
local g5 = weaponGO.tf.joints["MQ_Grow10"]
check(g5 and g5.lp and g5.lr and math.abs(g5.lp.x) < 1e-6 and g5.lp.z < -0.6205 - 0.01 and math.abs(g5.lr.z) > 0.01,
      "lance: the growing band's bone is pulled to the front and turned back along the drill")
frames(24, 1 / 60)
extract._FinishChargeLevel = 1
frames(30, 1 / 60)
local a1 = drillAngle(); frames(30, 1 / 60); local d1 = (drillAngle() - a1) % 360
frames(12, 1 / 60)
extract._FinishChargeLevel = 2
frames(96, 1 / 60)
extract._FinishChargeLevel = 3
frames(30, 1 / 60)
local a3 = drillAngle(); frames(30, 1 / 60); local d3 = (drillAngle() - a3) % 360
check(d1 > 20 and d3 > d1 * 2, string.format("lance: the drill turns while charging, faster at full (%.0f -> %.0f deg in 0.5 s)", d1, d3))
local dj = weaponGO.tf.joints["MQ_Drill"]
check(dj.lp and math.abs(dj.lp.z - 1.751) < 1e-3 and math.abs(dj.lp.x) < 1e-6, "lance: the drill stays on its pivot")
check(grown(24) == 24 and weaponMesh.matEnabled["MiquellaCharge3"] == true and weaponMesh.matEnabled["MiquellaChargeTip"] == true,
      "lance: full charge: every strand, the spin trails and the point's blade")
extract._FinishChargeLevel, chargeT0 = 0, nil
frames(30, 1 / 60)
check(grown(24) == 0, "lance: the strands go after the thrust")
print("ALL PASS")
