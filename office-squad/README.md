# OFFICE SQUAD — vertical comedy shorts, made entirely in code

Flat, bold-outline cartoon style with proper anatomy: tapered arms and legs with
elbows and knees, hands with a palm, thumb and four fingers (relaxed / open / fist /
point), and real shoes (sneakers, boots, heels).

| Character | |
|---|---|
| **Mighty Mo** | accountant by day, superhero... also by day |
| **Mr. Baldwin** | the boss |
| **Noor** | the only one who reads the emails |
| **Ruby** | handywoman; every problem is a hammer problem |
| **Grace** | HR; has a form for everything |
| **Kiki** | the intern; turns every task into cardio |
| **Space Steve** | IT; hasn't taken the suit off since 2019 |
| **Pixel** | the office cat, the real boss |

Episode 1: *The Last Slice* (1:32, 1080x1920).

    pip install pycairo edge-tts numpy
    python3 render.py            # -> output/office_squad_ep1_short.mp4

Built on the engine in `../wobbles` (camera, timeline, voices) and `../mask-buddies`
(voice/SFX pipeline). Music: CC0 Musopen recordings; SFX synthesized in code.
