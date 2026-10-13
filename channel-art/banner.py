"""YouTube channel banner (2560x1440) for Baby Shado, using the kids-shorts animals."""
import math, os, random, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kids-shorts"))
import animals as A  # noqa: E402
from animals import Pen, S, OUT, GOLD, star  # noqa: E402
from toon import font  # noqa: E402

W, H = 2560, 1440
SAFE = (507, 509, 2053, 932)  # visible on every device


def build():
    img = Image.new("RGBA", (W * S, H * S))
    d = ImageDraw.Draw(img)
    for y in range(0, H * S, 4):
        k = y / (H * S)
        d.rectangle([0, y, img.width, y + 4], fill=(int(120 + 110 * k), int(205 + 40 * k), 255))
    pen = Pen(img)
    # rainbow behind the name
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    for i, c in enumerate([(240, 60, 60), (250, 150, 40), (250, 230, 60), (90, 200, 90), (70, 140, 240), (150, 90, 220)]):
        r = 900 - i * 55
        od.arc([(1280 - r) * S, (1180 - r) * S, (1280 + r) * S, (1180 + r) * S], 180, 360, fill=c + (150,), width=55 * S)
    img.alpha_composite(over)
    pen = Pen(img)
    r = random.Random(5)
    for cx, cy, s in ((260, 220, 1.3), (900, 160, 0.9), (1750, 140, 1.0), (2350, 260, 1.2), (560, 420, 0.7), (2050, 400, 0.7)):
        for dx, dy, rr in ((0, 0, 60), (70, 12, 50), (-70, 14, 45), (25, -32, 52)):
            pen.ell(cx + dx * s, cy + dy * s, rr * 1.25 * s, rr * s, "white", 0)
    # smiling sun
    x, y = 2380, 520
    for i in range(12):
        a = i * math.pi / 6
        pen.line([(x + math.cos(a) * 120, y + math.sin(a) * 120), (x + math.cos(a) * 165, y + math.sin(a) * 165)], (255, 200, 40), 14)
    pen.ell(x, y, 100, 100, (255, 220, 60), 8)
    for sx in (-1, 1):
        pen.ell(x + sx * 32, y - 16, 10, 15, OUT, 0)
    pen.d.arc([pen.p(x - 42, y - 22), pen.p(x + 42, y + 40)], 20, 160, fill=OUT, width=8 * S)
    # hills
    for hx, hr, c in ((300, 900, (110, 195, 100)), (1280, 1100, (130, 210, 110)), (2300, 900, (110, 195, 100))):
        pen.ell(hx, 1500, hr, 560, c, 0)
    for _ in range(80):
        fx, fy = r.uniform(0, W), r.uniform(1080, H)
        for k in range(5):
            a = k * 2 * math.pi / 5
            pen.ell(fx + math.cos(a) * 10, fy + math.sin(a) * 10, 8, 8, r.choice([(255, 255, 255), (255, 170, 210), (255, 230, 90)]), 0)
        pen.ell(fx, fy, 6, 6, (250, 180, 40), 0)
    # outer animals (desktop / TV only)
    A.dino(Pen(img, 250, 1330, 1.1), "mommy", 0.3, 0.6, look=(0.6, -0.2), arms="up")
    A.elephant(Pen(img, 2310, 1330, 1.05), "baby", 0.3, 0.6, look=(-0.6, -0.2), arms="up", action=0.8)
    A.penguin(Pen(img, 470, 1360, 0.75), "daddy", 0.3, 0.0, look=(0.6, -0.2), arms="up")
    A.duck(Pen(img, 2090, 1370, 0.7), "mommy", 0.3, 0.0, look=(-0.6, -0.2))
    # inside the safe area: baby frog and baby duck framing the name
    A.frog(Pen(img, 680, 920, 0.72), "baby", 0.3, 0.7, look=(0.6, -0.2), arms="up")
    A.duck(Pen(img, 1885, 920, 0.72), "baby", 0.3, 0.7, look=(-0.6, -0.2), arms="up")
    # the name
    name = "Baby Shado"
    size = 180
    fw = [font(size).getlength(ch) / S for ch in name]
    x = 1280 - sum(fw) / 2
    cols = [(250, 90, 60), GOLD, (90, 200, 90), (70, 140, 240), (240, 80, 160), (150, 90, 220)]
    ci = 0
    for i, (ch, cw) in enumerate(zip(name, fw)):
        if ch != " ":
            Pen(img, x + cw / 2, 665 + 12 * math.sin(i * 0.9)).text(0, 0, ch, size, cols[ci % 6], 16)
            ci += 1
        x += cw
    p = Pen(img, 1280, 850)
    p.rect(-420, -48, 420, 48, "white", 8, 48)
    p.text(0, 0, "Kids Songs & Sing-Alongs", 62, (60, 150, 70), 0)
    for sx, sy in ((860, 545), (1700, 545), (790, 800), (1770, 800)):
        star(pen, sx, sy, 30, GOLD)
    return img


if __name__ == "__main__":
    img = build()
    out = img.convert("RGB").reduce(S)
    out.save(os.path.join(HERE, "baby_shado_banner.png"), optimize=True)
    prev = out.copy()
    d = ImageDraw.Draw(prev)
    d.rectangle(SAFE, outline=(255, 0, 0), width=6)
    d.rectangle((0, 0, W - 1, H - 1), outline=(0, 0, 255), width=6)
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    prev.resize((1280, 720)).save(os.path.join(HERE, "build", "banner_guides.png"))
    out.crop(SAFE).save(os.path.join(HERE, "build", "banner_mobile.png"))
    print("ok", os.path.getsize(os.path.join(HERE, "baby_shado_banner.png")) // 1024, "KB")
