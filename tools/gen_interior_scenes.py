"""Generates the 7 house interior scenes for Wrackmouth in scenes/interiors/:
- mayor_hall.tscn
- forge.tscn
- salt_gull.tscn
- lantern_watch.tscn
- cottage_harrow.tscn
- cottage_rook.tscn
- cottage_weaver.tscn

Run: python3 tools/gen_interior_scenes.py
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from gen_town_scenes import Scene, v, interactable

INTERIORS_DIR = ROOT / "scenes" / "interiors"
INTERIORS_DIR.mkdir(parents=True, exist_ok=True)

PLAYER_SCENE = "res://scenes/player/player.tscn"
HUD_SCENE = "res://scenes/ui/hud.tscn"
DLG_SCENE = "res://scenes/ui/dialogue_box.tscn"
NPC_SCENE = "res://scenes/npc/npc.tscn"


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
    loot_pairs = ", ".join(f'"{k}": {v}' for k, v in loot.items())
    loot_str = f"{{{loot_pairs}}}"
    interactable(
        s,
        name,
        x,
        y,
        "res://scripts/world/loot_container.gd",
        radius,
        container_id=f'"{container_id}"',
        container_name=f'"{container_name}"',
        loot=loot_str,
    )


def furn_prop(
    s: Scene,
    name: str,
    x: float,
    y: float,
    tex: str,
    cw: float,
    ch: float,
    col_y: float = -6.0,
    offset_y: float = -12.0,
    prop_scale: float = 0.5,
) -> None:
    """A Y-sorted solid furniture object with proportional scale."""
    s.node(name, "StaticBody2D", "Entities", position=v(x, y))
    s.node(
        "Sprite2D",
        "Sprite2D",
        f"Entities/{name}",
        scale=v(prop_scale, prop_scale),
        texture=s.ext("Texture2D", tex),
        offset=v(0, offset_y / prop_scale),
    )
    s.node(
        "Shape",
        "CollisionShape2D",
        f"Entities/{name}",
        position=v(0.0, col_y),
        shape=s.rect(cw, ch),
    )


def npc(
    s: Scene,
    name: str,
    x: float,
    y: float,
    display_name: str,
    dialogue_path: str,
    sprite_sheet_res: str,
    facing_row: int = 0,
    behaviour: str = "stationary",
    wander_radius: float = 0.0,
) -> None:
    """Instances an interactive NPC with correct Npc export properties."""
    s.instance(
        name,
        "Entities",
        NPC_SCENE,
        position=v(x, y),
        display_name=f'"{display_name}"',
        dialogue_path=f'"{dialogue_path}"',
        sprite_sheet=s.ext("Texture2D", sprite_sheet_res),
        facing_row=str(facing_row),
        behaviour=f'"{behaviour}"',
        wander_radius=str(wander_radius),
    )


def build_room_base(
    s: Scene,
    w: float,
    h: float,
    door_x: float,
    floor_tex: str,
    wall_tex: str,
    building_id: str,
) -> None:
    """Constructs the base room walls, tiled floor, door threshold, player, hud, and dialogue."""
    s.node(
        "Interior",
        "Node2D",
        None,
        script=s.ext("Script", "res://scripts/world/area_scene.gd"),
        area_size=f"Vector2i({int(w)}, {int(h)})",
        music_cue='"mus_wrackmouth"',
        ambience_cues='PackedStringArray("amb_fire")',
        is_outdoor="false",
    )

    # Cozy warm indoor ambient light
    s.node(
        "WarmIndoorLight",
        "CanvasModulate",
        ".",
        color="Color(1.0, 0.96, 0.88, 1.0)",
    )

    # Tiled Floor (TextureRect with STRETCH_TILE). The tile is 4x density art, so the rect is
    # laid out in texture pixels and scaled down 0.25 to world units.
    s.node(
        "Floor",
        "TextureRect",
        ".",
        offset_right=str(int(w) * 4),
        offset_bottom=str(int(h) * 4),
        scale=v(0.25, 0.25),
        texture=s.ext("Texture2D", floor_tex),
        stretch_mode="1",
    )

    # Timber / Stone Wall Header
    wall_scale_x = w / 512.0
    s.node(
        "WallHeader",
        "Sprite2D",
        ".",
        position=v(w / 2.0, 24.0),
        scale=v(wall_scale_x, 0.5),
        texture=s.ext("Texture2D", wall_tex),
    )

    # Perimeter Wall Collisions
    s.node("Walls", "StaticBody2D", ".")

    # Top wall
    s.node(
        "TopWall",
        "CollisionShape2D",
        "Walls",
        position=v(w / 2.0, 24.0),
        shape=s.rect(w, 48.0),
    )
    # Left wall
    s.node(
        "LeftWall",
        "CollisionShape2D",
        "Walls",
        position=v(8.0, h / 2.0),
        shape=s.rect(16.0, h),
    )
    # Right wall
    s.node(
        "RightWall",
        "CollisionShape2D",
        "Walls",
        position=v(w - 8.0, h / 2.0),
        shape=s.rect(16.0, h),
    )
    # Bottom wall left of door
    bw_l = max(0.0, door_x - 22.0)
    if bw_l > 0.0:
        s.node(
            "BottomWallLeft",
            "CollisionShape2D",
            "Walls",
            position=v(bw_l / 2.0, h - 8.0),
            shape=s.rect(bw_l, 16.0),
        )
    # Bottom wall right of door
    bw_r = max(0.0, w - (door_x + 22.0))
    if bw_r > 0.0:
        s.node(
            "BottomWallRight",
            "CollisionShape2D",
            "Walls",
            position=v(door_x + 22.0 + bw_r / 2.0, h - 8.0),
            shape=s.rect(bw_r, 16.0),
        )

    # Groups
    s.node("Entities", "Node2D", ".", y_sort_enabled="true")
    s.node("Interactables", "Node2D", ".")
    s.node("Zones", "Node2D", ".")
    s.node("Spawns", "Node2D", ".")

    # Spawns: from_town marker inside door threshold
    s.node("from_town", "Marker2D", "Spawns", position=v(door_x, h - 45.0))

    # Exit door leading back to Wrackmouth
    door(
        s,
        "DoorExit",
        door_x,
        h - 10.0,
        building_id,
        "Wrackmouth",
        "res://scenes/world/wrackmouth.tscn",
        "from_" + building_id,
        is_exit=True,
        radius=16.0,
    )

    # Player instance
    s.instance("Player", "Entities", PLAYER_SCENE, position=v(door_x, h - 45.0))

    # HUD & Dialogue
    s.instance("Hud", ".", HUD_SCENE)
    s.instance("DialogueBox", ".", DLG_SCENE)


# =============================================================================
# 1. Mayor's Hall (Wrackmouth Great Longhouse)
# =============================================================================
def gen_mayor_hall() -> None:
    s = Scene()
    w, h = 460, 290
    door_x = 230.0
    build_room_base(
        s,
        w,
        h,
        door_x,
        "res://assets/interiors/floor_wood.png",
        "res://assets/interiors/wall_timber.png",
        "mayor_hall",
    )

    # Central woven hall runner leading from entrance toward council dais
    s.node("AisleRug", "StaticBody2D", "Entities", position=v(230.0, 165.0))
    s.node(
        "Sprite2D",
        "Sprite2D",
        "Entities/AisleRug",
        scale=v(0.5, 0.7),
        texture=s.ext("Texture2D", "res://assets/interiors/furniture/rug_woven.png"),
        offset=v(0, 0),
    )

    # Stately Carved Dais Chair behind Mayor Tolle
    furn_prop(
        s,
        "MayorChair",
        230.0,
        80.0,
        "res://assets/interiors/furniture/chair_wood.png",
        18.0,
        14.0,
        col_y=-6.0,
        offset_y=-12.0,
        prop_scale=0.45,
    )

    # Grand Stone Fireplace Hearth on North-East Wall
    furn_prop(
        s,
        "GreatHearth",
        380.0,
        74.0,
        "res://assets/interiors/furniture/hearth.png",
        44.0,
        18.0,
        col_y=-9.0,
        offset_y=-20.0,
        prop_scale=0.5,
    )

    # Long Oak Great Council Table (Right Side of Hall, out of center aisle)
    furn_prop(
        s,
        "CouncilTable",
        340.0,
        150.0,
        "res://assets/interiors/furniture/table_wood.png",
        50.0,
        20.0,
        col_y=-10.0,
        offset_y=-14.0,
        prop_scale=0.5,
    )

    # Municipal Records Cupboard (Left Wall)
    furn_prop(
        s,
        "RecordsCupboard",
        70.0,
        64.0,
        "res://assets/interiors/furniture/cupboard.png",
        28.0,
        16.0,
        col_y=-8.0,
        offset_y=-20.0,
        prop_scale=0.4,
    )

    # Chancellor's Records Desk (Left Nook)
    furn_prop(
        s,
        "ChancellorDesk",
        95.0,
        120.0,
        "res://assets/interiors/furniture/table_wood.png",
        40.0,
        18.0,
        col_y=-8.0,
        offset_y=-12.0,
        prop_scale=0.4,
    )

    # Loot Containers
    loot_container(
        s,
        "MayorChest",
        50.0,
        100.0,
        "mayor_hall_chest",
        "Council Strongbox",
        {"coin": 18},
    )
    furn_prop(
        s,
        "ChestVisual",
        50.0,
        100.0,
        "res://assets/interiors/furniture/chest.png",
        20.0,
        12.0,
        col_y=-6.0,
        offset_y=-8.0,
        prop_scale=0.4,
    )

    loot_container(
        s,
        "MayorDesk",
        70.0,
        78.0,
        "mayor_hall_cupboard",
        "Records Cupboard",
        {"coin": 8, "mayor_letter": 1},
    )

    # --- NPCs ---
    # 1. Mayor Maren Tolle at the council dais (CENTER, DIRECTLY REACHABLE FROM ENTRANCE)
    npc(
        s,
        "MayorTolle",
        230.0,
        115.0,
        display_name="Mayor Maren Tolle",
        dialogue_path="res://data/dialogue/mayor.json",
        sprite_sheet_res="res://assets/npc/mayor.png",
        facing_row=0,
        behaviour="stationary",
        wander_radius=0.0,
    )

    # 2. Chancellor Alden at the Records Desk (Left Side)
    npc(
        s,
        "ChancellorAlden",
        115.0,
        130.0,
        display_name="Chancellor Alden",
        dialogue_path="res://data/dialogue/chancellor.json",
        sprite_sheet_res="res://assets/npc/ansa.png",
        facing_row=0,
        behaviour="stationary",
        wander_radius=0.0,
    )

    # 3. Guard Vance near the Hall Entrance
    npc(
        s,
        "GuardVance",
        165.0,
        235.0,
        display_name="Guard Vance",
        dialogue_path="res://data/dialogue/guard.json",
        sprite_sheet_res="res://assets/npc/guard.png",
        facing_row=3,
        behaviour="stationary",
        wander_radius=0.0,
    )

    (INTERIORS_DIR / "mayor_hall.tscn").write_text(s.render())


# =============================================================================
# 2. Kell's Forge
# =============================================================================
def gen_forge() -> None:
    s = Scene()
    w, h = 384, 256
    door_x = 192.0
    build_room_base(
        s,
        w,
        h,
        door_x,
        "res://assets/interiors/floor_stone.png",
        "res://assets/interiors/wall_stone.png",
        "forge",
    )

    # Glowing Forge Hearth
    furn_prop(
        s,
        "ForgeHearth",
        110.0,
        70.0,
        "res://assets/interiors/furniture/hearth.png",
        44.0,
        18.0,
        col_y=-9.0,
        offset_y=-20.0,
        prop_scale=0.5,
    )
    # Anvil on Stump
    furn_prop(
        s,
        "Anvil",
        170.0,
        110.0,
        "res://assets/interiors/furniture/anvil.png",
        18.0,
        14.0,
        col_y=-7.0,
        offset_y=-10.0,
        prop_scale=0.4,
    )
    # Heavy workbench table
    furn_prop(
        s,
        "WorkTable",
        290.0,
        75.0,
        "res://assets/interiors/furniture/table_wood.png",
        48.0,
        18.0,
        col_y=-9.0,
        offset_y=-14.0,
        prop_scale=0.45,
    )
    # Barrels
    furn_prop(
        s,
        "Barrels",
        50.0,
        70.0,
        "res://assets/interiors/furniture/barrels.png",
        28.0,
        14.0,
        col_y=-7.0,
        offset_y=-10.0,
        prop_scale=0.4,
    )

    # Loot Containers
    loot_container(
        s,
        "ScrapBin",
        340.0,
        80.0,
        "forge_scrap_bin",
        "Iron Scrap Bin",
        {"coin": 12, "iron_scrap": 2},
    )
    furn_prop(
        s,
        "ChestVisual",
        340.0,
        80.0,
        "res://assets/interiors/furniture/chest.png",
        20.0,
        12.0,
        col_y=-6.0,
        offset_y=-8.0,
        prop_scale=0.4,
    )

    loot_container(
        s,
        "ToolChest",
        240.0,
        76.0,
        "forge_tool_box",
        "Tool Chest",
        {"iron_scrap": 2, "coin": 6},
    )

    # Blacksmith Orsa Kell
    npc(
        s,
        "OrsaKell",
        190.0,
        110.0,
        display_name="Orsa Kell",
        dialogue_path="res://data/dialogue/orsa.json",
        sprite_sheet_res="res://assets/npc/orsa.png",
        facing_row=0,
        behaviour="wander",
        wander_radius=20.0,
    )

    (INTERIORS_DIR / "forge.tscn").write_text(s.render())


# =============================================================================
# 3. The Salt Gull Inn
# =============================================================================
def gen_salt_gull() -> None:
    s = Scene()
    w, h = 460, 280
    door_x = 230.0
    build_room_base(
        s,
        w,
        h,
        door_x,
        "res://assets/interiors/floor_wood.png",
        "res://assets/interiors/wall_timber.png",
        "salt_gull",
    )

    # Long Bar Counter
    furn_prop(
        s,
        "BarCounter",
        140.0,
        96.0,
        "res://assets/interiors/furniture/counter_bar.png",
        68.0,
        16.0,
        col_y=-8.0,
        offset_y=-12.0,
        prop_scale=0.5,
    )
    # Kegs & Barrels behind bar
    furn_prop(
        s,
        "AleBarrels",
        90.0,
        58.0,
        "res://assets/interiors/furniture/barrels.png",
        28.0,
        14.0,
        col_y=-7.0,
        offset_y=-10.0,
        prop_scale=0.4,
    )
    # Large Roaring Tavern Hearth
    furn_prop(
        s,
        "TavernHearth",
        360.0,
        74.0,
        "res://assets/interiors/furniture/hearth.png",
        44.0,
        18.0,
        col_y=-9.0,
        offset_y=-20.0,
        prop_scale=0.5,
    )
    # Tavern Dining Table
    furn_prop(
        s,
        "DiningTable",
        300.0,
        160.0,
        "res://assets/interiors/furniture/table_wood.png",
        50.0,
        20.0,
        col_y=-10.0,
        offset_y=-14.0,
        prop_scale=0.5,
    )
    # Guest bed in side alcove
    furn_prop(
        s,
        "InnBed",
        60.0,
        190.0,
        "res://assets/interiors/furniture/bed_wood.png",
        30.0,
        24.0,
        col_y=-12.0,
        offset_y=-18.0,
        prop_scale=0.4,
    )
    # Rug in dining area
    s.node("Rug", "StaticBody2D", "Entities", position=v(300.0, 162.0))
    s.node(
        "Sprite2D",
        "Sprite2D",
        "Entities/Rug",
        scale=v(0.5, 0.5),
        texture=s.ext("Texture2D", "res://assets/interiors/furniture/rug_woven.png"),
        offset=v(0, 0),
    )

    # Loot Containers
    loot_container(
        s,
        "PantryChest",
        410.0,
        76.0,
        "inn_pantry_chest",
        "Tavern Larder",
        {"coin": 14, "salvage_crate": 1},
    )
    furn_prop(
        s,
        "ChestVisual",
        410.0,
        76.0,
        "res://assets/interiors/furniture/chest.png",
        20.0,
        12.0,
        col_y=-6.0,
        offset_y=-8.0,
        prop_scale=0.4,
    )

    loot_container(
        s,
        "PatronPouch",
        260.0,
        170.0,
        "inn_patron_pouch",
        "Dropped Coin Purse",
        {"coin": 9},
    )

    # Innkeeper Bram Quillon behind the counter (easily reachable across bar)
    npc(
        s,
        "BramQuillon",
        140.0,
        78.0,
        display_name="Bram Quillon",
        dialogue_path="res://data/dialogue/bram.json",
        sprite_sheet_res="res://assets/npc/bram.png",
        facing_row=0,
        behaviour="stationary",
        wander_radius=0.0,
    )

    (INTERIORS_DIR / "salt_gull.tscn").write_text(s.render())


# =============================================================================
# 4. Lantern Watch Tower
# =============================================================================
def gen_lantern_watch() -> None:
    s = Scene()
    w, h = 320, 240
    door_x = 160.0
    build_room_base(
        s,
        w,
        h,
        door_x,
        "res://assets/interiors/floor_stone.png",
        "res://assets/interiors/wall_stone.png",
        "lantern_watch",
    )

    # Watchtower Hearth
    furn_prop(
        s,
        "WatchHearth",
        90.0,
        70.0,
        "res://assets/interiors/furniture/hearth.png",
        44.0,
        18.0,
        col_y=-9.0,
        offset_y=-20.0,
        prop_scale=0.5,
    )
    # Watchman's Desk
    furn_prop(
        s,
        "WatchDesk",
        230.0,
        75.0,
        "res://assets/interiors/furniture/table_wood.png",
        44.0,
        18.0,
        col_y=-9.0,
        offset_y=-14.0,
        prop_scale=0.45,
    )
    # Narrow Watch Cot
    furn_prop(
        s,
        "WatchCot",
        50.0,
        150.0,
        "res://assets/interiors/furniture/bed_wood.png",
        30.0,
        24.0,
        col_y=-12.0,
        offset_y=-18.0,
        prop_scale=0.4,
    )

    # Loot Container: Watch Locker
    loot_container(
        s,
        "WatchLocker",
        280.0,
        78.0,
        "lantern_watch_locker",
        "Watchman Locker",
        {"coin": 10, "salvage_crate": 1},
    )
    furn_prop(
        s,
        "ChestVisual",
        280.0,
        78.0,
        "res://assets/interiors/furniture/chest.png",
        20.0,
        12.0,
        col_y=-6.0,
        offset_y=-8.0,
        prop_scale=0.4,
    )

    # Watchman Teague Marrow
    npc(
        s,
        "TeagueMarrow",
        210.0,
        110.0,
        display_name="Teague Marrow",
        dialogue_path="res://data/dialogue/teague.json",
        sprite_sheet_res="res://assets/npc/teague.png",
        facing_row=0,
        behaviour="wander",
        wander_radius=18.0,
    )

    (INTERIORS_DIR / "lantern_watch.tscn").write_text(s.render())


# =============================================================================
# 5. Harrow Cottage (Fisherman's Hut)
# =============================================================================
def gen_cottage_harrow() -> None:
    s = Scene()
    w, h = 340, 240
    door_x = 170.0
    build_room_base(
        s,
        w,
        h,
        door_x,
        "res://assets/interiors/floor_wood.png",
        "res://assets/interiors/wall_timber.png",
        "cottage_harrow",
    )

    # Hearth
    furn_prop(
        s,
        "Hearth",
        90.0,
        70.0,
        "res://assets/interiors/furniture/hearth.png",
        44.0,
        18.0,
        col_y=-9.0,
        offset_y=-20.0,
        prop_scale=0.5,
    )
    # Fisher's Cot
    furn_prop(
        s,
        "Bed",
        60.0,
        150.0,
        "res://assets/interiors/furniture/bed_wood.png",
        30.0,
        24.0,
        col_y=-12.0,
        offset_y=-18.0,
        prop_scale=0.4,
    )
    # Fish-salting Table
    furn_prop(
        s,
        "Table",
        240.0,
        75.0,
        "res://assets/interiors/furniture/table_wood.png",
        44.0,
        18.0,
        col_y=-9.0,
        offset_y=-14.0,
        prop_scale=0.45,
    )

    # Loot Container: Fish Creel
    loot_container(
        s,
        "FishCreel",
        285.0,
        78.0,
        "harrow_creel",
        "Fisher Creel",
        {"coin": 7, "iron_scrap": 1},
    )
    furn_prop(
        s,
        "ChestVisual",
        285.0,
        78.0,
        "res://assets/interiors/furniture/chest.png",
        20.0,
        12.0,
        col_y=-6.0,
        offset_y=-8.0,
        prop_scale=0.4,
    )

    # Fisher Ansa NPC
    npc(
        s,
        "Ansa",
        210.0,
        110.0,
        display_name="Ansa Rook",
        dialogue_path="res://data/dialogue/ansa.json",
        sprite_sheet_res="res://assets/npc/ansa.png",
        facing_row=0,
        behaviour="wander",
        wander_radius=18.0,
    )

    (INTERIORS_DIR / "cottage_harrow.tscn").write_text(s.render())


# =============================================================================
# 6. Rook Cottage (Widow Rook's Home)
# =============================================================================
def gen_cottage_rook() -> None:
    s = Scene()
    w, h = 330, 230
    door_x = 165.0
    build_room_base(
        s,
        w,
        h,
        door_x,
        "res://assets/interiors/floor_wood.png",
        "res://assets/interiors/wall_stone.png",
        "cottage_rook",
    )

    # Hearth
    furn_prop(
        s,
        "Hearth",
        90.0,
        70.0,
        "res://assets/interiors/furniture/hearth.png",
        44.0,
        18.0,
        col_y=-9.0,
        offset_y=-20.0,
        prop_scale=0.5,
    )
    # Bed
    furn_prop(
        s,
        "Bed",
        55.0,
        145.0,
        "res://assets/interiors/furniture/bed_wood.png",
        30.0,
        24.0,
        col_y=-12.0,
        offset_y=-18.0,
        prop_scale=0.4,
    )
    # Herb dresser / cupboard
    furn_prop(
        s,
        "Cupboard",
        230.0,
        64.0,
        "res://assets/interiors/furniture/cupboard.png",
        28.0,
        16.0,
        col_y=-8.0,
        offset_y=-20.0,
        prop_scale=0.4,
    )
    # Hearth rug
    s.node("Rug", "StaticBody2D", "Entities", position=v(150.0, 120.0))
    s.node(
        "Sprite2D",
        "Sprite2D",
        "Entities/Rug",
        scale=v(0.4, 0.4),
        texture=s.ext("Texture2D", "res://assets/interiors/furniture/rug_woven.png"),
        offset=v(0, 0),
    )

    # Loot Container: Herbalist Basket
    loot_container(
        s,
        "HerbChest",
        275.0,
        76.0,
        "rook_herb_chest",
        "Apothecary Box",
        {"coin": 8, "moonherb": 2},
    )
    furn_prop(
        s,
        "ChestVisual",
        275.0,
        76.0,
        "res://assets/interiors/furniture/chest.png",
        20.0,
        12.0,
        col_y=-6.0,
        offset_y=-8.0,
        prop_scale=0.4,
    )

    # Pell NPC
    npc(
        s,
        "Pell",
        190.0,
        110.0,
        display_name="Pell Harrow",
        dialogue_path="res://data/dialogue/pell.json",
        sprite_sheet_res="res://assets/npc/pell.png",
        facing_row=0,
        behaviour="wander",
        wander_radius=18.0,
    )

    (INTERIORS_DIR / "cottage_rook.tscn").write_text(s.render())


# =============================================================================
# 7. Weaver's Cottage
# =============================================================================
def gen_cottage_weaver() -> None:
    s = Scene()
    w, h = 340, 240
    door_x = 170.0
    build_room_base(
        s,
        w,
        h,
        door_x,
        "res://assets/interiors/floor_wood.png",
        "res://assets/interiors/wall_timber.png",
        "cottage_weaver",
    )

    # Loom
    furn_prop(
        s,
        "Loom",
        235.0,
        72.0,
        "res://assets/interiors/furniture/loom.png",
        30.0,
        16.0,
        col_y=-8.0,
        offset_y=-14.0,
        prop_scale=0.45,
    )
    # Stone Hearth
    furn_prop(
        s,
        "Hearth",
        90.0,
        70.0,
        "res://assets/interiors/furniture/hearth.png",
        44.0,
        18.0,
        col_y=-9.0,
        offset_y=-20.0,
        prop_scale=0.5,
    )
    # Bed
    furn_prop(
        s,
        "Bed",
        55.0,
        145.0,
        "res://assets/interiors/furniture/bed_wood.png",
        30.0,
        24.0,
        col_y=-12.0,
        offset_y=-18.0,
        prop_scale=0.4,
    )

    # Loot Container: Weaver Chest
    loot_container(
        s,
        "WeaverChest",
        290.0,
        78.0,
        "weaver_chest",
        "Cloth Chest",
        {"coin": 9, "moonherb": 1},
    )
    furn_prop(
        s,
        "ChestVisual",
        290.0,
        78.0,
        "res://assets/interiors/furniture/chest.png",
        20.0,
        12.0,
        col_y=-6.0,
        offset_y=-8.0,
        prop_scale=0.4,
    )

    # Weaver Wren NPC
    npc(
        s,
        "Wren",
        190.0,
        105.0,
        display_name="Wren",
        dialogue_path="res://data/dialogue/wren.json",
        sprite_sheet_res="res://assets/npc/wren.png",
        facing_row=0,
        behaviour="wander",
        wander_radius=18.0,
    )

    (INTERIORS_DIR / "cottage_weaver.tscn").write_text(s.render())


def main() -> None:
    gen_mayor_hall()
    gen_forge()
    gen_salt_gull()
    gen_lantern_watch()
    gen_cottage_harrow()
    gen_cottage_rook()
    gen_cottage_weaver()
    print("generated 7 interior scenes in scenes/interiors/")


if __name__ == "__main__":
    main()
