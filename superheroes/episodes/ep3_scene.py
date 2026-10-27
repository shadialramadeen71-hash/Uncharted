"""Episode 3 - VOLT & NOVA: Iron Titan. Daylight downtown street."""
import math, random
from heroes import *
import cast
import ep3_story as story

F = lambda t: int(round(t * FPS)) + 1
TY = 14.0  # where the Titan stops


class Titan:
    pass


def build_titan(loc):
    t = Titan()
    gun = mat('gunmetal', '#4b5059', 0.35, 0.85)
    dark = mat('titandark', '#24272c', 0.5, 0.7)
    haz = mat('hazard', '#f2b705', 0.4, 0.2)
    t.eye_m = mat('titaneye', '#ff1a1a', 0.2, emit='#ff2020', estr=12)
    t.core_m = mat('titancore', '#ff3b1a', 0.2, emit='#ff4020', estr=10)
    t.ctrl = empty('titan_ctrl', None, loc)
    t.hips = empty('titan_hips', t.ctrl, (0, 0, 2.5))
    add('t_pelvis', box('t_pelvis', 0.75, 0.5, 0.3), dark, t.hips, (0, 0, 0), bevel=0.08)
    t.torso = empty('titan_torso', t.hips, (0, 0, 0.3))
    add('t_waist', capsule('t_waist', 0.38, 0.45, 0.5, up=True, segs=16), dark, t.torso)
    add('t_chest', box('t_chest', 1.05, 0.65, 0.7), gun, t.torso, (0, 0, 1.25), bevel=0.15)
    add('t_chestplate', box('t_cp', 0.7, 0.05, 0.45), dark, t.torso, (0, -0.66, 1.3), bevel=0.05)
    add('t_core', ellipsoid('t_core', 0.22, 0.08, 0.22, 24, 12), t.core_m, t.torso, (0, -0.7, 1.3))
    add('t_corering', ellipsoid('t_cr', 0.3, 0.06, 0.3, 24, 8), haz, t.torso, (0, -0.66, 1.3), subsurf=1)
    for s in (1, -1):
        for k in range(3):
            add(f't_stripe{s}{k}', box('t_st', 0.06, 0.02, 0.25), haz, t.torso, (s * (0.45 + k * 0.17), -0.66, 1.6),
                rot=(0, s * 0.6, 0))
        add(f't_vent{s}', box('t_vent', 0.18, 0.18, 0.25), dark, t.torso, (s * 0.6, 0.4, 2.05), bevel=0.04)
        add(f't_exh{s}', capsule('t_exh', 0.08, 0.08, 0.35, up=True, segs=12), dark, t.torso, (s * 0.6, 0.45, 2.2))
    t.neck = empty('titan_neck', t.torso, (0, 0, 1.95))
    add('t_neckm', capsule('t_neck', 0.2, 0.22, 0.2, up=True, segs=16), dark, t.neck)
    t.head = empty('titan_head', t.neck, (0, 0, 0.25))
    add('t_head', box('t_head', 0.42, 0.42, 0.34), gun, t.head, (0, 0, 0.3), bevel=0.12)
    add('t_visor', box('t_visor', 0.33, 0.04, 0.07), t.eye_m, t.head, (0, -0.41, 0.36), bevel=0.03)
    add('t_jaw', box('t_jaw', 0.3, 0.1, 0.1), dark, t.head, (0, -0.36, 0.1), bevel=0.04)
    add('t_antenna', capsule('t_ant', 0.025, 0.02, 0.5, up=True, segs=8), dark, t.head, (0.25, 0.1, 0.6))
    add('t_antlight', ellipsoid('t_al', 0.05, 0.05, 0.05, 10, 6), t.eye_m, t.head, (0.25, 0.1, 1.12))
    t.p = {}
    for s, S in ((1, 'L'), (-1, 'R')):
        sh = empty(f'titan_sh{S}', t.torso, (s * 1.25, 0, 1.6))
        sh.rotation_mode = 'ZXY'
        add(f't_shpad{S}', ellipsoid('t_shp', 0.42, 0.42, 0.36, 20, 10), gun, sh, (s * 0.05, 0, 0.1), subsurf=1)
        add(f't_shstripe{S}', ellipsoid('t_shs', 0.43, 0.2, 0.3, 20, 8), haz, sh, (s * 0.05, 0, 0.1), subsurf=1)
        add(f't_uarm{S}', capsule('t_ua', 0.2, 0.17, 1.0, segs=16), dark, sh)
        el = empty(f'titan_el{S}', sh, (0, 0, -1.05))
        add(f't_elb{S}', ellipsoid('t_elb', 0.22, 0.22, 0.22, 16, 8), gun, el)
        add(f't_farm{S}', capsule('t_fa', 0.24, 0.2, 0.95, segs=16), gun, el)
        wr = empty(f'titan_wr{S}', el, (0, 0, -1.05))
        add(f't_hand{S}', box('t_hand', 0.17, 0.2, 0.15), dark, wr, (0, 0, -0.1), bevel=0.05)
        claws = []
        for k, y in enumerate((-0.13, 0.0, 0.13)):
            c = empty(f'titan_claw{S}{k}', wr, (-s * 0.0, y, -0.22))
            add(f't_claw{S}{k}', capsule('t_claw', 0.05, 0.03, 0.28, segs=10), gun, c)
            claws.append(c)
        hp = empty(f'titan_hip{S}', t.hips, (s * 0.5, 0, -0.1))
        add(f't_thigh{S}', capsule('t_th', 0.32, 0.26, 1.0, segs=16), dark, hp)
        kn = empty(f'titan_knee{S}', hp, (0, 0, -1.1))
        add(f't_kneecap{S}', ellipsoid('t_kc', 0.3, 0.3, 0.3, 16, 8), haz, kn, (0, -0.06, 0))
        add(f't_shin{S}', capsule('t_sh', 0.3, 0.36, 1.0, segs=16), gun, kn)
        an = empty(f'titan_an{S}', kn, (0, 0, -1.15))
        add(f't_foot{S}', box('t_foot', 0.4, 0.62, 0.17), dark, an, (0, -0.15, -0.12), bevel=0.08)
        t.p.update({'sh' + S: sh, 'el' + S: el, 'wr' + S: wr, 'hip' + S: hp, 'knee' + S: kn, 'an' + S: an,
                    'claws' + S: claws})
    return t


def tpose(t, f, **kw):
    """keyframe titan joints: name=(x, y, z)"""
    m = {'torso': t.torso, 'head': t.head, 'hips': t.hips, 'neck': t.neck}
    m.update({k: v for k, v in t.p.items() if not k.startswith('claws')})
    for k, v in kw.items():
        if k == 'hips_loc':
            key(t.hips, f, loc=v)
        elif k.startswith('claws'):
            for c in t.p[k]:
                key(c, f, rot=(0, v, 0))
        else:
            key(m[k], f, rot=v)


def tstand(t, f, **kw):
    base = dict(torso=(0, 0, 0), head=(0, 0, 0), hips=(0, 0, 0), neck=(0, 0, 0),
                shL=(0, -0.25, 0), shR=(0, 0.25, 0), elL=(-0.5, 0, 0), elR=(-0.5, 0, 0), wrL=(0, 0, 0), wrR=(0, 0, 0),
                hipL=(0, -0.05, 0), hipR=(0, 0.05, 0), kneeL=(0.05, 0, 0), kneeR=(0.05, 0, 0), anL=(0, 0, 0),
                anR=(0, 0, 0), hips_loc=(0, 0, 2.5))
    base.update(kw)
    tpose(t, f, **base)


def build(lips):
    end = F(story.DURATION) - 1
    s = bpy.context.scene
    s.frame_start, s.frame_end = 1, end
    rnd = random.Random(9)

    # ------------------------------------------------------------ world: daylight street
    sky_world('#3f83e0', '#cfe3f5', strength=1.6)
    sun('sun', (math.radians(32), 0, math.radians(75)), '#fff1dc', 5.0, 0.02)
    area_light('street_fill', (0, -2, 9), (0, 0, 0), '#fff4e6', 1500, 8)
    asphalt = mat('asphalt', '#2c2d30', 0.85)
    add('road', box('road', 7, 120, 0.05), asphalt, None, (0, 40, -0.05))
    walk_m = mat('sidewalk', '#9a968e', 0.8)
    for sx in (1, -1):
        add(f'sidewalk{sx}', box('sw', 3, 120, 0.1), walk_m, None, (sx * 10, 40, 0.0))
        add(f'curb{sx}', box('curb', 0.15, 120, 0.12), mat('curb', '#bdb8ad', 0.7), None, (sx * 7.05, 40, 0.02))
    line_m = mat('paint', '#f0f0e8', 0.6)
    for y in range(-20, 100, 6):
        add(f'dash{y}', box('dash', 0.1, 1.4, 0.01), line_m, None, (0, y, 0.005))
    win = window_material('windows_day', lit='#9fc3e6', wall='#c4b49a', scale=1.4, glow_strength=0.25)
    win2 = window_material('windows_day2', lit='#87a9cc', wall='#8d9aa6', scale=1.8, glow_strength=0.2)
    y = -30
    while y < 110:
        for sx in (1, -1):
            w_ = rnd.uniform(4, 7)
            h_ = rnd.uniform(14, 45)
            d_ = rnd.uniform(6, 10)
            add(f'b{sx}{y}', box('b', d_ / 2, w_ / 2, h_ / 2), win if rnd.random() < 0.5 else win2, None,
                (sx * (13 + d_ / 2), y + w_ / 2, h_ / 2))
        y += rnd.uniform(5, 8)
    lampm = mat('lamp', '#3a3d42', 0.4, 0.8)
    for y in range(-10, 90, 14):
        for sx in (1, -1):
            add(f'lamp{sx}{y}', capsule('lp', 0.08, 0.08, 5.5, up=True, segs=10), lampm, None, (sx * 7.6, y, 0))
            add(f'lamparm{sx}{y}', box('la', 0.7, 0.06, 0.06), lampm, None, (sx * 7.0, y, 5.5))
            add(f'lamphead{sx}{y}', box('lh', 0.3, 0.15, 0.06), mat('lh', '#ddeeff', 0.2), None, (sx * 6.4, y, 5.45))
    # parked cars
    for i, (x, y_, col) in enumerate(((-5.5, -4, '#c0392b'), (5.4, 6, '#2e86c1'), (-5.5, 22, '#f4d03f'),
                                      (5.6, 30, '#ecf0f1'))):
        cm = mat(f'car{i}', col, 0.25, 0.4, coat=1.0)
        add(f'carbody{i}', box('cb', 0.9, 2.1, 0.38), cm, None, (x, y_, 0.62), bevel=0.25)
        add(f'cartop{i}', box('ct', 0.8, 1.1, 0.3), mat('glass', '#1a2633', 0.05, 0.5), None, (x, y_ + 0.2, 1.15),
            bevel=0.2)
        for dx in (-0.85, 0.85):
            for dy in (-1.3, 1.3):
                add(f'wheel{i}{dx}{dy}', ellipsoid('wh', 0.12, 0.36, 0.36, 16, 8), mat('tire', '#111111', 0.9),
                    None, (x + dx, y_ + dy, 0.36), rot=(0, 0, math.pi / 2))

    # ------------------------------------------------------------ characters
    volt = build_character(cast.volt(), (-0.9, 0, 0), facing=math.pi)
    nova = build_character(cast.nova(), (0.9, 0, 0), facing=math.pi)
    titan = build_titan((0, 30, 0))
    who = {'VOLT': volt, 'NOVA': nova}
    for L in lips:
        if L['speaker'] == 'TITAN':  # no mouth: the visor pulses with the voice
            for i, a in enumerate(L['env']):
                key_emission(titan.eye_m, L['start_frame'] + i, 8 + 40 * a)
            key_emission(titan.eye_m, L['start_frame'] + len(L['env']) + 1, 12)
            continue
        c = who[L['speaker']]
        lipsync(c, L['start_frame'], L['env'])

    # ------------------------------------------------------------ TITAN
    steps = [6, 35, 63, 92]  # stomp frames (match SFX)
    y0 = 30.0
    tstand(titan, 1)
    key(titan.ctrl, 1, loc=(0, y0, 0))
    for i, f in enumerate(steps):
        S = 'L' if i % 2 == 0 else 'R'
        O = 'R' if S == 'L' else 'L'
        mid = f - 14
        y_ = y0 - (i + 1) * (y0 - TY) / len(steps)
        tstand(titan, mid, **{'hip' + S: (-0.55, 0, 0), 'knee' + S: (0.9, 0, 0), 'hip' + O: (0.25, 0, 0),
                              'torso': (0.05, 0, 0.08 if S == 'L' else -0.08), 'hips_loc': (0, 0, 2.45),
                              'sh' + S: (0.3, 0, 0), 'sh' + O: (-0.3, 0, 0)})
        tstand(titan, f, **{'hip' + S: (-0.2, 0, 0), 'hip' + O: (0.2, 0, 0), 'knee' + O: (0.25, 0, 0),
                            'torso': (0.03, 0, 0), 'hips_loc': (0, 0, 2.38)})
        key(titan.ctrl, f, loc=(0, y_, 0))
    # point at the heroes while talking
    tstand(titan, 104, shR=(-1.3, 0.1, 0.2), elR=(-0.2, 0, 0), head=(0.15, 0, 0))
    tstand(titan, 214, shR=(-1.3, 0.1, 0.2), elR=(-0.2, 0, 0), head=(0.15, 0, 0))
    tstand(titan, 230, shR=(-0.6, 0.3, 0), shL=(-0.6, -0.3, 0), elL=(-1.2, 0, 0), elR=(-1.2, 0, 0))
    # zapped: shaking + glitching eyes and core
    for i, f in enumerate(range(234, 282, 3)):
        tstand(titan, f, torso=(rnd.uniform(-0.15, 0.1), rnd.uniform(-0.1, 0.1), rnd.uniform(-0.15, 0.15)),
               head=(rnd.uniform(-0.4, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(-0.4, 0.4)),
               shL=(rnd.uniform(-1.8, 0), -0.6, 0), shR=(rnd.uniform(-1.8, 0), 0.6, 0),
               elL=(-rnd.uniform(0, 1.5), 0, 0), elR=(-rnd.uniform(0, 1.5), 0, 0))
        key_emission(titan.eye_m, f, rnd.choice((0.0, 3.0, 40.0)))
        key_emission(titan.core_m, f, rnd.choice((0.5, 30.0, 4.0)))
    key_emission(titan.core_m, 284, 0.3)
    key_emission(titan.eye_m, 284, 6)
    # the punch (f286) and the fall
    tstand(titan, 286, torso=(0.05, 0, 0), head=(0, 0, 0), shL=(-0.6, -0.4, 0), shR=(-0.6, 0.4, 0))
    tstand(titan, 291, torso=(-0.35, 0, 0.1), head=(-0.7, 0, 0.3), shL=(-2.2, -0.8, 0), shR=(-2.0, 0.9, 0),
           elL=(-0.3, 0, 0), elR=(-0.3, 0, 0))
    key(titan.ctrl, 288, rot=(0, 0, 0))
    key(titan.ctrl, 296, rot=(-0.15, 0, 0.05))
    key(titan.ctrl, 318, rot=(-math.pi / 2, 0, 0.12))
    key(titan.ctrl, 322, rot=(-math.pi / 2 + 0.1, 0, 0.12))
    key(titan.ctrl, 328, rot=(-math.pi / 2, 0, 0.12))
    tstand(titan, 318, torso=(-0.2, 0, 0.1), head=(-0.4, 0, 0.6), shL=(-2.6, -1.0, 0), shR=(-2.6, 1.0, 0),
           elL=(-0.2, 0, 0), elR=(-0.2, 0, 0), kneeL=(0.4, 0, 0))
    key_emission(titan.eye_m, 318, 6)
    key_emission(titan.eye_m, 340, 0)
    for k in titan.ctrl.animation_data.action.layers[0].strips[0].channelbag(
            titan.ctrl.animation_data.action_slot).fcurves:
        if k.data_path == 'rotation_euler':
            for kp in k.keyframe_points:
                if kp.co[0] == 318:
                    kp.interpolation = 'LINEAR'
            for kp in k.keyframe_points:
                if kp.co[0] == 296:
                    kp.interpolation = 'BEZIER'
                    kp.easing = 'EASE_IN'


    # ------------------------------------------------------------ heroes
    ready_v = pose(**arm('R', 0.2, 0.3, el=0.6), **arm('L', 0.2, 0.3, el=0.6), **hands(FIST, FIST),
                   **leg('L', 0.15, 0.12, knee=0.25), **leg('R', -0.1, 0.12, knee=0.1), root_loc=(0, 0, -0.03))
    ready_n = pose(**arm('R', 0.3, 0.25, el=1.8), **arm('L', 0.1, 0.2, el=0.3), **hands(FIST, FIST),
                   **leg('L', 0.0, 0.12), **leg('R', 0.1, 0.12, knee=0.15))
    look_up = dict(head=(-0.35, 0, 0))
    apply_pose(volt, 1, pose(ready_v, **look_up))
    apply_pose(nova, 1, pose(ready_n, **look_up))
    brows(volt, 1, angry=0.6)
    brows(nova, 1, angry=0.6)
    # Volt turns to Nova and points at the Titan
    apply_pose(volt, 112, pose(ready_v, head=(-0.2, 0, 0.6)))
    apply_pose(volt, 122, pose(ready_v, **arm('R', 1.7, 0.1, el=0.05), pointR=True, curlR=1.45, thumbR=1.0,
                               head=(-0.25, 0, 0.5)))
    apply_pose(volt, 160, pose(ready_v, **arm('R', 1.7, 0.1, el=0.05), pointR=True, curlR=1.45, thumbR=1.0,
                               head=(-0.3, 0, 0.0)))
    apply_pose(volt, 172, pose(ready_v, head=(-0.25, 0, -0.1)))
    # Nova: fist into palm
    apply_pose(nova, 166, pose(ready_n, head=(-0.15, 0, -0.5)))
    apply_pose(nova, 176, pose(ready_n, **arm('R', 1.1, 0.0, el=1.6, twist=-0.4), **arm('L', 1.05, 0.0, el=1.55, twist=1.2),
                               **hands(OPEN, FIST), head=(-0.1, 0, -0.4), spine=(0.08, 0, 0)))
    apply_pose(nova, 184, pose(ready_n, **arm('R', 1.0, -0.05, el=1.75, twist=-0.4), **arm('L', 1.05, 0.0, el=1.55, twist=1.2),
                               **hands(OPEN, FIST), head=(-0.1, 0, -0.3), spine=(0.08, 0, 0)))
    apply_pose(nova, 212, pose(ready_n, head=(-0.35, 0, 0)))
    # Volt charges and fires
    charge = pose(ready_v, **arm('R', 0.35, 0.6, el=1.3), **arm('L', 0.35, 0.6, el=1.3),
                  **leg('L', 0.3, 0.22, knee=0.6, ankle=-0.3), **leg('R', 0.3, 0.22, knee=0.6, ankle=-0.3),
                  root_loc=(0, 0, -0.09), spine=(0.12, 0, 0), head=(-0.15, 0, 0))
    cast_ = pose(ready_v, **arm('R', 1.75, 0.05, el=0.05, twist=1.5), **arm('L', 1.75, 0.05, el=0.05, twist=1.5),
                 **hands(OPEN, OPEN), **leg('L', 0.35, 0.05, knee=0.3, ankle=-0.1), **leg('R', -0.35, 0.05, knee=0.1),
                 spine=(-0.05, 0, 0), head=(-0.3, 0, 0), root_loc=(0, 0, -0.04))
    apply_pose(volt, 214, ready_v)
    apply_pose(volt, 224, charge)
    apply_pose(volt, 229, charge)
    apply_pose(volt, 233, cast_)
    apply_pose(volt, 276, cast_)
    apply_pose(volt, 290, pose(ready_v, head=(-0.3, 0, 0)))
    iris = volt.cfg['mats']['iris']
    for f, e in ((214, 0.6), (228, 25), (276, 25), (290, 0.6)):
        key_emission(iris, f, e)
    emb = volt.cfg['mats']['emblem']
    for f, e in ((214, 3), (230, 25), (276, 25), (292, 3)):
        key_emission(emb, f, e)
    # Nova's flying punch
    fly = pose(**arm('R', 3.05, 0.1, el=0.0), **arm('L', 0.25, 0.15, el=0.2), **hands(FIST, FIST),
               **leg('L', 0.05, 0.02, knee=0.15), **leg('R', -0.1, 0.02, knee=0.4, ankle=0.4),
               root_rot=(1.3, 0, 0), head=(-1.0, 0, 0))
    hover = pose(**arm('R', 0.6, 0.4, el=1.2), **arm('L', 0.5, 0.4, el=1.0), **hands(FIST, FIST),
                 **leg('L', 0.1, 0.05, knee=0.4), **leg('R', -0.1, 0.05, knee=0.7, ankle=0.4), root_rot=(0.15, 0, 0))
    land = pose(ready_n, **leg('L', 0.4, 0.1, knee=0.9, ankle=-0.4), **leg('R', 0.4, 0.1, knee=0.9, ankle=-0.4),
                root_loc=(0, 0, -0.2))
    place(nova, 262, loc=(0.9, 0, 0), rot_z=math.pi)
    apply_pose(nova, 262, pose(ready_n, root_loc=(0, 0, -0.12), **leg('L', 0.3, 0.1, knee=0.7, ankle=-0.3),
                               **leg('R', 0.3, 0.1, knee=0.7, ankle=-0.3), head=(-0.4, 0, 0)))
    apply_pose(nova, 270, fly)
    place(nova, 270, loc=(0.9, 1.0, 0.8))
    place(nova, 286, loc=(0.15, TY - 2.6, 3.3), rot_z=math.pi)
    apply_pose(nova, 286, fly)
    place(nova, 292, loc=(0.4, TY - 4.0, 4.2))
    apply_pose(nova, 296, hover)
    place(nova, 312, loc=(0.6, TY - 6.0, 4.0))
    apply_pose(nova, 318, hover)
    place(nova, 338, loc=(0.9, 0.6, 0.0), rot_z=math.pi)
    apply_pose(nova, 330, pose(hover, root_rot=(-0.1, 0, 0)))
    apply_pose(nova, 340, land)
    apply_pose(nova, 350, ready_n)
    brows(nova, 330, angry=0.0, raise_=0.4)
    brows(volt, 330, angry=0.0, raise_=0.3)
    # face each other, banter, high five
    place(nova, 352, loc=(0.9, 0.6, 0.0), rot_z=math.pi)
    place(nova, 362, loc=(0.8, 0.4, 0.0), rot_z=-0.95)
    place(volt, 352, rot_z=math.pi)
    place(volt, 362, loc=(-0.8, 0.2, 0.0), rot_z=0.95)
    relax_n = pose(**arm('R', 0.1, 0.4, el=1.9, twist=0.9), **arm('L', 0.1, 0.4, el=1.9, twist=0.9),
                   **hands(FIST, FIST), head=(0.0, 0.08, 0.15))
    relax_v = pose(**arm('L', 0.1, 0.18, el=0.3), **arm('R', 0.1, 0.18, el=0.3), head=(0.0, -0.05, -0.15))
    apply_pose(nova, 364, relax_n)
    apply_pose(volt, 364, relax_v)
    apply_pose(nova, 392, relax_n)
    apply_pose(volt, 396, pose(relax_v, **arm('R', 0.4, 0.3, el=1.8, twist=-1.0), **hands(None, OPEN),
                               head=(0.1, 0, -0.1)))
    apply_pose(volt, 426, pose(relax_v, head=(0.05, 0, -0.15)))
    # turn to face each other, step in, high five (Volt's right hand meets Nova's left, camera side)
    place(volt, 426, loc=(-0.8, 0.2, 0.0), rot_z=0.95)
    place(nova, 426, loc=(0.8, 0.4, 0.0), rot_z=-0.95)
    place(volt, 436, loc=(-0.5, 0.3, 0.0), rot_z=math.pi / 2)
    place(nova, 436, loc=(0.5, 0.3, 0.0), rot_z=-math.pi / 2)
    hi_v = pose(relax_v, **arm('R', 2.15, -0.05, el=0.2), **hands(None, OPEN), head=(-0.2, 0, 0))
    hi_n = pose(relax_n, **arm('L', 2.15, -0.05, el=0.2), **arm('R', 0.1, 0.2, el=0.3), **hands(OPEN, FIST),
                head=(-0.2, 0, 0))
    apply_pose(volt, 432, pose(hi_v, **arm('R', 2.3, 0.1, el=1.2)))
    apply_pose(nova, 432, pose(hi_n, **arm('L', 2.3, 0.1, el=1.2)))
    apply_pose(volt, 440, hi_v)
    apply_pose(nova, 440, hi_n)
    apply_pose(volt, 450, pose(hi_v, **arm('R', 2.0, 0.0, el=0.5), head=(-0.05, 0, -0.5)))
    apply_pose(nova, 450, pose(hi_n, **arm('L', 2.0, 0.0, el=0.5), head=(-0.05, 0, 0.5)))
    for f in (50, 150, 300, 372, 410):
        blink(volt, f)
    for f in (70, 200, 345, 380, 420):
        blink(nova, f)

    # ------------------------------------------------------------ effects
    bolt_m = glow('bolt3', '#a8e2ff', 40)
    core_target = Vector((0, TY - 0.7, 4.1))
    for S in 'LR':
        ph = world_pos(volt.p['wrist' + S], 236) + Vector((0, 0.1, 0))
        flicker_bolts('zap' + S, ph, core_target, bolt_m, 233, 276, n_variants=3, seed=3 if S == 'L' else 4,
                      segs=24, jag=0.55, radius=0.03, branches=4)
    zl = point_light('zaplight', core_target + Vector((0, -1.5, 0)), '#9fdcff', 0, 0.5)
    for f, e in ((232, 0), (233, 6000), (240, 3000), (250, 7000), (260, 3500), (270, 6500), (277, 0)):
        key_light(zl, f, e)
    spark_m = glow('spark3', '#ffe3a0', 30)
    for k in range(5):
        p = core_target + Vector((rnd.uniform(-1.2, 1.2), 0.2, rnd.uniform(-1.2, 1.5)))
        flicker_bolts(f'tsp{k}', p, p + Vector((rnd.uniform(-0.6, 0.6), 0, rnd.uniform(-0.6, 0.6))), spark_m,
                      240 + k * 3, 283, n_variants=2, seed=40 + k, segs=6, jag=0.15, radius=0.012, branches=1)
    impact_m = glow('impact', '#ffd0ff', 10)
    burst = add('punchburst', ellipsoid('pb', 1, 1, 1, 20, 10), impact_m, None, (0.15, TY - 0.6, 4.9))
    key(burst, 285, scale=0.001)
    key(burst, 287, scale=0.7)
    key(burst, 292, scale=0.001)
    trail_m = glow('trail3', '#c06bff', 3)
    trail = add('trail3', capsule('trail3', 0.14, 0.01, 1.0, segs=16), trail_m, nova.root, (0, 0, -0.2))
    for f, sc in ((1, 0), (268, 0), (275, 3.0), (286, 3.0), (290, 0)):
        key(trail, f, scale=(1, 1, sc) if sc else 0.001)

    # ------------------------------------------------------------ cameras
    camA, tA = camera('camA', (0.6, -4.2, 0.55), (0, 22, 4.2), 26)
    key(camA, 1, loc=(0.6, -4.2, 0.55))
    key(camA, 112, loc=(0.4, -3.2, 0.6))
    key(tA, 1, loc=(0, 25, 4.6))
    key(tA, 112, loc=(0, 16, 4.0))
    shake(camA, 6, 14, 0.04, 1)
    shake(camA, 35, 43, 0.04, 2)
    shake(camA, 63, 71, 0.05, 3)
    shake(camA, 92, 100, 0.06, 4)
    camB, tB = camera('camB', (0.2, 4.6, 1.55), (0, 0, 1.45), 35)
    key(camB, 113, loc=(0.2, 4.6, 1.55))
    key(camB, 215, loc=(0.1, 3.9, 1.5))
    camC, tC = camera('camC', (-6.0, -1.8, 1.9), (0, 7.5, 2.6), 24)
    key(camC, 216, loc=(-6.0, -1.8, 1.9))
    key(camC, 266, loc=(-5.6, -1.0, 2.1))
    shake(camC, 233, 276, 0.03, 5)
    camD, tD = camera('camD', (6.0, 8.0, 2.2), (0, 11, 3.6), 24)
    key(camD, 267, loc=(6.0, 8.0, 2.2))
    key(tD, 267, loc=(0, 8, 2.5))
    key(tD, 286, loc=(0, 12, 4.0))
    key(tD, 318, loc=(0, 15, 1.5))
    key(camD, 330, loc=(6.2, 6.5, 2.6))
    key(tD, 345, loc=(0, 4, 1.2))
    shake(camD, 286, 296, 0.12, 6)
    shake(camD, 318, 334, 0.18, 7)
    camE, tE = camera('camE', (0.3, -4.4, 1.55), (0, 0.5, 1.45), 35)
    key(camE, 346, loc=(0.3, -4.4, 1.55))
    key(camE, 456, loc=(0.25, -3.6, 1.6))
    key(tE, 346, loc=(0, 0.5, 1.45))
    key(tE, 456, loc=(0, 0.4, 1.7))
    for cam_, f in ((camA, 1), (camB, 113), (camC, 216), (camD, 267), (camE, 346)):
        cut(cam_, f)
    compositor_glow(threshold=1.3, strength=0.4, size=0.55)
