"""Build an episode in Blender (bpy) and render it.

  python3 render.py ep1                 # full render -> build/ep1/frames/####.png
  python3 render.py ep1 --stills 1 90   # quick preview stills of chosen frames
  python3 render.py ep1 --blend         # just save build/ep1/ep1.blend
Then: ./make_video.sh ep1
"""
import importlib, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(ROOT, 'lib'), os.path.join(ROOT, 'episodes')]
import bpy
from heroes import reset_scene, load_lipsync

args = sys.argv[1:]
ep = args[0]
out = os.path.join(ROOT, 'build', ep)
stills = '--stills' in args
res = (640, 360) if stills else (960, 540)
s = reset_scene(res, samples=10)
importlib.import_module(ep + '_scene').build(load_lipsync(out))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, ep + '.blend'))
if '--blend' in args:
    sys.exit(0)
if stills:
    frames = [int(a) for a in args[args.index('--stills') + 1:] if a.isdigit()]
    os.makedirs(os.path.join(out, 'stills'), exist_ok=True)
    for f in frames:
        s.frame_set(f)
        s.render.filepath = os.path.join(out, 'stills', f'{f:04d}.png')
        bpy.ops.render.render(write_still=True)
else:
    if '--range' in args:
        i = args.index('--range')
        s.frame_start, s.frame_end = int(args[i + 1]), int(args[i + 2])
    s.render.filepath = os.path.join(out, 'frames', '')
    s.render.use_overwrite = False
    s.render.use_placeholder = True
    bpy.ops.render.render(animation=True)
