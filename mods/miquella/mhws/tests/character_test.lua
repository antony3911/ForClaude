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
Vector4f = { new = function(x, y, z, w) return { x = x, y = y, z = z, w = w } end }
Quaternion = { new = function(x, y, z, w) return { x = x, y = y, z = z, w = w } end }

local function resource(path) return { ToString = function() return "Resource[" .. path .. "]" end } end

-- The hunter's own model objects (children of its transform), with their meshes.
local function outfitGO(path)
  local g = { drawSelf = true, path = path }
  local mesh = { getMesh = function() return resource(path) end }
  function g:call(m, a)
    if m == "set_DrawSelf" then self.drawSelf = a
    elseif m == "getComponent(System.Type)" and a.name == "via.render.Mesh" then return mesh end
  end
  return g
end
local innerwear = outfitGO("Art/Model/Character/ch02/002/000/2/ch02_002_0002.mesh")
local armorLeg = outfitGO("Art/Model/Character/ch03/021/001/4/ch03_021_0014.mesh")
local face = outfitGO("Art/Model/Character/ch00/000/0000/ch00_000_0000.mesh")
local hair = outfitGO("Art/Model/Character/ch01/000/0/001/ch01_000_0001.mesh")
local weapon = outfitGO("Art/Model/Item/it02/00/0002/it0200_0002_0.mesh")
local function childXf(go, child, nxt)
  return { call = function(_, m)
    if m == "get_GameObject" then return go elseif m == "get_Child" then return child elseif m == "get_Next" then return nxt end
  end }
end
-- hunter -> [innerwear -> [armorLeg], face, hair, weapon]
local xWeapon = childXf(weapon)
local xHair = childXf(hair, nil, xWeapon)
local xFace = childXf(face, nil, xHair)
local xInner = childXf(innerwear, childXf(armorLeg), xFace)

-- The hunter: its transform has a Head joint 1.57 m up, turned 90 degrees about Y.
local s = math.sqrt(0.5)
local headJoint = { pos = { x = 2, y = 1.57, z = 5 }, rot = { x = 0, y = s, z = 0, w = s } }
function headJoint:call(m) if m == "get_Position" then return self.pos elseif m == "get_Rotation" then return self.rot end end
local hunterXf = { addr = 77 }
function hunterXf:get_address() return self.addr end
function hunterXf:call(m, a)
  if m == "getJointByName" and a == "Head" then return headJoint end
  if m == "get_Child" then return xInner end
end
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
    elseif m == "set_SameJointsConstraint" then self.sameJoints = a
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
      local mesh = { floats = {}, float4 = {}, enabled = {} }
      function mesh:add_ref() return self end
      function mesh:call() end
      function mesh:setMesh(r) self.meshRes = r end
      function mesh:set_Material(r) self.mdfRes = r end
      function mesh:get_MaterialNum() return self.mdfRes and 2 or 0 end
      local function body(m) return m.mdfRes and m.mdfRes.path:find("mq_body", 1, true) end
      function mesh:getMaterialName(i)
        return (body(self) and { "MiquellaCloth", "MiquellaSkin" } or { "MiquellaGlow", "MiquellaHalo" })[i + 1]
      end
      function mesh:getMaterialVariableNum() return 2 end
      function mesh:getMaterialVariableName(i, j)
        return (body(self) and { "ColorParam", "Emissive_Intensity" } or { "Dissolve", "Emissive_Intensity" })[j + 1]
      end
      function mesh:setMaterialFloat4(i, j, v) self.float4[i .. "." .. j] = v end
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
local function made(name)
  for i = #created, 1, -1 do if created[i].name == name then return created[i] end end
end
local function count(name)
  local n = 0
  for _, g in ipairs(created) do if g.name == name then n = n + 1 end end
  return n
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
local sliderAnswer, comboAnswer, checkAnswer, texts = {}, {}, {}, {}
imgui = {
  tree_node = function() return true end, tree_pop = function() end,
  checkbox = function(label, v)
    if checkAnswer[label] ~= nil then local a = checkAnswer[label]; checkAnswer[label] = nil; return true, a end
    return false, v
  end,
  slider_float = function(label, v)
    if sliderAnswer[label] then local a = sliderAnswer[label]; sliderAnswer[label] = nil; return true, a end
    return false, v
  end,
  combo = function(label, v)
    if comboAnswer[label] then local a = comboAnswer[label]; comboAnswer[label] = nil; return true, a end
    return false, v
  end,
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
  -- Circlet
  local go = made("MiquellaLight_Circlet")
  check(go ~= nil and count("MiquellaLight_Circlet") == 1, "makes one circlet object")
  local xf, mesh = go.xf, go.comps["via.render.Mesh"]
  check(mesh and mesh.meshRes and mesh.meshRes.path == "Art/Model/MiquellaLight/Character/mq_circlet.mesh", "circlet: sets our model")
  check(mesh and mesh.floats["1.1"] and math.abs(mesh.floats["1.1"] - 0.8) < 1e-6, "circlet: halo glow at its mdf2 value")
  check(xf.parent == hunterXf and go.drawSelf == true, "circlet: parented to the hunter, shown")
  -- Body
  local body = made("MiquellaLight_Body")
  check(body ~= nil and count("MiquellaLight_Body") == 1, "makes one body object")
  local bmesh = body.comps["via.render.Mesh"]
  check(bmesh.meshRes.path == "Art/Model/MiquellaLight/Character/mq_body_a.mesh"
    and bmesh.mdfRes.path == "Art/Model/MiquellaLight/Character/mq_body.mdf2", "body: shape A with its material")
  check(body.xf.parent == hunterXf and body.xf.sameJoints == true and body.drawSelf == true,
    "body: on the hunter's skeleton (SameJointsConstraint), shown")
  frames(40, 1 / 60)
  check(innerwear.drawSelf == false and armorLeg.drawSelf == false, "body: the hunter's innerwear and armor hidden")
  local tint = bmesh.float4["1.0"]
  check(tint and math.abs(tint.x - 2.9) < 1e-6 and math.abs(tint.y - 2.9) < 1e-6 and bmesh.float4["0.0"] == nil,
        "body: skin tone tint on MiquellaSkin's ColorParam only")
  check(face.drawSelf == true and hair.drawSelf == true and weapon.drawSelf == true, "body: face, hair and weapon stay")
  comboAnswer["Body shape"] = 3; menu(); frames(2, 1 / 60)
  check(bmesh.meshRes.path == "Art/Model/MiquellaLight/Character/mq_body_c.mesh" and count("MiquellaLight_Body") == 1,
    "body: picking shape C swaps the model in place")
  checkAnswer["Hide the hunter's armor and innerwear"] = false; menu(); frames(2, 1 / 60)
  check(innerwear.drawSelf == true and armorLeg.drawSelf == true, "outfit shown again when the option is off")
  checkAnswer["Hide the hunter's armor and innerwear"] = true; menu(); frames(40, 1 / 60)
  checkAnswer["Body"] = false; menu(); frames(2, 1 / 60)
  check(body.drawSelf == false and innerwear.drawSelf == true, "body off: hidden, outfit back")
  checkAnswer["Body"] = true; menu(); frames(40, 1 / 60)
  check(body.drawSelf == true and innerwear.drawSelf == false, "body on again")
  frames(60, 1 / 60)
  if mode == "nojoint" then
    check(xf.followed and math.abs(xf.world.y - 1.57) < 1e-6, "circlet: parent joint failed: follows the Head joint every frame")
  else
    check(xf.joint == "Head" and not xf.followed, "circlet: on the Head joint, no per-frame follow")
  end
  -- Offset in the head's own axes: 2 cm forward (+Z) with the head turned 90 deg about Y -> +X in the world.
  comboAnswer["Attach"] = 3; menu()
  sliderAnswer["Forward / back (cm)"] = 2.0; menu()
  frames(2, 1 / 60)
  check(xf.followed and math.abs(xf.world.x - 2.02) < 1e-6 and math.abs(xf.world.z - 5) < 1e-6,
    string.format("follow mode: offset turns with the head (%.3f, %.3f)", xf.world.x, xf.world.z))
  check(savedCfg and savedCfg.mode == 3 and savedCfg.offset[3] == 2.0 and savedCfg.bodyShape == 3, "menu choices saved")
  sliderAnswer["Glow"] = 2.0; menu()
  check(math.abs(mesh.floats["1.1"] - 1.6) < 1e-6 and math.abs(mesh.floats["0.1"] - 2.4) < 1e-6, "Glow slider scales both materials")
  hunterGO.drawn = false; frames(1, 1 / 60)
  check(go.drawSelf == false and body.drawSelf == false, "hidden with the hunter")
  hunterGO.drawn = true; frames(1, 1 / 60)
  -- An area change destroys our objects: new ones are made.
  go.valid, body.valid = false, false; frames(2, 1 / 60)
  check(count("MiquellaLight_Circlet") == 2 and count("MiquellaLight_Body") == 2
    and made("MiquellaLight_Body").drawSelf == true, "remade after the game destroys them")
  -- Reset scripts: hidden, outfit shown, and the next run takes them over instead of making more.
  onReset()
  check(made("MiquellaLight_Circlet").drawSelf == false and made("MiquellaLight_Body").drawSelf == false
    and innerwear.drawSelf == true, "script reset: ours hidden, the outfit shown")
  sceneObjects["MiquellaLight_Circlet"] = made("MiquellaLight_Circlet")
  sceneObjects["MiquellaLight_Body"] = made("MiquellaLight_Body")
  onFrame, onPre = {}, {}
  dofile(arg[1])
  frames(3, 1 / 60)
  check(#created == 4 and made("MiquellaLight_Body").drawSelf == true, "next run takes over the leftover objects")
end
print(failed == 0 and string.format("ALL PASS (%d)%s", passed, mode and (" " .. mode) or "")
  or string.format("%d FAILED, %d passed", failed, passed))
