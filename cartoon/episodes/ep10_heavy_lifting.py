"""Episode 10 (Paris winter) - Lifting something heavy? Bend your knees, keep it close."""
from engine import euro, euro_places as P
from engine.video import Episode
from episodes.cast_euro import add_albert, add_colette, add_mimi

TITLE = "Lifting heavy stuff? Save your back!"
DESCRIPTION = """Lifting heavy stuff? Save your BACK! 📦

Grandpa Albert plays the hero with a 25 kg flour sack… 😬 Mimi's rule:
✅ Bend your knees, not your back
✅ Keep the load close to your body
❌ Don't bend over or twist

Who needs to hear this? Tag them 👇
#shorts #health #safety #lifehacks #cartoon"""

SACK = (440, 1516)


def episode():
    ep = Episode(TITLE, [("LIFTING HEAVY STUFF?", "#f1e6c8"), ("SAVE YOUR BACK!", "#f0b44c")], "building_hall",
                 music_seed=52, mood="musette", bpm=168, theme="euro")
    add_albert(ep, 230, 1)
    add_colette(ep, 1320, -1)
    add_mimi(ep, 960, -1, z=-1)
    ep.say("colette", "Oof! This flour sack weighs a ton!")
    ep.say("albert", "Allow me, madame!")
    ep.say("albert", "Aaah! My back!", wait=0.6)
    ep.say("mimi", "Grandpa! Bend your knees, not your back.", wait=0.2)
    ep.say("mimi", "Keep it close, and stand up straight.")
    ep.say("colette", "My hero!", wait=0.9)
    return ep


def choreo(ep, L):
    a_, c_, m_ = ep.chars["albert"], ep.chars["colette"], ep.chars["mimi"]
    ep.draw("front", lambda ctx, t: euro.glow(ctx, 220, 450, 480, t=t))
    ep.draw("front", lambda ctx, t: euro.glow(ctx, 295, 600, 260, strength=0.4, t=t))

    # 0: Colette brings the sack in and drops it
    a, e = L[0]["start"], L[0]["end"]
    c_.expr(0, "worried")
    c_.pose(0, (40, 90), (30, 100), "hold", "hold", dur=0.01, swing=0.0)
    c_["lean"].key(0, -6.0)
    drop = c_.walk_to(0.0, SACK[0] + 160, speed=300)
    c_.pose(drop, (8, 12), (-5, 12), "open", "open", dur=0.3, swing=1.0)
    c_["lean"].to(drop, drop + 0.3, 0.0)
    ep.sound(drop + 0.1, "thud", 1.0)
    ep.shake(drop + 0.1, 0.7)
    back = c_.walk_to(drop + 0.5, SACK[0] + 330, speed=260)
    c_.turn(back, -1)
    a_.expr(0, "neutral")

    # 1-2: the wrong way: stiff legs, bent back
    a, e = L[1]["start"], L[1]["end"]
    a_.expr(a, "smug")
    bend = e + 0.1
    a_["lean"].to(bend, bend + 0.45, 72.0)
    a_.reach(bend, "F", (SACK[0] - 10, SACK[1] - 70), 0.45, hand="hold")
    a_.reach(bend, "B", (SACK[0] - 40, SACK[1] - 60), 0.45, hand="hold")
    crack = bend + 0.55
    ep.sound(crack, "crack", 1.0)
    ep.shake(crack, 1.2)
    a_.expr(crack, "pain")
    a_["shake"].to(crack, crack + 0.1, 0.4)
    ep.punch(crack, 1.35, 380, 1250, hold=1.2)
    a_.reach(crack + 0.1, "F", None, 0.3)
    a_.reach(crack + 0.1, "B", None, 0.3)
    a_.pose(crack + 0.1, (40, 120), (-60, 60), "open", "open", dur=0.3)

    # 3-4: Mimi teaches the squat lift
    a, e = L[3]["start"], L[3]["end"]
    m_.expr(a, "stern")
    m_.pose(a, (95, -5), None, "point", dur=0.2, swing=0)
    a_["shake"].to(a, a + 0.2, 0.0)
    a_["lean"].to(a + 0.4, a + 0.8, 8.0)
    a_.expr(a + 0.4, "worried")
    a, e = L[4]["start"], L[4]["end"]
    m_.expr(a, "neutral")
    m_.pose(a, (70, 30), None, "open", dur=0.3)
    a_["crouch"].to(a - 0.4, a + 0.2, 1.45)
    a_.reach(a - 0.2, "F", (SACK[0] - 20, SACK[1] - 80), 0.4, hand="hold")
    a_.reach(a - 0.2, "B", (SACK[0] - 50, SACK[1] - 70), 0.4, hand="hold")
    lift = a + (e - a) * 0.5
    a_["crouch"].to(lift, lift + 0.7, 0.0)
    a_["lean"].to(lift, lift + 0.7, 0.0)
    a_.reach(lift, "F", "mouth", 0.01)
    a_["reachF"].set(lift, (SACK[0] - 60, 1150))
    a_["reachB"].set(lift, (SACK[0] - 90, 1170))
    a_.expr(lift + 0.7, "happy")
    ep.tip = dict(t0=e - 0.1, title="Heavy lifting?", items=[
        (True, "Bend your knees"), (True, "Keep it close to you"), (False, "Don't bend or twist your back")])
    ep.sound(e - 0.1, "whoosh", 0.6)

    def draw_sack(ctx, t):
        if t < drop:
            hx, hy = c_.joints["handF"]
            P.sack(ctx, hx - 20, hy + 10, -0.1)
        elif t < lift:
            P.sack(ctx, SACK[0], SACK[1])
        else:
            hx, hy = a_.joints["handF"]
            P.sack(ctx, hx - 10, hy + 20, -0.05)
    ep.draw("front", draw_sack)

    a, e = L[5]["start"], L[5]["end"]
    c_.expr(a, "happy")
    c_["blush"].to(a, a + 0.3, 1.0)
    a_["blush"].to(a, a + 0.3, 1.0)
    ep.sound(e, "sparkle", 0.7)
    ep.follow_at = e - 0.2
    ep.end = e + 1.3
