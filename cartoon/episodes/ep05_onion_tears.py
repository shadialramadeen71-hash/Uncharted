"""Episode 5 (Paris winter) - Onion tears: chill the onion and use a sharp knife."""
from engine import euro
from engine.video import Episode
from episodes.cast_euro import add_albert, add_mimi

TITLE = "Onions make you cry? Try THIS"
DESCRIPTION = ("Grandpa Albert cries a river over an onion (so does the cat). Mimi's fix: chill the onion for "
               "15 minutes and use a sharp knife. #shorts #kitchenhacks #lifehacks #cooking #cartoon")

WINDOW = (560, 400, 440, 640)
BOARD = (830, 1272)
LAMP = (330, 500)


def episode():
    ep = Episode(TITLE, [("ONIONS MAKE", "#f1e6c8"), ("YOU CRY?", "#f0b44c")], "paris_apartment",
                 music_seed=8, mood="musette", bpm=176, theme="euro")
    add_albert(ep, 680, 1)
    add_mimi(ep, -200, 1)
    ep.say("albert", "Why, onion? Why are you so cruel?")
    ep.say("mimi", "Grandpa! Chill the onion for fifteen minutes first.", wait=0.5)
    ep.say("mimi", "And use a sharp knife. Dull ones crush it, so more tears.")
    ep.say("albert", "No tears! I am a genius!", wait=1.2)
    ep.say("mimi", "You're welcome.", gap=0.1)
    return ep


def choreo(ep, L):
    a_, m_ = ep.chars["albert"], ep.chars["mimi"]
    st = {}
    later = L[3]["start"] - 1.15
    cut = lambda t: 0.25 if t < later else min(1.0, 0.25 + (t - L[3]["start"] + 0.4) * 0.35)
    ep.draw("back", lambda ctx, t: euro.snow(ctx, t, WINDOW, n=70, size=0.8, seed=5))
    ep.draw("back", lambda ctx, t: euro.cat(ctx, 640, 1072, t, -1, "cry" if t < later else "happy", 0.95))
    ep.draw("back", lambda ctx, t: euro.board(ctx, BOARD[0], BOARD[1], cut(t)))
    ep.draw("front", lambda ctx, t: euro.glow(ctx, LAMP[0], LAMP[1], 620, t=t))

    # knife in hand + chopping, sobbing tears until the time skip
    def chop_keys(t0, t1):
        k = 0
        t = t0
        while t < t1:
            a_["reachF"].key(t, (BOARD[0] + 30 + (k % 3) * 12, BOARD[1] - 70), "out")
            a_["reachF"].key(t + 0.14, (BOARD[0] + 30 + (k % 3) * 12, BOARD[1] - 26), "in")
            ep.sound(t + 0.14, "chop", 0.6)
            t += 0.3
            k += 1
    a_.expr(0, "pain")
    a_["reachFw"].key(0, 1.0)
    a_["handF"].key(0, "fist")
    a_.reach(0, "B", (BOARD[0] - 50, BOARD[1] - 50), 0.01, hand="open")
    chop_keys(0.2, L[0]["end"] + 0.4)
    ep.draw("front", lambda ctx, t: euro.knife(ctx, a_.joints["handF"][0] + 6, a_.joints["handF"][1] - 4, 0.25))
    ep.draw("front", lambda ctx, t: euro.tears_from(ctx, a_.joints["eyes"], t, 1.0 if t < later else 0.0))
    ep.sound(0.1, "sob", 0.6)

    # 1-2: Mimi explains
    m_.walk_to(L[0]["end"] - 0.6, 300, speed=380)
    a, e = L[1]["start"], L[1]["end"]
    ep.sound(a - 0.05, "scratch", 0.6)
    m_.expr(a, "stern")
    m_.pose(a, (110, 10), None, "point", dur=0.25, swing=0)
    a_.reach(a, "F", None, 0.3)
    a_.reach(a, "B", None, 0.3)
    a_.turn(a + 0.1, -1)
    a_.expr(a, "worried")
    ep.punch(a, 1.25, 500, 1080, hold=e - a - 0.3)
    a, e = L[2]["start"], L[2]["end"]
    m_.expr(a, "neutral")
    m_.pose(a, (70, 30), None, "open", dur=0.3)
    ep.tip = dict(t0=e - 0.1, title="Onion tears?", items=[
        (True, "Chill it 15 min first"), (True, "Use a sharp knife"), (True, "Cut near a fan or window")])
    ep.sound(e - 0.1, "whoosh", 0.6)

    # time skip, then happy chopping
    ep.draw("ui", lambda ctx, t: euro.later_card(ctx, t, later, "Fifteen minutes later...", 1.1))
    ep.sound(later, "whoosh", 0.8)
    a, e = L[3]["start"], L[3]["end"]
    a_.turn(later + 0.5, 1)
    a_.reach(later + 0.5, "F", (BOARD[0] + 30, BOARD[1] - 70), 0.01)
    a_.reach(later + 0.5, "B", (BOARD[0] - 50, BOARD[1] - 50), 0.01, hand="open")
    a_.expr(later + 0.5, "happy")
    chop_keys(later + 0.7, e + 0.3)
    m_.rest(later + 0.5)
    m_.expr(later + 0.5, "neutral")
    a, e = L[4]["start"], L[4]["end"]
    m_.expr(a, "smug")
    ep.sound(e, "meow", 0.9)
    ep.follow_at = e - 0.2
    ep.end = e + 1.3
