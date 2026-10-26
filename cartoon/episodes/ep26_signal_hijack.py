"""Heroes 7 - Signal Hijack (Batcave -> rooftop): the Joker rebrands the signal."""
from engine import noir_places as N
from engine.anim import clamp
from engine.video import Episode
from episodes.cast_heroes import add_batman, add_joker, add_superman


TITLE = "The Joker hacked the Bat-Signal 😂🦇"
DESCRIPTION = """The Joker hacked the Bat-Signal 😂🦇

Batman wants it turned off. Superman has a very cool solution. ❄️

Fan-made parody animation. Batman, Superman and the Joker are © DC.
#shorts #batman #joker #superman #animation"""


def episode():
    ep = Episode(TITLE, [("SOMEONE HACKED", "#ffffff"), ("THE SIGNAL!", "#ffcc1a")], "batcave",
                 music_seed=97, mood="noir", bpm=130, theme="noir", max_len=20.0, hook_end=1.6,
                 base_zoom=1.0, base_cy=1000.0)
    add_batman(ep, 400, 1)
    add_joker(ep, 760, -1)
    add_superman(ep, 1400, -1)
    ep.say("batman", "The signal says... 'Ha ha'?", wait=0.3)
    ep.say("joker", "Like my new logo, Batsy?", wait=1.4)
    ep.say("batman", "Turn it off. Now.")
    ep.say("joker", "Make me!")
    ep.say("superman", "Chill out.", wait=0.5)
    ep.say("batman", "...Show-off.", wait=0.6)
    return ep


def choreo(ep, L):
    b_, j_, s_ = ep.chars["batman"], ep.chars["joker"], ep.chars["superman"]
    j_["visible"].key(0, 0.0)
    s_["visible"].key(0, 0.0)
    b_.expr(0, "stern")
    ep.punch(0.2, 1.1, 560, 960)
    c1 = L[0]["end"] + 0.5
    ep.draw("back", lambda ctx, t: N.monitor_ha(ctx) if t < c1 else N.signal_ha(ctx))

    # --- rooftop
    ep.cut(c1, "gotham_rooftop")
    b_["x"].set(c1, 330.0)
    b_["y"].key(c1, -900.0)
    land = c1 + 0.6
    b_["y"].key(land, 0.0, "in")
    b_["sqy"].to(land, land + 0.06, 0.88, "out")
    b_["sqy"].to(land + 0.06, land + 0.3, 1.0, "back")
    ep.sound(land, "thud", 0.9)
    j_["visible"].set(c1, 1.0)
    j_.expr(c1, "evil")
    j_.pose(c1, (150, 20), None, "open", dur=0.01, swing=0)
    a, e = L[2]["start"], L[2]["end"]
    b_.pose(a, (95, -5), None, "point", dur=0.2, swing=0)
    a, e = L[3]["start"], L[3]["end"]
    b_.rest(a)
    j_.pose(a, (60, 110), (40, 110), "fist", "fist", dur=0.2)

    # --- Superman's freezing breath
    a, e = L[4]["start"], L[4]["end"]
    fly = a - 0.6
    s_["visible"].set(fly, 1.0)
    s_["y"].key(fly, -600.0)
    s_["x"].key(fly, 1300.0)
    s_["rot"].key(fly, 30.0)
    s_["x"].key(a, 960.0, "out")
    s_["y"].key(a, -380.0, "out")
    s_.expr(a, "smug")
    ep.sound(fly, "whoosh", 0.9)
    blow = a + 0.25
    ep.sound(blow, "freeze", 1.0)
    j_.expr(blow + 0.3, "shocked")
    ep.draw("front", lambda ctx, t: N.breath(ctx, s_.joints["head"][0] - 60, s_.joints["head"][1] + 40,
                                             j_.joints["head"][0] + 40, j_.joints["head"][1], (t - blow) / 1.0)
            if blow <= t <= blow + 1.0 else None)
    ep.draw("front", lambda ctx, t: N.ice_block(ctx, 760, 1575, 300, 760, (t - blow - 0.3) / 0.5))
    a, e = L[5]["start"], L[5]["end"]
    b_.expr(a, "smug")
    s_["x"].to(a, a + 0.6, 1500.0, "in")
    s_["y"].to(a, a + 0.6, -900.0, "in")
    ep.follow_at = e + 0.3
    ep.end = e + 1.3
