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
  function go:call(sig, t) return self.comps[t.name] end
  go.scale = 1.0
  function go:get_Transform() local g = self; return { set_LocalScale = function(_, v) g.scale = v.x end } end
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
local preRender
re = { on_frame = function(f) onFrame = f end, on_draw_ui = function(f) onDraw = f end,
       on_pre_application_entry = function(name, f) if name == "BeginRendering" then preRender = f end end }
Vector3f = { new = function(x, y, z) return { x = x, y = y, z = z } end }
local comboAnswer = nil
local sliderAnswer = {}
local texts = {}
imgui = {
  tree_node = function() return true end, tree_pop = function() end, same_line = function() end,
  checkbox = function(l, v) return false, v end, button = function() return false end,
  text = function(t) texts[#texts + 1] = t end, text_colored = function(t) texts[#texts + 1] = "!! " .. t end,
  combo = function(label, idx, list)
    if comboAnswer and label:match("##Weapon$") then local a = comboAnswer; comboAnswer = nil; return true, a end
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
  failPaths["Art/Model/MiquellaLight/DualBlades/wp_miquella_db.mesh"] = true
end
dofile(arg[1])
local function frames(n, dt)
  for _ = 1, n do
    fakeTime = fakeTime + (dt or 0)
    onFrame()
    weaponGO.scale = 1.0          -- the game resets the weapon transform every frame
    if preRender then preRender() end
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
check(weaponMesh.meshPath == "Art/Model/MiquellaLight/DualBlades/wp_miquella_db.mesh", "main weapon model swapped")
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
-- Glow and Size sliders.
check(math.abs((weaponMesh.floats["MiquellaBlade.1"] or 0) - 1.2) < 1e-6, "glow at default intensity on the blade")
sliderAnswer.Glow = 2.0; sliderAnswer.Size = 1.3; onDraw()
frames(20)
check(math.abs(weaponMesh.floats["MiquellaBlade.1"] - 2.4) < 1e-6 and math.abs(weaponMesh.floats["MiquellaGlow.1"] - 2.4) < 1e-6, "glow slider scales blade and droplet")
check(weaponMesh.floats["MiquellaIvory.1"] == nil, "ivory not made to glow")
check(math.abs(weaponGO.scale - 1.3) < 1e-6, "size slider scales the weapon, every frame before rendering")
check(math.abs(subGO.scale - 1.0) < 1e-6, "unassigned sub weapon keeps its size")
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
-- Un-assign: back to the original.
comboAnswer = 1; onDraw()
frames(20)
check(weaponMesh.meshPath == "Art/Model/Item/it02/00/0002/it0200_0002_1.mesh", "original model restored")
check(weaponMesh.mdfPath == "Art/Model/Item/it02/00/0002/it0200_0002_1.mdf2", "original material restored")
check(weaponChain.path == "Art/Model/Item/it02/00/0002/it0200_0002_1.chain2", "original physics restored")
check(weaponGO.draw == true, "visible again")
check(math.abs(weaponGO.scale - 1.0) < 1e-6, "size reset on the original")
print("ALL PASS")
