"""TikTok profile picture (1080x1080) and series cover (1080x1920) for Tank & Zippy."""
import math, os, sys
from PIL import Image, ImageDraw
import toon
from toon import Pen, S, W, H, PURPLE, GOLD, RED, OUT, character, place, star, football
import sets as st


def rays(img, cx, cy, n=16, c=(110, 60, 165)):
    pen = Pen(img)
    for i in range(n):
        a = i * 2 * math.pi / n
        pen.poly([(cx, cy), (cx + math.cos(a) * 2500, cy + math.sin(a) * 2500),
                  (cx + math.cos(a + 0.2) * 2500, cy + math.sin(a + 0.2) * 2500)], c, 0)


def profile():
    size = 1080
    img = Image.new("RGBA", (size * S, size * S), PURPLE + (255,))
    rays(img, 540, 560)
    pen = Pen(img)
    place(img, character("tank", 0.0, False, (0.4, 0), t=0.6), 345, 610 + 523 * 1.55, sc=1.55)
    place(img, character("zippy", 0.7, False, (-0.4, -0.2), arms="up", t=0.0), 765, 640 + 381 * 1.5, sc=1.5)
    for x, y, r in ((150, 380, 30), (940, 360, 26)):
        star(pen, x, y, r, GOLD)
    Pen(img, 540, 170).rect(-300, -62, 300, 62, OUT, 0, 40)
    Pen(img, 540, 170).text(0, 0, "TANK & ZIPPY", 76, GOLD, 8)
    out = img.reduce(S).convert("RGB")
    # preview with the circular crop TikTok applies
    mask = Image.new("L", out.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    prev = Image.new("RGB", out.size, (255, 255, 255)); prev.paste(out, mask=mask)
    return out, prev


def cover():
    img = st.view(st.stadium("night"), 300)
    over = Image.new("RGBA", img.size, (20, 10, 40, 110))
    img.alpha_composite(over)
    img.alpha_composite(Image.new("RGBA", img.size, (60, 25, 100, 120)))
    beams = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(beams)
    for x0, x1 in ((150, 380), (930, 700)):
        bd.polygon([(x0 * S, 0), ((x0 + 60) * S, 0), ((x1 + 250) * S, 1700 * S), ((x1 - 250) * S, 1700 * S)], fill=(255, 240, 180, 50))
    img.alpha_composite(beams)
    pen = Pen(img)
    pen.rect(90, 150, 990, 560, (30, 15, 55), 10, 50)
    Pen(img, 540, 290).text(0, 0, "TANK", 170, GOLD, 14)
    Pen(img, 540, 450).text(0, 0, "& ZIPPY", 150, "white", 14)
    Pen(img, 540, 640).rect(-380, -50, 380, 50, RED, 7, 50)
    Pen(img, 540, 640).text(0, 0, "FUNNY FOOTBALL CARTOON", 50, "white", 0)
    place(img, character("tank", 0.0, False, (0.4, 0), arms="wave", t=0.6), 340, 1560, sc=1.25)
    place(img, character("zippy", 0.8, False, (-0.5, -0.3), arms="flail", ball=True, t=0.1), 790, 1420, sc=1.15, angle=-12, pivot_up=300)
    for x, y, r in ((120, 820, 30), (960, 800, 34), (90, 1300, 22), (1000, 1250, 24)):
        star(pen, x, y, r, GOLD)
    Pen(img, 540, 1740).rect(-400, -70, 400, 70, GOLD, 8, 70)
    Pen(img, 540, 1740).text(0, 0, "SEASON 1 · 8 EPISODES", 56, OUT, 0)
    return img.reduce(S).convert("RGB")


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else toon.HERE
    p, prev = profile()
    p.save(os.path.join(out_dir, "tiktok_profile.png"))
    prev.save(os.path.join(out_dir, "build", "tiktok_profile_circle_preview.png"))
    cover().save(os.path.join(out_dir, "tiktok_cover.png"))
    print("ok")
