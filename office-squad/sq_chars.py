"""OFFICE SQUAD characters.

Flat, bold-outline cartoon style (big round eyes, open mouths) with proper
anatomy: tapered limbs with elbows and knees, hands with a palm, thumb and
four fingers (relaxed / open / fist / point), and real shoes.

Frontal bodies; limb angles are screen angles: 0 = straight down,
positive = toward screen-right.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mask-buddies"))

import cairo  # noqa: E402

from characters import (INK, TAU, WALK_STYLES, Humanoid, col, ellipse, fill_ink, hexc,  # noqa: E402
                        path_poly, rrect, shade)


# --------------------------------------------------------------------------
# anatomy helpers
# --------------------------------------------------------------------------

def _seg_shape(ctx, p0, p1, w0, w1):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    path_poly(ctx, [(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
                    (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)])
    ctx.fill()
    ctx.arc(p0[0], p0[1], w0 / 2, 0, TAU)
    ctx.fill()
    ctx.arc(p1[0], p1[1], w1 / 2, 0, TAU)
    ctx.fill()


def limb(ctx, pts, widths, colors, lw=5):
    """Tapered multi-segment limb with one continuous ink outline."""
    col(ctx, INK)
    for i in range(len(pts) - 1):
        _seg_shape(ctx, pts[i], pts[i + 1], widths[i] + 2 * lw, widths[i + 1] + 2 * lw)
    for i in range(len(pts) - 1):
        col(ctx, colors[i])
        _seg_shape(ctx, pts[i], pts[i + 1], widths[i], widths[i + 1])


def stripe(ctx, pts, offset, color, w=6):
    """A racing stripe running down a limb."""
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    col(ctx, color)
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, y1 - y0) or 1e-6
        nx, ny = -(y1 - y0) / L * offset, (x1 - x0) / L * offset
        ctx.move_to(x0 + nx, y0 + ny)
        ctx.line_to(x1 + nx, y1 + ny)
    ctx.stroke()


def hand(ctx, wrist, ang, side, kind, skin, glove=False):
    """A real hand: palm, thumb and four fingers, oriented along the forearm."""
    ctx.save()
    ctx.translate(*wrist)
    ctx.rotate(-ang)
    g = 1.25 if glove else 1.0
    th = -side  # thumb faces the body's centre line
    fw = 9.5 * g

    def capsule(x0, y0, x1, y1, w):
        _seg_shape(ctx, (x0, y0), (x1, y1), w, w * 0.9)

    def shape(pad):
        # palm
        rrect(ctx, -17 * g - pad, -2 - pad, 34 * g + 2 * pad, 32 * g + 2 * pad, 12 + pad)
        ctx.fill()
        if kind in ("fist", "point"):
            for k in range(4):
                ctx.arc((-12 + k * 8) * g, 30 * g, 6 * g + pad, 0, TAU)
                ctx.fill()
            capsule(th * 14 * g, 8 * g, -th * 2 * g, 26 * g, fw + 2 * pad)
            if kind == "point":
                capsule(th * 10 * g, 28 * g, th * 10 * g, 62 * g, fw + 2 * pad)
        else:
            spread = 0.22 if kind == "open" else 0.06
            lengths = (24, 27, 25, 19) if kind == "open" else (17, 19, 18, 14)
            for k in range(4):
                x = th * (11 - k * 7.5) * g
                a = th * (1.5 - k) * spread
                L = lengths[k] * g
                capsule(x, 26 * g, x + math.sin(a) * L, 26 * g + math.cos(a) * L, fw + 2 * pad)
            capsule(th * 14 * g, 6 * g, th * 28 * g, 24 * g, (fw + 1) + 2 * pad)

    col(ctx, INK)
    shape(4.5)
    col(ctx, skin)
    shape(0)
    if kind in ("fist", "point"):
        ctx.set_line_width(2.5)
        col(ctx, shade(skin, 0.7))
        for k in range(3):
            x = (-8 + k * 8) * g
            ctx.move_to(x, 24 * g)
            ctx.line_to(x, 34 * g)
        ctx.stroke()
    ctx.restore()


def shoe(ctx, x, y, f, color, sole=None, heel=False, accent=None):
    """Three-quarter view shoe with heel, toe cap and sole."""
    ctx.save()
    ctx.translate(x, y)
    if heel:
        ctx.move_to(-f * 18, -18)
        ctx.line_to(f * 12, -20)
        ctx.curve_to(f * 30, -18, f * 40, -8, f * 40, 2)
        ctx.line_to(-f * 8, 2)
        ctx.line_to(-f * 14, 16)
        ctx.line_to(-f * 22, 16)
        ctx.line_to(-f * 24, -6)
        ctx.close_path()
        fill_ink(ctx, color, 4.5)
    else:
        ctx.move_to(-f * 26, -22)
        ctx.line_to(f * 8, -26)
        ctx.curve_to(f * 30, -24, f * 48, -12, f * 48, 4)
        ctx.line_to(f * 48, 12)
        ctx.line_to(-f * 30, 12)
        ctx.curve_to(-f * 34, 12, -f * 34, -16, -f * 26, -22)
        ctx.close_path()
        fill_ink(ctx, color, 5)
        ctx.rectangle(min(-f * 30, f * 48), 3, 78, 9)
        col(ctx, sole or hexc("#ffffff", 0.55))
        ctx.fill()
        if accent:
            ctx.move_to(-f * 14, -14)
            ctx.curve_to(f * 4, -4, f * 14, -10, f * 26, -2)
            ctx.set_line_width(5)
            col(ctx, accent)
            ctx.stroke()
        ctx.set_line_width(3)
        col(ctx, shade(color, 0.6) if color[0] + color[1] + color[2] > 1.2 else hexc("#ffffff", 0.7))
        for k in range(2):
            ctx.move_to(f * (2 + k * 9), -24 + k)
            ctx.line_to(f * (8 + k * 9), -16 + k)
        ctx.stroke()
    ctx.restore()


def eyes(ctx, st, pts, r=27, lashes=False, brow=None, seed=0.0, skin=None):
    f, t = st["facing"], st["t"]
    mood = st.get("mood")
    blink = ((t + seed) % 4.1) < 0.12
    big = 1.15 if mood == "shock" else 1.0
    for x, y in pts:
        ctx.arc(x, y, r * big, 0, TAU)
        fill_ink(ctx, hexc("#ffffff"), 5)
        if blink:
            ctx.arc(x, y, r * big, 0, TAU)
            col(ctx, skin or hexc("#f2c9a6"))
            ctx.fill()
            ctx.move_to(x - r, y + 2)
            ctx.curve_to(x - r * 0.4, y + 10, x + r * 0.4, y + 10, x + r, y + 2)
            col(ctx, INK)
            ctx.set_line_width(5)
            ctx.stroke()
        else:
            pr = r * (0.26 if mood == "shock" else 0.34)
            ctx.arc(x + f * r * 0.22, y + 1, pr, 0, TAU)
            col(ctx, INK)
            ctx.fill()
            ctx.arc(x + f * r * 0.22 + pr * 0.35, y - pr * 0.35, pr * 0.3, 0, TAU)
            col(ctx, hexc("#ffffff"))
            ctx.fill()
        if lashes and not blink:
            ctx.set_line_width(4)
            col(ctx, INK)
            for k in (-1, 0, 1):
                ctx.move_to(x + k * r * 0.55, y - r * 0.92)
                ctx.line_to(x + k * r * 0.8, y - r * 1.35)
            ctx.stroke()
    cx = sum(p[0] for p in pts) / len(pts)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(7)
    col(ctx, brow or INK)
    for x, y in pts:
        s = 1 if x > cx else -1
        by = y - r * 1.4
        if mood == "angry":      # inner ends pulled down
            ctx.move_to(x - s * r * 0.9, by + 12)
            ctx.line_to(x + s * r * 0.6, by - 10)
        elif mood == "sad":      # inner ends raised
            ctx.move_to(x - s * r * 0.9, by - 10)
            ctx.line_to(x + s * r * 0.6, by + 8)
        elif mood == "shock":
            ctx.move_to(x - r * 0.75, by - 14)
            ctx.curve_to(x - r * 0.25, by - 28, x + r * 0.25, by - 28, x + r * 0.75, by - 14)
        else:
            ctx.move_to(x - r * 0.75, by)
            ctx.curve_to(x - r * 0.25, by - 10, x + r * 0.25, by - 10, x + r * 0.75, by)
        ctx.stroke()


def mouth(ctx, st, x, y, w=26, lip=None):
    t, talk, mood = st["t"], st["talk"], st.get("mood")
    op = talk * (0.35 + 0.65 * abs(math.sin(t * 14)))
    if mood == "shock":
        op = max(op, 0.85)
    if mood == "happy" and op < 0.1:
        op = 0.35
    if op > 0.08:
        h = 10 + 34 * op
        ctx.save()
        ctx.move_to(x - w, y)
        ctx.curve_to(x - w, y + h * 1.4, x + w, y + h * 1.4, x + w, y)
        ctx.curve_to(x + w * 0.5, y - 6, x - w * 0.5, y - 6, x - w, y)
        ctx.close_path()
        ctx.clip_preserve()
        col(ctx, hexc("#7a1426"))
        ctx.fill()
        ellipse(ctx, x, y + h * 1.05, w * 0.6, h * 0.45)
        col(ctx, hexc("#ff7f8f"))
        ctx.fill()
        ctx.rectangle(x - w, y - 8, 2 * w, 9)
        col(ctx, hexc("#ffffff"))
        ctx.fill()
        ctx.restore()
        ctx.move_to(x - w, y)
        ctx.curve_to(x - w, y + h * 1.4, x + w, y + h * 1.4, x + w, y)
        ctx.curve_to(x + w * 0.5, y - 6, x - w * 0.5, y - 6, x - w, y)
        ctx.close_path()
        col(ctx, lip or INK)
        ctx.set_line_width(5)
        ctx.stroke()
    else:
        ctx.set_line_width(5.5)
        col(ctx, lip or INK)
        if mood in ("angry", "sad"):
            ctx.move_to(x - w * 0.7, y + 8)
            ctx.curve_to(x - w * 0.2, y - 4, x + w * 0.2, y - 4, x + w * 0.7, y + 8)
        else:
            ctx.move_to(x - w * 0.7, y)
            ctx.curve_to(x - w * 0.2, y + 12, x + w * 0.2, y + 12, x + w * 0.7, y)
        ctx.stroke()


def nose(ctx, f, y=22, color=None):
    ctx.move_to(f * 2, y - 14)
    ctx.curve_to(f * 14, y, f * 10, y + 8, f * -2, y + 8)
    ctx.set_line_width(4.5)
    col(ctx, color or INK)
    ctx.stroke()


# --------------------------------------------------------------------------
# items
# --------------------------------------------------------------------------

def draw_item(ctx, item, f=1):
    if item == "pizza":
        path_poly(ctx, [(-34, -10), (34, -10), (0, 70)])
        fill_ink(ctx, hexc("#ffcc4d"), 5)
        rrect(ctx, -40, -24, 80, 20, 10)
        fill_ink(ctx, hexc("#d9822b"), 5)
        for px, py in ((-10, 8), (12, 18), (0, 38)):
            ctx.arc(px, py, 7, 0, TAU)
            fill_ink(ctx, hexc("#d62f2f"), 2.5)
    elif item == "mug":
        rrect(ctx, -26, -60, 52, 60, 10)
        fill_ink(ctx, hexc("#ffffff"), 5)
        ctx.arc(f * 30, -32, 14, 0, TAU)
        ctx.set_line_width(7)
        col(ctx, INK)
        ctx.stroke()
        ctx.rectangle(-22, -44, 44, 12)
        col(ctx, hexc("#26c6da"))
        ctx.fill()
    elif item == "mallet":
        ctx.rotate(f * 0.7)  # rests over the shoulder, clear of the face
        rrect(ctx, -7, -110, 14, 130, 6)
        fill_ink(ctx, hexc("#9e9e9e"), 4)
        rrect(ctx, -46, -150, 92, 48, 14)
        fill_ink(ctx, hexc("#ff6fae"), 5)
    elif item == "clipboard":
        rrect(ctx, -40, -100, 80, 110, 8)
        fill_ink(ctx, hexc("#b07a4a"), 5)
        rrect(ctx, -32, -86, 64, 88, 4)
        fill_ink(ctx, hexc("#ffffff"), 3)
        ctx.set_line_width(3)
        col(ctx, hexc("#90a4ae"))
        for k in range(4):
            ctx.move_to(-24, -70 + k * 18)
            ctx.line_to(24, -70 + k * 18)
        ctx.stroke()
        rrect(ctx, -14, -108, 28, 14, 4)
        fill_ink(ctx, hexc("#cfd8dc"), 3)
    elif item == "report":
        path_poly(ctx, [(-36, -96), (36, -96), (36, 0), (-36, 0)])
        fill_ink(ctx, hexc("#ffffff"), 4)
        ctx.set_line_width(3)
        col(ctx, hexc("#90a4ae"))
        for k in range(5):
            ctx.move_to(-26, -80 + k * 15)
            ctx.line_to(26, -80 + k * 15)
        ctx.stroke()


# --------------------------------------------------------------------------
# base body
# --------------------------------------------------------------------------

class Squad(Humanoid):
    thigh = 112
    shin = 108
    foot_h = 26
    torso = 230
    torso_w = 190
    arm_up = 100
    arm_lo = 92
    head_off = 118
    head_top_ext = 120
    scale = 1.0
    skin = hexc("#f2c9a6")
    top = hexc("#888888")     # shirt / jacket
    sleeve = None            # upper sleeve colour (defaults to top)
    forearm = None           # forearm colour (defaults to sleeve -> long sleeves)
    pants = hexc("#455a64")
    shin_col = None
    shoe_col = hexc("#2b2b2b")
    shoe_sole = None
    shoe_accent = None
    heels = False
    glove = False
    default_style = "normal"
    item_side = 1

    # ---- pose ----
    def arm_targets(self, st):
        """(right_upper, right_lower, left_upper, left_lower) screen angles."""
        ph, w, t, f = st["phase"], st["walkw"], st["t"], st["facing"]
        amp = WALK_STYLES[st["style"]][2] * 0.65
        sw = f * amp * w * math.sin(ph)
        pose = st["arms"]
        bend = f * 0.18 * w
        R = (0.13 + sw, 0.05 + sw + bend)
        L = (-0.13 - sw, -0.05 - sw + bend)

        def both(up, lo):
            return (up, lo), (-up, -lo)

        if pose == "stiff":
            R, L = both(0.1, 0.04)
        elif pose == "up":
            wig = 0.1 * math.sin(t * 12)
            R, L = (2.55 + wig, 2.85 + wig), (-2.55 + wig, -2.85 + wig)
        elif pose == "wave":
            R = (2.35, 2.75 + 0.45 * math.sin(t * 10))
        elif pose == "point":
            if f > 0:
                R = (1.45, 1.5)
            else:
                L = (-1.45, -1.5)
        elif pose == "hips":
            R, L = both(0.8, -0.85)
        elif pose == "shrug":
            R, L = both(0.55, 1.95)
        elif pose == "hold":
            R = (0.32, -2.15)
        elif pose == "type":
            j = 0.12 * math.sin(t * 34)
            R, L = (0.35, -1.25 + j), (-0.35, 1.25 + j)
        elif pose == "hero":
            R, L = (2.95, 3.1), (-0.8, 0.85)
        elif pose == "facepalm":
            R = (0.65, -2.7)
        elif pose == "cover":
            R, L = (0.65, -2.65), (-0.65, 2.65)
        elif pose == "run":
            pass
        return R + L

    def hand_kind(self, st, side):
        pose = st["arms"]
        f = st["facing"]
        if pose in ("up", "wave", "shrug", "cover", "facepalm"):
            return "open"
        if pose == "point" and side == f:
            return "point"
        if pose == "hero" and side == 1:
            return "fist"
        if pose == "hold" and side == 1:
            return "fist"
        return "relax"

    # ---- kinematics ----
    def legs(self, st):
        if st.get("sit"):
            k = (0, 34)
            foot = (0, 34 + self.shin)
            return (k, foot, 0.0), (k, foot, 0.0), -(34 + self.shin + self.foot_h)
        ph, w, style = st["phase"], st["walkw"], st["style"]
        a = self.leg(ph, w, style)
        b = self.leg(ph + math.pi, w, style)
        return a, b, -self.hip_height(ph, w, style)

    def head_top(self, st):
        _, _, hip = self.legs(st)
        return (-hip + self.torso + self.head_off + self.head_top_ext) * self.scale + st.get("lift", 0)

    # ---- drawing ----
    def draw(self, ctx, st):
        f = st["facing"]
        ctx.save()
        sx = st.get("squash", 0.0)
        ctx.translate(st["x"] + math.sin(st["t"] * 70) * 7 * st["shake"], -st["jump"] - st.get("lift", 0))
        ctx.rotate(st.get("spin", 0.0))
        ctx.scale(self.scale * (1 + sx), self.scale * (1 - sx))
        legR, legL, hip = self.legs(st)
        if not st.get("sit"):
            hip += math.sin(st["t"] * 2.2) * 2.5 * (1 - st["walkw"])
        top = hip - self.torso
        self.behind(ctx, st, hip, top)
        # legs: the one on the far side of the walk first
        order = ((-1, legL), (1, legR)) if f > 0 else ((1, legR), (-1, legL))
        for side, lg in order:
            self.draw_leg(ctx, st, side, hip, lg)
        self.draw_torso(ctx, st, hip, top)
        arms = st.get("arm_ang") or self.arm_targets(st)
        sh_y = top + 36
        for side, (up, lo) in ((-1, arms[2:4]), (1, arms[0:2])):
            self.draw_arm(ctx, st, side, (side * (self.torso_w / 2 - 18), sh_y), up, lo)
        # neck + head
        talk = st["talk"]
        tilt = talk * 0.05 * math.sin(st["t"] * 13) + st.get("tilt", 0.0)
        bob = -abs(math.sin(st["t"] * 8)) * 5 * talk
        ctx.save()
        ctx.translate(0, top - self.head_off + 14 + bob)
        ctx.rotate(tilt)
        self.draw_head(ctx, st)
        ctx.restore()
        self.front(ctx, st, hip, top)
        ctx.restore()

    def behind(self, ctx, st, hip, top):
        pass

    def front(self, ctx, st, hip, top):
        pass

    def draw_leg(self, ctx, st, side, hip, lg):
        (kx, ky), (fx, fy), b = lg
        f = st["facing"]
        hx = side * 44
        p0 = (hx, hip)
        p1 = (hx + kx * f, hip + ky)
        p2 = (hx + fx * f, hip + fy)
        shin_c = self.shin_col or self.pants
        limb(ctx, [p0, p1, p2], [62, 50, 38], [self.pants, shin_c])
        self.leg_details(ctx, st, side, [p0, p1, p2])
        shoe(ctx, p2[0], p2[1] + self.foot_h * 0.5, f, self.shoe_col, self.shoe_sole, self.heels,
             self.shoe_accent)

    def leg_details(self, ctx, st, side, pts):
        pass

    def draw_arm(self, ctx, st, side, sh, up, lo):
        e = (sh[0] + math.sin(up) * self.arm_up, sh[1] + math.cos(up) * self.arm_up)
        w = (e[0] + math.sin(lo) * self.arm_lo, e[1] + math.cos(lo) * self.arm_lo)
        sl = self.sleeve or self.top
        fa = self.forearm or sl
        limb(ctx, [sh, e, w], [50, 42, 34], [sl, fa])
        self.arm_details(ctx, st, side, [sh, e, w])
        item = st.get("item")
        if item and side == self.item_side:
            ctx.save()
            ctx.translate(*w)
            draw_item(ctx, item, st["facing"])
            ctx.restore()
        hand(ctx, w, lo, side, self.hand_kind(st, side), hexc("#f4f4f4") if self.glove else self.skin,
             self.glove)

    def arm_details(self, ctx, st, side, pts):
        pass

    def draw_torso(self, ctx, st, hip, top):
        rrect(ctx, -self.torso_w / 2, top, self.torso_w, self.torso + 24, 34)
        fill_ink(ctx, self.top, 6)
        self.torso_details(ctx, st, hip, top)

    def torso_details(self, ctx, st, hip, top):
        pass

    def head_base(self, ctx, rx=90, ry=96, ears=True):
        if ears:
            for s in (-1, 1):
                ellipse(ctx, s * rx * 0.98, 12, 17, 22)
                fill_ink(ctx, self.skin, 5)
        ellipse(ctx, 0, 0, rx, ry)
        fill_ink(ctx, self.skin, 6)

    def draw_head(self, ctx, st):
        self.head_base(ctx)
        eyes(ctx, st, [(-32, -8), (32, -8)], skin=self.skin)
        nose(ctx, st["facing"])
        mouth(ctx, st, 0, 52)


# --------------------------------------------------------------------------
# the squad
# --------------------------------------------------------------------------

class Mo(Squad):
    """Mighty Mo - accountant by day, superhero... also by day."""
    scale = 1.05
    skin = hexc("#9a6440")
    top = hexc("#e53935")
    pants = hexc("#e53935")
    shoe_col = hexc("#c9a227")
    head_top_ext = 165

    def behind(self, ctx, st, hip, top):
        t, f, w = st["t"], st["facing"], st["walkw"]
        fl = 30 * math.sin(t * 6) + 60 * w + 160 * min(1.0, st.get("lift", 0) / 300)
        ctx.move_to(-self.torso_w / 2 + 10, top + 10)
        ctx.line_to(self.torso_w / 2 - 10, top + 10)
        ctx.curve_to(self.torso_w / 2 + 30, hip + 40, self.torso_w / 2 + 40 - f * fl, hip + 120,
                     self.torso_w / 2 + 50 - f * fl, hip + 170)
        ctx.line_to(-self.torso_w / 2 - 50 - f * fl, hip + 170)
        ctx.curve_to(-self.torso_w / 2 - 40 - f * fl, hip + 120, -self.torso_w / 2 - 30, hip + 40,
                     -self.torso_w / 2 + 10, top + 10)
        ctx.close_path()
        fill_ink(ctx, hexc("#ffc107"), 6)

    def torso_details(self, ctx, st, hip, top):
        rrect(ctx, -self.torso_w / 2 + 4, hip - 34, self.torso_w - 8, 30, 6)
        fill_ink(ctx, hexc("#ffc107"), 4)
        ctx.arc(0, top + 92, 44, 0, TAU)
        fill_ink(ctx, hexc("#ffd23f"), 6)
        ctx.select_font_face("Luckiest Guy")
        ctx.set_font_size(56)
        e = ctx.text_extents("M")
        ctx.move_to(-e.width / 2 - e.x_bearing, top + 112)
        col(ctx, INK)
        ctx.show_text("M")

    def draw_head(self, ctx, st):
        f = st["facing"]
        self.head_base(ctx)
        # flat-top
        rrect(ctx, -86, -165, 172, 120, 8)
        fill_ink(ctx, hexc("#141414"), 6)
        for s in (-1, 1):
            rrect(ctx, s * 86 - (14 if s > 0 else 0), -70, 14, 60, 4)
            col(ctx, hexc("#141414"))
            ctx.fill()
        # domino mask
        ctx.move_to(-92, -30)
        ctx.curve_to(-60, -46, 60, -46, 92, -30)
        ctx.line_to(92, 18)
        ctx.curve_to(40, 22, 14, 6, 0, 10)
        ctx.curve_to(-14, 6, -40, 22, -92, 18)
        ctx.close_path()
        fill_ink(ctx, hexc("#111111"), 4)
        eyes(ctx, st, [(-34, -8), (34, -8)], r=25, skin=hexc("#111111"), brow=hexc("#111111"))
        nose(ctx, f, 28, hexc("#3b2416"))
        # mustache
        ctx.move_to(0, 42)
        for s in (-1, 1):
            ctx.move_to(0, 42)
            ctx.curve_to(s * 20, 30, s * 46, 34, s * 54, 52)
            ctx.curve_to(s * 40, 46, s * 22, 50, 0, 50)
        fill_ink(ctx, hexc("#111111"), 3)
        mouth(ctx, st, 0, 60, 24)


class Baldwin(Squad):
    """Mr. Baldwin - the boss. Loves meetings, fears change."""
    skin = hexc("#f1c7a3")
    top = hexc("#33415c")
    pants = hexc("#2b3448")
    shoe_col = hexc("#1b1b1b")
    head_off = 124
    head_top_ext = 110

    def torso_details(self, ctx, st, hip, top):
        path_poly(ctx, [(-42, top + 2), (42, top + 2), (0, top + 120)])
        fill_ink(ctx, hexc("#ffffff"), 4)
        path_poly(ctx, [(-10, top + 18), (10, top + 18), (16, top + 120), (0, top + 140), (-16, top + 120)])
        fill_ink(ctx, hexc("#d32f2f"), 4)
        rrect(ctx, -12, top + 4, 24, 20, 4)
        fill_ink(ctx, hexc("#b71c1c"), 3)
        ctx.set_line_width(5)
        col(ctx, INK)
        for s in (-1, 1):
            ctx.move_to(s * 44, top + 2)
            ctx.line_to(s * 14, top + 140)
        ctx.stroke()
        for k in range(2):
            ctx.arc(0, top + 168 + k * 34, 7, 0, TAU)
            fill_ink(ctx, hexc("#90a4ae"), 3)

    def draw_head(self, ctx, st):
        self.head_base(ctx, 96, 106)
        g = cairo.RadialGradient(-20, -70, 4, -20, -70, 50)
        g.add_color_stop_rgba(0, 1, 1, 1, 0.7)
        g.add_color_stop_rgba(1, 1, 1, 1, 0)
        ctx.set_source(g)
        ctx.arc(-20, -70, 50, 0, TAU)
        ctx.fill()
        for s in (-1, 1):
            ellipse(ctx, s * 88, -20, 22, 40)
            fill_ink(ctx, hexc("#bdbdbd"), 5)
        eyes(ctx, st, [(-34, -6), (34, -6)], r=28, brow=hexc("#9e9e9e"), skin=self.skin, seed=1.1)
        nose(ctx, st["facing"], 30)
        mouth(ctx, st, 0, 62, 26)


class Noor(Squad):
    """Noor - the only one who actually reads the emails."""
    scale = 0.97
    skin = hexc("#f3c19a")
    top = hexc("#c98aa4")
    pants = hexc("#4a2f3d")
    shoe_col = hexc("#6d4c41")
    head_top_ext = 135

    def draw_torso(self, ctx, st, hip, top):
        path_poly(ctx, [(-self.torso_w / 2, top + 60), (self.torso_w / 2, top + 60),
                        (self.torso_w / 2 + 26, hip + 110), (-self.torso_w / 2 - 26, hip + 110)])
        fill_ink(ctx, self.top, 6)
        rrect(ctx, -self.torso_w / 2, top, self.torso_w, self.torso, 34)
        fill_ink(ctx, self.top, 6)
        for k in range(4):
            ctx.arc(0, top + 100 + k * 40, 6, 0, TAU)
            fill_ink(ctx, hexc("#fce4ec"), 3)
        path_poly(ctx, [(-112, top - 60), (112, top - 60), (138, top + 72), (-138, top + 72)])
        fill_ink(ctx, hexc("#8e2b3a"), 6)

    def draw_head(self, ctx, st):
        # hijab
        ellipse(ctx, 0, 0, 112, 124)
        fill_ink(ctx, hexc("#8e2b3a"), 6)
        ellipse(ctx, 0, 12, 76, 88)
        fill_ink(ctx, self.skin, 5)
        ellipse(ctx, 0, 12, 82, 94)
        ctx.set_line_width(10)
        col(ctx, hexc("#a8344a"))
        ctx.stroke()
        eyes(ctx, st, [(-28, 0), (28, 0)], r=24, lashes=True, skin=self.skin, seed=2.2)
        nose(ctx, st["facing"], 32)
        mouth(ctx, st, 0, 64, 22, lip=hexc("#c2185b"))


class Ruby(Squad):
    """Ruby - office handywoman. Every problem is a hammer problem."""
    scale = 0.97
    skin = hexc("#f7d3b5")
    top = hexc("#8e63c7")
    pants = hexc("#3f6fb5")
    shoe_col = hexc("#7b4a2a")
    head_top_ext = 130

    def torso_details(self, ctx, st, hip, top):
        rrect(ctx, -62, top + 70, 124, self.torso - 46, 14)
        fill_ink(ctx, hexc("#4f7fd0"), 5)
        for s in (-1, 1):
            ctx.move_to(s * 50, top + 72)
            ctx.line_to(s * 66, top)
            ctx.set_line_width(14)
            col(ctx, hexc("#4f7fd0"))
            ctx.stroke()
            ctx.arc(s * 48, top + 84, 7, 0, TAU)
            fill_ink(ctx, hexc("#ffd23f"), 3)
        rrect(ctx, -30, top + 110, 60, 40, 6)
        fill_ink(ctx, hexc("#3f6fb5"), 4)

    def behind(self, ctx, st, hip, top):
        ctx.save()
        ctx.translate(0, top - self.head_off + 14)
        ctx.move_to(-104, -20)
        ctx.curve_to(-120, 120, -90, 170, -60, 180)
        ctx.line_to(60, 180)
        ctx.curve_to(90, 170, 120, 120, 104, -20)
        ctx.curve_to(100, -140, -100, -140, -104, -20)
        fill_ink(ctx, hexc("#e8642c"), 6)
        ctx.restore()

    def draw_head(self, ctx, st):
        ctx.save()
        ctx.arc(0, 0, 200, math.pi, TAU)  # top of the hair, in front of the shoulders
        ctx.clip()
        ctx.move_to(-104, -20)
        ctx.curve_to(-100, -140, 100, -140, 104, -20)
        ctx.close_path()
        fill_ink(ctx, hexc("#e8642c"), 6)
        ctx.restore()
        self.head_base(ctx, 86, 92)
        # bangs
        ctx.move_to(-92, -10)
        ctx.curve_to(-96, -120, 96, -120, 92, -10)
        ctx.curve_to(60, -60, 20, -70, -10, -48)
        ctx.curve_to(-40, -60, -70, -40, -92, -10)
        fill_ink(ctx, hexc("#f07438"), 5)
        eyes(ctx, st, [(-30, 4), (30, 4)], r=25, lashes=True, skin=self.skin, seed=0.6)
        col(ctx, hexc("#d9825b"))
        for x, y in ((-56, 40), (-46, 48), (-62, 50), (56, 40), (46, 48), (62, 50)):
            ctx.arc(x, y, 3.5, 0, TAU)
            ctx.fill()
        nose(ctx, st["facing"], 34)
        mouth(ctx, st, 0, 62, 22, lip=hexc("#c2185b"))


class Grace(Squad):
    """Grace - HR. Has a form for everything."""
    scale = 0.98
    skin = hexc("#f1d0b5")
    top = hexc("#1f1f24")
    pants = hexc("#1f1f24")
    shin_col = hexc("#f1d0b5")
    shoe_col = hexc("#111111")
    heels = True
    head_top_ext = 150
    torso_w = 175

    def draw_torso(self, ctx, st, hip, top):
        rrect(ctx, -self.torso_w / 2, top, self.torso_w, self.torso + 24, 30)
        fill_ink(ctx, self.top, 6)
        path_poly(ctx, [(-36, top + 2), (36, top + 2), (0, top + 110)])
        fill_ink(ctx, hexc("#ffffff"), 4)
        ctx.set_line_width(5)
        col(ctx, hexc("#4a4a55"))
        for s in (-1, 1):
            ctx.move_to(s * 40, top + 2)
            ctx.line_to(s * 10, top + 130)
        ctx.stroke()
        # pencil skirt over the thighs
        path_poly(ctx, [(-self.torso_w / 2 + 6, hip - 30), (self.torso_w / 2 - 6, hip - 30),
                        (self.torso_w / 2 - 10, hip + 112), (-self.torso_w / 2 + 10, hip + 112)])
        fill_ink(ctx, hexc("#2a2a30"), 6)

    def draw_head(self, ctx, st):
        ctx.arc(0, -110, 44, 0, TAU)
        fill_ink(ctx, hexc("#24201f"), 6)
        ellipse(ctx, 0, -20, 98, 96)
        fill_ink(ctx, hexc("#24201f"), 6)
        self.head_base(ctx, 82, 92, ears=False)
        ctx.move_to(-84, -10)
        ctx.curve_to(-80, -100, 60, -110, 84, -20)
        ctx.curve_to(40, -70, -20, -60, -84, -10)
        fill_ink(ctx, hexc("#2e2927"), 5)
        if st.get("mood") is None:
            st = dict(st, mood="angry")
        eyes(ctx, st, [(-30, 4), (30, 4)], r=23, lashes=True, skin=self.skin, seed=3.3)
        nose(ctx, st["facing"], 34)
        mouth(ctx, st, 0, 62, 20, lip=hexc("#c62828"))


class Kiki(Squad):
    """Kiki - the intern. Turns every task into cardio."""
    scale = 0.92
    skin = hexc("#f0c8a0")
    top = hexc("#29c6e8")
    pants = hexc("#29c6e8")
    shoe_col = hexc("#ffffff")
    shoe_sole = hexc("#29c6e8")
    shoe_accent = hexc("#29c6e8")
    head_top_ext = 165

    def torso_details(self, ctx, st, hip, top):
        ctx.move_to(0, top + 20)
        ctx.line_to(0, hip + 20)
        ctx.set_line_width(5)
        col(ctx, hexc("#ffffff"))
        ctx.stroke()
        rrect(ctx, -46, top - 6, 92, 26, 10)
        fill_ink(ctx, hexc("#1fb2d4"), 4)
        rrect(ctx, -6, top + 30, 12, 22, 3)
        fill_ink(ctx, hexc("#e0e0e0"), 3)

    def arm_details(self, ctx, st, side, pts):
        stripe(ctx, pts, side * 14, hexc("#ffffff"))

    def leg_details(self, ctx, st, side, pts):
        stripe(ctx, pts, side * 18, hexc("#ffffff"))

    def draw_head(self, ctx, st):
        bounce = 5 * math.sin(st["t"] * 7) * (st["walkw"] + st["talk"])
        for s in (-1, 1):
            ctx.arc(s * 56, -104 + bounce * s, 34, 0, TAU)
            fill_ink(ctx, hexc("#8d5a3b"), 6)
        self.head_base(ctx, 88, 94)
        ctx.move_to(-90, -10)
        ctx.curve_to(-94, -116, 94, -116, 90, -10)
        ctx.curve_to(60, -54, -60, -54, -90, -10)
        fill_ink(ctx, hexc("#9a6440"), 5)
        rrect(ctx, -92, -60, 184, 26, 10)
        fill_ink(ctx, hexc("#ff4f8b"), 5)
        eyes(ctx, st, [(-30, 4), (30, 4)], r=26, lashes=True, skin=self.skin, seed=1.9)
        nose(ctx, st["facing"], 36)
        mouth(ctx, st, 0, 62, 22)


class Steve(Squad):
    """Space Steve - IT department. Has not taken the suit off since 2019."""
    scale = 1.02
    skin = hexc("#f2c9a6")
    top = hexc("#f2f2f2")
    pants = hexc("#f2f2f2")
    shoe_col = hexc("#9e9e9e")
    glove = True
    head_top_ext = 160
    torso_w = 210

    def torso_details(self, ctx, st, hip, top):
        rrect(ctx, 6, top + 50, 74, 60, 8)
        fill_ink(ctx, hexc("#37474f"), 5)
        for k, c in enumerate(("#ff5252", "#69f0ae")):
            on = int(st["t"] * 3 + k) % 2
            ctx.arc(26 + k * 30, top + 76, 8, 0, TAU)
            fill_ink(ctx, hexc(c) if on else shade(hexc(c), 0.5), 3)
        rrect(ctx, -82, top + 54, 60, 34, 6)
        fill_ink(ctx, hexc("#e53935"), 4)
        rrect(ctx, -self.torso_w / 2 + 4, hip - 30, self.torso_w - 8, 22, 6)
        fill_ink(ctx, hexc("#cfd8dc"), 4)

    def arm_details(self, ctx, st, side, pts):
        (x, y) = pts[1]
        ellipse(ctx, x, y, 24, 10)
        col(ctx, hexc("#cfd8dc"))
        ctx.fill()

    def leg_details(self, ctx, st, side, pts):
        (x, y) = pts[1]
        ellipse(ctx, x, y, 28, 11)
        col(ctx, hexc("#cfd8dc"))
        ctx.fill()

    def draw_head(self, ctx, st):
        rrect(ctx, -84, 70, 168, 40, 16)
        fill_ink(ctx, hexc("#b0bec5"), 6)
        self.head_base(ctx, 82, 88)
        ctx.move_to(-84, -6)
        ctx.curve_to(-90, -110, 90, -110, 84, -6)
        for k in range(6):
            ctx.line_to(84 - k * 30, -40 + (k % 2) * 20)
        ctx.close_path()
        fill_ink(ctx, hexc("#6d4c41"), 5)
        eyes(ctx, st, [(-30, 2), (30, 2)], r=22, skin=self.skin, seed=2.7)
        ctx.set_line_width(6)
        col(ctx, INK)
        for s in (-1, 1):
            ctx.arc(s * 30, 2, 33, 0, TAU)
            ctx.stroke()
        ctx.move_to(-4, 0)
        ctx.line_to(4, 0)
        ctx.stroke()
        nose(ctx, st["facing"], 36)
        mouth(ctx, st, 0, 62, 20)
        # helmet glass
        ctx.arc(0, -4, 132, 0, TAU)
        col(ctx, hexc("#bfe9ff", 0.22))
        ctx.fill_preserve()
        col(ctx, INK)
        ctx.set_line_width(7)
        ctx.stroke()
        ctx.arc(0, -4, 112, math.pi * 1.1, math.pi * 1.45)
        col(ctx, hexc("#ffffff", 0.85))
        ctx.set_line_width(12)
        ctx.stroke()


class Pixel:
    """Pixel - the office cat. The real boss."""
    scale = 1.0
    default_style = "normal"

    def head_top(self, st):
        return 210 + st.get("lift", 0)

    def arm_targets(self, st):
        return (0, 0, 0, 0)

    def draw(self, ctx, st):
        t, f, w = st["t"], st["facing"], st["walkw"]
        ctx.save()
        ctx.translate(st["x"] + math.sin(t * 70) * 7 * st["shake"],
                      -st["jump"] - st.get("lift", 0) - abs(math.sin(st["phase"])) * 18 * w)
        ctx.scale(st.get("cat_scale", 1.0), st.get("cat_scale", 1.0))
        fur, dark = hexc("#f39a3d"), hexc("#d9782a")
        # tail
        wag = math.sin(t * 3) * 0.3
        ctx.move_to(-f * 50, -30)
        ctx.curve_to(-f * 130, -30, -f * (120 + 30 * wag), -150, -f * 80, -150)
        ctx.set_line_width(26)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        col(ctx, INK)
        ctx.stroke_preserve()
        ctx.set_line_width(16)
        col(ctx, fur)
        ctx.stroke()
        # body (sitting, pear shaped)
        ctx.move_to(-70, 0)
        ctx.curve_to(-80, -90, -40, -130, 0, -130)
        ctx.curve_to(40, -130, 80, -90, 70, 0)
        ctx.close_path()
        fill_ink(ctx, fur, 6)
        ellipse(ctx, 0, -50, 34, 44)
        col(ctx, hexc("#ffe0b2"))
        ctx.fill()
        for s in (-1, 1):
            ellipse(ctx, s * 30, -6, 22, 12)
            fill_ink(ctx, fur, 5)
        # head
        ctx.save()
        ctx.translate(f * 4, -150)
        for s in (-1, 1):
            path_poly(ctx, [(s * 28, -40), (s * 70, -40), (s * 58, -92)])
            fill_ink(ctx, fur, 5)
            path_poly(ctx, [(s * 38, -44), (s * 62, -44), (s * 56, -74)])
            col(ctx, hexc("#ffab91"))
            ctx.fill()
        ellipse(ctx, 0, -10, 78, 62)
        fill_ink(ctx, fur, 6)
        for s in (-1, 1):
            ctx.move_to(s * 30, -50)
            ctx.line_to(s * 22, -34)
            ctx.set_line_width(5)
            col(ctx, dark)
            ctx.stroke()
        happy = st.get("mood") == "happy"
        for s in (-1, 1):
            if happy:
                ctx.move_to(s * 26 - 12, -12)
                ctx.curve_to(s * 26 - 4, -24, s * 26 + 4, -24, s * 26 + 12, -12)
                ctx.set_line_width(5)
                col(ctx, INK)
                ctx.stroke()
            else:
                ellipse(ctx, s * 26, -14, 15, 13)
                fill_ink(ctx, hexc("#fff59d"), 4)
                ellipse(ctx, s * 26 + f * 3, -14, 4, 10)
                col(ctx, INK)
                ctx.fill()
                ctx.rectangle(s * 26 - 16, -30, 32, 10)  # half-lidded, unimpressed
                col(ctx, fur)
                ctx.fill()
        path_poly(ctx, [(-7, 4), (7, 4), (0, 12)])
        fill_ink(ctx, hexc("#ff8a80"), 3)
        ctx.move_to(0, 12)
        ctx.curve_to(-8, 24, -16, 22, -18, 16)
        ctx.move_to(0, 12)
        ctx.curve_to(8, 24, 16, 22, 18, 16)
        ctx.set_line_width(4)
        col(ctx, INK)
        ctx.stroke()
        if st["talk"] > 0.1 or st.get("lick"):
            ellipse(ctx, 6, 26, 9, 12)
            fill_ink(ctx, hexc("#ff8a80"), 3)
        ctx.set_line_width(2.5)
        for s in (-1, 1):
            for k in (-1, 0, 1):
                ctx.move_to(s * 30, 8 + k * 6)
                ctx.line_to(s * 78, 2 + k * 12)
        ctx.stroke()
        ctx.restore()
        ctx.restore()


CAST = {"mo": Mo, "boss": Baldwin, "noor": Noor, "ruby": Ruby, "grace": Grace, "kiki": Kiki,
        "steve": Steve, "pixel": Pixel}
