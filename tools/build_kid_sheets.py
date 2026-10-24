"""Builds the village-kid sprite sheets from the Gemini kid sources and recolours them.

Sources in --src-dir (assets/source/gemini/kids/, git-ignored):
  sheet.jpeg   10 poses on magenta, reading order: 0-1 walk facing right, 2 front idle (three-quarter),
               3-4 walk facing left, 5-6 walk from behind, 7 idle from behind, 8-9 walk facing front.
  idle_a.jpeg  side idle facing left;  idle_b.jpeg  side idle facing right.

Output: four 384x512 sheets (96x128 cells, rows down/up/left/right, columns idle/stride A/idle/stride B, the
same layout as the hero and NPC sheets) named kid_a..kid_d.png in --out-dir. The kid is 44 art pixels tall
(the hero is about 61), each art pixel is 2x2 texture pixels like the hero's, and feet sit at the cell bottom.
Variants swap hair, tunic and skin by colour class, so boots, belt, trousers and outlines stay put.

Run: uv run --no-project --with pillow --with numpy python tools/build_kid_sheets.py --src-dir assets/source/gemini/kids --out-dir assets/npc
"""

import argparse
import colorsys
from pathlib import Path

import numpy as np
from PIL import Image
from pixelize import remove_background

KID_ART_HEIGHT = 44
UPSCALE = 2
CELL_W, CELL_H = 96, 128
FEET_MARGIN = 2

# Pose index in sheet.jpeg -> (row, column)
SHEET_POSES = {
    "down": (2, 8, 9),  # idle, stride A, stride B
    "up": (7, 5, 6),
    "left": (None, 3, 4),  # idle comes from idle_a.jpeg
    "right": (None, 0, 1),  # idle comes from idle_b.jpeg
}

VARIANTS = {
    "a": None,
    "b": {"hair": (0.86, 0.70, 0.38), "tunic": (0.62, 0.30, 0.22), "skin": (0.93, 0.80, 0.70)},
    "c": {"hair": (0.16, 0.14, 0.15), "tunic": (0.33, 0.42, 0.28), "skin": (0.66, 0.45, 0.32)},
    "d": {"hair": (0.65, 0.28, 0.14), "tunic": (0.28, 0.36, 0.52), "skin": (0.82, 0.60, 0.45)},
}


def runs(flags: np.ndarray) -> list[tuple[int, int]]:
    idx = np.where(flags)[0]
    out, start, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i > prev + 3:
            out.append((start, prev))
            start = i
        prev = i
    out.append((start, prev))
    return out


def split_sheet(path: Path, tolerance: int) -> list[Image.Image]:
    im = remove_background(Image.open(path).convert("RGB"), tolerance)
    alpha = np.array(im)[..., 3] > 128
    figs = []
    for y0, y1 in runs(alpha.any(axis=1)):
        for x0, x1 in runs(alpha[y0 : y1 + 1].any(axis=0)):
            figs.append(im.crop((x0, y0, x1 + 1, y1 + 1)))
    if len(figs) != 10:
        raise SystemExit(f"expected 10 poses in {path}, found {len(figs)}")
    return figs


def load_single(path: Path, tolerance: int) -> Image.Image:
    im = remove_background(Image.open(path).convert("RGB"), tolerance)
    return im.crop(im.getchannel("A").getbbox())


def to_art(im: Image.Image, scale: float) -> Image.Image:
    size = (max(1, round(im.width * scale)), max(1, round(im.height * scale)))
    return im.convert("RGBa").resize(size, Image.BOX).convert("RGBA")


def place(sheet: Image.Image, art: Image.Image, col: int, row: int) -> None:
    big = art.resize((art.width * UPSCALE, art.height * UPSCALE), Image.NEAREST)
    x = col * CELL_W + (CELL_W - big.width) // 2
    y = row * CELL_H + CELL_H - FEET_MARGIN - big.height
    sheet.alpha_composite(big, (x, y))


def build_base(src_dir: Path, colors: int, tolerance: int) -> Image.Image:
    figs = split_sheet(src_dir / "sheet.jpeg", tolerance)
    sheet_scale = KID_ART_HEIGHT / figs[7].height
    singles = {
        "left": load_single(src_dir / "idle_a.jpeg", tolerance),
        "right": load_single(src_dir / "idle_b.jpeg", tolerance),
    }
    sheet = Image.new("RGBA", (CELL_W * 4, CELL_H * 4), (0, 0, 0, 0))
    for row, direction in enumerate(["down", "up", "left", "right"]):
        idle_i, a_i, b_i = SHEET_POSES[direction]
        if idle_i is None:
            idle = to_art(singles[direction], KID_ART_HEIGHT / singles[direction].height)
        else:
            idle = to_art(figs[idle_i], sheet_scale)
        stride_a = to_art(figs[a_i], sheet_scale)
        stride_b = to_art(figs[b_i], sheet_scale)
        for col, frame in enumerate([idle, stride_a, idle, stride_b]):
            place(sheet, frame, col, row)
    alpha = np.array(sheet)[..., 3]
    quant = sheet.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE)
    out = np.array(quant.convert("RGBA"))
    out[..., 3] = np.where(alpha >= 128, 255, 0)
    return Image.fromarray(out, "RGBA")


def recolour(base: Image.Image, target: dict[str, tuple[float, float, float]]) -> Image.Image:
    """Swaps hair, tunic and skin. Classes: tunic is low-saturation mid-grey; in the top 42% of each cell's
    figure, dark brown is hair and light warm is skin; light warm below the head is hands and legs."""
    arr = np.array(base).astype(float) / 255.0
    out = arr.copy()
    for row in range(4):
        for col in range(4):
            cell = arr[row * CELL_H : (row + 1) * CELL_H, col * CELL_W : (col + 1) * CELL_W]
            opaque = cell[..., 3] > 0.5
            if not opaque.any():
                continue
            ys = np.where(opaque.any(axis=1))[0]
            head_limit = ys.min() + 0.42 * (ys.max() - ys.min())
            rgb = cell[..., :3]
            hsv = np.array([[colorsys.rgb_to_hsv(*px) for px in line] for line in rgb])
            sat, val = hsv[..., 1], hsv[..., 2]
            yy = np.arange(CELL_H)[:, None] * np.ones((1, CELL_W))
            warm = (hsv[..., 0] < 0.12) & (sat > 0.2)
            tunic = opaque & (sat < 0.2) & (val > 0.28) & (val < 0.8)
            skin = opaque & warm & (val >= 0.58)
            hair = opaque & warm & (val < 0.58) & (yy < head_limit)
            luma = rgb @ np.array([0.299, 0.587, 0.114])
            region = out[row * CELL_H : (row + 1) * CELL_H, col * CELL_W : (col + 1) * CELL_W]
            for mask, key in ((tunic, "tunic"), (skin, "skin"), (hair, "hair")):
                if mask.any():
                    ref = luma[mask].mean()
                    tint = np.array(target[key])
                    region[mask, :3] = np.clip(tint * (luma[mask, None] / ref), 0, 1)
    return Image.fromarray((out * 255).round().astype(np.uint8), "RGBA")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src-dir", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--colors", type=int, default=22)
    p.add_argument("--tolerance", type=int, default=160)
    a = p.parse_args()

    base = build_base(a.src_dir, a.colors, a.tolerance)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    for key, target in VARIANTS.items():
        sheet = base if target is None else recolour(base, target)
        path = a.out_dir / f"kid_{key}.png"
        sheet.save(path)
        print(f"wrote {path} ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    main()
