"""Hop Hop Froggy — renders the sing-along video (1920x1080) from build/song.json + build/song.wav."""
import json, math, os, random, subprocess, sys
from multiprocessing import Pool
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "nfl-short"))
from toon import Pen, S, OUT, GOLD, font, star, ease  # noqa: E402

W, H, FPS = 1920, 1080, 30
WATER_Y = 640
SONG = json.load(open(os.path.join(HERE, "build", "song.json")))
FINAL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "hop_hop_froggy.mp4")

FROGS = {  # color, scale, back-row x
    "baby": ((150, 215, 90), 0.55, 960),
    "mommy": ((110, 200, 100), 0.82, 640),
    "daddy": ((70, 165, 80), 1.0, 1280),
    "grandma": ((125, 180, 115), 0.78, 330),
    "grandpa": ((95, 150, 95), 0.82, 1590),
}
ORDER = ["baby", "mommy", "daddy", "grandma", "grandpa"]
VERSE_TITLES = ["Baby Froggy", "Mommy Froggy", "Daddy Froggy", "Grandma Froggy", "Grandpa Froggy",
                "Rainy Day", "Rainbow", "Goodnight"]
BACK_Y = 760
FRONT = (960, 905)


# ---------------------------------------------------------------- frog
def frog(pen, kind, t, mouth=0.0, blink=False, look=(0, 0), arms="down", sleepy=False, croak=0.0, umbrella=False):
    col = FROGS[kind][0]
    dark = tuple(int(c * 0.75) for c in col)
    light = (215, 240, 170)
    if umbrella:
        pen.line([(95, -60), (95, -330)], (110, 80, 40), 8)
        pen.d.pieslice([pen.p(-60, -460), pen.p(250, -230)], 180, 360, fill=(80, 170, 70), outline=OUT, width=int(6 * S * pen.sc))
        pen.line([(95, -460), (95, -345)], (60, 130, 50), 5)
    for sx in (-1, 1):
        pen.ell(sx * 95, -38, 62, 42, dark, 6)
        pen.ell(sx * 125, -8, 48, 15, dark, 5)
    pen.ell(0, -92, 115, 95, col, 7)
    pen.ell(0, -72, 76, 60, light, 0)
    if arms == "up":
        for sx in (-1, 1):
            pen.ell(sx * 125, -175 + 10 * math.sin(t * 10), 24, 40, col, 6)
    elif arms == "hug":
        for sx in (-1, 1):
            pen.ell(sx * 70, -95, 50, 22, col, 6)
    else:
        for sx in (-1, 1):
            pen.ell(sx * 82, -62, 22, 34, col, 6)
    if croak > 0:
        pen.ell(0, -140 + 30 * croak, 60 * croak + 10, 50 * croak + 8, (250, 170, 190), 6)
    pen.ell(0, -192, 122, 86, col, 7)
    for sx in (-1, 1):
        cx = sx * 62
        pen.ell(cx, -262, 44, 44, col, 7)
        if blink or sleepy:
            pen.d.arc([pen.p(cx - 26, -280), pen.p(cx + 26, -244)], 20, 160, fill=OUT, width=int(7 * S * pen.sc))
        else:
            pen.ell(cx, -264, 32, 32, "white", 0)
            pen.ell(cx + look[0] * 10, -264 + look[1] * 10, 15, 15, OUT, 0)
            pen.ell(cx + look[0] * 10 - 5, -269 + look[1] * 10, 5, 5, "white", 0)
        pen.ell(sx * 88, -192, 20, 11, (250, 150, 160), 0)
    if mouth > 0.08:
        pen.ell(0, -178, 46, 8 + 30 * mouth, (150, 30, 50), 6)
        pen.ell(0, -168 + 10 * mouth, 26, 6 + 10 * mouth, (250, 120, 140), 0)
    else:
        pen.d.arc([pen.p(-72, -240), pen.p(72, -168)], 25, 155, fill=OUT, width=int(7 * S * pen.sc))
    # accessories
    if kind == "baby":
        pen.d.arc([pen.p(-14, -310), pen.p(26, -270)], 180, 450, fill=dark, width=int(7 * S * pen.sc))
        pen.ell(0, -40, 50, 30, (250, 250, 255), 5)
    elif kind == "mommy":
        pen.poly([(-70, -305), (-25, -282), (-70, -258)], (240, 90, 150), 5)
        pen.poly([(-20, -305), (-65, -282), (-20, -258)], (240, 90, 150), 5)
        pen.ell(-45, -282, 12, 12, (255, 140, 190), 4)
        for i in range(7):
            a = math.pi * (0.2 + 0.6 * i / 6)
            pen.ell(math.cos(a) * 70, -150 + math.sin(a) * 30, 9, 9, "white", 3)
    elif kind == "daddy":
        pen.poly([(-40, -130), (0, -112), (-40, -94)], (60, 120, 220), 5)
        pen.poly([(40, -130), (0, -112), (40, -94)], (60, 120, 220), 5)
        pen.ell(0, -112, 11, 11, (40, 90, 190), 4)
    elif kind == "grandma":
        for sx in (-1, 1):
            pen.ell(sx * 62, -264, 36, 36, None, 5)
        pen.line([(-26, -264), (26, -264)], OUT, 5)
        pen.ell(0, -306, 70, 18, (190, 120, 200), 5)
        pen.ell(30, -322, 16, 14, (250, 200, 80), 4)
        pen.poly([(-110, -150), (110, -150), (80, -60), (-80, -60)], (190, 120, 200), 6)
    elif kind == "grandpa":
        pen.ell(-30, -205, 34, 14, (240, 240, 245), 4)
        pen.ell(30, -205, 34, 14, (240, 240, 245), 4)
        pen.d.chord([pen.p(-70, -340), pen.p(70, -270)], 180, 360, fill=(140, 90, 60), outline=OUT, width=int(5 * S * pen.sc))
        pen.rect(-80, -306, 90, -294, (140, 90, 60), 4, 4)
        pen.line([(130, -60), (150, 0)], (120, 75, 40), 9)
        pen.d.arc([pen.p(100, -90), pen.p(150, -40)], 180, 360, fill=(120, 75, 40), width=int(9 * S * pen.sc))
    if sleepy:
        pen.ell(0, -175, 22, 14 + 6 * math.sin(t * 2), (150, 30, 50), 5)


def lily_pad(pen, x, y, r=150):
    pen.ell(x, y, r, r * 0.32, (60, 150, 70), 6)
    pen.poly([(x, y), (x + r * 0.9, y - r * 0.12), (x + r * 0.9, y + r * 0.12)], (80, 160, 220), 0)
    pen.line([(x - r * 0.6, y), (x + r * 0.5, y)], (90, 180, 90), 4)


# ---------------------------------------------------------------- backgrounds
def sky_bg(theme):
    img = Image.new("RGB", (W * S, H * S))
    d = ImageDraw.Draw(img)
    top, bot = {"day": ((110, 200, 255), (200, 240, 255)), "rain": ((110, 125, 150), (170, 185, 205)),
                "night": ((15, 20, 60), (60, 60, 120))}[theme]
    for y in range(0, WATER_Y * S, 4):
        k = y / (WATER_Y * S)
        d.rectangle([0, y, img.width, y + 4], fill=tuple(int(a + (b - a) * k) for a, b in zip(top, bot)))
    pen = Pen(img)
    hill = {"day": (120, 200, 110), "rain": (100, 150, 100), "night": (40, 70, 60)}[theme]
    for x, r in ((200, 420), (900, 520), (1650, 460)):
        pen.ell(x, WATER_Y + 60, r, 230, hill, 0)
    water = {"day": (80, 160, 220), "rain": (90, 130, 170), "night": (30, 50, 100)}[theme]
    pen.rect(-10, WATER_Y, W + 10, H, water, 0)
    for i in range(14):
        x = (i * 157) % W
        pen.line([(x, WATER_Y + 60 + (i % 5) * 70), (x + 90, WATER_Y + 60 + (i % 5) * 70)], tuple(min(255, c + 40) for c in water), 5)
    for x in (60, 140, 1800, 1860):  # reeds
        pen.line([(x, H), (x + 20, WATER_Y - 120)], (70, 130, 60), 10)
        pen.ell(x + 20, WATER_Y - 150, 14, 45, (130, 80, 40), 4)
    if theme == "night":
        r = random.Random(4)
        for _ in range(90):
            pen.ell(r.uniform(0, W), r.uniform(0, WATER_Y - 100), 3, 3, (255, 255, 220), 0)
    for x in FROGS.values():
        lily_pad(pen, x[2], BACK_Y + 10, 125)
    lily_pad(pen, FRONT[0], FRONT[1] + 10, 190)
    return img


_BG = {}


def background(theme):
    if theme not in _BG:
        _BG[theme] = sky_bg(theme)
    return _BG[theme].convert("RGBA")


def sun(pen, t, beat):
    x, y = 1650, 150
    for i in range(12):
        a = i * math.pi / 6 + t * 0.4
        pen.line([(x + math.cos(a) * 110, y + math.sin(a) * 110), (x + math.cos(a) * 150, y + math.sin(a) * 150)], (255, 200, 40), 12)
    r = 92 + 6 * beat
    pen.ell(x, y, r, r, (255, 220, 60), 7)
    for sx in (-1, 1):
        pen.ell(x + sx * 30, y - 15, 9, 13, OUT, 0)
    pen.d.arc([pen.p(x - 40, y - 20), pen.p(x + 40, y + 40)], 20, 160, fill=OUT, width=7 * S)


def clouds(pen, t, grey=False):
    c = (230, 235, 240) if grey else "white"
    for i, (x0, y, s) in enumerate(((100, 120, 1.0), (700, 80, 1.2), (1200, 200, 0.8))):
        x = (x0 + t * 20 * (i + 1)) % (W + 400) - 200
        for dx, dy, r in ((0, 0, 60), (65, 12, 50), (-65, 14, 45), (25, -30, 52)):
            pen.ell(x + dx * s, y + dy * s, r * 1.2 * s, r * s, c, 0)


def rainbow(frame, k):
    over = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    cols = [(240, 60, 60), (250, 150, 40), (250, 230, 60), (90, 200, 90), (70, 140, 240), (140, 90, 220)]
    cx, cy = 960, WATER_Y + 40
    for i, c in enumerate(cols):
        r = 760 - i * 40
        d.arc([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], 180, 180 + 180 * k, fill=c + (220,), width=40 * S)
    frame.alpha_composite(over)


def raindrops(pen, t):
    r = random.Random(1)
    for i in range(70):
        x0, sp = r.uniform(0, W), r.uniform(700, 1000)
        y = (r.uniform(0, H) + t * sp) % H
        pen.line([(x0, y), (x0 - 8, y + 30)], (200, 220, 255), 4)


# ---------------------------------------------------------------- lyrics
def active_word(t):
    for w in SONG["words"]:
        if w["start"] <= t < w["start"] + w["dur"]:
            return w
    return None


def current_line(t):
    best = None
    for w in SONG["words"]:
        if w["start"] - 0.4 <= t:
            best = (w["verse"], w["line"])
    if best is None or t >= SONG["outro_start"]:
        return None, []
    return best, [w for w in SONG["words"] if (w["verse"], w["line"]) == best]


def lyrics(frame, t):
    key, words = current_line(t)
    if not words:
        return
    pen = Pen(frame)
    size = 66
    texts = [w["text"] for w in words]
    while True:
        widths = [font(size).getlength(x) / S for x in texts]
        gap = size / 3
        total = sum(widths) + gap * (len(words) - 1)
        if total < 1650 or size <= 40:
            break
        size -= 4
    pen.rect(960 - total / 2 - 50, 960, 960 + total / 2 + 50, 1060, (255, 255, 255), 7, 40)
    x = 960 - total / 2
    for w, wd in zip(words, widths):
        on = w["start"] <= t < w["start"] + w["dur"]
        done = t >= w["start"] + w["dur"]
        if on:
            pen.rect(x - 10, 975, x + wd + 10, 1045, (255, 225, 90), 0, 18)
        col = (230, 70, 40) if on else ((60, 150, 70) if done else (90, 90, 110))
        Pen(frame, x + wd / 2, 1010).text(0, 0, w["text"], size, col, 0)
        x += wd + gap


# ---------------------------------------------------------------- frame
def beat_phase(t):
    return (t / SONG["beat"]) % 1


def render(fi):
    t = fi / FPS
    verses = SONG["verses"]
    vi = next((v["index"] for v in verses if v["start"] <= t < v["end"]), None)
    who = verses[vi]["who"] if vi is not None else None
    theme = "rain" if who == "rain" else ("night" if who == "night" else "day")
    frame = background(theme)
    pen = Pen(frame)
    bp = beat_phase(t)
    pulse = math.exp(-bp * 5)
    if theme == "day":
        sun(pen, t, pulse)
        clouds(pen, t)
    elif theme == "rain":
        clouds(pen, t, grey=True)
    else:
        pen.ell(1650, 150, 80, 80, (250, 245, 210), 0)
        pen.ell(1685, 130, 72, 72, (15, 20, 60), 0)
    if who == "rainbow":
        rainbow(frame, ease((t - verses[vi]["start"]) / 3.0))
    w = active_word(t)
    featured = who if who in FROGS else None
    group = who in ("rain", "rainbow", "night")
    vstart = verses[vi]["start"] if vi is not None else 0
    # back-row frogs
    for kind in ORDER:
        if kind == featured:
            continue
        x = FROGS[kind][2]
        sc = FROGS[kind][1] * 0.72
        bob = 18 * pulse
        sing = group and w is not None
        mouth = math.sin(math.pi * min(1, (t - w["start"]) / w["dur"])) if sing else 0
        hop = 0
        if group and who != "night" and w is not None and w["text"].lower().strip("!,") in ("splish", "splash", "wow"):
            hop = 50 * math.sin(math.pi * min(1, (t - w["start"]) / w["dur"]))
        look = (0, -1) if who == "rainbow" else ((960 - x) / 900, 0)
        frog(Pen(frame, x, BACK_Y - bob - hop, sc), kind, t, mouth, blink=(t * 0.7 + x) % 4 < 0.12, look=look,
             sleepy=who == "night", umbrella=who == "rain", arms="up" if who == "rainbow" and hop > 10 else "down")
    # featured frog in front
    if featured:
        sc = FROGS[featured][1] * 1.25
        x, y = FRONT
        sing = w is not None
        phase = min(1, (t - w["start"]) / w["dur"]) if w else 0
        mouth = math.sin(math.pi * phase) if sing else 0
        hop = 0
        arms = "down"
        croak = 0
        text = w["text"].lower().strip("!,") if w else ""
        if text == "hop":
            hop = 140 * math.sin(math.pi * phase)
        line4 = w is not None and w["line"] == 3
        enter = ease((t - vstart) / 0.6)
        x = FROGS[featured][2] + (FRONT[0] - FROGS[featured][2]) * enter
        y = BACK_Y + (FRONT[1] - BACK_Y) * enter - 200 * math.sin(math.pi * enter) * (enter < 1)
        if line4 and featured == "baby" and text in ("pond",):
            hop = -60 * phase
        if line4 and featured == "daddy" and text in ("jump", "ever"):
            hop = 600 * math.sin(math.pi * min(1, (t - w["start"]) / 1.5))
        if line4 and featured == "grandma":
            hop = 40 * math.sin(math.pi * phase)
        if line4 and featured == "grandpa" and text == "ribbit":
            croak = math.sin(math.pi * phase)
        if line4 and featured == "mommy":
            arms = "hug"
        if text == "hop":
            arms = "up"
        frog(Pen(frame, x, y - hop, sc), featured, t, mouth, blink=False, look=(0, -0.3), arms=arms, croak=croak)
        if line4 and featured == "mommy":
            frog(Pen(frame, x + 150, y - 10, FROGS["baby"][1] * 0.9), "baby", t, 0, look=(-1, -0.3))
            for i in range(4):
                u = (t * 0.6 + i / 4) % 1
                hx, hy = x - 120 + i * 80, y - 420 - u * 200
                pen = Pen(frame)
                pen.ell(hx - 12, hy, 16, 16, (240, 80, 120), 0); pen.ell(hx + 12, hy, 16, 16, (240, 80, 120), 0)
                pen.poly([(hx - 27, hy + 4), (hx + 27, hy + 4), (hx, hy + 32)], (240, 80, 120), 0)
        if line4 and featured == "baby" and text == "pond":
            pen = Pen(frame)
            for i in range(12):
                a = -math.pi * (0.1 + 0.8 * i / 11)
                r = 60 + 260 * phase
                pen.ell(x + math.cos(a) * r, y - 40 + math.sin(a) * r * 0.8 + 200 * phase * phase, 14, 18, (200, 230, 255), 4)
        pen = Pen(frame)
        for i in range(5):
            a = t * 2 + i * 2 * math.pi / 5
            star(pen, x + math.cos(a) * 240, y - 200 + math.sin(a) * 60, 16, GOLD)
    if who == "rain":
        raindrops(Pen(frame), t)
    if who == "night":
        pen = Pen(frame)
        r = random.Random(7)
        for i in range(14):
            fx = r.uniform(100, W - 100) + 40 * math.sin(t + i)
            fy = r.uniform(200, 600) + 30 * math.cos(t * 1.3 + i)
            if math.sin(t * 3 + i) > -0.3:
                pen.ell(fx, fy, 9, 9, (255, 250, 150), 0)
        for i, kind in enumerate(ORDER):
            pen.text(FROGS[kind][2] + 60, BACK_Y - 260 - ((t * 30 + i * 20) % 60), "z", 44, "white", 5)
    # titles
    pen = Pen(frame)
    if t < SONG["intro_end"]:
        k = max(0.05, ease(t / 0.6))
        letters = "HOP HOP FROGGY!"
        fw = [font(130).getlength(ch) / S for ch in letters]
        x = 960 - sum(fw) / 2
        for i, (ch, cw) in enumerate(zip(letters, fw)):
            bounce = abs(math.sin(t * 6 + i * 0.5)) * 30
            if ch != " ":
                Pen(frame, x + cw / 2, 330 - bounce, k).text(0, 0, ch, 130, [(250, 90, 60), GOLD, (90, 200, 90), (70, 140, 240)][i % 4], 12)
            x += cw
        Pen(frame, 960, 480, k).text(0, 0, "The Froggy Family Song", 64, "white", 9)
    elif t >= SONG["outro_start"]:
        u = t - SONG["outro_start"]
        k = max(0.05, ease(u / 0.6))
        Pen(frame, 960, 320 - abs(math.sin(t * 6)) * 25, k).text(0, 0, "YAY! SING AGAIN!", 120, GOLD, 12)
        st_k = max(0.05, ease((u - 1) / 0.6))
        Pen(frame, 960, 470, st_k).text(0, 0, "Hop Hop Froggy!", 70, "white", 9)
        r = random.Random(3)
        for i in range(40):
            cx = (r.uniform(0, W) + u * 60 * (1 + i % 3)) % W
            cy = (u * 300 * (1 + i % 4) + r.uniform(0, H)) % H
            pen.rect(cx, cy, cx + 16, cy + 26, [(240, 90, 60), GOLD, (90, 200, 90), (70, 140, 240)][i % 4], 0, 3)
    elif vi is not None:
        title = VERSE_TITLES[vi]
        k = ease((t - vstart) / 0.4)
        p = Pen(frame, 70, 70, 0.6 + 0.4 * k)
        wd = font(56).getlength(title) / S + 60
        p.rect(0, 0, wd, 90, (255, 255, 255), 6, 45)
        p.text(wd / 2, 45, title, 56, (60, 150, 70), 0)
    lyrics(frame, t)
    return frame.convert("RGB").reduce(S).tobytes()


def main():
    n = int(SONG["total"] * FPS)
    if os.environ.get("PREVIEW"):
        for ts in map(float, os.environ["PREVIEW"].split(",")):
            Image.frombytes("RGB", (W, H), render(int(ts * FPS))).save(os.path.join(HERE, "build", f"prev_{ts:06.1f}.png"))
        return
    wav = os.path.join(HERE, "build", "song.wav")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", FINAL], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, buf in enumerate(pool.imap(render, range(n), chunksize=6)):
            ff.stdin.write(buf)
            if i % 300 == 0:
                print(f"frame {i}/{n}", flush=True)
    ff.stdin.close(); ff.wait()
    print("done", FINAL)


if __name__ == "__main__":
    main()
