"""Builds the four starting-weapon item icons (64x64, framed like the other items) from Gemini art.

Sources in --src-dir (assets/source/gemini/weapons/, git-ignored), each on a magenta background:
  iron_daggers.jpeg  a crossed pair of daggers
  sword.jpeg         one long sword (used for the two-handed sword, and shrunk for sword and shield)
  staff.jpeg         the staff
The sword-and-shield icon pairs the sword with a round shield drawn here; it is a placeholder until
Gemini supplies a real sword-and-shield image (drop it in as sword_shield.jpeg and it is used instead).

Run: uv run --no-project --with pillow --with numpy python tools/build_weapon_icons.py --src-dir assets/source/gemini/weapons --out-dir assets/ui/items
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pixelize import remove_background
from build_modular_art import make_icon_bg

ART_BOX = 46  # the art fits in this square, centred in the 64x64 frame
COLORS = 20


def load_art(path: Path, size: int, tolerance: int = 160) -> Image.Image:
    im = remove_background(Image.open(path).convert("RGB"), tolerance)
    im = im.crop(im.getchannel("A").getbbox())
    scale = size / max(im.size)
    small = im.convert("RGBa").resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.BOX)
    small = small.convert("RGBA")
    # Quantize so the downscale does not leave a blur of in-between colours; keep a hard alpha edge.
    alpha = np.array(small)[..., 3]
    out = np.array(small.convert("RGB").quantize(colors=COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGBA"))
    out[..., 3] = np.where(alpha >= 128, 255, 0)
    return Image.fromarray(out, "RGBA")


def framed(art: Image.Image, offset: tuple[int, int] = (0, 0)) -> Image.Image:
    icon = make_icon_bg()
    icon.alpha_composite(art, ((64 - art.width) // 2 + offset[0], (64 - art.height) // 2 + offset[1]))
    return icon


def round_shield(diameter: int) -> Image.Image:
    im = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    outline = (24, 18, 14, 255)
    d.ellipse([0, 0, diameter - 1, diameter - 1], fill=outline)
    d.ellipse([2, 2, diameter - 3, diameter - 3], fill=(96, 98, 108, 255))  # iron rim
    d.ellipse([5, 5, diameter - 6, diameter - 6], fill=(88, 64, 42, 255))  # planks
    for x in range(8, diameter - 7, 5):
        d.line([(x, 6), (x, diameter - 7)], fill=(66, 46, 30, 255))
    d.ellipse([diameter // 2 - 4, diameter // 2 - 4, diameter // 2 + 4, diameter // 2 + 4], fill=(150, 156, 168, 255), outline=outline)
    d.arc([2, 2, diameter - 3, diameter - 3], 200, 280, fill=(170, 176, 188, 255), width=2)
    return im


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src-dir", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    a = p.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)

    framed(load_art(a.src_dir / "iron_daggers.jpeg", ART_BOX)).save(a.out_dir / "iron_daggers.png")
    framed(load_art(a.src_dir / "sword.jpeg", ART_BOX)).save(a.out_dir / "two_handed_sword.png")
    framed(load_art(a.src_dir / "staff.jpeg", ART_BOX)).save(a.out_dir / "staff.png")

    real = a.src_dir / "sword_shield.jpeg"
    if real.exists():
        framed(load_art(real, ART_BOX)).save(a.out_dir / "iron_sword_shield.png")
    else:
        icon = make_icon_bg()
        icon.alpha_composite(round_shield(30), (9, 22))
        icon.alpha_composite(load_art(a.src_dir / "sword.jpeg", 40), (15, 8))
        icon.save(a.out_dir / "iron_sword_shield.png")
    print(f"wrote 4 weapon icons to {a.out_dir}")


if __name__ == "__main__":
    main()
