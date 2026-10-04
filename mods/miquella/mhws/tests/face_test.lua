-- Offline test for MiquellaLight_Face.lua with a stubbed REFramework API.
-- Usage: python run_lua.py face_test.lua <script>
local passed, failed = 0, 0
local function check(cond, label)
  if cond then passed = passed + 1 else failed = failed + 1; print("FAIL " .. label) end
end
local fakeTime = 0
os.clock = function() return fakeTime end
Vector3f = { new = function(x, y, z) return { x = x, y = y, z = z } end }
Quaternion = { new = function(w, x, y, z) return { x = x, y = y, z = z, w = w } end }   -- glm order

-- Quaternion helpers for the stub (parents: the head turned 90 degrees about Y in the world)
local function qmul(a, b)
  return { w = a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
           x = a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
           y = a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
           z = a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w }
end
local s2 = math.sqrt(0.5)
local HEAD = { x = 0, y = s2, z = 0, w = s2 }        -- the head's world turn
local ID = { x = 0, y = 0, z = 0, w = 1 }

local joints = {}
local function joint(name, lp, lr)
  local j = { name = name, lp = lp, lr = lr or ID, sets = 0 }
  function j:call(m, a)
    if m == "get_LocalPosition" then return { x = self.lp.x, y = self.lp.y, z = self.lp.z }
    elseif m == "get_LocalRotation" then return { x = self.lr.x, y = self.lr.y, z = self.lr.z, w = self.lr.w }
    elseif m == "get_Rotation" then return qmul(HEAD, self.lr)        -- parent = the head's turn
    elseif m == "set_LocalPosition" then self.lp = a; self.sets = self.sets + 1
    elseif m == "set_LocalRotation" then self.lr = a end
  end
  joints[name] = j
  return j
end
local head = { call = function(_, m) if m == "get_Rotation" then return HEAD end end }
for _, side in ipairs({ "L", "R" }) do
  local x = side == "L" and 1 or -1
  joint(side .. "_OuterEyeJ_LOD02", { x = 0.045 * x, y = 0.05, z = 0.08 })
  joint(side .. "_UpEyeLid_B_LOD00", { x = 0.039 * x, y = 0.05, z = 0.09 })
  joint(side .. "_UpEyeLidJ_LOD02", { x = 0.031 * x, y = 0.05, z = 0.07 })
  joint(side .. "_LoEyeLidJ_LOD02", { x = 0.031 * x, y = 0.05, z = 0.07 })
  joint(side .. "_cornerLip_LOD02", { x = 0.024 * x, y = -0.01, z = 0.086 })
  joint(side .. "_EyeBrow_C_LOD01", { x = 0.051 * x, y = 0.07, z = 0.08 })
  joint(side .. "_EyeBrow_B_LOD01", { x = 0.037 * x, y = 0.07, z = 0.09 })
  joint(side .. "_EyeBrow_A_LOD01", { x = 0.018 * x, y = 0.07, z = 0.09 })
end
local faceXf = { addr = 5 }
function faceXf:get_address() return self.addr end
function faceXf:call(m, a)
  if m == "getJointByName" then return a == "Head" and head or joints[a] end
  if m == "get_GameObject" then return self.go end
end
local function meshOf(path)
  return { getMesh = function() return { ToString = function() return "Resource[" .. path .. "]" end } end }
end
local faceGO = { call = function(_, m) if m == "getComponent(System.Type)" then return meshOf("Art/Model/Character/ch00/001/0000/ch00_001_0000.mesh") end end }
faceXf.go = faceGO
local hairXf = { call = function(_, m)
  if m == "get_GameObject" then return { call = function(_, mm) if mm == "getComponent(System.Type)" then return meshOf("Art/Model/Character/ch01/001/0/512/ch01_001_0512.mesh") end end } end
  if m == "get_Next" then return faceXf end
end }
local hunterXf = { call = function(_, m) if m == "get_Child" then return hairXf end end }
local hunterGO = { call = function(_, m) if m == "get_Transform" then return hunterXf end end }
local chr = { call = function(_, m) if m == "get_GameObject" then return hunterGO end end }
local master = { get_Valid = function() return true end, get_Character = function() return chr end }
sdk = { typeof = function(n) return { name = n } end,
        get_managed_singleton = function(n) return n == "app.PlayerManager" and { getMasterPlayer = function() return master end } or nil end }
local onFrame, phases, onUI, onReset = {}, {}, nil, nil
re = { on_frame = function(f) onFrame[#onFrame + 1] = f end,
       on_application_entry = function(name, f) phases[#phases + 1] = f end,
       on_pre_application_entry = function(name, f) phases[#phases + 1] = f end,
       on_draw_ui = function(f) onUI = f end, on_script_reset = function(f) onReset = f end }
local sliderAnswer, comboAnswer, checkAnswer, buttonAnswer, texts = {}, {}, {}, {}, {}
imgui = {
  tree_node = function() return true end, tree_pop = function() end,
  checkbox = function(l, v) if checkAnswer[l] ~= nil then local a = checkAnswer[l]; checkAnswer[l] = nil; return true, a end; return false, v end,
  slider_float = function(l, v) if sliderAnswer[l] then local a = sliderAnswer[l]; sliderAnswer[l] = nil; return true, a end; return false, v end,
  combo = function(l, v) if comboAnswer[l] then local a = comboAnswer[l]; comboAnswer[l] = nil; return true, a end; return false, v end,
  button = function(l) if buttonAnswer[l] then buttonAnswer[l] = nil; return true end; return false end,
  same_line = function() end, text = function(t) texts[#texts + 1] = t end,
}
local dumps = {}
json = { load_file = function() return nil end, dump_file = function(p, t) dumps[p] = t end }
local function frames(n)
  for _ = 1, n do
    fakeTime = fakeTime + 1 / 60
    for _, f in ipairs(onFrame) do f() end
    for _, f in ipairs(phases) do f() end
  end
end
local function menu() texts = {}; onUI(); return table.concat(texts, " | ") end
local function close(a, b, eps) return math.abs(a - b) < (eps or 1e-7) end

dofile(arg[1])
frames(5)
local o = joints.L_OuterEyeJ_LOD02
-- head turned 90 degrees about Y: the head's down (0, -d, -0.27 d) is the parent's own down/back
check(close(o.lp.x, 0.045) and close(o.lp.y, 0.05 - 0.002744) and close(o.lp.z, 0.08 - 0.27 * 0.002744),
  string.format("droop: outer eye corner down and back once (%.5f %.5f %.5f)", o.lp.x, o.lp.y, o.lp.z))
frames(20)
check(close(o.lp.y, 0.05 - 0.002744), "no piling up over many passes")
local r = joints.R_cornerLip_LOD02
local l = joints.L_cornerLip_LOD02
check(l.lp.y > -0.01 + 0.0023 and l.lp.x > 0.024 and r.lp.x < -0.024 and r.lp.y < l.lp.y,
  "smile: the left corner up and out, the right a little (mirrored outward)")
local lid = joints.L_UpEyeLidJ_LOD02
local ang = 2 * math.acos(math.min(1, lid.lr.w)) * 180 / math.pi
check(close(ang, 6.74, 1e-4) and close(lid.lr.x, math.sin(6.74 * math.pi / 360), 1e-6),
  string.format("upper lid turned 6.74 degrees about the head's left axis (%.3f)", ang))
local lo = joints.R_LoEyeLidJ_LOD02
check(lo.lr.x < 0 and close(2 * math.acos(lo.lr.w) * 180 / math.pi, 2.31, 1e-4), "lower lid raised 2.31 degrees (both sides same way)")
-- the game animates a joint: its new pose becomes the base
o.lp = { x = 0.045, y = 0.06, z = 0.08 }
frames(1)
check(close(o.lp.y, 0.06 - 0.002744), "the game's new pose is the base")
local info = menu()
check(info:find("14 / 14 joints", 1, true) ~= nil, "menu: joints found")
check(dumps["MiquellaLight/face_debug.json"] and dumps["MiquellaLight/face_debug.json"].found == 14, "debug written for Claude")
-- smile side to the right
comboAnswer["Smile side"] = 2; menu(); frames(70)
check(r.lp.y > l.lp.y and r.lp.x < -0.024, "smile side right: the right corner up")
check(close(l.lp.y, -0.01 + 0.27 * 0.002355, 1e-6), "the left corner back to the small share")
-- "Save as default" writes the current values; "Defaults" goes back to them
sliderAnswer["Droopy eyes (mm)"] = 3.5; menu()
buttonAnswer["Save as default"] = true; menu()
local fd = dumps["MiquellaLight/Face_defaults.json"]
check(fd and close(fd.droop, 3.5, 1e-6) and close(fd.lids, 6.74, 1e-6) and fd.smileSide == 2, "Save as default: the current values written")
sliderAnswer["Droopy eyes (mm)"] = 1.0; menu()
buttonAnswer["Defaults"] = true; local t = menu()
check(close(dumps["MiquellaLight/Face.json"].droop, 3.5, 1e-6) and t:find("eyes 3.50", 1, true) ~= nil, "Defaults: back to the saved defaults")
-- switched off: the game's pose back
checkAnswer["Enabled"] = false; menu(); frames(3)
check(close(o.lp.y, 0.06) and close(lid.lr.w, 1.0, 1e-9), "off: joints back to the game's pose")
check(dumps["MiquellaLight/Face.json"] and dumps["MiquellaLight/Face.json"].enabled == false, "settings saved")
print(failed == 0 and string.format("ALL PASS (%d)", passed) or string.format("%d FAILED, %d passed", failed, passed))
