"""'Stretch & Bruno' cast (flat pastel style): a very tall, clumsy, kind-hearted guy and his wise little bear."""

STRETCH = dict(
    look=dict(skin="#f6c7a1", hair="#3b2a3f", top="#ef6f6c", top2="#d85a58", pants="#3d5a80", shoe="#ffd166",
              sole="#fff6e0", hairstyle="tuft", nose="button", eye_s=0.85, leg_k=1.42, neck_len=70, neck_w=30,
              body_w=0.72, head_s=0.92, stride=0.95, lift=1.3, arm_swing=1.3, sleeve="long", iris="#2a2a3a",
              step="sneaker", stripe="#f4f1de"),
    voice=dict(voice="en-US-AndrewNeural", rate="+14%", pitch="+8Hz"),
    color="#ef6f6c", label="STRETCH",
)

BRUNO = dict(
    look=dict(skin="#9c6b45", top="#9c6b45", top2="#8a5d3b", pants="#9c6b45", shoe="#7f5536", hair="#9c6b45",
              muzzle="#e8c9a0", belly_patch="#e8c9a0", species="bear", nose="bear", hairstyle="none", paw=True,
              eye_s=0.55, eye_gap=0.85, leg_k=0.58, body_w=1.45, belly=30, head_s=1.15, neck_w=70, sleeve="long",
              stride=0.9, lift=0.9, mouth_dy=4, iris="#1e1410", step="paw"),
    voice=dict(voice="en-US-ChristopherNeural", rate="+4%", pitch="-16Hz"),
    color="#9c6b45", label="BRUNO",
)


def add_stretch(ep, x, facing=1, z=0):
    return ep.cast("stretch", STRETCH["look"], STRETCH["voice"], x, facing, 0.92, z, STRETCH["label"], STRETCH["color"])


def add_bruno(ep, x, facing=-1, z=1):
    return ep.cast("bruno", BRUNO["look"], BRUNO["voice"], x, facing, 0.95, z, BRUNO["label"], BRUNO["color"])
