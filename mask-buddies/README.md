# MASK BUDDIES — cartoon comedy shorts

Vertical 1080x1920 shorts (30 fps, ~40 s each) starring two masks:

- **Poly** — the black low-poly mask. Deadpan, strict, obsessed with rules.
- **Stitches** — the rubber mask with messy hair and a stitched scar. Looks terrifying,
  is actually shy and sweet, and can't stop doing the slow horror-movie walk.

Supporting cast in Maskville: **Ghosty** (bedsheet-ghost barista), **Granny Pumpkin**,
**Officer Quackers**, and one very committed pigeon.

| Ep | Title | Setting |
|----|-------|---------|
| 1 | The Slow Walk | Maskville street (day) |
| 2 | Boo Brew | Ghosty's café |
| 3 | Trick or Treat | Halloween night |

## Render

    pip install pycairo edge-tts numpy
    python3 render.py          # all episodes -> output/
    python3 render.py 2        # one episode
    python3 render.py 1 --preview 300 600   # PNG stills

Episode scripts live in `episodes.py`: a small timeline language (`walk`, `say`, `jump`,
`emote`, `cam`, `sfx` ...). Voice lines are generated with edge-tts and cached in `build/`.

## Credits / licences

- Music: Musopen Kickstarter recordings (CC0 / public domain), via archive.org:
  Mozart *Marriage of Figaro* overture, Mendelssohn *Italian Symphony IV (Saltarello)*,
  Grieg *In the Hall of the Mountain King*.
- Fonts: Luckiest Guy (Apache 2.0), Fredoka (OFL), from Google Fonts.
- Sound effects: synthesized in `audio.py` (no samples).
- Voices: Microsoft Edge neural TTS via edge-tts.
