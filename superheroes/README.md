# Superhero Shorts — Blender

Three short animated superhero episodes. Each one is under 20 seconds. Everything is generated with code in **Blender 5.2 (bpy) + Cycles**: the characters, sets, animation, lighting and cameras. The English dialogue is voiced with neural TTS (Piper). The sound effects and music are synthesized.

## The characters

| Character | Look | Voice |
|---|---|---|
| **VOLT** ⚡ | Deep-blue suit, golden gloves, boots and belt, a glowing lightning-bolt emblem, a dark mask, spiky black hair. His eyes glow when he charges up. | Confident American male |
| **NOVA** ★ | Purple suit, silver gloves and boots, a crimson cape that ripples, a golden star emblem, long red hair with a ponytail, green eyes. | American female |
| **SHADE** | Villain. Black hooded cloak, grey face, glowing violet eyes. He floats instead of walking. | Deep British male with reverb |
| **SAM** | Construction worker. Yellow hard hat, orange reflective vest, jeans, work boots. | American male |
| **IRON TITAN** | Five-metre war robot. Gunmetal armour, hazard stripes, a red visor and glowing chest core, three-claw hands. | Pitched-down robotic voice |

Every character has a full body built on a pivot hierarchy you can animate:
- **Hands:** palm, a thumb with 2 joints, and 4 fingers with 3 joints each. They can make a fist, open, spread, or point.
- **Arms:** shoulder (with twist about the arm's own axis), elbow, wrist.
- **Legs:** hip, knee, ankle, and a shaped foot with a sole.
- **Face:** eyes with iris, pupil and highlight (they blink), eyebrows that can look angry or surprised, nose, ears, and a mouth that lip-syncs to the voice audio.

## The episodes

1. **VOLT — Episode 1: Power Surge** (18 s). Shade drains the city's power into a stolen core and the skyline goes dark. Volt lands with a lightning strike, blasts Shade with lightning, catches the core, and the city lights come back on.
2. **NOVA — Episode 2: Falling Star** (18 s). At sunset, a beam snaps 40 floors up. Sam falls, Nova streaks across the sky, catches him in mid-air and sets him down on a rooftop.
3. **VOLT & NOVA — Episode 3: Iron Titan** (19 s). A giant robot stomps down Main Street. Volt short-circuits its core, Nova knocks it down with a flying punch, and they finish with a high five.

The finished videos are in `videos/` (1920×1080, 24 fps, English subtitles burned in).

## How to build

```bash
pip install bpy==5.2.* piper-tts scipy numpy      # plus ffmpeg with libass
# Piper voices: en_US-ryan-high, en_US-amy-medium, en_GB-alan-medium, en_US-joe-medium
export PIPER_VOICES=/path/to/voices
python3 lib/audio.py ep1 ep2 ep3                  # dialogue, lip-sync, SFX, music, subtitles
python3 render.py ep1 --stills 1 100 200          # quick preview frames
./queue.sh ep1 ep2 ep3                            # full render + videos/*.mp4
```

| File | Contents |
|---|---|
| `lib/heroes.py` | Character builder, poses, effects, environments |
| `lib/cast.py` | Character designs |
| `lib/audio.py` | Voices, lip-sync, sound and music |
| `episodes/epN_story.py` | Story, dialogue and timing |
| `episodes/epN_scene.py` | Sets, animation, cameras |
