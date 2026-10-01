-- MiquellaLight Scout (read-only)
--
-- Shows which model files the hunter is using right now: weapons, armor parts, and every
-- child object that has a mesh (face, hair, ...). For each one: the .mesh and .mdf2 paths,
-- material names, and the bone (joint) names. Nothing in the game is changed.
--
-- "Save report" writes everything to reframework/data/MiquellaLight/scout.json so it can
-- be shared, which is what we need to pick the weapon to replace and to line our models
-- up with the right bones. Weapons also list their material parameter names (the numbers
-- setMaterialFloat needs).
--
-- "Watch weapon state" records which number / true-false fields of the hunter's weapon
-- handling object change while you play (charge, demon mode, reload...) and saves them to
-- reframework/data/MiquellaLight/watch.json: that is how we find what the weapon action
-- effects should react to.
--
-- API usage follows MDF-XL (SilverEzredes) and the REFramework book examples. Untested.

local MOD = "MiquellaLight Scout"
local OUT = "MiquellaLight/scout.json"
local WATCH_OUT = "MiquellaLight/watch.json"
-- While watching, the report is also saved every few seconds per weapon type
-- (watch_cHunterWp00Handling.json ...), so nothing is lost and weapons don't overwrite each other.
local WATCH_AUTOSAVE = 2.0
local MAX_FIELDS = 600
local MAX_LOG = 200
local MESH = "via.render.Mesh"
local MAX_JOINTS = 600
local MAX_CHILDREN = 400

local report = nil
local status = ""
local showJoints = false
local watch = nil          -- { target, method, type, fields = { {field, name, last, changes, min, max} }, log }

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
        if withJoints then
            -- Parameter names per material, in index order (setMaterialFloat(material, index, value)).
            info.params = {}
            for i = 0, n - 1 do
                local names = {}
                local count = try(function() return mesh:getMaterialVariableNum(i) end) or 0
                for k = 0, count - 1 do
                    names[#names + 1] = try(function() return mesh:getMaterialVariableName(i, k) end) or "?"
                end
                info.params[#info.params + 1] = names
            end
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

-- ------------------------------------------------------------------ weapon state watch

-- Methods tried, in order, to reach the object holding the weapon's own state.
local HANDLING_METHODS = { "get_WeaponHandling", "get_WpHandling", "get_WeaponHandle" }

local function find_handling()
    local pm = sdk.get_managed_singleton("app.PlayerManager")
    local master = pm and try(function() return pm:getMasterPlayer() end)
    if not (master and try(function() return master:get_Valid() end)) then return nil end
    local character = master:get_Character()
    for _, m in ipairs(HANDLING_METHODS) do
        local h = try(function() return character:call(m) end)
        if h then return h, m end
    end
    return nil
end

-- Every instance field (including inherited ones) whose value is a number or true/false,
-- plus the same one level down inside object fields (a gauge or timer often lives in its
-- own small object). `catalog` collects every field's name and type for the report.
local function watchable_fields(obj, prefix, depth, list, catalog)
    list, catalog = list or {}, catalog or {}
    local td = try(function() return obj:get_type_definition() end)
    while td and #list < MAX_FIELDS do
        for _, f in ipairs(try(function() return td:get_fields() end) or {}) do
            if #list >= MAX_FIELDS then break end
            if not try(function() return f:is_static() end) then
                local name = prefix .. f:get_name()
                local ftype = try(function() return f:get_type():get_full_name() end) or "?"
                catalog[#catalog + 1] = name .. " : " .. ftype
                local v = try(function() return f:get_data(obj) end)
                if type(v) == "number" or type(v) == "boolean" then
                    list[#list + 1] = { field = f, owner = obj, name = name, last = v, changes = 0, min = v, max = v }
                elseif depth > 0 and type(v) == "userdata" and not ftype:match("^System%.") then
                    watchable_fields(v, name .. ".", depth - 1, list, catalog)
                end
            end
        end
        td = try(function() return td:get_parent_type() end)
    end
    return list, catalog
end

local function start_watch()
    local h, method = find_handling()
    if not h then return "Weapon handling object not found (tried " .. table.concat(HANDLING_METHODS, ", ") .. ")." end
    local typeName = try(function() return h:get_type_definition():get_full_name() end) or "?"
    local fields, catalog = watchable_fields(h, "", 1)
    watch = { target = h, method = method, type = typeName, fields = fields, catalog = catalog, log = {}, t0 = os.clock() }
    return "Watching " .. typeName .. " (" .. #watch.fields .. " fields). Do the action now."
end

local watch_report
local function update_watch()
    if not watch then return end
    if os.clock() >= (watch.nextSave or 0) then
        watch.nextSave = os.clock() + WATCH_AUTOSAVE
        local short = (watch.type or "unknown"):gsub("^app%.", "")
        pcall(json.dump_file, "MiquellaLight/watch_" .. short .. ".json", watch_report())
    end
    for _, w in ipairs(watch.fields) do
        local v = try(function() return w.field:get_data(w.owner) end)
        if v ~= nil and v ~= w.last then
            w.changes = w.changes + 1
            if type(v) == "number" then
                w.min, w.max = math.min(w.min, v), math.max(w.max, v)
            end
            if #watch.log < MAX_LOG then
                watch.log[#watch.log + 1] = string.format("%.2fs %s: %s -> %s", os.clock() - watch.t0, w.name,
                    tostring(w.last), tostring(v))
            end
            w.last = v
        end
    end
end

watch_report = function()
    local changed = {}
    for _, w in ipairs(watch.fields) do
        if w.changes > 0 then
            changed[#changed + 1] = { name = w.name, changes = w.changes, min = tostring(w.min), max = tostring(w.max),
                                      last = tostring(w.last) }
        end
    end
    table.sort(changed, function(a, b) return a.name < b.name end)
    return { type = watch.type, method = watch.method, fields = #watch.fields, changed = changed, log = watch.log,
             catalog = watch.catalog }
end

re.on_frame(update_watch)

local function show_entry(info, key)
    if not info then return end
    local label = (info.slot and (info.slot .. ": ") or "") .. info.name
    if imgui.tree_node(label .. "##" .. key) then
        imgui.text("mesh: " .. tostring(info.mesh))
        imgui.text("mdf2: " .. tostring(info.mdf2))
        if info.materials then
            imgui.text("materials: " .. table.concat(info.materials, ", "))
        end
        if info.params then
            for i, names in ipairs(info.params) do
                imgui.text("  params of " .. tostring(info.materials[i]) .. " (" .. #names .. "): "
                    .. table.concat(names, ", ", 1, math.min(#names, 30)))
            end
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
    if imgui.button(watch and "Stop watching" or "Watch weapon state") then
        if watch then
            watch = nil
            status = "Stopped watching."
        else
            status = start_watch()
        end
    end
    if watch then
        imgui.same_line()
        if imgui.button("Save watch") then
            json.dump_file(WATCH_OUT, watch_report())
            status = "Saved to reframework/data/" .. WATCH_OUT
        end
    end
    imgui.text(status)
    if watch then
        local r = watch_report()
        imgui.text(r.type .. ": " .. #r.changed .. " of " .. r.fields .. " fields changed")
        for _, c in ipairs(r.changed) do
            imgui.text(string.format("  %s  x%d  [%s .. %s]  now %s", c.name, c.changes, c.min, c.max, c.last))
        end
    end

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
