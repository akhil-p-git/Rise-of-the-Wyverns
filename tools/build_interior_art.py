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
    # Firewood logs
    d_h.rectangle([34, 66, 62, 72], fill=(74, 48, 28, 255))
    d_h.rectangle([36, 68, 60, 74], fill=(54, 32, 18, 255))
    # Glowing fiery coals
    d_h.ellipse([34, 62, 62, 76], fill=(190, 40, 15, 255))
    d_h.ellipse([36, 60, 60, 74], fill=(255, 120, 20, 255))
    d_h.ellipse([40, 62, 56, 72], fill=(255, 210, 80, 255))
    d_h.point([(46, 64), (48, 62), (50, 64), (47, 66)], fill=(255, 250, 180, 255))
    for gx in (34, 42, 50, 58, 64):
        d_h.line([(gx, 58), (gx, 78)], fill=(24, 24, 28, 255), width=2)
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

    print(
        "built interior art in assets/interiors/: floor_wood.png, floor_stone.png, "
        "wall_timber.png, wall_stone.png, and 11 furniture props"
    )


if __name__ == "__main__":
    build_interior_art()
