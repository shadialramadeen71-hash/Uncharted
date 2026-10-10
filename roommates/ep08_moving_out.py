"""Tank & Zippy: Roommates — Episode 8 (season finale): Moving Out?"""
import math, os, sys
import life as L
from life import casual, granny, Pen, GOLD, RED, OUT, GROUND
import sets as st
from toon import (place, burst, ease, blink_at, get_set, bg_copy, Timeline, star,
                  sfx_pop, sfx_boing, sfx_crash, sfx_ding, sfx_sad_trombone, sfx_thud)

NAME = "rm08"
MUSIC = os.path.join(L.HERE, "..", "nfl-short", "music", "goofy_attitude.mp3")
TITLE = "Ep 8: Moving Out?"
LINES = {
    "N1": ("narrator", "The season finale. Moving Out?"),
    "Z1": ("zippy", "I'm home! Tank? Why are there boxes everywhere?"),
    "T1": ("tank", "Yes, I need something bigger. This place is too small. Okay, bye."),
    "Z2": ("zippy", "He's... moving out."),
    "N2": ("narrator", "Zippy assumed the worst."),
    "Z3": ("zippy", "Tank, please don't leave! I'll stop cooking! I'll stop cutting hair!"),
    "T2": ("tank", "Leave? Buddy, I bought us a BIGGER couch!"),
    "Z4": ("zippy", "So... you're staying?"),
    "T3": ("tank", "Where else would I go? You're my best friend."),
    "G1": ("granny", "Is that giant couch going through MY door?!"),
    "N3": ("narrator", "Some things never change. Best friends. Worst ideas."),
    "Z5": ("zippy", "Same time next season?"),
    "T4": ("tank", "Wouldn't miss it."),
}


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = tl.say("N1", 0.4) + 0.4
    T["zippy_in"] = t
    t = L.say_all(tl, ["Z1", "T1", "Z2"], t + 0.4, 0.3)
    tl.fx(sfx_sad_trombone(), t - 0.3)
    t = L.say_all(tl, ["N2", "Z3", "T2"], t + 1.6, 0.25)
    T["open"] = t
    tl.fx(sfx_boing(), t); tl.fx(sfx_ding(), t + 0.2)
    t = L.say_all(tl, ["Z4", "T3"], t + 0.8, 0.3)
    T["hug"] = t
    tl.fx(sfx_pop(), t)
    T["granny"] = t + 0.8
    t = tl.say("G1", T["granny"] + 0.5) + 0.2
    T["crash"] = t + 0.3
    tl.fx(sfx_crash(1.0), T["crash"])
    T["B"] = T["crash"] + 1.6
    t = L.say_all(tl, ["N3", "Z5", "T4"], T["B"] + 0.8, 0.3)
    T["E"] = t + 1.2
    tl.fx(sfx_pop(), T["E"] + 0.1)
    T["end"] = T["E"] + 5.0
    return tl.result()


def phone_hand(pen, x, y):
    pen.rect(x - 16, y - 40, x + 16, y + 30, (40, 40, 60), 4, 8)


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t >= T["E"]:
        u = t - T["E"]
        frame = L.life_end_card(t, u, "Season Finale", None, final=True)
        k = ease((u - 0.5) / 0.4)
        Pen(frame, 540, 1560, 0.4 + 0.6 * k).text(0, 0, "THE END", 110, GOLD, 12)
        Pen(frame, 540, 1690, 0.4 + 0.6 * k).text(0, 0, "Thanks for watching!", 60, "white", 8)
        st.confetti(frame, t, T["E"], 30)
        return frame
    if t < T["B"]:  # ---- the boxes
        frame = bg_copy(get_set("living", st.living_room))
        pen = Pen(frame)
        L.boxes(pen, t)
        opened = t > T["open"]
        hug = t > T["hug"]
        on_phone = key == "T1" or t < T["zippy_in"] + 3.0 and not hug
        # big box / big couch
        if not opened:
            pen.rect(370, 1480 - 300, 710, 1480, (200, 150, 95), 7, 8)
            pen.text(540, 1330, "COUCH XXL", 40, (120, 70, 40), 0)
        else:
            k = ease((t - T["open"]) / 0.4)
            L.couch(pen, 560, 1480, w=760, color=(90, 160, 220), sc=0.5 + 0.5 * k)
            for i in range(6):
                a = t * 2 + i * math.pi / 3
                star(pen, 560 + math.cos(a) * 420, 1200 + math.sin(a) * 150, 20, GOLD)
            if t - T["open"] < 1.2:
                burst(frame, 540, 470, "TA-DA!", 0.7, (90, 160, 220))
        if not hug:
            place(frame, casual("tank", m["tank"], blink_at(t, 0), (-1, 0) if on_phone else (1, 0), t=t,
                                arms="facepalm" if on_phone else ("shrug" if key == "T2" else "down")), 240, GROUND, sc=0.95)
            if on_phone:
                phone_hand(Pen(frame), 240 + 112, GROUND - 0.95 * 515)
            zk = ease((t - T["zippy_in"]) / 0.6)
            sad = key in ("Z2", "Z3", "N2")
            if zk > 0:
                place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (-1, 0), t=t, sad=sad,
                                    arms="flail" if key == "Z3" else ("up" if key == "Z1" else "down")), 1300 - 450 * zk, GROUND, sc=0.88)
        else:
            place(frame, casual("tank", m["tank"], True, (1, 0), t=t, arms="hold"), 300, GROUND, sc=0.95)
            place(frame, casual("zippy", m["zippy"], True, (0, 0), t=t, arms="up", cheeks=True), 330, GROUND - 330, sc=0.8,
                  angle=-20, pivot_up=200)
            for i in range(5):
                u = (t * 0.5 + i / 5) % 1
                pen = Pen(frame)
                pen.ell(250 + i * 30, 800 - u * 300, 16, 16, (240, 80, 120), 0)
        gk = ease((t - T["granny"]) / 0.6)
        if gk > 0:
            place(frame, granny(m["granny"], blink_at(t, 2.0), (-1, 0), t, arms="wave" if key == "G1" else "cane"),
                  1300 - 300 * gk, GROUND, sc=0.75)
        if t > T["crash"]:
            burst(frame, 540, 470, "CRASH!", 0.7 + 0.3 * min(1, t - T["crash"]), RED)
            Pen(frame).text(540, 640, "(the door, again)", 46, "white", 6)
        L.title_card(frame, t, TITLE, y=200)
        return frame
    # ---- rooftop at sunset
    frame = bg_copy(get_set("roof", L.rooftop))
    pen = Pen(frame)
    L.couch(pen, 540, 1480, w=760, color=(90, 160, 220))
    place(frame, casual("tank", m["tank"], blink_at(t, 0), (0.6, -0.2), t=t, arms="down"), 380, 1440, sc=0.85)
    place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (-0.6, -0.2), t=t, arms="wave" if key == "Z5" else "down",
                        cheeks=True), 720, 1440, sc=0.82)
    pen = Pen(frame)
    pen.rect(540 - 400, 1310, 540 + 400, 1440, (75, 145, 205), 8, 30)
    for i in range(3):
        a = t * 0.8 + i * 2
        star(pen, 540 + 400 * math.cos(a), 300 + 60 * math.sin(a * 1.3), 16, (255, 245, 200))
    return frame


if __name__ == "__main__":
    L.run(sys.modules[__name__], "ep08_moving_out.mp4")
