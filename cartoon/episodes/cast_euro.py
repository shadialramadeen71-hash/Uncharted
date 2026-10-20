"""'Paris winter' cast, drawn in a European hand-drawn caricature style.

Albert: grumpy grandpa, trusts every old wives' remedy.  Mimi: his clever granddaughter.
Plus Minou, the black cat who judges everyone (drawn as a prop, see scene.cat)."""

ALBERT = dict(
    look=dict(skin="#efc3a4", hair="#ece8e0", brow="#d8d2c8", brow_w=13, top="#2f4f78", top2="#27416a",
              pants="#5b4b40", shoe="#2b2320", hairstyle="old", nose="big", eye_s=0.55, eye_gap=0.9, lid0=0.36,
              bags=True, jowls=True, body_w=1.18, belly=40, head_s=1.04, neck_w=52, stoop=4, stride=0.86, lift=0.8,
              arm_swing=0.7, coat=165, scarf="#9b3a2e", mouth_dy=16, sleeve="long", iris="#2b2118", step="leather"),
    voice=dict(voice="en-GB-RyanNeural", rate="+16%", pitch="-6Hz"),
    color="#2f4f78", label="ALBERT",
)

MIMI = dict(
    look=dict(skin="#f4d3b9", hair="#8b3f22", top="#d6a23c", top2="#b98a2c", pants="#8a3030", leg_w=32,
              shoe="#2a2624", hairstyle="bob", hat="beanie", hat_s=0.88, hat_c="#3f6a89", pompom="#f1e8d6", nose="button",
              eye_s=0.68, freckles=True, head_s=1.22, skirt="#3d6b58", sleeve="long", iris="#2b2118",
              stride=0.95, lift=1.2, step="heel"),
    voice=dict(voice="en-GB-MaisieNeural", rate="+20%", pitch="+0Hz"),
    color="#b5452f", label="MIMI",
)


def add_albert(ep, x, facing=1, z=0):
    return ep.cast("albert", ALBERT["look"], ALBERT["voice"], x, facing, 1.02, z, ALBERT["label"], ALBERT["color"])


def add_mimi(ep, x, facing=-1, z=1):
    return ep.cast("mimi", MIMI["look"], MIMI["voice"], x, facing, 0.74, z, MIMI["label"], MIMI["color"])

COLETTE = dict(  # the neighbourhood baker: round, warm, flour on her apron
    look=dict(skin="#ecb994", hair="#9a8f86", top="#8c3a49", top2="#74303c", pants="#5a4a44", shoe="#3a2a24",
              hairstyle="bun", nose="button", eye_s=0.62, lid0=0.18, glasses=True, body_w=1.36, belly=46,
              head_s=1.02, neck_w=48, coat=190, apron="#efe7d6", apron_len=150, sleeve="long", stride=0.82,
              lift=0.85, arm_swing=0.8, iris="#3a2a1a", mouth_dy=4, step="heel"),
    voice=dict(voice="en-GB-SoniaNeural", rate="+12%", pitch="-4Hz"),
    color="#8c3a49", label="COLETTE",
)

GASTON = dict(  # tall, thin, very proud cafe waiter
    look=dict(skin="#f0c9a8", hair="#1e1a1c", mustache_c=(0.12, 0.1, 0.11), top="#22262c", top2="#1a1d22",
              shirt_v="#f3efe6", bowtie="#7a1f24", pants="#22262c", shoe="#141416", hairstyle="slick", nose="long",
              mustache=True, eye_s=0.6, lid0=0.42, body_w=0.84, head_s=0.96, neck_w=34, apron="#f4f1ea", apron_waist=True,
              apron_len=200, sleeve="long", stride=1.08, arm_swing=0.5, iris="#2a2018", mouth_dy=22, step="heel"),
    voice=dict(voice="en-GB-ThomasNeural", rate="+12%", pitch="-2Hz"),
    color="#3a4a5c", label="GASTON",
)


def add_colette(ep, x, facing=-1, z=1):
    return ep.cast("colette", COLETTE["look"], COLETTE["voice"], x, facing, 0.94, z, COLETTE["label"], COLETTE["color"])


def add_gaston(ep, x, facing=-1, z=1):
    return ep.cast("gaston", GASTON["look"], GASTON["voice"], x, facing, 1.12, z, GASTON["label"], GASTON["color"])
