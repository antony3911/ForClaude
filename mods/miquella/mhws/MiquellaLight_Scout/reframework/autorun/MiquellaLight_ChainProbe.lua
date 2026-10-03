-- MiquellaLight: Chain probe (Monster Hunter Wilds, REFramework) -- a test, remove after use.
--
-- Question (robe, 2026-10-03): can an object our script makes carry swinging physics (via.motion.Chain2)?
-- The robe's skirt would be spawned like the body (SameJointsConstraint on the hunter), so the
-- probe does the same with copies of the hunter's own hair (the ch01 object with a chain2 asset;
-- the female hunter's eyebrows are under ch01 too): same mesh, material and chain2 asset, plus
-- components of our own. Three copies, each with a different set of components (VARIANTS), sit on
-- top of the real hair (which can be hidden from the menu).
--
-- First run (2026-10-03): a created Chain2 component is fine (no crash). The game's parts with a
-- chain also carry via.motion.ChildSecondary and via.motion.JointConstraints, hence the variants.
--
-- Written for Claude to read, every second, reframework/data/MiquellaLight/chain_probe.json:
-- - the components (type, chain asset, SameJointsConstraint) of the hunter's hair and outfit objects;
-- - for up to 8 hair joints the hunter's skeleton does not have (free for the chain to move), how
--   far each moved in the Head joint's space over the last 5 s and the most seen in any 5 s, on
--   each copy and on the real hair. Physics working: a copy's numbers close to the real hair's.
--   Not working: ~0 (rigid with the head).
-- Every game call is wrapped in pcall.

local OUT = "MiquellaLight/chain_probe.json"
local MESH, CHAIN2 = "via.render.Mesh", "via.motion.Chain2"
local VARIANTS = {
    { key = "chain", comps = { CHAIN2 } },
    { key = "chain+secondary", comps = { CHAIN2, "via.motion.ChildSecondary" } },
    { key = "chain+secondary+constraints", comps = { CHAIN2, "via.motion.ChildSecondary", "via.motion.JointConstraints" } },
}
local WINDOW = 5.0        -- s of samples the ranges cover
local MAX_JOINTS = 8

local config = { on = true, hideReal = false }   -- a hidden mesh may stop simulating: keep the real hair as the reference
local st = { info = "waiting for the hunter" }
for _, v in ipairs(VARIANTS) do v.st = {} end

local function try(fn, ...)
    local ok, r = pcall(fn, ...)
    if ok then return r end
    return nil
end

local function holder(typeName, path)
    return try(function()
        local res = sdk.create_resource(typeName, path):add_ref()
        return res:create_holder(typeName .. "Holder"):add_ref()
    end)
end

local function resource_path(res)
    local s = res and try(function() return res:ToString() end)
    if not s then return nil end
    return (s:gsub("^Resource%[", ""):gsub("%]$", ""))
end

local function component(go, typeName)
    return try(function() return go:call("getComponent(System.Type)", sdk.typeof(typeName)) end)
end

local function hunter_xf()
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local go = chr and try(function() return chr:call("get_GameObject") end)
    return go and try(function() return go:call("get_Transform") end)
end

local function components_of(go)
    local out = {}
    local arr = try(function() return go:call("get_Components") end)
    local n = arr and (try(function() return arr:get_size() end) or 0) or 0
    for i = 0, n - 1 do
        local c = try(function() return arr:get_element(i) end)
        out[#out + 1] = c and try(function() return c:get_type_definition():get_full_name() end) or "?"
    end
    return out
end

local function describe(go)
    local mesh = component(go, MESH)
    local chain = component(go, CHAIN2)
    local xf = try(function() return go:call("get_Transform") end)
    return {
        name = try(function() return go:call("get_Name") end),
        mesh = mesh and resource_path(try(function() return mesh:getMesh() end)),
        mdf2 = mesh and resource_path(try(function() return mesh:get_Material() end)),
        chain = chain and resource_path(try(function() return chain:get_ChainAsset() end)),
        chainEnabled = chain and try(function() return chain:call("get_Enabled") end),
        components = components_of(go),
        sameJoints = xf and try(function() return xf:call("get_SameJointsConstraint") end),
        parentJoint = xf and try(function() return xf:call("get_ParentJoint") end),
        joints = xf and try(function() return xf:call("get_Joints"):get_size() end),
    }
end

-- The hunter's children with a model under character/ch0*; the hair is the ch01 one with a chain.
local function scan(hxf)
    local found = { parts = {} }
    local function walk(xf, depth)
        if depth > 6 then return end
        local child = try(function() return xf:call("get_Child") end)
        while child do
            local go = try(function() return child:call("get_GameObject") end)
            local mesh = go and component(go, MESH)
            local path = mesh and resource_path(try(function() return mesh:getMesh() end))
            local low = path and path:lower() or ""
            if low:find("character/ch0", 1, true) then
                local d = describe(go)
                found.parts[#found.parts + 1] = d
                if low:find("character/ch01/", 1, true) and d.chain and not found.hair then
                    found.hair, found.hairGo = d, go
                end
            end
            walk(child, depth + 1)
            child = try(function() return child:call("get_Next") end)
        end
    end
    walk(hxf, 1)
    return found
end

local function find_leftover(name)
    local sm = sdk.get_native_singleton("via.SceneManager")
    local scene = sm and try(function()
        return sdk.call_native_func(sm, sdk.find_type_definition("via.SceneManager"), "get_CurrentScene()")
    end)
    return scene and try(function() return scene:call("findGameObject(System.String)", name) end)
end

local function create_object(name)
    local td = sdk.find_type_definition("via.GameObject")
    local m = td and try(function() return td:get_method("create(System.String)") end)
    local go = m and try(function() return m:call(nil, name) end)
    if not go then return nil end
    go = try(function() return go:add_ref() end) or go
    try(function() go:call(".ctor") end)
    return go
end

local function add_component(go, typeName)
    local c = component(go, typeName)
    if c then return c, "existing" end
    c = try(function() return go:call("createComponent(System.Type)", sdk.typeof(typeName)) end)
    if not c then return nil, "createComponent failed" end
    c = try(function() return c:add_ref() end) or c
    try(function() c:call(".ctor()") end)
    return c, "created"
end

local function identity_quat()
    local probe = try(function() return Quaternion.new(0.5, 0.1, 0.2, 0.3) end)
    if probe and math.abs(probe.w - 0.5) < 1e-6 then return Quaternion.new(1, 0, 0, 0) end
    return Quaternion.new(0, 0, 0, 1)
end

-- math on Vector3f / Quaternion fields
local function unrotate(q, v)
    local x, y, z, w = -q.x, -q.y, -q.z, q.w
    local tx = 2 * (y * v[3] - z * v[2])
    local ty = 2 * (z * v[1] - x * v[3])
    local tz = 2 * (x * v[2] - y * v[1])
    return { v[1] + w * tx + (y * tz - z * ty), v[2] + w * ty + (z * tx - x * tz), v[3] + w * tz + (x * ty - y * tx) }
end

local function in_head(hxf, joint)
    local h = try(function() return hxf:call("getJointByName", "Head") end)
    local hp = h and try(function() return h:call("get_Position") end)
    local hq = h and try(function() return h:call("get_Rotation") end)
    local p = joint and try(function() return joint:call("get_Position") end)
    if not (hp and hq and p) then return nil end
    return unrotate(hq, { p.x - hp.x, p.y - hp.y, p.z - hp.z })
end

local function make_copy(v, hxf, found)
    local s = v.st
    local name = "MiquellaLight_ChainProbe_" .. v.key
    local go = find_leftover(name) or create_object(name)
    if not go then s.info = "could not create a GameObject"; return end
    local mesh, how = add_component(go, MESH)
    s.meshComp = how
    if not mesh then s.info = "could not add a mesh"; return end
    local h = found.hair
    local m = h.mesh and holder("via.render.MeshResource", h.mesh)
    local d = h.mdf2 and holder("via.render.MeshMaterialResource", h.mdf2)
    s.meshLoaded, s.mdfLoaded = m ~= nil, d ~= nil
    try(function() mesh:setMesh(m) end)
    try(function() mesh:set_Material(d) end)
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do try(function() mesh:setMaterialsEnable(i, true) end) end
    try(function() mesh:set_Enabled(true) end)
    -- Render settings as on the hunter's own hair (a created mesh has StencilValue 0: no ambient light).
    local real = component(found.hairGo, MESH)
    for _, k in ipairs({ "StencilValue", "ShadowCastMode" }) do
        local val = real and try(function() return real:call("get_" .. k) end)
        if val ~= nil then try(function() mesh:call("set_" .. k, val) end) end
    end
    local xf = try(function() return go:call("get_Transform") end)
    try(function() xf:call("set_Parent", hxf) end)
    s.sameJoints = try(function() xf:call("set_SameJointsConstraint", true); return true end) and "on" or "failed"
    try(function() xf:call("set_LocalPosition", Vector3f.new(0, 0, 0)) end)
    try(function() xf:call("set_LocalRotation", identity_quat()) end)
    s.comps = {}
    for _, t in ipairs(v.comps) do
        local c, res = add_component(go, t)
        s.comps[t] = res
        if t == CHAIN2 then s.chain = c end
    end
    local c = s.chain and h.chain and holder("via.motion.Chain2Resource", h.chain)
    s.chainLoaded = c ~= nil
    s.chainSet = s.chain and c and try(function() s.chain:set_ChainAsset(c); return true end) or false
    if s.chain then try(function() s.chain:call("set_Enabled", true) end) end
    s.go, s.xf = go, xf
    s.madeAt = os.clock()
    s.info = "made"
end

-- Joints of the hair the hunter's skeleton does not have (the chain is free to move them), farthest from the head first.
local function pick_joints(hxf, xf)
    local arr = try(function() return xf:call("get_Joints") end)
    local n = arr and (try(function() return arr:get_size() end) or 0) or 0
    local free = {}
    for i = 0, n - 1 do
        local j = try(function() return arr:get_element(i) end)
        local name = j and try(function() return j:call("get_Name") end)
        if name and not try(function() return hxf:call("getJointByName", name) end) then
            local p = in_head(hxf, j)
            if p then free[#free + 1] = { name = name, d = math.sqrt(p[1] ^ 2 + p[2] ^ 2 + p[3] ^ 2) } end
        end
    end
    st.jointCount, st.freeCount = n, #free
    table.sort(free, function(a, b) return a.d > b.d end)
    local picked = {}
    for i = 1, math.min(MAX_JOINTS, #free) do picked[i] = { name = free[i].name, real = {}, peak = {} } end
    return picked
end

local function sample(list, p, now)
    if p then list[#list + 1] = { t = now, p = p } end
    while #list > 0 and now - list[1].t > WINDOW do table.remove(list, 1) end
end

local function range(list)
    if #list < 2 then return nil end
    local lo, hi = { 1e9, 1e9, 1e9 }, { -1e9, -1e9, -1e9 }
    for _, s in ipairs(list) do
        for k = 1, 3 do lo[k] = math.min(lo[k], s.p[k]); hi[k] = math.max(hi[k], s.p[k]) end
    end
    return math.floor(math.sqrt((hi[1] - lo[1]) ^ 2 + (hi[2] - lo[2]) ^ 2 + (hi[3] - lo[3]) ^ 2) * 1000 + 0.5)   -- mm
end

local function peak(tbl, key, val)
    if val and (tbl[key] == nil or val > tbl[key]) then tbl[key] = val end
    return tbl[key]
end

local nextWrite, found, hipMoves, peaks = 0, nil, {}, {}

re.on_frame(function()
    local now = os.clock()
    local hxf = hunter_xf()
    if not hxf then st.info = "waiting for the hunter"; return end
    if not config.on then
        for _, v in ipairs(VARIANTS) do
            if v.st.go then try(function() v.st.go:call("set_DrawSelf", false) end) end
        end
        if found and found.hairGo then try(function() found.hairGo:call("set_DrawSelf", true) end) end
        return
    end
    if not st.oldHidden then   -- the first run's single copy (of the eyebrows), left in the scene
        local old = find_leftover("MiquellaLight_ChainProbe")
        if old then try(function() old:call("set_DrawSelf", false) end) end
        st.oldHidden = true
    end
    if not found or not found.hair then found = scan(hxf) end
    if not found.hair then st.info = "no hair object with a chain under the hunter"; return end
    st.info = "running"
    for _, v in ipairs(VARIANTS) do
        if not v.st.go then make_copy(v, hxf, found) end
        if v.st.go then try(function() v.st.go:call("set_DrawSelf", true) end) end
    end
    try(function() found.hairGo:call("set_DrawSelf", not config.hideReal) end)
    local first = VARIANTS[1].st
    if not st.joints and first.xf and now - first.madeAt > 1.0 then st.joints = pick_joints(hxf, first.xf) end
    local realXf = try(function() return found.hairGo:call("get_Transform") end)
    for _, j in ipairs(st.joints or {}) do
        for _, v in ipairs(VARIANTS) do
            j[v.key] = j[v.key] or {}
            local jj = v.st.xf and try(function() return v.st.xf:call("getJointByName", j.name) end)
            sample(j[v.key], in_head(hxf, jj), now)
        end
        sample(j.real, in_head(hxf, realXf and try(function() return realXf:call("getJointByName", j.name) end)), now)
    end
    local hip = try(function() return hxf:call("getJointByName", "Hip") end)
    local hp = hip and try(function() return hip:call("get_Position") end)
    sample(hipMoves, hp and { hp.x, hp.y, hp.z }, now)
    if now >= nextWrite then
        nextWrite = now + 1.0
        local rows = {}
        for _, j in ipairs(st.joints or {}) do
            local r = { joint = j.name, real = range(j.real) }
            r.realPeak = peak(j.peak, "real", r.real)
            for _, v in ipairs(VARIANTS) do
                r[v.key] = range(j[v.key])
                r[v.key .. "Peak"] = peak(j.peak, v.key, r[v.key])
            end
            rows[#rows + 1] = r
        end
        st.rows = rows
        st.hipMovedMm = range(hipMoves)
        st.hipPeakMm = peak(peaks, "hip", st.hipMovedMm)
        local copies = {}
        for _, v in ipairs(VARIANTS) do
            local s = v.st
            copies[v.key] = { info = s.info, meshLoaded = s.meshLoaded, mdfLoaded = s.mdfLoaded,
                sameJoints = s.sameJoints, comps = s.comps, chainLoaded = s.chainLoaded, chainSet = s.chainSet == true,
                chain = s.chain and resource_path(try(function() return s.chain:get_ChainAsset() end)),
                components = s.go and components_of(s.go) }
        end
        pcall(json.dump_file, OUT, {
            info = st.info, copies = copies, jointCount = st.jointCount, freeJoints = st.freeCount,
            hipMovedMm = st.hipMovedMm, hipPeakMm = st.hipPeakMm, joints = rows,
            hair = found.hair, parts = found.parts,
        })
    end
end)

re.on_draw_ui(function()
    if not imgui.tree_node("MiquellaLight Chain probe (test)") then return end
    local c
    c, config.on = imgui.checkbox("Copies of the hair with our own physics", config.on)
    c, config.hideReal = imgui.checkbox("Hide the real hair", config.hideReal)
    imgui.text("Status: " .. tostring(st.info) .. ", hunter moved (5 s): " .. tostring(st.hipMovedMm) .. " mm")
    for _, v in ipairs(VARIANTS) do
        imgui.text(v.key .. ": " .. tostring(v.st.info) .. ", chain set " .. tostring(v.st.chainSet))
    end
    for _, r in ipairs(st.rows or {}) do
        local parts = { r.joint, "real " .. tostring(r.realPeak) }
        for _, v in ipairs(VARIANTS) do parts[#parts + 1] = v.key .. " " .. tostring(r[v.key .. "Peak"]) end
        imgui.text(table.concat(parts, " / ") .. " mm (most in 5 s)")
    end
    imgui.tree_pop()
end)
