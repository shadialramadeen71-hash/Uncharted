"""Tank & Zippy: Roommates — Episode 5: The Camping Trip."""
import math, sys
import numpy as np
from PIL import Image, ImageDraw
import life as L
from life import casual, granny, Pen, S, GOLD, RED, OUT, GROUND
from toon import (SR, lowpass, rng, place, burst, ease, blink_at, get_set, bg_copy, Timeline, star,
                  sfx_thud, sfx_whoosh, sfx_pop, sfx_boing, sfx_wind)

NAME = "rm05"
MUSIC = L.music("miniature_saloon.mp3")
TITLE = "Ep 5: The Camping Trip"
LINES = {
    "N1": ("narrator", "Episode five. The Camping Trip."),
    "Z1": ("zippy", "Fresh air! Nature! No Wi-Fi!"),
    "T1": ("tank", "Wait. No Wi-Fi?!"),
    "N2": ("narrator", "Step one: build the tent."),
    "Z2": ("zippy", "I'm okay!"),
    "Z3": ("zippy", "Fire! FIRE!"),
    "N3": ("narrator", "Then... something moved in the bushes."),
    "T3": ("tank", "Zippy... do bears eat roommates?"),
    "Z4": ("zippy", "BEAR!"),
    "G1": ("granny", "Yoo-hoo! I brought hot cocoa!"),
    "T4": ("tank", "Mrs. Pickles?! How did you find us?"),
    "G2": ("granny", "I followed the screaming, dear."),
    "N4": ("narrator", "Next time, on Tank and Zippy: The Job Interview!"),
}
TENT_X = 330


def sfx_rustle(d=1.5):
    n = int(d * SR); t = np.arange(n) / SR
    x = lowpass(rng.standard_normal(n), 3) - lowpass(rng.standard_normal(n), 20)
    return 0.6 * x * (np.sin(2 * np.pi * 5 * t) > 0) * np.minimum(1, (d - t) / 0.1)


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    tl.fx(sfx_wind(3.0), 0)
    t = L.say_all(tl, ["N1", "Z1", "T1"], 0.4, 0.3)
    t = tl.say("N2", t + 0.2) + 0.2
    T["build"] = t
    T["collapse"] = t + 1.4
    tl.fx(sfx_thud(), T["collapse"])
    t = tl.say("Z2", T["collapse"] + 1.2) + 0.5
    T["B"] = t
    T["burn"] = t + 1.2
    t = tl.say("Z3", T["burn"] + 0.3) + 0.1
    T["fly"] = t
    tl.fx(sfx_whoosh(0.6), t)
    tl.fx(sfx_rustle(2.0), t + 1.4)
    t = tl.say("N3", t + 1.0) + 0.3
    t = tl.say("T3", t) + 0.2
    T["jump"] = t
    tl.fx(sfx_boing(), t)
    t = tl.say("Z4", t) + 0.6
    T["granny"] = t
    tl.fx(sfx_rustle(0.8), t)
    t = L.say_all(tl, ["G1", "T4", "G2"], t + 0.6, 0.3)
    T["E"] = t + 0.8
    tl.fx(sfx_pop(), T["E"] + 0.1)
    T["end"] = tl.say("N4", T["E"] + 0.5) + 1.5
    return tl.result()


def flashlight(t):
    def draw(p, x, y):
        p.rect(x - 16, y - 20, x + 16, y + 60, (60, 60, 70), 4, 6)
        p.rect(x - 24, y - 40, x + 24, y - 16, (200, 200, 210), 4, 6)
    return draw


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t >= T["E"]:
        return L.life_end_card(t, t - T["E"], TITLE, "The Job Interview")
    frame = bg_copy(get_set("forest", L.forest))
    if t < T["B"]:  # ---- the tent
        pen = Pen(frame)
        if t < T["build"]:
            L.tent(pen, TENT_X, 1440, collapse=1.0, t=0)
        elif t < T["collapse"]:
            L.tent(pen, TENT_X, 1440, collapse=1 - ease((t - T["build"]) / 1.0), t=t)
        else:
            L.tent(pen, TENT_X, 1440, collapse=1.0, t=t)
            if t < T["collapse"] + 0.6:
                burst(frame, 540, 520, "FLOOMP!", 0.6 + (t - T["collapse"]), (240, 140, 40))
        inside = t > T["collapse"]
        if not inside:
            place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (0.6, 0), t=t, outfit="zippy_camp",
                                arms="up" if key == "Z1" else "down"), TENT_X + 120, GROUND, sc=0.85)
        place(frame, casual("tank", m["tank"], blink_at(t, 0), (-0.8, 0), t=t, outfit="tank_camp",
                            arms="hold", sad=key == "T1"), 790, GROUND, sc=0.95)
        pen = Pen(frame)
        pen.line([(TENT_X + 200, 1300), (690, GROUND - 0.95 * 340)], (230, 220, 190), 5)
        if key == "T1":
            burst(frame, 790, 560, "NO WI-FI?!", 0.55, (120, 200, 255))
        L.title_card(frame, t, TITLE, y=230)
        return frame
    # ---- campfire
    pen = Pen(frame)
    L.tent(pen, 130, 1250, collapse=0.0, t=t)
    shake = 12 * math.sin(t * 40) if T["fly"] + 1.4 < t < T["granny"] + 0.6 else 0
    if t < T["granny"] + 0.4:
        L.bush(pen, 1000, 1290, eyes=T["fly"] + 1.6 < t < T["granny"], shake=shake)
    L.glow(frame, 520, 1430, 430)
    L.campfire(Pen(frame), 520, 1500, t)
    jumped = t > T["jump"]
    burning = T["burn"] < t < T["fly"]
    stick = (lambda p, x, y: L.marshmallow_stick(p, x - 30, y, burning, t)) if t < T["fly"] else None
    if not jumped:
        place(frame, casual("tank", m["tank"], blink_at(t, 0), (1, -0.3), t=t, outfit="tank_camp",
                            arms="down", sad=key == "T3"), 230, GROUND, sc=0.95)
        place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (1 if t > T["fly"] else -0.6, 0), t=t, outfit="zippy_camp",
                            arms="hold" if stick else "flail" if key == "Z3" else "down", hold=stick), 760, GROUND, sc=0.85)
    else:
        place(frame, casual("tank", m["tank"], False, (1, -0.3), t=t, outfit="tank_camp", arms="hold"), 300, GROUND, sc=0.95)
        place(frame, casual("zippy", m["zippy"], False, (1, 0), t=t, outfit="zippy_camp", arms="flail" if key == "Z4" else "down"),
              330, GROUND - 330 - 12 * math.sin(t * 30) * (key == "Z4"), sc=0.8, angle=-25, pivot_up=200)
    f = t - T["fly"]
    if 0 < f < 1.4:
        pen = Pen(frame)
        k = f / 1.4
        mx, my = 900 + (1000 - 900) * k, 1000 - 700 * math.sin(k * math.pi)
        pen.rect(mx - 20, my - 20, mx + 20, my + 20, (90, 60, 40), 4, 10)
        for i in range(3):
            pen.poly([(mx - 15 + i * 12, my - 18), (mx - 9 + i * 12, my - 60), (mx - 3 + i * 12, my - 18)], (255, 150, 30), 3)
    gk = ease((t - T["granny"]) / 0.6)
    if gk > 0:
        place(frame, granny(m["granny"], blink_at(t, 2.0), (-1, 0), t, arms="hold", fur=True, hold=flashlight(t)),
              1050 - 200 * gk, GROUND, sc=0.75)
        beam = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        ImageDraw.Draw(beam).polygon([(800 * S, 1240 * S), (820 * S, 1210 * S), (300 * S, 700 * S), (180 * S, 900 * S)],
                                     fill=(255, 250, 200, 60))
        frame.alpha_composite(beam)
    if key == "Z4":
        burst(frame, 560, 520, "BEAR!!", 0.8 + 0.1 * math.sin(t * 30), RED)
    return frame


if __name__ == "__main__":
    L.run(sys.modules[__name__], "ep05_camping_trip.mp4")
