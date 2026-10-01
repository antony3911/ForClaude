-- Minimal stand-ins for the REFramework API, enough to drive MiquellaLight_Weapons.lua.
local failPaths = {}
local function resource(path) return { ToString = function() return "Resource[" .. path .. "]" end } end
local function newMesh(meshPath)
  local m = { meshPath = meshPath, mdfPath = meshPath:gsub("%.mesh$", ".mdf2"), enabled = true }
  function m:getMesh() return resource(self.meshPath) end
  function m:get_Material() return resource(self.mdfPath) end
  function m:setMesh(h) self.meshPath = h.path end
  function m:set_Material(h) self.mdfPath = h.path end
  function m:set_Enabled(v) self.enabled = v end
  m.floats = {}
  local function mats(self)
    if self.mdfPath:match("wp_miquella_db") then
      return { "MiquellaBlade", "MiquellaIvory", "MiquellaGrip", "MiquellaGlow", "MiquellaDemon1", "MiquellaDemon2", "MiquellaDemon3" }
    end
    if self.mdfPath:match("wp_miquella_gs") then
      return { "MiquellaBlade", "MiquellaGlow", "MiquellaIvory", "MiquellaTemper" }
    end
    return { "lambert" }
  end
  function m:get_MaterialNum() return #mats(self) end
  function m:getMaterialName(i) return mats(self)[i + 1] end
  function m:getMaterialVariableNum(i) return 3 end
  function m:getMaterialVariableName(i, j) return ({ "Emissive_Color", "Emissive_Intensity", "Dissolve" })[j + 1] end
  function m:setMaterialFloat(i, j, v) self.floats[mats(self)[i + 1] .. "." .. j] = v end
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
function chr:call(m)
  if m == "get_WeaponHandling" then
    return { get_field = function(_, n) if n == "_KijinExtern" then return kijin end end }
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
Quaternion = { new = function(w, x, y, z) return { w = w, x = x, y = y, z = z } end }
local comboAnswer = nil
local sizeAnswer = nil
local sliderAnswer = {}
local texts = {}
imgui = {
  tree_node = function() return true end, tree_pop = function() end, same_line = function() end,
  checkbox = function(l, v) return false, v end, button = function() return false end,
  text = function(t) texts[#texts + 1] = t end, text_colored = function(t) texts[#texts + 1] = "!! " .. t end,
  combo = function(label, idx, list)
    if comboAnswer and label:match("##Weapon$") then local a = comboAnswer; comboAnswer = nil; return true, a end
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
check(savedCfg and savedCfg.assign["Art/Model/Item/it02/00/0002/it0200_0002_1.mesh"] == "DualBlades", "assignment saved")
frames(20)
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/DualBlades/wp_miquella_db_s14.mesh", "main weapon model swapped (default size 1.4)")
check(weaponMesh.mdfPath == "Art/Model/MiquellaLight/DualBlades/wp_miquella_db.mdf2", "main weapon material swapped")
check(weaponChain.path == "Art/Model/Item/it00/99/it0099_0000_0.chain2", "physics chain replaced with the empty one")
check(subMesh.meshPath:match("it0200_0002_0"), "sub weapon untouched (not assigned)")
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
check(subMesh.meshPath:match("it0200_0002_0"), "unassigned sub weapon untouched")
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
-- The game equips a different (unassigned) weapon on the same object while sheathed.
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = false } })
frames(1)
weaponMesh.meshPath = "Art/Model/Item/it02/00/0005/it0200_0005_1.mesh"
frames(20)
check(weaponMesh.meshPath:match("it0200_0005_1") and weaponGO.draw == true, "different weapon left alone and visible")
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
savedCfg.swappedFrom = nil
weaponMesh.matEnabled = {}
dofile(arg[1])
hookPre({ nil, { ToString = function() return "MasterPlayer" end, _IsWeaponOn = true } })
frames(20)
kijin = 1
frames(10, 0.05)
check(visible("MiquellaDemon3"), "older config: the swapped weapon is still picked up after a reload")
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
check(savedCfg.assign["Art/Model/Item/it00/00/0000/it0000_0000_0.mesh"] == "GreatSword", "great sword: assignment saved")
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
for _, t in ipairs(texts) do if t:match("^Rings found: 3/3") then sawRings = true end end
check(sawRings, "great sword: menu reports the 3 ring joints")
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
comboAnswer = 1; onDraw()
frames(20)
check(weaponMesh.meshPath == "Art/Model/Item/it00/00/0000/it0000_0000_0.mesh", "great sword: original restored")
print("ALL PASS")
