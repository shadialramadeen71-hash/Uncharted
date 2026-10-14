"""Pickleton: the WOBBLES' world. Landscape 1920x1080, ground at world y=0."""
import math
import random

import cairo

from wob_chars import INK, TAU, col, ellipse, fill_ink, hexc, path_poly, rrect

W, H = 1920, 1080


def apply_cam(ctx, cam, parallax=1.0):
    ctx.translate(W / 2, H / 2)
    ctx.scale(cam["z"], cam["z"])
    ctx.translate(-cam["x"] * parallax, -cam["y"])


def vis(cam, pad=600):
    half = W / 2 / cam["z"] + pad
    return cam["x"] - half, cam["x"] + half


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


def cloud(ctx, x, y, s, a=0.95):
    for dx, dy, r in ((0, 0, 60), (70, -30, 75), (145, 0, 58), (72, 22, 62), (-50, 15, 40), (195, 18, 38)):
        ctx.arc(x + dx * s, y + dy * s, r * s, 0, TAU)
    col(ctx, hexc("#ffffff", a))
    ctx.fill()


def floor_and_wall(ctx, cam, wall, wall2, floor, floor2, stripe=110):
    a, b = vis(cam)
    ctx.rectangle(a, -2200, b - a, 2200)
    col(ctx, wall)
    ctx.fill()
    for k in range(int(a // stripe) - 1, int(b // stripe) + 2):
        ctx.rectangle(k * stripe, -2200, stripe / 2, 2200)
        col(ctx, wall2)
        ctx.fill()
    ctx.rectangle(a, -60, b - a, 30)
    col(ctx, hexc("#ffffff"))
    ctx.fill()
    ctx.rectangle(a, -30, b - a, 1400)
    col(ctx, floor)
    ctx.fill()
    ctx.set_line_width(4)
    col(ctx, floor2)
    for r in range(0, 8):
        y = -30 + r * 70 + r * r * 6
        ctx.move_to(a, y)
        ctx.line_to(b, y)
    ctx.stroke()


def window(ctx, x, y, w, h, t, night=False):
    rrect(ctx, x, y, w, h, 14)
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgb(0, 0.45, 0.78, 1.0)
    g.add_color_stop_rgb(1, 0.82, 0.94, 1.0)
    ctx.set_source(g)
    ctx.fill_preserve()
    col(ctx, INK)
    ctx.set_line_width(10)
    ctx.stroke()
    ctx.save()
    rrect(ctx, x, y, w, h, 14)
    ctx.clip()
    cloud(ctx, x + ((t * 20) % (w + 200)) - 100, y + h * 0.3, 0.5)
    ctx.restore()
    ctx.move_to(x + w / 2, y)
    ctx.line_to(x + w / 2, y + h)
    ctx.move_to(x, y + h / 2)
    ctx.line_to(x + w, y + h / 2)
    ctx.set_line_width(9)
    col(ctx, INK)
    ctx.stroke()
    # curtains
    for s, cx in ((1, x - 20), (-1, x + w + 20)):
        path_poly(ctx, [(cx, y - 40), (cx + s * 90, y - 40), (cx + s * 50, y + h + 30), (cx, y + h + 30)])
        fill_ink(ctx, hexc("#e57373"), 6)


class Scene:
    def draw_bg(self, ctx, cam, t, v):
        pass

    def draw_fg(self, ctx, cam, t, v):
        pass

    def draw_top(self, ctx, cam, t, v):
        pass


# --------------------------------------------------------------------------

class Intro(Scene):
    """Flying through clouds, then the title slams in."""

    def draw_bg(self, ctx, cam, t, v):
        st = v.get("scene_t", t)
        sky(ctx, hexc("#3fa9f5"), hexc("#bfe7ff"))
        rnd = random.Random(11)
        for i in range(16):
            x0, y0 = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
            ph = rnd.uniform(0, 1)
            u = (st * 0.35 + ph) % 1.0
            s = 0.3 + u * u * 6
            x = W / 2 + x0 * u * u * 1600
            y = H / 2 + y0 * u * u * 900
            cloud(ctx, x - 70 * s, y, s, a=min(0.95, (1 - u) * 3))

    def draw_top(self, ctx, cam, t, v):
        st = v.get("scene_t", t)
        if st < 1.2:
            return
        u = st - 1.2
        s = max(0.02, min(1.0, u * 2.5)) * (1 + 0.12 * math.exp(-u * 4) * math.sin(u * 20))
        ctx.save()
        ctx.translate(W / 2, H / 2 - 40)
        ctx.rotate(-0.05)
        ctx.scale(s, s)
        text_center(ctx, "THE", 0, -150, 110, hexc("#ffffff"), outline=(INK, 14))
        text_center(ctx, "WOBBLES", 0, 60, 280, hexc("#ffd23f"), outline=(INK, 22))
        if u > 1.0:
            text_center(ctx, v.get("ep_title", ""), 0, 190, 70, hexc("#ffffff"), font="Fredoka",
                        outline=(INK, 10))
        ctx.restore()


class LivingRoom(Scene):
    def draw_bg(self, ctx, cam, t, v):
        ctx.save()
        apply_cam(ctx, cam)
        floor_and_wall(ctx, cam, hexc("#f7c8d8"), hexc("#f2b8cb"), hexc("#b07a4a"), hexc("#94603a"))
        window(ctx, 120, -950, 380, 420, t)
        # pickle painting
        rrect(ctx, 820, -1060, 360, 260, 10)
        fill_ink(ctx, hexc("#e6c15a"), 12)
        rrect(ctx, 850, -1030, 300, 200, 6)
        col(ctx, hexc("#fff8e1"))
        ctx.fill()
        ctx.save()
        ctx.translate(1000, -930)
        ctx.rotate(-0.4)
        ellipse(ctx, 0, 0, 110, 40)
        fill_ink(ctx, hexc("#6abf4b"), 6)
        ctx.restore()
        # lamp
        rrect(ctx, 1460, -560, 18, 530, 6)
        fill_ink(ctx, hexc("#555566"), 4)
        path_poly(ctx, [(1400, -560), (1540, -560), (1500, -720), (1440, -720)])
        fill_ink(ctx, hexc("#ffe082"), 6)
        # TV
        rrect(ctx, 1640, -230, 300, 200, 10)
        fill_ink(ctx, hexc("#8d6e63"), 6)
        rrect(ctx, 1620, -560, 340, 320, 24)
        fill_ink(ctx, hexc("#5d4037"), 8)
        rrect(ctx, 1650, -530, 280, 240, 16)
        col(ctx, hexc("#9be15d" if int(t * 2) % 2 else "#7fd34a"))
        ctx.fill()
        text_center(ctx, "PICKLE TV", 1790, -400, 40, hexc("#1b5e20"))
        # couch (can fly)
        lift = v.get("couch_lift", 0.0)
        ctx.save()
        ctx.translate(0, -lift)
        x0, x1 = 500, 1440
        rrect(ctx, x0, -400, x1 - x0, 260, 50)
        fill_ink(ctx, hexc("#7e57c2"), 8)
        rrect(ctx, x0 - 60, -260, 140, 230, 40)
        fill_ink(ctx, hexc("#6a43b0"), 8)
        rrect(ctx, x1 - 80, -260, 140, 230, 40)
        fill_ink(ctx, hexc("#6a43b0"), 8)
        rrect(ctx, x0 + 60, -175, x1 - x0 - 120, 120, 26)
        fill_ink(ctx, hexc("#9575cd"), 7)
        if lift > 5:
            for k in range(3):
                fl = 60 + 40 * math.sin(t * 40 + k)
                path_poly(ctx, [(x0 + 150 + k * 250, -40), (x0 + 210 + k * 250, -40), (x0 + 180 + k * 250, -40 + fl * 2.2)])
                fill_ink(ctx, hexc("#ffb02e"), 5)
        ctx.restore()
        ctx.restore()


class Kitchen(Scene):
    def draw_bg(self, ctx, cam, t, v):
        ctx.save()
        apply_cam(ctx, cam)
        floor_and_wall(ctx, cam, hexc("#d7f0d0"), hexc("#c8e8bf"), hexc("#f3e5ab"), hexc("#d8c78b"), 80)
        # checker floor tint
        a, b = vis(cam)
        for r in range(0, 5):
            for k in range(int(a // 160) - 1, int(b // 160) + 2):
                if (k + r) % 2 == 0:
                    ctx.rectangle(k * 160, -30 + r * 160, 160, 160)
        col(ctx, hexc("#e0cf8a"))
        ctx.fill()
        # upper cabinets
        for k in range(4):
            rrect(ctx, 700 + k * 260, -1180, 240, 300, 14)
            fill_ink(ctx, hexc("#ffb74d"), 7)
            ctx.arc(700 + k * 260 + 200, -1030, 10, 0, TAU)
            col(ctx, INK)
            ctx.fill()
        window(ctx, 160, -1000, 360, 360, t)
        # counter + stove
        rrect(ctx, 640, -420, 1100, 400, 10)
        fill_ink(ctx, hexc("#ffcc80"), 8)
        rrect(ctx, 620, -460, 1140, 50, 10)
        fill_ink(ctx, hexc("#eceff1"), 7)
        rrect(ctx, 1100, -400, 300, 300, 10)
        fill_ink(ctx, hexc("#cfd8dc"), 6)
        rrect(ctx, 1130, -360, 240, 180, 10)
        fill_ink(ctx, hexc("#37474f"), 5)
        for k in range(2):
            ellipse(ctx, 1170 + k * 160, -470, 50, 10)
            fill_ink(ctx, hexc("#263238"), 4)
        # pot with steam
        rrect(ctx, 1290, -560, 120, 90, 14)
        fill_ink(ctx, hexc("#e53935"), 6)
        for k in range(3):
            y = -600 - ((t * 50 + k * 40) % 120)
            ctx.arc(1350 + 20 * math.sin(t * 3 + k), y, 14, 0, TAU)
            col(ctx, hexc("#ffffff", 0.6))
            ctx.fill()
        # fridge
        rrect(ctx, 1820, -900, 300, 880, 30)
        fill_ink(ctx, hexc("#eceff1"), 8)
        ctx.move_to(1820, -560)
        ctx.line_to(2120, -560)
        ctx.set_line_width(7)
        col(ctx, INK)
        ctx.stroke()
        for mx, my, c in ((1880, -800, "#ff6fae"), (1960, -700, "#ffd23f"), (2040, -820, "#6abf4b")):
            ctx.arc(mx, my, 20, 0, TAU)
            fill_ink(ctx, hexc(c), 4)
        # wall clock
        ctx.arc(1520, -1280 + 300, 70, 0, TAU)
        fill_ink(ctx, hexc("#ffffff"), 7)
        for a in (t * 0.5, t * 6):
            ctx.move_to(1520, -980)
            ctx.line_to(1520 + math.sin(a) * 50, -980 - math.cos(a) * 50)
        ctx.set_line_width(6)
        col(ctx, INK)
        ctx.stroke()
        ctx.restore()


class Backyard(Scene):
    GX = 1000  # grill x

    def draw_bg(self, ctx, cam, t, v):
        sky(ctx, hexc("#59b8ff"), hexc("#d6f1ff"))
        ctx.arc(1650, 160, 80, 0, TAU)
        fill_ink(ctx, hexc("#ffe066"), 6)
        for i in range(4):
            cloud(ctx, (i * 560 + t * 15) % 2400 - 300, 120 + (i % 2) * 90, 0.8)
        ctx.save()
        apply_cam(ctx, cam)
        a, b = vis(cam)
        # house back wall (left)
        rrect(ctx, -700, -1300, 1100, 1300, 0)
        fill_ink(ctx, hexc("#ffcc80"), 8)
        path_poly(ctx, [(-760, -1300), (-150, -1650), (460, -1300)])
        fill_ink(ctx, hexc("#c0504d"), 8)
        rrect(ctx, 80, -620, 220, 600, 16)
        fill_ink(ctx, hexc("#8d5a3b"), 7)
        window(ctx, -450, -1050, 300, 280, t)
        # neighbour's house far right
        rrect(ctx, 2000, -1100, 900, 1100, 0)
        fill_ink(ctx, hexc("#b3d1ff"), 8)
        path_poly(ctx, [(1950, -1100), (2450, -1400), (2950, -1100)])
        fill_ink(ctx, hexc("#5a6fa8"), 8)
        # tree
        rrect(ctx, 560, -700, 70, 700, 20)
        fill_ink(ctx, hexc("#8d5a3b"), 6)
        for dx, dy, r in ((0, -760, 170), (-120, -660, 120), (120, -660, 130), (0, -900, 120)):
            ctx.arc(595 + dx, dy, r, 0, TAU)
            fill_ink(ctx, hexc("#5cb85c"), 6)
        # lawn
        ctx.rectangle(a, -40, b - a, 1400)
        col(ctx, hexc("#6ccf5a"))
        ctx.fill()
        ctx.set_line_width(3)
        col(ctx, hexc("#52b043"))
        rnd = random.Random(2)
        for _ in range(140):
            x = rnd.uniform(a, b)
            y = rnd.uniform(-30, 500)
            ctx.move_to(x, y)
            ctx.line_to(x + 6, y - 22)
        ctx.stroke()
        ctx.restore()

    def draw_fg(self, ctx, cam, t, v):
        """Fence (hides the neighbour's legs) and the grill."""
        ctx.save()
        apply_cam(ctx, cam)
        a, b = vis(cam)
        ctx.rectangle(1300, -330, max(0, b - 1300), 40)
        col(ctx, hexc("#e8d5b0"))
        ctx.fill()
        for k in range(int(1300 // 70), int(b // 70) + 2):
            x = k * 70
            path_poly(ctx, [(x - 28, -40), (x - 28, -420), (x, -460), (x + 28, -420), (x + 28, -40)])
            fill_ink(ctx, hexc("#f5e6c8"), 5)
        # picnic table
        rrect(ctx, 1600, -260, 360, 36, 8)
        fill_ink(ctx, hexc("#a1663f"), 6)
        for lx in (1640, 1900):
            path_poly(ctx, [(lx, -224), (lx + 20, -224), (lx + 40, 0), (lx + 20, 0)])
            fill_ink(ctx, hexc("#8d5a3b"), 5)
        rrect(ctx, 1590, -290, 380, 40, 10)
        fill_ink(ctx, hexc("#e53935"), 5)
        if v.get("grill_gone"):
            ellipse(ctx, self.GX, -10, 200, 34)
            col(ctx, hexc("#3e2f22", 0.85))
            ctx.fill()
            for k in range(3):
                u = (t * 0.4 + k / 3) % 1.0
                ctx.arc(self.GX + 30 * math.sin(t * 2 + k), -40 - u * 300, 20 + u * 40, 0, TAU)
                col(ctx, hexc("#9e9e9e", 0.5 * (1 - u)))
                ctx.fill()
        else:
            self.grill(ctx, t, v)
        ctx.restore()

    def grill(self, ctx, t, v):
        gx = self.GX
        gy = -v.get("grill_y", 0.0)
        tilt = 0.15 * math.sin(t * 9) * min(1.0, v.get("grill_y", 0) / 200)
        ctx.save()
        ctx.translate(gx, gy)
        ctx.rotate(tilt)
        if v.get("grill_y", 0) > 5:
            for k in (-1, 1):
                fl = 80 + 50 * math.sin(t * 45 + k)
                path_poly(ctx, [(k * 60 - 30, 0), (k * 60 + 30, 0), (k * 60, fl * 2)])
                fill_ink(ctx, hexc("#ffb02e"), 5)
        for lx in (-80, 80):
            stroke_leg = [(lx, -200), (lx * 1.3, 0)]
            ctx.move_to(*stroke_leg[0])
            ctx.line_to(*stroke_leg[1])
            ctx.set_line_width(16)
            col(ctx, INK)
            ctx.stroke()
        ctx.move_to(-150, -330)
        ctx.curve_to(-150, -170, 150, -170, 150, -330)
        ctx.close_path()
        fill_ink(ctx, hexc("#263238"), 8)
        # turbo panel
        rrect(ctx, -60, -280, 120, 50, 10)
        fill_ink(ctx, hexc("#b0bec5"), 5)
        beep = v.get("beep", 0) and int(t * 6) % 2
        for k, c in enumerate(("#4caf50", "#ffeb3b", "#ff1744")):
            ctx.arc(-30 + k * 30, -255, 11, 0, TAU)
            fill_ink(ctx, hexc("#ffffff") if (k == 2 and beep) else hexc(c), 3)
        # grate + burgers on it
        ctx.rectangle(-160, -345, 320, 18)
        fill_ink(ctx, hexc("#90a4ae"), 5)
        if v.get("burgers_on", 1) and not v.get("burgers_t0"):
            for k in (-90, 0, 90):
                ellipse(ctx, k, -360, 40, 14)
                fill_ink(ctx, hexc("#6d3b1f"), 4)
        # flames
        fl = v.get("flame", 0.0)
        if fl > 0:
            for k in range(5):
                h = (30 + 25 * math.sin(t * 20 + k * 1.7)) * fl
                x = -120 + k * 60
                path_poly(ctx, [(x - 18, -345), (x + 18, -345), (x, -345 - h)])
                col(ctx, hexc("#ff7043" if k % 2 else "#ffca28"))
                ctx.fill()
        ctx.restore()

    def draw_top(self, ctx, cam, t, v):
        ctx.save()
        apply_cam(ctx, cam)
        gx = self.GX
        # smoke drifting right toward the neighbour's lawn
        sm = v.get("smoke", 0.0)
        for k in range(10):
            u = ((t * 0.25 + k / 10) % 1.0)
            x = gx + u * 900 + 40 * math.sin(t + k)
            y = -400 - u * 500
            ctx.arc(x, y, 30 + u * 70, 0, TAU)
            col(ctx, hexc("#9e9e9e", 0.45 * (1 - u) * sm))
            ctx.fill()
        # burger launch / rain
        t0 = v.get("burgers_t0")
        if t0:
            u = t - t0
            rnd = random.Random(5)
            for i in range(14):
                vx = rnd.uniform(-900, 900)
                vy = rnd.uniform(1400, 2300)
                tx = gx + vx * u
                ty = -360 - vy * u + 1500 * u * u
                if i == 3:   # this one is destined for Fussbucket's head
                    land = 1.45
                    if u >= land:
                        continue  # the engine draws it as a hat from here on
                    hy = -v.get("fuss_head", 640)
                    vy0 = (-360 + 1500 * land * land - hy) / land
                    tx = gx + (1530 - gx) * u / land
                    ty = -360 - vy0 * u + 1500 * u * u
                if ty > 10:
                    ty = 10
                    # landed: stays on lawn
                    tx = gx + vx * ((vy + math.sqrt(vy * vy + 4 * 1500 * 370)) / 3000)
                ctx.save()
                ctx.translate(tx, ty)
                ctx.rotate(u * 8 + i if ty < 10 else 0)
                ellipse(ctx, 0, 0, 44, 16)
                fill_ink(ctx, hexc("#e9b44c"), 4)
                ellipse(ctx, 0, 4, 40, 9)
                col(ctx, hexc("#6d3b1f"))
                ctx.fill()
                ctx.restore()
        ctx.restore()


class Sky(Scene):
    """The grill's last flight."""

    def draw_bg(self, ctx, cam, t, v):
        st = v.get("scene_t", 0)
        sky(ctx, hexc("#2f80ed"), hexc("#a9dcff"))
        for i in range(6):
            cloud(ctx, (i * 400) % 2200 - 200, ((i * 170 + st * 900) % 1400) - 200, 0.9)
        ctx.save()
        ctx.translate(W / 2 + 60 * math.sin(st * 3), H / 2 + 200)
        ctx.rotate(0.3 * math.sin(st * 4))
        sc = max(0.05, 1.0 - st * 0.25)
        ctx.scale(sc, sc)
        Backyard.grill(Backyard(), ctx, st, {"grill_y": 300, "beep": 1, "burgers_on": 0})
        ctx.restore()


SCENES = {"intro": Intro, "living": LivingRoom, "kitchen": Kitchen, "backyard": Backyard, "sky": Sky}
