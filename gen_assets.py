"""
gen_assets.py — generate every FarmSack asset procedurally with PIL.

Replaces the spliced source pack with clean, consistent cartoon sprites:
- terrain tiles, trees, decor, buildings, animals, UI buttons, crops.

Style notes:
- Chunky shapes with darker outlines, soft inner highlights.
- Diamond iso footprint for tiles; side-view critters for animals.
- Output dimensions match what the existing game expects.
"""

from PIL import Image, ImageDraw, ImageFilter
import os, math

OUT = r"C:/farmsack/assets/named"
os.makedirs(OUT, exist_ok=True)

# ============================================================
# COLOR PALETTE
# ============================================================
C = {
    'grass_light': (140, 205, 80),
    'grass_mid':   (105, 180, 60),
    'grass_dark':  (62, 130, 38),
    'grass_outline': (38, 78, 22),
    'dirt_light':  (172, 110, 60),
    'dirt_mid':    (135, 80, 35),
    'dirt_dark':   (90, 50, 22),
    'dirt_outline':(58, 32, 12),
    'wood_light':  (185, 130, 80),
    'wood_mid':    (140, 90, 50),
    'wood_dark':   (90, 55, 30),
    'wood_outline':(50, 28, 14),
    'stone_light': (190, 188, 175),
    'stone_mid':   (150, 145, 130),
    'stone_dark':  (95, 90, 78),
    'stone_outline':(58, 55, 48),
    'water_light': (140, 210, 240),
    'water_mid':   (88, 168, 220),
    'water_dark':  (45, 110, 170),
    'water_outline':(28, 70, 110),
    'red':         (220, 60, 60),
    'red_dark':    (135, 28, 35),
    'red_light':   (250, 105, 100),
    'orange':      (245, 135, 35),
    'orange_dark': (175, 80, 15),
    'orange_light':(255, 175, 90),
    'yellow':      (245, 200, 60),
    'yellow_dark': (170, 130, 25),
    'yellow_light':(255, 230, 110),
    'pink':        (250, 175, 205),
    'pink_dark':   (185, 95, 135),
    'pink_light':  (255, 215, 230),
    'blue':        (90, 145, 220),
    'blue_dark':   (40, 80, 150),
    'leaf':        (100, 180, 60),
    'leaf_dark':   (50, 120, 35),
    'leaf_light':  (150, 220, 100),
    'pine':        (60, 145, 70),
    'pine_dark':   (28, 85, 35),
    'snow':        (240, 248, 252),
    'snow_dark':   (180, 200, 210),
    'cloth_red':   (200, 65, 55),
    'cloth_blue':  (60, 110, 200),
    'cloth_dark':  (50, 30, 20),
    'skin':        (255, 220, 180),
    'skin_dark':   (180, 130, 90),
    'white':       (250, 248, 240),
    'white_dark':  (200, 195, 180),
    'black':       (35, 30, 28),
    'pig_pink':    (245, 180, 175),
    'pig_dark':    (190, 110, 110),
    'cow_white':   (252, 248, 240),
    'cow_black':   (50, 40, 35),
    'horse_brown': (135, 80, 45),
    'horse_dark':  (75, 40, 20),
    'horse_mane':  (50, 30, 15),
    'duck_green':  (50, 110, 70),
    'duck_brown':  (130, 100, 70),
    'dog_brown':   (170, 110, 70),
    'parchment':   (250, 235, 190),
    'parchment_dark':(200, 170, 110),
    'panel_bg':    (225, 195, 130),
}

# ============================================================
# DRAWING HELPERS
# ============================================================
def new_img(w, h):
    return Image.new('RGBA', (w, h), (0, 0, 0, 0))

def diamond(draw, cx, cy, w, h, fill, outline=None, ow=2):
    pts = [(cx, cy - h//2), (cx + w//2, cy), (cx, cy + h//2), (cx - w//2, cy)]
    draw.polygon(pts, fill=fill, outline=outline)
    if outline and ow > 1:
        # Re-draw outline at thickness ow
        draw.line(pts + [pts[0]], fill=outline, width=ow)

def ellipse(draw, cx, cy, rx, ry, fill, outline=None, ow=2):
    bbox = (cx - rx, cy - ry, cx + rx, cy + ry)
    if outline:
        draw.ellipse(bbox, fill=fill, outline=outline, width=ow)
    else:
        draw.ellipse(bbox, fill=fill)

def circle(draw, cx, cy, r, fill, outline=None, ow=2):
    ellipse(draw, cx, cy, r, r, fill, outline, ow)

def rrect(draw, x, y, w, h, r, fill, outline=None, ow=2):
    # Rounded rectangle using PIL's rounded_rectangle (Pillow 8.2+).
    bbox = (x, y, x + w, y + h)
    if outline:
        draw.rounded_rectangle(bbox, radius=r, fill=fill, outline=outline, width=ow)
    else:
        draw.rounded_rectangle(bbox, radius=r, fill=fill)

def line(draw, x1, y1, x2, y2, color, w=2):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=w)

def polygon(draw, pts, fill, outline=None, ow=2):
    draw.polygon(pts, fill=fill, outline=outline)
    if outline and ow > 1:
        draw.line(pts + [pts[0]], fill=outline, width=ow)

def shadow(draw, cx, cy, rx, ry, alpha=80):
    # Draw a soft black ellipse (used as a ground shadow for objects).
    img = Image.new('RGBA', (rx*2 + 4, ry*2 + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, rx*2 + 2, ry*2 + 2), fill=(0, 0, 0, alpha))
    img = img.filter(ImageFilter.GaussianBlur(2))
    return img, (cx - rx - 2, cy - ry - 2)

def paste_shadow(img, sh, pos):
    img.alpha_composite(sh, pos)

# ============================================================
# TERRAIN TILES — 100x80 (diamond + 30 px thickness)
# ============================================================
TILE_W, TILE_H = 96, 48

def tile_canvas():
    return new_img(100, 80)

def draw_iso_block(d, cx, cy, top_color, side_color, outline):
    # Top diamond face
    diamond(d, cx, cy, TILE_W, TILE_H, top_color, outline, 2)
    # Side thickness on bottom-left + bottom-right
    pts_l = [(cx - TILE_W//2, cy),
             (cx, cy + TILE_H//2),
             (cx, cy + TILE_H//2 + 12),
             (cx - TILE_W//2, cy + 12)]
    polygon(d, pts_l, side_color, outline, 2)
    pts_r = [(cx + TILE_W//2, cy),
             (cx, cy + TILE_H//2),
             (cx, cy + TILE_H//2 + 12),
             (cx + TILE_W//2, cy + 12)]
    polygon(d, pts_r, side_color, outline, 2)

def gen_terrain_grass():
    img = tile_canvas(); d = ImageDraw.Draw(img)
    cx, cy = 50, 28
    draw_iso_block(d, cx, cy, C['grass_mid'], C['grass_dark'], C['grass_outline'])
    # Light highlights as small green tufts
    for ox, oy in [(-22, -2), (-8, 8), (16, 2), (8, -8), (-2, 6), (24, -6)]:
        ellipse(d, cx + ox, cy + oy, 3, 2, C['grass_light'])
    return img

def gen_terrain_grass_flowers():
    img = gen_terrain_grass(); d = ImageDraw.Draw(img)
    # Sprinkle a few daisy flowers on the diamond
    for ox, oy in [(-14, 4), (10, -4), (-2, 12)]:
        for da in range(0, 360, 72):
            ax = ox + 3 * math.cos(math.radians(da))
            ay = oy + 2 * math.sin(math.radians(da))
            ellipse(d, 50 + ax, 28 + ay, 1.6, 1.4, C['white'])
        ellipse(d, 50 + ox, 28 + oy, 1.4, 1.2, C['yellow'])
    return img

def gen_terrain_dirt(plowed=False, watered=False):
    img = tile_canvas(); d = ImageDraw.Draw(img)
    cx, cy = 50, 28
    top = C['dirt_mid'] if not watered else (110, 70, 30)
    draw_iso_block(d, cx, cy, top, C['dirt_dark'], C['dirt_outline'])
    # Furrows on the diamond face
    for i in (-1, 0, 1):
        oy = i * 8
        line(d, cx - TILE_W//2 + 8, cy + oy, cx + TILE_W//2 - 8, cy + oy, C['dirt_dark'], 2)
    # Speckles
    for ox, oy in [(-18, 4), (12, -2), (-4, 10), (20, 4), (-10, -8)]:
        ellipse(d, cx + ox, cy + oy, 1.5, 1, C['dirt_light'])
    if watered:
        # Bluish wet sheen
        diamond(d, cx, cy, TILE_W - 4, TILE_H - 4, (100, 145, 195) + (0,))  # ignored alpha
        # Re-render with overlay using alpha blending instead
    return img

def gen_terrain_dirt1(): return gen_terrain_dirt()
def gen_terrain_dirt2():
    img = gen_terrain_dirt(); d = ImageDraw.Draw(img)
    # add little green sprouts to differentiate dirt2
    cx, cy = 50, 28
    for ox, oy in [(-10, 0), (8, 4), (0, -6)]:
        line(d, cx + ox, cy + oy + 2, cx + ox, cy + oy - 4, C['leaf_dark'], 2)
        circle(d, cx + ox, cy + oy - 4, 2, C['leaf'])
    return img

def gen_terrain_water():
    img = tile_canvas(); d = ImageDraw.Draw(img)
    cx, cy = 50, 28
    draw_iso_block(d, cx, cy, C['water_mid'], C['water_dark'], C['water_outline'])
    # Ripples
    for r, oy in [(20, -2), (12, 4)]:
        ellipse(d, cx, cy + oy, r, r//3, None, C['water_light'], 1)
    return img

def gen_terrain_stone():
    img = tile_canvas(); d = ImageDraw.Draw(img)
    cx, cy = 50, 28
    draw_iso_block(d, cx, cy, C['stone_mid'], C['stone_dark'], C['stone_outline'])
    # Cobble-style chunks
    for ox, oy, rx, ry in [(-15, -5, 6, 4), (5, -8, 7, 4), (15, 4, 7, 4),
                            (-10, 8, 6, 4), (-2, 0, 5, 3), (12, -2, 4, 3)]:
        ellipse(d, cx + ox, cy + oy, rx, ry, C['stone_light'], C['stone_outline'], 1)
    return img

def gen_terrain_wood(dark=False):
    img = tile_canvas(); d = ImageDraw.Draw(img)
    cx, cy = 50, 28
    base = C['wood_mid'] if not dark else C['wood_dark']
    draw_iso_block(d, cx, cy, base, C['wood_dark'], C['wood_outline'])
    # Plank lines parallel to iso x-axis
    for i in (-1, 0, 1):
        oy = i * 8
        line(d, cx - TILE_W//2 + 6, cy + oy, cx + TILE_W//2 - 6, cy + oy, C['wood_outline'], 2)
    # Wood-grain dashes
    for ox, oy in [(-12, -4), (8, 4), (16, -8), (-4, 8)]:
        line(d, cx + ox, cy + oy, cx + ox + 6, cy + oy, C['wood_light'], 1)
    return img

def gen_terrain_wood_dark(): return gen_terrain_wood(dark=True)
def gen_terrain_wood_light(): return gen_terrain_wood(dark=False)


# ============================================================
# TREES — 110x180 (trunk + canopy)
# ============================================================
def tree_canvas():
    return new_img(120, 200)

def draw_trunk(d, cx, base_y, w=12, h=36):
    rrect(d, cx - w//2, base_y - h, w, h, 4, C['wood_mid'], C['wood_outline'], 2)
    # Subtle inner highlight
    rrect(d, cx - w//2 + 2, base_y - h + 2, 3, h - 6, 1, C['wood_light'])

def gen_tree_oak(extra_fn=None):
    img = tree_canvas(); d = ImageDraw.Draw(img)
    cx = 60; base = 192
    # Shadow under tree
    sh, pos = shadow(d, cx, base + 2, 28, 7); img.alpha_composite(sh, pos)
    draw_trunk(d, cx, base)
    # Canopy: 3 overlapping circles
    for cxo, cyo, r in [(-14, -50, 22), (14, -50, 22), (0, -65, 24)]:
        circle(d, cx + cxo, base + cyo, r, C['leaf'], C['leaf_dark'], 2)
    # Highlights
    circle(d, cx - 8, base - 70, 6, C['leaf_light'])
    circle(d, cx + 8, base - 55, 4, C['leaf_light'])
    if extra_fn: extra_fn(d, cx, base)
    return img

def gen_tree_apple():
    def fruits(d, cx, base):
        for ox, oy in [(-15, -55), (10, -65), (5, -45), (-8, -70), (15, -50)]:
            circle(d, cx + ox, base + oy, 4, C['red'], C['red_dark'], 1)
            ellipse(d, cx + ox - 1, base + oy - 1, 1, 1, C['red_light'])
    return gen_tree_oak(fruits)

def gen_tree_orange():
    def fruits(d, cx, base):
        for ox, oy in [(-13, -55), (8, -65), (4, -45), (-10, -70), (12, -50)]:
            circle(d, cx + ox, base + oy, 4, C['orange'], C['orange_dark'], 1)
            ellipse(d, cx + ox - 1, base + oy - 1, 1, 1, C['orange_light'])
    return gen_tree_oak(fruits)

def gen_tree_cherry():
    img = tree_canvas(); d = ImageDraw.Draw(img)
    cx = 60; base = 192
    sh, pos = shadow(d, cx, base + 2, 28, 7); img.alpha_composite(sh, pos)
    draw_trunk(d, cx, base)
    for cxo, cyo, r in [(-14, -50, 22), (14, -50, 22), (0, -65, 24)]:
        circle(d, cx + cxo, base + cyo, r, C['pink'], C['pink_dark'], 2)
    circle(d, cx - 8, base - 70, 6, C['pink_light'])
    circle(d, cx + 8, base - 55, 4, C['pink_light'])
    # Petal flecks
    for ox, oy in [(-22, -60), (24, -54), (8, -82), (-6, -38)]:
        circle(d, cx + ox, base + oy, 1.5, C['white'])
    return img

def gen_pine(snow=False, yellow=False):
    img = tree_canvas(); d = ImageDraw.Draw(img)
    cx = 60; base = 192
    sh, pos = shadow(d, cx, base + 2, 22, 6); img.alpha_composite(sh, pos)
    draw_trunk(d, cx, base, w=10, h=22)
    base_y = base - 22
    color = C['pine']
    if yellow:
        color = (140, 175, 50)
    for i, (w_, off) in enumerate([(50, 0), (44, -16), (36, -32), (28, -48)]):
        pts = [(cx, base_y - 14 + off),
               (cx + w_//2, base_y + off),
               (cx - w_//2, base_y + off)]
        polygon(d, pts, color, C['pine_dark'], 2)
        if snow:
            # Snow caps on each layer's top edge
            sp = [(cx - w_//4, base_y + off - 2),
                  (cx + w_//4, base_y + off - 2),
                  (cx + 1, base_y - 12 + off)]
            polygon(d, sp, C['snow'], C['snow_dark'], 1)
    return img

def gen_tree_pine_dark():   return gen_pine()
def gen_tree_pine_yellow(): return gen_pine(yellow=True)
def gen_tree_pine_snow():   return gen_pine(snow=True)

def gen_tree_stump():
    img = new_img(80, 70); d = ImageDraw.Draw(img)
    cx, base = 40, 60
    sh, pos = shadow(d, cx, base + 2, 22, 6); img.alpha_composite(sh, pos)
    # Stump body
    rrect(d, cx - 18, base - 22, 36, 22, 6, C['wood_mid'], C['wood_outline'], 2)
    # Top oval (cut top)
    ellipse(d, cx, base - 22, 18, 7, C['wood_light'], C['wood_outline'], 2)
    # Concentric rings
    for r in (12, 7, 3):
        ellipse(d, cx, base - 22, r, r // 2.5, None, C['wood_dark'], 1)
    return img


# ============================================================
# DECOR — varied sizes
# ============================================================
def gen_decor_bush():
    img = new_img(72, 56); d = ImageDraw.Draw(img)
    cx, base = 36, 50
    sh, pos = shadow(d, cx, base, 18, 5); img.alpha_composite(sh, pos)
    for cxo, cyo, r in [(-10, -16, 12), (10, -16, 12), (0, -22, 14)]:
        circle(d, cx + cxo, base + cyo, r, C['leaf'], C['leaf_dark'], 2)
    circle(d, cx - 4, base - 28, 4, C['leaf_light'])
    return img

def gen_decor_daisies():
    img = new_img(64, 56); d = ImageDraw.Draw(img)
    cx, base = 32, 50
    sh, pos = shadow(d, cx, base, 16, 4); img.alpha_composite(sh, pos)
    # Green tuft base
    ellipse(d, cx, base - 6, 16, 8, C['leaf'], C['leaf_dark'], 1)
    # Daisies
    for fx, fy in [(-10, -10), (8, -14), (-2, -18), (14, -8)]:
        for da in range(0, 360, 72):
            ax = fx + 4 * math.cos(math.radians(da))
            ay = fy + 4 * math.sin(math.radians(da))
            circle(d, cx + ax, base + ay, 2.5, C['white'], C['white_dark'], 1)
        circle(d, cx + fx, base + fy, 1.8, C['yellow'], (140, 100, 25), 1)
    return img

def gen_decor_bluebells():
    img = new_img(64, 56); d = ImageDraw.Draw(img)
    cx, base = 32, 50
    sh, pos = shadow(d, cx, base, 14, 4); img.alpha_composite(sh, pos)
    ellipse(d, cx, base - 6, 14, 7, C['leaf'], C['leaf_dark'], 1)
    for fx, fy in [(-10, -10), (8, -14), (-2, -18), (12, -8), (-6, -16)]:
        # Drooping bluebell
        circle(d, cx + fx, base + fy, 3, C['blue'], C['blue_dark'], 1)
        line(d, cx + fx, base + fy + 2, cx + fx, base + fy - 4, C['leaf_dark'], 1)
    return img

def gen_decor_potted_plant():
    img = new_img(64, 70); d = ImageDraw.Draw(img)
    cx, base = 32, 64
    sh, pos = shadow(d, cx, base, 16, 4); img.alpha_composite(sh, pos)
    # Pot
    pts = [(cx - 14, base - 18), (cx + 14, base - 18),
           (cx + 11, base - 2),  (cx - 11, base - 2)]
    polygon(d, pts, (170, 105, 65), (95, 55, 30), 2)
    # Pot rim
    ellipse(d, cx, base - 18, 14, 4, (200, 130, 80), (95, 55, 30), 1)
    # Plant
    for cxo, cyo, r in [(-7, -28, 10), (7, -28, 10), (0, -36, 12)]:
        circle(d, cx + cxo, base + cyo, r, C['leaf'], C['leaf_dark'], 2)
    return img

def gen_decor_sunflower():
    img = new_img(56, 90); d = ImageDraw.Draw(img)
    cx, base = 28, 84
    sh, pos = shadow(d, cx, base, 12, 3); img.alpha_composite(sh, pos)
    # Pot
    pts = [(cx - 12, base - 14), (cx + 12, base - 14),
           (cx + 9, base - 2),  (cx - 9, base - 2)]
    polygon(d, pts, (170, 105, 65), (95, 55, 30), 2)
    # Stem
    line(d, cx, base - 14, cx, base - 50, C['leaf_dark'], 3)
    # Leaves on stem
    ellipse(d, cx - 5, base - 30, 7, 4, C['leaf'], C['leaf_dark'], 1)
    ellipse(d, cx + 5, base - 38, 7, 4, C['leaf'], C['leaf_dark'], 1)
    # Flower
    for da in range(0, 360, 30):
        ax = cx + 14 * math.cos(math.radians(da))
        ay = base - 60 + 14 * math.sin(math.radians(da))
        ellipse(d, ax, ay, 5, 6, C['yellow'], C['yellow_dark'], 1)
    circle(d, cx, base - 60, 9, (90, 55, 25), (50, 28, 12), 2)
    return img

def gen_decor_log():
    img = new_img(72, 36); d = ImageDraw.Draw(img)
    cx, cy = 36, 24
    sh, pos = shadow(d, cx, cy + 4, 28, 5); img.alpha_composite(sh, pos)
    # Cylinder seen from the side
    rrect(d, cx - 28, cy - 8, 56, 16, 7, C['wood_mid'], C['wood_outline'], 2)
    # End caps
    ellipse(d, cx - 28, cy, 4, 7, C['wood_light'], C['wood_outline'], 1)
    ellipse(d, cx + 28, cy, 4, 7, C['wood_light'], C['wood_outline'], 1)
    # Rings on the visible end
    for r in (5, 3, 1):
        ellipse(d, cx + 28, cy, r * 0.7, r, None, C['wood_dark'], 1)
    return img

def gen_decor_signpost():
    img = new_img(48, 80); d = ImageDraw.Draw(img)
    cx, base = 24, 76
    sh, pos = shadow(d, cx, base, 10, 3); img.alpha_composite(sh, pos)
    # Post
    rrect(d, cx - 2, base - 50, 4, 50, 1, C['wood_mid'], C['wood_outline'], 2)
    # Sign
    rrect(d, cx - 16, base - 56, 32, 18, 3, (200, 170, 110), C['wood_outline'], 2)
    # "→" on sign
    line(d, cx - 8, base - 47, cx + 8, base - 47, C['wood_outline'], 2)
    line(d, cx + 4, base - 51, cx + 8, base - 47, C['wood_outline'], 2)
    line(d, cx + 4, base - 43, cx + 8, base - 47, C['wood_outline'], 2)
    return img

def gen_decor_mailbox():
    img = new_img(48, 80); d = ImageDraw.Draw(img)
    cx, base = 24, 76
    sh, pos = shadow(d, cx, base, 10, 3); img.alpha_composite(sh, pos)
    # Post
    rrect(d, cx - 2, base - 50, 4, 50, 1, C['wood_mid'], C['wood_outline'], 2)
    # Mailbox body
    rrect(d, cx - 12, base - 60, 24, 18, 6, C['red'], C['red_dark'], 2)
    # Door divider
    line(d, cx, base - 60, cx, base - 42, C['red_dark'], 2)
    # Flag
    rrect(d, cx + 12, base - 58, 6, 4, 1, C['red'], C['red_dark'], 1)
    return img

def gen_decor_barrel():
    img = new_img(56, 64); d = ImageDraw.Draw(img)
    cx, base = 28, 60
    sh, pos = shadow(d, cx, base, 14, 4); img.alpha_composite(sh, pos)
    # Body
    rrect(d, cx - 16, base - 36, 32, 36, 8, C['wood_mid'], C['wood_outline'], 2)
    # Bands (metal hoops)
    line(d, cx - 16, base - 28, cx + 16, base - 28, C['wood_dark'], 3)
    line(d, cx - 16, base - 12, cx + 16, base - 12, C['wood_dark'], 3)
    # Top
    ellipse(d, cx, base - 36, 16, 5, C['wood_light'], C['wood_outline'], 2)
    # Stave lines
    for i in (-10, -3, 4, 11):
        line(d, cx + i, base - 33, cx + i, base - 4, C['wood_dark'], 1)
    return img

def gen_decor_crate():
    img = new_img(56, 56); d = ImageDraw.Draw(img)
    cx, base = 28, 52
    sh, pos = shadow(d, cx, base, 16, 4); img.alpha_composite(sh, pos)
    # Cube-ish crate
    pts = [(cx - 18, base - 28), (cx, base - 36),
           (cx + 18, base - 28), (cx, base - 20)]
    polygon(d, pts, C['wood_light'], C['wood_outline'], 2)  # top
    pts = [(cx - 18, base - 28), (cx, base - 20),
           (cx, base - 0), (cx - 18, base - 8)]
    polygon(d, pts, C['wood_mid'], C['wood_outline'], 2)
    pts = [(cx + 18, base - 28), (cx, base - 20),
           (cx, base - 0), (cx + 18, base - 8)]
    polygon(d, pts, C['wood_dark'], C['wood_outline'], 2)
    return img

def gen_decor_lamppost():
    img = new_img(40, 100); d = ImageDraw.Draw(img)
    cx, base = 20, 96
    sh, pos = shadow(d, cx, base, 8, 3); img.alpha_composite(sh, pos)
    # Pole base
    rrect(d, cx - 4, base - 6, 8, 6, 1, C['wood_dark'], C['wood_outline'], 1)
    rrect(d, cx - 2, base - 80, 4, 80, 1, C['wood_dark'], C['wood_outline'], 1)
    # Lamp top
    rrect(d, cx - 9, base - 90, 18, 10, 4, C['yellow_dark'], C['wood_outline'], 2)
    # Glow window
    rrect(d, cx - 7, base - 88, 14, 6, 2, C['yellow_light'], C['yellow_dark'], 1)
    # Cap
    pts = [(cx - 9, base - 90), (cx + 9, base - 90), (cx, base - 96)]
    polygon(d, pts, C['wood_dark'], C['wood_outline'], 1)
    return img

def gen_decor_well():
    img = new_img(80, 90); d = ImageDraw.Draw(img)
    cx, base = 40, 84
    sh, pos = shadow(d, cx, base, 24, 6); img.alpha_composite(sh, pos)
    # Stone base
    ellipse(d, cx, base - 4, 26, 8, C['stone_mid'], C['stone_outline'], 2)
    rrect(d, cx - 26, base - 26, 52, 22, 6, C['stone_mid'], C['stone_outline'], 2)
    # Stone block lines
    for i in (-13, 0, 13):
        line(d, cx + i, base - 26, cx + i, base - 6, C['stone_outline'], 1)
    line(d, cx - 26, base - 16, cx + 26, base - 16, C['stone_outline'], 1)
    # Water inside
    ellipse(d, cx, base - 30, 22, 6, C['water_mid'], C['water_outline'], 2)
    # Roof posts
    line(d, cx - 18, base - 30, cx - 18, base - 60, C['wood_mid'], 4)
    line(d, cx + 18, base - 30, cx + 18, base - 60, C['wood_mid'], 4)
    # Roof
    pts = [(cx - 26, base - 60), (cx, base - 78), (cx + 26, base - 60)]
    polygon(d, pts, C['red'], C['red_dark'], 2)
    return img


# ============================================================
# ANIMALS — side view, ~80x70
# ============================================================
def animal_canvas():
    return new_img(96, 80)

def gen_animal_cow():
    img = animal_canvas(); d = ImageDraw.Draw(img)
    cx, base = 48, 70
    sh, pos = shadow(d, cx, base, 28, 6); img.alpha_composite(sh, pos)
    # Body
    rrect(d, cx - 26, base - 30, 50, 22, 11, C['cow_white'], C['cow_black'], 2)
    # Spots
    for ox, oy, rx, ry in [(-12, -22, 6, 4), (8, -18, 7, 5), (-2, -28, 4, 3)]:
        ellipse(d, cx + ox, base + oy, rx, ry, C['cow_black'])
    # Head
    rrect(d, cx + 16, base - 36, 18, 16, 6, C['cow_white'], C['cow_black'], 2)
    ellipse(d, cx + 30, base - 28, 5, 4, C['pig_pink'], C['cow_black'], 1)  # snout
    # Eye
    circle(d, cx + 26, base - 32, 1.5, C['cow_black'])
    # Horns
    polygon(d, [(cx + 18, base - 36), (cx + 16, base - 42), (cx + 20, base - 38)], (250, 240, 200), C['cow_black'], 1)
    polygon(d, [(cx + 28, base - 36), (cx + 30, base - 42), (cx + 26, base - 38)], (250, 240, 200), C['cow_black'], 1)
    # Legs
    for ox in (-18, -8, 6, 16):
        rrect(d, cx + ox - 3, base - 12, 6, 12, 2, C['cow_white'], C['cow_black'], 2)
    # Tail
    line(d, cx - 26, base - 24, cx - 32, base - 14, C['cow_black'], 3)
    return img

def gen_animal_chicken():
    img = animal_canvas(); d = ImageDraw.Draw(img)
    cx, base = 48, 70
    sh, pos = shadow(d, cx, base, 14, 4); img.alpha_composite(sh, pos)
    # Body
    ellipse(d, cx, base - 18, 16, 14, C['white'], C['black'], 2)
    # Wing
    ellipse(d, cx + 2, base - 16, 10, 7, C['white_dark'], C['black'], 1)
    # Head
    circle(d, cx + 12, base - 26, 7, C['white'], C['black'], 2)
    # Comb
    for ox in (-2, 2, 6):
        circle(d, cx + 12 + ox, base - 32, 2, C['red'], C['red_dark'], 1)
    # Beak
    polygon(d, [(cx + 18, base - 25), (cx + 22, base - 24), (cx + 18, base - 23)],
            C['orange'], C['orange_dark'], 1)
    # Eye
    circle(d, cx + 13, base - 27, 1, C['black'])
    # Legs
    line(d, cx - 4, base - 4, cx - 4, base + 4, C['orange'], 2)
    line(d, cx + 4, base - 4, cx + 4, base + 4, C['orange'], 2)
    return img

def gen_animal_pig():
    img = animal_canvas(); d = ImageDraw.Draw(img)
    cx, base = 48, 70
    sh, pos = shadow(d, cx, base, 24, 5); img.alpha_composite(sh, pos)
    # Body
    ellipse(d, cx, base - 22, 24, 14, C['pig_pink'], C['pig_dark'], 2)
    # Head
    circle(d, cx + 18, base - 26, 10, C['pig_pink'], C['pig_dark'], 2)
    # Snout
    ellipse(d, cx + 26, base - 24, 4, 3, (220, 150, 145), C['pig_dark'], 1)
    circle(d, cx + 25, base - 24, 0.8, C['pig_dark'])
    circle(d, cx + 27, base - 24, 0.8, C['pig_dark'])
    # Eye
    circle(d, cx + 20, base - 28, 1, C['black'])
    # Ear
    polygon(d, [(cx + 14, base - 32), (cx + 18, base - 36), (cx + 18, base - 30)],
            C['pig_pink'], C['pig_dark'], 1)
    # Legs
    for ox in (-14, -4, 6, 14):
        rrect(d, cx + ox - 3, base - 14, 6, 12, 2, C['pig_pink'], C['pig_dark'], 2)
    # Curly tail
    line(d, cx - 22, base - 24, cx - 26, base - 22, C['pig_dark'], 2)
    return img

def gen_animal_sheep():
    img = animal_canvas(); d = ImageDraw.Draw(img)
    cx, base = 48, 70
    sh, pos = shadow(d, cx, base, 22, 5); img.alpha_composite(sh, pos)
    # Wool body — multiple bumps
    for ox, oy, r in [(-14, -22, 9), (-4, -26, 10), (6, -24, 10), (14, -22, 9)]:
        circle(d, cx + ox, base + oy, r, C['white'], C['cow_black'], 2)
    # Head (dark)
    circle(d, cx + 18, base - 24, 7, (60, 50, 45), C['black'], 2)
    # Ears
    ellipse(d, cx + 12, base - 30, 2, 4, (60, 50, 45), C['black'], 1)
    ellipse(d, cx + 24, base - 30, 2, 4, (60, 50, 45), C['black'], 1)
    # Eye
    circle(d, cx + 20, base - 24, 1, C['white'])
    # Legs (dark)
    for ox in (-12, -4, 4, 12):
        rrect(d, cx + ox - 2, base - 12, 4, 12, 1, (60, 50, 45), C['black'], 1)
    return img

def gen_animal_horse():
    img = animal_canvas(); d = ImageDraw.Draw(img)
    cx, base = 48, 70
    sh, pos = shadow(d, cx, base, 26, 6); img.alpha_composite(sh, pos)
    # Body
    rrect(d, cx - 24, base - 30, 46, 20, 9, C['horse_brown'], C['horse_dark'], 2)
    # Head
    rrect(d, cx + 16, base - 38, 14, 18, 5, C['horse_brown'], C['horse_dark'], 2)
    # Snout
    ellipse(d, cx + 28, base - 26, 3, 2, C['horse_dark'])
    circle(d, cx + 22, base - 32, 1, C['black'])
    # Mane
    for ox in (-24, -18, -12, -6, 0, 6, 12):
        line(d, cx + ox, base - 30, cx + ox - 2, base - 36, C['horse_mane'], 3)
    # Ears
    polygon(d, [(cx + 18, base - 38), (cx + 18, base - 44), (cx + 22, base - 38)],
            C['horse_brown'], C['horse_dark'], 1)
    # Legs
    for ox in (-18, -8, 6, 16):
        rrect(d, cx + ox - 3, base - 14, 6, 14, 2, C['horse_brown'], C['horse_dark'], 2)
    # Tail
    line(d, cx - 24, base - 24, cx - 32, base - 16, C['horse_mane'], 4)
    return img

def gen_animal_goat():
    img = animal_canvas(); d = ImageDraw.Draw(img)
    cx, base = 48, 70
    sh, pos = shadow(d, cx, base, 22, 5); img.alpha_composite(sh, pos)
    # Body
    rrect(d, cx - 22, base - 26, 40, 18, 9, C['white'], C['cow_black'], 2)
    # Head
    rrect(d, cx + 14, base - 32, 14, 14, 5, C['white'], C['cow_black'], 2)
    # Beard
    polygon(d, [(cx + 22, base - 18), (cx + 26, base - 18), (cx + 24, base - 12)],
            C['white_dark'], C['cow_black'], 1)
    # Horns
    polygon(d, [(cx + 16, base - 32), (cx + 14, base - 40), (cx + 18, base - 36)],
            (200, 180, 150), C['cow_black'], 1)
    polygon(d, [(cx + 26, base - 32), (cx + 28, base - 40), (cx + 24, base - 36)],
            (200, 180, 150), C['cow_black'], 1)
    # Eye
    circle(d, cx + 20, base - 26, 1, C['black'])
    # Legs
    for ox in (-16, -6, 6, 14):
        rrect(d, cx + ox - 2, base - 12, 4, 12, 1, C['white'], C['cow_black'], 1)
    return img

def gen_animal_duck():
    img = animal_canvas(); d = ImageDraw.Draw(img)
    cx, base = 48, 70
    sh, pos = shadow(d, cx, base, 18, 4); img.alpha_composite(sh, pos)
    # Body
    ellipse(d, cx, base - 18, 18, 12, C['duck_brown'], C['black'], 2)
    # Tail
    polygon(d, [(cx - 18, base - 22), (cx - 24, base - 18), (cx - 18, base - 16)],
            C['duck_brown'], C['black'], 1)
    # Wing
    ellipse(d, cx, base - 16, 12, 6, (170, 140, 100), C['black'], 1)
    # Head (green)
    circle(d, cx + 16, base - 26, 8, C['duck_green'], C['black'], 2)
    # Bill
    polygon(d, [(cx + 22, base - 24), (cx + 28, base - 24), (cx + 24, base - 22)],
            C['orange'], C['orange_dark'], 1)
    # Eye
    circle(d, cx + 18, base - 28, 1, C['black'])
    # Legs
    line(d, cx - 4, base - 6, cx - 4, base + 4, C['orange'], 2)
    line(d, cx + 4, base - 6, cx + 4, base + 4, C['orange'], 2)
    return img

def gen_animal_dog():
    img = animal_canvas(); d = ImageDraw.Draw(img)
    cx, base = 48, 70
    sh, pos = shadow(d, cx, base, 20, 5); img.alpha_composite(sh, pos)
    # Body
    rrect(d, cx - 20, base - 22, 36, 16, 8, C['dog_brown'], C['black'], 2)
    # White belly patch
    rrect(d, cx - 12, base - 14, 16, 8, 4, C['white'])
    # Head
    circle(d, cx + 12, base - 26, 9, C['dog_brown'], C['black'], 2)
    # Ear
    ellipse(d, cx + 6, base - 32, 3, 6, (110, 70, 40), C['black'], 1)
    # Snout
    ellipse(d, cx + 20, base - 24, 4, 3, C['white_dark'], C['black'], 1)
    circle(d, cx + 22, base - 26, 1, C['black'])
    # Eye
    circle(d, cx + 14, base - 28, 1, C['black'])
    # Legs
    for ox in (-14, -4, 4, 12):
        rrect(d, cx + ox - 2, base - 8, 4, 10, 1, C['dog_brown'], C['black'], 1)
    # Tail
    line(d, cx - 20, base - 20, cx - 28, base - 24, C['dog_brown'], 3)
    line(d, cx - 28, base - 24, cx - 28, base - 18, C['white'], 2)
    return img


# ============================================================
# BUILDINGS — large structures
# ============================================================
def gen_building_house():
    img = new_img(120, 130); d = ImageDraw.Draw(img)
    cx, base = 60, 124
    sh, pos = shadow(d, cx, base, 44, 8); img.alpha_composite(sh, pos)
    # Body (cream)
    rrect(d, cx - 36, base - 60, 72, 60, 4, (240, 220, 175), C['wood_outline'], 2)
    # Door
    rrect(d, cx - 8, base - 30, 16, 30, 3, (110, 70, 35), C['wood_outline'], 2)
    circle(d, cx + 4, base - 16, 1, C['yellow'])
    # Windows
    rrect(d, cx - 28, base - 50, 12, 12, 2, C['water_light'], C['wood_outline'], 2)
    line(d, cx - 22, base - 50, cx - 22, base - 38, C['wood_outline'], 1)
    line(d, cx - 28, base - 44, cx - 16, base - 44, C['wood_outline'], 1)
    rrect(d, cx + 16, base - 50, 12, 12, 2, C['water_light'], C['wood_outline'], 2)
    line(d, cx + 22, base - 50, cx + 22, base - 38, C['wood_outline'], 1)
    line(d, cx + 16, base - 44, cx + 28, base - 44, C['wood_outline'], 1)
    # Roof (blue)
    pts = [(cx - 42, base - 60), (cx, base - 96), (cx + 42, base - 60)]
    polygon(d, pts, C['blue'], C['blue_dark'], 2)
    # Roof shading
    polygon(d, [(cx - 42, base - 60), (cx, base - 96), (cx, base - 60)],
            (60, 100, 175), C['blue_dark'], 0)
    # Chimney
    rrect(d, cx + 14, base - 90, 8, 14, 1, (180, 120, 80), C['wood_outline'], 1)
    return img

def gen_building_barn():
    img = new_img(140, 140); d = ImageDraw.Draw(img)
    cx, base = 70, 134
    sh, pos = shadow(d, cx, base, 54, 9); img.alpha_composite(sh, pos)
    # Body (red)
    rrect(d, cx - 40, base - 60, 80, 60, 4, C['cloth_red'], C['red_dark'], 2)
    # White trim
    rrect(d, cx - 40, base - 62, 80, 4, 2, C['white'], C['red_dark'], 1)
    # Doors
    rrect(d, cx - 18, base - 42, 36, 42, 2, C['white'], C['red_dark'], 2)
    line(d, cx, base - 42, cx, base, C['red_dark'], 2)
    # X cross
    line(d, cx - 18, base - 42, cx, base, C['red_dark'], 1)
    line(d, cx, base - 42, cx - 18, base, C['red_dark'], 1)
    line(d, cx + 18, base - 42, cx, base, C['red_dark'], 1)
    line(d, cx, base - 42, cx + 18, base, C['red_dark'], 1)
    # Roof (gambrel)
    pts = [(cx - 44, base - 60), (cx - 36, base - 84),
           (cx, base - 96), (cx + 36, base - 84), (cx + 44, base - 60)]
    polygon(d, pts, (60, 50, 45), (28, 22, 18), 2)
    # Hayloft window
    pts = [(cx - 8, base - 70), (cx + 8, base - 70),
           (cx + 8, base - 84), (cx, base - 90), (cx - 8, base - 84)]
    polygon(d, pts, C['white'], C['red_dark'], 2)
    # Silo on the right
    rrect(d, cx + 44, base - 76, 18, 76, 6, (170, 50, 50), (90, 25, 30), 2)
    ellipse(d, cx + 53, base - 76, 9, 4, (190, 70, 70), (90, 25, 30), 1)
    # Silo top
    pts = [(cx + 44, base - 76), (cx + 53, base - 92), (cx + 62, base - 76)]
    polygon(d, pts, (60, 50, 45), (28, 22, 18), 2)
    return img

def gen_building_market_stall():
    img = new_img(120, 130); d = ImageDraw.Draw(img)
    cx, base = 60, 124
    sh, pos = shadow(d, cx, base, 44, 8); img.alpha_composite(sh, pos)
    # Stall counter (wood)
    rrect(d, cx - 38, base - 36, 76, 36, 4, C['wood_mid'], C['wood_outline'], 2)
    # Boards
    line(d, cx - 38, base - 24, cx + 38, base - 24, C['wood_outline'], 1)
    line(d, cx - 38, base - 12, cx + 38, base - 12, C['wood_outline'], 1)
    # Posts
    line(d, cx - 36, base - 36, cx - 36, base - 86, C['wood_dark'], 6)
    line(d, cx + 36, base - 36, cx + 36, base - 86, C['wood_dark'], 6)
    # Awning roof (red+white stripes)
    awn = [(cx - 48, base - 86), (cx + 48, base - 86),
           (cx + 38, base - 70), (cx - 38, base - 70)]
    polygon(d, awn, C['cloth_red'], C['red_dark'], 2)
    # Stripes
    for i, x_off in enumerate(range(-44, 44, 12)):
        if i % 2 == 0:
            polygon(d, [(cx + x_off, base - 86), (cx + x_off + 12, base - 86),
                         (cx + x_off + 9, base - 70), (cx + x_off + 3, base - 70)],
                    C['white'], C['red_dark'], 1)
    # Veggies on the counter
    circle(d, cx - 22, base - 38, 5, C['orange'], C['orange_dark'], 1)  # pumpkin
    circle(d, cx - 8, base - 38, 4, C['red'], C['red_dark'], 1)         # tomato
    circle(d, cx + 6, base - 38, 4, C['leaf'], C['leaf_dark'], 1)       # cabbage
    ellipse(d, cx + 18, base - 38, 5, 3, C['yellow'], C['yellow_dark'], 1)  # corn
    return img

def gen_building_windmill():
    img = new_img(120, 150); d = ImageDraw.Draw(img)
    cx, base = 60, 144
    sh, pos = shadow(d, cx, base, 36, 7); img.alpha_composite(sh, pos)
    # Tower (red brick-ish)
    rrect(d, cx - 22, base - 90, 44, 90, 6, (170, 60, 50), (90, 25, 30), 2)
    # Brick lines
    for i in range(0, 88, 12):
        line(d, cx - 22, base - i, cx + 22, base - i, (90, 25, 30), 1)
    # Door
    rrect(d, cx - 6, base - 22, 12, 22, 2, C['wood_dark'], C['wood_outline'], 1)
    # Window
    circle(d, cx, base - 50, 4, C['water_light'], C['wood_outline'], 1)
    # Cap (dark)
    pts = [(cx - 26, base - 90), (cx + 26, base - 90), (cx, base - 110)]
    polygon(d, pts, (50, 45, 40), (25, 22, 18), 2)
    # Hub
    circle(d, cx, base - 90, 4, C['wood_dark'], (28, 22, 18), 1)
    # Sails (4 blades)
    for ang in (0, 90, 180, 270):
        rad = math.radians(ang + 30)  # offset so they aren't axis-aligned
        x2 = cx + 36 * math.cos(rad)
        y2 = base - 90 + 36 * math.sin(rad)
        line(d, cx, base - 90, x2, y2, C['wood_outline'], 4)
        # blade rectangle
        bx = cx + 30 * math.cos(rad)
        by = base - 90 + 30 * math.sin(rad)
        rrect(d, bx - 6, by - 3, 12, 6, 1, (240, 220, 180), C['wood_outline'], 1)
    return img


# ============================================================
# UI BUTTONS — 80x80 wooden tile + central icon
# ============================================================
def ui_canvas():
    return new_img(80, 80)

def draw_ui_tile(d, accent=None):
    rrect(d, 4, 4, 72, 72, 12, (245, 220, 165), (110, 70, 35), 3)
    rrect(d, 8, 8, 64, 64, 8, (250, 230, 180), (180, 130, 75), 1)
    if accent:
        rrect(d, 4, 4, 72, 72, 12, accent + (40,), (110, 70, 35), 3)

def gen_ui_button(icon_fn):
    img = ui_canvas(); d = ImageDraw.Draw(img)
    draw_ui_tile(d)
    icon_fn(d)
    return img

def icon_select(d):
    cx, cy = 40, 40
    pts = [(cx - 8, cy - 16), (cx - 8, cy + 14), (cx - 2, cy + 6),
           (cx + 2, cy + 16), (cx + 6, cy + 14), (cx + 2, cy + 4),
           (cx + 12, cy + 4)]
    polygon(d, pts, C['white'], C['black'], 2)

def icon_move(d):
    cx, cy = 40, 40
    # Open hand: palm + 4 fingers + thumb
    rrect(d, cx - 14, cy - 6, 28, 18, 6, C['skin'], C['skin_dark'], 2)
    for fx in (-9, -2, 5, 11):
        rrect(d, cx + fx - 2, cy - 18, 5, 14, 2, C['skin'], C['skin_dark'], 2)

def icon_plow(d):
    cx, cy = 40, 40
    # Pickaxe: handle + head
    rrect(d, cx - 2, cy - 18, 4, 36, 1, C['wood_mid'], C['wood_outline'], 2)
    # Head
    polygon(d, [(cx - 16, cy - 16), (cx + 16, cy - 16), (cx + 14, cy - 8), (cx - 14, cy - 8)],
            C['stone_mid'], C['stone_outline'], 2)

def icon_plant(d):
    cx, cy = 40, 40
    # Soil mound
    polygon(d, [(cx - 16, cy + 16), (cx + 16, cy + 16), (cx + 12, cy + 8), (cx - 12, cy + 8)],
            C['dirt_mid'], C['dirt_outline'], 2)
    # Sprout
    line(d, cx, cy + 8, cx, cy - 12, C['leaf_dark'], 3)
    ellipse(d, cx - 6, cy - 8, 8, 6, C['leaf'], C['leaf_dark'], 2)
    ellipse(d, cx + 6, cy - 8, 8, 6, C['leaf'], C['leaf_dark'], 2)
    ellipse(d, cx, cy - 16, 6, 5, C['leaf_light'], C['leaf_dark'], 2)

def icon_water(d):
    cx, cy = 40, 40
    # Drop shape
    pts = []
    for t in range(0, 361, 10):
        rad = math.radians(t)
        if t < 180:
            x = cx + 14 * math.sin(rad)
            y = cy + 8 - 14 * math.cos(rad)
        else:
            x = cx + 14 * math.sin(rad)
            y = cy + 8 - 14 * math.cos(rad)
        pts.append((x, y))
    # Tear drop = circle bottom + triangle top
    polygon(d, [(cx, cy - 18), (cx - 12, cy + 4), (cx + 12, cy + 4)], C['water_mid'], C['water_outline'], 2)
    ellipse(d, cx, cy + 4, 14, 12, C['water_mid'], C['water_outline'], 2)
    # Highlight
    ellipse(d, cx - 3, cy, 3, 5, C['water_light'])

def icon_harvest(d):
    cx, cy = 40, 40
    # Sickle handle
    rrect(d, cx - 14, cy + 4, 14, 4, 1, C['wood_mid'], C['wood_outline'], 2)
    # Blade arc
    pts = []
    for t in range(180, 361, 10):
        rad = math.radians(t)
        x = cx - 4 + 18 * math.cos(rad)
        y = cy + 4 + 16 * math.sin(rad)
        pts.append((x, y))
    pts.append((cx - 4, cy + 4))
    polygon(d, pts, C['stone_mid'], C['stone_outline'], 2)
    # wheat ear
    ellipse(d, cx + 8, cy - 8, 4, 8, C['yellow'], C['yellow_dark'], 1)

def icon_sell(d):
    cx, cy = 40, 40
    # Coin stack
    for i in (0, 1, 2):
        ellipse(d, cx, cy - 4 + i*5, 14, 4, C['yellow'], C['yellow_dark'], 2)
    circle(d, cx, cy - 8, 12, C['yellow'], C['yellow_dark'], 2)
    # ¢ symbol
    line(d, cx - 4, cy - 14, cx - 4, cy - 2, C['yellow_dark'], 2)
    polygon(d, [(cx - 6, cy - 12), (cx + 4, cy - 14), (cx + 4, cy - 10)], C['yellow_dark'], None, 0)
    polygon(d, [(cx - 6, cy - 6), (cx + 4, cy - 4), (cx + 4, cy - 8)], C['yellow_dark'], None, 0)

def icon_build(d):
    cx, cy = 40, 40
    # Hammer
    rrect(d, cx - 2, cy - 4, 4, 24, 1, C['wood_mid'], C['wood_outline'], 2)
    rrect(d, cx - 14, cy - 16, 28, 14, 3, C['stone_mid'], C['stone_outline'], 2)
    rrect(d, cx + 6, cy - 14, 6, 10, 1, C['stone_dark'])

# Menu icons
def icon_shop(d):
    cx, cy = 40, 40
    # Awning red+white stripes
    pts = [(cx - 22, cy - 12), (cx + 22, cy - 12), (cx + 16, cy), (cx - 16, cy)]
    polygon(d, pts, C['cloth_red'], C['red_dark'], 2)
    for i in range(-18, 18, 8):
        polygon(d, [(cx + i, cy - 12), (cx + i + 8, cy - 12),
                     (cx + i + 4, cy), (cx + i - 4, cy)],
                C['white'], C['red_dark'], 1)
    # Counter base
    rrect(d, cx - 18, cy, 36, 18, 2, C['wood_mid'], C['wood_outline'], 2)
    # Veggies on counter
    circle(d, cx - 10, cy + 6, 3, C['orange'])
    circle(d, cx, cy + 6, 3, C['red'])
    circle(d, cx + 10, cy + 6, 3, C['leaf'])

def icon_inventory(d):
    cx, cy = 40, 40
    # Briefcase / bag
    rrect(d, cx - 16, cy - 8, 32, 24, 4, (170, 110, 60), C['wood_outline'], 2)
    # Handle
    rrect(d, cx - 10, cy - 16, 20, 8, 4, None, C['wood_outline'], 2)
    # Buckle
    rrect(d, cx - 4, cy - 2, 8, 4, 1, C['yellow'], C['yellow_dark'], 1)

def icon_orders(d):
    cx, cy = 40, 40
    # Clipboard
    rrect(d, cx - 14, cy - 18, 28, 36, 3, C['white'], C['black'], 2)
    rrect(d, cx - 8, cy - 22, 16, 6, 2, (170, 130, 80), C['wood_outline'], 2)
    for y in (-10, -2, 6):
        line(d, cx - 8, cy + y, cx + 8, cy + y, C['black'], 1)

def icon_achievements(d):
    cx, cy = 40, 40
    # Trophy
    rrect(d, cx - 14, cy - 16, 28, 16, 4, C['yellow'], C['yellow_dark'], 2)
    # Handles
    polygon(d, [(cx - 14, cy - 14), (cx - 22, cy - 8), (cx - 14, cy - 2)], C['yellow_dark'], C['yellow_dark'], 1)
    polygon(d, [(cx + 14, cy - 14), (cx + 22, cy - 8), (cx + 14, cy - 2)], C['yellow_dark'], C['yellow_dark'], 1)
    # Stem
    rrect(d, cx - 4, cy, 8, 6, 1, C['yellow_dark'])
    # Base
    rrect(d, cx - 12, cy + 6, 24, 6, 2, C['yellow_dark'], C['black'], 1)

def icon_friends(d):
    cx, cy = 40, 40
    # Two heads
    circle(d, cx - 8, cy - 6, 8, C['skin'], C['skin_dark'], 2)
    circle(d, cx + 8, cy - 6, 8, C['skin'], C['skin_dark'], 2)
    # Bodies
    polygon(d, [(cx - 16, cy + 16), (cx - 1, cy + 16), (cx - 4, cy + 2), (cx - 12, cy + 2)],
            C['cloth_blue'], C['blue_dark'], 1)
    polygon(d, [(cx + 1, cy + 16), (cx + 16, cy + 16), (cx + 12, cy + 2), (cx + 4, cy + 2)],
            C['cloth_red'], C['red_dark'], 1)

def icon_gifts(d):
    cx, cy = 40, 40
    # Box
    rrect(d, cx - 16, cy - 8, 32, 24, 3, C['cloth_red'], C['red_dark'], 2)
    # Lid
    rrect(d, cx - 18, cy - 14, 36, 8, 2, C['cloth_red'], C['red_dark'], 2)
    # Ribbon (vertical)
    rrect(d, cx - 3, cy - 14, 6, 30, 1, C['yellow'], C['yellow_dark'], 1)
    # Bow
    polygon(d, [(cx - 10, cy - 18), (cx - 2, cy - 14), (cx - 10, cy - 12)], C['yellow'], C['yellow_dark'], 1)
    polygon(d, [(cx + 10, cy - 18), (cx + 2, cy - 14), (cx + 10, cy - 12)], C['yellow'], C['yellow_dark'], 1)

# Misc UI buttons (BUY / SELL / UPGRADE / X / ? / GEAR)
def gen_misc_button(label, color):
    img = new_img(96, 56); d = ImageDraw.Draw(img)
    rrect(d, 2, 2, 92, 52, 12, color, (color[0]//2, color[1]//2, color[2]//2), 3)
    rrect(d, 4, 4, 88, 8, 6, (min(255, color[0]+30), min(255, color[1]+30), min(255, color[2]+30)))
    # Center text label drawn at known size
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
    except Exception:
        font = None
    bbox = d.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
    d.text(((96 - tw)//2, (56 - th)//2 - 1), label, fill=C['white'], font=font)
    return img

def gen_ui_buy():     return gen_misc_button('BUY',     (108, 195, 70))
def gen_ui_sellbtn(): return gen_misc_button('SELL',    (210, 75, 70))
def gen_ui_upgrade(): return gen_misc_button('UPGRADE', (75, 130, 200))

def gen_ui_close():
    img = new_img(56, 56); d = ImageDraw.Draw(img)
    rrect(d, 2, 2, 52, 52, 14, (210, 75, 70), (130, 30, 35), 3)
    line(d, 16, 16, 40, 40, C['white'], 5)
    line(d, 40, 16, 16, 40, C['white'], 5)
    return img

def gen_ui_help():
    img = new_img(56, 56); d = ImageDraw.Draw(img)
    rrect(d, 2, 2, 52, 52, 14, C['yellow'], C['yellow_dark'], 3)
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
    except Exception:
        font = None
    bbox = d.textbbox((0, 0), '?', font=font)
    tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
    d.text(((56 - tw)//2 - 1, (56 - th)//2 - 4), '?', fill=C['black'], font=font)
    return img

def gen_ui_settings():
    img = new_img(56, 56); d = ImageDraw.Draw(img)
    rrect(d, 2, 2, 52, 52, 14, C['wood_mid'], C['wood_outline'], 3)
    cx, cy = 28, 28
    # Gear: outer star + inner circle
    pts = []
    for i in range(16):
        ang = i * (math.pi * 2 / 16)
        r = 16 if i % 2 == 0 else 10
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    polygon(d, pts, C['stone_mid'], C['stone_outline'], 2)
    circle(d, cx, cy, 4, C['stone_dark'], C['stone_outline'], 1)
    return img


# ============================================================
# MAIN — emit everything
# ============================================================
def save(name, img):
    img.save(os.path.join(OUT, name + '.png'))

def main():
    # Terrain
    save('terrain_grass',         gen_terrain_grass())
    save('terrain_grass_flowers', gen_terrain_grass_flowers())
    save('terrain_dirt1',         gen_terrain_dirt1())
    save('terrain_dirt2',         gen_terrain_dirt2())
    save('terrain_water',         gen_terrain_water())
    save('terrain_stone',         gen_terrain_stone())
    save('terrain_wood_dark',     gen_terrain_wood_dark())
    save('terrain_wood_light',    gen_terrain_wood_light())
    # Trees
    save('tree_oak',         gen_tree_oak())
    save('tree_apple',       gen_tree_apple())
    save('tree_orange',      gen_tree_orange())
    save('tree_cherry',      gen_tree_cherry())
    save('tree_pine_dark',   gen_tree_pine_dark())
    save('tree_pine_yellow', gen_tree_pine_yellow())
    save('tree_pine_snow',   gen_tree_pine_snow())
    save('tree_stump',       gen_tree_stump())
    # Decor
    save('decor_bush',         gen_decor_bush())
    save('decor_daisies',      gen_decor_daisies())
    save('decor_bluebells',    gen_decor_bluebells())
    save('decor_potted_plant', gen_decor_potted_plant())
    save('decor_sunflower',    gen_decor_sunflower())
    save('decor_log',          gen_decor_log())
    save('decor_signpost',     gen_decor_signpost())
    save('decor_mailbox',      gen_decor_mailbox())
    save('decor_barrel',       gen_decor_barrel())
    save('decor_crate',        gen_decor_crate())
    save('decor_lamppost',     gen_decor_lamppost())
    save('decor_well',         gen_decor_well())
    # Animals
    save('animal_cow',     gen_animal_cow())
    save('animal_chicken', gen_animal_chicken())
    save('animal_pig',     gen_animal_pig())
    save('animal_sheep',   gen_animal_sheep())
    save('animal_horse',   gen_animal_horse())
    save('animal_goat',    gen_animal_goat())
    save('animal_duck',    gen_animal_duck())
    save('animal_dog',     gen_animal_dog())
    # Buildings
    save('building_house',        gen_building_house())
    save('building_barn',         gen_building_barn())
    save('building_market_stall', gen_building_market_stall())
    save('building_windmill',     gen_building_windmill())
    # UI tools
    save('ui_select',  gen_ui_button(icon_select))
    save('ui_move',    gen_ui_button(icon_move))
    save('ui_plow',    gen_ui_button(icon_plow))
    save('ui_plant',   gen_ui_button(icon_plant))
    save('ui_water',   gen_ui_button(icon_water))
    save('ui_harvest', gen_ui_button(icon_harvest))
    save('ui_sell',    gen_ui_button(icon_sell))
    save('ui_build',   gen_ui_button(icon_build))
    # Menu
    save('ui_shop',         gen_ui_button(icon_shop))
    save('ui_inventory',    gen_ui_button(icon_inventory))
    save('ui_orders',       gen_ui_button(icon_orders))
    save('ui_achievements', gen_ui_button(icon_achievements))
    save('ui_friends',      gen_ui_button(icon_friends))
    save('ui_gifts',        gen_ui_button(icon_gifts))
    # Misc UI buttons
    save('ui_buy',      gen_ui_buy())
    save('ui_sellbtn',  gen_ui_sellbtn())
    save('ui_upgrade',  gen_ui_upgrade())
    save('ui_close',    gen_ui_close())
    save('ui_help',     gen_ui_help())
    save('ui_settings', gen_ui_settings())
    print('Generated all assets.')

if __name__ == '__main__':
    main()
