"""3D episode 1 - The Pink Batmobile (Gotham street, Blender)."""
import math

import bpy

import toon3d as T
from engine.anim import Track
from engine.video import Episode
from episodes.cast_heroes import add_batman, add_joker, add_superman
from ep3d import sets as S

TITLE = "Who painted the Batmobile PINK?! 🦇💗"
DESCRIPTION = """Who painted the Batmobile PINK?! 🦇💗

The Joker's new paint job… and Superman's very fast car wash. 3D episode!

Fan-made parody animation (made in Blender). Batman, Superman and the Joker are © DC.
#shorts #batman #joker #superman #3danimation"""

PINK = (0.98, 0.35, 0.65)
BLACK = (0.03, 0.03, 0.05)


def episode():
    ep = Episode(TITLE, [("WHO PAINTED THE", "#ffffff"), ("BATMOBILE PINK?!", "#ff6fae")], "gotham_street",
                 music_seed=98, mood="noir", bpm=128, theme="noir", max_len=15.0, hook_end=1.8, floor="leather")
    add_joker(ep, 720, -1)
    add_batman(ep, -300, 1)
    add_superman(ep, 420, 1)
    ep.say("joker", "Ha! The Batmobile needed some color!")
    ep.say("batman", "...My car.", wait=0.5)
    ep.say("superman", "Relax. I've got this!", wait=0.8)
    ep.say("batman", "...It's shiny.", wait=2.0)
    ep.say("joker", "My hair is PINK!", fx="shout")
    return ep


def choreo(ep, L):
    j_, b_, s_ = ep.chars["joker"], ep.chars["batman"], ep.chars["superman"]
    st = ep.state = {}
    j_.expr(0, "evil")
    j_.pose(0, (100, 10), None, "hold", dur=0.01, swing=0)
    ep.sound(0.3, "sizzle", 0.5)
    ep.sound(1.2, "sizzle", 0.5)
    b_.expr(0, "stern")
    arrive = b_.walk_to(0.4, 230, speed=230)
    a, e = L[1]["start"], L[1]["end"]
    j_.turn(a - 0.4, -1)
    j_.rest(a - 0.3)
    s_["visible"].key(0, 0.0)
    s_["y"].key(0, -2400.0)
    land = L[2]["start"] - 0.2
    s_["visible"].set(land - 0.9, 1.0)
    s_["y"].key(land - 0.9, -2400.0)
    s_["y"].key(land, 0.0, "out")
    ep.sound(land - 0.8, "whoosh", 1.0)
    ep.sound(land, "thud", 0.8)
    s_.expr(land, "happy")
    s_.pose(L[2]["start"], (40, 50), None, "thumbsup", dur=0.2)
    # super-speed wash
    wash = L[2]["end"] + 0.15
    wash_end = wash + 1.6
    st.update(wash=wash, wash_end=wash_end, land=land)
    s_["visible"].set(wash, 0.0)
    s_["visible"].set(wash_end, 1.0)
    for k in range(5):
        ep.sound(wash + k * 0.3, "whoosh", 0.8)
    ep.sound(wash_end - 0.1, "sparkle", 1.0)
    ep.shake(wash, 1.0, 1.6)
    j_.tr["spin"] = Track(0.0)
    j_.tr["spin"].key(wash, 0.0)
    j_.tr["spin"].key(wash_end, 1440.0, "out")
    j_.expr(wash_end, "shocked")
    b_.expr(wash_end, "neutral")
    a, e = L[3]["start"], L[3]["end"]
    s_.pose(a, (18, 105), (12, 105), "fist", "fist", dur=0.2)  # arms folded, proud
    a, e = L[4]["start"], L[4]["end"]
    j_.pose(a, (160, 40), (-160, 40), "open", "open", dur=0.2)
    ep.end = e + 1.0


def build3d(ep, n):
    st = ep.state
    S.street()
    car, paint = S.batmobile()
    S.key_paint(paint, 0, PINK)
    S.key_paint(paint, int((st["wash_end"] - 0.2) * T.FPS), PINK)
    S.key_paint(paint, int(st["wash_end"] * T.FPS), BLACK)
    looks = {k: T.Toon(k, T.LOOKS[k]) for k in ("joker", "batman", "superman")}
    for k, toon in looks.items():
        toon.animate(ep.chars[k], n)
    # the Joker's spin + his hair turning pink
    j = looks["joker"]
    for fi in range(n):
        t = fi / T.FPS
        sp = ep.chars["joker"].tr["spin"].at(t)
        if sp:
            j.root.rotation_euler.z += math.radians(sp)
            j.root.keyframe_insert("rotation_euler", frame=fi)
    hair = bpy.data.materials["joker_hairm"]
    S.key_paint(hair, int(st["wash_end"] * T.FPS) - 1, T.LOOKS["joker"]["hair"])
    S.key_paint(hair, int(st["wash_end"] * T.FPS), PINK)
    can = S.spray_can(j.arms[1][1])
    # whirlwind around the car during the wash
    ww = S.whirlwind("whirl", (0.6, 1.8, 1.8))
    for fi, s in ((0, 0.0), (int(st["wash"] * T.FPS) - 1, 0.0), (int(st["wash"] * T.FPS) + 4, 1.0),
                  (int(st["wash_end"] * T.FPS) - 3, 1.0), (int(st["wash_end"] * T.FPS) + 2, 0.0)):
        ww.scale = (s + 1e-4, s + 1e-4, s + 1e-4)
        ww.keyframe_insert("scale", frame=fi)
    ww.rotation_euler = (0, 0, 0)
    ww.keyframe_insert("rotation_euler", frame=int(st["wash"] * T.FPS))
    ww.rotation_euler = (0, 0, 60)
    ww.keyframe_insert("rotation_euler", frame=int(st["wash_end"] * T.FPS))
    # sparkles on the clean car
    for k in range(6):
        sp = T.sphere(f"spark{k}", 0.08, (-1.2 + k * 0.6, 1.2, 0.9 + (k % 2) * 0.4), T.toon("sparkm", (1, 1, 0.8), emit=6.0))
        for fi, s in ((int(st["wash_end"] * T.FPS) - 1, 0.0), (int(st["wash_end"] * T.FPS) + 3 + k, 1.6),
                      (int(st["wash_end"] * T.FPS) + 18 + k, 0.0)):
            sp.scale = (s + 1e-4,) * 3
            sp.keyframe_insert("scale", frame=fi)
    # camera: wide, punch on Batman, back out for the wash
    cam, tgt = T.camera((0.2, -9.0, 1.7), (0.2, 0.5, 1.35), lens=55)
    l1s, l1e = int(ep.lines[1]["start"] * T.FPS), int(ep.lines[1]["end"] * T.FPS)
    keys = [(0, (0.9, -9.0, 1.5), (0.9, 0.5, 1.15)),
            (l1s - 2, (0.4, -9.0, 1.5), (0.4, 0.5, 1.15)),
            (l1s + 6, (-0.9, -6.0, 1.75), (-0.9, 0.0, 1.7)),
            (l1e + 4, (-0.9, -6.0, 1.75), (-0.9, 0.0, 1.7)),
            (l1e + 10, (0.2, -10.5, 1.6), (0.2, 0.5, 1.25)),
            (n - 1, (0.2, -9.5, 1.6), (0.2, 0.5, 1.25))]
    for fi, loc, look in keys:
        cam.location = loc
        tgt.location = look
        cam.keyframe_insert("location", frame=fi)
        tgt.keyframe_insert("location", frame=fi)
