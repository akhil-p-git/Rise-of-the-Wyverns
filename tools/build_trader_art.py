"""Builds the trader's art from existing sprites, so it matches the rest of Wrackmouth:

- assets/wrackmouth/shop_trader.png: the Rook cottage mirrored (door on the right), its painted smoke removed
  (the game animates smoke), with a hanging coin sign over the door and a stack of crates and sacks by the wall.
- assets/npc/merchant.png: Bram's sheet with the red tunic turned a deep violet, for Osric Venn.

Run: uv run --no-project --with pillow --with numpy python tools/build_trader_art.py
"""

import colorsys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUTLINE = (24, 18, 14, 255)


def build_shop() -> None:
    src = Image.open(ROOT / "assets" / "wrackmouth" / "cottage_rook.png").convert("RGBA")
    arr = np.array(src)
    arr[:44, 185:250] = 0  # painted chimney smoke
    shop = Image.fromarray(arr, "RGBA").transpose(Image.FLIP_LEFT_RIGHT)
    d = ImageDraw.Draw(shop)

    # Hanging sign: an iron bracket out of the wall above the door, a board with a gold coin.
    d.line([(196, 118), (196, 104)], fill=(44, 48, 56, 255), width=4)
    d.line([(196, 106), (252, 106)], fill=(44, 48, 56, 255), width=4)
    for chain_x in (204, 244):
        d.line([(chain_x, 108), (chain_x, 118)], fill=(70, 74, 84, 255), width=2)
    d.rectangle([198, 116, 250, 152], fill=OUTLINE)
    d.rectangle([200, 118, 248, 150], fill=(112, 82, 52, 255))
    d.rectangle([200, 118, 248, 122], fill=(138, 104, 68, 255))
    d.ellipse([212, 124, 236, 146], fill=OUTLINE)
    d.ellipse([214, 126, 234, 144], fill=(218, 168, 52, 255))
    d.ellipse([218, 130, 230, 140], outline=(250, 218, 110, 255), width=2)

    # Goods by the wall: two crates and two sacks.
    for x0, y0 in ((6, 226), (34, 236)):
        d.rectangle([x0, y0, x0 + 34, y0 + 30], fill=OUTLINE)
        d.rectangle([x0 + 2, y0 + 2, x0 + 32, y0 + 28], fill=(104, 76, 50, 255))
        d.line([(x0 + 2, y0 + 2), (x0 + 32, y0 + 28)], fill=(66, 46, 30, 255), width=2)
        d.line([(x0 + 2, y0 + 28), (x0 + 32, y0 + 2)], fill=(66, 46, 30, 255), width=2)
    for x0 in (66, 80):
        d.ellipse([x0, 244, x0 + 22, 276], fill=OUTLINE)
        d.ellipse([x0 + 2, 246, x0 + 20, 274], fill=(170, 150, 108, 255))
        d.line([(x0 + 6, 252), (x0 + 16, 252)], fill=(120, 100, 70, 255), width=2)
    shop.save(ROOT / "assets" / "wrackmouth" / "shop_trader.png")


def build_merchant() -> None:
    sheet = np.array(Image.open(ROOT / "assets" / "npc" / "bram.png").convert("RGBA")).astype(np.float32) / 255.0
    out = sheet.copy()
    flat = sheet.reshape(-1, 4)
    hsv = np.array([colorsys.rgb_to_hsv(*px[:3]) for px in flat])
    red = (flat[:, 3] > 0.5) & (hsv[:, 1] > 0.4) & ((hsv[:, 0] > 0.96) | (hsv[:, 0] < 0.03))
    target_hue = 0.78
    for i in np.where(red)[0]:
        r, g, b = colorsys.hsv_to_rgb(target_hue, hsv[i, 1] * 0.8, hsv[i, 2] * 0.85)
        flat[i, :3] = (r, g, b)
    out = flat.reshape(sheet.shape)
    Image.fromarray((out * 255).round().astype(np.uint8), "RGBA").save(ROOT / "assets" / "npc" / "merchant.png")


if __name__ == "__main__":
    build_shop()
    build_merchant()
    print("wrote assets/wrackmouth/shop_trader.png and assets/npc/merchant.png")
