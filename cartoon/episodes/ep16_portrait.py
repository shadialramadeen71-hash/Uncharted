"""The Count & Pip 3 - The Portrait (gallery): hiding from the guards as a painting."""
from engine import palace_places as P
from engine.video import Episode
from episodes.cast_palace import add_count, add_pip

TITLE = "Hiding as a painting… what could go wrong? 🖼️🤧"
DESCRIPTION = """Hiding as a painting… what could go wrong? 🖼️🤧

The guards are coming! The Count has a brilliant plan. Pip has doubts.

Rate his disguise from 1 to 10 👇
#shorts #cartoon #funny #fairytale #animation"""

FRAME = (330, 640, 420, 860)  # x, y, w, h


def episode():
    ep = Episode(TITLE, [("HIDING AS A", "#f6e7c1"), ("PAINTING?!", "#ffcc4d")], "gallery",
                 music_seed=73, mood="villain", bpm=108, theme="storybook", max_len=15.0,
                 base_zoom=1.0, base_cy=1000.0)
    add_count(ep, 160, 1)
    add_pip(ep, 820, -1)
    ep.cast("guard", dict(skin="#f0c9a8", top="#3f5fae", pants="#2b2633", shoe="#151418", step="heel"),
            dict(voice="en-GB-ThomasNeural", rate="+6%", pitch="-8Hz"), 1500, -1, 1.0, -5, "GUARD", "#3f5fae")
    ep.say("count", "Guards! Quick, Pip... I'm a painting!")
    ep.say("guard", "Hmm... who goes there?", wait=0.4)
    ep.say("count", "Ah... ah... ACHOO!", wait=0.5)
    ep.say("guard", "Paintings don't sneeze!")
    ep.say("count", "This one is... modern art.", gap=0.05)
    return ep


def choreo(ep, L):
    c_, p_, g_ = ep.chars["count"], ep.chars["pip"], ep.chars["guard"]
    from engine import euro
    for x in (360, 720):
        ep.draw("front", lambda ctx, t, x=x: euro.glow(ctx, x, 700, 240, color=(1.0, 0.8, 0.45), strength=0.4, t=t))
    g_["visible"].key(0, 0.0)  # off-screen: only his footsteps and voice
    g_.walk_to(L[0]["end"], 1240, speed=150)

    # 0: jump into the frame and freeze in a noble pose
    a, e = L[0]["start"], L[0]["end"]
    c_.expr(0, "shocked")
    jump = e - 0.4
    c_.walk_to(jump - 0.5, FRAME[0] + FRAME[2] / 2, speed=600)
    c_.hop(jump, 60, 0.3)
    c_.expr(jump + 0.3, "smug")
    c_.pose(jump + 0.3, (60, 110), (20, 40), "open", "relaxed", dur=0.2, swing=0)
    c_["tilt"].to(jump + 0.3, jump + 0.5, 10.0)
    p_.expr(a, "worried")
    p_["tilt"].to(jump + 0.3, jump + 0.5, -8.0)

    # 2: dust tickles his nose
    a, e = L[2]["start"], L[2]["end"]
    c_["tilt"].to(a, a + 0.6, 22.0)
    c_.expr(a, "pain")
    sneeze = e - 0.25
    c_["tilt"].to(sneeze, sneeze + 0.08, -16.0, "out")
    c_["lean"].to(sneeze, sneeze + 0.08, 14.0, "out")
    ep.shake(sneeze, 1.2)
    ep.sound(sneeze, "hit", 0.5)
    ep.draw("front", lambda ctx, t: P.dust(ctx, c_.joints["nose"][0] + 40, c_.joints["nose"][1], (t - sneeze) / 0.7))
    ep.draw("front", lambda ctx, t: P.dust(ctx, FRAME[0] + 200, FRAME[1] - 10, (t - L[2]["start"]) / 1.2)
            if t < sneeze else None)

    # 3-4: caught
    a, e = L[3]["start"], L[3]["end"]
    c_["lean"].to(a, a + 0.3, 0.0)
    c_["tilt"].to(a, a + 0.3, 0.0)
    c_.expr(a, "shocked")
    p_.reach(a, "F", "mouth", 0.3, hand="open")  # facepalm-ish
    ep.punch(a, 1.2, 640, 900, hold=0.6)
    a, e = L[4]["start"], L[4]["end"]
    c_.expr(a, "smug")
    c_.pose(a, (150, 30), None, "point", dur=0.2)
    ep.sound(e - 0.1, "trumpet", 0.7)
    ep.follow_at = e + 0.3
    ep.end = e + 1.4

    ep.draw("front", lambda ctx, t: P.big_frame(ctx, *FRAME))
