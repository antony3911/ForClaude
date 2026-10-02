-- MiquellaLight_MeshDiff: one-shot diagnostic, read only. Compares the game's own face object
-- (character/ch00) with our script-created MiquellaLight_Body: the GameObject's folder and
-- components, and every no-argument getter of their via.render.Mesh components. Written to
-- reframework/data/MiquellaLight/mesh_diff.json a few seconds after the hunter is found.
-- Why (2026-10-03): our body gets direct light but no ambient light (black in the shade).

local OUT = "MiquellaLight/mesh_diff.json"
local done, startedAt = false, nil

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

local function getters(obj)
    local out = {}
    local td = try(function() return obj:get_type_definition() end)
    local seen = {}
    while td do
        for _, m in ipairs(try(function() return td:get_methods() end) or {}) do
            local name = try(function() return m:get_name() end) or ""
            local rt = try(function() return m:get_return_type() end)
            local rn = rt and try(function() return rt:get_full_name() end) or ""
            -- only value types (numbers, flags, enums, small structs) and strings: no arrays or objects
            local simple = rn == "System.String" or (rt and try(function() return rt:is_value_type() end))
            if not seen[name] and simple and (name:match("^get_") or name:match("^is") or name:match("^has"))
                and try(function() return m:get_num_params() end) == 0 then
                seen[name] = true
                local ok, r = pcall(function() return m:call(obj) end)
                out[name] = ok and str(r) or "error"
            end
        end
        td = try(function() return td:get_parent_type() end)
        local tn = td and try(function() return td:get_full_name() end)
        if tn == "via.Component" or tn == "System.Object" then break end
    end
    return out
end

local function describe(go)
    local d = { name = str(try(function() return go:call("get_Name") end)) }
    local folder = try(function() return go:call("get_Folder") end)
    d.folder = folder and str(try(function() return folder:call("get_Path") end) or folder) or "nil"
    d.go = getters(go)
    d.components = {}
    local arr = try(function() return go:call("get_Components") end)
    for _, c in ipairs(arr and (try(function() return arr:get_elements() end) or {}) or {}) do
        local tn = try(function() return c:get_type_definition():get_full_name() end) or "?"
        table.insert(d.components, tn)
        if tn == "via.render.Mesh" then d.mesh = getters(c) end
    end
    return d
end

local function scan(xf, depth, out)
    if depth > 6 then return end
    local child = try(function() return xf:call("get_Child") end)
    while child do
        local go = try(function() return child:call("get_GameObject") end)
        if go then table.insert(out, go) end
        scan(child, depth + 1, out)
        child = try(function() return child:call("get_Next") end)
    end
end

local function mesh_path(go)
    local mesh = try(function() return go:call("getComponent(System.Type)", sdk.typeof("via.render.Mesh")) end)
    local res = mesh and try(function() return mesh:getMesh() end)
    return res and (try(function() return res:ToString() end) or "") or ""
end

re.on_frame(function()
    if done then return end
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local hgo = chr and try(function() return chr:call("get_GameObject") end)
    local hxf = hgo and try(function() return hgo:call("get_Transform") end)
    if not hxf then return end
    startedAt = startedAt or os.clock()
    if os.clock() - startedAt < 3 then return end
    done = true
    local all = {}
    scan(hxf, 0, all)
    local face, body, list = nil, nil, {}
    for _, go in ipairs(all) do
        local name = str(try(function() return go:call("get_Name") end))
        local path = mesh_path(go)
        table.insert(list, name .. " | " .. path)
        if name == "MiquellaLight_Body" then body = go end
        if not face and path:lower():find("character/ch00/") then face = go end
    end
    local result = { children = list, hunter = describe(hgo) }
    result.face = face and describe(face) or "not found"
    result.body = body and describe(body) or "not found"
    if face and body then
        local diff = {}
        for k, v in pairs(result.face.mesh or {}) do
            local b = (result.body.mesh or {})[k]
            if tostring(b) ~= tostring(v) then diff["mesh." .. k] = { face = v, body = b } end
        end
        for k, v in pairs(result.face.go or {}) do
            local b = (result.body.go or {})[k]
            if tostring(b) ~= tostring(v) then diff["go." .. k] = { face = v, body = b } end
        end
        result.diff = diff
    end
    json.dump_file(OUT, result)
end)

re.on_draw_ui(function()
    if imgui.tree_node("MiquellaLight: Mesh diff") then
        imgui.text(done and ("written: reframework/data/" .. OUT) or "waiting for the hunter")
        imgui.tree_pop()
    end
end)
