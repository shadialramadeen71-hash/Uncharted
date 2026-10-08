# Each segment: (speaker, text, [images shown in order], date tag, highlight keyword)
# speaker: N = narrator (background voice), C = cartoon host "Professor Hoot", CLIP = real archival video
SEGMENTS = [
    ("C", "Hey guys! Professor Hoot here. Today's story is one of the most famous secret missions in history. "
          "And a quick fact check: it was not Delta Force that got bin Laden. But Delta Force does show up in this story. Let's go!",
     ["TITLE"], "", ""),

    ("N", "September eleventh, two thousand one. Nineteen al-Qaeda hijackers turned four passenger planes into weapons.",
     ["wtc"], "SEPT 11, 2001", "9/11"),
    ("N", "Nearly three thousand people were killed. It was the deadliest terrorist attack in history.",
     ["groundzero"], "SEPT 11, 2001", "2,977 KILLED"),
    ("N", "The man behind it was Osama bin Laden, the founder and leader of al-Qaeda.",
     ["binladen"], "", "OSAMA BIN LADEN"),
    ("N", "The United States put a twenty-five million dollar reward on his head. The hunt had begun.",
     ["reward"], "", "$25,000,000"),
    ("N", "In December two thousand one, American forces cornered him in the mountains of Tora Bora, in eastern Afghanistan.",
     ["torabora", "strikes"], "DEC 2001", "TORA BORA"),
    ("N", "And this is where Delta Force comes in. Delta operators, alongside British commandos, pushed into the caves. "
          "But bin Laden slipped away, across the border, into Pakistan.",
     ["deltatora"], "DEC 2001", "DELTA FORCE"),
    ("C", "Ouch! After Tora Bora, the trail went cold. For almost ten years!",
     ["HOOT"], "", ""),

    ("N", "The CIA chased rumor after rumor. Then they found a thread: a trusted courier, known as Abu Ahmed al-Kuwaiti.",
     ["pakmap"], "2002 - 2010", "THE COURIER"),
    ("N", "In two thousand ten, they followed the courier's white car to a quiet city called Abbottabad, in Pakistan.",
     ["abbottabad", "abbview"], "AUG 2010", "ABBOTTABAD"),
    ("N", "It sat less than a mile from Pakistan's top military academy.",
     ["pma"], "", "< 1 MILE"),
    ("N", "There, they found a strange compound. Walls up to eighteen feet high. Barbed wire. No phone line. No internet.",
     ["cia_aerial", "cia_aerial2"], "", "18 FT WALLS"),
    ("N", "The people inside even burned their own trash, instead of putting it out for collection.",
     ["compound1"], "", "NO TRASH"),
    ("N", "And on the top floor lived a tall man who never left. Satellites watched him walk in circles in the garden. "
          "The CIA nicknamed him: the Pacer.",
     ["compound2"], "", "\"THE PACER\""),
    ("C", "So, was it really him? Even the CIA was not sure! Their guesses ranged from forty to ninety-five percent. "
          "The President later said it was close to a coin flip.",
     ["HOOT"], "", ""),

    ("N", "The mission went to the Navy's most elite counter-terrorism unit: SEAL Team Six, also known as DEVGRU.",
     ["seals_cave", "seal_sunset"], "", "SEAL TEAM SIX"),
    ("N", "The SEALs rehearsed the raid again and again, on a full-size replica of the compound.",
     ["breach"], "APRIL 2011", "REHEARSAL"),
    ("N", "On April twenty-ninth, two thousand eleven, President Obama gave the order. The codename: Operation Neptune Spear.",
     ["sitroom2"], "APR 29, 2011", "NEPTUNE SPEAR"),
    ("N", "Late at night on May first, two specially modified stealth Black Hawk helicopters lifted off from Jalalabad, in Afghanistan.",
     ["blackhawk"], "MAY 1, 2011", "STEALTH BLACK HAWKS"),
    ("N", "On board: twenty-three SEALs, an interpreter, and a combat dog named Cairo. "
          "They flew low for about ninety minutes, sneaking under Pakistan's radar.",
     ["fastrope"], "MAY 1, 2011", "23 SEALS + CAIRO"),
    ("N", "Then, right over the compound: disaster. One helicopter lost lift in the hot air between the high walls, "
          "and crashed into the courtyard.",
     ["cia_aerial"], "00:30 LOCAL", "CRASH!"),
    ("C", "Nobody on board was badly hurt. The SEALs just climbed out, and carried on with the mission!",
     ["HOOT"], "", ""),
    ("N", "They blasted through walls and gates, and fought their way up the stairs, floor by floor.",
     ["compound2", "breach"], "00:30 LOCAL", "FLOOR BY FLOOR"),
    ("N", "Back in Washington, the President and his team followed the raid from the White House Situation Room, "
          "in one of the most famous photographs of the century.",
     ["sitroom"], "WASHINGTON", "SITUATION ROOM"),
    ("N", "On the third floor, they found him. Then came the radio call: Geronimo. E. K. I. A. Enemy killed in action.",
     ["compound1"], "MAY 2, 2011", "GERONIMO - EKIA"),
    ("N", "The SEALs blew up the wrecked helicopter to protect its secret technology, and flew out. "
          "The whole raid took about thirty-eight minutes.",
     ["blackhawk"], "MAY 2, 2011", "38 MINUTES"),
    ("N", "Hours later, the President spoke to the nation.",
     ["vid_obama"], "MAY 1, 2011 - 11:35 PM ET", ""),
    ("CLIP", "", ["vid_obama"], "REAL FOOTAGE - WHITE HOUSE", ""),
    ("N", "Crowds poured into the streets, from Times Square to the gates of the White House.",
     ["timessq", "dc"], "MAY 2, 2011", "CELEBRATIONS"),
    ("N", "Bin Laden's body was flown to the aircraft carrier U.S.S. Carl Vinson, and buried at sea within twenty-four hours.",
     ["vid_vinson", "vinson"], "ARABIAN SEA", "BURIED AT SEA"),
    ("N", "Nearly ten years after September eleventh, the hunt for the world's most wanted man was over.",
     ["memorial"], "", "THE END OF THE HUNT"),
    ("C", "So remember: Delta Force almost got him at Tora Bora, but SEAL Team Six finished the job. "
          "If you liked this story, subscribe for more history. See you next time!",
     ["OUTRO"], "", ""),
]
