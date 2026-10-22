"""Builds all game-ready pixel art assets from raw Gemini images and kitbashed components.

Run: python3 tools/build_all_art.py
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pixelize import pixelize, remove_background

ROOT = Path(__file__).resolve().parent.parent

NEW_RAW = ROOT / "assets" / "source" / "gemini" / "new"
OLD_BEACH_RAW = ROOT / "assets" / "source" / "gemini" / "beach"


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
    # Pale beige sand and dark wet-sand shadow at base of beach props
    is_pale_sand = (
        (a > 0) & (r > 150) & (g > 138) & (b > 95) & (r >= g - 6) & (g >= b + 12)
    )
    arr[is_pale_sand, 3] = 0
    # Also remove flat muddy-brown ground shadow blobs on the bottom 30% that are disconnected or border-adjacent
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
    # Erode 1-2px isolated crumbs left behind in the bottom 40%
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


def save_sprite(
    im: Image.Image,
    dst: Path,
    width: int,
    colors: int = 24,
    strip_sand: bool = False,
) -> Image.Image:
    key = np.array(im.convert("RGB"))[0, 0]
    rgba = remove_background(im, 165)
    if strip_sand:
        rgba = strip_sand_island(rgba)
    bbox = rgba.getchannel("A").getbbox()
    if bbox:
        rgba = rgba.crop(bbox)
    out = pixelize(rgba, width, colors, 128, key)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    print(f"wrote {dst.relative_to(ROOT)} ({out.width}x{out.height})")
    return out


def build_grounds() -> None:
    # 1. Beach ground (320x180)
    beach_src = Image.open(NEW_RAW / "beach_ground_png_1792624473688.jpg")
    beach_out = pixelize(beach_src, 320, 32, 128)
    if beach_out.height != 180:
        beach_out = beach_out.resize((320, 180), Image.NEAREST)
    beach_dst = ROOT / "assets" / "beach" / "ground.png"
    beach_out.save(beach_dst)
    print(f"wrote {beach_dst.relative_to(ROOT)} ({beach_out.width}x{beach_out.height})")

    # Build water mask for new beach ground (ocean at top + 2 tide pools)
    rgb = np.array(beach_out.convert("RGB")).astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    water = ((b > r + 10) & (g > r + 5)) | (
        (rgb.min(axis=2) > 155) & (np.abs(b - r) < 45)
    )
    # Keep top-half ocean (y < 68) and the two tide pools around (64, 108) and (250, 78)
    h, w = water.shape
    yy, xx = np.mgrid[0:h, 0:w]
    ocean_zone = yy < 66
    pool_west = ((xx - 66) / 28.0) ** 2 + ((yy - 110) / 22.0) ** 2 <= 1.0
    pool_east = ((xx - 250) / 28.0) ** 2 + ((yy - 78) / 20.0) ** 2 <= 1.0
    valid_water = water & (ocean_zone | pool_west | pool_east)
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[valid_water] = 180
    # Smooth gradient near shore edges
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

    # 2. Wrackmouth ground (640x420)
    wm_src = Image.open(NEW_RAW / "wrackmouth_ground_png_1792624491205.jpg").resize(
        (1280, 840), Image.BILINEAR
    )
    wm_out = pixelize(wm_src, 640, 32, 128)
    if wm_out.height != 420:
        wm_out = wm_out.resize((640, 420), Image.NEAREST)
    wm_dst = ROOT / "assets" / "wrackmouth" / "ground.png"
    wm_dst.parent.mkdir(parents=True, exist_ok=True)
    wm_out.save(wm_dst)
    print(f"wrote {wm_dst.relative_to(ROOT)} ({wm_out.width}x{wm_out.height})")

    # 3. Crossholm road ground (640x360)
    cr_src = Image.open(NEW_RAW / "crossholm_road_ground_png_1792624507900.jpg")
    cr_out = pixelize(cr_src, 640, 32, 128)
    if cr_out.height != 360:
        cr_out = cr_out.resize((640, 360), Image.NEAREST)
    cr_dst = ROOT / "assets" / "crossholm_road" / "ground.png"
    cr_dst.parent.mkdir(parents=True, exist_ok=True)
    cr_out.save(cr_dst)
    print(f"wrote {cr_dst.relative_to(ROOT)} ({cr_out.width}x{cr_out.height})")


def build_buildings() -> None:
    wm_dir = ROOT / "assets" / "wrackmouth"
    cr_dir = ROOT / "assets" / "crossholm_road"
    wm_dir.mkdir(parents=True, exist_ok=True)
    cr_dir.mkdir(parents=True, exist_ok=True)

    hall = save_sprite(
        Image.open(NEW_RAW / "mayor_hall_1792624473522.jpg"),
        wm_dir / "mayor_hall.png",
        width=116,
        colors=28,
    )
    save_sprite(
        Image.open(NEW_RAW / "forge_1792624501091.jpg"),
        wm_dir / "forge.png",
        width=96,
        colors=28,
    )
    save_sprite(
        Image.open(NEW_RAW / "cottage_harrow_1792624473913.jpg"),
        wm_dir / "cottage_harrow.png",
        width=74,
        colors=24,
    )
    save_sprite(
        Image.open(NEW_RAW / "cottage_rook_1792624489518.jpg"),
        wm_dir / "cottage_rook.png",
        width=68,
        colors=24,
    )
    shuttered = save_sprite(
        Image.open(NEW_RAW / "cottage_shuttered_1792624502404.jpg"),
        wm_dir / "cottage_shuttered.png",
        width=68,
        colors=24,
    )

    # Build Salt Gull Inn from the second two-wing medieval building (`forge_1792624487817.jpg`)
    inn_raw = Image.open(NEW_RAW / "forge_1792624487817.jpg")
    inn_rgba = remove_background(inn_raw, 165)
    arr = np.array(inn_rgba)
    # Paint over the "KELL'S FORGE" text on the wooden signboard (x: 390..485, y: 435..530) with warm wood + white gull icon
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
    # Light up only the dark interior glass panes of the dormer and side windows
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
    inn_out = pixelize(inn_cropped, 124, 28, 128)
    inn_out.save(wm_dir / "salt_gull.png")
    print(f"wrote assets/wrackmouth/salt_gull.png ({inn_out.width}x{inn_out.height})")

    # Build Lantern Watch Tower (54x88) by extending Rook cottage into a 2-story stone-and-timber watchtower
    rook = Image.open(wm_dir / "cottage_rook.png")
    tower = build_lantern_watch(rook, hall)
    tower.save(wm_dir / "lantern_watch.png")
    print(f"wrote assets/wrackmouth/lantern_watch.png ({tower.width}x{tower.height})")

    # Build Burned Farm Ruins (82x60) from shuttered cottage with charred palette & glowing embers
    burned = build_burned_farm(shuttered)
    burned.save(cr_dir / "burned_farm.png")
    print(
        f"wrote assets/crossholm_road/burned_farm.png ({burned.width}x{burned.height})"
    )

    # Build Crossholm Garrison Gate & Walls
    gate, wall_n, wall_s = build_crossholm_fortifications(hall)
    gate.save(cr_dir / "gate.png")
    wall_n.save(cr_dir / "wall_north.png")
    wall_s.save(cr_dir / "wall_south.png")
    print(
        f"wrote assets/crossholm_road/gate.png ({gate.width}x{gate.height}), "
        f"wall_north.png ({wall_n.width}x{wall_n.height}), wall_south.png ({wall_s.width}x{wall_s.height})"
    )


def build_lantern_watch(rook: Image.Image, hall: Image.Image) -> Image.Image:
    """Constructs a 54x88 2-story coastal watchtower seamlessly from Rook cottage."""
    # Narrow rook (68x70) to 54x68 for a tower footprint
    slim = rook.resize((54, 68), Image.NEAREST)
    # Slice into roof+upper story (y: 0..46), middle wall+window band (y: 26..48), and lower door+stone base (y: 38..68)
    top_part = slim.crop((0, 0, 54, 46))
    mid_band = slim.crop((0, 28, 54, 48))
    bot_part = slim.crop((0, 38, 54, 68))

    img = Image.new("RGBA", (54, 88), (0, 0, 0, 0))
    img.alpha_composite(bot_part, (0, 58))
    img.alpha_composite(mid_band, (0, 40))
    img.alpha_composite(top_part, (0, 0))
    # Add warm beacon glow in the upper gable window (x: 14..22, y: 24..32)
    win = hall.crop((19, 55, 27, 66))
    img.alpha_composite(win, (14, 24))
    return img


def build_burned_farm(shuttered: Image.Image) -> Image.Image:
    """Creates a charred, smoking farmhouse ruin from shuttered cottage with glowing embers."""
    arr = np.array(shuttered.convert("RGBA")).astype(float)
    alpha = arr[..., 3] > 0
    # Char and darken wood/stone into soot & ash
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    arr[alpha, 0] = np.clip(lum[alpha] * 0.42 + 8, 12, 75)
    arr[alpha, 1] = np.clip(lum[alpha] * 0.36 + 5, 10, 62)
    arr[alpha, 2] = np.clip(lum[alpha] * 0.34 + 5, 10, 58)
    out = arr.astype(np.uint8)
    h, w = out.shape[:2]
    rng = np.random.default_rng(99)
    # Add glowing orange/red embers in the collapsed roof gaps and lower beams
    for y in range(int(h * 0.25), int(h * 0.88)):
        for x in range(int(w * 0.18), int(w * 0.82)):
            if out[y, x, 3] > 0 and out[y, x, 0] > 28 and rng.random() < 0.045:
                out[y, x, :3] = [235, 95, 25]
                if x + 1 < w and out[y, x + 1, 3] > 0:
                    out[y, x + 1, :3] = [255, 165, 45]
    return Image.fromarray(out, "RGBA")


def build_crossholm_fortifications(
    hall: Image.Image,
) -> tuple[Image.Image, Image.Image, Image.Image]:
    """Builds fortified stone garrison walls (north & south) and the closed oak/iron gatehouse
    using organic weathered stone masonry and iron-studded oak doors from MayorHall."""
    # Sample a clean horizontal stone masonry block from hall (x: 13..26, y: 74..92)
    stone_course = hall.crop((13, 75, 26, 91))
    door_patch = hall.crop((28, 70, 45, 96))

    def make_wall(w: int, h: int, seed: int) -> Image.Image:
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for ty in range(0, h, 14):
            offset = ((ty // 14) % 2) * 6
            for tx in range(-offset, w, 12):
                im.paste(stone_course, (tx, ty))
        arr = np.array(im).astype(float)
        # Moody highland stone shading with parapet highlight on left edge
        for x in range(w):
            if x < 9:
                shade = 0.72
            elif x < 12:
                shade = 0.42
            else:
                shade = 0.56 - 0.16 * ((x - 12) / max(1, w - 12))
            arr[:, x, :3] = np.clip(arr[:, x, :3] * shade, 14, 165)
        u = arr.astype(np.uint8)
        u[..., 3] = 255
        # Crenellations along the front-facing left parapet edge
        for y in range(5, h - 6, 14):
            u[y : y + 5, 0:4, 3] = 0
            u[y : y + 5, 4, :3] = [18, 16, 20]
        # Crisp dark border outlines
        u[:, -1, :3] = [18, 16, 20]
        u[0, :, :3] = [18, 16, 20]
        u[-1, :, :3] = [18, 16, 20]
        for y in range(h):
            if u[y, 0, 3] > 0:
                u[y, 0, :3] = [18, 16, 20]
        return Image.fromarray(u, "RGBA")

    wall_n = make_wall(48, 170, 101)
    wall_s = make_wall(48, 146, 202)

    # Gatehouse (48x64) with stone bastion, iron-studded oak gate, and 2 lit wall torches
    gw, gh = 48, 64
    gate = make_wall(gw, gh, 303)
    # Heavy iron-studded double doors centered at road entrance
    gate.alpha_composite(door_patch.resize((22, 32), Image.NEAREST), (13, 31))
    d = ImageDraw.Draw(gate)
    for tx in (7, gw - 10):
        d.rectangle([tx, 36, tx + 2, 42], fill=(48, 32, 22, 255))
        d.rectangle([tx - 1, 32, tx + 3, 36], fill=(235, 145, 38, 255))
        d.point((tx + 1, 33), fill=(255, 225, 115, 255))
    return gate, wall_n, wall_s


def build_props() -> None:
    beach_dir = ROOT / "assets" / "beach"
    cr_dir = ROOT / "assets" / "crossholm_road"
    props_dir = ROOT / "assets" / "props"
    props_dir.mkdir(parents=True, exist_ok=True)

    # 1. New 2-legged wyvern skeleton on beach (no sand island!)
    save_sprite(
        Image.open(NEW_RAW / "wyvern_skeleton_png_1792624477339.jpg"),
        beach_dir / "wyvern_skeleton.png",
        width=68,
        colors=20,
    )

    # 2. Clean sand stickers off beach wreck, crate, dead_tree, driftwood, signpost, campfires
    save_sprite(
        Image.open(OLD_BEACH_RAW / "wreck.jpeg"),
        beach_dir / "wreck.png",
        width=96,
        colors=24,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "crate.jpeg"),
        beach_dir / "crate.png",
        width=40,
        colors=20,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "dead_tree.jpeg"),
        props_dir / "dead_tree.png",
        width=52,
        colors=20,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "driftwood.jpeg"),
        props_dir / "driftwood.png",
        width=42,
        colors=18,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "signpost.jpeg"),
        props_dir / "signpost.png",
        width=18,
        colors=16,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "campfire_lit.jpeg"),
        props_dir / "campfire_lit.png",
        width=24,
        colors=20,
        strip_sand=True,
    )
    save_sprite(
        Image.open(OLD_BEACH_RAW / "campfire_unlit.jpeg"),
        props_dir / "campfire_unlit.png",
        width=24,
        colors=18,
        strip_sand=True,
    )

    # 3. Overturned merchant cart on Crossholm Road
    save_sprite(
        Image.open(NEW_RAW / "overturned_cart_png_1792624490029.jpg"),
        cr_dir / "cart.png",
        width=56,
        colors=24,
    )

    # 4. Craft bespoke pixel art interactable sprites (replacing Polygon2D diamonds!)
    build_moonherb_sprite().save(props_dir / "moonherb.png")
    build_open_grave_sprite().save(props_dir / "open_grave.png")
    build_iron_scrap_sprite().save(props_dir / "iron_scrap.png")
    build_rathole_sprite().save(props_dir / "rathole.png")
    print("wrote assets/props/{moonherb,open_grave,iron_scrap,rathole}.png")


def build_moonherb_sprite() -> Image.Image:
    """18x18 glowing bioluminescent cyan-silver fantasy herb rosette."""
    im = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    out = (18, 24, 32, 255)
    stem = (42, 68, 62, 255)
    leaf_dk = (75, 145, 165, 255)
    leaf_md = (135, 215, 230, 255)
    leaf_lt = (210, 250, 255, 255)
    # Dark mossy base
    d.ellipse([4, 12, 13, 16], fill=out)
    d.ellipse([5, 12, 12, 15], fill=stem)
    # Radiating spade leaves
    leaves = [
        [(9, 13), (4, 9), (3, 5), (7, 7)],
        [(9, 13), (13, 9), (14, 5), (10, 7)],
        [(9, 12), (7, 6), (9, 2), (11, 6)],
        [(8, 14), (2, 13), (3, 10), (7, 11)],
        [(10, 14), (15, 13), (14, 10), (11, 11)],
    ]
    for poly in leaves:
        d.polygon(poly, fill=leaf_dk, outline=out)
    # Bright glowing veins/tips
    for px, py in ((9, 4), (9, 5), (5, 7), (12, 7), (4, 11), (13, 11), (8, 8), (10, 8)):
        d.point((px, py), fill=leaf_md)
    for px, py in ((9, 3), (5, 6), (12, 6), (9, 7)):
        d.point((px, py), fill=leaf_lt)
    return im


def build_open_grave_sprite() -> Image.Image:
    """32x24 cracked stone cairn tomb dug open with glowing red-orange hex sigil and bone."""
    im = Image.new("RGBA", (32, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    out = (20, 18, 22, 255)
    dirt = (48, 38, 30, 255)
    pit = (16, 12, 14, 255)
    stone_dk = (65, 68, 72, 255)
    stone_md = (95, 100, 104, 255)
    stone_lt = (128, 132, 136, 255)
    hex_dk = (185, 45, 20, 255)
    hex_lt = (255, 135, 35, 255)
    bone = (218, 210, 188, 255)

    # Spilled earth mound & dark pit opening
    d.ellipse([2, 8, 29, 22], fill=dirt, outline=out)
    d.rectangle([7, 10, 22, 19], fill=pit, outline=out)
    # Displaced cracked stone tomb slab tilted to the right
    d.polygon([(12, 5), (28, 8), (26, 18), (10, 15)], fill=stone_md, outline=out)
    d.line([(12, 6), (27, 9)], fill=stone_lt)
    d.line([(18, 7), (16, 15)], fill=out)  # crack across lid
    # Glowing arcane hex-sigil burned into the stone slab
    for px, py in ((19, 10), (20, 9), (21, 10), (22, 11), (20, 12), (18, 11), (21, 12)):
        d.point((px, py), fill=hex_dk)
    for px, py in ((20, 10), (20, 11), (21, 11)):
        d.point((px, py), fill=hex_lt)
    # Headstone cairn stones on left
    d.ellipse([3, 4, 11, 12], fill=stone_dk, outline=out)
    d.ellipse([4, 2, 10, 7], fill=stone_md, outline=out)
    # Scorched bone sticking out of the pit
    d.line([(9, 16), (14, 13)], fill=bone)
    d.point((8, 16), fill=bone)
    d.point((14, 12), fill=hex_lt)
    return im


def build_iron_scrap_sprite() -> Image.Image:
    """20x16 pile of salvaged rusted ship iron plates and chain."""
    im = Image.new("RGBA", (20, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    out = (18, 16, 20, 255)
    iron_dk = (58, 62, 68, 255)
    iron_md = (92, 98, 106, 255)
    iron_lt = (142, 148, 156, 255)
    rust = (138, 72, 42, 255)

    # Bent iron hull plate
    d.polygon([(3, 10), (12, 5), (17, 8), (9, 13)], fill=iron_md, outline=out)
    d.line([(5, 9), (11, 6)], fill=iron_lt)
    # Second iron bracket & rivets
    d.polygon([(2, 7), (8, 4), (11, 6), (5, 10)], fill=iron_dk, outline=out)
    for px, py in ((6, 6), (10, 9), (13, 8), (8, 11)):
        d.point((px, py), fill=rust)
    for px, py in ((7, 5), (14, 8), (9, 10)):
        d.point((px, py), fill=iron_lt)
    return im


def build_rathole_sprite() -> Image.Image:
    """18x14 dark stone cellar foundation burrow hole with rubble."""
    im = Image.new("RGBA", (18, 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    out = (16, 14, 18, 255)
    hole = (12, 10, 14, 255)
    stone_dk = (62, 64, 68, 255)
    stone_md = (92, 94, 98, 255)
    dirt = (68, 52, 38, 255)

    # Stone arch surround
    d.ellipse([2, 2, 15, 12], fill=stone_md, outline=out)
    d.chord([4, 4, 13, 13], start=180, end=360, fill=hole, outline=out)
    d.rectangle([4, 7, 13, 11], fill=hole)
    # Small cobbles and dirt outside hole
    d.ellipse([1, 9, 5, 13], fill=stone_dk, outline=out)
    d.ellipse([12, 9, 16, 13], fill=dirt, outline=out)
    return im


def build_characters() -> None:
    """Builds the 4x4 Hero sheet (96x128, cell 24x32) and 8 distinct custom NPC sheets."""
    im_a = remove_background(
        Image.open(NEW_RAW / "hero_sheet_png_1792624478858.jpg"), 165
    )

    def get_cell(im: Image.Image, r: int, c: int, target_h: int = 30) -> Image.Image:
        cw, ch = im.width // 4, im.height // 4
        cell = im.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
        bbox = cell.getchannel("A").getbbox()
        cell = cell.crop(bbox)
        target_w = max(1, round(cell.width * target_h / cell.height))
        small = (
            cell.convert("RGBa").resize((target_w, target_h), Image.BOX).convert("RGBA")
        )
        arr = np.array(small)
        arr[..., 3] = np.where(arr[..., 3] >= 120, 255, 0)
        return Image.fromarray(arr, "RGBA")

    def make_opposite_stride(stride: Image.Image, idle: Image.Image) -> Image.Image:
        """Creates the opposite-foot stride for side view by combining upper body of idle
        with horizontally mirrored lower legs of stride."""
        out = idle.copy()
        w, h = out.size
        leg_y = int(h * 0.68)
        legs = stride.crop((0, leg_y, w, h)).transpose(Image.FLIP_LEFT_RIGHT)
        out.paste((0, 0, 0, 0), (0, leg_y, w, h))
        out.alpha_composite(legs, (0, leg_y))
        return out

    # Assemble 4x4 grid (Down, Up, Left, Right) at 24x32 per cell = 96x128 sheet
    def assemble_base_sheet(target_h: int = 30) -> Image.Image:
        down = [
            get_cell(im_a, 0, 0, target_h),
            get_cell(im_a, 0, 1, target_h),
            get_cell(im_a, 0, 2, target_h),
            get_cell(im_a, 0, 3, target_h),
        ]
        up = [
            get_cell(im_a, 1, 0, target_h),
            get_cell(im_a, 1, 1, target_h),
            get_cell(im_a, 1, 2, target_h),
            get_cell(im_a, 1, 3, target_h),
        ]
        left_idle = get_cell(im_a, 2, 0, target_h)
        left_step1 = get_cell(im_a, 2, 1, target_h)
        left_step2 = make_opposite_stride(left_step1, left_idle)
        left = [left_idle, left_step1, left_idle, left_step2]

        right = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in left]

        cell_w, cell_h = 24, 32
        sheet = Image.new("RGBA", (cell_w * 4, cell_h * 4), (0, 0, 0, 0))
        for r, row in enumerate([down, up, left, right]):
            for c, frame in enumerate(row):
                x = c * cell_w + (cell_w - frame.width) // 2
                y = r * cell_h + cell_h - frame.height
                sheet.alpha_composite(frame, (x, y))

        alpha = np.array(sheet)[..., 3]
        quant = sheet.convert("RGB").quantize(
            colors=24, method=Image.MEDIANCUT, dither=Image.NONE
        )
        out = np.array(quant.convert("RGBA"))
        out[..., 3] = np.where(alpha >= 128, 255, 0)
        return Image.fromarray(out, "RGBA")

    hero_sheet = assemble_base_sheet(30)
    hero_dst = ROOT / "assets" / "hero" / "hero_sheet.png"
    hero_dst.parent.mkdir(parents=True, exist_ok=True)
    hero_sheet.save(hero_dst)
    print(
        f"wrote {hero_dst.relative_to(ROOT)} ({hero_sheet.width}x{hero_sheet.height})"
    )

    # Build 8 distinct NPC sprite sheets in assets/npc/
    npc_dir = ROOT / "assets" / "npc"
    npc_dir.mkdir(parents=True, exist_ok=True)

    npcs = {
        "mayor": {
            "hair": (145, 150, 158),  # silver-streaked grey hair
            "tunic": (38, 78, 56),  # dark pine-green magistrate coat
            "pants": (32, 58, 44),  # long coat hem
            "leather": (195, 158, 64),  # brass chain of office
            "beard": None,
            "chain": True,
            "height": 30,
        },
        "orsa": {
            "hair": (148, 68, 42),  # braided copper-auburn hair
            "tunic": (52, 54, 60),  # charcoal smith shirt
            "pants": (108, 68, 42),  # heavy leather smith apron
            "leather": (75, 78, 86),  # iron bracers
            "beard": None,
            "apron": (118, 74, 44),
            "height": 30,
        },
        "bram": {
            "hair": (92, 62, 38),  # brown hair
            "tunic": (135, 58, 48),  # warm burgundy-brown tavern vest
            "pants": (72, 58, 46),  # dark trousers
            "leather": (198, 184, 158),  # rolled cream linen sleeves
            "beard": (82, 52, 32),  # full bushy brown beard
            "apron": (178, 168, 148),
            "height": 30,
        },
        "teague": {
            "hair": (52, 68, 88),  # dark navy oilskin hood
            "tunic": (46, 62, 82),  # navy-slate watchman cloak
            "pants": (38, 48, 62),  # dark oilskins
            "leather": (185, 148, 62),  # brass lantern clasp
            "beard": (135, 138, 142),  # salt-and-pepper beard
            "height": 30,
        },
        "pell": {
            "hair": (155, 160, 164),  # sea-grey hair
            "tunic": (58, 88, 94),  # weathered teal-slate fisherman wool sweater
            "pants": (62, 58, 50),
            "leather": (98, 78, 56),
            "beard": (148, 152, 156),  # grey fisherman beard
            "height": 30,
        },
        "ansa": {
            "hair": (58, 44, 62),  # dark plum-charcoal widow's shawl
            "tunic": (68, 52, 74),  # mourning dress bodice
            "pants": (52, 40, 58),  # long dark skirt
            "leather": (88, 72, 92),
            "beard": None,
            "height": 29,
        },
        "wren": {
            "hair": (188, 148, 78),  # sandy-gold hair
            "tunic": (124, 78, 52),  # russet tunic
            "pants": (68, 76, 58),  # mossy trousers
            "leather": (92, 112, 68),  # green scarf/wraps
            "beard": None,
            "height": 27,  # younger/shorter lookout
        },
        "dov": {
            "hair": (78, 58, 42),
            "tunic": (118, 108, 76),  # olive-tan padded gambeson
            "pants": (68, 62, 52),
            "leather": (92, 96, 104),  # iron shoulder guard
            "beard": (72, 52, 38),
            "height": 30,
        },
    }

    for name, cfg in npcs.items():
        base = assemble_base_sheet(cfg["height"])
        styled = style_npc_sheet(base, cfg)
        dst = npc_dir / f"{name}.png"
        styled.save(dst)
        print(f"wrote {dst.relative_to(ROOT)} ({styled.width}x{styled.height})")


def style_npc_sheet(sheet: Image.Image, cfg: dict) -> Image.Image:
    """Applies custom pixel-art clothing palette and details (beard, apron, chain) per cell."""
    arr = np.array(sheet.convert("RGBA")).astype(int)
    cell_w, cell_h = 24, 32
    hair_col = np.array(cfg["hair"])
    tunic_col = np.array(cfg["tunic"])
    pants_col = np.array(cfg["pants"])
    leather_col = np.array(cfg["leather"])

    for r in range(4):
        for c in range(4):
            y0, y1 = r * cell_h, (r + 1) * cell_h
            x0, x1 = c * cell_w, (c + 1) * cell_w
            cell = arr[y0:y1, x0:x1]
            alpha = cell[..., 3] > 0
            if not alpha.any():
                continue
            ys = np.where(alpha)[0]
            top_y, bot_y = ys.min(), ys.max()
            span = max(1, bot_y - top_y)

            for py in range(top_y, bot_y + 1):
                rel_y = (py - top_y) / span
                for px in range(cell_w):
                    if cell[py, px, 3] == 0:
                        continue
                    pr, pg, pb = cell[py, px, :3]
                    lum = (0.299 * pr + 0.587 * pg + 0.114 * pb) / 255.0
                    # Preserve very dark outlines
                    if max(pr, pg, pb) < 38:
                        continue
                    # Skin pixels (warm peach/tan on face and hands)
                    is_skin = (
                        (pr > 145) and (pg > 95) and (pr - pb > 42) and (pr > pg + 18)
                    )
                    # Grey tunic pixels (low saturation)
                    is_grey = abs(pr - pg) <= 18 and abs(pg - pb) <= 18 and pr < 160

                    if rel_y < 0.44 and not is_skin:
                        # Hair / hood region
                        scale = np.clip(lum * 1.35, 0.45, 1.35)
                        cell[py, px, :3] = np.clip(hair_col * scale, 20, 245)
                    elif rel_y >= 0.40 and rel_y < 0.73:
                        if is_grey:
                            scale = np.clip(lum * 1.45, 0.5, 1.35)
                            cell[py, px, :3] = np.clip(tunic_col * scale, 20, 245)
                        elif not is_skin:
                            scale = np.clip(lum * 1.25, 0.5, 1.3)
                            cell[py, px, :3] = np.clip(leather_col * scale, 20, 245)
                    elif rel_y >= 0.73 and rel_y < 0.90:
                        if not is_skin:
                            scale = np.clip(lum * 1.35, 0.45, 1.3)
                            cell[py, px, :3] = np.clip(pants_col * scale, 20, 245)

            # Add custom pixel details (beard on front/side rows, brass chain, smith apron)
            if cfg.get("beard") is not None and r in (0, 2, 3):
                bcol = cfg["beard"]
                by = top_y + int(span * 0.36)
                if r == 0:
                    for bx in range(9, 15):
                        if cell[by, bx, 3] > 0:
                            cell[by, bx, :3] = bcol
                            if by + 1 < cell_h:
                                cell[by + 1, bx, :3] = [max(15, v - 20) for v in bcol]
                elif r == 2:
                    for bx in range(7, 11):
                        if cell[by, bx, 3] > 0:
                            cell[by, bx, :3] = bcol
                elif r == 3:
                    for bx in range(13, 17):
                        if cell[by, bx, 3] > 0:
                            cell[by, bx, :3] = bcol

            if cfg.get("chain") and r == 0:
                cy = top_y + int(span * 0.48)
                for dx, dy in (
                    (-3, 0),
                    (-2, 1),
                    (-1, 2),
                    (0, 2),
                    (1, 2),
                    (2, 1),
                    (3, 0),
                ):
                    cx = 12 + dx
                    if (
                        0 <= cy + dy < cell_h
                        and 0 <= cx < cell_w
                        and cell[cy + dy, cx, 3] > 0
                    ):
                        cell[cy + dy, cx, :3] = [225, 185, 72]

            if cfg.get("apron") is not None and r == 0:
                acol = cfg["apron"]
                for ay in range(top_y + int(span * 0.52), top_y + int(span * 0.82)):
                    for ax in range(9, 15):
                        if cell[ay, ax, 3] > 0:
                            cell[ay, ax, :3] = acol

    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def main() -> None:
    build_grounds()
    build_buildings()
    build_props()
    build_characters()


if __name__ == "__main__":
    main()
