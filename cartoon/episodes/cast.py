"""The recurring cast: Max (clumsy, confident, always wrong) and Lily (calm, knows the real answer)."""

MAX = dict(
    look=dict(skin="#f2c29b", hair="#4a2f22", top="#f07f2a", top2="#d4621a", pants="#3b5c9e",
              shoe="#e8453c", sole="#ffffff", hairstyle="spiky", sleeve="long", hood=True, pocket=True,
              step="sneaker"),
    voice=dict(voice="en-US-GuyNeural", rate="+18%", pitch="+10Hz"),
    color="#f07f2a", label="MAX",
)

LILY = dict(
    look=dict(skin="#d9a07c", hair="#2a1b33", top="#2fb5a6", top2="#22897d", pants="#40355a",
              shoe="#33304a", hairstyle="pony", glasses=True, skirt="#7d55d6", leg_w=38, sleeve="short",
              iris="#3a2a1a", step="heel"),
    voice=dict(voice="en-US-AvaNeural", rate="+15%", pitch="+4Hz"),
    color="#2fb5a6", label="LILY",
)


def add_max(ep, x, facing=1, z=0):
    return ep.cast("max", MAX["look"], MAX["voice"], x, facing, 1.0, z, MAX["label"], MAX["color"])


def add_lily(ep, x, facing=-1, z=1):
    return ep.cast("lily", LILY["look"], LILY["voice"], x, facing, 0.95, z, LILY["label"], LILY["color"])
