"""Generates 4x-density pixel art interior textures and furniture props for
house interiors in Wrackmouth (Mayor's Hall, Kell's Forge, The Salt Gull Inn,
Lantern Watch Tower, and Cottages).
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent


def build_interior_art() -> None:
    int_dir = ROOT / "assets" / "interiors"
    furn_dir = int_dir / "furniture"
    furn_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261023)

    # 1. Seamless Wood Plank Floor (128x128, 8 planks x 16px)
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

    # 2. Seamless Flagstone Floor (128x128) (For Forge & Watchtower)
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

    # 3. Timber Wall Header & Beam (512x96)
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

    # 4. Stone Wall Header & Ashlar Blocks (512x96)
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

    # 5. Furniture: Iron-Bound Oak Chest (64x52)
    chest = Image.new("RGBA", (64, 52), (0, 0, 0, 0))
    d_ch = ImageDraw.Draw(chest)
    d_ch.ellipse([4, 40, 60, 50], fill=(18, 16, 22, 140))
    d_ch.rectangle([6, 12, 58, 46], fill=(74, 52, 34, 255))
    d_ch.rectangle([8, 14, 56, 44], fill=(92, 66, 44, 255))
    d_ch.arc([6, 4, 58, 22], 180, 0, fill=(62, 44, 30, 255), width=2)
    d_ch.line([(6, 24), (58, 24)], fill=(34, 24, 16, 255), width=2)
    for bx in (12, 48):
        d_ch.rectangle([bx, 8, bx + 4, 46], fill=(42, 44, 50, 255))
        d_ch.line([(bx, 8), (bx, 46)], fill=(75, 78, 86, 255))
        d_ch.point([(bx + 1, 11), (bx + 1, 26), (bx + 1, 40)], fill=(120, 125, 136, 255))
    d_ch.rectangle([29, 20, 35, 28], fill=(175, 135, 55, 255))
    d_ch.rectangle([30, 21, 34, 27], fill=(215, 175, 75, 255))
    d_ch.rectangle([31, 24, 33, 26], fill=(30, 24, 12, 255))
    chest.save(furn_dir / "chest.png")

    # 6. Furniture: Cupboard / Storage Dresser (80x112)
    cupboard = Image.new("RGBA", (80, 112), (0, 0, 0, 0))
    d_cup = ImageDraw.Draw(cupboard)
    d_cup.ellipse([8, 96, 72, 110], fill=(18, 16, 22, 160))
    d_cup.rectangle([10, 12, 70, 102], fill=(58, 42, 28, 255))
    d_cup.rectangle([12, 14, 68, 100], fill=(78, 56, 38, 255))
    d_cup.rectangle([8, 6, 72, 14], fill=(46, 32, 20, 255))
    d_cup.line([(8, 6), (72, 6)], fill=(96, 72, 50, 255))
    d_cup.line([(40, 14), (40, 100)], fill=(32, 22, 14, 255))
    d_cup.rectangle([16, 20, 36, 52], fill=(62, 44, 30, 255))
    d_cup.rectangle([44, 20, 64, 52], fill=(62, 44, 30, 255))
    d_cup.rectangle([16, 58, 36, 92], fill=(62, 44, 30, 255))
    d_cup.rectangle([44, 58, 64, 92], fill=(62, 44, 30, 255))
    d_cup.rectangle([34, 50, 37, 58], fill=(190, 150, 60, 255))
    d_cup.rectangle([43, 50, 46, 58], fill=(190, 150, 60, 255))
    cupboard.save(furn_dir / "cupboard.png")

    # 7. Furniture: Stone Fireplace Hearth (96x88)
    hearth = Image.new("RGBA", (96, 88), (0, 0, 0, 0))
    d_h = ImageDraw.Draw(hearth)
    d_h.ellipse([10, 74, 86, 86], fill=(18, 16, 22, 150))
    d_h.rectangle([14, 4, 82, 80], fill=(50, 54, 60, 255))
    d_h.rectangle([16, 6, 80, 78], fill=(70, 76, 84, 255))
    # Stone block courses
    for sy in range(12, 76, 14):
        d_h.line([(16, sy), (80, sy)], fill=(36, 40, 46, 255))
        d_h.line([(16, sy + 1), (80, sy + 1)], fill=(92, 100, 110, 255))
    d_h.rectangle([26, 32, 70, 78], fill=(18, 16, 18, 255))
    d_h.arc([26, 20, 70, 48], 180, 0, fill=(38, 42, 48, 255), width=3)
    d_h.rectangle([10, 20, 86, 28], fill=(42, 32, 24, 255))
    d_h.line([(10, 20), (86, 20)], fill=(96, 78, 58, 255))
    # Firewood logs and iron grate (the flames are the animated hearth_fire_sheet.png)
    d_h.rectangle([34, 68, 62, 74], fill=(74, 48, 28, 255))
    d_h.rectangle([36, 70, 60, 76], fill=(54, 32, 18, 255))
    d_h.ellipse([36, 70, 60, 77], fill=(30, 22, 18, 255))
    for gx in (34, 42, 50, 58, 64):
        d_h.line([(gx, 62), (gx, 78)], fill=(24, 24, 28, 255), width=2)
    hearth.save(furn_dir / "hearth.png")

    # 8. Furniture: Heavy Oak Table with Bench (112x64)
    table = Image.new("RGBA", (112, 64), (0, 0, 0, 0))
    d_tab = ImageDraw.Draw(table)
    d_tab.ellipse([10, 48, 102, 62], fill=(18, 16, 22, 150))
    for lx in (18, 90):
        d_tab.rectangle([lx, 26, lx + 6, 54], fill=(46, 32, 20, 255))
        d_tab.line([(lx, 26), (lx, 54)], fill=(68, 50, 34, 255))
    d_tab.rectangle([22, 42, 92, 46], fill=(40, 28, 18, 255))
    d_tab.rectangle([12, 14, 100, 28], fill=(62, 44, 28, 255))
    d_tab.rectangle([14, 12, 98, 24], fill=(88, 64, 42, 255))
    d_tab.line([(14, 12), (98, 12)], fill=(112, 84, 56, 255))
    d_tab.rectangle([34, 15, 52, 22], fill=(205, 192, 165, 255))
    d_tab.rectangle([70, 14, 76, 20], fill=(125, 130, 140, 255))
    table.save(furn_dir / "table_wood.png")

    # 9. Furniture: Timber Bedstead with Quilt (88x104)
    bed = Image.new("RGBA", (88, 104), (0, 0, 0, 0))
    d_bed = ImageDraw.Draw(bed)
    d_bed.ellipse([8, 84, 80, 100], fill=(18, 16, 22, 150))
    d_bed.rectangle([12, 8, 18, 48], fill=(44, 30, 20, 255))
    d_bed.rectangle([70, 8, 76, 48], fill=(44, 30, 20, 255))
    d_bed.rectangle([16, 12, 72, 34], fill=(58, 40, 26, 255))
    d_bed.rectangle([14, 32, 74, 90], fill=(52, 36, 24, 255))
    d_bed.rectangle([16, 46, 72, 88], fill=(38, 58, 44, 255))
    d_bed.rectangle([18, 48, 70, 86], fill=(48, 72, 54, 255))
    d_bed.rectangle([16, 40, 72, 48], fill=(185, 178, 162, 255))
    d_bed.rectangle([24, 26, 64, 40], fill=(210, 200, 180, 255))
    d_bed.line([(24, 26), (64, 26)], fill=(230, 222, 204, 255))
    d_bed.rectangle([12, 80, 18, 96], fill=(44, 30, 20, 255))
    d_bed.rectangle([70, 80, 76, 96], fill=(44, 30, 20, 255))
    d_bed.rectangle([16, 84, 72, 92], fill=(54, 38, 24, 255))
    bed.save(furn_dir / "bed_wood.png")

    # 10. Furniture: Blacksmith Anvil on Stump (56x64)
    anvil = Image.new("RGBA", (56, 64), (0, 0, 0, 0))
    d_an = ImageDraw.Draw(anvil)
    d_an.ellipse([6, 52, 50, 62], fill=(18, 16, 22, 160))
    d_an.rectangle([16, 32, 40, 56], fill=(62, 46, 32, 255))
    d_an.ellipse([16, 30, 40, 36], fill=(86, 64, 46, 255))
    d_an.rectangle([18, 24, 38, 32], fill=(48, 52, 60, 255))
    d_an.rectangle([14, 16, 42, 25], fill=(65, 72, 82, 255))
    d_an.polygon([(14, 16), (4, 18), (14, 23)], fill=(75, 82, 94, 255))
    d_an.rectangle([16, 14, 42, 17], fill=(130, 140, 155, 255))
    d_an.line([(16, 14), (42, 14)], fill=(185, 195, 210, 255))
    anvil.save(furn_dir / "anvil.png")

    # 11. Furniture: Weaver Upright Loom (88x80)
    loom = Image.new("RGBA", (88, 80), (0, 0, 0, 0))
    d_lm = ImageDraw.Draw(loom)
    d_lm.ellipse([10, 70, 78, 78], fill=(18, 16, 22, 140))
    d_lm.rectangle([14, 8, 20, 74], fill=(52, 38, 26, 255))
    d_lm.rectangle([68, 8, 74, 74], fill=(52, 38, 26, 255))
    d_lm.rectangle([12, 8, 76, 14], fill=(68, 48, 34, 255))
    d_lm.rectangle([12, 68, 76, 74], fill=(68, 48, 34, 255))
    d_lm.rectangle([22, 16, 66, 46], fill=(48, 68, 92, 255))
    for wy in range(18, 46, 4):
        d_lm.line([(22, wy), (66, wy)], fill=(62, 88, 118, 255))
    for wx in range(24, 66, 5):
        d_lm.line([(wx, 46), (wx, 66)], fill=(185, 175, 155, 255))
        d_lm.ellipse([wx - 2, 64, wx + 2, 69], fill=(70, 75, 82, 255))
    loom.save(furn_dir / "loom.png")

    # 12. Furniture: Woven Floor Rug (128x72)
    rug = Image.new("RGBA", (128, 72), (0, 0, 0, 0))
    d_rug = ImageDraw.Draw(rug)
    d_rug.rectangle([8, 8, 120, 64], fill=(32, 28, 30, 255))
    d_rug.rectangle([12, 12, 116, 60], fill=(110, 42, 36, 255))
    d_rug.rectangle([16, 16, 112, 56], fill=(136, 52, 44, 255))
    d_rug.polygon([(64, 20), (84, 36), (64, 52), (44, 36)], fill=(175, 140, 75, 255))
    d_rug.polygon([(64, 24), (78, 36), (64, 48), (50, 36)], fill=(110, 42, 36, 255))
    for fy in range(12, 60, 3):
        d_rug.line([(5, fy), (8, fy)], fill=(205, 195, 175, 255))
        d_rug.line([(120, fy), (123, fy)], fill=(205, 195, 175, 255))
    rug.save(furn_dir / "rug_woven.png")

    # 13. Furniture: Ale Barrels (80x64)
    barrels = Image.new("RGBA", (80, 64), (0, 0, 0, 0))
    d_bar = ImageDraw.Draw(barrels)
    d_bar.ellipse([6, 50, 74, 62], fill=(18, 16, 22, 150))
    for bx in (12, 44):
        d_bar.ellipse([bx, 20, bx + 24, 56], fill=(62, 44, 30, 255))
        d_bar.ellipse([bx + 2, 22, bx + 22, 32], fill=(86, 62, 42, 255))
        d_bar.ellipse([bx, 24, bx + 24, 28], outline=(45, 48, 54, 255), width=2)
        d_bar.ellipse([bx, 48, bx + 24, 52], outline=(45, 48, 54, 255), width=2)
        d_bar.line([(bx + 11, 26), (bx + 13, 26)], fill=(20, 16, 12, 255))
    barrels.save(furn_dir / "barrels.png")

    # 14. Furniture: Tavern Bar Counter (144x56)
    counter = Image.new("RGBA", (144, 56), (0, 0, 0, 0))
    d_cnt = ImageDraw.Draw(counter)
    d_cnt.ellipse([8, 44, 136, 54], fill=(18, 16, 22, 150))
    d_cnt.rectangle([10, 16, 134, 48], fill=(48, 34, 22, 255))
    for px in range(16, 130, 20):
        d_cnt.rectangle([px, 20, px + 14, 44], fill=(64, 46, 30, 255))
    d_cnt.rectangle([8, 8, 136, 20], fill=(82, 58, 36, 255))
    d_cnt.rectangle([10, 6, 134, 16], fill=(112, 82, 52, 255))
    d_cnt.line([(10, 6), (134, 6)], fill=(145, 110, 72, 255))
    for tx in (34, 78, 106):
        d_cnt.rectangle([tx, 8, tx + 6, 14], fill=(135, 140, 150, 255))
    counter.save(furn_dir / "counter_bar.png")

    # 15. Furniture: Carved Nordic Dais Chair (48x64)
    chair = Image.new("RGBA", (48, 64), (0, 0, 0, 0))
    d_ch = ImageDraw.Draw(chair)
    d_ch.ellipse([6, 52, 42, 60], fill=(18, 16, 22, 140))
    # Chair backrest posts
    d_ch.rectangle([8, 6, 12, 50], fill=(44, 30, 20, 255))
    d_ch.rectangle([36, 6, 40, 50], fill=(44, 30, 20, 255))
    # Carved back panel
    d_ch.rectangle([12, 8, 36, 32], fill=(68, 48, 32, 255))
    d_ch.line([(12, 8), (36, 8)], fill=(96, 72, 50, 255))
    # Finials
    d_ch.ellipse([7, 3, 13, 9], fill=(180, 145, 60, 255))
    d_ch.ellipse([35, 3, 41, 9], fill=(180, 145, 60, 255))
    # Padded cushion seat
    d_ch.rectangle([10, 32, 38, 44], fill=(95, 30, 28, 255))
    d_ch.rectangle([12, 34, 36, 42], fill=(130, 42, 38, 255))
    # Legs
    for lx in (10, 36):
        d_ch.rectangle([lx, 44, lx + 3, 56], fill=(48, 34, 22, 255))
    chair.save(furn_dir / "chair_wood.png")

    build_extras(furn_dir)
    print(
        "built interior art in assets/interiors/: floor_wood.png, floor_stone.png, "
        "wall_timber.png, wall_stone.png, and the furniture props"
    )


# --- extra furniture, windows, light and flames --------------------------------------------------

OUTLINE = (24, 18, 14, 255)
SHADOW = (18, 16, 22, 150)
WOOD_D, WOOD_M, WOOD_L = (46, 32, 20, 255), (74, 52, 34, 255), (104, 76, 50, 255)
IRON_D, IRON_M, IRON_L = (44, 48, 56, 255), (78, 84, 94, 255), (140, 148, 160, 255)
CLOTH = (205, 192, 165, 255)


def _canvas(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _shadow(d: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int) -> None:
    d.ellipse([x0, y0, x1, y1], fill=SHADOW)


def _box(d: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, mid, light=None, dark=None) -> None:
    """A lit rectangle: outline, body, light top edge and dark bottom edge."""
    d.rectangle([x0, y0, x1, y1], fill=OUTLINE)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=mid)
    if light:
        d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=light)
    if dark:
        d.line([(x0 + 1, y1 - 1), (x1 - 1, y1 - 1)], fill=dark)


def _flame(i: int) -> Image.Image:
    """One of four hearth flame frames (44x40): ember bed plus three leaning tongues."""
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


def _glow(path: Path, size: int, strength: float, tint: tuple[int, int, int]) -> None:
    """Soft radial additive light: premultiplied-friendly RGBA with alpha falling off with distance."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    r = np.hypot(xx - size / 2 + 0.5, yy - size / 2 + 0.5) / (size / 2)
    a = np.clip(1.0 - r, 0.0, 1.0) ** 2 * strength
    arr = np.zeros((size, size, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = tint
    arr[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(path)


def _shaft(path: Path) -> None:
    """Daylight falling from a window across the floor: a soft trapezoid, brightest next to the wall."""
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
    props_dir = furn_dir.parent.parent / "props"
    _fire_sheet(furn_dir / "hearth_fire_sheet.png")
    _glow(furn_dir / "hearth_glow.png", 192, 0.85, (255, 150, 60))
    _glow(furn_dir / "candle_glow.png", 64, 0.9, (255, 200, 110))
    _shaft(furn_dir / "light_shaft.png")

    # Wall window with panes and a pale sky (40x52)
    im, d = _canvas(40, 52)
    _box(d, 2, 2, 37, 49, WOOD_M, WOOD_L, WOOD_D)
    d.rectangle([6, 6, 33, 43], fill=(26, 28, 34, 255))
    d.rectangle([7, 7, 32, 42], fill=(150, 176, 196, 255))
    d.rectangle([7, 7, 32, 20], fill=(188, 208, 220, 255))
    d.line([(19, 6), (19, 43)], fill=WOOD_D, width=2)
    d.line([(6, 24), (33, 24)], fill=WOOD_D, width=2)
    d.rectangle([2, 44, 37, 49], fill=WOOD_L)
    im.save(furn_dir / "window_wall.png")

    # Shelf unit with jars and crocks (64x96)
    im, d = _canvas(64, 96)
    _shadow(d, 6, 84, 58, 94)
    _box(d, 6, 6, 57, 88, WOOD_M, WOOD_L, WOOD_D)
    for sy in (28, 52, 76):
        d.rectangle([8, sy, 55, sy + 4], fill=WOOD_L)
        d.line([(8, sy + 4), (55, sy + 4)], fill=WOOD_D)
    jars = [(12, (120, 70, 40)), (24, (70, 100, 80)), (36, (150, 130, 90)), (46, (110, 60, 54))]
    for row, base in enumerate((28, 52, 76)):
        for k, (jx, col) in enumerate(jars):
            jh = 12 + (k + row) % 3 * 3
            d.rectangle([jx, base - jh, jx + 7, base - 1], fill=col)
            d.rectangle([jx + 1, base - jh - 2, jx + 6, base - jh], fill=(60, 44, 30, 255))
            d.line([(jx + 1, base - jh + 2), (jx + 1, base - 3)], fill=tuple(min(255, c + 50) for c in col[:3]) + (255,))
    im.save(furn_dir / "shelf_unit.png")

    # Three-legged stool (24x28) and long bench (96x32)
    im, d = _canvas(24, 28)
    _shadow(d, 2, 22, 22, 27)
    for lx in (5, 17):
        d.rectangle([lx, 14, lx + 2, 24], fill=WOOD_D)
    d.rectangle([3, 8, 20, 15], fill=OUTLINE)
    d.rectangle([4, 9, 19, 14], fill=WOOD_M)
    d.line([(4, 9), (19, 9)], fill=WOOD_L)
    im.save(furn_dir / "stool.png")
    im, d = _canvas(96, 32)
    _shadow(d, 4, 24, 92, 31)
    for lx in (10, 82):
        d.rectangle([lx, 14, lx + 4, 28], fill=WOOD_D)
    d.rectangle([4, 8, 91, 18], fill=OUTLINE)
    d.rectangle([5, 9, 90, 16], fill=WOOD_M)
    d.line([(5, 9), (90, 9)], fill=WOOD_L)
    im.save(furn_dir / "bench.png")

    # Iron cauldron on a tripod (40x44)
    im, d = _canvas(40, 44)
    _shadow(d, 4, 36, 36, 43)
    for tx in (8, 20, 32):
        d.line([(20, 6), (tx, 38)], fill=IRON_D, width=2)
    d.ellipse([7, 14, 33, 38], fill=OUTLINE)
    d.ellipse([8, 15, 32, 37], fill=IRON_M)
    d.ellipse([10, 15, 30, 24], fill=(60, 90, 70, 255))
    d.arc([8, 15, 32, 37], 200, 340, fill=IRON_L, width=2)
    im.save(furn_dir / "cauldron.png")

    # Hanging herb bundles (56x40)
    im, d = _canvas(56, 40)
    d.line([(2, 4), (54, 4)], fill=WOOD_D, width=2)
    for k, (hx, col) in enumerate([(8, (88, 120, 70)), (22, (140, 120, 70)), (36, (90, 110, 80)), (48, (120, 90, 60))]):
        d.line([(hx, 4), (hx, 12)], fill=(150, 130, 90, 255))
        d.polygon([(hx - 4, 12), (hx + 4, 12), (hx + 6, 34 - k % 2 * 4), (hx, 38 - k % 2 * 4), (hx - 6, 34 - k % 2 * 4)], fill=col)
        d.line([(hx, 14), (hx, 32)], fill=tuple(max(0, c - 30) for c in col[:3]) + (255,))
    im.save(furn_dir / "herb_bunches.png")

    # Candle stand (16x40)
    im, d = _canvas(16, 40)
    _shadow(d, 1, 33, 15, 39)
    d.rectangle([7, 14, 9, 34], fill=IRON_M)
    d.rectangle([3, 32, 12, 35], fill=IRON_D)
    d.rectangle([5, 8, 10, 15], fill=(226, 214, 186, 255))
    d.rectangle([5, 8, 10, 9], fill=(250, 244, 226, 255))
    d.polygon([(7, 2), (9, 7), (7, 8), (6, 5)], fill=(255, 190, 60, 255))
    im.save(furn_dir / "candle_stand.png")

    # Table laid with bread, bowls and cups (112x64)
    im, d = _canvas(112, 64)
    _shadow(d, 8, 48, 104, 62)
    for lx in (16, 90):
        d.rectangle([lx, 26, lx + 6, 54], fill=WOOD_D)
    d.rectangle([10, 14, 102, 28], fill=OUTLINE)
    d.rectangle([12, 12, 100, 26], fill=(92, 66, 44, 255))
    d.line([(12, 12), (100, 12)], fill=(120, 90, 60, 255))
    d.ellipse([20, 14, 40, 22], fill=(190, 150, 90, 255))  # loaf
    d.ellipse([22, 14, 38, 19], fill=(214, 176, 112, 255))
    for bx in (50, 66):
        d.ellipse([bx, 14, bx + 11, 22], fill=(90, 60, 44, 255))
        d.ellipse([bx + 1, 14, bx + 10, 19], fill=(130, 98, 64, 255))
    for cx in (80, 90):
        d.rectangle([cx, 12, cx + 4, 20], fill=IRON_L)
        d.rectangle([cx, 12, cx + 4, 13], fill=(220, 224, 232, 255))
    im.save(furn_dir / "table_food.png")

    # Child's cot with a patched blanket (64x84)
    im, d = _canvas(64, 84)
    _shadow(d, 4, 68, 60, 82)
    d.rectangle([8, 10, 14, 64], fill=WOOD_D)
    d.rectangle([50, 10, 56, 64], fill=WOOD_D)
    d.rectangle([10, 14, 54, 70], fill=OUTLINE)
    d.rectangle([11, 15, 53, 69], fill=(64, 46, 30, 255))
    d.rectangle([12, 34, 52, 68], fill=(150, 108, 52, 255))
    d.rectangle([14, 36, 50, 66], fill=(176, 130, 66, 255))
    d.rectangle([20, 44, 32, 54], fill=(96, 120, 150, 255))  # patch
    d.rectangle([12, 18, 52, 32], fill=(205, 196, 176, 255))
    d.ellipse([20, 18, 44, 31], fill=(224, 216, 198, 255))
    im.save(furn_dir / "bed_kid.png")

    # Weapon rack with spears and a shield (72x80)
    im, d = _canvas(72, 80)
    _shadow(d, 4, 68, 68, 79)
    d.rectangle([6, 20, 10, 72], fill=WOOD_D)
    d.rectangle([62, 20, 66, 72], fill=WOOD_D)
    d.rectangle([6, 36, 66, 41], fill=WOOD_M)
    d.rectangle([6, 56, 66, 61], fill=WOOD_M)
    for sx in (18, 28, 38):
        d.line([(sx, 6), (sx, 66)], fill=(130, 100, 70, 255), width=2)
        d.polygon([(sx - 3, 12), (sx + 3, 12), (sx, 2)], fill=IRON_L)
    d.ellipse([46, 36, 64, 58], fill=OUTLINE)
    d.ellipse([47, 37, 63, 57], fill=(54, 70, 96, 255))
    d.ellipse([53, 43, 57, 51], fill=IRON_L)
    im.save(furn_dir / "weapon_rack.png")

    # Tool rack: hammers and tongs on a board (72x72)
    im, d = _canvas(72, 72)
    _shadow(d, 4, 62, 68, 71)
    _box(d, 4, 6, 67, 60, WOOD_M, WOOD_L, WOOD_D)
    for hx, col in ((16, IRON_M), (34, IRON_L), (52, IRON_M)):
        d.line([(hx, 14), (hx, 48)], fill=(130, 100, 70, 255), width=2)
        d.rectangle([hx - 6, 12, hx + 6, 20], fill=col)
    d.line([(24, 52), (60, 28)], fill=IRON_L, width=2)
    d.line([(26, 54), (62, 30)], fill=IRON_M, width=2)
    im.save(furn_dir / "tool_rack.png")

    # Grindstone in a frame (48x56)
    im, d = _canvas(48, 56)
    _shadow(d, 2, 46, 46, 55)
    d.rectangle([6, 24, 10, 50], fill=WOOD_D)
    d.rectangle([38, 24, 42, 50], fill=WOOD_D)
    d.ellipse([10, 12, 38, 44], fill=OUTLINE)
    d.ellipse([11, 13, 37, 43], fill=(110, 112, 118, 255))
    d.ellipse([20, 24, 28, 32], fill=WOOD_D)
    im.save(furn_dir / "grindstone.png")

    # Water trough (64x36)
    im, d = _canvas(64, 36)
    _shadow(d, 2, 28, 62, 35)
    d.rectangle([4, 10, 59, 30], fill=OUTLINE)
    d.rectangle([5, 11, 58, 29], fill=WOOD_M)
    d.rectangle([8, 12, 55, 18], fill=(48, 86, 110, 255))
    d.line([(8, 12), (55, 12)], fill=(110, 150, 170, 255))
    im.save(furn_dir / "trough.png")

    # Spinning wheel (56x64)
    im, d = _canvas(56, 64)
    _shadow(d, 4, 54, 52, 63)
    d.ellipse([10, 14, 42, 46], fill=OUTLINE)
    d.ellipse([12, 16, 40, 44], fill=(0, 0, 0, 0))
    d.ellipse([12, 16, 40, 44], outline=WOOD_L, width=2)
    for ang in range(0, 360, 45):
        import math

        d.line([(26, 30), (26 + 13 * math.cos(math.radians(ang)), 30 + 13 * math.sin(math.radians(ang)))], fill=WOOD_M)
    d.rectangle([40, 28, 52, 32], fill=WOOD_D)
    d.rectangle([48, 18, 52, 32], fill=WOOD_D)
    d.rectangle([10, 46, 14, 58], fill=WOOD_D)
    d.rectangle([38, 46, 42, 58], fill=WOOD_D)
    d.rectangle([48, 12, 54, 20], fill=(226, 214, 186, 255))
    im.save(furn_dir / "spinning_wheel.png")

    # Fishing net frame (88x80)
    im, d = _canvas(88, 80)
    _shadow(d, 4, 68, 84, 79)
    d.rectangle([6, 8, 11, 72], fill=WOOD_D)
    d.rectangle([77, 8, 82, 72], fill=WOOD_D)
    d.rectangle([4, 8, 84, 13], fill=WOOD_M)
    for nx in range(12, 78, 6):
        d.line([(nx, 13), (nx - 2 + (nx % 12) // 3, 62)], fill=(150, 142, 110, 255))
    for ny in range(20, 62, 7):
        d.line([(12, ny), (76, ny + 2)], fill=(124, 118, 92, 255))
    for fx in (24, 52):
        d.ellipse([fx, 52, fx + 14, 60], fill=(98, 118, 128, 255))
        d.polygon([(fx + 14, 56), (fx + 20, 52), (fx + 20, 60)], fill=(98, 118, 128, 255))
    im.save(furn_dir / "net_rack.png")

    # Bottle shelf for the bar (128x64)
    im, d = _canvas(128, 64)
    _box(d, 4, 6, 123, 58, WOOD_M, WOOD_L, WOOD_D)
    d.rectangle([8, 10, 119, 54], fill=(38, 28, 20, 255))
    d.rectangle([8, 32, 119, 36], fill=WOOD_L)
    for row, base in enumerate((32, 54)):
        for k in range(10):
            bx = 12 + k * 10.8
            col = [(70, 110, 76), (120, 70, 46), (82, 96, 130), (150, 120, 70)][(k + row) % 4]
            d.rectangle([bx, base - 16, bx + 6, base - 1], fill=col)
            d.rectangle([bx + 2, base - 22, bx + 4, base - 16], fill=col)
    im.save(furn_dir / "bottle_shelf.png")

    # Bear-fur rug (112x72)
    im, d = _canvas(112, 72)
    d.ellipse([6, 8, 106, 64], fill=(52, 38, 28, 255))
    d.ellipse([9, 10, 103, 61], fill=(142, 108, 76, 255))
    for k in range(120):
        px, py = 16 + (k * 37) % 80, 14 + (k * 53) % 42
        d.line([(px, py), (px + 3, py + 2)], fill=(176, 140, 102, 255))
    for k in range(40):
        px, py = 20 + (k * 29) % 70, 18 + (k * 41) % 34
        d.line([(px, py), (px - 2, py + 3)], fill=(104, 76, 52, 255))
    d.ellipse([88, 24, 108, 46], fill=(52, 38, 28, 255))  # head
    d.ellipse([90, 26, 106, 44], fill=(150, 116, 82, 255))
    d.ellipse([99, 31, 104, 36], fill=(30, 22, 18, 255))  # nose
    for cx, cy in ((92, 26), (92, 46)):
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(110, 82, 58, 255))  # ears
    for cx, cy in ((10, 18), (10, 54), (84, 14), (84, 58)):
        d.ellipse([cx, cy - 6, cx + 14, cy + 6], fill=(52, 38, 28, 255))  # paws
        d.ellipse([cx + 1, cy - 5, cx + 13, cy + 5], fill=(128, 96, 68, 255))
    im.save(furn_dir / "fur_rug.png")

    # Sacks and a crate (64x52)
    im, d = _canvas(64, 52)
    _shadow(d, 2, 42, 62, 51)
    _box(d, 34, 18, 60, 44, WOOD_M, WOOD_L, WOOD_D)
    d.line([(34, 18), (60, 44)], fill=WOOD_D)
    for sx, sh in ((6, 30), (20, 24)):
        d.polygon([(sx, 44), (sx + 2, 44 - sh), (sx + 10, 44 - sh - 4), (sx + 18, 44 - sh), (sx + 20, 44)], fill=OUTLINE)
        d.polygon([(sx + 2, 43), (sx + 3, 44 - sh + 1), (sx + 10, 44 - sh - 2), (sx + 17, 44 - sh + 1), (sx + 18, 43)], fill=(170, 150, 108, 255))
        d.line([(sx + 4, 44 - sh + 2), (sx + 16, 44 - sh + 2)], fill=(120, 100, 70, 255))
    im.save(furn_dir / "sacks.png")

    # Hall banner (32x80)
    im, d = _canvas(32, 80)
    d.rectangle([2, 2, 29, 5], fill=WOOD_M)
    d.polygon([(4, 5), (27, 5), (27, 66), (15, 76), (4, 66)], fill=OUTLINE)
    d.polygon([(6, 6), (25, 6), (25, 64), (15, 72), (6, 64)], fill=(46, 62, 92, 255))
    d.polygon([(15, 18), (22, 34), (15, 50), (8, 34)], fill=(190, 156, 78, 255))
    d.polygon([(15, 24), (19, 34), (15, 44), (11, 34)], fill=(46, 62, 92, 255))
    im.save(furn_dir / "banner.png")

    # Mayor's desk with scrolls and a seal (112x60)
    im, d = _canvas(112, 60)
    _shadow(d, 6, 46, 106, 59)
    for lx in (14, 92):
        d.rectangle([lx, 24, lx + 6, 52], fill=WOOD_D)
    d.rectangle([8, 12, 104, 28], fill=OUTLINE)
    d.rectangle([10, 10, 102, 26], fill=(84, 60, 40, 255))
    d.line([(10, 10), (102, 10)], fill=(118, 88, 58, 255))
    d.rectangle([20, 12, 46, 22], fill=(220, 206, 176, 255))
    d.line([(24, 15), (42, 15)], fill=(120, 100, 80, 255))
    d.line([(24, 18), (38, 18)], fill=(120, 100, 80, 255))
    d.ellipse([58, 13, 66, 21], fill=(150, 36, 30, 255))
    d.rectangle([76, 10, 98, 16], fill=(200, 188, 160, 255))
    im.save(furn_dir / "desk_scrolls.png")

    # Wooden room door with an iron ring handle and a number plate (40x56)
    im, d = _canvas(40, 56)
    _box(d, 2, 2, 37, 54, WOOD_D, WOOD_M, OUTLINE)
    d.rectangle([5, 5, 34, 54], fill=(84, 58, 38, 255))
    for px in (12, 20, 28):
        d.line([(px, 5), (px, 54)], fill=(58, 40, 26, 255))
    d.rectangle([4, 16, 35, 20], fill=IRON_M)
    d.rectangle([4, 38, 35, 42], fill=IRON_M)
    d.ellipse([26, 28, 32, 34], outline=IRON_L, width=2)
    d.rectangle([14, 8, 25, 13], fill=(190, 150, 60, 255))
    im.save(furn_dir / "room_door.png")

    # Coal bin (48x40) for the forge
    im, d = _canvas(48, 40)
    _shadow(d, 2, 32, 46, 39)
    _box(d, 4, 12, 43, 34, WOOD_M, WOOD_L, WOOD_D)
    d.polygon([(6, 14), (14, 6), (24, 10), (34, 4), (42, 14)], fill=(24, 24, 28, 255))
    for k in range(7):
        d.point([(10 + k * 5, 9 + k % 3)], fill=(86, 88, 96, 255))
    im.save(furn_dir / "coal_bin.png")


if __name__ == "__main__":
    build_interior_art()
