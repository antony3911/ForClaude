-- MiquellaLight: Character (Monster Hunter Wilds, REFramework)
--
-- Miquella's circlet ("halo") on the hunter's head WITHOUT overwriting any game file: the
-- script makes a GameObject of its own with a mesh (our model, from the patch pak
-- MiquellaLight_Character.pak) and puts it on the hunter's Head joint, the way EMV Engine
-- (alphazolam) and MDF-XL spawn and attach objects. The body, robe and hair are to go on the
-- same way later (see the research notes, section 15).
--
-- Two ways to follow the head: the object's transform parented to the hunter with the Head
-- joint as its parent joint (the engine moves it), or, if that does not hold, our script
-- copying the joint's position and rotation every frame before rendering. "Auto" tries the
-- first and falls back to the second when the circlet is not at the head a second later.
--
-- STATUS: untested (2026-10-02). Every game call is wrapped in pcall. Visual only.

local CONFIG_PATH = "MiquellaLight/Character.json"
local MESH = "via.render.Mesh"
local OBJECT_NAME = "MiquellaLight_Circlet"
-- The model is in the Head joint's space (bind pose): +Y up, +Z the face's front, +X the
-- hunter's left (build_weapon_kit.py circlet). glow: materials and their mdf2 Emissive_Intensity.
local CIRCLET = {
    mesh = "Art/Model/MiquellaLight/Character/mq_circlet.mesh",
    mdf2 = "Art/Model/MiquellaLight/Character/mq_circlet.mdf2",
    joint = "Head",
    glow = { MiquellaHalo = 0.8, MiquellaGlow = 1.2 },
}
local CHECK_AFTER = 1.0      -- s after attaching: is the circlet at the head?
local OFF_HEAD = 0.30        -- m from the Head joint: the parent joint did not hold
local REFRESH_AT = { 1.0, 3.0 }   -- s after spawning: set the model again (a resource made that frame may not be loaded)
local MODES = { "Auto", "Head joint", "Follow every frame" }

local config = {
    enabled = true,
    circlet = true,
    glow = 1.0,
    size = 1.0,
    offset = { 0.0, 0.0, 0.0 },   -- cm: left, up, forward (the head's own axes)
    mode = 1,
}
local saved = json.load_file(CONFIG_PATH)
if type(saved) == "table" then
    for k, v in pairs(saved) do config[k] = v end
end
if type(config.offset) ~= "table" then config.offset = { 0.0, 0.0, 0.0 } end
local function save_config() json.dump_file(CONFIG_PATH, config) end

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
holder("via.render.MeshResource", CIRCLET.mesh)
holder("via.render.MeshMaterialResource", CIRCLET.mdf2)

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

-- ------------------------------------------------------------------ the circlet object

local st = { info = "waiting for the hunter" }

local function find_leftover()
    -- After "Reset scripts" the old object is still in the scene: take it over.
    local sm = sdk.get_native_singleton("via.SceneManager")
    local scene = sm and try(function()
        return sdk.call_native_func(sm, sdk.find_type_definition("via.SceneManager"), "get_CurrentScene()")
    end)
    return scene and try(function() return scene:call("findGameObject(System.String)", OBJECT_NAME) end)
end

local function create_object()
    local td = sdk.find_type_definition("via.GameObject")
    local go = nil
    local m1 = td and try(function() return td:get_method("create(System.String)") end)
    if m1 then go = try(function() return m1:call(nil, OBJECT_NAME) end) end
    if not go then
        local m2 = td and try(function() return td:get_method("create(System.String, via.Folder)") end)
        if m2 then go = try(function() return m2:call(nil, OBJECT_NAME, nil) end) end
    end
    if not go then return nil end
    go = try(function() return go:add_ref() end) or go
    try(function() go:call(".ctor") end)
    return go
end

local function glow_slots(mesh)
    local slots = {}
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        local base = CIRCLET.glow[try(function() return mesh:getMaterialName(i) end) or ""]
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

local function apply_glow()
    if not st.mesh then return end
    st.glowSlots = st.glowSlots or glow_slots(st.mesh)
    for _, s in ipairs(st.glowSlots) do
        try(function() st.mesh:setMaterialFloat(s.mat, s.var, s.base * config.glow) end)
    end
end

local function set_model()
    local m = holder("via.render.MeshResource", CIRCLET.mesh)
    local d = holder("via.render.MeshMaterialResource", CIRCLET.mdf2)
    if not (m and d) then
        st.loadError = "could not load " .. CIRCLET.mesh .. " (is MiquellaLight_Character.pak installed?)"
        return false
    end
    st.loadError = nil
    try(function() st.mesh:setMesh(m) end)
    try(function() st.mesh:set_Material(d) end)
    local n = try(function() return st.mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do try(function() st.mesh:setMaterialsEnable(i, true) end) end
    try(function() st.mesh:set_Enabled(true) end)
    st.glowSlots = nil
    apply_glow()
    return true
end

local function spawn()
    local go = find_leftover()
    local reused = go ~= nil
    go = go or create_object()
    if not go then
        st.info = "could not create a GameObject (via.GameObject.create)"
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
        st.info = "could not add a mesh component"
        return false
    end
    st.go, st.mesh = go, mesh
    st.xf = try(function() return go:call("get_Transform") end)
    st.spawnedAt, st.refreshed = os.clock(), 0
    st.parentAddr, st.follow = nil, nil
    set_model()
    st.info = reused and "took over the circlet left by the last script run" or "circlet made"
    return st.xf ~= nil
end

local function local_offset()
    local o = config.offset
    return { o[1] / 100, o[2] / 100, o[3] / 100 }
end

local function attach(hxf, now)
    try(function() st.xf:call("set_Parent", hxf) end)
    local jointOk = try(function() st.xf:call("set_ParentJoint", CIRCLET.joint); return true end)
    local o = local_offset()
    try(function() st.xf:call("set_LocalPosition", Vector3f.new(o[1], o[2], o[3])) end)
    try(function() st.xf:call("set_LocalRotation", Quaternion.new(0, 0, 0, 1)) end)
    st.parentAddr = try(function() return hxf:get_address() end) or hxf
    st.attachAt, st.checked = now, false
    st.jointCall = jointOk and "set_ParentJoint ok" or "set_ParentJoint failed"
end

local function head_joint(hxf)
    return hxf and try(function() return hxf:call("getJointByName", CIRCLET.joint) end)
end

-- Follow mode: our object at the Head joint's world position and rotation, plus the offset.
local function follow()
    if not (st.follow and st.xf and st.hxf) then return end
    local j = head_joint(st.hxf)
    local p = j and try(function() return j:call("get_Position") end)
    local q = j and try(function() return j:call("get_Rotation") end)
    if not (p and q) then return end
    local x, y, z = rotate(q, local_offset())
    try(function() st.xf:call("set_Position", Vector3f.new(p.x + x, p.y + y, p.z + z)) end)
    try(function() st.xf:call("set_Rotation", q) end)
end

local function wanted_follow()
    if config.mode == 2 then return false end
    if config.mode == 3 then return true end
    return st.autoFollow == true
end

local function update(now)
    local chr = player_character()
    if not chr then
        st.info = "waiting for the hunter"
        return
    end
    local hxf, hgo = hunter_transform(chr)
    if not hxf then return end
    st.hxf = hxf
    local show = config.enabled and config.circlet
    -- The game destroys objects on area changes: make it again.
    if st.go and not try(function() return st.go:call("get_Valid") end) then
        st.go, st.mesh, st.xf = nil, nil, nil
    end
    if not st.go then
        if not show then return end
        if not spawn() then return end
    end
    for i, t in ipairs(REFRESH_AT) do
        if st.refreshed < i and now - st.spawnedAt >= t then
            st.refreshed = i
            set_model()
        end
    end
    local addr = try(function() return hxf:get_address() end) or hxf
    if st.parentAddr ~= addr then attach(hxf, now) end
    -- Auto: a second after attaching, is the circlet at the head? If not, follow it ourselves.
    if config.mode == 1 and not st.checked and now - st.attachAt >= CHECK_AFTER then
        st.checked = true
        local j = head_joint(hxf)
        local d = distance(try(function() return st.xf:call("get_Position") end),
                           j and try(function() return j:call("get_Position") end))
        st.lastDistance = d
        st.autoFollow = d == nil or d > OFF_HEAD
    end
    st.follow = wanted_follow()
    if st.follow then follow() end
    local s = config.size
    try(function() st.xf:call("set_LocalScale", Vector3f.new(s, s, s)) end)
    -- Hidden with the hunter (e.g. when the game hides it) and when switched off.
    local hunterShown = try(function() return hgo:call("get_DrawSelf") end)
    try(function() st.go:call("set_DrawSelf", show and hunterShown ~= false) end)
    if now >= (st.glowAt or 0) then
        st.glowAt = now + 2
        apply_glow()
    end
    local j = head_joint(hxf)
    local d = distance(try(function() return st.xf:call("get_Position") end),
                       j and try(function() return j:call("get_Position") end))
    st.info = string.format("circlet on: %s  (%s)  %s cm from the Head joint", st.follow and "following every frame"
        or "Head joint", st.jointCall or "?", d and string.format("%.1f", d * 100) or "?")
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

re.on_script_reset(function()
    if st.go then try(function() st.go:call("set_DrawSelf", false) end) end
end)

-- ------------------------------------------------------------------ menu

re.on_draw_ui(function()
    if not imgui.tree_node("MiquellaLight: Character") then return end
    local changed, c = false, false
    c, config.enabled = imgui.checkbox("Enabled", config.enabled); changed = changed or c
    c, config.circlet = imgui.checkbox("Circlet (halo)", config.circlet); changed = changed or c
    c, config.glow = imgui.slider_float("Glow", config.glow, 0.0, 5.0); changed = changed or c
    if c then apply_glow() end
    c, config.size = imgui.slider_float("Size", config.size, 0.8, 1.3); changed = changed or c
    local labels = { "Left / right (cm)", "Up / down (cm)", "Forward / back (cm)" }
    for i = 1, 3 do
        c, config.offset[i] = imgui.slider_float(labels[i], config.offset[i], -4.0, 4.0)
        if c then st.parentAddr = nil end
        changed = changed or c
    end
    c, config.mode = imgui.combo("Attach", config.mode, MODES)
    if c then st.parentAddr, st.autoFollow = nil, nil end
    changed = changed or c
    if imgui.button("Reset position") then
        config.offset, config.size, st.parentAddr = { 0.0, 0.0, 0.0 }, 1.0, nil
        changed = true
    end
    if st.loadError then imgui.text(st.loadError) end
    imgui.text(st.info or "")
    if config.mode == 1 and st.checked then
        imgui.text(string.format("Auto: %s cm off a second after attaching -> %s",
            st.lastDistance and string.format("%.1f", st.lastDistance * 100) or "?",
            st.autoFollow and "following every frame" or "Head joint holds"))
    end
    if not followHooked then imgui.text("(follow mode runs in on_frame: may lag a frame)") end
    if changed then save_config() end
    imgui.tree_pop()
end)

if not followHooked then
    re.on_frame(follow)
end
