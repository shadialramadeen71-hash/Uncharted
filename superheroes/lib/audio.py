"""Audio for an episode: Piper neural TTS dialogue, synthesized SFX + music,
lip-sync envelopes (per video frame) and ASS subtitles.

usage: python3 lib/audio.py ep1
"""
import importlib, json, os, subprocess, sys, wave
import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'episodes'))
VOICE_DIR = os.environ.get('PIPER_VOICES', '/tmp/claude-0/voices')
SR = 44100
FPS = 24

VOICES = {  # piper model, length scale (slower > 1), pitch shift (semitones), effect, subtitle colour (ASS BGR)
    'VOLT': dict(model='en_US-ryan-high', ls=0.92, pitch=0, fx=None, color='&H00FFC23F&'),
    'NOVA': dict(model='en_US-amy-medium', ls=0.95, pitch=0.5, fx=None, color='&H00D88BFF&'),
    'SHADE': dict(model='en_GB-alan-medium', ls=1.0, pitch=-4, fx='dark', color='&H00FF60C8&'),
    'SAM': dict(model='en_US-joe-medium', ls=0.95, pitch=0, fx=None, color='&H0030A0FF&'),
    'TITAN': dict(model='en_US-ryan-high', ls=1.15, pitch=-7, fx='robot', color='&H003030FF&'),
}

rng = np.random.default_rng(7)


# ------------------------------------------------------------------ helpers

def read_wav(p):
    with wave.open(p) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(1)
    return x, sr


def write_wav(p, x, sr=SR):
    x = np.clip(x, -1, 1)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    with wave.open(p, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def resample(x, sr_in, sr_out, pitch=0.0):
    """resample and optionally pitch-shift (changes duration like tape)"""
    r = 2 ** (pitch / 12)
    n = int(len(x) * sr_out / sr_in / r)
    t = np.arange(n) * (sr_in / sr_out) * r
    return np.interp(t, np.arange(len(x)), x).astype(np.float32)


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2), 'low')
    return signal.lfilter(b, a, x).astype(np.float32)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high')
    return signal.lfilter(b, a, x).astype(np.float32)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band')
    return signal.lfilter(b, a, x).astype(np.float32)


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    e = np.ones(n, np.float32) * s
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    A = min(A, n)
    e[:A] = np.linspace(0, 1, A)
    D2 = min(D, n - A)
    e[A:A + D2] = np.linspace(1, s, D2)
    if R < n:
        e[-R:] *= np.linspace(1, 0, R)
    return e


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def noise(dur):
    return rng.standard_normal(int(dur * SR)).astype(np.float32)


def reverb(x, mix=0.3, room=0.6):
    out = x.copy()
    for d, g in ((0.0297, 0.78), (0.0371, 0.74), (0.0411, 0.72), (0.0437, 0.7)):
        k = int(d * SR)
        y = np.zeros(len(x) + int(SR * 1.2), np.float32)
        y[:len(x)] += x
        for i in range(k, len(y), k):
            seg = y[i - k:i] * g * room
            y[i:i + k] += seg[:len(y[i:i + k])]
        out = out + mix * 0.25 * y[:len(x)]
    return out


# ------------------------------------------------------------------ voices

def tts(text, speaker, path):
    v = VOICES[speaker]
    model = os.path.join(VOICE_DIR, v['model'] + '.onnx')
    raw = path + '.raw.wav'
    subprocess.run([sys.executable, '-m', 'piper', '-m', model, '-f', raw, '--length-scale', str(v['ls'])],
                   input=text.encode(), check=True, capture_output=True)
    x, sr = read_wav(raw)
    os.remove(raw)
    x = resample(x, sr, SR, v['pitch'])
    # trim silence
    a = np.abs(x)
    idx = np.where(a > 0.01)[0]
    x = x[max(0, idx[0] - 200): idx[-1] + 2000]
    if v['fx'] == 'dark':
        x = x + 0.5 * lp(x, 300)
        pad = np.concatenate([x, np.zeros(int(SR * 0.6), np.float32)])
        x = reverb(pad, 0.7, 0.75)
    elif v['fx'] == 'robot':
        tt = np.arange(len(x)) / SR
        rm = x * np.sin(2 * np.pi * 55 * tt)
        x = 0.55 * x + 0.65 * rm
        x = np.round(x * 24) / 24
        x = lp(x, 5000)
        pad = np.concatenate([x, np.zeros(int(SR * 0.5), np.float32)])
        x = reverb(pad, 0.5, 0.6)
    x = x / (np.max(np.abs(x)) + 1e-6) * 0.85
    return x


def lip_env(x):
    hop = SR // FPS
    n = len(x) // hop + 1
    v = bp(x, 250, 3500)
    e = np.array([np.sqrt(np.mean(v[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(n)])
    ref = np.percentile(e, 92) + 1e-6
    e = np.clip(e / ref, 0, 1) ** 0.8
    e[e < 0.12] = 0
    # make sure the mouth closes sometimes between syllables
    return [round(float(a), 3) for a in e]


# ------------------------------------------------------------------ sfx

def sfx(kind, dur=None, **_):
    if kind == 'wind':
        x = lp(noise(dur), 500) * 0.6
        x *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * t_(dur) + 1)
        return x
    if kind == 'city':
        x = lp(noise(dur), 700) * 0.4
        for _ in range(4):  # distant horns
            s = rng.uniform(0, dur - 1)
            tt = t_(0.4)
            h = 0.06 * np.sign(np.sin(2 * np.pi * 330 * tt)) * env_adsr(len(tt), 0.02, 0.1, 0.8, 0.1)
            i = int(s * SR)
            x[i:i + len(h)] += lp(h, 1500)
        return x
    if kind == 'hum':
        tt = t_(dur)
        x = 0.4 * np.sin(2 * np.pi * 110 * tt) + 0.25 * np.sin(2 * np.pi * 220.7 * tt) + 0.1 * np.sin(
            2 * np.pi * 331 * tt)
        x *= 0.7 + 0.3 * np.sin(2 * np.pi * 3 * tt)
        x *= np.clip(tt / 0.5, 0, 1) * np.clip((dur - tt) / 0.3, 0, 1)
        return x
    if kind == 'powerdown':
        tt = t_(2.0)
        f = 400 * np.exp(-tt * 1.5) + 40
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.0)
        return x + 0.3 * lp(noise(2.0), 300) * np.exp(-tt * 2)
    if kind == 'thunder':
        d = 3.0
        tt = t_(d)
        crack = hp(noise(d), 2000) * np.exp(-tt * 18)
        rumble = lp(noise(d), 120) * 4 * np.exp(-tt * 1.1) * (1 + 0.5 * np.sin(2 * np.pi * 3 * tt))
        return crack * 1.2 + rumble
    if kind == 'impact':
        tt = t_(1.2)
        f = 90 * np.exp(-tt * 3) + 35
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4) * 1.4 + lp(noise(1.2), 900) * np.exp(-tt * 12)
    if kind in ('punch', 'land'):
        tt = t_(0.5)
        k = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-tt * 8) + 50) / SR) * np.exp(-tt * 9)
        return k + (0.8 if kind == 'punch' else 0.3) * bp(noise(0.5), 800, 4000) * np.exp(-tt * 30)
    if kind == 'charge':
        tt = t_(1.4)
        f = 150 + 900 * (tt / 1.4) ** 2
        return 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (tt / 1.4) + 0.2 * hp(noise(1.4), 3000) * (tt / 1.4)
    if kind == 'zap':
        tt = t_(dur)
        buzz = np.sign(np.sin(2 * np.pi * 60 * tt)) * 0.3
        crackle = hp(noise(dur), 1500) * (rng.random(len(tt)) < 0.02).astype(np.float32)
        crackle = lp(np.convolve(crackle, np.ones(60) / 6, 'same'), 9000)
        gate = (np.repeat(rng.random(int(dur * 40) + 1), SR // 40)[:len(tt)] > 0.25).astype(np.float32)
        x = (buzz + 1.2 * hp(noise(dur), 2500) * 0.5 + crackle) * (0.5 + 0.5 * gate)
        return x * np.clip(tt / 0.03, 0, 1) * np.clip((dur - tt) / 0.2, 0, 1)
    if kind == 'whoosh':
        d = 1.2
        tt = t_(d)
        x = noise(d)
        out = np.zeros_like(x)
        for i, fc in enumerate(np.linspace(300, 3000, 6)):
            seg = slice(int(i * len(x) / 6), int((i + 1) * len(x) / 6))
            out[seg] = bp(x, fc * 0.6, fc * 1.4)[seg]
        return out * np.sin(np.pi * tt / d) ** 2 * 1.6
    if kind == 'fallwind':
        tt = t_(dur)
        x = bp(noise(dur), 300, 1500) * (0.3 + 0.7 * tt / dur)
        return x * np.clip((dur - tt) / 0.3, 0, 1)
    if kind == 'creak':
        tt = t_(0.9)
        f = 70 + 30 * np.sin(2 * np.pi * 1.5 * tt)
        saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
        return bp(saw, 200, 1800) * np.sin(np.pi * tt / 0.9) * 1.2
    if kind == 'snap':
        tt = t_(1.5)
        clank = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * k) for f, k in ((523, 6), (1187, 8), (1730, 10), (2650, 12)))
        return 0.4 * clank + hp(noise(1.5), 1000) * np.exp(-tt * 25)
    if kind == 'catch':
        tt = t_(0.6)
        return lp(noise(0.6), 600) * np.exp(-tt * 10) * 1.2 + 0.4 * np.sin(2 * np.pi * 80 * tt) * np.exp(-tt * 10)
    if kind == 'powerup':
        tt = t_(2.5)
        f = 120 + 800 * (tt / 2.5) ** 1.5
        x = sum(np.sin(2 * np.pi * np.cumsum(f * m) / SR) / m for m in (1, 1.5, 2))
        return 0.35 * x * np.sin(np.pi * np.clip(tt / 2.5, 0, 1)) ** 0.5
    if kind == 'stomp':
        tt = t_(1.0)
        boom = np.sin(2 * np.pi * np.cumsum(60 * np.exp(-tt * 4) + 30) / SR) * np.exp(-tt * 5) * 1.6
        metal = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 14) for f in (310, 740, 1210)) * 0.15
        return boom + metal + lp(noise(1.0), 400) * np.exp(-tt * 8)
    if kind == 'robotglitch':
        tt = t_(1.6)
        f = 400 + 300 * np.sign(np.sin(2 * np.pi * 9 * tt))
        return 0.25 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-tt * 1.2)
    if kind == 'crash':
        d = 2.5
        tt = t_(d)
        boom = np.sin(2 * np.pi * np.cumsum(50 * np.exp(-tt * 2) + 25) / SR) * np.exp(-tt * 2.2) * 2
        debris = bp(noise(d), 500, 5000) * np.exp(-tt * 3) * (rng.random(len(tt)) < 0.5)
        metal = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5) for f in (220, 467, 911, 1503)) * 0.2
        return boom + debris + metal
    if kind == 'clap':
        tt = t_(0.3)
        return bp(noise(0.3), 1000, 5000) * np.exp(-tt * 40) * 2.5
    raise ValueError(kind)


# ------------------------------------------------------------------ music

NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)
PROGS = {
    'calm': ([57, 60, 64], [53, 57, 60], [55, 59, 62], [52, 55, 59]),
    'tense': ([45, 48, 52], [46, 49, 53], [45, 48, 52], [44, 47, 51]),
    'tense_drive': ([45, 48, 52], [41, 45, 48], [43, 47, 50], [40, 44, 47]),
    'action': ([50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 49, 52]),
    'heroic': ([48, 52, 55, 60], [43, 47, 50, 55], [45, 48, 52, 57], [41, 45, 48, 53]),
}


def saw(f, tt, detune=0.0):
    return 2 * ((f * (1 + detune) * tt) % 1) - 1


def music_section(mood, dur, bpm=112):
    tt = t_(dur)
    out = np.zeros(len(tt), np.float32)
    beat = 60 / bpm
    bar = beat * 4
    prog = PROGS[mood]
    nb = int(np.ceil(dur / bar))
    for b in range(nb):
        s, e = int(b * bar * SR), min(len(tt), int((b + 1) * bar * SR))
        if s >= len(tt):
            break
        seg = tt[s:e] - tt[s]
        chord = prog[b % len(prog)]
        pad = sum(saw(NOTE(m), seg) + saw(NOTE(m), seg, 0.004) for m in chord) / len(chord)
        pad *= env_adsr(e - s, 0.3 if mood in ('calm', 'tense') else 0.05, 0.3, 0.8, 0.3)
        out[s:e] += 0.18 * pad
        if mood != 'calm':  # bass pulse
            for q in range(8):
                qs = s + int(q * beat / 2 * SR)
                if qs >= e:
                    break
                n_ = min(int(beat / 2 * SR), e - qs)
                st = np.arange(n_) / SR
                out[qs:qs + n_] += 0.22 * saw(NOTE(chord[0] - 12), st) * np.exp(-st * 6)
        if mood in ('action', 'heroic', 'tense_drive'):  # drums
            for q in range(4):
                qs = s + int(q * beat * SR)
                if qs >= e:
                    break
                n_ = min(int(0.35 * SR), e - qs)
                st = np.arange(n_) / SR
                kick = np.sin(2 * np.pi * np.cumsum(110 * np.exp(-st * 25) + 45) / SR) * np.exp(-st * 9)
                out[qs:qs + n_] += 0.5 * kick
                if q % 2 == 1:
                    sn = hp(noise(0.35), 1500)[:n_] * np.exp(-st * 18)
                    out[qs:qs + n_] += 0.18 * sn
        if mood == 'heroic':  # brass-ish lead on top note
            top = chord[-1] + 12
            lead = saw(NOTE(top), seg) * env_adsr(e - s, 0.08, 0.4, 0.6, 0.3)
            out[s:e] += 0.07 * lead
    return lp(out, 4000 if mood in ('action', 'heroic') else 2200)


# ------------------------------------------------------------------ main

def ass_time(t):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'


def build(ep):
    story = importlib.import_module(ep + '_story')
    out = os.path.join(ROOT, 'build', ep)
    os.makedirs(os.path.join(out, 'lines'), exist_ok=True)
    N = int(story.DURATION * SR)
    voice = np.zeros(N, np.float32)
    lips = []
    events = []
    for i, (t0, spk, text) in enumerate(story.DIALOGUE):
        x = tts(text, spk, os.path.join(out, 'lines', f'{i:02d}'))
        write_wav(os.path.join(out, 'lines', f'{i:02d}_{spk}.wav'), x)
        s = int(t0 * SR)
        n = min(len(x), N - s)
        voice[s:s + n] += x[:n]
        dur = len(x) / SR
        lips.append(dict(speaker=spk, start_frame=int(round(t0 * FPS)) + 1, env=lip_env(x), text=text))
        events.append((t0, t0 + dur, spk, text))
        print(f'{t0:5.2f}-{t0 + dur:5.2f}  {spk}: {text}')
    for a, b in zip(events, events[1:]):
        if a[1] > b[0] + 0.05:
            print(f'  !! overlap: "{a[3]}" ends {a[1]:.2f} > next starts {b[0]:.2f}')
    if events[-1][1] > story.DURATION:
        print('  !! last line runs past end')
    with open(os.path.join(out, 'lipsync.json'), 'w') as f:
        json.dump(lips, f)

    fx = np.zeros(N, np.float32)
    for t0, kind, kw in story.SFX:
        x = sfx(kind, **kw) * kw.get('gain', 1.0)
        s = int(t0 * SR)
        n = min(len(x), N - s)
        fx[s:s + n] += x[:n]

    mus = np.zeros(N, np.float32)
    for a, b, mood in story.MUSIC:
        x = music_section(mood, b - a + 0.4)
        x[-int(0.4 * SR):] *= np.linspace(1, 0, int(0.4 * SR))
        x[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
        s = int(a * SR)
        n = min(len(x), N - s)
        mus[s:s + n] += x[:n]
    # duck music under dialogue
    ve = np.convolve(np.abs(voice), np.ones(4410) / 4410, 'same')
    duck = 1 - 0.6 * np.clip(ve / 0.05, 0, 1)
    mix = voice * 1.0 + fx * 0.45 + mus * 0.32 * duck
    tt = np.arange(N) / SR
    mix *= np.clip((story.DURATION - tt) / 0.6, 0, 1)
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    write_wav(os.path.join(out, 'mix.wav'), mix * 0.9)

    # subtitles (ASS) - speaker name in their colour + white line, title card at start
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,DejaVu Sans,60,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,5,2,2,90,90,430,1
Style: Title,DejaVu Sans,120,&H0000D7FF,&H000000FF,&H00000000,&H96000000,1,0,0,0,100,100,4,0,1,7,4,8,60,60,230,1
Style: Subtitle,DejaVu Sans,56,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,1,1,0,0,100,100,2,0,1,4,3,8,60,60,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f'Dialogue: 1,{ass_time(0.15)},{ass_time(2.9)},Title,,0,0,0,,{{\\fad(250,400)}}{story.TITLE}',
             f'Dialogue: 1,{ass_time(0.35)},{ass_time(2.9)},Subtitle,,0,0,0,,{{\\fad(300,400)}}{story.SUBTITLE}']
    for a, b, spk, text in events:
        col = VOICES[spk]['color']
        lines.append(f'Dialogue: 0,{ass_time(a)},{ass_time(b + 0.35)},Sub,,0,0,0,,'
                     f'{{\\c{col}}}{spk}: {{\\c&H00FFFFFF&}}{text}')
    with open(os.path.join(out, 'subs.ass'), 'w') as f:
        f.write(head + '\n'.join(lines) + '\n')


if __name__ == '__main__':
    for ep in sys.argv[1:]:
        print('==', ep)
        build(ep)
