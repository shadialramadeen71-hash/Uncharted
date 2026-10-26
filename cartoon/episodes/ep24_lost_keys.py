"""Heroes 5 - The Keys (Batcave -> street -> funhouse)."""
from engine import noir_places as N
from engine.video import Episode
from episodes.cast_heroes import add_batman, add_joker, add_superman

TITLE = "Batman lost the Batmobile keys 🔑🦇"
DESCRIPTION = """Batman lost the Batmobile keys 🔑🦇

From the Batcave… to the bus stop… to a very suspicious funhouse.

Fan-made parody animation. Batman, Superman and the Joker are © DC.
#shorts #batman #superman #joker #animation"""


def episode():
    ep = Episode(TITLE, [("WHERE ARE", "#ffffff"), ("THE KEYS?!", "#ffcc1a")], "batcave",
                 music_seed=95, mood="noir", bpm=128, theme="noir", max_len=20.0, hook_end=1.6,
                 base_zoom=1.0, base_cy=1000.0)
    add_batman(ep, 640, -1)
    add_superman(ep, 380, 1)
    add_joker(ep, 540, 1)
    ep.say("batman", "Where are the Batmobile keys?", wait=0.2)
    ep.say("superman", "Taking the bus, Bruce?", wait=1.6)
    ep.say("batman", "...Not one word.")
    ep.say("superman", "Need a lift?")
    ep.say("batman", "Just this once.")
    ep.say("joker", "Looking for these, Batsy? Ha ha ha!", wait=1.8)
    return ep


def choreo(ep, L):
    b_, s_, j_ = ep.chars["batman"], ep.chars["superman"], ep.chars["joker"]
    s_["visible"].key(0, 0.0)
    j_["visible"].key(0, 0.0)

    # --- Batcave: patting the utility belt
    b_.expr(0, "worried")
    a, e = L[0]["start"], L[0]["end"]
    for k in range(6):
        b_["armF"].key(a + k * 0.25, (20.0, 40.0) if k % 2 else (10.0, 70.0))
        b_["armB"].key(a + k * 0.25, (10.0, 70.0) if k % 2 else (20.0, 40.0))
    b_["look"].to(a, a + 0.3, (-1.0, 0.3))
    b_["look"].to(e - 0.4, e - 0.1, (1.0, 0.3))
    b_.turn(e - 0.5, 1)

    # --- the bus stop
    c1 = e + 0.5
    ep.cut(c1, "gotham_street")
    b_["x"].set(c1, 760.0)
    b_.turn(c1, -1)
    b_.rest(c1)
    b_.pose(c1, (40, 120), (30, 120), "fist", "fist", dur=0.01, swing=0)  # arms crossed, grumpy
    b_.expr(c1, "stern")
    s_["visible"].set(c1, 1.0)
    s_["y"].key(c1, -1000.0)
    s_["rot"].key(c1, 60.0)
    s_.pose(c1, (170, 0), None, "fist", None, dur=0.01, swing=0)
    land = L[1]["start"] - 0.1
    s_["y"].key(land, 0.0, "out")
    s_["rot"].key(land, 0.0, "back")
    s_.rest(land)
    s_.expr(land, "happy")
    ep.sound(c1 + 0.2, "whoosh", 0.9)
    ep.sound(land, "thud", 0.6)
    a, e = L[2]["start"], L[2]["end"]
    ep.punch(a, 1.3, 700, 1000, hold=e - a - 0.2)
    a, e = L[3]["start"], L[3]["end"]
    s_.pose(a, (40, 50), None, "thumbsup", dur=0.2)
    a, e = L[4]["start"], L[4]["end"]
    b_.expr(a, "neutral")
    lift = e + 0.1
    s_.walk_to(a, 600, speed=420)
    s_.reach(lift - 0.2, "F", (700, 1150), 0.2, hand="fist")
    s_.pose(lift, (170, 0), None, "fist", dur=0.2)
    for c in (s_, b_):
        c["y"].to(lift, lift + 0.9, -1800.0, "in")
    b_.expr(lift, "shocked")
    ep.sound(lift, "whoosh", 1.0)

    # --- the funhouse twist
    c2 = L[5]["start"] - 1.0
    ep.cut(c2, "funhouse")
    b_["visible"].set(c2, 0.0)
    s_["visible"].set(c2, 0.0)
    j_["visible"].set(c2, 1.0)
    j_.expr(c2, "evil")
    j_.pose(c2, (150, 20), None, "hold", dur=0.01, swing=0)
    a, e = L[5]["start"], L[5]["end"]
    ep.sound(a, "jingle", 1.0)
    ep.sound(a + 0.8, "jingle", 0.8)
    ep.punch(a + 0.5, 1.25, 560, 950)
    ep.draw("front", lambda ctx, t: N.keys(ctx, j_.joints["handF"][0] + 4, j_.joints["handF"][1] - 30, t) if t >= c2 else None)
    ep.follow_at = e + 0.3
    ep.end = e + 1.3
