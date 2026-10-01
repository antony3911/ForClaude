local function resource(path) return { ToString = function() return "Resource[" .. path .. "]" end } end
local function arr(t) return { get_size = function() return #t end, get_elements = function() return t end } end
local function joint(n) return { get_Name = function() return n end } end
local function xform(go, children, joints, parent)
  local x = { go = go, children = children or {}, joints = joints, parent = parent }
  function x:get_GameObject() return self.go end
  function x:get_Joints() if not self.joints then error("no joints") end return arr(self.joints) end
  function x:get_Parent() return self.parent end
  function x:get_ParentJoint() error("method missing") end
  function x:get_Child() return self.children[1] end
  return x
end
local function link_siblings(list)
  for i, c in ipairs(list) do c.get_Next = function() return list[i + 1] end end
end
local function go(name, meshPath, mats)
  local g = { name = name, comps = {} }
  function g:get_Name() return self.name end
  function g:call(sig, t) return self.comps[t.name] end
  function g:get_Transform() return self.xf end
  if meshPath then
    local m = {}
    function m:getMesh() return resource(meshPath) end
    function m:get_Material() return resource((meshPath:gsub("%.mesh$", ".mdf2"))) end
    function m:get_MaterialNum() return #mats end
    function m:getMaterialName(i) return mats[i + 1] end
    function m:getMaterialVariableNum(i) return 2 end
    function m:getMaterialVariableName(i, k) return ({ "Emissive_Intensity", "Dissolve" })[k + 1] end
    g.comps["via.render.Mesh"] = m
  end
  return g
end
local playerGO = go("Player", nil)
local face = go("Player_Face", "Art/Model/Character/ch01/000/1/001/ch01_000_1001.mesh", { "face", "eye" })
local hair = go("Player_Hair", "Art/Model/Character/ch01/000/0/001/ch01_000_0001.mesh", { "hair", "scalp" })
local empty = go("Collision", nil)
local weapon = go("Wp02_R", "Art/Model/Item/it02/00/0002/it0200_0002_1.mesh", { "blade" })
local pxf = xform(playerGO, nil, { joint("root"), joint("Hip"), joint("Spine_0"), joint("R_Hand") })
playerGO.xf = pxf
face.xf = xform(face, nil, nil, pxf); hair.xf = xform(hair, nil, { joint("Hair_00") }, pxf); empty.xf = xform(empty, nil, nil, pxf)
weapon.xf = xform(weapon, nil, { joint("wp_root") }, pxf)
local kids = { face.xf, hair.xf, empty.xf }
link_siblings(kids)
pxf.children = kids
-- Weapon handling object: a charge level (number), a flag (bool), an inherited field, a static
-- field and an object field (the last two must be ignored).
local function field(name, value, static)
  local f = { value = value }
  function f:get_name() return name end
  function f:is_static() return static or false end
  function f:get_data(obj) return self.value end
  return f
end
local chargeF, demonF, baseF = field("_ChargeLv", 0), field("_IsDemon", false), field("_Timer", 1.5)
local baseType = { get_fields = function() return { baseF, field("_Owner", {}) } end, get_parent_type = function() return nil end }
local handlingType = { get_fields = function() return { chargeF, demonF, field("Instance", 3, true) } end,
  get_parent_type = function() return baseType end, get_full_name = function() return "app.cHunterWp00Handling" end }
local handling = { get_type_definition = function() return handlingType end }
local chr = {
  get_IsFemale = function() return false end,
  call = function(self, m)
    if m == "get_Weapon" then return { get_GameObject = function() return weapon end } end
    if m == "get_WeaponHandling" then return handling end
    return nil
  end,
  getParts = function(self, i) if i == 1 then return go("ch02_002_0002", "Art/Model/Character/ch02/002/000/2/ch02_002_0002.mesh", { "body" }) end return nil end,
}
local master = { get_Valid = function() return true end, get_Character = function() return chr end, get_Object = function() return playerGO end }
sdk = { typeof = function(n) return { name = n } end,
        get_managed_singleton = function() return { getMasterPlayer = function() return master end } end }
local onDraw
local onFrame
re = { on_draw_ui = function(f) onDraw = f end, on_frame = function(f) onFrame = f end }
local press = {}
local out = {}
imgui = { tree_node = function(l) out[#out + 1] = l; return true end, tree_pop = function() end, same_line = function() end,
  button = function(l) return press[l] end, text = function(t) out[#out + 1] = t end,
  text_colored = function(t) out[#out + 1] = t end, checkbox = function(l, v) return false, true end }
local dumped
json = { dump_file = function(p, t) dumped = { p, t } end, load_file = function() end }
dofile(arg[1])
local function check(c, m) print((c and "PASS " or "FAIL ") .. m); if not c then os.exit(1) end end
onDraw()
press["Scan hunter"] = true; onDraw(); press["Scan hunter"] = nil
local all = table.concat(out, "\n")
check(all:match("mesh: Art/Model/Item/it02/00/0002/it0200_0002_1%.mesh"), "weapon mesh path shown")
check(all:match("materials: blade"), "weapon materials shown")
check(all:match("joints %(1%): wp_root"), "weapon joints shown")
check(all:match("params of blade %(2%): Emissive_Intensity, Dissolve"), "weapon material parameter names shown")
check(all:match("parent: Player"), "weapon parent shown")
check(all:match("body: ch02_002_0002"), "armor part listed")
check(all:match("Player_Hair  %->  Art/Model/Character/ch01/000/0/001/ch01_000_0001%.mesh"), "hair child listed")
check(not all:match("Collision  %->"), "objects without meshes skipped")
check(all:match("4 joints") and all:match("root, Hip, Spine_0, R_Hand"), "player skeleton shown")
out = {}
press["Save report"] = true; onDraw()
check(dumped and dumped[1] == "MiquellaLight/scout.json" and dumped[2].weapons[1].slot == "Weapon", "report saved")
check(dumped[2].weapons[1].params[1][2] == "Dissolve", "parameter names saved in the report")
-- Watch weapon state: only fields that change are reported, with their range.
press["Save report"] = nil
out = {}; press["Watch weapon state"] = true; onDraw(); press["Watch weapon state"] = nil
check(table.concat(out, "\n"):match("Watching app.cHunterWp00Handling %(3 fields%)"),
      "watch finds the handling object and its number/bool fields (inherited too, no static/object)")
onFrame()
chargeF.value = 1; onFrame(); chargeF.value = 2; onFrame(); demonF.value = true; onFrame()
out = {}; onDraw()
local w = table.concat(out, "\n")
check(w:match("2 of 3 fields changed"), "two fields changed")
check(w:match("_ChargeLv  x2  %[0 .. 2%]  now 2"), "charge level range recorded")
check(w:match("_IsDemon  x1") and not w:match("_Timer  x"), "flag recorded, unchanged field not listed")
press["Save watch"] = true; onDraw(); press["Save watch"] = nil
check(dumped[1] == "MiquellaLight/watch.json" and #dumped[2].changed == 2 and #dumped[2].log == 3, "watch saved with log")
out = {}; press["Stop watching"] = true; onDraw(); press["Stop watching"] = nil
onFrame()
check(table.concat(out, "\n"):match("Stopped watching"), "watch can be stopped")
-- No handling object: message, no crash.
local savedCall = chr.call
chr.call = function(self, m) if m == "get_WeaponHandling" then return nil end return savedCall(self, m) end
out = {}; press["Watch weapon state"] = true; onDraw(); press["Watch weapon state"] = nil
check(table.concat(out, "\n"):match("not found"), "missing handling object handled")
chr.call = savedCall
-- No hunter yet: no crash, a message instead.
master.get_Valid = function() return false end
out = {}; press["Save report"] = nil; press["Scan hunter"] = true; onDraw()
check(table.concat(out, "\n"):match("No hunter"), "no-hunter case handled")
print("ALL PASS")
