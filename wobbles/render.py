"""Render THE WOBBLES episodes.

    python3 render.py                    # all episodes -> output/
    python3 render.py 1 --preview 200 900  # PNG stills of chosen frames
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "mask-buddies"))


def install_fonts():
    import shutil
    import subprocess
    src = os.path.join(HERE, "..", "mask-buddies", "assets", "fonts")
    dst = os.path.expanduser("~/.fonts")
    os.makedirs(dst, exist_ok=True)
    new = [f for f in os.listdir(src) if f.endswith(".ttf") and not os.path.exists(os.path.join(dst, f))]
    for f in new:
        shutil.copy(os.path.join(src, f), dst)
    if new:
        subprocess.run(["fc-cache", "-f"], check=False)


def main():
    install_fonts()
    import wob_engine
    import wob_chars_hd  # the improved art: real hands, legs and shoes
    wob_engine.CAST.update(wob_chars_hd.CAST)
    from wob_episodes import EPISODES

    args = sys.argv[1:]
    vertical = "--vertical" in args
    args = [a for a in args if a != "--vertical"]
    if vertical:
        wob_engine.set_vertical(True)
    preview = None
    if "--preview" in args:
        i = args.index("--preview")
        preview = [int(x) for x in args[i + 1:]]
        args = args[:i]
    for n in [int(a) for a in args] or sorted(EPISODES):
        t0 = time.time()
        ep = EPISODES[n]().build()
        out = os.path.join(HERE, "output", f"the_wobbles_ep{n}{'_short' if vertical else ''}.mp4")
        print(f"Episode {n}: {ep.title} ({ep.total:.1f}s, {len(ep.frames)} frames)", flush=True)
        wob_engine.render(ep, out, preview=preview)
        print(f"  done in {time.time() - t0:.0f}s -> {out}", flush=True)


if __name__ == "__main__":
    main()
