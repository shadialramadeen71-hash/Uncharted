"""Stretch & Bruno 1 - Phone down, look both ways before you cross."""
from engine import flat_places as F, scene
from engine.video import Episode
from episodes.cast_flat import add_bruno, add_stretch

TITLE = "Texting while crossing? Watch this 🐻"
DESCRIPTION = """Texting while crossing? Watch this 🐻📱

Stretch almost walks into traffic… Bruno the bear saves the day:
✅ Phone down
✅ Look left, look right
✅ Then cross

Tag a friend who texts while walking 👇
#shorts #safety #kindness #cartoon #funny"""


def episode():
    ep = Episode(TITLE, [("TEXTING WHILE", "#ffffff"), ("CROSSING?", "#ffd166")], "city_crosswalk",
                 music_seed=61, mood=None, theme="flat", max_len=10.0, ambience="city", hook_end=1.4)
    add_stretch(ep, 120, 1)
    add_bruno(ep, -120, 1)
    ep.say("stretch", "Ooh, a new message!")
    ep.say("bruno", "Stop! Phone down!", gap=0.5)
    ep.say("bruno", "Look left, look right, then cross.")
    ep.say("stretch", "Got it, buddy!", gap=0.05)
    return ep


def choreo(ep, L):
    s_, b_ = ep.chars["stretch"], ep.chars["bruno"]
    s_.expr(0, "happy")
    s_.pose(0, (40, 95), None, "hold", None, dur=0.01, swing=0.0)
    s_["tilt"].key(0, -14.0)
    s_["look"].key(0, (0.6, 0.9))
    stop = s_.walk_to(0.0, 520, speed=280, ease="linear")
    b_.walk_to(0.1, 190, speed=230, ease="linear")

    a, e = L[1]["start"], L[1]["end"]
    b_.expr(a, "stern")
    b_.pose(a, (95, -5), None, "point", dur=0.2, swing=0)
    s_.expr(a, "shocked")
    s_["tilt"].to(a, a + 0.15, 0.0)
    s_["look"].to(a, a + 0.15, (1.0, 0.0))
    s_.hop(a + 0.05, 40, 0.3)
    car_t = e - 0.25
    ep.sound(car_t - 0.6, "car", 1.0)
    ep.sound(car_t + 0.1, "honk", 0.7)
    ep.draw("front", lambda ctx, t: F.car(ctx, (t - car_t + 0.35) / 0.75))
    ep.shake(car_t + 0.3, 0.8)
    ep.draw("back", lambda ctx, t: F.traffic_light(ctx, red=t < L[3]["start"]))

    a, e = L[2]["start"], L[2]["end"]
    b_.expr(a, "neutral")
    b_.pose(a, (70, 30), None, "open", dur=0.25)
    s_["look"].to(a + 0.1, a + 0.4, (-1.0, 0.0))
    s_["look"].to(a + 0.8, a + 1.1, (1.0, 0.0))
    s_.pose(a, (20, 40), None, "relaxed", dur=0.3)

    a, e = L[3]["start"], L[3]["end"]
    s_.expr(a, "happy")
    s_.pose(a, (40, 50), None, "thumbsup", dur=0.2)
    b_.expr(a, "happy")
    ep.sound(e, "ding", 0.6)
    ep.draw("ui", lambda ctx, t: F.lesson_card(ctx, t, e + 0.3, "Phone down. Look both ways.", "star"))
    ep.end = e + 1.6

    def phone(ctx, t):
        if t < L[1]["start"] + 0.1:
            hx, hy = s_.joints["handF"]
            scene.phone(ctx, hx + 6, hy - 24, 0.2, 0.75)
    ep.draw("front", phone)
