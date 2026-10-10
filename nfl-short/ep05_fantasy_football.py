"""Tank & Zippy — Episode 5: Fantasy Football."""
import math, os, sys
import toon
from toon import (Pen, GROUND, GOLD, RED, OUT, PURPLE, character, place, burst, ease, blink_at, end_card, get_set,
                  bg_copy, star, Timeline, sfx_sad_trombone, sfx_ding, sfx_thud, sfx_boing, sfx_pop, sfx_crowd, sfx_whoosh)
import sets as st

NAME = "ep05"
MUSIC = "wacky_wobblings.mp3"
TITLE = "Episode 5: Fantasy Football"
LINES = {
    "N1": ("narrator", "Episode five. Fantasy Football."),
    "Z1": ("zippy", "Tank! Fans can pick me for their fantasy teams!"),
    "T1": ("tank", "That's great, buddy! How many points are you worth?"),
    "Z2": ("zippy", "Two."),
    "T2": ("tank", "Two is... a number."),
    "Z3": ("zippy", "I need to be everyone's number one pick!"),
    "N2": ("narrator", "Zippy tried everything."),
    "N3": ("narrator", "It went... badly."),
    "T3": ("tank", "Buddy, maybe stop trying so hard."),
    "Z4": ("zippy", "Fine. I give up. Pass the popcorn."),
    "N4": ("narrator", "Meanwhile, a video of Zippy crashing into a hot dog stand went viral."),
    "Z5": ("zippy", "I'm famous for CRASHING?!"),
    "T4": ("tank", "You are very good at it."),
    "N5": ("narrator", "Next time, on Tank and Zippy: The Halftime Show!"),
}
CARD = 2.0
SEAT = 1330


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = tl.say("N1", 0.4) + 0.4
    t = tl.say("Z1", t) + 0.25
    t = tl.say("T1", t) + 0.3
    T["two"] = t
    tl.fx(sfx_ding(), t)
    t = tl.say("Z2", t + 0.2) + 0.3
    tl.fx(sfx_sad_trombone(), t)
    t += 2.0
    T["two_off"] = t
    t = tl.say("T2", t) + 0.3
    t = tl.say("Z3", t) + 0.3
    t = tl.say("N2", t) + 0.2
    T["M"] = t
    tl.fx(sfx_thud(), t + 0.8); tl.fx(sfx_thud(), t + 1.4)
    tl.fx(sfx_boing(), t + CARD + 1.2)
    tl.fx(sfx_whoosh(1.0), t + 2 * CARD + 0.3)
    tl.say("N3", t + 2 * CARD + 0.6)
    t = t + 2 * CARD + 0.6 + dur["N3"] + 0.5
    T["back"] = t
    t = tl.say("T3", t + 0.2) + 0.25
    t = tl.say("Z4", t) + 0.3
    T["viral"] = t
    tl.fx(sfx_ding(), t); tl.fx(sfx_ding(), t + 0.25); tl.fx(sfx_ding(), t + 0.5)
    t = tl.say("N4", t + 0.8) + 0.3
    tl.fx(sfx_crowd(2.0, 0.2), t)
    t = tl.say("Z5", t) + 0.3
    t = tl.say("T4", t) + 1.0
    T["E"] = t
    tl.fx(sfx_pop(), t + 0.1)
    T["end"] = tl.say("N5", t + 0.5) + 1.5
    return tl.result()


def popcorn(pen, x, y):
    pen.poly([(x - 60, y - 120), (x + 60, y - 120), (x + 45, y), (x - 45, y)], "white", 6)
    for i in range(3):
        pen.poly([(x - 40 + i * 40, y - 120), (x - 20 + i * 40, y - 120), (x - 15 + i * 30, y), (x - 30 + i * 30, y)], RED, 0)
    for i in range(7):
        pen.ell(x - 50 + i * 17, y - 130 - (i % 3) * 12, 16, 14, (255, 245, 200), 3)


def counter(pen, old, new, k):
    pen.rect(700, 140, 1040, 290, (30, 30, 40), 7, 20)
    pen.text(870, 180, "FANTASY PTS", 32, "white", 0)
    val = old if k < 0.5 else new
    pen.text(870, 245, str(val), 64, (120, 255, 120) if val > 0 else (255, 80, 80), 0)


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t >= T["E"]:
        return render_end(t, c)
    if t < T["M"] or t >= T["back"]:
        frame = bg_copy(get_set("living", st.living_room))
        sad = key in ("Z2", "T2")
        viral = t > T["viral"]
        bounce = abs(math.sin(t * 9)) * 30 if key == "Z3" or (viral and key == "Z5") else 0
        place(frame, character("tank", m["tank"], blink_at(t, 0), (0.7, 0.2), t=t, arms="down"), 320, SEAT, sc=0.9)
        place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (-0.3, 0.5) if not viral else (0, -0.2), t=t,
                               arms="flail" if bounce else "down"), 740, SEAT - bounce, sc=0.9)
        pen = Pen(frame)
        popcorn(pen, 470, 1190)
        st.phone(pen, 640, 1150, 0.22, [])
        st.couch_front(frame)
        if t < 2.8:
            a = ease(t / 0.4) * (1 - ease((t - 2.4) / 0.4))
            Pen(frame, 540, 140, 0.6 + 0.4 * a).rect(-470, -90, 470, 170, (40, 30, 70), 7, 30)
            Pen(frame, 540, 140, 0.6 + 0.4 * a).text(0, 0, "TANK & ZIPPY", 110, GOLD, 12)
            Pen(frame, 540, 250, 0.6 + 0.4 * a).text(0, 0, TITLE, 50, "white", 7)
        if T["two"] < t < T["two_off"]:
            k = ease((t - T["two"]) / 0.3)
            st.phone(Pen(frame), 540, 700, 0.4 + 0.75 * k, [("FANTASY", 34, (40, 40, 60)), ("ZIPPY", 58, (235, 110, 20)),
                                                            ("2 PTS", 78, (200, 40, 45)), ("(bench him)", 28, (120, 120, 130))])
        if viral and key != "T4":
            k = ease((t - T["viral"]) / 0.3)
            st.phone(Pen(frame), 540, 700, 0.4 + 0.75 * k, [("TRENDING", 34, (40, 40, 60)), ("ZIPPY", 58, (235, 110, 20)),
                                                            ("999 PTS", 62, (40, 170, 60)), ("most viral", 30, (120, 120, 130))])
            for i in range(8):
                a = t * 3 + i * math.pi / 4
                star(Pen(frame), 540 + math.cos(a) * 330, 700 + math.sin(a) * 420, 24, GOLD)
        if key == "T4":
            burst(frame, 540, 600, "999 PTS!", 0.8, (90, 200, 90))
        return frame
    # ---- montage
    u = t - T["M"]
    card = min(2, int(u // CARD))
    v = u - card * CARD
    if card == 0:  # training
        frame = bg_copy(get_set("gym", st.gym))
        down = v > 1.3
        ang = 90 if down else 75
        bob = 0 if down else 20 * abs(math.sin(v * 5))
        place(frame, character("zippy", 0, False, (0, 1) if not down else (0, 0), t=t, dizzy=down, arms="down"),
              560, GROUND - 60 - bob, angle=ang, pivot_up=0)
        label, old, new = "TRAINING", 2, 1
        if down:
            burst(frame, 540, 560, "OOF!", 0.6, (255, 170, 60))
    elif card == 1:  # dance video
        frame = bg_copy(get_set("living", st.living_room))
        pen = Pen(frame)
        pen.ell(860, 900, 110, 110, (255, 250, 230), 10)
        pen.ell(860, 900, 70, 70, (60, 50, 70), 0)
        pen.line([(860, 1010), (860, GROUND)], (60, 60, 70), 10)
        trip = v > 1.1
        place(frame, character("zippy", 0, False, (0, 0), t=t, arms="flail", dizzy=trip), 420,
              GROUND - (0 if trip else abs(math.sin(v * 8)) * 60), angle=(-80 * ease((v - 1.1) / 0.25)) if trip else 10 * math.sin(v * 10),
              pivot_up=0)
        pen = Pen(frame)
        pen.ell(80, 300, 18, 18, (255, 40, 40), 0)
        pen.text(150, 300, "REC", 40, "white", 5)
        label, old, new = "DANCE VIDEO", 1, 0
    else:  # begging in the empty stadium
        frame = st.view(get_set("night", lambda: st.stadium("night")), 700 + v * 20)
        place(frame, character("zippy", 0, blink_at(t, 1.3), (0, -0.3), t=t, arms="up"), 540, GROUND)
        pen = Pen(frame)
        pen.rect(370, 640, 710, 840, "white", 8, 10)
        pen.text(540, 700, "PICK ME!", 60, RED, 0)
        pen.text(540, 790, "PLEASE!!", 46, OUT, 0)
        st.tumbleweed(pen, -100 + v * 600, GROUND - 60, t, 55)
        label, old, new = "BEGGING", 0, -5
    pen = Pen(frame)
    counter(pen, old, new, v / CARD)
    pen.rect(40, 140, 560, 230, (30, 30, 40), 6, 18)
    pen.text(300, 185, f"{card + 1}. {label}", 50, GOLD, 0)
    return frame


def render_end(t, c):
    u = t - c["T"]["E"]
    return end_card(t, u, TITLE, "The Halftime Show", [
        (character("tank", 0, blink_at(t, 0), (0.4, 0), t=t, arms="wave"), 300, 1380, 0.9),
        (character("zippy", 0, blink_at(t, 1.3), (-0.4, 0), t=t, arms="wave"), 770, 1380 - abs(math.sin(t * 6)) * 40, 0.9)])


if __name__ == "__main__":
    toon.main(sys.modules[__name__], sys.argv[1] if len(sys.argv) > 1 else os.path.join(toon.HERE, "ep05_fantasy_football.mp4"))
