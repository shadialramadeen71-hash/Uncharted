"""Original 1930s-style swing tune (stride piano + clarinet + brushes) with a gramophone filter."""
import sys
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 44100
BPM = 132
BEAT = 60 / BPM
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 260
rng = np.random.default_rng(1931)
N = int(DUR * SR)
mix = np.zeros(N)

def midi(m): return 440 * 2 ** ((m - 69) / 12)

def add(sig, t):
    i = int(t * SR)
    if i >= N: return
    j = min(N, i + len(sig))
    mix[i:j] += sig[: j - i]

def piano(m, dur, vel):
    t = np.arange(int((dur + 0.6) * SR)) / SR
    f = midi(m)
    s = sum(np.sin(2 * np.pi * f * k * t * (1 + 0.0004 * k)) * (0.6 ** (k - 1)) * np.exp(-t * (2.2 + k * 0.9)) for k in range(1, 7))
    env = np.minimum(1, t / 0.004) * np.where(t < dur, 1, np.exp(-(t - dur) * 12))
    return vel * s * env

def clarinet(m, dur, vel):
    t = np.arange(int((dur + 0.08) * SR)) / SR
    f = midi(m)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.25)
    ph = 2 * np.cumsum(np.pi * f * vib / SR)
    s = sum(np.sin(k * ph) / k for k in (1, 3, 5, 7, 9)) + 0.15 * np.sin(2 * ph)
    env = np.minimum(1, t / 0.03) * np.where(t < dur, 1, np.exp(-(t - dur) * 40)) * (1 - 0.15 * t / max(dur, 0.1))
    return vel * s * env

def brush(vel, length=0.12):
    n = int(length * SR)
    s = rng.standard_normal(n) * np.exp(-np.linspace(0, 6, n))
    return vel * sosfilt(butter(2, [3000, 9000], 'bandpass', fs=SR, output='sos'), s)

def kick(vel):
    t = np.arange(int(0.25 * SR)) / SR
    return vel * np.sin(2 * np.pi * (55 + 60 * np.exp(-t * 30)) * t) * np.exp(-t * 14)

# chords: (bass root midi, chord tones midi)
C6 = (36, [52, 55, 57, 60]); A7 = (33, [52, 55, 57, 61]); Dm7 = (38, [53, 57, 60, 62]); G7 = (31, [53, 55, 59, 62])
D7 = (38, [54, 57, 60, 62]); F6 = (41, [53, 57, 60, 62]); Fm6 = (41, [53, 56, 60, 62]); E7 = (40, [52, 56, 59, 62])
Cm = (36, [51, 55, 60, 63]); Ab7 = (32, [51, 54, 56, 60])
A_SEC = [C6, A7, Dm7, G7, C6, A7, D7, G7, F6, Fm6, C6, A7, Dm7, G7, C6, G7]
B_SEC = [Cm, Cm, Fm6, Fm6, Cm, Ab7, G7, G7]
FORM = A_SEC + B_SEC + A_SEC

# a fixed 2-bar clarinet riff shape (scale degrees relative to chord tones), swung eighths
RIFF = [(0, 0, 1.5), (1.5, 2, 0.5), (2, 3, 1), (3, 2, 0.5), (3.5, 1, 0.5),
        (4, 3, 1), (5, 2, 0.5), (5.5, 1, 0.5), (6, 0, 1.5)]

def swing(beat_pos):
    whole = np.floor(beat_pos); frac = beat_pos - whole
    return (whole + (0.66 if abs(frac - 0.5) < 1e-6 else frac)) * BEAT

bar = 0
t0 = 0.0
while t0 < DUR:
    root, tones = FORM[bar % len(FORM)]
    # stride left hand: bass on 1 & 3, chord on 2 & 4
    add(piano(root, BEAT * 0.8, 0.32), t0)
    add(piano(root + 7 if root < 36 else root - 5, BEAT * 0.8, 0.28), t0 + 2 * BEAT)
    for b in (1, 3):
        for m in tones:
            add(piano(m, BEAT * 0.45, 0.10), t0 + b * BEAT)
    # walking-ish upright bass
    for b, iv in enumerate((0, 4, 7, 9)):
        add(piano(root - 12 + iv, BEAT * 0.9, 0.18) * 0.9, t0 + b * BEAT)
    # drums: brushes on every beat + swung offbeat, soft kick
    for b in range(4):
        add(brush(0.10 if b % 2 else 0.06), t0 + b * BEAT)
        add(brush(0.04, 0.06), t0 + (b + 0.66) * BEAT)
        add(kick(0.18), t0 + b * BEAT)
    # clarinet riff over each pair of bars, skip every 8th bar for a breath
    if bar % 2 == 0 and bar % 16 != 14:
        up = tones + [t + 12 for t in tones]
        for (pos, deg, ln) in RIFF:
            vel = 0.13 + 0.03 * rng.random()
            note = up[deg % len(up)] + 12
            add(clarinet(note, ln * BEAT * 0.92, vel), t0 + swing(pos))
    bar += 1
    t0 += 4 * BEAT

# --- gramophone treatment ---
mix = np.tanh(mix * 1.4)
mix = sosfilt(butter(3, [220, 3600], 'bandpass', fs=SR, output='sos'), mix)
# wow & flutter via resampling with slowly varying rate
tt = np.arange(N)
warp = tt + 0.0018 * SR * np.sin(2 * np.pi * 0.55 * tt / SR) / (2 * np.pi * 0.55)
mix = np.interp(warp, tt, mix)
hiss = sosfilt(butter(2, [2000, 8000], 'bandpass', fs=SR, output='sos'), rng.standard_normal(N)) * 0.012
crackle = np.zeros(N)
idx = rng.choice(N, int(DUR * 9), replace=False)
crackle[idx] = rng.standard_normal(len(idx)) * 0.35
crackle = sosfilt(butter(2, 1500, 'highpass', fs=SR, output='sos'), crackle)
mix = mix + hiss + crackle
fade = int(3 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)
mix[:int(0.5 * SR)] *= np.linspace(0, 1, int(0.5 * SR))
mix = mix / np.max(np.abs(mix)) * 0.8
wavfile.write(sys.argv[1], SR, (mix * 32767).astype(np.int16))
print("ok", DUR)
