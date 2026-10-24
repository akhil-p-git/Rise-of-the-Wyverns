"""Builds all game-ready high-density pixel art assets from raw Gemini images and kitbashed components.

All characters, buildings, and props are built at 4x world texel density (rendered at scale 0.25 in
Godot's canvas_items stretch mode), and ground maps at 1280x720 / 1280x840, preserving full native
pixel-art sharpness in fullscreen.

Run: python3 tools/build_all_art.py
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from pixelize import remove_background

ROOT = Path(__file__).resolve().parent.parent

NEW_RAW = ROOT / "assets" / "source" / "gemini" / "new"
OLD_BEACH_RAW = ROOT / "assets" / "source" / "gemini" / "beach"
INTRO_RAW = ROOT / "assets" / "source" / "gemini" / "intro"


def clean_rgba(im: Image.Image, tolerance: int = 165) -> Image.Image:
    """Removes background and neutralizes any magenta/purple anti-aliased fringe pixels
    without destructive low-color palette quantization."""
    rgba = remove_background(im, tolerance)
    arr = np.array(rgba).astype(int)
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    purple_excess = np.minimum(r, b) - g
    is_halo = (a > 0) & (purple_excess > 35) & (r > 95) & (b > 95)
    arr[is_halo, 3] = 0
    a = arr[..., 3]
    is_tinted_edge = (a > 0) & (purple_excess > 18)
    luma = ((0.299 * r + 0.587 * g + 0.114 * b) * 0.65).astype(int)
    arr[is_tinted_edge, 0] = np.clip(luma[is_tinted_edge], 16, 80)
    arr[is_tinted_edge, 1] = np.clip(luma[is_tinted_edge] - 2, 14, 78)
    arr[is_tinted_edge, 2] = np.clip(luma[is_tinted_edge] + 2, 18, 84)
    arr[..., 3] = np.where(arr[..., 3] >= 128, 255, 0)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def strip_sand_island(im: Image.Image) -> Image.Image:
    """Removes pale beige sand stickers around the bottom of beach props while preserving
    darker wood, stone, iron, and outlines."""
    arr = np.array(im.convert("RGBA"))
    h, w = arr.shape[:2]
    r, g, b, a = (
        arr[..., 0].astype(int),
        arr[..., 1].astype(int),
        arr[..., 2].astype(int),
        arr[..., 3].astype(int),
    )
    is_pale_sand = (
        (a > 0) & (r > 150) & (g > 138) & (b > 95) & (r >= g - 6) & (g >= b + 12)
    )
    arr[is_pale_sand, 3] = 0
    yy = np.arange(h)[:, None]
    is_ground_shadow = (
        (yy > int(h * 0.65))
        & (arr[..., 3] > 0)
        & (r > 70)
        & (r < 120)
        & (g > 60)
        & (g < 105)
        & (b > 42)
        & (b < 80)
        & (np.abs(r - g) < 18)
        & ((r - b) > 15)
    )
    arr[is_ground_shadow, 3] = 0
    for _ in range(3):
        alpha = arr[..., 3] > 0
        for y in range(int(h * 0.58), h):
            for x in range(w):
                if alpha[y, x]:
                    nbrs = (
                        int(
                            alpha[
                                max(0, y - 1) : min(h, y + 2),
                                max(0, x - 1) : min(w, x + 2),
                            ].sum()
                        )
                        - 1
                    )
                    if nbrs <= 2:
                        arr[y, x, 3] = 0
    return Image.fromarray(arr, "RGBA")


def resize_crisp_rgba(im: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resizes an RGBA pixel-art sprite to (target_w, target_h) preserving sharp pixel edges
    and clean binary alpha."""
    im = im.convert("RGBA")
    # Snap via nearest-neighbor so existing pixel-art blocks and 1px outlines stay razor-sharp
    out = im.resize((target_w, target_h), Image.NEAREST)
    arr = np.array(out)
    arr[..., 3] = np.where(arr[..., 3] >= 128, 255, 0)
    return Image.fromarray(arr, "RGBA")


def save_sprite(
    im: Image.Image,
    dst: Path,
    world_width: int,
    strip_sand: bool = False,
    scale_factor: int = 4,
) -> Image.Image:
    rgba = clean_rgba(im, 165)
    if strip_sand:
        rgba = strip_sand_island(rgba)
    bbox = rgba.getchannel("A").getbbox()
    if bbox:
        rgba = rgba.crop(bbox)
    target_w = world_width * scale_factor
    target_h = max(scale_factor, round(rgba.height * target_w / rgba.width))
    out = resize_crisp_rgba(rgba, target_w, target_h)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    print(f"wrote {dst.relative_to(ROOT)} ({out.width}x{out.height})")
    return out


def _build_grass_tile_layer(tw: int, th: int, base_rgb: np.ndarray) -> np.ndarray:
    """Synthesizes a true 1:1 pixel-art meadow grass & moss layer at 4x world resolution
    (4 texels per world unit). Uses multi-pixel (2-3px wide, 6-9px tall) shaded grass blade
    clusters, clover rosettes, and wildflowers with clean 1px dark pine bases—zero 1px noise
    and zero 8x8 blocky upscaling."""
    # Smooth macro lighting from base_rgb so forest shadows and sunlit clearings are preserved
    macro_pil = (
        Image.fromarray(base_rgb.astype(np.uint8), "RGB")
        .resize((max(16, tw // 32), max(16, th // 32)), Image.BILINEAR)
        .resize((tw, th), Image.BILINEAR)
    )
    macro = np.array(macro_pil, dtype=np.float32)
    macro_lum = 0.299 * macro[..., 0] + 0.587 * macro[..., 1] + 0.114 * macro[..., 2]
    # Normalize shade factor around 1.0 (clamped 0.72 .. 1.24)
    shade = np.clip(macro_lum / 58.0, 0.72, 1.24)[..., None]

    # Build a 256x256 seamless pixel-art grass tile in PIL, then tile across (tw, th)
    tile_sz = 256
    tile = Image.new("RGB", (tile_sz, tile_sz), (34, 60, 32))
    px = tile.load()
    rng = np.random.default_rng(421337)

    # 1. Soft organic moss patches (12-24px across) on the base turf
    for _ in range(140):
        cx = int(rng.integers(0, tile_sz))
        cy = int(rng.integers(0, tile_sz))
        rx = int(rng.integers(8, 22))
        ry = int(rng.integers(6, 16))
        col = (28, 52, 28) if rng.random() < 0.55 else (40, 70, 36)
        for dy in range(-ry, ry + 1):
            for dx in range(-rx, rx + 1):
                if (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0:
                    px[(cx + dx) % tile_sz, (cy + dy) % tile_sz] = col

    # 2. Hand-crafted pixel-art grass blade clusters (2px wide blades, 6-9px tall, 1px dark base)
    # Each tuft is a coherent pixel-art sprite matching the Hero/Building pixel scale
    for _ in range(720):
        cx = int(rng.integers(0, tile_sz))
        cy = int(rng.integers(0, tile_sz))
        n_blades = int(rng.integers(3, 6))
        span = (n_blades - 1) * 3
        start_x = cx - span // 2
        for b_i in range(n_blades):
            bx = start_x + b_i * 3
            bh = int(rng.integers(5, 9))
            lean = -1 if b_i < n_blades // 2 else (1 if b_i > n_blades // 2 else 0)
            # 1px dark pine root shadow at base
            for w_off in range(2):
                px[(bx + w_off) % tile_sz, (cy + 1) % tile_sz] = (18, 34, 20)
                px[(bx + w_off) % tile_sz, cy % tile_sz] = (24, 44, 24)
            # Upward blade body (2px wide at bottom, tapering to 1-2px at tip)
            for dy in range(1, bh + 1):
                cur_x = bx + (lean if dy >= bh // 2 else 0)
                if dy <= 2:
                    bcol = (32, 58, 30)
                    w_max = 2
                elif dy < bh - 1:
                    bcol = (46, 80, 38)
                    w_max = 2
                else:
                    bcol = (64, 102, 48)
                    w_max = 1 if dy == bh else 2
                for w_off in range(w_max):
                    px[(cur_x + w_off) % tile_sz, (cy - dy) % tile_sz] = bcol

    # 3. Hand-crafted pixel-art 4-leaf clover rosettes (8x8 texels)
    leaf_offsets = [(-2, -2), (2, -2), (-2, 2), (2, 2)]
    for _ in range(55):
        cx = int(rng.integers(0, tile_sz))
        cy = int(rng.integers(0, tile_sz))
        for ox, oy in leaf_offsets:
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    x0 = (cx + ox + dx) % tile_sz
                    y0 = (cy + oy + dy) % tile_sz
                    if abs(dx) == 1 and abs(dy) == 1:
                        px[x0, y0] = (20, 38, 22)
                    elif dy == -1:
                        px[x0, y0] = (70, 110, 52)
                    else:
                        px[x0, y0] = (50, 86, 42)
        px[cx % tile_sz, cy % tile_sz] = (22, 40, 22)

    # 4. Crisp pixel-art wildflowers (6x6 texels with 2x2 petals and 1px dark stem)
    for _ in range(28):
        cx = int(rng.integers(0, tile_sz))
        cy = int(rng.integers(0, tile_sz))
        is_blue = rng.random() < 0.45
        p_hi = (145, 192, 235) if is_blue else (232, 236, 224)
        p_lo = (98, 146, 196) if is_blue else (188, 196, 184)
        # Stem shadow
        for dy in range(1, 4):
            px[cx % tile_sz, (cy + dy) % tile_sz] = (20, 38, 22)
        # 4 petals around center
        for ox, oy in ((0, -2), (0, 2), (-2, 0), (2, 0)):
            px[(cx + ox) % tile_sz, (cy + oy) % tile_sz] = p_hi
            px[(cx + ox + 1) % tile_sz, (cy + oy) % tile_sz] = p_lo
        # Golden center
        px[cx % tile_sz, cy % tile_sz] = (238, 192, 62)
        px[(cx + 1) % tile_sz, cy % tile_sz] = (196, 148, 42)

    terrain_dir = ROOT / "assets" / "terrain"
    terrain_dir.mkdir(parents=True, exist_ok=True)
    tile.save(terrain_dir / "grass_tile.png")
    tile_arr = np.array(tile, dtype=np.float32)
    reps_y = (th + tile_sz - 1) // tile_sz
    reps_x = (tw + tile_sz - 1) // tile_sz
    tiled = np.tile(tile_arr, (reps_y, reps_x, 1))[:th, :tw]
    return np.clip(tiled * shade, 10.0, 245.0)


def _build_cobble_layer(tw: int, th: int) -> np.ndarray:
    """Loads or builds the organic Voronoi cobblestone tile (`assets/terrain/cobble_tile.png`)
    and tiles it across (tw, th)."""
    from build_modular_art import build_organic_terrain_tiles

    cob_path = ROOT / "assets" / "terrain" / "cobble_tile.png"
    if not cob_path.exists():
        build_organic_terrain_tiles()
    tile_arr = np.array(Image.open(cob_path).convert("RGB"), dtype=np.float32)
    tile_sz = tile_arr.shape[0]
    reps_y = (th + tile_sz - 1) // tile_sz
    reps_x = (tw + tile_sz - 1) // tile_sz
    return np.tile(tile_arr, (reps_y, reps_x, 1))[:th, :tw]


def _build_dirt_layer(tw: int, th: int, base_rgb: np.ndarray) -> np.ndarray:
    """Loads or builds the organic dirt & polygonal rubble tile (`assets/terrain/dirt_rubble_tile.png`)
    and tiles it across (tw, th) modulated by smooth road shading."""
    from build_modular_art import build_organic_terrain_tiles

    dirt_path = ROOT / "assets" / "terrain" / "dirt_rubble_tile.png"
    if not dirt_path.exists():
        build_organic_terrain_tiles()
    macro_pil = (
        Image.fromarray(base_rgb.astype(np.uint8), "RGB")
        .resize((max(16, tw // 24), max(16, th // 24)), Image.BILINEAR)
        .resize((tw, th), Image.BILINEAR)
    )
    macro = np.array(macro_pil, dtype=np.float32)
    macro_lum = 0.299 * macro[..., 0] + 0.587 * macro[..., 1] + 0.114 * macro[..., 2]
    shade = np.clip(macro_lum / 108.0, 0.84, 1.14)[..., None]

    tile_arr = np.array(Image.open(dirt_path).convert("RGB"), dtype=np.float32)
    tile_sz = tile_arr.shape[0]
    reps_y = (th + tile_sz - 1) // tile_sz
    reps_x = (tw + tile_sz - 1) // tile_sz
    tiled = np.tile(tile_arr, (reps_y, reps_x, 1))[:th, :tw]
    return np.clip(tiled * shade, 16.0, 235.0)


def sharpen_ground(
    im: Image.Image,
    world_size: tuple[int, int],
    grim_grade: bool = False,
    add_micro_detail: bool = True,
    scale_factor: int = 4,
    mode: str = "town",
) -> Image.Image:
    """Produces a true 4x-density (4 texels per world unit) pixel-art ground map.
    Replaces stretched low-res grass, dirt, and cobblestones with native 1:1 pixel-art
    terrain layers while preserving landmarks (tide pools, waves, cairns, scorched ash)."""
    ww, wh = world_size
    tw, th = ww * scale_factor, wh * scale_factor
    rgb = im.convert("RGB")
    if grim_grade:
        arr0 = np.array(rgb).astype(float)
        r0, g0, b0 = arr0[..., 0], arr0[..., 1], arr0[..., 2]
        is_green0 = (g0 > r0 * 1.06) & (g0 > b0 * 1.10)
        arr0[is_green0, 0] = np.clip(r0[is_green0] * 0.84 + 6, 0, 255)
        arr0[is_green0, 1] = np.clip(g0[is_green0] * 0.72 + 4, 0, 255)
        arr0[is_green0, 2] = np.clip(b0[is_green0] * 0.86 + 8, 0, 255)
        arr0 = np.clip((arr0 - 108.0) * 1.16 + 100.0, 10, 248)
        rgb = Image.fromarray(arr0.astype(np.uint8), "RGB")

    if not add_micro_detail:
        rgb_sharp = rgb.filter(
            ImageFilter.UnsharpMask(radius=1.4, percent=200, threshold=2)
        )
        mid = rgb_sharp.resize((ww * 2, wh * 2), Image.LANCZOS)
        quant = mid.quantize(
            colors=64, method=Image.FASTOCTREE, dither=Image.NONE
        ).convert("RGBA")
        return quant.resize((tw, th), Image.NEAREST)

    # Smoothly upscale source to (tw, th) for clean contour masks (zero 8x8 stair-stepping)
    smooth_pil = rgb.resize((tw, th), Image.BICUBIC)
    base_arr = np.array(smooth_pil, dtype=np.float32)

    # Also build a crisp edge-sharpened version of the source for landmarks (waves, cliffs, ash, cairns)
    landmark_pil = rgb.filter(
        ImageFilter.UnsharpMask(radius=1.5, percent=220, threshold=2)
    ).resize((ww * 2, wh * 2), Image.LANCZOS)
    landmark_pil = landmark_pil.filter(
        ImageFilter.UnsharpMask(radius=0.8, percent=160, threshold=2)
    ).resize((tw, th), Image.NEAREST)
    landmark_arr = np.array(landmark_pil, dtype=np.float32)

    yy, xx = np.mgrid[0:th, 0:tw]

    # Classify terrain masks using a heavily smoothed version of the source so pebbles/flowers
    # inside a road or meadow never punch holes that fall back to the low-res source image!
    zone_pil = rgb.resize((max(32, ww // 6), max(32, wh // 6)), Image.BILINEAR).resize(
        (tw, th), Image.BICUBIC
    )
    z_arr = np.array(zone_pil, dtype=np.float32)
    zr, zg, zb = z_arr[..., 0], z_arr[..., 1], z_arr[..., 2]
    zlum = 0.299 * zr + 0.587 * zg + 0.114 * zb

    wx = xx / float(scale_factor)
    wy = yy / float(scale_factor)

    # Synthesize 1:1 4x pixel-art layers
    grass_layer = _build_grass_tile_layer(tw, th, base_arr)
    dirt_layer = _build_dirt_layer(tw, th, base_arr)
    cobble_layer = _build_cobble_layer(tw, th)

    is_Plaza_curb = np.zeros((th, tw), dtype=bool)

    if mode == "wrackmouth":
        # Clean geometric oval for the central town plaza (centered at world 320, 206)
        plaza_dist = ((wx - 320.0) / 60.0) ** 2 + ((wy - 206.0) / 64.0) ** 2
        is_cobble = plaza_dist <= 1.0
        is_Plaza_curb = np.zeros((th, tw), dtype=bool)

        # Smooth road mask covers the 4 dirt roads + plaza apron without any pebble holes
        is_dirt_zone = (zg < zr * 1.03) & (zr > zb + 6.0)
        is_cairn_path = (wx < 105.0) & (wy > 325.0) & (zg < zr * 1.04)
        is_dirt = (
            is_dirt_zone | is_cairn_path | ((plaza_dist > 1.0) & (plaza_dist <= 1.24))
        ) & (~is_cobble)
        is_grass = (~is_cobble) & (~is_dirt)

        out = grass_layer.copy()
        out[is_dirt] = dirt_layer[is_dirt]
        out[is_cobble] = cobble_layer[is_cobble]

        from build_modular_art import build_plaza_circle_asset

        plaza_path = ROOT / "assets" / "props" / "plaza_circle.png"
        plaza_im = (
            Image.open(plaza_path).convert("RGBA")
            if plaza_path.exists()
            else build_plaza_circle_asset(cobble_layer[:256, :256])
        )
        out_rgba = Image.fromarray(
            np.clip(out, 8.0, 248.0).astype(np.uint8), "RGB"
        ).convert("RGBA")
        px_off = int(320 * scale_factor - plaza_im.width // 2)
        py_off = int(206 * scale_factor - plaza_im.height // 2)
        out_rgba.alpha_composite(plaza_im, (px_off, py_off))
        out = np.array(out_rgba.convert("RGB"), dtype=np.float32)

    elif mode == "crossholm":
        # Cobblestone king's road band runs horizontally (world y in 172..224)
        in_kings_road = (wy >= 172.0) & (wy <= 224.0)
        # Smooth north dirt track mask
        is_dirt_track = (
            (wx >= 250.0)
            & (wx <= 380.0)
            & (wy >= 28.0)
            & (wy <= 190.0)
            & (zr > zg + 3.0)
            & (zlum > 42.0)
        )
        is_cobble = in_kings_road & (~((wy < 184.0) & is_dirt_track))
        is_Plaza_curb = (
            in_kings_road
            & (((wy >= 172.0) & (wy <= 176.0)) | ((wy >= 220.0) & (wy <= 224.0)))
            & (~is_dirt_track)
        )
        is_dirt = is_dirt_track & (~is_cobble)

        # Preserve only the wyvern-scorched black ash crater (top center) and dark slate rock crags
        ash_dist = (
            ((wx - 332.0) / 88.0) ** 2
            + ((wy - 56.0) / 52.0) ** 2
            + 0.14 * np.sin(wx * 0.11) * np.cos(wy * 0.13)
        )
        in_ash_crater = (ash_dist <= 1.0) & (~is_dirt)
        in_ash_rim = (ash_dist > 0.82) & (ash_dist <= 1.08) & (~is_dirt)
        is_grass = (~is_cobble) & (~is_dirt) & (~in_ash_crater)

        out = grass_layer.copy()
        out[is_dirt] = dirt_layer[is_dirt]
        out[is_cobble] = cobble_layer[is_cobble]

        # Synthesize crisp 1:1 pixel-art scorched ash & glowing wyvern embers in the crater
        ash_base = dirt_layer * 0.34
        ash_base[..., 2] += 4.0
        ember_hash = (
            ((xx // 2) * 374761393 + (yy // 2) * 668265263) ^ 0x5BF03635
        ) & 0xFFFF
        is_ember = in_ash_crater & (ember_hash < 520)
        is_ember_core = in_ash_crater & (ember_hash < 160)
        out[in_ash_crater] = np.clip(ash_base[in_ash_crater], 14.0, 68.0)
        out[in_ash_rim] = np.clip(out[in_ash_rim] * 0.58, 16.0, 95.0)
        out[is_ember] = [215.0, 78.0, 24.0]
        out[is_ember_core] = [252.0, 168.0, 46.0]

    else:
        # Beach: preserve ocean, pools, and rock rings; upgrade sand, stone path, and coastal grass
        pool_w = ((wx - 66.0) / 34.0) ** 2 + ((wy - 110.0) / 26.0) ** 2 <= 1.0
        pool_e = ((wx - 250.0) / 34.0) ** 2 + ((wy - 78.0) / 24.0) ** 2 <= 1.0
        is_cobble = (wy > 122.0) & (wx > 128.0) & (wx < 172.0) & (zg < zr * 1.06)
        is_grass = (wy > 105.0) & (zg > zr + 4.0) & (~is_cobble) & (~pool_w) & (~pool_e)
        is_sand = (
            (wy > 54.0)
            & (~is_grass)
            & (~is_cobble)
            & (~pool_w)
            & (~pool_e)
            & (zlum > 48.0)
            & (zlum < 145.0)
            & (np.abs(zr - zg) < 22.0)
        )
        # Synthesize crisp 1:1 dark volcanic coastal sand & shingle layer from dirt_layer
        sand_layer = dirt_layer.copy()
        sand_lum = (
            0.299 * sand_layer[..., 0]
            + 0.587 * sand_layer[..., 1]
            + 0.114 * sand_layer[..., 2]
        )
        sand_layer[..., 0] = np.clip(sand_lum * 0.88 + 6.0, 28.0, 175.0)
        sand_layer[..., 1] = np.clip(sand_lum * 0.88 + 6.0, 28.0, 175.0)
        sand_layer[..., 2] = np.clip(sand_lum * 0.84 + 8.0, 28.0, 170.0)

        out = landmark_arr.copy()
        out[is_sand] = sand_layer[is_sand]
        out[is_cobble] = cobble_layer[is_cobble]
        out[is_grass] = grass_layer[is_grass]

    # Draw crisp stone curb bevel on Plaza / King's Road border
    if np.any(is_Plaza_curb):
        angle_joint = (
            ((np.arctan2(wy - 206.0, wx - 320.0) * 18.0) % 1.0 < 0.08)
            if mode == "wrackmouth"
            else ((xx % 32) < 2)
        )
        curb_body = is_Plaza_curb & (~angle_joint)
        curb_mortar = is_Plaza_curb & angle_joint
        out[curb_body] = [118.0, 122.0, 126.0]
        out[curb_mortar] = [32.0, 34.0, 38.0]

    # Add a 2px dark earth undercut shadow + overhanging 2px pixel-art grass blades at grass borders
    grass_up = np.roll(is_grass, 3, axis=0)
    grass_dn = np.roll(is_grass, -3, axis=0)
    grass_lf = np.roll(is_grass, 3, axis=1)
    grass_rt = np.roll(is_grass, -3, axis=1)
    border = (~is_grass) & (grass_up | grass_dn | grass_lf | grass_rt)
    # Deterministic 2px grass teeth along border
    tooth = (((xx // 2) * 374761393 + (yy // 2) * 668265263) & 3) < 2
    out[border & tooth] = [36.0, 66.0, 34.0]
    out[border & (~tooth)] *= 0.72

    out = np.clip(out, 8.0, 248.0).astype(np.uint8)
    return Image.fromarray(out, "RGB").convert("RGBA")


def build_grounds_and_intro() -> None:
    # 1. Beach ground (1280x720 = 4x of 320x180 world, scale=0.25)
    beach_src = Image.open(NEW_RAW / "beach_ground_png_1792624473688.jpg")
    beach_out = sharpen_ground(
        beach_src, (320, 180), grim_grade=False, scale_factor=4, mode="beach"
    )
    beach_dst = ROOT / "assets" / "beach" / "ground.png"
    beach_out.save(beach_dst)
    print(f"wrote {beach_dst.relative_to(ROOT)} ({beach_out.width}x{beach_out.height})")

    # Build water mask at 320x180 for beach shader (UV-mapped 0..1)
    beach_small = beach_out.resize((320, 180), Image.BILINEAR)
    rgb = np.array(beach_small.convert("RGB")).astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    water = ((b > r + 10) & (g > r + 5)) | (
        (rgb.min(axis=2) > 155) & (np.abs(b - r) < 45)
    )
    h, w = water.shape
    yy, xx = np.mgrid[0:h, 0:w]
    ocean_zone = yy < 66
    pool_west = ((xx - 66) / 28.0) ** 2 + ((yy - 110) / 22.0) ** 2 <= 1.0
    pool_east = ((xx - 250) / 28.0) ** 2 + ((yy - 78) / 20.0) ** 2 <= 1.0
    valid_water = water & (ocean_zone | pool_west | pool_east)
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[valid_water] = 180
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if valid_water[y, x] and not (
                valid_water[y - 1, x]
                and valid_water[y + 1, x]
                and valid_water[y, x - 1]
                and valid_water[y, x + 1]
            ):
                mask[y, x] = 65
    mask_dst = ROOT / "assets" / "beach" / "water_mask.png"
    Image.fromarray(mask, "L").save(mask_dst)
    print(f"wrote {mask_dst.relative_to(ROOT)}")

    # 2. Wrackmouth ground (2560x1680 = 4x of 640x420 world, scale=0.25)
    wm_raw = NEW_RAW / "wrackmouth_ground_v2.jpg"
    if not wm_raw.exists():
        wm_raw = NEW_RAW / "wrackmouth_ground_png_1792624491205.jpg"
    wm_src = Image.open(wm_raw)
    wm_out = sharpen_ground(
        wm_src, (640, 420), grim_grade=True, scale_factor=4, mode="wrackmouth"
    )
    wm_dst = ROOT / "assets" / "wrackmouth" / "ground.png"
    wm_dst.parent.mkdir(parents=True, exist_ok=True)
    wm_out.save(wm_dst)
    print(f"wrote {wm_dst.relative_to(ROOT)} ({wm_out.width}x{wm_out.height})")

    # 3. Crossholm road ground (2560x1440 = 4x of 640x360 world, scale=0.25)
    cr_raw = NEW_RAW / "crossholm_road_ground_v2.jpg"
    if not cr_raw.exists():
        cr_raw = NEW_RAW / "crossholm_road_ground_png_1792624507900.jpg"
    cr_src = Image.open(cr_raw)
    cr_out = sharpen_ground(
        cr_src, (640, 360), grim_grade=False, scale_factor=4, mode="crossholm"
    )
    cr_dst = ROOT / "assets" / "crossholm_road" / "ground.png"
    cr_dst.parent.mkdir(parents=True, exist_ok=True)
    cr_out.save(cr_dst)
    print(f"wrote {cr_dst.relative_to(ROOT)} ({cr_out.width}x{cr_out.height})")

    # 4. Intro & Menu storm sea + ships (4x density)
    intro_dir = ROOT / "assets" / "intro"
    if (INTRO_RAW / "storm_sea.jpeg").exists():
        sea_src = Image.open(INTRO_RAW / "storm_sea.jpeg")
        sea_out = sharpen_ground(
            sea_src,
            (320, 180),
            grim_grade=False,
            add_micro_detail=False,
            scale_factor=4,
        )
        sea_out.save(intro_dir / "storm_sea.png")
        print(f"wrote assets/intro/storm_sea.png ({sea_out.width}x{sea_out.height})")
    if (INTRO_RAW / "ship.jpeg").exists():
        save_sprite(
            Image.open(INTRO_RAW / "ship.jpeg"),
            intro_dir / "ship.png",
            world_width=120,
        )
    if (INTRO_RAW / "ship_broken.jpeg").exists():
        save_sprite(
            Image.open(INTRO_RAW / "ship_broken.jpeg"),
            intro_dir / "ship_broken.png",
            world_width=110,
        )


def build_buildings() -> None:
    wm_dir = ROOT / "assets" / "wrackmouth"
    cr_dir = ROOT / "assets" / "crossholm_road"
    wm_dir.mkdir(parents=True, exist_ok=True)
    cr_dir.mkdir(parents=True, exist_ok=True)

    hall = save_sprite(
        Image.open(NEW_RAW / "mayor_hall_1792624473522.jpg"),
        wm_dir / "mayor_hall.png",
        world_width=116,
    )
    save_sprite(
        Image.open(NEW_RAW / "forge_1792624501091.jpg"),
        wm_dir / "forge.png",
        world_width=96,
    )
    save_sprite(
        Image.open(NEW_RAW / "cottage_harrow_1792624473913.jpg"),
        wm_dir / "cottage_harrow.png",
        world_width=74,
    )
    rook = save_sprite(
        Image.open(NEW_RAW / "cottage_rook_1792624489518.jpg"),
        wm_dir / "cottage_rook.png",
        world_width=68,
    )
    shuttered = save_sprite(
        Image.open(NEW_RAW / "cottage_shuttered_1792624502404.jpg"),
        wm_dir / "cottage_shuttered.png",
        world_width=68,
    )

    # Salt Gull Inn at 4x density (496x440)
    inn_raw = Image.open(NEW_RAW / "forge_1792624487817.jpg")
    inn_rgba = clean_rgba(inn_raw, 165)
    arr = np.array(inn_rgba)
    for y in range(435, 530):
        for x in range(388, 488):
            r, g, b, a = arr[y, x]
            if a > 0 and r > 140 and g > 110 and b < 110:
                arr[y, x, :3] = [82, 58, 38]
    inn_edited = Image.fromarray(arr)
    draw_inn = ImageDraw.Draw(inn_edited)
    draw_inn.polygon(
        [
            (405, 480),
            (425, 468),
            (438, 482),
            (455, 472),
            (472, 490),
            (452, 484),
            (438, 492),
            (422, 478),
        ],
        fill=(230, 228, 218, 255),
    )
    arr2 = np.array(inn_edited)
    for y1, y2, x1, x2 in ((378, 418, 430, 460), (582, 650, 750, 796)):
        reg = arr2[y1:y2, x1:x2]
        dark_pane = (
            (reg[..., 3] > 0)
            & (reg[..., 0] < 48)
            & (reg[..., 1] < 48)
            & (reg[..., 2] < 52)
        )
        reg[dark_pane, 0] = 235
        reg[dark_pane, 1] = 162
        reg[dark_pane, 2] = 54
    bbox = Image.fromarray(arr2).getchannel("A").getbbox()
    inn_cropped = Image.fromarray(arr2).crop(bbox)
    inn_w = 124 * 4
    inn_h = round(inn_cropped.height * inn_w / inn_cropped.width)
    inn_out = resize_crisp_rgba(inn_cropped, inn_w, inn_h)
    inn_out.save(wm_dir / "salt_gull.png")
    print(f"wrote assets/wrackmouth/salt_gull.png ({inn_out.width}x{inn_out.height})")

    # Lantern Watch Tower (216x352 = 4x of 54x88)
    tower = build_lantern_watch(rook, hall)
    tower.save(wm_dir / "lantern_watch.png")
    print(f"wrote assets/wrackmouth/lantern_watch.png ({tower.width}x{tower.height})")

    # Burned Farm Ruins (4x density)
    burned = build_burned_farm(shuttered)
    burned.save(cr_dir / "burned_farm.png")
    print(
        f"wrote assets/crossholm_road/burned_farm.png ({burned.width}x{burned.height})"
    )

    # Crossholm Garrison Gate & Walls (4x density)
    gate, wall_n, wall_s = build_crossholm_fortifications(hall)
    gate.save(cr_dir / "gate.png")
    wall_n.save(cr_dir / "wall_north.png")
    wall_s.save(cr_dir / "wall_south.png")
    print(
        f"wrote assets/crossholm_road/gate.png ({gate.width}x{gate.height}), "
        f"wall_north.png ({wall_n.width}x{wall_n.height}), wall_south.png ({wall_s.width}x{wall_s.height})"
    )


def build_lantern_watch(rook: Image.Image, hall: Image.Image) -> Image.Image:
    """Constructs a 216x352 (4x of 54x88) 2-story coastal watchtower from 4x Rook cottage."""
    s = 4
    slim = rook.resize((54 * s, 68 * s), Image.NEAREST)
    top_part = slim.crop((0, 0, 54 * s, 46 * s))
    mid_band = slim.crop((0, 28 * s, 54 * s, 48 * s))
    bot_part = slim.crop((0, 38 * s, 54 * s, 68 * s))

    img = Image.new("RGBA", (54 * s, 88 * s), (0, 0, 0, 0))
    img.alpha_composite(bot_part, (0, 58 * s))
    img.alpha_composite(mid_band, (0, 40 * s))
    img.alpha_composite(top_part, (0, 0))
    win = hall.crop((19 * s, 55 * s, 27 * s, 66 * s))
    img.alpha_composite(win, (14 * s, 24 * s))
    return img


def build_burned_farm(shuttered: Image.Image) -> Image.Image:
    """Creates a charred, smoking farmhouse ruin at 4x resolution with glowing embers."""
    arr = np.array(shuttered.convert("RGBA")).astype(float)
    alpha = arr[..., 3] > 0
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    arr[alpha, 0] = np.clip(lum[alpha] * 0.42 + 8, 12, 75)
    arr[alpha, 1] = np.clip(lum[alpha] * 0.36 + 5, 10, 62)
    arr[alpha, 2] = np.clip(lum[alpha] * 0.34 + 5, 10, 58)
    out = arr.astype(np.uint8)
    h, w = out.shape[:2]
    rng = np.random.default_rng(99)
    for y in range(int(h * 0.25), int(h * 0.88), 2):
        for x in range(int(w * 0.18), int(w * 0.82), 2):
            if out[y, x, 3] > 0 and out[y, x, 0] > 28 and rng.random() < 0.045:
                out[y : y + 2, x : x + 2, :3] = [235, 95, 25]
                if x + 3 < w and out[y, x + 2, 3] > 0:
                    out[y : y + 2, x + 2 : x + 4, :3] = [255, 165, 45]
    return Image.fromarray(out, "RGBA")


def build_crossholm_fortifications(
    hall: Image.Image,
) -> tuple[Image.Image, Image.Image, Image.Image]:
    """Builds 4x resolution fortified stone garrison walls and gatehouse."""
    s = 4
    stone_course = hall.crop((13 * s, 75 * s, 26 * s, 91 * s))
    door_patch = hall.crop((28 * s, 70 * s, 45 * s, 96 * s))

    def make_wall(world_w: int, world_h: int) -> Image.Image:
        w, h = world_w * s, world_h * s
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        step_y = 14 * s
        step_x = 12 * s
        for ty in range(0, h, step_y):
            offset = ((ty // step_y) % 2) * (6 * s)
            for tx in range(-offset, w, step_x):
                im.paste(stone_course, (tx, ty))
        arr = np.array(im).astype(float)
        for x in range(w):
            wx = x / s
            if wx < 9:
                shade = 0.76
            elif wx < 12:
                shade = 0.44
            else:
                shade = 0.58 - 0.16 * ((wx - 12) / max(1, world_w - 12))
            arr[:, x, :3] = np.clip(arr[:, x, :3] * shade, 14, 175)
        u = arr.astype(np.uint8)
        u[..., 3] = 255
        for y in range(5 * s, h - 6 * s, 14 * s):
            u[y : y + 5 * s, 0 : 4 * s, 3] = 0
            u[y : y + 5 * s, 4 * s : 4 * s + 2, :3] = [18, 16, 20]
        u[:, -2:, :3] = [18, 16, 20]
        u[:2, :, :3] = [18, 16, 20]
        u[-2:, :, :3] = [18, 16, 20]
        for y in range(h):
            if u[y, 0, 3] > 0:
                u[y, :2, :3] = [18, 16, 20]
        return Image.fromarray(u, "RGBA")

    wall_n = make_wall(48, 170)
    wall_s = make_wall(48, 146)

    gw, gh = 48, 64
    gate = make_wall(gw, gh)
    gate.alpha_composite(
        door_patch.resize((22 * s, 32 * s), Image.NEAREST), (13 * s, 31 * s)
    )
    d = ImageDraw.Draw(gate)
    for tx in (7 * s, (gw - 10) * s):
        d.rectangle([tx, 36 * s, tx + 2 * s, 42 * s], fill=(48, 32, 22, 255))
        d.rectangle([tx - 1 * s, 32 * s, tx + 3 * s, 36 * s], fill=(235, 145, 38, 255))
        d.rectangle([tx, 33 * s, tx + 2 * s, 35 * s], fill=(255, 225, 115, 255))
    return gate, wall_n, wall_s


def build_props() -> None:
    beach_dir = ROOT / "assets" / "beach"
    cr_dir = ROOT / "assets" / "crossholm_road"
    props_dir = ROOT / "assets" / "props"
    props_dir.mkdir(parents=True, exist_ok=True)

    save_sprite(
        Image.open(NEW_RAW / "wyvern_skeleton_png_1792624477339.jpg"),
        beach_dir / "wyvern_skeleton.png",
        world_width=68,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "wreck.jpeg"),
        beach_dir / "wreck.png",
        world_width=96,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "crate.jpeg"),
        beach_dir / "crate.png",
        world_width=40,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "dead_tree.jpeg"),
        props_dir / "dead_tree.png",
        world_width=52,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "driftwood.jpeg"),
        props_dir / "driftwood.png",
        world_width=42,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "signpost.jpeg"),
        props_dir / "signpost.png",
        world_width=18,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "campfire_lit.jpeg"),
        props_dir / "campfire_lit.png",
        world_width=24,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "campfire_unlit.jpeg"),
        props_dir / "campfire_unlit.png",
        world_width=24,
        strip_sand=True,
    )
    save_sprite(
        Image.open(NEW_RAW / "overturned_cart_png_1792624490029.jpg"),
        cr_dir / "cart.png",
        world_width=56,
    )


def ramp_color(
    luma: np.ndarray,
    base_rgb: tuple[int, int, int],
    ref_luma: float = 0.30,
    contrast: float = 1.05,
) -> np.ndarray:
    base = np.array(base_rgb, dtype=float)
    ratio = np.clip((luma / max(0.05, ref_luma)) ** contrast, 0.30, 1.50)[..., None]
    out = base * ratio
    return np.clip(out, 14, 248).astype(int)


def style_npc_sheet(sheet: Image.Image, cfg: dict) -> Image.Image:
    """Applies multi-tone pixel-art shading ramps and accessories across the 384x512 sheet."""
    arr = np.array(sheet.convert("RGBA")).astype(int)
    cw, ch = 96, 128
    for r in range(4):
        for c in range(4):
            y0, y1 = r * ch, (r + 1) * ch
            x0, x1 = c * cw, (c + 1) * cw
            cell = arr[y0:y1, x0:x1]
            a = cell[..., 3] > 0
            if not a.any():
                continue
            pr, pg, pb = cell[..., 0], cell[..., 1], cell[..., 2]
            mx = np.maximum(np.maximum(pr, pg), pb)
            mn = np.minimum(np.minimum(pr, pg), pb)
            chroma = mx - mn
            luma = (0.299 * pr + 0.587 * pg + 0.114 * pb) / 255.0
            yy, xx = np.mgrid[0:ch, 0:cw]

            not_outline = a & (mx >= 32)
            is_eye_box = (
                (
                    (r == 0)
                    & (yy >= 34)
                    & (yy <= 46)
                    & (xx >= 34)
                    & (xx <= 62)
                    & ((mn > 160) | (mx < 95))
                )
                | (
                    (r == 2)
                    & (yy >= 32)
                    & (yy <= 45)
                    & (xx >= 26)
                    & (xx <= 45)
                    & ((mn > 160) | (mx < 95))
                )
                | (
                    (r == 3)
                    & (yy >= 32)
                    & (yy <= 45)
                    & (xx >= 51)
                    & (xx <= 70)
                    & ((mn > 160) | (mx < 95))
                )
            )
            editable = not_outline & (~is_eye_box)

            # Face & ear protection zone so ear/jaw shadows are always treated as skin, never hair
            in_face_lower = (
                ((r == 0) & (yy >= 39) & (yy <= 56) & (xx >= 34) & (xx <= 62))
                | ((r == 2) & (yy >= 38) & (yy <= 56) & (xx <= 50))
                | ((r == 3) & (yy >= 38) & (yy <= 56) & (xx >= 46))
            )

            is_cloth = editable & (yy >= 54) & (yy <= 102) & (chroma <= 22)
            is_skin = (
                editable
                & (~is_cloth)
                & (yy >= 26)
                & (yy <= 100)
                & (
                    ((pr >= 115) & (pg >= 70) & ((pr - pb) >= 32) & ((pr - pg) >= 12))
                    | (in_face_lower & (pr >= 85) & ((pr - pb) >= 20))
                )
                & (~((r == 1) & (yy < 57)))
            )
            is_hair = (
                editable
                & (~is_cloth)
                & (~is_skin)
                & (~in_face_lower)
                & ((yy <= 54) | ((r == 1) & (yy <= 58)))
            )
            is_pauldron = (
                editable
                & (~is_cloth)
                & (~is_skin)
                & (~is_hair)
                & (yy >= 53)
                & (yy < 73)
            )
            is_wraps = (
                editable
                & (~is_cloth)
                & (~is_skin)
                & (yy >= 73)
                & (yy < 95)
                & ((xx < 36) | (xx > 60) | (r in (2, 3)))
            )
            is_belt = (
                editable
                & (~is_cloth)
                & (~is_skin)
                & (~is_wraps)
                & (yy >= 82)
                & (yy < 95)
            )
            is_pants = editable & (~is_cloth) & (~is_skin) & (yy >= 95) & (yy < 112)
            is_boots = editable & (yy >= 112)

            if "skin" in cfg:
                cell[is_skin, :3] = ramp_color(luma[is_skin], cfg["skin"], 0.62, 0.95)
            if "hair" in cfg:
                cell[is_hair, :3] = ramp_color(luma[is_hair], cfg["hair"], 0.24, 1.05)
            if "tunic" in cfg:
                cell[is_cloth, :3] = ramp_color(
                    luma[is_cloth], cfg["tunic"], 0.30, 1.10
                )
            if "pauldron" in cfg:
                cell[is_pauldron, :3] = ramp_color(
                    luma[is_pauldron], cfg["pauldron"], 0.34, 1.05
                )
            if "wraps" in cfg:
                cell[is_wraps, :3] = ramp_color(luma[is_wraps], cfg["wraps"], 0.50, 1.0)
            if "belt" in cfg:
                cell[is_belt, :3] = ramp_color(luma[is_belt], cfg["belt"], 0.28, 1.05)
            if "pants" in cfg:
                cell[is_pants, :3] = ramp_color(
                    luma[is_pants], cfg["pants"], 0.30, 1.10
                )
            if "boots" in cfg:
                cell[is_boots, :3] = ramp_color(
                    luma[is_boots], cfg["boots"], 0.28, 1.05
                )

            if cfg.get("apron") is not None and r in (0, 2, 3):
                apron_col = cfg["apron"]
                if r == 0:
                    ap_mask = (
                        is_cloth & (yy >= 68) & (yy <= 102) & (xx >= 38) & (xx <= 58)
                    )
                    ap_border = (
                        is_cloth
                        & (yy >= 68)
                        & (yy <= 102)
                        & ((xx == 37) | (xx == 59) | (yy == 68))
                        & (xx >= 37)
                        & (xx <= 59)
                    )
                elif r == 2:
                    ap_mask = is_cloth & (yy >= 68) & (yy <= 102) & (xx <= 45)
                    ap_border = (
                        is_cloth & (yy >= 68) & (yy <= 102) & ((xx == 46) | (yy == 68))
                    )
                else:
                    ap_mask = is_cloth & (yy >= 68) & (yy <= 102) & (xx >= 51)
                    ap_border = (
                        is_cloth & (yy >= 68) & (yy <= 102) & ((xx == 50) | (yy == 68))
                    )
                cell[ap_mask, :3] = ramp_color(luma[ap_mask], apron_col, 0.30, 1.1)
                cell[ap_border, :3] = [24, 20, 22]

            if cfg.get("mayor_regalia"):
                mantle_mask = is_cloth & (yy >= 54) & (yy <= 67)
                cell[mantle_mask, :3] = ramp_color(
                    luma[mantle_mask], (158, 32, 42), 0.30, 1.10
                )
                if r == 0:
                    chain_curve = (
                        np.abs((yy - 58) - (10.0 - 0.07 * ((xx - 48.0) ** 2))) <= 1.5
                    )
                    chain_mask = is_cloth & chain_curve & (xx >= 36) & (xx <= 60)
                    chain_outline = (
                        is_cloth
                        & (
                            np.abs((yy - 58) - (10.0 - 0.07 * ((xx - 48.0) ** 2)))
                            <= 2.5
                        )
                        & (~chain_mask)
                        & (xx >= 36)
                        & (xx <= 60)
                    )
                    cell[chain_outline, :3] = [28, 22, 18]
                    cell[chain_mask, :3] = [238, 196, 74]
                    med = is_cloth & (((xx - 48.0) ** 2 + (yy - 71.0) ** 2) <= 9.0)
                    med_out = (
                        is_cloth
                        & (((xx - 48.0) ** 2 + (yy - 71.0) ** 2) <= 15.0)
                        & (~med)
                    )
                    cell[med_out, :3] = [24, 18, 16]
                    cell[med, :3] = [245, 205, 82]
                    cell[70, 47, :3] = [255, 245, 180]
                    cell[71, 48, :3] = [195, 40, 48]
                hem_gold = is_cloth & (yy >= 95) & (yy <= 98)
                cell[hem_gold, :3] = ramp_color(
                    luma[hem_gold], (225, 182, 66), 0.30, 1.1
                )

    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def build_characters() -> None:
    """Builds the 4x4 Hero sheet (384x512, cell 96x128) with stabilized torso/head walk cycle
    and 8 distinct multi-tone NPC sheets."""
    im_a = clean_rgba(Image.open(NEW_RAW / "hero_sheet_png_1792624478858.jpg"), 165)

    def raw_cell(r: int, c: int) -> Image.Image:
        return im_a.crop((c * 256, r * 256, (c + 1) * 256, (r + 1) * 256))

    def make_front_back_row(r: int) -> list[Image.Image]:
        """Animates front/back walk purely by lifting alternating boots vertically (dx=0)
        from the centered `idle` frame so the ankles never sway left and right."""
        idle = raw_cell(r, 0)
        leg_y = 200
        # Split idle lower legs cleanly at the centerline x=128
        left_leg = idle.crop((0, leg_y, 128, 254))
        right_leg = idle.crop((128, leg_y, 256, 254))
        upper_body = idle.crop((0, 0, 256, leg_y + 2))

        # Step A: Left foot lifts straight up (dy = -10, dx = 0); Right foot plants (dy = +2, dx = 0)
        step_a = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        step_a.alpha_composite(right_leg, (128, leg_y + 2))
        step_a.alpha_composite(left_leg, (0, leg_y - 10))
        step_a.alpha_composite(upper_body, (0, 0))

        # Step B: Right foot lifts straight up (dy = -10, dx = 0); Left foot plants (dy = +2, dx = 0)
        step_b = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        step_b.alpha_composite(left_leg, (0, leg_y + 2))
        step_b.alpha_composite(right_leg, (128, leg_y - 10))
        step_b.alpha_composite(upper_body, (0, 0))
        return [idle, step_a, idle.copy(), step_b]

    def make_side_row() -> list[Image.Image]:
        """Animates side walk by scissoring two left-pointing boots forward/back under the
        hips without ever flipping a boot backwards or shifting the hip centerline."""
        idle = raw_cell(2, 0)
        leg_y = 200
        boot_front = idle.crop((0, leg_y, 256, 254))
        # Create a slightly darker rear leg (still pointing LEFT, never flipped!)
        b_arr = np.array(boot_front).astype(np.float32)
        b_alpha = b_arr[..., 3] > 0
        b_arr[b_alpha, :3] = np.clip(b_arr[b_alpha, :3] * 0.78, 12.0, 240.0)
        boot_back = Image.fromarray(b_arr.astype(np.uint8), "RGBA")
        upper_body = idle.crop((0, 0, 256, leg_y + 2))

        # Step A: front leg steps forward (-8px), back leg trails (+8px, lifted 4px)
        step_a = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        step_a.alpha_composite(boot_back, (8, leg_y - 4))
        step_a.alpha_composite(boot_front, (-8, leg_y - 2))
        step_a.alpha_composite(upper_body, (0, 0))

        # Step B: back leg steps forward (-8px, lifted 4px), front leg trails (+8px)
        step_b = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        step_b.alpha_composite(boot_back, (-8, leg_y - 4))
        step_b.alpha_composite(boot_front, (8, leg_y - 2))
        step_b.alpha_composite(upper_body, (0, 0))
        return [idle, step_a, idle.copy(), step_b]

    down = make_front_back_row(0)
    up = make_front_back_row(1)
    left = make_side_row()
    right = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in left]

    cell_w, cell_h = 96, 128
    hero_sheet = Image.new("RGBA", (cell_w * 4, cell_h * 4), (0, 0, 0, 0))
    for r, row in enumerate([down, up, left, right]):
        for c, frame in enumerate(row):
            cropped = frame.crop((32, 0, 224, 256))
            scaled = cropped.resize((cell_w, cell_h), Image.NEAREST)
            hero_sheet.alpha_composite(scaled, (c * cell_w, r * cell_h))

    hero_dst = ROOT / "assets" / "hero" / "hero_sheet.png"
    hero_dst.parent.mkdir(parents=True, exist_ok=True)
    hero_sheet.save(hero_dst)
    print(
        f"wrote {hero_dst.relative_to(ROOT)} ({hero_sheet.width}x{hero_sheet.height})"
    )

    npc_dir = ROOT / "assets" / "npc"
    npc_dir.mkdir(parents=True, exist_ok=True)

    npcs = {
        "mayor": {
            "hair": (185, 192, 204),  # striking silver-white magistrate hair
            "skin": (222, 172, 142),
            "tunic": (34, 82, 58),  # deep emerald-pine magistrate coat
            "pauldron": (165, 34, 44),  # crimson velvet shoulder mantle
            "wraps": (198, 162, 68),  # gold-trimmed cuffs
            "belt": (195, 155, 56),  # gilded sash
            "pants": (28, 56, 42),
            "boots": (42, 34, 30),
            "mayor_regalia": True,
        },
        "orsa": {
            "hair": (168, 68, 36),  # fiery copper-auburn hair
            "skin": (204, 142, 106),  # warm forge-bronzed skin
            "tunic": (54, 58, 66),  # dark iron-charcoal smith shirt
            "pauldron": (92, 98, 108),  # forged steel shoulder guard
            "wraps": (84, 90, 100),  # steel bracers
            "belt": (78, 52, 36),
            "pants": (64, 52, 44),
            "boots": (48, 38, 32),
            "apron": (122, 74, 42),  # shaded leather smith apron
        },
        "bram": {
            "hair": (96, 58, 36),  # chestnut brown hair
            "skin": (218, 160, 126),
            "tunic": (142, 46, 42),  # rich burgundy tavern vest
            "pauldron": (118, 38, 34),
            "wraps": (212, 198, 174),  # rolled cream linen sleeves
            "belt": (72, 48, 32),
            "pants": (62, 52, 44),
            "boots": (52, 40, 32),
            "apron": (188, 176, 152),  # shaded linen innkeeper apron
        },
        "teague": {
            "hair": (124, 134, 148),  # weathered storm-grey hair
            "skin": (208, 156, 124),
            "tunic": (42, 62, 92),  # midnight-navy watchman oilskin coat
            "pauldron": (188, 148, 58),  # brass lantern-keeper's clasp
            "wraps": (58, 76, 104),
            "belt": (165, 128, 48),
            "pants": (36, 48, 68),
            "boots": (38, 34, 34),
        },
        "pell": {
            "hair": (168, 164, 148),  # sea-bleached sandy grey hair
            "skin": (198, 140, 104),  # sun-weathered fisherman tan
            "tunic": (52, 94, 102),  # coastal teal-slate wool sweater
            "pauldron": (108, 76, 52),  # weathered driftwood-brown leather
            "wraps": (138, 118, 94),  # rope-twine wrist wraps
            "belt": (74, 56, 40),
            "pants": (58, 62, 64),
            "boots": (46, 40, 34),
        },
        "ansa": {
            "hair": (38, 32, 46),  # raven-black hair
            "skin": (230, 188, 162),  # pale salt complexion
            "tunic": (78, 52, 92),  # deep twilight-plum mourning dress
            "pauldron": (104, 72, 118),  # plum-violet shawl
            "wraps": (142, 124, 152),  # lavender-grey cuffs
            "belt": (58, 40, 68),
            "pants": (54, 38, 64),
            "boots": (36, 28, 40),
        },
        "wren": {
            "hair": (198, 154, 68),  # bright golden-straw hair
            "skin": (220, 168, 136),
            "tunic": (64, 98, 58),  # forest-moss green tunic
            "pauldron": (134, 88, 48),  # warm russet leather shoulder patch
            "wraps": (176, 142, 96),
            "belt": (92, 64, 38),
            "pants": (72, 66, 52),
            "boots": (56, 44, 34),
        },
        "dov": {
            "hair": (68, 48, 34),  # dark umber hair
            "skin": (186, 128, 92),  # warm ochre-bronze skin
            "tunic": (138, 112, 58),  # highland amber-ochre gambeson
            "pauldron": (112, 118, 128),  # steel road-guard pauldron
            "wraps": (102, 108, 118),  # steel bracers
            "belt": (68, 48, 32),
            "pants": (62, 58, 48),
            "boots": (44, 36, 30),
        },
    }

    for name, cfg in npcs.items():
        styled = style_npc_sheet(hero_sheet, cfg)
        dst = npc_dir / f"{name}.png"
        styled.save(dst)
        print(f"wrote {dst.relative_to(ROOT)} ({styled.width}x{styled.height})")


def main() -> None:
    from build_modular_art import (
        build_combat_sheets_and_icons,
        build_hd_props_and_cemetery,
        build_modular_buildings_and_smoke,
        build_organic_terrain_tiles,
        build_plaza_circle_asset,
    )

    _, cobble_tile = build_organic_terrain_tiles()
    build_plaza_circle_asset(cobble_tile)
    build_grounds_and_intro()
    build_buildings()
    build_props()
    build_hd_props_and_cemetery()
    build_modular_buildings_and_smoke()
    build_characters()
    build_combat_sheets_and_icons()
    print("All high-density art assets built successfully!")


if __name__ == "__main__":
    main()
