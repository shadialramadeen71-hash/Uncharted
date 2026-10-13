"""Voices (edge-tts + per-character ffmpeg filters), synthesized SFX and mixing."""
import asyncio
import hashlib
import json
import os
import subprocess

import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "build", "voice_cache")

# Each character gets a distinct neural voice plus a filter that sells the mask.
VOICES = {
    # deep, calm rule-follower; slight metallic comb = voice behind hard plastic
    "poly": dict(voice="en-US-ChristopherNeural", rate="-6%", pitch="-16Hz",
                 af="aecho=0.7:0.5:6:0.35,volume=1.15"),
    # shy, soft-spoken, muffled by a rubber mask
    "stitches": dict(voice="en-US-BrianNeural", rate="-10%", pitch="+6Hz",
                     af="lowpass=f=2300,volume=1.9"),
    "ghosty": dict(voice="en-US-AnaNeural", rate="+6%", pitch="+0Hz",
                   af="aecho=0.8:0.6:70|140:0.3|0.18,volume=1.2"),
    "granny": dict(voice="en-GB-SoniaNeural", rate="-12%", pitch="-10Hz",
                   af="vibrato=f=6:d=0.18,volume=1.2"),
    "quackers": dict(voice="en-US-GuyNeural", rate="+15%", pitch="+28Hz",
                     af="highpass=f=280,volume=1.35"),
    "narrator": dict(voice="en-US-EricNeural", rate="+8%", pitch="+4Hz", af="volume=1.1"),
}

TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB,areverse")


def _ffmpeg_to_array(path, af=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if af:
        cmd += ["-af", af]
    cmd += ["-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    out = subprocess.run(cmd, check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def _patch_certifi():
    # edge-tts verifies TLS with certifi's bundle; behind a TLS-terminating
    # proxy we must hand it the proxy CA instead (never disable verification).
    bundle = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
    if os.path.exists(bundle):
        import certifi
        certifi.where = lambda: bundle


def tts(speaker, text):
    """Return mono float32 audio for a line, cached on disk."""
    cfg = VOICES[speaker]
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha1(json.dumps([text, cfg]).encode()).hexdigest()[:16]
    npy = os.path.join(CACHE, key + ".npy")
    if os.path.exists(npy):
        return np.load(npy)
    mp3 = os.path.join(CACHE, key + ".mp3")
    if not os.path.exists(mp3):
        _patch_certifi()
        import edge_tts
        for attempt in range(4):
            try:
                asyncio.run(edge_tts.Communicate(text, cfg["voice"], rate=cfg["rate"],
                                                 pitch=cfg["pitch"]).save(mp3))
                break
            except Exception:
                if attempt == 3:
                    raise
    a = _ffmpeg_to_array(mp3, TRIM + "," + cfg["af"])
    np.save(npy, a)
    return a


def load_music(path, start, dur):
    a = _ffmpeg_to_array(path, f"atrim=start={start}:duration={dur + 1},asetpts=PTS-STARTPTS")
    n = int(dur * SR)
    if len(a) < n:
        a = np.pad(a, (0, n - len(a)))
    a = a[:n]
    rms = np.sqrt(np.mean(a ** 2) + 1e-9)
    a = a * (0.07 / rms)  # normalise loudness so every track sits the same
    fade = int(1.5 * SR)
    a[-fade:] *= np.linspace(1, 0, fade)
    a[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    return a


# --------------------------------------------------------------------------
# Synthesized SFX (made from scratch here, so no licensing at all)
# --------------------------------------------------------------------------

def _t(d):
    return np.arange(int(d * SR)) / SR


def _env(n, a=0.005, r=0.1):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def _sweep(f0, f1, d, wave="sine", vib=0.0, vibf=6.0):
    t = _t(d)
    f = np.geomspace(f0, f1, len(t)) * (1 + vib * np.sin(2 * np.pi * vibf * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    if wave == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if wave == "square":
        return np.sign(np.sin(ph)) * 0.6
    return np.sin(ph)


def sfx_boing():
    d = 0.6
    t = _t(d)
    f = 180 + 260 * np.exp(-t * 6) * (1 + 0.5 * np.sin(2 * np.pi * 18 * t))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return s * np.exp(-t * 4) * 0.7


def sfx_slide_up():
    return _sweep(300, 1600, 0.7, vib=0.03) * _env(int(0.7 * SR), 0.02, 0.1) * 0.5


def sfx_slide_down():
    return _sweep(1500, 250, 0.8, vib=0.03) * _env(int(0.8 * SR), 0.02, 0.1) * 0.5


def sfx_ding():
    t = _t(1.4)
    s = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((1320, 1), (2640, 0.4), (3960, 0.2), (1985, 0.25)))
    return s * np.exp(-t * 3.5) * 0.35


def sfx_knock():
    out = np.zeros(int(0.9 * SR))
    rng = np.random.default_rng(1)
    for k, at in enumerate((0.0, 0.22, 0.44)):
        t = _t(0.12)
        hit = (np.sin(2 * np.pi * 140 * t) + 0.5 * rng.standard_normal(len(t))) * np.exp(-t * 45)
        i = int(at * SR)
        out[i:i + len(hit)] += hit * 0.8
    return out


def sfx_flap():
    rng = np.random.default_rng(2)
    t = _t(0.9)
    n = rng.standard_normal(len(t))
    n = np.convolve(n, np.ones(30) / 30, mode="same")
    return n * (0.5 + 0.5 * np.sin(2 * np.pi * 14 * t)) ** 2 * _env(len(t), 0.05, 0.3) * 1.6


def sfx_coo():
    out = []
    for f0, d in ((520, 0.22), (430, 0.38)):
        t = _t(d)
        f = f0 * (1 + 0.08 * np.sin(2 * np.pi * 9 * t)) * np.linspace(1.05, 0.95, len(t))
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
        out.append(s * _env(len(t), 0.04, 0.08) * 0.45)
        out.append(np.zeros(int(0.05 * SR)))
    return np.concatenate(out)


def sfx_sad_trombone():
    notes = [(293.7, 0.45), (277.2, 0.45), (261.6, 0.45), (246.9, 1.3)]
    out = []
    for i, (f, d) in enumerate(notes):
        vib = 0.025 if i == 3 else 0.006
        s = _sweep(f, f * (0.98 if i == 3 else 1.0), d, "saw", vib=vib, vibf=5.5)
        s = np.convolve(s, np.ones(12) / 12, mode="same")
        out.append(s * _env(len(s), 0.04, 0.12) * 0.32)
    return np.concatenate(out)


def sfx_stab():
    # horror-movie violin stab (detuned saws, tremolo)
    t = _t(1.3)
    s = sum(_sweep(f, f * 1.01, 1.3, "saw") for f in (1180, 1250, 1320, 1410))
    s *= (0.6 + 0.4 * np.sin(2 * np.pi * 22 * t)) * np.exp(-t * 2.2) * 0.12
    return s


def sfx_boom():
    t = _t(1.5)
    rng = np.random.default_rng(3)
    s = np.sin(2 * np.pi * np.cumsum(np.geomspace(120, 35, len(t))) / SR)
    n = np.convolve(rng.standard_normal(len(t)), np.ones(60) / 60, mode="same")
    return (s * 0.9 + n * 2.0) * np.exp(-t * 2.8) * 0.8


def sfx_pop():
    return _sweep(500, 1300, 0.09) * _env(int(0.09 * SR), 0.003, 0.03) * 0.5


def sfx_whoosh():
    rng = np.random.default_rng(4)
    t = _t(0.6)
    n = rng.standard_normal(len(t))
    k = np.convolve(n, np.ones(8) / 8, mode="same")
    return k * np.sin(np.pi * t / 0.6) ** 2 * 0.5


def sfx_step():
    rng = np.random.default_rng(5)
    t = _t(0.08)
    n = np.convolve(rng.standard_normal(len(t)), np.ones(18) / 18, mode="same")
    return (n * 2 + 0.4 * np.sin(2 * np.pi * 95 * t)) * np.exp(-t * 60) * 0.55


def sfx_scream():
    t = _t(1.1)
    f = 900 * (1 + 0.1 * np.sin(2 * np.pi * 7 * t)) * np.linspace(1, 1.25, len(t))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(6 * np.pi * np.cumsum(f) / SR)
    return s * _env(len(t), 0.03, 0.3) * 0.3


def sfx_cash():
    return np.concatenate([sfx_pop(), np.zeros(int(0.05 * SR)), sfx_ding() * 0.8])


def sfx_rimshot():
    rng = np.random.default_rng(6)
    out = np.zeros(int(1.3 * SR))
    for at, f, amp in ((0, 180, 0.7), (0.18, 180, 0.7), (0.45, 900, 1.0)):
        t = _t(0.35)
        n = rng.standard_normal(len(t))
        hit = (np.sin(2 * np.pi * f * t) * 0.6 + n * 0.5) * np.exp(-t * (30 if f < 500 else 9)) * amp
        i = int(at * SR)
        out[i:i + len(hit)] += hit * 0.5
    return out


SFX = {name[4:]: fn for name, fn in globals().items() if name.startswith("sfx_")}


def mix(total, lines, sfx_events, steps, music, duck_spans):
    """lines: [(t, array)], sfx_events: [(t, name, gain)], steps: [t]."""
    n = int(total * SR) + SR
    voice = np.zeros(n, dtype=np.float64)
    fx = np.zeros(n, dtype=np.float64)

    def put(buf, t, a, g=1.0):
        i = int(t * SR)
        if i >= n:
            return
        a = a[: n - i]
        buf[i:i + len(a)] += a * g

    for t, a in lines:
        put(voice, t, a)
    cache = {}
    for t, name, g in sfx_events:
        if name not in cache:
            cache[name] = SFX[name]()
        put(fx, t, cache[name], g)
    step = sfx_step()
    for t in steps:
        put(fx, t, step, 0.35)

    m = np.zeros(n)
    m[: len(music)] = music[:n]
    env = np.ones(n)
    for a, b in duck_spans:
        env[int(a * SR):int(b * SR)] = 0.38
    k = int(0.15 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    out = voice + fx + m * env
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    out = out[: int(total * SR)]
    out *= 0.95 / max(1e-6, np.max(np.abs(out)))
    return out.astype(np.float32)


def write_wav(path, a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1",
                    "-i", "-", "-ac", "2", path], input=a.tobytes(), check=True)


def envelope(a, fps):
    """Per-frame loudness 0..1 for lip/head animation."""
    hop = SR // fps
    nfr = len(a) // hop + 1
    out = np.zeros(nfr)
    for i in range(nfr):
        seg = a[i * hop:(i + 1) * hop]
        if len(seg):
            out[i] = np.sqrt(np.mean(seg ** 2))
    if out.max() > 0:
        out = np.clip(out / (np.percentile(out, 90) + 1e-6), 0, 1)
    return out
