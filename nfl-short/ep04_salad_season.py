"""Tank & Zippy — Episode 4: Salad Season."""
import math, os, sys, random
import toon
from toon import (Pen, GROUND, GOLD, RED, OUT, PURPLE, character, coach, place, burst, ease, blink_at, end_card,
                  get_set, bg_copy, star, Timeline, sfx_whoosh, sfx_boing, sfx_pop, sfx_sad_trombone, sfx_ding, sfx_crowd)
import sets as st

NAME = "ep04"
MUSIC = "the_fridge_is_hungry.ogg"
TITLE = "Episode 4: Salad Season"
LINES = {
    "N1": ("narrator", "Episode four. Salad Season."),
    "C1": ("coach", "Tank, the scale says... error."),
    "T1": ("tank", "It's the helmet. The helmet is heavy."),
    "C2": ("coach", "From now on: salad. Only salad."),
    "T2": ("tank", "Nooooooo!"),
    "N2": ("narrator", "Lunch time."),
    "T3": ("tank", "This is a leaf. I am eating one leaf."),
    "Z1": ("zippy", "Psst. Tank. Special delivery."),
    "T4": ("tank", "Zippy... you are a hero."),
    "C3": ("coach", "What is that smell?"),
    "Z2": ("zippy", "Smell? I smell nothing. I am a salad."),
    "C4": ("coach", "Is that... pepperoni?"),
    "Z3": ("zippy", "It's a tomato!"),
    "N3": ("narrator", "It was not a tomato."),
    "C5": ("coach", "Got any with extra cheese?"),
    "N4": ("narrator", "Next time, on Tank and Zippy: Fantasy Football!"),
}


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = tl.say("N1", 0.4) + 0.4
    T["weigh"] = t - 0.6
    t = tl.say("C1", t) + 0.25
    t = tl.say("T1", t) + 0.25
    t = tl.say("C2", t) + 0.2
    tl.fx(sfx_sad_trombone(), t)
    t = tl.say("T2", t) + 1.0
    T["B"] = t
    t = tl.say("N2", t + 0.3) + 0.3
    t = tl.say("T3", t) + 0.2
    T["zippy_in"] = t
    tl.fx(sfx_whoosh(0.5), t)
    t = tl.say("Z1", t + 0.5) + 0.2
    T["pizza"] = t
    tl.fx(sfx_boing(0.5), t); tl.fx(sfx_ding(), t + 0.1)
    t = tl.say("T4", t + 0.6) + 0.2
    T["coach_in"] = t
    tl.fx(sfx_whoosh(0.5), t)
    t = tl.say("C3", t + 0.5) + 0.15
    T["hide"] = t
    tl.fx(sfx_pop(), t)
    t = tl.say("Z2", t + 0.1) + 0.3
    t = tl.say("C4", t) + 0.2
    t = tl.say("Z3", t) + 0.3
    t = tl.say("N3", t) + 0.4
    t = tl.say("C5", t) + 0.1
    T["party"] = t
    tl.fx(sfx_ding(), t); tl.fx(sfx_crowd(2.0, 0.25), t)
    T["E"] = t + 2.4
    tl.fx(sfx_pop(), T["E"] + 0.1)
    T["end"] = tl.say("N4", T["E"] + 0.5) + 1.5
    return tl.result()


def scale_display(pen, reading, red):
    pen.rect(40, 560, 330, 760, (60, 60, 70), 7, 14)
    pen.rect(62, 585, 308, 735, (20, 40, 20), 0, 8)
    pen.text(185, 660, reading, 64 if len(reading) > 4 else 80, (255, 70, 70) if red else (120, 255, 120), 0)
    pen.rect(175, 760, 195, GROUND - 60, (150, 150, 160), 5)


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t < T["B"]:  # ---- gym weigh-in
        frame = bg_copy(get_set("gym", st.gym))
        pen = Pen(frame)
        w = t - T["weigh"]
        if w < 0:
            reading = "%03d" % random.Random(int(t * 12)).randint(100, 999)
        else:
            reading = "ERROR"
        scale_display(pen, reading, w >= 0 and int(t * 4) % 2 == 0)
        pen.rect(250, GROUND - 60, 620, GROUND, (200, 200, 210), 7, 10)
        drama = key == "T2"
        place(frame, character("tank", m["tank"], blink_at(t, 0), (0.6, -0.5 if drama else 0), t=t,
                               arms="flail" if drama else ("up" if key == "T1" else "down")), 435, GROUND - 60)
        k = ease((t - 0.3) / 0.6)
        place(frame, coach(m["coach"], blink_at(t, 0.7), (-1, 0), t, arms="point" if key == "C2" else "clipboard",
                           angry=key in ("C1", "C2")), 1300 - 450 * k, GROUND, sc=0.95)
        if t < 2.8:
            a = ease(t / 0.4) * (1 - ease((t - 2.4) / 0.4))
            Pen(frame, 540, 210, 0.6 + 0.4 * a).rect(-470, -140, 470, 120, (40, 30, 70), 7, 30)
            Pen(frame, 540, 160, 0.6 + 0.4 * a).text(0, 0, "TANK & ZIPPY", 110, GOLD, 12)
            Pen(frame, 540, 270, 0.6 + 0.4 * a).text(0, 0, TITLE, 52, "white", 7)
        if drama:
            Pen(frame).text(435, 520, "NOOO!", 90, (120, 200, 255), 8)
        return frame
    if t < T["E"]:  # ---- cafeteria
        frame = bg_copy(get_set("cafe", st.cafeteria))
        zk = ease((t - T["zippy_in"]) / 0.5)
        ck = ease((t - T["coach_in"]) / 0.6)
        party = t > T["party"]
        hide = T["hide"] < t < T["party"]
        pizza_out = t > T["pizza"]
        tank_happy = pizza_out and not hide
        place(frame, character("tank", m["tank"], blink_at(t, 0), (0.8 if pizza_out else 0, 0.6 if key == "T3" else 0), t=t,
                               arms="up" if party else "down"), 260, GROUND)
        if zk > 0:
            zx = 1300 - 680 * zk
            place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (-0.6, 0), t=t,
                                   arms="up" if party else ("flail" if key == "Z3" else "down")), zx,
                  GROUND - (abs(math.sin(t * 9)) * 30 if party else 0))
        if ck > 0:
            place(frame, coach(m["coach"], blink_at(t, 0.7), (-1, 0.2), t, arms="point" if key == "C4" else "clipboard",
                               angry=key in ("C3", "C4")), 1400 - 480 * ck, GROUND, sc=0.85)
        pen = Pen(frame)
        st.table(pen, 30, 1050, 1280)
        pen.ell(260, 1270, 110, 26, "white", 5)
        if not party:
            st.single_leaf(pen, 260, 1255)
        if pizza_out and not hide and not party:
            pk = ease((t - T["pizza"]) / 0.3)
            st.pizza(pen, 600, 1240 - 60 * math.sin(pk * math.pi), 150 * (0.4 + 0.6 * pk))
            for i in range(5):
                a = t * 3 + i * 1.3
                star(pen, 600 + math.cos(a) * 200, 1150 + math.sin(a) * 70, 18, GOLD)
            if tank_happy and key == "T4":
                star(pen, 225, 1068, 26, GOLD); star(pen, 295, 1068, 26, GOLD)
        if hide:
            st.pizza(Pen(frame), 620, 1090, 135)
            for i in range(3):
                y = 950 - ((t * 120 + i * 50) % 150)
                pen.line([(560 + i * 50 + 15 * math.sin(t * 6 + i + j * 0.6), y - j * 20) for j in range(6)], (140, 200, 90), 6)
        if party:
            st.pizza(pen, 540, 1240, 160)
            for x, y, a in ((390, 1090, 0.4), (700, 1110, -0.5), (900, 1080, 0.3)):
                st.pizza_slice(pen, x, y, a)
            st.confetti(frame, t, T["party"], 30)
            if t - T["party"] < 2.0:
                burst(frame, 540, 520, "PIZZA PARTY!", 0.7 + 0.1 * math.sin((t - T["party"]) * 18), (255, 170, 60))
        if key == "N2":
            Pen(frame).rect(320, 430, 760, 530, (30, 30, 40), 7, 18)
            Pen(frame).text(540, 480, "LUNCH TIME", 56, GOLD, 0)
        return frame
    u = t - T["E"]
    return end_card(t, u, TITLE, "Fantasy Football", [
        (character("tank", 0, blink_at(t, 0), (0.4, 0), t=t, arms="wave"), 300, 1380, 0.9),
        (character("zippy", 0, blink_at(t, 1.3), (-0.4, 0), t=t, arms="wave"), 770, 1380 - abs(math.sin(t * 6)) * 40, 0.9)])


if __name__ == "__main__":
    toon.main(sys.modules[__name__], sys.argv[1] if len(sys.argv) > 1 else os.path.join(toon.HERE, "ep04_salad_season.mp4"))
