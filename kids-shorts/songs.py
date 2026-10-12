"""Five original kids' songs (lyrics, melodies, chords and look). Render: python3 songs.py [song-id ...]"""
import os, sys
import engine

C, AM, F, G_, EM, DM = (48, "maj"), (45, "min"), (53, "maj"), (55, "maj"), (52, "min"), (50, "min")

SONGS = [
    dict(id="01_hop_hop_froggy", title="Hop Hop Froggy", animal="frog", scene="pond", hook="hop", sfx="ribbit",
         lead="marimba", bpm=140, key=0, accent=(60, 150, 70),
         rhythm=[1, 1, .5, .5, 1, .5, .5, 1],
         lines=[[67, 64, 72, 72, 72, 69, 69, 67], [69, 65, 74, 74, 74, 71, 71, 69], [67, 64, 72, 72, 72, 69, 69, 67]],
         last_notes=[69, 71, 72, 74, 72], chords=[C, AM, F, G_, C, AM, F, G_],
         verse_titles=["Baby Froggy", "Mommy Froggy", "Daddy Froggy", "Froggy Family"],
         verses=[dict(who="baby", lead=("Baby", "Froggy"), last=["Hop", "into", "the", "pond!"]),
                 dict(who="mommy", lead=("Mommy", "Froggy"), last=["Give", "a", "froggy", "hug!"]),
                 dict(who="daddy", lead=("Daddy", "Froggy"), last=["Biggest", "jump", "of", "all!"]),
                 dict(who="family", lead=("Froggy", "family"), last=["Hop", "hop,", "let's", "all", "dance!"])]),
    dict(id="02_quack_quack_ducky", title="Quack Quack Ducky", animal="duck", scene="farm", hook="quack", sfx="quack",
         lead="clarinet", bpm=140, key=2, accent=(230, 150, 30),
         rhythm=[1, 1, 1, .5, .5, 1, .5, .5],
         lines=[[60, 64, 67, 67, 67, 65, 65, 65], [62, 65, 69, 69, 69, 67, 67, 67], [64, 67, 72, 72, 72, 71, 71, 71]],
         last_notes=[67, 65, 64, 62, 60], chords=[C, F, G_, C, C, F, G_, C],
         verse_titles=["Baby Ducky", "Mommy Ducky", "Daddy Ducky", "Ducky Family"],
         verses=[dict(who="baby", lead=("Baby", "Ducky"), last=["Waddle,", "waddle,", "splash!"]),
                 dict(who="mommy", lead=("Mommy", "Ducky"), last=["Swimming", "in", "the", "pond!"]),
                 dict(who="daddy", lead=("Daddy", "Ducky"), last=["Flap", "your", "wings", "up", "high!"]),
                 dict(who="family", lead=("Ducky", "family"), last=["Quack", "along", "with", "me!"])]),
    dict(id="03_stomp_stomp_dino", title="Stomp Stomp Dino", animal="dino", scene="jungle", hook="stomp", sfx="stomp",
         lead="brass", bpm=140, key=-1, accent=(80, 140, 220), heavy=True,
         rhythm=[.5, .5, 1, 1, 1, 1, .5, .5],
         lines=[[60, 60, 67, 67, 67, 65, 64, 62], [62, 62, 69, 69, 69, 67, 65, 64], [60, 60, 67, 67, 67, 65, 64, 62]],
         last_notes=[64, 65, 67, 69, 67], chords=[C, C, F, G_, C, C, F, G_],
         verse_titles=["Baby Dino", "Mommy Dino", "Daddy Dino", "Dino Family"],
         verses=[dict(who="baby", lead=("Baby", "Dino"), last=["Tiny", "little", "roar!"]),
                 dict(who="mommy", lead=("Mommy", "Dino"), last=["Munching", "yummy", "leaves!"]),
                 dict(who="daddy", lead=("Daddy", "Dino"), last=["Biggest", "stomp", "of", "all!"]),
                 dict(who="family", lead=("Dino", "family"), last=["Stomp", "and", "dance", "all", "day!"])]),
    dict(id="04_toot_toot_ellie", title="Toot Toot Ellie", animal="elephant", scene="savanna", hook="toot", sfx="toot",
         lead="brass", bpm=140, key=0, accent=(150, 100, 200), family_scale=0.82,
         rhythm=[1, 1, .5, .5, .5, .5, 1, 1],
         lines=[[64, 62, 60, 64, 67, 67, 69, 67], [65, 64, 62, 65, 69, 69, 71, 69], [67, 65, 64, 67, 72, 72, 71, 72]],
         last_notes=[69, 67, 65, 64, 60], chords=[C, G_, AM, F, C, G_, F, C],
         verse_titles=["Baby Ellie", "Mommy Ellie", "Daddy Ellie", "Ellie Family"],
         verses=[dict(who="baby", lead=("Baby", "Ellie"), last=["Splashing", "in", "the", "mud!"]),
                 dict(who="mommy", lead=("Mommy", "Ellie"), last=["Flap", "your", "great", "big", "ears!"]),
                 dict(who="daddy", lead=("Daddy", "Ellie"), last=["Trunk", "up", "to", "the", "sky!"]),
                 dict(who="family", lead=("Ellie", "family"), last=["Toot", "toot,", "hip", "hooray!"])]),
    dict(id="05_slide_slide_penguin", title="Slide Slide Penguin", animal="penguin", scene="snow", hook="slide", sfx="slide",
         lead="glock", bpm=140, key=-2, accent=(50, 110, 200),
         rhythm=[1, .5, .5, 1, 1, .5, .5, 1],
         lines=[[72, 71, 69, 67, 67, 64, 64, 67], [74, 72, 71, 69, 69, 65, 65, 69], [72, 71, 69, 67, 67, 64, 64, 67]],
         last_notes=[69, 71, 72, 74, 72], chords=[C, EM, F, G_, C, EM, F, G_],
         verse_titles=["Baby Penguin", "Mommy Penguin", "Daddy Penguin", "Penguin Family"],
         verses=[dict(who="baby", lead=("Baby", "Penguin"), last=["Wiggle,", "wiggle,", "waddle!"]),
                 dict(who="mommy", lead=("Mommy", "Penguin"), last=["Sliding", "on", "the", "ice!"]),
                 dict(who="daddy", lead=("Daddy", "Penguin"), last=["Fishing", "in", "the", "sea!"]),
                 dict(who="family", lead=("Penguin", "family"), last=["Let's", "all", "slide", "together!"])]),
]

if __name__ == "__main__":
    want = sys.argv[1:]
    for cfg in SONGS:
        if want and cfg["id"] not in want and not any(w in cfg["id"] for w in want):
            continue
        prev = os.environ.get("PREVIEW")
        engine.make(cfg, os.path.join(engine.HERE, cfg["id"] + ".mp4"),
                    preview=[float(x) for x in prev.split(",")] if prev else None)
