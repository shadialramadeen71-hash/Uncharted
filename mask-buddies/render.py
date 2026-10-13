"""Render MASK BUDDIES shorts.

    python3 render.py            # all episodes -> output/
    python3 render.py 2          # just episode 2
    python3 render.py 1 --preview 90 300   # PNG stills of chosen frames
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def install_fonts():
    dst = os.path.expanduser("~/.fonts")
    os.makedirs(dst, exist_ok=True)
    src = os.path.join(HERE, "assets", "fonts")
    changed = False
    for f in os.listdir(src):
        if f.endswith(".ttf") and not os.path.exists(os.path.join(dst, f)):
            shutil.copy(os.path.join(src, f), dst)
            changed = True
    if changed:
        subprocess.run(["fc-cache", "-f"], check=False)


def main():
    install_fonts()
    import engine
    from episodes import EPISODES

    args = sys.argv[1:]
    preview = None
    if "--preview" in args:
        i = args.index("--preview")
        preview = [int(x) for x in args[i + 1:]]
        args = args[:i]
    eps = [int(a) for a in args] or sorted(EPISODES)
    out_dir = os.path.join(HERE, "output")
    for n in eps:
        t0 = time.time()
        ep = EPISODES[n]().build()
        out = os.path.join(out_dir, f"mask_buddies_ep{n}.mp4")
        print(f"Episode {n}: {ep.title}  ({ep.total:.1f}s, {len(ep.frames)} frames)", flush=True)
        engine.render(ep, out, preview_frames=preview)
        print(f"  done in {time.time() - t0:.0f}s -> {out}", flush=True)


if __name__ == "__main__":
    main()
