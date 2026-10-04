-- MiquellaLight_InstanceProbe: diagnostic + experiment. Looks at the per-instance render data the
-- game gives its own hunter parts and our script-created MiquellaLight_Body lacks.
-- Probe (read only, written to instance_probe.json 3 s after the hunter is found and again when
-- instance_test.json's "n" changes): every mesh under the hunter: its components (app.* ones with
-- their fields), and its via.render.Mesh getters whose names have UserParam / MaterialParam /
-- Instance; plus the via.render.Mesh methods with those words (name and parameter types).
-- Experiment (every frame while instance_test.json has "on": true), e.g.
--   {"n": 1, "on": true, "from": "Player_Face", "copy": ["UserParamPerInstance"]}
-- copies each listed getter's value from the "from" mesh (GameObject name, or a substring of its
-- mesh path) onto our body (and robe) with the matching set_ method. What it set goes to
-- instance_test_status.json.
-- Twin (while "twin": {"mesh": "<path>.mesh", "mdf2": "<path>.mdf2"} is in the command): spawns
-- MiquellaLight_Twin the way the character script spawns our body (a bare GameObject + Mesh, on
-- the hunter with SameJointsConstraint, StencilValue / ShadowCastMode from the face), e.g. with
-- the game's own innerwear body: dark like ours = the game sets up its own parts differently at
-- run time; normal = the difference is in our mesh data. "twin": false hides it.
-- Why (2026-10-04): with the same material, textures and parameters as the game's own skin part,
-- our body still comes out dark brown; mesh_diff.json shows the face with UserParamPerInstance
-- 44182 and 13 MaterialParams, our body 0 and 0.

local OUT = "MiquellaLight/instance_probe.json"
local CMD = "MiquellaLight/instance_test.json"
local STATUS = "MiquellaLight/instance_test_status.json"
local OURS = { MiquellaLight_Body = true, MiquellaLight_Robe = true, MiquellaLight_Twin = true }
local WORDS = { "UserParam", "MaterialParam", "Instance" }
local cmd, readAt, lastN, foundAt, probed, statusAt = {}, 0, nil, nil, false, 0
local twin = { go = nil, mesh = nil, key = nil }   -- MiquellaLight_Twin (see run_twin)

local function try(fn, ...)
    local ok, r = pcall(fn, ...)
    if ok then return r end
    return nil
end

local function str(v)
    local t = type(v)
    if t == "number" or t == "boolean" or t == "string" then return v end
    if v == nil then return "nil" end
    local s = try(function() return v:call("ToString()") end) or try(function() return tostring(v) end)
    return s or "?"
end

local function has_word(name)
    for _, w in ipairs(WORDS) do if name:find(w) then return true end end
    return false
end

local function each_type(td, fn)
    while td do
        local tn = try(function() return td:get_full_name() end) or ""
        if tn == "via.Component" or tn == "System.Object" or tn == "via.Behavior" then break end
        fn(td)
        td = try(function() return td:get_parent_type() end)
    end
end

local function mesh_values(mesh)
    local out = {}
    each_type(try(function() return mesh:get_type_definition() end), function(td)
        for _, m in ipairs(try(function() return td:get_methods() end) or {}) do
            local name = try(function() return m:get_name() end) or ""
            if has_word(name) and name:match("^get") and try(function() return m:get_num_params() end) == 0 then
                local ok, r = pcall(function() return m:call(mesh) end)
                out[name] = ok and str(r) or "error"
            end
        end
    end)
    return out
end

local function mesh_methods(mesh)
    local out = {}
    each_type(try(function() return mesh:get_type_definition() end), function(td)
        for _, m in ipairs(try(function() return td:get_methods() end) or {}) do
            local name = try(function() return m:get_name() end) or ""
            if has_word(name) then
                local ps = {}
                for _, p in ipairs(try(function() return m:get_param_types() end) or {}) do
                    table.insert(ps, try(function() return p:get_full_name() end) or "?")
                end
                local rt = try(function() return m:get_return_type():get_full_name() end) or "?"
                table.insert(out, rt .. " " .. name .. "(" .. table.concat(ps, ", ") .. ")")
            end
        end
    end)
    table.sort(out)
    return out
end

local function fields(obj)
    local out = {}
    each_type(try(function() return obj:get_type_definition() end), function(td)
        for _, f in ipairs(try(function() return td:get_fields() end) or {}) do
            local name = try(function() return f:get_name() end) or "?"
            if not try(function() return f:is_static() end) then
                local ft = try(function() return f:get_type():get_full_name() end) or "?"
                local ok, v = pcall(function() return f:get_data(obj) end)
                out[name] = ft .. " = " .. tostring(ok and str(v) or "error")
            end
        end
    end)
    return out
end

local function walk(xf, depth, out)
    if depth > 6 then return end
    local child = try(function() return xf:call("get_Child") end)
    while child do
        local go = try(function() return child:call("get_GameObject") end)
        if go then table.insert(out, go) end
        walk(child, depth + 1, out)
        child = try(function() return child:call("get_Next") end)
    end
end

local function get_mesh(go)
    return try(function() return go:call("getComponent(System.Type)", sdk.typeof("via.render.Mesh")) end)
end

local function mesh_path(mesh)
    local res = mesh and try(function() return mesh:getMesh() end)
    return res and (try(function() return res:ToString() end) or "") or ""
end

local function hunter_xf()
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local hgo = chr and try(function() return chr:call("get_GameObject") end)
    return hgo and try(function() return hgo:call("get_Transform") end)
end

local function probe(hxf)
    local all, result, methodsDone = {}, { parts = {} }, false
    walk(hxf, 0, all)
    for _, go in ipairs(all) do
        local mesh = get_mesh(go)
        if mesh then
            local name = str(try(function() return go:call("get_Name") end))
            local d = { mesh = mesh_path(mesh), values = mesh_values(mesh), components = {}, app = {} }
            d.enabled = try(function() return go:call("get_DrawSelf") end)
            local arr = try(function() return go:call("get_Components") end)
            for _, c in ipairs(arr and (try(function() return arr:get_elements() end) or {}) or {}) do
                local tn = try(function() return c:get_type_definition():get_full_name() end) or "?"
                table.insert(d.components, tn)
                if tn:match("^app%.") or tn:match("^ace%.") then d.app[tn] = fields(c) end
            end
            if not methodsDone then result.meshMethods = mesh_methods(mesh); methodsDone = true end
            result.parts[name] = d
        end
    end
    json.dump_file(OUT, result)
end

local function find_source(all, from)
    for _, go in ipairs(all) do
        local name = str(try(function() return go:call("get_Name") end))
        local mesh = get_mesh(go)
        if mesh and not OURS[name] and (name == from or mesh_path(mesh):find(from, 1, true)) then return mesh end
    end
    return nil
end

local function experiment(hxf)
    local all, status = {}, { set = {} }
    walk(hxf, 0, all)
    -- "set": {"Name": value} sets a literal value on our meshes
    for key, v in pairs(type(cmd.set) == "table" and cmd.set or {}) do
        for _, go in ipairs(all) do
            local name = str(try(function() return go:call("get_Name") end))
            local mesh = OURS[name] and get_mesh(go)
            if mesh then
                local ok = pcall(function() mesh:call("set_" .. key, v) end)
                status.set[name .. "." .. key] = { to = v, ok = ok, now = str(try(function() return mesh:call("get_" .. key) end)) }
            end
        end
    end
    local src = find_source(all, cmd.from or "Player_Face")
    status.source = src and mesh_path(src) or "not found: " .. tostring(cmd.from)
    if not src then return status end
    for _, go in ipairs(all) do
        local name = str(try(function() return go:call("get_Name") end))
        local mesh = OURS[name] and get_mesh(go)
        if mesh then
            for _, key in ipairs(cmd.copy or {}) do
                local v = try(function() return src:call("get_" .. key) end)
                local ok = v ~= nil and pcall(function() mesh:call("set_" .. key, v) end)
                local now = try(function() return mesh:call("get_" .. key) end)
                status.set[name .. "." .. key] = { from = str(v), ok = ok and true or false, now = str(now) }
            end
        end
    end
    return status
end

-- Every simple getter of a mesh plus its material variables, for twin_diff.json.
local function full_state(mesh)
    local out = {}
    each_type(try(function() return mesh:get_type_definition() end), function(td)
        for _, m in ipairs(try(function() return td:get_methods() end) or {}) do
            local name = try(function() return m:get_name() end) or ""
            local rt = try(function() return m:get_return_type() end)
            local simple = rt and try(function() return rt:is_value_type() end)
            if out["mesh." .. name] == nil and simple and name:match("^get_")
                and try(function() return m:get_num_params() end) == 0 then
                local ok, r = pcall(function() return m:call(mesh) end)
                out["mesh." .. name] = ok and str(r) or "error"
            end
        end
    end)
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        local mname = try(function() return mesh:getMaterialName(i) end) or ("#" .. i)
        local vn = try(function() return mesh:getMaterialVariableNum(i) end) or 0
        for j = 0, vn - 1 do
            local vname = try(function() return mesh:getMaterialVariableName(i, j) end) or ("#" .. j)
            local f4 = try(function() return mesh:getMaterialFloat4(i, j) end)
            local v = f4 and string.format("%.4g %.4g %.4g %.4g", f4.x, f4.y, f4.z, f4.w)
                or str(try(function() return mesh:getMaterialFloat(i, j) end))
            out["mat." .. mname .. "." .. vname] = v
        end
        out["mat." .. mname .. ".enabled"] = str(try(function() return mesh:getMaterialsEnable(i) end))
    end
    return out
end

local function twin_diff(hxf)
    local all = {}
    walk(hxf, 0, all)
    local name = tostring((cmd.twin or {}).mesh):match("([^/]+)%.mesh$")
    local real
    for _, go in ipairs(all) do
        if str(try(function() return go:call("get_Name") end)) == name then real = get_mesh(go) end
    end
    if not (real and twin.mesh) then return end
    local a, b, diff, same = full_state(real), full_state(twin.mesh), {}, 0
    for k, v in pairs(a) do
        if tostring(b[k]) ~= tostring(v) then diff[k] = { real = v, twin = b[k] } else same = same + 1 end
    end
    for k, v in pairs(b) do if a[k] == nil then diff[k] = { real = "missing", twin = v } end end
    json.dump_file("MiquellaLight/twin_diff.json", { same = same, diff = diff })
end

local holders = {}
local function holder(typeName, path)
    local key = typeName .. "|" .. path
    if holders[key] == nil then
        holders[key] = try(function()
            local res = sdk.create_resource(typeName, path):add_ref()
            return res:create_holder(typeName .. "Holder"):add_ref()
        end) or false
    end
    return holders[key] or nil
end


local function face_of(all)
    for _, go in ipairs(all) do
        local mesh = get_mesh(go)
        if mesh and mesh_path(mesh):lower():find("character/ch00/", 1, true) then return mesh end
    end
    return nil
end

local function run_twin(hxf, status)
    local want = cmd.twin
    if type(want) ~= "table" then
        if twin.go then
            try(function() twin.go:call("set_DrawSelf", false) end)
            local all = {}
            walk(hxf, 0, all)
            for _, go in ipairs(all) do
                if str(try(function() return go:call("get_Name") end)) == "MiquellaLight_Body" then
                    local m = get_mesh(go)
                    if m then try(function() m:set_Enabled(true) end) end
                end
            end
        end
        return
    end
    if not twin.go then
        local sm = sdk.get_native_singleton("via.SceneManager")
        local scene = sm and try(function()
            return sdk.call_native_func(sm, sdk.find_type_definition("via.SceneManager"), "get_CurrentScene()")
        end)
        twin.go = scene and try(function() return scene:call("findGameObject(System.String)", "MiquellaLight_Twin") end)
        if not twin.go then
            local m = sdk.find_type_definition("via.GameObject"):get_method("create(System.String)")
            twin.go = try(function() return m:call(nil, "MiquellaLight_Twin") end)
            twin.go = twin.go and (try(function() return twin.go:add_ref() end) or twin.go)
            if twin.go then try(function() twin.go:call(".ctor") end) end
        end
        if not twin.go then status.twin = "could not create"; return end
        twin.mesh = get_mesh(twin.go)
        if not twin.mesh then
            twin.mesh = try(function() return twin.go:call("createComponent(System.Type)", sdk.typeof("via.render.Mesh")) end)
            twin.mesh = twin.mesh and (try(function() return twin.mesh:add_ref() end) or twin.mesh)
            if twin.mesh then try(function() twin.mesh:call(".ctor()") end) end
        end
        twin.key = nil
    end
    local key = tostring(want.mesh) .. "|" .. tostring(want.mdf2)
    local empty = twin.mesh and (try(function() return twin.mesh:get_MaterialNum() end) or 0) == 0
    if twin.mesh and (twin.key ~= key or empty) and os.clock() >= (twin.retryAt or 0) then
        twin.retryAt = os.clock() + 1   -- a resource the game has not loaded yet comes in later
        local m = holder("via.render.MeshResource", want.mesh)
        local d = holder("via.render.MeshMaterialResource", want.mdf2)
        if m and d then
            try(function() twin.mesh:setMesh(m) end)
            try(function() twin.mesh:set_Material(d) end)
            local n = try(function() return twin.mesh:get_MaterialNum() end) or 0
            for i = 0, n - 1 do try(function() twin.mesh:setMaterialsEnable(i, true) end) end
            try(function() twin.mesh:set_Enabled(true) end)
            twin.key = key
        end
    end
    local xf = try(function() return twin.go:call("get_Transform") end)
    local parent = xf and try(function() return xf:call("get_Parent") end)
    if xf and not parent then
        try(function() xf:call("set_Parent", hxf) end)
        try(function() xf:call("set_SameJointsConstraint", true) end)
        try(function() xf:call("set_LocalPosition", Vector3f.new(0, 0, 0)) end)
    end
    try(function() twin.go:call("set_DrawSelf", true) end)
    local all = {}
    walk(hxf, 0, all)
    -- "hideBody": our body's mesh off (the character script keeps the hunter's armor hidden while
    -- its Body is on), so the twin is seen alone
    for _, go in ipairs(all) do
        if str(try(function() return go:call("get_Name") end)) == "MiquellaLight_Body" then
            local m = get_mesh(go)
            if m then try(function() m:set_Enabled(not want.hideBody) end) end
        end
    end
    local face = face_of(all)
    for _, name in ipairs({ "StencilValue", "ShadowCastMode", "BeautyMaskFlag", "UserParamPerInstance" }) do
        local v = face and try(function() return face:call("get_" .. name) end)
        if v ~= nil then try(function() twin.mesh:call("set_" .. name, v) end) end
    end
    -- the skin tone and stain slot the game sets on its own skin materials, from the face (as the
    -- character script does for our body)
    local fm, fvars = nil, {}
    local fn = face and (try(function() return face:get_MaterialNum() end) or 0) or 0
    for i = 0, fn - 1 do
        if try(function() return face:getMaterialName(i) end) == "face" then fm = i end
    end
    if fm then
        for j = 0, (try(function() return face:getMaterialVariableNum(fm) end) or 0) - 1 do
            fvars[try(function() return face:getMaterialVariableName(fm, j) end) or ""] = j
        end
        for i = 0, (try(function() return twin.mesh:get_MaterialNum() end) or 0) - 1 do
            for j = 0, (try(function() return twin.mesh:getMaterialVariableNum(i) end) or 0) - 1 do
                local vn = try(function() return twin.mesh:getMaterialVariableName(i, j) end)
                local fj = vn and fvars[vn]
                local v = fj and try(function() return face:getMaterialFloat4(fm, fj) end)
                if v and vn == "AddColorUV" then
                    try(function() twin.mesh:setMaterialFloat4(i, j, Vector4f.new(v.x, v.y, v.z, v.w)) end)
                elseif v and vn == "Stain_ID" then
                    try(function() twin.mesh:setMaterialFloat(i, j, v.x) end)
                end
            end
        end
    end
    status.twin = {
        mesh = mesh_path(twin.mesh), loaded = twin.key == key,
        parented = parent ~= nil, materials = try(function() return twin.mesh:get_MaterialNum() end),
        stencil = try(function() return twin.mesh:get_StencilValue() end),
    }
end

re.on_frame(function()
    local now = os.clock()
    if now - readAt > 0.5 then
        readAt = now
        local c = json.load_file(CMD)
        if type(c) == "table" then cmd = c end
    end
    local hxf = hunter_xf()
    if not hxf then return end
    foundAt = foundAt or now
    if (not probed and now - foundAt > 3) or (cmd.n ~= nil and cmd.n ~= lastN and probed) then
        probed, lastN = true, cmd.n
        probe(hxf)
        twin_diff(hxf)
    end
    local st = cmd.on and experiment(hxf) or {}
    run_twin(hxf, st)
    -- "faceParts": {"7": false}: the face mesh's parts (mesh groups) on / off; status lists 0..15
    if type(cmd.faceParts) == "table" then
        local all = {}
        walk(hxf, 0, all)
        local face = face_of(all)
        if face then
            for k, v in pairs(cmd.faceParts) do
                local i = tonumber(k)
                local ok = pcall(function() face:call("setPartsEnable(System.UInt64, System.Boolean)", i, v) end)
                    or pcall(function() face:setPartsEnable(i, v) end)
                st["setPart" .. k] = ok
            end
            local parts = {}
            for i = 0, 15 do
                parts[i + 1] = tostring(try(function() return face:getPartsEnable(i) end))
            end
            st.faceParts = table.concat(parts, " ")
        end
    end
    if now - statusAt > 1 then statusAt = now; json.dump_file(STATUS, st) end
end)

re.on_draw_ui(function()
    if imgui.tree_node("MiquellaLight: Instance probe") then
        imgui.text(probed and ("written: reframework/data/" .. OUT) or "waiting for the hunter")
        imgui.text("experiment: " .. (cmd.on and "on" or "off"))
        imgui.tree_pop()
    end
end)

-- The character script hides every ch03 part under the hunter each frame (the twin is one): show
-- the twin again right before rendering.
-- "show": "real" draws the hunter's own innerwear part (same name as the twin's mesh) instead of
-- the twin, to compare the two under the same light.
re.on_pre_application_entry("BeginRendering", function()
    local want = cmd.twin
    if not (twin.go and type(want) == "table") then return end
    local real = want.show == "real"
    try(function() twin.go:call("set_DrawSelf", not real) end)
    local hxf = hunter_xf()
    if not hxf then return end
    local all = {}
    walk(hxf, 0, all)
    local name = tostring(want.mesh):match("([^/]+)%.mesh$")
    for _, go in ipairs(all) do
        if str(try(function() return go:call("get_Name") end)) == name then
            try(function() go:call("set_DrawSelf", real) end)
        end
    end
end)
