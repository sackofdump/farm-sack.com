"""
Redo the tree sprites. The source 4-stage sheets aren't on a clean
1024/4 grid — bigger stages overflow their quarter, so split-by-quarter
followed by alpha-trim ends up grabbing pieces of two trees in the same
PNG.

This version walks the source's vertical alpha profile to find the column
gaps between trees, then splits at those gaps. Each piece is alpha-trimmed
and centered horizontally on its own canvas.
"""
import os
from PIL import Image
import numpy as np

SRC = 'C:/farmsack/NEW ASSETS/trees'
OUT = 'C:/farmsack/assets/named'

TREE_SRCS = {
    'Oak.png':         'oak',
    'Apple.png':       'apple',
    'Orange.png':      'orange',
    'Cherries.png':    'cherry',
    'Maple.png':       'maple',
    'Pine.png':        'pine_dark',
    'Golden_Pine.png': 'pine_yellow',
    'Snow_Pine.png':   'pine_snow',
    'Stump.png':       'stump',
}

ALPHA_THRESH = 20
PAD = 6  # transparent pixels around each tree

def find_tree_columns(im, min_gap=6):
    """Return [(x0, x1), ...] for each distinct tree. A "gap" is at least
    `min_gap` consecutive empty columns — without that buffer, two trees
    whose canopies barely-touch (or even share a single antialiased pixel
    between their bounding boxes) get glued together."""
    a = np.array(im.split()[-1])
    col_alpha = (a >= ALPHA_THRESH).any(axis=0)
    # Build a list of opaque column indices, then split into runs separated
    # by gaps wider than min_gap.
    runs = []
    in_run = False
    run_start = 0
    last_opaque = -10**9
    for x, on in enumerate(col_alpha):
        if on:
            if not in_run or (x - last_opaque) > min_gap:
                if in_run:
                    runs.append((run_start, last_opaque + 1))
                run_start = x
                in_run = True
            last_opaque = x
    if in_run:
        runs.append((run_start, last_opaque + 1))
    return runs

def square_pad_to_center(im, pad=PAD):
    """Trim alpha to bbox, then pad transparently so the visible content
    is symmetric around the horizontal center."""
    a = np.array(im.split()[-1])
    rows = (a >= ALPHA_THRESH).any(axis=1)
    cols = (a >= ALPHA_THRESH).any(axis=0)
    if not rows.any():
        return im
    y0, y1 = int(np.argmax(rows)), len(rows) - int(np.argmax(rows[::-1]))
    x0, x1 = int(np.argmax(cols)), len(cols) - int(np.argmax(cols[::-1]))
    cropped = im.crop((x0, y0, x1, y1))
    cw, ch = cropped.size
    new_w = cw + pad * 2
    new_h = ch + pad
    out = Image.new('RGBA', (new_w, new_h), (0, 0, 0, 0))
    out.paste(cropped, (pad, 0))
    return out

def redo_tree(src_name, out_id):
    path = os.path.join(SRC, src_name)
    if not os.path.exists(path):
        print(f'  MISSING: {src_name}')
        return
    sheet = Image.open(path).convert('RGBA')
    pieces = find_tree_columns(sheet)
    H = sheet.size[1]
    # Some sheets are a single sprite (e.g. Stump.png) — replicate it for
    # every "stage" so the placement code can still look up tree_<id>_<n>.
    if len(pieces) < 4:
        x0, x1 = pieces[0]
        only = square_pad_to_center(sheet.crop((x0, 0, x1, H)))
        for i in range(1, 5):
            only.save(os.path.join(OUT, f'tree_{out_id}_{i}.png'))
        only.save(os.path.join(OUT, f'tree_{out_id}.png'))
        print(f'  {src_name}: single sprite -> tree_{out_id}_1..4 (no growth)')
        return
    pieces = pieces[:4]
    for i, (x0, x1) in enumerate(pieces, start=1):
        slice_ = sheet.crop((x0, 0, x1, H))
        tile = square_pad_to_center(slice_)
        out_path = os.path.join(OUT, f'tree_{out_id}_{i}.png')
        tile.save(out_path)
        print(f'  {src_name}[stage {i}]  ->  tree_{out_id}_{i}.png  ({tile.size[0]}x{tile.size[1]})')
    x0, x1 = pieces[3]
    mature = square_pad_to_center(sheet.crop((x0, 0, x1, H)))
    mature.save(os.path.join(OUT, f'tree_{out_id}.png'))

for src, out_id in TREE_SRCS.items():
    redo_tree(src, out_id)

print('Done.')
