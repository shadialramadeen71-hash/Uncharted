"""Faris & Puff 3 - Hot sand burns feet: wear sandals (beach)."""
from engine import flat_places as F, scene, sunny_places as S
from engine.anim import EASE, clamp
from engine.video import Episode
from episodes.cast_sunny import add_faris, add_puff

TITLE = "Is the sand… LAVA?! 🏖️🔥"
DESCRIPTION = """Is the sand… LAVA?! 🏖️🔥

Puff learns the hard way. Faris to the rescue:
✅ Hot sand (and pavement) can burn bare feet
✅ Always wear sandals at the beach
✅ Too hot for your hand = too hot for paws

Tag your beach buddy 👇
#shorts #summer #beach #cartoon #funny"""


def episode():
    ep = Episode(TITLE, [("HOT SAND", "#ffffff"), ("OR LAVA?!", "#ffd166")], "beach",
                 music_seed=83, mood="bouncy", bpm=128, theme="flat", max_len=10.0, ambience="beach",
                 hook_end=1.4, base_zoom=1.0, base_cy=1000.0)
    add_faris(ep, 330, 1)
    add_puff(ep, 760, -1)
    ep.say("puff", "Ow, ow! The sand is LAVA!")
    ep.say("faris", "Hot sand burns feet. Always wear sandals!", wait=0.1)
    ep.say("puff", "Fashion AND safety!", wait=0.3)
    return ep


def choreo(ep, L):
    f_, p_ = ep.chars["faris"], ep.chars["puff"]
    a, e = L[0]["start"], L[0]["end"]
    p_.expr(0, "pain")
    p_.pose(0, (150, 30), (-150, 30), "open", "open", dur=0.01, swing=0)
    hops = []
    t = 0.1
    while t < L[1]["end"]:
        p_.hop(t, 70, 0.32)
        hops.append(t)
        ep.sound(t, "sizzle", 0.25)
        t += 0.42
    ep.draw("front", lambda ctx, t: S.heat_waves(ctx, p_.joints["chest"][0], 1550, t, 3, 0.6) if t < L[1]["end"] else None)
    f_.expr(0, "worried")

    a, e = L[1]["start"], L[1]["end"]
    f_.expr(a, "happy")
    toss = a + (e - a) * 0.6
    f_.pose(toss - 0.2, (150, 20), None, "open", dur=0.2)
    f_.pose(toss + 0.2, (5, 12), None, "relaxed", dur=0.3)
    land = toss + 0.6
    ep.sound(land, "pop", 0.7)

    def sandals(ctx, t):
        if t < toss:
            return
        x0 = p_.tr["x"].at(t)
        u = clamp((t - toss) / (land - toss))
        for k, dx in enumerate((-22, 26)):
            sx = 420 + (x0 + dx - 420) * u
            sy = 1250 + (1560 - 1250) * u - 300 * 4 * u * (1 - u) + p_.tr["y"].at(t) * (1 if u >= 1 else 0)
            S.flip_flop(ctx, sx, sy, 0.9, "#06d6a0" if k == 0 else "#ef476f")
    ep.draw("front", sandals)

    a, e = L[2]["start"], L[2]["end"]
    p_.expr(land, "happy")
    p_.rest(land)
    p_.pose(a, (40, 50), None, "thumbsup", dur=0.2)
    p_["tilt"].to(a, a + 0.3, 10.0)
    ep.sound(a, "sparkle", 0.6)
    ep.draw("front", lambda ctx, t: scene.sparkles(ctx, p_.joints["head"][0], p_.joints["head"][1], t, 120)
            if t > a else None)
    ep.draw("ui", lambda ctx, t: F.lesson_card(ctx, t, e + 0.3, "Hot sand burns. Wear sandals.", "star"))
    ep.end = e + 1.5
