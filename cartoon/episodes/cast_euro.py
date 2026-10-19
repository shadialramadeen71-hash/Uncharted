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
              shoe="#2a2624", hairstyle="bob", hat="beanie", hat_c="#3f6a89", pompom="#f1e8d6", nose="button",
              eye_s=0.68, freckles=True, head_s=1.22, skirt="#3d6b58", sleeve="long", iris="#2b2118",
              stride=0.95, lift=1.2, step="heel"),
    voice=dict(voice="en-GB-MaisieNeural", rate="+20%", pitch="+0Hz"),
    color="#b5452f", label="MIMI",
)


def add_albert(ep, x, facing=1, z=0):
    return ep.cast("albert", ALBERT["look"], ALBERT["voice"], x, facing, 1.02, z, ALBERT["label"], ALBERT["color"])


def add_mimi(ep, x, facing=-1, z=1):
    return ep.cast("mimi", MIMI["look"], MIMI["voice"], x, facing, 0.74, z, MIMI["label"], MIMI["color"])
