"""
Generate clean cartoon crop sprites for FarmSack.

Each crop has 4 stages and fits a 96x100 canvas: an iso dirt diamond at the
bottom, with plant artwork sized for the stage.

Output: assets/named/crop_<name>_<stage>.png  (transparent PNG)
"""
from PIL import Image, ImageDraw
import os

OUT = r"C:/farmsack/assets/named"

W, H = 100, 110
TILE_W = 92
TILE_H = 46

# ---------- Helpers ----------
def diamond(draw, cx, cy, w, h, fill, outline=None, ow=2):
    pts = [(cx, cy - h//2), (cx + w//2, cy), (cx, cy + h//2), (cx - w//2, cy)]
    draw.polygon(pts, fill=fill, outline=outline)

def ellipse(draw, cx, cy, rx, ry, fill, outline=None, ow=2):
    bbox = (cx - rx, cy - ry, cx + rx, cy + ry)
    draw.ellipse(bbox, fill=fill, outline=outline, width=ow)

def line(draw, x1, y1, x2, y2, color, w=2):
    draw.line([(x1,y1),(x2,y2)], fill=color, width=w)

def rect(draw, x, y, w, h, fill, outline=None, ow=2):
    draw.rectangle((x, y, x+w, y+h), fill=fill, outline=outline, width=ow)

# Dirt tile background (used by every stage of every crop)
def draw_dirt(draw, cx, cy):
    """Anchor: cy is the CENTER of the dirt diamond face."""
    # Outer outline (slightly larger for cartoon outline)
    diamond(draw, cx, cy, TILE_W + 2, TILE_H + 2, (60, 35, 15))
    # Two-tone dirt
    diamond(draw, cx, cy, TILE_W, TILE_H, (152, 92, 42))
    # Lighter highlight on the upper-left half
    pts = [(cx, cy - TILE_H//2 + 2),
           (cx + TILE_W//2 - 4, cy),
           (cx, cy),
           (cx - TILE_W//2 + 4, cy)]
    draw.polygon(pts, fill=(180, 115, 60))
    # Furrow lines
    for i in (-1, 0, 1):
        y_off = i * 8
        diamond(draw, cx, cy + y_off, TILE_W - 12, 6, (110, 65, 25))

# ---------- Plant primitives ----------
def sprout(draw, x, y, color=(95, 175, 70), dark=(45, 110, 35)):
    """Small two-leaf sprout, base at (x,y)."""
    ellipse(draw, x - 3, y - 4, 4, 5, color, dark, 1)
    ellipse(draw, x + 3, y - 4, 4, 5, color, dark, 1)
    ellipse(draw, x, y - 1, 2, 3, (60, 130, 50))

def bush(draw, x, y, h=12, color=(85, 165, 65), dark=(40, 100, 35), accent=None):
    ellipse(draw, x - 5, y - h//2, 6, h//2 + 2, color, dark, 1)
    ellipse(draw, x + 5, y - h//2, 6, h//2 + 2, color, dark, 1)
    ellipse(draw, x, y - h, 7, h//2 + 3, color, dark, 1)
    # Highlight
    ellipse(draw, x - 2, y - h - 1, 3, 3, (130, 200, 100))
    if accent:
        ellipse(draw, x, y - h, 3, 3, accent, (60,30,15), 1)

# ---------- Per-crop mature plants ----------
def draw_wheat_mature(draw, x, y):
    # Stalks
    for dx in (-3, 0, 3):
        line(draw, x + dx, y, x + dx, y - 22, (170, 130, 50), 2)
    # Wheat heads
    for dx, sy in ((-3, -22), (0, -28), (3, -22)):
        ellipse(draw, x + dx, y + sy, 4, 7, (242, 200, 70), (140, 100, 30), 1)
        # grain marks
        for i in (-2, 0, 2):
            line(draw, x + dx - 3, y + sy + i*2, x + dx + 3, y + sy + i*2, (140, 100, 30), 1)
        # awns
        line(draw, x + dx, y + sy - 7, x + dx - 2, y + sy - 11, (170, 130, 50), 1)
        line(draw, x + dx, y + sy - 7, x + dx + 2, y + sy - 11, (170, 130, 50), 1)

def draw_strawberry_mature(draw, x, y):
    # Leaves
    bush(draw, x, y, h=14)
    # Berries
    for dx, sy in ((-6, -2), (5, -1), (0, -8)):
        # heart-shaped berry
        ellipse(draw, x + dx, y + sy, 4, 5, (230, 60, 75), (130, 25, 35), 1)
        # seeds
        draw.point((x + dx - 1, y + sy - 1), fill=(255, 240, 170))
        draw.point((x + dx + 1, y + sy + 1), fill=(255, 240, 170))
        draw.point((x + dx + 1, y + sy - 1), fill=(255, 240, 170))

def draw_carrot_mature(draw, x, y):
    # Orange root visible above ground
    pts = [(x - 4, y - 1), (x + 4, y - 1), (x + 2, y + 6), (x - 2, y + 6)]
    draw.polygon(pts, fill=(255, 140, 65), outline=(170, 75, 20))
    # Highlight
    pts2 = [(x - 3, y), (x - 1, y), (x - 1, y + 5), (x - 3, y + 4)]
    draw.polygon(pts2, fill=(255, 180, 110))
    # Leafy tops
    for dx, ang in ((-3, -0.4), (0, 0), (3, 0.4)):
        # leaf as a tall ellipse
        rotated_leaf(draw, x + dx, y - 4, ang)

def rotated_leaf(draw, cx, cy, angle):
    # Approximation: tall ellipse with a darker outline at angle
    import math
    rx, ry = 3, 12
    pts = []
    for t in range(0, 361, 20):
        rad = math.radians(t)
        x0 = rx * math.cos(rad)
        y0 = ry * math.sin(rad) - ry  # anchor base at bottom
        # rotate
        x1 = x0 * math.cos(angle) - y0 * math.sin(angle)
        y1 = x0 * math.sin(angle) + y0 * math.cos(angle)
        pts.append((cx + x1, cy + y1))
    draw.polygon(pts, fill=(95, 175, 70), outline=(45, 110, 35))

def draw_corn_mature(draw, x, y):
    # Stalk
    line(draw, x, y, x, y - 30, (95, 175, 70), 4)
    # Leaves curling out
    for side, sy in ((-1, -10), (1, -16), (-1, -22)):
        pts = [(x, y + sy),
               (x + side*10, y + sy + 4),
               (x + side*8, y + sy + 8),
               (x, y + sy + 4)]
        draw.polygon(pts, fill=(95, 175, 70), outline=(45, 110, 35))
    # Cob
    rx, ry = 4, 10
    bbox = (x + 1, y - 22, x + 9, y - 2)
    draw.ellipse(bbox, fill=(244, 208, 63), outline=(150, 105, 25), width=1)
    # Kernel rows
    for i in range(-2, 3):
        line(draw, x + 2, y - 12 + i*3, x + 8, y - 12 + i*3, (170, 125, 30), 1)
    # Tassel
    for tx in (-2, 0, 2):
        line(draw, x, y - 30, x + tx, y - 35, (220, 180, 90), 1)

def draw_tomato_mature(draw, x, y):
    # Bushy green base
    bush(draw, x, y, h=14, color=(75, 150, 60))
    # Tomatoes
    for dx, sy, r in ((-5, -6, 4), (5, -10, 4), (-1, -16, 3)):
        ellipse(draw, x + dx, y + sy, r, r, (230, 60, 70), (130, 25, 35), 1)
        # highlight
        ellipse(draw, x + dx - 1, y + sy - 1, 1, 1, (255, 200, 200))
        # green calyx
        pts = [(x + dx, y + sy - r),
               (x + dx - 2, y + sy - r - 2),
               (x + dx + 2, y + sy - r - 2)]
        draw.polygon(pts, fill=(75, 150, 60), outline=(40, 100, 35))

def draw_pumpkin_mature(draw, x, y):
    # Big orange pumpkin
    ellipse(draw, x, y - 8, 14, 11, (245, 130, 30), (130, 60, 10), 2)
    # Ribs
    for rib_x in (-7, -3, 3, 7):
        ellipse(draw, x + rib_x, y - 8, 2, 9, (200, 95, 15))
    # Highlight
    ellipse(draw, x - 5, y - 12, 3, 2, (255, 180, 90))
    # Stem
    rect(draw, x - 1, y - 21, 3, 5, (95, 175, 70), (40, 100, 35))

# ---------- Stage builders ----------
def make_image():
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    return img

def gen_crop(name):
    """Return list of 4 PIL images, one per stage."""
    out = []
    cx = W // 2
    cy_dirt = H - 30                 # center of dirt diamond
    plant_y = cy_dirt - TILE_H//4    # baseline for plants

    for stage in (1, 2, 3, 4):
        img = make_image()
        d = ImageDraw.Draw(img)
        draw_dirt(d, cx, cy_dirt)
        # Plant cluster offsets for 5 plants
        offsets = [(-22, +6), (0, +8), (22, +6), (-12, -4), (12, -4)]
        for ox, oy in offsets:
            px = cx + ox
            py = plant_y + oy
            if stage == 1:
                sprout(d, px, py)
            elif stage == 2:
                bush(d, px, py, h=10)
            elif stage == 3:
                # Developing — slightly bigger bush + hint of color
                hint = {
                    'wheat':      (242, 200, 70),
                    'strawberry': (230, 60, 75),
                    'carrot':     (255, 140, 65),
                    'corn':       (244, 208, 63),
                    'tomato':     (230, 60, 70),
                    'pumpkin':    (245, 130, 30),
                }[name]
                bush(d, px, py, h=14, accent=hint)
            else:
                # Stage 4 — mature, per-crop unique
                draw_fn = {
                    'wheat':      draw_wheat_mature,
                    'strawberry': draw_strawberry_mature,
                    'carrot':     draw_carrot_mature,
                    'corn':       draw_corn_mature,
                    'tomato':     draw_tomato_mature,
                    'pumpkin':    draw_pumpkin_mature,
                }[name]
                draw_fn(d, px, py)
        out.append(img)
    return out

def main():
    os.makedirs(OUT, exist_ok=True)
    for name in ('wheat', 'strawberry', 'carrot', 'corn', 'tomato', 'pumpkin'):
        imgs = gen_crop(name)
        for i, img in enumerate(imgs, start=1):
            img.save(os.path.join(OUT, f'crop_{name}_{i}.png'))
    print('Saved 24 crop sprites.')

if __name__ == '__main__':
    main()
