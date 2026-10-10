"""Tank & Zippy — Episode 3: The Gatorade Shower."""
import math, os, sys
import toon
from toon import (Pen, GROUND, GOLD, RED, character, coach, place, burst, ease, blink_at, end_card, get_set,
                  bg_copy, Timeline, sfx_crowd, sfx_whoosh, sfx_boing, sfx_pop, sfx_splash, sfx_whistle)
import sets as st

NAME = "ep03"
MUSIC = "goofy_attitude.mp3"
TITLE = "Episode 3: The Gatorade Shower"
LINES = {
    "N1": ("narrator", "Episode three. The Gatorade Shower."),
    "Z1": ("zippy", "Tank! We won! You know what that means?"),
    "T1": ("tank", "A nap?"),
    "Z2": ("zippy", "No! The victory shower! We dump the cooler on Coach!"),
    "T2": ("tank", "Coach Pancake hates surprises."),
    "Z3": ("zippy", "That's what makes it a surprise!"),
    "N2": ("narrator", "Final whistle. The Waffles win!"),
    "Z4": ("zippy", "Hnnngh! It's... too... heavy!"),
    "T3": ("tank", "I got it, buddy."),
    "Z5": ("zippy", "Wait! I'm still holding on!"),
    "C1": ("coach", "Great game, ref!"),
    "R1": ("ref", "Fifteen yards. For all of you."),
    "C2": ("coach", "The game is OVER!"),
    "N3": ("narrator", "Next time, on Tank and Zippy: Salad Season!"),
}


def build_timeline(dur):
    tl = Timeline(dur); T = tl.T
    t = tl.say("N1", 0.4) + 0.4
    for k in ("Z1", "T1", "Z2", "T2", "Z3"):
        t = tl.say(k, t) + 0.25
    T["B"] = t + 0.3
    tl.fx(sfx_whistle(), T["B"] + 0.1)
    tl.fx(sfx_crowd(4.0, 0.4), T["B"] + 0.3)
    t = tl.say("N2", T["B"] + 0.9) + 0.3
    t = tl.say("Z4", t) + 0.3
    t = tl.say("T3", t) + 0.1
    T["lift"] = t
    tl.fx(sfx_boing(0.5), t)
    t = tl.say("Z5", t + 0.6) + 0.2
    T["ref_in"] = t
    t = tl.say("C1", t + 0.3) + 0.2
    T["dump"] = t
    tl.fx(sfx_whoosh(0.6), t)
    tl.fx(sfx_splash(), t + 0.25)
    tl.fx(sfx_boing(0.6), t + 0.85)
    tl.fx(sfx_crowd(2.5, 0.45), t + 0.5)
    t = tl.say("R1", t + 2.0) + 0.3
    t = tl.say("C2", t) + 0.9
    T["E"] = t
    tl.fx(sfx_pop(), t + 0.1)
    T["end"] = tl.say("N3", t + 0.5) + 1.5
    return tl.result()


def render_scene(t, c):
    T, m, key = c["T"], c["m"], c["key"]
    if t < T["B"]:  # ---- locker room plan
        frame = bg_copy(get_set("locker", st.locker_room))
        k = ease((t - 0.2) / 0.6)
        place(frame, character("tank", m["tank"], blink_at(t, 0), (0.6, 0), t=t,
                               arms="hips" if key == "T2" else "down"), -200 + 500 * k, GROUND)
        excited = key in ("Z1", "Z2", "Z3")
        place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (-0.6, 0), t=t, arms="flail" if excited else "down"),
              1300 - 520 * k, GROUND - (abs(math.sin(t * 9)) * 40 if excited else 0))
        if t < 2.8:
            a = ease(t / 0.4) * (1 - ease((t - 2.4) / 0.4))
            Pen(frame, 540, 330, 0.6 + 0.4 * a).text(0, 0, "TANK & ZIPPY", 120, GOLD, 12)
            Pen(frame, 540, 450, 0.6 + 0.4 * a).text(0, 0, TITLE, 50, "white", 7)
        if key == "T1":
            pen = Pen(frame)
            for i in range(3):
                pen.text(430 + i * 50, 600 - i * 60 - (t * 40) % 30, "z", 60 + i * 20, "white", 6)
        return frame
    if t < T["E"]:  # ---- night game sideline
        frame = st.view(get_set("night", lambda: st.stadium("night")), 400)
        pen = Pen(frame)
        u_lift = ease((t - T["lift"]) / 0.5)
        d = t - T["dump"]
        ref_k = ease((t - T["ref_in"]) / 0.9)
        rx = -300 + 730 * ref_k
        cx = 190 - 80 * ref_k
        # coach + referee
        place(frame, coach(m["coach"], blink_at(t, 0.7), (1 if ref_k > 0 else -1, 0), t,
                           arms="point" if key == "C1" else "clipboard", angry=key == "C2"), cx, GROUND, sc=0.82)
        soaked = d > 0.4
        if ref_k > 0:
            place(frame, coach(m["ref"], blink_at(t, 2.2), (-1 if d < 0 else 0, 0), t, style="ref", soaked=soaked,
                               arms="flag" if key == "R1" else "down"), rx, GROUND, sc=0.95)
        # tank
        tank_arms = "up" if u_lift > 0.5 and d < 0.6 else ("hips" if d > 1.5 else "down")
        place(frame, character("tank", m["tank"], blink_at(t, 0), (-0.8 if d > -1 else 0.6, -0.5 * u_lift), t=t,
                               arms=tank_arms), 820, GROUND)
        # cooler + zippy
        head_x, head_y = 430, GROUND - 516 * 0.95
        if d < 0:
            if u_lift <= 0:
                shake = 4 * math.sin(t * 50) if key == "Z4" else 0
                st.cooler(pen, 470 + shake, GROUND, 0.95)
                place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (-1, 0), t=t, arms="flail" if key == "Z4" else "down"),
                      660 if key != "Z4" else 640, GROUND)
                if key == "Z4":
                    Pen(frame).text(470, 1120 - (t * 80) % 40, "!", 80, (120, 200, 255), 6)
            else:
                cx0, cy0 = 470 + (820 - 470) * u_lift, GROUND + (800 - GROUND) * u_lift
                st.cooler(pen, cx0, cy0, 0.95)
                place(frame, character("zippy", m["zippy"], False, (-0.5, 1), t=t, arms="up"),
                      cx0 + 170, cy0 - 176 + 425, sc=0.8, angle=8 * math.sin(t * 6))
        else:
            k = ease(min(1, d / 0.8))
            tilt = -2.0 * ease(min(1, d / 0.3)) - (math.pi - 2.0) * k
            bx = 820 + (head_x - 820) * k
            by = 800 + (head_y - 800) * k - 260 * math.sin(k * math.pi)
            if 0.2 < d < 0.7:
                pen.poly([(bx - 200, by + 60), (bx - 120, by + 120), (head_x + 40, head_y - 40), (head_x - 60, head_y - 40)],
                         (255, 150, 40), 5)
            if 0.25 < d < 1.3:
                st.splash(pen, head_x, head_y - 60, (d - 0.25) / 1.05)
            st.cooler(Pen(frame), bx, by, 0.95, tilt)
            zk = ease(min(1, d / 1.0))
            zx = 990 + (head_x - 990) * zk
            zy = (800 - 176 + 425) + (head_y - (800 - 176 + 425)) * zk - 500 * math.sin(zk * math.pi)
            place(frame, character("zippy", m["zippy"], blink_at(t, 1.3), (0.2, 0.3), t=t, arms="flail" if d < 1.0 else "down",
                                   messy=False, dizzy=1.0 < d < 3.0), zx, zy, sc=0.8, angle=-360 * zk if d < 1.0 else 0, pivot_up=250)
            if 0.3 < d < 1.3:
                burst(frame, 540, 380, "SPLOOSH!", 0.7 + 0.2 * (d - 0.3), (255, 150, 40))
        if T["B"] < t < T["B"] + 2.4:
            st.confetti(frame, t, T["B"], 30)
            Pen(frame).rect(220, 330, 860, 470, (25, 25, 32), 8, 18)
            Pen(frame).text(540, 400, "WAFFLES WIN!", 70, GOLD, 0)
        return frame
    u = t - T["E"]
    return end_card(t, u, TITLE.replace("Episode 3: ", "Episode 3: "), "Salad Season", [
        (character("tank", 0, blink_at(t, 0), (0.4, 0), t=t, arms="wave"), 300, 1380, 0.9),
        (character("zippy", 0, blink_at(t, 1.3), (-0.4, 0), t=t, arms="wave"), 770, 1380 - abs(math.sin(t * 6)) * 40, 0.9)])


if __name__ == "__main__":
    toon.main(sys.modules[__name__], sys.argv[1] if len(sys.argv) > 1 else os.path.join(toon.HERE, "ep03_gatorade_shower.mp4"))
