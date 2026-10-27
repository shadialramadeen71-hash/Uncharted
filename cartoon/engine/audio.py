"""Audio: neural English TTS (edge-tts) with word timings, synthesized footsteps/SFX,
and procedurally composed background music (original, so it is copyright-free)."""
import asyncio
import hashlib
import json
import os
import ssl
import subprocess

import numpy as np
from scipy import signal

SR = 44100
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache", "tts")


# ------------------------------------------------------------------ TTS
def _ssl_ctx():
    for f in (os.environ.get("SSL_CERT_FILE"), "/root/.ccr/ca-bundle.crt"):
        if f and os.path.exists(f):
            return ssl.create_default_context(cafile=f)
    return None


async def _tts_stream(text, voice, rate, pitch):
    import edge_tts
    import edge_tts.communicate as comm

    ctx = _ssl_ctx()
    if ctx is not None:
        comm._SSL_CTX = ctx
    c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary",
                             proxy=os.environ.get("HTTPS_PROXY") or None)
    audio, words = bytearray(), []
    async for chunk in c.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            s = chunk["offset"] / 1e7
            words.append([s, s + chunk["duration"] / 1e7, chunk["text"]])
    return bytes(audio), words


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def tts(text, voice, rate="+0%", pitch="+0Hz"):
    """Returns (mono float32 audio, [(start, end, word)]) with leading/trailing silence trimmed."""
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha1(f"{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:16]
    mp3, js = os.path.join(CACHE, key + ".mp3"), os.path.join(CACHE, key + ".json")
    if not (os.path.exists(mp3) and os.path.exists(js)):
        last = None
        for attempt in range(6):
            try:
                audio, words = asyncio.run(_tts_stream(text, voice, rate, pitch))
                if len(audio) > 1000:
                    open(mp3, "wb").write(audio)
                    json.dump(words, open(js, "w"))
                    break
            except Exception as e:  # network hiccups: retry
                last = e
        else:
            raise RuntimeError(f"TTS failed for {text!r}: {last}")
    y = decode(mp3)
    words = json.load(open(js))
    env = np.abs(y)
    idx = np.where(env > 0.01)[0]
    a = max(0, idx[0] - int(0.02 * SR)) if len(idx) else 0
    b = min(len(y), idx[-1] + int(0.06 * SR)) if len(idx) else len(y)
    y = y[a:b]
    off = a / SR
    words = [(max(0.0, s - off), max(0.0, e - off), w) for s, e, w in words]
    return y, words


def voice_fx(y, fx):
    if not fx:
        return y
    if fx == "nasal":  # pinched-nose voice
        b, a = signal.butter(2, [700 / (SR / 2), 2600 / (SR / 2)], "band")
        z = signal.lfilter(b, a, y) * 2.2
        return (0.8 * z + 0.2 * y).astype(np.float32)
    if fx == "shout":
        return np.tanh(y * 2.2).astype(np.float32) * 0.8
    if fx == "gargle":  # talking with the head tilted back
        t = np.arange(len(y)) / SR
        return (y * (0.65 + 0.35 * np.sin(2 * np.pi * 23 * t))).astype(np.float32)
    return y


def mouth_curve(y, fps):
    """Per-video-frame mouth openness (0..1) and a 'width' cue from the voice."""
    hop = SR // fps
    n = len(y) // hop + 1
    rms = np.zeros(n)
    zcr = np.zeros(n)
    for i in range(n):
        seg = y[i * hop:(i + 1) * hop]
        if len(seg):
            rms[i] = np.sqrt(np.mean(seg ** 2))
            zcr[i] = np.mean(np.abs(np.diff(np.sign(seg)))) / 2 if len(seg) > 1 else 0
    m = np.clip(rms / (np.percentile(rms, 90) + 1e-6), 0, 1.15) ** 0.8
    w = np.clip((zcr - 0.05) * 6, 0, 1)
    return np.clip(m, 0, 1), w


# ------------------------------------------------------------------ helpers
def _t(d):
    return np.arange(int(d * SR)) / SR


def _noise(n, rng):
    return rng.standard_normal(n).astype(np.float32)


def _bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def _lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def _hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def room_reverb(x, wet=0.12, decay=0.35, seed=7):
    rng = np.random.default_rng(seed)
    n = int(decay * SR)
    ir = _noise(n, rng) * np.exp(-np.arange(n) / (SR * decay / 6.5))
    ir = _lp(ir, 5000)
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    w = signal.fftconvolve(x, ir)[:len(x)]
    return x + wet * w


# ------------------------------------------------------------------ footsteps
def footstep(rng, kind="sneaker", strength=1.0, speed=300.0):
    """Heel strike + toe roll on a wooden floor, randomised so no two steps are identical."""
    if kind == "snow":
        return snow_step(rng, strength, speed)
    if kind == "paw":  # soft padded bear feet
        t = _t(0.25)
        y = np.sin(2 * np.pi * np.cumsum(60 + 50 * np.exp(-t * 25)) / SR) * np.exp(-t * 20) * 0.9
        y += _bp(_noise(len(t), rng), 200, 1500) * np.exp(-t * 50) * 0.25
        return (y * rng.uniform(0.8, 1.1) * strength).astype(np.float32)
    d = 0.32
    t = _t(d)
    n = len(t)
    out = np.zeros(n, dtype=np.float32)
    v = rng.uniform(0.85, 1.15) * strength * (0.8 + 0.4 * min(speed / 500, 1))
    # heel: low thump with a pitch drop (floor resonance)
    f0 = rng.uniform(70, 95)
    ph = 2 * np.pi * np.cumsum(f0 * (1 + 1.2 * np.exp(-t * 60))) / SR
    thump = np.sin(ph) * np.exp(-t * rng.uniform(32, 42))
    # heel: contact noise
    nz = _noise(n, rng)
    if kind == "heel":  # harder sole, brighter click
        click = _bp(nz, 1800, 7000) * np.exp(-t * 140) * 1.4
        scuff_band = (1500, 6000)
    elif kind == "leather":  # heavy old leather shoes on old floorboards
        click = _bp(nz, 500, 3200) * np.exp(-t * 110) * 1.1
        thump = thump * 1.35
        creak_f = rng.uniform(380, 520)
        creak = np.sin(2 * np.pi * np.cumsum(creak_f * (1 + 0.08 * np.sin(2 * np.pi * 31 * t))) / SR)
        click = click + creak * np.exp(-((t - 0.09) / 0.05) ** 2) * 0.05 * (rng.random() < 0.4)
        scuff_band = (700, 3500)
    else:
        click = _bp(nz, 350, 2600) * np.exp(-t * 90)
        scuff_band = (900, 4500)
    out += (0.75 * thump + 0.55 * click) * v
    # toe roll ~60-80 ms later, softer
    dt = int(rng.uniform(0.055, 0.085) * SR)
    toe = (_bp(_noise(n, rng), *scuff_band) * np.exp(-t * 110) * 0.35 + 0.25 * np.sin(ph * 1.3) * np.exp(-t * 55))
    out[dt:] += toe[:n - dt].astype(np.float32) * v
    # cloth/shoe scuff
    sc = _bp(_noise(n, rng), 2500, 9000) * np.exp(-((t - 0.02) / 0.03) ** 2) * 0.06
    out += sc.astype(np.float32) * v
    out *= np.minimum(1, t / 0.0015)
    return out


def snow_step(rng, strength=1.0, speed=300.0):
    """Boot compressing fresh snow: a dense burst of tiny crackles plus a soft low 'whump'."""
    d = 0.38
    t = _t(d)
    n = len(t)
    v = rng.uniform(0.85, 1.15) * strength
    dens = np.exp(-((t - 0.06) / 0.07) ** 2) + 0.5 * np.exp(-((t - 0.16) / 0.06) ** 2)
    clicks = (rng.random(n) < 0.045 * dens) * rng.uniform(0.3, 1.0, n)
    crunch = _bp(clicks, 1200, 8000) * 2.2 + _bp(_noise(n, rng), 600, 4000) * 0.12 * dens
    whump = np.sin(2 * np.pi * np.cumsum(70 + 40 * np.exp(-t * 30)) / SR) * np.exp(-t * 25) * 0.35
    out = (crunch + whump) * v
    return (out * np.minimum(1, t / 0.003)).astype(np.float32)


# ------------------------------------------------------------------ sfx
def sfx(name, rng):
    if name == "pop":
        t = _t(0.18)
        f = 900 * np.exp(-t * 22) + 250
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 25) * 0.7).astype(np.float32)
    if name == "whoosh":
        t = _t(0.45)
        nz = _noise(len(t), rng)
        env = np.sin(np.pi * t / t[-1]) ** 2
        out = np.zeros_like(nz)
        for i, (lo, hi) in enumerate([(300, 900), (700, 1800), (1500, 3500), (2500, 6000)]):
            w = np.exp(-((t / t[-1] - (0.15 + 0.22 * i)) / 0.2) ** 2)
            out += _bp(nz, lo, hi) * w
        return (out * env * 0.9).astype(np.float32)
    if name == "boing":
        t = _t(0.6)
        f = 180 + 260 * np.exp(-t * 4) * (1 + 0.25 * np.sin(2 * np.pi * 14 * t))
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
        return (np.tanh(y * 1.5) * 0.5).astype(np.float32)
    if name == "scratch":  # record scratch
        t = _t(0.5)
        speed = np.where(t < 0.18, 1 - t / 0.18 * 1.6, -0.6 + (t - 0.18) * 2.2)
        f = 380 + 900 * np.abs(speed)
        saw = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
        y = _bp(saw + 0.7 * _noise(len(t), rng), 300, 4000) * np.exp(-t * 3)
        return (y / (np.max(np.abs(y)) + 1e-9) * 0.6).astype(np.float32)
    if name == "ding":
        t = _t(1.2)
        y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in
                [(1568, 0.6, 3.5), (3136 * 1.01, 0.25, 6), (4704 * 1.02, 0.12, 9), (2093, 0.2, 4)])
        return (y * 0.45).astype(np.float32)
    if name == "splash":
        t = _t(0.9)
        nz = _noise(len(t), rng)
        body = _bp(nz, 400, 5000) * np.exp(-t * 7)
        y = body * 0.6
        for _ in range(14):  # droplets
            t0 = rng.uniform(0.05, 0.6)
            f = rng.uniform(900, 2600)
            i0 = int(t0 * SR)
            tt = _t(0.06)
            drop = np.sin(2 * np.pi * np.cumsum(f * (1 + 2 * tt / 0.06)) / SR) * np.exp(-tt * 70) * rng.uniform(0.1, 0.3)
            y[i0:i0 + len(drop)] += drop[:len(y) - i0]
        return y.astype(np.float32)
    if name == "sizzle":
        t = _t(1.0)
        nz = _hp(_noise(len(t), rng), 3000)
        crackle = (rng.random(len(t)) > 0.9985) * rng.uniform(0.5, 1, len(t))
        y = nz * 0.12 * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t)) + _bp(crackle, 1500, 8000) * 2
        return (y * np.minimum(1, (1 - t) * 4)).astype(np.float32)
    if name == "water":  # running tap
        t = _t(2.5)
        nz = _noise(len(t), rng)
        y = _bp(nz, 500, 6000) * 0.18 * (0.85 + 0.15 * np.sin(2 * np.pi * 3.3 * t))
        env = np.minimum(1, t / 0.08) * np.minimum(1, (t[-1] - t) / 0.3)
        return (y * env).astype(np.float32)
    if name == "rustle":  # bag of rice
        t = _t(0.7)
        y = _bp(_noise(len(t), rng), 2000, 9000) * (rng.random(len(t)) > 0.6) * 0.3 * np.exp(-t * 3)
        y += _bp(_noise(len(t), rng), 200, 1200) * 0.15 * np.exp(-t * 5)
        return y.astype(np.float32)
    if name == "thud":
        t = _t(0.4)
        y = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-t * 8) + 45) / SR) * np.exp(-t * 14)
        return (y * 0.9).astype(np.float32)
    if name == "sparkle":
        out = np.zeros(int(0.9 * SR), dtype=np.float32)
        for i, f in enumerate([1760, 2217, 2637, 3520]):
            tt = _t(0.6)
            tone = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9) * 0.22
            i0 = int(i * 0.07 * SR)
            out[i0:i0 + len(tone)] += tone[:len(out) - i0]
        return out
    if name == "hit":  # comedic impact
        t = _t(0.35)
        y = np.sin(2 * np.pi * np.cumsum(200 * np.exp(-t * 20) + 60) / SR) * np.exp(-t * 10)
        y += _bp(_noise(len(t), rng), 800, 5000) * np.exp(-t * 40) * 0.5
        return (y * 0.8).astype(np.float32)
    if name == "meow":
        d = 0.75
        t = _t(d)
        u = t / d
        f0 = 480 + 330 * np.sin(np.pi * np.clip(u * 1.15, 0, 1)) ** 1.5 - 90 * u
        F1 = 700 + 650 * np.sin(np.pi * np.clip(u * 1.1, 0, 1))  # "mi-aa-ow" formant sweep
        ph = 2 * np.pi * np.cumsum(f0) / SR
        y = np.zeros(len(t))
        for k in range(1, 14):
            a = np.exp(-((k * f0 - F1) / 380) ** 2) + 0.35 * np.exp(-((k * f0 - 2.6 * F1) / 700) ** 2)
            y += a * np.sin(k * ph) / k ** 0.3
        env = np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.18)
        y = y * env + _bp(_noise(len(t), rng), 2000, 7000) * 0.02 * env
        return (y / (np.max(np.abs(y)) + 1e-9) * 0.6).astype(np.float32)
    if name == "slip":  # shoe squeak on ice + whoosh
        t = _t(0.5)
        f = 900 + 1500 * np.clip(t / 0.18, 0, 1)
        sq = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-((t - 0.1) / 0.08) ** 2) * 0.5
        wh = sfx("whoosh", rng)
        sq[:len(wh)] += wh[:len(sq)] * 0.8
        return sq.astype(np.float32)
    if name == "chop":
        t = _t(0.18)
        y = _bp(_noise(len(t), rng), 900, 5000) * np.exp(-t * 90) + np.sin(2 * np.pi * 160 * t) * np.exp(-t * 45) * 0.8
        return (y * 0.7).astype(np.float32)
    if name == "sob":
        t = _t(0.8)
        f = 320 + 60 * np.sin(2 * np.pi * 7 * t)
        y = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 5 * t)) * np.exp(-t * 2)
        return (_bp(y, 300, 2500) * 0.3).astype(np.float32)
    if name == "quack":
        t = _t(0.28)
        f = 260 * (1 - 0.25 * t / 0.28)
        y = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
        y = _bp(y, 700, 2600) * 1.6 + _bp(y, 2400, 4200) * 0.5
        env = np.minimum(1, t / 0.015) * np.exp(-t * 6)
        return (y * env / (np.max(np.abs(y * env)) + 1e-9) * 0.6).astype(np.float32)
    if name == "clonk":  # rock-hard bread knocking on wood
        t = _t(0.25)
        y = (np.sin(2 * np.pi * 420 * t) * np.exp(-t * 40) + 0.6 * np.sin(2 * np.pi * 1130 * t) * np.exp(-t * 60)
             + _bp(_noise(len(t), rng), 800, 4000) * np.exp(-t * 90) * 0.6)
        return (y * 0.7).astype(np.float32)
    if name == "crack":  # cartoon back "crack"
        out = np.zeros(int(0.3 * SR), dtype=np.float32)
        for k in range(3):
            c = _bp(_noise(int(0.03 * SR), rng), 1500, 7000) * np.exp(-_t(0.03) * 150)
            i0 = int(k * 0.05 * SR)
            out[i0:i0 + len(c)] += c.astype(np.float32)
        return out * 0.9
    if name == "sip":
        t = _t(0.5)
        y = _bp(_noise(len(t), rng), 1500, 6000) * np.minimum(1, t / 0.05) * np.exp(-t * 4) * 0.25
        return y.astype(np.float32)
    if name == "bell":  # shop door bell
        t = _t(1.0)
        y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in
                [(2093, 0.5, 4), (2637, 0.35, 5), (4186, 0.15, 8)])
        y2 = np.zeros_like(y)
        k = int(0.12 * SR)
        y2[k:] = y[:-k] * 0.7
        return ((y + y2) * 0.4).astype(np.float32)
    if name == "car":  # engine growing as it approaches, then a whoosh past
        d = 1.2
        t = _t(d)
        f = 70 + 60 * (t / d) ** 2
        eng = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * 0.4 + _bp(_noise(len(t), rng), 150, 900) * 0.6
        env = (t / d) ** 2.2 * np.minimum(1, (d - t) / 0.08)
        out = _lp(eng, 1500) * env
        wh = sfx("whoosh", rng)
        i0 = int((d - 0.35) * SR)
        out[i0:i0 + len(wh)] += wh[:len(out) - i0] * 1.2
        return (out / (np.max(np.abs(out)) + 1e-9) * 0.8).astype(np.float32)
    if name == "honk":
        t = _t(0.45)
        y = sum(signal.square(2 * np.pi * f * t, 0.5) for f in (392, 494)) * 0.3
        y = _lp(y, 2500) * np.minimum(1, t / 0.02) * np.minimum(1, (0.45 - t) / 0.05)
        return y.astype(np.float32)
    if name == "clink":  # empty can hitting the ground
        out = np.zeros(int(0.6 * SR))
        for k, (dt, g) in enumerate(((0.0, 1.0), (0.18, 0.5), (0.3, 0.25))):
            tt = _t(0.25)
            y = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * dcy) for f, dcy in ((1800, 30), (3100, 45), (4700, 60)))
            i0 = int(dt * SR)
            out[i0:i0 + len(y)] += y * g * 0.4
        return out.astype(np.float32)
    if name == "clank":  # bin lid
        t = _t(0.5)
        y = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 9) for f in (310, 523, 811)) * 0.3
        y += _bp(_noise(len(t), rng), 1000, 6000) * np.exp(-t * 60) * 0.5
        return y.astype(np.float32)
    if name == "growl":  # hungry stomach
        t = _t(0.9)
        f = 90 + 40 * np.sin(2 * np.pi * 3 * t) + 30 * t
        y = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t))
        return (_bp(y, 80, 700) * np.minimum(1, t / 0.1) * np.minimum(1, (0.9 - t) / 0.2) * 0.6).astype(np.float32)
    if name == "glug":  # drinking gulps
        out = np.zeros(int(1.0 * SR))
        for k in range(4):
            tt = _t(0.16)
            f = 180 + 120 * np.exp(-tt * 30) + rng.uniform(-20, 20)
            g = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 18) * 0.6
            g += _bp(_noise(len(tt), rng), 300, 1500) * np.exp(-tt * 30) * 0.2
            i0 = int(k * 0.22 * SR)
            out[i0:i0 + len(g)] += g
        return out.astype(np.float32)
    if name == "jingle":  # keys
        out = np.zeros(int(0.7 * SR))
        for _ in range(10):
            tt = _t(0.12)
            f = rng.uniform(3500, 7000)
            tone = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 40) * rng.uniform(0.1, 0.25)
            i0 = int(rng.uniform(0, 0.5) * SR)
            out[i0:i0 + len(tone)] += tone
        return out.astype(np.float32)
    if name == "horn":  # party blower
        t = _t(0.6)
        y = signal.sawtooth(2 * np.pi * np.cumsum(420 + 60 * np.sin(2 * np.pi * 6 * t)) / SR)
        return (_bp(y, 400, 3000) * np.minimum(1, t / 0.03) * np.minimum(1, (0.6 - t) / 0.1) * 0.4).astype(np.float32)
    if name == "freeze":
        t = _t(1.0)
        y = _hp(_noise(len(t), rng), 4000) * np.exp(-t * 3) * 0.25
        for k in range(8):
            tt = _t(0.3)
            tone = np.sin(2 * np.pi * (2000 + 400 * k) * tt) * np.exp(-tt * 10) * 0.1
            i0 = int(k * 0.06 * SR)
            y[i0:i0 + len(tone)] += tone
        return y.astype(np.float32)
    if name == "chew":
        out = np.zeros(int(0.8 * SR))
        for k in range(4):
            c = _bp(_noise(int(0.08 * SR), rng), 1500, 6000) * np.exp(-_t(0.08) * 40) * 0.35
            i0 = int(k * 0.18 * SR)
            out[i0:i0 + len(c)] += c
        return out.astype(np.float32)
    if name == "shatter":  # glass breaking into pieces
        t = _t(1.0)
        y = _hp(_noise(len(t), rng), 2500) * np.exp(-t * 12) * 0.5
        for _ in range(26):
            t0 = rng.uniform(0, 0.6) ** 1.5
            tt = _t(0.12)
            f = rng.uniform(3000, 9000)
            tink = np.sin(2 * np.pi * f * tt) * np.exp(-tt * rng.uniform(40, 90)) * rng.uniform(0.1, 0.35)
            i0 = int(t0 * SR)
            y[i0:i0 + len(tink)] += tink[:len(y) - i0]
        return y.astype(np.float32)
    if name == "magic":  # rising twinkly glissando
        out = np.zeros(int(1.2 * SR))
        for i in range(14):
            f = 900 * 2 ** (i / 7)
            tt = _t(0.5)
            tone = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2.76 * f * tt)) * np.exp(-tt * 7) * 0.12
            i0 = int(i * 0.045 * SR)
            out[i0:i0 + len(tone)] += tone[:len(out) - i0]
        return out.astype(np.float32)
    if name == "poof":
        t = _t(0.6)
        y = _lp(_noise(len(t), rng), 900) * np.exp(-t * 7) * 1.4
        y += np.sin(2 * np.pi * np.cumsum(140 * np.exp(-t * 6) + 50) / SR) * np.exp(-t * 12) * 0.5
        return (y * 0.7).astype(np.float32)
    if name == "trumpet":  # royal fanfare call (guards!)
        out = np.zeros(int(1.1 * SR))
        for i, (f, d) in enumerate(((523, 0.12), (523, 0.12), (659, 0.12), (784, 0.5))):
            tt = _t(d)
            y = sum(signal.sawtooth(2 * np.pi * f * k * tt) / k for k in (1, 2)) * np.minimum(1, tt / 0.02)
            y = _lp(y, 3000) * np.minimum(1, (d - tt) / 0.03) * 0.25
            i0 = int(i * 0.15 * SR)
            out[i0:i0 + len(y)] += y[:len(out) - i0]
        return out.astype(np.float32)
    raise KeyError(name)


# ------------------------------------------------------------------ music
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pluck(freq, dur, rng, bright=0.5, decay=0.996):
    """Karplus-Strong plucked string (ukulele / pizzicato bass), vectorised per period."""
    n = int(dur * SR)
    p = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, p)
    buf = _lp(buf, 800 + bright * 6000) if p > 12 else buf
    out = np.zeros(n + p + 1)
    out[:p] = buf
    i = p
    while i < n + 1:
        k = min(p, n + 1 - i)
        out[i:i + k] = decay * 0.5 * (out[i - p:i - p + k] + out[i - p + 1:i - p + 1 + k])
        i += k
    y = out[:n]
    return y * np.minimum(1, np.arange(n) / 30)


def marimba(freq, dur):
    t = _t(dur)
    y = (np.sin(2 * np.pi * freq * t) * np.exp(-t * 6) + 0.35 * np.sin(2 * np.pi * freq * 3.93 * t) * np.exp(-t * 22)
         + 0.12 * np.sin(2 * np.pi * freq * 9.2 * t) * np.exp(-t * 50))
    return y * np.minimum(1, t / 0.002)


def music(duration, seed=1, bpm=124, key="C", mood="bouncy"):
    """An original comedic ukulele/marimba groove. Deterministic per seed."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    root = 60 + NOTE[key]
    n = int((duration + 2) * SR)
    mix = np.zeros(n)
    progs = {
        "bouncy": [(0, "maj"), (9, "min"), (5, "maj"), (7, "maj")],
        "sneaky": [(0, "min"), (5, "min"), (3, "maj"), (7, "maj")],
    }
    prog = progs.get(mood, progs["bouncy"])
    quality = {"maj": [0, 4, 7], "min": [0, 3, 7]}
    scale = [0, 2, 4, 7, 9] if mood == "bouncy" else [0, 3, 5, 7, 10]

    def add(y, t0, g):
        i0 = int(t0 * SR)
        if i0 >= n:
            return
        y = y[:n - i0]
        mix[i0:i0 + len(y)] += g * y

    # melody motif: 2 bars of eighth notes, generated once and varied
    motif = []
    deg = 2
    for k in range(16):
        if rng.random() < 0.28 and k % 2 == 1:
            motif.append(None)
            continue
        deg = int(np.clip(deg + rng.choice([-2, -1, 1, 1, 2]), 0, 9))
        motif.append(deg)

    bars = int(duration / (4 * beat)) + 2
    for b in range(bars):
        t_bar = b * 4 * beat
        deg_root, q = prog[b % len(prog)]
        chord = [root + deg_root + iv for iv in quality[q]]
        # bass: oom-pah with octave bounce
        for k, (beat_i, octv) in enumerate([(0, -24), (1.5, -12), (2, -24), (3.5, -12)]):
            add(pluck(midi_hz(chord[0] + octv), beat * 1.2, rng, bright=0.25, decay=0.993), t_bar + beat_i * beat, 0.55)
        # ukulele strums on the off-beats
        for beat_i in (1, 3, 3.5):
            for j, m in enumerate(chord + [chord[0] + 12]):
                add(pluck(midi_hz(m), beat * 1.6, rng, bright=0.7, decay=0.995), t_bar + beat_i * beat + j * 0.012, 0.16)
        # marimba melody (skip the first bar so the hook breathes)
        if b >= 1:
            half = (b % 2) * 8
            for k in range(8):
                d = motif[half + k]
                if d is None:
                    continue
                if b % 4 == 3 and k >= 6:
                    continue
                m = root + 12 + scale[d % 5] + 12 * (d // 5)
                add(marimba(midi_hz(m), beat * 1.5), t_bar + k * beat / 2, 0.22)
        # light percussion
        for k in range(8):
            tt = t_bar + k * beat / 2
            nz = _hp(_noise(int(0.05 * SR), rng), 7000) * np.exp(-_t(0.05) * 90)
            add(nz, tt, 0.1 if k % 2 else 0.05)
        for beat_i in (0, 2):
            tk = _t(0.25)
            kick = np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tk * 30)) / SR) * np.exp(-tk * 14)
            add(kick, t_bar + beat_i * beat, 0.45)
        for beat_i in (1, 3):
            snap = _bp(_noise(int(0.12 * SR), rng), 1200, 6000) * np.exp(-_t(0.12) * 45)
            add(snap, t_bar + beat_i * beat, 0.28)
    mix = mix[:int(duration * SR)]
    fade = int(0.8 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix /= np.max(np.abs(mix)) + 1e-9
    return room_reverb(mix, wet=0.1).astype(np.float32)


def accordion(freq, dur, rng, bright=0.6):
    """Musette accordion note: three reeds (one in tune, two detuned = the Paris 'wet' tremolo)."""
    t = _t(dur)
    y = np.zeros(len(t))
    for det in (1.0, 1.0035, 0.9968):
        ph = 2 * np.pi * freq * det * t + rng.uniform(0, 6.28)
        y += signal.sawtooth(ph, 0.5 + 0.45 * bright) * 0.6 + signal.square(ph, 0.3) * 0.25
    y = _lp(y, 1800 + 2600 * bright)
    env = np.minimum(1, t / 0.035) * np.minimum(1, (dur - t) / 0.06)
    return y * env * (0.92 + 0.08 * np.sin(2 * np.pi * 5.5 * t))


def musette(duration, seed=1, bpm=168, key="A"):
    """An original Parisian musette waltz (3/4): accordion melody, oom-pah-pah bass/chords, brushes."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    root = 57 + NOTE[key] - NOTE["A"]  # A3
    n = int((duration + 2) * SR)
    mix = np.zeros(n)

    def add(y, t0, g):
        i0 = int(t0 * SR)
        if 0 <= i0 < n:
            y = y[:n - i0]
            mix[i0:i0 + len(y)] += g * y

    prog = [(0, "min"), (5, "min"), (7, "maj"), (0, "min"), (8, "maj"), (5, "min"), (7, "maj"), (0, "min")]
    quality = {"maj": [0, 4, 7], "min": [0, 3, 7]}
    scale = [0, 2, 3, 5, 7, 8, 11]  # harmonic minor
    # a 2-bar melodic cell (6 beats) built from chord tones with a chromatic run, varied per bar
    cells = []
    for _ in range(2):
        rhythm = [[1, 0.5, 0.5, 1], [1.5, 0.5, 1], [0.5, 0.5, 0.5, 0.5, 1], [2, 1]][rng.integers(0, 4)]
        cells.append(rhythm)
    bars = int(duration / (3 * beat)) + 2
    for b in range(bars):
        t0 = b * 3 * beat
        deg, q = prog[b % len(prog)]
        chord = [root + deg + iv for iv in quality[q]]
        add(accordion(midi_hz(chord[0] - 12), beat * 0.9, rng, 0.3), t0, 0.5)  # oom
        for k in (1, 2):  # pah pah
            for m in chord:
                add(accordion(midi_hz(m), beat * 0.45, rng, 0.45), t0 + k * beat, 0.16)
        if b >= 1:  # melody
            tt = t0
            rhythm = cells[b % 2]
            for i, dur_b in enumerate(rhythm):
                pick = chord[(i + b) % 3] + 12
                if i == len(rhythm) - 1 and b % 4 == 3:
                    pick = chord[0] + 12
                elif rng.random() < 0.3:
                    pick = root + 12 + scale[int(rng.integers(0, 7))]
                add(accordion(midi_hz(pick), dur_b * beat * 0.95, rng, 0.75), tt, 0.3)
                tt += dur_b * beat
        for k in range(3):  # brushes
            br = _bp(_noise(int(0.12 * SR), rng), 2500, 9000) * np.exp(-_t(0.12) * (25 if k else 12))
            add(br, t0 + k * beat, 0.06 if k else 0.09)
    mix = mix[:int(duration * SR)]
    fade = int(0.8 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix /= np.max(np.abs(mix)) + 1e-9
    return room_reverb(mix, wet=0.16, decay=0.6).astype(np.float32)


def ambience(kind, duration, seed=1):
    """Quiet background atmosphere (no music): city traffic, forest birds, park birds."""
    rng = np.random.default_rng(seed + 900)
    n = int(duration * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    if kind == "desert":  # hot wind in gusts
        gust = 0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * t) * np.sin(2 * np.pi * 0.07 * t + 1)
        out += _bp(_noise(n, rng), 150, 1200) * 0.18 * gust + _hp(_noise(n, rng), 3000) * 0.015 * gust
    elif kind == "beach":  # rolling waves
        wave = np.clip(np.sin(2 * np.pi * t / 4.5), 0, 1) ** 2
        out += _lp(_noise(n, rng), 1200) * 0.12 * (0.3 + wave) + _hp(_noise(n, rng), 2500) * 0.04 * wave
    elif kind == "city":
        out += _lp(_noise(n, rng), 400) * 0.25 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.2 * t))
        out += _bp(_noise(n, rng), 800, 3000) * 0.03
    else:
        out += _bp(_noise(n, rng), 300, 2500) * (0.05 if kind == "forest" else 0.035) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.15 * t))
        n_birds = int(duration * (1.4 if kind == "forest" else 1.0))
        for _ in range(n_birds):
            t0 = rng.uniform(0, duration - 0.6)
            base = rng.uniform(2500, 4200)
            for k in range(int(rng.integers(2, 5))):
                tt = _t(rng.uniform(0.06, 0.12))
                f = base * (1 + 0.25 * np.sin(np.pi * tt / tt[-1])) * rng.uniform(0.9, 1.1)
                chirp = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / tt[-1]) * rng.uniform(0.04, 0.09)
                i0 = int((t0 + k * 0.13) * SR)
                out[i0:i0 + len(chirp)] += chirp[:max(0, n - i0)]
    fade = int(0.3 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out.astype(np.float32)


def _celesta(freq, dur):
    t = _t(dur)
    return (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t * 6)
            + 0.15 * np.sin(2 * np.pi * 3.01 * freq * t) * np.exp(-t * 12)) * np.exp(-t * 3.5) * np.minimum(1, t / 0.003)


def villain_music(duration, seed=1, bpm=104):
    """Original mischievous 'sneaking villain' cue: tiptoe pizzicato, soft bassoon, celesta sparkles."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    root = 50  # D3
    n = int((duration + 2) * SR)
    mix = np.zeros(n)

    def add(y, t0, g):
        i0 = int(t0 * SR)
        if 0 <= i0 < n:
            y = y[:n - i0]
            mix[i0:i0 + len(y)] += g * y

    prog = [(0, [0, 3, 7]), (-4, [0, 4, 7]), (5, [0, 3, 7]), (7, [0, 4, 7])]  # i - VI - iv - V
    cell = [0, None, 2, None, 1, 0, 2, None]
    bars = int(duration / (4 * beat)) + 2
    for b in range(bars):
        t0 = b * 4 * beat
        deg, tri = prog[b % 4]
        chord = [root + deg + iv for iv in tri]
        for k in (0, 2):  # pizzicato bass
            add(pluck(midi_hz(chord[0] - 12), beat * 0.8, rng, bright=0.3, decay=0.99), t0 + k * beat, 0.6)
        tt = _t(beat * 3.8)  # soft bassoon pad
        bsn = signal.square(2 * np.pi * midi_hz(chord[0] - 12) * tt, 0.3)
        add(_lp(bsn, 700) * np.minimum(1, tt / 0.15) * np.minimum(1, (tt[-1] - tt) / 0.3) * 0.25, t0, 0.5)
        for i, c in enumerate(cell):  # tiptoe staccato plucks
            if c is None or (b % 4 == 3 and i > 4):
                continue
            m = chord[c] + 12 + (1 if (b % 2 and i == 5) else 0)
            add(pluck(midi_hz(m), beat * 0.35, rng, bright=0.6, decay=0.985), t0 + i * beat / 2, 0.32)
        if b % 4 == 3:  # sneaky chromatic creep up
            for i in range(4):
                add(pluck(midi_hz(chord[0] + 12 + i), beat * 0.3, rng, bright=0.6, decay=0.985), t0 + (2 + i * 0.5) * beat, 0.3)
        if b % 2 == 1:  # celesta sparkle
            for i in range(3):
                add(_celesta(midi_hz(chord[i % 3] + 24 + 12 * (i // 2)), 1.0), t0 + (1.5 + i * 0.25) * beat, 0.12)
        tk = _t(0.2)
        add(np.sin(2 * np.pi * np.cumsum(45 + 70 * np.exp(-tk * 30)) / SR) * np.exp(-tk * 16), t0, 0.3)
    mix = mix[:int(duration * SR)]
    fade = int(0.8 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix /= np.max(np.abs(mix)) + 1e-9
    return room_reverb(mix, wet=0.18, decay=0.8).astype(np.float32)


def _brass(freq, dur, bright=0.5):
    t = _t(dur)
    y = signal.sawtooth(2 * np.pi * freq * t) + 0.5 * signal.sawtooth(2 * np.pi * freq * 1.003 * t)
    y = _lp(y, 600 + 2200 * bright)
    return y * np.minimum(1, t / 0.04) * np.minimum(1, (dur - t) / 0.06)


def noir_music(duration, seed=1, bpm=132):
    """Original dark action cue: low brass ostinato, string tremolo, timpani, a heroic horn line."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    root = 38  # D2
    n = int((duration + 2) * SR)
    mix = np.zeros(n)

    def add(y, t0, g):
        i0 = int(t0 * SR)
        if 0 <= i0 < n:
            y = y[:n - i0]
            mix[i0:i0 + len(y)] += g * y

    prog = [(0, [0, 3, 7]), (-4, [0, 4, 7]), (-2, [0, 4, 7]), (-5, [0, 4, 7])]  # i - VI - VII - V
    ost = [0, 0, 3, 0, 2, 0, -1, 0]
    horn = [(0, 2), (7, 1), (12, 1), (15, 4)]
    bars = int(duration / (4 * beat)) + 2
    for b in range(bars):
        t0 = b * 4 * beat
        deg, tri = prog[b % 4]
        for i, iv in enumerate(ost):  # brass ostinato
            add(_brass(midi_hz(root + deg + iv), beat * 0.45, 0.35), t0 + i * beat / 2, 0.32)
        tt = _t(4 * beat)  # string tremolo chord
        trem = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 12 * tt))
        chord = sum(signal.sawtooth(2 * np.pi * midi_hz(root + 24 + deg + iv) * tt) for iv in tri)
        add(_lp(chord, 3000) * trem * np.minimum(1, tt / 0.2) * 0.12, t0, 1.0)
        tk = _t(0.6)  # timpani
        timp = np.sin(2 * np.pi * np.cumsum(midi_hz(root + deg) * (1 + 0.3 * np.exp(-tk * 20))) / SR) * np.exp(-tk * 5)
        add(timp + _lp(_noise(len(tk), rng), 300) * np.exp(-tk * 30) * 0.3, t0, 0.55)
        add(timp * 0.6, t0 + 2.5 * beat, 0.35)
        if b % 4 == 1:  # heroic horn call
            tt0 = t0
            for iv, d in horn:
                add(_brass(midi_hz(root + 24 + iv), beat * d * 0.95, 0.6), tt0, 0.2)
                tt0 += beat * d
    mix = mix[:int(duration * SR)]
    fade = int(0.8 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix /= np.max(np.abs(mix)) + 1e-9
    return room_reverb(mix, wet=0.2, decay=0.9).astype(np.float32)


def _epiano(freq, dur):
    t = _t(dur)
    y = (np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t * 4)
         + 0.08 * np.sin(2 * np.pi * 7 * freq * t) * np.exp(-t * 30))
    return y * np.exp(-t * 1.6) * np.minimum(1, t / 0.005) * (0.85 + 0.15 * np.sin(2 * np.pi * 5 * t))


def muzak(duration, seed=1, bpm=100):
    """Original 'elevator music': soft bossa e-piano on major-7th chords, brushed shaker, round bass."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    root = 53  # F3
    n = int((duration + 2) * SR)
    mix = np.zeros(n)

    def add(y, t0, g):
        i0 = int(t0 * SR)
        if 0 <= i0 < n:
            y = y[:n - i0]
            mix[i0:i0 + len(y)] += g * y

    prog = [(0, [0, 4, 7, 11]), (2, [0, 3, 7, 10]), (5, [0, 4, 7, 11]), (7, [0, 4, 7, 10])]
    bars = int(duration / (4 * beat)) + 2
    for b in range(bars):
        t0 = b * 4 * beat
        deg, ch = prog[b % 4]
        for off in (0, 1.5, 2.5):  # bossa comping
            for iv in ch:
                add(_epiano(midi_hz(root + deg + iv), beat * 1.2), t0 + off * beat, 0.08)
        for off, iv in ((0, 0), (1.5, 7), (2, 0), (3.5, 7)):
            tt = _t(beat * 0.8)
            add(np.sin(2 * np.pi * midi_hz(root - 12 + deg + iv) * tt) * np.exp(-tt * 3), t0 + off * beat, 0.35)
        for k in range(8):
            sh = _bp(_noise(int(0.06 * SR), rng), 4000, 9000) * np.exp(-_t(0.06) * 60)
            add(sh, t0 + k * beat / 2, 0.05 if k % 2 else 0.03)
        if b % 2 == 1:
            for i, iv in enumerate((11, 7, 4, 2)):
                add(_epiano(midi_hz(root + 12 + deg + iv), beat), t0 + i * beat, 0.07)
    mix = mix[:int(duration * SR)]
    fade = int(0.6 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix /= np.max(np.abs(mix)) + 1e-9
    return room_reverb(mix, wet=0.12).astype(np.float32)
