"""Backgrounds for Maskville.

Screen is 1080x1920.  World ground line is y = 0; the camera maps world
(cam.x, cam.y) to screen centre (540, 960) with zoom cam.z.
"""
import math
import random

import cairo

from characters import INK, TAU, col, ellipse, fill_ink, hexc, path_poly, rrect, shade

W, H = 1080, 1920


def apply_cam(ctx, cam, parallax=1.0):
    ctx.translate(W / 2, H / 2)
    ctx.scale(cam["z"], cam["z"])
    ctx.translate(-cam["x"] * parallax, -cam["y"])


def visible_range(cam, parallax=1.0, pad=700):
    half = W / 2 / cam["z"] + pad
    c = cam["x"] * parallax
    return c - half, c + half


def text_center(ctx, txt, x, y, size, color, font="Luckiest Guy", outline=None):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    e = ctx.text_extents(txt)
    ctx.move_to(x - e.width / 2 - e.x_bearing, y)
    ctx.text_path(txt)
    if outline:
        col(ctx, outline[0])
        ctx.set_line_width(outline[1])
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    col(ctx, color)
    ctx.fill()


def sky(ctx, top, bottom):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *top[:3])
    g.add_color_stop_rgb(1, *bottom[:3])
    ctx.set_source(g)
    ctx.paint()


def sunflower(ctx, x, y, s, t, seed):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(0.08 * math.sin(t * 1.5 + seed))
    ctx.scale(s, s)
    for i in range(12):
        a = i * TAU / 12
        ctx.save()
        ctx.rotate(a)
        ellipse(ctx, 0, -34, 11, 22)
        fill_ink(ctx, hexc("#ffc928"), 3)
        ctx.restore()
    ctx.arc(0, 0, 22, 0, TAU)
    fill_ink(ctx, hexc("#7a3e12"), 4)
    ctx.restore()


class Scene:
    def draw_bg(self, ctx, cam, t, v):
        pass

    def draw_fg(self, ctx, cam, t, v):
        pass


# --------------------------------------------------------------------------

HOUSE_COLS = ["#ffb3c7", "#9ad7ff", "#ffe08a", "#b9f0a8", "#d6b8ff", "#ffc49b"]


class StreetDay(Scene):
    def draw_bg(self, ctx, cam, t, v):
        sky(ctx, hexc("#62c6ff"), hexc("#d8f4ff"))
        # sun
        ctx.save()
        ctx.translate(860, 260)
        ctx.rotate(t * 0.15)
        for i in range(12):
            ctx.save()
            ctx.rotate(i * TAU / 12)
            path_poly(ctx, [(-14, -120), (14, -120), (0, -175)])
            col(ctx, hexc("#ffd84a", 0.8))
            ctx.fill()
            ctx.restore()
        ctx.restore()
        ctx.arc(860, 260, 95, 0, TAU)
        fill_ink(ctx, hexc("#ffe066"), 6)
        # clouds
        for i in range(6):
            x = (i * 430 - cam["x"] * 0.12 + t * 14) % 2600 - 500
            y = 170 + (i % 3) * 120
            for dx, dy, r in ((0, 0, 50), (55, -20, 62), (115, 0, 48), (60, 18, 50)):
                ctx.arc(x + dx, y + dy, r, 0, TAU)
                col(ctx, hexc("#ffffff", 0.92))
                ctx.fill()

        # hills
        ctx.save()
        apply_cam(ctx, cam, 0.3)
        a, b = visible_range(cam, 0.3, 900)
        ctx.move_to(a, 0)
        x = a
        while x <= b:
            ctx.line_to(x, -620 + 70 * math.sin(x / 260) + 40 * math.sin(x / 97))
            x += 20
        ctx.line_to(b, 0)
        ctx.close_path()
        col(ctx, hexc("#8fd47a"))
        ctx.fill()
        ctx.restore()

        # houses
        ctx.save()
        apply_cam(ctx, cam, 0.7)
        a, b = visible_range(cam, 0.7, 900)
        for i in range(int(a // 560) - 1, int(b // 560) + 2):
            self.house(ctx, i * 560, i)
        ctx.restore()

        # near layer: sidewalk, road, posts, planters
        ctx.save()
        apply_cam(ctx, cam, 1.0)
        a, b = visible_range(cam, 1.0, 900)
        ctx.rectangle(a, -130, b - a, 60)
        col(ctx, hexc("#79c96b"))
        ctx.fill()
        ctx.rectangle(a, -80, b - a, 130)
        col(ctx, hexc("#ddd7ce"))
        ctx.fill()
        ctx.set_line_width(3)
        col(ctx, hexc("#bfb8ad"))
        for k in range(int(a // 140) - 1, int(b // 140) + 2):
            ctx.move_to(k * 140, -80)
            ctx.line_to(k * 140 - 40, 50)
        ctx.stroke()
        ctx.rectangle(a, 50, b - a, 26)
        col(ctx, hexc("#9e978c"))
        ctx.fill()
        ctx.rectangle(a, 76, b - a, 1200)
        col(ctx, hexc("#4b4a57"))
        ctx.fill()
        for k in range(int(a // 260) - 1, int(b // 260) + 2):
            rrect(ctx, k * 260, 300, 150, 22, 10)
            col(ctx, hexc("#ffd84a"))
            ctx.fill()
        for k in range(int(a // 900) - 1, int(b // 900) + 2):
            self.lamp(ctx, k * 900 + 200)
        for k in range(int(a // 640) - 1, int(b // 640) + 2):
            self.planter(ctx, k * 640 + 470, t, k)
        if a < -300 < b:
            self.sign(ctx, -300)
        ctx.restore()

    def house(self, ctx, x, i):
        rnd = random.Random(i * 31 + 5)
        w = rnd.randint(360, 440)
        h = rnd.randint(380, 520)
        base = -120
        c = hexc(HOUSE_COLS[i % len(HOUSE_COLS)])
        rrect(ctx, x - w / 2, base - h, w, h, 10)
        fill_ink(ctx, c, 6)
        path_poly(ctx, [(x - w / 2 - 30, base - h + 6), (x, base - h - 170), (x + w / 2 + 30, base - h + 6)])
        fill_ink(ctx, hexc(rnd.choice(["#c4473a", "#5a4ea8", "#3d8a6a", "#a8553d"])), 6)
        # attic window shows a little mask face
        ctx.arc(x, base - h - 60, 34, 0, TAU)
        fill_ink(ctx, hexc("#fff4c2"), 5)
        kind = i % 3
        col(ctx, INK)
        if kind == 0:
            ctx.arc(x, base - h - 60, 12, 0, TAU)
            ctx.set_line_width(4)
            ctx.stroke()
        elif kind == 1:
            path_poly(ctx, [(x - 13, base - h - 52), (x + 13, base - h - 52), (x, base - h - 74)])
            ctx.set_line_width(4)
            ctx.stroke()
        else:
            ctx.rectangle(x - 11, base - h - 71, 22, 22)
            ctx.set_line_width(4)
            ctx.stroke()
        # windows
        for wx in (x - w / 4, x + w / 4):
            rrect(ctx, wx - 48, base - h + 70, 96, 100, 8)
            fill_ink(ctx, hexc("#bfe8ff"), 5)
            ctx.move_to(wx, base - h + 70)
            ctx.line_to(wx, base - h + 170)
            ctx.move_to(wx - 48, base - h + 120)
            ctx.line_to(wx + 48, base - h + 120)
            ctx.set_line_width(4)
            ctx.stroke()
        rrect(ctx, x - 45, base - 170, 90, 170, 40)
        fill_ink(ctx, hexc("#8a5a3b"), 5)
        ctx.arc(x + 25, base - 85, 7, 0, TAU)
        col(ctx, hexc("#ffd84a"))
        ctx.fill()

    def lamp(self, ctx, x):
        rrect(ctx, x - 12, -980, 24, 920, 10)
        fill_ink(ctx, hexc("#3d3a4f"), 5)
        rrect(ctx, x - 44, -1060, 88, 90, 20)
        fill_ink(ctx, hexc("#fff1a8"), 6)
        rrect(ctx, x - 40, -90, 80, 40, 10)
        fill_ink(ctx, hexc("#3d3a4f"), 5)

    def planter(self, ctx, x, t, k):
        for j, (dx, hgt) in enumerate(((-40, 230), (0, 290), (40, 210))):
            ctx.move_to(x + dx, -80)
            ctx.line_to(x + dx * 1.2, -80 - hgt)
            ctx.set_line_width(9)
            col(ctx, hexc("#3f8a35"))
            ctx.stroke()
            ellipse(ctx, x + dx + 18, -80 - hgt * 0.5, 22, 10)
            col(ctx, hexc("#4fa944"))
            ctx.fill()
            sunflower(ctx, x + dx * 1.2, -80 - hgt, 1.0, t, k * 3 + j)
        rrect(ctx, x - 80, -110, 160, 70, 12)
        fill_ink(ctx, hexc("#c86b3c"), 6)

    def sign(self, ctx, x):
        rrect(ctx, x - 12, -600, 24, 540, 6)
        fill_ink(ctx, hexc("#7a4a2a"), 5)
        rrect(ctx, x - 230, -760, 460, 210, 26)
        fill_ink(ctx, hexc("#fff3d6"), 7)
        text_center(ctx, "WELCOME TO", x, -690, 44, hexc("#5a4ea8"))
        text_center(ctx, "MASKVILLE", x, -620, 72, hexc("#e84a7f"), outline=(INK, 8))
        text_center(ctx, "pop: weird", x, -568, 30, hexc("#3d3a4f"), font="Fredoka")


# --------------------------------------------------------------------------

class Cafe(Scene):
    def draw_bg(self, ctx, cam, t, v):
        ctx.save()
        apply_cam(ctx, cam)
        a, b = visible_range(cam, 1.0, 900)
        # wallpaper stripes
        ctx.rectangle(a, -2400, b - a, 2400)
        col(ctx, hexc("#f7ddb8"))
        ctx.fill()
        for k in range(int(a // 90) - 1, int(b // 90) + 2):
            ctx.rectangle(k * 90, -2400, 45, 2400)
            col(ctx, hexc("#f2cf9f"))
            ctx.fill()
        # wainscot
        ctx.rectangle(a, -330, b - a, 270)
        col(ctx, hexc("#8a5a3b"))
        ctx.fill()
        ctx.rectangle(a, -340, b - a, 22)
        col(ctx, hexc("#6b4329"))
        ctx.fill()
        # neon sign
        flick = 0.85 + 0.15 * (math.sin(t * 23) > -0.9)
        rrect(ctx, 80, -1360, 920, 200, 40)
        fill_ink(ctx, hexc("#2c1f3d"), 8)
        text_center(ctx, "BOO BREW", 540, -1210, 130, hexc("#7cf5ff", flick),
                    outline=(hexc("#ff4fa3", flick), 10))
        # window
        rrect(ctx, -160, -1060, 420, 520, 20)
        fill_ink(ctx, hexc("#9fdcff"), 10)
        for sx, sy in ((-60, -920), (150, -720)):
            ctx.arc(sx, sy, 40, 0, TAU)
            col(ctx, hexc("#ffffff", 0.8))
            ctx.fill()
        ctx.move_to(50, -1060)
        ctx.line_to(50, -540)
        ctx.move_to(-160, -800)
        ctx.line_to(260, -800)
        ctx.set_line_width(8)
        col(ctx, INK)
        ctx.stroke()
        # menu board
        rrect(ctx, 640, -1090, 470, 420, 18)
        fill_ink(ctx, hexc("#24312a"), 10)
        text_center(ctx, "MENU", 875, -1015, 58, hexc("#fff3d6"))
        ctx.select_font_face("Fredoka", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(36)
        for k, line in enumerate(["Ghost Latte .... 3", "Scream Cheese .. 2",
                                  "Boo-berry Muffin 2", "Square Coffee .. ??"]):
            ctx.move_to(670, -945 + k * 66)
            col(ctx, hexc("#e9f5e1"))
            ctx.show_text(line)
        # hanging lamps
        for lx in (300, 760):
            ctx.move_to(lx, -2400)
            ctx.line_to(lx, -1420)
            ctx.set_line_width(5)
            col(ctx, INK)
            ctx.stroke()
            ctx.arc(lx, -1420, 50, math.pi, TAU)
            ctx.close_path()
            fill_ink(ctx, hexc("#ff7a59"), 6)
        # potted sunflower
        rrect(ctx, -110, -200, 140, 140, 14)
        fill_ink(ctx, hexc("#c86b3c"), 6)
        ctx.move_to(-40, -200)
        ctx.line_to(-40, -560)
        ctx.set_line_width(10)
        col(ctx, hexc("#3f8a35"))
        ctx.stroke()
        sunflower(ctx, -40, -560, 1.3, t, 1)
        # floor
        ctx.rectangle(a, -60, b - a, 1400)
        col(ctx, hexc("#efe3d3"))
        ctx.fill()
        for r in range(0, 9):
            for k in range(int(a // 120) - 1, int(b // 120) + 2):
                if (k + r) % 2 == 0:
                    ctx.rectangle(k * 120, -60 + r * 120, 120, 120)
            col(ctx, hexc("#3b2a4a"))
            ctx.fill()
        ctx.restore()

    def draw_fg(self, ctx, cam, t, v):
        ctx.save()
        apply_cam(ctx, cam)
        # counter
        rrect(ctx, 660, -380, 560, 420, 14)
        fill_ink(ctx, hexc("#a8693f"), 8)
        for k in range(5):
            ctx.rectangle(690 + k * 106, -320, 70, 330)
            col(ctx, hexc("#93592f"))
            ctx.fill()
        rrect(ctx, 640, -420, 600, 50, 14)
        fill_ink(ctx, hexc("#e9e4d8"), 7)
        # espresso machine
        rrect(ctx, 1040, -650, 160, 230, 20)
        fill_ink(ctx, hexc("#c9ced8"), 7)
        ctx.arc(1120, -560, 30, 0, TAU)
        fill_ink(ctx, hexc("#ff4fa3"), 5)
        steam = v.get("steam", 1.0)
        for k in range(3):
            y = -700 - ((t * 60 + k * 40) % 120)
            ctx.arc(1090 + 25 * math.sin(t * 3 + k), y, 14, 0, TAU)
            col(ctx, hexc("#ffffff", 0.6 * steam))
            ctx.fill()
        # register
        rrect(ctx, 690, -560, 150, 140, 14)
        fill_ink(ctx, hexc("#ffd84a"), 6)
        rrect(ctx, 710, -540, 110, 50, 8)
        fill_ink(ctx, hexc("#2c1f3d"), 4)
        price = v.get("price", "$3")
        text_center(ctx, price, 765, -500, 36, hexc("#7cf5ff"))
        ctx.restore()


# --------------------------------------------------------------------------

class NightStreet(Scene):
    def __init__(self):
        rnd = random.Random(3)
        self.stars = [(rnd.uniform(0, W), rnd.uniform(0, 900), rnd.uniform(2, 5), rnd.uniform(0, 6))
                      for _ in range(90)]

    def draw_bg(self, ctx, cam, t, v):
        sky(ctx, hexc("#0c1638"), hexc("#3b2a6b"))
        for x, y, r, p in self.stars:
            ctx.arc(x, y, r * (0.7 + 0.3 * math.sin(t * 3 + p)), 0, TAU)
            col(ctx, hexc("#fff7d6", 0.9))
            ctx.fill()
        ctx.arc(790, 330, 150, 0, TAU)
        col(ctx, hexc("#fff4c9"))
        ctx.fill()
        for cx, cy, r in ((740, 290, 26), (840, 380, 18), (820, 270, 12)):
            ctx.arc(cx, cy, r, 0, TAU)
            col(ctx, hexc("#e9ddb0"))
            ctx.fill()
        # bats
        for k in range(2):
            bx = (t * 160 + k * 600) % 1600 - 260
            by = 520 + k * 120 + 40 * math.sin(t * 2 + k)
            fl = math.sin(t * 18 + k)
            ctx.save()
            ctx.translate(bx, by)
            path_poly(ctx, [(-50, -20 * fl), (-20, 0), (0, -10), (20, 0), (50, -20 * fl), (20, 10), (0, 4), (-20, 10)])
            col(ctx, hexc("#120a1f"))
            ctx.fill()
            ctx.restore()
        # far houses
        ctx.save()
        apply_cam(ctx, cam, 0.6)
        a, b = visible_range(cam, 0.6, 900)
        for i in range(int(a // 480) - 1, int(b // 480) + 2):
            rnd = random.Random(i)
            x = i * 480
            h = rnd.randint(420, 620)
            rrect(ctx, x - 190, -150 - h, 380, h, 8)
            fill_ink(ctx, hexc("#2b2350"), 5)
            path_poly(ctx, [(x - 220, -150 - h), (x, -330 - h), (x + 220, -150 - h)])
            fill_ink(ctx, hexc("#1c1638"), 5)
            for wx in (x - 90, x + 90):
                rrect(ctx, wx - 40, -150 - h + 80, 80, 90, 6)
                fill_ink(ctx, hexc("#ffcf5a") if rnd.random() > 0.3 else hexc("#3d3470"), 4)
        ctx.restore()

        ctx.save()
        apply_cam(ctx, cam, 1.0)
        a, b = visible_range(cam, 1.0, 900)
        # Granny's house
        self.granny_house(ctx, 800, t, v)
        # sidewalk & road
        ctx.rectangle(a, -80, b - a, 130)
        col(ctx, hexc("#6b6680"))
        ctx.fill()
        ctx.rectangle(a, 50, b - a, 26)
        col(ctx, hexc("#4c4860"))
        ctx.fill()
        ctx.rectangle(a, 76, b - a, 1200)
        col(ctx, hexc("#25223a"))
        ctx.fill()
        # fence posts
        for k in range(int(a // 120) - 1, int(b // 120) + 2):
            x = k * 120
            if 560 < x < 1060:
                continue
            path_poly(ctx, [(x - 18, -80), (x - 18, -300), (x, -330), (x + 18, -300), (x + 18, -80)])
            fill_ink(ctx, hexc("#e8e2f0"), 4)
        ctx.restore()

    def granny_house(self, ctx, x, t, v):
        rrect(ctx, x - 420, -1050, 840, 980, 10)
        fill_ink(ctx, hexc("#4a3a7a"), 7)
        path_poly(ctx, [(x - 480, -1040), (x, -1380), (x + 480, -1040)])
        fill_ink(ctx, hexc("#2a1f4f"), 7)
        for wx in (x - 260, x + 260):
            rrect(ctx, wx - 80, -900, 160, 170, 10)
            fill_ink(ctx, hexc("#ffcf5a"), 6)
        # door
        open_ = v.get("door", 0.0)
        rrect(ctx, x - 110, -470, 220, 400, 18)
        g = cairo.LinearGradient(0, -470, 0, -70)
        g.add_color_stop_rgb(0, 1, 0.78, 0.35)
        g.add_color_stop_rgb(1, 1, 0.6, 0.2)
        ctx.set_source(g)
        ctx.fill_preserve()
        col(ctx, INK)
        ctx.set_line_width(7)
        ctx.stroke()
        dw = 220 * (1 - open_)
        if dw > 2:
            rrect(ctx, x - 110, -470, dw, 400, 18)
            fill_ink(ctx, hexc("#7a2e3a"), 7)
            ctx.arc(x - 110 + dw - 30, -270, 10, 0, TAU)
            col(ctx, hexc("#ffd84a"))
            ctx.fill()
        # steps
        rrect(ctx, x - 170, -90, 340, 30, 6)
        fill_ink(ctx, hexc("#7e7590"), 5)
        # jack-o-lanterns with flicker
        for jx in (x - 230, x + 230):
            fl = 0.7 + 0.3 * math.sin(t * 17 + jx)
            g = cairo.RadialGradient(jx, -140, 10, jx, -140, 150)
            g.add_color_stop_rgba(0, 1, 0.7, 0.2, 0.45 * fl)
            g.add_color_stop_rgba(1, 1, 0.5, 0.1, 0)
            ctx.set_source(g)
            ctx.arc(jx, -140, 150, 0, TAU)
            ctx.fill()
            ellipse(ctx, jx, -130, 70, 56)
            fill_ink(ctx, hexc("#f08a24"), 6)
            col(ctx, hexc("#ffe066", fl))
            for s in (-1, 1):
                path_poly(ctx, [(jx + s * 12, -140), (jx + s * 40, -140), (jx + s * 26, -162)])
                ctx.fill()
            path_poly(ctx, [(jx - 34, -116), (jx + 34, -116), (jx + 20, -98), (jx - 20, -98)])
            ctx.fill()


SCENES = {"street": StreetDay, "cafe": Cafe, "night": NightStreet}
