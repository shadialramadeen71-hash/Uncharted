"""'The Count & Pip' cast: a tall, green-faced 1888 villain who keeps failing at fairy-tale schemes,
and Pip, his small imp butler who is far too honest."""

COUNT = dict(
    look=dict(skin="#9cc58a", hair="#1c1a20", brow="#1c1a20", brow_w=11, mustache=True, mustache_c=(0.11, 0.1, 0.12),
              top="#2b2633", top2="#221e29", shirt_v="#f3efe6", pants="#3a3346", shoe="#151418", sole=None,
              hairstyle="slick", hat="tophat", nose="long", nose_k=1.6, eye_s=0.66, lid0=0.3, monocle=True, glove="#f2efe6",
              cape="#4b2a5c", cape_in="#a3243b", coat=230, leg_k=1.26, neck_len=16, body_w=0.86, head_s=0.95,
              stride=1.1, arm_swing=0.7, sleeve="long", iris="#5a1a1a", mouth_dy=22, step="heel"),
    voice=dict(voice="en-GB-RyanNeural", rate="+10%", pitch="-12Hz"),
    color="#4b2a5c", label="THE COUNT",
)

PIP = dict(
    look=dict(skin="#d64933", hair="#d64933", top="#24202b", top2="#1c1922", shirt_v="#f3efe6", bowtie="#c9a227",
              pants="#24202b", shoe="#151418", hairstyle="none", horns=True, horn_c="#f1e3c6", ears="pointy",
              tail=True, fangs=True, nose="button", eye_s=0.95, iris="#e0a800", head_s=1.32, leg_k=0.72, body_w=0.92,
              belly=20, neck_w=30, sleeve="long", stride=0.9, lift=1.3, arm_swing=1.3, step="heel"),
    voice=dict(voice="en-US-GuyNeural", rate="+18%", pitch="+38Hz"),
    color="#d64933", label="PIP",
)


def add_count(ep, x, facing=1, z=0):
    return ep.cast("count", COUNT["look"], COUNT["voice"], x, facing, 0.9, z, COUNT["label"], COUNT["color"])


def add_pip(ep, x, facing=-1, z=1):
    return ep.cast("pip", PIP["look"], PIP["voice"], x, facing, 0.62, z, PIP["label"], PIP["color"])
