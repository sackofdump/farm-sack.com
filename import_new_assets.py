"""
Import buildings, animals, and UI icons from NEW ASSETS/ into assets/named/
under the filenames index.html already references. Each PNG is alpha-trimmed
with a small pad so the rendered sprite has no extra invisible border.
"""
import os
from PIL import Image

SRC = 'C:/farmsack/NEW ASSETS'
OUT = 'C:/farmsack/assets/named'

def trim(im, pad=2, alpha_threshold=10):
    a = im.split()[-1]
    mask = a.point(lambda v: 255 if v >= alpha_threshold else 0)
    bb = mask.getbbox()
    if not bb:
        return im
    x0, y0, x1, y1 = bb
    x0 = max(0, x0 - pad); y0 = max(0, y0 - pad)
    x1 = min(im.size[0], x1 + pad); y1 = min(im.size[1], y1 + pad)
    return im.crop((x0, y0, x1, y1))

def copy_trim(src_rel, out_name):
    src = os.path.join(SRC, src_rel)
    if not os.path.exists(src):
        print(f'  MISSING: {src_rel}')
        return
    im = Image.open(src).convert('RGBA')
    im = trim(im)
    im.save(os.path.join(OUT, out_name))
    print(f'  {src_rel}  ->  {out_name}  ({im.size[0]}x{im.size[1]})')

# --- buildings ---
# game asset ids: building_house, building_barn, building_market_stall, building_windmill
# also bring in silo as building_silo for future use
copy_trim('buildings/farmhouse_trans.png',   'building_house.png')
copy_trim('buildings/barn_trans.png',        'building_barn.png')
copy_trim('buildings/marketstand_trans.png', 'building_market_stall.png')
copy_trim('buildings/windmill_trans.png',    'building_windmill.png')
copy_trim('buildings/silo_trans.png',        'building_silo.png')
copy_trim('buildings/Staff_trans.png',       'building_staff.png')

# --- animals ---
for name in ('chicken','duck','dog','pig','sheep','goat','cow','horse'):
    copy_trim(f'animals/{name}_trans.png', f'animal_{name}.png')
copy_trim('animals/coyote.png', 'animal_coyote.png')

# --- UI tools (toolbar action icons) ---
copy_trim('ui/auto.png',    'ui_auto.png')
copy_trim('ui/Clear.png',   'ui_clear.png')
copy_trim('ui/select.png',  'ui_select.png')
copy_trim('ui/Move.png',    'ui_move.png')
copy_trim('ui/plow.png',    'ui_plow.png')
copy_trim('ui/plant.png',   'ui_plant.png')
copy_trim('ui/water.png',   'ui_water.png')
copy_trim('ui/harvest.png', 'ui_harvest.png')
copy_trim('ui/sell.png',    'ui_sell.png')
copy_trim('ui/build.png',   'ui_build.png')

# --- UI buttons ---
copy_trim('ui/buy.png',           'ui_buy.png')
copy_trim('ui/sell.png',          'ui_sellbtn.png')
copy_trim('ui/upgrade.png',       'ui_upgrade.png')
copy_trim('ui/closeX.png',        'ui_close.png')
copy_trim('ui/settings_gear.png', 'ui_settings.png')
copy_trim('ui/market.png',        'ui_shop.png')

# --- trees ---
# Source sheets are 4 growth stages laid out horizontally. We split each into
# tree_<id>_1..4.png so the game can grow them like crops. The mature stage
# is also saved as tree_<id>.png for static placement / shop preview.
def split_tree_stages(src_rel, out_id, stages=4):
    src = os.path.join(SRC, src_rel)
    if not os.path.exists(src):
        print(f'  MISSING: {src_rel}')
        return
    im = Image.open(src).convert('RGBA')
    W, H = im.size
    cw = W // stages
    for i in range(stages):
        box = (i * cw, 0, (i + 1) * cw, H)
        tile = trim(im.crop(box))
        tile.save(os.path.join(OUT, f'tree_{out_id}_{i + 1}.png'))
        print(f'  {src_rel}[stage {i+1}]  ->  tree_{out_id}_{i+1}.png  ({tile.size[0]}x{tile.size[1]})')
    # Mature alias
    mature = trim(im.crop(((stages - 1) * cw, 0, W, H)))
    mature.save(os.path.join(OUT, f'tree_{out_id}.png'))

split_tree_stages('trees/Oak.png',         'oak')
split_tree_stages('trees/Apple.png',       'apple')
split_tree_stages('trees/Orange.png',      'orange')
split_tree_stages('trees/Cherries.png',    'cherry')
split_tree_stages('trees/Pine.png',        'pine_dark')
split_tree_stages('trees/Golden_Pine.png', 'pine_yellow')
split_tree_stages('trees/Snow_Pine.png',   'pine_snow')
# Stump sheet may be 4 stumps (stages of decay) — split same way; the game
# treats stump as a single sprite.
split_tree_stages('trees/Stump.png',       'stump')

# --- decor ---
copy_trim('decor/bush.png',            'decor_bush.png')
copy_trim('decor/daisies.png',         'decor_daisies.png')
copy_trim('decor/bluebells.png',       'decor_bluebells.png')
copy_trim('decor/potted_plant.png',    'decor_potted_plant.png')
copy_trim('decor/sunflower_plant.png', 'decor_sunflower.png')
copy_trim('decor/log.png',             'decor_log.png')
copy_trim('decor/signpost.png',        'decor_signpost.png')
copy_trim('decor/mailbox.png',         'decor_mailbox.png')
copy_trim('decor/barrel.png',          'decor_barrel.png')
copy_trim('decor/crate.png',           'decor_crate.png')
copy_trim('decor/lamp_post.png',       'decor_lamppost.png')
copy_trim('decor/well.png',            'decor_well.png')

# --- HUD currency icons (game uses bottom_01/02 names) ---
copy_trim('ui/coin.png', 'bottom_01.png')
copy_trim('ui/cash.png', 'bottom_02.png')
# Also save cash as a tool icon for the toolbar's Sell button.
copy_trim('ui/cash.png', 'ui_cash.png')

# --- XP / energy bars (saved with descriptive names; integration TBD) ---
copy_trim('ui/xpbar.png',     'ui_xpbar.png')
copy_trim('ui/energybar.png', 'ui_energybar.png')

print('Done.')
