"""The Count & Pip 1 - The Glass Slipper (ballroom)."""
from engine import palace_places as P, scene
from engine.anim import clamp
from engine.video import Episode
from episodes.cast_palace import add_count, add_pip

TITLE = "The villain vs. the glass slipper 👠💥"
DESCRIPTION = """The villain vs. the glass slipper 👠💥

The Count sneaks into the royal ball to steal the famous glass slipper…
His imp butler Pip tries to warn him. He does not listen. 🙈

Should Pip quit this job? 👇
#shorts #cartoon #funny #fairytale #animation"""

PED = (770, 1236)


def episode():
    ep = Episode(TITLE, [("THE VILLAIN VS.", "#f6e7c1"), ("THE GLASS SLIPPER", "#ffcc4d")], "ballroom",
                 music_seed=71, mood="villain", bpm=104, theme="storybook", max_len=15.0,
                 base_zoom=1.0, base_cy=1000.0)
    add_count(ep, -260, 1)
    add_pip(ep, -480, 1)
    ep.say("count", "At last... the glass slipper is MINE!")
    ep.say("pip", "Master, it's a size four. You're a size... canoe.", wait=0.2)
    ep.say("count", "Nonsense! Glass stretches!")
    ep.say("pip", "That was Cinderella's only pair.", wait=0.6)
    ep.say("count", "...RUN!", gap=0.05)
    return ep


def choreo(ep, L):
    c_, p_ = ep.chars["count"], ep.chars["pip"]
    ep.draw("back", lambda ctx, t: P.pedestal(ctx, PED[0], PED[1]))
    from engine import euro
    ep.draw("front", lambda ctx, t: euro.glow(ctx, 540, 190, 520, color=(1.0, 0.9, 0.6), strength=0.4, t=t))

    # 0: sneaking in on tiptoe
    c_.expr(0, "evil")
    c_["lean"].key(0, 10.0)
    c_.pose(0, (60, 100), (40, 110), "open", "open", dur=0.01, swing=0.0)
    arrive = c_.walk_to(0.0, 560, speed=420)
    p_.walk_to(0.2, 290, speed=440)
    p_.expr(0, "worried")
    c_["lean"].to(arrive, arrive + 0.3, 0.0)
    a, e = L[0]["start"], L[0]["end"]
    c_.pose(e - 0.6, (150, 30), None, "fist", dur=0.2)

    # 1: Pip's warning
    a, e = L[1]["start"], L[1]["end"]
    c_.rest(a)
    c_.turn(a + 0.1, -1)
    c_.expr(a, "stern")
    p_.pose(a, (95, -5), None, "point", dur=0.2, swing=0)

    # 2: he grabs it and "stretches" it
    a, e = L[2]["start"], L[2]["end"]
    p_.rest(a)
    c_.turn(a, 1)
    c_.expr(a, "evil")
    grab = a + 0.2
    c_.reach(grab, "F", (PED[0] - 30, PED[1] - 30), 0.3, hand="hold")
    c_.reach(grab + 0.5, "F", "mouth", 0.3, hand="hold")
    c_.reach(grab + 0.5, "B", "mouth", 0.3, hand="hold")
    snap = e + 0.1
    c_["handF"].set(snap - 0.1, "fist")
    ep.sound(snap, "shatter", 1.0)
    ep.shake(snap, 1.2)
    c_.expr(snap, "shocked")
    ep.punch(snap - 0.05, 1.4, 600, 900, hold=0.8)
    c_.reach(snap + 0.4, "F", None, 0.3)
    c_.reach(snap + 0.4, "B", None, 0.3)

    # 3-4: busted
    a, e = L[3]["start"], L[3]["end"]
    p_.expr(a, "stern")
    c_.expr(a, "worried")
    ep.sound(e - 0.1, "trumpet", 0.8)
    a, e = L[4]["start"], L[4]["end"]
    c_.expr(a, "shocked")
    c_.turn(a, -1)
    p_.turn(a, -1)
    c_.pose(a, (80, 60), (-40, 60), "open", "open", dur=0.15, swing=1.4)
    c_.walk_to(e - 0.1, -400, speed=900)
    p_.walk_to(e, -400, speed=820)
    ep.follow_at = e + 0.3
    ep.end = e + 1.4

    def slipper(ctx, t):
        if t < grab + 0.2:
            P.glass_slipper(ctx, PED[0], PED[1] - 14, t)
        elif t < snap:
            hx, hy = c_.joints["handF"]
            P.glass_slipper(ctx, hx + 20, hy - 20, t, 0.9, -0.3, shine=False)
        else:
            hx, hy = c_.joints["handF"] if t < snap + 0.6 else (0, 0)
            P.shards(ctx, hx + 20, hy - 20, (t - snap) / 0.8)
    ep.draw("front", slipper)
