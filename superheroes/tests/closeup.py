import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from heroes import *
import cast
reset_scene((1280, 720), 24)
night_world('#0c1226', '#3b3060', stars=False, strength=1.5)
v = build_character(cast.volt(), (-0.35, 0, 0))
n = build_character(cast.nova(), (0.35, 0, 0), facing=0.3)
apply_pose(v, None, pose(**arm('R', 1.2, 0.3, el=0.6, twist=0.6), **hands(None, OPEN), **arm('L', 0.4, 0.2, el=1.9), **hands(FIST, None)))
apply_pose(n, None, pose(**arm('R', 1.3, 0.1, el=0.4), **hands(None, dict(curl=0.7, thumb=0.5, spread=0.1))))
area_light('key', (-2, -4, 3), (0.9, 0, -0.5), '#fff3e0', 600, 3)
area_light('rim', (2, 3, 3), (-1.0, 0, 3.0), '#7fb0ff', 400, 3)
cam, t = camera('cam', (0, -2.2, 1.55), (0, 0, 1.45), 50)
bpy.context.scene.camera = cam
bpy.context.scene.render.filepath = sys.argv[-1]
bpy.ops.render.render(write_still=True)
