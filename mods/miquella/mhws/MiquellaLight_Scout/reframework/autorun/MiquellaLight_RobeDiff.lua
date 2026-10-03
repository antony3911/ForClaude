-- MiquellaLight_RobeDiff: diagnostic, read only. Each time our robe (MiquellaLight_Robe) shows a
-- new mesh, a few seconds later every no-argument getter of its via.render.Mesh and its materials
-- (name, on/off, variables) go to reframework/data/MiquellaLight/robe_diff_<mesh>.json.
-- Why (2026-10-04): the fitted robes (plain, body lines) render black, the drapes do not, with
-- the same mdf2 and like mesh data. Compare the files of a black and a fine one.

local DIR = "MiquellaLight/"
local WAIT = 3.0
local lastPath, changedAt, dumped = nil, nil, {}

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

local function vec(v)
    if type(v) ~= "userdata" then return str(v) end
    local x, y, z, w = try(function() return v.x end), try(function() return v.y end),
        try(function() return v.z end), try(function() return v.w end)
    if x then return { x, y, z, w } end
    return str(v)
end

local function materials(mesh)
    local out = {}
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        local m = { name = str(try(function() return mesh:getMaterialName(i) end)),
                    enabled = str(try(function() return mesh:getMaterialsEnable(i) end)), vars = {} }
        local vn = try(function() return mesh:getMaterialVariableNum(i) end) or 0
        for j = 0, vn - 1 do
            local name = try(function() return mesh:getMaterialVariableName(i, j) end) or ("#" .. j)
            local f = try(function() return mesh:getMaterialFloat(i, j) end)
            local f4 = try(function() return mesh:getMaterialFloat4(i, j) end)
            m.vars[name] = f4 and vec(f4) or str(f)
        end
        table.insert(out, m)
    end
    return out
end

local function find_robe(xf, depth)
    if depth > 6 then return nil end
    local child = try(function() return xf:call("get_Child") end)
    while child do
        local go = try(function() return child:call("get_GameObject") end)
        if go and try(function() return go:call("get_Name") end) == "MiquellaLight_Robe" then return go end
        local r = find_robe(child, depth + 1)
        if r then return r end
        child = try(function() return child:call("get_Next") end)
    end
    return nil
end

re.on_frame(function()
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local hgo = chr and try(function() return chr:call("get_GameObject") end)
    local hxf = hgo and try(function() return hgo:call("get_Transform") end)
    if not hxf then return end
    local go = find_robe(hxf, 0)
    local mesh = go and try(function() return go:call("getComponent(System.Type)", sdk.typeof("via.render.Mesh")) end)
    local res = mesh and try(function() return mesh:getMesh() end)
    local path = res and (try(function() return res:ToString() end) or "") or ""
    if path ~= lastPath then lastPath, changedAt = path, os.clock() end
    if path == "" or dumped[path] or os.clock() - changedAt < WAIT then return end
    dumped[path] = true
    local base = path:match("([^/\\]+)%.mesh") or "robe"
    json.dump_file(DIR .. "robe_diff_" .. base .. ".json", {
        path = path, go = getters(go), mesh = getters(mesh), materials = materials(mesh),
        components = (function()
            local t = {}
            local arr = try(function() return go:call("get_Components") end)
            for _, c in ipairs(arr and (try(function() return arr:get_elements() end) or {}) or {}) do
                table.insert(t, try(function() return c:get_type_definition():get_full_name() end) or "?")
            end
            return t
        end)() })
end)

re.on_draw_ui(function()
    if imgui.tree_node("MiquellaLight: Robe diff") then
        local n = 0
        for _ in pairs(dumped) do n = n + 1 end
        imgui.text("robe meshes written: " .. n .. " (reframework/data/" .. DIR .. "robe_diff_*.json)")
        imgui.tree_pop()
    end
end)
