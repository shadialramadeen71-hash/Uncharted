"""Tank & Zippy — Episode 6: The Halftime Show."""
import math, os, sys
import numpy as np
import toon
from toon import (Pen, GROUND, GOLD, RED, OUT, PURPLE, SR, character, coach, place, burst, ease, blink_at, end_card,
                  get_set, bg_copy, star, Timeline, sfx_crowd, sfx_whoosh, sfx_pop, sfx_drum, sfx_crash, sfx_boing)
import sets as st

NAME = "ep06"
MUSIC = "entry_of_the_gladiators.mp3"
TITLE = "Episode 6: The Halftime Show"
LINES = {
    "N1": ("narrator", "Episode six. The Halftime Show."),
    "C1": ("coach", "The singer is stuck in traffic?! Halftime starts in one minute!"),
    "Z1": ("zippy", "Don't worry, Coach. Tank can sing!"),
    "T1": ("tank", "I only know opera."),
    "C2": ("coach", "Do it. Just... do it."),
    "N2": ("narrator", "Ladies and gentlemen... the halftime show!"),
    "T2": ("tank", "Ooooooh... waaaaffles... my looooove!"),
    "N3": ("narrator", "The crowd was... confused."),
    "Z2": ("zippy", "Hit it!"),
    "Z3": ("zippy", "Drum solo!"),
    "C3": ("coach", "They... love it?"),
    "T3": ("tank", "Thank you. I'll be here all week."),
    "N4": ("narrator", "Next time, on Tank and Zippy: Rivalry Week!"),
}
BULBS = [100 + i * 110 for i in range(9)]


def sfx_crickets(d=2.5):
    n = int(d * SR); t = np.arange(n) / SR
    gate = (np.sin(2 * np.pi * 3 * t) > 0.3) * (np.sin(2 * np.pi * 40 * t) > 0)
    return 0.12 * np.sin(2 * np.pi * 4600 * t) * gate


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = tl.say("N1", 0.4) + 0.4
    for k in ("C1", "Z1", "T1", "C2"):
        t = tl.say(k, t) + 0.25
    T["B"] = t + 0.3
    tl.fx(sfx_crowd(2.5, 0.4), T["B"])
    t = tl.say("N2", T["B"] + 0.4) + 0.3
    T["sing"] = t
    t = tl.say("T2", t) + 0.3
    for i in range(4):
        tl.fx(sfx_pop(), T["sing"] + 0.7 + i * 0.55)
    tl.fx(sfx_crickets(), t)
    t = tl.say("N3", t + 0.6) + 0.6
    T["zippy_in"] = t
    tl.fx(sfx_whoosh(0.5), t)
    t = tl.say("Z2", t + 0.4) + 0.1
    T["drums"] = t
    for i in range(14):
        tl.fx(sfx_drum(), t + i * 0.22)
    tl.say("Z3", t + 0.5)
    T["boom"] = t + 2.0
    tl.fx(sfx_crash(0.9), T["boom"])
    tl.fx(sfx_crowd(4.0, 0.5), T["boom"] + 0.3)
    t = T["boom"] + 3.2
    T["coach_in"] = t
    t = tl.say("C3", t + 0.3) + 0.3
    t = tl.say("T3", t) + 1.0
    T["E"] = t
    tl.fx(sfx_pop(), t + 0.1)
    T["end"] = tl.say("N4", t + 0.5) + 1.5
    return tl.result()


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t < T["B"]:  # ---- backstage panic
        frame = bg_copy(get_set("backstage", st.backstage))
        k = ease((t - 0.2) / 0.6)
        on_phone = key in (None, "N1", "C1") and t < T["B"] - 3
        place(frame, coach(m["coach"], blink_at(t, 0.7), (1, 0), t, arms="facepalm" if on_phone else ("point" if key == "C2" else "clipboard"),
                           angry=True), -200 + 400 * k, GROUND, sc=0.9)
        if on_phone:
            Pen(frame).rect(175, 1035, 215, 1105, (40, 40, 60), 5, 8)
        place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (1 if key == "Z1" else -1, 0), t=t,
                               arms="flail" if key == "Z1" else "down"), 520, GROUND, sc=0.85)
        place(frame, character("tank", m["tank"], blink_at(t, 0), (-0.8, 0), t=t, arms="hips" if key == "T1" else "down"),
              1300 - 470 * k, GROUND, sc=0.9)
        if t < 2.8:
            a = ease(t / 0.4) * (1 - ease((t - 2.4) / 0.4))
            Pen(frame, 540, 160, 0.6 + 0.4 * a).rect(-480, -100, 480, 160, (40, 30, 70), 7, 30)
            Pen(frame, 540, 160, 0.6 + 0.4 * a).text(0, 0, "TANK & ZIPPY", 110, GOLD, 12)
            Pen(frame, 540, 270, 0.6 + 0.4 * a).text(0, 0, TITLE, 48, "white", 7)
        if key == "C1":
            Pen(frame).text(820, 400, "1:00", 110, (255, 80, 60), 10)
        return frame
    if t < T["E"]:  # ---- the stage
        frame = bg_copy(get_set("stage", st.concert_stage))
        pen = Pen(frame)
        boom = t > T["boom"]
        hue = int(t * 3) % 3
        screen_txt = "ENCORE!" if boom else ("TANK" if t > T["sing"] else "HALFTIME")
        pen.text(540, 440, screen_txt, 130, [GOLD, (120, 220, 255), (255, 120, 200)][hue] if boom else GOLD, 0)
        for i, x in enumerate(BULBS):
            popped = T["sing"] + 0.7 + (i % 4) * 0.55 < t and i % 2 == 0 and not boom
            pen.ell(x, 110, 26, 26, (60, 60, 70) if popped else (255, 245, 180), 5)
        if not boom or int(t * 6) % 2:
            st.stage_lights(frame, t)
        singing = key == "T2"
        place(frame, character("tank", m["tank"], blink_at(t, 0) or singing, (0.6, -0.3), t=t,
                               arms="up" if boom else ("wave" if singing else "down")), 380, GROUND)
        st.mic_stand(Pen(frame), 560, GROUND)
        if singing:
            st.music_notes(Pen(frame), 560, 900, t)
        zk = ease((t - T["zippy_in"]) / 0.4)
        if zk > 0:
            drumming = t > T["drums"]
            place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (0, 0.4) if drumming else (-1, 0), t=t,
                                   arms="flail" if drumming else "up"), 1300 - 470 * zk,
                  GROUND - 90 - (abs(math.sin(t * 14)) * 25 if drumming else 0), sc=0.8)
            st.drum(Pen(frame), 830, GROUND, t, drumming and int((t - T["drums"]) / 0.22 * 2) % 2 == 0 and not boom)
        if boom:
            b = t - T["boom"]
            for j, x0 in enumerate((150, 930, 540)):
                for i in range(10):
                    a = i * math.pi / 5 + j
                    r = 60 + 380 * min(1, (b + j * 0.3) % 1.4)
                    star(Pen(frame), x0 + math.cos(a) * r, 700 + j * 120 + math.sin(a) * r * 0.7, 20, [GOLD, (255, 120, 200), (120, 220, 255)][j])
            if b < 2.5:
                burst(frame, 540, 250, "ENCORE!", 0.75 + 0.1 * math.sin(b * 18), (255, 120, 200))
        if key == "N3":
            Pen(frame).text(540, 760, "...", 150, "white", 10)
        ck = ease((t - T["coach_in"]) / 0.5)
        if ck > 0:
            place(frame, coach(m["coach"], blink_at(t, 0.7), (1, -0.3), t, arms="clipboard"), -260 + 360 * ck, GROUND, sc=0.85)
        st.crowd_heads(frame, t, 1.0 if boom else 0.0)
        return frame
    u = t - T["E"]
    return end_card(t, u, TITLE, "Rivalry Week", [
        (character("tank", 0, blink_at(t, 0), (0.4, 0), t=t, arms="wave"), 300, 1380, 0.9),
        (character("zippy", 0, blink_at(t, 1.3), (-0.4, 0), t=t, arms="wave"), 770, 1380 - abs(math.sin(t * 6)) * 40, 0.9)],
        bg=(40, 15, 70), rays=(65, 25, 105))


if __name__ == "__main__":
    toon.main(sys.modules[__name__], sys.argv[1] if len(sys.argv) > 1 else os.path.join(toon.HERE, "ep06_halftime_show.mp4"))
