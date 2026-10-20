"""Episode 4 (Paris winter) - Frozen fingers: never rub them with snow or hold them to the stove."""
from engine import euro, scene
from engine.video import Episode
from episodes.cast_euro import add_albert, add_mimi

TITLE = "Frozen fingers? Never rub them with snow!"
DESCRIPTION = """Frozen fingers? NEVER rub them with snow! ❄️

Grandpa Albert tries every old trick… Mimi knows the real one:
✅ Warm water — not hot
❌ Don't rub them
❌ No stove or heater (numb skin burns easily)

Did your family ever use the snow trick? 👇

Not medical advice — see a doctor if skin turns white, grey or blistered.
#shorts #winter #lifehacks #firstaid #cartoon"""

WINDOW = (560, 400, 440, 640)
BOWL = (720, 1270)
LAMP = (330, 500)


def episode():
    ep = Episode(TITLE, [("FROZEN FINGERS?", "#f1e6c8"), ("DON'T RUB THEM!", "#f0b44c")], "paris_apartment",
                 music_seed=4, mood="musette", bpm=168, theme="euro")
    add_albert(ep, -220, 1)
    add_mimi(ep, 1320, -1)
    ep.say("albert", "Brrr! My fingers are frozen!")
    ep.say("albert", "Rub them with snow! Old family trick!")
    ep.say("mimi", "No, Grandpa! Rubbing hurts frozen skin.", wait=0.1)
    ep.say("albert", "Then I'll warm them on the stove!")
    ep.say("mimi", "No! Numb skin burns. Warm water, not hot.")
    ep.say("albert", "Ahh... my fingers say merci.", wait=0.3)
    return ep


def choreo(ep, L):
    a_, m_ = ep.chars["albert"], ep.chars["mimi"]
    ep.draw("back", lambda ctx, t: euro.snow(ctx, t, WINDOW, n=70, size=0.8, seed=2))
    cat = {"mood": "sleep"}
    ep.draw("back", lambda ctx, t: euro.cat(ctx, 640, 1072, t, -1, cat_mood(t), 0.95))
    ep.draw("front", lambda ctx, t: euro.glow(ctx, LAMP[0], LAMP[1], 620, t=t))

    # 0: shivering entrance
    a, e = L[0]["start"], L[0]["end"]
    a_.expr(0, "worried")
    a_.pose(0, (40, 100), (30, 110), "fist", "fist", dur=0.01, swing=0.3)
    a_.walk_to(0.0, 400, speed=260)
    a_["shake"].key(0, 0.35)
    a_["shake"].to(e + 1.2, e + 1.5, 0.0)
    ep.draw("front", lambda ctx, t, e=e: euro.shiver(ctx, a_.joints["head"][0], a_.joints["head"][1] + 40, t)
            if t < e + 1.2 else None)

    # 1: snowball rub
    a, e = L[1]["start"], L[1]["end"]
    a_.expr(a, "happy")
    ep.sound(a + 0.2, "pop", 0.6)
    for k in range(10):
        a_["armF"].key(a + 0.3 + k * 0.12, (60.0, 70.0) if k % 2 else (50.0, 90.0))
        a_["armB"].key(a + 0.3 + k * 0.12, (55.0, 80.0) if k % 2 else (65.0, 65.0))
    ep.draw("front", lambda ctx, t, a=a, e=e: (ellipse_snowball(ctx, *a_.joints["handF"]))
            if a + 0.2 <= t <= e + 0.6 else None)

    # 2: Mimi rushes in
    m_.walk_to(L[1]["end"] - 0.6, 900, speed=420)
    a, e = L[2]["start"], L[2]["end"]
    ep.sound(a - 0.05, "scratch", 0.7)
    m_.expr(a, "stern")
    m_.pose(a, (95, -5), None, "point", dur=0.2, swing=0)
    a_.expr(a, "shocked")
    a_.rest(a + 0.1)
    ep.punch(a, 1.3, 700, 1100, hold=e - a - 0.3)
    cat_at = {"judge": a}

    # 3: the stove idea
    a, e = L[3]["start"], L[3]["end"]
    m_.rest(a)
    m_.expr(a, "worried")
    a_.expr(a, "smug")
    a_.walk_to(a + 0.1, 330, speed=260)
    a_.turn(a + 0.6, -1)
    a_.reach(a + 0.7, "F", (200, 1080), 0.35, hand="open")
    a_.reach(a + 0.7, "B", (210, 1110), 0.35, hand="open")
    ep.draw("front", lambda ctx, t, a=a: scene.steam(ctx, 120, 990, t) if t > a else None)

    # 4: the right way: a bowl of warm water
    a, e = L[4]["start"], L[4]["end"]
    ep.sound(a - 0.05, "scratch", 0.6)
    m_.expr(a, "stern")
    m_.pose(a, (95, -5), None, "point", dur=0.2, swing=0)
    a_.reach(a, "F", None, 0.2)
    a_.reach(a, "B", None, 0.2)
    a_.expr(a, "shocked")
    a_.turn(a + 0.2, 1)
    bowl_t = a + (e - a) * 0.55
    ep.sound(bowl_t, "pop", 0.7)
    ep.draw("back", lambda ctx, t, b=bowl_t: euro.bowl(ctx, BOWL[0], BOWL[1], t) if t >= b else None)
    m_.pose(bowl_t, (70, 20), None, "open", dur=0.25)
    ep.tip = dict(t0=e - 0.2, title="Frozen fingers?", items=[
        (False, "Don't rub them (or use snow)"), (False, "No stove or heater"), (True, "Warm water, not hot")])
    ep.sound(e - 0.2, "whoosh", 0.6)

    # 5: relief
    a, e = L[5]["start"], L[5]["end"]
    t_walk = a_.walk_to(a - 0.5, 540, speed=240)
    a_.reach(t_walk, "F", (BOWL[0] - 20, BOWL[1] + 6), 0.35, hand="open")
    a_.reach(t_walk, "B", (BOWL[0] - 40, BOWL[1] + 10), 0.35, hand="open")
    ep.sound(t_walk + 0.3, "splash", 0.35)
    a_.expr(t_walk + 0.3, "relieved")
    m_.expr(a, "happy")
    m_.pose(a, (40, 50), None, "thumbsup", dur=0.25)
    cat_at["happy"] = e - 0.2
    ep.sound(e - 0.1, "meow", 0.9)
    ep.follow_at = e - 0.2
    ep.end = e + 1.3

    def cat_mood(t):
        if t >= cat_at.get("happy", 99):
            return "happy"
        if t >= cat_at.get("judge", 99):
            return "judge"
        return "sleep"


def ellipse_snowball(ctx, x, y):
    from engine.character import ellipse, fill_stroke
    ellipse(ctx, x + 10, y - 20, 30, 28)
    fill_stroke(ctx, (0.95, 0.96, 0.99), ow=4)
