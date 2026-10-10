# Tank & Zippy: Roommates

A cartoon comedy series of vertical shorts (under 60 seconds each). Same two best friends from
*Tank & Zippy*, but no football this time: everyday clothes and everyday life, sharing a tiny apartment.

## Characters

| Character | Who they are |
|---|---|
| **Tank** | Big, calm, bearded, green hoodie. Loves naps, coffee and his couch. The patient one. |
| **Zippy** | Small, spiky orange hair, lightning-bolt tee. Full of energy and terrible ideas. |
| **Mrs. Pickles** | Tiny landlady with a grey bun, round glasses and a cane. Somehow everywhere. Owns the building, an ice cream shop and a goldfish named Sir Bubbles. |
| **Narrator** | Dry and honest. "It was very hard." |

## Season 1

| # | Title | Story | Location | Music (CC0, OpenGameArt) |
|---|---|---|---|---|
| 1 | **Moving Day** | Fourth floor, no elevator. The giant couch won't fit through the door, so it goes through it. "That's coming out of your deposit." | Street, apartment hallway | "Happy Ukulele" by Tarush Singhal |
| 2 | **Breakfast Disaster** | Chef Zippy makes pancakes. Smoke alarm, a pancake stuck to the ceiling, and breakfast lands on Tank's face. | Kitchen | "Happy Awkward Trumpet" by GloriaTheAnimator |
| 3 | **The Goldfish Sitters** | They look after Sir Bubbles: movie night, karaoke, spa day. He comes back wearing sunglasses. | Hallway, living room, bathroom | "8-bit Bossa" by Joth |
| 4 | **The Haircut** | Zippy watched half a video. Tank goes from "the Half Moon" to fully bald, then Zippy sneezes off his own eyebrow. | Bathroom | "Silly Song" by Timopy |
| 5 | **The Camping Trip** | No Wi-Fi, a collapsing tent, a flaming marshmallow, glowing eyes in the bushes... it's Mrs. Pickles with cocoa. | Forest at night | "Miniature Saloon" by Zane Little Music |
| 6 | **The Job Interview** | "Do NOT eat the product." Seven scoops later, Zippy is hired as the official taste tester. | Living room, Pickles' Ice Cream | "Taking You to the Circus" by Pro Sensory |
| 7 | **The Surprise Party** | Mrs. Pickles spoils the surprise, Zippy brings Tank a present on his own birthday, and the cake ends up on Tank's face. | Hallway, party living room | "Rolling Circus" by cinameng |
| 8 | **Moving Out?** (finale) | Boxes everywhere and a phone call make Zippy think Tank is leaving. It's a bigger couch, for both of them. The door does not survive (again). | Living room, rooftop at sunset | "Goofy Attitude" by SkyleTheFrench |

## How it's made

- `life.py`: everyday-clothes characters (`casual`), Mrs. Pickles (`granny`), new locations and props.
  It reuses the animation engine from `../nfl-short/toon.py`.
- `epNN_*.py`: one file per episode. Render with `python3 ep01_moving_day.py` → 1080×1920, 30 fps MP4.
- Voices: Google Text-to-Speech (`pip install gTTS`) with pitch shifting per character.
- All music is CC0 / public domain from OpenGameArt.org. No attribution required.
