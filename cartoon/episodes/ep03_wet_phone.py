"""Episode 3 - Phone fell in water? Don't use rice."""
from engine import scene
from engine.anim import clamp
from engine.video import Episode
from episodes.cast import add_lily, add_max

TITLE = "Phone fell in water? NOT rice!"
DESCRIPTION = ("Max texts while walking... and feeds his phone to the fish. Rice is a myth: power it off, wipe it, "
               "and let it air dry port-down. #shorts #lifehacks #phone #cartoon #funny")

BOWL = (600, 1240)


def episode():
    ep = Episode(TITLE, [("PHONE FELL IN WATER?", "#4da3ff"), ("DON'T USE RICE!", "#ffd21f")], "living_room",
                 music_seed=37, bpm=122)
    add_max(ep, -180, 1)
    add_lily(ep, 1320, -1)
    ep.say("max", "Texting and walking. I'm a pro.")
    ep.say("max", "NOOO! My phone!", wait=0.8, fx="shout")
    ep.say("max", "Rice! Rice fixes everything!")
    ep.say("lily", "Nope! Rice leaves dust and grains inside.", wait=0.2)
    ep.say("lily", "Turn it off, wipe it, and air dry it, port down.")
    ep.say("max", "So... can I eat the rice?", gap=0.1)
    ep.say("lily", "Sure.", gap=0.1)
    return ep


def choreo(ep, L):
    m, l = ep.chars["max"], ep.chars["lily"]
    s = {"bump": None}

    # 0: strolling in while texting
    a, e = L[0]["start"], L[0]["end"]
    m.expr(0, "smug")
    m.pose(0, (35, 85), None, "hold", None, dur=0.01, swing=0.0)
    m["swing"].key(0, 0.0)
    m["tilt"].key(0, -10.0)
    m["look"].key(0, (0.7, 0.9))
    bump = m.walk_to(0.0, 420, speed=210, ease="linear") + 0.0
    bump = max(bump, e + 0.1)
    s["bump"] = bump
    ep.sound(bump, "thud", 1.0)
    ep.shake(bump, 1.0)
    m.expr(bump, "shocked")
    m["tilt"].to(bump, bump + 0.15, 0.0)
    m["look"].to(bump, bump + 0.15, (1.0, 0.0))
    m.pose(bump, (150, 20), (-150, 20), "open", "open", dur=0.2)
    land = bump + 0.5
    ep.sound(land, "splash", 1.0)
    ep.punch(land - 0.1, 1.45, BOWL[0], BOWL[1] - 120, hold=0.7)

    def draw_phone(ctx, t):
        if t < bump:
            hx, hy = m.joints["handF"]
            scene.phone(ctx, hx + 4, hy - 26, 0.15, 0.9)
        elif t < land:
            u = (t - bump) / (land - bump)
            sx, sy = m.joints["handF"] if u < 0.05 else s.setdefault("from", m.joints["handF"])
            x = sx + (BOWL[0] + 20 - sx) * u
            y = sy + (BOWL[1] - sy) * u - 260 * 4 * u * (1 - u)
            scene.phone(ctx, x, y, u * 9, 0.9)
        elif t >= s["grab"] and t < L[2]["start"]:
            hx, hy = m.joints["handF"]
            scene.phone(ctx, hx + 4, hy - 26, 0.15, 0.9, lit=0.0)
            scene.sweat(ctx, hx + 20, hy - 70, t)
    ep.draw("front", draw_phone)
    fish = {"mood": "happy"}
    ep.draw("back", lambda ctx, t, a=a, e=e: scene.fishbowl(ctx, BOWL[0], BOWL[1], t,
                                                   phone_in=1.0 if land <= t < s["grab"] else 0.0,
                                                   fish_mood="angry" if t >= land else "happy"))
    ep.draw("front", lambda ctx, t, a=a, e=e: scene.splash(ctx, BOWL[0], BOWL[1] - 60, (t - land) / 0.7))

    # 1: NOOO -> grab it back
    a, e = L[1]["start"], L[1]["end"]
    m.expr(a, "worried")
    ep.punch(a, 1.3, 420, 1000, hold=0.6)
    s["grab"] = e - 0.15
    m.reach(a + 0.2, "F", (BOWL[0] - 20, BOWL[1] - 10), 0.35, hand="hold")
    m.reach(e - 0.15, "F", None, 0.3)
    m.pose(e - 0.15, (35, 85), (-8, 12), "hold", "relaxed", dur=0.3)
    ep.sound(e - 0.15, "splash", 0.4)

    # 2: the rice bag
    a, e = L[2]["start"], L[2]["end"]
    ep.sound(a, "pop", 0.9)
    ep.sound(a + 0.2, "rustle", 0.8)
    m.expr(a, "silly")
    m.pose(a, (50, 95), (20, 90), "hold", "hold", dur=0.2)
    ep.draw("front", lambda ctx, t, a=a, e=e: scene.rice_bag(ctx, m.joints["chest"][0] + 30, m.joints["chest"][1] + 10,
                                                   -0.1, clamp((t - a) / 0.2) * 0.85) if a <= t < L[3]["start"] + 1.0 else None)
    ep.draw("front", lambda ctx, t, a=a, e=e: scene.sparkles(ctx, m.joints["chest"][0] + 30, m.joints["chest"][1], t, 120)
            if a <= t < e else None)

    # 3: Lily
    l.walk_to(L[2]["start"] + 0.4, 840, speed=420)
    a, e = L[3]["start"], L[3]["end"]
    ep.sound(a - 0.05, "scratch", 0.8)
    l.expr(a, "stern")
    l.pose(a, (95, -5), None, "point", dur=0.2, swing=0)
    m.expr(a, "shocked")
    m.rest(a + 1.0)
    ep.punch(a, 1.3, 720, 1020, hold=e - a - 0.3)
    ep.draw("front", lambda ctx, t, a=a, e=e: scene.stamp(ctx, m.joints["head"][0] + 20, m.joints["head"][1] - 230, (t - a) / 2.0, False) if a <= t <= a + 2.0 else None)

    # 4: the right way
    a, e = L[4]["start"], L[4]["end"]
    l.expr(a, "neutral")
    l.pose(a, (70, 30), None, "open", dur=0.3)
    l.pose(a + (e - a) * 0.5, (135, 25), None, "point", dur=0.3)
    m.expr(a, "neutral")
    m["look"].to(a, a + 0.2, (1, -0.2))
    ep.tip = dict(t0=e - 0.3, title="WET PHONE?", color=(0.2, 0.55, 0.95), items=[
        (False, "Don't put it in rice"), (True, "Power off + wipe dry"), (True, "Air dry, port down")])
    ep.sound(e - 0.3, "whoosh", 0.7)

    # 5-6: punchline
    a, e = L[5]["start"], L[5]["end"]
    m.expr(a, "silly")
    m["tilt"].to(a, a + 0.3, 12)
    m.pose(a, (40, 120), None, "point", dur=0.25)
    a, e = L[6]["start"], L[6]["end"]
    l.expr(a, "smug")
    l.rest(a)
    m.expr(e, "happy")
    m.hop(e, 60, 0.32)
    ep.sound(e + 0.32, "boing", 0.5)
    ep.follow_at = e - 0.2
    ep.end = e + 1.3
