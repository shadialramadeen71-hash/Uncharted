"""MASK BUDDIES episode scripts.

Poly     - the low-poly black mask. Strict, deadpan, obsessed with rules.
Stitches - the rubber horror mask. Looks terrifying, is actually shy and sweet,
           and physically cannot stop doing the slow horror-movie walk.
"""
import os

from engine import Episode

HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC = os.path.join(HERE, "assets", "music")


def ep1():
    e = Episode(1, "The Slow Walk", "street", os.path.join(MUSIC, "figaro.mp3"), music_start=0.0)
    e.add("stitches", -420, z=1)
    e.add("poly", -150, z=2)
    e.add("pigeon", 1500, z=5, y=-1500)
    e.cam(follow="poly", offset=-160, dur=3.0, at=0)

    e.walk("poly", 760, at=0.0)
    e.walk("stitches", 330, at=0.0)
    e.cam(x=540, dur=1.2, at=3.4)
    e.face("poly", -1, at=3.5)
    e.arms("poly", "hips", at=3.6)
    e.emote("poly", "anger", 1.6, at=3.6)
    e.cursor = 3.8
    e.say("poly", "Stitches. Why do you always walk so slowly behind me?")
    e.cursor = max(e.cursor, 6.4)
    e.say("stitches", "It's my thing. I never run. Ever.")
    e.say("poly", "We are late for coffee. Running is mandatory.")
    e.arms("stitches", "shrug")
    e.say("stitches", "Running is... off-brand.")
    e.arms("stitches", "stiff")

    e.arms("poly", "point")
    e.say("poly", "Fine. New game.")
    e.face("poly", 1)
    e.arms("poly", "swing")
    e.sfx("ding")
    e.say("poly", "Green light!", gap=0.0)
    # Stitches finally hurries... sort of
    e.walk("stitches", 640, style="normal", speed=180)
    e.wait(0.6)
    e.face("poly", -1)
    e.sfx("whoosh")
    e.setstate("stitches", frozen=True, at=e.cursor + 0.35)
    e.say("poly", "Red light!", gap=0.0)
    e.shake("stitches", 0.4, 0.4)
    e.emote("stitches", "sweat", 2.0)
    e.wait(0.6)

    # the pigeon
    t = e.cursor
    e.do("pigeon", "fly", at=t, x=500, y=-760, dur=1.4, then="stitches")
    e.sfx("flap", at=t)
    e.cam(x=600, y=-640, z=1.45, dur=1.0, at=t + 0.4)
    e.wait(1.6)
    e.sfx("coo")
    e.fx_text("COO.", 760, 520, dur=1.2, color="#cfd6ff", size=90)
    e.wait(1.2)
    e.say("stitches", "Can I move now?")
    e.say("poly", "No. Rules are rules.")
    e.cam(x=540, y=-560, z=1.0, dur=0.8)
    e.sfx("pop")
    e.setstate("stitches", hat="nest", hat_t=e.cursor)
    e.sfx("coo", at=e.cursor + 0.3)
    e.fx_text("COO COO!", 540, 520, dur=1.3, color="#cfd6ff", size=90)
    e.wait(1.3)
    e.say("poly", "Congratulations. You are a tree now.")
    e.emote("stitches", "heart", 3.0)
    e.say("stitches", "I've always wanted to be a tree.", gap=0.2)
    e.sfx("rimshot")
    e.wait(1.0)
    e.end_card = "NEXT: THE BOO BREW CAFE"
    return e


def ep2():
    e = Episode(2, "Boo Brew", "cafe", os.path.join(MUSIC, "saltarello.mp3"), music_start=2.0)
    e.add("ghosty", 930, facing=-1, z=-1, lift=260)
    e.add("stitches", -380, z=1, item="spatula")
    e.add("poly", -180, z=2)
    e.sfx("ding", at=0.3, gain=0.8)
    e.walk("poly", 520, at=0.2)
    e.walk("stitches", 230, at=0.2)

    e.cursor = 3.1
    e.say("ghosty", "Welcome to Boo Brew! What can I get you?")
    e.say("poly", "One black coffee. In a square cup. Exactly ninety degrees.")
    e.emote("poly", "!?", 1.5, at=e.cursor + 1.6)
    e.say("ghosty", "Um... all our cups are round, sir.")
    e.arms("poly", "shrug")
    e.say("poly", "Then I will drink it... in a circle.")
    e.arms("poly", "swing")
    e.say("ghosty", "Okay! And for you, sir?")

    # the stare
    t = e.cursor
    e.cam(x=240, y=-600, z=2.5, dur=0.5, at=t)
    e.sfx("stab", at=t + 0.4)
    e.setstate("stitches", eyes_shine=1, at=t + 0.4)
    e.wait(2.0)
    e.setstate("stitches", eyes_shine=0)
    e.cam(x=540, y=-560, z=1.0, dur=0.35)
    e.setstate("ghosty", scared=1)
    e.shake("ghosty", 3.6, 1.0)
    e.wait(0.3)
    t = e.cursor
    e.say("ghosty", "Okay okay! Free coffee! Free muffins! Take the whole cafe!")
    for k, (kind, x) in enumerate((("cup", 760), ("muffin", 880), ("muffin", 1000), ("coins", 820))):
        e.prop(kind, x, -420, at=t + 0.5 + k * 0.6)
        e.sfx("pop", at=t + 0.5 + k * 0.6)
    e.var("price", "$0", at=t + 2.4)
    e.sfx("cash", at=t + 2.4)
    e.setstate("ghosty", scared=0)

    e.face("poly", -1)
    e.say("poly", "How do you do that?")
    e.say("stitches", "I just... look at people.")
    e.face("poly", 1)

    # Poly tries it
    t = e.cursor
    e.cam(x=560, y=-600, z=2.4, dur=0.5, at=t)
    e.setstate("poly", eye_glow=1, at=t + 0.3)
    e.sfx("boing", at=t + 1.1, gain=0.6)
    e.wait(1.6)
    e.setstate("poly", eye_glow=0)
    e.cam(x=540, y=-560, z=1.0, dur=0.35)
    e.wait(0.3)
    e.say("ghosty", "Are you okay? You look like math homework.")
    e.emote("poly", "sweat", 3.0)
    e.var("price", "$9.99")
    e.prop("squarecup", 640, -420)
    e.say("poly", "One coffee. Full price.", gap=0.1)
    e.sfx("sad_trombone")
    e.wait(2.6)
    e.end_card = "NEXT: TRICK OR TREAT"
    return e


def ep3():
    e = Episode(3, "Trick or Treat", "night", os.path.join(MUSIC, "mountain_king.mp3"), music_start=0.0)
    e.add("granny", 800, facing=-1, z=-1, visible=False, item="cane")
    e.add("quackers", 1500, facing=-1, z=3)
    e.add("stitches", -420, z=1)
    e.add("poly", -180, z=2)
    e.walk("poly", 560, at=0.2)
    e.walk("stitches", 330, at=0.2)

    e.cursor = 3.4
    e.arms("poly", "knock")
    e.sfx("knock", at=3.5)
    e.fx_text("KNOCK KNOCK!", 600, 640, dur=1.2, at=3.5)
    e.wait(1.3)
    e.arms("poly", "swing")
    e.var("door", 1.0, dur=0.5)
    e.setstate("granny", visible=True)
    e.sfx("slide_up", gain=0.6)
    e.wait(0.6)
    e.arms("granny", "wave")
    e.say("granny", "Ohh, look at you two! What lovely costumes!")
    e.arms("granny", "swing")
    e.say("poly", "Ma'am, this is my actual face.")
    e.say("stitches", "Mine too.")
    e.say("granny", "And this... is MINE, dearie!", gap=0.0)

    # the scare
    t = e.cursor
    e.setstate("granny", glow=1.0, at=t)
    e.sfx("boom", at=t)
    e.sfx("scream", at=t + 0.15)
    e.fx_text("BOO!", 760, 560, dur=1.3, at=t, color="#ffb02e", size=180)
    for who in ("poly", "stitches"):
        e.jump(who, 190, 0.5, at=t + 0.05)
        e.arms(who, "up", at=t + 0.05)
        e.emote(who, "!", 1.6, at=t + 0.05)
        e.shake(who, 2.4, 1.0, at=t + 0.05)
    e.wait(0.6)
    e.say("stitches", "Aaaaah!", gap=0.4)
    e.setstate("granny", glow=0.0)

    # the law arrives
    e.cam(x=650, dur=1.0)
    e.walk("quackers", 1070, style="run", wait=True)
    e.arms("poly", "swing")
    e.arms("stitches", "cover")
    e.say("quackers", "Quack! What's all the screaming about?")
    e.arms("poly", "point")
    e.say("poly", "Officer! The pumpkin lady scared us!")
    e.arms("poly", "swing")
    e.say("quackers", "Granny Pumpkin? She's the scariest person in Maskville.")
    e.wait(0.3)
    e.say("quackers", "Also, she makes great pie.")
    e.setstate("granny", item="pie")
    e.arms("granny", "hold")
    e.sfx("ding")
    e.say("granny", "Pie for everyone!")
    e.arms("stitches", "stiff")
    e.emote("stitches", "heart", 3.0)
    e.shake("stitches", 2.5, 0.35)
    e.say("stitches", "I'm still shaking. But I'll take two slices.", gap=0.2)
    e.sfx("rimshot")
    e.wait(1.0)
    e.end_card = "SEE YOU NEXT TIME!"
    return e


EPISODES = {1: ep1, 2: ep2, 3: ep3}
