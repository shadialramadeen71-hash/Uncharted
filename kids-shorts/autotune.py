"""TD-PSOLA: puts a spoken word onto one exact musical note and stretches it to a given length,
keeping the voice's natural timbre (no chipmunk effect)."""
import numpy as np


def frame_f0(x, sr, i, n=1024, lo=120, hi=450):
    seg = x[max(0, i - n // 2): i + n // 2]
    if len(seg) < n // 2 or np.sqrt(np.mean(seg ** 2)) < 0.06 * (np.abs(x).max() + 1e-9):
        return 0.0
    seg = seg - seg.mean()
    ac = np.correlate(seg, seg, "full")[len(seg) - 1:]
    a, b = sr // hi, sr // lo
    lag = a + int(np.argmax(ac[a:b]))
    if ac[lag] < 0.3 * ac[0]:
        return 0.0
    return sr / lag


def pitch_marks(x, sr):
    marks, p = [], 0
    hop = int(0.01 * sr)
    while p < len(x):
        f = frame_f0(x, sr, p, sr // 24)
        if f <= 0:
            marks.append((p, 0)); p += hop; continue
        T = int(sr / f)
        a, b = p + int(0.8 * T), min(len(x), p + int(1.2 * T))
        if a >= b:
            break
        q = a + int(np.argmax(np.abs(x[a:b])))
        marks.append((q, T)); p = q
    return marks


def psola(x, sr, target_hz, out_len):
    marks = pitch_marks(x, sr)
    if not marks:
        return np.zeros(int(out_len * sr))
    n_out = int(out_len * sr)
    y = np.zeros(n_out + sr)
    Tt = int(sr / target_hz)
    pos = [m[0] for m in marks]
    s = 0
    while s < n_out:
        u = s * len(x) / n_out
        k = int(np.argmin(np.abs(np.array(pos) - u)))
        c, T = marks[k]
        voiced = T > 0
        half = T if voiced else int(0.01 * sr)
        a, b = max(0, c - half), min(len(x), c + half)
        seg = x[a:b] * np.hanning(b - a) if b - a > 4 else np.zeros(1)
        st = s - (c - a)
        if st >= 0:
            y[st:st + len(seg)] += seg
        s += Tt if voiced else int(0.01 * sr)
    y = y[:n_out]
    fade = min(len(y) // 4, int(0.015 * sr))
    if fade:
        y[:fade] *= np.linspace(0, 1, fade); y[-fade:] *= np.linspace(1, 0, fade)
    return y / (np.abs(y).max() + 1e-6)
