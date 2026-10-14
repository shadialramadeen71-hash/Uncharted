"""OFFICE SQUAD - episode scripts (built on the WOBBLES engine)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "wobbles"))
sys.path.insert(1, os.path.join(HERE, "..", "mask-buddies"))

import numpy as np  # noqa: E402

import audio  # noqa: E402
import wob_engine  # noqa: E402
import sq_chars  # noqa: E402
import sq_world  # noqa: E402
from wob_engine import Episode  # noqa: E402

# ---- plug the squad into the engine ------------------------------------------
wob_engine.CAST.update(sq_chars.CAST)
wob_engine.SCENES.update(sq_world.SCENES)
wob_engine.SHOW.update(title="OFFICE SQUAD", logo="OFFICE SQUAD")
audio.CACHE = os.path.join(HERE, "build", "voice_cache")
wob_engine.NAMES.update({
    "mo": ("MIGHTY MO", "#e53935"), "boss": ("MR. BALDWIN", "#33415c"), "noor": ("NOOR", "#8e2b3a"),
    "ruby": ("RUBY", "#e8642c"), "grace": ("GRACE (HR)", "#1f1f24"), "kiki": ("KIKI", "#1fb2d4"),
    "steve": ("SPACE STEVE", "#78909c"), "pixel": ("PIXEL", "#f39a3d"),
})
audio.VOICES.update({
    "mo": dict(voice="en-US-ChristopherNeural", rate="+6%", pitch="-4Hz",
               af="aecho=0.8:0.5:40:0.18,volume=1.2"),
    "boss": dict(voice="en-GB-ThomasNeural", rate="-6%", pitch="-14Hz", af="volume=1.25"),
    "noor": dict(voice="en-US-AvaNeural", rate="-2%", pitch="+0Hz", af="volume=1.15"),
    "ruby": dict(voice="en-GB-LibbyNeural", rate="+4%", pitch="+2Hz", af="volume=1.15"),
    "grace": dict(voice="en-US-AriaNeural", rate="-6%", pitch="-8Hz", af="volume=1.15"),
    "kiki": dict(voice="en-US-JennyNeural", rate="+14%", pitch="+22Hz", af="volume=1.15"),
    # inside a helmet: band-limited radio with a little echo
    "steve": dict(voice="en-US-SteffanNeural", rate="-8%", pitch="-2Hz",
                  af="highpass=f=300,lowpass=f=3200,aecho=0.8:0.7:22:0.45,volume=1.6"),
})


# ---- extra SFX ---------------------------------------------------------------
def sfx_typing():
    rng = np.random.default_rng(21)
    n = int(2.4 * audio.SR)
    out = np.zeros(n)
    t = 0.0
    while t < 2.3:
        k = audio._t(0.03)
        click = rng.standard_normal(len(k)) * np.exp(-k * 260) + np.sin(2 * np.pi * 1900 * k) * np.exp(-k * 200)
        i = int(t * audio.SR)
        out[i:i + len(click)] += click * rng.uniform(0.25, 0.5)
        t += rng.uniform(0.05, 0.13)
    return out * 0.6


def sfx_meow():
    t = audio._t(0.8)
    f = 520 + 380 * np.sin(np.pi * t / 0.8) ** 1.5
    ph = 2 * np.pi * np.cumsum(f) / audio.SR
    s = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)
    s *= 0.6 + 0.4 * np.sin(np.pi * t / 0.8)
    return s * audio._env(len(t), 0.05, 0.25) * 0.3


def sfx_burp():
    rng = np.random.default_rng(22)
    t = audio._t(0.7)
    f = 95 * (1 + 0.25 * rng.standard_normal(len(t)).cumsum() / len(t) * 40)
    f = np.clip(f, 60, 140)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / audio.SR))
    s = np.convolve(s, np.ones(40) / 40, mode="same")
    return s * audio._env(len(t), 0.03, 0.2) * 0.7


for _fn in (sfx_typing, sfx_meow, sfx_burp):
    audio.SFX[_fn.__name__[4:]] = _fn

MUSIC = os.path.join(HERE, "..", "mask-buddies", "assets", "music")
FIGARO = os.path.join(MUSIC, "figaro.mp3")
SALT = os.path.join(MUSIC, "saltarello.mp3")
KING = os.path.join(MUSIC, "mountain_king.mp3")

SQUAD = ("boss", "noor", "ruby", "mo", "grace", "kiki", "steve", "pixel")


def title_card(e):
    """The poster: everyone pops in, then the ribbon banner."""
    e.cut("burst", cam={"x": 1130, "y": -600, "z": 0.68}, music=(FIGARO, 0.0))
    poses = {
        "noor": (690, -3, 150, "hold", "mug", "happy"),
        "boss": (1000, -2, 170, "swing", None, "shock"),
        "ruby": (1310, -1, 150, "hold", "mallet", "happy"),
        "mo": (560, 1, 0, "hero", None, "shock"),
        "grace": (830, 2, 0, "hold", "clipboard", "shock"),
        "kiki": (1170, 3, 0, "up", None, "shock"),
        "steve": (1440, 4, 0, "wave", None, "shock"),
        "pixel": (1700, 6, 0, "swing", None, None),
    }
    for i, n in enumerate(("boss", "noor", "ruby", "mo", "grace", "kiki", "steve", "pixel")):
        x, z, lift, arms, item, mood = poses[n]
        t = 0.25 + i * 0.22
        e.place(n, x, facing=1, at=t, z=z, lift=float(lift), arms=arms, item=item, mood=mood, sit=False)
        e.jump(n, 110, 0.35, at=t)
        e.sfx("pop", at=t, gain=0.8)
    e.var("banner", 1.0, at=2.3, dur=0.5)
    e.sfx("whoosh", at=2.2)
    e.sfx("fanfare", at=2.5)
    e.wait(6.0)


def reset(e, *names):
    for n in names:
        e.set(n, lift=0.0, arms="swing", item=None, mood=None, sit=False, z=1)


def ep1():
    e = Episode(1, "The Last Slice")
    for n in SQUAD:
        e.add(n, z=1)
    title_card(e)

    # ---------------- BREAK ROOM: one slice left -----------------------------
    e.cut("breakroom", music=(SALT, 4.0))
    e.hide(*SQUAD)
    reset(e, *SQUAD)
    e.var("slices", 1)
    e.place("kiki", -300, facing=1, z=3)
    e.walk("kiki", 760, style="run", wait=True)
    e.arms("kiki", "up")
    e.mood("kiki", "happy")
    e.say("kiki", "One slice left! Protein! ...ish.")
    e.arms("kiki", "swing")
    t = e.cursor
    e.place("mo", 1420, facing=-1, z=4, lift=700.0, arms="hero", at=t)
    e.tween("mo", "lift", 0.0, 0.8, at=t)
    e.sfx("whoosh", at=t)
    e.sfx("thud", at=t + 0.8)
    e.focus(1250, at=t)
    e.wait(1.0)
    e.say("mo", "Stand back, citizen! This slice needs a HERO!")
    e.arms("mo", "swing")
    e.face("kiki", 1)
    e.arms("kiki", "hips")
    e.say("kiki", "Mo. You're an accountant.")
    e.arms("mo", "point")
    e.say("mo", "By day.")
    e.arms("mo", "swing")
    e.place("steve", -300, facing=1, z=2, style="stiff")
    e.walk("steve", 420, style="stiff", speed=160, wait=True)
    e.arms("steve", "wave")
    e.say("steve", "Fellow humans. In space, all food is shared equally.")
    e.arms("steve", "swing")
    e.face("kiki", -1)
    e.say("kiki", "We are not in space, Steve.")
    e.say("steve", "Speak for yourself.")
    e.place("ruby", 2300, facing=-1, z=5, item="mallet", arms="hold")
    e.walk("ruby", 1620, wait=True)
    e.mood("ruby", "happy")
    e.say("ruby", "I fixed the printer this morning. I deserve that pizza.")
    e.place("noor", -250, facing=1, z=1, item="mug", arms="hold")
    e.walk("noor", 230, wait=True)
    e.say("noor", "Guys... it's nine A.M.")

    # the boss
    t = e.cursor
    e.sfx("stab", at=t, gain=0.6)
    e.place("boss", 2400, facing=-1, z=6, mood="angry", at=t)
    e.walk("boss", 1360, speed=420, at=t)
    for n in ("kiki", "mo", "steve", "ruby", "noor"):
        e.emote(n, "!", 1.4, at=t + 1.2)
        e.mood(n, "shock", at=t + 1.2)
    e.wait(2.6)
    e.arms("boss", "hips")
    e.say("boss", "What is going on in here?!")
    e.place("grace", 2300, facing=-1, z=7, item="clipboard", arms="hold")
    e.walk("grace", 1800, wait=True)
    e.say("grace", "This is a clear HR violation. Form twenty-seven B.")
    e.arms("boss", "point")
    e.say("boss", "Fine. Whoever finishes the quarterly report first... gets the last slice.")
    e.arms("boss", "swing")
    t = e.cursor
    e.fx_text("GO GO GO!", 960, 300, dur=1.2, at=t, color="#ffe14d")
    e.sfx("whoosh", at=t)
    for n, d in (("kiki", 0.0), ("mo", 0.1), ("steve", 0.2), ("ruby", 0.25)):
        e.walk(n, -1200, style="run", at=t + d)
    e.wait(1.6)

    # ---------------- OFFICE: the race ---------------------------------------
    e.cut("office", music=(KING, 112.0))
    e.hide(*SQUAD)
    for n, x in (("kiki", 400), ("mo", 980), ("steve", 1560)):
        e.place(n, x, facing=1, z=-1, sit=True, arms="type", mood="angry", item=None, lift=0.0)
    e.place("ruby", 2200, facing=-1, z=2, item="mallet", arms="hold", mood=None)
    for k in range(4):
        e.sfx("typing", at=e.cursor + k * 2.2, gain=0.8)
    e.fx_text("TYPE TYPE TYPE!", 960, 280, dur=1.4)
    e.focus(400)
    e.wait(0.4)
    e.say("kiki", "Fastest fingers in the building! Feel the burn!")
    e.focus(1560)
    e.wait(0.3)
    e.say("steve", "My gloves... keep... hitting... caps lock.")
    e.focus(980)
    e.shake("mo", 3.0, 0.5)
    e.wait(0.4)
    e.say("mo", "Super speed... ACTIVATE!")
    e.wait(0.8)
    t = e.cursor
    e.set("mo", sit=False, z=3, arms="hero", item="report", mood="happy", at=t)
    e.jump("mo", 200, 0.55, at=t)
    e.sfx("fanfare", at=t)
    e.fx_text("DONE!", 960, 300, dur=1.2, at=t, color="#69f0ae", size=180)
    e.wait(0.8)
    e.say("mo", "DONE! The slice is MINE!", gap=0.1)
    e.walk("mo", -1200, style="run")
    e.wait(1.2)

    # ---------------- BREAK ROOM: the real winner ----------------------------
    e.cut("breakroom", music=(FIGARO, 60.0))
    e.hide(*SQUAD)
    e.var("slices", 0)
    e.place("pixel", 1000, facing=1, z=9, lift=290.0, mood="happy", lick=True)
    e.place("mo", -300, facing=1, z=3, arms="swing", item="report", mood="happy", sit=False)
    e.walk("mo", 640, style="run", wait=True)
    e.arms("mo", "hero")
    e.say("mo", "Behold! The report! Now give me my...")
    e.mood("mo", "shock")
    e.arms("mo", "swing")
    t = e.cursor
    e.focus(1000, at=t)
    e.sfx("burp", at=t + 0.3)
    e.fx_text("BURP!", 960, 360, dur=1.2, at=t + 0.3, color="#ffb02e")
    e.wait(1.6)
    e.say("mo", "...slice.", gap=0.4)
    for n, x, d in (("kiki", 300, 0.0), ("steve", 120, 0.3), ("ruby", 1700, 0.1), ("boss", 1450, 0.5)):
        e.place(n, -400 if x < 1000 else 2400, facing=1 if x < 1000 else -1, z=4, sit=False, arms="swing",
                mood="shock", item="mallet" if n == "ruby" else None, at=e.cursor + d)
        e.walk(n, x, style="run", at=e.cursor + d)
    e.wait(1.8)
    e.set("pixel", lick=False)
    e.mood("pixel", None)
    e.arms("boss", "facepalm")
    e.say("boss", "...Meeting adjourned.")
    e.sfx("meow")
    e.fx_text("MEOW.", 960, 360, dur=1.3, color="#ffb02e", size=130)
    e.wait(1.0)
    e.sfx("rimshot")
    e.wait(1.2)
    e.end_card = "Episode 2 coming soon!"
    return e


EPISODES = {1: ep1}
