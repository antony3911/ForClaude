-- Minimal stand-ins for the REFramework API, enough to drive MiquellaLight_Weapons.lua.
local failPaths = {}
local function resource(path) return { ToString = function() return "Resource[" .. path .. "]" end } end
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
      return { "MiquellaGauge1", "MiquellaGauge2", "MiquellaGauge3", "MiquellaGlow", "MiquellaIvory", "MiquellaTemper" }
    end
    if self.mdfPath:match("wp_miquella_gl%.") then
      return { "MiquellaBlade", "MiquellaCore", "MiquellaGlow", "MiquellaIvory" }
    end
    if self.mdfPath:match("wp_miquella_ig%.") then
      return { "MiquellaBlade", "MiquellaExtractOrange", "MiquellaExtractRed", "MiquellaExtractWhite", "MiquellaGlow", "MiquellaIvory", "MiquellaTemper" }
    end
    if self.mdfPath:match("wp_miquella_hm%.") then
      return { "MiquellaCharge1", "MiquellaCharge2", "MiquellaCharge3", "MiquellaGlow", "MiquellaIvory" }
    end
    if self.mdfPath:match("wp_miquella_gs") then
      return { "MiquellaBlade", "MiquellaGlow", "MiquellaIvory", "MiquellaTemper" }
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
        function j:call(jm, v) if jm == "set_LocalPosition" then self.lp = v elseif jm == "set_LocalRotation" then self.lr = v end end
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
local extract = {}               -- field -> value (insect glaive timers)
local insectGO = nil             -- the kinsect GameObject behind _Insect
function chr:call(m)
  if m == "get_WeaponHandling" then
    return { get_field = function(_, n)
      if n == "_KijinExtern" then return kijin end
      if n == "_ChargeLv" then return chargeLv end
      if n == "_RapidAmmoGauge" then return rapidGauge end
      if n == "_IsRapidMode" then return rapidMode end
      if n == "_IsCharge" then return bowDraw end
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
json = { load_file = function() return nil end, dump_file = function(p, t) savedCfg = t end }

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
check(texts[2] and texts[2]:match("it0200_0002_1%.mesh"), "menu shows the original main weapon path")
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
check(texts[2] and texts[2]:match("it0000_0000_0%.mesh"), "great sword: menu shows its model path")
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
chargeLv = 3
frames(30, 1 / 60)
local c = weaponMesh.colors["MiquellaBlade"]
check(c and c.z > 0.8, "great sword: level 3 turns the blade white")
check(weaponMesh.floats["MiquellaTemper.3"] == 1.0, "great sword: level 3 runs the band on the temper line")
local band1 = weaponMesh.floats["MiquellaTemper.4"]
frames(10, 1 / 60)
check(weaponMesh.floats["MiquellaTemper.4"] ~= band1, "great sword: the band moves")
chargeLv = 0
frames(90, 1 / 60)                   -- 0.35 s per level on the way down
check(math.abs(weaponMesh.floats["MiquellaBlade.1"] - 1.2 * glow) < 1e-6 and weaponMesh.floats["MiquellaTemper.3"] == 0.0,
      "great sword: releasing the charge fades back")
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
comboPick = { slot = "SubWeapon", name = "SwordShield_ShieldB" }; onDraw()
frames(30, 1 / 60)
check(shieldMesh.meshPath == "Art/Model/MiquellaLight/SwordShield/wp_miquella_sns_shield_bubble.mesh", "sword & shield: film B picked for every shield")
check(savedCfg.assignShield.it01 == "SwordShield_ShieldB", "sword & shield: shield choice saved per type")
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
bowDraw, chargeLv = true, 1
frames(60, 1 / 60)
local z1 = front.lp.z
check(z1 < REST - 0.2 and z1 > PACKED + 0.05, string.format("bow: drawing packs the rings part way (%.3f)", z1))
check(math.abs(gauge(1) - 1.8) < 0.05 and gauge(3) < 0.4, string.format("bow: level 1 lights the first pair (%.2f %.2f %.2f)", gauge(1), gauge(2), gauge(3)))
chargeLv = 3
frames(60, 1 / 60)
check(math.abs(front.lp.z - PACKED) < 0.01, string.format("bow: level 3 packs them tight (%.3f)", front.lp.z))
check(gauge(3) > 3.3, "bow: level 3 lights every ring")
local col = weaponMesh.colors["MiquellaGauge3"]
check(col and col.z > 0.5 and col.y > 0.8, "bow: level 3 turns them white gold")
texts = {}; onDraw()
local sawDraw = false
for _, t in ipairs(texts) do if t:match("^Draw: _IsCharge") then sawDraw = true end end
check(sawDraw, "bow: menu shows the draw field")
bowDraw, chargeLv = false, 0
local far = 0
for _ = 1, 90 do frames(1, 1 / 60); far = math.max(far, front.lp.z) end
check(far > REST + 0.03, string.format("bow: loosing springs the rings past their places (%.3f)", far))
frames(120, 1 / 60)
check(math.abs(front.lp.z - REST) < 0.01, "bow: and they settle back")
check(math.abs(gauge(3) - 1) < 1e-3, "bow: glow back to normal")
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
extract = { _ExtractTimerRed = 0, _ExtractTimerWhite = 0, _ExtractTimerOrange = 0, _ExtractTimerTripple = 0 }
chargeLv = 0
frames(20, 1 / 60)
comboPick = { slot = "Weapon", name = "InsectGlaive" }; onDraw()
frames(40, 1 / 60)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/InsectGlaive/wp_miquella_ig.mesh", "insect glaive: model swapped")
check(kinsectMesh.meshPath == "Art/Model/MiquellaLight/Kinsect/wp_miquella_kinsect.mesh", "insect glaive: kinsect takes the swallowtail")
local function orb(n) return weaponMesh.matEnabled["MiquellaExtract" .. n] == true end
check(not orb("Red") and not orb("White") and not orb("Orange"), "insect glaive: no orbs without extracts")
extract._ExtractTimerRed = 30
frames(30, 1 / 60)
check(orb("Red") and not orb("White"), "insect glaive: red extract shows the rot orb")
local o = weaponGO.tf.joints["MQ_OrbRed"]
local p1 = { o.lp.x, o.lp.y }
frames(30, 1 / 60)
local moved = math.sqrt((o.lp.x - p1[1]) ^ 2 + (o.lp.y - p1[2]) ^ 2)
local r = math.sqrt(o.lp.x ^ 2 + o.lp.y ^ 2)
check(moved > 0.05 and math.abs(r - 0.1408) < 1e-3, string.format("insect glaive: the orb circles the blade (moved %.3f, r %.4f)", moved, r))
extract._ExtractTimerWhite, extract._ExtractTimerOrange, extract._ExtractTimerTripple = 30, 30, 30
frames(40, 1 / 60)
check(orb("White") and orb("Orange"), "insect glaive: all three orbs")
check(weaponMesh.floats["MiquellaBlade.1"] / (1.2 * glow) > 1.7, "insect glaive: three extracts brighten the blade")
extract._ExtractTimerTripple = 0
chargeLv = 3
frames(60, 1 / 60)
local ic = weaponMesh.colors["MiquellaBlade"]
check(ic and ic.y > 0.8 and ic.z > 0.5 and ic.z < 0.7, "insect glaive: level 3 charge is white gold")
chargeLv = 0
extract._ExtractTimerRed = 0
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
extract = { _IsReload = false, _IsChargeShot = false, _RyuugekiChargeTimer = 0 }
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
extract._IsChargeShot = true
frames(20, 1 / 60)
local z1 = top.lp.z
frames(70, 1 / 60)
local z3 = top.lp.z
check(z3 < z1 - 0.05, string.format("gunlance: charged shelling winds tighter per level (%.3f -> %.3f)", z1, z3))
local gc = weaponMesh.colors["MiquellaCore"]
check(gc and gc.y > 0.8 and gc.z > 0.5, "gunlance: full charge is white gold")
extract._IsChargeShot = false
local far = 0
for _ = 1, 60 do frames(1, 1 / 60); far = math.max(far, top.lp.z) end
check(far > REST_TOP + 0.02, string.format("gunlance: the shot lets the spring fly back past its place (%.3f)", far))
extract._RyuugekiChargeTimer = 1.0
frames(60, 1 / 60)
check(math.abs(top.lp.z - (REST_TOP - 0.636)) < 0.01, "gunlance: Wyvern's Fire winds it all the way")
extract._RyuugekiChargeTimer = 0
frames(120, 1 / 60)
check(math.abs(top.lp.z - REST_TOP) < 0.01, "gunlance: back after the blast")
texts = {}; onDraw()
local sawGl = false
for _, t in ipairs(texts) do if t:match("^Gunlance: _IsReload") then sawGl = true end end
check(sawGl, "gunlance: menu shows the fields")
print("ALL PASS")
