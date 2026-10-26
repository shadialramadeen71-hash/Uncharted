"""Fan-made heroes cast in a late-90s dark-deco animated style: Batman, Superman and the Joker."""

BATMAN = dict(
    look=dict(skin="#e9c2a2", hair="#16161d", cowl="#1a1a22", cape="#1a1a22", cape_in="#2c2c38", cape_collar=False,
              top="#7d838e", top2="#6a707a", emblem="bat", belt="#d9b23a", pants="#7d838e", shoe="#1a1a22",
              sole=None, glove="#1a1a22", sleeve="long", hairstyle="none", ears="none", eyes="slits", eye_s=0.8,
              head_s=0.74, jaw=True, sh_f=60, sh_b=-56, body_w=1.28, leg_k=1.24, neck_w=60, stride=1.05, arm_swing=0.8, mouth_dy=18,
              step="leather"),
    voice=dict(voice="en-US-ChristopherNeural", rate="-2%", pitch="-22Hz"),
    color="#3a3f4a", label="BATMAN",
)

SUPERMAN = dict(
    look=dict(skin="#f0c7a5", hair="#14141c", brow="#14141c", forelock=True, top="#2459c7", top2="#1d47a0",
              emblem="S", belt="#f2c12e", pants="#2459c7", shoe="#c8202a", sole=None, cape="#c8202a",
              cape_in="#a3141c", cape_collar=False, sleeve="long", hairstyle="slick", eye_s=0.8, iris="#2a6fd6",
              head_s=0.74, jaw=True, sh_f=60, sh_b=-56, body_w=1.28, leg_k=1.22, neck_w=60, stride=1.05, mouth_dy=12, step="leather"),
    voice=dict(voice="en-US-GuyNeural", rate="+6%", pitch="-6Hz"),
    color="#2459c7", label="SUPERMAN",
)

JOKER = dict(
    look=dict(skin="#f2f0e8", hair="#2f9e44", brow="#2f9e44", top="#6a2c91", top2="#58247a", shirt_v="#e8862b",
              bowtie="#2f9e44", coat=200, pants="#6a2c91", shoe="#2b1a3a", sole=None, glove="#6a2c91",
              sleeve="long", hairstyle="slick", nose="long", nose_k=1.35, eyes="joker", eye_s=0.75, mouth_k=1.6,
              head_s=0.82, sh_f=34, sh_b=-30, body_w=0.82, leg_k=1.24, neck_w=34, stride=1.15, arm_swing=1.4, mouth_dy=10,
              step="heel"),
    voice=dict(voice="en-US-RogerNeural", rate="+16%", pitch="+14Hz"),
    color="#6a2c91", label="JOKER",
)


def add_batman(ep, x, facing=1, z=0):
    return ep.cast("batman", BATMAN["look"], BATMAN["voice"], x, facing, 0.94, z, BATMAN["label"], BATMAN["color"])


def add_superman(ep, x, facing=-1, z=1):
    return ep.cast("superman", SUPERMAN["look"], SUPERMAN["voice"], x, facing, 0.94, z, SUPERMAN["label"], SUPERMAN["color"])


def add_joker(ep, x, facing=-1, z=1):
    return ep.cast("joker", JOKER["look"], JOKER["voice"], x, facing, 0.92, z, JOKER["label"], JOKER["color"])
