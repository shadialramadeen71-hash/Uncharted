"""YouTube profile picture (800x800, shown as a circle) for Baby Shado."""
import math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "kids-shorts"))
import animals as A  # noqa: E402
from animals import Pen, S, OUT, GOLD, star  # noqa: E402
from toon import font  # noqa: E402

N = 800


def build():
    img = Image.new("RGBA", (N * S, N * S), (120, 205, 255, 255))
    pen = Pen(img)
    for i in range(16):  # sunburst
        a = i * math.pi / 8
        pen.poly([(400, 470), (400 + math.cos(a) * 900, 470 + math.sin(a) * 900),
                  (400 + math.cos(a + 0.2) * 900, 470 + math.sin(a + 0.2) * 900)], (150, 220, 255), 0)
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    for i, c in enumerate([(240, 60, 60), (250, 150, 40), (250, 230, 60), (90, 200, 90), (70, 140, 240), (150, 90, 220)]):
        r = 380 - i * 26
        od.arc([(400 - r) * S, (560 - r) * S, (400 + r) * S, (560 + r) * S], 180, 360, fill=c + (230,), width=26 * S)
    img.alpha_composite(over)
    pen = Pen(img)
    pen.ell(400, 820, 420, 170, (110, 200, 100), 0)
    A.frog(Pen(img, 400, 815, 1.45), "baby", 0.3, 0.75, look=(0, -0.15), arms="up")
    for sx, sy, r in ((150, 470, 26), (650, 470, 26), (110, 600, 18), (690, 600, 18)):
        star(pen, sx, sy, r, GOLD)
    cols = [(250, 90, 60), GOLD, (90, 200, 90), (70, 140, 240), (240, 80, 160), (150, 90, 220)]
    ci = 0
    for row, y, size in (("BABY", 120, 120), ("SHADO", 235, 120)):
        fw = [font(size).getlength(ch) / S for ch in row]
        x = 400 - sum(fw) / 2
        for ch, cw in zip(row, fw):
            Pen(img, x + cw / 2, y).text(0, 0, ch, size, cols[ci % 6], 14)
            ci += 1; x += cw
    return img


if __name__ == "__main__":
    out = build().convert("RGB").reduce(S)
    out.save(os.path.join(HERE, "baby_shado_profile.png"), optimize=True)
    mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, N - 1, N - 1], fill=255)
    circ = Image.new("RGB", (N, N), "white"); circ.paste(out, mask=mask)
    sheet = Image.new("RGB", (N + 260, N), "white")
    sheet.paste(circ, (0, 0))
    for i, s in enumerate((176, 98, 48)):
        sheet.paste(circ.resize((s, s), Image.LANCZOS), (N + 30, 30 + sum((176, 98, 48)[:i]) + 30 * i))
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    sheet.save(os.path.join(HERE, "build", "profile_check.png"))
    print("ok")
