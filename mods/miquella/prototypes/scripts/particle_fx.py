"""Particle effects for the previews, built the way game effects are (many small sprites
pushed around by force fields, coloured by age), instead of modelled flame shapes.

  fire_burst   frenzied flame: a ball of curling fire, white-yellow when born, burning
               through orange and deep red into dark smoke
  cold_breath  frost: cold air leaking off the ice and drifting away, fading as it goes

The particle state is simulated by stepping the scene's frames; call settle(frame) after
building everything.
"""
import math

import bpy
from mathutils import Vector

import common as c


def puff_material(name, ramp, strength, opacity, smoke=None):
    """Soft sprite: opaque in the middle, fading to nothing at its edge (facing), coloured
    and dimmed by the particle's age through `ramp` [(position, hex, strength factor)]."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for nd in list(nodes):
        nodes.remove(nd)
    out = nodes.new("ShaderNodeOutputMaterial")
    info = nodes.new("ShaderNodeParticleInfo")
    age = nodes.new("ShaderNodeMath")
    age.operation = "DIVIDE"
    links.new(info.outputs["Age"], age.inputs[0])
    links.new(info.outputs["Lifetime"], age.inputs[1])
    colour = nodes.new("ShaderNodeValToRGB")
    els = colour.color_ramp.elements
    els[0].position, els[0].color = ramp[0][0], c.hex_to_linear(ramp[0][1])
    els[1].position, els[1].color = ramp[-1][0], c.hex_to_linear(ramp[-1][1])
    for pos, hx, _ in ramp[1:-1]:
        e = els.new(pos)
        e.color = c.hex_to_linear(hx)
    links.new(age.outputs["Value"], colour.inputs["Fac"])
    power = nodes.new("ShaderNodeFloatCurve")
    pts = power.mapping.curves[0].points
    pts[0].location = (ramp[0][0], ramp[0][2])
    pts[1].location = (ramp[-1][0], ramp[-1][2])
    for pos, _, f in ramp[1:-1]:
        pts.new(pos, f)
    power.mapping.update()
    links.new(age.outputs["Value"], power.inputs["Value"])
    emission = nodes.new("ShaderNodeEmission")
    links.new(colour.outputs["Color"], emission.inputs["Color"])
    em_strength = nodes.new("ShaderNodeMath")
    em_strength.operation = "MULTIPLY"
    em_strength.inputs[1].default_value = strength
    links.new(power.outputs["Value"], em_strength.inputs[0])
    links.new(em_strength.outputs["Value"], emission.inputs["Strength"])
    # Soft edge: opacity from how directly the surface faces the camera.
    lw = nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    edge = nodes.new("ShaderNodeMath")
    edge.operation = "SUBTRACT"
    edge.inputs[0].default_value = 1.0
    links.new(lw.outputs["Facing"], edge.inputs[1])
    soft = nodes.new("ShaderNodeMath")
    soft.operation = "POWER"
    soft.inputs[1].default_value = 2.5
    links.new(edge.outputs["Value"], soft.inputs[0])
    fade = nodes.new("ShaderNodeMath")                 # and fade out over the particle's life
    fade.operation = "MULTIPLY"
    links.new(soft.outputs["Value"], fade.inputs[0])
    life = nodes.new("ShaderNodeMapRange")
    life.inputs["From Min"].default_value = 0.6
    life.inputs["From Max"].default_value = 1.0
    life.inputs["To Min"].default_value = opacity
    life.inputs["To Max"].default_value = 0.0
    links.new(age.outputs["Value"], life.inputs["Value"])
    links.new(life.outputs["Result"], fade.inputs[1])
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(fade.outputs["Value"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    if smoke:
        # Darken toward smoke: emission plus a little absorbing diffuse.
        diffuse = nodes.new("ShaderNodeBsdfDiffuse")
        diffuse.inputs["Color"].default_value = c.hex_to_linear(smoke)
        add = nodes.new("ShaderNodeAddShader")
        links.new(emission.outputs["Emission"], add.inputs[0])
        links.new(diffuse.outputs["BSDF"], add.inputs[1])
        links.new(add.outputs["Shader"], mix.inputs[2])
    else:
        links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def _sprite(name, mat):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=2, location=(0, 0, -50))
    s = bpy.context.active_object
    s.name = name
    s.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    s.hide_render = False
    return s


def _field(kind, location, strength, coll, **props):
    bpy.ops.object.effector_add(type=kind, location=Vector(location))
    f = bpy.context.active_object
    f.field.strength = strength
    for k, v in props.items():
        setattr(f.field, k, v)
    for col in list(f.users_collection):
        col.objects.unlink(f)
    coll.objects.link(f)
    return f


def emitter(name, center, radius, count, lifetime, speed, size, sprite, frames, seed, fields, gravity=0.0,
            damping=0.0):
    coll = bpy.data.collections.new(f"{name}_Fields")
    bpy.context.scene.collection.children.link(coll)
    for kind, offset, strength, props in fields:
        _field(kind, Vector(center) + Vector(offset), strength, coll, **props)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=radius, subdivisions=3, location=Vector(center))
    em = bpy.context.active_object
    em.name = name
    ps = em.modifiers.new("fx", "PARTICLE_SYSTEM").particle_system
    ps.seed = seed
    st = ps.settings
    st.count = count
    st.frame_start, st.frame_end = 1, frames
    st.lifetime = lifetime
    st.lifetime_random = 0.5
    st.emit_from = "FACE"
    st.normal_factor = speed
    st.factor_random = speed * 0.5
    st.damping = damping
    st.render_type = "OBJECT"
    st.instance_object = sprite
    st.particle_size = size
    st.size_random = 0.6
    st.use_rotations = True
    st.rotation_factor_random = 1.0
    st.effector_weights.gravity = gravity
    st.effector_weights.collection = coll
    em.show_instancer_for_render = False
    return em


def settle(frame):
    scene = bpy.context.scene
    scene.frame_start = 1
    for f in range(1, frame + 1):
        scene.frame_set(f)


def fire_burst(prefix, center, radius, frames=40, seed=7):
    """Frenzied flame: fire bursting out of a ball and curling back on itself."""
    mat = puff_material(f"{prefix}_Puff", [
        (0.0, "#FFF6D0", 1.0), (0.18, "#FFD34A", 0.9), (0.42, "#FF7A12", 0.55),
        (0.68, "#B0160C", 0.25), (1.0, "#2A0A26", 0.0)], strength=6.0, opacity=0.35, smoke="#1A0612")
    sprite = _sprite(f"{prefix}_Sprite", mat)
    r = radius
    return [sprite, emitter(f"{prefix}_Fire", center, r * 0.6, 14000, 12, r * 3.5, r * 0.22, sprite, frames, seed,
                            [("VORTEX", (0, 0, 0), r * 3, {}),
                             ("TURBULENCE", (0, 0, 0), r * 9, {"size": r * 0.5, "flow": 0.3}),
                             ("FORCE", (0, 0, 0), -r * 6, {}),           # pulls flames back: curling
                             ("WIND", (0, 0, -r * 3), r * 2, {})],        # and lifts them a little
                            damping=0.1)]


def cold_breath(prefix, center, radius, frames=60, seed=11):
    """Frost: cold air leaking off the ice, sinking a little and drifting away, fading."""
    mat = puff_material(f"{prefix}_Puff", [
        (0.0, "#FFFFFF", 1.0), (0.35, "#DDEEFF", 0.6), (1.0, "#A8CCF0", 0.0)], strength=0.9, opacity=0.1)
    sprite = _sprite(f"{prefix}_Sprite", mat)
    r = radius
    return [sprite, emitter(f"{prefix}_Breath", center, r * 0.9, 5000, 50, r * 0.8, r * 0.38, sprite, frames, seed,
                            [("TURBULENCE", (0, 0, 0), r * 3, {"size": r * 1.5, "flow": 0.5}),
                             ("WIND", (r * 4, 0, r), r * 1.2, {})],
                            gravity=0.004, damping=0.3)]


# ------------------------------------------------------------------ flow strands
# Sprites read as blobs at this size, so the effects are drawn as many thin, see-through
# strands traced through a swirling flow field (curl noise): the shapes come from the flow,
# not from modelling, the way smoke and fire streak in a game effect.

def curl(p, freq, seed_offset):
    """Curl of a 3D noise vector field (divergence-free swirling flow)."""
    from mathutils import noise
    e = 1e-3
    q = p * freq + seed_offset

    def n(v):
        return noise.noise_vector(v)

    dx, dy, dz = Vector((e, 0, 0)), Vector((0, e, 0)), Vector((0, 0, e))
    a = (n(q + dy).z - n(q - dy).z) - (n(q + dz).y - n(q - dz).y)
    b = (n(q + dz).x - n(q - dz).x) - (n(q + dx).z - n(q - dx).z)
    cc = (n(q + dx).y - n(q - dx).y) - (n(q + dy).x - n(q - dy).x)
    return Vector((a, b, cc)) / (2 * e)


def strand_material(name, centre_obj, reach, ramp, strength, opacity):
    """See-through emissive strand, coloured by distance from the effect's centre and fading
    out toward `reach`."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for nd in list(nodes):
        nodes.remove(nd)
    out = nodes.new("ShaderNodeOutputMaterial")
    coords = nodes.new("ShaderNodeTexCoord")
    coords.object = centre_obj
    d = nodes.new("ShaderNodeVectorMath")
    d.operation = "LENGTH"
    links.new(coords.outputs["Object"], d.inputs[0])
    t = nodes.new("ShaderNodeMath")
    t.operation = "DIVIDE"
    t.inputs[1].default_value = reach
    links.new(d.outputs["Value"], t.inputs[0])
    colour = nodes.new("ShaderNodeValToRGB")
    els = colour.color_ramp.elements
    els[0].position, els[0].color = ramp[0][0], c.hex_to_linear(ramp[0][1])
    els[1].position, els[1].color = ramp[-1][0], c.hex_to_linear(ramp[-1][1])
    for pos, hx in ramp[1:-1]:
        e = els.new(pos)
        e.color = c.hex_to_linear(hx)
    links.new(t.outputs["Value"], colour.inputs["Fac"])
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = strength
    links.new(colour.outputs["Color"], emission.inputs["Color"])
    fade = nodes.new("ShaderNodeMapRange")
    fade.inputs["From Min"].default_value = 0.25
    fade.inputs["From Max"].default_value = 1.0
    fade.inputs["To Min"].default_value = opacity
    fade.inputs["To Max"].default_value = 0.0
    links.new(t.outputs["Value"], fade.inputs["Value"])
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(fade.outputs["Result"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def trace(start, steps, dt, velocity):
    pts = [start]
    p = start.copy()
    for i in range(steps):
        p = p + velocity(p, i / steps) * dt
        pts.append(p.copy())
    return pts


GOLD_BURST = [(0.2, "#FFF6DC"), (0.4, "#FFD878"), (0.62, "#FFA628"), (0.82, "#B8641A"), (1.0, "#2A1A0A")]


def burst_strands(prefix, center, radius, ramp=GOLD_BURST, count=220, strength=2.4, seed=3, lift=0.4):
    """A burst of light: strands thrown out of a point through the swirling flow, bright at
    the heart and fading out (the explosion version of fire_strands, in any palette)."""
    import random
    rng = random.Random(seed)
    C = Vector(center)
    hub = c.link(bpy.data.objects.new(f"{prefix}_Centre", None))
    hub.location = C
    mat = strand_material(f"{prefix}_Strand", hub, radius * 3.2, ramp, strength=strength, opacity=0.55)
    off = Vector((rng.uniform(0, 50), rng.uniform(0, 50), rng.uniform(0, 50)))

    def vel(p, t):
        rel = p - C
        return (rel.normalized() * (1.8 - 2.0 * t) * radius * 3 + curl(rel / radius, 0.8, off) * radius
                + Vector((0, 0, radius * lift)))

    objs = [hub]
    for k in range(count):
        z = rng.uniform(-1, 1)
        a = rng.uniform(0, 2 * math.pi)
        d = Vector((math.sqrt(1 - z * z) * math.cos(a), math.sqrt(1 - z * z) * math.sin(a), z))
        pts = trace(C + d * radius * rng.uniform(0.1, 0.4), 36, rng.uniform(0.012, 0.022), vel)
        objs.append(c.curve_tube(f"{prefix}_S{k}", pts, [1 - 0.8 * i / (len(pts) - 1) for i in range(len(pts))],
                                 mat, bevel=radius * rng.uniform(0.02, 0.05), resolution=1))
    return objs


def fire_strands(prefix, center, radius, count=260, seed=7):
    """Frenzied flame: strands of fire leaving the ball, swirling and curling back on
    themselves, white-yellow near the ball, orange, deep red, then dark smoke."""
    import random
    rng = random.Random(seed)
    C = Vector(center)
    hub = c.link(bpy.data.objects.new(f"{prefix}_Centre", None))
    hub.location = C
    mat = strand_material(f"{prefix}_Strand", hub, radius * 3.2,
                          [(0.25, "#FFE08A"), (0.42, "#FFB82A"), (0.6, "#FF6A10"), (0.8, "#A0120E"), (1.0, "#2A0A26")],
                          strength=2.0, opacity=0.5)
    off = Vector((rng.uniform(0, 50), rng.uniform(0, 50), rng.uniform(0, 50)))

    def vel(p, t):
        rel = p - C
        out = rel.normalized()
        swirl = curl(rel / radius, 0.9, off)
        return out * (1.6 - 2.2 * t) * radius * 3 + swirl * radius * 1.1 + Vector((0, 0, radius * 0.9))

    objs = [hub]
    for k in range(count):
        z = rng.uniform(-1, 1)
        a = rng.uniform(0, 2 * math.pi)
        d = Vector((math.sqrt(1 - z * z) * math.cos(a), math.sqrt(1 - z * z) * math.sin(a), z))
        pts = trace(C + d * radius * rng.uniform(0.75, 1.0), 40, rng.uniform(0.012, 0.02), vel)
        w = radius * rng.uniform(0.02, 0.06)
        objs.append(c.curve_tube(f"{prefix}_S{k}", pts, [1 - 0.8 * i / (len(pts) - 1) for i in range(len(pts))],
                                 mat, bevel=w, resolution=1))
    return objs


def breath_strands(prefix, center, radius, count=420, seed=11):
    """Frost: faint strands of cold air seeping off the ice, sinking a little and drifting
    away, thinning out as they go."""
    import random
    rng = random.Random(seed)
    C = Vector(center)
    hub = c.link(bpy.data.objects.new(f"{prefix}_Centre", None))
    hub.location = C
    mat = strand_material(f"{prefix}_Strand", hub, radius * 6.0,
                          [(0.15, "#FFFFFF"), (0.5, "#DDEEFF"), (1.0, "#9CC4EC")], strength=0.5, opacity=0.03)
    off = Vector((rng.uniform(0, 50), rng.uniform(0, 50), rng.uniform(0, 50)))
    drift = Vector((1.0, 0.3, -0.35)).normalized()

    def vel(p, t):
        rel = p - C
        return (rel.normalized() * radius * 0.6 + drift * radius * (0.6 + 2.0 * t)
                + curl(rel / radius, 0.45, off) * radius * 0.5)

    objs = [hub]
    glint = c.make_material(f"{prefix}_Glint", "#FFFFFF", roughness=0.1, emission="#DDF0FF", strength=8.0)
    for k in range(count):
        z = rng.uniform(-0.6, 1)
        a = rng.uniform(0, 2 * math.pi)
        d = Vector((math.sqrt(1 - z * z) * math.cos(a), math.sqrt(1 - z * z) * math.sin(a), z))
        pts = trace(C + d * radius * 0.9, 50, rng.uniform(0.03, 0.05), vel)
        w = radius * rng.uniform(0.05, 0.14)
        objs.append(c.curve_tube(f"{prefix}_S{k}", pts, [0.4 + 2.8 * i / (len(pts) - 1) for i in range(len(pts))],
                                 mat, bevel=w, resolution=3))
        if k % 18 == 0:                                       # a glint of frost riding the breath
            p = pts[rng.randrange(10, len(pts))]
            bpy.ops.mesh.primitive_ico_sphere_add(radius=radius * rng.uniform(0.02, 0.045), subdivisions=1, location=p)
            g = bpy.context.active_object
            g.name = f"{prefix}_Glint_{k}"
            g.data.materials.append(glint)
            objs.append(g)
    return objs


def cold_plume(prefix, center, radius, drift=(1.0, 0.0, -0.3), seed=11):
    """Frost: cold air leaking off the ice and trailing away in a streaky plume (a thin
    volume whose wisps are drawn out along the drift and thin out with distance), with
    glints of frost riding in it."""
    import random
    rng = random.Random(seed)
    C = Vector(center)
    d = Vector(drift).normalized()
    hub = c.link(bpy.data.objects.new(f"{prefix}_Centre", None))
    hub.location = C
    mat = bpy.data.materials.new(f"{prefix}_Plume")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for nd in list(nodes):
        nodes.remove(nd)
    out = nodes.new("ShaderNodeOutputMaterial")
    vol = nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = c.hex_to_linear("#EAF4FF")
    vol.inputs["Emission Color"].default_value = c.hex_to_linear("#CFE6FF")
    coords = nodes.new("ShaderNodeTexCoord")
    coords.object = hub
    rel = nodes.new("ShaderNodeVectorMath")
    rel.operation = "SCALE"
    rel.inputs["Scale"].default_value = 1.0 / radius
    links.new(coords.outputs["Object"], rel.inputs[0])
    along = nodes.new("ShaderNodeVectorMath")
    along.operation = "DOT_PRODUCT"
    along.inputs[1].default_value = d
    links.new(rel.outputs["Vector"], along.inputs[0])
    on_axis = nodes.new("ShaderNodeVectorMath")
    on_axis.operation = "SCALE"
    on_axis.inputs[0].default_value = d
    links.new(along.outputs["Value"], on_axis.inputs["Scale"])
    off_axis = nodes.new("ShaderNodeVectorMath")
    off_axis.operation = "SUBTRACT"
    links.new(rel.outputs["Vector"], off_axis.inputs[0])
    links.new(on_axis.outputs["Vector"], off_axis.inputs[1])
    perp = nodes.new("ShaderNodeVectorMath")
    perp.operation = "LENGTH"
    links.new(off_axis.outputs["Vector"], perp.inputs[0])
    # Streaks: noise squashed along the drift so its features are drawn out into wisps.
    squash = nodes.new("ShaderNodeVectorMath")
    squash.operation = "SCALE"
    squash.inputs["Scale"].default_value = 0.22
    links.new(on_axis.outputs["Vector"], squash.inputs[0])
    streak = nodes.new("ShaderNodeVectorMath")
    streak.operation = "ADD"
    links.new(off_axis.outputs["Vector"], streak.inputs[0])
    links.new(squash.outputs["Vector"], streak.inputs[1])
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.7
    noise.inputs["Detail"].default_value = 9.0
    noise.inputs["Distortion"].default_value = 0.8
    noise.noise_dimensions = "4D"
    noise.inputs["W"].default_value = rng.uniform(0, 10)
    links.new(streak.outputs["Vector"], noise.inputs["Vector"])
    wisp = nodes.new("ShaderNodeMapRange")
    wisp.inputs["From Min"].default_value = 0.52
    wisp.inputs["From Max"].default_value = 0.78
    links.new(noise.outputs["Fac"], wisp.inputs["Value"])
    # The plume widens as it goes and fades from the ice to its tail.
    width = nodes.new("ShaderNodeMath")
    width.operation = "MULTIPLY_ADD"
    width.inputs[1].default_value = 0.3
    width.inputs[2].default_value = 1.1
    links.new(along.outputs["Value"], width.inputs[0])
    across = nodes.new("ShaderNodeMath")
    across.operation = "DIVIDE"
    links.new(perp.outputs["Value"], across.inputs[0])
    links.new(width.outputs["Value"], across.inputs[1])
    side = nodes.new("ShaderNodeMapRange")
    side.inputs["From Min"].default_value = 0.3
    side.inputs["From Max"].default_value = 1.0
    side.inputs["To Min"].default_value = 1.0
    side.inputs["To Max"].default_value = 0.0
    links.new(across.outputs["Value"], side.inputs["Value"])
    head = nodes.new("ShaderNodeMapRange")
    head.inputs["From Min"].default_value = -0.8
    head.inputs["From Max"].default_value = 0.6
    links.new(along.outputs["Value"], head.inputs["Value"])
    tail = nodes.new("ShaderNodeMapRange")
    tail.inputs["From Min"].default_value = 1.0
    tail.inputs["From Max"].default_value = 6.5
    tail.inputs["To Min"].default_value = 1.0
    tail.inputs["To Max"].default_value = 0.0
    links.new(along.outputs["Value"], tail.inputs["Value"])
    dens = nodes.new("ShaderNodeMath")
    dens.operation = "MULTIPLY"
    links.new(wisp.outputs["Result"], dens.inputs[0])
    links.new(side.outputs["Result"], dens.inputs[1])
    dens2 = nodes.new("ShaderNodeMath")
    dens2.operation = "MULTIPLY"
    links.new(dens.outputs["Value"], dens2.inputs[0])
    links.new(head.outputs["Result"], dens2.inputs[1])
    dens3 = nodes.new("ShaderNodeMath")
    dens3.operation = "MULTIPLY"
    links.new(dens2.outputs["Value"], dens3.inputs[0])
    links.new(tail.outputs["Result"], dens3.inputs[1])
    amount = nodes.new("ShaderNodeMath")
    amount.operation = "MULTIPLY"
    amount.inputs[1].default_value = 190.0
    links.new(dens3.outputs["Value"], amount.inputs[0])
    links.new(amount.outputs["Value"], vol.inputs["Density"])
    glow = nodes.new("ShaderNodeMath")
    glow.operation = "MULTIPLY"
    glow.inputs[1].default_value = 4.0
    links.new(dens3.outputs["Value"], glow.inputs[0])
    links.new(glow.outputs["Value"], vol.inputs["Emission Strength"])
    links.new(vol.outputs["Volume"], out.inputs["Volume"])
    # Domain: an egg stretched along the drift, starting just behind the ice.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=C + d * radius * 2.6)
    dom = bpy.context.active_object
    dom.name = f"{prefix}_Plume"
    dom.scale = (radius * 4.2, radius * 2.4, radius * 2.4)
    dom.rotation_mode = "QUATERNION"
    dom.rotation_quaternion = Vector((1, 0, 0)).rotation_difference(d)
    dom.data.materials.append(mat)
    objs = [hub, dom]
    glint = c.make_material(f"{prefix}_Glint", "#FFFFFF", roughness=0.1, emission="#DDF0FF", strength=8.0)
    for k in range(16):
        u = rng.uniform(0.3, 5.0)
        side_v = d.orthogonal().normalized()
        side_v.rotate(__import__("mathutils").Quaternion(d, rng.uniform(0, 2 * math.pi)))
        p = C + d * radius * u + side_v * radius * rng.uniform(0, 0.9 + 0.25 * u)
        bpy.ops.mesh.primitive_ico_sphere_add(radius=radius * rng.uniform(0.02, 0.04), subdivisions=1, location=p)
        g = bpy.context.active_object
        g.name = f"{prefix}_Glint_{k}"
        g.data.materials.append(glint)
        objs.append(g)
    return objs
