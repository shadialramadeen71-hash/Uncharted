"""OFFICE SQUAD locations: sunburst intro, break room, open-plan office."""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "wobbles"))
sys.path.insert(1, os.path.join(HERE, "..", "mask-buddies"))

import cairo  # noqa: E402

import wob_world  # noqa: E402
from sq_chars import INK, TAU, col, draw_item, ellipse, fill_ink, hexc, path_poly, rrect  # noqa: E402
from wob_world import Scene, apply_cam, text_center, vis  # noqa: E402


def WH():
    return wob_world.W, wob_world.H


def sparkle(ctx, x, y, r):
    path_poly(ctx, [(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25),
                    (x, y + r), (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)])
    col(ctx, hexc("#ffffff"))
    ctx.fill()


def ribbon(ctx, cx, cy, w, h, text, size):
    """Red ribbon banner with folded tails, like the show's poster."""
    for s in (-1, 1):
        x0 = cx + s * (w / 2 - 20)
        path_poly(ctx, [(x0, cy - h * 0.25), (x0 + s * 120, cy - h * 0.25), (x0 + s * 80, cy + h * 0.3),
                        (x0 + s * 120, cy + h * 0.85), (x0, cy + h * 0.85)])
        fill_ink(ctx, hexc("#b71c1c"), 7)
    ctx.move_to(cx - w / 2, cy - h / 2 + 10)
    ctx.curve_to(cx - w / 4, cy - h / 2 - 14, cx + w / 4, cy - h / 2 - 14, cx + w / 2, cy - h / 2 + 10)
    ctx.line_to(cx + w / 2, cy + h / 2 + 10)
    ctx.curve_to(cx + w / 4, cy + h / 2 - 14, cx - w / 4, cy + h / 2 - 14, cx - w / 2, cy + h / 2 + 10)
    ctx.close_path()
    fill_ink(ctx, hexc("#e53935"), 8)
    ctx.save()
    ctx.translate(cx, cy + size * 0.36)
    ctx.rotate(-0.03)
    text_center(ctx, text, 0, 0, size, hexc("#ffe14d"), outline=(INK, 12))
    ctx.restore()


class Burst(Scene):
    """Sunburst title card with the squad posing, like the poster."""

    def draw_bg(self, ctx, cam, t, v):
        W, H = WH()
        cx, cy = W / 2, H * 0.4
        g = cairo.RadialGradient(cx, cy, 50, cx, cy, max(W, H))
        g.add_color_stop_rgb(0, 1.0, 0.82, 0.25)
        g.add_color_stop_rgb(1, 0.96, 0.42, 0.12)
        ctx.set_source(g)
        ctx.paint()
        rot = t * 0.12
        for i in range(24):
            a0 = rot + i * TAU / 24
            ctx.move_to(cx, cy)
            ctx.line_to(cx + math.cos(a0) * 3000, cy + math.sin(a0) * 3000)
            ctx.line_to(cx + math.cos(a0 + TAU / 48) * 3000, cy + math.sin(a0 + TAU / 48) * 3000)
            ctx.close_path()
            col(ctx, hexc("#ffffff", 0.12))
            ctx.fill()
        rnd = random.Random(1)
        for _ in range(10):
            x, y = rnd.uniform(60, W - 60), rnd.uniform(80, H * 0.62)
            sparkle(ctx, x, y, 14 + 10 * abs(math.sin(t * 3 + x)))

    def draw_top(self, ctx, cam, t, v):
        W, H = WH()
        b = v.get("banner", 0.0)
        if b <= 0:
            return
        ctx.save()
        ctx.translate(W / 2, H * 0.68)
        k = min(1.0, W / 1300) * (0.4 + 0.6 * b) * (1 + 0.1 * math.sin(min(1.0, b) * math.pi))
        ctx.scale(k, k)
        ribbon(ctx, 0, 0, 1200, 190, "OFFICE SQUAD", 150)
        if v.get("ep_title") and b >= 1:
            text_center(ctx, v["ep_title"], 0, 230, 72, hexc("#ffffff"), font="Fredoka", outline=(INK, 10))
        ctx.restore()


def floor_wall(ctx, cam, wall, panel, floor, tile):
    a, b = vis(cam)
    ctx.rectangle(a, -2400, b - a, 2400)
    col(ctx, wall)
    ctx.fill()
    ctx.rectangle(a, -330, b - a, 300)
    col(ctx, panel)
    ctx.fill()
    ctx.rectangle(a, -340, b - a, 16)
    col(ctx, hexc("#ffffff"))
    ctx.fill()
    ctx.rectangle(a, -30, b - a, 1500)
    col(ctx, floor)
    ctx.fill()
    for r in range(8):
        for k in range(int(a // 150) - 1, int(b // 150) + 2):
            if (k + r) % 2 == 0:
                ctx.rectangle(k * 150, -30 + r * 150, 150, 150)
    col(ctx, tile)
    ctx.fill()


def city_window(ctx, x, y, w, h, t):
    rrect(ctx, x, y, w, h, 12)
    g = cairo.LinearGradient(0, y, 0, y + h)
    g.add_color_stop_rgb(0, 0.42, 0.75, 1.0)
    g.add_color_stop_rgb(1, 0.85, 0.95, 1.0)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    rnd = random.Random(int(x))
    bx = x
    while bx < x + w:
        bw, bh = rnd.uniform(60, 130), rnd.uniform(h * 0.3, h * 0.8)
        ctx.rectangle(bx, y + h - bh, bw, bh)
        col(ctx, hexc(rnd.choice(["#90a4ae", "#78909c", "#b0bec5", "#8fa3c7"])))
        ctx.fill()
        for wy in range(int(y + h - bh + 16), int(y + h), 34):
            for wx in range(int(bx + 12), int(bx + bw - 12), 26):
                ctx.rectangle(wx, wy, 12, 16)
        col(ctx, hexc("#e3f2fd"))
        ctx.fill()
        bx += bw + 6
    ctx.restore()
    rrect(ctx, x, y, w, h, 12)
    col(ctx, INK)
    ctx.set_line_width(10)
    ctx.stroke()
    ctx.move_to(x + w / 2, y)
    ctx.line_to(x + w / 2, y + h)
    ctx.stroke()


class BreakRoom(Scene):
    TABLE_X = 1000

    def draw_bg(self, ctx, cam, t, v):
        ctx.save()
        apply_cam(ctx, cam)
        floor_wall(ctx, cam, hexc("#fff3d6"), hexc("#4db6ac"), hexc("#e0e0e0"), hexc("#cfd8dc"))
        city_window(ctx, 1240, -1150, 520, 440, t)
        # poster
        rrect(ctx, 420, -1180, 300, 380, 8)
        fill_ink(ctx, hexc("#ffffff"), 8)
        ctx.save()
        ctx.translate(570, -1010)
        draw_item(ctx, "pizza")
        ctx.restore()
        text_center(ctx, "TEAMWORK", 570, -860, 44, hexc("#e53935"))
        # counter, coffee machine, microwave
        rrect(ctx, -300, -420, 720, 390, 10)
        fill_ink(ctx, hexc("#8d6e63"), 8)
        rrect(ctx, -320, -460, 760, 50, 10)
        fill_ink(ctx, hexc("#eceff1"), 7)
        rrect(ctx, -240, -700, 200, 240, 18)
        fill_ink(ctx, hexc("#37474f"), 7)
        rrect(ctx, -200, -560, 120, 90, 8)
        fill_ink(ctx, hexc("#263238"), 4)
        for k in range(3):
            y = -720 - ((t * 50 + k * 40) % 120)
            ctx.arc(-140 + 18 * math.sin(t * 3 + k), y, 14, 0, TAU)
            col(ctx, hexc("#ffffff", 0.6))
            ctx.fill()
        rrect(ctx, 80, -650, 300, 190, 16)
        fill_ink(ctx, hexc("#cfd8dc"), 7)
        rrect(ctx, 110, -625, 190, 140, 10)
        fill_ink(ctx, hexc("#263238"), 5)
        ctx.arc(340, -600, 14, 0, TAU)
        fill_ink(ctx, hexc("#ff7043"), 4)
        # fridge
        rrect(ctx, 1900, -1000, 320, 980, 30)
        fill_ink(ctx, hexc("#e3f2fd"), 8)
        ctx.move_to(1900, -640)
        ctx.line_to(2220, -640)
        ctx.set_line_width(7)
        col(ctx, INK)
        ctx.stroke()
        rrect(ctx, 1960, -940, 160, 110, 6)
        fill_ink(ctx, hexc("#fff59d"), 4)
        ctx.select_font_face("Fredoka", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(26)
        col(ctx, INK)
        for k, line in enumerate(("DO NOT EAT", "MY LUNCH", "- Steve")):
            ctx.move_to(1975, -905 + k * 30)
            ctx.show_text(line)
        ctx.restore()

    def draw_fg(self, ctx, cam, t, v):
        ctx.save()
        apply_cam(ctx, cam)
        x = self.TABLE_X
        for lx in (x - 170, x + 150):
            rrect(ctx, lx, -250, 22, 250, 6)
            fill_ink(ctx, hexc("#6d4c41"), 5)
        rrect(ctx, x - 220, -290, 440, 46, 12)
        fill_ink(ctx, hexc("#a1663f"), 7)
        # pizza box
        path_poly(ctx, [(x - 150, -300), (x + 150, -300), (x + 120, -350), (x - 120, -350)])
        fill_ink(ctx, hexc("#e9c38b"), 6)
        path_poly(ctx, [(x - 120, -350), (x + 120, -350), (x + 120, -520), (x - 120, -520)])
        fill_ink(ctx, hexc("#f2d3a2"), 6)
        text_center(ctx, "PIZZA", x, -420, 54, hexc("#e53935"))
        ellipse(ctx, x, -326, 110, 18)
        col(ctx, hexc("#d7a86e"))
        ctx.fill()
        if v.get("slices", 1):
            ctx.save()
            ctx.translate(x - 10, -334)
            ctx.rotate(-1.4)
            ctx.scale(0.8, 0.5)
            draw_item(ctx, "pizza")
            ctx.restore()
        else:
            for cx_, cy_ in ((x - 40, -328), (x + 30, -322), (x + 60, -330)):
                ctx.arc(cx_, cy_, 5, 0, TAU)
                col(ctx, hexc("#c77d3a"))
                ctx.fill()
        ctx.restore()


class Office(Scene):
    DESKS = (420, 1000, 1580)

    def draw_bg(self, ctx, cam, t, v):
        ctx.save()
        apply_cam(ctx, cam)
        floor_wall(ctx, cam, hexc("#e3eefc"), hexc("#5c6bc0"), hexc("#b0bec5"), hexc("#a3b3bb"))
        city_window(ctx, 120, -1200, 560, 520, t)
        city_window(ctx, 1320, -1200, 560, 520, t + 1)
        # clock + poster
        ctx.arc(1000, -1060, 80, 0, TAU)
        fill_ink(ctx, hexc("#ffffff"), 8)
        for a in (t * 0.4, t * 5):
            ctx.move_to(1000, -1060)
            ctx.line_to(1000 + math.sin(a) * 55, -1060 - math.cos(a) * 55)
        ctx.set_line_width(7)
        col(ctx, INK)
        ctx.stroke()
        rrect(ctx, 820, -920, 360, 150, 10)
        fill_ink(ctx, hexc("#ffd23f"), 7)
        text_center(ctx, "SYNERGY!", 1000, -825, 70, hexc("#e53935"), outline=(INK, 6))
        # water cooler + printer + plant
        rrect(ctx, -260, -560, 140, 530, 14)
        fill_ink(ctx, hexc("#eceff1"), 7)
        ctx.arc(-190, -640, 80, 0, TAU)
        fill_ink(ctx, hexc("#81d4fa"), 7)
        rrect(ctx, 2060, -470, 280, 440, 16)
        fill_ink(ctx, hexc("#cfd8dc"), 7)
        rrect(ctx, 2090, -440, 220, 70, 8)
        fill_ink(ctx, hexc("#455a64"), 5)
        if v.get("printer_jam"):
            text_center(ctx, "ERROR", 2200, -390, 40, hexc("#ff5252"))
        ctx.restore()

    def draw_fg(self, ctx, cam, t, v):
        """Desks: anyone sitting behind one (z < 0) is hidden from the waist down."""
        ctx.save()
        apply_cam(ctx, cam)
        for i, x in enumerate(self.DESKS):
            for lx in (x - 230, x + 210):
                rrect(ctx, lx, -300, 20, 300, 6)
                fill_ink(ctx, hexc("#78909c"), 5)
            rrect(ctx, x - 250, -340, 500, 260, 12)
            fill_ink(ctx, hexc("#f5f5f5"), 7)
            rrect(ctx, x - 270, -360, 540, 40, 10)
            fill_ink(ctx, hexc("#d7ccc8"), 7)
            # monitor at the side, keyboard in front
            rrect(ctx, x + 130, -560, 150, 110, 10)
            fill_ink(ctx, hexc("#263238"), 7)
            g = abs(math.sin(t * 2 + i)) * 0.3
            rrect(ctx, x + 142, -548, 126, 86, 6)
            col(ctx, (0.3 + g, 0.75, 1.0, 1))
            ctx.fill()
            rrect(ctx, x + 195, -450, 20, 90, 4)
            fill_ink(ctx, hexc("#455a64"), 4)
            rrect(ctx, x - 110, -380, 200, 26, 6)
            fill_ink(ctx, hexc("#37474f"), 5)
            ctx.arc(x - 190, -385, 26, math.pi, TAU)
            fill_ink(ctx, hexc("#ffffff"), 5)
        ctx.restore()


SCENES = {"burst": Burst, "breakroom": BreakRoom, "office": Office}
