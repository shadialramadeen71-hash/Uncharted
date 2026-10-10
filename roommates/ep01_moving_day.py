"""Tank & Zippy: Roommates — Episode 1: Moving Day."""
import math, sys
from PIL import Image
import life as L
from life import casual, granny, Pen, S, GOLD, RED, OUT, GROUND
from toon import (place, burst, ease, blink_at, get_set, bg_copy, Timeline, star,
                  sfx_thud, sfx_crash, sfx_whoosh, sfx_pop, sfx_ding)

NAME = "rm01"
MUSIC = L.music("happy_ukulele.mp3")
TITLE = "Ep 1: Moving Day"
LINES = {
    "N1": ("narrator", "Tank and Zippy: Roommates. Episode one. Moving Day."),
    "Z1": ("zippy", "Tank! Our first apartment! Fourth floor!"),
    "T1": ("tank", "Fourth floor? There's an elevator, right?"),
    "G1": ("granny", "The elevator's broken, dearies. I'm Mrs. Pickles. Your landlady."),
    "T2": ("tank", "Great."),
    "N2": ("narrator", "Four floors later."),
    "T3": ("tank", "It... won't... fit."),
    "Z2": ("zippy", "Tilt it! Left! No, your OTHER left!"),
    "N3": ("narrator", "The couch fit. The door did not."),
    "G2": ("granny", "That's coming out of your deposit."),
    "Z3": ("zippy", "Welcome home, buddy!"),
    "T4": ("tank", "Home... sweet home."),
    "N4": ("narrator", "Next time, on Tank and Zippy: Breakfast Disaster!"),
}
SIDEWALK = 1330


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = L.say_all(tl, ["N1", "Z1", "T1"], 0.4, 0.3)
    T["granny"] = t
    tl.fx(sfx_ding(), t)
    t = L.say_all(tl, ["G1", "T2"], t + 0.5, 0.3)
    T["B"] = t + 0.3
    t = tl.say("N2", T["B"] + 0.3) + 0.2
    T["stuck"] = t
    for i in range(3):
        tl.fx(sfx_thud(), t + i * 0.45)
    t = tl.say("T3", t + 1.4) + 0.25
    T["tilt"] = t
    t = tl.say("Z2", t) + 0.3
    T["crash"] = t
    tl.fx(sfx_whoosh(0.5), t - 0.2); tl.fx(sfx_crash(1.0), t + 0.2)
    t = L.say_all(tl, ["N3"], t + 1.4, 0.3)
    T["granny2"] = t
    t = L.say_all(tl, ["G2", "Z3", "T4"], t + 0.4, 0.3)
    T["E"] = t + 0.8
    tl.fx(sfx_pop(), T["E"] + 0.1)
    T["end"] = tl.say("N4", T["E"] + 0.5) + 1.5
    return tl.result()


def couch_sprite(angle):
    layer = Image.new("RGBA", (900 * S, 700 * S), (0, 0, 0, 0))
    L.couch(Pen(layer), 450, 520, w=560, sc=0.8)
    return layer.rotate(angle, center=(450 * S, 450 * S), resample=Image.BICUBIC)


def put(frame, layer, x, y):
    """Place a 900x700 couch layer so its rotation centre (450, 450) lands at (x, y)."""
    frame.alpha_composite(layer, (int((x - 450) * S), int((y - 450) * S)))


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t < T["B"]:  # ---- outside the building
        frame = bg_copy(get_set("street", L.street))
        k = ease((t - 0.2) / 0.7)
        excited = key == "Z1"
        place(frame, casual("tank", m["tank"], blink_at(t, 0), (0.3, -0.6) if key == "T1" else (0.6, 0), t=t,
                            sad=key == "T2", arms="hold"), -250 + 520 * k, SIDEWALK + 140, sc=0.9)
        pen = Pen(frame)
        bx = -250 + 520 * k
        pen.rect(bx - 95, 1105, bx + 95, 1255, (200, 150, 95), 6, 6)
        pen.text(bx, 1180, "STUFF", 30, (120, 70, 40), 0)
        place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (-0.6, -0.4), t=t, arms="flail" if excited else "down"),
              1300 - 520 * k, SIDEWALK + 140 - (abs(math.sin(t * 9)) * 40 if excited else 0), sc=0.9)
        gk = ease((t - T["granny"]) / 0.5)
        if gk > 0:
            place(frame, granny(m["granny"], blink_at(t, 2.0), (0, 0.4), t, arms="wave" if key == "G1" else "cane"),
                  540, 1200 + 90 * (1 - gk), sc=0.7 * (0.6 + 0.4 * gk))
        L.title_card(frame, t, TITLE, y=230)
        if key == "T1":
            Pen(frame).text(270, 820, "4", 160, (255, 80, 80), 10)
        return frame
    if t < T["E"]:  # ---- fourth floor hallway
        frame = bg_copy(get_set("hall", L.hallway))
        pen = Pen(frame)
        crashed = t > T["crash"] + 0.2
        L.door(pen, fallen=crashed)
        if T["B"] < t < T["stuck"] + 2.0:
            Pen(frame).rect(380, 160, 700, 250, (40, 30, 30), 6, 20)
            Pen(frame).text(540, 205, "FLOOR 4", 54, GOLD, 0)
        # tank + couch
        walk = ease((t - T["B"] - 0.3) / 1.2)
        tx = -250 + 470 * walk
        ang = 0
        if T["stuck"] < t < T["crash"]:
            tx += -18 * abs(math.sin((t - T["stuck"]) * math.pi / 0.45)) if t < T["stuck"] + 1.35 else 0
        if T["tilt"] < t < T["crash"]:
            ang = 28 * math.sin((t - T["tilt"]) * 4.5)
        if t > T["crash"]:
            ck = ease((t - T["crash"]) / 0.35)
            tx = 220 + 320 * ck
        dizzy = crashed and t < T["granny2"]
        tank = casual("tank", m["tank"], blink_at(t, 0), (0.6, -0.5), t=t, arms="up", dizzy=dizzy, angry=key == "T3")
        place(frame, tank, tx, GROUND)
        put(frame, couch_sprite(ang), tx, GROUND - 676 - 120)
        if key == "T3":
            pen.ell(tx + 70, GROUND - 560, 14, 20, (120, 200, 255), 3)
        if crashed and t < T["crash"] + 0.9:
            u = t - T["crash"] - 0.2
            for i in range(10):
                a = i * math.pi / 5
                r = 80 + 500 * u
                Pen(frame).ell(540 + math.cos(a) * r, 1250 + math.sin(a) * r * 0.5, 60 * (1 - u), 50 * (1 - u), (220, 210, 190), 0)
            burst(frame, 540, 420, "CRASH!", 0.6 + u, RED)
        zx = 820
        place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (-1, -0.4), t=t,
                            arms="point" if key == "Z2" else ("wave" if key == "Z3" else "down")), zx, GROUND, sc=0.85)
        gk = ease((t - T["granny2"]) / 0.6)
        if gk > 0:
            place(frame, granny(m["granny"], blink_at(t, 2.0), (-1, 0), t), 1300 - 300 * gk, GROUND, sc=0.75)
        return frame
    return L.life_end_card(t, t - T["E"], TITLE, "Breakfast Disaster")


if __name__ == "__main__":
    L.run(sys.modules[__name__], "ep01_moving_day.mp4")
