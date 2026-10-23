"""The Count & Pip 2 - The Magic Wand (throne room)."""
import math

from engine import palace_places as P, scene
from engine.anim import EASE, clamp
from engine.video import Episode
from episodes.cast_palace import add_count, add_pip

TITLE = "He stole the fairy godmother's wand 🪄🎃"
DESCRIPTION = """He stole the fairy godmother's wand 🪄🎃

The Count wants a golden carriage… Pip just wanted to help. 😅

What would YOU turn into a carriage? 👇
#shorts #cartoon #funny #magic #fairytale"""

PUMPKIN = (800, 1580)


def episode():
    ep = Episode(TITLE, [("HE STOLE THE", "#f6e7c1"), ("MAGIC WAND!", "#ffcc4d")], "throne_room",
                 music_seed=72, mood="villain", bpm=100, theme="storybook", max_len=15.0,
                 base_zoom=1.0, base_cy=1000.0)
    ep.cap_y = 1150  # keep the captions above the pumpkin gag
    add_count(ep, 330, 1)
    add_pip(ep, 610, 1, z=1)
    ep.say("count", "Behold! The magic wand!")
    ep.say("pip", "Ooh! Turn the pumpkin into a carriage!", wait=0.1)
    ep.say("count", "Hocus... pocus... CARRIAGE!")
    ep.say("pip", "Master... I'm the pumpkin now.", wait=0.6)
    ep.say("count", "Can you at least roll?", gap=0.05)
    return ep


def choreo(ep, L):
    c_, p_ = ep.chars["count"], ep.chars["pip"]
    from engine import euro
    for x in (40, 1000):
        ep.draw("front", lambda ctx, t, x=x: euro.glow(ctx, x, 1030, 260, color=(1.0, 0.8, 0.45), strength=0.4, t=t))
    ep.draw("back", lambda ctx, t: P.pumpkin(ctx, PUMPKIN[0], PUMPKIN[1], 0.75) if t < zap + 0.25 else None)

    # 0: wand up
    a, e = L[0]["start"], L[0]["end"]
    c_.expr(0, "evil")
    c_.pose(0, (160, 10), None, "fist", dur=0.3)
    ep.sound(0.4, "magic", 0.8)
    p_.expr(0, "happy")

    # 1: Pip points at the pumpkin, stepping right in front of it
    a, e = L[1]["start"], L[1]["end"]
    p_.walk_to(a, 720, speed=250)
    p_.pose(a + 0.4, (95, -5), None, "point", dur=0.2, swing=0)
    p_.turn(e - 0.2, -1)

    # 2: the spell... hits Pip
    a, e = L[2]["start"], L[2]["end"]
    c_.pose(a, (150, 0), None, "fist", dur=0.3)
    c_.pose(a + 0.8, (170, 10), None, "fist", dur=0.3)
    zap = e - 0.3
    c_.pose(zap - 0.15, (95, -10), None, "fist", dur=0.15)
    ep.sound(zap - 0.2, "magic", 1.0)
    ep.sound(zap, "poof", 1.0)
    ep.shake(zap, 1.0)
    p_["visible"].set(zap + 0.1, 0.0)
    c_.expr(zap + 0.1, "shocked")
    ep.punch(zap, 1.3, 640, 1200, hold=1.6)

    def zap_fx(ctx, t):
        if zap - 0.25 <= t < zap + 0.05:
            hx, hy = c_.joints["handF"]
            tx, ty = 720, 1400
            ctx.move_to(hx + 40, hy - 20)
            for k in range(1, 7):
                u = k / 6
                ctx.line_to(hx + 40 + (tx - hx - 40) * u + 18 * math.sin(k * 7 + t * 60), hy - 20 + (ty - hy + 20) * u)
            ctx.set_source_rgba(1, 0.85, 0.3, 0.9)
            ctx.set_line_width(10)
            ctx.stroke()
        P.poof(ctx, 720, 1420, (t - zap) / 0.8)
        if t >= zap + 0.1:
            hop = abs(math.sin((t - L[4]["end"]) * 9)) * 60 if t > L[4]["end"] else 0
            P.pumpkin(ctx, 720, PUMPKIN[1] - hop, 1.05, pip=True, t=t)
    ep.draw("front", zap_fx)

    def wand(ctx, t):
        hx, hy = c_.joints["handF"]
        P.wand(ctx, hx, hy - 10, -1.2 if t < zap - 0.2 else -0.15, glow=1.0 if t < 1.6 or zap - 0.4 < t < zap else 0.0, t=t)
    ep.draw("front", wand)

    a, e = L[3]["start"], L[3]["end"]
    c_.expr(a, "worried")
    c_.pose(a, (40, 60), None, "fist", dur=0.3)
    a, e = L[4]["start"], L[4]["end"]
    c_.expr(a, "smug")
    for k in range(3):
        ep.sound(e + 0.1 + k * 0.35, "boing", 0.5)
    ep.follow_at = e + 0.3
    ep.end = e + 1.5
