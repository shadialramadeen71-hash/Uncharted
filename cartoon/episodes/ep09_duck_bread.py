"""Episode 9 (Paris winter) - Don't feed ducks bread: give peas, oats or sweetcorn."""
import math

from engine import euro, euro_places as P
from engine.character import ellipse
from engine.video import Episode
from episodes.cast_euro import add_albert, add_mimi

TITLE = "Feeding ducks bread? Please don't!"
DESCRIPTION = """Feeding ducks bread? Please don't! 🦆

Grandpa Albert brings a whole baguette… Mimi explains:
❌ Bread is junk food for ducks
✅ Give peas, oats or sweetcorn instead
✅ Just a little at a time

Share this with someone who feeds the ducks! 👇
#shorts #animals #nature #lifehacks #cartoon"""


def episode():
    ep = Episode(TITLE, [("FEEDING DUCKS", "#f1e6c8"), ("BREAD? DON'T!", "#f0b44c")], "paris_park",
                 music_seed=44, mood="musette", bpm=170, theme="euro", floor="snow")
    add_albert(ep, 380, 1)
    add_mimi(ep, 1340, -1)
    ep.say("albert", "Here, little ducks! Fresh bread!")
    ep.say("mimi", "Grandpa, stop! Bread is junk food for ducks.", wait=0.4)
    ep.say("mimi", "Give them peas, oats or sweetcorn instead.")
    ep.say("albert", "And the bread?", wait=1.0)
    ep.say("mimi", "That's your lunch.", gap=0.1)
    return ep


def choreo(ep, L):
    a_, m_ = ep.chars["albert"], ep.chars["mimi"]
    ducks = {"mood": "calm"}
    ep.draw("back", lambda ctx, t: euro.snow(ctx, t, n=80, size=0.7, speed=0.7, seed=3, alpha=0.7))
    ep.draw("front", lambda ctx, t: euro.snow(ctx, t, n=35, size=1.3, speed=1.1, seed=9))
    ep.draw("front", lambda ctx, t: euro.glow(ctx, 1010, 940, 420, strength=0.4, t=t))
    ep.draw("back", lambda ctx, t: euro.cat(ctx, 300, 1372, t, 1, "judge", 0.85, look=0.6))

    throws = []  # (t0, kind)

    def draw_ducks(ctx, t):
        mood = ducks_mood(t)
        for i, (x0, y0) in enumerate(((560, 1318), (720, 1336), (420, 1340))):
            x = x0 + 30 * math.sin(t * 0.7 + i * 2)
            P.duck(ctx, x, y0, t + i, 1 if math.cos(t * 0.7 + i * 2) > 0 else -1, mood, 0.7)
        for t0, kind in throws:  # thrown food arcs into the pond
            u = (t - t0) / 0.6
            if 0 <= u <= 1.6:
                hx, hy = 520, 1150
                for k in range(5 if kind == "peas" else 3):
                    tx = 520 + k * 50
                    px = hx + (tx - hx) * min(u, 1)
                    py = hy + (1320 - hy) * min(u, 1) - 160 * 4 * min(u, 1) * (1 - min(u, 1))
                    if kind == "peas":
                        ellipse(ctx, px, py, 7, 7)
                        ctx.set_source_rgb(0.4, 0.7, 0.3)
                    else:
                        ellipse(ctx, px, py, 16, 11)
                        ctx.set_source_rgb(0.85, 0.65, 0.35)
                    ctx.fill()
    ep.draw("back", draw_ducks)

    # 0: throwing bread
    a, e = L[0]["start"], L[0]["end"]
    a_.expr(0, "happy")
    for k in range(3):
        tk = a + 0.3 + k * 0.7
        a_.pose(tk, (150, 20), None, "open", dur=0.15)
        a_.pose(tk + 0.25, (60, 60), None, "hold", dur=0.25)
        throws.append((tk + 0.2, "bread"))
        ep.sound(tk + 0.2, "whoosh", 0.3)
    ep.sound(a + 1.4, "quack", 0.6)

    # 1-2: Mimi
    m_.walk_to(L[0]["end"] - 0.6, 820, speed=420)
    a, e = L[1]["start"], L[1]["end"]
    ep.sound(a - 0.05, "scratch", 0.7)
    m_.expr(a, "stern")
    m_.pose(a, (95, -5), None, "point", dur=0.2, swing=0)
    a_.expr(a, "shocked")
    a_.rest(a)
    a_.turn(a + 0.2, 1)
    ep.punch(a, 1.25, 640, 1150, hold=e - a - 0.3)
    a, e = L[2]["start"], L[2]["end"]
    m_.expr(a, "neutral")
    m_.pose(a, (70, 30), None, "open", dur=0.3)
    ep.tip = dict(t0=e - 0.1, title="Feeding ducks?", items=[
        (False, "No bread"), (True, "Peas, oats, sweetcorn"), (True, "Just a little at a time")])
    ep.sound(e - 0.1, "whoosh", 0.6)

    # peas time: happy ducks
    peas = e + 0.15
    a_.pose(peas, (150, 20), None, "open", dur=0.15)
    a_.pose(peas + 0.3, (8, 12), None, "relaxed", dur=0.3)
    throws.append((peas + 0.2, "peas"))
    for k in range(3):
        ep.sound(peas + 0.6 + k * 0.25, "quack", 0.7)
    happy_at = peas + 0.6

    a, e = L[3]["start"], L[3]["end"]
    a_.expr(a, "worried")
    a_.turn(a, -1)
    a, e = L[4]["start"], L[4]["end"]
    m_.expr(a, "smug")
    a_.expr(e, "happy")
    a_.reach(e, "F", "mouth", 0.3, hand="hold")
    ep.sound(e + 0.35, "chop", 0.8)
    ep.draw("front", lambda ctx, t, e=e: P.baguette(ctx, a_.joints["handF"][0], a_.joints["handF"][1] - 20, 0.9, 200)
            if t >= e else None)
    ep.follow_at = e - 0.2
    ep.end = e + 1.3

    def ducks_mood(t):
        if t >= happy_at:
            return "eat"
        if t >= L[0]["start"] + 1.0:
            return "angry"
        return "calm"
