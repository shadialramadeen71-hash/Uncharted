import cairo, math, json, subprocess, sys, os
import numpy as np, shapefile
from PIL import Image

W, H, FPS = 1920, 1080, 30
D = os.path.dirname(os.path.abspath(__file__))
FONT = "Inter"
BG = (0.043, 0.051, 0.063)
RED = (0.86, 0.20, 0.18)
AMBER = (0.95, 0.70, 0.25)
WHITE = (0.95, 0.95, 0.93)
GREY = (0.62, 0.65, 0.70)

def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def ramp(t, a, b):
    return ease((t - a) / (b - a)) if b > a else float(t >= a)

# ---------------- text ----------------
def text(cr, s, x, y, size, color=WHITE, alpha=1.0, weight=cairo.FONT_WEIGHT_NORMAL, align="left", spacing=0):
    cr.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, weight)
    cr.set_font_size(size)
    ext = cr.text_extents(s)
    w = ext.x_advance + spacing * len(s)
    if align == "center": x -= w / 2
    elif align == "right": x -= w
    cr.set_source_rgba(*color, alpha)
    if spacing:
        for ch in s:
            cr.move_to(x, y); cr.show_text(ch); x += cr.text_extents(ch).x_advance + spacing
    else:
        cr.move_to(x, y); cr.show_text(s)
    return w

def bold(cr, *a, **k):
    k["weight"] = cairo.FONT_WEIGHT_BOLD
    return text(cr, *a, **k)

def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()

def panel(cr, x, y, w, h, alpha=0.82):
    rrect(cr, x, y, w, h, 10); cr.set_source_rgba(0.05, 0.06, 0.08, alpha); cr.fill()

def lower_third(cr, t, title, sub=None, a=0.4, b=None, dur=None):
    al = ramp(t, a, a + 0.6) * (1 - ramp(t, b - 0.6, b) if b else 1)
    if al <= 0: return
    off = (1 - al) * 30
    y = H - 190
    cr.set_source_rgba(*RED, al); cr.rectangle(110 - off, y, 8, 100 if sub else 64); cr.fill()
    cr.set_source_rgba(0.04, 0.05, 0.06, 0.75 * al); cr.rectangle(118 - off, y, 1000, 100 if sub else 64); cr.fill()
    bold(cr, title, 145 - off, y + 44, 38, alpha=al)
    if sub: text(cr, sub, 145 - off, y + 84, 26, GREY, al)

def vignette(cr, strength=0.65):
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, strength)
    cr.set_source(g); cr.paint()

def grain_bars(cr):
    cr.set_source_rgba(0, 0, 0, 1)

# ---------------- images ----------------
_img = {}
def load(name, crop=None):
    if name not in _img:
        im = Image.open(os.path.join(D, "img", name)).convert("RGBA")
        if crop: im = im.crop(crop)
        a = np.array(im)
        bgra = np.ascontiguousarray(a[:, :, [2, 1, 0, 3]])
        surf = cairo.ImageSurface.create_for_data(memoryview(bgra), cairo.FORMAT_ARGB32, im.width, im.height, im.width * 4)
        _img[name] = (surf, bgra)
    return _img[name][0]

def kenburns(cr, name, t, dur, z0=1.04, z1=1.16, px=(0.5, 0.5), py=(0.5, 0.5), dark=0.35, crop=None):
    s = load(name, crop)
    iw, ih = s.get_width(), s.get_height()
    p = t / dur
    z = z0 + (z1 - z0) * p
    base = max(W / iw, H / ih) * z
    cx = px[0] + (px[1] - px[0]) * p
    cy = py[0] + (py[1] - py[0]) * p
    vw, vh = iw * base, ih * base
    ox = -(vw - W) * cx; oy = -(vh - H) * cy
    cr.save(); cr.translate(ox, oy); cr.scale(base, base)
    cr.set_source_surface(s, 0, 0); cr.get_source().set_filter(cairo.FILTER_GOOD); cr.paint(); cr.restore()
    cr.set_source_rgba(0, 0, 0, dark); cr.paint()
    vignette(cr)

# ---------------- maps ----------------
def merc(lat):
    lat = max(-85, min(85, lat))
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))

def load_shapes(path, filt=None):
    r = shapefile.Reader(path)
    flds = [f[0] for f in r.fields[1:]]
    out = []
    for sr in r.iterShapeRecords():
        rec = dict(zip(flds, sr.record))
        if filt and not filt(rec): continue
        pts = sr.shape.points; parts = list(sr.shape.parts) + [len(pts)]
        polys = []
        for i in range(len(parts) - 1):
            p = np.array(pts[parts[i]:parts[i + 1]], dtype=float)
            if len(p) < 3: continue
            p[:, 1] = np.degrees(np.log(np.tan(np.pi / 4 + np.radians(np.clip(p[:, 1], -85, 85)) / 2)))
            polys.append((p, p[:, 0].min(), p[:, 0].max(), p[:, 1].min(), p[:, 1].max()))
        out.append((rec, polys))
    return out

COUNTRIES = load_shapes(os.path.join(D, "geo/ne_50m_admin_0_countries.shp"))
STATES = load_shapes(os.path.join(D, "geo/ne_50m_admin_1_states_provinces.shp"), lambda r: r.get("adm0_a3") == "USA")

class Cam:
    def __init__(self, lon, lat, scale): self.lon, self.lat, self.s = lon, lat, scale
    def xy(self, lon, lat):
        return (W / 2 + (lon - self.lon) * self.s, H / 2 - (merc(lat) - merc(self.lat)) * self.s)

def cam_lerp(a, b, p):
    p = ease(p)
    ls = math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * p
    # move center in screen-space-consistent way
    return Cam(a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p, math.exp(ls))

def draw_polys(cr, cam, shapes, fill, stroke, lw, highlight=None, hl_fill=None):
    my = merc(cam.lat)
    x0 = cam.lon - W / 2 / cam.s; x1 = cam.lon + W / 2 / cam.s
    y0 = my - H / 2 / cam.s; y1 = my + H / 2 / cam.s
    for rec, polys in shapes:
        hl = highlight is not None and highlight(rec)
        for p, a, b, c, d in polys:
            if b < x0 or a > x1 or d < y0 or c > y1: continue
            xs = W / 2 + (p[:, 0] - cam.lon) * cam.s
            ys = H / 2 - (p[:, 1] - my) * cam.s
            cr.move_to(xs[0], ys[0])
            for i in range(1, len(xs)): cr.line_to(xs[i], ys[i])
            cr.close_path()
            if fill or (hl and hl_fill):
                c_ = hl_fill if hl and hl_fill else fill
                cr.set_source_rgba(*c_); cr.fill_preserve()
            cr.set_source_rgba(*stroke); cr.set_line_width(lw); cr.stroke()

def basemap(cr, cam, hl_state=None, hl_country=None, hl_alpha=1.0):
    cr.set_source_rgb(0.035, 0.055, 0.075); cr.paint()
    # graticule
    cr.set_source_rgba(1, 1, 1, 0.035); cr.set_line_width(1)
    for lon in range(-180, 181, 10):
        x, _ = cam.xy(lon, 0); cr.move_to(x, 0); cr.line_to(x, H)
    for lat in range(-80, 81, 10):
        _, y = cam.xy(0, lat); cr.move_to(0, y); cr.line_to(W, y)
    cr.stroke()
    hlc = (0.30, 0.10, 0.10, 0.9 * hl_alpha)
    draw_polys(cr, cam, COUNTRIES, (0.11, 0.13, 0.16, 1), (0.25, 0.28, 0.33, 1), 1.0,
               (lambda r: r.get("ADM0_A3") == hl_country) if hl_country else None, hlc)
    if cam.s > 6:
        sa = min(1, (cam.s - 6) / 6)
        draw_polys(cr, cam, STATES, None, (0.36, 0.40, 0.46, sa), 1.0)
        if hl_state:
            draw_polys(cr, cam, [s for s in STATES if s[0].get("name") == hl_state], (0.42, 0.11, 0.10, 0.45 * hl_alpha),
                       (0.95, 0.40, 0.35, hl_alpha), 2.0)

def marker(cr, cam, lon, lat, label, t, a=0.0, color=RED, sub=None, side="right", size=30):
    al = ramp(t, a, a + 0.5)
    if al <= 0: return
    x, y = cam.xy(lon, lat)
    pulse = (t * 0.8) % 1.0
    cr.set_source_rgba(*color, 0.5 * (1 - pulse) * al); cr.arc(x, y, 10 + 30 * pulse, 0, 2 * math.pi); cr.fill()
    cr.set_source_rgba(*color, al); cr.arc(x, y, 9, 0, 2 * math.pi); cr.fill()
    cr.set_source_rgba(1, 1, 1, al); cr.set_line_width(2.5); cr.arc(x, y, 9, 0, 2 * math.pi); cr.stroke()
    dx = 24 if side == "right" else -24
    al_ = "left" if side == "right" else "right"
    # shadow for legibility
    for ox, oy in ((2, 2),):
        bold(cr, label, x + dx + ox, y + 10 + oy, size, (0, 0, 0), al * 0.8, align=al_)
    bold(cr, label, x + dx, y + 10, size, WHITE, al, align=al_)
    if sub:
        text(cr, sub, x + dx + 2, y + 10 + size * 1.1 + 2, size * 0.72, (0, 0, 0), al * 0.8, align=al_)
        text(cr, sub, x + dx, y + 10 + size * 1.1, size * 0.72, AMBER, al, align=al_)

def arc_line(cr, cam, a, b, p, color=AMBER, dashed=False, lift=0.25, lw=4):
    if p <= 0: return
    x0, y0 = cam.xy(*a); x1, y1 = cam.xy(*b)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    cx, cy = mx - dy * lift, my + dx * lift * (-1 if dx > 0 else 1) * -1
    cx, cy = mx + dy * lift * (-1 if dx > 0 else 1), my - abs(dx) * lift
    n = 80; k = max(2, int(n * p))
    cr.set_source_rgba(*color, 0.95); cr.set_line_width(lw)
    if dashed: cr.set_dash([14, 10])
    for i in range(k + 1):
        u = i / n
        x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1
        y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1
        (cr.move_to if i == 0 else cr.line_to)(x, y)
    cr.stroke(); cr.set_dash([])
    if p < 1:
        cr.set_source_rgba(1, 1, 1, 1); cr.arc(x, y, 6, 0, 2 * math.pi); cr.fill()

def map_title(cr, t, s, sub=None):
    al = ramp(t, 0.3, 1.0)
    bold(cr, s.upper(), 110, 140, 30, AMBER, al, spacing=4)
    if sub: text(cr, sub, 110, 185, 30, WHITE, al)

# ---------------- places ----------------
FORT_HOOD = (-97.77, 31.14)
AUSTIN = (-97.74, 30.27)
ARLINGTON = (-77.10, 38.88)
WALTER_REED = (-77.03, 38.97)
LEAVENWORTH = (-94.92, 39.35)
YEMEN = (44.21, 15.35)
KABUL = (69.17, 34.53)
WORLD = (-30, 30, 4.2)
USA = (-96, 38.5, 26)
TEXAS = (-99.3, 31.3, 95)
CENTRAL_TX = (-97.9, 30.9, 210)

# ---------------- scenes ----------------
def s01(cr, t, d):
    if t < 11:
        kenburns(cr, "16.jpeg", t, 11, 1.02, 1.12, dark=0.55)
        al = ramp(t, 1.0, 2.2) * (1 - ramp(t, 9.8, 10.8))
        text(cr, "NOVEMBER 5, 2009  ·  KILLEEN, TEXAS", W / 2, 420, 30, AMBER, al, align="center", spacing=6)
        bold(cr, "THE FORT HOOD SHOOTING", W / 2, 530, 104, WHITE, al, align="center")
        cr.set_source_rgba(*RED, al); cr.rectangle(W / 2 - 80, 575, 160, 5); cr.fill()
        text(cr, "13 killed  ·  more than 30 wounded  ·  about 10 minutes", W / 2, 650, 34, GREY, al, align="center")
    elif t < 21:
        u = t - 11
        cr.set_source_rgb(*BG); cr.paint()
        s = load("mug.jpg", (0, 0, 262, 287))
        sc = 2.85 + 0.15 * u / 10
        iw, ih = 262 * sc, 287 * sc
        al = ramp(u, 0, 0.8)
        cr.save(); cr.translate(W * 0.33 - iw / 2, H / 2 - ih / 2); cr.scale(sc, sc)
        cr.set_source_surface(s, 0, 0); cr.get_source().set_filter(cairo.FILTER_BEST); cr.paint_with_alpha(al); cr.restore()
        x = W * 0.58
        a2 = ramp(u, 1.0, 1.8)
        text(cr, "THE GUNMAN", x, 400, 28, AMBER, a2, spacing=6)
        bold(cr, "Nidal Malik Hasan", x, 480, 72, WHITE, a2)
        lines = ["U.S. Army Major", "Psychiatrist", "Born 1970 · Arlington, Virginia"]
        for i, l in enumerate(lines):
            text(cr, l, x, 560 + i * 52, 36, GREY, ramp(u, 2 + i * 0.6, 2.8 + i * 0.6))
        vignette(cr, 0.5)
    else:
        u = t - 21
        kenburns(cr, "02.jpeg", u, d - 21, 1.0, 1.1, px=(0.3, 0.6), dark=0.35)
        lower_third(cr, u, "Fort Hood, Texas", "Ambulances outside the Soldier Readiness Processing Center", 0.6)

def s02(cr, t, d):
    k = [(0, WORLD), (5, USA), (9, TEXAS), (13, CENTRAL_TX)]
    cam = None
    for i in range(len(k) - 1):
        if t <= k[i + 1][0]:
            cam = cam_lerp(k[i][1], k[i + 1][1], (t - k[i][0]) / (k[i + 1][0] - k[i][0])); break
    if cam is None: cam = Cam(*CENTRAL_TX)
    basemap(cr, cam, hl_state="Texas", hl_country="USA" if t < 7 else None, hl_alpha=ramp(t, 6, 9))
    if t > 10: marker(cr, cam, *AUSTIN, "Austin", t, 10.5, GREY, size=26)
    if t > 9: marker(cr, cam, *FORT_HOOD, "Fort Hood", t, 9.5, RED, sub="Near Killeen, Central Texas")
    map_title(cr, t, "Location", "Fort Hood, Texas")
    vignette(cr, 0.5)

def s03(cr, t, d):
    cam_a = (-87, 37, 34)
    cam = cam_lerp(cam_a, (-87.5, 35.5, 30), t / d)
    basemap(cr, cam, hl_state="Virginia", hl_alpha=ramp(t, 0.5, 2) * (1 - ramp(t, 9, 11)))
    marker(cr, cam, *ARLINGTON, "Arlington, VA", t, 1.0, AMBER, sub="Born 1970", side="left", size=28)
    marker(cr, cam, *WALTER_REED, "Walter Reed", t, 12.5, RED, sub="2003 – 2009", size=28)
    if t > 17: marker(cr, cam, *FORT_HOOD, "Fort Hood", t, 17.5, RED, sub="July 2009", size=28)
    arc_line(cr, cam, WALTER_REED, FORT_HOOD, ramp(t, 17, 21))
    map_title(cr, t, "Background", "Nidal Malik Hasan")
    items = [("1970", "Born in Arlington, Virginia", 1.5), ("1988", "Enlists in the U.S. Army", 6.5),
             ("2003", "Graduates military medical school", 9.5), ("2003–09", "Psychiatry training, Walter Reed", 13)]
    panel(cr, 1170, 640, 640, 320, 0.8 * ramp(t, 1, 1.6))
    for i, (y, s, a) in enumerate(items):
        al = ramp(t, a, a + 0.6)
        bold(cr, y, 1200, 700 + i * 72, 32, AMBER, al)
        text(cr, s, 1360, 700 + i * 72, 28, WHITE, al)
    vignette(cr, 0.45)

def s04(cr, t, d):
    cam = cam_lerp((-50, 35, 8), (-15, 30, 5.2), ramp(t, 0, 6))
    basemap(cr, cam, hl_country="YEM", hl_alpha=ramp(t, 5, 7))
    marker(cr, cam, *WALTER_REED, "Washington, D.C.", t, 0.5, RED, side="left", sub="Hasan · Walter Reed", size=28)
    marker(cr, cam, *YEMEN, "Yemen", t, 7, AMBER, sub="Anwar al-Awlaki", size=28)
    arc_line(cr, cam, WALTER_REED, YEMEN, ramp(t, 6, 11), AMBER, dashed=True, lift=0.18)
    map_title(cr, t, "Warning signs", "Emails to a radical cleric")
    al = ramp(t, 9, 10)
    panel(cr, 1300, 700, 520, 250, 0.85 * al)
    n = int(min(20, max(0, (t - 9.5) * 4)))
    w = bold(cr, f"~{n}", 1340, 820, 96, AMBER, al)
    text(cr, "emails", 1340 + w + 20, 820, 36, WHITE, al)
    text(cr, "Dec 2008 – Jun 2009", 1340, 880, 30, GREY, al)
    al2 = ramp(t, 19, 20)
    panel(cr, 110, 820, 1000, 120, 0.85 * al2)
    bold(cr, "FBI-led task force review:", 140, 868, 30, RED, al2)
    text(cr, "no further action taken", 140, 912, 30, WHITE, al2)
    vignette(cr, 0.45)

def s05(cr, t, d):
    cam = cam_lerp((-97.6, 31.0, 300), (-20, 32, 4.4), ramp(t, 4, 11))
    basemap(cr, cam, hl_state="Texas", hl_country="AFG", hl_alpha=1)
    marker(cr, cam, *FORT_HOOD, "Fort Hood", t, 0.3, RED, sub="Arrives July 2009", size=28)
    marker(cr, cam, *KABUL, "Afghanistan", t, 10, AMBER, sub="Planned deployment", side="left", size=28)
    arc_line(cr, cam, FORT_HOOD, KABUL, ramp(t, 9, 13), AMBER, dashed=True, lift=0.15)
    map_title(cr, t, "2009", "Transfer to Fort Hood")
    al = ramp(t, 12.5, 13.3)
    panel(cr, 110, 820, 820, 120, 0.85 * al)
    bold(cr, "August 2009", 140, 868, 30, AMBER, al)
    text(cr, "Buys an FN Five-seven pistol near the base", 140, 912, 30, WHITE, al)
    vignette(cr, 0.45)

def s06(cr, t, d):
    cr.set_source_rgb(*BG); cr.paint()
    s = load("12.png")
    iw, ih = s.get_width(), s.get_height()
    dot = (0.2353 * iw, 0.2643 * ih)
    z0 = 1.55; z1 = 3.2
    z = z0 * (z1 / z0) ** ease(ramp(t, 2, 11))
    fx = (W / 2 - iw * z0 / 2) * (1 - ramp(t, 2, 11)) + (W / 2 - dot[0] * z1) * ramp(t, 2, 11)
    # center on dot progressively
    cxp = iw / 2 + (dot[0] - iw / 2) * ease(ramp(t, 2, 11))
    cyp = ih / 2 + (dot[1] - ih / 2) * ease(ramp(t, 2, 11))
    cr.save(); cr.translate(W / 2 - cxp * z, H / 2 - cyp * z); cr.scale(z, z)
    cr.set_source_rgb(0.93, 0.92, 0.88); cr.rectangle(0, 0, iw, ih); cr.fill()
    cr.set_source_surface(s, 0, 0); cr.get_source().set_filter(cairo.FILTER_GOOD); cr.paint(); cr.restore()
    x, y = W / 2 + (dot[0] - cxp) * z, H / 2 + (dot[1] - cyp) * z
    pulse = (t * 0.9) % 1
    cr.set_source_rgba(*RED, 0.6 * (1 - pulse)); cr.arc(x, y, 12 + 60 * pulse, 0, 2 * math.pi); cr.fill()
    cr.set_source_rgba(0, 0, 0, 0.25); cr.paint()
    al = ramp(t, 4, 5)
    panel(cr, x + 60, y - 60, 720, 130, 0.9 * al)
    bold(cr, "Soldier Readiness Processing Center", x + 90, y - 10, 32, WHITE, al)
    text(cr, "Medical checks before deployment", x + 90, y + 40, 28, GREY, al)
    # clock
    al2 = ramp(t, 10.5, 11.5)
    panel(cr, 110, 110, 440, 170, 0.9 * al2)
    text(cr, "NOVEMBER 5, 2009", 140, 160, 24, AMBER, al2, spacing=4)
    bold(cr, "≈ 1:34 PM", 140, 245, 72, WHITE, al2)
    text(cr, "Base map: U.S. Army", W - 40, H - 30, 20, GREY, 0.8, align="right")
    vignette(cr, 0.5)

def s07(cr, t, d):
    if t < 9:
        kenburns(cr, "04.jpeg", t, 9, 1.0, 1.12, px=(0.4, 0.6), dark=0.3)
        lower_third(cr, t, "Taking cover", "Soldiers and police during the attack · Nov 5, 2009", 0.5, 8.8)
    else:
        u = t - 9
        kenburns(cr, "14.jpeg", u, d - 9, 1.0, 1.1, px=(0.3, 0.5), dark=0.55)
        people = [("Capt. John Gaffaney", "Charged the gunman · killed", 0.8),
                  ("Michael Cahill", "Civilian physician assistant · charged with a chair · killed", 4.5),
                  ("Spc. Logan Burnett", "Threw a table at the gunman · wounded", 9.5)]
        panel(cr, 110, 540, 1250, 400, 0.8 * ramp(u, 0.4, 1))
        text(cr, "THOSE WHO FOUGHT BACK", 145, 600, 26, AMBER, ramp(u, 0.4, 1), spacing=5)
        for i, (n, s, a) in enumerate(people):
            al = ramp(u, a, a + 0.6)
            bold(cr, n, 145, 680 + i * 100, 40, WHITE, al)
            text(cr, s, 145, 720 + i * 100, 26, GREY, al)

def s08(cr, t, d):
    if t < 12:
        kenburns(cr, "01.jpeg", t, 12, 1.0, 1.12, px=(0.5, 0.3), dark=0.35)
        lower_third(cr, t, "Base police respond", "Officers arrive within minutes", 0.5, 11.8)
    else:
        u = t - 12
        kenburns(cr, "00.jpeg", u, d - 12, 1.02, 1.12, px=(0.6, 0.4), dark=0.6)
        steps = [("≈ 1:34 PM", "First shots inside the processing center", 0.3),
                 ("Minutes later", "Sgt. Kimberly Munley exchanges fire · wounded", 1.5),
                 ("≈ 1:44 PM", "Sgt. Mark Todd shoots Hasan", 5.5),
                 ("", "Weapon kicked away · Hasan handcuffed", 9.0)]
        panel(cr, 110, 330, 1100, 520, 0.8 * ramp(u, 0, 0.6))
        text(cr, "HOW THE ATTACK WAS STOPPED", 145, 395, 26, AMBER, ramp(u, 0, 0.6), spacing=5)
        for i, (a_, b_, s) in enumerate(steps):
            al = ramp(u, s, s + 0.6)
            cy = 470 + i * 95
            cr.set_source_rgba(*(RED if i >= 2 else AMBER), al); cr.arc(160, cy - 10, 10, 0, 2 * math.pi); cr.fill()
            if i < 3:
                cr.set_source_rgba(1, 1, 1, 0.25 * al); cr.set_line_width(2); cr.move_to(160, cy + 5); cr.line_to(160, cy + 80); cr.stroke()
            bold(cr, a_, 195, cy, 32, WHITE, al)
            text(cr, b_, 195 + (260 if a_ else 0), cy, 30, GREY if a_ else WHITE, al)

def s09(cr, t, d):
    cr.set_source_rgb(*BG); cr.paint()
    s = load("mug.jpg", (0, 0, 262, 287))
    sc = 3.0 + 0.2 * t / d
    cr.save(); cr.translate(W * 0.33 - 131 * sc, H / 2 - 143.5 * sc); cr.scale(sc, sc)
    cr.set_source_surface(s, 0, 0); cr.get_source().set_filter(cairo.FILTER_BEST); cr.paint(); cr.restore()
    x = W * 0.58
    items = [("Shot by police", 0.5), ("Paralyzed from the waist down", 3.5), ("Held in Bell County jail", 8.5), ("Awaiting trial", 10.5)]
    text(cr, "IN CUSTODY", x, 400, 28, AMBER, ramp(t, 0.2, 0.8), spacing=6)
    for i, (s_, a) in enumerate(items):
        al = ramp(t, a, a + 0.6)
        cr.set_source_rgba(*RED, al); cr.rectangle(x, 455 + i * 70, 6, 40); cr.fill()
        text(cr, s_, x + 26, 488 + i * 70, 38, WHITE, al)
    vignette(cr, 0.5)

def s10(cr, t, d):
    kenburns(cr, "08.jpeg", t, d, 1.0, 1.12, px=(0.4, 0.5), dark=0.5)
    lower_third(cr, t, "Lt. Gen. Robert Cone briefs reporters", "Fort Hood · November 6, 2009", 0.5, 9)
    al = ramp(t, 13, 13.8)
    panel(cr, W - 900, 300, 790, 400, 0.88 * al)
    text(cr, "CHARGES", W - 860, 370, 26, AMBER, al, spacing=6)
    bold(cr, "13", W - 860, 480, 96, RED, al)
    text(cr, "counts of premeditated murder", W - 720, 470, 30, WHITE, al)
    a2 = ramp(t, 18.5, 19.3)
    bold(cr, "32", W - 860, 630, 96, RED, a2)
    text(cr, "counts of attempted murder", W - 720, 620, 30, WHITE, a2)

def s11(cr, t, d):
    kenburns(cr, "15.jpeg", t, d, 1.05, 1.15, dark=0.7)
    text(cr, "COURT-MARTIAL · FORT HOOD", W / 2, 200, 28, AMBER, ramp(t, 0.3, 1), align="center", spacing=6)
    cards = [("AUG 6, 2013", "Trial begins", "Hasan represents himself", 0.8),
             ("AUG 23, 2013", "Guilty", "on all 45 counts", 15.0),
             ("AUG 28, 2013", "Death sentence", "by a military jury", 20.5)]
    for i, (dte, h, s, a) in enumerate(cards):
        al = ramp(t, a, a + 0.7); x = 150 + i * 560; off = (1 - al) * 40
        panel(cr, x, 330 + off, 500, 420, 0.85 * al)
        cr.set_source_rgba(*(RED if i else AMBER), al); cr.rectangle(x, 330 + off, 500, 8); cr.fill()
        text(cr, dte, x + 40, 420 + off, 28, AMBER, al, spacing=3)
        bold(cr, h, x + 40, 530 + off, 58, WHITE, al)
        text(cr, s, x + 40, 600 + off, 30, GREY, al)
    al = ramp(t, 6, 6.8)
    text(cr, "“The evidence will clearly show that I am the shooter.” — Hasan, opening statement",
         W / 2, 880, 30, WHITE, al * (1 - ramp(t, 14, 14.8)), align="center")

def s12(cr, t, d):
    if t < 13:
        cam = cam_lerp((-97, 35, 60), (-96.3, 35.6, 56), t / 13)
        basemap(cr, cam, hl_state="Kansas", hl_alpha=ramp(t, 2, 3.5))
        marker(cr, cam, *FORT_HOOD, "Fort Hood", t, 0.3, GREY, size=28)
        marker(cr, cam, *LEAVENWORTH, "Fort Leavenworth, Kansas", t, 2.5, RED, sub="U.S. Disciplinary Barracks · military death row", size=30)
        arc_line(cr, cam, FORT_HOOD, LEAVENWORTH, ramp(t, 1, 3.5), RED, lift=0.2)
        map_title(cr, t, "Death row", "Where Hasan is held")
        vignette(cr, 0.45)
    else:
        u = t - 13
        kenburns(cr, "13.jpeg", u, d - 13, 1.0, 1.1, px=(0.6, 0.5), dark=0.3)
        lower_third(cr, u, "Purple Heart awarded", "Families of the fallen receive the medal · 2015", 0.5)

def s13(cr, t, d):
    cr.set_source_rgb(*BG); cr.paint()
    text(cr, "THE CASE TODAY", 110, 150, 28, AMBER, ramp(t, 0.2, 0.8), spacing=6)
    items = [("2013", "Sentenced to death", 0.3),
             ("2023", "Military's highest court upholds sentence", 3.0),
             ("Mar 2025", "U.S. Supreme Court declines the case", 7.0),
             ("Oct 2026", "President approves the execution", 11.0),
             ("Dec 3, 2026", "Scheduled: firing squad at Fort Hood", 14.5)]
    x0, x1, y = 200, W - 200, 520
    prog = ramp(t, 0.3, 16)
    cr.set_source_rgba(1, 1, 1, 0.15); cr.set_line_width(4); cr.move_to(x0, y); cr.line_to(x1, y); cr.stroke()
    cr.set_source_rgba(*RED, 1); cr.move_to(x0, y); cr.line_to(x0 + (x1 - x0) * prog, y); cr.stroke()
    for i, (dte, s, a) in enumerate(items):
        al = ramp(t, a, a + 0.6)
        x = x0 + (x1 - x0) * i / (len(items) - 1)
        last = i == len(items) - 1
        cr.set_source_rgba(*(RED if last else WHITE), al); cr.arc(x, y, 14 if last else 10, 0, 2 * math.pi); cr.fill()
        up = i % 2 == 0
        bold(cr, dte, x, y + (-70 if up else 90), 36, AMBER if not last else RED, al, align="center")
        words = s.split(" "); l1 = " ".join(words[:len(words) // 2 + 1]); l2 = " ".join(words[len(words) // 2 + 1:])
        text(cr, l1, x, y + (-170 if up else 140), 26, WHITE, al, align="center")
        text(cr, l2, x, y + (-136 if up else 174), 26, WHITE, al, align="center")
    al = ramp(t, 20, 21)
    panel(cr, 360, 790, W - 720, 150, 0.9 * al)
    text(cr, "Would be the first U.S. military execution since 1961", W / 2, 850, 34, WHITE, al, align="center")
    a2 = ramp(t, 27, 28)
    text(cr, "Civilian federal appeals could still delay it for years", W / 2, 905, 30, AMBER, a2, align="center")

VICTIMS = ["Michael Grant Cahill", "Maj. Libardo Eduardo Caraveo", "Staff Sgt. Justin Michael DeCrow",
           "Capt. John Paul Gaffaney", "Spc. Frederick Greene", "Spc. Jason Dean Hunt",
           "Staff Sgt. Amy Sue Krueger", "Pfc. Aaron Thomas Nemelka", "Pfc. Michael Scott Pearson",
           "Capt. Russell Gilbert Seager", "Pfc. Francheska Velez", "Lt. Col. Juanita Lee Warman",
           "Pfc. Kham See Xiong"]

def s14(cr, t, d):
    kenburns(cr, "09.jpeg", t, d, 1.0, 1.12, px=(0.5, 0.4), dark=0.72)
    al = ramp(t, 0.3, 1.2)
    text(cr, "IN MEMORY", W / 2, 170, 30, AMBER, al, align="center", spacing=8)
    for i, n in enumerate(VICTIMS):
        col, row = (0, i) if i < 7 else (1, i - 7)
        x = W / 2 - 420 if col == 0 else W / 2 + 420
        a = ramp(t, 1.0 + i * 0.75, 1.8 + i * 0.75)
        text(cr, n, x, 280 + row * 78, 36, WHITE, a, align="center")
    a2 = ramp(t, 11, 12)
    text(cr, "and the unborn child of Pfc. Francheska Velez", W / 2 + 420, 280 + 6 * 78, 28, GREY, a2, align="center")

def credits(cr, t, d):
    cr.set_source_rgb(0, 0, 0); cr.paint()
    al = ramp(t, 0.3, 1.2) * (1 - ramp(t, d - 1.5, d - 0.2))
    lines = [("CREDITS", AMBER, 28, True),
             ("Photos: U.S. Army / U.S. Department of Defense (public domain), via Wikimedia Commons", WHITE, 26, False),
             ("Map data: Natural Earth (public domain)", WHITE, 26, False),
             ("Music: “Lightless Dawn” by Kevin MacLeod (incompetech.com)", WHITE, 26, False),
             ("Licensed under Creative Commons: By Attribution 4.0 — creativecommons.org/licenses/by/4.0/", GREY, 24, False),
             ("Narration: AI-generated voice", WHITE, 26, False),
             ("Sources: AP, Military Times, U.S. Senate report (2011), court records", GREY, 24, False)]
    for i, (s, c, sz, b) in enumerate(lines):
        (bold if b else text)(cr, s, W / 2, 360 + i * 66, sz, c, al, align="center")

SCENES = {k: globals()[k] for k in ["s01", "s02", "s03", "s04", "s05", "s06", "s07", "s08", "s09", "s10", "s11", "s12", "s13", "s14"]}
SCENES["credits"] = credits

def render(name, dur, out):
    fn = SCENES[name]
    n = int(round(dur * FPS))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        cr = cairo.Context(surf)
        cr.set_source_rgb(*BG); cr.paint()
        fn(cr, t, dur)
        # fade in/out from black
        f = min(1, t / 0.5, (dur - t) / 0.5)
        if f < 1: cr.set_source_rgba(0, 0, 0, 1 - max(0, f)); cr.paint()
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    name, dur, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    if len(sys.argv) > 4:  # preview single frame
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); cr = cairo.Context(surf)
        cr.set_source_rgb(*BG); cr.paint(); SCENES[name](cr, float(sys.argv[4]), dur); surf.write_to_png(out)
    else:
        render(name, dur, out)
