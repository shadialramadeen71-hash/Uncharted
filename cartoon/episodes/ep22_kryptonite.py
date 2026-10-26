"""Heroes 3 - "Kryptonite": the Joker's secret weapon is... a pickle."""
import math

from engine import noir_places as N
from engine.anim import clamp
from engine.video import Episode
from episodes.cast_heroes import add_joker, add_superman

TITLE = "The Joker's secret weapon vs Superman 🥒💚"
DESCRIPTION = """The Joker's secret weapon vs Superman 🥒💚

He finally found "kryptonite"… or did he?

Fan-made parody animation. Superman and the Joker are © DC.
#shorts #superman #joker #animation #funny"""

ROCK_SIDE = 1


def episode():
    ep = Episode(TITLE, [("JOKER FOUND", "#ffffff"), ("KRYPTONITE?!", "#52e05f")], "bank_vault",
                 music_seed=93, mood="noir", bpm=130, theme="noir", max_len=20.0, hook_end=1.8,
                 base_zoom=1.0, base_cy=1000.0)
    add_superman(ep, -260, 1)
    add_joker(ep, 760, -1)
    ep.say("superman", "Drop the money, Joker.", wait=0.6)
    ep.say("joker", "Not so fast! Behold... KRYPTONITE!")
    ep.say("superman", "...Wait. Is that a pickle?", wait=0.8)
    ep.say("joker", "It was dark in the store!")
    ep.say("superman", "Nice try.", wait=0.1)
    return ep


def choreo(ep, L):
    s_, j_ = ep.chars["superman"], ep.chars["joker"]
    s_.expr(0, "stern")
    j_.expr(0, "evil")
    s_.walk_to(0.0, 330, speed=420)
    j_.pose(0, (60, 70), (40, 80), "hold", "hold", dur=0.01, swing=0)

    a, e = L[1]["start"], L[1]["end"]
    reveal = a + (e - a) * 0.6
    j_.pose(reveal - 0.2, (150, 20), None, "hold", dur=0.2)
    ep.sound(reveal, "magic", 0.9)
    s_.expr(reveal + 0.1, "pain")
    s_["lean"].to(reveal + 0.1, reveal + 0.5, -16.0, "back")
    s_["crouch"].to(reveal + 0.1, reveal + 0.5, 0.5)
    s_.pose(reveal + 0.1, (60, 120), (40, 110), "open", "open", dur=0.3)
    ep.shake(reveal + 0.1, 0.6)

    a, e = L[2]["start"], L[2]["end"]
    sniff = a - 0.6
    s_["lean"].to(sniff, sniff + 0.4, 10.0)
    s_["crouch"].to(sniff, sniff + 0.4, 0.0)
    s_.expr(sniff, "neutral")
    s_.rest(sniff)
    s_["look"].to(sniff, sniff + 0.3, (1.0, -0.4))
    j_.expr(e - 0.3, "worried")

    a, e = L[3]["start"], L[3]["end"]
    j_.expr(a, "shocked")
    s_["lean"].to(a, a + 0.3, 0.0)
    s_.expr(a, "smug")

    a, e = L[4]["start"], L[4]["end"]
    flick = e + 0.05
    s_.walk_to(a - 0.1, 560, speed=500)
    s_.pose(flick - 0.15, (95, -10), None, "fist", dur=0.12, swing=0)
    ep.sound(flick, "hit", 1.0)
    ep.shake(flick, 1.4)
    j_.expr(flick, "pain")
    j_["x"].to(flick, flick + 0.7, 1500.0, "out")
    j_["y"].to(flick, flick + 0.7, -700.0, "out")
    j_["rot"].to(flick, flick + 0.7, -540.0, "linear")
    ep.draw("ui", lambda ctx, t: N.action_word(ctx, 760, 820, (t - flick) / 0.9, "POW!"))
    ep.follow_at = flick + 0.6
    ep.end = flick + 1.7

    def rock(ctx, t):
        if t < reveal - 0.1 or t > flick:
            return
        hx, hy = j_.joints["handF"]
        pickle = t > L[2]["start"] - 0.3
        N.green_rock(ctx, hx - 10, hy - 30, t, 1.0, pickle=pickle)
    ep.draw("front", rock)
