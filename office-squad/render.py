"""Render OFFICE SQUAD vertical shorts.

    python3 render.py                       # all episodes -> output/office_squad_epN_short.mp4
    python3 render.py 1 --preview 100 400   # PNG stills
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def install_fonts():
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
    from sq_episodes import EPISODES
    import wob_engine
    wob_engine.set_vertical(True)

    args = sys.argv[1:]
    preview = None
    if "--preview" in args:
        i = args.index("--preview")
        preview = [int(x) for x in args[i + 1:]]
        args = args[:i]
    for n in [int(a) for a in args] or sorted(EPISODES):
        t0 = time.time()
        ep = EPISODES[n]().build()
        out = os.path.join(HERE, "output", f"office_squad_ep{n}_short.mp4")
        print(f"Episode {n}: {ep.title} ({ep.total:.1f}s, {len(ep.frames)} frames)", flush=True)
        wob_engine.render(ep, out, preview=preview)
        print(f"  done in {time.time() - t0:.0f}s -> {out}", flush=True)


if __name__ == "__main__":
    main()
