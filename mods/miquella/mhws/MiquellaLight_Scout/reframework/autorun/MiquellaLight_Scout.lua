-- MiquellaLight Scout (read-only)
--
-- Shows which model files the hunter is using right now: weapons, armor parts, and every
-- child object that has a mesh (face, hair, ...). For each one: the .mesh and .mdf2 paths,
-- material names, and the bone (joint) names. Nothing in the game is changed.
--
-- "Save report" writes everything to reframework/data/MiquellaLight/scout.json so it can
-- be shared, which is what we need to pick the weapon to replace and to line our models
-- up with the right bones.
--
-- API usage follows MDF-XL (SilverEzredes) and the REFramework book examples. Untested.

local MOD = "MiquellaLight Scout"
local OUT = "MiquellaLight/scout.json"
local MESH = "via.render.Mesh"
local MAX_JOINTS = 600
local MAX_CHILDREN = 400

local report = nil
local status = ""
local showJoints = false

local function try(fn, ...)
    local ok, result = pcall(fn, ...)
    if ok then return result end
    return nil
end

local function component(go, typeName)
    return try(function()
        return go:call("getComponent(System.Type)", sdk.typeof(typeName))
    end)
end

-- "Resource[Art/Model/.../x.mesh]" -> "Art/Model/.../x.mesh"
local function resource_path(res)
    local s = res and try(function() return res:ToString() end)
    if not s then return nil end
    return (s:gsub("^Resource%[", ""):gsub("%]$", ""))
end

local function joint_names(xf)
    local joints = try(function() return xf:get_Joints() end)
    if not joints then return nil end
    local names = {}
    for i, j in ipairs(joints:get_elements()) do
        if i > MAX_JOINTS then break end
        names[#names + 1] = try(function() return j:get_Name() end) or "?"
    end
    return names
end

local function describe(go, withJoints)
    if not go then return nil end
    local info = { name = try(function() return go:get_Name() end) or "?" }
    local mesh = component(go, MESH)
    if mesh then
        info.mesh = resource_path(try(function() return mesh:getMesh() end))
        info.mdf2 = resource_path(try(function() return mesh:get_Material() end))
        info.materials = {}
        local n = try(function() return mesh:get_MaterialNum() end) or 0
        for i = 0, n - 1 do
            info.materials[#info.materials + 1] = try(function() return mesh:getMaterialName(i) end) or "?"
        end
    end
    local xf = try(function() return go:get_Transform() end)
    if xf then
        local parent = try(function() return xf:get_Parent() end)
        if parent then
            info.parent = try(function() return parent:get_GameObject():get_Name() end)
        end
        info.parent_joint = try(function() return tostring(xf:get_ParentJoint()) end)
        if withJoints then
            info.joints = joint_names(xf)
        end
    end
    return info
end

local function collect_children(xf, out, depth)
    if depth > 8 or #out >= MAX_CHILDREN then return end
    local child = try(function() return xf:get_Child() end)
    while child and #out < MAX_CHILDREN do
        local go = try(function() return child:get_GameObject() end)
        local info = go and describe(go, false)
        if info then
            info.depth = depth
            out[#out + 1] = info
        end
        collect_children(child, out, depth + 1)
        child = try(function() return child:get_Next() end)
    end
end

local function scan()
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    if not (master and try(function() return master:get_Valid() end)) then
        return nil, "No hunter in the scene yet."
    end
    local character = master:get_Character()
    local playerObj = master:get_Object()
    local r = {
        female = try(function() return character:get_IsFemale() end),
        weapons = {},
        armor = {},
        children = {},
    }

    for _, slot in ipairs({ "Weapon", "SubWeapon", "ReserveWeapon", "ReserveSubWeapon" }) do
        local w = try(function() return character:call("get_" .. slot) end)
        local go = w and try(function() return w:get_GameObject() end)
        if go then
            local info = describe(go, true)
            info.slot = slot
            r.weapons[#r.weapons + 1] = info
        end
    end

    local partNames = { [0] = "helm", "body", "arm", "waist", "leg", "slinger" }
    for i = 0, 5 do
        local go = try(function() return character:getParts(i) end)
        if go then
            local info = describe(go, false)
            info.slot = partNames[i]
            r.armor[#r.armor + 1] = info
        end
    end

    local xf = playerObj and try(function() return playerObj:get_Transform() end)
    if xf then
        r.player_joints = joint_names(xf)
        collect_children(xf, r.children, 0)
    end
    return r, "Scanned."
end

local function show_entry(info, key)
    if not info then return end
    local label = (info.slot and (info.slot .. ": ") or "") .. info.name
    if imgui.tree_node(label .. "##" .. key) then
        imgui.text("mesh: " .. tostring(info.mesh))
        imgui.text("mdf2: " .. tostring(info.mdf2))
        if info.materials then
            imgui.text("materials: " .. table.concat(info.materials, ", "))
        end
        imgui.text("parent: " .. tostring(info.parent) .. "   parent joint: " .. tostring(info.parent_joint))
        if info.joints then
            imgui.text("joints (" .. #info.joints .. "): " .. table.concat(info.joints, ", ", 1, math.min(#info.joints, 40)))
        end
        imgui.tree_pop()
    end
end

re.on_draw_ui(function()
    if not imgui.tree_node(MOD) then return end

    if imgui.button("Scan hunter") then
        local r, msg = scan()
        report, status = r, msg
    end
    imgui.same_line()
    if imgui.button("Save report") then
        if report then
            json.dump_file(OUT, report)
            status = "Saved to reframework/data/" .. OUT
        else
            status = "Scan first."
        end
    end
    imgui.text(status)

    if report then
        imgui.text("Female body type: " .. tostring(report.female))
        if imgui.tree_node("Weapons (" .. #report.weapons .. ")") then
            for i, w in ipairs(report.weapons) do show_entry(w, "w" .. i) end
            imgui.tree_pop()
        end
        if imgui.tree_node("Armor parts (" .. #report.armor .. ")") then
            for i, a in ipairs(report.armor) do show_entry(a, "a" .. i) end
            imgui.tree_pop()
        end
        if imgui.tree_node("Child objects with meshes") then
            for i, c in ipairs(report.children) do
                if c.mesh then
                    imgui.text(string.rep("  ", c.depth) .. c.name .. "  ->  " .. c.mesh)
                end
            end
            imgui.tree_pop()
        end
        local changed
        changed, showJoints = imgui.checkbox("Show hunter skeleton joints", showJoints)
        if showJoints and report.player_joints then
            imgui.text_colored(#report.player_joints .. " joints", 0xFFA0D0FF)
            for i = 1, #report.player_joints, 6 do
                imgui.text(table.concat(report.player_joints, ", ", i, math.min(i + 5, #report.player_joints)))
            end
        end
    end
    imgui.tree_pop()
end)
