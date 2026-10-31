"""Voices (Microsoft Edge neural TTS), procedural background music and sound effects."""
import asyncio
import hashlib
import json
import os
import subprocess
import wave

import numpy as np

SR = 44100
CACHE = os.path.join(os.path.dirname(__file__), "build", "tts")

# Leo: a cute child voice. Bruno: a deep, slow, friendly voice.
VOICES = {
    "leo": dict(voice="en-US-AnaNeural", rate="+12%", pitch="+0Hz"),
    "bruno": dict(voice="en-US-GuyNeural", rate="+6%", pitch="-22Hz"),
}


def _patch_certs():
    """Behind a TLS-intercepting proxy edge-tts must trust the proxy CA bundle."""
    bundle = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
    if os.path.exists(bundle):
        import certifi
        certifi.where = lambda: bundle


def tts(who, text):
    """Returns (mono float32 samples, [(word, start_s, end_s), ...]) — cached on disk."""
    os.makedirs(CACHE, exist_ok=True)
    cfg = VOICES[who]
    key = hashlib.sha1(json.dumps([cfg, text]).encode()).hexdigest()[:16]
    mp3, meta = os.path.join(CACHE, key + ".mp3"), os.path.join(CACHE, key + ".json")
    if not (os.path.exists(mp3) and os.path.exists(meta)):
        _patch_certs()
        import edge_tts

        async def run():
            words = []
            com = edge_tts.Communicate(text, cfg["voice"], rate=cfg["rate"], pitch=cfg["pitch"],
                                       boundary="WordBoundary")
            with open(mp3, "wb") as f:
                async for ch in com.stream():
                    if ch["type"] == "audio":
                        f.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        st = ch["offset"] / 1e7
                        words.append((ch["text"], st, st + ch["duration"] / 1e7))
            return words

        words = asyncio.run(run())
        with open(meta, "w") as f:
            json.dump(words, f)
    with open(meta) as f:
        words = [tuple(w) for w in json.load(f)]
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", mp3, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy(), words


def envelope(samples, fps):
    """Per-frame loudness 0..1 used for lip sync."""
    hop = SR // fps
    n = len(samples) // hop + 1
    env = np.zeros(n)
    for i in range(n):
        seg = samples[i * hop:(i + 1) * hop]
        if len(seg):
            env[i] = np.sqrt(np.mean(seg ** 2))
    peak = np.percentile(env[env > 0], 95) if np.any(env > 0) else 1
    env = np.clip(env / (peak + 1e-9), 0, 1)
    env[env < 0.12] = 0
    return env


# ---------------------------------------------------------------- synthesis
def _t(d):
    return np.arange(int(SR * d)) / SR


def pluck(f, d=0.45, a=0.3, decay=7.0):
    t = _t(d)
    y = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(4 * np.pi * f * t) + 0.18 * np.sin(6 * np.pi * f * t)
    att = np.minimum(1, t / 0.005)
    return a * y * np.exp(-decay * t) * att


def noise(d, seed=0):
    return np.random.default_rng(seed).uniform(-1, 1, int(SR * d))


def lowpass(x, k=0.1):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        y[i] = acc
    return y


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def music(dur, seed=1, bpm=116, key=60):
    """Happy little ukulele-style loop: I-V-vi-IV with a random pentatonic melody."""
    rng = np.random.default_rng(seed)
    out = np.zeros(int(SR * (dur + 1)))
    beat = 60 / bpm
    prog = [(0, 4, 7), (7, 11, 14), (9, 12, 16), (5, 9, 12)]
    penta = [0, 2, 4, 7, 9, 12, 14, 16]

    def add(sig, at):
        i = int(at * SR)
        if i >= len(out):
            return
        j = min(len(out), i + len(sig))
        out[i:j] += sig[:j - i]

    t, bar = 0.0, 0
    note = 4
    while t < dur:
        chord = prog[bar % 4]
        add(pluck(midi(key - 24 + chord[0]), 0.9, 0.35, 3.5), t)
        add(pluck(midi(key - 24 + chord[0]), 0.9, 0.25, 3.5), t + 2 * beat)
        for b in range(8):  # strum on the off-beats
            if b % 2 == 1:
                for k, iv in enumerate(chord):
                    add(pluck(midi(key - 12 + iv), 0.35, 0.07, 9), t + b * beat / 2 + k * 0.012)
        for b in range(8):  # melody in eighth notes
            if rng.random() < 0.72:
                note = int(np.clip(note + rng.integers(-2, 3), 0, len(penta) - 1))
                add(pluck(midi(key + penta[note]), 0.4, 0.13, 6), t + b * beat / 2)
        for b in range(8):  # soft shaker
            add(np.abs(noise(0.05, bar * 8 + b)) * np.exp(-60 * _t(0.05)) * 0.025, t + b * beat / 2)
        t += 4 * beat
        bar += 1
    return out[:int(SR * dur)]


def sfx(name):
    if name == "pop":
        t = _t(0.18)
        f = 900 * np.exp(-12 * t) + 300
        return 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-18 * t)
    if name == "buzz":
        t = _t(1.4)
        f = 210 + 25 * np.sin(2 * np.pi * 7 * t)
        saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
        return 0.16 * saw * np.minimum(1, t / 0.1) * np.minimum(1, (1.4 - t) / 0.3) * (0.7 + 0.3 * np.sin(2 * np.pi * 13 * t))
    if name == "whoosh":
        t = _t(0.9)
        n = lowpass(noise(0.9, 5), 0.08)
        return 0.9 * n * np.sin(np.pi * t / 0.9) ** 2
    if name == "dig":
        out = np.zeros(int(SR * 1.8))
        for i in range(8):
            burst = lowpass(noise(0.12, i), 0.25) * np.exp(-30 * _t(0.12)) * 0.6
            s = int(i * 0.22 * SR)
            out[s:s + len(burst)] += burst
        return out
    if name == "sparkle":
        out = np.zeros(int(SR * 1.0))
        for i, n in enumerate((84, 88, 91, 96, 100)):
            p = pluck(midi(n), 0.5, 0.12, 8)
            s = int(i * 0.07 * SR)
            out[s:s + len(p)] += p
        return out
    if name == "boing":
        t = _t(0.6)
        f = 180 + 120 * np.exp(-5 * t) * np.sin(2 * np.pi * 9 * t)
        return 0.45 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-4 * t)
    if name == "poof":
        t = _t(0.7)
        return 0.9 * lowpass(noise(0.7, 9), 0.06) * np.exp(-6 * t)
    if name == "rumble":
        t = _t(2.6)
        return 1.4 * lowpass(noise(2.6, 4), 0.02) * np.minimum(1, t / 0.4) * np.minimum(1, (2.6 - t) / 0.8)
    if name == "splash":
        t = _t(0.8)
        return 0.8 * lowpass(noise(0.8, 2), 0.3) * np.exp(-7 * t)
    if name == "plop":
        t = _t(0.25)
        f = 300 + 900 * t
        return 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-14 * t)
    if name == "ding":
        return pluck(midi(88), 0.8, 0.25, 4) + pluck(midi(95), 0.8, 0.15, 4)
    if name == "tada":
        out = np.zeros(int(SR * 1.0))
        for i, n in enumerate((72, 76, 79, 84)):
            p = pluck(midi(n), 0.8, 0.18, 4)
            s = int(i * 0.06 * SR)
            out[s:s + len(p)] += p
        return out
    raise ValueError(name)


def write_wav(path, x):
    x = np.tanh(x * 1.1)
    data = (np.clip(x, -1, 1) * 32000).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
