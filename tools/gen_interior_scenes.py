"""Generates the house interior scenes for Wrackmouth in scenes/interiors/:
mayor_hall, forge, salt_gull (and its rented room salt_gull_room), lantern_watch, cottage_harrow, cottage_rook,
cottage_weaver, trader_shop.

Props are bottom-aligned sprites (the node sits at the prop's feet) drawn at 0.5 scale from
assets/interiors/furniture/. Rooms are sized so the 320x180 camera sees most of one.

Run: python3 tools/gen_interior_scenes.py
"""

from __future__ import annotations

from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from gen_town_scenes import SCHEDULED, Scene, v, interactable

INTERIORS_DIR = ROOT / "scenes" / "interiors"
INTERIORS_DIR.mkdir(parents=True, exist_ok=True)
FURNITURE = "res://assets/interiors/furniture/"

PLAYER_SCENE = "res://scenes/player/player.tscn"
HUD_SCENE = "res://scenes/ui/hud.tscn"
DLG_SCENE = "res://scenes/ui/dialogue_box.tscn"
NPC_SCENE = "res://scenes/npc/npc.tscn"

WOOD_FLOOR = "res://assets/interiors/floor_wood.png"
STONE_FLOOR = "res://assets/interiors/floor_stone.png"
TIMBER_WALL = "res://assets/interiors/wall_timber.png"
STONE_WALL = "res://assets/interiors/wall_stone.png"


def tex_size(name: str) -> tuple[int, int]:
    with Image.open(ROOT / "assets" / "interiors" / "furniture" / f"{name}.png") as im:
        return im.size


def door(
    s: Scene,
    name: str,
    x: float,
    y: float,
    building_id: str,
    building_name: str,
    target_scene: str,
    target_spawn: str,
    is_exit: bool = False,
    radius: float = 18.0,
) -> None:
    interactable(
        s,
        name,
        x,
        y,
        "res://scripts/world/building_door.gd",
        radius,
        building_id=f'"{building_id}"',
        building_name=f'"{building_name}"',
        target_scene=f'"{target_scene}"',
        target_spawn=f'"{target_spawn}"',
        is_exit="true" if is_exit else "false",
    )


def loot_container(
    s: Scene,
    name: str,
    x: float,
    y: float,
    container_id: str,
    container_name: str,
    loot: dict[str, int],
    radius: float = 16.0,
) -> None:
    loot_pairs = ", ".join(f'"{k}": {n}' for k, n in loot.items())
    interactable(
        s,
        name,
        x,
        y,
        "res://scripts/world/loot_container.gd",
        radius,
        container_id=f'"{container_id}"',
        container_name=f'"{container_name}"',
        loot=f"{{{loot_pairs}}}",
    )


def prop(
    s: Scene,
    name: str,
    tex: str,
    x: float,
    y: float,
    cw: float | None = None,
    ch: float = 8.0,
    scale: float = 0.5,
    solid: bool = True,
) -> None:
    """A Y-sorted prop whose feet are at (x, y); solid props block a cw x ch footprint at the feet."""
    w, h = tex_size(tex)
    s.node(name, "StaticBody2D", "Entities", position=v(x, y))
    s.node(
        "Sprite2D",
        "Sprite2D",
        f"Entities/{name}",
        scale=v(scale, scale),
        texture=s.ext("Texture2D", FURNITURE + tex + ".png"),
        offset=v(0, -h / 2.0),
    )
    if solid:
        s.node(
            "Shape",
            "CollisionShape2D",
            f"Entities/{name}",
            position=v(0.0, -ch / 2.0),
            shape=s.rect(cw if cw is not None else w * scale * 0.8, ch),
        )


def decor(s: Scene, name: str, tex: str, x: float, y: float, scale: float = 0.5, z: int = 0) -> None:
    """Non-solid picture on the wall or floor (windows, banners, rugs), feet at (x, y)."""
    _, h = tex_size(tex)
    props = {
        "position": v(x, y),
        "scale": v(scale, scale),
        "texture": s.ext("Texture2D", FURNITURE + tex + ".png"),
        "offset": v(0, -h / 2.0),
    }
    if z:
        props["z_index"] = str(z)
    s.node(name, "Sprite2D", ".", **props)


def window(s: Scene, name: str, x: float) -> None:
    decor(s, name, "window_wall", x, 40.0)
    s.node(
        name + "Light",
        "Sprite2D",
        ".",
        script=s.ext("Script", "res://scripts/world/day_light.gd"),
        position=v(x, 76.0),
        scale=v(0.5, 0.5),
        texture=s.ext("Texture2D", FURNITURE + "light_shaft.png"),
        z_index="1",
    )


def animated(
    s: Scene,
    name: str,
    x: float,
    y: float,
    sheet: str,
    frames: int,
    frame_h: float,
    glow: str,
    glow_scale: tuple[float, float],
    glow_offset: tuple[float, float],
    scale: float = 0.5,
    fps: float = 7.0,
    shape: tuple[float, float] | None = None,
    z_index: int = 0,
) -> None:
    """A prop with an animated sprite sheet and a pulsing additive halo (see animated_prop.gd)."""
    extra = {"z_index": str(z_index)} if z_index else {}
    s.node(
        name,
        "StaticBody2D",
        "Entities",
        position=v(x, y),
        script=s.ext("Script", "res://scripts/world/animated_prop.gd"),
        fps=f"{fps:g}",
        glow_texture=s.ext("Texture2D", FURNITURE + glow + ".png"),
        glow_scale=v(*glow_scale),
        glow_offset=v(*glow_offset),
        **extra,
    )
    s.node(
        "Sprite2D",
        "Sprite2D",
        f"Entities/{name}",
        scale=v(scale, scale),
        texture=s.ext("Texture2D", FURNITURE + sheet + ".png"),
        offset=v(0, -frame_h / 2.0),
        hframes=str(frames),
    )
    if shape:
        s.node("Shape", "CollisionShape2D", f"Entities/{name}", position=v(0, -shape[1] / 2.0), shape=s.rect(*shape))


def hearth(s: Scene, name: str, x: float, y: float, scale: float = 0.5) -> None:
    """A stone hearth with live flames and a warm halo; (x, y) is the hearth's feet."""
    w, h = tex_size("hearth")
    prop(s, name, "hearth", x, y, cw=w * scale * 0.8, ch=10.0, scale=scale)
    # The fire sits in the opening (texture px 48, 78); z_index 1 draws it over the stonework it sits behind.
    animated(
        s,
        name + "Fire",
        x,
        y - (h - 78) * scale + 0.5,
        "hearth_fire_sheet",
        4,
        40.0,
        "hearth_glow",
        (0.55 * scale / 0.5, 0.4 * scale / 0.5),
        (0.0, -10.0 * scale / 0.5),
        scale=scale,
        z_index=1,
    )


def candle(s: Scene, name: str, x: float, y: float) -> None:
    animated(
        s, name, x, y, "candle_stand", 1, 44.0, "candle_glow", (0.55, 0.55), (0.0, -17.0), fps=1.0, shape=(6.0, 5.0)
    )


def torch(s: Scene, name: str, x: float, y: float = 42.0) -> None:
    """A wall-mounted iron torch with animated flame and soft amber light."""
    decor(s, name + "Bracket", "torch_wall", x, y, scale=0.5, z=-1)
    animated(
        s,
        name + "Flame",
        x,
        y - 10.0,
        "torch_flame_sheet",
        4,
        32.0,
        "torch_glow",
        (0.5, 0.5),
        (0.0, -6.0),
        scale=0.5,
        fps=7.0,
        z_index=1,
    )


def bed(s: Scene, name: str, x: float, y: float, kind: str = "wood", cw: float = 36.0, ch: float = 14.0) -> None:
    """A bedstead asset ('wood', 'inn', or 'kid')."""
    tex = f"bed_{kind}" if not kind.startswith("bed_") else kind
    prop(s, name, tex, x, y, cw=cw, ch=ch, scale=0.5)


def chest(s: Scene, name: str, x: float, y: float, container_id: str, container_name: str, loot: dict[str, int]) -> None:
    prop(s, name + "Visual", "chest", x, y, cw=26.0, ch=9.0, scale=0.5)
    loot_container(s, name, x, y - 5.0, container_id, container_name, loot)


def npc(
    s: Scene,
    name: str,
    x: float,
    y: float,
    display_name: str,
    dialogue: str,
    sheet: str,
    facing_row: int = 0,
    behaviour: str = "stationary",
    wander_radius: float = 0.0,
) -> None:
    """Instances an interactive NPC; scheduled NPCs get their dialogue name as `npc_id`."""
    s.instance(
        name,
        "Entities",
        NPC_SCENE,
        position=v(x, y),
        display_name=f'"{display_name}"',
        npc_id=f'"{dialogue}"' if dialogue in SCHEDULED else '""',
        dialogue_path=f'"res://data/dialogue/{dialogue}.json"',
        sprite_sheet=s.ext("Texture2D", f"res://assets/npc/{sheet}.png"),
        facing_row=str(facing_row),
        behaviour=f'"{behaviour}"',
        wander_radius=f"{wander_radius:g}",
    )


def build_room_base(
    s: Scene,
    w: float,
    h: float,
    door_x: float,
    floor_tex: str,
    wall_tex: str,
    building_id: str,
    building_name: str,
    exit_name: str = "Wrackmouth",
    exit_scene: str = "res://scenes/world/wrackmouth.tscn",
) -> None:
    """Root, floor, wall header, perimeter collision, exit door, player, HUD and dialogue."""
    s.node(
        "Interior",
        "Node2D",
        None,
        script=s.ext("Script", "res://scripts/world/area_scene.gd"),
        area_size=f"Vector2i({int(w)}, {int(h)})",
        music_cue='"mus_wrackmouth"',
        ambience_cues='PackedStringArray("amb_fire")',
        is_outdoor="false",
        place_id=f'"{building_id}"',
    )
    s.node("WarmIndoorLight", "CanvasModulate", ".", color="Color(1.0, 0.96, 0.88, 1.0)")

    s.node(
        "Floor",
        "TextureRect",
        ".",
        offset_right=str(int(w) * 4),
        offset_bottom=str(int(h) * 4),
        scale=v(0.25, 0.25),
        texture=s.ext("Texture2D", floor_tex),
        stretch_mode="1",
        z_index="-2",
    )
    s.node(
        "WallHeader",
        "Sprite2D",
        ".",
        position=v(w / 2.0, 24.0),
        scale=v(w / 512.0, 0.5),
        texture=s.ext("Texture2D", wall_tex),
        z_index="-2",
    )

    s.node("Walls", "StaticBody2D", ".")
    s.node("TopWall", "CollisionShape2D", "Walls", position=v(w / 2.0, 24.0), shape=s.rect(w, 48.0))
    s.node("LeftWall", "CollisionShape2D", "Walls", position=v(8.0, h / 2.0), shape=s.rect(16.0, h))
    s.node("RightWall", "CollisionShape2D", "Walls", position=v(w - 8.0, h / 2.0), shape=s.rect(16.0, h))
    s.node("BottomWall", "CollisionShape2D", "Walls", position=v(w / 2.0, h - 6.0), shape=s.rect(w, 12.0))

    s.node(
        "DoorThreshold",
        "Sprite2D",
        ".",
        position=v(door_x, h - 8.0),
        scale=v(0.5, 0.5),
        texture=s.ext("Texture2D", "res://assets/interiors/furniture/interior_door_threshold.png"),
        z_index="-1",
    )

    s.node("Entities", "Node2D", ".", y_sort_enabled="true")
    s.node("Interactables", "Node2D", ".")
    s.node("Zones", "Node2D", ".")
    s.node("Spawns", "Node2D", ".")
    s.node("from_town", "Marker2D", "Spawns", position=v(door_x, h - 45.0))
    door(
        s,
        "DoorExit",
        door_x,
        h - 16.0,
        building_id,
        exit_name,
        exit_scene,
        "from_" + building_id,
        is_exit=True,
        radius=18.0,
    )
    s.instance("Player", "Entities", PLAYER_SCENE, position=v(door_x, h - 45.0))
    s.instance("Hud", ".", HUD_SCENE)
    s.instance("DialogueBox", ".", DLG_SCENE)


def rug(s: Scene, name: str, tex: str, x: float, y: float, scale: float = 0.5) -> None:
    decor(s, name, tex, x, y, scale=scale, z=-1)


def write(s: Scene, building_id: str) -> None:
    (INTERIORS_DIR / f"{building_id}.tscn").write_text(s.render())


# =============================================================================
# 1. Mayor's Hall
# =============================================================================
def gen_mayor_hall() -> None:
    s = Scene()
    w, h, dx = 340.0, 230.0, 170.0
    build_room_base(s, w, h, dx, WOOD_FLOOR, TIMBER_WALL, "mayor_hall", "Mayor's Hall")
    window(s, "WindowWest", 55.0)
    window(s, "WindowEast", 285.0)

    # Wall Torches with animated fire & soft amber glow
    torch(s, "TorchFarWest", 35.0, 42.0)
    torch(s, "TorchWest", 105.0, 42.0)
    torch(s, "TorchEast", 235.0, 42.0)
    torch(s, "TorchFarEast", 305.0, 42.0)

    decor(s, "BannerWest", "banner", 112.0, 46.0)
    decor(s, "BannerEast", "banner", 228.0, 46.0)
    rug(s, "AisleRug", "rug_woven", 170.0, 170.0, scale=0.7)
    rug(s, "FurRug", "fur_rug", 170.0, 112.0)

    hearth(s, "Hearth", 170.0, 74.0)
    candle(s, "CandleWest", 128.0, 86.0)
    candle(s, "CandleEast", 212.0, 86.0)
    prop(s, "MayorChair", "chair_wood", 170.0, 92.0, cw=18.0, ch=8.0)
    prop(s, "RecordsDesk", "desk_scrolls", 98.0, 108.0, cw=50.0, ch=10.0)
    prop(s, "RecordsStool", "stool", 98.0, 94.0, cw=10.0, ch=6.0)
    prop(s, "Cupboard", "cupboard", 48.0, 92.0, cw=32.0, ch=10.0)
    loot_container(s, "MayorDesk", 48.0, 88.0, "mayor_hall_cupboard", "Records Cupboard", {"coin": 8})
    chest(s, "MayorChest", 300.0, 98.0, "mayor_hall_chest", "Council Strongbox", {"coin": 18})
    prop(s, "WeaponRack", "weapon_rack", 296.0, 140.0, cw=30.0, ch=8.0)
    prop(s, "TableWest", "table_food", 95.0, 176.0, cw=44.0, ch=10.0)
    prop(s, "TableEast", "table_food", 245.0, 176.0, cw=44.0, ch=10.0)
    for nm, sx in (("StoolA", 66.0), ("StoolB", 124.0), ("StoolC", 216.0), ("StoolD", 274.0)):
        prop(s, nm, "stool", sx, 182.0, cw=10.0, ch=6.0)
    prop(s, "Sacks", "sacks", 36.0, 150.0, cw=30.0, ch=8.0)

    npc(s, "MayorTolle", 170.0, 108.0, "Mayor Maren Tolle", "mayor", "mayor")
    npc(s, "ChancellorAlden", 130.0, 122.0, "Chancellor Alden", "chancellor", "ansa")
    npc(s, "GuardVance", 124.0, 200.0, "Guard Vance", "guard", "guard", facing_row=3)
    write(s, "mayor_hall")


# =============================================================================
# 2. Kell's Forge
# =============================================================================
def gen_forge() -> None:
    s = Scene()
    w, h, dx = 300.0, 190.0, 150.0
    build_room_base(s, w, h, dx, STONE_FLOOR, STONE_WALL, "forge", "Kell's Forge")
    window(s, "WindowWest", 70.0)

    # Wall Torches with warm amber fire
    torch(s, "TorchWest", 40.0, 42.0)
    torch(s, "TorchMid", 120.0, 42.0)
    torch(s, "TorchEast", 260.0, 42.0)

    hearth(s, "ForgeHearth", 205.0, 78.0, scale=0.75)
    prop(s, "ToolRack", "tool_rack", 78.0, 80.0, cw=32.0, ch=8.0)
    prop(s, "Anvil", "anvil", 150.0, 118.0, cw=22.0, ch=8.0)
    prop(s, "Grindstone", "grindstone", 258.0, 128.0, cw=18.0, ch=8.0)
    prop(s, "CoalBin", "coal_bin", 262.0, 100.0, cw=22.0, ch=8.0)
    prop(s, "Trough", "trough", 96.0, 138.0, cw=30.0, ch=8.0)
    prop(s, "Barrels", "barrels", 34.0, 150.0, cw=34.0, ch=10.0)
    chest(s, "ScrapBin", 36.0, 104.0, "forge_scrap_bin", "Iron Scrap Bin", {"coin": 12, "iron_scrap": 2})
    chest(s, "ToolChest", 262.0, 160.0, "forge_tool_box", "Tool Chest", {"iron_scrap": 2, "coin": 6})
    npc(s, "OrsaKell", 185.0, 134.0, "Orsa Kell", "orsa", "orsa", behaviour="wander", wander_radius=14.0)
    write(s, "forge")


# =============================================================================
# 3. The Salt Gull Inn
# =============================================================================
def gen_salt_gull() -> None:
    s = Scene()
    w, h, dx = 340.0, 230.0, 170.0
    build_room_base(s, w, h, dx, WOOD_FLOOR, TIMBER_WALL, "salt_gull", "The Salt Gull")
    window(s, "WindowWest", 40.0)
    window(s, "WindowEast", 300.0)

    # Wall Torches around tavern hall
    torch(s, "TorchBarWest", 45.0, 42.0)
    torch(s, "TorchBarMid", 135.0, 42.0)
    torch(s, "TorchHearthEast", 205.0, 42.0)
    torch(s, "TorchEast", 305.0, 42.0)

    decor(s, "BottleShelf", "bottle_shelf", 98.0, 44.0)
    rug(s, "FurRug", "fur_rug", 170.0, 168.0)

    decor(s, "RoomDoorArt", "room_door", 170.0, 48.0)
    s.node(
        "RoomDoor",
        "Area2D",
        "Interactables",
        position=v(170.0, 60.0),
        collision_layer="2",
        collision_mask="0",
        monitoring="false",
        script=s.ext("Script", "res://scripts/world/room_rental_door.gd"),
        building_id='"salt_gull_room"',
        building_name='"Your Room"',
        target_scene='"res://scenes/interiors/salt_gull_room.tscn"',
        target_spawn='"from_town"',
        rent_cost="5",
    )
    s.node("Reach", "CollisionShape2D", "Interactables/RoomDoor", shape=s._sub("CircleShape2D", "radius = 16"))
    s.node("from_salt_gull_room", "Marker2D", "Spawns", position=v(170.0, 70.0))
    prop(s, "Bar", "counter_bar", 98.0, 100.0, cw=68.0, ch=12.0)
    prop(s, "Barrels", "barrels", 140.0, 86.0, cw=34.0, ch=10.0)
    hearth(s, "Hearth", 240.0, 76.0)
    candle(s, "CandleWest", 204.0, 90.0)
    candle(s, "CandleEast", 276.0, 90.0)

    # Upgraded Inn bed with fur throw
    bed(s, "GuestBed", 302.0, 112.0, "inn", cw=36.0, ch=14.0)

    prop(s, "TableNear", "table_food", 232.0, 150.0, cw=44.0, ch=10.0)
    prop(s, "TableFar", "table_food", 110.0, 170.0, cw=44.0, ch=10.0)
    for nm, sx, sy in (("StoolA", 205.0, 158.0), ("StoolB", 258.0, 158.0), ("StoolC", 82.0, 178.0), ("StoolD", 138.0, 178.0)):
        prop(s, nm, "stool", sx, sy, cw=10.0, ch=6.0)
    prop(s, "Bench", "bench", 300.0, 182.0, cw=44.0, ch=8.0)
    chest(s, "PantryChest", 40.0, 124.0, "inn_pantry_chest", "Tavern Larder", {"coin": 14, "salvage_crate": 1})
    loot_container(s, "PatronPouch", 300.0, 170.0, "inn_patron_pouch", "Dropped Coin Purse", {"coin": 9})
    s.node(
        "Mark",
        "Polygon2D",
        "Interactables/PatronPouch",
        color="Color(0.8, 0.65, 0.25, 1)",
        polygon="PackedVector2Array(0, -4, 3, 0, 0, 4, -3, 0)",
    )

    npc(s, "BramQuillon", 98.0, 80.0, "Bram Quillon", "bram", "bram", behaviour="wander", wander_radius=14.0)
    npc(s, "OrsaKell", 232.0, 168.0, "Orsa Kell", "orsa", "orsa", facing_row=1)
    npc(s, "Pell", 112.0, 190.0, "Pell Harrow", "pell", "pell", facing_row=1)
    npc(s, "Sela", 175.0, 180.0, "Sela Shore", "sela", "orsa")
    write(s, "salt_gull")


# =============================================================================
# 4. Lantern Watch Tower
# =============================================================================
def gen_lantern_watch() -> None:
    s = Scene()
    w, h, dx = 260.0, 200.0, 130.0
    build_room_base(s, w, h, dx, STONE_FLOOR, STONE_WALL, "lantern_watch", "Lantern Watch")
    window(s, "WindowWest", 50.0)
    window(s, "WindowEast", 210.0)

    # Wall Torches on stone walls
    torch(s, "TorchWest", 35.0, 42.0)
    torch(s, "TorchMid", 130.0, 42.0)
    torch(s, "TorchEast", 225.0, 42.0)

    hearth(s, "Hearth", 130.0, 76.0)
    candle(s, "CandleWest", 92.0, 90.0)
    candle(s, "CandleEast", 168.0, 90.0)
    prop(s, "WeaponRackWest", "weapon_rack", 52.0, 98.0, cw=30.0, ch=8.0)
    prop(s, "WeaponRackEast", "weapon_rack", 208.0, 98.0, cw=30.0, ch=8.0)

    # Upgraded watch bunks
    bed(s, "BunkWest", 44.0, 156.0, "wood", cw=36.0, ch=14.0)
    bed(s, "BunkEast", 216.0, 156.0, "wood", cw=36.0, ch=14.0)

    prop(s, "Table", "table_food", 130.0, 128.0, cw=44.0, ch=10.0)
    prop(s, "StoolA", "stool", 104.0, 136.0, cw=10.0, ch=6.0)
    prop(s, "StoolB", "stool", 156.0, 136.0, cw=10.0, ch=6.0)
    chest(s, "WatchLocker", 238.0, 78.0, "lantern_watch_locker", "Watchman Locker", {"coin": 10, "salvage_crate": 1})
    npc(s, "TeagueMarrow", 90.0, 170.0, "Teague Marrow", "teague", "teague", behaviour="wander", wander_radius=14.0)
    write(s, "lantern_watch")


# =============================================================================
# 5. Harrow Cottage (the fisher Pell's home)
# =============================================================================
def gen_cottage_harrow() -> None:
    s = Scene()
    w, h, dx = 240.0, 170.0, 120.0
    build_room_base(s, w, h, dx, WOOD_FLOOR, TIMBER_WALL, "cottage_harrow", "Harrow Cottage")
    window(s, "WindowWest", 60.0)

    # Wall Torches
    torch(s, "TorchWest", 35.0, 42.0)
    torch(s, "TorchEast", 185.0, 42.0)

    decor(s, "Herbs", "herb_bunches", 150.0, 40.0)
    rug(s, "FurRug", "fur_rug", 120.0, 136.0, scale=0.4)
    hearth(s, "Hearth", 200.0, 76.0)
    prop(s, "Cauldron", "cauldron", 160.0, 96.0, cw=16.0, ch=8.0)
    prop(s, "NetRack", "net_rack", 112.0, 72.0, cw=40.0, ch=8.0)

    # Upgraded adult timber bed & child's cot
    bed(s, "Bed", 40.0, 112.0, "wood", cw=36.0, ch=14.0)
    bed(s, "Cot", 214.0, 142.0, "kid", cw=28.0, ch=12.0)

    prop(s, "Table", "table_food", 168.0, 134.0, cw=44.0, ch=10.0)
    prop(s, "StoolA", "stool", 142.0, 142.0, cw=10.0, ch=6.0)
    prop(s, "Barrels", "barrels", 44.0, 150.0, cw=34.0, ch=10.0)
    chest(s, "FishCreel", 84.0, 150.0, "harrow_creel", "Fisher Creel", {"coin": 7, "iron_scrap": 1})
    candle(s, "Candle", 82.0, 84.0)
    npc(s, "Pell", 100.0, 108.0, "Pell Harrow", "pell", "pell", behaviour="wander", wander_radius=14.0)
    npc(s, "Tam", 150.0, 112.0, "Tam", "tam", "kid_a", behaviour="wander", wander_radius=22.0)
    write(s, "cottage_harrow")


# =============================================================================
# 6. Rook Cottage (the widow Ansa's home, an apothecary corner)
# =============================================================================
def gen_cottage_rook() -> None:
    s = Scene()
    w, h, dx = 240.0, 170.0, 120.0
    build_room_base(s, w, h, dx, WOOD_FLOOR, TIMBER_WALL, "cottage_rook", "Rook Cottage")
    window(s, "WindowEast", 180.0)

    # Wall Torches
    torch(s, "TorchWest", 30.0, 42.0)
    torch(s, "TorchEast", 210.0, 42.0)

    decor(s, "HerbsWest", "herb_bunches", 104.0, 40.0)
    decor(s, "HerbsMid", "herb_bunches", 150.0, 40.0)
    rug(s, "FurRug", "fur_rug", 120.0, 136.0, scale=0.4)
    hearth(s, "Hearth", 56.0, 76.0)
    prop(s, "Cauldron", "cauldron", 96.0, 96.0, cw=16.0, ch=8.0)
    prop(s, "Shelf", "shelf_unit", 206.0, 82.0, cw=26.0, ch=8.0)

    # Upgraded beds
    bed(s, "Bed", 206.0, 138.0, "wood", cw=36.0, ch=14.0)
    bed(s, "Cot", 160.0, 146.0, "kid", cw=28.0, ch=12.0)

    prop(s, "Table", "table_food", 58.0, 140.0, cw=44.0, ch=10.0)
    prop(s, "StoolA", "stool", 34.0, 148.0, cw=10.0, ch=6.0)
    prop(s, "StoolB", "stool", 82.0, 148.0, cw=10.0, ch=6.0)
    chest(s, "HerbChest", 164.0, 100.0, "rook_herb_chest", "Apothecary Box", {"coin": 8, "moonherb": 2})
    candle(s, "Candle", 128.0, 90.0)
    npc(s, "Ansa", 120.0, 104.0, "Ansa Rook", "ansa", "ansa", behaviour="wander", wander_radius=14.0)
    npc(s, "Isa", 150.0, 124.0, "Isa", "isa", "kid_b", behaviour="wander", wander_radius=20.0)
    write(s, "cottage_rook")


# =============================================================================
# 7. Weaver's Cottage
# =============================================================================
def gen_cottage_weaver() -> None:
    s = Scene()
    w, h, dx = 240.0, 170.0, 120.0
    build_room_base(s, w, h, dx, WOOD_FLOOR, TIMBER_WALL, "cottage_weaver", "Weaver's Cottage")
    window(s, "WindowWest", 50.0)
    window(s, "WindowMid", 118.0)

    # Wall Torches
    torch(s, "TorchWest", 30.0, 42.0)
    torch(s, "TorchEast", 210.0, 42.0)

    rug(s, "FurRug", "fur_rug", 120.0, 136.0, scale=0.4)
    hearth(s, "Hearth", 196.0, 76.0)
    prop(s, "Loom", "loom", 62.0, 100.0, cw=40.0, ch=8.0)
    prop(s, "SpinningWheel", "spinning_wheel", 112.0, 96.0, cw=22.0, ch=8.0)

    # Upgraded beds
    bed(s, "Bed", 206.0, 140.0, "wood", cw=36.0, ch=14.0)
    bed(s, "Cot", 162.0, 146.0, "kid", cw=28.0, ch=12.0)

    prop(s, "Sacks", "sacks", 80.0, 152.0, cw=30.0, ch=8.0)
    prop(s, "Stool", "stool", 62.0, 118.0, cw=10.0, ch=6.0)
    chest(s, "WeaverChest", 36.0, 150.0, "weaver_chest", "Cloth Chest", {"coin": 9, "moonherb": 1})
    candle(s, "Candle", 150.0, 90.0)
    npc(s, "Wren", 130.0, 128.0, "Wren", "wren", "wren", behaviour="wander", wander_radius=18.0)
    npc(s, "Lyra", 175.0, 112.0, "Lyra the Weaver", "lyra", "wren")
    write(s, "cottage_weaver")


# =============================================================================
# 8. The Salt Gull's rented room
# =============================================================================
def gen_salt_gull_room() -> None:
    s = Scene()
    w, h, dx = 200.0, 150.0, 100.0
    build_room_base(
        s,
        w,
        h,
        dx,
        WOOD_FLOOR,
        TIMBER_WALL,
        "salt_gull_room",
        "Your Room",
        exit_name="the Salt Gull",
        exit_scene="res://scenes/interiors/salt_gull.tscn",
    )
    window(s, "Window", 150.0)

    # Wall Torches
    torch(s, "TorchWest", 30.0, 42.0)
    torch(s, "TorchEast", 170.0, 42.0)

    rug(s, "FurRug", "fur_rug", 100.0, 108.0, scale=0.4)
    hearth(s, "Hearth", 50.0, 76.0)

    # Upgraded inn bed with fur throw
    bed(s, "Bed", 150.0, 104.0, "inn", cw=36.0, ch=14.0)

    s.node(
        "Bedstead",
        "Area2D",
        "Interactables",
        position=v(150.0, 112.0),
        collision_layer="2",
        collision_mask="0",
        monitoring="false",
        script=s.ext("Script", "res://scripts/rest_spot.gd"),
        prompt='"Sleep"',
    )
    s.node("Reach", "CollisionShape2D", "Interactables/Bedstead", shape=s._sub("CircleShape2D", "radius = 18"))
    prop(s, "Table", "table_food", 70.0, 124.0, cw=44.0, ch=10.0)
    prop(s, "Stool", "stool", 96.0, 132.0, cw=10.0, ch=6.0)
    chest(s, "TravellerChest", 22.0, 130.0, "inn_room_chest", "Traveller's Chest", {"coin": 6})
    candle(s, "Candle", 120.0, 84.0)
    write(s, "salt_gull_room")


# =============================================================================
# 9. Venn's Goods (the trader's shop)
# =============================================================================
def gen_trader_shop() -> None:
    s = Scene()
    w, h, dx = 260.0, 180.0, 130.0
    build_room_base(s, w, h, dx, WOOD_FLOOR, TIMBER_WALL, "trader_shop", "Venn's Goods")
    window(s, "WindowWest", 50.0)
    window(s, "WindowEast", 210.0)

    # Wall Torches
    torch(s, "TorchWest", 30.0, 42.0)
    torch(s, "TorchMid", 130.0, 42.0)
    torch(s, "TorchEast", 230.0, 42.0)

    decor(s, "BottleShelf", "bottle_shelf", 130.0, 44.0)
    rug(s, "WovenRug", "rug_woven", 130.0, 148.0, scale=0.6)
    prop(s, "Counter", "counter_bar", 130.0, 102.0, cw=68.0, ch=12.0)
    prop(s, "ShelfWest", "shelf_unit", 40.0, 90.0, cw=26.0, ch=8.0)
    prop(s, "ShelfEast", "shelf_unit", 220.0, 90.0, cw=26.0, ch=8.0)
    prop(s, "Barrels", "barrels", 38.0, 150.0, cw=34.0, ch=10.0)
    prop(s, "Sacks", "sacks", 82.0, 154.0, cw=30.0, ch=8.0)
    prop(s, "SacksEast", "sacks", 222.0, 150.0, cw=30.0, ch=8.0)
    prop(s, "Table", "table_food", 186.0, 130.0, cw=44.0, ch=10.0)
    candle(s, "CandleWest", 92.0, 88.0)
    candle(s, "CandleEast", 168.0, 88.0)
    npc(s, "OsricVenn", 130.0, 84.0, "Osric Venn", "osric", "merchant", behaviour="wander", wander_radius=12.0)
    write(s, "trader_shop")


def main() -> None:
    gen_mayor_hall()
    gen_forge()
    gen_salt_gull()
    gen_lantern_watch()
    gen_cottage_harrow()
    gen_cottage_rook()
    gen_cottage_weaver()
    gen_salt_gull_room()
    gen_trader_shop()
    print(f"generated 9 interior scenes in {INTERIORS_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
