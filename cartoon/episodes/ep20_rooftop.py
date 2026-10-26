"""Heroes 1 - The Rooftop: Batman works alone... until his grapple hooks a blimp."""
from engine import noir_places as N
from engine.video import Episode
from episodes.cast_heroes import add_batman, add_superman

TITLE = "Batman: 'I work alone' 🦇😂"
DESCRIPTION = """Batman: "I work alone." The grapple: 🎈

Superman drops by the rooftop for a friendly chat… it does not go as planned.

Fan-made parody animation. Batman and Superman are © DC.
#shorts #batman #superman #animation #funny"""

BLIMP = (250, 520)


def episode():
    ep = Episode(TITLE, [("I WORK", "#ffffff"), ("ALONE.", "#ffcc1a")], "gotham_rooftop",
                 music_seed=91, mood="noir", bpm=132, theme="noir", max_len=20.0, hook_end=1.8,
                 base_zoom=1.0, base_cy=1000.0)
    add_batman(ep, 380, 1)
    add_superman(ep, 1400, -1)
    ep.say("superman", "Evening, Bruce!", wait=0.9)
    ep.say("batman", "Never say my name on a rooftop.")
    ep.say("superman", "Okay... Bat-buddy.")
    ep.say("batman", "Hmph. I work alone.", wait=0.2)
    ep.say("superman", "...Need a lift?", wait=1.6)
    return ep


def choreo(ep, L):
    b_, s_ = ep.chars["batman"], ep.chars["superman"]
    b_.expr(0, "stern")
    # Superman swoops in from the sky
    s_["y"].key(0.0, -1100.0)
    s_["x"].key(0.0, 1400.0)
    s_["rot"].key(0.0, 70.0)
    s_.pose(0, (170, 0), (-20, 10), "fist", "relaxed", dur=0.01, swing=0)
    land = L[0]["start"] - 0.05
    s_["y"].key(land, 0.0, "out")
    s_["x"].key(land, 780.0, "out")
    s_["rot"].key(land - 0.2, 10.0, "out")
    s_["rot"].key(land + 0.2, 0.0, "back")
    s_.rest(land)
    s_["sqy"].to(land, land + 0.06, 0.88, "out")
    s_["sqy"].to(land + 0.06, land + 0.3, 1.0, "back")
    ep.sound(0.2, "whoosh", 1.0)
    ep.sound(land, "thud", 0.8)
    s_.expr(0, "happy")
    s_.pose(L[0]["start"] + 0.1, (150, 30), None, "open", dur=0.2)

    a, e = L[1]["start"], L[1]["end"]
    s_.rest(a)
    b_.turn(a - 0.2, 1)
    b_.pose(a + 0.2, (95, -5), None, "point", dur=0.2, swing=0)
    ep.punch(a, 1.3, 400, 1000, hold=e - a - 0.3)
    a, e = L[2]["start"], L[2]["end"]
    b_.rest(a)
    s_.expr(a, "silly")
    s_.pose(a + 0.2, (40, 50), None, "thumbsup", dur=0.2)

    # grapple... hooks the blimp, and Batman is yanked into the sky
    a, e = L[3]["start"], L[3]["end"]
    s_.rest(a)
    b_.expr(a, "smug")
    fire = e + 0.1
    b_.pose(fire - 0.3, (150, -5), None, "fist", dur=0.2, swing=0)
    ep.sound(fire, "whoosh", 0.8)
    hooked = fire + 0.35
    ep.sound(hooked, "clink", 0.7)
    yank = hooked + 0.25
    b_.expr(yank, "shocked")
    b_["y"].to(yank, yank + 0.9, -1700.0, "in")
    b_["x"].to(yank, yank + 0.9, 160.0, "in")
    b_["rot"].to(yank, yank + 0.5, -25.0)
    b_.pose(yank, (170, 0), (-150, 20), "fist", "open", dur=0.15)
    ep.sound(yank, "boing", 0.7)
    ep.shake(yank, 1.0)
    s_.expr(yank + 0.3, "shocked")
    s_["look"].to(yank, yank + 0.5, (-0.6, -1.0))
    ep.draw("front", lambda ctx, t: N.grapple(ctx, b_.joints["handF"][0], b_.joints["handF"][1], BLIMP[0], BLIMP[1],
                                              (t - fire) / 0.35) if fire <= t < yank + 1.2 else None)
    a, e = L[4]["start"], L[4]["end"]
    s_.expr(a, "smug")
    s_["look"].to(a, a + 0.3, (0.0, 0.0))
    ep.follow_at = e + 0.3
    ep.end = e + 1.4
