"""'Faris & Puff' cast: Faris, a tall, gentle, slightly dramatic man in a long blue robe with kohl-lined eyes,
and Puff, a polar bear cub who is NOT built for the heat."""

FARIS = dict(
    look=dict(skin="#d9a27c", hair="#1b1416", brow="#1b1416", brow_w=10, beard="#1b1416", kohl=True,
              top="#2c5aa0", top2="#244a85", coat=370, cape="#1f3f78", cape_in="#d9b24a", cape_collar=False,
              pants="#2c5aa0", shoe="#8a5a3a", sole=None, hairstyle="slick", eye_s=0.8, iris="#3a2416",
              leg_k=1.3, neck_len=14, body_w=0.86, head_s=0.95, sleeve="long", stride=1.0, mouth_dy=10,
              step="sneaker"),
    voice=dict(voice="en-US-BrianNeural", rate="+10%", pitch="-2Hz"),
    color="#2c5aa0", label="FARIS",
)

PUFF = dict(
    look=dict(skin="#eef1f4", top="#eef1f4", top2="#dfe4ea", pants="#eef1f4", shoe="#dfe4ea", hair="#eef1f4",
              muzzle="#ffffff", species="bear", nose="bear", hairstyle="none", paw=True, eye_s=0.72, eye_gap=0.85,
              leg_k=0.6, body_w=1.38, belly=24, head_s=1.4, neck_w=70, sleeve="long", stride=0.9, lift=1.1,
              mouth_dy=4, iris="#1e1410", step="paw"),
    voice=dict(voice="en-US-AnaNeural", rate="+8%", pitch="+0Hz"),
    color="#5aa9d6", label="PUFF",
)


def add_faris(ep, x, facing=1, z=0):
    return ep.cast("faris", FARIS["look"], FARIS["voice"], x, facing, 0.92, z, FARIS["label"], FARIS["color"])


def add_puff(ep, x, facing=-1, z=1):
    return ep.cast("puff", PUFF["look"], PUFF["voice"], x, facing, 0.56, z, PUFF["label"], PUFF["color"])
