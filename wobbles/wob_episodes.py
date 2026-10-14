"""THE WOBBLES - episode scripts.

Gary   - dad, pickle-factory worker, self-declared grill master. Catchphrase: "Oh, pickles."
Linda  - mom, the only sane one.
Max    - 10, inventor, has never read a safety label.
Pip    - 7, sings everything, loudly.
Biscuit- the round beagle.
Mr. Fussbucket - next door, loves his lawn more than people.
"""
import os

from wob_engine import Episode

HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC = os.path.join(HERE, "..", "mask-buddies", "assets", "music")
FIGARO = os.path.join(MUSIC, "figaro.mp3")
SALT = os.path.join(MUSIC, "saltarello.mp3")
KING = os.path.join(MUSIC, "mountain_king.mp3")


def ep1():
    e = Episode(1, "The Great Barbecue Disaster")
    for n in ("gary", "linda", "max", "pip", "biscuit", "fuss"):
        e.add(n, z={"fuss": -1, "biscuit": 5}.get(n, 1 + len(e.order)))

    # ---------------- INTRO -------------------------------------------------
    e.cut("intro", music=(FIGARO, 0.0))
    e.sfx("whoosh", at=0.3)
    e.sfx("fanfare", at=1.25)
    e.wait(5.2)

    # ---------------- COUCH GAG ---------------------------------------------
    e.cut("living")
    for n, x0, x1 in (("gary", -300, 640), ("linda", -520, 880), ("max", -720, 1110),
                      ("pip", -880, 1300), ("biscuit", -1100, 1640)):
        e.place(n, x0, facing=1)
        e.walk(n, x1, style="run")
    e.set("max", item="remote")
    e.set("pip", item="mic")
    e.wait(3.5)
    for n in ("gary", "linda", "max", "pip"):
        e.set(n, sit=True)
        e.sfx("thud", gain=0.5)
    e.face("biscuit", -1)
    e.wait(0.4)
    e.arms("max", "point")
    e.say("max", "Wanna see my new couch upgrade?")
    e.mood("gary", "shock")
    e.say("gary", "Max, no!", gap=0.0)
    t = e.cursor
    e.sfx("rocket", at=t)
    e.var("couch_lift", 1500.0, at=t + 0.2, dur=1.6)
    for n in ("gary", "linda", "max", "pip"):
        e.tween(n, "lift", 1500.0, 1.6, at=t + 0.2)
        e.arms(n, "up", at=t + 0.2)
    e.fx_text("WHOOOSH!", 960, 300, dur=1.6, at=t + 0.3)
    e.sfx("bark", at=t + 0.6)
    e.jump("biscuit", 120, 0.4, at=t + 0.6)
    e.wait(2.4)
    # ...and they land
    t = e.cursor
    e.var("couch_lift", 0.0, at=t, dur=0.5)
    for n in ("gary", "linda", "max", "pip"):
        e.tween(n, "lift", 0.0, 0.5, at=t)
        e.arms(n, "swing", at=t + 0.5)
        e.set(n, hat="soot", at=t + 0.5)
    e.sfx("boom", at=t + 0.5, gain=0.8)
    e.var("quake", 1.0, at=t + 0.5)
    e.var("quake", 0.0, at=t + 0.9)
    e.wait(1.2)
    e.mood("gary", "sad")
    e.say("gary", "Oh, pickles.")
    e.say("pip", "Again! Again! Again!")
    e.wait(0.3)

    # ---------------- KITCHEN -----------------------------------------------
    e.hide("biscuit")
    e.cut("kitchen", cam={"x": 1050})
    e.place("linda", 600, facing=1, sit=False, hat=None, mood=None)
    e.place("gary", 980, facing=-1, sit=False, hat=None, mood=None, item="spatula")
    e.place("max", 1450, facing=-1, sit=False, hat=None, item=None)
    e.place("pip", 300, facing=1, sit=False, hat=None)
    e.wait(0.4)
    e.arms("linda", "hips")
    e.say("linda", "Gary, the neighbors are coming to the barbecue at noon. Please, don't embarrass us.")
    e.arms("linda", "swing")
    e.arms("gary", "point")
    e.say("gary", "Relax, Linda. I am a grill master. I have a hat that says so.")
    e.arms("gary", "swing")
    e.face("gary", 1)
    e.say("max", "Dad, I upgraded the grill. It's now four hundred percent more powerful.")
    e.mood("gary", "happy")
    e.say("gary", "Did you add a turbo button?")
    e.arms("max", "shrug")
    e.say("max", "Obviously. Just never push the red one.")
    e.arms("max", "swing")
    e.arms("pip", "up")
    e.emote("pip", "music", 3.5)
    e.say("pip", "Never push the red one! Never push the red one! La la laaa!")
    e.arms("pip", "swing")
    e.face("gary", -1)
    e.say("gary", "Thank you, sweetie. We heard you.", gap=0.5)

    # ---------------- BACKYARD ----------------------------------------------
    e.cut("backyard", cam={"x": 1050}, music=(SALT, 4.0))
    e.place("gary", 760, facing=1, item="spatula", mood=None)
    e.place("linda", -200, facing=1, item="plate")
    e.place("max", 300, facing=1)
    e.place("pip", 140, facing=1)
    e.place("biscuit", 1300, facing=-1)
    e.place("fuss", 1530, facing=-1, lift=-420.0)
    e.var("flame", 1.0)
    e.var("smoke", 1.0)
    e.sfx("sizzle")
    e.wait(1.0)
    e.tween("fuss", "lift", 0.0, 0.5)
    e.sfx("slide_up", gain=0.6)
    e.wait(0.6)
    e.emote("fuss", "anger", 2.0)
    e.say("fuss", "Wobble! Your smoke is touching my lawn!")
    e.face("gary", 1)
    e.arms("gary", "shrug")
    e.say("gary", "It's a barbecue, Mister Fussbucket. Smoke is part of the flavor.")
    e.arms("gary", "swing")
    e.arms("fuss", "up")
    e.say("fuss", "My lawn does not want flavor! My lawn wants peace!")
    e.arms("fuss", "swing")
    e.walk("linda", 420)
    e.wait(0.9)
    e.say("linda", "Gary, honey, the burgers are taking forever.")
    e.face("gary", -1)
    e.say("gary", "Fine. Time for a little... turbo.")
    e.face("gary", 1)
    e.arms("gary", "point")
    e.sfx("pop")
    e.wait(0.3)
    e.emote("max", "!", 1.5)
    e.mood("max", "shock")
    e.say("max", "Dad! That's the RED one!", gap=0.0)

    # KA-BLAMMO
    t = e.cursor
    e.focus(1250, at=t)
    e.sfx("boom", at=t)
    e.sfx("rocket", at=t, gain=0.5)
    e.var("flash", 1.0, at=t)
    e.var("flash", 0.0, at=t, dur=0.4)
    e.var("quake", 1.0, at=t)
    e.var("quake", 0.0, at=t + 0.8)
    e.var("burgers_t0", t, at=t)
    e.var("flame", 3.0, at=t)
    e.fx_text("KA-BLAMMO!", 960, 260, dur=1.4, at=t + 0.1, color="#ff7043", size=180)
    for n in ("gary", "linda", "max", "pip", "fuss"):
        e.jump(n, 170, 0.55, at=t + 0.05)
        e.mood(n, "shock", at=t + 0.05)
        e.arms(n, "up", at=t + 0.05)
    e.set("fuss", hat="burger", at=t + 1.45)
    e.sfx("thud", at=t + 1.45)
    # Biscuit has the best day of his life
    e.walk("biscuit", 1900, style="run", at=t + 0.6)
    e.walk("biscuit", 200, style="run", at=t + 1.6)
    for k in range(3):
        e.sfx("bark", at=t + 1.0 + k * 0.7)
    e.emote("biscuit", "heart", 3.0, at=t + 1.2)
    e.wait(2.6)
    e.var("flame", 1.0)
    for n in ("gary", "linda", "max", "pip"):
        e.arms(n, "swing")
    e.mood("fuss", "sad")
    e.arms("fuss", "swing")
    e.say("fuss", "My lawn! My beautiful, beautiful...")
    e.wait(0.4)
    e.mood("fuss", "happy")
    e.say("fuss", "...wait. This is actually delicious.")
    e.mood("gary", "happy")
    e.arms("gary", "hips")
    e.say("gary", "I meant to do that.")
    e.arms("gary", "swing")

    # the beeping
    e.var("beep", 1)
    for k in range(4):
        e.sfx("beep", at=e.cursor + k * 0.45)
    e.wait(0.4)
    e.mood("linda", "shock")
    e.say("linda", "Gary... why is the grill beeping?")
    e.arms("max", "shrug")
    e.mood("max", None)
    e.say("max", "Oh. That's the self-destruct. We have about five seconds.")
    for k in range(4):
        e.sfx("beep", at=e.cursor + k * 0.3)
    t = e.cursor
    for n in ("gary", "linda", "max", "pip"):
        e.emote(n, "!", 1.2, at=t)
        e.mood(n, "shock", at=t)
        e.walk(n, -900, style="run", at=t + 0.3)
    e.tween("fuss", "lift", -420.0, 0.4, at=t + 0.3)
    e.fx_text("RUN!", 960, 260, dur=1.0, at=t + 0.2, color="#ff5252")
    e.focus(1000, at=t + 0.8)
    e.wait(1.6)
    e.sfx("rocket")
    e.var("grill_y", 1600.0, dur=1.6)
    e.wait(1.8)

    # ---------------- THE GRILL'S LAST FLIGHT --------------------------------
    e.cut("sky", music=(KING, 128.0))
    e.hide("gary", "linda", "max", "pip", "biscuit", "fuss")
    e.sfx("rocket", gain=0.6)
    e.wait(2.4)
    t = e.cursor
    e.var("flash", 1.0, at=t)
    e.var("flash", 0.0, at=t + 0.1, dur=0.8)
    e.sfx("boom", at=t)
    e.fx_text("KABOOM!", 960, 540, dur=1.4, at=t, color="#ffb02e", size=260)
    e.wait(1.6)

    # ---------------- BACKYARD, AFTER ---------------------------------------
    e.cut("backyard", cam={"x": 1050})
    e.var("burgers_t0", 0)
    e.var("grill_y", 0.0)
    e.var("beep", 0)
    e.var("flame", 0.0)
    e.var("smoke", 0.0)
    e.var("burgers_on", 0)
    e.var("grill_gone", 1)
    e.place("gary", -300, facing=1, mood="sad", item="spatula")
    e.place("fuss", 1530, facing=-1, lift=0.0, mood="happy")
    e.focus(1075)
    e.walk("gary", 620, style="sneak", wait=True)
    e.wait(0.3)
    e.say("fuss", "Same time next week, Wobble?")
    e.mood("gary", "happy")
    e.face("gary", 1)
    e.say("gary", "Oh... pickles. Yes!", gap=0.2)
    e.sfx("rimshot")
    e.wait(1.2)
    e.end_card = "Episode 2 coming soon!"
    return e


EPISODES = {1: ep1}
