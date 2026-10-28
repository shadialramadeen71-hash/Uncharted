"""Episode 3 - VOLT & NOVA: "Iron Titan"

Broad daylight downtown. A five-metre war robot, the IRON TITAN, stomps down
Main Street demanding surrender. Volt and Nova team up for the first time:
Volt overloads its circuits with lightning while Nova flies in with a
knockout punch. The Titan crashes to the asphalt - and the two heroes seal
their new partnership with a high five.
"""
TITLE = 'VOLT & NOVA'
SUBTITLE = 'Episode 3: Iron Titan'
DURATION = 19.0
DIALOGUE = [
    (0.6, 'TITAN', "Surrender, humans. Resistance is futile."),
    (4.75, 'VOLT', "Nova, I'll short-circuit its core!"),
    (7.0, 'NOVA', "And I'll knock it off its feet!"),
    (14.8, 'NOVA', "Not bad, Sparky."),
    (16.45, 'VOLT', "Not bad yourself, Starlight."),
]
SFX = [
    (0.0, 'city', dict(dur=19.0, gain=0.35)),
    (0.2, 'stomp', dict(gain=0.9)), (1.4, 'stomp', dict(gain=0.9)), (2.6, 'stomp', dict(gain=0.9)),
    (3.8, 'stomp', dict(gain=0.9)),
    (9.0, 'charge', dict(gain=0.5)),
    (9.6, 'zap', dict(dur=1.8, gain=0.9)),
    (10.0, 'robotglitch', dict(gain=0.6)),
    (11.1, 'whoosh', dict(gain=0.9)),
    (11.9, 'punch', dict(gain=1.0)),
    (13.2, 'crash', dict(gain=1.0)),
    (18.3, 'clap', dict(gain=0.9)),
]
MUSIC = [(0.0, 4.5, 'tense_drive'), (4.5, 9.0, 'tense_drive'), (9.0, 13.6, 'action'), (13.6, 19.0, 'heroic')]
