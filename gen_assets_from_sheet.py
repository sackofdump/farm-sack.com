"""
Extract individual sprites from C:/farmsack/farm.png and write them to
assets/named/ with the filenames the game expects.

Background removal: 4-connected flood fill from the edges over white pixels.
Anything not reachable from the edge stays — so white pixels INSIDE a sprite
(daisy petals, sheep wool, etc.) are preserved.

Per-section bounding boxes are hand-tuned from a connected-component dump
of the source sheet.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = 'C:/farmsack/farm.png'
OUT = 'C:/farmsack/assets/named'
os.makedirs(OUT, exist_ok=True)

# ---------- Background removal ----------
rgb = np.array(Image.open(SRC).convert('RGB'))
H, W = rgb.shape[:2]
white = (rgb[:, :, 0] > 232) & (rgb[:, :, 1] > 232) & (rgb[:, :, 2] > 232)
lab, _ = ndimage.label(white)  # 4-connected by default
edge = np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]]))
edge = edge[edge != 0]
bg = np.isin(lab, edge)
alpha = np.where(bg, 0, 255).astype(np.uint8)
sheet = Image.fromarray(np.dstack([rgb, alpha]), 'RGBA')

# ---------- Helpers ----------
def crop_trim(x0, y0, x1, y1, pad=2):
    sub = sheet.crop((int(x0), int(y0), int(x1), int(y1)))
    bb = sub.getbbox()
    if not bb:
        return None
    xa, ya, xb, yb = bb
    xa = max(0, xa - pad); ya = max(0, ya - pad)
    xb = min(sub.size[0], xb + pad); yb = min(sub.size[1], yb + pad)
    return sub.crop((xa, ya, xb, yb))

written = []
def save(name, im):
    if im is None:
        print(f'  SKIP {name}: empty crop')
        return
    im.save(os.path.join(OUT, f'{name}.png'))
    written.append(name)

def grid(x0, y0, x1, y1, rows, cols, names):
    cw = (x1 - x0) / cols
    ch = (y1 - y0) / rows
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            if idx >= len(names): break
            n = names[idx]
            if n is None: continue
            xa = x0 + c * cw
            xb = x0 + (c + 1) * cw
            ya = y0 + r * ch
            yb = y0 + (r + 1) * ch
            save(n, crop_trim(xa, ya, xb, yb))

# ---------- TERRAIN (2 rows x 4 cols, skip row 3 path tiles) ----------
grid(28, 58, 472, 242, 2, 4, [
    'terrain_grass', 'terrain_wood_dark', 'terrain_wood_light', 'terrain_grass_flowers',
    'terrain_water', 'terrain_stone', 'terrain_dirt1', 'terrain_dirt2',
])

# ---------- TREES (2 rows x 4 cols) ----------
grid(510, 50, 945, 318, 2, 4, [
    'tree_oak', 'tree_apple', 'tree_orange', 'tree_cherry',
    'tree_pine_dark', 'tree_pine_yellow', 'tree_pine_snow', 'tree_stump',
])

# ---------- DECOR (4 rows x 4 cols, with empty cells; hand boxes) ----------
decor = {
    # Row 1: rocks (skip), daisies, bush, log
    'decor_daisies':      (1080,  56, 1192, 134),
    'decor_bush':         (1200,  56, 1290, 134),
    'decor_log':          (1290,  56, 1390, 134),
    # Row 2: signpost, mailbox, barrel, crate
    'decor_signpost':     ( 985, 130, 1080, 215),
    'decor_mailbox':      (1080, 130, 1185, 215),
    'decor_barrel':       (1195, 130, 1285, 215),
    'decor_crate':        (1290, 130, 1390, 215),
    # Row 3: empty, well, bench (skip), sunflower
    'decor_well':         (1080, 210, 1190, 300),
    'decor_sunflower':    (1300, 210, 1390, 300),
    # Row 4: bluebells, grass-tuft (used as potted_plant), lamppost
    'decor_bluebells':    ( 975, 285, 1080, 380),
    'decor_potted_plant': (1080, 285, 1185, 380),
    'decor_lamppost':     (1195, 280, 1285, 380),
}
for n, b in decor.items():
    save(n, crop_trim(*b))

# ---------- CROPS (6 crops x 4 stages each) ----------
# Row groups: strawberry+carrot (y~410-475), corn+tomato (y~485-575), wheat+pumpkin (y~575-670)
# LEFT crops: stages at x ~ 530, 605, 680, 760 (skip leftmost component which is the row label)
# RIGHT crops: stages at x ~ 950, 1040, 1140, 1240
LEFT_X  = [(525, 600), (600, 680), (680, 755), (755, 835)]
RIGHT_X = [(945, 1035), (1035, 1135), (1135, 1230), (1230, 1335)]
crop_rows = [
    ('strawberry', LEFT_X,  395, 480),
    ('carrot',     RIGHT_X, 392, 482),
    ('corn',       LEFT_X,  483, 575),
    ('tomato',     RIGHT_X, 480, 578),
    ('wheat',      LEFT_X,  570, 672),
    ('pumpkin',    RIGHT_X, 575, 675),
]
for name, xs, y0, y1 in crop_rows:
    for i, (xa, xb) in enumerate(xs, start=1):
        save(f'crop_{name}_{i}', crop_trim(xa, y0, xb, y1))

# ---------- BUILDINGS (4 large structures in one row) ----------
bldgs = {
    'building_house':        ( 25, 665, 250, 865),
    'building_barn':         (260, 665, 460, 855),
    'building_market_stall': (465, 685, 610, 845),
    'building_windmill':     (605, 660, 755, 850),
}
for n, b in bldgs.items():
    save(n, crop_trim(*b))

# ---------- ANIMALS (2 rows x 4 cols; cow+horse share column 1) ----------
animals = {
    # Row 1
    'animal_cow':     ( 840, 705,  965, 775),
    'animal_chicken': ( 980, 690, 1080, 775),
    'animal_pig':     (1100, 690, 1205, 775),
    'animal_sheep':   (1245, 685, 1355, 775),
    # Row 2
    'animal_horse':   ( 840, 775,  975, 875),
    'animal_goat':    ( 985, 775, 1090, 875),
    'animal_duck':    (1115, 775, 1210, 875),
    'animal_dog':     (1245, 775, 1355, 875),
}
for n, b in animals.items():
    save(n, crop_trim(*b))

# ---------- TOP-BAR UI CHIPS (coin / cash / star / lightning / gear) ----------
topbar = {
    'bottom_01': ( 35, 905,  220, 970),  # coin chip
    'bottom_02': ( 225, 905, 395, 970),  # cash chip
    'bottom_03': ( 400, 900, 595, 970),  # star/level chip
    'bottom_04': ( 600, 905, 750, 970),  # lightning chip
    'bottom_05': ( 752, 905, 815, 970),  # gear button (sole right)
}
for n, b in topbar.items():
    save(n, crop_trim(*b))

# ---------- TOOL BUTTONS (8 buttons in lower-left bar) ----------
tools = ['ui_select', 'ui_move', 'ui_plow', 'ui_plant', 'ui_water', 'ui_harvest', 'ui_sell', 'ui_build']
tool_xs = [(40, 122), (132, 215), (225, 307), (318, 400), (411, 492), (502, 585), (595, 678), (688, 770)]
for n, (xa, xb) in zip(tools, tool_xs):
    save(n, crop_trim(xa, 1015, xb, 1100))

# ---------- MENU/SHOP BUTTONS (6 buttons in upper-right bar) ----------
menu = ['ui_shop', 'ui_inventory', 'ui_orders', 'ui_achievements', 'ui_friends', 'ui_gifts']
menu_xs = [(835, 920), (925, 1010), (1020, 1090), (1110, 1190), (1200, 1290), (1295, 1380)]
for n, (xa, xb) in zip(menu, menu_xs):
    save(n, crop_trim(xa, 895, xb, 985))

# ---------- MISC UI BUTTONS (BUY / SELL / UPGRADE / X / ? / gear) ----------
misc = {
    'ui_buy':      ( 840, 1045,  920, 1110),
    'ui_sellbtn':  ( 925, 1045, 1015, 1110),
    'ui_upgrade':  (1020, 1045, 1130, 1110),
    'ui_close':    (1135, 1045, 1210, 1110),
    'ui_help':     (1215, 1045, 1290, 1110),
    'ui_settings': (1290, 1045, 1380, 1110),
}
for n, b in misc.items():
    save(n, crop_trim(*b))

print(f'\nWrote {len(written)} sprites to {OUT}')
