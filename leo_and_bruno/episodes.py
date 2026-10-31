"""The episodes of "Leo & Bruno". Each episode is a list of beats (a spoken line or an action)
plus a draw function that animates the scene at time T using the timeline `tl`."""
import math

from draw import (GY, bee, bg_beach, bg_forest, bg_night, bg_river, bg_snow, chest, circle, clamp,
                  cookie, draw_bruno, draw_leo, drops, ellipse, paint, text, ease_in, ease_out, ease_out_back, fish, honey_tree,
                  lerp, line, moon, night_ground, pop_text, rocket, smoke, smooth, snowball, snowfall,
                  snowman_base, sparkle, treasure_map)

BS = 0.85  # Bruno's scale


def leo(ctx, T, tl, x, **kw):
    kw.setdefault("mouth", tl.mouth("leo", T))
    kw.setdefault("blink", tl.blink("leo", T))
    return draw_leo(ctx, x, kw.pop("y", GY), **kw)


def bruno(ctx, T, tl, x, **kw):
    kw.setdefault("mouth", tl.mouth("bruno", T))
    kw.setdefault("blink", tl.blink("bruno", T))
    kw.setdefault("s", BS)
    return draw_bruno(ctx, x, kw.pop("y", GY), **kw)


def shake(ctx, amount, T):
    if amount > 0:
        ctx.translate(math.sin(T * 63) * amount, math.cos(T * 71) * amount)


# =================================================================== 1. The Honey Hunt
def draw_ep1(ctx, T, tl):
    p_reach, p_bees, p_run = tl.p(2, T), tl.p(3, T), tl.p(4, T)
    ctx.save()
    shake(ctx, 7 * tl.on(3, T), T)
    bg_forest(ctx, T)
    hive = (790, 950)
    jiggle = math.sin(T * 45) * 10 if p_reach > 0.45 else 0
    honey_tree(ctx, 960, GY, hive, jiggle)

    # Bruno walks to the tree, reaches up, then everybody runs away to the left
    bx = lerp(600, 690, smooth(tl.p(1, T)))
    walking = 0 < tl.p(1, T) < 1
    leo_x = 250
    face_b = 1
    if p_run > 0:
        bx -= ease_in(p_run) * 1100
        leo_x -= ease_in(clamp(p_run * 1.2)) * 900
        face_b = -1
    reach = smooth(p_reach * 2) if p_bees == 0 else 1 - smooth(p_bees * 3)
    b_expr = "scared" if p_bees > 0 else ("surprised" if p_reach > 0.6 else "happy")
    b_arms = (18 + 150 * reach * 0.2, 18 + 150 * reach) if p_bees == 0 else (150, 150)
    if p_run > 0:
        b_arms = (160, 160)
    l_expr = "scared" if p_run > 0 else ("surprised" if p_bees > 0 else "happy")
    l_arms = (14, 105) if tl.on(0, T) else ((150, 150) if p_run > 0 or p_bees > 0 else (14, 14))
    run_phase = T * 22 if p_run > 0 else None

    leo(ctx, T, tl, leo_x, face=-1 if p_run > 0 else 1, expr=l_expr, arms=l_arms, walk=run_phase,
        look=(0.7, -0.3) if tl.on(0, T) else (0.6, 0))
    bruno(ctx, T, tl, bx, face=face_b, expr=b_expr, arms=b_arms,
          walk=(T * 12 if walking else run_phase), look=(0.5, -0.8) if p_reach > 0 and p_bees == 0 else (0.6, 0),
          hop=abs(math.sin(T * 18)) * 25 if p_bees > 0 and p_run == 0 else 0)

    # bees pour out of the hive and chase Bruno
    if p_reach > 0.55:
        n = 7
        for i in range(n):
            out = clamp((T - tl.t0(2) - 0.75 - i * 0.06) * 2.5)
            if out <= 0:
                continue
            ang = T * (3 + i * 0.4) + i * 2 * math.pi / n
            tx, ty = bx + math.cos(ang) * 170, GY - 700 + math.sin(ang * 1.3) * 120
            if p_run > 0:
                tx += 120 + i * 25
            x = lerp(hive[0], tx, out)
            y = lerp(hive[1], ty, out)
            bee(ctx, x, y, T + i, 1.1, face=-1 if p_run > 0 else (1 if math.sin(ang) < 0 else -1))
    pop_text(ctx, "BZZZ!", 760, 760, T - tl.t0(2) - 0.8, 120)
    ctx.restore()


EP1 = dict(
    num=1, title="The Honey Hunt", seed=3,
    beats=[
        dict(say=("leo", "Bruno, look! A honey tree!")),
        dict(say=("bruno", "Honey? Yummy! Mine!")),
        dict(act="reach", dur=1.3, sfx=[("boing", 0.2), ("buzz", 0.75)]),
        dict(say=("bruno", "Uh-oh... Bees!"), sfx=[("buzz", 0.0)]),
        dict(say=("leo", "Run, Bruno! Run!"), min=1.9, sfx=[("whoosh", 0.3), ("buzz", 0.3)]),
    ],
    draw=draw_ep1,
)


# =================================================================== 2. The Treasure Map
def draw_ep2(ctx, T, tl):
    p_dig, p_open = tl.p(2, T), tl.p(3, T)
    bg_beach(ctx, T)
    spot = (820, 1640)
    # the X in the sand / the hole
    hole = smooth(p_dig * 1.6)
    if hole > 0:
        ellipse(ctx, spot[0], spot[1], 70 + 70 * hole, 16 + 22 * hole)
        paint(ctx, "#B8874A", 5)
    else:
        line(ctx, [(spot[0] - 40, spot[1] - 22), (spot[0] + 40, spot[1] + 22)], 12, "#D84B3B")
        line(ctx, [(spot[0] + 40, spot[1] - 22), (spot[0] - 40, spot[1] + 22)], 12, "#D84B3B")

    bx = lerp(560, 640, smooth(tl.p(1, T)))
    walking = 0 < tl.p(1, T) < 1
    digging = 0 < p_dig < 0.85
    if digging:
        b_arms = (40 + 50 * abs(math.sin(T * 14)), 40 + 50 * abs(math.cos(T * 14)))
    elif tl.on(5, T):
        b_arms = (20, 135)
    elif p_open > 0:
        b_arms = (150, 150)
    else:
        b_arms = (18, 18)
    b_expr = "laugh" if tl.on(5, T) and tl.mouth("bruno", T) < 0.05 else ("surprised" if p_open > 0 and not tl.on(5, T) else "happy")
    face_b = -1 if tl.on(0, T) else 1
    hands = bruno(ctx, T, tl, bx, face=face_b, arms=b_arms, expr=b_expr, walk=T * 12 if walking else None,
                  rot=0.12 if digging else 0, look=(0.7, 0.6) if digging else (0.6, 0))

    l_jump = abs(math.sin((T - tl.t0(4)) * 9)) * 60 if tl.on(4, T) else 0
    l_expr = "surprised" if tl.on(4, T) else ("laugh" if tl.on(5, T) else "happy")
    l_arms = (14, 120) if tl.on(0, T) else ((150, 150) if tl.on(4, T) else (14, 14))
    lh = leo(ctx, T, tl, 230, hop=l_jump, expr=l_expr, arms=l_arms)
    if tl.on(0, T) or tl.on(1, T):  # Leo shows the map
        k = ease_out_back(tl.p(0, T) * 3)
        treasure_map(ctx, lh["front"][0] + 50, lh["front"][1] - 70, 1.1 * k, -0.1)

    # chest rises out of the hole, then opens
    if p_dig > 0.55:
        rise = smooth((p_dig - 0.55) / 0.45)
        chest(ctx, spot[0], spot[1] + 10 - rise * 30, 0.95, lid=smooth(p_open * 1.5) if p_open > 0 else 0,
              glow=smooth(p_open * 2) if p_open > 0 else 0, t=T)
    if digging:  # sand flying
        for i in range(8):
            age = ((T * 3 + i * 0.37) % 1.0)
            sx = spot[0] - 60 - age * 380 - i * 8
            sy = spot[1] - 40 - math.sin(age * math.pi) * 300
            circle(ctx, sx, sy, 10 + (i % 3) * 4)
            paint(ctx, "#E9C075", 3)
    if p_open > 0:
        for i in range(6):
            a = T * 2 + i
            sparkle(ctx, spot[0] + math.cos(a) * 170, spot[1] - 200 + math.sin(a * 1.3) * 90,
                    18 + 8 * math.sin(T * 6 + i))
    if tl.on(5, T):  # Bruno munches a cookie
        cookie(ctx, hands["front"][0], hands["front"][1] - 20, 34)
    pop_text(ctx, "DIG! DIG!", 700, 1000, T - tl.t0(2) - 0.1, 100, life=1.4)


EP2 = dict(
    num=2, title="The Treasure Map", seed=7,
    beats=[
        dict(say=("leo", "Bruno! I found a treasure map!"), sfx=[("pop", 0.1)]),
        dict(say=("bruno", "X marks the spot! Let's dig!")),
        dict(act="dig", dur=2.0, sfx=[("dig", 0.0), ("boing", 1.5)]),
        dict(act="open", dur=0.7, sfx=[("sparkle", 0.0)]),
        dict(say=("leo", "Cookies?!")),
        dict(say=("bruno", "Best treasure ever!"), sfx=[("tada", 0.0)]),
    ],
    draw=draw_ep2,
)


# =================================================================== 3. The Snow Bear
def draw_ep3(ctx, T, tl):
    p_lift = tl.p(2, T)
    ctx.save()
    hit = p_lift >= 0.78
    shake(ctx, 10 * clamp(1 - (T - tl.t0(2) - tl.dur(2) * 0.78) * 2.5) if hit else 0, T)
    bg_snow(ctx, T)
    snowman_base(ctx, 470, GY + 10)

    bx = 790
    snow = 1.0 if hit else 0.0
    shiver = math.sin(T * 70) * 6 if (tl.on(3, T) or tl.on(4, T)) else 0
    wobble = math.sin(T * 9) * 0.06 * smooth(p_lift * 2) if 0 < p_lift < 0.78 else 0
    if tl.on(1, T):
        b_arms, b_expr = (20, 160), "happy"
    elif 0 < p_lift < 0.78:
        b_arms, b_expr = (165, 165), "surprised" if p_lift > 0.5 else "happy"
    elif hit:
        b_arms, b_expr = (30, 30), "scared"
    else:
        b_arms, b_expr = (18, 18), "happy"
    hands = bruno(ctx, T, tl, bx + shiver, face=-1, arms=b_arms, expr=b_expr, rot=wobble, snow=snow,
                  look=(0, -1) if 0 < p_lift < 0.78 else (0.6, 0))
    if 0 < p_lift < 0.78:
        r = lerp(50, 185, smooth(p_lift / 0.55))
        hx = (hands["front"][0] + hands["back"][0]) / 2
        hy = min(hands["front"][1], hands["back"][1])
        drop = ease_in((p_lift - 0.6) / 0.18) if p_lift > 0.6 else 0
        snowball(ctx, hx, min(hy - r + 20, GY - 690 - r) + drop * 300, r, T * 2)
    if hit:
        age = T - tl.t0(2) - tl.dur(2) * 0.78
        for i in range(14):
            a = i * 2 * math.pi / 14
            d = 80 + 340 * ease_out(age * 2)
            circle(ctx, bx + math.cos(a) * d, GY - 520 + math.sin(a) * d * 0.7, 40 * clamp(1 - age * 1.2))
            ctx.set_source_rgba(1, 1, 1, 0.95)
            ctx.fill()
        pop_text(ctx, "POOF!", 790, 760, age, 140, color="#BFE9FF")

    l_expr = "laugh" if tl.on(4, T) and tl.mouth("leo", T) < 0.05 else ("surprised" if hit and not tl.on(4, T) else "happy")
    l_arms = (150, 150) if tl.on(0, T) else ((40, 40) if tl.on(4, T) else (14, 14))
    leo(ctx, T, tl, 200, expr=l_expr, arms=l_arms,
        hop=abs(math.sin(T * 10)) * 40 if tl.on(0, T) or tl.on(4, T) else 0)
    snowfall(ctx, T)
    ctx.restore()


EP3 = dict(
    num=3, title="The Snow Bear", seed=11,
    beats=[
        dict(say=("leo", "Let's build a giant snowman!")),
        dict(say=("bruno", "Leave it to me!")),
        dict(act="lift", dur=2.4, sfx=[("boing", 1.2), ("poof", 1.85)]),
        dict(say=("bruno", "Brrr! So... cold!")),
        dict(say=("leo", "Ha ha! You're a snow bear!"), sfx=[("ding", 0.2)]),
    ],
    draw=draw_ep3,
)


# =================================================================== 4. Mission to the Moon
def draw_ep4(ctx, T, tl):
    p_board, p_fly = tl.p(2, T), tl.p(4, T)
    count = tl.on(3, T)
    star_shift = ease_in(p_fly) * 900
    ctx.save()
    shake(ctx, 6 * count * clamp((T - tl.t0(3)) / tl.dur(3)) + 9 * (0 < p_fly < 0.5), T)
    bg_night(ctx, T, star_shift)
    moon(ctx, 260, 700, 110)
    ctx.save()
    ctx.translate(0, star_shift)
    night_ground(ctx, T)
    ctx.restore()

    rx, ry = 790, GY
    fly_y = -ease_in(p_fly) * 2400
    boarded = p_board >= 1

    def crew(c, wx, wy, wr):
        if not boarded:
            return
        draw_leo(c, wx - 38, wy + 160, s=0.33, mouth=tl.mouth("leo", T), blink=tl.blink("leo", T),
                 expr="happy" if p_fly == 0 else "surprised")
        draw_bruno(c, wx + 40, wy + 230, s=0.3, mouth=tl.mouth("bruno", T), blink=tl.blink("bruno", T),
                   expr="happy" if p_fly == 0 else "laugh")

    flame = 0.0
    if count:
        w = tl.word(3, T)
        flame = 0.25 if w >= 3 else 0
    if p_fly > 0:
        flame = 1.2
    if p_fly > 0 or (count and tl.word(3, T) >= 3):
        smoke(ctx, rx, ry + star_shift, tl.t0(3), T - tl.t0(3) - 1.0, n=12)
    rocket(ctx, rx, ry + fly_y, 0.95, rot=math.sin(T * 50) * 0.01 * count, flame=flame, t=T, window_fn=crew)

    if not boarded:
        jump = smooth(p_board)
        arc = math.sin(jump * math.pi) * 260
        lx = lerp(200, rx - 40, jump)
        bx = lerp(480, rx + 40, jump)
        sc = lerp(1.0, 0.35, jump)
        a = 1 - smooth((p_board - 0.6) / 0.4) if p_board > 0.6 else 1
        l_arms = (14, 150) if tl.on(0, T) else ((150, 150) if p_board > 0 else (14, 14))
        b_arms = (18, 150) if tl.on(1, T) else ((150, 150) if p_board > 0 else (18, 18))
        bruno(ctx, T, tl, bx, y=GY - arc, s=BS * sc, face=-1 if tl.on(0, T) else 1, arms=b_arms, alpha=a,
              look=(0.5, -0.8) if tl.on(0, T) else (0.6, 0))
        leo(ctx, T, tl, lx, y=GY - arc * 1.2, s=sc, arms=l_arms, alpha=a,
            look=(-0.3, -1) if tl.on(0, T) else (0.6, 0))

    if count:  # 3 · 2 · 1 · BLAST OFF from the spoken word timings
        w = tl.word(3, T)
        labels = ["3", "2", "1", "BLAST OFF!", "BLAST OFF!"]
        if 0 <= w < len(labels):
            age = T - tl.word_start(3, w)
            k = ease_out_back(age / 0.2)
            ctx.save()
            ctx.translate(540, 820)
            ctx.scale(k, k)
            text(ctx, labels[w], 0, 60, 230 if w < 3 else 140, color="#FFE14D", sw=20)
            ctx.restore()
    if p_fly > 0.55:  # tiny rocket zooming past the moon
        q = (p_fly - 0.55) / 0.45
        rocket(ctx, lerp(-80, 560, q), lerp(900, 520, q), 0.18, rot=1.1, flame=1.0, t=T)
    ctx.restore()


EP4 = dict(
    num=4, title="Mission to the Moon", seed=5,
    beats=[
        dict(say=("leo", "Ready for the moon, Bruno?")),
        dict(say=("bruno", "Ready, Captain Leo!")),
        dict(act="board", dur=0.9, sfx=[("boing", 0.0)]),
        dict(say=("leo", "Three, two, one... Blast off!"), sfx=[("rumble", 1.2)]),
        dict(act="fly", dur=2.0, sfx=[("whoosh", 0.0), ("sparkle", 1.4)]),
    ],
    draw=draw_ep4,
)


# =================================================================== 5. Gone Fishing
def draw_ep5(ctx, T, tl):
    p_bite, p_pull, p_splash = tl.p(1, T), tl.p(2, T), tl.p(4, T)
    bg_river(ctx, T)
    bx = 560
    lean = -0.12 * smooth(p_bite * 2) if p_pull == 0 or p_pull >= 1 else -0.18
    if p_splash > 0:
        lean = 0
    b_expr = "happy"
    if 0 < p_bite:
        b_expr = "surprised"
    if tl.on(3, T):
        b_expr = "happy"
    if p_splash > 0.25:
        b_expr = "surprised"
    hands = bruno(ctx, T, tl, bx, face=1, arms=(30, 70), rot=lean, expr=b_expr,
                  look=(1, 0.2) if p_pull == 0 else (0.8, -0.8))
    hx, hy = hands["front"]
    tip = (hx + 150, hy - 320 - 60 * smooth(p_bite * 2))
    line(ctx, [(hx - 30, hy + 40), tip], 14, "#6B3E1E")
    circle(ctx, hx, hy, 46)
    paint(ctx, "#9A5B2C", 7)

    bob = (860, 1290)
    if p_pull == 0:  # line to the bobber in the water
        dip = 26 * abs(math.sin(T * 14)) * (p_bite > 0.1)
        line(ctx, [tip, (bob[0], bob[1] - 10 + dip)], 3, "#FFFFFF", 0.9)
        circle(ctx, bob[0], bob[1] + dip, 16)
        paint(ctx, "#E53935", 4)
        if p_bite > 0.1:
            for k in range(2):
                rr = ((T * 1.5 + k * 0.5) % 1.0)
                ellipse(ctx, bob[0], bob[1] + 18, 30 + rr * 90, 8 + rr * 20)
                ctx.set_source_rgba(1, 1, 1, 0.7 * (1 - rr))
                ctx.set_line_width(4)
                ctx.stroke()
            pop_text(ctx, "!", hx - 40, GY - 900, T - tl.t0(1) - 0.2, 150, color="#FF5252", rot=0)
    else:
        # the (tiny) fish flies out of the water and dangles from the line
        if p_splash < 0.45:
            q = ease_out(p_pull)
            fx = lerp(bob[0], tip[0], q)
            fy = lerp(bob[1], tip[1] + 170, q) - math.sin(q * math.pi) * 200
            sway = math.sin(T * 6) * 18
            line(ctx, [tip, (fx + sway * 0.3, fy - 30)], 3, "#FFFFFF", 0.9)
            wig = math.sin(T * (30 if p_splash > 0 else 10)) * 0.5
            fish(ctx, fx + sway * 0.3, fy, 0.75, rot=math.pi / 2 + wig * 0.3, wiggle=wig)
            if p_pull < 1:
                drops(ctx, bob[0], bob[1], T - tl.t0(2), n=8, power=380, seed=3)
        else:
            line(ctx, [tip, (tip[0], tip[1] + 140)], 3, "#FFFFFF", 0.9)
            q = (p_splash - 0.45) / 0.55
            fish(ctx, lerp(tip[0], 900, q), lerp(tip[1] + 170, 1300, ease_in(q)) - math.sin(q * math.pi) * 160,
                 0.75, rot=q * 6, wiggle=math.sin(T * 30) * 0.5)
            if q > 0.9:
                drops(ctx, 900, 1300, T - tl.t0(4) - tl.dur(4) * 0.95, n=8, power=300, seed=9)
        if 0.25 < p_splash:  # the fish splashes Bruno right in the face
            drops(ctx, tip[0] - 40, tip[1] + 170, T - tl.t0(4) - tl.dur(4) * 0.25, n=16, power=460, seed=5)
        if tl.on(5, T) or p_splash > 0.5:  # dripping wet bear
            for i in range(5):
                age = (T * 1.4 + i * 0.2) % 1.0
                ellipse(ctx, bx - 120 + i * 60, GY - 640 + age * 160, 7, 11)
                paint(ctx, "#7FD4FF", 3, a=1 - age)
    pop_text(ctx, "SPLASH!", 760, 820, T - tl.t0(4) - tl.dur(4) * 0.3, 110, color="#7FD4FF")

    l_expr = "laugh" if tl.on(3, T) and tl.mouth("leo", T) < 0.05 else (
        "surprised" if 0 < p_bite < 1 or 0 < p_pull else "happy")
    leo(ctx, T, tl, 190, expr=l_expr, arms=(40, 40) if tl.on(3, T) else ((14, 120) if tl.on(3, T) else (14, 14)),
        hop=abs(math.sin(T * 10)) * 35 if tl.on(3, T) else 0, look=(1, 0))


EP5 = dict(
    num=5, title="Gone Fishing", seed=9,
    beats=[
        dict(say=("bruno", "Shh... I'll catch a big fish.")),
        dict(act="bite", dur=1.1, sfx=[("plop", 0.15), ("plop", 0.45)]),
        dict(act="pull", dur=0.8, sfx=[("splash", 0.0), ("boing", 0.4)]),
        dict(say=("leo", "Ha! That's a tiny fish!")),
        dict(act="splash", dur=1.1, sfx=[("splash", 0.3), ("plop", 1.0)]),
        dict(say=("bruno", "Hey! Come back!")),
    ],
    draw=draw_ep5,
)

EPISODES = [EP1, EP2, EP3, EP4, EP5]
