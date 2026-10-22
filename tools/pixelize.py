"""Turns a large AI-generated or painted image into game-ready pixel art.

Steps: optional background removal, optional crop to the sprite, block downscale
(to a target width, or by a fixed source block size), palette quantization (no
dithering), alpha cutoff, and an optional nearest-neighbor preview.

Run: uv run --with pillow --with numpy python tools/pixelize.py in.png out.png --width 32 --colors 16
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def remove_background(im: Image.Image, tolerance: int) -> Image.Image:
    """Make pixels transparent when they are close to the corner colour and
    connected to a corner (flood fill, so same-coloured interior detail stays)."""
    arr = np.array(im.convert("RGBA"))
    h, w = arr.shape[:2]
    key = arr[0, 0, :3].astype(int)
    near = np.abs(arr[..., :3].astype(int) - key).sum(axis=2) <= tolerance
    seen = np.zeros((h, w), bool)
    stack = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    while stack:
        y, x = stack.pop()
        if 0 <= y < h and 0 <= x < w and near[y, x] and not seen[y, x]:
            seen[y, x] = True
            stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    arr[seen, 3] = 0
    # Background pockets the flood fill cannot reach (between the legs) and the
    # generator's tinted drop shadow: drop pixels that point the same way as the key.
    kdir = key - key.mean()
    rgb = arr[..., :3].astype(float)
    pdir = rgb - rgb.mean(axis=2, keepdims=True)
    norm = np.linalg.norm(pdir, axis=2) * np.linalg.norm(kdir)
    cos = np.divide((pdir @ kdir), norm, out=np.zeros((h, w)), where=norm > 0)
    arr[(cos > 0.93) & (np.linalg.norm(pdir, axis=2) > 40), 3] = 0
    return Image.fromarray(arr, "RGBA")


def remap_key_tint(out: np.ndarray, key: np.ndarray) -> None:
    """Edge pixels the generator anti-aliased against the background carry its
    tint (dark purple outlines on a magenta key). Remap palette colours whose
    hue points the same way as the key to the nearest colour that doesn't."""
    kdir = key.astype(float) - key[:3].mean()
    pal = np.unique(out[out[..., 3] > 0][:, :3], axis=0).astype(float)
    cdir = pal - pal.mean(axis=1, keepdims=True)
    norm = np.linalg.norm(cdir, axis=1) * np.linalg.norm(kdir)
    cos = np.divide(cdir @ kdir, norm, out=np.zeros(len(pal)), where=norm > 0)
    tinted = (cos > 0.8) & (np.linalg.norm(cdir, axis=1) > 8)
    if tinted.all() or not tinted.any():
        return
    clean = pal[~tinted]
    for col in pal[tinted]:
        nearest = clean[np.argmin(np.abs(clean - col).sum(axis=1))].astype(np.uint8)
        hit = (out[..., :3] == col.astype(np.uint8)).all(axis=2) & (out[..., 3] > 0)
        out[hit, :3] = nearest


def pixelize(
    im: Image.Image,
    width: int,
    colors: int,
    alpha_cutoff: int,
    key: np.ndarray | None = None,
) -> Image.Image:
    im = im.convert("RGBA")
    height = max(1, round(im.height * width / im.width))
    # premultiplied alpha, so removed-background pixels don't tint the edge colours
    small = im.convert("RGBa").resize((width, height), Image.BOX).convert("RGBA")
    alpha = np.array(small)[..., 3]
    rgb = small.convert("RGB").quantize(
        colors=colors, method=Image.MEDIANCUT, dither=Image.NONE
    )
    out = np.array(rgb.convert("RGBA"))
    out[..., 3] = np.where(alpha >= alpha_cutoff, 255, 0)
    if key is not None:
        remap_key_tint(out, key)
    return Image.fromarray(out, "RGBA")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("src", type=Path)
    p.add_argument("dst", type=Path)
    size = p.add_mutually_exclusive_group(required=True)
    size.add_argument("--width", type=int, help="output width in pixels")
    size.add_argument(
        "--block",
        type=int,
        help="source pixels per output pixel; keeps every asset on the same pixel grid",
    )
    p.add_argument(
        "--crop",
        action="store_true",
        help="crop to the opaque area before downscaling (needs --remove-bg)",
    )
    p.add_argument("--colors", type=int, default=16, help="palette size")
    p.add_argument("--alpha-cutoff", type=int, default=128)
    p.add_argument(
        "--remove-bg",
        type=int,
        metavar="TOLERANCE",
        help="flood-remove the corner colour (sum of RGB differences)",
    )
    p.add_argument(
        "--preview",
        type=int,
        default=0,
        help="also write <dst>_xN.png upscaled with nearest-neighbor",
    )
    a = p.parse_args()

    im = Image.open(a.src)
    key = None
    if a.remove_bg is not None:
        key = np.array(im.convert("RGB"))[0, 0]
        im = remove_background(im, a.remove_bg)
    if a.crop:
        bbox = im.getchannel("A").getbbox()
        if bbox:
            im = im.crop(bbox)
    width = a.width or max(1, round(im.width / a.block))
    out = pixelize(im, width, a.colors, a.alpha_cutoff, key)
    a.dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(a.dst)
    if a.preview:
        big = out.resize((out.width * a.preview, out.height * a.preview), Image.NEAREST)
        big.save(a.dst.with_name(f"{a.dst.stem}_x{a.preview}.png"))
    print(f"wrote {a.dst} ({out.width}x{out.height}, {a.colors} colors)")


if __name__ == "__main__":
    main()
