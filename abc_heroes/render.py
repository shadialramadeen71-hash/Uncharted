"""Render the "Brick Heroes ABC" YouTube Shorts series (1080x1920, <=15 s each).

Usage:  python3 render.py            # all 26 episodes
        python3 render.py A B C      # selected letters
"""
import math, os, random, subprocess, sys, tempfile
from functools import lru_cache
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

from episodes import LETTERS, episode
from audio import build_audio

W, H, FPS, LENGTH = 1080, 1920, 30, 14.5
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
SKIN, INK = (255, 210, 31), (25, 25, 35)


# ---------------------------------------------------------------- helpers
def ease_out_back(x):
    x = min(max(x, 0), 1); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def ease(x):
    x = min(max(x, 0), 1)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


@lru_cache(maxsize=256)
def font(size):
    return ImageFont.truetype(FONT, size)


@lru_cache(maxsize=128)
def text_img(text, size, fill, stroke=(25, 25, 35), sw=10):
    f = font(size)
    l, t, r, b = f.getbbox(text, stroke_width=sw)
    im = Image.new("RGBA", (r - l + 4, b - t + 4))
    ImageDraw.Draw(im).text((2 - l, 2 - t), text, font=f, fill=fill,
                            stroke_width=sw, stroke_fill=stroke)
    return im


def paste_center(frame, im, cx, cy, scale=1.0):
    if scale <= 0.01:
        return
    if abs(scale - 1) > 0.01:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))),
                       Image.BILINEAR)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


@lru_cache(maxsize=32)
def emoji_img(e, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new("RGBA", (160, 160))
    ImageDraw.Draw(im).text((10, 10), e, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    k = size / max(im.size)
    return im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)


# ---------------------------------------------------------------- bricks
def draw_brick(d, x, y, w, h, color, stud=True):
    """One toy brick (front view) with studs on top."""
    sw = max(2, int(h * 0.08))
    if stud:
        n = max(1, round(w / h * 1.0))
        sw_ = w / n
        for i in range(n):
            sx = x + sw_ * i + sw_ * 0.22
            d.rounded_rectangle([sx, y - h * 0.22, sx + sw_ * 0.56, y + 2], radius=3,
                                fill=shade(color, 1.12), outline=INK, width=sw)
    d.rounded_rectangle([x, y, x + w, y + h], radius=max(3, h // 8),
                        fill=color, outline=INK, width=sw)
    d.line([x + sw * 2, y + sw * 2, x + w - sw * 2, y + sw * 2], fill=shade(color, 1.3), width=sw)


def letter_layout(ch, cols=14, rows=16, cell_w=62, cell_h=44):
    """Turn a glyph into a list of bricks (col, row, length) - built from code."""
    gw, gh = cols * 20, rows * 20
    m = Image.new("L", (gw, gh))
    f = ImageFont.truetype(FONT, int(gh * 1.25))
    l, t, r, b = f.getbbox(ch)
    ImageDraw.Draw(m).text(((gw - (r - l)) / 2 - l, (gh - (b - t)) / 2 - t), ch, font=f, fill=255)
    m = m.resize((cols, rows), Image.BOX)
    on = [[m.getpixel((c, r)) > 110 for c in range(cols)] for r in range(rows)]
    bricks = []
    for r in range(rows):
        c = 0
        while c < cols:
            if on[r][c]:
                ln = 2 if (c + 1 < cols and on[r][c + 1] and (c + r) % 2 == 0) else 1
                bricks.append((c, r, ln)); c += ln
            else:
                c += 1
    return bricks, cols * cell_w, rows * cell_h, cell_w, cell_h, rows


BRICK_COLORS = [(230, 50, 45), (30, 120, 230), (255, 200, 0), (45, 175, 75),
                (255, 130, 20), (160, 70, 200)]


class BrickLetter:
    def __init__(self, ch, main):
        (self.bricks, self.w, self.h, self.cw, self.chh, self.rows) = letter_layout(ch)
        rnd = random.Random(ord(ch))
        self.colors = [main if rnd.random() < 0.55 else rnd.choice(BRICK_COLORS)
                       for _ in self.bricks]
        self.full = self.render(1.0)

    def render(self, progress, drop=260):
        im = Image.new("RGBA", (self.w + 20, self.h + 40))
        d = ImageDraw.Draw(im)
        order = sorted(range(len(self.bricks)), key=lambda i: -self.bricks[i][1])
        for k, i in enumerate(order):
            c, r, ln = self.bricks[i]
            # bottom rows land first
            start = (self.rows - 1 - r) / self.rows * 0.8
            p = (progress - start) / 0.2
            if p <= 0:
                continue
            y_off = -(1 - ease_out_back(p)) * drop
            draw_brick(d, 10 + c * self.cw, 22 + r * self.chh + y_off, ln * self.cw - 2,
                       self.chh - 2, self.colors[i])
        return im


# ---------------------------------------------------------------- hero
def rot(pts, cx, cy, ang):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def draw_hero(frame, hero, letter, cx, cy, s=1.0, arms=(10, -10), t=0.0, legs=0.0):
    """Brick-style minifigure superhero. (cx, cy) = hip centre. arms = degrees."""
    d = ImageDraw.Draw(frame)
    S = lambda v: v * s
    ow = max(3, int(5 * s))
    flutter = math.sin(t * 9) * 18
    # cape (behind)
    d.polygon([(cx - S(50), cy - S(148)), (cx + S(50), cy - S(148)),
               (cx + S(88 + flutter), cy + S(95)), (cx - S(88 - flutter), cy + S(95))],
              fill=hero["cape"], outline=INK, width=ow)
    # legs
    for side in (-1, 1):
        lx = cx + side * S(30)
        swing = legs * side * 22
        pts = [(lx - S(26), cy), (lx + S(26), cy), (lx + S(26), cy + S(120)), (lx - S(26), cy + S(120))]
        d.polygon(rot(pts, lx, cy, swing), fill=hero["legs"], outline=INK, width=ow)
        foot = [(lx - S(30), cy + S(105)), (lx + S(30), cy + S(105)), (lx + S(30), cy + S(128)), (lx - S(30), cy + S(128))]
        d.polygon(rot(foot, lx, cy, swing), fill=shade(hero["legs"], 0.7), outline=INK, width=ow)
    d.rounded_rectangle([cx - S(60), cy - S(24), cx + S(60), cy + S(8)], radius=int(S(6)),
                        fill=shade(hero["legs"], 0.85), outline=INK, width=ow)
    # arms (behind torso edge)
    for side, ang in ((-1, arms[0]), (1, arms[1])):
        sx, sy = cx + side * S(54), cy - S(138)
        pts = [(sx - S(17), sy), (sx + S(17), sy), (sx + S(15), sy + S(100)), (sx - S(15), sy + S(100))]
        d.polygon(rot(pts, sx, sy, ang * -side), fill=hero["suit"], outline=INK, width=ow)
        hx, hy = rot([(sx, sy + S(112))], sx, sy, ang * -side)[0]
        r = S(19)
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=SKIN, outline=INK, width=ow)
        d.ellipse([hx - r * 0.45, hy - r * 0.45, hx + r * 0.45, hy + r * 0.45], fill=shade(SKIN, 0.75))
    # torso
    d.polygon([(cx - S(50), cy - S(152)), (cx + S(50), cy - S(152)), (cx + S(62), cy - S(22)), (cx - S(62), cy - S(22))],
              fill=hero["suit"], outline=INK, width=ow)
    d.rectangle([cx - S(62), cy - S(42), cx + S(62), cy - S(30)], fill=hero["cape"])
    er = S(34)
    d.ellipse([cx - er, cy - S(92) - er, cx + er, cy - S(92) + er], fill=hero["cape"], outline=INK, width=ow)
    f = font(max(8, int(S(46))))
    d.text((cx, cy - S(92)), letter, font=f, fill=hero["suit"], anchor="mm",
           stroke_width=max(1, int(S(2))), stroke_fill=INK)
    # neck + head
    d.rectangle([cx - S(20), cy - S(166), cx + S(20), cy - S(150)], fill=shade(SKIN, 0.85), outline=INK, width=ow)
    d.rounded_rectangle([cx - S(22), cy - S(276), cx + S(22), cy - S(250)], radius=int(S(5)), fill=SKIN, outline=INK, width=ow)
    d.rounded_rectangle([cx - S(46), cy - S(258), cx + S(46), cy - S(162)], radius=int(S(20)), fill=SKIN, outline=INK, width=ow)
    if hero["hair"]:
        hc = hero["hair"]
        d.chord([cx - S(52), cy - S(290), cx + S(52), cy - S(200)], 180, 360, fill=hc, outline=INK, width=ow)
        d.ellipse([cx + S(36), cy - S(262), cx + S(78), cy - S(190)], fill=hc, outline=INK, width=ow)
    # mask + eyes
    d.rounded_rectangle([cx - S(46), cy - S(232), cx + S(46), cy - S(202)], radius=int(S(10)), fill=hero["mask"])
    blink = (t % 3.1) < 0.12
    for ex in (-17, 17):
        x = cx + S(ex)
        if blink:
            d.line([x - S(9), cy - S(217), x + S(9), cy - S(217)], fill="white", width=ow)
        else:
            d.ellipse([x - S(11), cy - S(226), x + S(11), cy - S(208)], fill="white")
            d.ellipse([x - S(6), cy - S(222), x + S(6), cy - S(210)], fill=INK)
    d.arc([cx - S(22), cy - S(206), cx + S(22), cy - S(176)], 15, 165, fill=INK, width=max(3, int(S(6))))


# ---------------------------------------------------------------- background
def make_background(hero, seed):
    rnd = random.Random(seed)
    bg = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(bg)
    top, bot = (70, 170, 255), shade(hero["suit"], 0.6)
    top = tuple(int(lerp(a, b, 0.15)) for a, b in zip(top, hero["suit"]))
    for y in range(H):
        k = y / H
        d.line([0, y, W, y], fill=tuple(int(lerp(a, b, k ** 1.4)) for a, b in zip(top, (255, 220, 170))))
    # sun burst
    rays = Image.new("RGBA", (W, H)); rd = ImageDraw.Draw(rays)
    for i in range(18):
        a0 = i * 20
        rd.pieslice([-900, -1300, 1980, 1600], a0, a0 + 9, fill=(255, 255, 255, 40))
    bg.alpha_composite(rays)
    city = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(city)
    # brick city skyline
    x = -20
    while x < W:
        bw = rnd.randint(110, 190); bh = rnd.randint(260, 560)
        col = shade(rnd.choice(BRICK_COLORS), 0.75)
        y0 = H - 240 - bh
        d.rectangle([x, y0, x + bw, H - 240], fill=col, outline=INK, width=5)
        for wy in range(y0 + 30, H - 270, 70):
            for wx in range(x + 18, x + bw - 30, 46):
                d.rectangle([wx, wy, wx + 24, wy + 34], fill=(255, 240, 150) if rnd.random() < .6 else (60, 70, 110))
        for sx in range(x + 12, x + bw - 20, 40):
            d.rectangle([sx, y0 - 14, sx + 22, y0], fill=shade(col, 1.15), outline=INK, width=4)
        x += bw + rnd.randint(4, 30)
    city.putalpha(city.getchannel("A").point(lambda a: a * 0.6))
    bg.alpha_composite(city)
    d = ImageDraw.Draw(bg)
    # green baseplate
    d.rectangle([0, H - 250, W, H], fill=(55, 165, 65))
    for sx in range(10, W, 54):
        d.rounded_rectangle([sx, H - 268, sx + 34, H - 248], radius=4, fill=(75, 190, 85), outline=(25, 90, 30), width=3)
    for yy in range(H - 200, H, 54):
        for sx in range(30 if (yy // 54) % 2 else 4, W, 54):
            d.ellipse([sx, yy, sx + 30, yy + 22], fill=(70, 185, 80), outline=(35, 120, 45), width=3)
    return bg


# ---------------------------------------------------------------- episode
def render_episode(i):
    ep = episode(i)
    L, hero = ep["letter"], ep["hero"]
    os.makedirs(OUT, exist_ok=True)
    name = f"{i + 1:02d}_{L}_{ep['word'].replace(' ', '_').replace('-', '')}"
    mp4 = os.path.join(OUT, name + ".mp4")
    bg = make_background(hero, i)
    bl = BrickLetter(L, hero["suit"])
    lower = text_img(L.lower(), 520, (255, 210, 0), sw=18)
    upper_small = bl.full.resize((bl.full.width // 2, bl.full.height // 2), Image.LANCZOS)
    title = text_img("BRICK HEROES", 120, (255, 220, 0), sw=12)
    title2 = text_img("ABC", 200, (255, 255, 255), sw=14)
    hname = text_img(hero["name"], 70, (255, 255, 255), sw=8)
    emo = emoji_img(ep["emoji"], 520)
    w1 = text_img(f"{L} is for", 110, (255, 255, 255), sw=10)
    ws = 170
    while font(ws).getlength(ep["word"]) > 720:
        ws -= 10
    w2 = text_img(ep["word"], ws, (255, 210, 0), sw=14)
    big_little = text_img(f"Big {L}  •  little {L.lower()}", 90, (255, 255, 255), sw=9)
    end1 = text_img("NEXT:" if ep["next"] else "YOU DID IT!", 130, (255, 255, 255), sw=12)
    end2 = text_img(ep["next"] if ep["next"] else "A - Z", 360 if ep["next"] else 240, (255, 220, 0), sw=18)
    stars = [(random.Random(i * 99 + k).randint(0, W), random.Random(k * 7 + i).randint(0, H - 400),
              random.Random(k).random() * 6) for k in range(40)]

    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "a.wav")
        build_audio(ep, LENGTH, wav)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
               "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", mp4]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fi in range(int(LENGTH * FPS)):
            t = fi / FPS
            beat = (t * 2) % 1                      # 120 BPM
            bounce = math.exp(-beat * 6) * 14
            fr = bg.copy()
            d = ImageDraw.Draw(fr)
            for sx, sy, ph in stars:                # twinkles
                a = (math.sin(t * 4 + ph) + 1) / 2
                r = 4 + 8 * a
                d.polygon([(sx, sy - r * 2), (sx + r * .5, sy - r * .5), (sx + r * 2, sy), (sx + r * .5, sy + r * .5),
                           (sx, sy + r * 2), (sx - r * .5, sy + r * .5), (sx - r * 2, sy), (sx - r * .5, sy - r * .5)],
                          fill=(255, 255, 255, int(120 + 135 * a)))
            if t < 2.0:                                         # 1) intro
                k = ease_out_back(t / 0.9)
                paste_center(fr, title, W / 2, 330 - bounce, k)
                paste_center(fr, title2, W / 2, 520 - bounce, ease_out_back((t - 0.3) / 0.8))
                hy = lerp(-400, 1180, ease(t / 1.1))
                draw_hero(fr, hero, L, W / 2, hy, 1.9, arms=(165, 165), t=t)
                paste_center(fr, hname, W / 2, 1560, ease_out_back((t - 1.0) / 0.5))
            elif t < 6.0:                                       # 2) build the letter
                pr = min(1, (t - 2.0) / 1.8)
                im = bl.full if pr >= 1 else bl.render(pr)
                pulse = 1 + (0.04 * math.exp(-beat * 5) if t > 4 else 0)
                paste_center(fr, im, W / 2, 760 - (bounce if t > 4 else 0), pulse)
                wave_ = math.sin(t * 10) * 35
                draw_hero(fr, hero, L, 850, 1500, 0.9, arms=(150 + wave_, 15), t=t)
                paste_center(fr, text_img(f"Letter {L}", 120, (255, 255, 255), sw=11), W / 2, 1270,
                             ease_out_back((t - 2.2) / 0.5))
            elif t < 10.0:                                      # 3) word
                lt = t - 6.0
                paste_center(fr, upper_small, 270, 300, ease_out_back(lt / 0.4))
                wob = math.sin(t * 6) * 0.03
                paste_center(fr, emo, W / 2, 780 - bounce, ease_out_back((lt - 0.2) / 0.6) * (1 + wob))
                paste_center(fr, w1, 600, 1180, ease_out_back((lt - 0.3) / 0.5))
                paste_center(fr, w2, 600, 1350 - bounce * .5, ease_out_back((lt - 0.6) / 0.5))
                draw_hero(fr, hero, L, 170, 1560, 0.75, arms=(15, 120), t=t)
            elif t < 12.75:                                     # 4) upper + lower case
                lt = t - 10.0
                jump = abs(math.sin(lt * math.pi * 2)) * 120
                paste_center(fr, upper_small, 300, 760 - bounce, ease_out_back(lt / 0.5) * 1.05)
                paste_center(fr, lower, 790, 760 - bounce, ease_out_back((lt - 0.5) / 0.5) * 0.85)
                paste_center(fr, big_little, W / 2, 1180, ease_out_back((lt - 0.2) / 0.5))
                draw_hero(fr, hero, L, W / 2, 1560 - jump, 0.8, arms=(160, 160), t=t, legs=math.sin(lt * 12) * .5)
            else:                                               # 5) end card
                lt = t - 12.75
                paste_center(fr, end1, W / 2, 520, ease_out_back(lt / 0.4))
                paste_center(fr, end2, W / 2, 860 - bounce, ease_out_back((lt - 0.2) / 0.5))
                draw_hero(fr, hero, L, W / 2 + lt * 300, 1500 - lt * 500, 1.0, arms=(170, 170), t=t)
            p.stdin.write(fr.convert("RGB").tobytes())
        p.stdin.close()
        p.wait()
    print("done", mp4, flush=True)
    return mp4


if __name__ == "__main__":
    want = [a.upper() for a in sys.argv[1:]]
    idx = [k for k, (l, _, _) in enumerate(LETTERS) if not want or l in want]
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        pool.map(render_episode, idx)
