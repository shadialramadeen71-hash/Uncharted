"""3D episode 2 - Stuck in an Elevator (Blender)."""
import bpy

import toon3d as T
from engine.anim import Track
from engine.video import Episode
from episodes.cast_heroes import add_batman, add_joker, add_superman
from ep3d import sets as S

TITLE = "Batman stuck in an elevator with the Joker 🛗😂"
DESCRIPTION = """Batman stuck in an elevator with the Joker 🛗😂

Elevator music. Awkward small talk. Then the power goes out…

Fan-made parody animation (made in Blender). Batman, Superman and the Joker are © DC.
#shorts #batman #joker #superman #3danimation"""


def episode():
    ep = Episode(TITLE, [("STUCK IN AN ELEVATOR", "#ffffff"), ("WITH THE JOKER", "#3ddc97")], "batcave",
                 music_seed=99, mood="muzak", bpm=100, theme="noir", max_len=15.0, hook_end=1.8, floor="leather")
    add_batman(ep, 400, 1)
    add_joker(ep, 690, -1)
    add_superman(ep, 545, 1)
    ep.say("joker", "Going up, Batsy?", wait=0.3)
    ep.say("joker", "So... come here often?", wait=1.6)
    ep.say("batman", "No.")
    ep.say("joker", "Uh oh.", wait=1.0)
    ep.say("superman", "Need a lift?", wait=1.5)
    ep.say("batman", "Stop saying that.")
    return ep


def choreo(ep, L):
    b_, j_, s_ = ep.chars["batman"], ep.chars["joker"], ep.chars["superman"]
    st = ep.state = {}
    b_["face"].key(0, 0.25)
    j_["face"].key(0, -0.3)
    b_.expr(0, "stern")
    j_.expr(0, "evil")
    b_.pose(0, (40, 120), (30, 120), "fist", "fist", dur=0.01, swing=0)  # arms crossed
    ep.sound(0.1, "ding", 0.8)
    # awkward silence: the Joker rocks on his heels
    a = L[0]["end"]
    for k in range(4):
        j_["y"].key(a + 0.2 + k * 0.4, -14.0 if k % 2 == 0 else 0.0)
    a, e = L[1]["start"], L[1]["end"]
    j_["face"].to(a - 0.2, a, -0.6)
    j_.pose(a, (60, 60), None, "open", dur=0.2)
    a, e = L[2]["start"], L[2]["end"]
    b_["face"].to(a - 0.1, a, 0.15)
    stop = e + 0.4
    st["stop"] = stop
    ep.sound(stop, "thud", 1.2)
    ep.shake(stop, 1.6, 0.6)
    b_.expr(stop, "worried")
    j_.expr(stop + 0.1, "shocked")
    j_.rest(stop)
    # roof ripped off, Superman floats down
    rip = L[4]["start"] - 1.1
    st["rip"] = rip
    ep.sound(rip, "crack", 1.0)
    ep.sound(rip + 0.05, "whoosh", 1.0)
    s_.tr["depth"] = Track(1.1)
    s_["visible"].key(0, 0.0)
    s_["visible"].set(rip + 0.2, 1.0)
    s_["y"].key(rip + 0.2, -1800.0)
    s_["y"].key(L[4]["start"], -240.0, "out")
    s_.expr(rip, "happy")
    s_.pose(L[4]["start"], (40, 50), None, "thumbsup", dur=0.2)
    b_.expr(L[4]["start"], "shocked")
    j_.expr(L[4]["start"], "happy")
    a, e = L[5]["start"], L[5]["end"]
    b_.expr(a, "stern")
    ep.end = e + 1.0


def build3d(ep, n):
    st = ep.state
    ceiling, key = S.elevator()
    looks = {k: T.Toon(k, T.LOOKS[k]) for k in ("batman", "joker", "superman")}
    for k, toon in looks.items():
        toon.animate(ep.chars[k], n)
    fps = T.FPS
    stop, rip = int(st["stop"] * fps), int(st["rip"] * fps)
    # lights flicker after the stop, then the roof goes up and moonlight pours in
    for fi, e in ((0, 260), (stop, 260), (stop + 2, 20), (stop + 5, 200), (stop + 8, 10), (stop + 12, 120), (rip - 1, 90)):
        key.data.energy = e
        key.data.keyframe_insert("energy", frame=fi)
    for fi, z, r in ((0, 3.25, 0.0), (rip, 3.25, 0.0), (rip + 15, 14.0, 0.6)):
        ceiling.location.z = z
        ceiling.rotation_euler.x = r
        ceiling.keyframe_insert("location", frame=fi)
        ceiling.keyframe_insert("rotation_euler", frame=fi)
    moon = S.moon_light()
    for fi, e in ((0, 0.0), (rip, 0.0), (rip + 10, 3.0)):
        moon.data.energy = e
        moon.data.keyframe_insert("energy", frame=fi)
    world = bpy.context.scene.world
    bg = world.node_tree.nodes["Background"]
    for fi, s in ((0, 0.3), (rip, 0.3), (rip + 10, 1.0)):
        bg.inputs["Strength"].default_value = s
        bg.inputs["Strength"].keyframe_insert("default_value", frame=fi)
    cam, tgt = T.camera((0.05, -3.4, 1.45), (0.05, 1.0, 1.4), lens=22)
    keys = [(0, (0.05, -3.4, 1.45), (0.05, 1.0, 1.4)),
            (int(ep.lines[1]["start"] * fps), (0.05, -3.4, 1.45), (0.05, 1.0, 1.4)),
            (int(ep.lines[2]["start"] * fps), (-0.35, -2.2, 1.75), (-0.45, 0.6, 1.75)),
            (stop, (-0.35, -2.2, 1.75), (-0.45, 0.6, 1.75)),
            (stop + 6, (0.05, -3.4, 1.45), (0.05, 1.0, 1.4)),
            (rip, (0.05, -3.4, 1.45), (0.05, 1.0, 1.6)),
            (rip + 12, (0.05, -3.6, 1.2), (0.05, 1.0, 2.0)),
            (n - 1, (0.05, -3.6, 1.2), (0.05, 1.0, 2.0))]
    for fi, loc, look in keys:
        cam.location = loc
        tgt.location = look
        cam.keyframe_insert("location", frame=fi)
        tgt.keyframe_insert("location", frame=fi)
