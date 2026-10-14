# THE WOBBLES — a family sitcom cartoon, made entirely in code

16:9 1920x1080 episodes. An original family in the town of Pickleton:

- **Gary** — dad, pickle-factory worker, "grill master". Catchphrase: *"Oh, pickles."*
- **Linda** — mom, the only sane one.
- **Max** (10) — inventor who has never read a safety label.
- **Pip** (7) — sings everything, loudly.
- **Biscuit** — a very round beagle.
- **Mr. Fussbucket** — next door; loves his lawn more than people.

| Ep | Title | Story |
|----|-------|-------|
| 1 | The Great Barbecue Disaster | flying couch, turbo grill, burger rain, self-destruct |
| 2 | The Talent Show | Pip and a howling Biscuit; Mr. Fussbucket judges |
| 3 | Robo-Biscuit | Max's robot dog fetches everything — including the fence |

Add `--vertical` to render 1080x1920 shorts with a speaker-following camera:

    python3 render.py --vertical      # -> output/the_wobbles_epN_short.mp4

## Render

    pip install pycairo edge-tts numpy
    python3 render.py                 # -> output/the_wobbles_ep1.mp4
    python3 render.py 1 --preview 300 # PNG still of frame 300

Files: `wob_chars.py` (characters, faces, blinking, talking mouths, sitting),
`wob_world.py` (intro, living room, kitchen, backyard, sky), `wob_engine.py`
(multi-scene timeline, camera, tweens, voices, SFX, music per scene),
`wob_episodes.py` (scripts). Reuses the voice/SFX pipeline from `../mask-buddies`.

Music: CC0 Musopen recordings (see ../mask-buddies/README.md). SFX synthesized in code.
