#!/usr/bin/env python3
"""Render cartoon episodes as YouTube Shorts (1080x1920, 30 fps, <=20 s).

    python make.py            # render every episode
    python make.py ep01       # render one episode
    python make.py ep01 --preview 0,45,120   # write PNG previews of some frames
"""
import argparse
import glob
import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from engine.video import build  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episodes", nargs="*", help="episode ids, e.g. ep01 (default: all)")
    ap.add_argument("--preview", help="comma separated frame numbers to export as PNG instead of video")
    ap.add_argument("--out", default=os.path.join(HERE, "output"))
    args = ap.parse_args()
    mods = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(HERE, "episodes", "ep*.py")))
    if args.episodes:
        mods = [m for m in mods if any(m.startswith(e) for e in args.episodes)]
    for name in mods:
        mod = importlib.import_module("episodes." + name)
        ep = mod.episode()
        out = os.path.join(args.out, name + ".mp4")
        frames = [int(x) for x in args.preview.split(",")] if args.preview else None
        t0 = time.time()
        dur = build(ep, mod.choreo, out, frames)
        print(f"{name}: {dur:.1f}s -> {out if not frames else 'previews'} ({time.time() - t0:.0f}s)")
        if not frames:
            with open(os.path.join(args.out, name + ".txt"), "w") as f:
                f.write(mod.TITLE + "\n\n" + mod.DESCRIPTION + "\n")


if __name__ == "__main__":
    main()
