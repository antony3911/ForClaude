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
local chr = {
  get_IsFemale = function() return false end,
  call = function(self, m) if m == "get_Weapon" then return { get_GameObject = function() return weapon end } end return nil end,
  getParts = function(self, i) if i == 1 then return go("ch02_002_0002", "Art/Model/Character/ch02/002/000/2/ch02_002_0002.mesh", { "body" }) end return nil end,
}
local master = { get_Valid = function() return true end, get_Character = function() return chr end, get_Object = function() return playerGO end }
sdk = { typeof = function(n) return { name = n } end,
        get_managed_singleton = function() return { getMasterPlayer = function() return master end } end }
local onDraw
re = { on_draw_ui = function(f) onDraw = f end, on_frame = function() end }
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
check(all:match("parent: Player"), "weapon parent shown")
check(all:match("body: ch02_002_0002"), "armor part listed")
check(all:match("Player_Hair  %->  Art/Model/Character/ch01/000/0/001/ch01_000_0001%.mesh"), "hair child listed")
check(not all:match("Collision  %->"), "objects without meshes skipped")
check(all:match("4 joints") and all:match("root, Hip, Spine_0, R_Hand"), "player skeleton shown")
out = {}
press["Save report"] = true; onDraw()
check(dumped and dumped[1] == "MiquellaLight/scout.json" and dumped[2].weapons[1].slot == "Weapon", "report saved")
-- No hunter yet: no crash, a message instead.
master.get_Valid = function() return false end
out = {}; press["Save report"] = nil; press["Scan hunter"] = true; onDraw()
check(table.concat(out, "\n"):match("No hunter"), "no-hunter case handled")
print("ALL PASS")
