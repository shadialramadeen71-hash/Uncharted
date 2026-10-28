"""Episode 1 - VOLT: "Power Surge"

Midnight. The villain SHADE has drained the city's power grid into a stolen
Power Core and gloats on a rooftop as the skyline goes dark. A bolt of
lightning splits the sky: VOLT lands. Shade mocks him as "a little spark";
Volt answers with a storm of lightning, knocks the core loose, catches it -
and the city lights flood back on.
"""
TITLE = 'VOLT'
SUBTITLE = 'Episode 1: Power Surge'
DURATION = 18.0
DIALOGUE = [
    (0.6, 'SHADE', "At last... this city's power is mine!"),
    (4.6, 'VOLT', "Lights out? Not on my watch, Shade."),
    (7.3, 'SHADE', "You're just a little spark, hero."),
    (10.45, 'VOLT', "Then watch me shine!"),
    (15.0, 'VOLT', "Power's back on. Good night, city."),
]
SFX = [
    (0.0, 'wind', dict(dur=18.0, gain=0.25)),
    (0.4, 'hum', dict(dur=10.6, gain=0.25)),
    (1.2, 'powerdown', dict(gain=0.6)),
    (3.35, 'thunder', dict(gain=1.0)),
    (3.5, 'impact', dict(gain=0.9)),
    (8.9, 'charge', dict(gain=0.5)),
    (11.45, 'zap', dict(dur=1.6, gain=0.8)),
    (12.0, 'impact', dict(gain=0.6)),
    (13.25, 'catch', dict(gain=0.7)),
    (14.2, 'powerup', dict(gain=0.7)),
]
MUSIC = [(0.0, 3.3, 'tense'), (3.3, 10.8, 'tense_drive'), (10.8, 14.0, 'action'), (14.0, 18.0, 'heroic')]
