"""THE WOBBLES - family sitcom characters, drawn procedurally with cairo.

Reuses the limb/walk machinery from mask-buddies (Humanoid) and adds:
sitting, lifting (for flying couches), blinking eyes, talking mouths, moods.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mask-buddies"))

import cairo  # noqa: E402

from characters import (INK, TAU, WALK_STYLES, Humanoid, col, ellipse, fill_ink, hexc,  # noqa: E402
                        path_poly, rrect, shade, stroke_limb)


# --------------------------------------------------------------------------
# Face kit
# --------------------------------------------------------------------------

def eyes(ctx, st, pts, r, skin, lashes=False, seed=0.0):
    """Big round cartoon eyes; pupils look toward facing; periodic blink."""
    f = st["facing"]
    t = st["t"]
    blink = ((t + seed) % 3.9) < 0.13 or st.get("eyes_closed")
    mood = st.get("mood")
    wide = 1.18 if mood == "shock" else 1.0
    for x, y in pts:
        ellipse(ctx, x, y, r * wide, r * 1.12 * wide)
        fill_ink(ctx, hexc("#ffffff"), 5)
        if blink:
            ellipse(ctx, x, y, r * wide, r * 1.12 * wide)
            col(ctx, skin)
            ctx.fill()
            ctx.move_to(x - r, y)
            ctx.line_to(x + r, y)
            col(ctx, INK)
            ctx.set_line_width(5)
            ctx.stroke()
        else:
            pr = r * (0.22 if mood == "shock" else 0.3)
            ctx.arc(x + f * r * 0.35, y + 2, pr, 0, TAU)
            col(ctx, INK)
            ctx.fill()
        if lashes:
            ctx.set_line_width(4)
            col(ctx, INK)
            for k in (-1, 0, 1):
                ctx.move_to(x + k * r * 0.5, y - r * 1.05)
                ctx.line_to(x + k * r * 0.75, y - r * 1.45)
            ctx.stroke()
    # brows by mood
    ctx.set_line_width(7)
    col(ctx, INK)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for x, y in pts:
        s = 1 if x > sum(p[0] for p in pts) / len(pts) else -1
        by = y - r * 1.45
        if mood == "angry":
            ctx.move_to(x - s * r * 0.8, by - 10)
            ctx.line_to(x + s * r * 0.6, by + 12)
        elif mood == "sad":
            ctx.move_to(x - s * r * 0.8, by + 10)
            ctx.line_to(x + s * r * 0.6, by - 8)
        elif mood == "shock":
            ctx.move_to(x - r * 0.7, by - 18)
            ctx.curve_to(x - r * 0.2, by - 30, x + r * 0.2, by - 30, x + r * 0.7, by - 18)
        else:
            ctx.move_to(x - r * 0.7, by)
            ctx.curve_to(x - r * 0.2, by - 10, x + r * 0.2, by - 10, x + r * 0.7, by)
        ctx.stroke()


def mouth(ctx, st, x, y, w, lip=None, teeth=True):
    t = st["t"]
    talk = st["talk"]
    mood = st.get("mood")
    op = talk * (0.35 + 0.65 * abs(math.sin(t * 14)))
    if mood == "shock":
        op = max(op, 0.9)
    if op > 0.08:
        h = 8 + 46 * op
        ctx.save()
        ellipse(ctx, x, y + h * 0.35, w * (0.8 + 0.2 * op), h)
        ctx.clip_preserve()
        col(ctx, hexc("#5a1020"))
        ctx.fill()
        ellipse(ctx, x, y + h * 1.1, w * 0.6, h * 0.55)
        col(ctx, hexc("#ff7a8a"))
        ctx.fill()
        if teeth:
            ctx.rectangle(x - w, y - h * 0.7, 2 * w, h * 0.45)
            col(ctx, hexc("#ffffff"))
            ctx.fill()
        ctx.restore()
        ellipse(ctx, x, y + h * 0.35, w * (0.8 + 0.2 * op), h)
        col(ctx, lip or INK)
        ctx.set_line_width(5)
        ctx.stroke()
    else:
        ctx.set_line_width(6)
        col(ctx, lip or INK)
        if mood in ("angry", "sad"):
            ctx.move_to(x - w, y + 10)
            ctx.curve_to(x - w * 0.3, y - 8, x + w * 0.3, y - 8, x + w, y + 10)
        else:
            ctx.move_to(x - w, y)
            ctx.curve_to(x - w * 0.3, y + 18, x + w * 0.3, y + 18, x + w, y)
        ctx.stroke()


# --------------------------------------------------------------------------
# Base for the family: sits, lifts, carries mic/plate/etc.
# --------------------------------------------------------------------------

class Toon(Humanoid):
    skin = hexc("#f4c69a")

    def sit_legs(self):
        a, b = 1.45, 0.05
        kx, ky = math.sin(a) * self.thigh, math.cos(a) * self.thigh
        fx, fy = kx + math.sin(b) * self.shin, ky + math.cos(b) * self.shin
        return (kx, ky), (fx, fy), b

    def hip_y(self, st):
        if st.get("sit"):
            _, (_, fy), _ = self.sit_legs()
            return -(fy + self.foot_h)
        return -self.hip_height(st["phase"], st["walkw"], st["style"])

    def head_top(self, st):
        return (-self.hip_y(st) + self.torso + self.head_off + self.head_top_ext) * self.scale + st.get("lift", 0)

    def draw(self, ctx, st):
        f = st["facing"]
        ph, w, style = st["phase"], st["walkw"], st["style"]
        ctx.save()
        sx = st.get("squash", 0.0)
        ctx.translate(st["x"] + math.sin(st["t"] * 70) * 7 * st["shake"], -st["jump"] - st.get("lift", 0))
        ctx.rotate(st.get("spin", 0.0))
        ctx.scale(self.scale * (1 + sx), self.scale * (1 - sx))
        hip = self.hip_y(st)
        if not st.get("sit"):
            hip += math.sin(st["t"] * 2.2) * 2.5 * (1 - w)
        if st.get("sit"):
            near_leg = far_leg = self.sit_legs()
        else:
            near_leg = self.leg(ph, w, style)
            far_leg = self.leg(ph + math.pi, w, style)
        shoulder_y = hip - self.torso + 34
        arms = st.get("arm_ang") or self.arm_targets(st)
        self.draw_arm(ctx, (f * -6, shoulder_y), arms[2], arms[3], f, far=True, st=st)
        self.draw_leg(ctx, hip, far_leg, f, far=True)
        self.draw_leg(ctx, hip, near_leg, f, far=False)
        self.draw_torso(ctx, hip, f, st)
        self.draw_arm(ctx, (f * 10, shoulder_y), arms[0], arms[1], f, far=False, st=st)
        neck_y = hip - self.torso
        talk = st["talk"]
        tilt = talk * 0.06 * math.sin(st["t"] * 13) + st.get("tilt", 0.0)
        bob = -abs(math.sin(st["t"] * 8)) * 6 * talk
        ctx.save()
        ctx.translate(f * 4, neck_y - self.head_off + bob)
        ctx.rotate(tilt)
        self.draw_head(ctx, st)
        ctx.restore()
        ctx.restore()

    def held_item(self, ctx, p, ang, f, st):
        item = st.get("item")
        if item == "mic":
            ctx.save()
            ctx.translate(*p)
            ctx.rotate(-f * 0.3)
            stroke_limb(ctx, [(0, 10), (0, -40)], 12, hexc("#333344"), 4)
            ctx.arc(0, -55, 22, 0, TAU)
            fill_ink(ctx, hexc("#c0c6d6"), 5)
            ctx.restore()
        elif item == "plate":
            ctx.save()
            ctx.translate(p[0] + f * 20, p[1] - 10)
            ellipse(ctx, 0, 0, 80, 18)
            fill_ink(ctx, hexc("#ffffff"), 5)
            for k in (-30, 0, 30):
                ellipse(ctx, k, -14, 26, 12)
                fill_ink(ctx, hexc("#e9b44c"), 3)
            ctx.restore()
        elif item == "remote":
            ctx.save()
            ctx.translate(*p)
            rrect(ctx, -12, -50, 24, 60, 6)
            fill_ink(ctx, hexc("#333344"), 4)
            ctx.arc(0, -36, 7, 0, TAU)
            col(ctx, hexc("#ff3b3b"))
            ctx.fill()
            ctx.restore()
        elif item in ("gnome", "card10", "wrench", "sandwich"):
            ctx.save()
            ctx.translate(*p)
            draw_item(ctx, item)
            ctx.restore()
        else:
            super().held_item(ctx, p, ang, f, st)


# --------------------------------------------------------------------------
# The family
# --------------------------------------------------------------------------

class Gary(Toon):
    """Dad. Pickle-factory worker, self-declared grill master."""
    scale = 1.05
    skin = hexc("#f4c69a")
    body = hexc("#79aee6")
    shoe = hexc("#2b2b2b")
    hand = hexc("#f4c69a")
    torso_w = 190
    head_off = 112
    head_top_ext = 150

    def leg_col(self):
        return hexc("#6d4c41")

    def torso_details(self, ctx, hip, top, f, st):
        ellipse(ctx, f * 22, hip - 70, 100, 92)
        fill_ink(ctx, self.body, 6)
        # polo collar + pickle badge
        path_poly(ctx, [(-40, top + 2), (0, top + 34), (40, top + 2)], close=False)
        ctx.set_line_width(6)
        col(ctx, hexc("#ffffff"))
        ctx.stroke()
        ellipse(ctx, -f * 45, top + 70, 16, 9)
        fill_ink(ctx, hexc("#6abf4b"), 3)
        rrect(ctx, -self.torso_w / 2 + 6, hip - 14, self.torso_w - 12, 16, 6)
        fill_ink(ctx, hexc("#3e2723"), 3)

    def draw_head(self, ctx, st):
        for s in (-1, 1):
            ellipse(ctx, s * 92, 0, 18, 26)
            fill_ink(ctx, self.skin, 5)
        ellipse(ctx, 0, 0, 92, 108)
        fill_ink(ctx, self.skin, 7)
        # ginger beard
        ctx.move_to(-90, 6)
        ctx.curve_to(-92, 90, -40, 122, 0, 124)
        ctx.curve_to(40, 122, 92, 90, 90, 6)
        ctx.curve_to(60, 40, 30, 46, 0, 44)
        ctx.curve_to(-30, 46, -60, 40, -90, 6)
        fill_ink(ctx, hexc("#c4622d"), 6)
        mouth(ctx, st, st["facing"] * 6, 68, 30)
        eyes(ctx, st, [(-32, -18), (32, -18)], 26, self.skin, seed=0.4)
        # nose
        ellipse(ctx, st["facing"] * 10, 22, 26, 22)
        fill_ink(ctx, hexc("#ec9a7e"), 5)
        # cap
        ctx.save()
        ctx.move_to(-96, -50)
        ctx.curve_to(-96, -150, 96, -150, 96, -50)
        ctx.close_path()
        fill_ink(ctx, hexc("#3d8b3d"), 6)
        f = st["facing"]
        ellipse(ctx, f * 70, -52, 80, 16)
        fill_ink(ctx, hexc("#2e6e2e"), 5)
        ellipse(ctx, 0, -100, 26, 15)
        fill_ink(ctx, hexc("#9be15d"), 4)
        ctx.restore()


class Linda(Toon):
    """Mom. The only sane person in the house."""
    scale = 1.0
    skin = hexc("#c98a5e")
    body = hexc("#8e44ad")
    shoe = hexc("#d6334a")
    hand = hexc("#c98a5e")
    torso_w = 140
    head_off = 104
    head_top_ext = 190

    def leg_col(self):
        return self.skin

    def sleeve_col(self):
        return hexc("#a35fc4")

    def draw_torso(self, ctx, hip, f, st):
        top = hip - self.torso
        path_poly(ctx, [(-62, top + 70), (62, top + 70), (105, hip + 110), (-105, hip + 110)])
        fill_ink(ctx, self.body)
        rrect(ctx, -70, top, 140, 120, 46)
        fill_ink(ctx, self.body)
        for k in range(3):
            ctx.arc(0, top + 30 + k * 34, 7, 0, TAU)
            col(ctx, hexc("#ffffff"))
            ctx.fill()

    def draw_head(self, ctx, st):
        # big red curly hair cloud
        for a in range(14):
            ang = math.pi + a * math.pi / 13
            ctx.arc(math.cos(ang) * 92, -20 + math.sin(ang) * 110, 46, 0, TAU)
            fill_ink(ctx, hexc("#b8322a"), 5)
        ellipse(ctx, 0, -60, 100, 90)
        col(ctx, hexc("#b8322a"))
        ctx.fill()
        ellipse(ctx, 0, 6, 80, 98)
        fill_ink(ctx, self.skin, 7)
        # earrings
        for s in (-1, 1):
            ctx.arc(s * 80, 40, 11, 0, TAU)
            fill_ink(ctx, hexc("#f5f0e1"), 3)
        # fringe curls
        for i in range(-3, 4):
            ctx.arc(i * 22, -82, 20, 0, TAU)
            fill_ink(ctx, hexc("#b8322a"), 4)
        eyes(ctx, st, [(-28, -10), (28, -10)], 22, self.skin, lashes=True, seed=1.7)
        ctx.move_to(st["facing"] * 6, 4)
        ctx.line_to(st["facing"] * 16, 30)
        ctx.line_to(st["facing"] * 2, 32)
        ctx.set_line_width(4)
        col(ctx, INK)
        ctx.stroke()
        mouth(ctx, st, st["facing"] * 4, 58, 24, lip=hexc("#c2185b"))


class Max(Toon):
    """Son, 10. Inventor. Has never once read a safety label."""
    scale = 0.72
    skin = hexc("#f1c27d")
    body = hexc("#ff8f1f")
    shoe = hexc("#e53935")
    hand = hexc("#f1c27d")
    torso_w = 150
    head_off = 120
    head_top_ext = 160

    def leg_col(self):
        return hexc("#3f6fd1")

    def torso_details(self, ctx, hip, top, f, st):
        # atom logo
        cx, cy = 0, top + 80
        ctx.set_line_width(4)
        col(ctx, hexc("#ffffff"))
        for a in (0, 1.05, 2.1):
            ctx.save()
            ctx.translate(cx, cy)
            ctx.rotate(a)
            ctx.scale(34, 12)
            ctx.arc(0, 0, 1, 0, TAU)
            ctx.restore()
            ctx.stroke()
        ctx.arc(cx, cy, 6, 0, TAU)
        ctx.fill()

    def draw_head(self, ctx, st):
        for s in (-1, 1):
            ellipse(ctx, s * 104, 6, 18, 24)
            fill_ink(ctx, self.skin, 5)
        ellipse(ctx, 0, 0, 104, 112)
        fill_ink(ctx, self.skin, 7)
        # bowl haircut
        ctx.move_to(-108, 0)
        ctx.curve_to(-118, -150, 118, -150, 108, 0)
        ctx.line_to(80, -40)
        ctx.line_to(-80, -40)
        ctx.close_path()
        fill_ink(ctx, hexc("#4a2c1a"), 6)
        # goggles on forehead
        ctx.rectangle(-106, -92, 212, 18)
        col(ctx, hexc("#555566"))
        ctx.fill()
        for s in (-1, 1):
            ctx.arc(s * 40, -84, 26, 0, TAU)
            fill_ink(ctx, hexc("#7ee0ff"), 5)
        eyes(ctx, st, [(-38, 4), (38, 4)], 24, self.skin, seed=2.3)
        # glasses
        ctx.set_line_width(7)
        col(ctx, INK)
        for s in (-1, 1):
            ctx.arc(s * 38, 4, 36, 0, TAU)
            ctx.stroke()
        ctx.move_to(-4, 0)
        ctx.line_to(4, 0)
        ctx.stroke()
        # freckles
        col(ctx, hexc("#c98a4a"))
        for x, y in ((-70, 46), (-58, 54), (-74, 60), (70, 46), (58, 54), (74, 60)):
            ctx.arc(x, y, 4, 0, TAU)
            ctx.fill()
        mouth(ctx, st, st["facing"] * 4, 66, 26)


class Pip(Toon):
    """Daughter, 7. Sings everything. Loudly."""
    scale = 0.6
    skin = hexc("#8d5a3b")
    body = hexc("#ffd23f")
    shoe = hexc("#ff6fae")
    hand = hexc("#8d5a3b")
    torso_w = 140
    head_off = 118
    head_top_ext = 200

    def leg_col(self):
        return self.skin

    def draw_torso(self, ctx, hip, f, st):
        top = hip - self.torso
        path_poly(ctx, [(-60, top + 60), (60, top + 60), (110, hip + 70), (-110, hip + 70)])
        fill_ink(ctx, self.body)
        rrect(ctx, -68, top, 136, 110, 44)
        fill_ink(ctx, self.body)
        # star
        pts = []
        for i in range(10):
            r = 26 if i % 2 == 0 else 11
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((math.cos(a) * r, top + 60 + math.sin(a) * r))
        path_poly(ctx, pts)
        fill_ink(ctx, hexc("#ff6fae"), 3)

    def draw_head(self, ctx, st):
        bounce = 6 * math.sin(st["t"] * 6) * (st["talk"] + st["walkw"])
        for s in (-1, 1):
            ctx.arc(s * 112, -70 + bounce * s, 52, 0, TAU)
            fill_ink(ctx, hexc("#ff6fae"), 6)
        ellipse(ctx, 0, 0, 104, 110)
        fill_ink(ctx, self.skin, 7)
        ctx.move_to(-104, -10)
        ctx.curve_to(-110, -140, 110, -140, 104, -10)
        ctx.curve_to(60, -70, -60, -70, -104, -10)
        fill_ink(ctx, hexc("#2b1a12"), 6)
        # star clip
        ctx.arc(60, -70, 14, 0, TAU)
        fill_ink(ctx, hexc("#ffd23f"), 4)
        eyes(ctx, st, [(-36, 0), (36, 0)], 30, self.skin, lashes=True, seed=0.9)
        for s in (-1, 1):
            ellipse(ctx, s * 66, 42, 16, 9)
            col(ctx, hexc("#ff8fb0", 0.7))
            ctx.fill()
        mouth(ctx, st, st["facing"] * 4, 62, 26)


class Fussbucket(Toon):
    """Next-door neighbour. Loves his lawn more than people."""
    scale = 1.0
    skin = hexc("#f0d2b6")
    body = hexc("#7a8b3a")
    shoe = hexc("#4e342e")
    hand = hexc("#f0d2b6")
    torso_w = 120
    torso = 200
    head_off = 120
    head_top_ext = 140

    def leg_col(self):
        return hexc("#8d8d99")

    def sleeve_col(self):
        return hexc("#f4f4f4")

    def torso_details(self, ctx, hip, top, f, st):
        path_poly(ctx, [(-30, top + 4), (0, top + 60), (30, top + 4)])
        fill_ink(ctx, hexc("#f4f4f4"), 4)
        path_poly(ctx, [(-6, top + 20), (6, top + 20), (8, top + 70), (0, top + 80), (-8, top + 70)])
        fill_ink(ctx, hexc("#c62828"), 3)

    def draw_head(self, ctx, st):
        for s in (-1, 1):
            ellipse(ctx, s * 72, 4, 22, 32)
            fill_ink(ctx, self.skin, 5)
        ellipse(ctx, 0, 0, 72, 116)
        fill_ink(ctx, self.skin, 7)
        # comb-over
        ctx.set_line_width(5)
        col(ctx, hexc("#9e9e9e"))
        for k in range(5):
            ctx.move_to(-64, -70 + k * 6)
            ctx.curve_to(-20, -120 + k * 4, 30, -112 + k * 5, 62, -78 + k * 6)
        ctx.stroke()
        if st.get("mood") is None:
            st = dict(st, mood="angry")
        eyes(ctx, st, [(-26, -24), (26, -24)], 18, self.skin, seed=2.9)
        # half-moon glasses
        ctx.set_line_width(4)
        col(ctx, INK)
        for s in (-1, 1):
            ctx.arc(s * 26, -16, 22, 0, math.pi)
            ctx.stroke()
        ellipse(ctx, st["facing"] * 8, 18, 14, 26)
        fill_ink(ctx, hexc("#e8b49a"), 4)
        ctx.rectangle(-22, 46, 44, 9)
        col(ctx, hexc("#9e9e9e"))
        ctx.fill()
        mouth(ctx, st, 0, 74, 22)


class Dog:
    """Biscuit, a very round beagle."""
    scale = 1.0
    default_style = "normal"
    fur = hexc("#c98f4a")
    fur_dark = hexc("#b07a3c")
    belly = hexc("#f2e1c4")
    ear = hexc("#7a4a24")
    collar = hexc("#ffd23f")

    def head_top(self, st):
        return 230 + st.get("lift", 0)

    def arm_targets(self, st):
        return (0, 0, 0, 0)

    def draw(self, ctx, st):
        t, f, ph, w = st["t"], st["facing"], st["phase"], st["walkw"]
        howl = st.get("howl", 0)
        ctx.save()
        ctx.translate(st["x"] + math.sin(t * 70) * 7 * st["shake"], -st["jump"] - st.get("lift", 0))
        ctx.scale(f, 1)
        for i, (lx, off) in enumerate(((-70, 0), (60, math.pi), (-50, math.pi), (80, 0))):
            a = 0.5 * w * math.sin(ph * 1.6 + off)
            stroke_limb(ctx, [(lx, -70), (lx + math.sin(a) * 60, -10)], 26,
                        self.fur_dark if i < 2 else self.fur, 5)
        wag = math.sin(t * 16) * 0.5
        ctx.save()
        ctx.translate(-110, -120)
        ctx.rotate(-0.8 + wag)
        self.draw_tail(ctx)
        ctx.restore()
        ellipse(ctx, 0, -110, 125, 70)
        fill_ink(ctx, self.fur, 6)
        ellipse(ctx, -20, -130, 60, 34)
        col(ctx, self.belly)
        ctx.fill()
        self.body_details(ctx, st)
        ctx.save()
        ctx.translate(120, -170 - 4 * abs(math.sin(t * 8)) * st["talk"] - 30 * howl)
        ctx.rotate(-0.7 * howl)
        ellipse(ctx, 0, 0, 62, 56)
        fill_ink(ctx, self.fur, 6)
        ellipse(ctx, 40, 22, 40, 28)
        fill_ink(ctx, self.belly, 5)
        ellipse(ctx, 74, 12, 14, 11)
        col(ctx, INK)
        ctx.fill()
        ctx.save()
        ctx.rotate(0.2 + 0.15 * math.sin(t * 5))
        ellipse(ctx, -40, 20, 22, 50)
        fill_ink(ctx, self.ear, 5)
        ctx.restore()
        self.draw_eye(ctx, st)
        op = max(st["talk"], howl)
        if op > 0.1:
            ellipse(ctx, 52, 48, 18, 16 * op)
            col(ctx, hexc("#5a1020"))
            ctx.fill()
        carry = st.get("carry")
        if carry:
            ctx.save()
            ctx.translate(70, 58)
            ctx.scale(f, 1)  # keep the carried thing upright
            draw_item(ctx, carry)
            ctx.restore()
        self.head_details(ctx, st)
        ctx.restore()
        ctx.arc(80, -150, 10, 0, TAU)
        fill_ink(ctx, self.collar, 3)
        ctx.restore()

    def draw_tail(self, ctx):
        stroke_limb(ctx, [(0, 0), (0, -60)], 16, self.fur, 5)

    def draw_eye(self, ctx, st):
        ctx.arc(14, -16, 14, 0, TAU)
        fill_ink(ctx, hexc("#ffffff"), 4)
        ctx.arc(18, -14, 6, 0, TAU)
        col(ctx, INK)
        ctx.fill()

    def body_details(self, ctx, st):
        pass

    def head_details(self, ctx, st):
        pass


class RoboDog(Dog):
    """Robo-Biscuit: Max's chore robot. Fetches anything. Literally anything."""
    fur = hexc("#b0bec5")
    fur_dark = hexc("#90a4ae")
    belly = hexc("#eceff1")
    ear = hexc("#607d8b")
    collar = hexc("#ff1744")

    def draw_tail(self, ctx):
        stroke_limb(ctx, [(0, 0), (0, -50)], 10, hexc("#78909c"), 4)
        ctx.arc(0, -60, 12, 0, TAU)
        fill_ink(ctx, hexc("#ff1744"), 3)

    def draw_eye(self, ctx, st):
        on = 0.6 + 0.4 * math.sin(st["t"] * 9)
        g = cairo.RadialGradient(16, -16, 2, 16, -16, 34)
        g.add_color_stop_rgba(0, 1, 0.1, 0.2, 0.7 * on)
        g.add_color_stop_rgba(1, 1, 0.1, 0.2, 0)
        ctx.set_source(g)
        ctx.arc(16, -16, 34, 0, TAU)
        ctx.fill()
        rrect(ctx, 0, -26, 34, 20, 6)
        fill_ink(ctx, hexc("#ff5252"), 4)

    def body_details(self, ctx, st):
        for x in (-80, -30, 20, 70):
            ctx.arc(x, -150, 6, 0, TAU)
            fill_ink(ctx, hexc("#78909c"), 2)
        rrect(ctx, -60, -110, 80, 40, 8)
        fill_ink(ctx, hexc("#37474f"), 3)
        for k in range(3):
            ctx.arc(-44 + k * 24, -90, 6, 0, TAU)
            col(ctx, hexc(("#4caf50", "#ffeb3b", "#ff1744")[k]) if int(st["t"] * 4 + k) % 2 else hexc("#263238"))
            ctx.fill()

    def head_details(self, ctx, st):
        ctx.move_to(-10, -54)
        ctx.line_to(-20, -110)
        ctx.set_line_width(5)
        col(ctx, INK)
        ctx.stroke()
        ctx.arc(-20, -116, 10, 0, TAU)
        fill_ink(ctx, hexc("#ff1744") if int(st["t"] * 3) % 2 else hexc("#ffeb3b"), 3)


def draw_item(ctx, item):
    """Small props a character can hold or a dog can carry, drawn around (0, 0)."""
    if item == "gnome":
        rrect(ctx, -26, -40, 52, 50, 14)
        fill_ink(ctx, hexc("#1e88e5"), 4)
        ctx.arc(0, -52, 20, 0, TAU)
        fill_ink(ctx, hexc("#f4c69a"), 4)
        path_poly(ctx, [(-22, -60), (22, -60), (0, -118)])
        fill_ink(ctx, hexc("#e53935"), 4)
        path_poly(ctx, [(-18, -46), (18, -46), (0, -10)])
        fill_ink(ctx, hexc("#ffffff"), 3)
    elif item == "card10":
        rrect(ctx, -60, -120, 120, 100, 10)
        fill_ink(ctx, hexc("#ffffff"), 5)
        ctx.select_font_face("Luckiest Guy")
        ctx.set_font_size(70)
        e = ctx.text_extents("10")
        ctx.move_to(-e.width / 2 - e.x_bearing, -42)
        col(ctx, hexc("#e53935"))
        ctx.show_text("10")
        stroke_limb(ctx, [(0, -20), (0, 10)], 8, hexc("#8d5a3b"), 3)
    elif item == "sandwich":
        path_poly(ctx, [(-40, 0), (40, 0), (0, -50)])
        fill_ink(ctx, hexc("#f3d18a"), 4)
        ctx.move_to(-30, -10)
        ctx.line_to(30, -10)
        ctx.set_line_width(6)
        col(ctx, hexc("#7cb342"))
        ctx.stroke()
    elif item == "plank":
        ctx.save()
        ctx.rotate(-0.15)
        path_poly(ctx, [(-90, -14), (60, -14), (90, 0), (60, 14), (-90, 14)])
        fill_ink(ctx, hexc("#f5e6c8"), 4)
        ctx.restore()
    elif item == "wrench":
        stroke_limb(ctx, [(0, 0), (0, -80)], 12, hexc("#9e9e9e"), 4)
        ctx.arc(0, -92, 18, 0, TAU)
        fill_ink(ctx, hexc("#9e9e9e"), 4)
        ctx.rectangle(-6, -112, 12, 22)
        col(ctx, hexc("#ffffff"))
        ctx.fill()


CAST = {"gary": Gary, "linda": Linda, "max": Max, "pip": Pip, "fuss": Fussbucket, "biscuit": Dog,
        "robo": RoboDog}
