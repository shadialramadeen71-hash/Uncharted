"""Tank & Zippy — Episode 8 (season finale): The Big Game."""
import math, os, sys
from PIL import Image
import toon
from toon import (Pen, GROUND, GOLD, RED, OUT, PURPLE, S, character, coach, place, burst, ease, blink_at, end_card,
                  get_set, Timeline, sfx_crowd, sfx_whoosh, sfx_boing, sfx_pop, sfx_crash, sfx_whistle, sfx_ding)
from ep02_waffle_trouble import spicy, end_zone
import sets as st

NAME = "ep08"
MUSIC = "victory_victory_victory.ogg"
TITLE = "Episode 8: The Big Game"
LINES = {
    "N1": ("narrator", "The season finale. The Big Game."),
    "C1": ("coach", "Three seconds left. We need a miracle."),
    "Z1": ("zippy", "Coach... I have an idea."),
    "T1": ("tank", "Oh no."),
    "C2": ("coach", "Absolutely not."),
    "Z2": ("zippy", "The Flying Play!"),
    "C3": ("coach", "That play is a penalty!"),
    "R1": ("ref", "Actually, I checked the rulebook. Flying is allowed... if you say please."),
    "Z3": ("zippy", "Pleeeease?"),
    "R2": ("ref", "Fine."),
    "T2": ("tank", "HIKE!"),
    "S1": ("spicy", "Not agaaaain!"),
    "Z4": ("zippy", "We did it! Also... the trophy is stuck on my head."),
    "T3": ("tank", "Best season ever, buddy."),
    "N2": ("narrator", "And so, Tank and Zippy became champions. Best friends. Worst ideas."),
}
RED_TEAM = (200, 40, 45)


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    tl.fx(sfx_crowd(3.0, 0.2), 0)
    t = tl.say("N1", 0.4) + 0.4
    for k in ("C1", "Z1"):
        t = tl.say(k, t) + 0.25
    t = tl.say("T1", t) + 0.15
    t = tl.say("C2", t) + 0.3
    t = tl.say("Z2", t) + 0.25
    t = tl.say("C3", t) + 0.2
    T["ref_in"] = t
    t = tl.say("R1", t + 0.5) + 0.25
    t = tl.say("Z3", t) + 0.3
    t = tl.say("R2", t) + 0.4
    T["B"] = t
    tl.fx(sfx_crowd(3.0, 0.3), t)
    t = tl.say("T2", t + 0.8)
    T["lift"] = t + 0.1; T["throw"] = T["lift"] + 0.7
    tl.fx(sfx_boing(), T["lift"]); tl.fx(sfx_whoosh(1.0), T["throw"])
    T["C"] = T["throw"] + 0.35
    tl.say("S1", T["C"] + 0.9)
    tl.fx(sfx_whoosh(1.6), T["C"] + 1.0)
    T["D"] = T["C"] + 3.2
    T["land"] = T["D"] + 0.7
    tl.fx(sfx_crash(0.7), T["land"])
    tl.fx(sfx_whistle(), T["land"] + 0.4)
    tl.fx(sfx_crowd(4.0, 0.55), T["land"] + 0.5)
    T["F"] = T["land"] + 2.8
    tl.fx(sfx_ding(), T["F"])
    t = tl.say("Z4", T["F"] + 0.6) + 0.3
    t = tl.say("T3", t) + 0.4
    t = tl.say("N2", t) + 1.0
    T["E"] = t
    tl.fx(sfx_pop(), t + 0.1)
    T["end"] = t + 4.5
    return tl.result()


def snowy():
    return get_set("snow", lambda: st.stadium("snow"))


def trophy_hat(frame, x, y, sc):
    """Trophy stuck upside-down on a head; (x, y) = top of the head."""
    layer = Image.new("RGBA", (500 * S, 500 * S), (0, 0, 0, 0))
    st.trophy(Pen(layer), 250, 470, sc)
    layer = layer.rotate(180)
    frame.alpha_composite(layer, (int((x - 250) * S), int((y - 470 + 440 * sc - 30) * S)))


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    score = (26, 24, "0:00") if t > T["land"] + 0.3 else (20, 24, "0:03")
    if t < T["B"]:  # ---- sideline: the plan
        frame = st.view(snowy(), 250)
        st.scoreboard(Pen(frame), *score, y=150)
        place(frame, coach(m["coach"], blink_at(t, 0.7), (1, 0), t, arms="point" if key in ("C2", "C3") else "clipboard",
                           angry=key in ("C2", "C3")), 160, GROUND, sc=0.8)
        place(frame, character("tank", m["tank"], blink_at(t, 0), (0.8, 0), t=t, arms="hips" if key == "T1" else "down"),
              430, GROUND, sc=0.92)
        excited = key in ("Z2", "Z3")
        place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (1 if t > T["ref_in"] else -1, 0), t=t,
                               arms="flail" if excited else ("up" if key == "Z3" else "down")), 700,
              GROUND - (abs(math.sin(t * 9)) * 35 if excited else 0), sc=0.85)
        rk = ease((t - T["ref_in"]) / 0.6)
        if rk > 0:
            place(frame, coach(m["ref"], blink_at(t, 2.2), (-1, 0), t, style="ref"), 1300 - 380 * rk, GROUND, sc=0.85)
        if key == "Z1":
            Pen(frame).text(700, 860, "!", 120, GOLD, 10)
        if t < 2.8:
            a = ease(t / 0.4) * (1 - ease((t - 2.4) / 0.4))
            Pen(frame, 540, 520, 0.6 + 0.4 * a).rect(-470, -100, 470, 160, (40, 30, 70), 7, 30)
            Pen(frame, 540, 520, 0.6 + 0.4 * a).text(0, 0, "TANK & ZIPPY", 110, GOLD, 12)
            Pen(frame, 540, 630, 0.6 + 0.4 * a).text(0, 0, "Season Finale: The Big Game", 46, "white", 7)
        st.snowfall(frame, t)
        return frame
    if t < T["C"]:  # ---- line of scrimmage
        frame = st.view(snowy(), 600)
        st.scoreboard(Pen(frame), *score, y=150)
        lift = ease((t - T["lift"]) / 0.4)
        thr = (t - T["throw"]) / 0.35
        place(frame, character("opp", 0, blink_at(t, 2.7), (0, -1) if thr > 0 else (-0.8, 0), t=t, angry=True,
                               jersey=RED_TEAM, number="99", arms="hips"), 880, GROUND, sc=0.85)
        place(frame, character("tank", m["tank"], blink_at(t, 0), (0.5, -0.3 * lift), t=t,
                               arms="throw" if thr > 0 else ("up" if lift > 0.5 else "down")), 250, GROUND)
        if thr <= 0:
            place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (0.6, 0), t=t, ball=True,
                                   arms="flail" if lift > 0.5 else "down"), 560 + (250 - 560) * lift, GROUND + (590 - GROUND) * lift, sc=0.85)
        else:
            k = min(thr, 1.5)
            place(frame, character("zippy", m["zippy"], False, (1, -1), t=t, ball=True, arms="flail"),
                  250 + 1100 * k, 590 - 900 * k + 500 * k * k, sc=0.85, angle=-720 * k, pivot_up=300)
        if key == "T2":
            burst(frame, 540, 1150, "HIKE!", 0.9, RED)
        st.snowfall(frame, t)
        return frame
    if t < T["D"]:  # ---- flight over the snow
        u = t - T["C"]
        span = T["D"] - T["C"]
        frame = st.view(snowy(), 600 + u * 1500)
        sx = 1400 - (u - 0.6) * 900
        if -300 < sx < 1500:
            place(frame, spicy(m["spicy"], False, (1, -1), t, arms="flail"), sx, GROUND, sc=0.8)
        zy = 1300 - math.sin(min(1, u / span) * math.pi) * 350
        pen = Pen(frame)
        for i in range(6):
            yy = zy - 380 + i * 60
            pen.line([(560 - 600 - (i % 2) * 120 - 60 * math.sin(t * 30 + i), yy), (360 - (i % 2) * 120, yy)], "white", 9)
        place(frame, character("zippy", m["zippy"], False, (1, 0), t=t, ball=True, arms="flail"),
              560, zy, sc=1.15, angle=-u * 540, pivot_up=300)
        st.snowfall(frame, t)
        return frame
    if t < T["F"]:  # ---- touchdown in the snow
        u = t - T["D"]
        frame = st.view(snowy(), 300)
        pen = Pen(frame)
        end_zone(pen, 560)
        landed = t > T["land"]
        if not landed:
            k = u / 0.7
            place(frame, character("zippy", 0, False, (1, 1), t=t, ball=True, arms="flail"),
                  -100 + 820 * k, 700 + 820 * k * k - 400 * k, sc=1.0, angle=-540 * k, pivot_up=300)
        else:
            place(frame, character("zippy", 0, False, (0, 0), t=t, ball=False, arms="flail"), 720, 1600, sc=0.9, angle=180, pivot_up=300)
            pen.ell(720, 1420, 260, 110, (240, 245, 252), 7)
            pen.ell(620, 1380, 120, 70, (250, 252, 255), 0)
            pen.ell(820, 1390, 130, 70, (250, 252, 255), 0)
            toon.football(Pen(frame), 900, 1250, 34, 0.5)
            burst(frame, 540, 560, "TOUCHDOWN!", 0.8 + 0.1 * math.sin((t - T["land"]) * 16), GOLD)
            st.confetti(frame, t, T["land"], 40)
        st.scoreboard(Pen(frame), *score, y=150)
        st.snowfall(frame, t)
        return frame
    if t < T["E"]:  # ---- champions
        u = t - T["F"]
        frame = st.view(snowy(), 700)
        pen = Pen(frame)
        pen.rect(160, 1380, 920, 1480, (80, 40, 120), 7, 12)
        pen.text(540, 1430, "CHAMPIONS", 60, GOLD, 0)
        place(frame, coach(m["coach"], blink_at(t, 0.7), (1, -0.3), t, arms="point"), 110, GROUND, sc=0.75)
        place(frame, character("tank", m["tank"], blink_at(t, 0), (0.6, -0.2), t=t, arms="up"), 400, 1380, sc=0.9)
        hop = abs(math.sin(t * 6)) * 30
        place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (-0.5, -0.4), t=t, arms="up"), 720, 1380 - hop, sc=0.85)
        trophy_hat(frame, 720, 1380 - hop - 560 * 0.85, 0.7)
        place(frame, character("opp", 0, blink_at(t, 2.7), (-1, 0), t=t, jersey=RED_TEAM, number="99", arms="wave"), 990, GROUND, sc=0.7)
        st.confetti(frame, t, T["F"], 50)
        if u < 2.5:
            burst(frame, 540, 520, "CHAMPIONS!", 0.8 + 0.1 * math.sin(u * 14), GOLD)
        st.scoreboard(Pen(frame), *score, y=150)
        st.snowfall(frame, t, 40)
        return frame
    u = t - T["E"]
    frame = end_card(t, u, "Season 1 Finale", None, [
        (character("tank", 0, blink_at(t, 0), (0.4, 0), t=t, arms="wave"), 300, 1330, 0.9),
        (character("zippy", 0, blink_at(t, 1.3), (-0.4, 0), t=t, arms="up"), 770, 1330 - abs(math.sin(t * 6)) * 40, 0.85)])
    trophy_hat(frame, 770, 1330 - abs(math.sin(t * 6)) * 40 - 560 * 0.85, 0.7)
    k = ease((u - 0.5) / 0.4)
    Pen(frame, 540, 1530, 0.4 + 0.6 * k).text(0, 0, "THE END", 110, GOLD, 12)
    Pen(frame, 540, 1660, 0.4 + 0.6 * k).text(0, 0, "Thanks for watching!", 60, "white", 8)
    st.confetti(frame, t, T["E"], 30)
    return frame


if __name__ == "__main__":
    toon.main(sys.modules[__name__], sys.argv[1] if len(sys.argv) > 1 else os.path.join(toon.HERE, "ep08_the_big_game.mp4"))
