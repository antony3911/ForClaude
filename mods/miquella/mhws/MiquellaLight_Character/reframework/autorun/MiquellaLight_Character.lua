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
-- Skin tone of the body. The skin is the game's own skin material (SkinEdit): a neutral albedo
-- coloured from the SkinMap palette at AddColorUV, which the game sets on the hunter's face from
-- character creation: "Match the face" copies it over. The others tint ColorParam on top
-- (multipliers of the matched tone).
local SKIN_TONES = {
    { "Match the face", nil },
    { "Fairer", { 1.05, 1.08, 1.12 } },
    { "Darker", { 0.85, 0.78, 0.72 } },
    { "Much darker", { 0.60, 0.50, 0.42 } },
}
local SKIN_NAMES = {}
for i, t in ipairs(SKIN_TONES) do SKIN_NAMES[i] = t[1] end
local BODY_SHAPES = { "A slender", "B youthful", "C soft" }
local BODY_MESHES = { DIR .. "mq_body_a.mesh", DIR .. "mq_body_b.mesh", DIR .. "mq_body_c.mesh" }
PIECES[2].mesh = nil   -- set below, once config is read
local CHECK_AFTER = 1.0      -- s after attaching: is the circlet at the head?
local OFF_HEAD = 0.30        -- m from the Head joint: the parent joint did not hold
local REFRESH_AT = { 1.0, 3.0 }   -- s after spawning: set the model again (a resource made that frame may not be loaded)
local MODES = { "Auto", "Head joint", "Follow every frame" }
local OUTFIT_PATHS = { "character/ch02/", "character/ch03/" }   -- armor and innerwear (lower case)
local OUTFIT_SCAN = 0.5      -- s between looks for the hunter's outfit objects
local SCAN_DEPTH = 6

local config = {
    enabled = true,
    circlet = true,
    glow = 1.0,
    size = 1.0,
    offset = { 0.0, 0.0, 0.0 },   -- cm: left, up, forward (the head's own axes)
    mode = 1,
    body = true,
    bodyShape = 1,
    hideOutfit = true,
    skinTone = 1,
}
local saved = json.load_file(CONFIG_PATH)
if type(saved) == "table" then
    for k, v in pairs(saved) do config[k] = v end
end
if type(config.offset) ~= "table" then config.offset = { 0.0, 0.0, 0.0 } end
if not BODY_MESHES[config.bodyShape] then config.bodyShape = 1 end
if not SKIN_TONES[config.skinTone] then config.skinTone = 1 end
local function save_config() json.dump_file(CONFIG_PATH, config) end
PIECES[2].mesh = function() return BODY_MESHES[config.bodyShape] end
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
for _, m in ipairs(BODY_MESHES) do holder("via.render.MeshResource", m) end

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

local function glow_slots(p)
    local slots = {}
    local mesh = p.st.mesh
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        local base = p.glow and p.glow[try(function() return mesh:getMaterialName(i) end) or ""]
        if base then
            local vars = try(function() return mesh:getMaterialVariableNum(i) end) or 0
            for j = 0, vars - 1 do
                if try(function() return mesh:getMaterialVariableName(i, j) end) == "Emissive_Intensity" then
                    slots[#slots + 1] = { mat = i, var = j, base = base }
                end
            end
        end
    end
    return slots
end

local function apply_glow(p)
    if not (p.glow and p.st.mesh) then return end
    p.st.glowSlots = p.st.glowSlots or glow_slots(p)
    for _, s in ipairs(p.st.glowSlots) do
        try(function() p.st.mesh:setMaterialFloat(s.mat, s.var, s.base * config.glow) end)
    end
end

local function material_var(mesh, matName, varName)
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        if not matName or try(function() return mesh:getMaterialName(i) end) == matName then
            local vars = try(function() return mesh:getMaterialVariableNum(i) end) or 0
            for j = 0, vars - 1 do
                if try(function() return mesh:getMaterialVariableName(i, j) end) == varName then
                    return { mat = i, var = j }
                end
            end
        end
    end
    return nil
end

local function apply_tint(p)
    if not (p.tint and p.st.mesh) then return end
    local mesh = p.st.mesh
    p.st.tintSlot = p.st.tintSlot or material_var(mesh, p.tint, "ColorParam")
    p.st.uvSlot = p.st.uvSlot or material_var(mesh, p.tint, "AddColorUV")
    local tone = SKIN_TONES[config.skinTone][2] or { 1.0, 1.0, 1.0 }
    local slot = p.st.tintSlot
    p.st.tinted = slot and try(function()
        mesh:setMaterialFloat4(slot.mat, slot.var, Vector4f.new(tone[1], tone[2], tone[3], 1.0))
        return true
    end)
    -- The face's skin tone (its AddColorUV), for every choice: the others tint on top of it.
    local face = st.hxf and face_mesh(st.hxf)
    if face and p.st.uvSlot then
        p.st.faceSlot = p.st.faceSlot or material_var(face, nil, "AddColorUV")
        local f, u = p.st.faceSlot, p.st.uvSlot
        local uv = f and try(function() return face:getMaterialFloat4(f.mat, f.var) end)
        p.st.faceUV = uv and try(function()
            mesh:setMaterialFloat4(u.mat, u.var, Vector4f.new(uv.x, uv.y, uv.z, uv.w))
            return string.format("%.2f, %.2f", uv.x, uv.y)
        end)
    end
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
    p.st.tintSlot, p.st.uvSlot, p.st.faceSlot = nil, nil, nil
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

local function local_offset()
    local o = config.offset
    return { o[1] / 100, o[2] / 100, o[3] / 100 }
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
    try(function() xf:call("set_LocalRotation", Quaternion.new(0, 0, 0, 1)) end)
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
    if s.meshPath ~= p.mesh() then set_model(p) end      -- another body shape picked
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
    else
        s.info = string.format("on the skeleton (%s), %s; render: %s; skin %s", s.jointCall or "?",
            BODY_SHAPES[config.bodyShape], s.render or "not matched yet",
            (s.tinted and SKIN_NAMES[config.skinTone] or "not tinted")
            .. (s.faceUV and (", face tone " .. s.faceUV) or ", face tone not found"))
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
    c, config.hideOutfit = imgui.checkbox("Hide the hunter's armor and innerwear", config.hideOutfit)
    changed = changed or c
    local b = PIECES[2].st
    if b.loadError then imgui.text(b.loadError) end
    if b.info then imgui.text("Body: " .. b.info .. string.format("  (outfit objects hidden: %d)", #outfit.list)) end
    -- Circlet
    c, config.circlet = imgui.checkbox("Circlet (halo)", config.circlet); changed = changed or c
    c, config.glow = imgui.slider_float("Glow", config.glow, 0.0, 5.0); changed = changed or c
    if c then apply_glow(PIECES[1]) end
    c, config.size = imgui.slider_float("Size", config.size, 0.8, 1.3); changed = changed or c
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
        config.offset, config.size, PIECES[1].st.parentAddr = { 0.0, 0.0, 0.0 }, 1.0, nil
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
