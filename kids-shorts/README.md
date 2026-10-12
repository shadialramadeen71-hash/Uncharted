# Kids' Sing-Along Shorts

Five original sing-along songs for kids, in the style of classic animal-family songs like *Baby Shark*.
All lyrics, melodies, arrangements and characters are original, so they are safe to upload and monetize.

- Format: vertical YouTube Shorts, 1080×1920, 30 fps, each under 60 seconds
- The music starts in the first second, the lyrics light up word by word (karaoke style), and they sit above the Shorts buttons
- Vocals: Google Text-to-Speech words pitch-corrected onto the melody with TD-PSOLA (`autotune.py`): 94% of notes land within half a semitone

## Hop Hop Froggy  (`01_hop_hop_froggy.mp4`)

Baby Froggy, hop hop hop, hop hop hop!  
Baby Froggy, hop hop hop, hop hop hop!  
Baby Froggy, hop hop hop, hop hop hop!  
Baby Froggy, Hop into the pond!

Mommy Froggy, hop hop hop, hop hop hop!  
Mommy Froggy, hop hop hop, hop hop hop!  
Mommy Froggy, hop hop hop, hop hop hop!  
Mommy Froggy, Give a froggy hug!

Daddy Froggy, hop hop hop, hop hop hop!  
Daddy Froggy, hop hop hop, hop hop hop!  
Daddy Froggy, hop hop hop, hop hop hop!  
Daddy Froggy, Biggest jump of all!

Froggy family, hop hop hop, hop hop hop!  
Froggy family, hop hop hop, hop hop hop!  
Froggy family, hop hop hop, hop hop hop!  
Froggy family, Hop hop, let's all dance!

*Yay! Sing it again!*

## Quack Quack Ducky  (`02_quack_quack_ducky.mp4`)

Baby Ducky, quack quack quack, quack quack quack!  
Baby Ducky, quack quack quack, quack quack quack!  
Baby Ducky, quack quack quack, quack quack quack!  
Baby Ducky, Waddle, waddle, splash!

Mommy Ducky, quack quack quack, quack quack quack!  
Mommy Ducky, quack quack quack, quack quack quack!  
Mommy Ducky, quack quack quack, quack quack quack!  
Mommy Ducky, Swimming in the pond!

Daddy Ducky, quack quack quack, quack quack quack!  
Daddy Ducky, quack quack quack, quack quack quack!  
Daddy Ducky, quack quack quack, quack quack quack!  
Daddy Ducky, Flap your wings up high!

Ducky family, quack quack quack, quack quack quack!  
Ducky family, quack quack quack, quack quack quack!  
Ducky family, quack quack quack, quack quack quack!  
Ducky family, Quack along with me!

*Yay! Sing it again!*

## Stomp Stomp Dino  (`03_stomp_stomp_dino.mp4`)

Baby Dino, stomp stomp stomp, stomp stomp stomp!  
Baby Dino, stomp stomp stomp, stomp stomp stomp!  
Baby Dino, stomp stomp stomp, stomp stomp stomp!  
Baby Dino, Tiny little roar!

Mommy Dino, stomp stomp stomp, stomp stomp stomp!  
Mommy Dino, stomp stomp stomp, stomp stomp stomp!  
Mommy Dino, stomp stomp stomp, stomp stomp stomp!  
Mommy Dino, Munching yummy leaves!

Daddy Dino, stomp stomp stomp, stomp stomp stomp!  
Daddy Dino, stomp stomp stomp, stomp stomp stomp!  
Daddy Dino, stomp stomp stomp, stomp stomp stomp!  
Daddy Dino, Biggest stomp of all!

Dino family, stomp stomp stomp, stomp stomp stomp!  
Dino family, stomp stomp stomp, stomp stomp stomp!  
Dino family, stomp stomp stomp, stomp stomp stomp!  
Dino family, Stomp and dance all day!

*Yay! Sing it again!*

## Toot Toot Ellie  (`04_toot_toot_ellie.mp4`)

Baby Ellie, toot toot toot, toot toot toot!  
Baby Ellie, toot toot toot, toot toot toot!  
Baby Ellie, toot toot toot, toot toot toot!  
Baby Ellie, Splashing in the mud!

Mommy Ellie, toot toot toot, toot toot toot!  
Mommy Ellie, toot toot toot, toot toot toot!  
Mommy Ellie, toot toot toot, toot toot toot!  
Mommy Ellie, Flap your great big ears!

Daddy Ellie, toot toot toot, toot toot toot!  
Daddy Ellie, toot toot toot, toot toot toot!  
Daddy Ellie, toot toot toot, toot toot toot!  
Daddy Ellie, Trunk up to the sky!

Ellie family, toot toot toot, toot toot toot!  
Ellie family, toot toot toot, toot toot toot!  
Ellie family, toot toot toot, toot toot toot!  
Ellie family, Toot toot, hip hooray!

*Yay! Sing it again!*

## Slide Slide Penguin  (`05_slide_slide_penguin.mp4`)

Baby Penguin, slide slide slide, slide slide slide!  
Baby Penguin, slide slide slide, slide slide slide!  
Baby Penguin, slide slide slide, slide slide slide!  
Baby Penguin, Wiggle, wiggle, waddle!

Mommy Penguin, slide slide slide, slide slide slide!  
Mommy Penguin, slide slide slide, slide slide slide!  
Mommy Penguin, slide slide slide, slide slide slide!  
Mommy Penguin, Sliding on the ice!

Daddy Penguin, slide slide slide, slide slide slide!  
Daddy Penguin, slide slide slide, slide slide slide!  
Daddy Penguin, slide slide slide, slide slide slide!  
Daddy Penguin, Fishing in the sea!

Penguin family, slide slide slide, slide slide slide!  
Penguin family, slide slide slide, slide slide slide!  
Penguin family, slide slide slide, slide slide slide!  
Penguin family, Let's all slide together!

*Yay! Sing it again!*

## Uploading to YouTube (kids' content)

1. Under **Audience**, choose **Yes, it's made for kids**. This is required by YouTube/COPPA for children's content.
2. Title example: `Hop Hop Froggy 🐸 | Froggy Family Song | Kids Songs & Nursery Rhymes #shorts`
3. Description: put the lyrics, plus a line like `Original song. Sing along with the Froggy Family!`
4. Tags: kids songs, nursery rhymes, sing along, animal songs, toddler songs, family song, the animal's name
5. Keep it kid-safe: no links to external sites in the description, and no requests to 'like' or 'comment' (comments are disabled on made-for-kids videos anyway).
6. Upload one Short a day to build up the channel.

## Rebuild

`python3 songs.py` renders all five (or `python3 songs.py dino` for one).
