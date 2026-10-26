"""Heroes 6 - The Joker's Birthday (funhouse -> bank vault -> rooftop)."""
from engine import noir_places as N
from engine.video import Episode
from episodes.cast_heroes import add_batman, add_joker, add_superman

TITLE = "It's the Joker's birthday… 🎂🃏"
DESCRIPTION = """It's the Joker's birthday… 🎂🃏

He picked his own present. The heroes picked a better one.

Fan-made parody animation. Batman, Superman and the Joker are © DC.
#shorts #joker #batman #superman #animation"""


def episode():
    ep = Episode(TITLE, [("IT'S THE JOKER'S", "#ffffff"), ("BIRTHDAY!", "#3ddc97")], "funhouse",
                 music_seed=96, mood="noir", bpm=124, theme="noir", max_len=20.0, hook_end=1.6,
                 base_zoom=1.0, base_cy=1000.0)
    add_joker(ep, 540, 1)
    add_superman(ep, 260, 1)
    add_batman(ep, 330, 1)
    ep.say("joker", "It's my birthday! Time for presents!")
    ep.say("joker", "Ooh, this vault looks gift-wrapped!", wait=1.0)
    ep.say("superman", "Happy birthday, Joker.")
    ep.say("batman", "We even got you a cake.", wait=1.2)
    ep.say("joker", "Aww! ...Is there a file inside?")
    ep.say("batman", "No.", gap=0.05)
    return ep


def choreo(ep, L):
    j_, s_, b_ = ep.chars["joker"], ep.chars["superman"], ep.chars["batman"]
    s_["visible"].key(0, 0.0)
    b_["visible"].key(0, 0.0)
    j_.expr(0, "evil")
    j_.pose(0, (150, 20), (-150, 20), "open", "open", dur=0.01, swing=0)
    ep.sound(0.3, "horn", 1.0)
    ep.sound(1.2, "horn", 0.8)
    hat_until = {"t": 99.0}
    ep.draw("front", lambda ctx, t: N.party_hat(ctx, j_.joints["head"], 1 if j_.tr["face"].at(t) > 0 else -1))

    # --- the vault
    c1 = L[0]["end"] + 0.4
    ep.cut(c1, "bank_vault")
    j_["x"].set(c1, -200.0)
    j_.rest(c1)
    j_.walk_to(c1 + 0.1, 640, speed=520)
    a, e = L[1]["start"], L[1]["end"]
    j_.pose(a, (150, 20), None, "open", dur=0.2)
    s_["visible"].set(c1 + 0.01, 1.0)
    s_["x"].set(c1 + 0.01, 320.0)
    s_.pose(c1, (40, 120), (30, 120), "fist", "fist", dur=0.01, swing=0)
    s_.expr(c1, "smug")
    a, e = L[2]["start"], L[2]["end"]
    j_.turn(a + 0.3, -1)
    j_.expr(a + 0.3, "shocked")
    j_.hop(a + 0.35, 60, 0.3)
    ep.sound(a + 0.35, "boing", 0.7)
    ep.punch(a + 0.3, 1.3, 600, 900, hold=0.8)

    # --- the rooftop: tied up, with a cake
    c2 = L[3]["start"] - 0.9
    ep.cut(c2, "gotham_rooftop")
    s_["visible"].set(c2, 0.0)
    b_["visible"].set(c2, 1.0)
    j_["x"].set(c2, 740.0)
    j_.turn(c2, -1)
    j_.pose(c2, (8, 10), (-8, 10), "fist", "fist", dur=0.01, swing=0)
    j_.expr(c2, "worried")
    b_.pose(c2, (60, 70), None, "hold", dur=0.01, swing=0)
    b_.expr(c2, "neutral")
    ep.draw("front", lambda ctx, t: N.rope_bind(ctx, j_.joints["chest"]) if t >= c2 else None)
    ep.draw("front", lambda ctx, t: N.cake(ctx, b_.joints["handF"][0] + 20, b_.joints["handF"][1] - 6, t, 0.8)
            if t >= c2 else None)
    a, e = L[4]["start"], L[4]["end"]
    j_.expr(a, "happy")
    j_["look"].to(a + 0.6, a + 0.9, (0.6, -0.6))
    a, e = L[5]["start"], L[5]["end"]
    b_.expr(a, "stern")
    j_.expr(e, "worried")
    ep.follow_at = e + 0.3
    ep.end = e + 1.3
