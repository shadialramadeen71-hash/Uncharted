"""Hop Hop Froggy — an original kids' song. Builds the full audio (backing + sung TTS vocals) and a timing map."""
import json, os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "build", "words")
os.makedirs(CACHE, exist_ok=True)
SR, BPM = 44100, 120
BEAT = 60 / BPM
BAR = 4 * BEAT
VOICE_F0 = 230.0
rng = np.random.default_rng(3)

# ---------------------------------------------------------------- the song (original lyrics and melody)
VERSES = [
    dict(lead=("Baby", "Froggy"), hook="hop", last=["Splash", "in", "the", "pond!"], who="baby", key=0),
    dict(lead=("Mommy", "Froggy"), hook="hop", last=["Give", "a", "big", "hug!"], who="mommy", key=0),
    dict(lead=("Daddy", "Froggy"), hook="hop", last=["Biggest", "jump", "ever!"], who="daddy", key=0),
    dict(lead=("Grandma", "Froggy"), hook="hop", last=["Slow", "and", "steady!"], who="grandma", key=1),
    dict(lead=("Grandpa", "Froggy"), hook="hop", last=["Ribbit", "ribbit", "ribbit!"], who="grandpa", key=1),
    dict(lead=("Raindrops", "falling"), hook=("splish", "splash", "splish"), last=["Froggies", "love", "the", "rain!"], who="rain", key=3),
    dict(lead=("Rainbow", "colors"), hook="wow", last=["Look", "up", "in", "the", "sky!"], who="rainbow", key=3),
    dict(lead=("Sleepy", "Froggies"), hook="yawn", last=["Goodnight,", "everyone!"], who="night", key=0, soft=True),
]
INTRO_BARS, OUTRO_BARS = 4, 4
# melody per line, MIDI notes for: lead1 lead2 h h h | h h h   (beats: 1 1 .5 .5 1 | .5 .5 1 rest 2)
HOOK_RHYTHM = [1, 1, 0.5, 0.5, 1, 0.5, 0.5, 1]
LINE_NOTES = [
    [67, 64, 72, 72, 72, 69, 69, 67],
    [69, 65, 74, 74, 74, 71, 71, 69],
    [67, 64, 72, 72, 72, 69, 69, 67],
]
CHORDS = [  # one chord per bar, 8 bars per verse (root midi, quality)
    (48, "maj"), (45, "min"), (53, "maj"), (55, "maj"), (48, "maj"), (45, "min"), (53, "maj"), (55, "maj")]


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def verse_words(v):
    """Returns [(text, beat_offset, beats, midi)] for one 8-bar verse."""
    out = []
    hook = v["hook"] if isinstance(v["hook"], tuple) else (v["hook"],) * 3
    for li in range(3):
        b = li * 8
        words = [v["lead"][0], v["lead"][1], hook[0], hook[1], hook[2], hook[0], hook[1], hook[2]]
        for w, d, n in zip(words, HOOK_RHYTHM, LINE_NOTES[li]):
            out.append((w, b, d, n)); b += d
    b = 24
    out.append((v["lead"][0], b, 1, 67)); out.append((v["lead"][1], b + 1, 1, 67))
    last = v["last"]
    notes = [69, 71, 72, 74, 72][:len(last)]
    notes[-1] = 72
    b += 2
    for i, w in enumerate(last):
        d = 1 if i < len(last) - 1 else max(1, 5 - (len(last) - 1))
        out.append((w, b, d, notes[i])); b += d
    return out


def timeline():
    """Absolute word timings plus section markers."""
    words, verses = [], []
    t0 = INTRO_BARS * BAR
    for vi, v in enumerate(VERSES):
        start = t0 + vi * 8 * BAR
        verses.append(dict(index=vi, who=v["who"], start=start, end=start + 8 * BAR))
        for w, b, d, n in verse_words(v):
            words.append(dict(text=w, start=start + b * BEAT, dur=d * BEAT, midi=n + v["key"], verse=vi,
                              line=int(b // 8)))
    total = t0 + len(VERSES) * 8 * BAR + OUTRO_BARS * BAR + 1.5
    return dict(words=words, verses=verses, intro_end=t0, outro_start=t0 + len(VERSES) * 8 * BAR, total=total,
                bpm=BPM, beat=BEAT)


# ---------------------------------------------------------------- synths
def env_ad(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    return 0.9 * np.sin(2 * np.pi * (50 * t + 60 * (1 - np.exp(-t * 30)) / 30)) * np.exp(-t * 9)


def snare():
    n = int(0.22 * SR); t = np.arange(n) / SR
    return 0.45 * (rng.standard_normal(n) * np.exp(-t * 20) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25))


def hat():
    n = int(0.06 * SR); x = rng.standard_normal(n)
    x = x - np.convolve(x, np.ones(4) / 4, "same")
    return 0.18 * x * np.exp(-np.arange(n) / SR * 60)


def marimba(f, dur):
    n = int(max(dur, 0.25) * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 18)) * env_ad(n, 0.003, 0.35)


def musicbox(f, dur):
    n = int(max(dur, 0.6) * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * 2 * t) + 0.3 * np.sin(2 * np.pi * f * 6 * t)) * env_ad(n, 0.002, 0.6) * 0.6


def bass(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    return 0.55 * x * np.minimum(1, t / 0.01) * np.minimum(1, (dur - t) / 0.05)


def pluck(freqs, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * t) for f in freqs)
    x = np.convolve(x, np.ones(6) / 6, "same")
    return 0.12 * x * env_ad(n, 0.003, 0.12)


def ribbit():
    n = int(0.45 * SR); t = np.arange(n) / SR
    gate = (np.sin(2 * np.pi * 22 * t) > 0) * np.exp(-t * 5)
    return 0.5 * np.sign(np.sin(2 * np.pi * (180 - 60 * t) * t)) * gate * 0.6


def splash():
    n = int(0.8 * SR); t = np.arange(n) / SR
    x = np.convolve(rng.standard_normal(n), np.ones(5) / 5, "same") * np.exp(-t * 5)
    return 0.6 * x


def add(buf, x, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    buf[i:i + len(x)] += x[: len(buf) - i]


# ---------------------------------------------------------------- sung vocals
def run(*cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def tts_word(word, tld):
    from gtts import gTTS
    key = "".join(ch for ch in word.lower() if ch.isalnum())
    path = os.path.join(CACHE, f"{key}_{tld}.wav")
    if not os.path.exists(path):
        mp3 = path[:-4] + ".mp3"
        gTTS(word.strip(",!"), lang="en", tld=tld).save(mp3)
        run("ffmpeg", "-y", "-i", mp3, "-af",
            "silenceremove=start_periods=1:start_threshold=-40dB,areverse,silenceremove=start_periods=1:start_threshold=-40dB,areverse",
            "-ac", "1", "-ar", "24000", path)
    return path


_F0 = {}


def measured_f0(path, sr=24000):
    """Median pitch of the voiced part of a TTS word (frame-wise autocorrelation)."""
    if path in _F0:
        return _F0[path]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         check=True, stdout=subprocess.PIPE).stdout
    x = np.frombuffer(raw, np.float32)
    fs, N = [], 1024
    peak = np.abs(x).max() + 1e-9
    for i in range(0, len(x) - N, N // 2):
        seg = x[i:i + N]
        if np.sqrt(np.mean(seg ** 2)) < 0.08 * peak:
            continue
        ac = np.correlate(seg, seg, "full")[N - 1:]
        lo, hi = sr // 450, sr // 120
        fs.append(sr / (lo + np.argmax(ac[lo:hi])))
    _F0[path] = float(np.median(fs)) if fs else VOICE_F0
    return _F0[path]


def atempo_chain(r):
    parts = []
    while r > 2.0:
        parts.append("atempo=2.0"); r /= 2.0
    while r < 0.5:
        parts.append("atempo=0.5"); r /= 0.5
    parts.append(f"atempo={r:.5f}")
    return ",".join(parts)


def sing(word, midi, dur, tld="us"):
    src = tts_word(word, tld)
    key = "".join(ch for ch in word.lower() if ch.isalnum())
    out = os.path.join(CACHE, f"sung_{key}_{tld}_{midi}_{int(dur * 1000)}.wav")
    if not os.path.exists(out):
        with wave.open(src) as w:
            n = w.getnframes()
        length = n / 24000
        f = midi_hz(midi) / measured_f0(src)
        target = max(0.18, dur * 0.9)
        r = (length / f) / target
        run("ffmpeg", "-y", "-i", src, "-af", f"asetrate={int(24000 * f)},aresample={SR},{atempo_chain(r)}", "-ac", "1", out)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, stdout=subprocess.PIPE).stdout
    x = np.frombuffer(raw, np.float32).copy()
    fade = min(len(x) // 4, int(0.02 * SR))
    if fade > 0:
        x[:fade] *= np.linspace(0, 1, fade); x[-fade:] *= np.linspace(1, 0, fade)
    return x / (np.abs(x).max() + 1e-6)


# ---------------------------------------------------------------- mix
def build(path_wav, path_json):
    T = timeline()
    n = int(T["total"] * SR)
    drums, bassb, chords, lead, vox, fx = (np.zeros(n) for _ in range(6))
    bars_total = int((T["outro_start"] + OUTRO_BARS * BAR) / BAR)
    for bar in range(bars_total):
        t = bar * BAR
        vi = int((t - T["intro_end"]) // (8 * BAR)) if t >= T["intro_end"] else -1
        in_outro = t >= T["outro_start"]
        v = VERSES[vi] if 0 <= vi < len(VERSES) and not in_outro else None
        soft = v is not None and v.get("soft")
        key = v["key"] if v else 0
        root, q = CHORDS[bar % 8]
        root += key
        third = 3 if q == "min" else 4
        tones = [midi_hz(root + 12), midi_hz(root + 12 + third), midi_hz(root + 19)]
        if not soft:
            for b in range(4):
                add(drums, kick() if b in (0, 2) else snare(), t + b * BEAT)
                add(drums, hat(), t + b * BEAT + BEAT / 2)
                add(bassb, bass(midi_hz(root - 12 + (7 if b == 2 else 0)), BEAT * 0.9), t + b * BEAT)
                add(chords, pluck(tones, BEAT * 0.45), t + b * BEAT + BEAT / 2)
        else:
            for b in range(4):
                add(chords, musicbox(tones[b % 3] / 2, BEAT * 1.2) * 0.35, t + b * BEAT)
    # intro / outro melody on the marimba
    for start in (0.0, T["outro_start"]):
        for li in (0, 1):
            b = li * 8
            for d, m in zip(HOOK_RHYTHM, LINE_NOTES[li]):
                add(lead, marimba(midi_hz(m), d * BEAT) * 0.5, start + b * BEAT); b += d
    add(fx, ribbit(), 0.2); add(fx, ribbit(), BAR * 2 + 0.2); add(fx, ribbit(), T["outro_start"] + BAR * 3.5)
    # sung words + doubled marimba melody
    for w in T["words"]:
        v = VERSES[w["verse"]]
        inst = musicbox if v.get("soft") else marimba
        add(lead, inst(midi_hz(w["midi"]), w["dur"]) * 0.28, w["start"])
        a = sing(w["text"], w["midi"], w["dur"], "us")
        b = sing(w["text"], w["midi"], w["dur"], "com.au")
        add(vox, a * 0.6, w["start"]); add(vox, b * 0.4, w["start"] + 0.012)
        if w["text"].startswith("Splash") or w["text"].startswith("splash"):
            add(fx, splash() * 0.6, w["start"] + 0.1)
        if w["text"].lower().startswith("ribbit"):
            add(fx, ribbit() * 0.5, w["start"] + w["dur"] * 0.5)
    yay = sing("Yay!", 76, 1.0, "us")
    add(vox, yay * 0.7, T["outro_start"] + BAR * 3)
    # simple echo on vocals
    d = int(0.18 * SR)
    vox[d:] += vox[:-d] * 0.18
    mix = drums * 0.55 + bassb * 0.5 + chords * 0.6 + lead * 0.55 + vox * 0.9 + fx * 0.6
    fade = int(1.5 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix * 1.2) * 0.9
    stereo = np.stack([mix, np.roll(mix, 30)], 1)
    with wave.open(path_wav, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((stereo * 32767).astype(np.int16).tobytes())
    with open(path_json, "w") as f:
        json.dump(T, f, indent=1)
    return T


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    T = build(os.path.join(HERE, "build", "song.wav"), os.path.join(HERE, "build", "song.json"))
    print(f"total {T['total']:.1f}s, {len(T['words'])} sung words")
