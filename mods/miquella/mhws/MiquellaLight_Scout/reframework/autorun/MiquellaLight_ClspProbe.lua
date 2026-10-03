-- MiquellaLight_ClspProbe: diagnostic, read only. For the hunter's parts that have a
-- via.character.CollisionShapePreset (and app.ChainSetting): the preset infos' fields and
-- getters (which .clsp, flags), the ChainSetting's fields, and the methods of both types and of
-- the info type. Written once, 5 s after the hunter is found, to clsp_probe.json.
-- Why (2026-10-04): the game's chained parts carry these two and do not go through the legs;
-- the robe has only Chain2. What would ours need?

local OUT = "MiquellaLight/clsp_probe.json"
local foundAt, done = nil, false

local function try(fn, ...)
    local ok, r = pcall(fn, ...)
    if ok then return r end
    return nil
end

local function str(v)
    local t = type(v)
    if t == "number" or t == "boolean" or t == "string" then return v end
    if v == nil then return "nil" end
    return try(function() return v:call("ToString()") end) or try(function() return tostring(v) end) or "?"
end

local function methods(td)
    local out = {}
    while td do
        local tn = try(function() return td:get_full_name() end) or "?"
        if tn == "via.Component" or tn == "System.Object" or tn == "System.ValueType" then break end
        for _, m in ipairs(try(function() return td:get_methods() end) or {}) do
            local name = try(function() return m:get_name() end) or "?"
            local n = try(function() return m:get_num_params() end) or 0
            local params = {}
            for _, p in ipairs(try(function() return m:get_param_types() end) or {}) do
                table.insert(params, try(function() return p:get_full_name() end) or "?")
            end
            local rt = try(function() return m:get_return_type():get_full_name() end) or "?"
            table.insert(out, tn .. "::" .. name .. "(" .. table.concat(params, ", ") .. ") -> " .. rt)
        end
        td = try(function() return td:get_parent_type() end)
    end
    return out
end

local function fields(obj)
    local out = {}
    local td = try(function() return obj:get_type_definition() end)
    while td do
        local tn = try(function() return td:get_full_name() end) or "?"
        if tn == "via.Component" or tn == "System.Object" or tn == "System.ValueType" then break end
        for _, f in ipairs(try(function() return td:get_fields() end) or {}) do
            local name = try(function() return f:get_name() end) or "?"
            if not try(function() return f:is_static() end) then
                local ok, v = pcall(function() return f:get_data(obj) end)
                out[name] = ok and str(v) or "error"
            end
        end
        td = try(function() return td:get_parent_type() end)
    end
    return out
end

local function getters(obj)
    local out = {}
    local td = try(function() return obj:get_type_definition() end)
    local seen = {}
    while td do
        local tn = try(function() return td:get_full_name() end) or "?"
        if tn == "via.Component" or tn == "System.Object" or tn == "System.ValueType" then break end
        for _, m in ipairs(try(function() return td:get_methods() end) or {}) do
            local name = try(function() return m:get_name() end) or ""
            if not seen[name] and name:match("^get_") and try(function() return m:get_num_params() end) == 0 then
                seen[name] = true
                local ok, r = pcall(function() return m:call(obj) end)
                out[name] = ok and str(r) or "error"
            end
        end
        td = try(function() return td:get_parent_type() end)
    end
    return out
end

local function component(go, typeName)
    return try(function() return go:call("getComponent(System.Type)", sdk.typeof(typeName)) end)
end

re.on_frame(function()
    if done then return end
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local hgo = chr and try(function() return chr:call("get_GameObject") end)
    local hxf = hgo and try(function() return hgo:call("get_Transform") end)
    if not hxf then return end
    foundAt = foundAt or os.clock()
    if os.clock() - foundAt < 5 then return end
    done = true
    local out = { types = {}, parts = {} }
    for _, tn in ipairs({ "via.character.CollisionShapePreset", "app.ChainSetting", "via.motion.Chain2" }) do
        out.types[tn] = methods(sdk.find_type_definition(tn))
    end
    local child = try(function() return hxf:call("get_Child") end)
    local infoTypeDone = false
    while child do
        local go = try(function() return child:call("get_GameObject") end)
        local name = go and try(function() return go:call("get_Name") end) or "?"
        local csp = go and component(go, "via.character.CollisionShapePreset")
        local cs = go and component(go, "app.ChainSetting")
        if csp or cs then
            local part = { name = name }
            if csp then
                part.csp = getters(csp)
                part.cspFields = fields(csp)
                local arr = try(function() return csp:call("get_CollisionShapePresetInfos") end)
                local els = arr and (try(function() return arr:get_elements() end) or {}) or {}
                if #els == 0 and arr then
                    local n = try(function() return arr:call("get_Count") end) or 0
                    for i = 0, n - 1 do
                        local e = try(function() return arr:call("get_Item", i) end)
                        if e then table.insert(els, e) end
                    end
                end
                part.infos = {}
                for _, e in ipairs(els) do
                    table.insert(part.infos, { fields = fields(e), get = getters(e) })
                    if not infoTypeDone then
                        infoTypeDone = true
                        local td = try(function() return e:get_type_definition() end)
                        out.types.info = { name = td and try(function() return td:get_full_name() end), methods = methods(td) }
                    end
                end
            end
            if cs then part.chainSetting = fields(cs) end
            table.insert(out.parts, part)
        end
        child = try(function() return child:call("get_Next") end)
    end
    json.dump_file(OUT, out)
end)
