"""Episode 7 (Paris winter) - Stale baguette? Splash it with water and pop it in a hot oven."""
from engine import euro, euro_places as P
from engine.video import Episode
from episodes.cast_euro import add_albert, add_colette

TITLE = "Rock-hard baguette? Don't throw it away!"
DESCRIPTION = """Rock-hard baguette? Don't throw it away! 🥖

Grandpa Albert knocks on the counter with it… Madame Colette's bakery trick:
✅ Splash it with water
✅ Hot oven (about 180°C / 350°F) for 5–10 min
✅ Eat it while it's warm

Did you know this one? 👇
#shorts #kitchenhacks #foodwaste #baking #cartoon"""

OVEN = (900, 1110)


def episode():
    ep = Episode(TITLE, [("STALE BAGUETTE?", "#f1e6c8"), ("DON'T THROW IT AWAY!", "#f0b44c")], "boulangerie",
                 music_seed=21, mood="musette", bpm=176, theme="euro")
    add_albert(ep, -240, 1)
    add_colette(ep, 720, -1)
    ep.say("albert", "Colette! Your baguette is hard as a rock!")
    ep.say("colette", "It's not broken, mon cher. It's just stale.", wait=0.2)
    ep.say("colette", "Splash it with water, then five minutes in a hot oven.")
    ep.say("albert", "Crunchy! Like new!", wait=1.3)
    ep.say("colette", "Bon appetit!", gap=0.1)
    return ep


def choreo(ep, L):
    a_, c_ = ep.chars["albert"], ep.chars["colette"]
    ep.draw("front", lambda ctx, t: euro.glow(ctx, 330, 200, 520, t=t))
    ep.draw("front", lambda ctx, t: euro.glow(ctx, OVEN[0], OVEN[1], 330, color=(1.0, 0.6, 0.25), strength=0.45, t=t))
    ep.sound(0.05, "bell", 0.8)

    # 0: Albert storms in and knocks the baguette on the counter
    a, e = L[0]["start"], L[0]["end"]
    a_.expr(0, "stern")
    a_.pose(0, (60, 70), None, "fist", None, dur=0.01, swing=0.3)
    arrive = a_.walk_to(0.0, 290, speed=300)
    for k in range(3):
        tk = arrive + 0.1 + k * 0.35
        a_["reachF"].key(tk, (420.0, 1110.0), "out")
        a_["reachF"].key(tk + 0.17, (430.0, 1190.0), "in")
        ep.sound(tk + 0.17, "clonk", 0.9)
    a_["reachFw"].to(arrive, arrive + 0.1, 1.0)
    a_["reachFw"].to(arrive + 1.2, arrive + 1.4, 0.0)
    c_.expr(arrive + 0.2, "worried")

    # 1-2: Colette explains, takes the baguette to the oven
    a, e = L[1]["start"], L[1]["end"]
    c_.expr(a, "happy")
    c_.pose(a, (70, 30), None, "open", dur=0.3)
    a, e = L[2]["start"], L[2]["end"]
    take = a + 0.1
    c_.reach(take, "F", (430, 1170), 0.3, hand="hold")
    a_.pose(take, (8, 12), None, "relaxed", dur=0.3)
    splash_t = a + 0.9
    ep.sound(splash_t, "splash", 0.35)
    c_.reach(splash_t + 0.3, "F", None, 0.3)
    to_oven = c_.walk_to(splash_t + 0.4, 740, speed=260)
    c_.turn(to_oven, 1)
    c_.reach(to_oven + 0.1, "F", (OVEN[0] - 30, OVEN[1] - 30), 0.35, hand="hold")
    in_oven = to_oven + 0.45
    ep.tip = dict(t0=e - 0.1, title="Stale bread?", items=[
        (True, "Splash it with water"), (True, "Hot oven, 5 to 10 min"), (True, "Eat it while warm")])
    ep.sound(e - 0.1, "whoosh", 0.6)

    later = L[3]["start"] - 1.2
    ep.draw("ui", lambda ctx, t: euro.later_card(ctx, t, later, "Five minutes later...", 1.1))
    ep.sound(later, "whoosh", 0.8)
    ep.sound(later + 1.0, "ding", 0.8)
    # after the time skip Colette hands over the fresh, steaming baguette
    c_.turn(later + 0.5, -1)
    c_.walk_to(later + 0.5, 560, speed=600)
    c_.reach(later + 0.6, "F", (440, 1150), 0.01, hand="hold")
    give = L[3]["start"] - 0.1
    c_.reach(give + 0.3, "F", None, 0.3)
    c_.expr(later + 0.5, "happy")
    a_.reach(give, "F", (440, 1150), 0.25, hand="hold")
    a_.reach(give + 0.5, "F", "mouth", 0.3, hand="hold")
    ep.sound(give + 0.8, "chop", 0.9)
    ep.sound(give + 1.0, "chop", 0.7)
    a_.expr(give + 0.8, "happy")

    def draw_bread(ctx, t):
        if t < take + 0.2:
            hx, hy = a_.joints["handF"]
            P.baguette(ctx, hx + 60, hy - 6, 0.35, 280, "#b98a4a")
        elif t < in_oven:
            hx, hy = c_.joints["handF"]
            P.baguette(ctx, hx, hy - 20, 0.4, 280, "#b98a4a")
            if splash_t <= t < splash_t + 0.6:
                from engine import scene
                scene.splash(ctx, hx, hy - 40, (t - splash_t) / 0.6)
        elif t >= later + 0.6:
            who = c_ if t < give + 0.2 else a_
            hx, hy = who.joints["handF"]
            P.baguette(ctx, hx, hy - 20, 0.5 if who is c_ else -0.9, 280, "#b98a4a", fresh=1.0)
            from engine import scene
            scene.steam(ctx, hx, hy - 60, t)
    ep.draw("front", draw_bread)

    a, e = L[4]["start"], L[4]["end"]
    c_.pose(a, (40, 50), None, "thumbsup", dur=0.25)
    ep.follow_at = e - 0.2
    ep.end = e + 1.3
