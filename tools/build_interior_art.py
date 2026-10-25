"""Generates 4x-density pixel art interior textures and furniture props for
house interiors in Wrackmouth (Mayor's Hall, Kell's Forge, The Salt Gull Inn,
Lantern Watch Tower, Cottages, and Trader Shop).
"""

from __future__ import annotations

import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent

# Universal dark-fantasy pixel art palette
OUTLINE = (20, 16, 22, 255)
SHADOW = (16, 14, 20, 140)

# Wood tones: deep aged oak, spruce, and walnut
WOOD_DEEP = (34, 22, 14, 255)
WOOD_DARK = (52, 36, 24, 255)
WOOD_MID = (78, 56, 38, 255)
WOOD_LIGHT = (112, 82, 54, 255)
WOOD_HI = (142, 108, 72, 255)

# Iron & steel tones
IRON_DEEP = (24, 26, 32, 255)
IRON_DARK = (46, 50, 58, 255)
IRON_MID = (76, 82, 94, 255)
IRON_LIGHT = (130, 140, 154, 255)
IRON_HI = (190, 200, 215, 255)

# Brass & gold
BRASS_DARK = (130, 96, 36, 255)
BRASS_MID = (185, 145, 55, 255)
BRASS_HI = (235, 195, 95, 255)

# Cloth & linen
LINEN_DARK = (160, 150, 130, 255)
LINEN_MID = (205, 196, 174, 255)
LINEN_LIGHT = (238, 232, 214, 255)

# Nordic Pine Green (Quilt)
PINE_DEEP = (20, 36, 28, 255)
PINE_DARK = (34, 58, 44, 255)
PINE_MID = (52, 84, 64, 255)
PINE_LIGHT = (76, 114, 88, 255)
PINE_HI = (104, 146, 116, 255)

# Crimson Velvet & Madder
CRIMSON_DEEP = (48, 16, 20, 255)
CRIMSON_DARK = (88, 24, 28, 255)
CRIMSON_MID = (138, 38, 42, 255)
CRIMSON_LIGHT = (184, 58, 62, 255)
CRIMSON_HI = (220, 88, 88, 255)

# Stone tones
STONE_DEEP = (32, 34, 38, 255)
STONE_DARK = (52, 56, 64, 255)
STONE_MID = (74, 80, 90, 255)
STONE_LIGHT = (106, 114, 126, 255)
STONE_HI = (148, 156, 170, 255)


def _canvas(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _shadow(d: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int) -> None:
    d.ellipse([x0, y0, x1, y1], fill=SHADOW)


def _box(
    d: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    mid,
    light=None,
    dark=None,
    outline=OUTLINE,
) -> None:
    """A shaded pixel art box: dark outline, body, light top/left edges, dark bottom/right."""
    d.rectangle([x0, y0, x1, y1], fill=outline)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=mid)
    if light:
        d.line([(x0 + 1, y0 + 1), (x1 - 2, y0 + 1)], fill=light)
        d.line([(x0 + 1, y0 + 1), (x0 + 1, y1 - 2)], fill=light)
    if dark:
        d.line([(x0 + 1, y1 - 1), (x1 - 1, y1 - 1)], fill=dark)
        d.line([(x1 - 1, y0 + 1), (x1 - 1, y1 - 1)], fill=dark)


def build_interior_art() -> None:
    int_dir = ROOT / "assets" / "interiors"
    furn_dir = int_dir / "furniture"
    furn_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261024)

    # =========================================================================
    # 1. Seamless Wood Plank Floor (128x128, 8 planks x 16px)
    # =========================================================================
    sz = 128
    arr = np.zeros((sz, sz, 4), dtype=np.float32)
    plank_h = 16
    num_planks = sz // plank_h

    base_colors = [
        (96.0, 74.0, 54.0),
        (88.0, 68.0, 48.0),
        (102.0, 78.0, 58.0),
        (84.0, 64.0, 46.0),
        (94.0, 72.0, 52.0),
        (90.0, 70.0, 50.0),
        (98.0, 76.0, 56.0),
        (86.0, 66.0, 47.0),
    ]

    for p_i in range(num_planks):
        y0 = p_i * plank_h
        y1 = y0 + plank_h
        br, bg, bb = base_colors[p_i]

        for y in range(y0, y1):
            factor = 1.05 - 0.10 * ((y - y0) / plank_h)
            for x in range(sz):
                noise = float(rng.integers(-3, 4))
                arr[y, x, 0] = br * factor + noise
                arr[y, x, 1] = bg * factor + noise * 0.8
                arr[y, x, 2] = bb * factor + noise * 0.6
                arr[y, x, 3] = 255.0

        for g_row in [y0 + 4, y0 + 9, y0 + 13]:
            g_shift = float(rng.integers(-5, 6))
            for x in range(sz):
                g_noise = float(rng.integers(-2, 3))
                arr[g_row, x, 0] += g_shift + g_noise
                arr[g_row, x, 1] += (g_shift + g_noise) * 0.8
                arr[g_row, x, 2] += (g_shift + g_noise) * 0.6

        for x in range(sz):
            arr[y0, x, 0] += 16.0
            arr[y0, x, 1] += 13.0
            arr[y0, x, 2] += 10.0

        for x in range(sz):
            arr[y1 - 1, x, 0] -= 28.0
            arr[y1 - 1, x, 1] -= 24.0
            arr[y1 - 1, x, 2] -= 20.0

        j_x = (p_i * 47 + 23) % sz
        for y in range(y0, y1 - 1):
            arr[y, j_x, 0] -= 26.0
            arr[y, j_x, 1] -= 22.0
            arr[y, j_x, 2] -= 18.0

        for nx in [j_x - 3, j_x + 3]:
            nx = nx % sz
            arr[y0 + 3, nx] = [46.0, 42.0, 48.0, 255.0]
            arr[y1 - 4, nx] = [46.0, 42.0, 48.0, 255.0]

    floor_wood = Image.fromarray(np.clip(arr, 0.0, 255.0).astype(np.uint8), "RGBA")
    floor_wood.save(int_dir / "floor_wood.png")

    # =========================================================================
    # 2. Seamless Flagstone Floor (128x128)
    # =========================================================================
    st_sz = 128
    floor_stone = Image.new("RGBA", (st_sz, st_sz), (34, 34, 38, 255))
    d_stone = ImageDraw.Draw(floor_stone)
    grid_w, grid_h = 32, 16
    for r_i in range(st_sz // grid_h):
        y0 = r_i * grid_h
        y1 = y0 + grid_h
        x_offset = (r_i % 2) * (grid_w // 2)
        for c_i in range(-1, (st_sz // grid_w) + 2):
            x0 = c_i * grid_w + x_offset
            x1 = x0 + grid_w
            s_val = int(rng.integers(64, 82))
            s_r = s_val
            s_g = int(s_val * 1.04)
            s_b = int(s_val * 1.10)
            d_stone.rectangle(
                [x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=(s_r, s_g, s_b, 255)
            )
            d_stone.line(
                [(x0 + 2, y0 + 2), (x1 - 2, y0 + 2)],
                fill=(s_r + 18, s_g + 18, s_b + 20, 255),
            )
            d_stone.line(
                [(x0 + 2, y0 + 2), (x0 + 2, y1 - 2)],
                fill=(s_r + 14, s_g + 14, s_b + 16, 255),
            )
            d_stone.line(
                [(x0 + 2, y1 - 1), (x1 - 1, y1 - 1)],
                fill=(s_r - 20, s_g - 20, s_b - 18, 255),
            )
    floor_stone.save(int_dir / "floor_stone.png")

    # =========================================================================
    # 3. Timber Wall Header & Beam (512x96)
    # =========================================================================
    wall_timber = Image.new("RGBA", (512, 96), (46, 36, 28, 255))
    d_wt = ImageDraw.Draw(wall_timber)
    d_wt.rectangle([0, 0, 512, 24], fill=(36, 26, 18, 255))
    d_wt.line([(0, 24), (512, 24)], fill=(20, 14, 10, 255))
    d_wt.line([(0, 25), (512, 25)], fill=(60, 48, 36, 255))
    for px in range(0, 512, 64):
        d_wt.rectangle([px, 24, px + 12, 96], fill=(40, 30, 22, 255))
        d_wt.line([(px, 24), (px, 96)], fill=(56, 44, 32, 255))
        d_wt.line([(px + 12, 24), (px + 12, 96)], fill=(24, 18, 12, 255))
    d_wt.rectangle([0, 84, 512, 96], fill=(32, 24, 18, 255))
    d_wt.line([(0, 84), (512, 84)], fill=(62, 50, 38, 255))
    wall_timber.save(int_dir / "wall_timber.png")

    # =========================================================================
    # 4. Stone Wall Header & Ashlar Blocks (512x96)
    # =========================================================================
    wall_stone = Image.new("RGBA", (512, 96), (36, 38, 44, 255))
    d_ws = ImageDraw.Draw(wall_stone)
    d_ws.rectangle([0, 0, 512, 20], fill=(32, 24, 18, 255))
    d_ws.line([(0, 20), (512, 20)], fill=(18, 14, 10, 255))
    for row_y in range(20, 84, 22):
        d_ws.line([(0, row_y), (512, row_y)], fill=(22, 24, 28, 255))
        d_ws.line([(0, row_y + 1), (512, row_y + 1)], fill=(75, 82, 92, 255))
        x_stagger = (row_y // 22 % 2) * 44
        for bx in range(-44, 512, 88):
            d_ws.line(
                [(bx + x_stagger, row_y), (bx + x_stagger, row_y + 22)],
                fill=(22, 24, 28, 255),
            )
    d_ws.rectangle([0, 84, 512, 96], fill=(28, 30, 34, 255))
    wall_stone.save(int_dir / "wall_stone.png")

    # =========================================================================
    # 5. Upgraded Timber Bedstead with Quilt (88x104) — Noble/Adult Bed
    # =========================================================================
    bed_im, d_bed = _canvas(88, 104)
    # Ambient shadow beneath bed
    _shadow(d_bed, 6, 82, 82, 102)

    # 1. Four heavy corner posts with turned finials
    # Back headboard posts
    _box(d_bed, 8, 4, 16, 52, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    _box(d_bed, 72, 4, 80, 52, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    # Headboard carved finials
    d_bed.ellipse([7, 1, 17, 9], fill=OUTLINE)
    d_bed.ellipse([8, 2, 16, 8], fill=WOOD_HI)
    d_bed.ellipse([71, 1, 81, 9], fill=OUTLINE)
    d_bed.ellipse([72, 2, 80, 8], fill=WOOD_HI)

    # 2. Carved Oak Headboard panel
    _box(d_bed, 14, 8, 74, 38, WOOD_MID, WOOD_LIGHT, WOOD_DEEP)
    # Nordic carved arch motif in headboard
    d_bed.arc([22, 12, 66, 36], 180, 360, fill=WOOD_DEEP, width=2)
    d_bed.line([(44, 12), (44, 36)], fill=WOOD_DEEP, width=2)
    d_bed.line([(32, 22), (56, 22)], fill=WOOD_LIGHT, width=1)

    # 3. Side Rails & Mattress Foundation
    _box(d_bed, 12, 32, 76, 90, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    d_bed.rectangle([14, 34, 74, 88], fill=WOOD_DEEP)

    # 4. Fluffy down pillow at head of bed
    _box(d_bed, 20, 24, 68, 40, LINEN_MID, LINEN_LIGHT, LINEN_DARK)
    # Pillow center depression indent
    d_bed.ellipse([34, 28, 54, 36], fill=LINEN_DARK)
    d_bed.ellipse([36, 29, 52, 34], fill=LINEN_MID)

    # 5. Turn-down folded linen sheet
    _box(d_bed, 15, 38, 73, 46, LINEN_LIGHT, (255, 252, 240, 255), LINEN_DARK)
    d_bed.line([(15, 46), (73, 46)], fill=OUTLINE)

    # 6. Nordic pine-green wool quilt with diamond quilting stitches
    _box(d_bed, 14, 46, 74, 88, PINE_MID, PINE_LIGHT, PINE_DARK)
    # Layered quilted diamond grid
    for qx in range(18, 72, 10):
        for qy in range(50, 84, 8):
            d_bed.point([(qx, qy)], fill=PINE_HI)
            d_bed.line([(qx - 4, qy), (qx, qy - 4)], fill=PINE_DARK)
            d_bed.line([(qx, qy - 4), (qx + 4, qy)], fill=PINE_LIGHT)
            d_bed.line([(qx + 4, qy), (qx, qy + 4)], fill=PINE_DEEP)
            d_bed.line([(qx, qy + 4), (qx - 4, qy)], fill=PINE_DARK)
    # Quilt drape shadow folds on sides
    d_bed.line([(15, 47), (15, 87)], fill=PINE_DEEP, width=1)
    d_bed.line([(73, 47), (73, 87)], fill=PINE_DEEP, width=1)

    # 7. Footboard & front posts
    _box(d_bed, 8, 78, 16, 96, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    _box(d_bed, 72, 78, 80, 96, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    d_bed.ellipse([7, 75, 17, 82], fill=WOOD_HI)
    d_bed.ellipse([71, 75, 81, 82], fill=WOOD_HI)
    _box(d_bed, 14, 84, 74, 94, WOOD_MID, WOOD_LIGHT, WOOD_DEEP)
    bed_im.save(furn_dir / "bed_wood.png")

    # =========================================================================
    # 6. Inn / Noble Bedstead with Fur Throw (88x104) — The Salt Gull Bed
    # =========================================================================
    inn_im, d_inn = _canvas(88, 104)
    _shadow(d_inn, 6, 82, 82, 102)

    # Posts & carved headboard
    _box(d_inn, 8, 4, 16, 52, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    _box(d_inn, 72, 4, 80, 52, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    d_inn.ellipse([7, 1, 17, 9], fill=BRASS_MID)
    d_inn.ellipse([71, 1, 81, 9], fill=BRASS_MID)
    _box(d_inn, 14, 8, 74, 38, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    # Brass studs along headboard
    for bx in range(20, 70, 8):
        d_inn.point([(bx, 14)], fill=BRASS_HI)

    # Base mattress & pillows
    _box(d_inn, 12, 32, 76, 90, WOOD_DEEP, WOOD_DARK, (16, 12, 10, 255))
    _box(d_inn, 18, 22, 42, 38, LINEN_MID, LINEN_LIGHT, LINEN_DARK)
    _box(d_inn, 46, 22, 70, 38, LINEN_MID, LINEN_LIGHT, LINEN_DARK)

    # Crimson velvet quilt with gold border
    _box(d_inn, 14, 38, 74, 88, CRIMSON_MID, CRIMSON_LIGHT, CRIMSON_DEEP)
    d_inn.rectangle([18, 42, 70, 84], outline=BRASS_MID)

    # Thick layered wolf/bear fur pelt draped across the lower half
    d_inn.ellipse([14, 58, 74, 86], fill=(54, 42, 32, 255))
    d_inn.ellipse([16, 60, 72, 84], fill=(136, 106, 76, 255))
    for k in range(80):
        fx = 18 + (k * 29) % 52
        fy = 62 + (k * 43) % 20
        d_inn.line([(fx, fy), (fx + 2, fy + 2)], fill=(182, 150, 112, 255))
        d_inn.line([(fx, fy), (fx - 1, fy + 2)], fill=(96, 72, 48, 255))

    # Front footboard
    _box(d_inn, 8, 78, 16, 96, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    _box(d_inn, 72, 78, 80, 96, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    d_inn.ellipse([7, 75, 17, 82], fill=BRASS_MID)
    d_inn.ellipse([71, 75, 81, 82], fill=BRASS_MID)
    _box(d_inn, 14, 84, 74, 94, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    inn_im.save(furn_dir / "bed_inn.png")

    # =========================================================================
    # 7. Cozy Rustic Cottage Cot (64x84) — Fisher & Weaver Cottages
    # =========================================================================
    cot_im, d_cot = _canvas(64, 84)
    _shadow(d_cot, 4, 68, 60, 82)

    # Rough-hewn wooden poles
    _box(d_cot, 6, 8, 12, 54, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    _box(d_cot, 52, 8, 58, 54, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    _box(d_cot, 10, 12, 54, 28, WOOD_DARK, WOOD_MID, WOOD_DEEP)

    # Straw mattress ticking peeking out
    d_cot.rectangle([10, 24, 54, 72], fill=(168, 142, 86, 255))
    for sx in range(12, 52, 4):
        d_cot.line([(sx, 26), (sx + 2, 70)], fill=(196, 172, 110, 255))

    # Burlap linen pillow
    _box(d_cot, 14, 18, 50, 32, LINEN_MID, LINEN_LIGHT, LINEN_DARK)

    # Patchwork rustic quilt (warm rustic earth tones & visible stitches)
    _box(d_cot, 10, 32, 54, 72, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    patches = [
        ((12, 34, 26, 46), (148, 62, 48, 255)),   # madder red
        ((26, 34, 40, 46), (62, 88, 118, 255)),   # indigo wool
        ((40, 34, 52, 46), (170, 134, 66, 255)),  # mustard
        ((12, 46, 26, 58), (56, 88, 66, 255)),    # forest green
        ((26, 46, 40, 58), (142, 108, 76, 255)),  # coarse wool
        ((40, 46, 52, 58), (138, 52, 44, 255)),   # rustic red
        ((12, 58, 26, 70), (74, 98, 124, 255)),   # slate blue
        ((26, 58, 40, 70), (160, 126, 58, 255)),  # gold ochre
        ((40, 58, 52, 70), (48, 78, 58, 255)),    # dark green
    ]
    for (px0, py0, px1, py1), col in patches:
        d_cot.rectangle([px0, py0, px1, py1], fill=col)
        # White thread cross-stitches around patch seams
        d_cot.point([(px0 + 2, py0 + 2), (px1 - 2, py0 + 2), (px0 + 2, py1 - 2), (px1 - 2, py1 - 2)], fill=(225, 220, 205, 255))

    # Front cot frame
    _box(d_cot, 6, 68, 12, 78, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    _box(d_cot, 52, 68, 58, 78, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    _box(d_cot, 10, 70, 54, 76, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    cot_im.save(furn_dir / "bed_kid.png")

    # =========================================================================
    # 8. Brand-New Wall Torch Sconce (24x44) & Animated Flame Sheet (96x32)
    # =========================================================================
    torch_im, d_tor = _canvas(24, 44)
    # Wrought iron diamond backplate fixed to the wall
    d_tor.polygon([(12, 12), (18, 22), (12, 32), (6, 22)], fill=OUTLINE)
    d_tor.polygon([(12, 14), (16, 22), (12, 30), (8, 22)], fill=IRON_MID)
    d_tor.point([(12, 16), (12, 28)], fill=IRON_HI)
    # Curved forged iron sconce arm extending outward
    d_tor.arc([8, 18, 16, 32], 0, 180, fill=IRON_DARK, width=2)
    d_tor.line([(12, 24), (12, 36)], fill=IRON_MID, width=2)
    # Iron torch collar / ring
    _box(d_tor, 7, 20, 17, 26, IRON_MID, IRON_LIGHT, IRON_DARK)
    # Wooden torch shaft
    d_tor.rectangle([10, 12, 14, 38], fill=WOOD_MID)
    d_tor.line([(10, 12), (10, 38)], fill=WOOD_LIGHT)
    d_tor.line([(14, 12), (14, 38)], fill=WOOD_DARK)
    # Bound blackened pitch cloth head
    d_tor.rectangle([8, 6, 16, 14], fill=(30, 26, 24, 255))
    d_tor.rectangle([9, 7, 15, 13], fill=(54, 44, 36, 255))
    # Wire wrappings
    d_tor.line([(8, 8), (16, 8)], fill=IRON_LIGHT)
    d_tor.line([(8, 11), (16, 11)], fill=IRON_LIGHT)
    # Charred glowing ember tip
    d_tor.point([(11, 6), (12, 5), (13, 6)], fill=(255, 140, 40, 255))
    torch_im.save(furn_dir / "torch_wall.png")

    # 4-frame animated torch flame sheet (96x32 = 4 frames of 24x32)
    flame_sheet = Image.new("RGBA", (24 * 4, 32), (0, 0, 0, 0))
    for f_i in range(4):
        f_im, d_fl = _canvas(24, 32)
        cx = 12
        bot_y = 28
        sway = [-2, 1, 2, -1][f_i]
        fl_h = [18, 22, 19, 21][f_i]

        # Outer crimson fire tongue
        d_fl.polygon(
            [
                (cx - 5, bot_y),
                (cx - 4 + sway, bot_y - fl_h // 2),
                (cx + sway, bot_y - fl_h),
                (cx + 4 + sway, bot_y - fl_h // 2),
                (cx + 5, bot_y),
            ],
            fill=(220, 54, 18, 255),
        )
        # Bright vibrant orange fire core
        d_fl.polygon(
            [
                (cx - 3, bot_y),
                (cx - 2 + sway, bot_y - fl_h // 2 + 2),
                (cx + sway, bot_y - fl_h + 4),
                (cx + 2 + sway, bot_y - fl_h // 2 + 2),
                (cx + 3, bot_y),
            ],
            fill=(255, 148, 28, 255),
        )
        # White-hot inner flame center
        d_fl.ellipse(
            [cx - 2, bot_y - 10, cx + 2, bot_y - 2], fill=(255, 246, 175, 255)
        )
        # Flying ember sparks
        spark_y = bot_y - fl_h - ((f_i * 3) % 5)
        d_fl.point([(cx + sway * 2, spark_y)], fill=(255, 220, 100, 255))

        flame_sheet.alpha_composite(f_im, (f_i * 24, 0))
    flame_sheet.save(furn_dir / "torch_flame_sheet.png")

    # Torch radial glow (128x128 soft additive amber)
    _glow(furn_dir / "torch_glow.png", 128, 0.85, (255, 160, 60))

    # =========================================================================
    # 9. Upgraded Cast Iron Candle Stand (20x44)
    # =========================================================================
    cnd_im, d_cnd = _canvas(20, 44)
    _shadow(d_cnd, 2, 38, 18, 43)
    # Tripod scrollwork feet
    d_cnd.line([(4, 40), (10, 36)], fill=IRON_DARK, width=2)
    d_cnd.line([(16, 40), (10, 36)], fill=IRON_DARK, width=2)
    d_cnd.line([(10, 41), (10, 36)], fill=IRON_DARK, width=2)
    # Turned iron central column
    d_cnd.rectangle([9, 16, 11, 36], fill=IRON_MID)
    d_cnd.line([(9, 16), (9, 36)], fill=IRON_LIGHT)
    d_cnd.line([(11, 16), (11, 36)], fill=IRON_DARK)
    # Iron drip pan saucer
    d_cnd.rectangle([5, 16, 15, 19], fill=IRON_DARK)
    d_cnd.line([(5, 16), (15, 16)], fill=IRON_LIGHT)
    # Melted wax pooling on saucer
    d_cnd.rectangle([6, 15, 14, 17], fill=LINEN_MID)
    # Tallow candle cylinder
    d_cnd.rectangle([7, 8, 13, 16], fill=LINEN_LIGHT)
    d_cnd.line([(7, 8), (7, 16)], fill=(255, 255, 250, 255))
    d_cnd.line([(13, 8), (13, 16)], fill=LINEN_DARK)
    # Wax drip running down side
    d_cnd.line([(11, 10), (11, 17)], fill=(255, 252, 240, 255))
    # Charred wick & bright golden teardrop flame
    d_cnd.line([(10, 5), (10, 8)], fill=(32, 24, 20, 255))
    d_cnd.polygon([(10, 1), (12, 5), (10, 6), (8, 5)], fill=(255, 195, 60, 255))
    d_cnd.point([(10, 4)], fill=(255, 250, 180, 255))
    cnd_im.save(furn_dir / "candle_stand.png")

    # =========================================================================
    # 10. Upgraded Fireplace Hearth (96x88)
    # =========================================================================
    h_im, d_h = _canvas(96, 88)
    _shadow(d_h, 8, 74, 88, 86)
    # Masonry chimney stack
    _box(d_h, 12, 4, 84, 80, STONE_MID, STONE_LIGHT, STONE_DARK)
    # Individual stacked stone courses
    courses = [14, 26, 38, 50, 62, 74]
    for cy in courses:
        d_h.line([(14, cy), (82, cy)], fill=STONE_DEEP, width=1)
        d_h.line([(14, cy + 1), (82, cy + 1)], fill=STONE_LIGHT, width=1)
        stagger = 16 if (cy // 12) % 2 == 0 else 32
        for sx in range(14 + stagger, 80, 28):
            d_h.line([(sx, cy - 11), (sx, cy)], fill=STONE_DEEP, width=1)
            d_h.point([(sx + 1, cy - 10)], fill=STONE_LIGHT)

    # Heavy dark oak mantel shelf
    _box(d_h, 8, 20, 88, 28, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    # Brass candlestick on mantel shelf
    d_h.rectangle([20, 13, 24, 20], fill=BRASS_MID)
    d_h.point([(22, 11)], fill=(255, 220, 100, 255))

    # Deep arched firebox with soot-blackened interior
    d_h.rectangle([24, 34, 72, 78], fill=(16, 14, 16, 255))
    d_h.arc([24, 22, 72, 46], 180, 360, fill=STONE_DEEP, width=3)

    # Cast-iron andirons & firewood logs in ash bed
    d_h.rectangle([30, 68, 66, 75], fill=(58, 42, 28, 255))
    d_h.rectangle([32, 70, 64, 77], fill=(42, 28, 18, 255))
    d_h.ellipse([32, 72, 64, 78], fill=(24, 18, 16, 255))
    # Iron grate bars
    for gx in (32, 40, 48, 56, 64):
        d_h.line([(gx, 64), (gx, 78)], fill=IRON_DARK, width=2)
        d_h.line([(gx, 64), (gx, 70)], fill=IRON_LIGHT, width=1)
    # Leaning iron poker against hearth wall
    d_h.line([(80, 22), (86, 76)], fill=IRON_MID, width=2)
    d_h.point([(80, 22)], fill=BRASS_HI)
    h_im.save(furn_dir / "hearth.png")

    # =========================================================================
    # 11. Upgraded Solid Oak Table (112x64) & Table with Feast (112x64)
    # =========================================================================
    tab_im, d_tab = _canvas(112, 64)
    _shadow(d_tab, 8, 48, 104, 62)
    # Sturdy chamfered legs
    for lx in (18, 88):
        _box(d_tab, lx, 24, lx + 8, 54, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    # Trestle cross-stretcher beam with wedge key
    _box(d_tab, 22, 42, 90, 47, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    d_tab.rectangle([16, 40, 20, 49], fill=WOOD_DEEP)
    d_tab.rectangle([92, 40, 96, 49], fill=WOOD_DEEP)
    # Tabletop with thick edge bevels and wood planks
    _box(d_tab, 10, 12, 102, 26, WOOD_MID, WOOD_LIGHT, WOOD_DEEP)
    # Plank grooves across table
    d_tab.line([(12, 16), (100, 16)], fill=WOOD_DEEP)
    d_tab.line([(12, 21), (100, 21)], fill=WOOD_DEEP)
    d_tab.line([(12, 13), (100, 13)], fill=WOOD_HI)
    tab_im.save(furn_dir / "table_wood.png")

    # Table with food, bread, and pewter tankards
    food_im = tab_im.copy()
    d_food = ImageDraw.Draw(food_im)
    # Round crusty sourdough loaf on cutting board
    _box(d_food, 18, 11, 38, 21, WOOD_LIGHT, WOOD_HI, WOOD_MID)
    d_food.ellipse([22, 10, 34, 18], fill=(188, 138, 72, 255))
    d_food.ellipse([24, 11, 32, 15], fill=(225, 185, 115, 255))
    d_food.line([(25, 13), (31, 13)], fill=(150, 95, 45, 255))
    # Pewter tankards with frothy ale
    for tx in (46, 68):
        _box(d_food, tx, 8, tx + 6, 17, IRON_MID, IRON_HI, IRON_DARK)
        d_food.ellipse([tx, 7, tx + 6, 10], fill=(245, 242, 230, 255))  # foam
    # Wooden bowl of stew with spoon
    d_food.ellipse([82, 11, 96, 20], fill=WOOD_DEEP)
    d_food.ellipse([83, 12, 95, 18], fill=(160, 68, 32, 255))  # stew broth
    d_food.line([(92, 10), (98, 7)], fill=WOOD_LIGHT, width=1)  # spoon
    food_im.save(furn_dir / "table_food.png")

    # =========================================================================
    # 12. Carved Nordic High-Back Chair (48x64)
    # =========================================================================
    ch_im, d_ch = _canvas(48, 64)
    _shadow(d_ch, 6, 52, 42, 60)
    # Tall carved backrest posts with brass finials
    _box(d_ch, 8, 4, 13, 50, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    _box(d_ch, 35, 4, 40, 50, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    d_ch.ellipse([7, 1, 14, 7], fill=BRASS_MID)
    d_ch.ellipse([34, 1, 41, 7], fill=BRASS_MID)
    # Carved backrest panel with arched top
    _box(d_ch, 13, 8, 35, 32, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    d_ch.arc([16, 10, 32, 26], 180, 360, fill=WOOD_DEEP, width=2)
    # Padded dark crimson leather cushion
    _box(d_ch, 10, 32, 38, 44, CRIMSON_MID, CRIMSON_LIGHT, CRIMSON_DARK)
    # Brass upholstery studs
    for bx in range(12, 38, 5):
        d_ch.point([(bx, 42)], fill=BRASS_HI)
    # Chair legs and foot stretchers
    for lx in (10, 35):
        _box(d_ch, lx, 44, lx + 3, 56, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    ch_im.save(furn_dir / "chair_wood.png")

    # =========================================================================
    # 13. Stool (24x28) & Bench (96x32)
    # =========================================================================
    st_im, d_st = _canvas(24, 28)
    _shadow(d_st, 2, 22, 22, 27)
    for lx in (5, 17):
        _box(d_st, lx, 14, lx + 2, 24, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    _box(d_st, 3, 8, 21, 15, WOOD_MID, WOOD_LIGHT, WOOD_DEEP)
    d_st.ellipse([5, 9, 19, 13], fill=WOOD_LIGHT)
    st_im.save(furn_dir / "stool.png")

    bn_im, d_bn = _canvas(96, 32)
    _shadow(d_bn, 4, 24, 92, 31)
    for lx in (10, 82):
        _box(d_bn, lx, 14, lx + 4, 28, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    _box(d_bn, 4, 8, 92, 18, WOOD_MID, WOOD_LIGHT, WOOD_DEEP)
    d_bn.line([(6, 10), (90, 10)], fill=WOOD_HI)
    bn_im.save(furn_dir / "bench.png")

    # =========================================================================
    # 14. Storage Cupboard (80x112)
    # =========================================================================
    cup_im, d_cup = _canvas(80, 112)
    _shadow(d_cup, 6, 98, 74, 110)
    _box(d_cup, 8, 10, 72, 102, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    # Crown cornice molding
    _box(d_cup, 6, 4, 74, 12, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    # Double door panels
    d_cup.line([(40, 12), (40, 100)], fill=OUTLINE, width=2)
    for dx in (14, 44):
        # Top panel
        _box(d_cup, dx, 18, dx + 22, 52, WOOD_MID, WOOD_LIGHT, WOOD_DEEP)
        # Bottom panel
        _box(d_cup, dx, 58, dx + 22, 94, WOOD_MID, WOOD_LIGHT, WOOD_DEEP)
    # Brass drop handles
    d_cup.rectangle([34, 52, 37, 60], fill=BRASS_MID)
    d_cup.rectangle([43, 52, 46, 60], fill=BRASS_MID)
    cup_im.save(furn_dir / "cupboard.png")

    # =========================================================================
    # 15. Iron-Bound Chest (64x52)
    # =========================================================================
    ch_box_im, d_chb = _canvas(64, 52)
    _shadow(d_chb, 4, 40, 60, 50)
    _box(d_chb, 6, 12, 58, 46, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    # Iron corner straps & vertical bands
    for bx in (12, 48):
        _box(d_chb, bx, 10, bx + 4, 46, IRON_MID, IRON_HI, IRON_DARK)
        d_chb.point([(bx + 1, 14), (bx + 1, 28), (bx + 1, 40)], fill=IRON_HI)
    # Brass keyhole escutcheon plate & latch
    d_chb.rectangle([28, 20, 36, 28], fill=BRASS_MID)
    d_chb.point([(32, 23)], fill=OUTLINE)
    d_chb.line([(32, 24), (32, 26)], fill=OUTLINE)
    ch_box_im.save(furn_dir / "chest.png")

    # =========================================================================
    # 16. Rugs: Fur Pelt Rug (112x72) & Woven Nordic Rug (128x72)
    # =========================================================================
    fur_im, d_fur = _canvas(112, 72)
    # Dark shadow under fur
    d_fur.ellipse([4, 6, 108, 66], fill=SHADOW)
    # Outer dark fur body
    d_fur.ellipse([8, 10, 104, 62], fill=(48, 36, 26, 255))
    # Layered mid-tone fur with organic contours
    d_fur.ellipse([12, 14, 100, 58], fill=(116, 88, 62, 255))
    d_fur.ellipse([18, 18, 94, 54], fill=(148, 116, 82, 255))
    # Directional fur strands
    for k in range(160):
        px = 16 + (k * 37) % 78
        py = 16 + (k * 53) % 40
        d_fur.line([(px, py), (px + 3, py + 1)], fill=(188, 154, 118, 255))
    # Sculpted bear head & ears
    d_fur.ellipse([88, 24, 108, 48], fill=(48, 36, 26, 255))
    d_fur.ellipse([90, 26, 106, 46], fill=(136, 104, 74, 255))
    d_fur.ellipse([100, 33, 105, 39], fill=(24, 18, 14, 255))  # black nose
    for cy in (24, 46):
        d_fur.ellipse([92, cy - 4, 98, cy + 4], fill=(86, 64, 44, 255))  # ears
    # Four paws with ivory claws
    for cx, cy in ((10, 16), (10, 56), (82, 12), (82, 60)):
        d_fur.ellipse([cx, cy - 5, cx + 14, cy + 5], fill=(54, 40, 28, 255))
        d_fur.point([(cx + 1, cy - 2), (cx + 1, cy), (cx + 1, cy + 2)], fill=(225, 220, 205, 255))
    fur_im.save(furn_dir / "fur_rug.png")

    # Woven Nordic Tapestry Rug (128x72)
    wov_im, d_wov = _canvas(128, 72)
    # Dark border
    d_wov.rectangle([6, 6, 122, 66], fill=OUTLINE)
    d_wov.rectangle([8, 8, 120, 64], fill=CRIMSON_DARK)
    d_wov.rectangle([12, 12, 116, 60], fill=CRIMSON_MID)
    # Inner gold weave border
    d_wov.rectangle([16, 16, 112, 56], outline=BRASS_MID, width=2)
    # Nordic diamond knotwork center motifs
    for cx in (40, 64, 88):
        d_wov.polygon([(cx, 22), (cx + 12, 36), (cx, 50), (cx - 12, 36)], fill=BRASS_MID)
        d_wov.polygon([(cx, 26), (cx + 8, 36), (cx, 46), (cx - 8, 36)], fill=CRIMSON_DEEP)
        d_wov.point([(cx, 36)], fill=BRASS_HI)
    # Fringed ends
    for fy in range(10, 62, 3):
        d_wov.line([(3, fy), (6, fy)], fill=LINEN_MID)
        d_wov.line([(122, fy), (125, fy)], fill=LINEN_MID)
    wov_im.save(furn_dir / "rug_woven.png")

    # =========================================================================
    # 17. Room Door, Sacks, Barrels, Anvil, Loom, Weapon & Tool Racks, Extras
    # =========================================================================
    build_extras(furn_dir)
    print(
        "built upgraded interior art in assets/interiors/: floor_wood.png, floor_stone.png, "
        "wall_timber.png, wall_stone.png, and 24 high-detail furniture props"
    )


def _glow(path: Path, size: int, strength: float, tint: tuple[int, int, int]) -> None:
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    r = np.hypot(xx - size / 2 + 0.5, yy - size / 2 + 0.5) / (size / 2)
    a = np.clip(1.0 - r, 0.0, 1.0) ** 2 * strength
    arr = np.zeros((size, size, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = tint
    arr[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(path)


def _flame(i: int) -> Image.Image:
    im, d = _canvas(44, 40)
    d.ellipse([4, 30, 40, 40], fill=(150, 36, 14, 255))
    d.ellipse([8, 31, 36, 40], fill=(235, 100, 24, 255))
    sway = [(-2, 0, 2), (2, -1, -2), (0, 2, 1), (-1, -2, 3)][i]
    for k, (cx, hgt, wid) in enumerate([(14, 24, 7), (22, 32, 9), (31, 22, 6)]):
        lean = sway[k]
        h = hgt + (3 if (i + k) % 2 else -2)
        for layer, (col, shrink) in enumerate([((226, 74, 18, 255), 0), ((255, 150, 30, 255), 2), ((255, 232, 130, 255), 4)]):
            top = 36 - h + shrink * 2
            w = max(2, wid - shrink)
            d.polygon(
                [(cx - w, 36), (cx - w // 2 + lean, 36 - h // 2 + shrink), (cx + lean * 2, top), (cx + w // 2 + lean, 36 - h // 2 + shrink), (cx + w, 36)],
                fill=col,
            )
    return im


def _fire_sheet(path: Path) -> None:
    sheet = Image.new("RGBA", (44 * 4, 40), (0, 0, 0, 0))
    for i in range(4):
        sheet.alpha_composite(_flame(i), (i * 44, 0))
    sheet.save(path)


def _shaft(path: Path) -> None:
    w, h = 64, 88
    arr = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        t = y / (h - 1)
        half = 14 + 18 * t
        for x in range(w):
            dx = abs(x - w / 2 + 0.5)
            edge = np.clip((half - dx) / 6.0, 0.0, 1.0)
            fade = (1.0 - t) ** 1.2
            arr[y, x] = (255, 236, 190, int(edge * fade * 150))
    Image.fromarray(arr, "RGBA").save(path)


def build_extras(furn_dir: Path) -> None:
    _fire_sheet(furn_dir / "hearth_fire_sheet.png")
    _glow(furn_dir / "hearth_glow.png", 192, 0.85, (255, 150, 60))
    _glow(furn_dir / "candle_glow.png", 64, 0.9, (255, 200, 110))
    _shaft(furn_dir / "light_shaft.png")

    # Wall window with leaded diamond panes (40x52)
    im, d = _canvas(40, 52)
    _box(d, 2, 2, 38, 50, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    d.rectangle([6, 6, 34, 44], fill=(22, 26, 32, 255))
    d.rectangle([7, 7, 33, 43], fill=(138, 168, 192, 255))
    d.rectangle([7, 7, 33, 22], fill=(178, 204, 222, 255))
    d.line([(20, 6), (20, 44)], fill=WOOD_DEEP, width=2)
    d.line([(6, 25), (34, 25)], fill=WOOD_DEEP, width=2)
    _box(d, 1, 46, 39, 51, WOOD_LIGHT, WOOD_HI, WOOD_DARK)
    im.save(furn_dir / "window_wall.png")

    # Shelf unit with pottery crocks and jars (64x96)
    im, d = _canvas(64, 96)
    _shadow(d, 6, 84, 58, 94)
    _box(d, 6, 6, 58, 88, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    for sy in (28, 52, 76):
        d.rectangle([8, sy, 56, sy + 4], fill=WOOD_LIGHT)
        d.line([(8, sy + 4), (56, sy + 4)], fill=WOOD_DEEP)
    jars = [(12, (130, 72, 42)), (24, (72, 104, 82)), (36, (160, 138, 94)), (46, (115, 62, 56))]
    for row, base in enumerate((28, 52, 76)):
        for k, (jx, col) in enumerate(jars):
            jh = 12 + (k + row) % 3 * 3
            d.rectangle([jx, base - jh, jx + 7, base - 1], fill=col)
            d.rectangle([jx + 1, base - jh - 2, jx + 6, base - jh], fill=(50, 36, 24, 255))
            d.line([(jx + 1, base - jh + 2), (jx + 1, base - 3)], fill=tuple(min(255, c + 50) for c in col[:3]) + (255,))
    im.save(furn_dir / "shelf_unit.png")

    # Cast Iron Cauldron on Tripod (40x44)
    im, d = _canvas(40, 44)
    _shadow(d, 4, 36, 36, 43)
    for tx in (8, 20, 32):
        d.line([(20, 6), (tx, 38)], fill=IRON_DARK, width=2)
    d.ellipse([7, 14, 33, 38], fill=OUTLINE)
    d.ellipse([8, 15, 32, 37], fill=IRON_MID)
    d.ellipse([10, 15, 30, 24], fill=(54, 86, 64, 255))  # savory broth
    d.arc([8, 15, 32, 37], 200, 340, fill=IRON_HI, width=2)
    im.save(furn_dir / "cauldron.png")

    # Hanging herb bundles (56x40)
    im, d = _canvas(56, 40)
    d.line([(2, 4), (54, 4)], fill=WOOD_DARK, width=2)
    for k, (hx, col) in enumerate([(8, (88, 120, 70)), (22, (140, 120, 70)), (36, (90, 110, 80)), (48, (120, 90, 60))]):
        d.line([(hx, 4), (hx, 12)], fill=(150, 130, 90, 255))
        d.polygon([(hx - 4, 12), (hx + 4, 12), (hx + 6, 34 - k % 2 * 4), (hx, 38 - k % 2 * 4), (hx - 6, 34 - k % 2 * 4)], fill=col)
        d.line([(hx, 14), (hx, 32)], fill=tuple(max(0, c - 30) for c in col[:3]) + (255,))
    im.save(furn_dir / "herb_bunches.png")

    # Weapon rack with spears and shield (72x80)
    im, d = _canvas(72, 80)
    _shadow(d, 4, 68, 68, 79)
    d.rectangle([6, 20, 10, 72], fill=WOOD_DARK)
    d.rectangle([62, 20, 66, 72], fill=WOOD_DARK)
    d.rectangle([6, 36, 66, 41], fill=WOOD_MID)
    d.rectangle([6, 56, 66, 61], fill=WOOD_MID)
    for sx in (18, 28, 38):
        d.line([(sx, 6), (sx, 66)], fill=(130, 100, 70, 255), width=2)
        d.polygon([(sx - 3, 12), (sx + 3, 12), (sx, 2)], fill=IRON_HI)
    d.ellipse([46, 36, 64, 58], fill=OUTLINE)
    d.ellipse([47, 37, 63, 57], fill=(54, 70, 96, 255))
    d.ellipse([53, 43, 57, 51], fill=IRON_HI)
    im.save(furn_dir / "weapon_rack.png")

    # Blacksmith tool rack (72x72)
    im, d = _canvas(72, 72)
    _shadow(d, 4, 62, 68, 71)
    _box(d, 4, 6, 68, 60, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    for hx, col in ((16, IRON_MID), (34, IRON_HI), (52, IRON_MID)):
        d.line([(hx, 14), (hx, 48)], fill=(130, 100, 70, 255), width=2)
        d.rectangle([hx - 6, 12, hx + 6, 20], fill=col)
    d.line([(24, 52), (60, 28)], fill=IRON_HI, width=2)
    d.line([(26, 54), (62, 30)], fill=IRON_MID, width=2)
    im.save(furn_dir / "tool_rack.png")

    # Blacksmith Anvil on Tree Stump (56x64)
    im, d = _canvas(56, 64)
    _shadow(d, 6, 52, 50, 62)
    d.rectangle([16, 32, 40, 56], fill=(62, 46, 32, 255))
    d.ellipse([16, 30, 40, 36], fill=(86, 64, 46, 255))
    d.rectangle([18, 24, 38, 32], fill=IRON_DARK)
    d.rectangle([14, 16, 42, 25], fill=IRON_MID)
    d.polygon([(14, 16), (4, 18), (14, 23)], fill=IRON_LIGHT)
    d.rectangle([16, 14, 42, 17], fill=IRON_LIGHT)
    d.line([(16, 14), (42, 14)], fill=IRON_HI)
    im.save(furn_dir / "anvil.png")

    # Weaver Upright Loom (88x80)
    im, d = _canvas(88, 80)
    _shadow(d, 10, 70, 78, 78)
    d.rectangle([14, 8, 20, 74], fill=WOOD_DARK)
    d.rectangle([68, 8, 74, 74], fill=WOOD_DARK)
    d.rectangle([12, 8, 76, 14], fill=WOOD_MID)
    d.rectangle([12, 68, 76, 74], fill=WOOD_MID)
    d.rectangle([22, 16, 66, 46], fill=(48, 68, 92, 255))
    for wy in range(18, 46, 4):
        d.line([(22, wy), (66, wy)], fill=(62, 88, 118, 255))
    for wx in range(24, 66, 5):
        d.line([(wx, 46), (wx, 66)], fill=LINEN_MID)
        d.ellipse([wx - 2, 64, wx + 2, 69], fill=(70, 75, 82, 255))
    im.save(furn_dir / "loom.png")

    # Spinning Wheel (56x64)
    im, d = _canvas(56, 64)
    _shadow(d, 4, 54, 52, 63)
    d.ellipse([10, 14, 42, 46], fill=OUTLINE)
    d.ellipse([12, 16, 40, 44], outline=WOOD_LIGHT, width=2)
    for ang in range(0, 360, 45):
        d.line([(26, 30), (26 + 13 * math.cos(math.radians(ang)), 30 + 13 * math.sin(math.radians(ang)))], fill=WOOD_MID)
    d.rectangle([40, 28, 52, 32], fill=WOOD_DARK)
    d.rectangle([48, 18, 52, 32], fill=WOOD_DARK)
    d.rectangle([10, 46, 14, 58], fill=WOOD_DARK)
    d.rectangle([38, 46, 42, 58], fill=WOOD_DARK)
    d.rectangle([48, 12, 54, 20], fill=LINEN_LIGHT)
    im.save(furn_dir / "spinning_wheel.png")

    # Grindstone (48x56)
    im, d = _canvas(48, 56)
    _shadow(d, 2, 46, 46, 55)
    d.rectangle([6, 24, 10, 50], fill=WOOD_DARK)
    d.rectangle([38, 24, 42, 50], fill=WOOD_DARK)
    d.ellipse([10, 12, 38, 44], fill=OUTLINE)
    d.ellipse([11, 13, 37, 43], fill=STONE_MID)
    d.ellipse([20, 24, 28, 32], fill=WOOD_DARK)
    im.save(furn_dir / "grindstone.png")

    # Water trough (64x36)
    im, d = _canvas(64, 36)
    _shadow(d, 2, 28, 62, 35)
    _box(d, 4, 10, 60, 30, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    d.rectangle([8, 12, 56, 22], fill=(42, 80, 106, 255))
    d.line([(8, 12), (56, 12)], fill=(110, 150, 175, 255))
    im.save(furn_dir / "trough.png")

    # Ale Barrels (80x64)
    im, d = _canvas(80, 64)
    _shadow(d, 6, 50, 74, 62)
    for bx in (12, 44):
        d.ellipse([bx, 20, bx + 24, 56], fill=WOOD_MID)
        d.ellipse([bx + 2, 22, bx + 22, 32], fill=WOOD_LIGHT)
        d.ellipse([bx, 24, bx + 24, 28], outline=IRON_MID, width=2)
        d.ellipse([bx, 48, bx + 24, 52], outline=IRON_MID, width=2)
        d.line([(bx + 11, 26), (bx + 13, 26)], fill=OUTLINE)
    im.save(furn_dir / "barrels.png")

    # Tavern Bar Counter (144x56)
    im, d = _canvas(144, 56)
    _shadow(d, 8, 44, 136, 54)
    d.rectangle([10, 16, 134, 48], fill=WOOD_DARK)
    for px in range(16, 130, 20):
        d.rectangle([px, 20, px + 14, 44], fill=WOOD_MID)
    _box(d, 8, 8, 136, 20, WOOD_MID, WOOD_LIGHT, WOOD_DEEP)
    for tx in (34, 78, 106):
        d.rectangle([tx, 8, tx + 6, 14], fill=IRON_LIGHT)
    im.save(furn_dir / "counter_bar.png")

    # Fishing net frame (88x80)
    im, d = _canvas(88, 80)
    _shadow(d, 4, 68, 84, 79)
    d.rectangle([6, 8, 11, 72], fill=WOOD_DARK)
    d.rectangle([77, 8, 82, 72], fill=WOOD_DARK)
    d.rectangle([4, 8, 84, 13], fill=WOOD_MID)
    for nx in range(12, 78, 6):
        d.line([(nx, 13), (nx - 2 + (nx % 12) // 3, 62)], fill=(150, 142, 110, 255))
    for ny in range(20, 62, 7):
        d.line([(12, ny), (76, ny + 2)], fill=(124, 118, 92, 255))
    for fx in (24, 52):
        d.ellipse([fx, 52, fx + 14, 60], fill=(98, 118, 128, 255))
    im.save(furn_dir / "net_rack.png")

    # Bottle shelf for bar (128x64)
    im, d = _canvas(128, 64)
    _box(d, 4, 6, 124, 58, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    d.rectangle([8, 10, 120, 54], fill=WOOD_DEEP)
    d.rectangle([8, 32, 120, 36], fill=WOOD_LIGHT)
    for row, base in enumerate((32, 54)):
        for k in range(10):
            bx = 12 + k * 10.8
            col = [(70, 110, 76), (120, 70, 46), (82, 96, 130), (150, 120, 70)][(k + row) % 4]
            d.rectangle([bx, base - 16, bx + 6, base - 1], fill=col)
            d.rectangle([bx + 2, base - 22, bx + 4, base - 16], fill=col)
    im.save(furn_dir / "bottle_shelf.png")

    # Sacks and crate (64x52)
    im, d = _canvas(64, 52)
    _shadow(d, 2, 42, 62, 51)
    _box(d, 34, 18, 60, 44, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    d.line([(34, 18), (60, 44)], fill=WOOD_DEEP)
    for sx, sh in ((6, 30), (20, 24)):
        d.polygon([(sx, 44), (sx + 2, 44 - sh), (sx + 10, 44 - sh - 4), (sx + 18, 44 - sh), (sx + 20, 44)], fill=OUTLINE)
        d.polygon([(sx + 2, 43), (sx + 3, 44 - sh + 1), (sx + 10, 44 - sh - 2), (sx + 17, 44 - sh + 1), (sx + 18, 43)], fill=(170, 150, 108, 255))
        d.line([(sx + 4, 44 - sh + 2), (sx + 16, 44 - sh + 2)], fill=(120, 100, 70, 255))
    im.save(furn_dir / "sacks.png")

    # Hall banner (32x80)
    im, d = _canvas(32, 80)
    d.rectangle([2, 2, 30, 6], fill=WOOD_MID)
    d.polygon([(4, 6), (28, 6), (28, 66), (16, 76), (4, 66)], fill=OUTLINE)
    d.polygon([(6, 7), (26, 7), (26, 64), (16, 72), (6, 64)], fill=(46, 62, 92, 255))
    d.polygon([(16, 18), (23, 34), (16, 50), (9, 34)], fill=BRASS_MID)
    d.polygon([(16, 24), (20, 34), (16, 44), (12, 34)], fill=(46, 62, 92, 255))
    im.save(furn_dir / "banner.png")

    # Mayor's desk with scrolls (112x60)
    im, d = _canvas(112, 60)
    _shadow(d, 6, 46, 106, 59)
    for lx in (14, 92):
        _box(d, lx, 24, lx + 6, 52, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    _box(d, 8, 10, 104, 26, WOOD_MID, WOOD_LIGHT, WOOD_DEEP)
    d.rectangle([20, 12, 46, 22], fill=LINEN_LIGHT)
    d.line([(24, 15), (42, 15)], fill=(120, 100, 80, 255))
    d.line([(24, 18), (38, 18)], fill=(120, 100, 80, 255))
    d.ellipse([58, 13, 66, 21], fill=CRIMSON_MID)
    d.rectangle([76, 10, 98, 16], fill=LINEN_MID)
    im.save(furn_dir / "desk_scrolls.png")

    # Interior wooden door (40x56)
    im, d = _canvas(40, 56)
    _box(d, 2, 2, 38, 54, WOOD_DARK, WOOD_MID, WOOD_DEEP)
    d.rectangle([5, 5, 35, 54], fill=(84, 58, 38, 255))
    for px in (12, 20, 28):
        d.line([(px, 5), (px, 54)], fill=WOOD_DEEP)
    d.rectangle([4, 16, 36, 20], fill=IRON_MID)
    d.rectangle([4, 38, 36, 42], fill=IRON_MID)
    d.ellipse([26, 28, 32, 34], outline=IRON_HI, width=2)
    d.rectangle([14, 8, 26, 13], fill=BRASS_MID)
    im.save(furn_dir / "room_door.png")

    # Coal bin for forge (48x40)
    im, d = _canvas(48, 40)
    _shadow(d, 2, 32, 46, 39)
    _box(d, 4, 12, 44, 34, WOOD_MID, WOOD_LIGHT, WOOD_DARK)
    d.polygon([(6, 14), (14, 6), (24, 10), (34, 4), (42, 14)], fill=(24, 24, 28, 255))
    for k in range(7):
        d.point([(10 + k * 5, 9 + k % 3)], fill=(86, 88, 96, 255))
    im.save(furn_dir / "coal_bin.png")


if __name__ == "__main__":
    build_interior_art()
