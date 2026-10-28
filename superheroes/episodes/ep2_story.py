"""Episode 2 - NOVA: "Falling Star"

Sunset over a half-built skyscraper. Steelworker SAM is checking a beam
forty floors up when the bolts snap. He falls - and a streak of purple light
shoots across the sky. NOVA catches him in mid-air and sets him down safely,
leaving him with one line he'll never forget.
"""
TITLE = 'NOVA'
SUBTITLE = 'Episode 2: Falling Star'
DURATION = 18.0
DIALOGUE = [
    (0.8, 'SAM', "Hmm... this beam doesn't feel right."),
    (3.6, 'SAM', "Whoa! Help! Somebody help me!"),
    (6.4, 'NOVA', "Hold on! I've got you!"),
    (10.0, 'SAM', "You... you can fly?"),
    (12.6, 'NOVA', "Every star falls sometimes. I just catch them."),
]
SFX = [
    (0.0, 'wind', dict(dur=18.0, gain=0.45)),
    (2.4, 'creak', dict(gain=0.8)),
    (3.3, 'snap', dict(gain=0.9)),
    (3.6, 'fallwind', dict(dur=4.4, gain=0.5)),
    (5.6, 'whoosh', dict(gain=0.9)),
    (7.95, 'catch', dict(gain=0.8)),
    (8.4, 'whoosh', dict(gain=0.5)),
    (15.4, 'land', dict(gain=0.6)),
]
MUSIC = [(0.0, 3.3, 'calm'), (3.3, 7.9, 'action'), (7.9, 18.0, 'heroic')]
