"""
Convert the new high-res seamless ground textures in NEW ASSETS/ to iso
diamond terrain tiles (96x48) for FarmSack.

  grass_tile.png       -> terrain_grass.png
  dirt_tile.png        -> terrain_dirt2.png  (untilled dirt)
  tilleddirt_tile.png  -> terrain_dirt1.png  (plowed soil)
"""
import os
from PIL import Image, ImageDraw

SRC_DIR = 'C:/farmsack/NEW ASSETS/tiles'
OUT     = 'C:/farmsack/assets/named'
W, H    = 96, 48

DIAMOND_PTS = [(W // 2, 0), (W - 1, H // 2), (W // 2, H - 1), (0, H // 2)]

def make_mask():
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon(DIAMOND_PTS, fill=255)
    return m

MASK = make_mask()

def make_tile(src_name, out_name, rotate_deg=0):
    src = Image.open(os.path.join(SRC_DIR, src_name)).convert('RGBA')
    if rotate_deg:
        # Rotate so furrows align with iso NW-SE direction. After rotation,
        # the source has a transparent border in the corners, so we crop a
        # smaller region from the center to stay inside the rotated content.
        src = src.rotate(rotate_deg, resample=Image.BICUBIC, expand=False)
    sw, sh = src.size
    # Center-crop a region with the iso aspect ratio (2:1 wide), then scale.
    # After a 45-degree rotation the safe central region is ~70% of original.
    safe = 0.65 if rotate_deg else 1.0
    crop_w = int(sw * safe / 2) * 2
    crop_h = crop_w // 2
    x0 = (sw - crop_w) // 2
    y0 = (sh - crop_h) // 2
    patch = src.crop((x0, y0, x0 + crop_w, y0 + crop_h))
    tile = patch.resize((W, H), Image.LANCZOS)
    tile.putalpha(MASK)
    tile.save(os.path.join(OUT, out_name))
    print(f'  {src_name}  ->  {out_name}')

make_tile('grass_tile.png',       'terrain_grass.png')
make_tile('dirt_tile.png',        'terrain_dirt2.png')
# Rotate tilled dirt 45 deg so the diagonal furrows in the source align with
# the iso NW-SE direction (furrows look properly plowed, not striped).
make_tile('tilleddirt_tile.png',  'terrain_dirt1.png', rotate_deg=45)
make_tile('stone_tile.png',       'terrain_stone.png')
print('Done.')
