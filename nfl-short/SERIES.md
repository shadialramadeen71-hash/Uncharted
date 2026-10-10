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
| 3 | **The Gatorade Shower** | Tank and Zippy plan the victory dunk on Coach Pancake. Zippy can't lift the cooler, so Tank lifts it with Zippy still hanging on, and the referee gets soaked instead. "Fifteen yards. For all of you." | ✅ `ep03_gatorade_shower.mp4` |
| 4 | **Salad Season** | The scale says ERROR, so Coach puts Tank on salad. Zippy smuggles in a pizza, hides it on his face ("I am a salad"), and Coach ends up asking for extra cheese. | ✅ `ep04_salad_season.mp4` |
| 5 | **Fantasy Football** | Zippy is worth 2 fantasy points. Training, a dance video and begging take him down to -5, then his hot dog crash from Episode 1 goes viral: 999 points. | ✅ `ep05_fantasy_football.mp4` |
| 6 | **The Halftime Show** | The singer is stuck in traffic. Tank sings opera and pops the stage lights, the crowd is confused, and then Zippy's drum solo gets an ENCORE. | ✅ `ep06_halftime_show.mp4` |
| 7 | **Rivalry Week** | Bus ride to Hot Sauce Stadium ("Are we there yet?"). Mr. Spicy brings Brick, and Tank and Brick have a stare-down. Brick just needed a hug. Group hug. | ✅ `ep07_rivalry_week.mp4` |
| 8 | **The Big Game** (finale) | Snowy championship, 0:03 left, down 20-24. The Flying Play returns, and the referee allows it if Zippy says please. Touchdown in the snow, 26-24 champions, and the trophy gets stuck on Zippy's head. | ✅ `ep08_the_big_game.mp4` |

## Locations and music

| # | Locations | Music (all CC0 / public domain, from OpenGameArt.org) |
|---|---|---|
| 1 | Daytime stadium, hot dog stand | "I Am Not Clumsy" by HydroGene |
| 2 | Daytime stadium, end zone | "I Am Not Clumsy" by HydroGene |
| 3 | Locker room, night game under the lights | "Goofy Attitude" by SkyleTheFrench |
| 4 | Team gym (weigh-in), cafeteria | "The Fridge Is Hungry" by congusbongus |
| 5 | Zippy's apartment, gym, empty night stadium | "Wacky Wobblings" by Fupi |
| 6 | Backstage, concert stage | "Entry of the Gladiators (March of Triumph)" by Eldritch Grim |
| 7 | Desert highway (team bus), Hot Sauce Stadium at sunset | "Spaghetti Western" by Spring Spring |
| 8 | Snowy championship stadium at night | "Victory Victory Victory" by Spring Spring |

## How episodes are made

- `toon.py`: shared engine (characters, stadium, captions, voices, sound effects, music, rendering).
- `sets.py`: locations and props (locker room, gym, cafeteria, apartment, stage, desert road, themed stadiums...).
- `epXX_*.py`: one file per episode with its script (`LINES`), timing (`build_timeline`) and scenes (`render_scene`).
- Render: `python3 ep02_waffle_trouble.py` → 1080×1920, 30 fps MP4.
- Voices: Google Text-to-Speech (`pip install gTTS`) with pitch shifting per character.
- Music: every track is CC0 / public domain from OpenGameArt.org (see the table above). No attribution required.
- All characters and teams are original and fictional. No real NFL teams, logos or players.
