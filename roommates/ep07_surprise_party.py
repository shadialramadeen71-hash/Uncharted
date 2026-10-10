"""Tank & Zippy: Roommates — Episode 7: The Surprise Party."""
import math, sys
from PIL import Image
import life as L
from life import casual, granny, Pen, GOLD, RED, OUT, GROUND
import sets as st
from toon import (place, burst, ease, blink_at, get_set, bg_copy, Timeline, star,
                  sfx_pop, sfx_whoosh, sfx_thud, sfx_crowd, sfx_ding)

NAME = "rm07"
MUSIC = L.music("rolling_circus.mp3")
TITLE = "Ep 7: The Surprise Party"
LINES = {
    "N1": ("narrator", "Episode seven. The Surprise Party. Today is Zippy's birthday."),
    "T1": ("tank", "Mrs. Pickles, keep Zippy busy for one hour. I'm planning a surprise party."),
    "G1": ("granny", "My lips are sealed, dear."),
    "G2": ("granny", "Zippy! Tank is definitely NOT planning a surprise party for you!"),
    "Z1": ("zippy", "What?"),
    "T2": ("tank", "Mrs. Pickles!"),
    "N2": ("narrator", "One hour later. Lights off. Everybody hide."),
    "T3": ("tank", "SURPRISE!"),
    "Z2": ("zippy", "Surprise! I already knew. So I brought YOU a present!"),
    "T4": ("tank", "Buddy... it's YOUR birthday."),
    "Z3": ("zippy", "I know. But the best gift is having a roommate like you."),
    "G3": ("granny", "Make a wish, dear!"),
    "T5": ("tank", "Happy birthday, buddy."),
    "N3": ("narrator", "Next time, on Tank and Zippy: the season finale. Moving Out?"),
}


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = L.say_all(tl, ["N1", "T1", "G1"], 0.4, 0.3)
    T["zippy_in"] = t
    t = L.say_all(tl, ["G2", "Z1", "T2"], t + 0.5, 0.3)
    T["B"] = t + 0.3
    t = tl.say("N2", T["B"] + 0.3) + 0.4
    T["door"] = t
    tl.fx(sfx_thud(0.2), t)
    T["lights"] = t + 0.6
    tl.fx(sfx_pop(), T["lights"]); tl.fx(sfx_crowd(1.5, 0.25), T["lights"])
    t = tl.say("T3", T["lights"]) + 0.3
    t = L.say_all(tl, ["Z2", "T4"], t, 0.3)
    T["open"] = t
    tl.fx(sfx_ding(), t)
    t = L.say_all(tl, ["Z3", "G3"], t + 0.2, 0.3)
    T["blow"] = t + 0.3
    tl.fx(sfx_whoosh(0.8), T["blow"]); tl.fx(sfx_thud(), T["blow"] + 0.5)
    t = tl.say("T5", T["blow"] + 1.6) + 1.0
    T["E"] = t
    tl.fx(sfx_pop(), t + 0.1)
    T["end"] = tl.say("N3", t + 0.5) + 1.5
    return tl.result()


def photo(pen, x, y):
    pen.rect(x - 120, y - 170, x + 120, y, (200, 150, 80), 7, 6)
    pen.rect(x - 100, y - 150, x + 100, y - 20, (190, 230, 250), 0, 4)
    pen.ell(x - 40, y - 70, 38, 38, (150, 95, 60), 4)
    pen.ell(x + 45, y - 75, 30, 30, (255, 214, 170), 4)
    for i in range(5):
        pen.poly([(x + 20 + i * 12, y - 100), (x + 26 + i * 12, y - 120), (x + 32 + i * 12, y - 100)], (235, 120, 40), 0)
    pen.text(x, y - 135, "BEST ROOMMATES", 22, OUT, 0)
    for i in range(4):
        star(pen, x - 140 + i * 95, y - 210 - 10 * (i % 2), 16, GOLD)


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t >= T["E"]:
        return L.life_end_card(t, t - T["E"], TITLE, "Moving Out?", sprites=[
            (casual("tank", 0, blink_at(t, 0), (0.4, 0), arms="wave", t=t, outfit="tank_party"), 300, 1380, 0.9),
            (casual("zippy", 0, blink_at(t, 1.3), (-0.4, 0), arms="wave", t=t, outfit="zippy_party"), 770,
             1380 - abs(math.sin(t * 6)) * 40, 0.9)])
    if t < T["B"]:  # ---- hallway: the leak
        frame = bg_copy(get_set("hall", L.hallway))
        L.door(Pen(frame))
        whisper = key == "T1"
        place(frame, casual("tank", m["tank"], blink_at(t, 0), (1, 0.4), t=t, arms="facepalm" if key == "T2" else "down",
                            angry=key == "T2"), 300, GROUND, sc=0.95)
        place(frame, granny(m["granny"], blink_at(t, 2.0), (-1 if t < T["zippy_in"] else 1, 0), t,
                            arms="wave" if key == "G2" else "cane"), 590, GROUND, sc=0.78)
        zk = ease((t - T["zippy_in"]) / 0.6)
        if zk > 0:
            place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (-1, 0), t=t, arms="down"), 1300 - 430 * zk, GROUND, sc=0.88)
        if whisper:
            Pen(frame).text(450, 760, "psst...", 50, "white", 6)
        if key == "G1":
            Pen(frame).text(590, 900, "shh!", 50, "white", 6)
        if key == "Z1":
            burst(frame, 870, 640, "?!", 0.5, (255, 220, 80))
        L.title_card(frame, t, TITLE, y=200)
        return frame
    frame = bg_copy(get_set("living", st.living_room))
    lights = t > T["lights"]
    L.party_decor(frame, t)
    opened = t > T["open"]
    b = t - T["blow"]
    place(frame, casual("tank", m["tank"], blink_at(t, 0), (1, 0), t=t, outfit="tank_party",
                        arms="up" if key == "T3" else ("hold" if key == "T5" else "down"), sad=key == "T4"), 340, GROUND)
    place(frame, granny(m["granny"], blink_at(t, 2.0), (1, 0), t, arms="wave" if key in ("T3", "G3") else "cane"), 100, GROUND, sc=0.72)
    zk = ease((t - T["door"]) / 0.5)
    if zk > 0:
        hold = (lambda p, x, y: L.gift(p, x, y + 40)) if not opened else None
        place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (-1, 0), t=t, outfit="zippy_party",
                            arms="hold" if hold else ("up" if key == "Z2" else "down"), hold=hold, cheeks=True),
              1300 - 420 * zk, GROUND, sc=0.88)
    pen = Pen(frame)
    if opened and b < 0:
        photo(pen, 880, 780)
    # cake on a little table
    pen.rect(470, 1440, 790, 1480, (170, 115, 70), 7, 10)
    for x in (500, 760):
        pen.rect(x - 12, 1480, x + 12, 1560, (130, 85, 50), 4)
    L.cake(pen, 630, 1440, candles=True, lit=b < 0.2, t=t)
    if 0 < b < 0.5:
        for i in range(5):
            y = 1150 + i * 40
            pen.line([(870 - b * 400, y), (760 - b * 400, y)], "white", 8)
    if b > 0.3:
        k = min(1, (b - 0.3) / 0.25)
        fx, fy = 630 + (340 - 630) * k, 1330 + (960 - 1330) * k - 150 * math.sin(k * math.pi)
        pen.ell(fx, fy, 70 + 30 * k, 50 + 30 * k, (250, 230, 240), 5)
        pen.ell(fx - 20, fy - 10, 20, 14, (240, 120, 160), 0)
        if 0.55 < b < 1.4:
            burst(frame, 540, 470, "SPLAT!", 0.6, (240, 120, 160))
    if not lights:
        dark = Image.new("RGBA", frame.size, (5, 5, 20, 215))
        frame.alpha_composite(dark)
        pen = Pen(frame)
        for x, y in ((305, 950), (375, 950), (85, 1195), (118, 1195)):
            pen.ell(x, y, 14, 18, "white", 0)
            pen.ell(x + 3, y, 6, 8, OUT, 0)
    if T["lights"] < t < T["lights"] + 1.5:
        burst(frame, 540, 470, "SURPRISE!", 0.75 + 0.1 * math.sin(t * 20), GOLD)
        st.confetti(frame, t, T["lights"], 40)
    return frame


if __name__ == "__main__":
    L.run(sys.modules[__name__], "ep07_surprise_party.mp4")
