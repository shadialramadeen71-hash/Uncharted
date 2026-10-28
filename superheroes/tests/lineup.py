import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from heroes import *
import cast
reset_scene((1280, 720), 24)
night_world('#0c1226', '#3b3060', stars=False, strength=1.5)
add('floor', box('floor', 10, 10, 0.05), mat('fl', '#3a3d45', 0.6), None, (0, 0, -0.05))
cs = [build_character(cast.volt(), (-1.6, 0, 0)), build_character(cast.nova(), (-0.5, 0, 0)),
      build_character(cast.shade(), (0.6, 0, 0.2)), build_character(cast.worker(), (1.7, 0, 0))]
v, n, sh, w = cs
apply_pose(v, None, pose(**arm('R', 0.4, 0.2, el=1.9), **arm('L', 0.4, 0.2, el=1.9), **hands(FIST, FIST)))
apply_pose(n, None, pose(**arm('L', 2.7, 0.3, el=0.2), **hands(OPEN, None)))
apply_pose(sh, None, pose(**arm('R', 1.3, 0.2, el=0.5), **hands(None, OPEN)))
brows(sh, 1, angry=1)
area_light('key', (-3, -5, 4), (0.9, 0, -0.5), '#fff3e0', 900, 4)
area_light('rim', (2, 4, 3), (-1.0, 0, 3.0), '#7fb0ff', 500, 3)
cam, t = camera('cam', (0, -5.5, 1.3), (0.05, 0, 1.0), 40)
bpy.context.scene.camera = cam
bpy.context.scene.render.filepath = sys.argv[-1]
bpy.ops.render.render(write_still=True)
