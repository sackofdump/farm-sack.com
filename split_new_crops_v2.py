"""
Split each new 4-stage crop sheet in NEW ASSETS/crops/ into per-stage
PNGs at assets/named/crop_<id>_<n>.png, padded so the visible content
sits centered horizontally on the canvas.
"""
import os
from PIL import Image
import numpy as np

SRC = 'C:/farmsack/NEW ASSETS/crops'
OUT = 'C:/farmsack/assets/named'

# Source filename → crop id used in code.
SHEETS = {
    'Bell_Peppers.png': 'pepper',
    'Blueberries.png':  'blueberry',
    'Cotton.png':       'cotton',
    'Eggplant.png':     'eggplant',
    'Grapes.png':       'grape',
    'Mushrooms.png':    'mushroom',
    'Onions.png':       'onion',
    'Pineapple.png':    'pineapple',
    'Potatoes.png':     'potato',
    'Rice.png':         'rice',
    'Watermelon.png':   'watermelon',
    'Sunflower.png':    'sunflower',
    # Mutations — same 4-stage layout as the base crops.
    'glowbite_pepper.png': 'glowbite_pepper',
    # Animal feed — corn-style crop that fills the silo instead of selling.
    'Animal_feed.png': 'feed_corn',
}

ALPHA_THRESH = 20
PAD = 6

def find_columns(im, min_gap=6):
    a = np.array(im.split()[-1])
    on = (a >= ALPHA_THRESH).any(axis=0)
    runs = []
    in_run = False
    last = -10**9
    start = 0
    for x, v in enumerate(on):
        if v:
            if not in_run or (x - last) > min_gap:
                if in_run: runs.append((start, last + 1))
                start = x; in_run = True
            last = x
    if in_run: runs.append((start, last + 1))
    return runs

def trim_pad(slice_img, pad=PAD):
    a = np.array(slice_img.split()[-1])
    rows = (a >= ALPHA_THRESH).any(axis=1)
    cols = (a >= ALPHA_THRESH).any(axis=0)
    if not rows.any(): return slice_img
    y0, y1 = int(np.argmax(rows)), len(rows) - int(np.argmax(rows[::-1]))
    x0, x1 = int(np.argmax(cols)), len(cols) - int(np.argmax(cols[::-1]))
    cropped = slice_img.crop((x0, y0, x1, y1))
    cw, ch = cropped.size
    out = Image.new('RGBA', (cw + pad * 2, ch + pad), (0, 0, 0, 0))
    out.paste(cropped, (pad, 0))
    return out

for fname, cid in SHEETS.items():
    src = os.path.join(SRC, fname)
    if not os.path.exists(src):
        print(f'  MISSING: {fname}'); continue
    sheet = Image.open(src).convert('RGBA')
    H = sheet.size[1]
    pieces = find_columns(sheet)
    if len(pieces) < 4:
        print(f'  WARN {fname}: {len(pieces)} pieces detected — falling back to /4 split')
        W = sheet.size[0]; cw = W // 4
        pieces = [(i * cw, (i + 1) * cw) for i in range(4)]
    pieces = pieces[:4]
    for i, (x0, x1) in enumerate(pieces, start=1):
        tile = trim_pad(sheet.crop((x0, 0, x1, H)))
        out_path = os.path.join(OUT, f'crop_{cid}_{i}.png')
        tile.save(out_path)
        print(f'  {fname}[stage {i}] -> crop_{cid}_{i}.png  ({tile.size[0]}x{tile.size[1]})')
print('Done.')
