-- MiquellaLight_ChainScan: diagnostic, read only. Every GameObject under the hunter: name, mesh,
-- component types, and for via.motion.Chain2 its collision settings (getters with "Collision",
-- "Collider", "Model" in the name). Written once, 5 s after the hunter is found, and again when
-- reframework/data/MiquellaLight/chain_scan_again.json changes, to chain_scan.json.
-- Why (2026-10-04): the robe's legs come through its skirt; the game's own long skirts do not.
-- What do their objects have that ours lacks?

local OUT = "MiquellaLight/chain_scan.json"
local AGAIN = "MiquellaLight/chain_scan_again.json"
local foundAt, done, lastAgain, checkAt = nil, false, nil, 0

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

local function getters(obj, pattern)
    local out = {}
    local td = try(function() return obj:get_type_definition() end)
    local seen = {}
    while td do
        for _, m in ipairs(try(function() return td:get_methods() end) or {}) do
            local name = try(function() return m:get_name() end) or ""
            if not seen[name] and name:match("^get_") and name:find(pattern)
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

local function fields(obj)
    local out = {}
    local td = try(function() return obj:get_type_definition() end)
    for _, f in ipairs(td and (try(function() return td:get_fields() end) or {}) or {}) do
        local name = try(function() return f:get_name() end) or "?"
        if not (try(function() return f:is_static() end)) then
            out[name] = str(try(function() return f:get_data(obj) end))
        end
    end
    return out
end

local function describe(go)
    local d = { name = str(try(function() return go:call("get_Name") end)), components = {} }
    local arr = try(function() return go:call("get_Components") end)
    for _, c in ipairs(arr and (try(function() return arr:get_elements() end) or {}) or {}) do
        local tn = try(function() return c:get_type_definition():get_full_name() end) or "?"
        local entry = { type = tn }
        if tn == "via.render.Mesh" then
            local res = try(function() return c:getMesh() end)
            entry.mesh = res and str(try(function() return res:ToString() end)) or "nil"
        elseif tn == "via.motion.Chain2" then
            entry.get = getters(c, "Coll")
            for k, v in pairs(getters(c, "Model")) do entry.get[k] = v end
            for k, v in pairs(getters(c, "Resource")) do entry.get[k] = v end
            for k, v in pairs(getters(c, "Enable")) do entry.get[k] = v end
        elseif tn:find("Chain") or tn:find("Collid") or tn:find("Collision") then
            entry.get = getters(c, ".")
            entry.fields = fields(c)
        end
        table.insert(d.components, entry)
    end
    return d
end

local function scan(xf, depth, out)
    if depth > 4 then return end
    local child = try(function() return xf:call("get_Child") end)
    while child do
        local go = try(function() return child:call("get_GameObject") end)
        if go then table.insert(out, describe(go)) end
        scan(child, depth + 1, out)
        child = try(function() return child:call("get_Next") end)
    end
end

re.on_frame(function()
    local now = os.clock()
    if now - checkAt > 1 then
        checkAt = now
        local again = json.load_file(AGAIN)
        local key = type(again) == "table" and tostring(again.n) or nil
        if key and key ~= lastAgain then
            if lastAgain ~= nil then done = false end
            lastAgain = key
        end
    end
    if done then return end
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local hgo = chr and try(function() return chr:call("get_GameObject") end)
    local hxf = hgo and try(function() return hgo:call("get_Transform") end)
    if not hxf then return end
    foundAt = foundAt or now
    if now - foundAt < 5 then return end
    done = true
    local out = { hunter = describe(hgo), children = {} }
    scan(hxf, 0, out.children)
    json.dump_file(OUT, out)
end)
