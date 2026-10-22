"""Builds a water mask for the ground image: the sea (connected to the top edge) and
any extra pools given as seed points. Output is grayscale, 0 on land and rising to 255
with distance from the shore, so a shader can keep the shoreline calm and move open water.

Run: uv run --no-project --with pillow --with numpy --with scipy python tools/make_water_mask.py assets/beach/ground.png assets/beach/water_mask.png --seed 252,102 --seed 270,69
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

FALLOFF_PX = 14.0


def is_water(rgb: np.ndarray, green_margin: int) -> np.ndarray:
    r, b = rgb[..., 0].astype(int), rgb[..., 2].astype(int)
    g = rgb[..., 1].astype(int)
    bluish = (b > r + 6) & (g > r + green_margin)  # excludes blue-grey rocks
    foam = (rgb.min(axis=2) > 150) & (np.abs(b - r) < 40)
    return bluish | foam


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("src", type=Path)
    p.add_argument("dst", type=Path)
    p.add_argument(
        "--green-margin",
        type=int,
        default=12,
        help="how much greener than red water must be (lower for dark seas)",
    )
    p.add_argument(
        "--seed", action="append", default=[], help="x,y pixel inside a pool"
    )
    a = p.parse_args()

    rgb = np.array(Image.open(a.src).convert("RGB"))
    labels, _ = ndimage.label(is_water(rgb, a.green_margin))
    keep = {labels[0, x] for x in range(rgb.shape[1]) if labels[0, x]}
    for seed in a.seed:
        x, y = (int(v) for v in seed.split(","))
        if labels[y, x]:
            keep.add(labels[y, x])
    water = np.isin(labels, list(keep))
    water = ndimage.binary_closing(water, iterations=1)
    dist = ndimage.distance_transform_edt(water)
    mask = np.clip(dist / FALLOFF_PX, 0.0, 1.0) * 255
    mask[water & (mask < 40)] = (
        40  # edge water still moves a little, so the foam line breathes
    )
    Image.fromarray(mask.astype(np.uint8), "L").save(a.dst)
    print(f"wrote {a.dst}: {water.mean():.1%} of pixels are water")


if __name__ == "__main__":
    main()
