"""Episode 2 - Burned your hand? Cool running water for 20 minutes, never ice."""
import math

from engine import scene
from engine.video import Episode
from episodes.cast import add_lily, add_max

TITLE = "Burned your hand? NOT ice!"
DESCRIPTION = ("Max burns his hand making pancakes and runs for the ice. Lily knows better: cool running water "
               "for 20 minutes. #shorts #lifehacks #firstaid #cartoon #funny")

PAN = (945, 1168)
TAP = (548, 1062)


def episode():
    ep = Episode(TITLE, [("BURNED YOUR HAND?", "#ff4d4d"), ("DON'T USE ICE!", "#ffd21f")], "kitchen",
                 music_seed=23, bpm=128)
    add_max(ep, 640, 1)
    add_lily(ep, 1320, -1)
    ep.say("max", "Pancake time!")
    ep.say("max", "OUCH! Hot hot hot! Ice!", wait=0.6, fx="shout")
    ep.say("lily", "No ice! It can hurt your skin more.", wait=0.2)
    ep.say("lily", "Cool running water, twenty minutes.")
    ep.say("max", "Ahhh... so much better.", wait=0.3)
    ep.say("max", "Twenty minutes? My pancake!", gap=0.1)
    return ep


def choreo(ep, L):
    m, l = ep.chars["max"], ep.chars["lily"]
    st = {}

    ep.draw("back", lambda ctx, t: scene.pan(ctx, PAN[0], PAN[1], math.pi))
    ep.draw("back", lambda ctx, t: scene.steam(ctx, PAN[0], PAN[1] - 30, t))

    # 0: reaching for the pan
    a, e = L[0]["start"], L[0]["end"]
    m.expr(a, "happy")
    m["look"].key(a, (0.6, 0.4))
    touch = e + 0.15
    m.reach(touch - 0.45, "F", (PAN[0] - 80, PAN[1] - 6), 0.45, hand="open")
    ep.sound(touch, "sizzle", 1.0)

    # 1: OUCH -> hop -> sprint to the fridge
    ouch = touch + 0.12
    m.expr(ouch, "pain")
    m.reach(ouch, "F", None, 0.12)
    m.hop(ouch, 120, 0.42)
    ep.shake(ouch, 1.6)
    ep.sound(ouch, "hit", 0.8)
    ep.punch(ouch, 1.45, 760, 980, hold=0.5)
    for k in range(10):  # shaking the burnt hand
        m["armF"].key(ouch + 0.1 + k * 0.09, (120.0, 20.0) if k % 2 else (80.0, 70.0), "inout")
    m["handF"].set(ouch + 0.1, "open")
    ep.draw("front", lambda ctx, t, a=a, e=e: scene.burst(ctx, 820, 760, (t - ouch) / 1.0, "OUCH!") if ouch <= t <= ouch + 1.0 else None)
    a, e = L[1]["start"], L[1]["end"]
    run = a + (e - a) * 0.5
    m.expr(run, "worried")
    m.pose(run, (60, 80), (-40, 60), "open", "fist", dur=0.2, swing=1.4)
    arrive = m.walk_to(run, 330, speed=700)
    st["run"] = run
    ep.draw("back", lambda ctx, t, a=a, e=e: scene.speed_lines(ctx, m.joints["chest"][0] + 120, m.joints["chest"][1], t, -1)
            if run + 0.1 <= t <= arrive - 0.05 else None)
    ep.draw("front", lambda ctx, t, a=a, e=e: scene.sweat(ctx, m.joints["head"][0] + 60, m.joints["head"][1] - 110, t)
            if run <= t <= L[3]["start"] else None)

    # 2: Lily walks in
    l.walk_to(e - 0.5, 800, speed=460)
    a, e = L[2]["start"], L[2]["end"]
    ep.sound(a - 0.05, "scratch", 0.8)
    l.expr(a, "stern")
    l.pose(a, (95, -5), None, "point", dur=0.2, swing=0)
    m.turn(a + 0.1, 1)
    m.expr(a + 0.1, "shocked")
    m.rest(a + 0.1)
    ep.punch(a, 1.3, 600, 1020, hold=e - a - 0.3)
    ep.draw("front", lambda ctx, t, a=a, e=e: scene.stamp(ctx, m.joints["head"][0] + 20, m.joints["head"][1] - 230, (t - a) / 2.0, False) if a <= t <= a + 2.0 else None)

    # 3: point at the sink, tap on, Max walks over
    a, e = L[3]["start"], L[3]["end"]
    l.expr(a, "neutral")
    l.pose(a, (110, -10), None, "point", dur=0.25)
    tap_on = a + 0.3
    ep.sound(tap_on, "water", 0.8)
    ep.sound(tap_on + 2.3, "water", 0.8)
    ep.sound(tap_on + 4.6, "water", 0.6)
    ep.draw("back", lambda ctx, t, a=a, e=e: scene.water_stream(ctx, TAP[0], TAP[1], 1195, t, min(1.0, max(0.0, (t - tap_on) / 0.3))))
    m.expr(a, "worried")
    reach_t = m.walk_to(a + 0.2, 440, speed=330)
    m.turn(reach_t, 1)
    m.reach(reach_t, "F", (TAP[0] - 6, 1135), 0.35, hand="open")
    l.rest(e)

    # 4: relief
    a, e = L[4]["start"], L[4]["end"]
    m.expr(a, "relieved")
    m["lean"].to(a, a + 0.5, 8)
    ep.draw("front", lambda ctx, t, a=a, e=e: scene.sparkles(ctx, TAP[0], 1130, t, 70) if a <= t <= e + 0.5 else None)
    ep.tip = dict(t0=a, title="BURNED?", items=[
        (True, "Cool running water"), (True, "Keep it there 20 min"), (False, "No ice, no butter")])
    ep.sound(a, "whoosh", 0.7)
    l.expr(a, "happy")
    l.pose(a + 0.2, (40, 50), None, "thumbsup", dur=0.25)

    # 5: punchline
    a, e = L[5]["start"], L[5]["end"]
    m.expr(a, "shocked")
    m["look"].to(a, a + 0.2, (1, -0.3))
    ep.punch(a + 0.6, 1.35, 800, 1080, hold=0.7)
    ep.sound(a + 0.6, "boing", 0.6)
    ep.draw("back", lambda ctx, t, a=a, e=e: [scene.steam(ctx, PAN[0] + dx, PAN[1] - 30, t * 1.3 + dx) for dx in (-50, 50)]
            if t >= a + 0.5 else None)
    l.expr(e - 0.3, "smug")
    ep.follow_at = e - 0.3
    ep.end = e + 1.3
