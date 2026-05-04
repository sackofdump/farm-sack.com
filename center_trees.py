"""
Re-pad each tree_*.png so the trunk sits at the horizontal center of the
image. The shop preview uses object-fit: contain + center alignment, so
asymmetric trunks make the tree look like it's leaning out of the card.
We detect the trunk by the median X of opaque pixels in the bottom 20%
of the image, then pad the narrow side with transparent pixels.
"""
import os
import glob
from PIL import Image

OUT = 'C:/farmsack/assets/named'

def trunk_x(im, alpha_threshold=20):
    """Alpha-weighted horizontal centroid (center of mass) of the sprite.
    For asymmetric trees this balances the visible pixel mass instead of
    just the bbox edges, so a leaning canopy can't drag the trunk off to
    one side of the preview."""
    w, h = im.size
    a = im.split()[-1]
    px = a.load()
    total = 0.0
    sum_x = 0.0
    for y in range(h):
        for x in range(w):
            v = px[x, y]
            if v >= alpha_threshold:
                sum_x += x * v
                total += v
    if total == 0:
        return w // 2
    return int(round(sum_x / total))

def center_on_trunk(path):
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    tx = trunk_x(im)
    # Desired: trunk at exact image center. Pad narrower side.
    pad_left = max(0, (w - 2 * tx))
    pad_right = max(0, (2 * tx - w))
    if pad_left == 0 and pad_right == 0:
        return False
    new_w = w + pad_left + pad_right
    out = Image.new('RGBA', (new_w, h), (0, 0, 0, 0))
    out.paste(im, (pad_left, 0))
    out.save(path)
    return True

count = 0
for path in sorted(glob.glob(os.path.join(OUT, 'tree_*.png'))):
    if center_on_trunk(path):
        count += 1
        print('  centered', os.path.basename(path))
    else:
        print('  ok      ', os.path.basename(path))
print(f'Done. Re-centered {count} files.')
