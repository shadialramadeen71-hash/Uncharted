"""Heroes 4 - The Greenhouse Stakeout: Superman's allergies vs. stealth."""
import math

from engine import noir_places as N, palace_places as P
from engine.video import Episode
from episodes.cast_heroes import add_batman, add_superman

TITLE = "Batman's stakeout ruined by a super sneeze 🤧🦇"
DESCRIPTION = """Batman's stakeout ruined by a super sneeze 🤧🦇

A silent stakeout in the greenhouse… with Superman. And pollen.

Fan-made parody animation. Batman and Superman are © DC.
#shorts #batman #superman #animation #funny"""


def episode():
    ep = Episode(TITLE, [("SILENT", "#ffffff"), ("STAKEOUT", "#ffcc1a")], "greenhouse",
                 music_seed=94, mood="noir", bpm=112, theme="noir", max_len=20.0, hook_end=1.8,
                 base_zoom=1.0, base_cy=1000.0)
    add_batman(ep, 300, 1)
    add_superman(ep, 760, -1)
    ep.say("superman", "Why are we hiding in a greenhouse?", wait=0.3)
    ep.say("batman", "Stakeout. Not one sound.")
    ep.say("superman", "Ah... ah... ah...", wait=0.3)
    ep.say("superman", "ACHOO!", fx="shout", gap=0.1)
    ep.say("batman", "...Stealth mode, Clark.", wait=1.4)
    ep.say("superman", "Sorry. Pollen.")
    return ep


def choreo(ep, L):
    b_, s_ = ep.chars["batman"], ep.chars["superman"]
    b_.expr(0, "stern")
    s_.expr(0, "worried")
    b_["crouch"].key(0, 0.4)
    s_["crouch"].key(0, 0.3)

    a, e = L[1]["start"], L[1]["end"]
    b_.turn(a - 0.1, 1)
    b_.pose(a, (95, -5), None, "point", dur=0.2, swing=0)
    a, e = L[2]["start"], L[2]["end"]
    b_.rest(a)
    s_["tilt"].to(a, e, 22.0)
    s_.expr(a, "pain")
    s_["lean"].to(a, e, -10.0)
    ep.punch(a, 1.35, 760, 900, hold=e - a)
    a, e = L[3]["start"], L[3]["end"]
    sneeze = a + 0.05
    s_["tilt"].to(sneeze, sneeze + 0.08, -18.0, "out")
    s_["lean"].to(sneeze, sneeze + 0.08, 16.0, "out")
    ep.sound(sneeze + 0.05, "whoosh", 1.2)
    ep.sound(sneeze + 0.2, "shatter", 1.0)
    ep.shake(sneeze, 2.0, 0.8)
    ep.unpunch(sneeze)
    # Batman is blown backwards, cape flapping
    b_.expr(sneeze + 0.05, "shocked")
    b_["x"].to(sneeze + 0.05, sneeze + 0.5, 150.0, "out")
    b_["lean"].to(sneeze + 0.05, sneeze + 0.3, -22.0, "out")
    b_["lean"].to(sneeze + 0.9, sneeze + 1.3, 0.0)
    b_.pose(sneeze + 0.05, (150, 30), (-150, 30), "open", "open", dur=0.15)
    b_.rest(sneeze + 1.0)
    ep.draw("ui", lambda ctx, t: N.action_word(ctx, 640, 760, (t - sneeze) / 1.0, "ACHOO!"))

    def wind(ctx, t):
        u = (t - sneeze) / 0.7
        if 0 <= u <= 1:
            for k in range(7):
                y = 820 + k * 70
                x1 = 700 - 900 * u
                ctx.move_to(x1 + 200, y)
                ctx.line_to(x1, y + 10 * math.sin(k))
                ctx.set_source_rgba(1, 1, 1, 0.7 * (1 - u))
                ctx.set_line_width(6)
                ctx.stroke()
        for k, x in enumerate((180, 420, 640, 900)):
            P.shards(ctx, x, 380 + (k % 2) * 120, (t - sneeze - 0.15 - k * 0.05) / 1.0)
    ep.draw("front", wind)

    a, e = L[4]["start"], L[4]["end"]
    b_.expr(a, "stern")
    b_["crouch"].to(a, a + 0.3, 0.0)
    s_.expr(a - 0.3, "worried")
    s_["tilt"].to(a - 0.3, a, 0.0)
    s_["lean"].to(a - 0.3, a, 0.0)
    a, e = L[5]["start"], L[5]["end"]
    s_.expr(a, "silly")
    s_.pose(a, (60, 120), None, "open", dur=0.2)
    ep.follow_at = e + 0.3
    ep.end = e + 1.4
