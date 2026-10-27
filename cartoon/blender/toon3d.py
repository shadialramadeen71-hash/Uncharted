"""3D toon renderer in Blender (bpy) for the hero episodes.

Episodes are authored with the same engine as the 2D series (dialogue, timing, Tracks for x/y/facing,
arm poses, expressions, scene cuts); this module turns them into a cel-shaded 3D scene: characters
built from primitives with jointed limbs, mouths driven by the voice, walk cycles from the engine's
gait phase, cameras, lights and sets.  1 m in Blender = 300 px of the 2D layout.
"""
import math

import bpy
from mathutils import Vector

PX = 1 / 300.0  # 2D px -> metres
FPS = 30


# ------------------------------------------------------------------ scene setup
def reset(res=(540, 960)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "Standard"
    return sc


def use_engine(sc, engine):
    sc.render.engine = engine
    if engine == "CYCLES":
        sc.cycles.samples = 12
        sc.cycles.use_denoising = True
        sc.cycles.device = "CPU"
        sc.cycles.max_bounces = 2
    else:
        try:
            sc.eevee.taa_render_samples = 4
        except AttributeError:
            pass
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = "ABSOLUTE"
    sc.render.line_thickness = 1.5
    ls = sc.view_layers[0].freestyle_settings.linesets
    if len(ls) == 0:
        ls.new("lines")
    ls[0].select_by_visibility = True
    if ls[0].linestyle is None:
        ls[0].linestyle = bpy.data.linestyles.new("ink")
    ls[0].linestyle.color = (0.02, 0.02, 0.04)
    ls[0].linestyle.thickness = 1.5


def world(color_top=(0.35, 0.05, 0.04), color_bottom=(0.9, 0.35, 0.12), strength=1.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    tex = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tex.outputs["Window"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = (*color_bottom, 1)
    ramp.color_ramp.elements[1].color = (*color_top, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs[0])


# ------------------------------------------------------------------ materials
_MATS = {}


def toon(name, color, shadow=None, emit=0.0, gloss=False):
    """Cel-shaded material: two hard tones (lit / dark-blue shadow), like 90s TV animation."""
    key = (name, tuple(color), emit)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    if emit > 0:
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs["Color"].default_value = (*color, 1)
        e.inputs["Strength"].default_value = emit
        nt.links.new(e.outputs[0], out.inputs[0])
    else:
        p = nt.nodes.new("ShaderNodeBsdfPrincipled")
        p.inputs["Base Color"].default_value = (*color, 1)
        p.inputs["Roughness"].default_value = 0.25 if gloss else 0.9
        if "Specular IOR Level" in p.inputs:
            p.inputs["Specular IOR Level"].default_value = 0.5 if gloss else 0.05
        if bpy.context.scene.render.engine != "CYCLES":
            s2r = nt.nodes.new("ShaderNodeShaderToRGB")
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.interpolation = "CONSTANT"
            sh = shadow or tuple(c * 0.35 + d for c, d in zip(color, (0.0, 0.01, 0.06)))
            ramp.color_ramp.elements[0].color = (*sh, 1)
            ramp.color_ramp.elements[1].position = 0.18
            ramp.color_ramp.elements[1].color = (*color, 1)
            nt.links.new(p.outputs[0], s2r.inputs[0])
            nt.links.new(s2r.outputs["Color"], ramp.inputs["Fac"])
            em = nt.nodes.new("ShaderNodeEmission")
            nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
            nt.links.new(em.outputs[0], out.inputs[0])
        else:
            nt.links.new(p.outputs[0], out.inputs[0])
    _MATS[key] = m
    return m


def _assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def _smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


# ------------------------------------------------------------------ primitives
def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.location = loc
    if parent:
        e.parent = parent
    return e


def sphere(name, r, loc, mat, parent=None, scale=(1, 1, 1), seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    _smooth(_assign(o, mat))
    if parent:
        o.parent = parent
    return o


def cyl(name, r, depth, loc, mat, parent=None, rot=(0, 0, 0), verts=20):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    _smooth(_assign(o, mat))
    if parent:
        o.parent = parent
    return o


def box(name, size, loc, mat, parent=None, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    _assign(o, mat)
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = 3
    if parent:
        o.parent = parent
    return o


def cone(name, r1, r2, depth, loc, mat, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot, vertices=24)
    o = bpy.context.object
    o.name = name
    _smooth(_assign(o, mat))
    if parent:
        o.parent = parent
    return o


def capsule(name, r, length, loc, mat, parent=None):
    """Limb segment hanging down from loc (its pivot)."""
    piv = empty(name + "_pivot", loc, parent)
    cyl(name, r, length, (0, 0, -length / 2), mat, piv)
    sphere(name + "_j", r, (0, 0, 0), mat, piv, seg=16)
    sphere(name + "_e", r, (0, 0, -length), mat, piv, seg=16)
    return piv


def text_obj(name, txt, loc, mat, parent=None, size=0.2, rot=(math.pi / 2, 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.body = txt
    o.data.size = size
    o.data.align_x = "CENTER"
    o.data.align_y = "CENTER"
    o.data.extrude = 0.01
    _assign(o, mat)
    if parent:
        o.parent = parent
    return o


# ------------------------------------------------------------------ characters
LOOKS = {
    "batman": dict(suit=(0.42, 0.45, 0.52), dark=(0.02, 0.025, 0.04), hi=(0.15, 0.25, 0.5), skin=(0.78, 0.55, 0.4),
                   belt=(0.95, 0.6, 0.12), emblem="bat", cape=(0.02, 0.025, 0.04), cowl=True, height=1.0),
    "superman": dict(suit=(0.1, 0.25, 0.75), dark=(0.75, 0.06, 0.06), skin=(0.9, 0.68, 0.52), belt=(0.98, 0.78, 0.1),
                     emblem="S", cape=(0.78, 0.06, 0.06), hair=(0.03, 0.03, 0.05), boots=(0.78, 0.06, 0.06), height=1.0),
    "joker": dict(suit=(0.4, 0.14, 0.55), dark=(0.25, 0.08, 0.35), skin=(0.95, 0.94, 0.9), shirt=(0.95, 0.5, 0.12),
                  hair=(0.12, 0.6, 0.2), boots=(0.15, 0.06, 0.2), coat=True, height=1.02, grin=True),
}


class Toon:
    """A jointed toon character; animate() reads the 2D engine character's tracks each frame."""

    def __init__(self, name, look):
        L = self.L = look
        self.name = name
        h = look.get("height", 1.0)
        self.root = empty(name + "_root")
        self.body = empty(name + "_body", (0, 0, 0.95 * h), self.root)  # pelvis
        suit = toon(name + "_suit", L["suit"])
        dark = toon(name + "_dark", L.get("dark", L["suit"]))
        skin = toon(name + "_skin", L["skin"])
        boots = toon(name + "_boots", L.get("boots", L.get("dark", (0.05, 0.05, 0.05))))
        # legs (pivot at the hip, knee pivot inside)
        self.legs = []
        for side in (-1, 1):
            hipp = empty(f"{name}_hip{side}", (0.11 * side, 0, 0), self.body)
            thigh = capsule(f"{name}_thigh{side}", 0.085, 0.45, (0, 0, 0), suit, hipp)
            knee = empty(f"{name}_knee{side}", (0, 0, -0.45), hipp)
            capsule(f"{name}_shin{side}", 0.075, 0.42, (0, 0, 0), boots if L.get("boots") or name == "batman" else suit, knee)
            box(f"{name}_foot{side}", (0.13, 0.26, 0.09), (0, -0.07, -0.47), boots, knee, bevel=0.03)
            self.legs.append((hipp, knee))
        # torso
        self.chest = empty(name + "_chest", (0, 0, 0.0), self.body)
        tor = sphere(name + "_torso", 0.26, (0, 0, 0.33), suit, self.chest, scale=(0.95 if name == "joker" else 1.08, 0.68, 1.38))
        sphere(name + "_pelvis", 0.22, (0, 0, 0.02), suit if not L.get("coat") else dark, self.chest, scale=(1.05, 0.8, 0.6))
        if L.get("belt"):
            cyl(name + "_belt", 0.25, 0.07, (0, 0, 0.1), toon(name + "_beltm", L["belt"]), self.chest)
        if L.get("coat"):  # long purple coat tails + orange shirt + green bow
            cone(name + "_coat", 0.33, 0.24, 0.6, (0, 0.02, -0.15), toon(name + "_coatm", L["suit"]), self.chest)
            box(name + "_shirt", (0.14, 0.02, 0.32), (0, -0.2, 0.42), toon(name + "_shirtm", L["shirt"]), self.chest)
            box(name + "_bow", (0.14, 0.03, 0.06), (0, -0.22, 0.6), toon(name + "_bowm", L["hair"]), self.chest)
        if L.get("emblem") == "bat":
            sphere(name + "_oval", 0.13, (0, -0.21, 0.45), toon(name + "_ovalm", (0.98, 0.72, 0.15)), self.chest, scale=(1.2, 0.2, 0.6))
            for sx in (-1, 1):
                box(name + f"_wing{sx}", (0.1, 0.02, 0.035), (0.07 * sx, -0.24, 0.46), dark, self.chest, rot=(0, -0.35 * sx, 0))
            box(name + "_batb", (0.05, 0.02, 0.06), (0, -0.24, 0.45), dark, self.chest)
        if L.get("emblem") == "S":
            box(name + "_shield", (0.22, 0.02, 0.16), (0, -0.21, 0.47), toon(name + "_shm", (0.85, 0.08, 0.08)), self.chest,
                rot=(0, 0, 0))
            text_obj(name + "_S", "S", (0, -0.235, 0.46), toon(name + "_sm", (1.0, 0.82, 0.1)), self.chest, size=0.17)
        # cape: subdivided plane with a wave modifier (flutters on its own)
        if L.get("cape"):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.2, 0.05))
            cape = bpy.context.object
            cape.name = name + "_cape"
            cape.scale = (0.62, 1, 1.25)
            cape.rotation_euler = (math.pi / 2 - 0.12, 0, 0)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.subdivide(number_cuts=10)
            bpy.ops.object.mode_set(mode="OBJECT")
            _assign(cape, toon(name + "_capem", L["cape"]))
            sol = cape.modifiers.new("thick", "SOLIDIFY")
            sol.thickness = 0.02
            wave = cape.modifiers.new("wave", "WAVE")
            wave.height = 0.04
            wave.width = 0.6
            wave.speed = 0.08
            wave.use_normal = True
            cape.parent = self.chest
            self.cape = cape
        # arms (shoulder pivot -> elbow pivot -> mitten hand)
        self.arms = []
        for side in (-1, 1):
            sh = empty(f"{name}_sh{side}", (0.36 * side * (0.85 if name == "joker" else 1), 0, 0.62), self.chest)
            capsule(f"{name}_upper{side}", 0.07, 0.3, (0, 0, 0), suit, sh)
            el = empty(f"{name}_el{side}", (0, 0, -0.3), sh)
            glove = toon(name + "_glove", L["dark"]) if name == "batman" else (toon(name + "_glovej", L["suit"]) if name == "joker" else suit)
            capsule(f"{name}_fore{side}", 0.065, 0.28, (0, 0, 0), glove, el)
            sphere(f"{name}_hand{side}", 0.085, (0, 0, -0.33), glove if name != "superman" else skin, el, scale=(0.9, 0.7, 1.1))
            self.arms.append((sh, el))
        # head
        self.neck = empty(name + "_neck", (0, 0, 0.72), self.chest)
        cyl(name + "_neckm", 0.08, 0.12, (0, 0, 0.04), skin, self.neck)
        self.head = empty(name + "_head", (0, 0, 0.2), self.neck)
        sphere(name + "_skull", 0.17, (0, 0, 0.02), skin, self.head, scale=(0.95, 1.0, 1.15))
        sphere(name + "_jaw", 0.15, (0, -0.02, -0.08), skin, self.head, scale=(1.05, 1.0, 0.75))
        eye_white = toon(name + "_eyew", (1, 1, 1))
        black = toon("black", (0.02, 0.02, 0.03))
        if L.get("cowl"):
            sphere(name + "_cowl", 0.18, (0, 0.012, 0.06), dark, self.head, scale=(0.98, 1.02, 1.08))
            for sx in (-1, 1):
                cone(name + f"_ear{sx}", 0.045, 0.0, 0.17, (0.09 * sx, 0.0, 0.25), dark, self.head)
                box(name + f"_eye{sx}", (0.055, 0.02, 0.022), (0.06 * sx, -0.17, 0.05), eye_white, self.head,
                    rot=(0, 0.25 * sx, 0))
            self.brows = []
        else:
            for sx in (-1, 1):
                sphere(name + f"_eye{sx}", 0.032, (0.06 * sx, -0.15, 0.05), eye_white, self.head, scale=(1, 0.5, 1.3), seg=16)
                sphere(name + f"_pupil{sx}", 0.016, (0.06 * sx, -0.168, 0.05), black, self.head, scale=(1, 0.5, 1.2), seg=12)
            self.brows = [box(name + f"_brow{sx}", (0.07, 0.02, 0.016), (0.06 * sx, -0.16, 0.11),
                              toon(name + "_browm", L.get("hair", (0.05, 0.05, 0.05))), self.head) for sx in (-1, 1)]
        if L.get("hair"):
            sphere(name + "_hair", 0.175, (0, 0.03, 0.08), toon(name + "_hairm", L["hair"]), self.head, scale=(1.0, 1.0, 0.85))
            if name == "superman":
                bpy.ops.mesh.primitive_torus_add(major_radius=0.025, minor_radius=0.008, location=(0.02, -0.16, 0.16))
                curl = bpy.context.object
                curl.parent = self.head
                _assign(curl, toon(name + "_hairm", L["hair"]))
        if name == "joker":
            cone(name + "_nose", 0.03, 0.0, 0.12, (0, -0.2, 0.0), skin, self.head, rot=(math.pi / 2, 0, 0))
        # mouth: dark disc scaled by the voice; the Joker's grin is wider
        self.mouth = sphere(name + "_mouth", 0.05, (0, -0.15, -0.09), toon("mouthm", (0.25, 0.04, 0.08)), self.head,
                            scale=(1.9 if L.get("grin") else 1.0, 0.4, 0.25), seg=16)
        if L.get("grin"):
            box(name + "_teeth", (0.15, 0.02, 0.02), (0, -0.165, -0.08), eye_white, self.head)

    # --------------------------------------------------------------
    def animate(self, ch, n, ground_z=0.0, fps=FPS):
        """Key every frame from the 2D engine character ch (tracks, gait phase, mouth curve)."""
        for fi in range(n):
            t = fi / fps
            tr = ch.tr
            phase, w, v = ch.frames[min(fi, len(ch.frames) - 1)]
            x = (tr["x"].at(t) - 540) * PX
            y_up = -tr["y"].at(t) * PX
            face = tr["face"].at(t)
            vis = tr["visible"].at(t) > 0.5
            self.root.location = (x, tr.get("depth", None).at(t) if "depth" in tr else 0.0, ground_z + y_up)
            # facing: +1 -> look to screen-right, -1 -> screen-left, turned 3/4 towards the camera
            self.root.rotation_euler = (math.radians(tr["rot"].at(t)) * -1 * (1 if face >= 0 else -1), 0,
                                        math.radians(90 - 35) * (1 if face >= 0 else -1) * min(1, abs(face) * 2))
            self.root.scale = (1, 1, 1) if vis else (0.0001, 0.0001, 0.0001)
            self.root.keyframe_insert("location", frame=fi)
            self.root.keyframe_insert("rotation_euler", frame=fi)
            self.root.keyframe_insert("scale", frame=fi)
            # walk: legs swing opposite, knees bend in swing; pelvis bobs
            p = phase % 1.0
            sw = 0.55 * w
            for k, (hipp, knee) in enumerate(self.legs):
                ph = 2 * math.pi * (p + 0.5 * k)
                hipp.rotation_euler = (sw * math.sin(ph), 0, 0)
                knee.rotation_euler = (-max(0.0, math.cos(ph)) * 0.9 * w - 0.05, 0, 0)
                hipp.keyframe_insert("rotation_euler", frame=fi)
                knee.keyframe_insert("rotation_euler", frame=fi)
            self.body.location.z = 0.95 * self.L.get("height", 1.0) - 0.03 * w * abs(math.cos(2 * math.pi * p))
            self.body.keyframe_insert("location", frame=fi)
            lean = tr["lean"].at(t)
            self.chest.rotation_euler = (math.radians(-lean), 0, 0)
            self.chest.keyframe_insert("rotation_euler", frame=fi)
            # arms: the 2D pose (shoulder, elbow) angles map onto forward rotations
            for k, (sh, el) in enumerate(self.arms):
                side = "F" if k == 1 else "B"
                s_a, e_a = tr["arm" + side].at(t)
                swing = -0.45 * w * math.sin(2 * math.pi * (p + 0.5 * k)) * tr["swing"].at(t)
                sh.rotation_euler = (-math.radians(s_a) + swing, 0, (0.12 if k else -0.12))
                el.rotation_euler = (-math.radians(e_a), 0, 0)
                sh.keyframe_insert("rotation_euler", frame=fi)
                el.keyframe_insert("rotation_euler", frame=fi)
            # head tilt + lip sync + brows by expression
            self.neck.rotation_euler = (math.radians(tr["tilt"].at(t)) * 0.6, 0, 0)
            self.neck.keyframe_insert("rotation_euler", frame=fi)
            m, _ = ch.mouth(t)
            ex = tr["expr"].at(t)
            base = 0.18 if ex in ("happy", "evil", "silly") else 0.12
            if ex == "shocked":
                base = 0.6
            self.mouth.scale = ((1.9 if self.L.get("grin") else 1.0) * (1 + 0.2 * m), 0.4, base + 0.9 * m)
            self.mouth.keyframe_insert("scale", frame=fi)
            for sx, b in zip((-1, 1), self.brows):
                ang = {"stern": 0.35, "evil": 0.4, "worried": -0.35, "shocked": -0.15}.get(ex, 0.0)
                b.rotation_euler = (0, ang * sx, 0)
                b.location.z = 0.11 + (0.025 if ex in ("shocked", "worried") else 0.0)
                b.keyframe_insert("rotation_euler", frame=fi)
                b.keyframe_insert("location", frame=fi)


def camera(loc, look_at, lens=32):
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = loc
    target = empty("cam_target", look_at)
    con = cam.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    bpy.context.scene.camera = cam
    return cam, target


def light(kind, loc, energy, color=(1, 1, 1), size=1.0, rot=(0, 0, 0)):
    d = bpy.data.lights.new(kind + "_l", kind)
    d.energy = energy
    d.color = color
    if hasattr(d, "shadow_soft_size"):
        d.shadow_soft_size = size
    o = bpy.data.objects.new(kind, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    return o
