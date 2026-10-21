"""Stretch & Bruno 2 - Don't litter: leave only footprints."""
from engine import flat_places as F
from engine.anim import clamp
from engine.video import Episode
from episodes.cast_flat import add_bruno, add_stretch

TITLE = "Littering in the forest? Bruno says NO 🐻"
DESCRIPTION = """Littering in the forest? Bruno says NO 🐻🌲

Stretch tosses his juice can… right onto a bear's head.
✅ Keep your trash with you
✅ Put it in the bin
✅ Leave only footprints

Would you have picked it up? 👇
#shorts #nature #environment #cartoon #funny"""

BIN = (985, 1370)


def episode():
    ep = Episode(TITLE, [("LITTER IN", "#ffffff"), ("THE FOREST?", "#ffd166")], "forest_camp",
                 music_seed=62, mood=None, theme="flat", max_len=10.0, ambience="forest", hook_end=1.4)
    add_stretch(ep, 520, 1)
    add_bruno(ep, 170, 1)
    ep.say("stretch", "Done with my juice!")
    ep.say("bruno", "Hey! This forest is my home!", wait=0.5)
    ep.say("stretch", "Oops! Sorry, roommate.")
    return ep


def choreo(ep, L):
    s_, b_ = ep.chars["stretch"], ep.chars["bruno"]
    a, e = L[0]["start"], L[0]["end"]
    s_.expr(0, "happy")
    s_.reach(0, "F", "mouth", 0.01, hand="hold")
    toss = e - 0.1
    s_.reach(toss, "F", None, 0.15)
    s_.pose(toss, (-60, 20), None, "open", dur=0.15)
    hit = toss + 0.55
    ep.sound(hit, "hit", 0.8)
    ep.sound(hit + 0.05, "clink", 0.7)
    b_.expr(hit, "pain")
    ep.shake(hit, 0.7)
    b_["sqy"].to(hit, hit + 0.06, 0.9, "out")
    b_["sqy"].to(hit + 0.06, hit + 0.25, 1.0, "back")

    a, e = L[1]["start"], L[1]["end"]
    b_.expr(a, "stern")
    b_.pose(a, (150, 30), None, "hold", dur=0.2, swing=0)
    s_.turn(a, -1)
    s_.expr(a, "shocked")
    ep.punch(a, 1.2, 330, 1200, hold=e - a - 0.2)

    a, e = L[2]["start"], L[2]["end"]
    s_.expr(a, "worried")
    give = a + 0.1
    b_.pose(give, (80, 20), None, "hold", dur=0.2)
    s_.reach(give, "F", (330, 1180), 0.25, hand="hold")
    s_.reach(give + 0.35, "F", None, 0.2)
    s_.turn(give + 0.4, 1)
    at_bin = s_.walk_to(give + 0.45, 860, speed=520)
    s_.reach(at_bin, "F", (BIN[0] - 10, BIN[1] - 40), 0.2, hand="open")
    ep.sound(at_bin + 0.2, "clank", 0.8)
    b_.expr(at_bin + 0.2, "happy")
    s_.expr(at_bin + 0.2, "happy")
    b_.rest(give + 0.3)
    end = max(e, at_bin + 0.3)
    ep.sound(end, "ding", 0.6)
    ep.draw("ui", lambda ctx, t: F.lesson_card(ctx, t, end + 0.3, "Leave only footprints.", "star"))
    ep.end = end + 1.6

    def can(ctx, t):
        if t < toss:
            hx, hy = s_.joints["handF"]
            F.can(ctx, hx + 8, hy - 20, 0.2)
        elif t < hit:
            u = (t - toss) / (hit - toss)
            sx, sy = 520 - 40, 1000
            tx, ty = b_.joints["head"][0], b_.joints["head"][1] - 90
            F.can(ctx, sx + (tx - sx) * u, sy + (ty - sy) * u - 220 * 4 * u * (1 - u), u * 12)
        elif t < give + 0.2:
            hx, hy = b_.joints["handF"] if t > L[1]["start"] else (b_.joints["head"][0] + 60, 1540)
            F.can(ctx, hx, hy - 20, 0.0 if t > L[1]["start"] else 1.57)
        elif t < at_bin + 0.15:
            hx, hy = s_.joints["handF"]
            F.can(ctx, hx + 8, hy - 20, 0.2)
        elif t < at_bin + 0.35:
            F.can(ctx, BIN[0], BIN[1] - 30 + 120 * clamp((t - at_bin - 0.15) / 0.2), 0.3)
    ep.draw("front", can)
