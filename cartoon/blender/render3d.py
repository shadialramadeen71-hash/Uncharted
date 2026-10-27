#!/usr/bin/env python3
"""Render a 3D (Blender) episode as a YouTube Short.

    python blender/render3d.py ep27            # full render
    python blender/render3d.py ep27 --preview 30,120,300   # a few frames only

Audio, timing and captions come from the 2D engine; the picture is rendered by Blender (bpy)."""
import argparse
import glob
import importlib
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import cairo  # noqa: E402

from engine import character, scene, video  # noqa: E402
import toon3d as T  # noqa: E402

FPS = video.FPS


def pick_engine(sc):
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng
            return eng
        except TypeError:
            continue
    return "CYCLES"


def run(name, preview=None, engine=None):
    mod = importlib.import_module("ep3d." + name)
    ep = mod.episode()
    character.set_style("noir")
    scene.set_theme("noir")
    video._voice_pass(ep)
    mod.choreo(ep, ep.lines)
    dur = ep.end
    assert dur <= ep.max_len, f"{dur:.1f}s > {ep.max_len}s"
    n = int(dur * FPS)
    for c in ep.chars.values():
        c.simulate(FPS, n)
    video._mouths(ep, n)
    out_dir = os.path.join(os.path.dirname(HERE), "output")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + ".mp4")
    wav = out[:-4] + ".wav"
    video._mix(ep, dur, wav)

    # ---- 3D
    sc = T.reset()
    eng = engine or pick_engine(sc)
    T.use_engine(sc, eng)
    mod.build3d(ep, n)
    sc.frame_start, sc.frame_end = 0, n - 1
    frames_dir = os.path.join(out_dir, ".frames_" + name)
    os.makedirs(frames_dir, exist_ok=True)
    t0 = time.time()
    todo = preview if preview is not None else range(n)
    for fi in todo:
        sc.frame_set(fi)
        sc.render.filepath = os.path.join(frames_dir, f"f_{fi:04d}.png")
        bpy.ops.render.render(write_still=True)
        if fi % 30 == 0:
            print(f"  frame {fi}/{n}  {time.time() - t0:.0f}s", flush=True)

    # ---- captions / titles composited on top, then encode
    def ui(surf, fi):
        ctx = cairo.Context(surf)
        t = fi / FPS
        scene.hook_title(ctx, t, ep.hook, ep.hook_end)
        ln = video._active_line(ep, t)
        if ln:
            scene.captions(ctx, ln, t, y=ep.cap_y or scene.THEME["cap_y"])
        for fn in ep.layers["ui"]:
            fn(ctx, t)
        if ep.follow_at is not None:
            scene.follow_card(ctx, t, ep.follow_at)
        surf.flush()

    if preview is not None:
        for fi in preview:
            s = cairo.ImageSurface.create_from_png(os.path.join(frames_dir, f"f_{fi:04d}.png"))
            ui(s, fi)
            s.write_to_png(os.path.join(out_dir, f"{name}_preview_{fi:04d}.png"))
        return
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{scene.W}x{scene.H}",
        "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-ar", "48000", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    for fi in range(n):
        s = cairo.ImageSurface.create_from_png(os.path.join(frames_dir, f"f_{fi:04d}.png"))
        if s.get_format() != cairo.FORMAT_ARGB32:
            s2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, scene.W, scene.H)
            c2 = cairo.Context(s2)
            c2.set_source_surface(s, 0, 0)
            c2.paint()
            s = s2
        ui(s, fi)
        proc.stdin.write(s.get_data())
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    for f in glob.glob(os.path.join(frames_dir, "*.png")):
        os.remove(f)
    os.rmdir(frames_dir)
    with open(out[:-4] + ".txt", "w") as f:
        f.write(mod.TITLE + "\n\n" + mod.DESCRIPTION + "\n")
    print(f"{name}: {dur:.1f}s -> {out} ({time.time() - t0:.0f}s, engine {eng})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--preview")
    ap.add_argument("--engine")
    a = ap.parse_args()
    run(a.episode, [int(x) for x in a.preview.split(",")] if a.preview else None, a.engine)
