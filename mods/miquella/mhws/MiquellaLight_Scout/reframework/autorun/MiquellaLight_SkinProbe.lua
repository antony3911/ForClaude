-- MiquellaLight_SkinProbe: diagnostic, read only. Every mesh under the hunter whose material
-- names look like skin ("skin", "face", "Skin"): each such material's variables with their values
-- now (float / float4), and the mesh's render settings that touch lighting. Written once, 5 s after
-- the hunter is found (and again when skin_probe_again.json's "n" changes) to skin_probe.json.
-- Why (2026-10-04): our body's skin (the game's SkinEdit material) comes out darker and browner
-- than the face, though its albedo is like the game's body texture; the game sets more on its
-- skin materials at run time than the AddColorUV we copy.

local OUT = "MiquellaLight/skin_probe.json"
local AGAIN = "MiquellaLight/skin_probe_again.json"
local foundAt, done, lastAgain, checkAt = nil, false, nil, 0

local function try(fn, ...)
    local ok, r = pcall(fn, ...)
    if ok then return r end
    return nil
end

local function vec(v)
    if type(v) == "number" or type(v) == "boolean" then return v end
    if v == nil then return nil end
    local x = try(function() return v.x end)
    if x then return { x, try(function() return v.y end), try(function() return v.z end), try(function() return v.w end) } end
    return tostring(v)
end

local function materials(mesh)
    local out = {}
    local n = try(function() return mesh:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        local name = try(function() return mesh:getMaterialName(i) end) or ("#" .. i)
        if name:lower():find("skin") or name:lower():find("face") then
            local vars = {}
            local vn = try(function() return mesh:getMaterialVariableNum(i) end) or 0
            for j = 0, vn - 1 do
                local vname = try(function() return mesh:getMaterialVariableName(i, j) end) or ("#" .. j)
                local vt = try(function() return mesh:getMaterialVariableType(i, j) end)
                local f4 = try(function() return mesh:getMaterialFloat4(i, j) end)
                local f = try(function() return mesh:getMaterialFloat(i, j) end)
                vars[vname] = { type = vt, f = f, f4 = vec(f4) }
            end
            out[name] = vars
        end
    end
    return out
end

local function mesh_info(go)
    local mesh = try(function() return go:call("getComponent(System.Type)", sdk.typeof("via.render.Mesh")) end)
    if not mesh then return nil end
    local res = try(function() return mesh:getMesh() end)
    local mats = materials(mesh)
    if next(mats) == nil then return nil end
    return {
        mesh = res and tostring(try(function() return res:ToString() end)) or "?",
        enabled = try(function() return mesh:get_Enabled() end),
        stencil = try(function() return mesh:get_StencilValue() end),
        materials = mats,
    }
end

local function scan(xf, depth, out)
    if depth > 4 then return end
    local child = try(function() return xf:call("get_Child") end)
    while child do
        local go = try(function() return child:call("get_GameObject") end)
        local info = go and mesh_info(go)
        if info then out[try(function() return go:call("get_Name") end) or "?"] = info end
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
    local out = {}
    scan(hxf, 0, out)
    json.dump_file(OUT, out)
end)
