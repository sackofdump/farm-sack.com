"""
Procedural iso terrain tiles (96 x 48 iso diamond) for FarmSack.

Each tile is a clean diamond with no transparent gaps inside the shape — so
neighboring tiles stitch together with no white seams.  Natural feel comes
from per-tile noise, two-tone iso lighting (lighter upper half, darker lower
half), and small speckle/blade/pebble accents.
"""
import os
import random
from PIL import Image, ImageDraw

OUT = 'C:/farmsack/assets/named'
os.makedirs(OUT, exist_ok=True)

W, H = 96, 48
CX, CY = W / 2, H / 2

# --- diamond geometry helpers ---
DIAMOND_PTS = [(W // 2, 0), (W - 1, H // 2), (W // 2, H - 1), (0, H // 2)]
UPPER_PTS   = [(W // 2, 0), (W - 1, H // 2), (0, H // 2)]
LOWER_PTS   = [(W // 2, H - 1), (W - 1, H // 2), (0, H // 2)]

def in_diamond(x, y, margin=0.0):
    dx = abs(x - CX) / CX
    dy = abs(y - CY) / CY
    return dx + dy <= 1.0 - margin

def make_mask():
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon(DIAMOND_PTS, fill=255)
    return m

MASK = make_mask()

def base(color_lower, color_upper):
    """Build a fresh diamond filled with two-tone iso lighting."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon(DIAMOND_PTS, fill=color_lower + (255,))
    d.polygon(UPPER_PTS,   fill=color_upper + (255,))
    return img

def speckle(img, count, palette, sizes=(1,), blade=False, blade_chance=0.0,
            seed_offset=0):
    d = ImageDraw.Draw(img)
    px = img.load()
    for i in range(count):
        for _try in range(25):
            x = random.randint(2, W - 3)
            y = random.randint(2, H - 3)
            if in_diamond(x, y, margin=0.04):
                break
        else:
            continue
        c = random.choice(palette) + (255,)
        s = random.choice(sizes)
        if s == 1:
            px[x, y] = c
        else:
            d.ellipse([x - s // 2, y - s // 2, x + s // 2, y + s // 2], fill=c)
        if blade and random.random() < blade_chance:
            l = random.randint(1, 3)
            d.line([(x, y), (x, y - l)], fill=c)

def add_noise(img, n):
    px = img.load()
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            d = random.randint(-n, n)
            px[x, y] = (max(0, min(255, r + d)),
                        max(0, min(255, g + d)),
                        max(0, min(255, b + d)),
                        a)

def finish(img):
    img.putalpha(MASK)
    return img

# ============ TERRAINS ============

def make_grass():
    random.seed(101)
    img = base((92, 152, 60), (118, 178, 78))
    speckle(img, 130,
            [(80, 138, 50), (135, 200, 92), (96, 160, 64), (148, 208, 100),
             (75, 130, 48), (110, 175, 78)],
            sizes=(1, 1, 1, 2), blade=True, blade_chance=0.35)
    add_noise(img, 6)
    return finish(img)

def make_grass_flowers():
    random.seed(102)
    img = make_grass()
    d = ImageDraw.Draw(img)
    flowers = [(255, 250, 230), (255, 230, 130), (250, 215, 240), (200, 230, 255)]
    for _ in range(6):
        for _try in range(25):
            x = random.randint(8, W - 9)
            y = random.randint(8, H - 9)
            if in_diamond(x, y, margin=0.18):
                break
        c = random.choice(flowers) + (255,)
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=c)
        ImageDraw.Draw(img).point((x, y), fill=(220, 180, 80, 255))
    return img

def make_dirt(plowed=False, seed=13):
    random.seed(seed)
    if plowed:
        img = base((128, 78, 36), (156, 100, 50))
    else:
        img = base((146, 92, 44), (172, 114, 60))
    speckle(img, 60 if plowed else 25,
            [(105, 65, 30), (188, 130, 72), (92, 56, 24), (210, 158, 100),
             (140, 90, 44), (170, 115, 60)],
            sizes=(1, 1, 2, 2))
    if plowed:
        # A few subtle clumps so it reads as freshly-tilled (loose, varied)
        d = ImageDraw.Draw(img)
        for _ in range(8):
            for _try in range(20):
                x = random.randint(6, W - 7)
                y = random.randint(6, H - 7)
                if in_diamond(x, y, margin=0.12):
                    break
            d.ellipse([x - 2, y - 1, x + 2, y + 1],
                      fill=(180, 122, 66, 255), outline=(110, 70, 32, 255))
    add_noise(img, 9 if plowed else 7)
    return finish(img)

def make_water():
    random.seed(202)
    img = base((52, 130, 198), (78, 162, 224))
    d = ImageDraw.Draw(img)
    # ripple curves
    px = img.load()
    for offset in (-12, -4, 6, 14):
        for x in range(4, W - 4):
            y = int(CY + offset + 1.5 * (1 - abs(x - CX) / CX))
            if 1 <= y < H - 1 and in_diamond(x, y, margin=0.06):
                px[x, y] = (210, 235, 250, 255)
    speckle(img, 30,
            [(120, 195, 240), (180, 220, 248), (60, 142, 210)],
            sizes=(1, 1, 1))
    add_noise(img, 4)
    return finish(img)

def make_stone():
    random.seed(303)
    img = base((130, 130, 138), (162, 162, 170))
    # cobblestone irregular ovals
    d = ImageDraw.Draw(img)
    placed = []
    for _ in range(40):
        for _try in range(25):
            x = random.randint(4, W - 5)
            y = random.randint(4, H - 5)
            if not in_diamond(x, y, margin=0.06):
                continue
            if any((x - px) ** 2 + ((y - py) * 2) ** 2 < 28 for px, py in placed):
                continue
            placed.append((x, y))
            break
        else:
            continue
        rx = random.randint(3, 5)
        ry = random.randint(2, 3)
        shade = random.randint(-25, 20)
        c = (max(0, min(255, 150 + shade)),) * 3 + (255,)
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=c, outline=(95, 95, 100, 255))
    add_noise(img, 5)
    return finish(img)

def make_wood(dark=False):
    random.seed(404 if dark else 405)
    if dark:
        img = base((86, 56, 28), (110, 72, 38))
        plank_color = (130, 86, 44, 255)
        grain_color = (62, 38, 18, 255)
    else:
        img = base((150, 110, 60), (180, 138, 80))
        plank_color = (200, 158, 96, 255)
        grain_color = (120, 84, 38, 255)
    d = ImageDraw.Draw(img)
    # Iso plank lines: parallel along NW-SE direction
    px = img.load()
    for offset in (-16, -8, 0, 8, 16):
        for x in range(1, W - 1):
            y = int(CY + offset + (x - CX) * 0.5)
            if 1 <= y < H - 1 and in_diamond(x, y, margin=0.04):
                px[x, y] = grain_color
    # subtle grain noise lines
    speckle(img, 50, [plank_color[:3], grain_color[:3]], sizes=(1,))
    add_noise(img, 5)
    return finish(img)

# ============ SAVE ============
TILES = {
    'terrain_grass':         make_grass(),
    'terrain_grass_flowers': make_grass_flowers(),
    'terrain_dirt1':         make_dirt(plowed=True),
    'terrain_dirt2':         make_dirt(plowed=False),
    'terrain_water':         make_water(),
    'terrain_stone':         make_stone(),
    'terrain_wood_dark':     make_wood(dark=True),
    'terrain_wood_light':    make_wood(dark=False),
}

for name, img in TILES.items():
    img.save(os.path.join(OUT, f'{name}.png'))
    print(f'  wrote {name}.png  ({img.size[0]}x{img.size[1]})')

print('Done.')
