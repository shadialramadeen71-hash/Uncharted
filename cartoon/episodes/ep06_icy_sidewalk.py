"""Episode 6 (Paris winter) - Icy sidewalk: walk like a penguin."""
from engine import euro
from engine.video import Episode
from episodes.cast_euro import add_albert, add_mimi

TITLE = "Icy sidewalk? Walk like a PENGUIN"
DESCRIPTION = ("Grandpa Albert has walked on ice for 70 years... until today. Mimi's penguin walk: small flat steps, "
               "arms out, lean slightly forward. #shorts #winter #lifehacks #safety #cartoon")

ICE_X = 640
LAMP = (1010, 760)


def episode():
    ep = Episode(TITLE, [("ICY SIDEWALK?", "#f1e6c8"), ("WALK LIKE A PENGUIN!", "#f0b44c")], "paris_street",
                 music_seed=15, mood="musette", bpm=172, theme="euro", floor="snow")
    add_albert(ep, -260, 1)
    add_mimi(ep, 1340, -1)
    ep.say("albert", "Ice? Pah! Seventy years I've walked on ice!")
    ep.say("albert", "Ow. Seventy-one years.", wait=1.1)
    ep.say("mimi", "Walk like a penguin, Grandpa!", wait=0.3)
    ep.say("mimi", "Small flat steps, arms out, lean a bit forward.")
    ep.say("albert", "I look ridiculous.", wait=0.2)
    ep.say("mimi", "Ridiculous, but standing!")
    return ep


def choreo(ep, L):
    a_, m_ = ep.chars["albert"], ep.chars["mimi"]
    ep.draw("back", lambda ctx, t: euro.snow(ctx, t, n=90, size=0.7, speed=0.8, seed=1, alpha=0.7))
    ep.draw("front", lambda ctx, t: euro.snow(ctx, t, n=45, size=1.4, speed=1.2, seed=7))
    ep.draw("front", lambda ctx, t: euro.glow(ctx, LAMP[0], LAMP[1], 520, t=t))
    ep.draw("front", lambda ctx, t: euro.glow(ctx, 140, 1270, 420, strength=0.35, t=t))
    mood = {}
    ep.draw("back", lambda ctx, t: euro.cat(ctx, 190, 1372, t, 1, cat_mood(t), 0.9))

    # 0: proud walk onto the ice
    a, e = L[0]["start"], L[0]["end"]
    a_.expr(0, "smug")
    slip = a_.walk_to(0.2, ICE_X - 30, speed=(ICE_X - 30 + 260) / max(1.0, e - 0.1), ease="linear")
    a_.expr(slip, "shocked")
    ep.sound(slip, "slip", 1.0)
    a_["x"].to(slip, slip + 0.35, float(ICE_X + 60), "out")
    a_["rot"].to(slip, slip + 0.38, -84.0, "in")
    a_["y"].to(slip, slip + 0.38, -52.0, "in")
    a_.pose(slip, (160, 10), (-160, 10), "open", "open", dur=0.2)
    land = slip + 0.38
    ep.sound(land, "thud", 1.2)
    ep.shake(land, 1.5)
    a_.expr(land, "pain")
    ep.draw("front", lambda ctx, t: euro.dizzy(ctx, a_.joints["head"][0], a_.joints["head"][1] - 40, t)
            if land < t < L[2]["start"] + 0.6 else None)
    mood["laugh"] = land + 0.2
    ep.sound(land + 0.3, "meow", 0.8)
    ep.punch(land, 1.3, ICE_X - 200, 1300, hold=1.3)

    # 2-3: Mimi waddles in like a penguin
    a, e = L[2]["start"], L[2]["end"]
    m_["penguin"].key(0, 1.0)
    m_.pose(0, (38, 18), (-38, 18), "open", "open", dur=0.01, swing=0.0)
    m_.walk_to(L[1]["start"] - 0.4, 980, speed=150)
    m_.expr(a, "happy")
    mood["judge"] = a
    a, e = L[3]["start"], L[3]["end"]
    m_.expr(a, "neutral")
    up = a + 0.3
    a_["rot"].to(up, up + 0.45, 0.0, "back")
    a_["y"].to(up, up + 0.45, 0.0, "out")
    a_.rest(up)
    a_.expr(up + 0.3, "worried")
    ep.sound(up, "whoosh", 0.5)
    ep.tip = dict(t0=e - 0.1, title="Icy sidewalk?", items=[
        (True, "Small, flat steps"), (True, "Arms out for balance"), (True, "Lean slightly forward")])
    ep.sound(e - 0.1, "whoosh", 0.6)

    # 4-5: Albert tries the penguin walk
    a, e = L[4]["start"], L[4]["end"]
    a_["penguin"].to(a - 0.4, a - 0.2, 1.0)
    a_.pose(a - 0.4, (36, 18), (-36, 18), "open", "open", dur=0.2, swing=0.0)
    a_.walk_to(a - 0.3, ICE_X + 110, speed=120)
    a_.expr(a, "stern")
    mood["laugh2"] = a
    a, e = L[5]["start"], L[5]["end"]
    m_.expr(a, "happy")
    m_.pose(a, (40, 50), None, "thumbsup", dur=0.25)
    ep.sound(e, "meow", 0.8)
    ep.follow_at = e - 0.2
    ep.end = e + 1.3

    def cat_mood(t):
        if t >= mood.get("laugh2", 99):
            return "laugh"
        if t >= mood.get("judge", 99):
            return "judge"
        if t >= mood.get("laugh", 99):
            return "laugh"
        return "judge"
