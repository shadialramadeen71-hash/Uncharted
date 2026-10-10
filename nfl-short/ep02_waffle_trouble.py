"""Tank & Zippy — Episode 2: Waffle Trouble."""
import math, os, sys
from PIL import Image
import toon
from toon import (Pen, AX, AY, SPR_W, SPR_H, S, W, H, GROUND, PURPLE, GOLD, RED, OUT, character, coach, place,
                  world_view, burst, football, star, ease, blink_at, yellow_flag, sfx_crowd, sfx_whoosh, sfx_whistle,
                  sfx_thud, sfx_boing, sfx_crash, sfx_pop)

NAME = "ep02"
LINES = {
    "N1": ("narrator", "Episode two. Waffle Trouble."),
    "C1": ("coach", "Bad news, boys. Our mascot ate gas station sushi."),
    "T1": ("tank", "Oh no. Not Sir Syrup!"),
    "C2": ("coach", "We need a new waffle. Someone small. Someone brave."),
    "Z1": ("zippy", "Why is everyone looking at me?"),
    "N2": ("narrator", "Ten minutes later."),
    "Z2": ("zippy", "I look delicious."),
    "T2": ("tank", "You look like breakfast."),
    "N3": ("narrator", "Then came the rival mascot. Mister Spicy."),
    "S1": ("spicy", "Nice costume, pancake!"),
    "Z3": ("zippy", "I am a WAFFLE!"),
    "S2": ("spicy", "Watch and learn, breakfast boy!"),
    "Z4": ("zippy", "Oh yeah? Watch THIS!"),
    "Z5": ("zippy", "Whoa, whoa, whoa, whoa!"),
    "N4": ("narrator", "The referees had questions."),
    "T3": ("tank", "Coach... can a waffle score a touchdown?"),
    "C3": ("coach", "Absolutely not."),
    "Z6": ("zippy", "Can someone help me up? I live here now."),
    "N5": ("narrator", "Next time, on Tank and Zippy: The Gatorade Shower!"),
}

WAFFLE, WAFFLE_DK, SYRUP = (232, 178, 85), (196, 136, 55), (140, 70, 20)
SKIN_Z = (255, 214, 170)


# ---------------------------------------------------------------- new characters
def waffle_zippy(mouth=0.0, blink=False, look=(0, 0), t=0.0, ball=False, dizzy=False, arms="out", sweat=False):
    img = Image.new("RGBA", (SPR_W * S, SPR_H * S), (0, 0, 0, 0))
    pen = Pen(img, AX, AY)
    lh, half = 105, 185
    cy = -lh - half
    for sx in (-1, 1):
        pen.limb([(sx * 55, -lh - 10), (sx * 55, -22)], (240, 240, 240), 38)
        pen.ell(sx * 67, -16, 46, 19, (30, 30, 35))
    if arms == "up":
        hands = [(-half - 70, cy - 170), (half + 70, cy - 170)]
    elif arms == "flail":
        hands = [(-half - 110, cy - 60 + 70 * math.sin(t * 25)), (half + 110, cy - 60 - 70 * math.sin(t * 25))]
    else:
        hands = [(-half - 95, cy + 40 + 8 * math.sin(t * 3)), (half + 95, cy + 40 + 8 * math.sin(t * 3 + 1))]
    for sx, hnd in zip((-1, 1), hands):
        pen.limb([(sx * (half - 10), cy + 20), hnd], PURPLE, 30)
        pen.ell(hnd[0], hnd[1], 24, 24, SKIN_Z)
    # waffle body
    pen.rect(-half, cy - half, half, cy + half, WAFFLE, 8, 40)
    for i in range(4):
        for j in range(4):
            x0, y0 = -half + 26 + i * 84, cy - half + 26 + j * 84
            if 1 <= i <= 2 and 1 <= j <= 2:
                continue
            pen.rect(x0, y0, x0 + 64, y0 + 64, WAFFLE_DK, 0, 10)
    pen.rect(-50, cy - half - 30, 50, cy - half + 30, (255, 235, 120), 6, 10)  # butter
    for dx, ln in ((-120, 90), (-30, 50), (90, 120), (150, 60)):  # syrup drips
        pen.rect(dx - 14, cy - half - 4, dx + 14, cy - half + ln, SYRUP, 0, 14)
        pen.ell(dx, cy - half + ln, 17, 17, SYRUP, 0)
    pen.rect(-half + 10, cy - half - 6, half - 10, cy - half + 22, SYRUP, 0, 12)
    # face hole
    pen.ell(0, cy, 100, 100, (120, 70, 30), 7)
    pen.ell(0, cy + 4, 88, 88, SKIN_Z, 0)
    for sx in (-1, 1):
        cx, ey = sx * 32, cy - 10
        if dizzy:
            pts = [(cx + math.cos(t * 9 * sx + i * 0.5) * 22 * i / 14, ey + math.sin(t * 9 * sx + i * 0.5) * 22 * i / 14) for i in range(15)]
            pen.ell(cx, ey, 24, 28, "white", 4); pen.line(pts, OUT, 5)
        elif blink:
            pen.line([(cx - 22, ey), (cx + 22, ey)], OUT, 7)
        else:
            pen.ell(cx, ey, 24, 29, "white", 4)
            pen.ell(cx + look[0] * 10, ey + look[1] * 10, 11, 11, OUT, 0)
            pen.ell(cx + look[0] * 10 - 4, ey + look[1] * 10 - 4, 3, 3, "white", 0)
        pen.line([(cx - 18, ey - 38), (cx + 18, ey - 42)], OUT, 6)
    my = cy + 45
    if mouth > 0.1:
        pen.ell(0, my, 20 + 8 * mouth, 5 + 22 * mouth, (110, 20, 30), 5)
    else:
        pen.line([(math.cos(a) * 24, my - 8 + math.sin(a) * 14) for a in [0.3 + i * 0.25 for i in range(11)]], OUT, 6)
    if sweat:
        pen.ell(78, cy - 50 + (t * 60) % 30, 12, 18, (120, 200, 255), 3)
    if ball:
        football(pen, half - 30, cy - half + 40, 40, 0.7)
        pen.ell(half - 60, cy - half + 85, 24, 14, SYRUP, 0)
    if dizzy:
        for i in range(4):
            a = t * 4 + i * math.pi / 2
            star(pen, math.cos(a) * 200, cy - half - 70 + math.sin(a) * 40, 22, GOLD)
    return img


def spicy(mouth=0.0, blink=False, look=(0, 0), t=0.0, arms="hips", fallen=False):
    """Mister Spicy: the rival team's giant hot-sauce-bottle mascot."""
    img = Image.new("RGBA", (SPR_W * S, SPR_H * S), (0, 0, 0, 0))
    pen = Pen(img, AX, AY)
    lh, bw, bh = 110, 270, 430
    top = -lh - bh
    for sx in (-1, 1):
        pen.limb([(sx * 60, -lh - 10), (sx * 60, -22)], (40, 40, 45), 34)
        pen.ell(sx * 74, -16, 50, 19, (240, 240, 240))
    sh = top + 170
    if arms == "up":
        hands = [(-230, top + 20 + 30 * math.sin(t * 12)), (230, top + 20 - 30 * math.sin(t * 12))]
    elif arms == "flail":
        hands = [(-260, sh - 40 + 60 * math.sin(t * 22)), (260, sh - 40 - 60 * math.sin(t * 22))]
    else:
        hands = [(-200, -lh - 150), (200, -lh - 150)]
    for sx, hnd in zip((-1, 1), hands):
        elbow = ((sx * bw / 2 + hnd[0]) / 2 + sx * 40, (sh + hnd[1]) / 2 - 20)
        pen.limb([(sx * (bw / 2 - 15), sh), elbow, hnd], (40, 40, 45), 26)
        pen.ell(hnd[0], hnd[1], 26, 26, "white")
    # flames on top
    for i, dx in enumerate((-40, 0, 40)):
        fh = 90 + 25 * math.sin(t * 14 + i * 2)
        pen.poly([(dx - 30, top - 70), (dx, top - 70 - fh), (dx + 30, top - 70)], (255, 140, 30), 5)
        pen.poly([(dx - 14, top - 70), (dx, top - 70 - fh * 0.55), (dx + 14, top - 70)], (255, 220, 60), 0)
    pen.rect(-55, top - 80, 55, top - 10, (40, 150, 60), 6, 12)  # cap
    pen.poly([(-60, top - 8), (60, top - 8), (bw / 2, top + 110), (-bw / 2, top + 110)], RED, 7)  # neck
    pen.rect(-bw / 2, top + 100, bw / 2, -lh, RED, 7, 50)
    pen.rect(-bw / 2 + 25, top + 250, bw / 2 - 25, -lh - 40, (255, 245, 225), 6, 16)
    pen.text(0, top + 300, "SPICY", 58, RED, 0)
    pen.poly([(0, top + 340), (30, top + 400), (0, -lh - 55), (-30, top + 400)], (255, 140, 30), 4)
    # face
    fy = top + 170
    for sx in (-1, 1):
        cx = sx * 50
        if blink:
            pen.line([(cx - 22, fy), (cx + 22, fy)], OUT, 7)
        elif fallen:
            pen.line([(cx - 20, fy - 20), (cx + 20, fy + 20)], OUT, 8)
            pen.line([(cx - 20, fy + 20), (cx + 20, fy - 20)], OUT, 8)
        else:
            pen.ell(cx, fy, 26, 30, "white", 4)
            pen.ell(cx + look[0] * 10, fy + look[1] * 10, 11, 11, OUT, 0)
        pen.line([(cx - sx * 30, fy - 52), (cx + sx * 24, fy - 34)], OUT, 11)
    my = fy + 62
    if mouth > 0.1:
        pen.ell(0, my, 40, 8 + 26 * mouth, (90, 10, 20), 5)
    else:  # smug grin
        pen.line([(math.cos(a) * 46, my - 12 + math.sin(a) * 20) for a in [0.2 + i * 0.27 for i in range(11)]], OUT, 7)
    return img


def end_zone(pen, x0):
    pen.poly([(x0, 905), (x0 + 900, 905), (x0 + 600, H), (x0 - 300, H)], (110, 60, 165), 0)
    pen.poly([(x0, 905), (x0 + 14, 905), (x0 - 286, H), (x0 - 300, H)], (245, 245, 245), 0)
    pen.text(x0 + 220, 1010, "WAFFLES", 80, GOLD, 7)


# ---------------------------------------------------------------- timeline
def build_timeline(dur):
    ev, sfx, T = [], [], {}

    def say(key, t):
        ev.append((key, t)); return t + dur[key]

    sfx.append((sfx_crowd(3.0, 0.15), 0.0))
    t = say("N1", 0.4) + 0.4
    t = say("C1", t) + 0.25
    t = say("T1", t) + 0.25
    t = say("C2", t) + 0.2
    T["stare"] = t
    sfx.append((sfx_boing(0.4), t))
    t = say("Z1", t + 0.3) + 0.5
    T["B"] = t
    sfx.append((sfx_pop(), t + 0.2))
    t = say("N2", t + 0.2) + 0.3
    t = say("Z2", t) + 0.25
    t = say("T2", t) + 0.5
    T["C"] = t
    sfx.append((sfx_whoosh(0.8), t + 0.2))
    sfx.append((sfx_crowd(2.5, 0.2), t + 0.5))
    T["spicy_in"] = t + 0.2
    t = say("N3", t + 0.3) + 0.3
    t = say("S1", t) + 0.2
    t = say("Z3", t) + 0.2
    T["battle"] = t
    sfx.append((sfx_crowd(1.5, 0.3), t))
    t = say("S2", t + 0.9) + 0.1
    T["spin"] = t
    sfx.append((sfx_whoosh(0.9), t))
    t += 1.2
    t = say("Z4", t) + 0.2
    T["D"] = t
    rate = T["tumble_rate"] = 1.5  # quarter turns per second
    for i in range(3):
        sfx.append((sfx_thud(), t + (i + 1) / rate))
    say("Z5", t + 0.2)
    T["hit"] = t + 0.6
    sfx.append((sfx_crash(0.8), T["hit"]))
    T["ball"] = t + 0.62
    sfx.append((sfx_boing(), T["ball"] + 0.45))
    T["D2"] = t + 2.4
    for i in range(3):
        sfx.append((sfx_thud(), T["D2"] + (i + 1) / rate))
    T["td"] = T["D2"] + 3 / rate + 0.15
    sfx.append((sfx_crowd(3.0, 0.45), T["td"]))
    T["E"] = T["td"] + 2.0
    sfx.append((sfx_whistle(), T["E"]))
    t = say("N4", T["E"] + 0.8) + 0.3
    t = say("T3", t) + 0.25
    t = say("C3", t) + 0.35
    t = say("Z6", t) + 0.8
    T["F"] = t
    sfx.append((sfx_pop(), t + 0.2))
    t = say("N5", t + 0.5) + 1.5
    T["end"] = t
    T["captions_off"] = T["F"]
    return ev, sfx, T


# ---------------------------------------------------------------- scenes
def tumble_pose(u, rate):
    """Square waffle rolling to the right: returns (x offset, lift, angle)."""
    q = u * rate
    k = int(q); f = q - k
    f = f * f * (3 - 2 * f)
    phi = f * 90
    lift = 185 * (math.sqrt(2) * math.cos(math.radians(45 - phi)) - 1)
    return (k + f) * 370, lift, -(k * 90 + phi)


def render_scene(t, c):
    T, m, who, key = c["T"], c["m"], c["who"], c["key"]
    world = c["world"]
    if t < T["B"]:  # ---- sideline meeting
        frame = world_view(world, 200)
        stare = t > T["stare"]
        k = ease((t - 0.2) / 0.6)
        place(frame, coach(m["coach"], blink_at(t, 0.7), (1, 0) if stare else (0.6, 0), t,
                           arms="point" if key == "C2" else "clipboard", angry=key == "C1"), -200 + 400 * k, GROUND, sc=0.95)
        place(frame, character("tank", m["tank"], blink_at(t, 0), (1, 0) if stare else (-0.6, 0), t=t,
                               arms="flail" if key == "T1" else "down"), 560, GROUND, sc=0.9)
        place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (-0.6, 0), t=t,
                               arms="hips" if key == "Z1" else "down"), 905, GROUND, sc=0.9)
        if t < 2.6:
            a = ease(t / 0.4) * (1 - ease((t - 2.2) / 0.4))
            Pen(frame, 540, 300, 0.6 + 0.4 * a).text(0, 0, "TANK & ZIPPY", 120, GOLD, 12)
            Pen(frame, 540, 420, 0.6 + 0.4 * a).text(0, 0, "Episode 2: Waffle Trouble", 56, "white", 7)
        if stare:
            pen = Pen(frame)
            for i in range(3):
                pen.text(905 - 60 + i * 60, 760 - 20 * math.sin(t * 6 + i), "!", 90, GOLD, 8)
    elif t < T["C"]:  # ---- the costume
        frame = world_view(world, 650)
        u = t - T["B"]
        if u < 0.35:
            Pen(frame).ell(700, 1150, 400 * (1 - u / 0.35) + 50, 400 * (1 - u / 0.35) + 50, "white", 0)
        place(frame, character("tank", m["tank"], blink_at(t, 0), (0.7, 0), t=t, arms="hips"), 260, GROUND)
        place(frame, waffle_zippy(m["zippy"], blink_at(t, 1.3), (-0.6, 0), t, arms="up" if key == "Z2" else "out"),
              740, GROUND - (abs(math.sin(t * 8)) * 25 if key == "Z2" else 0))
        if key == "N2" or (key is None and u < 1.8):
            Pen(frame).rect(240, 280, 840, 400, (30, 30, 40), 7, 20)
            Pen(frame).text(540, 340, "10 MINUTES LATER...", 54, GOLD, 0)
    elif t < T["D"]:  # ---- dance battle
        frame = world_view(world, 900)
        k = ease((t - T["spicy_in"]) / 0.5)
        sx = 1500 - 690 * k
        spin = (t - T["spin"]) / 1.1
        ang = 720 * ease(spin) if 0 < spin < 1 else 0
        place(frame, spicy(m["spicy"], blink_at(t, 2.1), (-1, 0), t, arms="up" if 0 < spin < 1.2 else "hips"),
              sx, GROUND, sc=0.85, angle=ang, pivot_up=330)
        if k < 1:
            pen = Pen(frame)
            for i in range(4):
                pen.line([(sx + 150 + i * 20, 1000 + i * 90), (sx + 380 + i * 30, 1000 + i * 90)], (255, 160, 40), 12)
        angry = key == "Z3"
        shake = 10 * math.sin(t * 60) if angry else 0
        place(frame, waffle_zippy(m["zippy"], blink_at(t, 1.3), (1, 0), t, arms="flail" if angry else "out",
                                  sweat=0 < spin < 1.5), 280 + shake, GROUND, sc=0.9)
        if T["battle"] < t < T["battle"] + 1.0:
            burst(frame, 540, 420, "DANCE BATTLE!", 0.7 + 0.15 * math.sin((t - T["battle"]) * 20), (120, 200, 255))
        if 0 < spin < 1:
            pen = Pen(frame)
            for i in range(6):
                a = t * 8 + i * math.pi / 3
                star(pen, sx + math.cos(a) * 260, 1100 + math.sin(a) * 200, 22, GOLD)
    elif t < T["D2"]:  # ---- the tumble
        u = t - T["D"]
        frame = world_view(world, 900)
        dx, lift, ang = tumble_pose(u, T["tumble_rate"])
        zx = 280 + dx
        hit = t > T["hit"]
        if not hit:
            place(frame, spicy(m["spicy"], blink_at(t, 2.1), (-1, 0), t), 810, GROUND, sc=0.85)
        else:
            h = t - T["hit"]
            place(frame, spicy(0, False, (0, 0), t, arms="flail", fallen=True), 810 + 500 * h, GROUND - 1300 * h + 1500 * h * h,
                  sc=0.85, angle=-900 * h, pivot_up=330)
            if h < 0.6:
                burst(frame, 540, 420, "STRIKE!", 0.7 + h, RED)
        b = t - T["ball"]
        ball = b > 0.45
        if 0 < b <= 0.45:
            football(Pen(frame), zx + 120, -100 + 1100 * (b / 0.45) ** 2, 40, b * 14)
        place(frame, waffle_zippy(m["zippy"], False, (1, -1), t, ball=ball, arms="flail"), zx, GROUND - lift,
              sc=0.9, angle=ang, pivot_up=290)
        if 0.45 < b < 0.9:
            burst(frame, 540, 420, "STICKY!", 0.6 + (b - 0.45), (180, 110, 40))
    elif t < T["E"]:  # ---- touchdown
        u = t - T["D2"]
        frame = world_view(world, 300)
        end_zone(Pen(frame), 620)
        stop_at = 3 / T["tumble_rate"]
        dx, lift, ang = tumble_pose(min(u, stop_at), T["tumble_rate"])
        place(frame, waffle_zippy(m["zippy"], False, (1, -1), t, ball=True, arms="flail", dizzy=u > stop_at),
              -350 + dx, GROUND - lift, sc=0.9, angle=ang, pivot_up=290)
        if t > T["td"]:
            burst(frame, 540, 420, "TOUCHDOWN!", 0.75 + 0.1 * math.sin((t - T["td"]) * 16), GOLD)
            pen = Pen(frame)
            for i in range(24):
                x = (i * 137 + (t - T["td"]) * 90 * (1 + i % 3)) % 1080
                y = ((t - T["td"]) * 500 * (1 + i % 4) + i * 77) % 900
                pen.rect(x, y, x + 18, y + 30, [GOLD, PURPLE, "white", RED][i % 4], 0, 3)
    elif t < T["F"]:  # ---- the ruling
        u = t - T["E"]
        frame = world_view(world, 300)
        end_zone(Pen(frame), 620)
        flag = min(1, u / 0.6)
        place(frame, waffle_zippy(m["zippy"], blink_at(t, 1.3), (-0.5, -0.5), t, ball=True, arms="flail" if key == "Z6" else "out"),
              780, GROUND - 25, sc=0.9, angle=90, pivot_up=290)
        kc = ease((u - 0.2) / 0.8)
        place(frame, character("tank", m["tank"], blink_at(t, 0), (0.8, 0.3), t=t, arms="flail" if kc < 1 else "hips"),
              -300 + 560 * kc, GROUND, sc=0.9)
        place(frame, coach(m["coach"], blink_at(t, 0.7), (0.8, 0.2), t, arms="facepalm" if key == "C3" else "clipboard",
                           angry=True), -500 + 630 * kc, GROUND + 60, sc=0.8)
        yellow_flag(Pen(frame), 120 + 450 * flag, 250 + 1150 * flag ** 2, (1 - flag) * 8)
        if 0.8 < u and key in ("N4", None) and u < 4:
            pen = Pen(frame)
            for i, (x, y) in enumerate(((220, 380), (540, 330), (860, 380))):
                pen.text(x, y + 15 * math.sin(t * 5 + i), "?", 150, "white", 10)
    else:  # ---- end card
        u = t - T["F"]
        frame = Image.new("RGBA", (W * S, H * S), PURPLE + (255,))
        pen = Pen(frame)
        for i in range(14):
            a = i * math.pi / 7 + u * 0.4
            pen.poly([(540, 1000), (540 + math.cos(a) * 1600, 1000 + math.sin(a) * 1600),
                      (540 + math.cos(a + 0.22) * 1600, 1000 + math.sin(a + 0.22) * 1600)], (110, 60, 165), 0)
        k = ease(u / 0.4)
        Pen(frame, 540, 260, 0.3 + 0.7 * k).text(0, 0, "TANK & ZIPPY", 120, GOLD, 12)
        Pen(frame, 540, 380, 0.3 + 0.7 * k).text(0, 0, "Episode 2: Waffle Trouble", 56, "white", 7)
        place(frame, character("tank", m["tank"], blink_at(t, 0), (0.4, 0), t=t, arms="wave"), 300, 1380, sc=0.9)
        place(frame, waffle_zippy(m["zippy"], blink_at(t, 1.3), (-0.4, 0), t, ball=True, arms="up"),
              770, 1380 - abs(math.sin(t * 6)) * 40, sc=0.85)
        k2 = ease((u - 0.6) / 0.4)
        Pen(frame, 540, 1580, 0.4 + 0.6 * k2).text(0, 0, "NEXT TIME:", 60, "white", 8)
        Pen(frame, 540, 1680, 0.4 + 0.6 * k2).text(0, 0, "The Gatorade Shower", 80, GOLD, 10)
        Pen(frame, 540, 1810, 0.4 + 0.6 * k2).text(0, 0, "FOLLOW FOR MORE!", 56, "white", 7)
    return frame


if __name__ == "__main__":
    toon.main(sys.modules[__name__],
              sys.argv[1] if len(sys.argv) > 1 else os.path.join(toon.HERE, "ep02_waffle_trouble.mp4"))
