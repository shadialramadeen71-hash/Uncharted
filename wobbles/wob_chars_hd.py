"""THE WOBBLES, redrawn in the improved style (same look as OFFICE SQUAD):
proper hands with fingers, tapered arms and legs with elbows and knees, real
shoes, big round cartoon eyes. Same characters, same outfits.

Importing this and updating wob_engine.CAST swaps the family to the new art.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "office-squad"))
sys.path.insert(1, os.path.join(HERE, "..", "mask-buddies"))

import sq_chars  # noqa: E402
import wob_chars  # noqa: E402
from sq_chars import (INK, TAU, Squad, col, ellipse, eyes, fill_ink, hexc, mouth, nose,  # noqa: E402
                      path_poly, rrect)
from characters import stroke_limb  # noqa: E402


def draw_item(ctx, item, f=1):
    """Every prop the Wobbles use, in the new style."""
    if item == "spatula":
        stroke_limb(ctx, [(0, 10), (0, -80)], 12, hexc("#c8915a"), 4)
        rrect(ctx, -26, -150, 52, 70, 10)
        fill_ink(ctx, hexc("#d9d9de"), 5)
        for k in (-10, 0, 10):
            ctx.rectangle(k - 2, -140, 4, 46)
        col(ctx, hexc("#9e9e9e"))
        ctx.fill()
    elif item == "remote":
        rrect(ctx, -14, -70, 28, 80, 8)
        fill_ink(ctx, hexc("#333344"), 4)
        ctx.arc(0, -52, 7, 0, TAU)
        col(ctx, hexc("#ff3b3b"))
        ctx.fill()
    elif item == "mic":
        stroke_limb(ctx, [(0, 10), (0, -50)], 14, hexc("#333344"), 4)
        ctx.arc(0, -66, 24, 0, TAU)
        fill_ink(ctx, hexc("#c0c6d6"), 5)
        ctx.set_line_width(2)
        col(ctx, hexc("#8a90a0"))
        for k in (-10, 0, 10):
            ctx.move_to(k, -88)
            ctx.line_to(k, -44)
        ctx.stroke()
    elif item == "plate":
        ctx.save()
        ctx.translate(0, -16)
        ellipse(ctx, 0, 0, 82, 18)
        fill_ink(ctx, hexc("#ffffff"), 5)
        for k in (-30, 0, 30):
            ellipse(ctx, k, -14, 26, 12)
            fill_ink(ctx, hexc("#e9b44c"), 3)
        ctx.restore()
    elif item in ("gnome", "card10", "sandwich", "wrench", "plank"):
        wob_chars.draw_item(ctx, item)
    else:
        sq_chars.draw_item(ctx, item, f)


class Fam(Squad):
    def draw_arm(self, ctx, st, side, sh, up, lo):
        # same as Squad.draw_arm but with the Wobbles' props
        e = (sh[0] + math.sin(up) * self.arm_up, sh[1] + math.cos(up) * self.arm_up)
        w = (e[0] + math.sin(lo) * self.arm_lo, e[1] + math.cos(lo) * self.arm_lo)
        sl = self.sleeve or self.top
        fa = self.forearm or sl
        sq_chars.limb(ctx, [sh, e, w], [50, 42, 34], [sl, fa])
        self.arm_details(ctx, st, side, [sh, e, w])
        item = st.get("item")
        if item and side == self.item_arm(st):
            ctx.save()
            ctx.translate(*w)
            draw_item(ctx, item, st["facing"])
            ctx.restore()
        kind = self.hand_kind(st, side)
        if item and side == self.item_arm(st):
            kind = "fist"
        sq_chars.hand(ctx, w, lo, side, kind, self.skin)


class Gary(Fam):
    """Dad. Pickle-factory worker, self-declared grill master."""
    scale = 1.05
    skin = hexc("#f4c69a")
    top = hexc("#79aee6")
    forearm = hexc("#f4c69a")
    pants = hexc("#6d4c41")
    shoe_col = hexc("#2b2b2b")
    torso_w = 215
    head_top_ext = 150

    def torso_details(self, ctx, st, hip, top):
        f = st["facing"]
        ellipse(ctx, f * 8, hip - 72, 104, 92)
        fill_ink(ctx, self.top, 6)
        path_poly(ctx, [(-42, top + 2), (0, top + 40), (42, top + 2)], close=False)
        ctx.set_line_width(7)
        col(ctx, hexc("#ffffff"))
        ctx.stroke()
        for k in range(2):
            ctx.arc(0, top + 52 + k * 26, 5, 0, TAU)
            fill_ink(ctx, hexc("#ffffff"), 2)
        ellipse(ctx, -54, top + 76, 18, 9)
        fill_ink(ctx, hexc("#6abf4b"), 3)
        rrect(ctx, -self.torso_w / 2 + 6, hip - 14, self.torso_w - 12, 18, 6)
        fill_ink(ctx, hexc("#3e2723"), 3)

    def arm_details(self, ctx, st, side, pts):
        (x, y) = pts[1]
        ellipse(ctx, x, y, 26, 14)  # short polo sleeve cuff at the elbow
        fill_ink(ctx, self.top, 4)

    def draw_head(self, ctx, st):
        f = st["facing"]
        self.head_base(ctx, 92, 100)
        # ginger beard around the jaw
        ctx.move_to(-92, 4)
        ctx.curve_to(-94, 96, -40, 128, 0, 130)
        ctx.curve_to(40, 128, 94, 96, 92, 4)
        ctx.curve_to(62, 42, 30, 46, 0, 44)
        ctx.curve_to(-30, 46, -62, 42, -92, 4)
        fill_ink(ctx, hexc("#c4622d"), 6)
        mouth(ctx, st, 0, 72, 28)
        eyes(ctx, st, [(-34, -16), (34, -16)], r=28, skin=self.skin, seed=0.4)
        ellipse(ctx, f * 8, 24, 24, 20)
        fill_ink(ctx, hexc("#ec9a7e"), 5)
        # green cap with pickle logo
        ctx.move_to(-98, -52)
        ctx.curve_to(-98, -158, 98, -158, 98, -52)
        ctx.close_path()
        fill_ink(ctx, hexc("#3d8b3d"), 6)
        ellipse(ctx, f * 70, -54, 84, 17)
        fill_ink(ctx, hexc("#2e6e2e"), 5)
        ellipse(ctx, 0, -104, 28, 15)
        fill_ink(ctx, hexc("#9be15d"), 4)


class Linda(Fam):
    """Mom. The only sane person in the house."""
    skin = hexc("#c98a5e")
    top = hexc("#8e44ad")
    sleeve = hexc("#a35fc4")
    pants = hexc("#8e44ad")
    shin_col = hexc("#c98a5e")
    shoe_col = hexc("#d6334a")
    heels = True
    torso_w = 175
    head_top_ext = 190

    def draw_torso(self, ctx, st, hip, top):
        path_poly(ctx, [(-self.torso_w / 2 + 6, top + 80), (self.torso_w / 2 - 6, top + 80),
                        (self.torso_w / 2 + 40, hip + 112), (-self.torso_w / 2 - 40, hip + 112)])
        fill_ink(ctx, self.top, 6)
        rrect(ctx, -self.torso_w / 2, top, self.torso_w, 150, 34)
        fill_ink(ctx, self.top, 6)
        rrect(ctx, -self.torso_w / 2 + 6, top + 128, self.torso_w - 12, 18, 6)
        fill_ink(ctx, hexc("#ffd23f"), 3)
        for k in range(3):
            ctx.arc(0, top + 34 + k * 30, 6, 0, TAU)
            fill_ink(ctx, hexc("#ffffff"), 2)

    def draw_head(self, ctx, st):
        for a in range(15):
            ang = math.pi * 0.95 + a * math.pi * 1.1 / 14
            ctx.arc(math.cos(ang) * 96, -18 + math.sin(ang) * 112, 46, 0, TAU)
            fill_ink(ctx, hexc("#b8322a"), 5)
        ellipse(ctx, 0, -50, 110, 96)
        col(ctx, hexc("#b8322a"))
        ctx.fill()
        self.head_base(ctx, 82, 94, ears=False)
        for s in (-1, 1):
            ctx.arc(s * 80, 42, 11, 0, TAU)
            fill_ink(ctx, hexc("#f5f0e1"), 3)
        for i in range(-3, 4):
            ctx.arc(i * 22, -82, 21, 0, TAU)
            fill_ink(ctx, hexc("#c4392f"), 4)
        eyes(ctx, st, [(-30, -6), (30, -6)], r=25, lashes=True, skin=self.skin, seed=1.7)
        nose(ctx, st["facing"], 30, hexc("#7a4a2a"))
        mouth(ctx, st, 0, 60, 22, lip=hexc("#c2185b"))


class Max(Fam):
    """Son, 10. Inventor. Has never once read a safety label."""
    scale = 0.75
    skin = hexc("#f1c27d")
    top = hexc("#ff8f1f")
    forearm = hexc("#f1c27d")
    pants = hexc("#3f6fd1")
    shoe_col = hexc("#e53935")
    shoe_sole = hexc("#ffffff")
    head_top_ext = 160

    def torso_details(self, ctx, st, hip, top):
        cx, cy = 0, top + 92
        ctx.set_line_width(5)
        col(ctx, hexc("#ffffff"))
        for a in (0, 1.05, 2.1):
            ctx.save()
            ctx.translate(cx, cy)
            ctx.rotate(a)
            ctx.scale(40, 14)
            ctx.arc(0, 0, 1, 0, TAU)
            ctx.restore()
            ctx.stroke()
        ctx.arc(cx, cy, 7, 0, TAU)
        ctx.fill()

    def arm_details(self, ctx, st, side, pts):
        (x, y) = pts[1]
        ellipse(ctx, x, y - 6, 27, 16)
        fill_ink(ctx, self.top, 4)

    def draw_head(self, ctx, st):
        self.head_base(ctx, 100, 104)
        ctx.move_to(-104, 0)
        ctx.curve_to(-116, -150, 116, -150, 104, 0)
        ctx.line_to(78, -40)
        ctx.line_to(-78, -40)
        ctx.close_path()
        fill_ink(ctx, hexc("#4a2c1a"), 6)
        ctx.rectangle(-104, -94, 208, 18)
        col(ctx, hexc("#555566"))
        ctx.fill()
        for s in (-1, 1):
            ctx.arc(s * 40, -86, 27, 0, TAU)
            fill_ink(ctx, hexc("#7ee0ff"), 5)
        eyes(ctx, st, [(-38, 6), (38, 6)], r=25, skin=self.skin, seed=2.3)
        ctx.set_line_width(7)
        col(ctx, INK)
        for s in (-1, 1):
            ctx.arc(s * 38, 6, 37, 0, TAU)
            ctx.stroke()
        ctx.move_to(-2, 2)
        ctx.line_to(2, 2)
        ctx.stroke()
        col(ctx, hexc("#c98a4a"))
        for x, y in ((-72, 50), (-60, 58), (-76, 64), (72, 50), (60, 58), (76, 64)):
            ctx.arc(x, y, 4, 0, TAU)
            ctx.fill()
        nose(ctx, st["facing"], 40)
        mouth(ctx, st, 0, 72, 26)


class Pip(Fam):
    """Daughter, 7. Sings everything. Loudly."""
    scale = 0.62
    skin = hexc("#8d5a3b")
    top = hexc("#ffd23f")
    forearm = hexc("#8d5a3b")
    pants = hexc("#8d5a3b")
    shoe_col = hexc("#ff6fae")
    head_top_ext = 200

    def draw_torso(self, ctx, st, hip, top):
        path_poly(ctx, [(-self.torso_w / 2 + 6, top + 70), (self.torso_w / 2 - 6, top + 70),
                        (self.torso_w / 2 + 50, hip + 80), (-self.torso_w / 2 - 50, hip + 80)])
        fill_ink(ctx, self.top, 6)
        rrect(ctx, -self.torso_w / 2, top, self.torso_w, 130, 34)
        fill_ink(ctx, self.top, 6)
        pts = []
        for i in range(10):
            r = 30 if i % 2 == 0 else 13
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((math.cos(a) * r, top + 70 + math.sin(a) * r))
        path_poly(ctx, pts)
        fill_ink(ctx, hexc("#ff6fae"), 4)

    def arm_details(self, ctx, st, side, pts):
        (x, y) = pts[0]
        ellipse(ctx, x, y + 18, 30, 22)
        fill_ink(ctx, self.top, 4)

    def draw_head(self, ctx, st):
        bounce = 6 * math.sin(st["t"] * 6) * (st["talk"] + st["walkw"])
        for s in (-1, 1):
            ctx.arc(s * 112, -70 + bounce * s, 52, 0, TAU)
            fill_ink(ctx, hexc("#ff6fae"), 6)
        self.head_base(ctx, 104, 106)
        ctx.move_to(-104, -10)
        ctx.curve_to(-110, -138, 110, -138, 104, -10)
        ctx.curve_to(60, -70, -60, -70, -104, -10)
        fill_ink(ctx, hexc("#2b1a12"), 6)
        ctx.arc(60, -72, 15, 0, TAU)
        fill_ink(ctx, hexc("#ffd23f"), 4)
        eyes(ctx, st, [(-38, 4), (38, 4)], r=31, lashes=True, skin=self.skin, seed=0.9)
        for s in (-1, 1):
            ellipse(ctx, s * 68, 46, 16, 9)
            col(ctx, hexc("#ff8fb0", 0.7))
            ctx.fill()
        nose(ctx, st["facing"], 40, hexc("#4a2c1a"))
        mouth(ctx, st, 0, 70, 26)


class Fussbucket(Fam):
    """Next-door neighbour. Loves his lawn more than people."""
    skin = hexc("#f0d2b6")
    top = hexc("#7a8b3a")
    sleeve = hexc("#f4f4f4")
    pants = hexc("#8d8d99")
    shoe_col = hexc("#4e342e")
    torso_w = 160
    torso = 240
    head_off = 130
    head_top_ext = 140

    def torso_details(self, ctx, st, hip, top):
        path_poly(ctx, [(-34, top + 2), (0, top + 70), (34, top + 2)])
        fill_ink(ctx, hexc("#f4f4f4"), 4)
        path_poly(ctx, [(-7, top + 18), (7, top + 18), (9, top + 78), (0, top + 90), (-9, top + 78)])
        fill_ink(ctx, hexc("#c62828"), 3)
        ctx.set_line_width(3)
        col(ctx, hexc("#5f6e2a"))
        for k in range(5):
            ctx.move_to(-self.torso_w / 2 + 10, top + 110 + k * 24)
            ctx.line_to(self.torso_w / 2 - 10, top + 110 + k * 24)
        ctx.stroke()

    def draw_head(self, ctx, st):
        for s in (-1, 1):
            ellipse(ctx, s * 72, 8, 22, 32)
            fill_ink(ctx, self.skin, 5)
        ellipse(ctx, 0, 0, 74, 116)
        fill_ink(ctx, self.skin, 6)
        ctx.set_line_width(5)
        col(ctx, hexc("#9e9e9e"))
        for k in range(5):
            ctx.move_to(-66, -70 + k * 6)
            ctx.curve_to(-20, -122 + k * 4, 30, -114 + k * 5, 64, -78 + k * 6)
        ctx.stroke()
        if st.get("mood") is None:
            st = dict(st, mood="angry")
        eyes(ctx, st, [(-28, -22), (28, -22)], r=22, brow=hexc("#8e8e8e"), skin=self.skin, seed=2.9)
        ctx.set_line_width(4)
        col(ctx, INK)
        for s in (-1, 1):
            ctx.arc(s * 28, -14, 26, 0, math.pi)
            ctx.stroke()
        ellipse(ctx, st["facing"] * 8, 22, 15, 26)
        fill_ink(ctx, hexc("#e8b49a"), 4)
        ctx.rectangle(-24, 50, 48, 9)
        col(ctx, hexc("#9e9e9e"))
        ctx.fill()
        mouth(ctx, st, 0, 80, 22)


CAST = {"gary": Gary, "linda": Linda, "max": Max, "pip": Pip, "fuss": Fussbucket,
        "biscuit": wob_chars.Dog, "robo": wob_chars.RoboDog}
