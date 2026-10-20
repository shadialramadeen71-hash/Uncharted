"""Episode 8 (Paris winter) - Coffee on your shirt? Blot, don't rub - then cold water from the back."""
from engine import euro, euro_places as P
from engine.anim import Track, clamp
from engine.video import Episode
from episodes.cast_euro import add_albert, add_gaston, add_mimi

TITLE = "Coffee stain? STOP rubbing it!"
DESCRIPTION = """Coffee stain? STOP rubbing it! ☕

Grandpa Albert scrubs… and the stain only grows. Gaston the waiter knows better:
❌ Don't rub (it spreads the stain)
✅ Blot with a clean cloth
✅ Rinse with cold water from the back of the fabric

What's the worst stain you've had? 👇
#shorts #cleaninghacks #lifehacks #laundry #cartoon"""

TABLE = (560, 1250)


def episode():
    ep = Episode(TITLE, [("COFFEE STAIN?", "#f1e6c8"), ("STOP RUBBING IT!", "#f0b44c")], "cafe",
                 music_seed=31, mood="musette", bpm=164, theme="euro")
    add_albert(ep, 360, 1)
    add_gaston(ep, 1340, -1)
    add_mimi(ep, 175, 1, z=-1)
    ep.say("gaston", "Your cafe, monsieur.")
    ep.say("albert", "Merci! ...Oh no, my coat!", wait=0.3)
    ep.say("albert", "Quick, rub it out!")
    ep.say("gaston", "Non, non! Rubbing spreads it.", wait=0.1)
    ep.say("gaston", "Blot it, then cold water from the back.")
    ep.say("mimi", "Grandpa, you're a mess.", wait=0.2)
    return ep


def choreo(ep, L):
    a_, g_, m_ = ep.chars["albert"], ep.chars["gaston"], ep.chars["mimi"]
    stain_r = Track(0.0)
    ep.draw("back", lambda ctx, t: P.bistro_table(ctx, TABLE[0], TABLE[1]))
    ep.draw("front", lambda ctx, t: euro.glow(ctx, 300, 390, 520, t=t))
    ep.draw("front", lambda ctx, t: euro.glow(ctx, 820, 350, 480, t=t))

    # 0: Gaston glides in with a tray
    a, e = L[0]["start"], L[0]["end"]
    g_.expr(0, "smug")
    g_.pose(0, (60, 70), None, "open", None, dur=0.01, swing=0.0)
    arrive = g_.walk_to(0.0, 760, speed=480)
    put = max(arrive, e - 0.3)
    g_.reach(put, "F", (TABLE[0] + 60, TABLE[1] - 40), 0.3, hand="hold")
    g_.reach(put + 0.5, "F", None, 0.3)
    g_.rest(put + 0.6)
    m_.expr(0, "happy")
    a_.expr(0, "happy")

    # 1: pick up the cup, sip, SPILL
    a, e = L[1]["start"], L[1]["end"]
    pick = a - 0.2
    a_.reach(pick, "F", (TABLE[0] + 30, TABLE[1] - 30), 0.3, hand="hold")
    a_.reach(pick + 0.4, "F", "mouth", 0.35, hand="hold")
    ep.sound(pick + 0.8, "sip", 0.8)
    spill = a + (e - a) * 0.55
    a_.reach(spill, "F", (440, 1200), 0.15, hand="open")
    ep.sound(spill, "splash", 0.6)
    ep.shake(spill, 0.8)
    a_.expr(spill, "shocked")
    stain_r.key(spill, 0.0)
    stain_r.key(spill + 0.2, 34.0, "out")

    # 2: rubbing makes it worse
    a, e = L[2]["start"], L[2]["end"]
    a_.expr(a, "worried")
    a_["reachF"].set(a, (420.0, 1180.0))
    a_["reachFw"].to(a, a + 0.1, 1.0)
    for k in range(10):
        a_["reachF"].key(a + 0.1 + k * 0.11, (410.0 + (k % 2) * 40, 1150.0 + (k % 3) * 20))
    a_["handF"].set(a, "fist")
    stain_r.to(a + 0.1, e + 0.3, 78.0, "linear")

    # 3-4: Gaston to the rescue
    a, e = L[3]["start"], L[3]["end"]
    ep.sound(a - 0.05, "scratch", 0.7)
    g_.expr(a, "stern")
    g_.pose(a, (95, -5), None, "point", dur=0.2)
    a_.reach(a, "F", None, 0.2)
    a_.expr(a, "shocked")
    ep.punch(a, 1.3, 600, 1000, hold=e - a - 0.2)
    a, e = L[4]["start"], L[4]["end"]
    g_.rest(a)
    g_.expr(a, "neutral")
    near = g_.walk_to(a, 620, speed=360)
    for k in range(6):
        g_["reachF"].key(near + 0.1 + k * 0.2, (470.0, 1150.0 + (k % 2) * 14))
    g_["reachFw"].to(near, near + 0.1, 1.0)
    g_["reachFw"].to(e + 0.2, e + 0.4, 0.0)
    g_["handF"].set(near, "hold")
    stain_r.to(near + 0.1, e + 0.4, 22.0)
    ep.tip = dict(t0=e - 0.1, title="Coffee stain?", items=[
        (False, "Don't rub it"), (True, "Blot with a clean cloth"), (True, "Cold water from the back")])
    ep.sound(e - 0.1, "whoosh", 0.6)

    def props(ctx, t):
        cx, cy = a_.joints["chest"]
        P.stain(ctx, cx + 30, cy + 10, stain_r.at(t))
        if t < pick + 0.15:
            P.cup(ctx, TABLE[0] + 60, TABLE[1] - 18, steam_t=t) if t > put + 0.2 else None
            if t <= put + 0.2:
                hx, hy = g_.joints["handF"]
                P.cup(ctx, hx + 10, hy - 6, steam_t=t)
        elif t < spill + 0.6:
            hx, hy = a_.joints["handF"]
            P.cup(ctx, hx + 6, hy - 4, tilt=clamp((t - spill) / 0.15) * 1.6)
        else:
            P.cup(ctx, TABLE[0] + 60, TABLE[1] - 18)
        if L[2]["start"] <= t < L[3]["start"]:
            P.napkin(ctx, *a_.joints["handF"], 0.3)
        if L[4]["start"] + 0.4 <= t < L[4]["end"] + 0.3:
            P.napkin(ctx, *g_.joints["handF"], -0.2)
    ep.draw("front", props)

    a, e = L[5]["start"], L[5]["end"]
    m_.expr(a, "smug")
    a_.expr(a, "silly")
    ep.follow_at = e - 0.2
    ep.end = e + 1.3
