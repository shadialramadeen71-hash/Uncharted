"""Tank & Zippy: Roommates — Episode 3: The Goldfish Sitters."""
import math, sys
from PIL import Image
import life as L
from life import casual, granny, Pen, S, W, H, GOLD, RED, OUT, GROUND
import sets as st
from toon import place, burst, ease, blink_at, get_set, bg_copy, Timeline, sfx_ding, sfx_pop, sfx_thud, star

NAME = "rm03"
MUSIC = L.music("bossa_nova_8bit.mp3")
TITLE = "Ep 3: The Goldfish Sitters"
LINES = {
    "N1": ("narrator", "Episode three. The Goldfish Sitters."),
    "G1": ("granny", "I'm off to bingo, dearies. Please watch Sir Bubbles. He's very sensitive."),
    "Z1": ("zippy", "Don't worry. We're professionals."),
    "T1": ("tank", "Since when?"),
    "Z2": ("zippy", "Tank, he looks bored."),
    "T2": ("tank", "He's a fish."),
    "Z3": ("zippy", "Let's show him the world!"),
    "N2": ("narrator", "Sir Bubbles had the best day of his life."),
    "G2": ("granny", "I'm back! Was he any trouble?"),
    "T3": ("tank", "Not at all."),
    "G3": ("granny", "Why is he wearing sunglasses?"),
    "Z4": ("zippy", "He's on vacation."),
    "N3": ("narrator", "Next time, on Tank and Zippy: The Haircut!"),
}
CARD = 2.2
SEAT = 1330


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = L.say_all(tl, ["N1", "G1", "Z1", "T1"], 0.4, 0.3)
    T["B"] = t + 0.3
    t = L.say_all(tl, ["Z2", "T2", "Z3"], T["B"] + 0.3, 0.3)
    T["M"] = t + 0.2
    for i in range(3):
        tl.fx(sfx_ding(), T["M"] + i * CARD)
    tl.say("N2", T["M"] + 2 * CARD + 0.3)
    T["C"] = T["M"] + 2 * CARD + 0.3 + dur["N2"] + 0.5
    for i in range(3):
        tl.fx(sfx_thud(0.15), T["C"] + 0.1 + i * 0.25)
    t = L.say_all(tl, ["G2", "T3", "G3", "Z4"], T["C"] + 1.0, 0.3)
    T["E"] = t + 0.8
    tl.fx(sfx_pop(), T["E"] + 0.1)
    T["end"] = tl.say("N3", T["E"] + 0.5) + 1.5
    return tl.result()


def bowl(t, sunglasses=False, sc=0.8):
    return lambda p, x, y: L.fishbowl(p, x, y + 60, t, sunglasses, sc)


def coffee_table(pen):
    pen.rect(330, 1440, 750, 1480, (170, 115, 70), 7, 10)
    for x in (370, 710):
        pen.rect(x - 12, 1480, x + 12, 1560, (130, 85, 50), 4)


def tv(pen, on=True, t=0.0):
    pen.rect(-40, 700, 260, 920, (30, 30, 35), 8, 12)
    pen.rect(-20, 720, 240, 900, (120, 200, 255) if on and int(t * 3) % 2 else (90, 160, 230), 0, 8)
    pen.rect(90, 920, 130, 980, (30, 30, 35), 4)


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t >= T["E"]:
        return L.life_end_card(t, t - T["E"], TITLE, "The Haircut")
    if t < T["B"] or t >= T["C"]:  # ---- hallway hand-over / return
        frame = bg_copy(get_set("hall", L.hallway))
        pen = Pen(frame)
        L.door(pen, open_k=1.0)
        back = t >= T["C"]
        handed = back or t > T["B"] - 3.0
        gx = 190 if not back else 190
        gk = 1.0 if not back else ease((t - T["C"] - 0.5) / 0.6)
        place(frame, granny(m["granny"], blink_at(t, 2.0), (1, 0), t, arms="hold" if not handed else "wave",
                            hold=bowl(t, sc=0.7) if not handed else None), -250 + (gx + 250) * gk, GROUND, sc=0.8)
        place(frame, casual("tank", m["tank"], blink_at(t, 0), (-0.5, 0), t=t, arms="hips" if key == "T1" else "down"),
              560, GROUND, sc=0.92)
        place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (-0.8, 0), t=t, arms="hold" if handed else "wave",
                            hold=bowl(t, sunglasses=back) if handed else None), 870, GROUND, sc=0.9)
        if key == "G3":
            burst(frame, 870, 620, "?!", 0.5, (255, 220, 80))
        L.title_card(frame, t, TITLE, y=200)
        return frame
    if t < T["M"]:  # ---- the couch
        frame = bg_copy(get_set("living", st.living_room))
        place(frame, casual("tank", m["tank"], blink_at(t, 0), (0.6, 0.5), t=t, arms="down"), 320, SEAT, sc=0.9)
        place(frame, casual("zippy", m["zippy"], blink_at(t, 1.3), (-0.2, 0.6), t=t,
                            arms="flail" if key == "Z3" else "down", sad=key == "Z2"), 740, SEAT, sc=0.9)
        st.couch_front(frame)
        pen = Pen(frame)
        coffee_table(pen)
        L.fishbowl(pen, 540, 1370, t, False, 0.8)
        if key == "Z2":
            pen.text(540, 1220, "...", 60, "white", 6)
        return frame
    # ---- montage
    u = t - T["M"]
    card = min(2, int(u // CARD))
    v = u - card * CARD
    if card == 0:
        frame = bg_copy(get_set("living", st.living_room))
        frame.alpha_composite(Image.new("RGBA", frame.size, (10, 10, 40, 150)))
        pen = Pen(frame)
        tv(pen, True, t)
        place(frame, casual("zippy", 0, False, (-1, 0), t=t, arms="down"), 760, SEAT, sc=0.9)
        st.couch_front(frame)
        pen = Pen(frame)
        coffee_table(pen)
        L.fishbowl(pen, 540, 1370, t, False, 0.8)
        for i in range(5):
            pen.ell(470 + i * 30, 1290 - (i % 2) * 14, 14, 12, (255, 245, 200), 3)
        label = "1. MOVIE NIGHT"
    elif card == 1:
        frame = bg_copy(get_set("living", st.living_room))
        st.stage_lights(frame, t, ((255, 120, 200), (120, 220, 255)))
        place(frame, casual("zippy", 0.5 + 0.5 * math.sin(t * 14), False, (-1, -0.3), t=t, arms="wave"), 760,
              GROUND - abs(math.sin(t * 8)) * 30, sc=0.95)
        pen = Pen(frame)
        st.mic_stand(pen, 640, GROUND)
        coffee_table(pen)
        L.fishbowl(pen, 450, 1370, t, False, 0.8)
        st.music_notes(pen, 640, 900, t)
        label = "2. KARAOKE"
    else:
        frame = bg_copy(get_set("bath", L.bathroom))
        pen = Pen(frame)
        place(frame, casual("zippy", 0, True, (0, 0), t=t, arms="up"), 360, 1420, sc=0.9)
        for sx in (-1, 1):
            pen.ell(360 + sx * 34, 1420 - 0.9 * 403, 26, 26, (140, 210, 120), 4)
        L.bathtub(pen, 80, 760, 1480, True, t)
        L.fishbowl(pen, 640, 1210, t, True, 0.75)
        label = "3. SPA DAY"
    pen = Pen(frame)
    pen.rect(40, 140, 560, 230, (30, 30, 40), 6, 18)
    pen.text(300, 185, label, 50, GOLD, 0)
    for i in range(4):
        a = t * 3 + i * math.pi / 2
        star(pen, 900 + math.cos(a) * 80, 260 + math.sin(a) * 40, 16, GOLD)
    return frame


if __name__ == "__main__":
    L.run(sys.modules[__name__], "ep03_goldfish_sitters.mp4")
