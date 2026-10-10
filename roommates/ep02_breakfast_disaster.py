"""Tank & Zippy: Roommates — Episode 2: Breakfast Disaster."""
import math, sys
import numpy as np
import life as L
from life import casual, granny, Pen, GOLD, RED, OUT, GROUND
from toon import (SR, place, burst, ease, blink_at, get_set, bg_copy, Timeline, sfx_boing, sfx_pop, sfx_whoosh, sfx_thud)

NAME = "rm02"
MUSIC = L.music("happy_awkward_trumpet.mp3")
TITLE = "Ep 2: Breakfast Disaster"
LINES = {
    "N1": ("narrator", "Episode two. Breakfast Disaster."),
    "Z1": ("zippy", "Good morning! Chef Zippy is making pancakes!"),
    "T1": ("tank", "Have you ever made pancakes before?"),
    "Z2": ("zippy", "How hard can it be?"),
    "N2": ("narrator", "Very hard. It was very hard."),
    "Z3": ("zippy", "Time for the big flip!"),
    "Z4": ("zippy", "Where did it go?"),
    "T2": ("tank", "Buddy... look up."),
    "T3": ("tank", "Breakfast... is served."),
    "G1": ("granny", "Is something burning, dearies?"),
    "Z5": ("zippy", "Just my dreams, Mrs. Pickles."),
    "G2": ("granny", "Ooh, pancakes! Don't mind if I do."),
    "N3": ("narrator", "Next time, on Tank and Zippy: The Goldfish Sitters!"),
}
TX, ZX, STOOL = 250, 620, 200
PX = ZX - 210


def sfx_beeps(d=2.4):
    n = int(d * SR); t = np.arange(n) / SR
    gate = (t % 0.4) < 0.18
    return 0.22 * np.sign(np.sin(2 * np.pi * 3100 * t)) * gate


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = L.say_all(tl, ["N1", "Z1", "T1", "Z2"], 0.4, 0.3)
    T["smoke"] = t
    tl.fx(sfx_beeps(3.0), t + 0.4)
    t = tl.say("N2", t + 0.3) + 0.4
    t = tl.say("Z3", t) + 0.1
    T["flip"] = t
    tl.fx(sfx_whoosh(0.4), t); tl.fx(sfx_thud(), t + 0.4)
    t = L.say_all(tl, ["Z4", "T2"], t + 0.8, 0.3)
    T["fall"] = t + 0.4
    tl.fx(sfx_thud(), T["fall"] + 0.35)
    t = tl.say("T3", T["fall"] + 1.0) + 0.3
    T["granny"] = t
    t = L.say_all(tl, ["G1", "Z5"], t + 0.5, 0.3)
    T["grab"] = t
    tl.fx(sfx_pop(), t + 0.2)
    t = tl.say("G2", t) + 0.9
    T["E"] = t
    tl.fx(sfx_pop(), t + 0.1)
    T["end"] = tl.say("N3", t + 0.5) + 1.5
    return tl.result()


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t >= T["E"]:
        return L.life_end_card(t, t - T["E"], TITLE, "The Goldfish Sitters")
    frame = bg_copy(get_set("kitchen", L.kitchen))
    pen = Pen(frame)
    alarm = T["smoke"] + 0.4 < t < T["smoke"] + 3.4
    pen.rect(480, 0, 600, 40, (240, 240, 240), 5, 10)
    pen.ell(540, 40, 22, 14, (255, 60, 60) if alarm and int(t * 5) % 2 else (150, 150, 150), 4)
    # pancake state
    f = t - T["flip"]
    fall = t - T["fall"]
    tank_face = fall > 0.35 and t < T["grab"] + 0.3
    look_up = key in ("T2",) or (key == "Z4")
    # tank in pajamas with coffee
    place(frame, casual("tank", m["tank"], blink_at(t, 0) or (t < T["smoke"] and not key == "T1"), (0.6, -1 if look_up else 0),
                        t=t, outfit="tank_pj", arms="hold", hold=L.mug), TX, GROUND, sc=0.95)
    if tank_face:
        pen.ell(TX, 955, 105, 92, (225, 170, 90), 6)
        pen.ell(TX - 30, 930, 20, 12, (200, 140, 70), 0)
        pen.ell(TX + 35, 975, 16, 10, (200, 140, 70), 0)
    # zippy on a stool with the pan
    pen.rect(ZX - 90, GROUND - STOOL, ZX + 90, GROUND - STOOL + 30, (150, 100, 60), 6, 8)
    for dx in (-70, 70):
        pen.rect(ZX + dx - 10, GROUND - STOOL + 30, ZX + dx + 10, GROUND, (120, 80, 45), 4)
    hop = abs(math.sin(t * 9)) * 25 if key == "Z1" else 0
    place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (0, -1) if look_up else (-0.6, 0), t=t, outfit="zippy_chef",
                        arms="up" if 0 < f < 0.5 else "hold", sad=key == "Z5"), ZX, GROUND - STOOL - hop)
    smoke = 0.0 if t < T["smoke"] else min(1.0, (t - T["smoke"]) / 1.0)
    if f < 0:
        L.frying_pan(Pen(frame), PX, 1010, smoke, t, pancake=True)
    else:
        L.frying_pan(Pen(frame), PX, 1010 if f > 0.5 else 760, smoke * 0.5, t, pancake=False)
        if fall < 0:
            k = min(1, f / 0.4)
            py = 1000 + (45 - 1000) * k
            if k < 1:
                pen.ell(PX, py, 75, 18, (225, 170, 90), 4)
            else:
                pen.ell(PX, 45, 95, 28, (225, 170, 90), 5)
                for i in range(3):
                    pen.ell(ZX - 90 + i * 50, 80 + 10 * math.sin(t * 3 + i), 8, 14, (225, 170, 90), 0)
                if f < 0.9:
                    burst(frame, 540, 360, "SPLAT!", 0.6 + f * 0.3, (225, 170, 90))
        elif fall < 0.35:
            k = fall / 0.35
            pen.ell(PX + (TX - ZX + 40) * k, 45 + (955 - 45) * k * k, 90, 30 + 30 * k, (225, 170, 90), 5)
    gk = ease((t - T["granny"]) / 0.6)
    if gk > 0:
        grabbed = t > T["grab"] + 0.3
        place(frame, granny(m["granny"], blink_at(t, 2.0), (-1, 0), t, arms="hold" if grabbed else "cane"), 1300 - 380 * gk,
              GROUND, sc=0.75)
        if grabbed:
            eat = max(0.15, 1 - (t - T["grab"] - 0.3) / 2.5)
            pen.ell(920, 1300, 70 * eat, 22 * eat, (225, 170, 90), 4)
    if key == "N2":
        Pen(frame).text(540, 620, "BEEP! BEEP!", 70, (255, 80, 80), 8)
    L.title_card(frame, t, TITLE, y=270)
    return frame


if __name__ == "__main__":
    L.run(sys.modules[__name__], "ep02_breakfast_disaster.mp4")
