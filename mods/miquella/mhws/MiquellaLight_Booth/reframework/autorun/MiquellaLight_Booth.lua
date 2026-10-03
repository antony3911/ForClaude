-- MiquellaLight_Booth: a photo booth for checking the character in game. Puts the game camera at a
-- fixed spot relative to the hunter (face front / three-quarter / side, whole body front / side /
-- back), following the hunter's facing, so every look at the face or the robe has the same framing.
-- Off by default; menu "MiquellaLight: Booth", or Claude writes reframework/data/MiquellaLight/
-- booth.json: {"view": "face_front", "distance": 0.45, "yaw": 0, "height": 0} (read twice a second;
-- a view name not in VIEWS, or "off", turns it off).

local CMD_PATH = "MiquellaLight/booth.json"
local STATUS_PATH = "MiquellaLight/booth_status.json"

-- target: what it looks at, from the hunter (m: up, forward) or from the Head joint (head = true);
-- yaw: degrees around the hunter from its front (+ toward its left); distance: m.
local VIEWS = {
    { key = "off", name = "Off" },
    { key = "face_front", name = "Face, front", head = true, up = 0.07, fwd = 0.04, yaw = 0, distance = 0.45 },
    { key = "face_34", name = "Face, three-quarter", head = true, up = 0.07, fwd = 0.04, yaw = 40, distance = 0.45 },
    { key = "face_side", name = "Face, side", head = true, up = 0.07, fwd = 0.02, yaw = 90, distance = 0.45 },
    { key = "body_front", name = "Body, front", up = 0.95, fwd = 0.0, yaw = 0, distance = 2.6 },
    { key = "body_34", name = "Body, three-quarter", up = 0.95, fwd = 0.0, yaw = 40, distance = 2.6 },
    { key = "body_side", name = "Body, side", up = 0.95, fwd = 0.0, yaw = 90, distance = 2.6 },
    { key = "body_back", name = "Body, back", up = 0.95, fwd = 0.0, yaw = 180, distance = 2.6 },
    { key = "legs_front", name = "Legs and hem, front", up = 0.55, fwd = 0.0, yaw = 0, distance = 1.6 },
}
local VIEW_NAMES, VIEW_INDEX = {}, {}
for i, v in ipairs(VIEWS) do VIEW_NAMES[i], VIEW_INDEX[v.key] = v.name, i end

local config = {
    view = 1,
    distance = 1.0,     -- times the view's own distance
    yaw = 0.0,          -- degrees added to the view's
    height = 0.0,       -- cm added to the target's height
    plusZ = false,      -- the camera looks along its +Z (RE Engine: -Z, it seems; flip if it looks away)
}
local st = { applied = 0, err = nil, lastCmd = nil, cmdAt = 0 }

local function try(fn, ...)
    local ok, r = pcall(fn, ...)
    if ok then return r end
    st.err = tostring(r)
    return nil
end

local function hunter_xf()
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local go = chr and try(function() return chr:call("get_GameObject") end)
    return go and try(function() return go:call("get_Transform") end)
end

local function v3(x, y, z) return Vector3f.new(x, y, z) end

-- unit quaternion (w, x, y, z) product
local function qmul(a, b)
    return { a[1] * b[1] - a[2] * b[2] - a[3] * b[3] - a[4] * b[4],
             a[1] * b[2] + a[2] * b[1] + a[3] * b[4] - a[4] * b[3],
             a[1] * b[3] - a[2] * b[4] + a[3] * b[1] + a[4] * b[2],
             a[1] * b[4] + a[2] * b[3] - a[3] * b[2] + a[4] * b[1] }
end

-- rotation that turns the camera's forward (-Z, or +Z) onto the direction d (x, y, z)
local function look_rotation(dx, dy, dz)
    local len = math.sqrt(dx * dx + dy * dy + dz * dz)
    if len < 1e-6 then return nil end
    dx, dy, dz = dx / len, dy / len, dz / len
    local yaw, pitch
    if config.plusZ then
        yaw, pitch = math.atan(dx, dz), -math.asin(dy)
    else
        yaw, pitch = math.atan(-dx, -dz), math.asin(dy)
    end
    local qy = { math.cos(yaw / 2), 0, math.sin(yaw / 2), 0 }
    local qx = { math.cos(pitch / 2), math.sin(pitch / 2), 0, 0 }
    local q = qmul(qy, qx)
    return Quaternion.new(q[1], q[2], q[3], q[4])
end

local function place()
    local view = VIEWS[config.view]
    if not view or view.key == "off" then return end
    local hxf = hunter_xf()
    local cam = sdk.get_primary_camera()
    local cxf = cam and try(function() return cam:call("get_GameObject"):call("get_Transform") end)
    if not (hxf and cxf) then return end
    local pos = try(function() return hxf:call("get_Position") end)
    local fz = try(function() return hxf:call("get_AxisZ") end)
    if not (pos and fz) then return end
    -- the hunter's front, flat
    local fl = math.sqrt(fz.x * fz.x + fz.z * fz.z)
    if fl < 1e-6 then return end
    local fx, fzz = fz.x / fl, fz.z / fl
    local base = pos
    if view.head then
        local j = try(function() return hxf:call("getJointByName", "Head") end)
        base = j and try(function() return j:call("get_Position") end) or pos
    end
    local h = view.up + config.height / 100
    local tx, ty, tz = base.x + fx * view.fwd, base.y + h, base.z + fzz * view.fwd
    if view.head then ty = base.y + h end
    if not view.head then tx, ty, tz = pos.x + fx * view.fwd, pos.y + h, pos.z + fzz * view.fwd end
    -- around the hunter by yaw from its front (+ toward its left: the front turned counter-clockwise from above)
    local a = math.rad(view.yaw + config.yaw)
    local ox = fx * math.cos(a) + fzz * math.sin(a)
    local oz = -fx * math.sin(a) + fzz * math.cos(a)
    local d = view.distance * config.distance
    local cx, cy, cz = tx + ox * d, ty, tz + oz * d
    local rot = look_rotation(tx - cx, ty - cy, tz - cz)
    if not rot then return end
    try(function() cxf:call("set_Position", v3(cx, cy, cz)) end)
    try(function() cxf:call("set_Rotation", rot) end)
    st.applied = st.applied + 1
end

local function read_command()
    local now = os.clock()
    if now - st.cmdAt < 0.5 then return end
    st.cmdAt = now
    local cmd = json.load_file(CMD_PATH)
    if type(cmd) ~= "table" then return end
    local key = json.dump_string and json.dump_string(cmd) or tostring(cmd.view) .. tostring(cmd.distance)
        .. tostring(cmd.yaw) .. tostring(cmd.height) .. tostring(cmd.plusZ)
    if key == st.lastCmd then return end
    st.lastCmd = key
    if cmd.view then config.view = VIEW_INDEX[cmd.view] or 1 end
    if type(cmd.distance) == "number" then config.distance = cmd.distance end
    if type(cmd.yaw) == "number" then config.yaw = cmd.yaw end
    if type(cmd.height) == "number" then config.height = cmd.height end
    if type(cmd.plusZ) == "boolean" then config.plusZ = cmd.plusZ end
    json.dump_file(STATUS_PATH, { view = VIEWS[config.view].key, distance = config.distance, yaw = config.yaw,
        height = config.height, plusZ = config.plusZ, applied = st.applied, err = st.err })
end

-- After the game's own camera update, before the frame is drawn.
local hooked = {}
for _, phase in ipairs({ "LateUpdateBehavior", "BeginRendering" }) do
    if re.on_pre_application_entry then
        hooked[phase] = pcall(re.on_pre_application_entry, phase, function() place() end)
    end
end

re.on_frame(function() read_command() end)

re.on_draw_ui(function()
    if not imgui.tree_node("MiquellaLight: Booth") then return end
    local c
    c, config.view = imgui.combo("View", config.view, VIEW_NAMES)
    c, config.distance = imgui.slider_float("Distance (x the view's)", config.distance, 0.3, 3.0)
    c, config.yaw = imgui.slider_float("Turn (deg)", config.yaw, -180.0, 180.0)
    c, config.height = imgui.slider_float("Height (cm)", config.height, -60.0, 60.0)
    c, config.plusZ = imgui.checkbox("Camera looks along +Z (flip if it faces away)", config.plusZ)
    imgui.text(string.format("placed %d times%s", st.applied, st.err and ("; last error: " .. st.err) or ""))
    imgui.tree_pop()
end)
