# Tank & Zippy

A cartoon comedy series of vertical shorts (under 60 seconds each) about two best friends on a
fictional pro football team, the **Waffles**. One is huge, one is tiny, and both are full of terrible ideas.

## Characters

| Character | Who they are | Running jokes |
|---|---|---|
| **Tank** (#77) | Giant lineman, deep voice, calm and kind | The voice of reason who still goes along with every bad plan |
| **Zippy** (#1) | Tiny, hyper wide receiver, squeaky voice | Always ends up flying, stuck, or covered in food. "Totally worth it." |
| **Coach Pancake** | Short, round head coach with a giant mustache and a clipboard | Facepalms. Makes up rules on the spot. |
| **Mr. Spicy** | Mascot of the rival team, the Hot Sauce: a giant, boastful hot-sauce bottle | Always gets knocked over by accident |
| **Brick** (#99) | The Hot Sauce's grumpy lineman | Just stares |
| **Narrator** | Dry, British-sounding announcer | Delivers the punchline penalties |

## Season 1

| # | Title | Story | Status |
|---|---|---|---|
| 1 | **The Flying Play** | Zippy's trick play: Tank throws *him* instead of the ball. Zippy flies past a "No Flying Zone" sign and lands in a hot dog stand. Penalty: unnecessary flying. | ✅ `tank_and_zippy_nfl_short.mp4` |
| 2 | **Waffle Trouble** | The mascot is sick, so Zippy has to wear a giant waffle costume. A dance battle with Mr. Spicy goes wrong. Zippy tumbles across the field, knocks Spicy down, the ball sticks to the syrup, and he rolls into the end zone. Can a waffle score? No. | ✅ `ep02_waffle_trouble.mp4` |
| 3 | **The Gatorade Shower** | Tank and Zippy try the classic victory dunk on Coach Pancake. Zippy can't lift the cooler, Tank lifts it with Zippy still holding on, and the referee gets soaked instead. | Next |
| 4 | **Salad Season** | Coach puts Tank on a strict salad diet. Zippy runs a ridiculous pizza-smuggling operation inside his helmet. | Planned |
| 5 | **Fantasy Football** | Zippy finds out fans gave him 2 fantasy points. He tries to become everyone's #1 pick and only gets worse. | Planned |
| 6 | **Halftime Show** | The halftime singer is stuck in traffic. Tank sings opera, and Zippy plays the drums on Brick's helmet. | Planned |
| 7 | **Rivalry Week** | The Waffles vs. the Hot Sauce. Spicy wants revenge for Episode 2 and Brick wants Zippy. Tank has to protect his buddy. | Planned |
| 8 | **The Big Game** (finale) | Championship game, last play. Zippy says "I have an idea" and everyone screams "NO!" The Flying Play returns, and this time it's legal. | Planned |

## How episodes are made

- `toon.py`: shared engine (characters, stadium, captions, voices, sound effects, music, rendering).
- `epXX_*.py`: one file per episode with its script (`LINES`), timing (`build_timeline`) and scenes (`render_scene`).
- Render: `python3 ep02_waffle_trouble.py` → 1080×1920, 30 fps MP4.
- Voices: Google Text-to-Speech (`pip install gTTS`) with pitch shifting per character.
- Music: **"I Am Not Clumsy" by HydroGene**, CC0 / public domain (OpenGameArt.org). No attribution required.
- All characters and teams are original and fictional. No real NFL teams, logos or players.
