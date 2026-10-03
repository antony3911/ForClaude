-- MiquellaLight_ChainTest: experiment. Adds to our robe object (MiquellaLight_Robe) what the
-- game's chained parts have and ours lacks, from reframework/data/MiquellaLight/chain_test.json:
--   {"chainSetting": true, "clsp": "Art/Model/Character/ch03/025/001/5/ch03_025_0015.clsp", "n": 1}
-- (applied once per robe object and command; change "n" to apply again). What it did goes to
-- chain_test_status.json.
-- Why (2026-10-04): the legs come through the robe's skirt; the game's chained parts carry
-- app.ChainSetting (registers the chain in the hunter's ChainSettingCollection) and a
-- via.character.CollisionShapePreset (their .clsp: capsules on the legs).

local CMD = "MiquellaLight/chain_test.json"
local STATUS = "MiquellaLight/chain_test_status.json"
local cmd, cmdKey, readAt = nil, nil, 0
local doneFor = {}       -- robe object address .. command key -> true
local status = {}
local holders = {}

local function try(fn, ...)
    local ok, r = pcall(fn, ...)
    if ok then return r end
    status.lastError = tostring(r)
    return nil
end

local function find(xf, name, depth)
    if depth > 6 then return nil end
    local child = try(function() return xf:call("get_Child") end)
    while child do
        local go = try(function() return child:call("get_GameObject") end)
        if go and try(function() return go:call("get_Name") end) == name then return go end
        local r = find(child, name, depth + 1)
        if r then return r end
        child = try(function() return child:call("get_Next") end)
    end
    return nil
end

local function component(go, tn)
    return try(function() return go:call("getComponent(System.Type)", sdk.typeof(tn)) end)
end

local function add(go, tn)
    local c = component(go, tn)
    if c then return c, false end
    c = try(function() return go:call("createComponent(System.Type)", sdk.typeof(tn)) end)
    if c then try(function() c:add_ref() end) end
    return c, true
end

local function clsp_holder(path)
    if holders[path] == nil then
        holders[path] = try(function()
            local res = sdk.create_resource("via.character.CollisionShapePresetResource", path):add_ref()
            return res:create_holder("via.character.CollisionShapePresetResourceHolder"):add_ref()
        end) or false
    end
    return holders[path] or nil
end

local function apply(go)
    local s = {}
    local chain2 = component(go, "via.motion.Chain2")
    if cmd.chainSetting then
        local c, made = add(go, "app.ChainSetting")
        s.chainSetting = c and (made and "created" or "already there") or "failed"
        if c then
            s.chainSettingChain2 = tostring(try(function() return c:get_field("_Chain2") end))
            s.chainSettingCollection = tostring(try(function() return c:get_field("_Collection") end))
        end
    end
    if type(cmd.clsp) == "string" then
        local csp, made = add(go, "via.character.CollisionShapePreset")
        s.csp = csp and (made and "created" or "already there") or "failed"
        local h = clsp_holder(cmd.clsp)
        s.clspHolder = h and "ok" or "failed"
        if csp and h then
            try(function() csp:call("setCollisionShapePresetInfosCount", 1) end)
            local info = try(function() return csp:call("getCollisionShapePresetInfos", 0) end)
            if not info then
                info = try(function() return sdk.create_instance("via.character.CollisionShapePresetInfo"):add_ref() end)
            end
            s.info = info and "ok" or "failed"
            if info then
                try(function() info:call("set_Resource", h) end)
                try(function() info:call("set_Enabled", true) end)
                try(function() csp:call("setCollisionShapePresetInfos", 0, info) end)
                local back = try(function() return csp:call("getCollisionShapePresetInfos", 0) end)
                s.infoResource = back and tostring(try(function() return back:call("get_Resource"):call("ToString()") end)) or "?"
                s.infoShapes = back and try(function() return back:call("get_ShapeNum") end) or "?"
            end
            -- off and on again: a preset added after the object started may not register its shapes
            try(function() csp:call("set_Enabled", false) end)
            try(function() csp:call("set_Enabled", true) end)
            if chain2 then
                try(function() chain2:call("set_EnabledCollision", false) end)
                try(function() chain2:call("set_EnabledCollision", true) end)
            end
        end
    end
    local chain = component(go, "via.motion.Chain2")
    if chain then
        if cmd.enableCollision ~= nil then try(function() chain:call("set_EnabledCollision", cmd.enableCollision) end) end
        s.chainCollision = tostring(try(function() return chain:call("get_EnabledCollision") end))
    end
    return s
end

re.on_frame(function()
    local now = os.clock()
    if now - readAt > 0.5 then
        readAt = now
        local c = json.load_file(CMD)
        if type(c) == "table" then
            cmd = c
            cmdKey = tostring(c.n) .. tostring(c.chainSetting) .. tostring(c.clsp) .. tostring(c.enableCollision)
        end
    end
    if not cmd then return end
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local hgo = chr and try(function() return chr:call("get_GameObject") end)
    local hxf = hgo and try(function() return hgo:call("get_Transform") end)
    if not hxf then return end
    local go = find(hxf, "MiquellaLight_Robe", 0)
    if not go then return end
    local key = tostring(go:get_address()) .. "|" .. cmdKey
    if doneFor[key] then return end
    doneFor[key] = true
    status.applied = apply(go)
    status.at = now
    json.dump_file(STATUS, status)
end)
