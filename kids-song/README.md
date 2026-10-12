# Hop Hop Froggy — The Froggy Family Song

An original sing-along kids' song in the style of classic family animal songs. The lyrics, melody, arrangement and visuals are all original (not Baby Shark), so you own them and can monetize them on YouTube.

- Video: `hop_hop_froggy.mp4` (1920×1080, 2:25)
- Thumbnail: `thumbnail.png` (1280×720)
- Tempo: 120 BPM, key of C (key changes up on Grandma/Grandpa and the rain/rainbow verses, with a soft lullaby ending)

## Lyrics

Baby Froggy, hop hop hop, hop hop hop!  
Baby Froggy, hop hop hop, hop hop hop!  
Baby Froggy, hop hop hop, hop hop hop!  
Baby Froggy, Splash in the pond!

Mommy Froggy, hop hop hop, hop hop hop!  
Mommy Froggy, hop hop hop, hop hop hop!  
Mommy Froggy, hop hop hop, hop hop hop!  
Mommy Froggy, Give a big hug!

Daddy Froggy, hop hop hop, hop hop hop!  
Daddy Froggy, hop hop hop, hop hop hop!  
Daddy Froggy, hop hop hop, hop hop hop!  
Daddy Froggy, Biggest jump ever!

Grandma Froggy, hop hop hop, hop hop hop!  
Grandma Froggy, hop hop hop, hop hop hop!  
Grandma Froggy, hop hop hop, hop hop hop!  
Grandma Froggy, Slow and steady!

Grandpa Froggy, hop hop hop, hop hop hop!  
Grandpa Froggy, hop hop hop, hop hop hop!  
Grandpa Froggy, hop hop hop, hop hop hop!  
Grandpa Froggy, Ribbit ribbit ribbit!

Raindrops falling, splish splash splish, splish splash splish!  
Raindrops falling, splish splash splish, splish splash splish!  
Raindrops falling, splish splash splish, splish splash splish!  
Raindrops falling, Froggies love the rain!

Rainbow colors, wow wow wow, wow wow wow!  
Rainbow colors, wow wow wow, wow wow wow!  
Rainbow colors, wow wow wow, wow wow wow!  
Rainbow colors, Look up in the sky!

Sleepy Froggies, yawn yawn yawn, yawn yawn yawn!  
Sleepy Froggies, yawn yawn yawn, yawn yawn yawn!  
Sleepy Froggies, yawn yawn yawn, yawn yawn yawn!  
Sleepy Froggies, Goodnight, everyone!

*(Outro)* Yay! Sing again!

## How it's made

- `song.py` writes the melody and backing track (synthesized drums, bass, chords, marimba, music box) and the sung vocals: each word is spoken by Google Text-to-Speech, then pitch-corrected and time-stretched onto its note.
- `video.py` draws the pond, the frog family and the karaoke lyrics, frame by frame.
- Build: `python3 song.py && python3 video.py && python3 thumbnail.py`.
