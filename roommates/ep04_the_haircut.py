"""Tank & Zippy: Roommates — Episode 4: The Haircut."""
import math, sys, random
import numpy as np
import life as L
from life import casual, granny, Pen, GOLD, RED, OUT, GROUND
from toon import SR, lowpass, place, burst, ease, blink_at, get_set, bg_copy, Timeline, star, sfx_ding, sfx_pop

NAME = "rm04"
MUSIC = L.music("silly_song.ogg")
TITLE = "Ep 4: The Haircut"
LINES = {
    "N1": ("narrator", "Episode four. The Haircut."),
    "T1": ("tank", "I need a haircut, but the barber is closed."),
    "Z1": ("zippy", "Say no more. I watched a video once."),
    "T2": ("tank", "Once?"),
    "Z2": ("zippy", "Half of one."),
    "N2": ("narrator", "Ten minutes later."),
    "T3": ("tank", "Zippy... why is it so breezy on the left?"),
    "Z3": ("zippy", "That's a style! It's called... the Half Moon."),
    "T4": ("tank", "Zippy."),
    "Z4": ("zippy", "Look on the bright side!"),
    "G1": ("granny", "Oh my! Tank, you look just like my late husband, Harold. So handsome!"),
    "T5": ("tank", "Thank you?"),
    "Z5": ("zippy", "Ah... ah... CHOO!"),
    "Z6": ("zippy", "Uh oh."),
    "N3": ("narrator", "Next time, on Tank and Zippy: The Camping Trip!"),
}
TX, ZX, STOOL = 430, 800, 250


def sfx_buzz(d=2.0):
    n = int(d * SR); t = np.arange(n) / SR
    saw = 2 * ((t * 118) % 1) - 1
    return 0.25 * lowpass(saw, 3) * (0.8 + 0.2 * np.sin(2 * np.pi * 9 * t)) * np.minimum(1, (d - t) / 0.05)


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = L.say_all(tl, ["N1", "T1", "Z1", "T2", "Z2"], 0.4, 0.3)
    T["buzz1"] = t
    tl.fx(sfx_buzz(2.2), t)
    t = tl.say("N2", t + 2.4) + 0.3
    T["half"] = t - 0.2
    t = L.say_all(tl, ["T3", "Z3"], t, 0.3)
    T["buzz2"] = t
    tl.fx(sfx_buzz(1.4), t)
    T["bald"] = t + 1.4
    tl.fx(sfx_ding(), T["bald"])
    t = L.say_all(tl, ["T4", "Z4"], T["bald"] + 0.3, 0.3)
    T["granny"] = t
    t = L.say_all(tl, ["G1", "T5"], t + 0.5, 0.3)
    t = tl.say("Z5", t) + 0.05
    T["sneeze"] = t
    tl.fx(sfx_buzz(0.35), t)
    t = tl.say("Z6", t + 0.6) + 0.9
    T["E"] = t
    tl.fx(sfx_pop(), t + 0.1)
    T["end"] = tl.say("N3", t + 0.5) + 1.5
    return tl.result()


def hair_particles(pen, t, t0, x, y):
    r = random.Random(int((t - t0) * 6))
    for i in range(14):
        u = ((t - t0) * 1.5 + i / 14) % 1
        a = r.uniform(-math.pi, 0)
        pen.line([(x + math.cos(a) * 160 * u, y + math.sin(a) * 100 * u + 500 * u * u),
                  (x + math.cos(a) * 160 * u + 14, y + math.sin(a) * 100 * u + 500 * u * u + 6)], (30, 24, 22), 5)


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t >= T["E"]:
        return L.life_end_card(t, t - T["E"], TITLE, "The Camping Trip")
    frame = bg_copy(get_set("bath", L.bathroom))
    pen = Pen(frame)
    hair = "full" if t < T["half"] else ("half" if t < T["bald"] else "bald")
    buzzing = (T["buzz1"] < t < T["buzz1"] + 2.2) or (T["buzz2"] < t < T["bald"])
    if T["buzz1"] + 2.2 < t < T["half"]:
        pen.rect(260, 140, 820, 260, (30, 30, 40), 7, 20)
        pen.text(540, 200, "10 MINUTES LATER...", 50, GOLD, 0)
    place(frame, casual("tank", m["tank"], blink_at(t, 0) or buzzing, (0.7, -0.3), t=t, hair=hair,
                        angry=key in ("T3", "T4"), sad=key == "T5" and False), TX, GROUND, sc=0.95)
    # barber cape
    neck_y = GROUND - 0.95 * 395
    pen.poly([(TX - 110, neck_y), (TX + 110, neck_y), (TX + 270, GROUND - 120), (TX - 270, GROUND - 120)], (245, 245, 250), 7)
    for i in range(4):
        pen.line([(TX - 60 + i * 40, neck_y + 30), (TX - 150 + i * 100, GROUND - 140)], (220, 220, 230), 4)
    if buzzing:
        hair_particles(pen, t, T["buzz1"], TX - 40, GROUND - 0.95 * 600)
    if hair == "bald" and t < T["bald"] + 3.0:
        k = t - T["bald"]
        star(pen, TX - 60, GROUND - 0.95 * 600, 40 + 20 * math.sin(k * 10), (255, 255, 230))
        if key == "Z4":
            burst(frame, 540, 330, "SHINE!", 0.7, (255, 240, 150))
    # zippy on a stool with clippers
    pen.rect(ZX - 90, GROUND - STOOL, ZX + 90, GROUND - STOOL + 30, (150, 100, 60), 6, 8)
    for dx in (-70, 70):
        pen.rect(ZX + dx - 10, GROUND - STOOL + 30, ZX + dx + 10, GROUND, (120, 80, 45), 4)
    sneeze = T["sneeze"] < t
    clip = lambda p, x, y: L.clippers(p, x - 120, y + 70, t if buzzing or (T["sneeze"] < t < T["sneeze"] + 0.35) else 0)
    place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3) or key == "Z5", (-1, -0.3), t=t, arms="hold", hold=clip,
                        brow_gone=sneeze, sad=key == "Z6"), ZX, GROUND - STOOL - (8 * math.sin(t * 30) if buzzing else 0))
    if T["sneeze"] < t < T["sneeze"] + 0.6:
        burst(frame, 540, 330, "ACHOO!", 0.7, (150, 220, 255))
    gk = ease((t - T["granny"]) / 0.6)
    if gk > 0:
        place(frame, granny(m["granny"], blink_at(t, 2.0), (-1, -0.3), t, arms="wave" if key == "G1" else "cane"),
              1320 - 320 * gk, GROUND, sc=0.72)
        if key == "G1":
            for i in range(3):
                pen.ell(960 + i * 30, 900 - ((t * 80 + i * 30) % 100), 12, 10, (240, 90, 130), 0)
    L.title_card(frame, t, TITLE, y=200)
    return frame


if __name__ == "__main__":
    L.run(sys.modules[__name__], "ep04_the_haircut.mp4")
