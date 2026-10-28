"""Character designs for the series."""
from heroes import mat, glow


def volt():
    suit = mat('volt_suit', '#1546b0', 0.35, coat=0.4, sheen=0.2)
    gold = mat('volt_gold', '#ffc21a', 0.3, 0.6, coat=0.5)
    return dict(
        name='Volt', hair='spiky', mask=True, emblem='bolt', bulk=1.08,
        mats=dict(skin=mat('volt_skin', '#d9a37e', 0.45, sheen=0.3), pelvis=gold, torso=suit, belt=gold,
                  emblem=mat('volt_emblem', '#ffe14a', 0.3, emit='#ffd21f', estr=3.0),
                  shoulder=suit, upperarm=suit, forearm=suit, glove=gold, thigh=suit, shin=suit, boot=gold,
                  neck=suit, mask=mat('volt_mask', '#0b1430', 0.3, coat=0.6), hair=mat('volt_hair', '#1a1210', 0.5),
                  brow=mat('volt_hair', '#1a1210'), iris=mat('volt_iris', '#3fa9ff', 0.2, emit='#3fa9ff', estr=0.6)))


def nova():
    suit = mat('nova_suit', '#5a2a8c', 0.35, coat=0.5, sheen=0.2)
    silver = mat('nova_silver', '#d8dbe6', 0.25, 0.9)
    return dict(
        name='Nova', female=True, hair='long', mask=True, emblem='star', cape=True, bulk=1.0,
        mats=dict(skin=mat('nova_skin', '#f0c4a4', 0.42, sheen=0.3), pelvis=suit, torso=suit, belt=silver,
                  emblem=mat('nova_emblem', '#ffd24a', 0.3, 0.5, emit='#ffcf40', estr=2.5),
                  shoulder=suit, upperarm=suit, forearm=suit, glove=silver, thigh=suit, shin=suit, boot=silver,
                  neck=suit, mask=mat('nova_mask', '#2c0f45', 0.3, coat=0.6), hair=mat('nova_hair', '#b8321c', 0.45, sheen=0.5),
                  brow=mat('nova_brow', '#7a1f12'), lips=mat('nova_lips', '#b24453', 0.35),
                  iris=mat('nova_iris', '#3fbf6f', 0.2), cape=mat('nova_cape', '#c41f4f', 0.55, sheen=0.6)))


def shade():
    cloak = mat('shade_cloak', '#0d0714', 0.75, sheen=0.1)
    dark = mat('shade_dark', '#1d1726', 0.5)
    return dict(
        name='Shade', hair=None, hood=True, cloak=True, glow_eyes=True, bulk=0.95, cuffs=False,
        mats=dict(skin=mat('shade_skin', '#6f6a78', 0.6), pelvis=dark, torso=dark, shoulder=cloak, upperarm=cloak,
                  forearm=cloak, glove=mat('shade_glove', '#2a2433', 0.4, 0.3), thigh=dark, shin=dark, boot=dark,
                  neck=dark, brow=mat('shade_brow', '#1a1520'), cloak=cloak,
                  eye=glow('shade_eye', '#c24bff', 12), mouth=mat('shade_mouth', '#0c0a10', 0.6)))


def worker():
    return dict(
        name='Sam', hair='short', hat='hardhat', bulk=1.0, cuffs=False, no_boot_cuff=False,
        mats=dict(skin=mat('sam_skin', '#8d5a3b', 0.45, sheen=0.3), pelvis=mat('jeans', '#2d4a78', 0.75),
                  torso=mat('shirt', '#7c8288', 0.7), vest=mat('vest', '#ff6a12', 0.55),
                  stripe=mat('reflect', '#e8f0b0', 0.2, 0.3, emit='#e8f0b0', estr=0.4),
                  shoulder=mat('shirt'), upperarm=mat('shirt'), forearm=mat('sam_skin'),
                  glove=mat('work_glove', '#8a6a3a', 0.8), thigh=mat('jeans'), shin=mat('jeans'),
                  boot=mat('work_boot', '#5a3a1e', 0.7), neck=mat('sam_skin'), hair=mat('sam_hair', '#0f0b09', 0.6),
                  brow=mat('sam_hair'), iris=mat('sam_iris', '#4a2c12', 0.2), hat=mat('hardhat', '#ffd000', 0.3, coat=0.8)))
