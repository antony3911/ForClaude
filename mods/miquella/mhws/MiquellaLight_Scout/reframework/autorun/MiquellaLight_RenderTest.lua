-- MiquellaLight_RenderTest: diagnostic. Sets via.render.Mesh draw switches on our objects every
-- frame from reframework/data/MiquellaLight/render_test.json, e.g.
--   {"MiquellaLight_Body": {"DrawShadowCast": false, "DrawVoxelize": false}, "MiquellaLight_Robe": {}}
-- (read twice a second; a switch left out is not touched). What it found and set goes to
-- render_test_status.json.
-- Why (2026-10-04): the fitted robe shows a blocky pattern in game, the mesh itself is smooth;
-- suspects: the hidden body still casting shadows, or in the voxel / distance-field lighting.

local CMD = "MiquellaLight/render_test.json"
local STATUS = "MiquellaLight/render_test_status.json"
local want, readAt, report = {}, 0, {}

local function try(fn, ...)
    local ok, r = pcall(fn, ...)
    if ok then return r end
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

re.on_frame(function()
    local now = os.clock()
    if now - readAt > 0.5 then
        readAt = now
        local c = json.load_file(CMD)
        if type(c) == "table" then want = c end
    end
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local hgo = chr and try(function() return chr:call("get_GameObject") end)
    local hxf = hgo and try(function() return hgo:call("get_Transform") end)
    if not hxf then return end
    local rep = {}
    for name, switches in pairs(want) do
        local go = find(hxf, name, 0)
        local mesh = go and try(function() return go:call("getComponent(System.Type)", sdk.typeof("via.render.Mesh")) end)
        rep[name] = { found = mesh ~= nil }
        if mesh and type(switches) == "table" then
            for k, v in pairs(switches) do
                try(function() mesh:call("set_" .. k, v) end)
                rep[name][k] = tostring(try(function() return mesh:call("get_" .. k) end))
            end
        end
    end
    if now - (report.at or 0) > 2 then
        report.at = now
        json.dump_file(STATUS, rep)
    end
end)
