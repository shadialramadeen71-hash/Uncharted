"""Build timeline, mix audio, render frames in parallel, mux final MP4.
usage: python3 -I render.py <scratch dir> <out.mp4> [--preview SECONDS_LIST]"""
import sys, os, json, math, subprocess, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from scipy.io import wavfile

S = sys.argv[1]; OUT = sys.argv[2]
sys.path.insert(0, S); sys.path.insert(0, S + "/tools")
from script import SEGMENTS
from owl import make_owl

W, H, FPS, SR = 1920, 1080, 30, 44100
GAP = 0.32
INTRO = 3.2
CREDITS = 7.0
XFADE = 0.35
MEDIA = S + "/media"
FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
_fonts = {}
def font(path, size):
    k = (path, size)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]

# real speech in the archival clip (seconds in source video), from pause detection
CLIP_SRC = (5.6, 25.9)
CLIP_LINES = [(6.1, 6.6, "Good evening."),
              (7.9, 11.8, "Tonight, I can report to the American people and to the world"),
              (12.3, 18.4, "that the United States has conducted an operation that killed Osama bin Laden,"),
              (18.9, 25.5, "the leader of al Qaeda, and a terrorist who's responsible for the murder of thousands of innocent men, women, and children.")]
VINSON_SRC = 42.0
MUSIC_A, MUSIC_B, MUSIC_SWITCH_SEG = "Hitman", "Volatile_Reaction", 15

CREDIT_LINES = [
    "Photos & video: Wikimedia Commons. Public domain unless noted:",
    "WTC on 9/11 - Michael Foran (CC BY 2.0)   |   Osama bin Laden - Hamid Mir (CC BY-SA 3.0)",
    "Pakistan map - Carport (CC BY-SA 3.0)   |   Abbottabad - Wasim 5560 (CC BY-SA 4.0)",
    "PMA Gate - Hassanpak30 (CC BY-SA 3.0)   |   Compound photos - Sajjad Ali Qureshi (CC BY-SA 2.0 / CC BY 2.0)",
    "Times Square - Josh Pesavento (CC BY 2.0)   |   Washington DC - Bektour (CC BY-SA 3.0)",
    "9/11 Memorial - Paul Sableman (CC BY 2.0)   |   White House, U.S. Navy, U.S. Army, CIA, FBI, FEMA, NASA",
    "Music: \"Hitman\" & \"Volatile Reaction\" by Kevin MacLeod (incompetech.com), CC BY 4.0   |   Voices: Piper TTS",
]

# ---------------------------------------------------------------- audio helpers
def read_wav(p):
    sr, a = wavfile.read(p)
    a = a.astype(np.float32) / 32768.0
    if a.ndim > 1: a = a.mean(1)
    assert sr == SR, (p, sr)
    return a

def speech_spans(a, thr_db=-38, min_pause=0.16):
    """Return list of (start,end) seconds of speech separated by pauses >= min_pause."""
    hop = int(0.01 * SR)
    n = len(a) // hop
    e = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2)) + 1e-9 for i in range(n)])
    on = 20 * np.log10(e) > thr_db
    spans = []; s = None; last = None
    for i, v in enumerate(on):
        if v:
            if s is None: s = i
            elif last is not None and (i - last) * 0.01 >= min_pause:
                spans.append((s * 0.01, (last + 1) * 0.01)); s = i
            last = i
    if s is not None: spans.append((s * 0.01, (last + 1) * 0.01))
    return spans

def word_times(text, a):
    """Estimate (word, start, end) per word aligned to speech phrases in audio a."""
    words = text.split()
    # phrases split after punctuation
    phrases = []; cur = []
    for w in words:
        cur.append(w)
        if re.search(r"[,.!?:;]$", w): phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    spans = speech_spans(a)
    if not spans: spans = [(0, len(a) / SR)]
    # merge spans until counts match (merge smallest gaps first)
    while len(spans) > len(phrases):
        gaps = [spans[i + 1][0] - spans[i][1] for i in range(len(spans) - 1)]
        i = int(np.argmin(gaps)); spans[i:i + 2] = [(spans[i][0], spans[i + 1][1])]
    out = []
    if len(spans) == len(phrases):
        groups = list(zip(phrases, spans))
    else:  # fewer pauses than punctuation -> proportional over whole speech
        groups = [(words, (spans[0][0], spans[-1][1]))]
    for ws, (s, e) in groups:
        wts = [len(re.sub(r"[^\w$%]", "", w)) + 2 for w in ws]
        tot = sum(wts); t = s
        for w, k in zip(ws, wts):
            d = (e - s) * k / tot
            out.append((w, t, t + d)); t += d
    return out

def envelope(a, fps=FPS):
    hop = SR // fps
    n = len(a) // hop + 1
    e = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(a) else 0 for i in range(n)])
    return e

# ---------------------------------------------------------------- timeline
def build():
    t = INTRO
    segs = []
    voice_items = []
    for i, (sp, text, vis, tag, kw) in enumerate(SEGMENTS):
        if sp == "CLIP":
            dur = CLIP_SRC[1] - CLIP_SRC[0]
            words = []
            for (s, e, line) in CLIP_LINES:
                ws = line.split(); wts = [len(w) + 2 for w in ws]; tot = sum(wts); tt = s
                for w, k in zip(ws, wts):
                    d = (e - s) * k / tot; words.append((w, tt - CLIP_SRC[0], tt - CLIP_SRC[0] + d)); tt += d
            segs.append(dict(i=i, sp=sp, start=t, dur=dur, vis=vis, tag=tag, kw=kw, words=words, text=" ".join(l for _, _, l in CLIP_LINES)))
            t += dur + 0.15
            continue
        p = f"{S}/audio/seg{i:02d}.wav"
        a = read_wav(p)
        dur = len(a) / SR
        segs.append(dict(i=i, sp=sp, start=t, dur=dur + GAP, vis=vis, tag=tag, kw=kw, words=word_times(text, a), text=text, wav=p))
        voice_items.append((t, p, sp))
        t += dur + GAP
    total = t + CREDITS
    # flattened visual items
    items = []
    for sg in segs:
        n = len(sg["vis"])
        for k, v in enumerate(sg["vis"]):
            s = sg["start"] + sg["dur"] * k / n
            e = sg["start"] + sg["dur"] * (k + 1) / n
            items.append(dict(name=v, start=s, end=e, seg=sg["i"], sp=sg["sp"]))
    items.insert(0, dict(name="INTRO", start=0, end=INTRO, seg=-1, sp=""))
    items.append(dict(name="CREDITS", start=t, end=total, seg=-2, sp=""))
    # video source offsets
    for it in items:
        if it["name"] == "vid_obama":
            sg = next(x for x in segs if x["i"] == it["seg"])
            it["src0"] = CLIP_SRC[0] if sg["sp"] == "CLIP" else CLIP_SRC[0] - (it["end"] - it["start"])
        if it["name"] == "vid_vinson":
            it["src0"] = VINSON_SRC
    return segs, items, total, voice_items

# ---------------------------------------------------------------- audio mix
def mix_audio(segs, total, voice_items, path):
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32); cartoon = np.zeros(n, np.float32); clip = np.zeros(n, np.float32)
    for (t, p, sp) in voice_items:
        a = read_wav(p); i = int(t * SR)
        (cartoon if sp == "C" else voice)[i:i + len(a)] += a
    sg = next(x for x in segs if x["sp"] == "CLIP")
    raw = f"{S}/audio/clip_obama.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(CLIP_SRC[0]), "-t", str(CLIP_SRC[1] - CLIP_SRC[0]), "-i", f"{MEDIA}/vid_obama.webm",
                    "-af", "loudnorm=I=-16:TP=-1.5,afade=t=in:d=0.15,afade=t=out:st=%f:d=0.3" % (CLIP_SRC[1] - CLIP_SRC[0] - 0.3), "-ar", str(SR), "-ac", "1", raw], check=True)
    a = read_wav(raw); i = int(sg["start"] * SR); clip[i:i + len(a)] += a
    # music: Kevin MacLeod tracks (CC BY 4.0), suspense -> action at the SEAL Team Six section
    music = np.zeros(n, np.float32)
    switch = next(x for x in segs if x["i"] == MUSIC_SWITCH_SEG)["start"]
    XF = 2.5
    for (fn, t0, t1, src0) in ((MUSIC_A, 0.0, switch + XF, 0.0), (MUSIC_B, switch, total, 0.0)):
        tmpm = f"{S}/audio/{fn}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(src0), "-t", str(t1 - t0 + 1), "-i", f"{S}/music/{fn}.mp3",
                        "-af", "loudnorm=I=-16:TP=-2", "-ar", str(SR), "-ac", "1", tmpm], check=True)
        m = read_wav(tmpm)[:int((t1 - t0) * SR)]
        env = np.ones(len(m), np.float32)
        f = int(XF * SR)
        if t0 > 0: env[:f] = np.linspace(0, 1, f)
        if t1 < total: env[-f:] = np.minimum(env[-f:], np.linspace(1, 0, f))
        else: env[-int(4 * SR):] = np.minimum(env[-int(4 * SR):], np.linspace(1, 0, int(4 * SR)))
        i = int(t0 * SR); music[i:i + len(m)] += (m * env)[:n - i]
    # ducking envelope
    act = np.abs(voice + cartoon)
    hop = 441
    blocks = np.array([act[j:j + hop].max() for j in range(0, n, hop)])
    speaking = np.convolve(blocks > 0.02, np.ones(60), "same") > 0  # within ~0.3s of speech
    clipon = np.zeros(len(blocks), bool)
    clipon[int(sg["start"] * 100):int((sg["start"] + sg["dur"]) * 100)] = True
    target = np.where(clipon, 0.07, np.where(speaking, 0.26, 0.75))
    g = np.zeros_like(target); cur = 0.75
    for j, v in enumerate(target):
        cur += (v - cur) * (0.25 if v < cur else 0.03); g[j] = cur
    gain = np.repeat(g, hop)[:n]
    out = voice * 1.0 + cartoon * 1.0 + clip * 0.95 + music * gain
    out = out / max(1e-6, np.max(np.abs(out))) * 0.9
    tmp = path + ".pre.wav"
    wavfile.write(tmp, SR, (out * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", str(SR), "-ac", "2", path], check=True)
    return cartoon

# ---------------------------------------------------------------- visuals
_cache = {}
def prepared(name):
    """2112x1188 canvas for Ken Burns."""
    if name in _cache: return _cache[name]
    CW, CH = 2112, 1188
    fn = next(f for f in os.listdir(MEDIA) if f.rsplit(".", 1)[0] == name)
    im = Image.open(f"{MEDIA}/{fn}").convert("RGB")
    ar = im.width / im.height
    def cover(img, w, h):
        r = max(w / img.width, h / img.height)
        img = img.resize((max(w, int(img.width * r + 1)), max(h, int(img.height * r + 1))), Image.LANCZOS)
        x = (img.width - w) // 2; y = (img.height - h) // 2
        return img.crop((x, y, x + w, y + h))
    if 1.4 <= ar <= 2.2:
        c = cover(im, CW, CH)
    else:
        bg = cover(im, CW // 4, CH // 4).filter(ImageFilter.GaussianBlur(8)).resize((CW, CH), Image.BILINEAR)
        bg = ImageEnhance.Brightness(bg).enhance(0.45)
        r = min(CW * 0.9 / im.width, CH * 0.9 / im.height)
        fg = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
        sh = Image.new("RGBA", (fg.width + 80, fg.height + 80), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle((40, 40, fg.width + 40, fg.height + 40), fill=(0, 0, 0, 170))
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        bg = bg.convert("RGBA")
        x = (CW - fg.width) // 2; y = (CH - fg.height) // 2
        bg.alpha_composite(sh, (x - 40, y - 30))
        bg = bg.convert("RGB"); bg.paste(fg, (x, y))
        c = bg
    c = ImageEnhance.Contrast(c).enhance(1.06)
    _cache[name] = c
    return c

def kenburns(name, p, variant):
    c = prepared(name)
    e = p * p * (3 - 2 * p) if 0 <= p <= 1 else max(0, min(1.15, p))
    zin = variant % 2 == 0
    z = 0.08 * (e if zin else 1 - e)
    cw = c.width * (1 - z) / 1.0; ch = cw * 9 / 16
    cw = min(cw, c.width); ch = min(ch, c.height)
    dirx = [-1, 1, 0, 1][variant % 4]; diry = [0, -1, 1, 1][variant % 4]
    cx = c.width / 2 + dirx * (c.width - cw) / 2 * (e - 0.5) * 1.6
    cy = c.height / 2 + diry * (c.height - ch) / 2 * (e - 0.5) * 1.6
    cx = min(max(cx, cw / 2), c.width - cw / 2); cy = min(max(cy, ch / 2), c.height - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return c.resize((W, H), Image.BILINEAR, box=box)

def video_frame(name, src_t):
    d = f"{S}/frames/{name}"
    idx = int(round(src_t * FPS)) + 1
    files = sorted(os.listdir(d)) if name not in _cache else _cache[name]
    _cache[name] = files
    off = int(files[0].split(".")[0].split("_")[1])  # first frame number corresponds to its source frame
    k = min(max(idx - off, 0), len(files) - 1)
    return Image.open(f"{d}/{files[k]}").convert("RGB")

_vig = None
def vignette():
    global _vig
    if _vig is None:
        y, x = np.mgrid[0:H, 0:W]
        r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        a = np.clip((r - 0.75) / 0.7, 0, 1) ** 1.6 * 150
        _vig = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), a.astype(np.uint8)]), "RGBA")
    return _vig

def text_w(f, s):
    return f.getlength(s)

def draw_outline_text(d, xy, s, f, fill, stroke=8, sfill=(0, 0, 0), anchor="la"):
    d.text(xy, s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill, anchor=anchor)

def subtitle_chunks(words, maxw, f):
    """Group words into lines that fit maxw, breaking preferably at punctuation."""
    chunks = []; cur = []
    for k, (w, s, e) in enumerate(words):
        test = " ".join(x[0] for x in cur + [(w, s, e)])
        if cur and (text_w(f, test) > maxw or len(cur) >= 9):
            chunks.append(cur); cur = []
        cur.append((w, s, e))
        if re.search(r"[.!?:]$", w) and len(cur) >= 3:
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return chunks

def draw_subs(img, words, lt, cx, y, maxw, size=56, box=False):
    f = font(FONT_XB, size)
    chunks = subtitle_chunks(words, maxw, f)
    cur = None
    for ch in chunks:
        if ch[0][1] - 0.05 <= lt: cur = ch
    if cur is None or lt > cur[-1][2] + 0.6: return
    d = ImageDraw.Draw(img, "RGBA")
    line = " ".join(w for w, _, _ in cur)
    x = cx - text_w(f, line) / 2
    for w, s, e in cur:
        col = (255, 214, 0) if s <= lt < e + 0.02 else (255, 255, 255)
        d.text((x, y), w, font=f, fill=col, stroke_width=6, stroke_fill=(0, 0, 0))
        x += text_w(f, w + " ")

def draw_tag(img, tag, lt):
    if not tag: return
    f = font(FONT_BOLD, 34)
    d = ImageDraw.Draw(img, "RGBA")
    k = min(1, lt / 0.35); k = 1 - (1 - k) ** 3
    tw = text_w(f, tag)
    x = -tw - 80 + (60 + tw + 80) * k
    d.rounded_rectangle((x, 46, x + tw + 44, 104), 10, fill=(215, 38, 61))
    d.text((x + 22, 75), tag, font=f, fill="white", anchor="lm")

def draw_keyword(img, kw, lt):
    if not kw: return
    k = min(1, max(0, (lt - 0.15) / 0.3))
    if k <= 0: return
    sc = 1 + 0.25 * (1 - k) ** 2 * math.sin(k * math.pi)
    size = int(96 * (0.6 + 0.4 * k) * sc)
    f = font(FONT_BLACK, size)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((W / 2, 190), kw, font=f, fill=(255, 255, 255), stroke_width=max(4, size // 10), stroke_fill=(0, 0, 0), anchor="mm")

def owl_sprite(mouth, blink, wing, look, scale):
    key = ("owl", round(mouth * 6), blink > 0.5, round(wing * 4), round(look * 2), round(scale, 2))
    if key not in _cache:
        o = make_owl(round(mouth * 6) / 6, 1 if blink > 0.5 else 0, round(wing * 4) / 4, round(look * 2) / 2)
        _cache[key] = o.resize((int(o.width * scale), int(o.height * scale)), Image.LANCZOS)
    return _cache[key]

def owl_state(t, env_c):
    fi = int(t * FPS)
    m = env_c[fi] if fi < len(env_c) else 0
    mouth = min(1, m / 0.12)
    blink = 1 if (t % 3.7) < 0.12 else 0
    wing = math.sin(t * 2.2) * 0.3 + mouth * 0.5
    look = math.sin(t * 0.6) * 0.5
    return mouth, blink, wing, look

def speech_bubble(img, box):
    d = ImageDraw.Draw(img, "RGBA")
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 + 8, y0 + 10, x1 + 8, y1 + 10), 40, fill=(0, 0, 0, 90))
    d.rounded_rectangle(box, 40, fill=(255, 255, 255), outline=(20, 20, 20), width=6)
    d.polygon([(x0 + 4, y1 - 120), (x0 - 70, y1 - 30), (x0 + 4, y1 - 60)], fill=(255, 255, 255))
    d.line([(x0 + 2, y1 - 122), (x0 - 70, y1 - 30), (x0 + 2, y1 - 60)], fill=(20, 20, 20), width=6)

def bubble_text(img, words, lt, box):
    """Show current sentence in the bubble, dark text with highlighted current word."""
    f = font(FONT_XB, 50)
    x0, y0, x1, y1 = box
    maxw = x1 - x0 - 90
    # current sentence
    sents = []; cur = []
    for w in words:
        cur.append(w)
        if re.search(r"[.!?]$", w[0]): sents.append(cur); cur = []
    if cur: sents.append(cur)
    sel = sents[0]
    for s_ in sents:
        if s_[0][1] - 0.1 <= lt: sel = s_
    # wrap
    lines = []; ln = []
    for w in sel:
        if ln and text_w(f, " ".join(x[0] for x in ln + [w])) > maxw: lines.append(ln); ln = []
        ln.append(w)
    if ln: lines.append(ln)
    d = ImageDraw.Draw(img, "RGBA")
    lh = 64
    y = (y0 + y1) / 2 - lh * len(lines) / 2
    for ln in lines:
        x = (x0 + x1) / 2 - text_w(f, " ".join(w for w, _, _ in ln)) / 2
        for w, s, e in ln:
            col = (215, 38, 61) if s <= lt < e + 0.02 else (25, 25, 30)
            d.text((x, y), w, font=f, fill=col)
            x += text_w(f, w + " ")
        y += lh

def card_bg(name, t, dark=0.35):
    key = ("cardbg", name)
    if key not in _cache:
        c = prepared(name).resize((W // 6, H // 6)).filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR)
        c = ImageEnhance.Brightness(c).enhance(dark)
        overlay = Image.new("RGB", (W, H), (10, 20, 45))
        _cache[key] = Image.blend(c, overlay, 0.45)
    return _cache[key].copy()

def title_text(img, lt, alpha=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    k = min(1, lt / 0.6); k = 1 - (1 - k) ** 3
    f1 = font(FONT_BLACK, int(150 * (0.8 + 0.2 * k)))
    d.text((W / 2, 300), "THE HUNT FOR", font=font(FONT_BLACK, 84), fill=(255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0), anchor="mm")
    d.text((W / 2, 440), "BIN LADEN", font=f1, fill=(255, 90, 80), stroke_width=14, stroke_fill=(0, 0, 0), anchor="mm")
    d.text((W / 2, 570), "How SEAL Team Six found the world's most wanted man", font=font(FONT_BOLD, 44), fill=(235, 235, 235), stroke_width=4, stroke_fill=(0, 0, 0), anchor="mm")
    d.rounded_rectangle((W / 2 - 170, 625, W / 2 + 170, 695), 14, fill=(0, 0, 0, 200))
    d.text((W / 2, 660), "2001 - 2011", font=font(FONT_BLACK, 50), fill="white", anchor="mm")

def render_item(it, t, segs_by_i, env_c, variant):
    p = (t - it["start"]) / max(0.01, it["end"] - it["start"])
    n = it["name"]
    if n.startswith("vid_"):
        return video_frame(n, it["src0"] + (t - it["start"]))
    if n in ("INTRO", "TITLE"):
        img = kenburns("cia_aerial", (t / 20.0), 0)
        img = ImageEnhance.Brightness(img).enhance(0.5).convert("RGBA")
        title_text(img, t)
        return img.convert("RGB")
    if n in ("HOOT", "OUTRO"):
        sg = segs_by_i[it["seg"]]
        # background: blurred version of previous visual
        prev = "memorial" if n == "OUTRO" else it.get("prevname", "cia_aerial")
        img = card_bg(prev, t).convert("RGBA")
        return img.convert("RGB")
    if n == "CREDITS":
        img = card_bg("memorial", t, 0.25)
        return img
    return kenburns(n, p, variant)

def compose(t, segs, items, segs_by_i, env_c):
    # find active item
    k = max(j for j, it in enumerate(items) if it["start"] <= t or j == 0)
    it = items[k]
    img = render_item(it, t, segs_by_i, env_c, k)
    pv = items[k - 1] if k > 0 else None
    if pv and t - it["start"] < XFADE and not (pv["name"] == "INTRO" and it["name"] == "TITLE") \
            and not (pv["name"] == it["name"] and it["name"].startswith("vid_")):
        prev = render_item(items[k - 1], t, segs_by_i, env_c, k - 1)
        a = (t - it["start"]) / XFADE
        img = Image.blend(prev, img, a * a * (3 - 2 * a))
    img = img.convert("RGBA")
    img.alpha_composite(vignette())
    sg = segs_by_i.get(it["seg"])
    n = it["name"]
    if n == "INTRO":
        pass
    elif n == "CREDITS":
        lt = t - it["start"]
        d = ImageDraw.Draw(img, "RGBA")
        d.text((W / 2, 200), "CREDITS & SOURCES", font=font(FONT_BLACK, 70), fill="white", stroke_width=6, stroke_fill=(0, 0, 0), anchor="mm")
        for j, line in enumerate(CREDIT_LINES):
            d.text((W / 2, 330 + j * 70), line, font=font(FONT_BOLD, 34), fill=(230, 230, 230), anchor="mm")
        d.text((W / 2, 900), "Thanks for watching!", font=font(FONT_BLACK, 60), fill=(255, 214, 0), stroke_width=6, stroke_fill=(0, 0, 0), anchor="mm")
    elif sg is not None:
        lt = t - sg["start"]
        if sg["sp"] == "C":
            mouth, blink, wing, look = owl_state(t, env_c)
            enter = min(1, lt / 0.45); enter = 1 - (1 - enter) ** 3
            if n == "TITLE":
                # owl pops in at right of the title
                o = owl_sprite(mouth, blink, wing, -0.5, 0.62)
                x = int(W - o.width + 40 + (1 - enter) * 600); y = int(H - o.height - 20 + math.sin(t * 3) * 6)
                img.alpha_composite(o, (x, y))
                draw_subs(img, sg["words"], lt, W / 2 - 260, 960, 1150, 52)
            else:
                o = owl_sprite(mouth, blink, wing, look, 1.12)
                x = int(-60 - (1 - enter) * 900); y = int(H - o.height + 30 + math.sin(t * 3) * 8)
                img.alpha_composite(o, (x, y))
                bx = (x + o.width + 60, 170, W - 70, 700) if n == "HOOT" else (x + o.width + 60, 120, W - 70, 560)
                if enter > 0.6:
                    speech_bubble(img, bx); bubble_text(img, sg["words"], lt, bx)
                d = ImageDraw.Draw(img, "RGBA")
                d.rounded_rectangle((60, 40, 470, 105), 14, fill=(255, 214, 0))
                d.text((265, 72), "PROFESSOR HOOT", font=font(FONT_BLACK, 36), fill=(20, 20, 20), anchor="mm")
                if n == "OUTRO":
                    pulse = 1 + 0.04 * math.sin(t * 6)
                    bw, bh = int(520 * pulse), int(120 * pulse)
                    cx, cy = (bx[0] + bx[2]) // 2, 720
                    d.rounded_rectangle((cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2), 24, fill=(230, 30, 30))
                    d.text((cx, cy), "SUBSCRIBE", font=font(FONT_BLACK, int(66 * pulse)), fill="white", anchor="mm")
                    d.text((cx, cy + 120), "for more history stories", font=font(FONT_BOLD, 40), fill="white", stroke_width=3, stroke_fill=(0, 0, 0), anchor="mm")
        elif sg["sp"] == "CLIP":
            d = ImageDraw.Draw(img, "RGBA")
            d.rounded_rectangle((60, 46, 640, 104), 10, fill=(215, 38, 61))
            d.text((82, 75), "REAL FOOTAGE - THE WHITE HOUSE", font=font(FONT_BOLD, 32), fill="white", anchor="lm")
            k2 = min(1, lt / 0.5)
            d.rectangle((0, 760, int(820 * k2), 840), fill=(10, 10, 20, 220))
            d.rectangle((0, 760, 14, 840), fill=(255, 214, 0))
            d.text((40, 800), "PRESIDENT BARACK OBAMA  |  MAY 1, 2011", font=font(FONT_BOLD, 36), fill="white", anchor="lm")
            draw_subs(img, sg["words"], lt, W / 2, 940, 1600, 54)
        else:
            draw_tag(img, sg["tag"], lt)
            draw_keyword(img, sg["kw"], lt)
            draw_subs(img, sg["words"], lt, W / 2, 950, 1640, 56)
    return img.convert("RGB")

def extract_video_frames():
    for name, s0, dur in (("vid_obama", 0.0, CLIP_SRC[1] + 0.5), ("vid_vinson", VINSON_SRC, 14.0)):
        d = f"{S}/frames/{name}"
        if os.path.isdir(d) and os.listdir(d): continue
        os.makedirs(d, exist_ok=True)
        start_frame = int(round(s0 * FPS)) + 1
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(s0), "-t", str(dur), "-i", f"{MEDIA}/{name}.webm",
                        "-vf", f"fps={FPS},scale={W}:{H}:flags=lanczos,eq=contrast=1.04", "-q:v", "3",
                        "-start_number", str(start_frame), f"{d}/f_%06d.jpg"], check=True)

def worker(args):
    wid, f0, f1, state = args
    segs, items, env_c = state["segs"], state["items"], np.array(state["env_c"])
    segs_by_i = {s["i"]: s for s in segs}
    out = f"{S}/chunks/c{wid:03d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        img = compose(fi / FPS, segs, items, segs_by_i, env_c)
        p.stdin.write(img.tobytes())
    p.stdin.close(); p.wait()
    return out

def main():
    segs, items, total, voice_items = build()
    # remember the previous photo for owl card backgrounds
    last = "cia_aerial"
    for it in items:
        if it["name"] in ("HOOT",): it["prevname"] = last
        elif not it["name"].startswith("vid_") and it["name"] not in ("INTRO", "TITLE", "OUTRO", "CREDITS"): last = it["name"]
    print(f"total {total:.1f}s, {len(items)} visual items", flush=True)
    extract_video_frames()
    wav = f"{S}/audio/final_mix.wav"
    cartoon = mix_audio(segs, total, voice_items, wav)
    env_c = envelope(cartoon)
    env_c = np.convolve(env_c, [0.25, 0.5, 0.25], "same")
    state = dict(segs=segs, items=items, env_c=env_c.tolist())
    json.dump(dict(segs=segs, items=items, total=total), open(f"{S}/timeline.json", "w"), indent=1, default=str)
    if "--preview" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1].split(",")]
        segs_by_i = {s["i"]: s for s in segs}
        os.makedirs(f"{S}/preview", exist_ok=True)
        for t in ts:
            compose(t, segs, items, segs_by_i, env_c).save(f"{S}/preview/p_{t:07.2f}.jpg", quality=85)
        print("preview done"); return
    nfr = int(total * FPS)
    os.makedirs(f"{S}/chunks", exist_ok=True)
    nchunks = 16
    bounds = [int(nfr * k / nchunks) for k in range(nchunks + 1)]
    from multiprocessing import Pool
    with Pool(4) as pool:
        outs = pool.map(worker, [(k, bounds[k], bounds[k + 1], state) for k in range(nchunks)])
    lst = f"{S}/chunks/list.txt"
    open(lst, "w").write("".join(f"file '{o}'\n" for o in outs))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("done", OUT)

if __name__ == "__main__":
    main()
