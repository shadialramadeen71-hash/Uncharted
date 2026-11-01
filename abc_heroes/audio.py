"""Music + voice generated entirely in code (numpy synthesis + espeak-ng TTS)."""
import os, shutil, subprocess, tempfile, wave
import numpy as np
from episodes import TUNES

SR = 44100
BPM = 120
BEAT = 60.0 / BPM
NOTE_IDX = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def parse_tune(s):
    out = []
    for tok in s.split():
        name, _, dur = tok.partition(":")
        midi = 12 * (int(name[-1]) + 1) + NOTE_IDX[name[0]]
        out.append((midi, float(dur) if dur else 1.0))
    return out


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def toy_piano(f, dur):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 4.0) * np.minimum(1, t / 0.005)
    w = np.sin(2*np.pi*f*t) + 0.35*np.sin(4*np.pi*f*t) + 0.12*np.sin(6*np.pi*f*t)
    return w * env


def bass(f, dur):
    t = np.arange(int(dur * SR)) / SR
    tri = 2 * np.abs(2 * ((f * t) % 1) - 1) - 1
    env = np.minimum(1, t / 0.01) * np.exp(-t * 2.5)
    return tri * env


def kick():
    t = np.arange(int(0.18 * SR)) / SR
    f = 50 + 90 * np.exp(-t * 30)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t * 18)


def noise_hit(dur, decay, hp=False, seed=0):
    rng = np.random.default_rng(seed)
    n = rng.uniform(-1, 1, int(dur * SR))
    if hp:
        n = np.diff(n, prepend=0)
    return n * np.exp(-np.arange(len(n)) / SR * decay)


CHORDS = {"C": (48, [0, 4, 7]), "F": (53, [5, 9, 0]), "G": (55, [7, 11, 2]),
          "Am": (57, [9, 0, 4])}


def add(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig * gain


def music(tune_name, length):
    n = int(length * SR)
    mel = np.zeros(n); bs = np.zeros(n); dr = np.zeros(n)
    notes = parse_tune(TUNES[tune_name])
    t = 0.0; bar_notes = {}
    while t < length:                       # loop the melody to fill length
        for midi, beats in notes:
            if t >= length:
                break
            d = beats * BEAT
            add(mel, toy_piano(hz(midi), max(d, 0.35) + 0.3), t, 0.30)
            bar_notes.setdefault(int(t // (4 * BEAT)), []).append(midi % 12)
            t += d
    for bar in range(int(np.ceil(length / (4 * BEAT)))):
        pcs = bar_notes.get(bar, [0])
        name = max(CHORDS, key=lambda c: sum(p in CHORDS[c][1] for p in pcs))
        root = CHORDS[name][0]
        for half in range(2):
            add(bs, bass(hz(root - 12 + (7 if half else 0)), 2 * BEAT), (bar*4 + half*2) * BEAT, 0.35)
    k, sn = kick(), noise_hit(0.15, 25, seed=1)
    for b in range(int(length / BEAT) + 1):
        bt = b * BEAT
        if b % 2 == 0:
            add(dr, k, bt, 0.55)
        else:
            add(dr, sn, bt, 0.16)
        add(dr, noise_hit(0.04, 120, hp=True, seed=b), bt + BEAT / 2, 0.07)
    return mel + bs + dr


def read_wav(path):
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    if sr != SR:
        x = np.interp(np.arange(int(len(x) * SR / sr)) * sr / SR, np.arange(len(x)), x)
    return x


def speak(text, tmpdir, idx):
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        return None
    path = os.path.join(tmpdir, f"v{idx}.wav")
    for voice in ("mb-us1", "en-us+f3"):    # friendly female voice, fallback
        r = subprocess.run([exe, "-v", voice, "-s", "150", "-p", "65", "-w", path, text],
                           capture_output=True)
        if r.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 1000:
            return read_wav(path)
    return None


def build_audio(ep, length, out_path):
    mix = music(ep["tune"], length)
    voice = np.zeros_like(mix)
    with tempfile.TemporaryDirectory() as td:
        for i, (at, text) in enumerate(ep["lines"]):
            v = speak(text, td, i)
            if v is not None:
                v = v / (np.abs(v).max() + 1e-9)
                add(voice, v, at, 0.9)
    # duck the music under the voice
    env = np.convolve(np.abs(voice), np.ones(2205) / 2205, mode="same")
    duck = 1.0 - 0.45 * np.clip(env * 8, 0, 1)
    out = mix * duck + voice
    fade = int(0.4 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = out / (np.abs(out).max() + 1e-9) * 0.89
    with wave.open(out_path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())
