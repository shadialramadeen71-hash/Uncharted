"""Episode 1 - VOLT: Power Surge. Night rooftop."""
import math, random
from heroes import *
import cast
import ep1_story as story

F = lambda t: int(round(t * FPS)) + 1  # seconds -> frame


def build(lips):
    end = F(story.DURATION) - 1
    s = bpy.context.scene
    s.frame_start, s.frame_end = 1, end

    # ------------------------------------------------------------ world / city
    night_world('#03050d', '#2b1e52', stars=True, strength=1.0)
    win = window_material('windows', glow_strength=3.0)
    skyline(win, seed=4, count=90, rmin=20, rmax=120, hmin=-25, hmax=30)
    add('moon', ellipsoid('moon', 6, 6, 6, 32, 16), glow('moon', '#e6ecff', 6), None, (-60, 190, 75))
    concrete = mat('concrete', '#4a4b50', 0.85)
    add('roof', box('roof', 9, 8, 0.5), concrete, None, (0, 1, -0.5))
    add('roofbody', box('roofbody', 9, 8, 25), mat('facade', '#1c1f27', 0.7), None, (0, 1, -26))
    ledge = mat('ledge', '#5c5d63', 0.7)
    add('ledgeN', box('ledgeN', 9, 0.2, 0.35), ledge, None, (0, 9, 0.35), bevel=0.03)
    add('ledgeE', box('ledgeE', 0.2, 8, 0.35), ledge, None, (9, 1, 0.35), bevel=0.03)
    add('ledgeW', box('ledgeW', 0.2, 8, 0.35), ledge, None, (-9, 1, 0.35), bevel=0.03)
    metal = mat('roofmetal', '#6d7178', 0.4, 0.8)
    for i, (x, y) in enumerate(((4.2, 5.5), (-3.6, 2.2), (5.5, -2.5))):
        add(f'ac{i}', box(f'ac{i}', 0.7, 0.55, 0.45), metal, None, (x, y, 0.45), bevel=0.04)
        add(f'fan{i}', ellipsoid(f'fan{i}', 0.4, 0.4, 0.04, 20, 6), mat('fan', '#202225', 0.5, 0.6), None,
            (x, y, 0.92))
    wt = mat('watertower', '#5a3d2b', 0.8)
    add('wtank', capsule('wtank', 1.2, 1.2, 1.8, up=True, segs=24), wt, None, (-5.5, 6.2, 2.2))
    add('wroof', cone('wroof', 1.35, 0.8, 24), mat('wroofm', '#2c2f33', 0.6), None, (-5.5, 6.2, 4.9))
    for dx in (-0.8, 0.8):
        for dy in (-0.8, 0.8):
            add(f'wleg{dx}{dy}', capsule('wleg', 0.06, 0.06, 2.2, up=True, segs=8), metal, None,
                (-5.5 + dx, 6.2 + dy, 0))
    add('hut', box('hut', 1.2, 1.0, 1.3), mat('hutm', '#3b3d44', 0.8), None, (6.2, 3.8, 1.3))
    add('hutdoor', box('hutdoor', 0.45, 0.02, 0.9), mat('door', '#5a1e1e', 0.6), None, (6.2, 2.79, 0.9))
    add('hutlamp', ellipsoid('hutlamp', 0.08, 0.05, 0.05), glow('lampm', '#ffd28a', 15), None, (6.2, 2.75, 2.0))
    point_light('hutlight', (6.2, 2.5, 1.9), '#ffcf8a', 60, 0.1)

    # ------------------------------------------------------------ lights
    moon = sun('moonlight', (math.radians(-55), math.radians(20), math.radians(160)), '#9db4ff', 0.6, 0.02)
    key_ = area_light('key', (-3.5, -3.0, 4.5), (math.radians(50), 0, math.radians(-40)), '#cfe0ff', 250, 4)
    vfill = area_light('voltfill', (1.5, 2.5, 2.6), (math.radians(-60), 0, math.radians(150)), '#ffe8d0', 220, 2.5)
    sfill = area_light('shadefill', (-1.5, 1.0, 2.8), (math.radians(55), 0, math.radians(-25)), '#9a6cff', 70, 2.5)
    rim = area_light('rim', (3, 8, 3.5), (math.radians(-60), 0, math.radians(160)), '#a070ff', 400, 3)

    # ------------------------------------------------------------ characters
    volt = build_character(cast.volt(), (0, -0.6, 0), facing=math.pi)
    shade = build_character(cast.shade(), (0, 4.0, 0.25), facing=0.0)
    who = {'VOLT': volt, 'SHADE': shade}
    for L in lips:
        lipsync(who[L['speaker']], L['start_frame'], L['env'])
        c = who[L['speaker']]
        n = len(L['env'])
        for f in range(L['start_frame'], L['start_frame'] + n, 14):  # small talking head motion
            look(c, f, turn=random.uniform(-0.06, 0.06), nod=random.uniform(-0.05, 0.05))

    # power core
    core_m = glow('core', '#38e1ff', 6)
    core = add('core', ellipsoid('core', 0.085, 0.085, 0.085, 24, 12), core_m, None, (0, 0, 0))
    for i in range(3):
        add(f'corering{i}', ellipsoid('corering', 0.13, 0.13, 0.008, 32, 4), mat('ring', '#c9d6e8', 0.2, 1.0),
            core, rot=(i * 1.05, i * 0.7, 0), subsurf=1)
    corelight = point_light('corelight', (0, 0, 0), '#38e1ff', 40, 0.08, parent=core)
    sh_grip = empty('shade_grip', shade.p['wristR'], (0.09, -0.01, -0.07))
    v_grip = empty('volt_grip', volt.p['wristR'], (0.085, 0.0, -0.075))
    c1 = core.constraints.new('COPY_LOCATION')
    c1.target = sh_grip
    c2 = core.constraints.new('COPY_LOCATION')
    c2.target = v_grip

    def infl(f, a, b):
        c1.influence, c2.influence = a, b
        c1.keyframe_insert('influence', frame=f)
        c2.keyframe_insert('influence', frame=f)

    # ------------------------------------------------------------ SHADE animation
    hold = pose(**arm('R', 1.75, 0.25, el=0.35, twist=1.4), **arm('L', 0.6, 0.35, el=1.1),
                **hands(dict(curl=0.6, thumb=0.4, spread=0.15), dict(curl=0.25, thumb=0.1, spread=0.2)),
                spine=(-0.08, 0, 0))
    raise_ = pose(hold, **arm('R', 2.5, 0.2, el=0.15, twist=1.4), spine=(-0.18, 0, 0), head=(-0.2, 0, 0))
    mock = pose(hold, **arm('L', 1.2, 0.6, el=0.9, twist=1.2), **hands(OPEN, None), spine=(-0.1, 0, 0.15),
                head=(-0.15, 0.15, 0))
    apply_pose(shade, 1, hold)
    apply_pose(shade, 20, raise_)
    apply_pose(shade, 70, raise_)
    apply_pose(shade, 95, pose(hold, head=(0.1, 0, 0)))  # startled look down at the lightning
    apply_pose(shade, 175, hold)
    apply_pose(shade, 190, mock)
    apply_pose(shade, 240, pose(mock, spine=(-0.2, 0, 0.1)))
    apply_pose(shade, 262, hold)
    # hover bob
    for f in range(1, 276, 24):
        place(shade, f, loc=(0, 4.0, 0.25 + 0.06 * math.sin(f / 24 * math.pi)))
    brows(shade, 1, angry=1.0)
    # zapped: jolts, then blown back, then dissolves
    rnd = random.Random(5)
    for f in range(277, 291, 2):
        apply_pose(shade, f, pose(hold, spine=(rnd.uniform(-0.35, -0.1), rnd.uniform(-0.15, 0.15), 0),
                                  head=(rnd.uniform(-0.4, 0.1), 0, rnd.uniform(-0.2, 0.2)),
                                  **arm('L', rnd.uniform(1.5, 2.6), 0.8, el=0.3), **arm('R', rnd.uniform(1.5, 2.6), 0.6, el=0.3),
                                  **hands(OPEN, OPEN)))
    place(shade, 289, loc=(0, 4.0, 0.25))
    place(shade, 300, loc=(0, 6.0, 0.9))
    apply_pose(shade, 300, pose(hold, spine=(-0.6, 0, 0), head=(-0.5, 0, 0), **arm('L', 2.8, 0.6, el=0.2),
                                **arm('R', 2.8, 0.6, el=0.2), **hands(OPEN, OPEN)))
    place(shade, 304, loc=(0, 6.4, 0.6))
    key(shade.ctrl, 312, scale=0.92)
    key(shade.ctrl, 330, scale=0.001)
    smoke = add('smoke', ellipsoid('smoke', 1, 1, 1, 20, 10), mat('smokem', '#2a1440', 0.9, emit='#7a2cff', estr=0.6),
                None, (0, 6.4, 1.3))
    key(smoke, 1, scale=0.001)
    key(smoke, 311, scale=0.001)
    key(smoke, 322, scale=0.9)
    key(smoke, 340, scale=0.001)

    # core: held by Shade, drained city -> knocked loose -> caught by Volt
    infl(1, 1, 0)
    key_emission(core_m, 1, 4)
    key_emission(core_m, 50, 18)
    key_light(corelight, 1, 20)
    key_light(corelight, 50, 120)
    key_emission(win, 1, 3.0)
    key_emission(win, 25, 3.0)
    key_emission(win, 55, 0.03)
    infl(289, 1, 0)
    p0 = world_pos(sh_grip, 289)
    infl(290, 0, 0)
    key(core, 290, loc=p0, rot=(0, 0, 0))
    key(core, 304, loc=(0.3, 2.2, 3.2), rot=(4, 2, 1))
    p1 = None  # Volt's grip at catch time, computed after Volt is animated

    # ------------------------------------------------------------ VOLT animation
    landing = pose(spine=(0.55, 0, 0), head=(-0.45, 0, 0), root_loc=(0, 0, -0.52),
                   **leg('L', 1.55, 0.15, knee=1.75, ankle=0.2), **leg('R', 0.0, 0.08, knee=2.4, ankle=0.9),
                   **arm('R', 0.9, 0.12, el=0.05), **arm('L', -0.5, 0.9, el=0.4),
                   **hands(OPEN, FIST))
    stand = pose(**arm('R', 0.15, 0.25, el=0.4), **arm('L', 0.15, 0.25, el=0.4), **hands(FIST, FIST),
                 **leg('L', 0.0, 0.08), **leg('R', 0.0, 0.08), spine=(-0.03, 0, 0))
    point = pose(stand, **arm('R', 1.5, 0.1, el=0.1, twist=0.3), pointR=True, curlR=1.45, thumbR=1.0,
                 spine=(0.05, 0, -0.1))
    charge = pose(stand, **arm('R', 0.35, 0.55, el=1.3), **arm('L', 0.35, 0.55, el=1.3), **hands(FIST, FIST),
                  **leg('L', 0.25, 0.2, knee=0.5, ankle=-0.25), **leg('R', 0.25, 0.2, knee=0.5, ankle=-0.25),
                  root_loc=(0, 0, -0.07), spine=(0.12, 0, 0), head=(0.1, 0, 0))
    cast_ = pose(stand, **arm('R', 1.5, 0.05, el=0.05, twist=1.5), **arm('L', 1.5, 0.05, el=0.05, twist=1.5),
                 **hands(OPEN, OPEN), **leg('L', 0.35, 0.05, knee=0.3, ankle=-0.1), **leg('R', -0.35, 0.05, knee=0.1),
                 spine=(0.08, 0, 0), root_loc=(0, 0, -0.04))
    catch = pose(stand, **arm('R', 1.2, 0.15, el=0.5, twist=1.5), **hands(FIST, dict(curl=0.7, thumb=0.5, spread=0.1)),
                 head=(0.25, 0, 0), spine=(0.08, 0, 0))
    raise_core = pose(stand, **arm('R', 2.95, 0.15, el=0.05, twist=1.5), **hands(FIST, dict(curl=0.75, thumb=0.6, spread=0.1)),
                      head=(-0.25, 0, 0), spine=(-0.08, 0, 0))
    raise_look = pose(raise_core, head=(-0.1, 0, 0.5), spine=(-0.05, 0, 0.25))

    place(volt, 1, loc=(0, -0.6, 40))
    place(volt, 76, loc=(0, -0.6, 9))
    place(volt, 81, loc=(0, -0.6, 0))
    apply_pose(volt, 1, landing)
    apply_pose(volt, 88, landing)
    apply_pose(volt, 104, pose(stand, head=(0.05, 0, 0)))
    brows(volt, 1, angry=0.4)
    apply_pose(volt, 112, stand)
    apply_pose(volt, 120, point)
    apply_pose(volt, 150, point)
    apply_pose(volt, 162, stand)
    apply_pose(volt, 214, stand)
    apply_pose(volt, 226, charge)
    brows(volt, 214, angry=0.4)
    brows(volt, 230, angry=1.0)
    apply_pose(volt, 262, charge)
    apply_pose(volt, 274, cast_)
    apply_pose(volt, 292, cast_)
    apply_pose(volt, 304, stand)
    apply_pose(volt, 315, catch)
    apply_pose(volt, 340, catch)
    brows(volt, 300, angry=0.1, raise_=0.6)
    apply_pose(volt, 352, raise_core)
    apply_pose(volt, 372, raise_core)
    apply_pose(volt, 392, raise_look)
    apply_pose(volt, 432, raise_look)
    for f in (60, 140, 200, 250, 330, 385, 420):
        blink(volt, f)

    p1 = world_pos(v_grip, 319)
    key(core, 319, loc=p1, rot=(6, 3, 2))
    infl(318, 0, 0)
    infl(319, 0, 1)
    key_emission(core_m, 300, 10)
    key_emission(core_m, 345, 10)
    key_emission(core_m, 365, 30)
    key_light(corelight, 345, 80)
    key_light(corelight, 365, 300)
    key_light(corelight, 400, 120)
    key_emission(win, 350, 0.03)
    key_emission(win, 385, 3.2)

    # eyes / suit glow while charging
    iris = volt.cfg['mats']['iris']
    key_emission(iris, 210, 0.6)
    key_emission(iris, 230, 25)
    key_emission(iris, 300, 25)
    key_emission(iris, 320, 0.6)
    emb = volt.cfg['mats']['emblem']
    key_emission(emb, 210, 3)
    key_emission(emb, 235, 25)
    key_emission(emb, 300, 25)
    key_emission(emb, 325, 3)

    # ------------------------------------------------------------ lightning
    bolt_m = glow('bolt', '#9fdcff', 40)
    strike = (0, -0.6, 0.05)
    flicker_bolts('strike', (2, -1, 60), strike, bolt_m, 79, 86, n_variants=3, seed=1, segs=26, jag=1.8,
                  radius=0.06, branches=4)
    flash = point_light('flash', (0, -0.6, 4), '#bfe4ff', 0, 0.5)
    for f, e in ((78, 0), (79, 25000), (81, 4000), (82, 20000), (84, 3000), (86, 9000), (90, 0)):
        key_light(flash, f, e)
    ring_m = glow('shock', '#9fdcff', 6)
    ring = add('shockring', ellipsoid('shockring', 1, 1, 0.02, 40, 6), ring_m, None, (0, -0.6, 0.03))
    key(ring, 80, scale=(0.01, 0.01, 1))
    key(ring, 92, scale=(3.5, 3.5, 1))
    key(ring, 93, scale=(0.001, 0.001, 1))
    key_emission(ring_m, 80, 12)
    key_emission(ring_m, 92, 0)
    shake_cam = None

    # charge sparks around fists
    small = glow('spark', '#c8ecff', 30)
    for S in 'LR':
        pf = world_pos(volt.p['wrist' + S], 240)
        for k in range(3):
            a = Vector((random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)))
            flicker_bolts(f'spark{S}{k}', pf, pf + a, small, 222 + k * 4, 272, n_variants=2, seed=20 + k,
                          segs=6, jag=0.06, radius=0.006, branches=0)
    vglow = point_light('voltglow', (0, -0.6, 1.3), '#7fd0ff', 0, 0.3)
    key_light(vglow, 214, 0)
    key_light(vglow, 235, 150)
    key_light(vglow, 296, 250)
    key_light(vglow, 315, 0)

    # main zap: both hands -> Shade's chest
    target = world_pos(shade.p['spine'], 280) + Vector((0, 0, 0.42))
    for S in 'LR':
        ph = world_pos(volt.p['wrist' + S], 276) + Vector((0, 0.12, 0))
        flicker_bolts('zap' + S, ph, target, bolt_m, 276, 291, n_variants=3, seed=7 if S == 'L' else 9, segs=18,
                      jag=0.35, radius=0.025, branches=3)
    zl = point_light('zaplight', target, '#9fdcff', 0, 0.3)
    for f, e in ((275, 0), (276, 2500), (280, 1200), (284, 2600), (288, 1500), (291, 0)):
        key_light(zl, f, e)

    # ------------------------------------------------------------ cameras
    shade_head = lambda f: world_pos(shade.p['head'], f) + Vector((0, 0, 0.12))
    camA, tA = camera('camA', (1.8, -1.0, 0.7), (0, 4.0, 1.8), 32)
    key(camA, 1, loc=(1.8, -1.0, 0.7))
    key(camA, 79, loc=(0.9, 1.0, 1.0))
    camB, tB = camera('camB', (-4.2, -5.2, 1.0), (0, -0.4, 0.75), 28)
    key(camB, 80, loc=(-4.2, -5.2, 1.0))
    key(tB, 80, loc=(0, -0.4, 0.75))
    key(tB, 104, loc=(0, -0.4, 0.75))
    key(tB, 120, loc=(0, 0.6, 1.5))
    key(camB, 170, loc=(-3.4, -4.6, 1.3))
    shake(camB, 81, 100, 0.12, seed=2)
    camC, tC = camera('camC', (1.15, -2.4, 2.0), shade_head(200), 50)
    key(camC, 171, loc=(1.15, -2.4, 2.0))
    key(camC, 213, loc=(1.0, -1.9, 1.95))
    camD, tD = camera('camD', (0.3, 1.6, 1.15), (0, -0.6, 1.45), 45)
    key(camD, 214, loc=(0.35, 1.7, 1.05))
    key(camD, 275, loc=(0.25, 1.15, 1.2))
    camE, tE = camera('camE', (-7.2, 1.7, 1.7), (0, 1.9, 1.35), 30)
    key(tE, 276, loc=(0, 1.9, 1.35))
    key(tE, 300, loc=(0, 3.0, 1.6))
    key(tE, 319, loc=(0, 0.6, 1.5))
    key(camE, 276, loc=(-7.2, 1.7, 1.7))
    key(camE, 340, loc=(-6.4, 0.8, 1.5))
    shake(camE, 276, 292, 0.05, seed=3)
    camF, tF = camera('camF', (1.0, 1.9, 0.45), (0, -0.6, 1.85), 28)
    key(camF, 341, loc=(1.0, 1.9, 0.45))
    key(tF, 341, loc=(0, -0.6, 1.85))
    key(camF, 432, loc=(2.2, 3.4, 0.9))
    key(tF, 432, loc=(0, -0.6, 2.2))
    flf = area_light('frontfill', (0.8, 1.6, 1.4), (math.radians(-85), 0, math.radians(170)), '#fff0dd', 0, 1.0)
    key_light(flf, 340, 0)
    key_light(flf, 341, 120)
    for cam_, f in ((camA, 1), (camB, 80), (camC, 171), (camD, 214), (camE, 276), (camF, 341)):
        cut(cam_, f)
    compositor_glow(threshold=1.2, strength=0.5, size=0.55)
