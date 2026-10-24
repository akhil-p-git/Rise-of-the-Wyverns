"""Builds native 4x-density pixel art sprite sheets for Court Wizard Calder and
Wrackmouth Town Guards, plus arcane furniture props and royal banners for Mayor's Hall.

Run: python3 tools/build_court_art.py
"""

from __future__ import annotations

import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent


def build_wizard_sprite_sheet() -> None:
    """Builds `assets/npc/wizard.png` (384x512, 4 directions x 4 frames).
    Deep indigo/violet robes with gold trim, silver beard, and an arcane glowing staff.
    """
    cw, ch = 96, 128
    sheet = Image.new("RGBA", (cw * 4, ch * 4), (0, 0, 0, 0))

    # Base colors
    robe_dark = (34, 28, 54, 255)
    robe_mid = (54, 44, 84, 255)
    robe_hi = (78, 65, 118, 255)
    gold_trim = (215, 175, 65, 255)
    gold_hi = (255, 225, 110, 255)
    hair_col = (205, 212, 225, 255)
    skin_col = (210, 178, 150, 255)
    skin_sh = (175, 140, 115, 255)
    staff_wood = (78, 54, 36, 255)
    crystal_cyan = (65, 215, 245, 255)
    crystal_hi = (185, 245, 255, 255)
    outline = (20, 16, 28, 255)

    def draw_wizard_frame(
        direction: int, walk_col: int
    ) -> Image.Image:
        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)

        # Foot stride vertical shift
        is_stride_a = (walk_col == 1)
        is_stride_b = (walk_col == 3)
        foot_l_y = -3 if is_stride_a else 0
        foot_r_y = -3 if is_stride_b else 0

        # Center of character in 96x128 cell
        cx = 48
        cy = 60

        # Drop shadow
        d.ellipse([cx - 16, cy + 34, cx + 16, cy + 42], fill=(18, 16, 24, 140))

        # 1. Boots
        boot_y = cy + 32
        d.rectangle([cx - 9, boot_y + foot_l_y, cx - 2, boot_y + foot_l_y + 4], fill=outline)
        d.rectangle([cx + 2, boot_y + foot_r_y, cx + 9, boot_y + foot_r_y + 4], fill=outline)
        d.rectangle([cx - 8, boot_y + foot_l_y, cx - 3, boot_y + foot_l_y + 3], fill=(38, 30, 26, 255))
        d.rectangle([cx + 3, boot_y + foot_r_y, cx + 8, boot_y + foot_r_y + 3], fill=(38, 30, 26, 255))

        # 2. Flowing Robes
        robe_pts = [
            (cx - 14, cy + 32),
            (cx + 14, cy + 32),
            (cx + 12, cy + 6),
            (cx - 12, cy + 6),
        ]
        d.polygon([(x, y + 1) for x, y in robe_pts], fill=outline)
        d.polygon(robe_pts, fill=robe_mid)
        # Robe shadow folds
        d.polygon([(cx - 12, cy + 32), (cx - 2, cy + 32), (cx - 1, cy + 10), (cx - 8, cy + 10)], fill=robe_dark)
        # Gold hem trim
        d.line([(cx - 13, cy + 31), (cx + 13, cy + 31)], fill=gold_trim, width=2)
        d.line([(cx - 11, cy + 30), (cx + 11, cy + 30)], fill=gold_hi, width=1)

        # 3. Torso / Mantle
        d.rectangle([cx - 11, cy - 2, cx + 11, cy + 8], fill=robe_mid)
        d.rectangle([cx - 12, cy - 2, cx + 12, cy - 2], fill=outline)
        # Gold stole / sash down chest
        if direction != 1:  # front or sides
            d.rectangle([cx - 3, cy - 1, cx + 3, cy + 18], fill=gold_trim)
            d.line([(cx, cy - 1), (cx, cy + 18)], fill=gold_hi)

        # 4. Arms & Hands
        if direction in (0, 1):  # Front or Back
            # Left arm
            d.rectangle([cx - 15, cy + 2, cx - 11, cy + 16], fill=robe_mid)
            d.rectangle([cx - 15, cy + 16, cx - 12, cy + 20], fill=skin_col)
            # Right arm (holding staff)
            d.rectangle([cx + 11, cy + 2, cx + 15, cy + 14], fill=robe_mid)
            d.rectangle([cx + 12, cy + 14, cx + 16, cy + 18], fill=skin_col)
        elif direction == 2:  # Left
            d.rectangle([cx - 10, cy + 2, cx - 5, cy + 16], fill=robe_mid)
            d.rectangle([cx - 10, cy + 16, cx - 6, cy + 19], fill=skin_col)
        else:  # Right
            d.rectangle([cx + 5, cy + 2, cx + 10, cy + 16], fill=robe_mid)
            d.rectangle([cx + 6, cy + 16, cx + 10, cy + 19], fill=skin_col)

        # 5. Head, Hood & Beard
        head_y = cy - 14
        # Hood cowl
        d.ellipse([cx - 12, head_y - 12, cx + 12, head_y + 12], fill=outline)
        d.ellipse([cx - 11, head_y - 11, cx + 11, head_y + 11], fill=robe_mid)
        d.ellipse([cx - 9, head_y - 9, cx + 9, head_y + 9], fill=robe_dark)

        if direction == 0:  # Front face
            # Face inside hood
            d.rectangle([cx - 7, head_y - 4, cx + 7, head_y + 4], fill=skin_col)
            d.rectangle([cx - 6, head_y - 2, cx + 6, head_y + 4], fill=skin_col)
            # Eyes
            d.point([(cx - 4, head_y - 1), (cx + 3, head_y - 1)], fill=(25, 25, 35, 255))
            d.point([(cx - 4, head_y - 2), (cx + 3, head_y - 2)], fill=hair_col)
            # Long Silver Beard
            beard_pts = [(cx - 6, head_y + 3), (cx + 6, head_y + 3), (cx + 3, head_y + 16), (cx - 3, head_y + 16)]
            d.polygon(beard_pts, fill=hair_col)
            d.line([(cx, head_y + 3), (cx, head_y + 15)], fill=(235, 240, 255, 255))
        elif direction == 1:  # Back of hood
            d.ellipse([cx - 10, head_y - 10, cx + 10, head_y + 10], fill=robe_mid)
            # Hood point
            d.polygon([(cx - 4, head_y), (cx + 4, head_y), (cx, head_y + 12)], fill=robe_dark)
        elif direction == 2:  # Left profile
            d.rectangle([cx - 9, head_y - 3, cx - 2, head_y + 4], fill=skin_col)
            d.point([(cx - 7, head_y - 1)], fill=(25, 25, 35, 255))
            # Beard profile
            d.polygon([(cx - 9, head_y + 2), (cx - 1, head_y + 2), (cx - 4, head_y + 14)], fill=hair_col)
        else:  # Right profile
            d.rectangle([cx + 2, head_y - 3, cx + 9, head_y + 4], fill=skin_col)
            d.point([(cx + 6, head_y - 1)], fill=(25, 25, 35, 255))
            # Beard profile
            d.polygon([(cx + 1, head_y + 2), (cx + 9, head_y + 2), (cx + 4, head_y + 14)], fill=hair_col)

        # 6. Runic Staff & Arcane Crystal
        staff_x = cx + 16 if direction in (0, 1, 3) else cx - 16
        staff_top_y = cy - 24
        staff_bot_y = cy + 34
        # Wood staff shaft
        d.line([(staff_x, staff_top_y + 6), (staff_x, staff_bot_y)], fill=staff_wood, width=2)
        d.line([(staff_x, staff_top_y + 6), (staff_x, staff_bot_y)], fill=(110, 78, 52, 255), width=1)
        # Carved crescent finial at top
        d.arc([staff_x - 5, staff_top_y, staff_x + 5, staff_top_y + 10], 0, 360, fill=gold_trim, width=2)
        # Glowing Arcane Crystal
        d.ellipse([staff_x - 3, staff_top_y + 2, staff_x + 3, staff_top_y + 8], fill=crystal_cyan)
        d.point([(staff_x - 1, staff_top_y + 3), (staff_x, staff_top_y + 4)], fill=crystal_hi)

        return im

    for dir_i in range(4):
        for col_i in range(4):
            f = draw_wizard_frame(dir_i, col_i)
            sheet.alpha_composite(f, (col_i * cw, dir_i * ch))

    sheet.save(ROOT / "assets" / "npc" / "wizard.png")
    print("built assets/npc/wizard.png (384x512)")


def build_guard_sprite_sheet() -> None:
    """Builds `assets/npc/guard.png` (384x512, 4 directions x 4 frames).
    Steel helm, chainmail, dark-blue crest tabard, and an upright iron halberd spear.
    """
    cw, ch = 96, 128
    sheet = Image.new("RGBA", (cw * 4, ch * 4), (0, 0, 0, 0))

    steel_dark = (48, 52, 60, 255)
    steel_mid = (82, 90, 102, 255)
    steel_hi = (150, 162, 178, 255)
    tabard_col = (30, 48, 72, 255)
    tabard_hi = (45, 68, 98, 255)
    gold_crest = (195, 160, 60, 255)
    skin_col = (205, 170, 142, 255)
    wood_shaft = (68, 48, 34, 255)
    outline = (20, 22, 26, 255)

    def draw_guard_frame(
        direction: int, walk_col: int
    ) -> Image.Image:
        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)

        is_stride_a = (walk_col == 1)
        is_stride_b = (walk_col == 3)
        foot_l_y = -3 if is_stride_a else 0
        foot_r_y = -3 if is_stride_b else 0

        cx = 48
        cy = 60

        # Drop shadow
        d.ellipse([cx - 16, cy + 34, cx + 16, cy + 42], fill=(18, 16, 24, 140))

        # 1. Armored Greaves & Boots
        boot_y = cy + 28
        d.rectangle([cx - 9, boot_y + foot_l_y, cx - 2, boot_y + foot_l_y + 8], fill=steel_mid)
        d.rectangle([cx + 2, boot_y + foot_r_y, cx + 9, boot_y + foot_r_y + 8], fill=steel_mid)
        d.line([(cx - 8, boot_y + foot_l_y), (cx - 8, boot_y + foot_l_y + 8)], fill=steel_hi)
        d.line([(cx + 3, boot_y + foot_r_y), (cx + 3, boot_y + foot_r_y + 8)], fill=steel_hi)

        # 2. Chainmail Hauberk & Blue Tabard
        d.rectangle([cx - 11, cy + 4, cx + 11, cy + 26], fill=tabard_col)
        d.line([(cx - 11, cy + 4), (cx - 11, cy + 26)], fill=tabard_hi)
        d.line([(cx + 11, cy + 4), (cx + 11, cy + 26)], fill=outline)
        # Leather belt with iron buckle
        d.rectangle([cx - 12, cy + 18, cx + 12, cy + 21], fill=(36, 28, 22, 255))
        d.rectangle([cx - 3, cy + 17, cx + 3, cy + 22], fill=steel_hi)

        # Crest on tabard
        if direction != 1:  # front or sides
            d.polygon([(cx, cy + 8), (cx + 4, cy + 12), (cx, cy + 16), (cx - 4, cy + 12)], fill=gold_crest)

        # 3. Steel Pauldrons & Arms
        d.rectangle([cx - 15, cy + 4, cx - 10, cy + 11], fill=steel_mid)
        d.rectangle([cx + 10, cy + 4, cx + 15, cy + 11], fill=steel_mid)
        d.line([(cx - 15, cy + 4), (cx - 10, cy + 4)], fill=steel_hi)
        d.line([(cx + 10, cy + 4), (cx + 15, cy + 4)], fill=steel_hi)
        # Bracers
        d.rectangle([cx - 14, cy + 11, cx - 11, cy + 18], fill=steel_dark)
        d.rectangle([cx + 11, cy + 11, cx + 14, cy + 18], fill=steel_dark)

        # 4. Steel Sallet Helm & Chain Coif
        head_y = cy - 12
        # Coif
        d.ellipse([cx - 10, head_y - 8, cx + 10, head_y + 12], fill=steel_dark)
        # Steel Helm Dome
        d.ellipse([cx - 10, head_y - 12, cx + 10, head_y + 4], fill=steel_mid)
        d.line([(cx - 8, head_y - 11), (cx + 6, head_y - 11)], fill=steel_hi)
        # Visor / eye slit
        if direction == 0:  # Front
            d.rectangle([cx - 7, head_y - 2, cx + 7, head_y + 1], fill=(16, 16, 20, 255))
            d.rectangle([cx - 6, head_y + 2, cx + 6, head_y + 8], fill=steel_mid)
        elif direction == 1:  # Back
            d.ellipse([cx - 9, head_y - 10, cx + 9, head_y + 6], fill=steel_mid)
            d.rectangle([cx - 8, head_y + 2, cx + 8, head_y + 10], fill=steel_dark)
        elif direction == 2:  # Left
            d.rectangle([cx - 8, head_y - 2, cx - 1, head_y + 1], fill=(16, 16, 20, 255))
            d.rectangle([cx - 8, head_y + 2, cx - 2, head_y + 8], fill=steel_mid)
        else:  # Right
            d.rectangle([cx + 1, head_y - 2, cx + 8, head_y + 1], fill=(16, 16, 20, 255))
            d.rectangle([cx + 2, head_y + 2, cx + 8, head_y + 8], fill=steel_mid)

        # 5. Upright Halberd / Guard Spear
        spear_x = cx + 16 if direction in (0, 1, 3) else cx - 16
        spear_top_y = cy - 32
        spear_bot_y = cy + 34
        # Ash shaft
        d.line([(spear_x, spear_top_y + 16), (spear_x, spear_bot_y)], fill=wood_shaft, width=2)
        # Steel spearhead
        d.polygon(
            [(spear_x, spear_top_y), (spear_x + 4, spear_top_y + 16), (spear_x - 4, spear_top_y + 16)],
            fill=steel_hi,
        )
        d.line([(spear_x, spear_top_y), (spear_x, spear_top_y + 16)], fill=(235, 245, 255, 255))
        # Halberd side axe blade
        d.polygon(
            [(spear_x - 1, spear_top_y + 8), (spear_x - 9, spear_top_y + 4), (spear_x - 7, spear_top_y + 16), (spear_x - 1, spear_top_y + 14)],
            fill=steel_mid,
        )

        return im

    for dir_i in range(4):
        for col_i in range(4):
            f = draw_guard_frame(dir_i, col_i)
            sheet.alpha_composite(f, (col_i * cw, dir_i * ch))

    sheet.save(ROOT / "assets" / "npc" / "guard.png")
    print("built assets/npc/guard.png (384x512)")


def build_court_furniture_and_decor() -> None:
    furn_dir = ROOT / "assets" / "interiors" / "furniture"
    furn_dir.mkdir(parents=True, exist_ok=True)

    # 1. Alchemical Table (96x64)
    alc = Image.new("RGBA", (96, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(alc)
    # Shadow
    d.ellipse([8, 48, 88, 62], fill=(18, 16, 22, 140))
    # Wooden Table
    d.rectangle([12, 18, 84, 52], fill=(54, 38, 26, 255))
    d.rectangle([10, 16, 86, 24], fill=(78, 56, 38, 255))
    d.line([(10, 16), (86, 16)], fill=(112, 82, 54, 255))
    # Glass alembic retort (curved flask)
    d.ellipse([20, 8, 32, 20], fill=(90, 175, 215, 180))
    d.arc([22, 4, 40, 18], 160, 340, fill=(180, 235, 255, 220), width=2)
    # Glowing Red Potion Bottle
    d.rectangle([46, 10, 54, 20], fill=(225, 45, 40, 220))
    d.point([(48, 12), (49, 13)], fill=(255, 170, 170, 255))
    # Glowing Cyan Arcane Phial
    d.rectangle([58, 8, 64, 20], fill=(40, 210, 240, 220))
    d.point([(60, 10), (61, 11)], fill=(210, 250, 255, 255))
    # Open Grimoire on lectern
    d.polygon([(70, 14), (82, 10), (90, 14), (80, 18)], fill=(195, 185, 160, 255))
    d.line([(80, 10), (80, 18)], fill=(110, 80, 50, 255))
    alc.save(furn_dir / "alchemical_table.png")

    # 2. Arcane Bookshelf (80x112)
    bks = Image.new("RGBA", (80, 112), (0, 0, 0, 0))
    d = ImageDraw.Draw(bks)
    # Shadow
    d.ellipse([8, 96, 72, 110], fill=(18, 16, 22, 150))
    # Timber Case
    d.rectangle([10, 8, 70, 102], fill=(48, 34, 22, 255))
    d.rectangle([12, 10, 68, 100], fill=(68, 48, 32, 255))
    # Shelves
    for sy in (32, 54, 76):
        d.rectangle([12, sy, 68, sy + 4], fill=(36, 24, 16, 255))
        d.line([(12, sy), (68, sy)], fill=(92, 68, 44, 255))
    # Colorful Arcane Books
    book_cols = [
        (165, 45, 35, 255), (42, 85, 150, 255), (55, 125, 68, 255),
        (185, 145, 55, 255), (110, 45, 145, 255), (65, 195, 215, 255),
    ]
    for row_i, sy in enumerate([14, 36, 58]):
        bx = 16
        while bx < 64:
            bw = int(np.random.randint(4, 8))
            bh = int(np.random.randint(12, 17))
            col_b = book_cols[(row_i * 3 + bx) % len(book_cols)]
            d.rectangle([bx, sy + 18 - bh, bx + bw, sy + 18], fill=col_b)
            d.line([(bx + 1, sy + 18 - bh), (bx + 1, sy + 18)], fill=(min(255, col_b[0]+50), min(255, col_b[1]+50), min(255, col_b[2]+50), 255))
            bx += bw + 2
    bks.save(furn_dir / "bookshelf_arcane.png")

    # 3. Royal Wyvern Banner (64x112)
    ban = Image.new("RGBA", (64, 112), (0, 0, 0, 0))
    d = ImageDraw.Draw(ban)
    # Brass hanging rod
    d.rectangle([6, 8, 58, 12], fill=(195, 160, 60, 255))
    d.ellipse([4, 6, 8, 14], fill=(235, 195, 85, 255))
    d.ellipse([56, 6, 60, 14], fill=(235, 195, 85, 255))
    # Crimson velvet banner body with swallowtail bottom
    ban_pts = [(10, 12), (54, 12), (54, 88), (32, 102), (10, 88)]
    d.polygon(ban_pts, fill=(125, 25, 30, 255))
    # Gold border
    d.line([(12, 14), (52, 14), (52, 86), (32, 99), (12, 86), (12, 14)], fill=(215, 175, 65, 255), width=2)
    # Wyvern crest silhouette (gold)
    d.ellipse([26, 32, 38, 44], fill=(235, 195, 75, 255))  # body
    d.polygon([(32, 24), (28, 34), (36, 34)], fill=(235, 195, 75, 255))  # head
    d.polygon([(26, 34), (16, 26), (22, 42)], fill=(215, 175, 65, 255))  # wing left
    d.polygon([(38, 34), (48, 26), (42, 42)], fill=(215, 175, 65, 255))  # wing right
    d.line([(32, 44), (32, 60), (38, 64)], fill=(215, 175, 65, 255), width=2)  # tail
    ban.save(furn_dir / "royal_banner.png")

    print(
        "built assets/interiors/furniture/{alchemical_table,bookshelf_arcane,royal_banner}.png"
    )


if __name__ == "__main__":
    build_wizard_sprite_sheet()
    build_guard_sprite_sheet()
    build_court_furniture_and_decor()
