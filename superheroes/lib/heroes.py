"""Procedural character / scene toolkit for the superhero shorts (Blender 5.x, bpy).

Every character is built from code: a pivot hierarchy (empties) carries the
meshes, so posing a joint is just keyframing that empty's rotation.

Axis conventions (character facing -Y, i.e. toward a camera placed at -Y):
  side s = +1 -> character's LEFT  (+X)
  side s = -1 -> character's RIGHT (-X)
  shoulder/hip X rotation negative  -> limb swings forward
  elbow X negative -> forearm bends forward, knee X positive -> shin bends back
  spine/head X positive -> lean / look down, Z positive -> turn to own left
"""
import bpy, bmesh, math, random, json, os
from mathutils import Vector

FPS = 24
PI = math.pi


# --------------------------------------------------------------------------- scene

def reset_scene(res=(960, 540), samples=20):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.fps = FPS
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.samples = samples
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.06
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 3
    s.cycles.diffuse_bounces = 1
    s.cycles.glossy_bounces = 1
    s.cycles.transmission_bounces = 2
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.cycles.blur_glossy = 1.0
    s.render.use_persistent_data = True
    s.render.image_settings.file_format = 'PNG'
    s.view_settings.view_transform = 'AgX'
    try:
        s.view_settings.look = 'AgX - Punchy'
    except Exception:
        pass
    return s


def link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def srgb(h):
    """hex -> linear rgb tuple"""
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


# --------------------------------------------------------------------------- materials

def mat(name, color='#808080', rough=0.5, metal=0.0, emit=None, estr=0.0, coat=0.0, sheen=0.0, alpha=1.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    col = srgb(color) if isinstance(color, str) else color
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if coat:
        b.inputs['Coat Weight'].default_value = coat
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
    if emit:
        e = srgb(emit) if isinstance(emit, str) else emit
        b.inputs['Emission Color'].default_value = (*e, 1)
        b.inputs['Emission Strength'].default_value = estr
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
    m.diffuse_color = (*col, 1)
    return m


def glow(name, color, strength=8.0):
    """pure emission material (lightning, energy, lights)"""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*srgb(color), 1)
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def key_emission(m, frame, strength):
    """keyframe emission strength of a glow() or mat() material"""
    nt = m.node_tree
    sock = None
    for n in nt.nodes:
        if n.type == 'EMISSION':
            sock = n.inputs['Strength']
        elif n.type == 'BSDF_PRINCIPLED':
            sock = n.inputs['Emission Strength']
    sock.default_value = strength
    sock.keyframe_insert('default_value', frame=frame)


# --------------------------------------------------------------------------- meshes

def _finish(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.update()
    return me


def revolve(name, prof, segs=24, sx=1.0, sy=1.0, drop=None):
    """surface of revolution around Z. prof = [(z, r), ...] top->bottom, r==0 -> pole.
    drop(x, y, z) -> True removes faces (used for openings like a hood's face hole)."""
    verts, faces, rings = [], [], []
    for z, r in prof:
        if r < 1e-6:
            rings.append([len(verts)])
            verts.append((0, 0, z))
        else:
            ring = []
            for i in range(segs):
                a = 2 * PI * i / segs
                ring.append(len(verts))
                verts.append((math.cos(a) * r * sx, math.sin(a) * r * sy, z))
            rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        for i in range(segs):
            j = (i + 1) % segs
            if len(A) == 1:
                f = (A[0], B[j], B[i])
            elif len(B) == 1:
                f = (A[i], A[j], B[0])
            else:
                f = (A[i], A[j], B[j], B[i])
            if drop:
                c = [sum(verts[k][d] for k in f) / len(f) for d in range(3)]
                if drop(*c):
                    continue
            faces.append(f)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    return _finish(me)


def capsule_prof(r1, r2, L, n=7, up=False):
    p = []
    for i in range(n + 1):
        a = PI / 2 * (1 - i / n)
        p.append((r1 * math.sin(a), r1 * math.cos(a)))
    for i in range(1, n + 1) if L < 1e-6 else range(n + 1):
        a = -PI / 2 * i / n
        p.append((-L + r2 * math.sin(a), r2 * math.cos(a)))
    if up:
        p = [(-z, r) for z, r in reversed(p)]
    return p


def capsule(name, r1, r2, L, up=False, sx=1, sy=1, segs=20):
    """tapered capsule hanging from the origin down -Z (or up +Z)"""
    return revolve(name, capsule_prof(r1, r2, L, up=up), segs, sx, sy)


def ellipsoid(name, rx, ry, rz, segs=24, rings=14, drop=None):
    prof = []
    for i in range(rings + 1):
        a = PI / 2 - PI * i / rings
        prof.append((math.sin(a) * rz, math.cos(a)))
    return revolve(name, prof, segs, rx, ry, drop=drop)


def cone(name, r, h, segs=12):
    return revolve(name, [(h, 0), (0, r), (0, 0)], segs)


def box(name, sx, sy, sz):
    """box with half sizes sx, sy, sz centered at origin"""
    v = [(x * sx, y * sy, z * sz) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return me


def prism(name, pts2d, depth):
    """extrude a 2D outline in the XZ plane by depth along Y (emblems)"""
    n = len(pts2d)
    v = [(x, -depth / 2, z) for x, z in pts2d] + [(x, depth / 2, z) for x, z in pts2d]
    f = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return me


def add(name, me, m=None, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
        subsurf=0, bevel=0.0, smooth=True):
    if m is not None:
        me.materials.append(m)
    o = link(bpy.data.objects.new(name, me))
    o.parent = parent
    o.location, o.rotation_euler, o.scale = loc, rot, scale
    if bevel:
        b = o.modifiers.new('bevel', 'BEVEL')
        b.width = bevel
        b.segments = 4
        b.limit_method = 'NONE'
        for p in me.polygons:
            p.use_smooth = True
    if subsurf:
        s = o.modifiers.new('subsurf', 'SUBSURF')
        s.levels = 1
        s.render_levels = subsurf
    return o


def empty(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    o = link(bpy.data.objects.new(name, None))
    o.empty_display_size = 0.05
    o.parent = parent
    o.location, o.rotation_euler = loc, rot
    return o


# --------------------------------------------------------------------------- keyframes

def key(o, frame, loc=None, rot=None, scale=None):
    if loc is not None:
        o.location = loc
        o.keyframe_insert('location', frame=frame)
    if rot is not None:
        o.rotation_euler = rot
        o.keyframe_insert('rotation_euler', frame=frame)
    if scale is not None:
        o.scale = scale if hasattr(scale, '__len__') else (scale,) * 3
        o.keyframe_insert('scale', frame=frame)


def show(o, frames_visible, start, end):
    """hide_render/hide_viewport keys: visible only on frames in frames_visible within [start, end]"""
    vis = set(frames_visible)
    for f in range(start - 1, end + 2):
        h = f not in vis
        o.hide_render = h
        o.hide_viewport = h
        o.keyframe_insert('hide_render', frame=f)
        o.keyframe_insert('hide_viewport', frame=f)


def hide_until(o, f_on, f_off=None):
    o.hide_render = True
    o.keyframe_insert('hide_render', frame=0)
    o.hide_render = True
    o.keyframe_insert('hide_render', frame=f_on - 1)
    o.hide_render = False
    o.keyframe_insert('hide_render', frame=f_on)
    if f_off:
        o.hide_render = True
        o.keyframe_insert('hide_render', frame=f_off)


def world_pos(o, frame):
    bpy.context.scene.frame_set(frame)
    return o.matrix_world.translation.copy()


# --------------------------------------------------------------------------- character

BOLT = [(-0.02, 0.07), (0.035, 0.07), (0.01, 0.015), (0.04, 0.015), (-0.03, -0.075),
        (-0.005, -0.012), (-0.035, -0.012)]


def star_pts(r1=0.065, r2=0.027, n=5):
    p = []
    for i in range(2 * n):
        a = PI / 2 + PI * i / n
        r = r1 if i % 2 == 0 else r2
        p.append((math.cos(a) * r, math.sin(a) * r))
    return p


class Character:
    pass


FINGERS = [  # (name, y offset, phalanx lengths, radius)
    ('index', -0.027, (0.036, 0.024, 0.019), 0.0105),
    ('middle', -0.009, (0.039, 0.026, 0.021), 0.0108),
    ('ring', 0.009, (0.036, 0.025, 0.020), 0.0102),
    ('pinky', 0.026, (0.029, 0.019, 0.016), 0.0090),
]


def build_character(cfg, loc=(0, 0, 0), facing=0.0):
    """cfg: name, mats{...}, female, bulk, hair, mask, emblem, cape, cloak, hat"""
    n = cfg['name']
    M = cfg['mats']
    fem = cfg.get('female', False)
    w = cfg.get('bulk', 1.0) * (0.86 if fem else 1.0)
    c = Character()
    c.name, c.cfg, c.p = n, cfg, {}

    ctrl = empty(n + '_ctrl', loc=loc, rot=(0, 0, facing))
    sc = cfg.get('scale', 0.92)
    ctrl.scale = (sc, sc, sc)
    c.ctrl = ctrl
    c.hip_h = 0.98
    root = empty(n + '_root', ctrl, (0, 0, c.hip_h))
    c.p['root'] = c.root = root

    # ---- pelvis / torso
    add(n + '_pelvis', ellipsoid(n + '_pelvis', 0.155 * w * (1.12 if fem else 1), 0.11, 0.12), M['pelvis'],
        root, (0, 0, -0.03), subsurf=1)
    spine = empty(n + '_spine', root, (0, 0, 0.06))
    c.p['spine'] = spine
    add(n + '_abdomen', capsule(n + '_abd', 0.135 * w, 0.145 * w, 0.26, up=True, sy=0.74), M['torso'],
        spine, (0, 0, 0.0), subsurf=1)
    chest_rx = 0.235 * w * (0.88 if fem else 1)
    add(n + '_chest', ellipsoid(n + '_chest', chest_rx, 0.142, 0.2), M['torso'], spine, (0, 0, 0.42), subsurf=1)
    if fem:
        for s in (1, -1):
            add(n + '_bust' + str(s), ellipsoid(n + '_bust', 0.066, 0.06, 0.058), M['torso'], spine,
                (s * 0.072, -0.098, 0.39), subsurf=1)
    if 'belt' in M:
        add(n + '_belt', ellipsoid(n + '_belt', 0.152 * w * (1.08 if fem else 1), 0.112, 0.032), M['belt'],
            spine, (0, 0, 0.0), subsurf=1)
        add(n + '_buckle', box(n + '_buckle', 0.03, 0.012, 0.024), M.get('emblem', M['belt']), spine,
            (0, -0.112, 0.0), bevel=0.008)
    if 'vest' in M:
        add(n + '_vest', ellipsoid(n + '_vest', chest_rx * 1.04, 0.15, 0.2), M['vest'], spine, (0, 0, 0.41),
            subsurf=1)
        add(n + '_vest_low', capsule(n + '_vl', 0.142 * w, 0.15 * w, 0.2, up=True, sy=0.76), M['vest'], spine,
            (0, 0, 0.08), subsurf=1)
        for s in (1, -1):
            add(n + '_stripe' + str(s), box(n + '_stripe', 0.012, 0.004, 0.11), M['stripe'], spine,
                (s * 0.08, -0.15, 0.36), rot=(0.12, 0, 0), bevel=0.003)
    if cfg.get('emblem') == 'bolt':
        add(n + '_emblem_bg', ellipsoid(n + '_ebg', 0.085, 0.02, 0.085), M['belt'], spine, (0, -0.128, 0.45),
            subsurf=1)
        add(n + '_emblem', prism(n + '_bolt', [(x * 1.05, z * 1.05) for x, z in BOLT], 0.012), M['emblem'], spine,
            (0, -0.146, 0.45), rot=(0, 0, 0))
    elif cfg.get('emblem') == 'star':
        add(n + '_emblem', prism(n + '_star', star_pts(), 0.012), M['emblem'], spine, (0, -0.158, 0.47),
            rot=(0.25, 0, 0))

    # ---- neck / head
    neck = empty(n + '_neck', spine, (0, 0, 0.575))
    c.p['neck'] = neck
    add(n + '_neckm', capsule(n + '_neckm', 0.056, 0.06, 0.08, up=True), M.get('neck', M['skin']), neck,
        (0, 0, -0.02), subsurf=1)
    head = empty(n + '_head', neck, (0, 0, 0.075))
    c.p['head'] = head
    hs = 0.95 if fem else 1.0
    add(n + '_skull', ellipsoid(n + '_skull', 0.105 * hs, 0.118 * hs, 0.135 * hs), M['skin'], head,
        (0, 0, 0.12), subsurf=1)
    add(n + '_jaw', ellipsoid(n + '_jaw', (0.08 if fem else 0.088) * hs, 0.094 * hs, 0.074 * hs), M['skin'], head,
        (0, -0.02, 0.05), subsurf=1)
    for s in (1, -1):
        add(n + '_ear' + str(s), ellipsoid(n + '_ear', 0.012, 0.024, 0.034), M['skin'], head,
            (s * 0.104 * hs, 0.005, 0.115), subsurf=1)
    add(n + '_nose', ellipsoid(n + '_nose', 0.014, 0.016, 0.024), M['skin'], head, (0, -0.118 * hs, 0.098),
        subsurf=1)
    c.mouth = add(n + '_mouth', ellipsoid(n + '_mouth', 0.026, 0.011, 0.0075), M.get('mouth', mat('mouth', '#4a1015', 0.4)),
                  head, (0, -0.107 * hs, 0.052), subsurf=1)
    if fem:
        add(n + '_lips', ellipsoid(n + '_lips', 0.028, 0.009, 0.006), M['lips'], head, (0, -0.109 * hs, 0.06),
            subsurf=1)
    if cfg.get('mask'):
        add(n + '_mask', ellipsoid(n + '_mask', 0.112 * hs, 0.126 * hs, 0.05, segs=32,
                                   drop=lambda x, y, z: y > 0.035 or (y > -0.02 and abs(z) > 0.02)),
            M['mask'], head, (0, 0, 0.135), subsurf=2)
    # eyes
    c.eyes, c.brows = [], []
    for s in (1, -1):
        piv = empty(n + '_eyepiv' + str(s), head, (s * 0.041 * hs, -0.117 * hs, 0.135))
        if cfg.get('glow_eyes'):
            e = add(n + '_eye' + str(s), ellipsoid(n + '_eye', 0.024, 0.014, 0.012), M['eye'], piv,
                    (0, 0, 0), rot=(0, -s * 0.25, 0), subsurf=1)
        else:
            e = add(n + '_eye' + str(s), ellipsoid(n + '_eye', 0.025, 0.016, 0.021), mat('eyewhite', '#f4f1ea', 0.15),
                    piv, (0, 0, 0), rot=(0, 0, -s * 0.25), subsurf=1)
            add(n + '_iris' + str(s), ellipsoid(n + '_iris', 0.0125, 0.005, 0.0135), M['iris'], e, (0, -0.0128, -0.001),
                subsurf=1)
            add(n + '_pupil' + str(s), ellipsoid(n + '_pupil', 0.006, 0.003, 0.0065), mat('pupil', '#050505', 0.1), e,
                (0, -0.0168, -0.001), subsurf=1)
            add(n + '_glint' + str(s), ellipsoid(n + '_glint', 0.0025, 0.002, 0.0025), glow('glint', '#ffffff', 4), e,
                (0.0045, -0.019, 0.0045))
        c.eyes.append(piv)
        b = add(n + '_brow' + str(s), ellipsoid(n + '_brow', 0.024, 0.007, 0.0065), M['brow'], head,
                (s * 0.041 * hs, -0.112 * hs, 0.19), rot=(0, -s * 0.12, 0), subsurf=1)
        c.brows.append(b)
    _hair(c, cfg, head, hs)

    # ---- arms
    sh_x = (0.2 if fem else 0.232) * w
    add(n + '_traps', ellipsoid(n + '_traps', (0.17 if fem else 0.2) * w, 0.11, 0.075), M['torso'], spine,
        (0, 0.01, 0.545), subsurf=1)
    for s, S in ((1, 'L'), (-1, 'R')):
        sh = empty(f'{n}_shoulder{S}', spine, (s * sh_x, 0, 0.52))
        sh.rotation_mode = 'ZXY'  # twist about the arm's own axis first
        c.p['shoulder' + S] = sh
        add(f'{n}_delt{S}', ellipsoid(n + '_delt', 0.078 * w, 0.074 * w, 0.08 * w), M['shoulder'], sh, (0, 0, -0.005),
            subsurf=1)
        add(f'{n}_uarm{S}', capsule(n + '_uarm', 0.064 * w, 0.05 * w, 0.27), M['upperarm'], sh, subsurf=1)
        el = empty(f'{n}_elbow{S}', sh, (0, 0, -0.28))
        c.p['elbow' + S] = el
        add(f'{n}_farm{S}', capsule(n + '_farm', 0.051 * w, 0.037 * w, 0.24), M['forearm'], el, subsurf=1)
        if cfg.get('cuffs', True):
            add(f'{n}_cuff{S}', capsule(n + '_cuff', 0.05 * w, 0.042 * w, 0.11), M['glove'], el, (0, 0, -0.135),
                subsurf=1)
        wr = empty(f'{n}_wrist{S}', el, (0, 0, -0.245))
        c.p['wrist' + S] = wr
        _hand(c, n, S, s, wr, M['glove'], w)

    # ---- legs
    hip_x = (0.092 if fem else 0.1) * w
    for s, S in ((1, 'L'), (-1, 'R')):
        hp = empty(f'{n}_hip{S}', root, (s * hip_x, 0, -0.04))
        c.p['hip' + S] = hp
        add(f'{n}_thigh{S}', capsule(n + '_thigh', 0.088 * w, 0.06 * w, 0.43), M['thigh'], hp, subsurf=1)
        kn = empty(f'{n}_knee{S}', hp, (0, 0, -0.44))
        c.p['knee' + S] = kn
        add(f'{n}_shin{S}', capsule(n + '_shin', 0.06 * w, 0.044 * w, 0.4, sy=1.05), M['shin'], kn, subsurf=1)
        add(f'{n}_calf{S}', ellipsoid(n + '_calf', 0.056 * w, 0.06 * w, 0.12), M['shin'], kn, (0, 0.012, -0.13),
            subsurf=1)
        if 'boot' in M and not cfg.get('no_boot_cuff'):
            add(f'{n}_bootc{S}', capsule(n + '_bootc', 0.066 * w, 0.05 * w, 0.24), M['boot'], kn, (0, 0, -0.17),
                subsurf=1)
        an = empty(f'{n}_ankle{S}', kn, (0, 0, -0.42))
        c.p['ankle' + S] = an
        add(f'{n}_foot{S}', box(n + '_foot', 0.046 * w, 0.115, 0.036), M.get('boot', M['shin']), an,
            (0, -0.05, -0.024), bevel=0.03)
        add(f'{n}_toe{S}', ellipsoid(n + '_toe', 0.05 * w, 0.05, 0.035), M.get('boot', M['shin']), an,
            (0, -0.135, -0.03), subsurf=1)
        add(f'{n}_sole{S}', box(n + '_sole', 0.05 * w, 0.14, 0.008), mat('sole', '#1b1b1b', 0.8), an,
            (0, -0.07, -0.058), bevel=0.006)

    # ---- capes / cloaks
    if cfg.get('cape'):
        _cape(c, n, spine, M['cape'], w)
    if cfg.get('cloak'):
        _cloak(c, n, spine, M['cloak'])

    c.rest = rest_pose()
    apply_pose(c, None, c.rest)
    return c


def _hand(c, n, S, s, wr, gm, w):
    pin = -s  # palm faces toward the body centre
    add(f'{n}_palm{S}', box(n + '_palm', 0.017 * w, 0.039, 0.044), gm, wr, (pin * 0.002, 0, -0.045), bevel=0.014)
    for fname, y, lens, r in FINGERS:
        par = wr
        z = -0.084
        chain = []
        for i, L in enumerate(lens):
            pv = empty(f'{n}_{fname}{i}{S}', par, (0, y if i == 0 else 0, z))
            add(f'{n}_{fname}{i}{S}m', capsule(n + '_ph', r * (1 - 0.08 * i), r * (0.92 - 0.08 * i), L - r * 0.5), gm,
                pv, subsurf=1)
            chain.append(pv)
            par, z = pv, -L
        c.p[f'{fname}{S}'] = chain
    tb = empty(f'{n}_thumb0{S}', wr, (pin * 0.01, -0.036, -0.022), rot=(-0.65, 0, s * 0.35))
    add(f'{n}_thumbm0{S}', capsule(n + '_th', 0.0135, 0.012, 0.03), gm, tb, subsurf=1)
    t1 = empty(f'{n}_thumb1{S}', tb, (0, 0, -0.036))
    add(f'{n}_thumbm1{S}', capsule(n + '_th1', 0.0118, 0.0105, 0.022), gm, t1, subsurf=1)
    c.p['thumb' + S] = [tb, t1]


def _hair(c, cfg, head, hs):
    n, M, style = c.name, cfg['mats'], cfg.get('hair')
    if style == 'spiky':
        add(n + '_haircap', ellipsoid(n + '_hc', 0.112 * hs, 0.124 * hs, 0.1,
                                      drop=lambda x, y, z: z < -0.045 or (y < -0.07 and z < 0.035)),
            M['hair'], head, (0, 0.012, 0.17), subsurf=1)
        rnd = random.Random(3)
        k = 0
        for th, phis in ((-0.25, (-0.45, -0.15, 0.15, 0.45)), (0.35, (-0.6, -0.2, 0.2, 0.6)),
                         (0.95, (-0.5, 0.0, 0.5)), (1.5, (-0.3, 0.3))):
            for ph in phis:
                ph += rnd.uniform(-0.06, 0.06)
                pos = (math.sin(ph) * 0.085 * math.cos(th * 0.5), 0.012 + math.sin(th) * 0.1,
                       0.17 + math.cos(th) * 0.085 * math.cos(ph))
                add(f'{n}_spike{k}', cone(n + '_sp', 0.036, 0.1 + rnd.uniform(-0.015, 0.03)), M['hair'], head, pos,
                    rot=(-th - 0.45, ph * 1.1, 0), subsurf=1)
                k += 1
    elif style == 'long':
        add(n + '_haircap', ellipsoid(n + '_hc', 0.116 * hs, 0.128 * hs, 0.11, drop=lambda x, y, z: z < -0.06),
            M['hair'], head, (0, 0.01, 0.165), subsurf=1)
        add(n + '_hairback', capsule(n + '_hb', 0.11, 0.07, 0.3, sx=1.05, sy=0.55), M['hair'], head,
            (0, 0.06, 0.16), rot=(-0.12, 0, 0), subsurf=1)
        for s in (1, -1):
            add(n + '_lock' + str(s), capsule(n + '_lk', 0.035, 0.022, 0.2, sy=0.6), M['hair'], head,
                (s * 0.095, -0.02, 0.15), rot=(0, s * 0.12, 0), subsurf=1)
        add(n + '_fringe', ellipsoid(n + '_fr', 0.075, 0.03, 0.03), M['hair'], head, (0.03, -0.092, 0.222),
            rot=(0.35, 0, -0.35), subsurf=1)
        c.ponytail = empty(n + '_ptpiv', head, (0, 0.13, 0.2))
        add(n + '_ponytail', capsule(n + '_pt', 0.05, 0.02, 0.33), M['hair'], c.ponytail, rot=(0.35, 0, 0),
            subsurf=1)
    elif style == 'short':
        add(n + '_haircap', ellipsoid(n + '_hc', 0.111 * hs, 0.124 * hs, 0.095, drop=lambda x, y, z: z < -0.05),
            M['hair'], head, (0, 0.014, 0.172), subsurf=1)
    if cfg.get('hat') == 'hardhat':
        add(n + '_hat', ellipsoid(n + '_hat', 0.125, 0.135, 0.1, drop=lambda x, y, z: z < -0.005), M['hat'], head,
            (0, 0.0, 0.2), subsurf=1)
        add(n + '_brim', ellipsoid(n + '_brim', 0.14, 0.16, 0.012), M['hat'], head, (0, -0.01, 0.2), subsurf=1)
        add(n + '_ridge', ellipsoid(n + '_ridge', 0.025, 0.13, 0.03), M['hat'], head, (0, 0, 0.28), subsurf=1)
    if cfg.get('hood'):
        hood = add(n + '_hood', ellipsoid(n + '_hood', 0.155, 0.165, 0.19, segs=28, rings=18,
                                          drop=lambda x, y, z: y < -0.07 and z < 0.13),
                   M['cloak'], head, (0, 0.015, 0.12), subsurf=1)
        so = hood.modifiers.new('solid', 'SOLIDIFY')
        so.thickness = 0.012
        hood.modifiers.move(len(hood.modifiers) - 1, 0)


def _cape(c, n, spine, m, w):
    cols, rows = 10, 16
    verts, faces = [], []
    for j in range(rows + 1):
        t = j / rows
        half = (0.2 + 0.32 * t) * w
        for i in range(cols + 1):
            u = i / cols - 0.5
            verts.append((u * 2 * half, 0.155 + 0.16 * t + 0.05 * math.cos(u * PI) * (1 - t * 0.5), -1.22 * t))
    for j in range(rows):
        for i in range(cols):
            a = j * (cols + 1) + i
            faces.append((a, a + 1, a + cols + 2, a + cols + 1))
    me = bpy.data.meshes.new(n + '_cape')
    me.from_pydata(verts, [], faces)
    _finish(me)
    o = add(n + '_cape', me, m, spine, (0, 0, 0.56))
    vg = o.vertex_groups.new(name='flutter')
    for j in range(rows + 1):
        vg.add([j * (cols + 1) + i for i in range(cols + 1)], (j / rows) ** 1.3, 'REPLACE')
    wv = o.modifiers.new('wave', 'WAVE')
    wv.use_normal = True
    wv.height, wv.width, wv.narrowness, wv.speed = 0.06, 0.45, 1.2, -0.04
    wv.vertex_group = 'flutter'
    sol = o.modifiers.new('solid', 'SOLIDIFY')
    sol.thickness = 0.012
    ss = o.modifiers.new('ss', 'SUBSURF')
    ss.levels, ss.render_levels = 1, 2
    c.cape = o


def _cloak(c, n, spine, m):
    prof = [(0.62, 0.075), (0.57, 0.22), (0.5, 0.32), (0.4, 0.33), (0.1, 0.26), (-0.3, 0.3), (-0.7, 0.4), (-1.02, 0.5)]
    o = add(n + '_cloak', revolve(n + '_cloak', prof, 32, 1.0, 0.82), m, spine, (0, 0.02, 0))
    for p in o.data.polygons:
        p.use_smooth = True
    vg = o.vertex_groups.new(name='flutter')
    for v in o.data.vertices:
        vg.add([v.index], max(0.0, min(1.0, (0.1 - v.co.z) / 1.1)), 'REPLACE')
    wv = o.modifiers.new('wave', 'WAVE')
    wv.use_normal = True
    wv.height, wv.width, wv.narrowness, wv.speed = 0.035, 0.35, 1.5, -0.03
    wv.vertex_group = 'flutter'
    sol = o.modifiers.new('solid', 'SOLIDIFY')
    sol.thickness = 0.015
    ss = o.modifiers.new('ss', 'SUBSURF')
    ss.levels, ss.render_levels = 1, 2
    c.cloak = o


# --------------------------------------------------------------------------- poses

JOINTS = ['spine', 'neck', 'head'] + [j + s for s in 'LR' for j in
                                      ('shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle')]


def rest_pose():
    p = {j: (0.0, 0.0, 0.0) for j in JOINTS}
    p.update(arm('L', 0.05, 0.12, el=0.18), **arm('R', 0.05, 0.12, el=0.18))
    p['curlL'] = p['curlR'] = 0.35
    p['spreadL'] = p['spreadR'] = 0.05
    p['thumbL'] = p['thumbR'] = 0.2
    p['root_loc'] = (0, 0, 0)
    p['root_rot'] = (0, 0, 0)
    return p


def _s(S):
    return 1 if S == 'L' else -1


def arm(S, fwd=0.0, out=0.0, el=0.0, twist=0.0, wrist=(0, 0, 0), el_side=0.0):
    s = _s(S)
    return {'shoulder' + S: (-fwd, -s * out, s * twist), 'elbow' + S: (-el, -s * el_side, 0), 'wrist' + S: wrist}


def leg(S, fwd=0.0, out=0.0, knee=0.0, ankle=0.0):
    s = _s(S)
    return {'hip' + S: (-fwd, -s * out, 0), 'knee' + S: (knee, 0, 0), 'ankle' + S: (ankle, 0, 0)}


def pose(base=None, **kw):
    p = dict(base or rest_pose())
    for k, v in kw.items():
        if isinstance(v, dict):
            p.update(v)
        else:
            p[k] = v
    return p


def merge(*dicts):
    out = {}
    for d in dicts:
        out.update(d)
    return out


def apply_pose(c, frame, p):
    for j in JOINTS:
        if j in p:
            c.p[j].rotation_euler = p[j]
            if frame is not None:
                c.p[j].keyframe_insert('rotation_euler', frame=frame)
    c.root.location = Vector((0, 0, c.hip_h)) + Vector(p.get('root_loc', (0, 0, 0)))
    c.root.rotation_euler = p.get('root_rot', (0, 0, 0))
    if frame is not None:
        c.root.keyframe_insert('location', frame=frame)
        c.root.keyframe_insert('rotation_euler', frame=frame)
    for S in 'LR':
        s = _s(S)
        curl = p.get('curl' + S, 0.35)
        spread = p.get('spread' + S, 0.05)
        for k, (fname, *_r) in enumerate(FINGERS):
            for i, pv in enumerate(c.p[f'{fname}{S}']):
                cv = curl * (1.0 if i == 0 else 1.15) * (1 + 0.08 * k)
                if fname == 'index' and p.get('point' + S):
                    cv = 0.02
                sp = (k - 1.5) * spread if i == 0 else 0
                pv.rotation_euler = (sp, s * cv, 0)
                if frame is not None:
                    pv.keyframe_insert('rotation_euler', frame=frame)
        th = p.get('thumb' + S, 0.2)
        tb, t1 = c.p['thumb' + S]
        tb.rotation_euler = (-0.65 - th * 0.4, s * th * 0.6, s * (0.35 + th * 0.5))
        t1.rotation_euler = (0, s * th * 0.9, 0)
        if frame is not None:
            tb.keyframe_insert('rotation_euler', frame=frame)
            t1.keyframe_insert('rotation_euler', frame=frame)


FIST = dict(curl=1.45, thumb=1.0, spread=0.0)
OPEN = dict(curl=0.05, thumb=0.0, spread=0.18)


def hands(L=None, R=None):
    out = {}
    for S, h in (('L', L), ('R', R)):
        if h:
            out['curl' + S], out['thumb' + S], out['spread' + S] = h['curl'], h['thumb'], h['spread']
    return out


def place(c, frame, loc=None, rot_z=None, rot=None):
    if loc is not None:
        c.ctrl.location = loc
        c.ctrl.keyframe_insert('location', frame=frame)
    if rot_z is not None or rot is not None:
        c.ctrl.rotation_euler = rot if rot is not None else (0, 0, rot_z)
        c.ctrl.keyframe_insert('rotation_euler', frame=frame)


def blink(c, f):
    for e in c.eyes:
        key(e, f - 1, scale=(1, 1, 1))
        key(e, f + 1, scale=(1, 1, 0.08))
        key(e, f + 3, scale=(1, 1, 1))


def brows(c, f, angry=0.0, raise_=0.0):
    hs = 0.95 if c.cfg.get('female') else 1.0
    for s, b in zip((1, -1), c.brows):
        b.location = (s * 0.041 * hs, -0.112 * hs, 0.19 + raise_ * 0.012)
        b.rotation_euler = (0, -s * (0.12 + angry * 0.45 - raise_ * 0.2), 0)
        b.keyframe_insert('location', frame=f)
        b.keyframe_insert('rotation_euler', frame=f)


def lipsync(c, start_frame, env, head_bob=True, max_open=3.6):
    """env: per-frame loudness 0..1 starting at start_frame"""
    m = c.mouth
    key(m, start_frame - 1, scale=(1, 1, 1))
    for i, a in enumerate(env):
        o = min(1.0, a)
        key(m, start_frame + i, scale=(1 - 0.18 * o, 1, 1 + (max_open - 1) * o))
    key(m, start_frame + len(env) + 1, scale=(1, 1, 1))


def look(c, frame, turn=0.0, nod=0.0, tilt=0.0, neck=None):
    c.p['head'].rotation_euler = (nod, tilt, turn)
    c.p['head'].keyframe_insert('rotation_euler', frame=frame)
    if neck is not None:
        c.p['neck'].rotation_euler = neck
        c.p['neck'].keyframe_insert('rotation_euler', frame=frame)


def idle_breath(c, start, end, amp=0.012, period=48):
    """subtle chest/shoulder breathing on spine X"""
    for f in range(start, end + 1, period // 2):
        ph = ((f - start) // (period // 2)) % 2
        r = c.p['spine'].rotation_euler.copy()
        key(c.p['spine'], f, rot=(amp if ph else -amp * 0.3, r[1], r[2]))


# --------------------------------------------------------------------------- effects

def bolt_curve(name, p0, p1, m, seed=0, segs=16, jag=0.18, radius=0.018, branches=2):
    rnd = random.Random(seed)
    v0, v1 = Vector(p0), Vector(p1)
    d = v1 - v0
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = 2

    def spline(a, b, n, j):
        pts = []
        for i in range(n + 1):
            t = i / n
            p = a + (b - a) * t
            if 0 < i < n:
                p += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * j * math.sin(PI * t)
            pts.append(p)
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for q, p in zip(sp.points, pts):
            q.co = (p.x, p.y, p.z, 1)
        return pts

    main = spline(v0, v1, segs, jag)
    for b in range(branches):
        k = rnd.randint(3, segs - 3)
        a = main[k]
        tip = a + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * d.length * 0.25
        spline(a, tip, 6, jag * 0.6)
    o = link(bpy.data.objects.new(name, cu))
    cu.materials.append(m)
    return o


def flicker_bolts(name, p0, p1, m, start, end, n_variants=3, seed=0, **kw):
    """several jagged variants; each visible on alternating frames -> crackling lightning"""
    objs = []
    for v in range(n_variants):
        o = bolt_curve(f'{name}_{v}', p0, p1, m, seed=seed * 31 + v, **kw)
        frames = [f for f in range(start, end + 1) if (f - start) % n_variants == v or
                  ((f - start) % n_variants == (v + 1) % n_variants and v == 0)]
        show(o, frames, start, end)
        objs.append(o)
    return objs


def point_light(name, loc, color, energy, radius=0.1, parent=None):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.color = srgb(color)
    ld.energy = energy
    ld.shadow_soft_size = radius
    o = link(bpy.data.objects.new(name, ld))
    o.location = loc
    o.parent = parent
    return o


def area_light(name, loc, rot, color, energy, size=2.0):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.color = srgb(color)
    ld.energy = energy
    ld.size = size
    o = link(bpy.data.objects.new(name, ld))
    o.location, o.rotation_euler = loc, rot
    return o


def sun(name, rot, color, strength, angle=0.02):
    ld = bpy.data.lights.new(name, 'SUN')
    ld.color = srgb(color)
    ld.energy = strength
    ld.angle = angle
    o = link(bpy.data.objects.new(name, ld))
    o.rotation_euler = rot
    return o


def key_light(o, frame, energy):
    o.data.energy = energy
    o.data.keyframe_insert('energy', frame=frame)


def camera(name, loc, target, lens=35, dof_obj=None, fstop=2.8):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_end = 800
    cd.sensor_width = 36
    c = link(bpy.data.objects.new(name, cd))
    c.location = loc
    t = empty(name + '_tgt', loc=target)
    con = c.constraints.new('TRACK_TO')
    con.target = t
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    if dof_obj is not None:
        cd.dof.use_dof = True
        cd.dof.focus_object = dof_obj
        cd.dof.aperture_fstop = fstop
    return c, t


def cut(cam, frame):
    m = bpy.context.scene.timeline_markers.new(f'{cam.name}_{frame}', frame=frame)
    m.camera = cam
    if frame <= bpy.context.scene.frame_start:
        bpy.context.scene.camera = cam


def shake(cam, start, end, amp=0.05, seed=1):
    rnd = random.Random(seed)
    bpy.context.scene.frame_set(start)
    base = cam.location.copy()
    for f in range(start, end + 1, 2):
        k = 1 - (f - start) / max(1, end - start)
        key(cam, f, loc=base + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * amp * k)
    key(cam, end + 2, loc=base)


def compositor_glow(threshold=1.0, strength=0.6, size=0.5):
    s = bpy.context.scene
    try:
        t = bpy.data.node_groups.new('Comp', 'CompositorNodeTree')
        t.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = t.nodes.new('CompositorNodeRLayers')
        g = t.nodes.new('CompositorNodeGlare')
        out = t.nodes.new('NodeGroupOutput')
        g.inputs['Type'].default_value = 'Bloom'
        g.inputs['Threshold'].default_value = threshold
        g.inputs['Strength'].default_value = strength
        g.inputs['Size'].default_value = size
        t.links.new(rl.outputs['Image'], g.inputs['Image'])
        t.links.new(g.outputs['Image'], out.inputs[0])
        s.compositing_node_group = t
        s.render.use_compositing = True
    except Exception as e:  # bloom is cosmetic
        print('compositor glow skipped:', e)


# --------------------------------------------------------------------------- environment

def window_material(name='windows', lit='#ffcf7a', wall='#141821', scale=1.6, glow_strength=3.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    add_ = nt.nodes.new('ShaderNodeMath')
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.offset = 0.0
    br.inputs['Color1'].default_value = (*srgb(lit), 1)
    br.inputs['Color2'].default_value = (*srgb('#1a1408'), 1)
    br.inputs['Mortar'].default_value = (*srgb(wall), 1)
    br.inputs['Scale'].default_value = scale
    br.inputs['Mortar Size'].default_value = 0.09
    br.inputs['Brick Width'].default_value = 0.55
    br.inputs['Row Height'].default_value = 0.5
    br.inputs['Bias'].default_value = 0.25
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    nt.links.new(sep.outputs['X'], add_.inputs[0])
    nt.links.new(sep.outputs['Y'], add_.inputs[1])
    nt.links.new(add_.outputs[0], comb.inputs['X'])
    nt.links.new(sep.outputs['Z'], comb.inputs['Y'])
    nt.links.new(comb.outputs[0], br.inputs['Vector'])
    inv = nt.nodes.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs['Fac'], inv.inputs[1])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (*srgb(wall), 1)
    mix.inputs['B'].default_value = (0.02, 0.025, 0.03, 1)
    nt.links.new(inv.outputs[0], mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    emit = nt.nodes.new('ShaderNodeMix')
    emit.data_type = 'RGBA'
    emit.inputs['A'].default_value = (0, 0, 0, 1)
    nt.links.new(inv.outputs[0], emit.inputs['Factor'])
    nt.links.new(br.outputs['Color'], emit.inputs['B'])
    nt.links.new(emit.outputs['Result'], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = glow_strength
    b.inputs['Roughness'].default_value = 0.35
    m.cycles.emission_sampling = 'NONE'  # thousands of tiny windows: visible glow only, not light sources
    return m


def skyline(m_win, seed=4, count=70, rmin=22, rmax=110, hmin=-20, hmax=35, ground=-40, exclude=None):
    rnd = random.Random(seed)
    objs = []
    for i in range(count):
        a = rnd.uniform(0, 2 * PI)
        if exclude and exclude(a):
            continue
        r = rnd.uniform(rmin, rmax)
        w_ = rnd.uniform(3, 9)
        d_ = rnd.uniform(3, 9)
        top = rnd.uniform(hmin, hmax) * (0.6 + r / rmax)
        hh = (top - ground) / 2
        o = add(f'bld{i}', box(f'bld{i}', w_, d_, hh), m_win, None,
                (math.cos(a) * r, math.sin(a) * r, ground + hh), rot=(0, 0, rnd.uniform(-0.2, 0.2)))
        objs.append(o)
        if rnd.random() < 0.35:
            add(f'ant{i}', capsule(f'ant{i}', 0.08, 0.05, rnd.uniform(2, 6), up=True, segs=8),
                mat('antenna', '#202226', 0.5, 0.8), None, (o.location.x, o.location.y, top))
            add(f'antl{i}', ellipsoid(f'antl{i}', 0.18, 0.18, 0.18, 10, 6), glow('redlight', '#ff2a2a', 25), None,
                (o.location.x, o.location.y, top + 4))
    return objs


def night_world(top='#04060f', horizon='#2a1d4a', stars=True, strength=1.0):
    w = bpy.data.worlds.new('night')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], ramp.inputs[0])
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*srgb(horizon), 1)
    ramp.color_ramp.elements[1].position = 0.35
    ramp.color_ramp.elements[1].color = (*srgb(top), 1)
    col = ramp.outputs[0]
    if stars:
        vor = nt.nodes.new('ShaderNodeTexVoronoi')
        vor.inputs['Scale'].default_value = 180
        st = nt.nodes.new('ShaderNodeMath')
        st.operation = 'LESS_THAN'
        st.inputs[1].default_value = 0.035
        nt.links.new(tc.outputs['Generated'], vor.inputs['Vector'])
        nt.links.new(vor.outputs['Distance'], st.inputs[0])
        mul = nt.nodes.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        nt.links.new(st.outputs[0], mul.inputs[0])
        nt.links.new(sep.outputs['Z'], mul.inputs[1])
        ad = nt.nodes.new('ShaderNodeMix')
        ad.data_type = 'RGBA'
        ad.blend_type = 'ADD'
        nt.links.new(mul.outputs[0], ad.inputs['Factor'])
        nt.links.new(col, ad.inputs['A'])
        ad.inputs['B'].default_value = (1.5, 1.5, 1.7, 1)
        col = ad.outputs['Result']
    nt.links.new(col, bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    return w


def sky_world(top='#3d7fd8', horizon='#f2b27a', strength=1.0, name='sky'):
    w = night_world(top, horizon, stars=False, strength=strength)
    w.name = name
    return w


def load_lipsync(ep_dir):
    p = os.path.join(ep_dir, 'lipsync.json')
    with open(p) as f:
        return json.load(f)


def walk(c, start, end, base=None, period=24, stride=0.38, arm_swing=0.35):
    """keyframe a walk cycle on the joints between start and end (ctrl travel is keyed separately)"""
    base = base or rest_pose()
    for f in range(start, end + 1, period // 4):
        ph = ((f - start) / period) * 2 * PI
        sL, sR = math.sin(ph), math.sin(ph + PI)
        p = pose(base,
                 **leg('L', stride * sL, 0.03, knee=0.15 + 0.55 * max(0.0, math.cos(ph)), ankle=-0.1 * sL),
                 **leg('R', stride * sR, 0.03, knee=0.15 + 0.55 * max(0.0, math.cos(ph + PI)), ankle=-0.1 * sR),
                 **arm('L', arm_swing * sR, 0.12, el=0.3), **arm('R', arm_swing * sL, 0.12, el=0.3),
                 root_loc=(0, 0, -0.02 - 0.025 * abs(math.cos(ph))))
        apply_pose(c, f, p)


def child_of(o, target, frames_on_off):
    """Child Of constraint without scale; frames_on_off = [(frame, influence), ...]"""
    con = o.constraints.new('CHILD_OF')
    con.target = target
    con.use_scale_x = con.use_scale_y = con.use_scale_z = False
    con.set_inverse_pending = False
    con.inverse_matrix.identity()
    for f, v in frames_on_off:
        con.influence = v
        con.keyframe_insert('influence', frame=f)
    return con


def sunset_world(top='#1b2b6b', mid='#c0507a', horizon='#ffb35c', strength=1.0):
    w = bpy.data.worlds.new('sunset')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], ramp.inputs[0])
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.0, (*srgb(horizon), 1)
    cr.elements[1].position, cr.elements[1].color = 0.45, (*srgb(top), 1)
    e = cr.elements.new(0.12)
    e.color = (*srgb(mid), 1)
    nt.links.new(ramp.outputs[0], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    return w
