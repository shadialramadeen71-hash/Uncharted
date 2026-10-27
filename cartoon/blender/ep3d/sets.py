"""3D sets and props for the Blender episodes."""
import math
import random

import bpy

import toon3d as T


def window_mat(name, lit=(1.0, 0.75, 0.35), wall=(0.06, 0.04, 0.07), scale=6.0, seed=0):
    """Building facade: a brick texture used as a grid of randomly lit windows."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = scale
    brick.inputs["Mortar Size"].default_value = 0.35
    brick.inputs["Color1"].default_value = (*lit, 1)
    brick.inputs["Color2"].default_value = (*wall, 1)
    brick.inputs["Mortar"].default_value = (*wall, 1)
    brick.offset = 0.0
    brick.inputs["Bias"].default_value = 0.15 + seed * 0.05
    nt.links.new(brick.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def street():
    T.world((0.3, 0.04, 0.03), (0.95, 0.38, 0.14), 1.0)
    road = T.toon("road", (0.05, 0.05, 0.07), gloss=True)
    walk = T.toon("sidewalk", (0.14, 0.13, 0.16))
    T.box("road", (40, 30, 0.1), (0, 8, -0.05), road)
    T.box("sidewalk", (40, 4, 0.2), (0, -3.2, 0.0), walk)
    for k in range(-6, 7):  # dashed line
        T.box(f"dash{k}", (1.2, 0.12, 0.02), (k * 3.0, 4.0, 0.01), T.toon("dash", (0.9, 0.75, 0.2)))
    random.seed(3)
    for i, x in enumerate(range(-16, 18, 4)):  # deco towers behind the street
        h = random.uniform(10, 24)
        b = T.box(f"tower{i}", (3.6, 3.0, h), (x, 16 + random.uniform(-1, 1), h / 2), window_mat(f"win{i}", seed=i % 4))
        if random.random() < 0.5:
            T.cone(f"spire{i}", 0.6, 0.0, 3, (x, 16, h + 1.5), T.toon("tower", (0.05, 0.03, 0.05)))
    for x in (-4.5, 4.5):  # street lamps
        T.cyl(f"lamp{x}", 0.06, 4, (x, -1.6, 2), T.toon("lamppost", (0.05, 0.05, 0.06)))
        T.sphere(f"bulb{x}", 0.25, (x, -1.6, 4.1), T.toon("bulb", (1.0, 0.85, 0.5), emit=4.0))
        T.light("POINT", (x, -1.6, 3.8), 600, (1.0, 0.8, 0.5), 0.3)
    T.light("SUN", (0, 0, 10), 2.5, (1.0, 0.6, 0.45), rot=(0.9, 0.2, 0.6))
    T.light("SUN", (0, 0, 10), 1.2, (0.35, 0.5, 1.0), rot=(1.2, -0.3, -2.4))  # blue rim from behind


def batmobile(loc=(0.6, 1.8, 0)):
    """Long low car with fins; its paint colour can be keyed (pink -> black)."""
    root = T.empty("car", loc)
    paint = T.toon("carpaint", (0.03, 0.03, 0.05), gloss=True)
    body = T.box("carbody", (4.4, 1.5, 0.55), (0, 0, 0.55), paint, root, bevel=0.2)
    T.box("carhood", (1.6, 1.3, 0.35), (0.9, 0, 0.95), paint, root, bevel=0.15)
    T.sphere("canopy", 0.6, (-0.3, 0, 1.0), T.toon("glass", (0.2, 0.32, 0.5), gloss=True), root, scale=(1.4, 0.9, 0.5))
    for sy in (-0.7, 0.7):
        T.box(f"fin{sy}", (0.9, 0.06, 0.35), (-1.8, sy, 0.95), paint, root, rot=(0, 0.35, 0))
    for wx in (-1.4, 1.4):
        for wy in (-0.78, 0.78):
            T.cyl(f"wheel{wx}{wy}", 0.38, 0.3, (wx, wy, 0.38), T.toon("tyre", (0.02, 0.02, 0.02)), root, rot=(math.pi / 2, 0, 0))
    T.sphere("headl", 0.12, (2.2, -0.5, 0.6), T.toon("headlight", (1, 0.95, 0.7), emit=3.0), root)
    T.sphere("headr", 0.12, (2.2, 0.5, 0.6), T.toon("headlight", (1, 0.95, 0.7), emit=3.0), root)
    return root, paint


def key_paint(mat, frame, color):
    """Key the toon ramp's lit + shadow colours (or the BSDF base colour in Cycles)."""
    nt = mat.node_tree
    for node in nt.nodes:
        if node.type == "VALTORGB":
            node.color_ramp.elements[1].color = (*color, 1)
            node.color_ramp.elements[1].keyframe_insert("color", frame=frame)
            node.color_ramp.elements[0].color = (*[c * 0.35 for c in color], 1)
            node.color_ramp.elements[0].keyframe_insert("color", frame=frame)
        if node.type == "BSDF_PRINCIPLED":
            node.inputs["Base Color"].default_value = (*color, 1)
            node.inputs["Base Color"].keyframe_insert("default_value", frame=frame)


def whirlwind(name, loc):
    bpy.ops.mesh.primitive_cone_add(radius1=1.6, radius2=3.2, depth=4.0, location=loc, vertices=32)
    o = bpy.context.object
    o.name = name
    m = bpy.data.materials.new(name + "m")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.75, 0.85, 1.0, 1)
    em.inputs["Strength"].default_value = 1.5
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 3.0
    wave.inputs["Distortion"].default_value = 4.0
    nt.links.new(wave.outputs["Fac"], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    if hasattr(m, "blend_method"):
        m.blend_method = "BLEND"
    o.data.materials.append(m)
    return o


def spray_can(parent):
    can = T.cyl("spraycan", 0.05, 0.18, (0, -0.05, -0.42), T.toon("canm", (0.95, 0.4, 0.7)), parent)
    T.cyl("spraycap", 0.03, 0.04, (0, -0.05, -0.31), T.toon("capm", (0.9, 0.9, 0.9)), parent)
    return can


def elevator():
    T.world((0.02, 0.02, 0.03), (0.05, 0.05, 0.06), 0.3)
    wood = T.toon("wood", (0.42, 0.22, 0.12))
    brass = T.toon("brass", (0.85, 0.65, 0.25), gloss=True)
    T.box("floor", (3.4, 3.0, 0.1), (0, 0.6, -0.05), T.toon("carpet", (0.45, 0.08, 0.1)))
    T.box("back", (3.4, 0.1, 3.2), (0, 2.1, 1.6), wood)
    for sx in (-1, 1):
        T.box(f"side{sx}", (0.1, 3.0, 3.2), (1.7 * sx, 0.6, 1.6), wood)
        for k in range(3):
            T.box(f"panel{sx}{k}", (0.02, 0.8, 2.2), (1.64 * sx, -0.4 + k * 0.95, 1.5), brass)
    for k in range(4):
        T.box(f"bpanel{k}", (0.7, 0.02, 2.4), (-1.2 + k * 0.8, 2.04, 1.5), T.toon("woodlight", (0.55, 0.3, 0.16)))
    T.box("rail", (3.2, 0.06, 0.06), (0, 2.0, 1.0), brass)
    ceiling = T.box("ceiling", (3.4, 3.0, 0.1), (0, 0.6, 3.25), wood)
    lamp = T.box("ceilinglamp", (1.6, 1.2, 0.04), (0, 0.6, 3.19), T.toon("lampm", (1.0, 0.92, 0.75), emit=3.0), ceiling)
    lamp.parent = ceiling
    lamp.location = (0, 0, -0.06 / 1)
    # floor indicator + buttons
    T.box("indicator", (0.7, 0.02, 0.22), (0, 2.03, 2.9), brass)
    T.text_obj("floor_no", "13", (0, 2.0, 2.9), T.toon("digits", (1.0, 0.3, 0.2), emit=3.0), size=0.16)
    for k in range(6):
        T.sphere(f"btn{k}", 0.035, (1.6, -0.6 + (k % 2) * 0.12, 1.2 + (k // 2) * 0.14),
                 T.toon("btnm", (1.0, 0.9, 0.6), emit=1.5), scale=(0.4, 1, 1), seg=12)
    key = T.light("AREA", (0, 0.6, 3.0), 260, (1.0, 0.92, 0.78), 1.4, rot=(0, 0, 0))
    fill = T.light("POINT", (0, -2.5, 1.8), 60, (0.5, 0.6, 1.0), 1.0)
    return ceiling, key


def moon_light():
    return T.light("SUN", (0, 0, 10), 0.0, (0.55, 0.65, 1.0), rot=(0.3, 0.0, 0.0))
