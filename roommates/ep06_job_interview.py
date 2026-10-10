"""Tank & Zippy: Roommates — Episode 6: The Job Interview."""
import math, sys
import life as L
from life import casual, granny, Pen, GOLD, RED, OUT, GROUND
import sets as st
from toon import place, burst, ease, blink_at, get_set, bg_copy, Timeline, star, sfx_pop, sfx_crash, sfx_ding, sfx_boing

NAME = "rm06"
MUSIC = L.music("taking_you_to_the_circus.mp3")
TITLE = "Ep 6: The Job Interview"
LINES = {
    "N1": ("narrator", "Episode six. The Job Interview."),
    "T1": ("tank", "Remember, buddy: be confident, be calm, and do NOT eat the product."),
    "Z1": ("zippy", "Confident. Calm. Don't eat. Got it."),
    "N2": ("narrator", "Pickles' Ice Cream. Wait... Mrs. Pickles owns an ice cream shop?"),
    "G1": ("granny", "Welcome, Zippy. Why do you want this job?"),
    "Z2": ("zippy", "Because I love ice cream! I AM ice cream!"),
    "G2": ("granny", "Show me how you make a cone."),
    "Z3": ("zippy", "Seven scoops! For customer satisfaction!"),
    "N3": ("narrator", "He ate the product."),
    "G3": ("granny", "You're hired. As our official taste tester!"),
    "Z4": ("zippy", "Best. Day. Ever!"),
    "T2": ("tank", "Did you eat the product?"),
    "Z5": ("zippy", "I AM the product."),
    "N4": ("narrator", "Next time, on Tank and Zippy: The Surprise Party!"),
}
SCOOPS = 7
SPLAT = [((255, 190, 210), -40, -60, 46), ((150, 90, 60), 30, -90, 40), ((180, 230, 180), 50, -10, 30),
         ((250, 245, 230), -55, 20, 34), ((255, 220, 120), 0, -130, 36), ((200, 160, 230), 20, 60, 30)]


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = L.say_all(tl, ["N1", "T1", "Z1"], 0.4, 0.3)
    T["B"] = t + 0.3
    t = L.say_all(tl, ["N2", "G1", "Z2", "G2"], T["B"] + 0.3, 0.3)
    T["scoop"] = t
    for i in range(SCOOPS):
        tl.fx(sfx_pop(), t + 0.2 + i * 0.35)
    t = tl.say("Z3", t + 0.3 + SCOOPS * 0.35) + 0.3
    T["fall"] = t
    tl.fx(sfx_crash(0.8), t + 0.4)
    t = L.say_all(tl, ["N3", "G3"], t + 1.4, 0.3)
    tl.fx(sfx_ding(), t)
    t = tl.say("Z4", t) + 0.3
    T["tank_in"] = t
    t = L.say_all(tl, ["T2", "Z5"], t + 0.6, 0.3)
    T["E"] = t + 0.8
    tl.fx(sfx_pop(), T["E"] + 0.1)
    T["end"] = tl.say("N4", T["E"] + 0.5) + 1.5
    return tl.result()


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t >= T["E"]:
        return L.life_end_card(t, t - T["E"], TITLE, "The Surprise Party")
    if t < T["B"]:  # ---- pep talk at home
        frame = bg_copy(get_set("living", st.living_room))
        place(frame, casual("tank", m["tank"], blink_at(t, 0), (0.7, 0.2), t=t, arms="point" if key == "T1" else "hips"),
              300, GROUND)
        place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (-0.7, 0), t=t, outfit="zippy_suit",
                            arms="hips" if key == "Z1" else "down"), 790, GROUND, sc=0.95)
        L.title_card(frame, t, TITLE, y=230)
        return frame
    frame = bg_copy(get_set("shop", L.ice_cream_shop))
    pen = Pen(frame)
    n = 0 if t < T["scoop"] else min(SCOOPS, int((t - T["scoop"] - 0.2) / 0.35) + 1)
    fell = t > T["fall"] + 0.4
    hired = t > T["tank_in"] - 1.5
    place(frame, granny(m["granny"], blink_at(t, 2.0), (1, -0.4 if n > 4 else 0), t,
                        arms="wave" if key == "G3" else "cane"), 260, GROUND, sc=0.85)
    holding = not fell and t > T["scoop"]
    nervous = key == "Z2"
    zippy = casual("zippy", m["zippy"], blink_at(t, 1.3), (-0.6, -1 if n > 3 and not fell else 0), t=t, outfit="zippy_suit",
                   arms="point" if holding else ("up" if key == "Z4" else "down"), cheeks=fell)
    zx = 680
    place(frame, zippy, zx, GROUND - (abs(math.sin(t * 9)) * 30 if key == "Z4" else 0), sc=0.95)
    head_y = GROUND - 0.95 * 400
    if holding:
        L.cone(pen, zx + 165, 1185, n, t)
    if nervous:
        pen.ell(zx + 70, head_y - 40 + (t * 60) % 30, 12, 18, (120, 200, 255), 3)
    f = t - T["fall"]
    if 0 < f < 0.4:
        for i in range(SCOOPS):
            k = f / 0.4
            pen.ell(zx + 165 * (1 - k) + 30 * math.sin(i) * k, 1145 - i * 52 + (head_y + i * 52 - 1145) * k, 44, 36,
                    [(255, 190, 210), (250, 245, 230), (150, 90, 60), (180, 230, 180), (255, 220, 120), (200, 160, 230)][i % 6], 5)
    if fell:
        for col, dx, dy, r in SPLAT:
            pen.ell(zx + dx, head_y + dy, r, r * 0.8, col, 4)
        if f < 1.0:
            burst(frame, 540, 470, "SPLAT!", 0.6 + f * 0.3, (255, 150, 190))
    if key == "Z3":
        for i in range(3):
            pen.text(zx + 160, head_y - 400 + 30 * math.sin(t * 8 + i), "!", 80, GOLD, 6)
    if hired:
        pen.rect(560, 1500, 820, 1560, GOLD, 5, 14)
        pen.text(690, 1530, "TASTE TESTER", 32, OUT, 0)
    tk = ease((t - T["tank_in"]) / 0.6)
    if tk > 0:
        place(frame, casual("tank", m["tank"], blink_at(t, 0), (-1, 0), t=t, arms="hips"), 1350 - 360 * tk, GROUND, sc=0.9)
    if key == "N2":
        pen.text(540, 650, "?!", 120, (240, 80, 120), 10)
    return frame


if __name__ == "__main__":
    L.run(sys.modules[__name__], "ep06_job_interview.mp4")
