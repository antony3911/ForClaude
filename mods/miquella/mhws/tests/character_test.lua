-- Offline test for MiquellaLight_Character.lua with a stubbed REFramework API.
-- Usage: python run_lua.py character_test.lua <script> [nojoint | nocreate | missing]
local mode = arg[2]
local passed, failed = 0, 0
local function check(cond, label)
  if cond then passed = passed + 1 else failed = failed + 1; print("FAIL " .. label) end
end

local fakeTime = 0
os.clock = function() return fakeTime end
Vector3f = { new = function(x, y, z) return { x = x, y = y, z = z } end }
Quaternion = { new = function(x, y, z, w) return { x = x, y = y, z = z, w = w } end }

-- The hunter: its transform has a Head joint 1.57 m up, turned 90 degrees about Y.
local s = math.sqrt(0.5)
local headJoint = { pos = { x = 2, y = 1.57, z = 5 }, rot = { x = 0, y = s, z = 0, w = s } }
function headJoint:call(m) if m == "get_Position" then return self.pos elseif m == "get_Rotation" then return self.rot end end
local hunterXf = { addr = 77 }
function hunterXf:get_address() return self.addr end
function hunterXf:call(m, a) if m == "getJointByName" and a == "Head" then return headJoint end end
local hunterGO = { drawn = true }
function hunterGO:call(m)
  if m == "get_Transform" then return hunterXf elseif m == "get_DrawSelf" then return self.drawn end
end
local chr = {}
function chr:call(m) if m == "get_GameObject" then return hunterGO end end
local master = { get_Valid = function() return true end, get_Character = function() return chr end }
local pm = { getMasterPlayer = function() return master end }

-- Objects the script makes.
local created = {}
local function newObject(name)
  local go = { name = name, valid = true, drawSelf = nil, comps = {} }
  local xf = { lp = { x = 0, y = 0, z = 0 }, world = { x = 0, y = 0, z = 0 } }
  function xf:call(m, a)
    if m == "set_Parent" then self.parent = a
    elseif m == "set_ParentJoint" then
      if mode == "nojoint" then error("no such method") end
      self.joint = a
    elseif m == "set_LocalPosition" then self.lp = a
    elseif m == "set_LocalRotation" then self.lr = a
    elseif m == "set_LocalScale" then self.ls = a
    elseif m == "set_Position" then self.world = a; self.followed = true
    elseif m == "set_Rotation" then self.wr = a
    elseif m == "get_Position" then
      if self.followed then return self.world end
      -- Parented to the Head joint: the joint's position (offset ignored); else the hunter's root.
      if self.parent == hunterXf and self.joint == "Head" then return headJoint.pos end
      return { x = 2, y = 0, z = 5 }
    end
  end
  go.xf = xf
  function go:call(m, a)
    if m == ".ctor" then return
    elseif m == "get_Transform" then return self.xf
    elseif m == "get_Valid" then return self.valid
    elseif m == "set_DrawSelf" then self.drawSelf = a
    elseif m == "getComponent(System.Type)" then return self.comps[a.name]
    elseif m == "createComponent(System.Type)" then
      local mesh = { floats = {}, enabled = {} }
      function mesh:add_ref() return self end
      function mesh:call() end
      function mesh:setMesh(r) self.meshRes = r end
      function mesh:set_Material(r) self.mdfRes = r end
      function mesh:get_MaterialNum() return self.mdfRes and 2 or 0 end
      function mesh:getMaterialName(i) return ({ "MiquellaGlow", "MiquellaHalo" })[i + 1] end
      function mesh:getMaterialVariableNum() return 2 end
      function mesh:getMaterialVariableName(i, j) return ({ "Dissolve", "Emissive_Intensity" })[j + 1] end
      function mesh:setMaterialFloat(i, j, v) self.floats[i .. "." .. j] = v end
      function mesh:setMaterialsEnable(i, v) self.enabled[i] = v end
      function mesh:set_Enabled(v) self.on = v end
      self.comps[a.name] = mesh
      return mesh
    end
  end
  function go:add_ref() return self end
  created[#created + 1] = go
  return go
end

local sceneObjects = {}
local scene = { call = function(_, m, n) if m == "findGameObject(System.String)" then return sceneObjects[n] end end }
local failPaths = {}
if mode == "missing" then failPaths["Art/Model/MiquellaLight/Character/mq_circlet.mesh"] = true end
sdk = {
  typeof = function(n) return { name = n } end,
  get_managed_singleton = function(n) return n == "app.PlayerManager" and pm or nil end,
  get_native_singleton = function(n) return n == "via.SceneManager" and {} or nil end,
  call_native_func = function(_, _, m) if m == "get_CurrentScene()" then return scene end end,
  find_type_definition = function(n)
    if n ~= "via.GameObject" or mode == "nocreate" then return nil end
    return { get_method = function(_, sig)
      if sig == "create(System.String)" then return { call = function(_, _, name) return newObject(name) end } end
    end }
  end,
  create_resource = function(t, path)
    if failPaths[path] then return nil end
    local r = {}
    function r:add_ref() return self end
    function r:create_holder() local h = { path = path }; function h:add_ref() return self end; return h end
    return r
  end,
}
local onFrame, onPre, onUI, onReset = {}, {}, nil, nil
re = {
  on_frame = function(f) onFrame[#onFrame + 1] = f end,
  on_pre_application_entry = function(_, f) onPre[#onPre + 1] = f end,
  on_draw_ui = function(f) onUI = f end,
  on_script_reset = function(f) onReset = f end,
}
local sliderAnswer, comboAnswer, texts = {}, nil, {}
imgui = {
  tree_node = function() return true end, tree_pop = function() end,
  checkbox = function(_, v) return false, v end,
  slider_float = function(label, v)
    if sliderAnswer[label] then local a = sliderAnswer[label]; sliderAnswer[label] = nil; return true, a end
    return false, v
  end,
  combo = function(_, v) if comboAnswer then local a = comboAnswer; comboAnswer = nil; return true, a end; return false, v end,
  button = function() return false end,
  text = function(t) texts[#texts + 1] = t end,
}
local savedCfg
json = { load_file = function() return nil end, dump_file = function(_, t) savedCfg = t end }

local function frames(n, dt)
  for _ = 1, n do
    fakeTime = fakeTime + dt
    for _, f in ipairs(onFrame) do f() end
    for _, f in ipairs(onPre) do f() end
  end
end
local function menu() texts = {}; onUI(); return table.concat(texts, " | ") end

dofile(arg[1])

frames(3, 1 / 60)
if mode == "nocreate" then
  check(#created == 0 and menu():find("could not create", 1, true), "no GameObject.create: says so in the menu")
elseif mode == "missing" then
  check(menu():find("MiquellaLight_Character.pak", 1, true) ~= nil, "missing model: names the pak in the menu")
else
  check(#created == 1 and created[1].name == "MiquellaLight_Circlet", "makes one circlet object")
  local go = created[1]
  local xf, mesh = go.xf, go.comps["via.render.Mesh"]
  check(mesh and mesh.meshRes and mesh.meshRes.path == "Art/Model/MiquellaLight/Character/mq_circlet.mesh", "sets our model")
  check(mesh and mesh.floats["1.1"] and math.abs(mesh.floats["1.1"] - 0.8) < 1e-6, "halo glow at its mdf2 value")
  check(xf.parent == hunterXf, "parented to the hunter")
  check(go.drawSelf == true, "shown")
  frames(90, 1 / 60)
  if mode == "nojoint" then
    check(xf.followed and math.abs(xf.world.y - 1.57) < 1e-6, "parent joint failed: follows the Head joint every frame")
  else
    check(xf.joint == "Head" and not xf.followed, "on the Head joint, no per-frame follow")
  end
  -- Offset in the head's own axes: 2 cm forward (+Z) with the head turned 90 deg about Y -> +X in the world.
  comboAnswer = 3; menu()
  sliderAnswer["Forward / back (cm)"] = 2.0; menu()
  frames(2, 1 / 60)
  check(xf.followed and math.abs(xf.world.x - 2.02) < 1e-6 and math.abs(xf.world.z - 5) < 1e-6,
    string.format("follow mode: offset turns with the head (%.3f, %.3f)", xf.world.x, xf.world.z))
  check(savedCfg and savedCfg.mode == 3 and savedCfg.offset[3] == 2.0, "menu choices saved")
  sliderAnswer["Glow"] = 2.0; menu()
  check(math.abs(mesh.floats["1.1"] - 1.6) < 1e-6 and math.abs(mesh.floats["0.1"] - 2.4) < 1e-6, "Glow slider scales both materials")
  hunterGO.drawn = false; frames(1, 1 / 60)
  check(go.drawSelf == false, "hidden with the hunter")
  hunterGO.drawn = true; frames(1, 1 / 60)
  -- An area change destroys our object: a new one is made.
  go.valid = false; frames(2, 1 / 60)
  check(#created == 2 and created[2].drawSelf == true, "remade after the game destroys it")
  -- Reset scripts: hidden, and the next run takes it over instead of making another.
  onReset()
  check(created[2].drawSelf == false, "hidden on script reset")
  sceneObjects["MiquellaLight_Circlet"] = created[2]
  onFrame, onPre = {}, {}
  dofile(arg[1])
  frames(3, 1 / 60)
  check(#created == 2 and created[2].drawSelf == true, "next run takes over the leftover object")
end
print(failed == 0 and string.format("ALL PASS (%d)%s", passed, mode and (" " .. mode) or "")
  or string.format("%d FAILED, %d passed", failed, passed))
