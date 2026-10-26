"""Heroes 2 - Knock Knock: the Joker's cream-pie joke backfires."""
import math

from engine import noir_places as N
from engine.anim import clamp
from engine.video import Episode
from episodes.cast_heroes import add_batman, add_joker

TITLE = "The Joker tells Batman a joke… 🃏🥧"
DESCRIPTION = """The Joker tells Batman a joke… 🃏🥧

Knock knock. Who's there? Cream pie. Cream pie who?
Batman always gets the last laugh. 😂

Fan-made parody animation. Batman and the Joker are © DC.
#shorts #batman #joker #animation #funny"""


def episode():
    ep = Episode(TITLE, [("KNOCK KNOCK,", "#ffffff"), ("BATSY!", "#3ddc97")], "funhouse",
                 music_seed=92, mood="noir", bpm=126, theme="noir", max_len=20.0, hook_end=1.8,
                 base_zoom=1.0, base_cy=1000.0)
    add_batman(ep, -260, 1)
    add_joker(ep, 760, -1)
    ep.say("joker", "Knock knock, Batsy!", wait=0.5)
    ep.say("batman", "...Who's there?")
    ep.say("joker", "CREAM PIE! Ha ha ha!")
    ep.say("batman", "Cream pie who?", wait=1.6)
    ep.say("joker", "...Very funny.", fx="nasal")
    return ep


def choreo(ep, L):
    b_, j_ = ep.chars["batman"], ep.chars["joker"]
    j_.expr(0, "evil")
    b_.expr(0, "stern")
    b_.walk_to(0.0, 330, speed=380)
    j_.pose(0, (150, 30), None, "open", dur=0.01, swing=0)

    a, e = L[2]["start"], L[2]["end"]
    j_.pose(a, (60, 70), None, "hold", dur=0.2)
    throw = e - 0.2
    j_.pose(throw, (140, 0), None, "open", dur=0.12)
    ep.sound(throw, "whoosh", 0.7)
    # Batman answers with a batarang that knocks the pie back
    bat_t = throw + 0.15
    b_.pose(bat_t - 0.1, (110, -10), None, "open", dur=0.12, swing=0)
    ep.sound(bat_t, "whoosh", 0.6)
    meet = throw + 0.45
    ep.sound(meet, "clink", 0.8)
    splat_t = meet + 0.35
    ep.sound(splat_t, "splash", 0.9)
    ep.shake(splat_t, 1.0)
    j_.expr(splat_t, "worried")
    j_["shake"].to(splat_t, splat_t + 0.05, 0.3)
    j_["shake"].to(splat_t + 0.3, splat_t + 0.5, 0.0)
    j_.rest(splat_t + 0.1)
    ep.punch(splat_t, 1.35, 700, 900, hold=1.4)
    ep.draw("ui", lambda ctx, t: N.action_word(ctx, 760, 760, (t - splat_t) / 1.0, "SPLAT!"))
    b_.rest(meet)
    b_.expr(splat_t + 0.2, "smug")

    def props(ctx, t):
        jx, jy = j_.joints["handF"]
        mx_, my_ = 560, 1020
        if t < throw:
            N.pie(ctx, jx - 10, jy - 20)
        elif t < meet:
            u = (t - throw) / (meet - throw)
            N.pie(ctx, jx + (mx_ - jx) * u, jy + (my_ - jy) * u - 80 * 4 * u * (1 - u), -u * 2)
        elif t < splat_t:
            u = (t - meet) / (splat_t - meet)
            fx, fy = j_.joints["head"]
            N.pie(ctx, mx_ + (fx - mx_) * u, my_ + (fy - my_) * u, -2 - u * 6)
        if bat_t <= t < meet + 0.4:
            bx, by = b_.joints["handF"]
            u = clamp((t - bat_t) / (meet - bat_t))
            N.batarang(ctx, bx + (mx_ - bx) * u, by + (my_ - by) * u, t * 30)
        if t >= splat_t:
            fx, fy = j_.joints["head"]
            N.splat(ctx, fx + 10, fy + 10, min(0.59, (t - splat_t) / 1.5))
    ep.draw("front", props)

    a, e = L[3]["start"], L[3]["end"]
    b_.pose(a, (40, 120), None, "fist", dur=0.3)
    a, e = L[4]["start"], L[4]["end"]
    ep.follow_at = e + 0.3
    ep.end = e + 1.4
