-- MiquellaLight: Character (Monster Hunter Wilds, REFramework)
--
-- Miquella on the hunter WITHOUT overwriting any game file: the script makes GameObjects of its
-- own with our meshes (patch pak MiquellaLight_Character.pak) and puts them on the hunter, the
-- way EMV Engine (alphazolam) and MDF-XL spawn and attach objects (research notes, section 15):
-- - the circlet ("halo") on the Head joint: its transform parented to the hunter with Head as
--   the parent joint, or, if that does not hold, our script copying the joint every frame
--   before rendering ("Auto" tries the first and falls back to the second a second later);
-- - the body (three shapes, A / B / C) on the whole skeleton: parented to the hunter with
--   SameJointsConstraint, so its bones (named like the hunter's) follow the hunter's. While it
--   shows, the hunter's own armor and innerwear (models under character/ch02 and ch03) are
--   hidden; the face (ch00) and hair (ch01) stay.
--
-- STATUS: untested (2026-10-02). Every game call is wrapped in pcall. Visual only.

local CONFIG_PATH = "MiquellaLight/Character.json"
local MESH = "via.render.Mesh"
local DIR = "Art/Model/MiquellaLight/Character/"
-- glow: materials and their mdf2 Emissive_Intensity (the Glow slider scales them).
local PIECES = {
    {
        key = "circlet", name = "MiquellaLight_Circlet", attach = "joint", joint = "Head",
        -- In the Head joint's space (bind pose): +Y up, +Z the face's front (build_weapon_kit.py circlet).
        mesh = function() return DIR .. "mq_circlet.mesh" end, mdf2 = DIR .. "mq_circlet.mdf2",
        glow = { MiquellaHalo = 0.8, MiquellaGlow = 1.2 },
    },
    {
        key = "body", name = "MiquellaLight_Body", attach = "skeleton",
        -- On the hunter's skeleton in its bind pose (miquella_body.py kit).
        mesh = nil, mdf2 = DIR .. "mq_body.mdf2",
        tint = "MiquellaSkin",
    },
}
-- Skin of the body: the game's own skin material (SkinEdit) over a flat albedo of the face
-- texture's neck colour (miquella_body.py). The face's skin tone (AddColorUV of its "face"
-- material, set in character creation) is copied onto it; the SkinEdit skin still comes out ~3x
-- darker than the face, hence SKIN_BASE on ColorParam (calibrated in game 2026-10-03: 3.3 over
-- a warmer albedo; the face's neck colour is ~15 % lighter). The tone choices tint on top.
-- (Tried and dropped the same day: the face's own material on the body -- darker, and its vertex
-- shader mangled the body.)
local FACE_MATERIAL = "face"
local COPY_VARS = { AddColorUV = true }
local SKIN_BASE = 2.9
local SKIN_TONES = {
    { "Match the face", nil },
    { "Fairer", { 1.05, 1.08, 1.12 } },
    { "Darker", { 0.85, 0.78, 0.72 } },
    { "Much darker", { 0.60, 0.50, 0.42 } },
}
local SKIN_NAMES = {}
for i, t in ipairs(SKIN_TONES) do SKIN_NAMES[i] = t[1] end
local BODY_SHAPES = { "A slender", "B youthful", "C soft" }
local BODY_MESHES = { DIR .. "mq_body_a", DIR .. "mq_body_b", DIR .. "mq_body_c" }
-- Each sex of hunter has its own body meshes (miquella_body.py kit; Miquella's shape is the same):
-- the female face (ch00_001) has a lower, thinner neck for the body to meet and the female
-- skeleton narrower shoulders. Female ones end in _f; which one is read off the face's mesh path.
local hunterFemale = nil     -- nil until the face is found
local function body_mesh(shape) return BODY_MESHES[shape] .. (hunterFemale and "_f" or "") .. ".mesh" end
PIECES[2].mesh = nil   -- set below, once config is read
local CHECK_AFTER = 1.0      -- s after attaching: is the circlet at the head?
local OFF_HEAD = 0.30        -- m from the Head joint: the parent joint did not hold
local REFRESH_AT = { 1.0, 3.0 }   -- s after spawning: set the model again (a resource made that frame may not be loaded)
local MODES = { "Auto", "Head joint", "Follow every frame" }
-- The circlet's size on the head (the user 2026-10-03: the model's own size is a little big on
-- their hunter, 0.8 to 0.9 all look good, not decided yet -> a slider over just that range).
local SIZE_MIN, SIZE_MAX, SIZE_DEFAULT = 0.8, 0.9, 0.85
local OUTFIT_PATHS = { "character/ch02/", "character/ch03/" }   -- armor and innerwear (lower case)
local OUTFIT_SCAN = 0.5      -- s between looks for the hunter's outfit objects
local SCAN_DEPTH = 6

local config = {
    enabled = true,
    circlet = true,
    glow = 1.0,
    size = SIZE_DEFAULT,
    offset = { 0.0, 0.0, 0.0 },   -- cm: left, up, forward (the head's own axes)
    mode = 1,
    body = true,
    bodyShape = 1,
    hideOutfit = true,
    skinTone = 1,
    skinBrightness = 1.0,   -- ColorParam multiplier on top of the face's
}
local saved = json.load_file(CONFIG_PATH)
if type(saved) == "table" then
    for k, v in pairs(saved) do config[k] = v end
end
if type(config.offset) ~= "table" then config.offset = { 0.0, 0.0, 0.0 } end
if type(config.size) ~= "number" or config.size < SIZE_MIN or config.size > SIZE_MAX then config.size = SIZE_DEFAULT end
if not BODY_MESHES[config.bodyShape] then config.bodyShape = 1 end
if not SKIN_TONES[config.skinTone] then config.skinTone = 1 end
config.skinShift, config.skinBright = nil, nil   -- test sliders of 2026-10-03, gone
if type(config.skinBrightness) ~= "number" or config.skinVersion ~= 3 then
    config.skinBrightness, config.skinTone = 1.0, 1   -- earlier values were for other materials
end
config.skinVersion = 3
local function save_config() json.dump_file(CONFIG_PATH, config) end
PIECES[2].mesh = function() return body_mesh(config.bodyShape) end
local function piece_on(p)
    if not config.enabled then return false end
    if p.key == "circlet" then return config.circlet end
    return config.body
end

local face_mesh      -- the hunter's face mesh component (defined below)

local function try(fn, ...)
    local ok, result = pcall(fn, ...)
    if ok then return result end
    return nil
end

-- ------------------------------------------------------------------ resources

local holders, retryAt = {}, {}
local function holder(typeName, path)
    local key = typeName .. "|" .. path
    if holders[key] == false and os.clock() >= (retryAt[key] or 0) then holders[key] = nil end
    if holders[key] == nil then
        retryAt[key] = os.clock() + 5
        holders[key] = try(function()
            local res = sdk.create_resource(typeName, path):add_ref()
            return res:create_holder(typeName .. "Holder"):add_ref()
        end) or false
    end
    return holders[key] or nil
end
-- Load now, so the first spawn has them ready.
for _, p in ipairs(PIECES) do holder("via.render.MeshMaterialResource", p.mdf2) end
holder("via.render.MeshResource", PIECES[1].mesh())
for _, m in ipairs(BODY_MESHES) do
    holder("via.render.MeshResource", m .. ".mesh")
    holder("via.render.MeshResource", m .. "_f.mesh")
end

local function resource_path(res)
    local s = res and try(function() return res:ToString() end)
    if not s then return nil end
    return (s:gsub("^Resource%[", ""):gsub("%]$", ""))
end

-- ------------------------------------------------------------------ hunter

local function player_character()
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    if not (master and try(function() return master:get_Valid() end)) then return nil end
    return try(function() return master:get_Character() end)
end

local function hunter_transform(chr)
    local go = try(function() return chr:call("get_GameObject") end)
    return go and try(function() return go:call("get_Transform") end), go
end

local function address(obj)
    return try(function() return obj:get_address() end) or obj
end

-- ------------------------------------------------------------------ math (Vector3f / Quaternion fields only)

local function rotate(q, v)
    -- v + 2w (q x v) + 2 q x (q x v)
    local tx = 2 * (q.y * v[3] - q.z * v[2])
    local ty = 2 * (q.z * v[1] - q.x * v[3])
    local tz = 2 * (q.x * v[2] - q.y * v[1])
    return v[1] + q.w * tx + (q.y * tz - q.z * ty),
           v[2] + q.w * ty + (q.z * tx - q.x * tz),
           v[3] + q.w * tz + (q.x * ty - q.y * tx)
end

local function distance(a, b)
    if not (a and b) then return nil end
    return math.sqrt((a.x - b.x) ^ 2 + (a.y - b.y) ^ 2 + (a.z - b.z) ^ 2)
end

local function unrotate(q, v)   -- by the inverse of q
    return rotate({ x = -q.x, y = -q.y, z = -q.z, w = q.w }, v)
end

-- ------------------------------------------------------------------ our objects

local st = { hxf = nil, info = "waiting for the hunter" }
for _, p in ipairs(PIECES) do p.st = {} end

local function find_leftover(name)
    -- After "Reset scripts" the old object is still in the scene: take it over.
    local sm = sdk.get_native_singleton("via.SceneManager")
    local scene = sm and try(function()
        return sdk.call_native_func(sm, sdk.find_type_definition("via.SceneManager"), "get_CurrentScene()")
    end)
    return scene and try(function() return scene:call("findGameObject(System.String)", name) end)
end

local function create_object(name)
    local td = sdk.find_type_definition("via.GameObject")
    local go = nil
    local m1 = td and try(function() return td:get_method("create(System.String)") end)
    if m1 then go = try(function() return m1:call(nil, name) end) end
    if not go then
        local m2 = td and try(function() return td:get_method("create(System.String, via.Folder)") end)
        if m2 then go = try(function() return m2:call(nil, name, nil) end) end
    end
    if not go then return nil end
    go = try(function() return go:add_ref() end) or go
    try(function() go:call(".ctor") end)
    return go
end

-- The glow materials' emission switches, as on the dual blades' glow material: MiquellaHalo was
-- copied from the ivory, whose Emissive_Power 0 turns the emission off whatever the intensity
-- (2026-10-03: the circlet showed as plain metal). Set here until the mdf2 is rebuilt with them.
local EMIT_ON = { Emissive_Power = 1.0, UseCounterExposureEmit = 1.0, CounterExposureEmit_Blend = 0.8 }

local function glow_slots(p)
    local slots = {}
    local mesh = p.st.mesh
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        local base = p.glow and p.glow[try(function() return mesh:getMaterialName(i) end) or ""]
        if base then
            local vars = try(function() return mesh:getMaterialVariableNum(i) end) or 0
            local slot = { mat = i, base = base, on = {} }
            for j = 0, vars - 1 do
                local name = try(function() return mesh:getMaterialVariableName(i, j) end)
                if name == "Emissive_Intensity" then slot.var = j
                elseif name and EMIT_ON[name] then slot.on[j] = EMIT_ON[name] end
            end
            if slot.var then slots[#slots + 1] = slot end
        end
    end
    return slots
end

local function apply_glow(p)
    if not (p.glow and p.st.mesh) then return end
    p.st.glowSlots = p.st.glowSlots or glow_slots(p)
    for _, s in ipairs(p.st.glowSlots) do
        try(function() p.st.mesh:setMaterialFloat(s.mat, s.var, s.base * config.glow) end)
        for j, v in pairs(s.on) do try(function() p.st.mesh:setMaterialFloat(s.mat, j, v) end) end
    end
end

local function material_index(mesh, name)
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        if try(function() return mesh:getMaterialName(i) end) == name then return i end
    end
    return nil
end

local function var_table(mesh, mat)
    local t = {}
    local n = try(function() return mesh:getMaterialVariableNum(mat) end) or 0
    for j = 0, n - 1 do
        local name = try(function() return mesh:getMaterialVariableName(mat, j) end)
        if name then t[name] = j end
    end
    return t
end

local function apply_tint(p)
    if not (p.tint and p.st.mesh) then return end
    local mesh, s = p.st.mesh, p.st
    s.ourMat = s.ourMat or material_index(mesh, p.tint)
    if not s.ourMat then return end
    s.ourVars = s.ourVars or var_table(mesh, s.ourMat)
    local face = st.hxf and face_mesh(st.hxf)
    if face then
        s.faceMat = s.faceMat or material_index(face, FACE_MATERIAL)
        s.faceVars = s.faceVars or (s.faceMat and var_table(face, s.faceMat))
    end
    if face and s.faceMat then
        local copied = 0
        for name in pairs(COPY_VARS) do
            local j, k = s.faceVars[name], s.ourVars[name]
            local v = j and k and try(function() return face:getMaterialFloat4(s.faceMat, j) end)
            if v and try(function()
                mesh:setMaterialFloat4(s.ourMat, k, Vector4f.new(v.x, v.y, v.z, v.w))
                return true
            end) then copied = copied + 1 end
        end
        s.copied = copied
    end
    local tone = SKIN_TONES[config.skinTone][2] or { 1.0, 1.0, 1.0 }
    local b = config.skinBrightness * SKIN_BASE
    s.tinted = s.ourVars.ColorParam and try(function()
        mesh:setMaterialFloat4(s.ourMat, s.ourVars.ColorParam, Vector4f.new(tone[1] * b, tone[2] * b, tone[3] * b, 1.0))
        return true
    end)
end

local function set_model(p)
    local path = p.mesh()
    local m = holder("via.render.MeshResource", path)
    local d = holder("via.render.MeshMaterialResource", p.mdf2)
    if not (m and d) then
        p.st.loadError = "could not load " .. path .. " (is MiquellaLight_Character.pak installed?)"
        return false
    end
    p.st.loadError = nil
    try(function() p.st.mesh:setMesh(m) end)
    try(function() p.st.mesh:set_Material(d) end)
    local n = try(function() return p.st.mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do try(function() p.st.mesh:setMaterialsEnable(i, true) end) end
    try(function() p.st.mesh:set_Enabled(true) end)
    p.st.meshPath = path
    p.st.glowSlots = nil
    p.st.renderMatched = nil
    p.st.ourMat, p.st.ourVars, p.st.faceMat, p.st.faceVars = nil, nil, nil, nil
    apply_glow(p)
    apply_tint(p)
    return true
end

local function spawn(p)
    local go = find_leftover(p.name)
    local reused = go ~= nil
    go = go or create_object(p.name)
    if not go then
        p.st.info = "could not create a GameObject (via.GameObject.create)"
        return false
    end
    local mesh = try(function() return go:call("getComponent(System.Type)", sdk.typeof(MESH)) end)
    if not mesh then
        mesh = try(function() return go:call("createComponent(System.Type)", sdk.typeof(MESH)) end)
        if mesh then
            mesh = try(function() return mesh:add_ref() end) or mesh
            try(function() mesh:call(".ctor()") end)
        end
    end
    if not mesh then
        p.st.info = "could not add a mesh component"
        return false
    end
    p.st.go, p.st.mesh = go, mesh
    p.st.xf = try(function() return go:call("get_Transform") end)
    p.st.spawnedAt, p.st.refreshed = os.clock(), 0
    p.st.parentAddr, p.st.follow = nil, nil
    set_model(p)
    p.st.info = reused and "took over the object left by the last script run" or "made"
    return p.st.xf ~= nil
end

-- Size scales the circlet about the middle of the head at the brow (Head joint space), so a smaller
-- one hugs the head instead of sinking toward the neck as it would about the joint itself.
local SIZE_PIVOT = { 0.0, 0.128, 0.0 }
local function local_offset()
    local o, k = config.offset, 1 - config.size
    return { o[1] / 100 + SIZE_PIVOT[1] * k, o[2] / 100 + SIZE_PIVOT[2] * k, o[3] / 100 + SIZE_PIVOT[3] * k }
end

-- REFramework's Quaternion.new takes (w, x, y, z) (glm), not (x, y, z, w): new(0, 0, 0, 1) is
-- half a turn about Z, which hung the circlet upside down from the Head joint, its front 13 cm
-- below it at the base of the neck (2026-10-03, circlet_debug.json). Checked once, as the weapons
-- script does, in case the order changes.
local function identity_quat()
    local probe = try(function() return Quaternion.new(0.5, 0.1, 0.2, 0.3) end)
    if probe and math.abs(probe.w - 0.5) < 1e-6 then return Quaternion.new(1, 0, 0, 0) end
    return Quaternion.new(0, 0, 0, 1)
end

local function attach(p, hxf, now)
    local xf = p.st.xf
    try(function() xf:call("set_Parent", hxf) end)
    if p.attach == "joint" then
        local ok = try(function() xf:call("set_ParentJoint", p.joint); return true end)
        local o = local_offset()
        try(function() xf:call("set_LocalPosition", Vector3f.new(o[1], o[2], o[3])) end)
        p.st.jointCall = ok and "set_ParentJoint ok" or "set_ParentJoint failed"
    else
        local ok = try(function() xf:call("set_SameJointsConstraint", true); return true end)
        try(function() xf:call("set_LocalPosition", Vector3f.new(0, 0, 0)) end)
        p.st.jointCall = ok and "SameJointsConstraint on" or "SameJointsConstraint failed"
    end
    try(function() xf:call("set_LocalRotation", identity_quat()) end)
    p.st.parentAddr = address(hxf)
    p.st.attachAt, p.st.checked = now, false
end

local function head_joint(hxf, name)
    return hxf and try(function() return hxf:call("getJointByName", name) end)
end

-- Follow mode (joint pieces): our object at the joint's world position and rotation, plus the offset.
local function follow()
    for _, p in ipairs(PIECES) do
        local s = p.st
        if p.attach == "joint" and s.follow and s.xf and st.hxf then
            local j = head_joint(st.hxf, p.joint)
            local pos = j and try(function() return j:call("get_Position") end)
            local q = j and try(function() return j:call("get_Rotation") end)
            if pos and q then
                local x, y, z = rotate(q, local_offset())
                try(function() s.xf:call("set_Position", Vector3f.new(pos.x + x, pos.y + y, pos.z + z)) end)
                try(function() s.xf:call("set_Rotation", q) end)
            end
        end
    end
end

-- Where the circlet really is (2026-10-03: in game a dark ring sat at the base of the neck),
-- written for Claude to read: our object and the Head / Neck_0 joints and the hunter's root,
-- in the world and in the Head joint's own axes. The circlet's front (FRONT, file space) should
-- come out ~13 cm above Head and ~11 cm in front of it (build_weapon_kit.py circlet).
local DEBUG_PATH = "MiquellaLight/circlet_debug.json"
local FRONT = { 0.0, 0.128, 0.113 }
local function vec(v) return v and { v.x, v.y, v.z, v.w } end
local function write_debug(p, hxf)
    local s = p.st
    local j, n = head_joint(hxf, p.joint), head_joint(hxf, "Neck_0")
    local hp = j and try(function() return j:call("get_Position") end)
    local hq = j and try(function() return j:call("get_Rotation") end)
    local op = try(function() return s.xf:call("get_Position") end)
    local oq = try(function() return s.xf:call("get_Rotation") end)
    local d = { mode = MODES[config.mode], follow = s.follow == true, jointCall = s.jointCall,
        head = vec(hp), headRot = vec(hq), neck0 = vec(n and try(function() return n:call("get_Position") end)),
        hunter = vec(try(function() return hxf:call("get_Position") end)),
        hunterRot = vec(try(function() return hxf:call("get_Rotation") end)),
        obj = vec(op), objRot = vec(oq), objScale = vec(try(function() return s.xf:call("get_LocalScale") end)) }
    if hp and hq and op and oq then
        d.objInHead = { unrotate(hq, { op.x - hp.x, op.y - hp.y, op.z - hp.z }) }
        local fx, fy, fz = rotate(oq, { FRONT[1] * config.size, FRONT[2] * config.size, FRONT[3] * config.size })
        d.front = { op.x + fx, op.y + fy, op.z + fz }
        d.frontInHead = { unrotate(hq, { d.front[1] - hp.x, d.front[2] - hp.y, d.front[3] - hp.z }) }
        d.upOfHead = { rotate(hq, { 0, 1, 0 }) }      -- the Head joint's +Y in the world
        d.upOfObj = { rotate(oq, { 0, 1, 0 }) }
    end
    pcall(json.dump_file, DEBUG_PATH, d)
end

-- ------------------------------------------------------------------ the hunter's outfit

local outfit = { list = {}, nextScan = 0, hidden = false }

local function mesh_path(go)
    local mesh = try(function() return go:call("getComponent(System.Type)", sdk.typeof(MESH)) end)
    local s = mesh and resource_path(try(function() return mesh:getMesh() end))
    return s and s:lower()
end

local function is_outfit(path)
    if not path then return false end
    for _, pat in ipairs(OUTFIT_PATHS) do
        if path:find(pat, 1, true) then return true end
    end
    return false
end

local function scan_outfit(xf, out, depth)
    if depth > SCAN_DEPTH then return end
    local child = try(function() return xf:call("get_Child") end)
    while child do
        local go = try(function() return child:call("get_GameObject") end)
        if go and is_outfit(mesh_path(go)) then out[#out + 1] = go end
        scan_outfit(child, out, depth + 1)
        child = try(function() return child:call("get_Next") end)
    end
end

local function update_outfit(hxf, now)
    local hide = config.enabled and config.body and config.hideOutfit and PIECES[2].st.go ~= nil
    if hide and now >= outfit.nextScan then
        outfit.nextScan = now + OUTFIT_SCAN
        local found = {}
        scan_outfit(hxf, found, 1)
        outfit.list = found
    end
    if hide then
        for _, go in ipairs(outfit.list) do try(function() go:call("set_DrawSelf", false) end) end
        outfit.hidden = true
    elseif outfit.hidden then
        for _, go in ipairs(outfit.list) do try(function() go:call("set_DrawSelf", true) end) end
        outfit.hidden, outfit.list = false, {}
    end
end

-- ------------------------------------------------------------------ frame

-- Render settings copied from the hunter's own face mesh onto ours. A created via.render.Mesh
-- has StencilValue 0 where the hunter's meshes have 1: ours got the sun but no ambient light,
-- black in the shade (2026-10-03, found with MiquellaLight_MeshDiff.lua).
local MATCH_RENDER = { "StencilValue", "ShadowCastMode" }

function face_mesh(hxf)
    local child = try(function() return hxf:call("get_Child") end)
    while child do
        local go = try(function() return child:call("get_GameObject") end)
        local path = go and mesh_path(go)
        if path and path:find("character/ch00/", 1, true) then
            hunterFemale = path:find("ch00_001", 1, true) ~= nil
            return try(function() return go:call("getComponent(System.Type)", sdk.typeof(MESH)) end)
        end
        child = try(function() return child:call("get_Next") end)
    end
    return nil
end

local function match_render(p, hxf)
    local face = face_mesh(hxf)
    if not face then return end
    local got = {}
    for _, name in ipairs(MATCH_RENDER) do
        local v = try(function() return face:call("get_" .. name) end)
        if v ~= nil then
            try(function() p.st.mesh:call("set_" .. name, v) end)
            local now = try(function() return p.st.mesh:call("get_" .. name) end)
            table.insert(got, name .. " " .. tostring(now))
        end
    end
    p.st.render = table.concat(got, ", ")
    p.st.renderMatched = true
end

local function update_piece(p, hxf, hgo, now)
    local s = p.st
    local show = piece_on(p)
    -- The game destroys objects on area changes: make it again.
    if s.go and not try(function() return s.go:call("get_Valid") end) then
        s.go, s.mesh, s.xf = nil, nil, nil
    end
    if not s.go then
        if not show then return end
        if not spawn(p) then return end
    end
    for i, t in ipairs(REFRESH_AT) do
        if s.refreshed < i and now - s.spawnedAt >= t then
            s.refreshed = i
            set_model(p)
        end
    end
    if p.key == "body" and s.sexOf ~= address(hxf) and face_mesh(hxf) then
        s.sexOf = address(hxf)          -- face_mesh set hunterFemale
    end
    if s.meshPath ~= p.mesh() then set_model(p) end      -- another body shape picked, or the hunter's sex found
    if s.parentAddr ~= address(hxf) then attach(p, hxf, now) end
    if not s.renderMatched and now >= (s.renderAt or 0) then
        s.renderAt = now + 1
        match_render(p, hxf)
    end
    if p.attach == "joint" then
        -- Auto: a second after attaching, is it at the joint? If not, follow it ourselves.
        if config.mode == 1 and not s.checked and now - s.attachAt >= CHECK_AFTER then
            s.checked = true
            local j = head_joint(hxf, p.joint)
            local d = distance(try(function() return s.xf:call("get_Position") end),
                               j and try(function() return j:call("get_Position") end))
            s.lastDistance = d
            s.autoFollow = d == nil or d > OFF_HEAD
        end
        s.follow = config.mode == 3 or (config.mode == 1 and s.autoFollow == true)
        if s.follow then follow() end
        local k = config.size
        try(function() s.xf:call("set_LocalScale", Vector3f.new(k, k, k)) end)
        local j = head_joint(hxf, p.joint)
        local d = distance(try(function() return s.xf:call("get_Position") end),
                           j and try(function() return j:call("get_Position") end))
        s.info = string.format("on: %s  (%s)  %s cm from the %s joint", s.follow and "following every frame"
            or p.joint .. " joint", s.jointCall or "?", d and string.format("%.1f", d * 100) or "?", p.joint)
        if now >= (s.debugAt or 0) then
            s.debugAt = now + 1
            write_debug(p, hxf)
        end
    else
        s.info = string.format("on the skeleton (%s), %s for a %s hunter; render: %s; skin %s", s.jointCall or "?",
            BODY_SHAPES[config.bodyShape], hunterFemale == nil and "?" or hunterFemale and "female" or "male",
            s.render or "not matched yet",
            (s.tinted and SKIN_NAMES[config.skinTone] or "not tinted")
            .. (s.copied == 1 and ", face skin tone copied" or ", face skin tone not found"))
    end
    -- Hidden with the hunter (e.g. when the game hides it) and when switched off.
    local hunterShown = try(function() return hgo:call("get_DrawSelf") end)
    try(function() s.go:call("set_DrawSelf", show and hunterShown ~= false) end)
    if (p.glow or p.tint) and now >= (s.glowAt or 0) then
        s.glowAt = now + 2
        apply_glow(p)
        apply_tint(p)
    end
end

local function update(now)
    local chr = player_character()
    if not chr then
        st.info = "waiting for the hunter"
        return
    end
    local hxf, hgo = hunter_transform(chr)
    if not hxf then return end
    st.hxf, st.info = hxf, nil
    for _, p in ipairs(PIECES) do update_piece(p, hxf, hgo, now) end
    update_outfit(hxf, now)
end

re.on_frame(function()
    update(os.clock())
end)

-- Follow mode: after the animation, before rendering.
local followHooked = false
if re.on_pre_application_entry then
    for _, phase in ipairs({ "PrepareRendering", "BeginRendering" }) do
        followHooked = pcall(re.on_pre_application_entry, phase, follow) or followHooked
    end
end
if not followHooked then re.on_frame(follow) end

re.on_script_reset(function()
    for _, p in ipairs(PIECES) do
        if p.st.go then try(function() p.st.go:call("set_DrawSelf", false) end) end
    end
    for _, go in ipairs(outfit.list) do try(function() go:call("set_DrawSelf", true) end) end
end)

-- ------------------------------------------------------------------ menu

re.on_draw_ui(function()
    if not imgui.tree_node("MiquellaLight: Character") then return end
    local changed, c = false, false
    c, config.enabled = imgui.checkbox("Enabled", config.enabled); changed = changed or c
    if st.info then imgui.text(st.info) end
    -- Body
    c, config.body = imgui.checkbox("Body", config.body); changed = changed or c
    c, config.bodyShape = imgui.combo("Body shape", config.bodyShape, BODY_SHAPES); changed = changed or c
    c, config.skinTone = imgui.combo("Skin tone", config.skinTone, SKIN_NAMES)
    if c then
        changed = true
        apply_tint(PIECES[2])
    end
    c, config.skinBrightness = imgui.slider_float("Skin brightness", config.skinBrightness, 0.5, 1.5)
    if c then
        changed = true
        apply_tint(PIECES[2])
    end
    c, config.hideOutfit = imgui.checkbox("Hide the hunter's armor and innerwear", config.hideOutfit)
    changed = changed or c
    local b = PIECES[2].st
    if b.loadError then imgui.text(b.loadError) end
    if b.info then imgui.text("Body: " .. b.info .. string.format("  (outfit objects hidden: %d)", #outfit.list)) end
    -- Circlet
    c, config.circlet = imgui.checkbox("Circlet (halo)", config.circlet); changed = changed or c
    c, config.glow = imgui.slider_float("Glow", config.glow, 0.0, 5.0); changed = changed or c
    if c then apply_glow(PIECES[1]) end
    c, config.size = imgui.slider_float("Size", config.size, SIZE_MIN, SIZE_MAX); changed = changed or c
    if c then PIECES[1].st.parentAddr = nil end
    local labels = { "Left / right (cm)", "Up / down (cm)", "Forward / back (cm)" }
    for i = 1, 3 do
        c, config.offset[i] = imgui.slider_float(labels[i], config.offset[i], -4.0, 4.0)
        if c then PIECES[1].st.parentAddr = nil end
        changed = changed or c
    end
    c, config.mode = imgui.combo("Attach", config.mode, MODES)
    if c then PIECES[1].st.parentAddr, PIECES[1].st.autoFollow = nil, nil end
    changed = changed or c
    if imgui.button("Reset position") then
        config.offset, config.size, PIECES[1].st.parentAddr = { 0.0, 0.0, 0.0 }, SIZE_DEFAULT, nil
        changed = true
    end
    local s = PIECES[1].st
    if s.loadError then imgui.text(s.loadError) end
    if s.info then imgui.text("Circlet: " .. s.info) end
    if config.mode == 1 and s.checked then
        imgui.text(string.format("Auto: %s cm off a second after attaching -> %s",
            s.lastDistance and string.format("%.1f", s.lastDistance * 100) or "?",
            s.autoFollow and "following every frame" or "Head joint holds"))
    end
    if not followHooked then imgui.text("(follow mode runs in on_frame: may lag a frame)") end
    if changed then save_config() end
    imgui.tree_pop()
end)
