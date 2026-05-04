"""
Procedural placeholder crop_carrot_{1..4}.png and crop_corn_{1..4}.png so the
game runs cleanly until real carrot/corn artwork is provided.

Each image: a transparent 256x256 canvas with the plant body in the upper
~70% (matching the new sprite convention) — drawCropOnTile renders only the
top 70% of source, anchoring sprite bottom at iso diamond bottom.
"""
import os
import math
import random
from PIL import Image, ImageDraw

OUT = 'C:/farmsack/assets/named'
os.makedirs(OUT, exist_ok=True)

W, H = 256, 256
GROUND = int(H * 0.70)  # y at which plant base sits (so renderer crops cleanly)

def new_canvas():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))

# ---------------- CARROT ----------------
def draw_carrot_leaf(d, cx, base_y, length, side, color=(85, 165, 55), dark=(45, 110, 35)):
    # leaf as a tapered ellipse leaning outward
    sway = side * 0.35
    tip_x = cx + sway * length
    tip_y = base_y - length
    # body
    pts = []
    for t in range(0, 361, 18):
        rad = math.radians(t)
        x0 = 6 * math.cos(rad)
        y0 = (length / 2) * math.sin(rad) - length / 2
        # rotate by sway angle
        ang = math.atan2(sway, 1) * 0.5
        rx = x0 * math.cos(ang) - y0 * math.sin(ang)
        ry = x0 * math.sin(ang) + y0 * math.cos(ang)
        pts.append((cx + rx, base_y + ry))
    d.polygon(pts, fill=color, outline=dark)

def make_carrot(stage):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx = W // 2
    if stage == 1:
        # tiny pair of leaves
        draw_carrot_leaf(d, cx - 4, GROUND, 24, -1)
        draw_carrot_leaf(d, cx + 4, GROUND, 24, +1)
    elif stage == 2:
        for dx, side, l in ((-10, -1.2, 38), (-2, -0.4, 44), (6, 0.6, 42), (12, 1.2, 36)):
            draw_carrot_leaf(d, cx + dx, GROUND, l, side)
    elif stage == 3:
        for dx, side, l in ((-14, -1.3, 50), (-4, -0.4, 58), (4, 0.4, 60), (14, 1.2, 52)):
            draw_carrot_leaf(d, cx + dx, GROUND, l, side)
        # carrot tops barely peeking above ground
        d.polygon([(cx - 14, GROUND - 2), (cx - 8, GROUND - 2),
                   (cx - 11, GROUND + 6)], fill=(255, 140, 60), outline=(170, 75, 20))
        d.polygon([(cx + 6, GROUND - 2), (cx + 12, GROUND - 2),
                   (cx + 9, GROUND + 6)], fill=(255, 140, 60), outline=(170, 75, 20))
    else:  # stage 4 mature
        for dx, side, l in ((-18, -1.3, 60), (-6, -0.5, 70), (6, 0.5, 70), (18, 1.2, 60)):
            draw_carrot_leaf(d, cx + dx, GROUND, l, side)
        # 3 carrots clearly visible
        for offs in (-18, 0, 18):
            cxo = cx + offs
            d.polygon([(cxo - 8, GROUND), (cxo + 8, GROUND),
                       (cxo + 4, GROUND + 26), (cxo - 4, GROUND + 26)],
                      fill=(255, 140, 65), outline=(165, 75, 20))
            d.polygon([(cxo - 6, GROUND + 2), (cxo - 4, GROUND + 2),
                       (cxo - 4, GROUND + 24), (cxo - 6, GROUND + 22)],
                      fill=(255, 180, 110))
    return img

# ---------------- CORN ----------------
def draw_corn_stalk(d, cx, base_y, height, leaf_starts):
    d.line([(cx, base_y), (cx, base_y - height)], fill=(95, 175, 70), width=4)
    for sy, side in leaf_starts:
        ly = base_y - sy
        pts = [(cx, ly),
               (cx + side * 18, ly + 4),
               (cx + side * 14, ly + 10),
               (cx, ly + 4)]
        d.polygon(pts, fill=(95, 175, 70), outline=(45, 110, 35))

def make_corn(stage):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx = W // 2
    if stage == 1:
        d.line([(cx, GROUND), (cx, GROUND - 18)], fill=(95, 175, 70), width=3)
        d.polygon([(cx - 6, GROUND - 14), (cx, GROUND - 8), (cx + 6, GROUND - 14),
                   (cx, GROUND - 18)], fill=(105, 185, 80))
    elif stage == 2:
        draw_corn_stalk(d, cx - 12, GROUND, 50, [(20, -1), (32, 1)])
        draw_corn_stalk(d, cx + 12, GROUND, 50, [(20, 1), (32, -1)])
    elif stage == 3:
        for dx in (-18, 0, 18):
            draw_corn_stalk(d, cx + dx, GROUND, 80,
                            [(22, -1), (38, 1), (54, -1)])
        # green cob hint
        d.ellipse([cx - 4, GROUND - 64, cx + 4, GROUND - 44],
                  fill=(150, 195, 90), outline=(80, 130, 35))
    else:  # stage 4 mature
        for dx in (-22, -8, 8, 22):
            draw_corn_stalk(d, cx + dx, GROUND, 110,
                            [(28, -1), (46, 1), (62, -1), (78, 1)])
        # three yellow cobs
        for cob_dx in (-15, 0, 15):
            cxo = cx + cob_dx
            d.ellipse([cxo - 5, GROUND - 92, cxo + 5, GROUND - 60],
                      fill=(244, 208, 63), outline=(150, 105, 25))
            for ky in range(-88, -60, 4):
                d.line([(cxo - 4, GROUND + ky), (cxo + 4, GROUND + ky)],
                       fill=(170, 125, 30), width=1)
            # tassel
            for tx in (-3, 0, 3):
                d.line([(cxo, GROUND - 92), (cxo + tx, GROUND - 102)],
                       fill=(220, 180, 90), width=1)
    return img

# ---------------- save ----------------
for stage in (1, 2, 3, 4):
    make_carrot(stage).save(os.path.join(OUT, f'crop_carrot_{stage}.png'))
    make_corn(stage).save(os.path.join(OUT, f'crop_corn_{stage}.png'))
print('Wrote 8 placeholder crop sprites (carrot + corn x 4 stages).')
