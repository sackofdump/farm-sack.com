"""
Split each 2x2 crop-stage sheet in NEW ASSETS/ into 4 individual stage PNGs
with proper alpha trimming, written to assets/named/crop_<name>_<1..4>.png.

Stage order within each sheet: TL=1, TR=2, BL=3, BR=4.
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

SRC_DIR = 'C:/farmsack/NEW ASSETS/crops'
OUT_DIR = 'C:/farmsack/assets/named'

# 2x2 sheets: TL=stage1, TR=stage2, BL=stage3, BR=stage4
SHEETS = {
    'new_pumpkin.png':    'pumpkin',
    'new_strawberry.png': 'strawberry',
    'new_tomatos.png':    'tomato',
    'new_wheat.png':      'wheat',
}

# 4x2 sheets: top row = first crop stages 1-4, bottom row = second crop stages 1-4
SHEETS_4x2 = {
    'new_corncarrots.png': ('corn', 'carrot'),
}

def keep_largest_blob(im, alpha_threshold=20):
    """Within a quadrant, keep only the largest connected blob; clear the rest.
    Removes any sprite-bleed from adjacent quadrants."""
    arr = np.array(im)
    a = arr[:, :, 3]
    mask = a >= alpha_threshold
    # Dilate so antialiased edges of the same sprite stay connected
    mask_d = ndimage.binary_dilation(mask, iterations=2)
    lab, n = ndimage.label(mask_d)
    if n == 0:
        return im
    sizes = ndimage.sum(mask_d, lab, range(1, n + 1))
    biggest = int(np.argmax(sizes)) + 1
    keep = lab == biggest
    arr[~keep, 3] = 0
    return Image.fromarray(arr, 'RGBA')


def trim_alpha(im, pad=4, alpha_threshold=20):
    a = im.split()[-1]
    mask = a.point(lambda v: 255 if v >= alpha_threshold else 0)
    bb = mask.getbbox()
    if not bb:
        return im
    x0, y0, x1, y1 = bb
    x0 = max(0, x0 - pad); y0 = max(0, y0 - pad)
    x1 = min(im.size[0], x1 + pad); y1 = min(im.size[1], y1 + pad)
    return im.crop((x0, y0, x1, y1))

for fname, crop_id in SHEETS.items():
    src = Image.open(os.path.join(SRC_DIR, fname)).convert('RGBA')
    W, H = src.size
    halfW, halfH = W // 2, H // 2
    quads = {
        1: (0, 0, halfW, halfH),       # TL
        2: (halfW, 0, W, halfH),       # TR
        3: (0, halfH, halfW, H),       # BL
        4: (halfW, halfH, W, H),       # BR
    }
    for stage, box in quads.items():
        tile = src.crop(box)
        tile = keep_largest_blob(tile)
        tile = trim_alpha(tile)
        out_path = os.path.join(OUT_DIR, f'crop_{crop_id}_{stage}.png')
        tile.save(out_path)
        print(f'  wrote {out_path}  ({tile.size[0]}x{tile.size[1]})')

for fname, (top_id, bot_id) in SHEETS_4x2.items():
    src = Image.open(os.path.join(SRC_DIR, fname)).convert('RGBA')
    W, H = src.size
    cw = W // 4
    ch = H // 2
    for col in range(4):
        for row, crop_id in enumerate((top_id, bot_id)):
            stage = col + 1
            box = (col * cw, row * ch, (col + 1) * cw, (row + 1) * ch)
            tile = src.crop(box)
            tile = keep_largest_blob(tile)
            tile = trim_alpha(tile)
            out_path = os.path.join(OUT_DIR, f'crop_{crop_id}_{stage}.png')
            tile.save(out_path)
            print(f'  wrote {out_path}  ({tile.size[0]}x{tile.size[1]})')

print('Done.')
