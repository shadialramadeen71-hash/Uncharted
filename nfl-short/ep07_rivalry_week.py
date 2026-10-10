"""Tank & Zippy — Episode 7: Rivalry Week."""
import math, os, sys
import toon
from toon import (Pen, GROUND, GOLD, RED, OUT, PURPLE, character, place, burst, ease, blink_at, end_card, get_set,
                  bg_copy, star, Timeline, sfx_whoosh, sfx_boing, sfx_pop, sfx_wind, sfx_ding, sfx_crowd)
from ep02_waffle_trouble import spicy
import sets as st

NAME = "ep07"
MUSIC = "spaghetti_western.ogg"
TITLE = "Episode 7: Rivalry Week"
LINES = {
    "N1": ("narrator", "Episode seven. Rivalry Week."),
    "Z1": ("zippy", "Are we there yet?"),
    "T1": ("tank", "We left five minutes ago."),
    "Z2": ("zippy", "Are we there yet NOW?"),
    "T2": ("tank", "No."),
    "N2": ("narrator", "Destination: Hot Sauce Stadium. Home of Mister Spicy... and Brick."),
    "S1": ("spicy", "Well, well, well. If it isn't the waffle."),
    "Z3": ("zippy", "FORMER waffle!"),
    "S2": ("spicy", "Brick here has been waiting for you."),
    "N3": ("narrator", "Brick doesn't talk. Brick only stares."),
    "T3": ("tank", "If you want my buddy, you go through me."),
    "N4": ("narrator", "Brick... just needed a hug."),
    "S3": ("spicy", "Brick! What are you doing?!"),
    "Z4": ("zippy", "Group hug!"),
    "S4": ("spicy", "Fine. But I'm still spicy."),
    "N5": ("narrator", "Next time, on Tank and Zippy: the season finale. The Big Game!"),
}
RED_TEAM = (200, 40, 45)


def heart(pen, x, y, r, c=(240, 60, 90)):
    pen.ell(x - r * 0.5, y, r * 0.6, r * 0.6, c, 0)
    pen.ell(x + r * 0.5, y, r * 0.6, r * 0.6, c, 0)
    pen.poly([(x - r * 1.08, y + r * 0.15), (x + r * 1.08, y + r * 0.15), (x, y + r * 1.25)], c, 0)


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = tl.say("N1", 0.4) + 0.4
    for k in ("Z1", "T1", "Z2"):
        t = tl.say(k, t) + 0.25
    t = tl.say("T2", t + 0.3) + 0.5
    T["sign"] = t
    t = tl.say("N2", t) + 0.4
    T["B"] = t
    tl.fx(sfx_crowd(2.0, 0.2), t)
    t = tl.say("S1", t + 0.4) + 0.25
    t = tl.say("Z3", t) + 0.25
    t = tl.say("S2", t) + 0.25
    T["brick"] = t
    t = tl.say("N3", t + 0.2) + 0.3
    T["step"] = t
    tl.fx(sfx_whoosh(0.4), t)
    t = tl.say("T3", t + 0.4) + 0.3
    T["stare"] = t
    tl.fx(sfx_wind(3.4), t)
    T["hug"] = t + 3.4
    tl.fx(sfx_pop(), T["hug"]); tl.fx(sfx_ding(), T["hug"] + 0.1)
    t = tl.say("N4", T["hug"] + 0.5) + 0.3
    t = tl.say("S3", t) + 0.25
    T["group"] = t
    tl.fx(sfx_boing(), t)
    t = tl.say("Z4", t + 0.1) + 0.3
    t = tl.say("S4", t) + 1.0
    T["E"] = t
    tl.fx(sfx_pop(), t + 0.1)
    T["end"] = tl.say("N5", t + 0.5) + 1.5
    return tl.result()


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t < T["B"]:  # ---- the bus
        frame = st.view(get_set("desert", st.desert_road), t * 500)
        pen = Pen(frame)
        bob = 6 * math.sin(t * 9)
        st.bus(pen, 130, 1500 + bob, t)
        speaker = c["who"]
        if speaker in ("tank", "zippy"):
            wx = 130 + 60 + (1 if speaker == "tank" else 3) * 140 + 55
            pen.rect(wx - 150, 860 + bob, wx + 150, 960 + bob, "white", 6, 30)
            pen.poly([(wx - 20, 958 + bob), (wx + 20, 958 + bob), (wx, 1010 + bob)], "white", 0)
            pen.text(wx, 910 + bob, "...?" if speaker == "zippy" else "...", 50, OUT, 0)
        sx = 1300 - (t - T["sign"]) * 500
        if -300 < sx < 1400:
            pen.rect(sx - 10, 900, sx + 10, 1200, (110, 110, 120), 5)
            pen.rect(sx - 230, 760, sx + 230, 960, (40, 130, 70), 8, 14)
            pen.text(sx, 820, "HOT SAUCE", 52, "white", 0)
            pen.text(sx, 900, "STADIUM  >", 52, "white", 0)
        if t < 2.8:
            a = ease(t / 0.4) * (1 - ease((t - 2.4) / 0.4))
            Pen(frame, 540, 230, 0.6 + 0.4 * a).rect(-470, -100, 470, 160, (40, 30, 70), 7, 30)
            Pen(frame, 540, 230, 0.6 + 0.4 * a).text(0, 0, "TANK & ZIPPY", 110, GOLD, 12)
            Pen(frame, 540, 340, 0.6 + 0.4 * a).text(0, 0, TITLE, 50, "white", 7)
        return frame
    if t < T["E"]:  # ---- hot sauce stadium
        frame = st.view(get_set("hotsauce", lambda: st.stadium("hotsauce")), 300)
        pen = Pen(frame)
        if T["stare"] <= t < T["hug"]:  # close-up stare down
            u = t - T["stare"]
            zoom = 2.1 + 0.15 * u
            place(frame, character("tank", 0, False, (1, 0), t=t, angry=True), 250, 1050 + 523 * zoom, sc=zoom)
            tremble = 4 * math.sin(t * 40) if u > 2.2 else 0
            place(frame, character("opp", 0, False, (-1, 0), t=t, angry=True, jersey=RED_TEAM, number="99"),
                  840 + tremble, 1050 + 523 * zoom, sc=zoom)
            pen = Pen(frame)
            pen.rect(530, 0, 550, 1920, OUT, 0)
            if u > 1.0:
                pen.ell(330, 820 + (u - 1) * 120, 20, 30, (120, 200, 255), 4)
            st.tumbleweed(Pen(frame), -150 + u * 420, 1500, t, 80)
            burst(frame, 540, 260, "STARE DOWN", 0.7, (255, 120, 50))
            return frame
        hug = t > T["hug"]
        group = t > T["group"]
        step = ease((t - T["step"]) / 0.4)
        if not hug:
            place(frame, spicy(m["spicy"], blink_at(t, 2.1), (-1, 0), t, arms="up" if key == "S1" else "hips"), 660, GROUND, sc=0.75)
            bk = ease((t - T["brick"]) / 0.6)
            place(frame, character("opp", 0, blink_at(t, 2.7) and t < T["brick"], (-1, 0), t=t, angry=True, jersey=RED_TEAM,
                                   number="99", arms="hips"), 1350 - 440 * bk, GROUND, sc=0.8)
            place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (1, 0), t=t, arms="flail" if key == "Z3" else "down"),
                  440 - 290 * step, GROUND, sc=0.85)
            place(frame, character("tank", m["tank"], blink_at(t, 0), (1, 0), t=t, arms="hips" if step > 0.5 else "down",
                                   angry=step > 0.5), 200 + 200 * step, GROUND, sc=0.92)
        else:
            h = t - T["hug"]
            place(frame, spicy(m["spicy"], blink_at(t, 2.1), (-1, 0), t, arms="flail" if key == "S3" else ("up" if group else "hips")),
                  880 - (130 if group else 0) * ease((t - T["group"]) / 0.4), GROUND, sc=0.8)
            place(frame, character("tank", m["tank"], True, (0.5, 0), t=t, arms="up"), 390, GROUND)
            place(frame, character("opp", 0, True, (-1, 0), t=t, jersey=RED_TEAM, number="99", arms="hips"), 650, GROUND, sc=0.92, angle=8)
            pen = Pen(frame)
            for y in (1130, 1210):
                pen.line([(560, y), (420, y + 25), (250, y + 5)], OUT, 50)
                pen.line([(560, y), (420, y + 25), (250, y + 5)], RED_TEAM, 36)
                pen.ell(250, y + 5, 30, 30, (235, 185, 150))
            if group:
                g = ease((t - T["group"]) / 0.5)
                place(frame, character("zippy", m["zippy"], False, (0, 0), t=t, arms="up"), 160 + 360 * g,
                      GROUND - 520 * math.sin(g * math.pi * 0.5) - 120 * g, sc=0.8)
            else:
                place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (1, -0.3), t=t, arms="down"), 160, GROUND, sc=0.9)
            for i in range(6):
                u = (h * 0.5 + i / 6) % 1
                heart(Pen(frame), 300 + i * 100 + 30 * math.sin(h * 3 + i), 900 - u * 500, 28 * (1 - u * 0.4))
        if T["brick"] < t < T["step"]:
            Pen(frame).text(920, 760 + 10 * math.sin(t * 3), "...", 90, "white", 8)
        return frame
    u = t - T["E"]
    return end_card(t, u, TITLE, "The Big Game", [
        (character("tank", 0, blink_at(t, 0), (0.4, 0), t=t, arms="wave"), 260, 1380, 0.85),
        (character("zippy", 0, blink_at(t, 1.3), (-0.4, 0), t=t, arms="wave"), 560, 1380 - abs(math.sin(t * 6)) * 40, 0.8),
        (character("opp", 0, blink_at(t, 2.7), (-0.4, 0), t=t, jersey=RED_TEAM, number="99", arms="wave"), 860, 1380, 0.75)],
        bg=(150, 40, 35), rays=(180, 60, 50))


if __name__ == "__main__":
    toon.main(sys.modules[__name__], sys.argv[1] if len(sys.argv) > 1 else os.path.join(toon.HERE, "ep07_rivalry_week.mp4"))
