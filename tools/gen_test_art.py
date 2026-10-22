"""Draws the art-quality test scene: terrain, props, a tree set, and a hero walk cycle.

Run: uv run --with pillow --with numpy python tools/gen_test_art.py
Output goes to assets/test_art/. Everything is seeded, so reruns are identical.
"""

import itertools
import random
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "assets" / "test_art"
W, H = 640, 352
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def c(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


GRASS = [c("3f7d3a"), c("52963f"), c("66ab47"), c("86c859")]
DIRT = [c("7d5a40"), c("9a7350"), c("b58f64"), c("cfae80")]
WATER = [c("25619f"), c("3478b8"), c("5aa0d8"), c("c4e8f7")]
SAND = [c("b79d62"), c("d3bb7e"), c("e8d59d")]
LEAF = [c("24582f"), c("33753a"), c("4b9444"), c("78bd55")]
BARK = [c("3d271f"), c("5f3f2e"), c("7e5a40")]
STONE = [c("4d5058"), c("6d727c"), c("949aa6"), c("b8bec9")]
OUTLINE = c("1f3a2b")


def new(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def smooth_noise(w, h, scale, seed):
    rng = np.random.default_rng(seed)
    g = rng.random((h // scale + 3, w // scale + 3))
    ys, xs = np.arange(h) / scale, np.arange(w) / scale
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = ys - y0, xs - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a, b = g[y0][:, x0], g[y0][:, x0 + 1]
    cc, d = g[y0 + 1][:, x0], g[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx[None, :]
    bot = cc + (d - cc) * fx[None, :]
    return top + (bot - top) * fy[:, None]


def fbm(scale, seed):
    n = (
        smooth_noise(W, H, scale, seed) * 0.65
        + smooth_noise(W, H, max(scale // 3, 2), seed + 1) * 0.35
    )
    return n


BAYER_FULL = np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W]


def banded(v, levels, spread=0.8):
    """Quantize 0..1 noise into `levels` tones with ordered dithering at the band edges."""
    idx = np.floor(v * levels + (BAYER_FULL - 0.5) * spread).astype(int)
    return np.clip(idx, 0, levels - 1)


def paint(arr, mask, palette, idx):
    pal = np.array(palette, dtype=np.uint8)
    arr[mask] = pal[idx[mask]]


def seg_dist(points):
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    best = np.full((H, W), 1e9)
    for (x0, y0), (x1, y1) in itertools.pairwise(points):
        dx, dy = x1 - x0, y1 - y0
        t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / (dx * dx + dy * dy), 0, 1)
        best = np.minimum(best, np.hypot(xx - (x0 + t * dx), yy - (y0 + t * dy)))
    return best


def edge(mask, dy=0, dx=0):
    """Pixels of `mask` whose neighbour at (dy, dx) is outside it."""
    return mask & ~np.roll(np.roll(mask, dy, axis=0), dx, axis=1)


def terrain(rng):
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    nrng = np.random.default_rng(5)
    # ground: calm, large patches of two greens with dithered borders
    g = banded(np.clip(fbm(34, 10) * 0.8 + 0.2, 0, 0.999), 3, 0.5)
    paint(arr, np.ones((H, W), bool), GRASS[:3], g)
    # sparse tufts: dark base pixel with a light tip
    for _ in range(420):
        x, y = rng.randrange(2, W - 2), rng.randrange(3, H - 1)
        arr[y, x] = GRASS[0]
        arr[y - 1, x] = GRASS[3]
        if rng.random() < 0.5:
            arr[y - 2, x + 1] = GRASS[3]
            arr[y - 1, x + 1] = GRASS[0]
    # path
    main = [(-10, 205), (140, 196), (270, 214), (380, 208), (520, 238), (650, 232)]
    branch = [(300, 212), (312, 150), (296, 96), (318, 30), (320, -10)]
    dist = np.minimum(seg_dist(main), seg_dist(branch) * 1.15)
    path = dist < 15 + (fbm(14, 20) - 0.5) * 9
    d = banded(np.clip(fbm(9, 30) * 1.1, 0, 0.999), 4, 0.9)
    shadow_lip = (np.roll(path, 1, 0) | np.roll(path, 2, 0)) & ~path
    arr[shadow_lip] = np.array(GRASS[0], dtype=np.uint8)
    paint(arr, path, DIRT, d)
    arr[edge(path, 1, 0)] = np.array(DIRT[3], dtype=np.uint8)
    arr[edge(path, -1, 0)] = np.array(DIRT[0], dtype=np.uint8)
    arr[edge(path, 0, 1) | edge(path, 0, -1)] = np.array(DIRT[1], dtype=np.uint8)
    border = path & (
        edge(path, 1, 0) | edge(path, -1, 0) | edge(path, 0, 1) | edge(path, 0, -1)
    )
    over = border & (nrng.random((H, W)) < 0.28)  # grass leaning over the lip
    arr[over] = np.array(GRASS[1], dtype=np.uint8)
    for _ in range(90):  # pebbles on the path
        x, y = rng.randrange(W), rng.randrange(H)
        if path[y, x] and not border[y, x] and x + 1 < W and path[y, x + 1]:
            arr[y, x] = DIRT[3]
            arr[y, x + 1] = DIRT[3]
            arr[y + 1, x] = DIRT[0]
            arr[y + 1, x + 1] = DIRT[0]
    # pond: warped ellipse, sand shore, dark rim, foam, depth dithering
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    r2 = ((xx - 500) / 92) ** 2 + ((yy - 88) / 52) ** 2
    warp = (fbm(22, 40) - 0.5) * 0.5
    pond = r2 < 1 + warp
    shore = (r2 < (1 + warp) * 1.42) & ~pond & ~path
    s = banded(np.clip(fbm(8, 50), 0, 0.999), 3, 0.8)
    paint(arr, shore, SAND, s)
    arr[
        edge(shore, 1, 0) | edge(shore, -1, 0) | edge(shore, 0, 1) | edge(shore, 0, -1)
    ] = np.array(SAND[0], dtype=np.uint8)
    sh_over = shore & (nrng.random((H, W)) < 0.12) & (r2 > (1 + warp) * 1.3)
    arr[sh_over] = np.array(GRASS[1], dtype=np.uint8)
    depth = np.clip(1.0 - r2, 0, 1)
    wv = banded(
        np.clip(
            0.55 + depth * 0.4 - 0.25 + 0.12 * np.sin(xx / 7.0 + yy / 5.0), 0, 0.999
        ),
        3,
        0.7,
    )
    paint(arr, pond, WATER[:3], 2 - wv)
    rim = edge(pond, 1, 0) | edge(pond, -1, 0) | edge(pond, 0, 1) | edge(pond, 0, -1)
    arr[rim] = np.array(WATER[0], dtype=np.uint8)
    inner = (
        np.roll(rim, 1, 0)
        | np.roll(rim, -1, 0)
        | np.roll(rim, 1, 1)
        | np.roll(rim, -1, 1)
    )
    foam = pond & inner & ~rim & (nrng.random((H, W)) < 0.35)
    arr[foam] = np.array(WATER[3], dtype=np.uint8)
    for _ in range(46):  # wave glints
        x, y = rng.randrange(W), rng.randrange(H)
        if pond[y, x] and not inner[y, x] and 4 < x < W - 8 and pond[y, x + 5]:
            for k in range(rng.randrange(3, 6)):
                arr[y, x + k] = WATER[2]
            arr[y, x + 2] = WATER[3]
    return arr, path, pond, shore


def shade_blob(w, h, circles, light, tones, rng, outline, rim_light=None):
    """Union of circles shaded by distance from a light point, dithered tone
    borders, and a 1px outline."""
    mask = {}
    for cx, cy, r in circles:
        for y in range(h):
            for x in range(w):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    dd = ((x - light[0]) ** 2 + (y - light[1]) ** 2) ** 0.5 / 22.0
                    dd += (
                        BAYER[y % 4, x % 4] * 0.14 - 0.07 + (rng.random() - 0.5) * 0.06
                    )
                    mask[(x, y)] = tones[
                        3 if dd < 0.28 else 2 if dd < 0.55 else 1 if dd < 0.82 else 0
                    ]
    im = new(w, h)
    px = im.load()
    for (x, y), col in mask.items():
        px[x, y] = col
    for x, y in list(mask):
        if any(
            (x + dx, y + dy) not in mask
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            px[x, y] = outline
    return im


def leaf_detail(im, rng):
    """Small light and dark leaf clumps so the canopy isn't smooth."""
    px = im.load()
    w, h = im.size
    for _ in range(46):
        x, y = rng.randrange(2, w - 3), rng.randrange(2, h - 3)
        if px[x, y][3] and px[x, y] in (LEAF[1], LEAF[2]):
            hi = px[x, y] == LEAF[2] and rng.random() < 0.6
            px[x, y] = LEAF[3] if hi else LEAF[0]
            if px[x + 1, y] == px[x, y] or px[x + 1, y][3] == 0:
                continue
            px[x + 1, y] = LEAF[3] if hi else LEAF[0]


def ground_shadow(im, cx, cy, rx, ry, alpha=64):
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                px[x, y] = (10, 20, 30, alpha)


def tree(seed):
    rng = random.Random(seed)
    im = new(44, 56)
    ground_shadow(im, 26, 51, 15, 4)
    px = im.load()
    for y in range(32, 52):  # trunk with flared roots
        flare = 1 if y > 46 else 0
        for x in range(18 - flare, 25 + flare):
            px[x, y] = BARK[1] if x < 22 else BARK[0]
            if x in (18 - flare, 24 + flare) or y == 51:
                px[x, y] = OUTLINE
    for y in (36, 37, 40, 44):
        px[20, y] = BARK[2]
    px[22, 42] = BARK[0]
    circles = [(22, 20, 15)]
    for _ in range(11):  # bumpy silhouette from many small lobes
        ang = rng.random() * 6.283
        rad = 11 + rng.random() * 6
        circles.append(
            (
                22 + int(np.cos(ang) * rad),
                22 + int(np.sin(ang) * rad * 0.8),
                rng.randrange(4, 8),
            )
        )
    canopy = shade_blob(44, 44, circles, (13, 9), LEAF, rng, OUTLINE)
    leaf_detail(canopy, rng)
    im.alpha_composite(canopy, (0, 0))
    return im


def bush(seed):
    rng = random.Random(seed)
    im = new(26, 18)
    ground_shadow(im, 14, 15, 10, 3, 56)
    b = shade_blob(
        26, 18, [(8, 10, 6), (14, 8, 7), (19, 11, 6)], (9, 4), LEAF, rng, OUTLINE
    )
    leaf_detail(b, rng)
    im.alpha_composite(b)
    return im


def rock(seed):
    rng = random.Random(seed)
    im = new(18, 12)
    ground_shadow(im, 10, 10, 7, 2, 56)
    im.alpha_composite(
        shade_blob(18, 12, [(7, 6, 5), (11, 7, 5)], (5, 3), STONE, rng, c("2a2d34"))
    )
    return im


def flowers(rng, kind):
    im = new(7, 7)
    px = im.load()
    for x, y in ((1, 3), (4, 2), (3, 5)):
        px[x, y + 1] = GRASS[0]
        px[x, y] = kind
        px[x - 1 if x > 0 else x, y] = kind if rng.random() < 0.5 else px[x, y]
    return im


def hero(frame=0):
    """16x32 front-facing hero. frame 0 idle, 1 and 3 mid-stride, 2 idle."""
    ol = c("2b1c2c")
    skin, skin_d, blush = c("f2cba3"), c("d6a07a"), c("e79a8c")
    hair, hair_d, hair_l = c("7a4a2b"), c("55301f"), c("a8703f")
    tun = [c("27468a"), c("3a62b0"), c("6f9be0")]
    belt, buckle = c("5a3a22"), c("f0c94c")
    pants, boot, boot_l = c("5d4b3b"), c("37271f"), c("55402f")
    up = new(16, 32)
    lg = new(16, 32)
    u, g = up.load(), lg.load()

    def rect(px, x0, y0, x1, y1, col):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                px[x, y] = col

    rect(u, 5, 1, 10, 1, hair)  # hair cap
    rect(u, 4, 2, 11, 3, hair)
    rect(u, 3, 4, 12, 8, hair)
    rect(u, 5, 1, 7, 1, hair_l)
    rect(u, 4, 2, 5, 3, hair_l)
    u[6, 2] = hair_l
    rect(u, 8, 3, 11, 3, hair_d)
    rect(u, 4, 5, 11, 12, skin)  # face
    for x in (4, 6, 8, 10):  # fringe
        rect(u, x, 4, x + 1, 5, hair)
    u[7, 5] = hair_d
    u[11, 5] = hair_d
    rect(u, 3, 9, 3, 11, hair_d)
    rect(u, 12, 9, 12, 11, hair_d)
    rect(u, 4, 6, 4, 8, hair)
    rect(u, 11, 6, 11, 8, hair_d)
    for x in (5, 10):  # eyes: dark with a white glint
        u[x, 8] = ol
        u[x, 9] = ol
    u[5, 8] = c("ffffff")
    u[10, 8] = c("ffffff")
    u[4, 10] = blush
    u[11, 10] = blush
    u[7, 11] = skin_d
    u[8, 11] = skin_d
    rect(u, 6, 13, 9, 13, skin_d)  # neck
    rect(u, 3, 14, 12, 23, tun[1])  # tunic
    rect(u, 3, 14, 4, 23, tun[2])
    rect(u, 11, 14, 12, 23, tun[0])
    rect(u, 6, 14, 9, 14, tun[2])  # collar
    u[7, 15] = tun[2]
    u[8, 15] = tun[2]
    rect(u, 3, 20, 12, 20, belt)
    u[7, 20] = buckle
    u[8, 20] = buckle
    rect(u, 2, 15, 2, 20, tun[2])  # arms
    rect(u, 13, 15, 13, 20, tun[0])
    u[2, 21] = skin
    u[13, 21] = skin_d
    rect(u, 3, 23, 12, 23, tun[0])  # hem
    rect(g, 4, 24, 11, 26, pants)  # legs
    g[7, 24] = c("45372b")
    g[8, 24] = c("45372b")
    lift_l = 1 if frame == 1 else 0
    lift_r = 1 if frame == 3 else 0
    rect(g, 4, 27, 7, 29 - lift_l, boot)  # boots
    rect(g, 8, 27, 11, 29 - lift_r, boot)
    g[4, 27] = boot_l
    g[5, 27] = boot_l
    g[8, 27] = boot_l
    g[9, 27] = boot_l
    bob = -1 if frame in (1, 3) else 0
    im = new(16, 32)
    im.alpha_composite(lg)
    im.alpha_composite(up, (0, bob))
    px = im.load()
    filled = {(x, y) for y in range(32) for x in range(16) if px[x, y][3]}
    for x, y in filled:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (nx, ny) not in filled and 0 <= nx < 16 and 0 <= ny < 32:
                px[nx, ny] = ol
    shadow = new(16, 32)
    ground_shadow(shadow, 8, 30, 6, 1.6, 70)
    shadow.alpha_composite(im)
    return shadow


def grade(arr):
    """Warm tint, dappled light, and a soft vignette over the finished frame."""
    rgb = arr[..., :3].astype(float)
    dapple = 1 + (smooth_noise(W, H, 56, 77) - 0.5) * 0.2
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    r2 = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    vig = 1 - 0.16 * np.clip(r2 - 0.25, 0, 1.2)
    rgb *= dapple[..., None] * vig[..., None] * np.array([1.04, 1.0, 0.94])
    arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return arr


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(11)
    arr, _path, pond, _shore = terrain(rng)
    base = Image.fromarray(arr, "RGBA")
    # lily pads on the pond
    for lx, ly in ((470, 80), (520, 100), (495, 66), (540, 74)):
        if pond[ly, lx]:
            pad = shade_blob(
                14, 9, [(7, 4, 5)], (4, 2), LEAF, random.Random(lx), OUTLINE
            )
            pad.putpixel((11, 4), (0, 0, 0, 0))
            base.alpha_composite(pad, (lx - 7, ly - 4))
    for fx, fy in (
        (140, 120),
        (210, 290),
        (410, 300),
        (90, 270),
        (560, 190),
        (250, 130),
        (600, 290),
    ):
        kind = rng.choice([c("f6e46e"), c("ffffff"), c("ea6b90")])
        base.alpha_composite(flowers(rng, kind), (fx, fy))
    objs = []
    for i, (tx, ty) in enumerate(
        [
            (60, 120),
            (150, 70),
            (240, 150),
            (400, 150),
            (590, 170),
            (110, 300),
            (430, 320),
            (610, 320),
            (345, 70),
        ]
    ):
        objs.append((tx, ty, tree(i), 22, 51))
    for i, (bx, by) in enumerate(
        [(195, 170), (360, 288), (55, 215), (570, 262), (265, 80)]
    ):
        objs.append((bx, by, bush(i), 13, 15))
    for i, (rx, ry) in enumerate([(120, 245), (455, 255), (330, 140)]):
        objs.append((rx, ry, rock(i), 9, 10))
    for fx, fy, im, ax, ay in sorted(objs, key=lambda o: o[1]):
        base.alpha_composite(im, (fx - ax, fy - ay))
    graded = Image.fromarray(grade(np.array(base)), "RGBA")
    graded.save(OUT / "demo_map.png")
    sheet = new(16 * 4, 32)
    for f in range(4):
        sheet.alpha_composite(hero(f), (f * 16, 0))
    sheet.save(OUT / "hero_walk.png")
    tree(0).save(OUT / "tree.png")
    print("wrote", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
