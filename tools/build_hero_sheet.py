"""Builds the 4x4 hero sprite sheet from 12 source views (magenta background).

Rows: down, up, left, right. Columns: idle, stride A, idle, stride B, which is the
frame order `player.gd` expects. Frames share one palette and are anchored at the
feet (bottom centre) so they do not jitter.

Source files in --src-dir: idle_<dir>.png, walk_<dir>_left.png, walk_<dir>_right.png.

Run: uv run --no-project --with pillow --with numpy python tools/build_hero_sheet.py --src-dir DIR --out assets/hero/hero_sheet.png
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from pixelize import remove_background

DIRECTIONS = ["down", "up", "left", "right"]


def load_frame(path: Path, block: int, tolerance: int) -> Image.Image:
    im = remove_background(Image.open(path).convert("RGB"), tolerance)
    bbox = im.getchannel("A").getbbox()
    im = im.crop(bbox)
    size = (max(1, round(im.width / block)), max(1, round(im.height / block)))
    return im.convert("RGBa").resize(size, Image.BOX).convert("RGBA")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument(
        "--block", type=int, default=8, help="source pixels per output pixel"
    )
    p.add_argument("--colors", type=int, default=24)
    p.add_argument("--tolerance", type=int, default=160)
    a = p.parse_args()

    rows = []
    for d in DIRECTIONS:
        idle = load_frame(a.src_dir / f"idle_{d}.png", a.block, a.tolerance)
        step_a = load_frame(a.src_dir / f"walk_{d}_left.png", a.block, a.tolerance)
        step_b = load_frame(a.src_dir / f"walk_{d}_right.png", a.block, a.tolerance)
        rows.append([idle, step_a, idle, step_b])

    cell_w = max(f.width for r in rows for f in r) + 2
    cell_h = max(f.height for r in rows for f in r)
    sheet = Image.new("RGBA", (cell_w * 4, cell_h * len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, frame in enumerate(row):
            sheet.alpha_composite(
                frame,
                (
                    x * cell_w + (cell_w - frame.width) // 2,
                    y * cell_h + cell_h - frame.height,
                ),
            )

    alpha = np.array(sheet)[..., 3]
    quant = sheet.convert("RGB").quantize(
        colors=a.colors, method=Image.MEDIANCUT, dither=Image.NONE
    )
    out = np.array(quant.convert("RGBA"))
    out[..., 3] = np.where(alpha >= 128, 255, 0)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, "RGBA").save(a.out)
    print(
        f"wrote {a.out} ({sheet.width}x{sheet.height}, cell {cell_w}x{cell_h}, {a.colors} colors)"
    )


if __name__ == "__main__":
    main()
