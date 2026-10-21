"""Stretch & Bruno 3 - Sharing makes it better."""
from engine import flat_places as F
from engine.video import Episode
from episodes.cast_flat import add_bruno, add_stretch

TITLE = "Forgot your lunch? Bruno shares 🐻🥪"
DESCRIPTION = """Forgot your lunch? Bruno shares 🐻🥪

Stretch's stomach is growling… and a little bear knows what to do.
❤️ Sharing makes everything taste better.

Who would you share your lunch with? 👇
#shorts #kindness #friendship #cartoon #wholesome"""


def episode():
    ep = Episode(TITLE, [("FORGOT YOUR", "#ffffff"), ("LUNCH?", "#ffd166")], "picnic_park",
                 music_seed=63, mood=None, theme="flat", max_len=10.0, ambience="park", hook_end=1.4)
    add_stretch(ep, 440, 1)
    add_bruno(ep, 850, -1)
    ep.say("stretch", "I forgot my lunch...", wait=0.6)
    ep.say("bruno", "Here. Half is yours.")
    ep.say("stretch", "Mmm! Even tastier!", wait=0.3)
    ep.say("bruno", "Sharing does that.")
    return ep


def choreo(ep, L):
    s_, b_ = ep.chars["stretch"], ep.chars["bruno"]
    ep.sound(0.15, "growl", 1.0)
    s_.expr(0, "worried")
    s_["sqx"].key(0.15, 1.0)
    s_["sqx"].to(0.2, 0.3, 0.94)
    s_["sqx"].to(0.3, 0.5, 1.0, "back")
    s_.pose(0, (60, 70), (40, 80), "open", "open", dur=0.01, swing=0)
    b_.expr(0, "neutral")
    b_.reach(0, "F", "mouth", 0.01, hand="hold")

    a, e = L[1]["start"], L[1]["end"]
    b_.reach(a, "F", None, 0.2)
    b_.pose(a, (70, 30), (60, 40), "hold", "hold", dur=0.2)
    split = a + 0.4
    ep.sound(split, "pop", 0.6)
    b_.expr(split, "happy")
    give = e - 0.1
    s_.reach(give, "F", (690, 1250), 0.25, hand="hold")
    s_.expr(give, "happy")

    a, e = L[2]["start"], L[2]["end"]
    s_.reach(a - 0.3, "F", "mouth", 0.25, hand="hold")
    b_.reach(a - 0.3, "F", "mouth", 0.25, hand="hold")
    ep.sound(a - 0.05, "chew", 0.8)
    s_.expr(a, "relieved")
    a, e = L[3]["start"], L[3]["end"]
    s_.expr(a, "happy")
    b_.expr(a, "happy")
    s_.reach(a, "F", None, 0.3)
    ep.sound(e, "sparkle", 0.6)
    ep.draw("ui", lambda ctx, t: F.lesson_card(ctx, t, e + 0.3, "Sharing makes it better.", "heart"))
    ep.end = e + 1.6

    def food(ctx, t):
        bx, by = b_.joints["handF"]
        if t < split:
            F.sandwich(ctx, bx - 10, by - 10)
            return
        F.sandwich(ctx, bx - 4, by - 10, half=True)
        if t < give + 0.2:
            bx2, by2 = b_.joints["handB"]
            F.sandwich(ctx, bx2 - 4, by2 - 10, half=True)
        else:
            sx, sy = s_.joints["handF"]
            F.sandwich(ctx, sx + 6, sy - 10, half=True)
    ep.draw("front", food)
