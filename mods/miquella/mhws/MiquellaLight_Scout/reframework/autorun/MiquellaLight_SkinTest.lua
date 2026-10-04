-- MiquellaLight_SkinTest: experiment. Every frame sets variables on our body's skin materials
-- (MiquellaSkin, -Chest, -Waist) from reframework/data/MiquellaLight/skin_test.json, e.g.
--   {"on": true, "colorParam": 1.0, "stain": true, "normalBlend": 0.0}
-- stain: Stain_ID copied from the face's material (the game sets it at run time; ours is 0).
-- Status (what it set) to skin_test_status.json.
-- Why (2026-10-04): our skin vs the game's own "skin" material differs only in ColorParam (ours
-- 2.9), Stain_ID (game 378, ours 0) and NormalBlendParam (game 0, ours 0.5); the body is darker
-- and browner than the face.

local CMD = "MiquellaLight/skin_test.json"
local STATUS = "MiquellaLight/skin_test_status.json"
local SKINS = { MiquellaSkin = true, MiquellaSkinChest = true, MiquellaSkinWaist = true }
local cmd, readAt, statusAt = {}, 0, 0

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

local function var_index(mesh, mat, name)
    local n = try(function() return mesh:getMaterialVariableNum(mat) end) or 0
    for j = 0, n - 1 do
        if try(function() return mesh:getMaterialVariableName(mat, j) end) == name then return j end
    end
    return nil
end

local function mesh_of(go)
    return go and try(function() return go:call("getComponent(System.Type)", sdk.typeof("via.render.Mesh")) end)
end

local function apply(test)
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    local chr = master and try(function() return master:get_Character() end)
    local hgo = chr and try(function() return chr:call("get_GameObject") end)
    local hxf = hgo and try(function() return hgo:call("get_Transform") end)
    if not hxf then return end
    local body = mesh_of(find(hxf, "MiquellaLight_Body", 0))
    local face = mesh_of(find(hxf, "Player_Face", 0))
    if not body then return end
    local stain
    if cmd.stain and face then
        local fm
        local n = try(function() return face:get_MaterialNum() end) or 0
        for i = 0, n - 1 do if try(function() return face:getMaterialName(i) end) == "face" then fm = i end end
        local j = fm and var_index(face, fm, "Stain_ID")
        local v = j and try(function() return face:getMaterialFloat4(fm, j) end)
        stain = v and v.x
    end
    local n = try(function() return body:get_MaterialNum() end) or 0
    for i = 0, n - 1 do
        local name = try(function() return body:getMaterialName(i) end)
        if SKINS[name] then
            if cmd.colorParam then
                local j = var_index(body, i, "ColorParam")
                if j then try(function() body:setMaterialFloat4(i, j, Vector4f.new(cmd.colorParam, cmd.colorParam, cmd.colorParam, 1.0)) end) end
            end
            if stain then
                local j = var_index(body, i, "Stain_ID")
                if j then try(function() body:setMaterialFloat(i, j, stain) end) end
            end
            if cmd.normalBlend then
                local j = var_index(body, i, "NormalBlendParam")
                if j then try(function() body:setMaterialFloat(i, j, cmd.normalBlend) end) end
            end
            if test then
                local j = var_index(body, i, "Stain_ID")
                local v = j and try(function() return body:getMaterialFloat4(i, j) end)
                local c = var_index(body, i, "ColorParam")
                local cv = c and try(function() return body:getMaterialFloat4(i, c) end)
                test[name] = { stain = v and v.x, colorParam = cv and cv.x }
            end
        end
    end
    if test then test.faceStain = stain end
end

re.on_pre_application_entry("BeginRendering", function()
    if cmd.on then apply(nil) end
end)

re.on_frame(function()
    local now = os.clock()
    if now - readAt > 0.5 then
        readAt = now
        local c = json.load_file(CMD)
        if type(c) == "table" then cmd = c end
    end
    if cmd.on then apply(nil) end
    if now - statusAt > 2 then
        statusAt = now
        local t = {}
        if cmd.on then apply(t) end
        json.dump_file(STATUS, t)
    end
end)
