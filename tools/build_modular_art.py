"""Builds native 4x-density (1px texel) modular building parts, animated fire & chimney
smoke sheets, high-resolution cemetery/quest props, organic cobble plaza & road rubble
tiles, hero combat sprite sheets (punch, power punch, 2-hands-up block), and item icons.

Automatically invoked by `tools/build_all_art.py`.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent


def _draw_organic_stone(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    rng: np.random.Generator,
    base_col: tuple[int, int, int],
    outline_col: tuple[int, int, int, int] = (22, 22, 26, 255),
    shadow_below: bool = True,
) -> None:
    """Draws a hand-shaded multi-tone polygonal cobblestone/rubble rock (matching the
    exact style of campfire_lit.png stones—never a flat rectangle)."""
    n_pts = int(rng.integers(7, 11))
    angles = np.linspace(0, 2 * math.pi, n_pts, endpoint=False)
    pts_outer = []
    pts_inner = []
    pts_hi = []
    pts_sh = []
    for a in angles:
        jitter = float(rng.uniform(0.82, 1.16))
        px = cx + math.cos(a) * rx * jitter
        py = cy + math.sin(a) * ry * jitter
        pts_outer.append((px, py))
        pts_inner.append(
            (
                cx + math.cos(a) * (rx * jitter - 1.3),
                cy + math.sin(a) * (ry * jitter - 1.3),
            )
        )
        pts_hi.append(
            (
                cx - 0.8 + math.cos(a) * (rx * jitter * 0.65),
                cy - 0.8 + math.sin(a) * (ry * jitter * 0.65),
            )
        )
        pts_sh.append(
            (
                cx + 0.7 + math.cos(a) * (rx * jitter - 1.8),
                cy + 0.9 + math.sin(a) * (ry * jitter - 1.8),
            )
        )

    if shadow_below:
        pts_drop = [(x + 1.0, y + 2.0) for x, y in pts_outer]
        draw.polygon(pts_drop, fill=(28, 22, 18, 185))

    r, g, b = base_col
    col_sh = (
        max(16, int(r * 0.72)),
        max(16, int(g * 0.72)),
        max(18, int(b * 0.74)),
        255,
    )
    col_md = (r, g, b, 255)
    col_hi = (
        min(240, int(r * 1.22 + 10)),
        min(240, int(g * 1.22 + 10)),
        min(242, int(b * 1.20 + 10)),
        255,
    )

    draw.polygon(pts_outer, fill=outline_col)
    draw.polygon(pts_inner, fill=col_sh)
    # Shift mid-tone slightly toward top-left
    pts_mid = [(x - 0.6, y - 0.8) for x, y in pts_sh]
    draw.polygon(pts_mid, fill=col_md)
    draw.polygon(pts_hi, fill=col_hi)


def build_organic_terrain_tiles() -> tuple[np.ndarray, np.ndarray]:
    """Builds and saves `assets/terrain/dirt_rubble_tile.png` and
    `assets/terrain/cobble_tile.png` at 4x native density, returning their RGB arrays."""
    terrain_dir = ROOT / "assets" / "terrain"
    terrain_dir.mkdir(parents=True, exist_ok=True)

    # 1. Organic Dirt & Rubble Tile (256x256)
    sz = 256
    rng = np.random.default_rng(20261022)
    yy, xx = np.mgrid[0:sz, 0:sz]
    # Seamless multi-octave soil texture (no flat circles!)
    tau = 2.0 * math.pi / sz
    soil_wave = (
        np.sin(xx * tau * 2.0 + np.cos(yy * tau * 2.0)) * 7.0
        + np.cos(yy * tau * 3.0 - np.sin(xx * tau * 4.0)) * 5.0
        + np.sin((xx + yy) * tau * 6.0) * 3.5
    )
    # Fine pixel soil grain (2x2 coherent soil clods)
    h_clod = (((xx // 2) * 374761393 + (yy // 2) * 668265263) ^ 0x5BF03635) & 0xFFFF
    grain = ((h_clod.astype(np.float32) / 65535.0) - 0.5) * 11.0
    delta = np.round((soil_wave + grain) / 4.0) * 4.0

    dirt_arr = np.zeros((sz, sz, 3), dtype=np.float32)
    dirt_arr[..., 0] = np.clip(104.0 + delta * 1.05, 68.0, 142.0)
    dirt_arr[..., 1] = np.clip(78.0 + delta * 0.82, 50.0, 110.0)
    dirt_arr[..., 2] = np.clip(54.0 + delta * 0.58, 34.0, 80.0)

    dirt_im = Image.fromarray(dirt_arr.astype(np.uint8), "RGB").convert("RGBA")
    rubble_layer = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(rubble_layer)

    stone_pal = [
        (106, 104, 100),
        (94, 92, 90),
        (118, 106, 90),
        (86, 86, 88),
        (112, 98, 82),
    ]
    # Scatter natural clusters of organic polygonal rubble stones (wrapped across tile edges)
    for _ in range(38):
        cluster_x = float(rng.uniform(0, sz))
        cluster_y = float(rng.uniform(0, sz))
        n_stones = int(rng.integers(2, 5))
        for s_i in range(n_stones):
            sx = (cluster_x + float(rng.normal(0, 7.5))) % sz
            sy = (cluster_y + float(rng.normal(0, 6.5))) % sz
            rx = (
                float(rng.uniform(3.2, 6.8))
                if s_i == 0
                else float(rng.uniform(2.2, 4.5))
            )
            ry = rx * float(rng.uniform(0.68, 0.88))
            bcol = stone_pal[int(rng.integers(0, len(stone_pal)))]
            for ox in (-sz, 0, sz):
                for oy in (-sz, 0, sz):
                    if -16 <= sx + ox <= sz + 16 and -16 <= sy + oy <= sz + 16:
                        _draw_organic_stone(
                            rdraw,
                            sx + ox,
                            sy + oy,
                            rx,
                            ry,
                            rng,
                            bcol,
                            shadow_below=True,
                        )

    dirt_im.alpha_composite(rubble_layer)
    dirt_im.save(terrain_dir / "dirt_rubble_tile.png")

    # 2. Organic Weathered Medieval Cobblestone Tile (256x256)
    # Uses jittered Voronoi stone cells with multi-tone radial bevels, mortar crevices & moss
    grid_n = 12
    cell_step = sz / grid_n
    seeds_x = []
    seeds_y = []
    seed_cols = []
    cobble_pal = [
        (88, 94, 102),
        (98, 104, 112),
        (108, 112, 118),
        (82, 88, 96),
        (102, 104, 100),
        (92, 96, 94),
    ]
    for gy in range(grid_n):
        for gx in range(grid_n):
            sx = (gx + 0.5 + float(rng.uniform(-0.28, 0.28))) * cell_step
            sy = (gy + 0.5 + float(rng.uniform(-0.26, 0.26))) * cell_step
            seeds_x.append(sx)
            seeds_y.append(sy)
            seed_cols.append(cobble_pal[int(rng.integers(0, len(cobble_pal)))])

    sx_arr = np.array(seeds_x, dtype=np.float32)
    sy_arr = np.array(seeds_y, dtype=np.float32)
    sc_arr = np.array(seed_cols, dtype=np.float32)

    # Compute wrapped distance to 1st and 2nd nearest stone center for every pixel
    dx = np.abs(xx[..., None] - sx_arr[None, None, :])
    dx = np.minimum(dx, sz - dx)
    dy = np.abs(yy[..., None] - sy_arr[None, None, :])
    dy = np.minimum(dy, sz - dy)
    # Slightly flatten stones horizontally (typical top-down perspective)
    dist = np.sqrt((dx * 0.88) ** 2 + (dy * 1.08) ** 2)
    idx2 = np.argpartition(dist, 2, axis=-1)[..., :2]
    d1 = np.take_along_axis(dist, idx2[..., 0:1], axis=-1)[..., 0]
    d2 = np.take_along_axis(dist, idx2[..., 1:2], axis=-1)[..., 0]
    nearest_id = idx2[..., 0]

    # Signed offset from stone center for 3D top-left sunlit bevel & bottom-right shadow
    raw_dx = xx - sx_arr[nearest_id]
    raw_dx = np.where(
        raw_dx > sz * 0.5,
        raw_dx - sz,
        np.where(raw_dx < -sz * 0.5, raw_dx + sz, raw_dx),
    )
    raw_dy = yy - sy_arr[nearest_id]
    raw_dy = np.where(
        raw_dy > sz * 0.5,
        raw_dy - sz,
        np.where(raw_dy < -sz * 0.5, raw_dy + sz, raw_dy),
    )

    edge_gap = d2 - d1
    is_mortar = edge_gap < 1.95
    is_rim = (~is_mortar) & (edge_gap < 3.6)

    cob_arr = sc_arr[nearest_id].copy()
    # Top-left rim gets crisp highlight; bottom-right rim gets shadow bevel
    light_dir = (-raw_dx * 0.65 - raw_dy * 0.76) / np.maximum(1.0, d1)
    hi_rim = is_rim & (light_dir > 0.15)
    sh_rim = is_rim & (light_dir < -0.10)
    cob_arr[hi_rim] = np.clip(cob_arr[hi_rim] * 1.22 + 12.0, 0.0, 236.0)
    cob_arr[sh_rim] = np.clip(cob_arr[sh_rim] * 0.74, 18.0, 210.0)
    # Subtle dome shading + granite grain across stone interior
    cob_arr[~is_mortar] = np.clip(
        cob_arr[~is_mortar]
        + light_dir[~is_mortar, None] * 8.0
        + grain[~is_mortar, None] * 0.5,
        24.0,
        235.0,
    )
    # Deep charcoal mortar crevice
    cob_arr[is_mortar] = [28.0, 30.0, 34.0]
    # Moss tufts in mortar junctions (where edge_gap is small and d1 is large)
    is_moss = is_mortar & (d1 > 10.2) & ((h_clod % 5) < 2)
    cob_arr[is_moss] = [44.0, 74.0, 38.0]

    cobble_u8 = np.clip(cob_arr, 14.0, 240.0).astype(np.uint8)
    Image.fromarray(cobble_u8, "RGB").save(terrain_dir / "cobble_tile.png")
    print("wrote assets/terrain/{dirt_rubble_tile,cobble_tile}.png")
    return np.array(dirt_im.convert("RGB"), dtype=np.float32), cobble_u8.astype(
        np.float32
    )


def build_plaza_circle_asset(cobble_tile: np.ndarray) -> Image.Image:
    """Builds and saves `assets/props/plaza_circle.png` (520x552 at 4x density):
    an ornate, weathered dark-fantasy stone town plaza with concentric carved curb stones,
    organic Voronoi cobbles, mossy crevices, and an inner hearth stone ring."""
    w, h = 520, 552
    cx, cy = w / 2.0, h / 2.0
    rx, ry = 240.0, 256.0

    reps_y = (h + 255) // 256
    reps_x = (w + 255) // 256
    tiled_cob = np.tile(cobble_tile, (reps_y, reps_x, 1))[:h, :w].copy()

    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - cx) / rx
    ny = (yy - cy) / ry
    r_norm = np.sqrt(nx**2 + ny**2)
    angle = np.arctan2(yy - cy, xx - cx)

    out = np.zeros((h, w, 4), dtype=np.uint8)
    # Outer drop shadow on dirt (r_norm in 1.0 .. 1.035)
    in_drop = (r_norm > 1.0) & (r_norm <= 1.032)
    out[in_drop] = [24, 18, 14, 150]

    # Inside plaza (r_norm <= 1.0)
    rgb = tiled_cob.copy()

    # Concentric inner ring around the central fireplace (r_norm in 0.24 .. 0.31)
    in_inner_ring = (r_norm >= 0.24) & (r_norm <= 0.31)
    inner_seam = (
        (np.abs(r_norm - 0.24) < 0.012)
        | (np.abs(r_norm - 0.31) < 0.012)
        | (((angle * 16.0 / math.pi) % 1.0) < 0.09)
    )
    rgb[in_inner_ring & (~inner_seam)] = np.clip(
        rgb[in_inner_ring & (~inner_seam)] * 1.12 + np.array([10.0, 8.0, 4.0]),
        30.0,
        230.0,
    )
    rgb[in_inner_ring & inner_seam] = [26.0, 28.0, 32.0]

    # Outer carved stone curb ring (r_norm in 0.86 .. 1.0)
    # Add organic stone wobble to the outer and inner curb edges so it looks hand-laid
    stone_idx = np.floor((angle + math.pi) / (2.0 * math.pi) * 36.0)
    stone_hash = (
        (stone_idx.astype(np.uint32) * np.uint32(2654435761)) & np.uint32(0xFF)
    ).astype(np.float32) / 255.0
    r_outer_edge = 0.992 - 0.008 * np.sin(angle * 36.0)
    r_inner_edge = 0.865 + 0.007 * np.cos(angle * 36.0)

    in_curb = (r_norm >= r_inner_edge) & (r_norm <= r_outer_edge)
    radial_joint = ((angle + math.pi) / (2.0 * math.pi) * 36.0) % 1.0
    is_curb_mortar = in_curb & (
        (radial_joint < 0.085)
        | (radial_joint > 0.94)
        | (np.abs(r_norm - r_inner_edge) < 0.012)
        | (np.abs(r_norm - r_outer_edge) < 0.014)
    )
    # 3D bevel on each curb stone block
    is_curb_hi = (
        in_curb
        & (~is_curb_mortar)
        & ((np.abs(r_norm - r_inner_edge) < 0.032) | (radial_joint < 0.18))
    )
    is_curb_sh = (
        in_curb
        & (~is_curb_mortar)
        & (~is_curb_hi)
        & ((np.abs(r_norm - r_outer_edge) < 0.035) | (radial_joint > 0.82))
    )

    curb_base_shade = 104.0 + (stone_hash - 0.5) * 22.0
    for c_i, c_bias in enumerate((-2.0, 2.0, 6.0)):
        rgb[in_curb, c_i] = curb_base_shade[in_curb] + c_bias
    rgb[is_curb_hi] = np.clip(rgb[is_curb_hi] + 24.0, 0.0, 238.0)
    rgb[is_curb_sh] = np.clip(rgb[is_curb_sh] - 24.0, 20.0, 210.0)
    rgb[is_curb_mortar] = [24.0, 26.0, 30.0]

    # Trim outside r_outer_edge
    valid_stone = r_norm <= r_outer_edge
    out[valid_stone, :3] = np.clip(rgb[valid_stone], 14.0, 242.0).astype(np.uint8)
    out[valid_stone, 3] = 255

    im = Image.fromarray(out, "RGBA")
    dst = ROOT / "assets" / "props" / "plaza_circle.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    print(f"wrote {dst.relative_to(ROOT)} ({im.width}x{im.height})")
    return im


def build_hd_props_and_cemetery() -> None:
    """Builds native 4x-density (1px texel) props so nothing in the world looks like a
    blocky 1x sprite stretched 4x:
    - rathole.png (72x56)
    - open_grave.png (128x96)
    - moonherb.png (72x72)
    - iron_scrap.png (80x64)
    - headstone_1.png (80x104)
    - headstone_2.png (76x96)
    - cairn_stones.png (128x112)
    - campfire_lit_sheet.png (384x85, 4 frames) & fire_glow.png (128x128)
    """
    props_dir = ROOT / "assets" / "props"
    props_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(88421)

    # 1. Native 4x Rat Hole / Cellar Foundation Grate (72x56)
    rh = Image.new("RGBA", (72, 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(rh)
    # Stone arch surround built of individual shaded voussoir stones
    arch_stones = [
        (12, 36, 22, 46),
        (14, 24, 24, 36),
        (20, 14, 34, 24),
        (32, 11, 44, 21),
        (42, 14, 54, 24),
        (48, 24, 58, 36),
        (50, 36, 60, 46),
    ]
    d.ellipse([10, 34, 62, 52], fill=(24, 18, 14, 190))
    # Dark burrow void inside arch
    d.chord(
        [18, 16, 54, 52],
        start=180,
        end=360,
        fill=(10, 8, 12, 255),
        outline=(22, 20, 24, 255),
    )
    d.rectangle([18, 32, 54, 46], fill=(10, 8, 12, 255))
    # Broken iron cellar grate bars inside the hole
    for bx in (26, 35, 44):
        bar_len = 36 if bx != 35 else 27  # middle bar snapped off by giant rats!
        d.rectangle([bx, 18, bx + 2, bar_len], fill=(58, 62, 68, 255))
        d.line([(bx, 19), (bx, bar_len)], fill=(96, 102, 110, 255))
    # Glowing amber rat eyes deep in the shadow
    d.point((31, 36), fill=(225, 120, 35, 255))
    d.point((39, 36), fill=(225, 120, 35, 255))
    for x0, y0, x1, y1 in arch_stones:
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        _draw_organic_stone(
            d,
            cx,
            cy,
            (x1 - x0) * 0.55,
            (y1 - y0) * 0.55,
            rng,
            (92, 96, 102),
            shadow_below=False,
        )
    # Spilled earth & gnawed wood splinters at threshold
    for sx, sy, rx, ry in (
        (16, 46, 5, 3),
        (54, 46, 6, 3.5),
        (26, 48, 4, 2.5),
        (44, 48, 4.5, 2.5),
    ):
        _draw_organic_stone(d, sx, sy, rx, ry, rng, (86, 66, 46), shadow_below=False)
    rh.save(props_dir / "rathole.png")

    # 2. Native 4x Open Grave with Glowing Hex Rune (128x96)
    og = Image.new("RGBA", (128, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(og)
    # Spilled dark earth mound
    d.ellipse([8, 26, 120, 88], fill=(28, 20, 16, 210))
    for _ in range(42):
        ex = float(rng.uniform(18, 110))
        ey = float(rng.uniform(34, 80))
        _draw_organic_stone(
            d,
            ex,
            ey,
            float(rng.uniform(4, 9)),
            float(rng.uniform(3, 6)),
            rng,
            (62, 46, 34) if rng.random() < 0.6 else (76, 58, 42),
            shadow_below=False,
        )
    # Stone crypt rim & deep shadow pit dug open from below
    d.polygon(
        [(24, 38), (94, 34), (102, 74), (18, 78)],
        fill=(48, 52, 58, 255),
        outline=(18, 16, 20, 255),
    )
    d.polygon(
        [(30, 42), (88, 39), (94, 68), (24, 72)],
        fill=(12, 10, 14, 255),
        outline=(26, 24, 28, 255),
    )
    # Bleached & scorched bone inside the pit
    d.line([(38, 62), (58, 50)], fill=(224, 214, 190, 255), width=3)
    d.ellipse([34, 59, 41, 66], fill=(232, 222, 198, 255), outline=(24, 20, 18, 255))
    d.ellipse([55, 47, 62, 54], fill=(232, 222, 198, 255), outline=(24, 20, 18, 255))
    # Heavy cracked stone lid pushed askew to the right/top
    lid_outer = [(46, 18), (114, 28), (106, 66), (38, 56)]
    lid_top = [(48, 20), (112, 30), (105, 62), (40, 52)]
    d.polygon(lid_outer, fill=(20, 20, 24, 255))
    d.polygon(lid_top, fill=(96, 100, 106, 255))
    # Chiseled bevel highlight along top & left of stone slab
    d.line([(48, 21), (111, 30)], fill=(142, 146, 152, 255), width=2)
    d.line([(48, 21), (41, 51)], fill=(132, 136, 142, 255), width=2)
    d.line([(40, 53), (105, 63)], fill=(58, 62, 68, 255), width=2)
    # Jagged crack splitting the lid
    crack = [(74, 24), (70, 36), (76, 44), (68, 57)]
    d.line(crack, fill=(22, 20, 24, 255), width=2)
    # Glowing fiery arcane Hex-Mark burned into the stone lid
    hx, hy = 82, 42
    d.ellipse([hx - 11, hy - 8, hx + 11, hy + 8], outline=(165, 38, 18, 220), width=2)
    rune_lines = [
        [(hx - 7, hy - 5), (hx + 7, hy + 5)],
        [(hx + 7, hy - 5), (hx - 7, hy + 5)],
        [(hx, hy - 8), (hx, hy + 8)],
        [(hx - 8, hy), (hx + 8, hy)],
    ]
    for rl in rune_lines:
        d.line(rl, fill=(235, 85, 22, 255), width=2)
    for rl in rune_lines:
        d.line(rl, fill=(255, 185, 55, 255), width=1)
    og.save(props_dir / "open_grave.png")

    # 3. Native 4x Headstone 1 (80x104), Headstone 2 (76x96), and Cairn Stones (128x112)
    hs1 = Image.new("RGBA", (80, 104), (0, 0, 0, 0))
    d = ImageDraw.Draw(hs1)
    d.ellipse([14, 82, 66, 98], fill=(20, 28, 18, 190))
    # Sculpted arched Nordic headstone with side thickness
    d.rounded_rectangle(
        [18, 12, 62, 90],
        radius=18,
        fill=(58, 62, 66, 255),
        outline=(18, 18, 22, 255),
        width=2,
    )
    d.rounded_rectangle(
        [18, 12, 56, 88],
        radius=16,
        fill=(98, 104, 110, 255),
        outline=(18, 18, 22, 255),
        width=2,
    )
    d.arc([20, 14, 54, 48], start=180, end=350, fill=(144, 148, 154, 255), width=2)
    # Carved runic wheel-cross on the headstone face
    d.ellipse([28, 26, 46, 44], outline=(46, 50, 54, 255), width=2)
    d.line([(37, 24), (37, 62)], fill=(46, 50, 54, 255), width=2)
    d.line([(26, 35), (48, 35)], fill=(46, 50, 54, 255), width=2)
    # Weathering lines & moss tufts at base
    for my, mx0, mx1 in ((68, 24, 48), (74, 22, 46)):
        d.line([(mx0, my), (mx1, my)], fill=(52, 56, 60, 255), width=1)
    for mx, my, mr in ((22, 86, 6), (32, 88, 7), (44, 87, 6), (54, 85, 5), (26, 20, 4)):
        d.ellipse(
            [mx - mr, my - mr // 2, mx + mr, my + mr // 2],
            fill=(44, 76, 38, 255),
            outline=(22, 38, 20, 255),
        )
    hs1.save(props_dir / "headstone_1.png")

    hs2 = Image.new("RGBA", (76, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(hs2)
    d.ellipse([12, 76, 64, 92], fill=(20, 28, 18, 190))
    # Slightly tilted, notched ancient slate marker
    poly_side = [(20, 16), (56, 12), (60, 84), (16, 84)]
    poly_face = [(18, 16), (50, 12), (54, 84), (16, 84)]
    d.polygon(poly_side, fill=(56, 60, 64, 255), outline=(18, 18, 22, 255))
    d.polygon(poly_face, fill=(92, 98, 104, 255), outline=(18, 18, 22, 255))
    d.line([(20, 17), (49, 14)], fill=(138, 142, 148, 255), width=2)
    d.line([(42, 14), (34, 34), (44, 48)], fill=(24, 24, 28, 255), width=2)
    for my in (32, 44, 56):
        d.line([(24, my), (46, my - 2)], fill=(48, 52, 56, 255), width=2)
    for mx, my, mr in ((20, 82, 6), (34, 84, 8), (48, 82, 6)):
        d.ellipse(
            [mx - mr, my - mr // 2, mx + mr, my + mr // 2],
            fill=(42, 74, 36, 255),
            outline=(20, 36, 18, 255),
        )
    hs2.save(props_dir / "headstone_2.png")

    # Stacked Stone Burial Cairn (128x112)
    cairn = Image.new("RGBA", (128, 112), (0, 0, 0, 0))
    d = ImageDraw.Draw(cairn)
    d.ellipse([12, 72, 116, 106], fill=(18, 26, 18, 200))
    # Stack boulder tiers from bottom to top so upper stones overlap lower stones cleanly
    cairn_boulders = [
        # Base tier
        (34, 86, 20, 13, (82, 86, 92)),
        (64, 88, 22, 14, (92, 96, 102)),
        (92, 84, 18, 12, (78, 82, 88)),
        (24, 76, 16, 11, (88, 92, 96)),
        (102, 74, 15, 11, (84, 88, 94)),
        # Lower-mid tier
        (46, 72, 21, 14, (98, 102, 108)),
        (78, 72, 20, 13, (90, 94, 100)),
        (34, 62, 16, 12, (94, 98, 104)),
        (90, 60, 15, 11, (86, 90, 96)),
        # Upper-mid tier
        (62, 56, 22, 14, (104, 108, 114)),
        (48, 44, 16, 11, (96, 100, 106)),
        (74, 44, 16, 11, (92, 96, 102)),
        # Crown tier
        (62, 32, 17, 12, (110, 114, 120)),
        (62, 20, 11, 8, (118, 122, 128)),
    ]
    for bx, by, brx, bry, bcol in cairn_boulders:
        _draw_organic_stone(d, bx, by, brx, bry, rng, bcol, shadow_below=True)
    # Moss patches nestled between cairn boulders
    for mx, my, mr in ((48, 80, 6), (76, 82, 7), (56, 64, 5), (70, 48, 5), (36, 88, 6)):
        d.ellipse(
            [mx - mr, my - mr // 2, mx + mr, my + mr // 2],
            fill=(46, 78, 40, 255),
            outline=(22, 38, 20, 255),
        )
    cairn.save(props_dir / "cairn_stones.png")

    # 4. Native 4x Bioluminescent Moonherb (72x72)
    mh = Image.new("RGBA", (72, 72), (0, 0, 0, 0))
    # Soft cyan bioluminescent ground glow
    yy, xx = np.mgrid[0:72, 0:72]
    dist_mh = np.sqrt((xx - 36.0) ** 2 + (yy - 40.0) ** 2)
    glow_a = np.clip((1.0 - dist_mh / 32.0) ** 2 * 95.0, 0.0, 95.0).astype(np.uint8)
    glow_arr = np.zeros((72, 72, 4), dtype=np.uint8)
    glow_arr[..., 0] = 90
    glow_arr[..., 1] = 210
    glow_arr[..., 2] = 235
    glow_arr[..., 3] = glow_a
    mh = Image.alpha_composite(mh, Image.fromarray(glow_arr, "RGBA"))
    d = ImageDraw.Draw(mh)
    d.ellipse([18, 46, 54, 62], fill=(16, 26, 28, 220))
    leaf_specs = [
        # (tip_x, tip_y, left_x, left_y, right_x, right_y)
        (14, 38, 24, 34, 26, 48),
        (58, 38, 46, 48, 48, 34),
        (18, 22, 30, 26, 26, 40),
        (54, 22, 46, 40, 42, 26),
        (28, 12, 36, 24, 28, 34),
        (44, 12, 44, 34, 36, 24),
        (36, 8, 42, 24, 30, 24),
    ]
    for tx, ty, lx, ly, rx_p, ry_p in leaf_specs:
        poly = [(36, 50), (lx, ly), (tx, ty), (rx_p, ry_p)]
        d.polygon(poly, fill=(58, 134, 156, 255), outline=(16, 28, 36, 255))
        inner = [
            (36, 47),
            ((lx + 36) // 2, (ly + 47) // 2),
            (tx, ty + 3),
            ((rx_p + 36) // 2, (ry_p + 47) // 2),
        ]
        d.polygon(inner, fill=(124, 212, 232, 255))
        d.line([(36, 48), (tx, ty + 2)], fill=(215, 252, 255, 255), width=2)
    mh.save(props_dir / "moonherb.png")

    # 5. Native 4x Iron Scrap (80x64)
    sc = Image.new("RGBA", (80, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(sc)
    d.ellipse([10, 28, 70, 56], fill=(22, 18, 16, 185))
    # Heavy bent iron hull bracket + rivet plate + chain links
    d.polygon(
        [(12, 38), (48, 18), (68, 30), (34, 52)],
        fill=(76, 82, 90, 255),
        outline=(18, 18, 22, 255),
    )
    d.polygon([(15, 36), (47, 20), (63, 29), (33, 47)], fill=(104, 110, 120, 255))
    d.line([(16, 35), (47, 20)], fill=(158, 164, 174, 255), width=2)
    # Rusted cross-strap
    d.polygon(
        [(18, 22), (34, 14), (58, 38), (44, 48)],
        fill=(118, 66, 42, 255),
        outline=(18, 18, 22, 255),
    )
    d.line([(21, 22), (54, 39)], fill=(154, 92, 58, 255), width=2)
    # Rivet heads
    for rx_p, ry_p in ((26, 32), (38, 26), (48, 32), (34, 42)):
        d.ellipse(
            [rx_p - 3, ry_p - 2, rx_p + 3, ry_p + 2],
            fill=(162, 168, 178, 255),
            outline=(22, 22, 26, 255),
        )
    sc.save(props_dir / "iron_scrap.png")

    # 6. Animated 4-Frame Campfire Sheet (384x85) + Warm Additive Fire Glow (128x128)
    base_fire = Image.open(props_dir / "campfire_lit.png").convert("RGBA")
    fw, fh = base_fire.size  # 96x85
    sheet = Image.new("RGBA", (fw * 4, fh), (0, 0, 0, 0))
    base_arr = np.array(base_fire)

    for f_idx in range(4):
        frame = base_arr.copy()
        # Animate the flame region (y in 8..60, x in 24..72) where warm orange/yellow pixels live
        for y in range(6, 58):
            for x in range(22, 74):
                r, g, b, a = base_arr[y, x]
                if a > 0 and r > 150 and r > b + 45:
                    # Horizontal wave shift + vertical tongue flicker
                    wave_x = round(math.sin(y * 0.24 + f_idx * math.pi * 0.5) * 2.2)
                    wave_y = round(math.cos(x * 0.22 - f_idx * math.pi * 0.5) * 1.8)
                    ny = max(4, min(57, y + wave_y))
                    nx = max(20, min(75, x + wave_x))
                    boost = 1.0 + 0.12 * math.sin(f_idx * math.pi * 0.5 + y * 0.15)
                    frame[ny, nx, 0] = min(255, int(r * boost))
                    frame[ny, nx, 1] = min(255, int(g * boost))
                    frame[ny, nx, 2] = b
                    frame[ny, nx, 3] = 255
        fim = Image.fromarray(frame, "RGBA")
        fd = ImageDraw.Draw(fim)
        # Rising ember sparks that ascend across the 4 frames
        sparks = [
            (42, 22 - f_idx * 4),
            (54, 18 - ((f_idx + 2) % 4) * 4),
            (48, 14 - ((f_idx + 1) % 4) * 3),
            (38, 26 - ((f_idx + 3) % 4) * 4),
        ]
        for sx, sy in sparks:
            if 2 <= sy < 40:
                fd.rectangle([sx, sy, sx + 2, sy + 2], fill=(255, 210, 75, 255))
                fd.point((sx + 1, sy), fill=(255, 248, 185, 255))
        sheet.alpha_composite(fim, (f_idx * fw, 0))

    sheet.save(props_dir / "campfire_lit_sheet.png")

    # Soft radial fire & window glow textures
    glow_sz = 128
    gy, gx = np.mgrid[0:glow_sz, 0:glow_sz]
    gr = np.sqrt(((gx - 64.0) / 60.0) ** 2 + ((gy - 64.0) / 60.0) ** 2)
    falloff = np.clip(1.0 - gr, 0.0, 1.0) ** 2.2
    fglow = np.zeros((glow_sz, glow_sz, 4), dtype=np.uint8)
    fglow[..., 0] = 255
    fglow[..., 1] = np.clip(155 + (1.0 - gr) * 75, 140, 235).astype(np.uint8)
    fglow[..., 2] = 55
    fglow[..., 3] = (falloff * 185.0).astype(np.uint8)
    Image.fromarray(fglow, "RGBA").save(props_dir / "fire_glow.png")
    print(
        "wrote native 4x assets/props/{rathole,open_grave,headstone_1,headstone_2,"
        "cairn_stones,moonherb,iron_scrap,campfire_lit_sheet,fire_glow}.png"
    )


def build_modular_buildings_and_smoke() -> None:
    """Extracts and saves modular building assets in `assets/buildings/parts/`:
    - chimney_stone.png
    - chimney_smoke_sheet.png (6 frames of curling hearth smoke)
    - window_amber.png, window_dormer.png, door_timber.png, window_glow.png
    Strips the static painted smoke from `mayor_hall.png` so only moving smoke is shown,
    brightens window panes, and builds additional modular village houses."""
    parts_dir = ROOT / "assets" / "buildings" / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    wm_dir = ROOT / "assets" / "wrackmouth"

    hall_path = wm_dir / "mayor_hall.png"
    hall = Image.open(hall_path).convert("RGBA")
    hall_arr = np.array(hall)

    # 1. Strip the static painted smoke wisp from MayorHall (y < 62, x in 345..395)
    hall_arr[:62, 345:395] = [0, 0, 0, 0]

    # Clean stone chimney stack on MayorHall is around x=346..388, y=62..146
    clean_hall = Image.fromarray(hall_arr, "RGBA")
    chimney_crop = clean_hall.crop((346, 62, 388, 146))
    chimney_crop.save(parts_dir / "chimney_stone.png")

    # Save modular windows and timber double-doors
    win_amber = hall.crop((46, 300, 86, 368))
    win_amber.save(parts_dir / "window_amber.png")
    win_dormer = hall.crop((250, 210, 316, 286))
    win_dormer.save(parts_dir / "window_dormer.png")
    door_timber = hall.crop((92, 326, 174, 456))
    door_timber.save(parts_dir / "door_timber.png")

    # Soft, warm golden-amber window glow texture (128x128)
    glow_sz = 128
    gy, gx = np.mgrid[0:glow_sz, 0:glow_sz]
    gr = np.sqrt(((gx - 64.0) / 58.0) ** 2 + ((gy - 64.0) / 58.0) ** 2)
    falloff = np.clip(1.0 - gr, 0.0, 1.0) ** 2.0
    wglow = np.zeros((glow_sz, glow_sz, 4), dtype=np.uint8)
    wglow[..., 0] = 255
    wglow[..., 1] = 195
    wglow[..., 2] = 85
    wglow[..., 3] = (falloff * 210.0).astype(np.uint8)
    Image.fromarray(wglow, "RGBA").save(parts_dir / "window_glow.png")

    # Brighten and warm up all lit window panes across every building in Wrackmouth
    for b_file in (
        "mayor_hall.png",
        "forge.png",
        "salt_gull.png",
        "cottage_harrow.png",
        "cottage_rook.png",
        "lantern_watch.png",
    ):
        b_path = wm_dir / b_file
        if not b_path.exists():
            continue
        b_arr = (
            hall_arr.copy()
            if b_file == "mayor_hall.png"
            else np.array(Image.open(b_path).convert("RGBA"))
        )
        # Strip any static painted smoke from Forge and Salt Gull chimney tops
        if b_file == "forge.png":
            b_arr[:29, 88:114] = [0, 0, 0, 0]
        elif b_file == "salt_gull.png":
            b_arr[:24, 400:435] = [0, 0, 0, 0]
        r = b_arr[..., 0].astype(np.float32)
        g = b_arr[..., 1].astype(np.float32)
        b = b_arr[..., 2].astype(np.float32)
        a = b_arr[..., 3] > 0
        # Detect warm amber window pane pixels (high R & G, much lower B)
        is_pane = a & (r > 155.0) & (g > 95.0) & (r > b + 55.0) & (g > b + 25.0)
        b_arr[is_pane, 0] = np.clip(r[is_pane] * 1.18 + 22.0, 210.0, 255.0).astype(
            np.uint8
        )
        b_arr[is_pane, 1] = np.clip(g[is_pane] * 1.22 + 24.0, 155.0, 248.0).astype(
            np.uint8
        )
        b_arr[is_pane, 2] = np.clip(b[is_pane] * 1.10 + 18.0, 65.0, 165.0).astype(
            np.uint8
        )
        Image.fromarray(b_arr, "RGBA").save(b_path)

    # 2. Build 6-frame Animated Chimney Smoke Sheet (384x128 = 6 frames of 64x128)
    n_frames = 6
    sw, sh = 64, 128
    smoke_sheet = Image.new("RGBA", (sw * n_frames, sh), (0, 0, 0, 0))
    for f_i in range(n_frames):
        phase = f_i / float(n_frames)
        fim = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fim)
        # Draw 5 rising smoke puffs per frame; as each puff rises from y=112 to y=12,
        # it drifts gently right, sways sinusoidally, expands in radius, and fades out
        for p_idx in range(5):
            t = (p_idx + phase) / 5.0  # 0.0 at chimney mouth -> 1.0 at top dissipation
            py = 114.0 - t * 98.0
            px = (
                28.0
                + t * 14.0
                + math.sin(t * math.pi * 2.5 + phase * math.tau * 0.0) * 5.5
            )
            rad_x = 6.0 + t * 12.0
            rad_y = 5.0 + t * 9.5
            # Alpha bell curve: fades in right at mouth, peaks at t=0.35, fades out at top
            alpha = round(math.sin(t * math.pi) ** 0.85 * (1.0 - t * 0.45) * 185.0)
            if alpha <= 4:
                continue
            # Dark underside of smoke puff
            fd.ellipse(
                [px - rad_x, py - rad_y + 2, px + rad_x, py + rad_y + 2],
                fill=(118, 124, 134, int(alpha * 0.75)),
            )
            # Main smoke puff body
            fd.ellipse(
                [px - rad_x, py - rad_y, px + rad_x, py + rad_y],
                fill=(168, 174, 184, alpha),
            )
            # Bright sunlit top-left wisp highlight
            fd.ellipse(
                [
                    px - rad_x * 0.65 - 1.5,
                    py - rad_y * 0.65 - 1.5,
                    px + rad_x * 0.35,
                    py + rad_y * 0.35,
                ],
                fill=(212, 218, 226, int(alpha * 0.85)),
            )
        fim = fim.filter(ImageFilter.GaussianBlur(radius=0.8))
        # Quantize alpha & RGB slightly so it blends pixel-art crispness with soft smoke translucency
        farr = np.array(fim)
        farr[..., 3] = (farr[..., 3] // 16) * 16
        smoke_sheet.alpha_composite(Image.fromarray(farr, "RGBA"), (f_i * sw, 0))

    smoke_sheet.save(parts_dir / "chimney_smoke_sheet.png")

    # 3. Assemble Modular Village Houses (`cottage_weaver.png` & `boathouse.png`)
    # Cottage Weaver: built from Harrow cottage base + modular stone chimney + glowing dormer window
    harrow = Image.open(wm_dir / "cottage_harrow.png").convert("RGBA")
    weaver = harrow.transpose(Image.FLIP_LEFT_RIGHT).copy()
    # Tint roof shingles slightly warmer slate-moss and attach chimney_crop on the right roof slope
    chim_small = chimney_crop.resize((40, 64), Image.NEAREST)
    weaver_canvas = Image.new("RGBA", (weaver.width, weaver.height + 16), (0, 0, 0, 0))
    weaver_canvas.alpha_composite(chim_small, (weaver.width - 78, 4))
    weaver_canvas.alpha_composite(weaver, (0, 16))
    weaver_canvas.save(wm_dir / "cottage_weaver.png")

    print(
        "wrote assets/buildings/parts/{chimney_stone,chimney_smoke_sheet,window_amber,"
        "window_dormer,door_timber,window_glow}.png and assets/wrackmouth/cottage_weaver.png"
    )


def make_icon_bg() -> Image.Image:
    """The dark rounded 64x64 frame every inventory item icon sits in."""
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(
        [2, 2, 61, 61],
        radius=8,
        fill=(22, 20, 28, 235),
        outline=(92, 82, 68, 255),
        width=2,
    )
    d.rounded_rectangle(
        [5, 5, 58, 58],
        radius=6,
        outline=(46, 42, 52, 255),
        width=1,
    )
    return im


def build_combat_sheets_and_icons() -> None:
    """Builds 4x4 Hero Combat sprite sheets (`hero_punch_sheet.png` and `hero_block_sheet.png`,
    384x512 each) that preserve exact palette-shader compatibility with `hero_sheet.png`,
    plus 64x64 thematic pixel-art item icons in `assets/ui/items/`."""
    hero_path = ROOT / "assets" / "hero" / "hero_sheet.png"
    hero = Image.open(hero_path).convert("RGBA")
    cw, ch = 96, 128

    punch_sheet = Image.new("RGBA", (cw * 4, ch * 4), (0, 0, 0, 0))
    block_sheet = Image.new("RGBA", (cw * 4, ch * 4), (0, 0, 0, 0))

    # Skin/wrap/outline colors matching `hero_sheet.png` so `character_palette.gdshader`
    # automatically recolors skin/cloth/hair on combat frames too!
    outline = (20, 16, 18, 255)
    skin_dk = (168, 102, 68, 255)
    skin_md = (204, 134, 94, 255)
    skin_lt = (232, 164, 122, 255)
    wrap_dk = (92, 74, 56, 255)
    wrap_lt = (132, 108, 82, 255)

    for row in range(4):
        idle = hero.crop((0, row * ch, cw, (row + 1) * ch))
        stride = hero.crop((cw, row * ch, cw * 2, (row + 1) * ch))

        # --- PUNCH SHEET (4 columns: 0=guard, 1=jab, 2=power windup, 3=power haymaker) ---
        for col in range(4):
            base = (stride if col in (1, 3) else idle).copy()
            # Shift body 2px in attack direction on impact frames (col 1 & 3)
            dx_body, dy_body = 0, 0
            if col in (1, 3):
                mag = 2 if col == 1 else 4
                if row == 0:
                    dy_body = mag
                elif row == 1:
                    dy_body = -mag
                elif row == 2:
                    dx_body = -mag
                else:
                    dx_body = mag
            elif col == 2:
                # Wind-up pulls back 2px
                if row == 0:
                    dy_body = -2
                elif row == 1:
                    dy_body = 2
                elif row == 2:
                    dx_body = 2
                else:
                    dx_body = -2

            cell = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            cell.alpha_composite(base, (dx_body, dy_body))
            d = ImageDraw.Draw(cell)

            if col == 1:
                # Normal Punch: extended fist + crisp white-silver motion arc
                if row == 0:  # Down
                    d.rounded_rectangle(
                        [30, 78, 43, 93], radius=3, fill=wrap_dk, outline=outline
                    )
                    d.rounded_rectangle(
                        [31, 84, 42, 95], radius=3, fill=skin_md, outline=outline
                    )
                    d.rectangle([33, 86, 40, 91], fill=skin_lt)
                    d.arc(
                        [24, 80, 50, 102],
                        start=20,
                        end=160,
                        fill=(235, 240, 248, 230),
                        width=2,
                    )
                elif row == 1:  # Up
                    d.rounded_rectangle(
                        [54, 56, 66, 70], radius=3, fill=wrap_dk, outline=outline
                    )
                    d.rounded_rectangle(
                        [55, 50, 65, 60], radius=3, fill=skin_md, outline=outline
                    )
                    d.arc(
                        [48, 42, 72, 64],
                        start=200,
                        end=340,
                        fill=(235, 240, 248, 230),
                        width=2,
                    )
                elif row == 2:  # Left
                    d.rounded_rectangle(
                        [14, 70, 34, 81], radius=3, fill=wrap_lt, outline=outline
                    )
                    d.rounded_rectangle(
                        [8, 69, 20, 81], radius=3, fill=skin_md, outline=outline
                    )
                    d.rectangle([10, 71, 16, 77], fill=skin_lt)
                    d.arc(
                        [2, 62, 26, 88],
                        start=110,
                        end=250,
                        fill=(235, 240, 248, 230),
                        width=2,
                    )
                else:  # Right
                    d.rounded_rectangle(
                        [62, 70, 82, 81], radius=3, fill=wrap_lt, outline=outline
                    )
                    d.rounded_rectangle(
                        [76, 69, 88, 81], radius=3, fill=skin_md, outline=outline
                    )
                    d.rectangle([80, 71, 86, 77], fill=skin_lt)
                    d.arc(
                        [70, 62, 94, 88],
                        start=-70,
                        end=70,
                        fill=(235, 240, 248, 230),
                        width=2,
                    )

            elif col == 2:
                # Power Attack Wind-up: coiled glowing fist
                fx, fy = (
                    (62, 72)
                    if row == 0
                    else (
                        (34, 68) if row == 1 else ((52, 72) if row == 2 else (44, 72))
                    )
                )
                d.ellipse([fx - 9, fy - 9, fx + 9, fy + 9], fill=(255, 175, 45, 115))
                d.rounded_rectangle(
                    [fx - 6, fy - 6, fx + 6, fy + 6],
                    radius=3,
                    fill=skin_md,
                    outline=outline,
                )
                d.rectangle([fx - 3, fy - 3, fx + 3, fy + 2], fill=skin_lt)

            elif col == 3:
                # Power Attack Impact: heavy extended haymaker + golden shockwave crescent
                if row == 0:  # Down
                    d.rounded_rectangle(
                        [48, 80, 64, 98], radius=4, fill=wrap_lt, outline=outline
                    )
                    d.rounded_rectangle(
                        [48, 88, 64, 102], radius=4, fill=skin_md, outline=outline
                    )
                    d.rectangle([51, 90, 61, 98], fill=skin_lt)
                    d.arc(
                        [26, 78, 74, 112],
                        start=10,
                        end=170,
                        fill=(255, 185, 45, 255),
                        width=4,
                    )
                    d.arc(
                        [30, 82, 70, 110],
                        start=20,
                        end=160,
                        fill=(255, 245, 165, 255),
                        width=2,
                    )
                elif row == 1:  # Up
                    d.rounded_rectangle(
                        [32, 48, 48, 66], radius=4, fill=wrap_lt, outline=outline
                    )
                    d.rounded_rectangle(
                        [32, 42, 48, 56], radius=4, fill=skin_md, outline=outline
                    )
                    d.arc(
                        [22, 32, 70, 64],
                        start=190,
                        end=350,
                        fill=(255, 185, 45, 255),
                        width=4,
                    )
                    d.arc(
                        [26, 35, 66, 60],
                        start=200,
                        end=340,
                        fill=(255, 245, 165, 255),
                        width=2,
                    )
                elif row == 2:  # Left
                    d.rounded_rectangle(
                        [10, 66, 34, 80], radius=4, fill=wrap_lt, outline=outline
                    )
                    d.rounded_rectangle(
                        [4, 65, 18, 81], radius=4, fill=skin_md, outline=outline
                    )
                    d.rectangle([6, 68, 14, 76], fill=skin_lt)
                    d.arc(
                        [0, 52, 32, 94],
                        start=100,
                        end=260,
                        fill=(255, 185, 45, 255),
                        width=4,
                    )
                    d.arc(
                        [3, 56, 28, 90],
                        start=115,
                        end=245,
                        fill=(255, 245, 165, 255),
                        width=2,
                    )
                else:  # Right
                    d.rounded_rectangle(
                        [62, 66, 86, 80], radius=4, fill=wrap_lt, outline=outline
                    )
                    d.rounded_rectangle(
                        [78, 65, 92, 81], radius=4, fill=skin_md, outline=outline
                    )
                    d.rectangle([82, 68, 90, 76], fill=skin_lt)
                    d.arc(
                        [64, 52, 95, 94],
                        start=-80,
                        end=80,
                        fill=(255, 185, 45, 255),
                        width=4,
                    )
                    d.arc(
                        [68, 56, 92, 90],
                        start=-65,
                        end=65,
                        fill=(255, 245, 165, 255),
                        width=2,
                    )

            punch_sheet.alpha_composite(cell, (col * cw, row * ch))

        # --- BLOCK SHEET (2 Hands Up High Guard in all 4 directions) ---
        for col in range(4):
            cell = idle.copy()
            d = ImageDraw.Draw(cell)
            bob = -1 if col in (1, 2) else 0
            # Erase lowered resting hands (y in 76..92 on the outer sides) and draw BOTH wrapped
            # forearms & fists raised vertically in front of the face/upper chest ("2 hands up")!
            if (
                row == 0
            ):  # Facing Down: two wrapped forearms & fists held up at chest/chin level
                for fx in (34, 52):
                    # Wrapped vertical forearm
                    d.rounded_rectangle(
                        [fx, 58 + bob, fx + 10, 76 + bob],
                        radius=3,
                        fill=wrap_lt,
                        outline=outline,
                    )
                    d.line(
                        [(fx + 2, 64 + bob), (fx + 8, 64 + bob)], fill=wrap_dk, width=2
                    )
                    d.line(
                        [(fx + 2, 70 + bob), (fx + 8, 70 + bob)], fill=wrap_dk, width=2
                    )
                    # Raised clenched fist at chin/cheek guard height
                    d.rounded_rectangle(
                        [fx - 1, 49 + bob, fx + 11, 60 + bob],
                        radius=3,
                        fill=skin_md,
                        outline=outline,
                    )
                    d.rectangle([fx + 2, 51 + bob, fx + 8, 56 + bob], fill=skin_lt)
            elif (
                row == 1
            ):  # Facing Up: elbows & raised fists visible flanking head/shoulders
                for fx in (28, 58):
                    d.rounded_rectangle(
                        [fx, 54 + bob, fx + 10, 72 + bob],
                        radius=3,
                        fill=wrap_lt,
                        outline=outline,
                    )
                    d.rounded_rectangle(
                        [fx, 46 + bob, fx + 10, 56 + bob],
                        radius=3,
                        fill=skin_dk,
                        outline=outline,
                    )
            elif (
                row == 2
            ):  # Facing Left: both lead & rear forearms/fists raised in twin high guard
                # Rear (far) hand slightly ahead & higher
                d.rounded_rectangle(
                    [20, 54 + bob, 30, 72 + bob],
                    radius=3,
                    fill=wrap_dk,
                    outline=outline,
                )
                d.rounded_rectangle(
                    [19, 45 + bob, 30, 56 + bob],
                    radius=3,
                    fill=skin_dk,
                    outline=outline,
                )
                # Lead (near) hand & forearm
                d.rounded_rectangle(
                    [27, 57 + bob, 38, 76 + bob],
                    radius=3,
                    fill=wrap_lt,
                    outline=outline,
                )
                d.rounded_rectangle(
                    [26, 48 + bob, 38, 59 + bob],
                    radius=3,
                    fill=skin_md,
                    outline=outline,
                )
                d.rectangle([28, 50 + bob, 35, 55 + bob], fill=skin_lt)
            else:  # Facing Right: both lead & rear forearms/fists raised in twin high guard
                d.rounded_rectangle(
                    [66, 54 + bob, 76, 72 + bob],
                    radius=3,
                    fill=wrap_dk,
                    outline=outline,
                )
                d.rounded_rectangle(
                    [66, 45 + bob, 77, 56 + bob],
                    radius=3,
                    fill=skin_dk,
                    outline=outline,
                )
                d.rounded_rectangle(
                    [58, 57 + bob, 69, 76 + bob],
                    radius=3,
                    fill=wrap_lt,
                    outline=outline,
                )
                d.rounded_rectangle(
                    [58, 48 + bob, 70, 59 + bob],
                    radius=3,
                    fill=skin_md,
                    outline=outline,
                )
                d.rectangle([61, 50 + bob, 68, 55 + bob], fill=skin_lt)

            block_sheet.alpha_composite(cell, (col * cw, row * ch))

    punch_sheet.save(ROOT / "assets" / "hero" / "hero_punch_sheet.png")
    block_sheet.save(ROOT / "assets" / "hero" / "hero_block_sheet.png")
    print("wrote assets/hero/{hero_punch_sheet,hero_block_sheet}.png (384x512)")

    # --- ITEM ICONS (64x64 crisp pixel art in assets/ui/items/) ---
    items_dir = ROOT / "assets" / "ui" / "items"
    items_dir.mkdir(parents=True, exist_ok=True)
    props_dir = ROOT / "assets" / "props"

    # 1. Coin icon
    ic_coin = make_icon_bg()
    d = ImageDraw.Draw(ic_coin)
    for cx, cy, r_c in ((26, 36, 13), (38, 28, 14)):
        d.ellipse(
            [cx - r_c, cy - r_c, cx + r_c, cy + r_c],
            fill=(218, 168, 52, 255),
            outline=outline,
            width=2,
        )
        d.ellipse(
            [cx - r_c + 3, cy - r_c + 3, cx + r_c - 3, cy + r_c - 3],
            outline=(250, 218, 110, 255),
            width=2,
        )
        d.rectangle([cx - 2, cy - 5, cx + 2, cy + 5], fill=(164, 118, 32, 255))
    ic_coin.save(items_dir / "coin.png")

    # 2. Salvage Crate icon
    ic_crate = make_icon_bg()
    crate_sp = Image.open(ROOT / "assets" / "beach" / "crate.png").convert("RGBA")
    crate_thumb = crate_sp.resize((48, 40), Image.LANCZOS)
    ic_crate.alpha_composite(crate_thumb, (8, 12))
    ic_crate.save(items_dir / "salvage_crate.png")

    # 3. Iron Scrap icon
    ic_scrap = make_icon_bg()
    scrap_sp = (
        Image.open(props_dir / "iron_scrap.png")
        .convert("RGBA")
        .resize((52, 42), Image.LANCZOS)
    )
    ic_scrap.alpha_composite(scrap_sp, (6, 11))
    ic_scrap.save(items_dir / "iron_scrap.png")

    # 4. Moonherb icon
    ic_herb = make_icon_bg()
    herb_sp = (
        Image.open(props_dir / "moonherb.png")
        .convert("RGBA")
        .resize((50, 50), Image.LANCZOS)
    )
    ic_herb.alpha_composite(herb_sp, (7, 7))
    ic_herb.save(items_dir / "moonherb.png")

    # 5. Hex-marked Bone icon
    ic_bone = make_icon_bg()
    d = ImageDraw.Draw(ic_bone)
    d.line([(16, 48), (48, 16)], fill=(24, 20, 22, 255), width=11)
    d.line([(16, 48), (48, 16)], fill=(222, 212, 186, 255), width=7)
    for bx, by in ((14, 44), (20, 50), (44, 14), (50, 20)):
        d.ellipse(
            [bx - 5, by - 5, bx + 5, by + 5],
            fill=(232, 222, 198, 255),
            outline=outline,
            width=2,
        )
    # Glowing hex mark on bone shaft
    d.ellipse([26, 26, 38, 38], fill=(225, 68, 24, 220))
    d.line([(28, 28), (36, 36)], fill=(255, 195, 65, 255), width=2)
    d.line([(36, 28), (28, 36)], fill=(255, 195, 65, 255), width=2)
    ic_bone.save(items_dir / "hex_bone.png")

    # 6. Mayor's Letter icon
    ic_let = make_icon_bg()
    d = ImageDraw.Draw(ic_let)
    d.polygon(
        [(12, 18), (52, 14), (50, 48), (10, 44)],
        fill=(218, 202, 168, 255),
        outline=outline,
    )
    d.line([(14, 18), (32, 34), (50, 16)], fill=(168, 148, 116, 255), width=2)
    # Crimson wax seal
    d.ellipse([26, 28, 38, 40], fill=(172, 32, 38, 255), outline=outline, width=2)
    d.ellipse([29, 31, 35, 37], fill=(215, 58, 62, 255))
    ic_let.save(items_dir / "mayor_letter.png")

    # 7. Dov's Tally Stick icon
    ic_tally = make_icon_bg()
    d = ImageDraw.Draw(ic_tally)
    d.polygon(
        [(14, 44), (46, 14), (52, 20), (20, 50)],
        fill=(142, 98, 58, 255),
        outline=outline,
    )
    for step_i in range(5):
        tx = 22 + step_i * 5
        ty = 40 - step_i * 5
        d.line([(tx - 2, ty - 2), (tx + 2, ty + 2)], fill=(235, 215, 175, 255), width=2)
    ic_tally.save(items_dir / "carters_tally.png")
    print(
        "wrote assets/ui/items/{coin,salvage_crate,iron_scrap,moonherb,hex_bone,mayor_letter,carters_tally}.png"
    )


def build_all_modular() -> tuple[np.ndarray, np.ndarray]:
    dirt_tile, cobble_tile = build_organic_terrain_tiles()
    build_plaza_circle_asset(cobble_tile)
    build_hd_props_and_cemetery()
    build_modular_buildings_and_smoke()
    build_combat_sheets_and_icons()
    return dirt_tile, cobble_tile


if __name__ == "__main__":
    build_all_modular()
