"""Episode 2 - NOVA: Falling Star. Sunset, skyscraper construction site."""
import math, random
from heroes import *
import cast
import ep2_story as story

F = lambda t: int(round(t * FPS)) + 1
H = 40.0  # height of the working floor


def build(lips):
    end = F(story.DURATION) - 1
    s = bpy.context.scene
    s.frame_start, s.frame_end = 1, end

    # ------------------------------------------------------------ world
    sunset_world()
    win = window_material('windows_dusk', lit='#ffd9a0', wall='#2a2d36', glow_strength=1.2)
    skyline(win, seed=11, count=110, rmin=25, rmax=160, hmin=-10, hmax=30, ground=-1)
    add('ground', box('ground', 400, 400, 0.5), mat('ground', '#2b2c30', 0.9), None, (0, 0, -1.5))
    add('sundisk', ellipsoid('sundisk', 14, 14, 14, 32, 16), glow('sunm', '#ffd27a', 12), None, (-260, 300, 18))
    sun('sun', (math.radians(84), 0, math.radians(220)), '#ffb070', 3.0, 0.03)
    area_light('roof_fill', (10.1, -13.8, 29.0), (math.radians(70), 0, 0), '#ffd6b0', 350, 3)
    area_light('sky_fill', (0, -10, H + 8), (math.radians(30), 0, 0), '#8aa0ff', 900, 10)

    # steel skeleton (columns + girders), crane
    steel = mat('steel', '#b8441c', 0.55, 0.6)
    for ix, x in enumerate((3, 9, 15)):
        for iy, y in enumerate((-4, 2, 8)):
            add(f'col{ix}{iy}', box('col', 0.18, 0.18, (H + 4) / 2), steel, None, (x, y, (H + 4) / 2 - 1))
    for z in range(4, int(H) + 5, 4):
        for y in (-4, 2, 8):
            add(f'gx{z}{y}', box('gx', 6.2, 0.12, 0.18), steel, None, (9, y, z), bevel=0.01)
        for x in (3, 9, 15):
            add(f'gy{z}{x}', box('gy', 0.12, 6.2, 0.18), steel, None, (x, 2, z), bevel=0.01)
    add('deck', box('deck', 6.1, 6.1, 0.08), mat('plank', '#8a6a44', 0.8), None, (9, 2, H - 0.15))
    yel = mat('crane', '#f2b705', 0.45, 0.3)
    add('mast', box('mast', 0.7, 0.7, 30), yel, None, (22, 14, 29))
    add('jib', box('jib', 22, 0.5, 0.6), yel, None, (12, 14, 58.5))
    add('cab', box('cab', 1.4, 1.2, 1.2), mat('cab', '#e8e8e8', 0.3), None, (22, 12.6, 57))
    add('cwt', box('cwt', 2.2, 1.2, 1.4), mat('cwt', '#6a6a6a', 0.7), None, (30, 14, 57.5))
    add('cable', capsule('cable', 0.02, 0.02, 12, segs=6), mat('cablem', '#111111', 0.4, 0.8), None, (-4, 14, 58))
    add('hook', box('hook', 0.3, 0.3, 0.3), mat('hookm', '#d8a800', 0.4, 0.6), None, (-4, 14, 46), bevel=0.05)
    warn = glow('warnlight', '#ff3020', 30)
    add('craneLight', ellipsoid('cl', 0.25, 0.25, 0.25, 12, 6), warn, None, (22, 14, 59.5))

    # the beam Sam stands on: cantilevered out from the skeleton toward -X
    piv = empty('beam_piv', None, (3, 0, H))
    add('beam', box('beam', 3.4, 0.12, 0.16), steel, piv, (-3.4, 0, 0), bevel=0.01)
    add('beamflange', box('bf', 3.4, 0.22, 0.03), steel, piv, (-3.4, 0, 0.15), bevel=0.01)
    bolts = [add(f'bolt{i}', ellipsoid('bolt', 0.05, 0.05, 0.05, 10, 6), mat('boltm', '#888888', 0.3, 1), piv,
                 (-0.2, -0.2 + 0.13 * i, 0.19)) for i in range(4)]

    # landing roof
    roof_c = (11.0, -9.0, 26.0)
    add('lroof', box('lroof', 4.5, 4.5, 13.5), mat('lroofm', '#3c3f47', 0.7), None,
        (roof_c[0], roof_c[1], roof_c[2] - 13.5))
    add('lroof_top', box('lrt', 4.6, 4.6, 0.12), mat('tarm', '#55575c', 0.9), None, roof_c)
    add('helipad', ellipsoid('heli', 2.2, 2.2, 0.01, 40, 4), mat('heli', '#d9d9d9', 0.6), None,
        (roof_c[0], roof_c[1], roof_c[2] + 0.12))
    add('helipadH', box('hh', 0.15, 1.0, 0.012), mat('helih', '#c62020', 0.6), None,
        (roof_c[0], roof_c[1], roof_c[2] + 0.13))

    # ------------------------------------------------------------ characters
    sam = build_character(cast.worker(), (1.5, 0, H + 0.19), facing=-math.pi / 2)
    nova = build_character(cast.nova(), (-30, -6, H - 8), facing=-math.pi / 2)
    who = {'SAM': sam, 'NOVA': nova}
    random.seed(2)
    for L in lips:
        c = who[L['speaker']]
        lipsync(c, L['start_frame'], L['env'])
        for f in range(L['start_frame'], L['start_frame'] + len(L['env']), 14):
            look(c, f, turn=random.uniform(-0.08, 0.08), nod=random.uniform(-0.06, 0.04))

    # ------------------------------------------------------------ SAM
    place(sam, 1, loc=(1.5, 0, H + 0.19), rot_z=-math.pi / 2)
    place(sam, 44, loc=(-1.4, 0, H + 0.19))
    walk(sam, 1, 44, period=22, stride=0.35)
    look(sam, 1)
    stand = pose(**arm('L', 0.1, 0.15, el=0.3), **arm('R', 0.1, 0.15, el=0.3))
    apply_pose(sam, 50, stand)
    scratch = pose(stand, **arm('R', 0.9, 0.9, el=2.3, twist=0.5), head=(0.35, 0.1, 0), spine=(0.12, 0, 0))
    apply_pose(sam, 58, scratch)
    apply_pose(sam, 74, scratch)
    alarm = pose(stand, **arm('L', 0.7, 0.9, el=0.4), **arm('R', 0.7, 0.9, el=0.4), **hands(OPEN, OPEN),
                 head=(0.4, 0, 0), spine=(0.1, 0, 0), **leg('L', 0.2, 0.15, knee=0.4), **leg('R', 0.1, 0.15, knee=0.4),
                 root_loc=(0, 0, -0.06))
    apply_pose(sam, 82, alarm)
    brows(sam, 1)
    brows(sam, 55, raise_=0.5)
    brows(sam, 82, raise_=1.2)
    # beam wobble + snap
    key(piv, 56, rot=(0, 0, 0))
    key(piv, 60, rot=(0.03, -0.04, 0))
    key(piv, 64, rot=(-0.02, 0.0, 0))
    key(piv, 68, rot=(0.02, -0.05, 0))
    key(piv, 78, rot=(0, -0.05, 0))
    key(piv, 82, rot=(0, -0.35, 0), loc=(3, 0, H))
    key(piv, 130, rot=(0.6, -1.4, 0.3), loc=(2.0, 0.3, H - 20))
    key(piv, 160, loc=(1.5, 0.3, H - 45))
    for i, b in enumerate(bolts):
        key(b, 79, loc=(-0.2, -0.2 + 0.13 * i, 0.19))
        key(b, 110, loc=(-0.2 + i * 0.4, -1 + i * 0.6, -14))
    # fall: Sam tumbles from the beam
    place(sam, 81, loc=(-1.4, 0, H + 0.19), rot=(0, 0, -math.pi / 2))
    place(sam, 88, loc=(-1.7, -0.2, H - 0.3), rot=(0.4, -0.3, -math.pi / 2))
    place(sam, 191, loc=(-2.4, -0.6, 21.0), rot=(1.7, -1.4, -math.pi / 2 + 0.6))
    fl = pose(**arm('L', 2.4, 1.0, el=0.5), **arm('R', 2.7, 0.8, el=0.4), **hands(OPEN, OPEN),
              **leg('L', 0.6, 0.3, knee=1.0), **leg('R', -0.2, 0.2, knee=0.6), head=(-0.3, 0, 0))
    fl2 = pose(**arm('L', 2.8, 0.7, el=0.3), **arm('R', 2.2, 1.1, el=0.6), **hands(OPEN, OPEN),
               **leg('L', -0.1, 0.2, knee=0.5), **leg('R', 0.7, 0.3, knee=1.2), head=(-0.4, 0, 0.2))
    for i, f in enumerate(range(88, 192, 9)):
        apply_pose(sam, f, fl if i % 2 == 0 else fl2)

    # ------------------------------------------------------------ NOVA flight path
    fly = pose(**arm('R', 3.05, 0.15, el=0.05, twist=0.0), **arm('L', 0.2, 0.15, el=0.1), **hands(FIST, FIST),
               **leg('L', 0.05, 0.02, knee=0.15), **leg('R', -0.1, 0.02, knee=0.35, ankle=0.4),
               root_rot=(1.45, 0, 0), head=(-1.0, 0, 0))
    reach = pose(fly, **arm('R', 1.9, 0.2, el=0.6, twist=1.5), **arm('L', 1.9, 0.2, el=0.6, twist=1.5),
                 **hands(OPEN, OPEN), root_rot=(0.9, 0, 0), head=(-0.6, 0, 0))
    carry = pose(**arm('R', 1.15, 0.2, el=1.1, twist=1.4), **arm('L', 1.15, 0.2, el=1.1, twist=1.4),
                 **hands(dict(curl=0.9, thumb=0.6, spread=0.05), dict(curl=0.9, thumb=0.6, spread=0.05)),
                 **leg('L', 0.15, 0.03, knee=0.3), **leg('R', -0.1, 0.03, knee=0.6, ankle=0.4),
                 root_rot=(0.45, 0, 0), head=(0.05, 0, 0.2))
    land = pose(carry, root_rot=(0, 0, 0), **leg('L', 0.4, 0.05, knee=0.9, ankle=-0.4),
                **leg('R', 0.4, 0.05, knee=0.9, ankle=-0.4), root_loc=(0, 0, -0.18))
    stand_n = pose(**arm('L', 0.1, 0.18, el=0.25), **arm('R', 0.1, 0.18, el=0.25))
    wave = pose(stand_n, **arm('R', 0.4, 2.4, el=0.5, twist=0.0), **hands(None, OPEN), head=(0, 0.1, -0.2))
    takeoff = pose(fly, root_rot=(0.3, 0, 0))

    apply_pose(nova, 1, fly)
    place(nova, 1, loc=(-70, -20, 30), rot_z=-1.2)
    place(nova, 130, loc=(-70, -20, 30))
    place(nova, 140, loc=(-38, -12, 25), rot_z=-1.2)
    place(nova, 176, loc=(-9, -3, 22.5), rot_z=-1.3)
    apply_pose(nova, 176, fly)
    apply_pose(nova, 186, reach)
    place(nova, 191, loc=(-3.5, -0.8, 21.2), rot_z=-1.45)
    apply_pose(nova, 194, carry)
    # carry: fly up and over to the roof
    place(nova, 210, loc=(-0.5, -2.5, 22.6), rot_z=-1.75)
    place(nova, 260, loc=(5.5, -6.0, 26.5), rot_z=-2.0)
    place(nova, 330, loc=(10.0, -8.4, 27.8), rot_z=-2.3)
    apply_pose(nova, 330, carry)
    place(nova, 368, loc=(11.0, -9.0, 26.12), rot_z=-0.8)
    apply_pose(nova, 368, land)
    apply_pose(nova, 384, pose(stand_n, head=(0.1, 0, 0.3)))
    place(nova, 384, loc=(11.0, -9.0, 26.12), rot_z=-0.8)
    apply_pose(nova, 396, wave)
    apply_pose(nova, 404, pose(wave, **arm('R', 0.4, 2.7, el=0.8)))
    apply_pose(nova, 410, takeoff)
    place(nova, 410, loc=(11.0, -9.0, 26.12))
    place(nova, 432, loc=(13.0, -14.0, 48.0))
    brows(nova, 1, angry=0.5)
    brows(nova, 200, angry=0.0, raise_=0.3)
    for f in (230, 290, 350, 392):
        blink(nova, f)
    for f in (20, 66, 250, 300, 400):
        blink(sam, f)

    # Sam rides in Nova's arms (Child Of on Nova's hips) from the catch until set down
    sam.ctrl.rotation_mode = 'ZYX'
    child_of(sam.ctrl, nova.root, [(1, 0), (191, 0), (192, 1), (375, 1), (376, 0)])
    carried = pose(**hands(dict(curl=0.6, thumb=0.4, spread=0.1), dict(curl=0.6, thumb=0.4, spread=0.1)),
                   **arm('R', 0.9, 1.2, el=1.3, twist=0.5), **arm('L', 0.4, 0.3, el=0.8),
                   **leg('L', 1.45, 0.05, knee=1.5), **leg('R', 1.4, 0.05, knee=1.6), spine=(0.25, 0, 0),
                   head=(-0.2, 0, 0.5))
    key(sam.ctrl, 192, loc=(0.75, -0.45, -0.25), rot=(0, -1.4, 1.75))
    apply_pose(sam, 192, carried)
    apply_pose(sam, 240, carried)
    apply_pose(sam, 252, pose(carried, head=(-0.1, 0, 0.9)))
    key(sam.ctrl, 375, loc=(0.75, -0.45, -0.25), rot=(0, -1.4, 1.75))
    apply_pose(sam, 375, carried)
    # set down on the roof, in front of Nova
    bpy.context.scene.frame_set(376)
    key(sam.ctrl, 376, loc=(9.4, -9.3, 26.12), rot=(0, 0, 0.8))
    apply_pose(sam, 376, pose(stand, head=(-0.1, 0, 0)))
    key(sam.ctrl, 432, loc=(9.4, -9.3, 26.12), rot=(0, 0, 0.8))
    apply_pose(sam, 400, pose(stand, head=(-0.3, 0, -0.3)))
    apply_pose(sam, 418, pose(stand, head=(-0.7, 0, -0.1), **arm('R', 0.6, 1.4, el=0.3), **hands(None, OPEN)))
    brows(sam, 376, raise_=1.0)

    # streak trail behind Nova while flying fast
    trail_m = glow('trail', '#c06bff', 3)
    trail = add('trail', capsule('trail', 0.14, 0.01, 1.0, segs=16), trail_m, nova.root, (0, 0, -0.2))
    for f, sc in ((1, 0), (134, 0), (140, 3.5), (176, 3.0), (190, 0), (410, 0), (420, 3.5)):
        key(trail, f, scale=(1, 1, sc) if sc else 0.001)
    key_emission(trail_m, 140, 3)
    key_emission(trail_m, 190, 0)
    key_emission(trail_m, 405, 0)
    key_emission(trail_m, 418, 3)
    nl = point_light('novaglow', (0, 0, 0.6), '#c06bff', 0, 0.3, parent=nova.root)
    for f, e in ((130, 0), (140, 250), (190, 80), (230, 30)):
        key_light(nl, f, e)
    emb = nova.cfg['mats']['emblem']
    key_emission(emb, 130, 2.5)
    key_emission(emb, 150, 15)
    key_emission(emb, 230, 2.5)

    # ------------------------------------------------------------ cameras
    camA, tA = camera('camA', (-4.5, -6.0, H + 1.6), (-0.3, 0, H + 1.4), 35)
    key(camA, 1, loc=(-4.5, -6.0, H + 1.6))
    key(camA, 80, loc=(-3.6, -4.6, H + 1.5))
    key(tA, 1, loc=(0.6, 0, H + 1.3))
    key(tA, 50, loc=(-1.2, 0, H + 1.35))
    camB, tB = camera('camB', (-6.5, -7.0, H + 3.5), (-1.6, 0, H), 30)
    for i, f in enumerate(range(81, 141, 6)):
        p = world_pos(sam.root, f)
        key(tB, f, loc=p)
        key(camB, f, loc=p + Vector((-3.2 - 0.05 * i, -3.6, 2.4 - 0.1 * i)))
    camC, tC = camera('camC', (-10.0, -24.0, 17.0), (-4.0, -1.5, 23.0), 32)
    key(camC, 135, loc=(-10.0, -24.0, 17.0))
    key(camC, 191, loc=(-7.5, -18.0, 19.0))
    key(tC, 135, loc=(-9.0, -3.0, 24.0))
    key(tC, 191, loc=(-3.2, -0.8, 22.0))
    shake(camC, 192, 200, 0.12, seed=5)
    camD, tD = camera('camD', (0, 0, 0), (0, 0, 0), 38)
    # follow cam for the flight: offset from Nova
    for f in range(200, 300, 10):
        p = world_pos(nova.root, f)
        key(tD, f, loc=p + Vector((0, 0, 0.3)))
        key(camD, f, loc=p + Vector((-2.4, -2.8, 0.6)))
    camE, tE = camera('camE', (5.5, -16.0, 27.4), (11.0, -9.2, 27.0), 32)
    key(camE, 300, loc=(4.0, -17.5, 28.4))
    key(tE, 300, loc=(9.5, -8.5, 27.3))
    key(camE, 380, loc=(6.0, -15.5, 27.3))
    key(tE, 380, loc=(10.7, -9.4, 27.1))
    key(tE, 410, loc=(10.8, -9.3, 27.2))
    key(tE, 432, loc=(12.0, -12.0, 36.0))
    camF, tF = camera('camF', (10.1, -14.6, 27.5), (10.2, -9.1, 27.15), 40)
    key(camF, 376, loc=(10.1, -14.6, 27.5))
    key(camF, 410, loc=(10.2, -13.9, 27.45))
    key(tF, 376, loc=(10.2, -9.1, 27.15))
    key(tF, 410, loc=(10.3, -9.1, 27.2))
    key(tF, 432, loc=(11.5, -11.0, 31.0))
    for cam_, f in ((camA, 1), (camB, 81), (camC, 135), (camD, 200), (camE, 300), (camF, 376)):
        cut(cam_, f)
    compositor_glow(threshold=1.3, strength=0.45, size=0.55)
