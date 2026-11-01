"""Episode data for "Brick Heroes ABC" - one letter per YouTube Short."""

# (letter, word, emoji)
LETTERS = [
    ("A", "Apple", "🍎"), ("B", "Ball", "⚽"), ("C", "Cat", "🐱"),
    ("D", "Dog", "🐶"), ("E", "Egg", "🥚"), ("F", "Fish", "🐟"),
    ("G", "Grapes", "🍇"), ("H", "Hat", "🎩"), ("I", "Ice cream", "🍦"),
    ("J", "Juice", "🧃"), ("K", "Kite", "🪁"), ("L", "Lion", "🦁"),
    ("M", "Moon", "🌙"), ("N", "Nest", "🪺"), ("O", "Orange", "🍊"),
    ("P", "Pizza", "🍕"), ("Q", "Queen", "👸"), ("R", "Rocket", "🚀"),
    ("S", "Sun", "🌞"), ("T", "Tree", "🌳"), ("U", "Umbrella", "☔"),
    ("V", "Violin", "🎻"), ("W", "Whale", "🐳"), ("X", "X-ray", "🩻"),
    ("Y", "Yo-yo", "🪀"), ("Z", "Zebra", "🦓"),
]

# How the speech engine should say each letter name.
LETTER_SAY = {
    "A": "ay", "B": "bee", "C": "see", "D": "dee", "E": "ee", "F": "eff",
    "G": "jee", "H": "aitch", "I": "eye", "J": "jay", "K": "kay", "L": "ell",
    "M": "em", "N": "en", "O": "oh", "P": "pee", "Q": "cue", "R": "are",
    "S": "ess", "T": "tee", "U": "you", "V": "vee", "W": "double you",
    "X": "ex", "Y": "why", "Z": "zee",
}

# Original brick-built superhero team (not based on any existing franchise).
HEROES = [
    dict(name="Captain Spark", suit=(220, 40, 40), cape=(255, 196, 0),
         mask=(30, 30, 120), legs=(30, 60, 170), hair=None),
    dict(name="Blue Bolt", suit=(25, 110, 230), cape=(200, 205, 215),
         mask=(15, 25, 60), legs=(20, 40, 110), hair=None),
    dict(name="Star Girl", suit=(240, 80, 170), cape=(255, 255, 255),
         mask=(120, 30, 160), legs=(140, 40, 170), hair=(120, 60, 20)),
    dict(name="Green Guardian", suit=(40, 170, 70), cape=(20, 20, 20),
         mask=(10, 70, 30), legs=(25, 100, 45), hair=None),
    dict(name="Turbo Tiger", suit=(255, 140, 20), cape=(40, 40, 40),
         mask=(40, 40, 40), legs=(60, 60, 60), hair=None),
    dict(name="Night Brick", suit=(100, 50, 170), cape=(25, 20, 50),
         mask=(20, 15, 40), legs=(55, 30, 100), hair=(25, 25, 25)),
]

# Public-domain traditional melodies (notes in C major, default 1 beat each).
TUNES = {
    "Twinkle Twinkle / ABC Song":
        "C5 C5 G5 G5 A5 A5 G5:2 F5 F5 E5 E5 D5 D5 C5:2 G5 G5 F5 F5 E5 E5 D5:2 "
        "G5 G5 F5 F5 E5 E5 D5:2",
    "Mary Had a Little Lamb":
        "E5 D5 C5 D5 E5 E5 E5:2 D5 D5 D5:2 E5 G5 G5:2 E5 D5 C5 D5 E5 E5 E5 E5 "
        "D5 D5 E5 D5 C5:4",
    "London Bridge":
        "G5:1.5 A5:0.5 G5 F5 E5 F5 G5:2 D5 E5 F5:2 E5 F5 G5:2 "
        "G5:1.5 A5:0.5 G5 F5 E5 F5 G5:2 D5:2 G5:2 E5 C5:3",
    "Old MacDonald":
        "C5 C5 C5 G4 A4 A4 G4:2 E5 E5 D5 D5 C5:3 G4 "
        "C5 C5 C5 G4 A4 A4 G4:2 E5 E5 D5 D5 C5:4",
    "Frere Jacques":
        "C5 D5 E5 C5 C5 D5 E5 C5 E5 F5 G5:2 E5 F5 G5:2 "
        "G5:0.5 A5:0.5 G5:0.5 F5:0.5 E5 C5 G5:0.5 A5:0.5 G5:0.5 F5:0.5 E5 C5 "
        "C5 G4 C5:2 C5 G4 C5:2",
    "Yankee Doodle":
        "C5 C5 D5 E5 C5 E5 D5 G4 C5 C5 D5 E5 C5:2 B4:2 "
        "C5 C5 D5 E5 F5 E5 D5 C5 B4 G4 A4 B4 C5:2 C5:2",
}
TUNE_ORDER = list(TUNES)


def episode(i):
    letter, word, emoji = LETTERS[i]
    hero = HEROES[i % len(HEROES)]
    tune = TUNE_ORDER[i % len(TUNE_ORDER)]
    nxt = LETTERS[i + 1][0] if i + 1 < len(LETTERS) else None
    say = LETTER_SAY[letter]
    # (start seconds, text) - spoken lines, timed to the 120 BPM beat grid.
    lines = [
        (0.25, "Brick Heroes!"),
        (2.1, f"Letter {say}!"),
        (4.1, f"{say}, {say}, {say}!"),
        (6.1, f"{say} is for {word}!"),
        (8.2, f"{word}! {word}!"),
        (10.1, f"Big {say}, little {say}!"),
        (12.8, f"Next is {LETTER_SAY[nxt]}!" if nxt else "You know A to Z!"),
    ]
    return dict(index=i, letter=letter, word=word, emoji=emoji, hero=hero,
                tune=tune, next=nxt, lines=lines)
