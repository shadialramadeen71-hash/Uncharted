"""Faris & Puff 1 - Drink water before you feel thirsty (desert)."""
from engine import flat_places as F, scene, sunny_places as S
from engine.anim import Track
from engine.video import Episode
from episodes.cast_sunny import add_faris, add_puff

TITLE = "A polar bear in the desert?! 🐻‍❄️☀️"
DESCRIPTION = """A polar bear in the desert?! 🐻‍❄️☀️

Puff is literally melting… Faris has the fix:
✅ Drink water BEFORE you feel thirsty
✅ Sip a little, all day long
✅ Extra water on hot days

Do you drink enough water? Be honest 👇
#shorts #health #summer #cartoon #funny"""


def episode():
    ep = Episode(TITLE, [("POLAR BEAR", "#ffffff"), ("IN THE DESERT?!", "#ffd166")], "desert",
                 music_seed=81, mood="bouncy", bpm=122, theme="flat", max_len=10.0, ambience="desert",
                 hook_end=1.4, base_zoom=1.0, base_cy=1000.0)
    add_faris(ep, 330, 1)
    add_puff(ep, 760, -1)
    ep.say("puff", "Faris... I'm melting!")
    ep.say("faris", "Drink water before you're thirsty!")
    ep.say("puff", "Ahh! Polar bear restored!", wait=0.5)
    return ep


def choreo(ep, L):
    f_, p_ = ep.chars["faris"], ep.chars["puff"]
    melt = Track(30.0)
    p_.expr(0, "worried")
    p_["sqy"].key(0, 0.9)
    p_["sqx"].key(0, 1.08)
    p_["lean"].key(0, -6.0)
    melt.key(0.0, 30.0)
    melt.key(L[0]["end"], 70.0)
    f_.expr(0, "neutral")
    ep.draw("back", lambda ctx, t: S.puddle(ctx, 760, 1566, melt.at(t)))
    ep.draw("front", lambda ctx, t: scene.sweat(ctx, p_.joints["head"][0] + 50, p_.joints["head"][1] - 80, t)
            if t < L[2]["start"] else None)
    ep.draw("front", lambda ctx, t: S.heat_waves(ctx, 760, 1480, t, 3, 0.4))

    a, e = L[1]["start"], L[1]["end"]
    f_.expr(a, "happy")
    give = a + 0.5
    f_.reach(give, "F", (640, 1330), 0.35, hand="hold")
    p_.reach(give + 0.3, "F", (650, 1340), 0.3, hand="hold")
    f_.reach(e - 0.4, "F", None, 0.3)
    drink = e
    p_.reach(drink, "F", "mouth", 0.3, hand="hold")
    ep.sound(drink + 0.25, "glug", 1.0)
    p_["sqy"].to(drink + 0.4, drink + 0.7, 1.0, "back")
    p_["sqx"].to(drink + 0.4, drink + 0.7, 1.0, "back")
    p_["lean"].to(drink + 0.4, drink + 0.7, 0.0)
    melt.key(drink + 0.4, 70.0)
    melt.key(drink + 1.0, 0.0)

    a, e = L[2]["start"], L[2]["end"]
    p_.expr(a, "happy")
    p_.reach(a + 0.2, "F", None, 0.2)
    p_.pose(a + 0.2, (150, 20), None, "open", dur=0.2)
    p_.hop(a + 0.2, 60, 0.35)
    ep.sound(a + 0.2, "sparkle", 0.6)
    ep.draw("ui", lambda ctx, t: F.lesson_card(ctx, t, e + 0.3, "Sip water all day. Don't wait for thirst.", "star"))
    ep.end = e + 1.5

    def water(ctx, t):
        if t < give + 0.45:
            hx, hy = f_.joints["handF"]
            S.bottle(ctx, hx + 6, hy - 10)
        elif t < a + 0.3:
            hx, hy = p_.joints["handF"]
            lvl = 1.0 if t < drink + 0.2 else max(0.15, 1 - (t - drink - 0.2))
            S.bottle(ctx, hx, hy - 10, -1.2 if t > drink + 0.1 else 0.0, lvl)
    ep.draw("front", water)
