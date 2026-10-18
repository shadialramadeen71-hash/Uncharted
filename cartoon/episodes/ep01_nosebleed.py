"""Episode 1 - Nosebleed: lean FORWARD, don't tilt your head back."""
from engine import scene
from engine.video import Episode
from episodes.cast import add_lily, add_max

TITLE = "Nosebleed? Stop tilting your head back!"
DESCRIPTION = ("Max gets a nosebleed and does the classic mistake. Lean forward and pinch the soft part of "
               "your nose for 10 minutes. #shorts #lifehacks #firstaid #cartoon #funny")


def episode():
    ep = Episode(TITLE, [("NOSEBLEED?", "#ff4d4d"), ("STOP DOING THIS!", "#ffd21f")], "living_room",
                 music_seed=11, bpm=126)
    add_max(ep, 340, 1)
    add_lily(ep, 1300, -1)
    ep.say("max", "Ah... ah... ACHOO!")
    ep.say("max", "Oh no, a nosebleed! Quick, head back!")
    ep.say("lily", "STOP! Never tilt your head back!", wait=0.5)
    ep.say("max", "Why not?", fx="gargle")
    ep.say("lily", "The blood runs down your throat. Lean forward and pinch the soft part for ten minutes.")
    ep.say("max", "Like dis?", fx="nasal")
    ep.say("lily", "Perfect!")
    ep.say("max", "I sound like a duck.", fx="nasal", gap=0.1)
    return ep


def choreo(ep, L):
    m, l = ep.chars["max"], ep.chars["lily"]
    # 0: the sneeze
    a, e = L[0]["start"], L[0]["end"]
    m.expr(0, "worried")
    m["tilt"].to(a, e - 0.45, 18)
    m["lean"].to(a, e - 0.45, -8)
    m.pose(a, (40, 60), (-30, 40), "open", "open", dur=0.5, ease="inout")
    sneeze = e - 0.35
    m["tilt"].to(sneeze, sneeze + 0.08, -16, "out")
    m["lean"].to(sneeze, sneeze + 0.08, 16, "out")
    m.expr(sneeze, "pain")
    ep.shake(sneeze, 1.2)
    ep.sound(sneeze, "hit", 0.6)
    m["bleed"].to(sneeze + 0.1, sneeze + 0.5, 1.0)
    m.rest(sneeze + 0.2)
    m["tilt"].to(e + 0.05, e + 0.3, 0)
    m["lean"].to(e + 0.05, e + 0.3, 0)

    # 1: panic + head back
    a, e = L[1]["start"], L[1]["end"]
    m.expr(a, "shocked")
    m.pose(a, (150, 30), (-150, 30), "open", "open", dur=0.3)
    ep.punch(a, 1.4, 360, 1000, hold=0.7)
    ep.sound(a, "pop", 0.8)
    back = a + (e - a) * 0.6
    m["tilt"].to(back, back + 0.3, 58, "back")
    m["lean"].to(back, back + 0.3, -20, "back")
    m.pose(back, (60, 70), (-40, 60), "relaxed", "relaxed", dur=0.3)
    m["look"].to(back, back + 0.2, (0.2, -1.0))
    ep.sound(back, "boing", 0.6)

    # 2: Lily storms in
    l.walk_to(L[1]["end"] - 0.45, 790, speed=480)
    a, e = L[2]["start"], L[2]["end"]
    ep.sound(a - 0.05, "scratch", 0.9)
    l.expr(a, "stern")
    l.pose(a, (95, -5), None, "point", dur=0.2, swing=0)
    ep.punch(a, 1.35, 740, 1020, hold=e - a - 0.3)
    m["look"].to(a, a + 0.2, (1.0, -0.6))
    m.expr(a, "worried")
    ep.draw("front", lambda ctx, t, a=a, e=e: scene.stamp(ctx, m.joints["head"][0] - 40, m.joints["head"][1] - 240,
                                                      (t - a) / 2.2, False) if a <= t <= a + 2.2 else None)

    # 3: "Why not?" (gargling)
    a, e = L[3]["start"], L[3]["end"]
    l.rest(a - 0.1)
    l.expr(a, "neutral")
    m.pose(a, (70, 40), None, "open", dur=0.25)

    # 4: the explanation, Max follows along
    a, e = L[4]["start"], L[4]["end"]
    l.pose(a, (70, 30), None, "open", dur=0.3)
    l.expr(a, "neutral")
    fwd = a + (e - a) * 0.38
    m["tilt"].to(fwd, fwd + 0.4, -12)
    m["lean"].to(fwd, fwd + 0.4, 16)
    m["look"].to(fwd, fwd + 0.3, (0.5, 0.6))
    m.expr(fwd, "neutral")
    l.pose(fwd, (135, 25), None, "point", dur=0.3)
    pinch = a + (e - a) * 0.66
    m.reach(pinch, "F", "nose", 0.35, hand="pinch")
    m.pose(pinch, None, (-10, 20), None, "relaxed")
    ep.sound(pinch + 0.3, "pop", 0.5)
    ep.tip = dict(t0=e - 0.2, title="NOSEBLEED?", items=[
        (False, "Don't tilt head back"), (True, "Sit + lean FORWARD"), (True, "Pinch soft part 10 min")])
    ep.sound(e - 0.2, "whoosh", 0.7)

    # 5-7: punchline
    a = L[5]["start"]
    m["bleed"].to(a, a + 1.5, 0.0)
    m.expr(a, "silly")
    m["look"].to(a, a + 0.2, (1, 0))
    a, e = L[6]["start"], L[6]["end"]
    l.expr(a, "happy")
    l.pose(a, (40, 50), None, "thumbsup", dur=0.25)
    l.hop(a, 40, 0.3)
    ep.sound(a, "sparkle", 0.8)
    ep.draw("front", lambda ctx, t, a=a, e=e: scene.sparkles(ctx, l.joints["head"][0], l.joints["head"][1] - 20, t)
            if a <= t <= a + 1.4 else None)
    a, e = L[7]["start"], L[7]["end"]
    m.expr(a, "relieved")
    l.expr(e - 0.2, "smug")
    ep.follow_at = e - 0.4
    ep.end = e + 1.4
