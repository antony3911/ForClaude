-- MiquellaLight: Face (Monster Hunter Wilds, REFramework)
--
-- Miquella's look on the hunter's own face WITHOUT replacing it (2026-10-04): small offsets on the
-- face's own joints, added every frame on top of whatever the game set (character creation,
-- expressions, talking, blinking), so the face stays the hunter's and keeps all its motion.
-- The direction (DESIGN.md "臉", the user 2026-10-04): droopy eyes, upper lids half down, a haughty,
-- toying look -- one mouth corner up, the lower lids pushed up a little (the eye a smile makes).
--
-- The face (the hunter's child object with a character/ch00 mesh) has 393 joints, ~150 of them
-- facial (prototypes/scripts/face_tune_preview.py shows these offsets on the game's female face):
--   outer eye corners  L/R_OuterEyeJ_LOD02 (+ UpEyeLid_B_LOD00 for the lid's outer half)
--   upper / lower lids L/R_UpEyeLidJ_LOD02 / LoEyeLidJ_LOD02: at the eye's centre, turned about the
--                      head's left axis (+ lowers, - raises)
--   mouth corners      L/R_cornerLip_LOD02;  brows L/R_EyeBrow_A/B/C_LOD01 (inner, middle, outer)
-- Offsets are in the Head joint's space (x the hunter's left, y up, z the face's front), mirrored
-- for the right side.
--
-- Additive without piling up: per joint the script remembers what it set; if the joint still holds
-- that, the game did not touch it this frame and the remembered base is used, otherwise what the
-- game set is the new base. Set after the behaviour update and again before rendering.
--
-- STATUS: untested in game (2026-10-04). Every game call is wrapped in pcall. Visual only.

local CONFIG_PATH = "MiquellaLight/Face.json"
local DEBUG_PATH = "MiquellaLight/face_debug.json"
local MESH = "via.render.Mesh"
local SIDES = { "Left", "Right" }

local config = {
    enabled = true,
    droop = 2.2,      -- mm: outer eye corners down
    lids = 11.0,      -- degrees: upper lids lowered
    squint = 5.0,     -- degrees: lower lids raised
    smile = 2.6,      -- mm: one mouth corner up (and back)
    smileSide = 1,    -- the hunter's left / right
    brow = 0.0,       -- mm: the smile side's outer brow lifted
}
local saved = json.load_file(CONFIG_PATH)
if type(saved) == "table" then
    for k, v in pairs(saved) do if config[k] ~= nil and type(v) == type(config[k]) then config[k] = v end end
end
if not SIDES[config.smileSide] then config.smileSide = 1 end
local function save_config() json.dump_file(CONFIG_PATH, config) end

local function try(fn, ...)
    local ok, result = pcall(fn, ...)
    if ok then return result end
    return nil
end

-- ------------------------------------------------------------------ the tweaks

-- Each: joint, side ("L"/"R" for one side, nil = both, mirrored), move (head space, m) and turn
-- (head-space axis, radians) from the sliders.
local function tweaks()
    local mm, rad = 0.001, math.pi / 180
    local d, s, b = config.droop * mm, config.smile * mm, config.brow * mm
    local main = config.smileSide == 1 and "L" or "R"
    local other = main == "L" and "R" or "L"
    return {
        { "{s}_OuterEyeJ_LOD02", nil, { 0, -d, -0.27 * d } },
        { "{s}_UpEyeLid_B_LOD00", nil, { 0, -0.27 * d, 0 } },
        { "{s}_UpEyeLidJ_LOD02", nil, nil, { 1, 0, 0 }, config.lids * rad },
        { "{s}_LoEyeLidJ_LOD02", nil, nil, { 1, 0, 0 }, -config.squint * rad },
        { main .. "_cornerLip_LOD02", main, { 0.35 * s, s, -0.54 * s } },
        { other .. "_cornerLip_LOD02", other, { 0.12 * s, 0.27 * s, -0.15 * s } },
        { main .. "_EyeBrow_C_LOD01", main, { 0, b, 0 } },
        { main .. "_EyeBrow_B_LOD01", main, { 0, 0.5 * b, 0 } },
        { "{s}_EyeBrow_A_LOD01", nil, { 0, -0.3 * b, 0 } },
    }
end

-- ------------------------------------------------------------------ math (tables {x, y, z, w})

local function q(t) return { x = t.x, y = t.y, z = t.z, w = t.w } end
local function qmul(a, b)
    return { w = a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
             x = a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
             y = a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
             z = a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w }
end
local function qconj(a) return { x = -a.x, y = -a.y, z = -a.z, w = a.w } end
-- unit length again: the parent's turn is worked out from what we set last pass, so any drift
-- would feed on itself (it blew up to NaN in the offline test)
local function qnorm(a)
    local n = math.sqrt(a.x * a.x + a.y * a.y + a.z * a.z + a.w * a.w)
    if n < 1e-9 then return { x = 0, y = 0, z = 0, w = 1 } end
    return { x = a.x / n, y = a.y / n, z = a.z / n, w = a.w / n }
end
local function rotate(a, v)
    local r = qmul(qmul(a, { x = v[1], y = v[2], z = v[3], w = 0 }), qconj(a))
    return { r.x, r.y, r.z }
end
local function axis_angle(v, angle)
    local s = math.sin(angle / 2)
    return { x = v[1] * s, y = v[2] * s, z = v[3] * s, w = math.cos(angle / 2) }
end

local quatOrder = nil
local function to_quat(a)
    if quatOrder == nil then
        local probe = try(function() return Quaternion.new(0.5, 0.1, 0.2, 0.3) end)
        quatOrder = (probe and math.abs(probe.w - 0.5) < 1e-6) and "wxyz" or "xyzw"
    end
    if quatOrder == "wxyz" then return Quaternion.new(a.w, a.x, a.y, a.z) end
    return Quaternion.new(a.x, a.y, a.z, a.w)
end

local function near(a, b, eps)
    return a and b and math.abs(a.x - b.x) < eps and math.abs(a.y - b.y) < eps and math.abs(a.z - b.z) < eps
        and (a.w == nil or math.abs(a.w - b.w) < eps)
end

-- ------------------------------------------------------------------ the hunter's face

local st = { info = "waiting for the hunter", joints = {}, faceAddr = nil, found = 0, total = 0,
             taken = 0, kept = 0, phases = {} }

local function face_object()
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    if not (master and try(function() return master:get_Valid() end)) then return nil end
    local chr = try(function() return master:get_Character() end)
    local go = chr and try(function() return chr:call("get_GameObject") end)
    local hxf = go and try(function() return go:call("get_Transform") end)
    local child = hxf and try(function() return hxf:call("get_Child") end)
    while child do
        local cgo = try(function() return child:call("get_GameObject") end)
        local mesh = cgo and try(function() return cgo:call("getComponent(System.Type)", sdk.typeof(MESH)) end)
        local res = mesh and try(function() return mesh:getMesh() end)
        local path = res and try(function() return res:ToString() end)
        if path and path:lower():find("character/ch00/", 1, true) then return child, path end
        child = try(function() return child:call("get_Next") end)
    end
    return nil
end

local function find_joints(fxf)
    local list = {}
    st.found, st.total = 0, 0
    for _, t in ipairs(tweaks()) do
        local sides = t[2] and { t[2] } or { "L", "R" }
        for _, side in ipairs(sides) do
            local name = t[1]:gsub("{s}", side)
            st.total = st.total + 1
            local j = try(function() return fxf:call("getJointByName", name) end)
            if j then st.found = st.found + 1 end
            list[name] = j or false
        end
    end
    return list
end

-- One pass: every tweak onto its joint, on top of the game's own pose this frame.
local function apply(phase)
    if not (config.enabled and st.fxf) then return end
    local head = try(function() return st.fxf:call("getJointByName", "Head") end)
    local hq = head and try(function() return head:call("get_Rotation") end)
    if not hq then return end
    hq = qnorm(q(hq))
    for _, t in ipairs(tweaks()) do
        local sides = t[2] and { t[2] } or { "L", "R" }
        for _, side in ipairs(sides) do
            local name = t[1]:gsub("{s}", side)
            local j = st.joints[name]
            local mirror = side == "R" and -1 or 1     -- offsets are written for the left side
            if j then
                local s = st.state[name] or {}
                st.state[name] = s
                local lp = try(function() return j:call("get_LocalPosition") end)
                local lr = try(function() return j:call("get_LocalRotation") end)
                local wr = try(function() return j:call("get_Rotation") end)
                if lp and lr and wr then
                    lp, lr, wr = { x = lp.x, y = lp.y, z = lp.z }, qnorm(q(lr)), qnorm(q(wr))
                    -- still what we set: the game left it; otherwise the game's is the new base
                    if not (near(lp, s.setP, 1e-6) and near(lr, s.setR, 1e-6)) then
                        s.baseP, s.baseR = lp, lr
                        st.taken = st.taken + 1
                    else
                        st.kept = st.kept + 1
                    end
                    -- the parent's world turn (world = parent * local), with our own change backed out
                    local parent = qnorm(qmul(wr, qconj(lr)))
                    local p, r = s.baseP, s.baseR
                    if t[3] then
                        local m = t[3]
                        local w = rotate(hq, { m[1] * mirror, m[2], m[3] })
                        local l = rotate(qconj(parent), w)
                        p = { x = p.x + l[1], y = p.y + l[2], z = p.z + l[3] }
                    end
                    if t[4] then
                        local a = t[4]
                        -- mirrored: a turn about x stays, about y or z reverses
                        local angle = t[5] * ((a[1] ~= 0 or mirror == 1) and 1 or -1)
                        local w = axis_angle(rotate(hq, a), angle)
                        r = qnorm(qmul(qmul(qmul(qconj(parent), w), parent), r))
                    end
                    try(function() j:call("set_LocalPosition", Vector3f.new(p.x, p.y, p.z)) end)
                    try(function() j:call("set_LocalRotation", to_quat(r)) end)
                    s.setP, s.setR = p, r
                end
            end
        end
    end
    st.phases[phase] = (st.phases[phase] or 0) + 1
end

-- Back to the game's own pose (switched off, script reset).
local function restore()
    for name, j in pairs(st.joints) do
        local s = st.state and st.state[name]
        if j and s and s.baseP then
            try(function() j:call("set_LocalPosition", Vector3f.new(s.baseP.x, s.baseP.y, s.baseP.z)) end)
            try(function() j:call("set_LocalRotation", to_quat(s.baseR)) end)
            s.setP, s.setR = nil, nil
        end
    end
end

local function write_debug(path)
    local d = { face = path, found = st.found, total = st.total, enabled = config.enabled,
                takenFromGame = st.lastTaken, keptOurs = st.lastKept, phases = st.phases, joints = {} }
    for name, s in pairs(st.state or {}) do
        d.joints[name] = { base = s.baseP and { s.baseP.x, s.baseP.y, s.baseP.z },
                           set = s.setP and { s.setP.x, s.setP.y, s.setP.z } }
    end
    pcall(json.dump_file, DEBUG_PATH, d)
end

local debugAt, lookAt = 0, 0
re.on_frame(function()
    local now = os.clock()
    if now < lookAt and st.fxf then return end
    lookAt = now + 1.0
    local fxf, path = face_object()
    if not fxf then
        st.fxf, st.info = nil, "waiting for the hunter's face"
        return
    end
    local addr = try(function() return fxf:get_address() end) or fxf
    if addr ~= st.faceAddr then
        restore()     -- the old face's joints, if it is still there (state below starts afresh)
        st.faceAddr, st.fxf, st.state = addr, fxf, {}
        st.joints = find_joints(fxf)
    end
    -- over the last second: the game set the joint anew (animated) / it still held ours
    st.info = string.format("face %s: %d / %d joints; last second: game's pose taken %d, ours kept %d",
        (path or "?"):match("ch00_%d+_%d+") or "?", st.found, st.total, st.taken, st.kept)
    st.lastTaken, st.lastKept, st.taken, st.kept = st.taken, st.kept, 0, 0
    if now >= debugAt then
        debugAt = now + 2
        write_debug(path)
    end
end)

local hooked = false
if re.on_application_entry then
    hooked = pcall(re.on_application_entry, "LateUpdateBehavior", function() apply("LateUpdateBehavior") end) or hooked
end
if re.on_pre_application_entry then
    for _, phase in ipairs({ "PrepareRendering", "BeginRendering" }) do
        hooked = pcall(re.on_pre_application_entry, phase, function() apply(phase) end) or hooked
    end
end
if not hooked then re.on_frame(function() apply("on_frame") end) end

re.on_script_reset(restore)

-- ------------------------------------------------------------------ menu

re.on_draw_ui(function()
    if not imgui.tree_node("MiquellaLight: Face") then return end
    local changed, c = false, false
    c, config.enabled = imgui.checkbox("Enabled", config.enabled); changed = changed or c
    if c and not config.enabled then restore() end
    imgui.text(st.info or "")
    c, config.droop = imgui.slider_float("Droopy eyes (mm)", config.droop, 0.0, 4.0); changed = changed or c
    c, config.lids = imgui.slider_float("Upper lids lowered (deg)", config.lids, 0.0, 20.0); changed = changed or c
    c, config.squint = imgui.slider_float("Lower lids raised (deg)", config.squint, 0.0, 10.0); changed = changed or c
    c, config.smile = imgui.slider_float("Smile corner (mm)", config.smile, 0.0, 4.0); changed = changed or c
    c, config.smileSide = imgui.combo("Smile side", config.smileSide, SIDES); changed = changed or c
    c, config.brow = imgui.slider_float("Brow lift (mm)", config.brow, 0.0, 3.0); changed = changed or c
    if imgui.button("Defaults") then
        config.droop, config.lids, config.squint, config.smile, config.smileSide, config.brow = 2.2, 11.0, 5.0, 2.6, 1, 0.0
        changed = true
    end
    if changed then
        if config.smileSide ~= st.side then   -- other joints for the smile and brow: back to the
            st.side = config.smileSide           -- game's pose, then look them up (state kept: a fresh
            restore()                            -- one would take our own offset as the base)
            if st.fxf then st.joints = find_joints(st.fxf) end
        end
        save_config()
    end
    imgui.tree_pop()
end)
