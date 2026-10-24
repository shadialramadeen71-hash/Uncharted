"""Faris & Puff 2 - Never wait in a parked car (car park)."""
from engine import flat_places as F, sunny_places as S
from engine.video import Episode
from episodes.cast_sunny import add_faris, add_puff

TITLE = "Waiting in a hot car? NEVER 🚗🔥"
DESCRIPTION = """Waiting in a hot car? NEVER 🚗🔥

Puff wants to wait in the car… Faris stops him just in time:
❌ Never wait in a parked car in the heat
❌ Never leave kids or pets inside — not even for a minute
✅ Wait in the shade (or come along!)

Share this so nobody forgets 👇
#shorts #safety #summer #cartoon #parenting"""

CAR = (790, 1560)


def episode():
    ep = Episode(TITLE, [("WAIT IN A", "#ffffff"), ("HOT CAR?!", "#ffd166")], "car_park",
                 music_seed=82, mood="bouncy", bpm=118, theme="flat", max_len=10.0, ambience="city",
                 hook_end=1.4, base_zoom=1.0, base_cy=1000.0)
    add_faris(ep, 260, 1)
    add_puff(ep, 470, 1)
    ep.say("puff", "It's so hot! I'll wait in the car.")
    ep.say("faris", "Never! A parked car gets dangerously hot, fast.", wait=0.1)
    ep.say("puff", "Shade it is!", wait=0.1)
    return ep


def choreo(ep, L):
    f_, p_ = ep.chars["faris"], ep.chars["puff"]
    ep.draw("back", lambda ctx, t: S.parked_car(ctx, CAR[0], CAR[1], t))
    p_.expr(0, "happy")
    p_.walk_to(0.2, 600, speed=200)

    a, e = L[1]["start"], L[1]["end"]
    f_.expr(a, "shocked")
    stop = f_.walk_to(a - 0.1, 440, speed=420)
    f_.reach(stop, "F", (600, 1400), 0.25, hand="open")
    p_.turn(a, -1)
    p_.expr(a, "shocked")
    ep.sound(a + 0.3, "sizzle", 0.6)
    ep.draw("front", lambda ctx, t, a=a: S.thermometer(ctx, CAR[0] - 60, 960, (t - a - 0.4) / 0.9) if t > a + 0.4 else None)
    f_.expr(a + 0.5, "stern")

    a, e = L[2]["start"], L[2]["end"]
    f_.reach(a, "F", None, 0.2)
    p_.expr(a, "happy")
    p_.pose(a, (40, 50), None, "thumbsup", dur=0.2)
    f_.turn(a + 0.1, -1)
    f_.walk_to(a + 0.2, 140, speed=380)
    p_.walk_to(a + 0.3, 250, speed=380)
    ep.draw("ui", lambda ctx, t: F.lesson_card(ctx, t, e + 0.3, "Never leave kids or pets in a parked car.", "heart"))
    ep.end = e + 1.6
