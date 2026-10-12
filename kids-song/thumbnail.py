"""YouTube thumbnail (1280x720) for Hop Hop Froggy."""
import math, os
import video as V
from video import Pen, S, font, star, GOLD

img = V.background("day")
pen = Pen(img)
V.sun(pen, 0.3, 1.0)
V.clouds(pen, 3.0)
for kind in V.ORDER:
    if kind != "baby":
        V.frog(Pen(img, V.FROGS[kind][2], V.BACK_Y, V.FROGS[kind][1] * 0.72), kind, 0.3, 0.6, look=(0, -0.3), arms="up")
V.frog(Pen(img, 960, 905 - 120, 0.55 * 2.3), "baby", 0.0, 1.0, look=(0, -0.2), arms="up")
letters = "HOP HOP FROGGY!"
fw = [font(170).getlength(ch) / S for ch in letters]
x = 960 - sum(fw) / 2
cols = [(250, 90, 60), GOLD, (90, 200, 90), (70, 140, 240)]
for i, (ch, cw) in enumerate(zip(letters, fw)):
    if ch != " ":
        Pen(img, x + cw / 2, 190 + 18 * math.sin(i * 0.9)).text(0, 0, ch, 170, cols[i % 4], 16)
    x += cw
Pen(img, 960, 1000).rect(-470, -60, 470, 60, (255, 255, 255), 8, 60)
Pen(img, 960, 1000).text(0, 0, "Froggy Family Song", 76, (60, 150, 70), 0)
for x, y in ((180, 520), (1740, 520), (420, 120), (1500, 110)):
    star(pen, x, y, 34, GOLD)
img.convert("RGB").reduce(S).resize((1280, 720)).save(os.path.join(V.HERE, "thumbnail.png"))
print("ok")
