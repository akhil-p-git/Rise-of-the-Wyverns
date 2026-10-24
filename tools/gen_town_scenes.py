"""Writes the gray-box town scenes (scenes/world/wrackmouth.tscn and crossholm_road.tscn).

The layout lives here as data so it can be reviewed and tweaked in one place; once real art
arrives, edit the generated scenes in the Godot editor instead and stop running this.

Run: python3 tools/gen_town_scenes.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NPC_SCENE = "res://scenes/npc/npc.tscn"


class Scene:
    """Collects nodes and shared resources, then renders them as a .tscn file."""

    def __init__(self) -> None:
        self.exts: dict[str, tuple[str, str]] = {}
        self.subs: dict[tuple, str] = {}
        self.sub_lines: list[str] = []
        self.nodes: list[str] = []

    def ext(self, kind: str, path: str) -> str:
        key = path
        if key not in self.exts:
            self.exts[key] = (f"{len(self.exts) + 1}_{kind.lower()}", kind)
        return f'ExtResource("{self.exts[key][0]}")'

    def rect(self, w: float, h: float) -> str:
        return self._sub("RectangleShape2D", f"size = Vector2({w:g}, {h:g})")

    def _sub(self, kind: str, body: str) -> str:
        key = (kind, body)
        if key not in self.subs:
            sid = f"{kind.lower()}_{len(self.subs)}"
            self.subs[key] = sid
            self.sub_lines.append(f'[sub_resource type="{kind}" id="{sid}"]\n{body}\n')
        return f'SubResource("{self.subs[key]}")'

    def node(self, name: str, kind: str, parent: str | None, **props: str) -> None:
        head = f'[node name="{name}" type="{kind}"'
        if parent is not None:
            head += f' parent="{parent}"'
        body = "".join(f"{k} = {v}\n" for k, v in props.items())
        self.nodes.append(head + "]\n" + body)

    def instance(self, name: str, parent: str, path: str, **props: str) -> None:
        ref = self.ext("PackedScene", path)
        head = f'[node name="{name}" parent="{parent}" instance={ref}]\n'
        self.nodes.append(head + "".join(f"{k} = {v}\n" for k, v in props.items()))

    def render(self) -> str:
        out = ["[gd_scene format=3]\n"]
        for path, (rid, kind) in self.exts.items():
            out.append(f'[ext_resource type="{kind}" path="{path}" id="{rid}"]')
        out.append("")
        out.extend(self.sub_lines)
        out.extend(self.nodes)
        return "\n".join(out)


def v(x: float, y: float) -> str:
    return f"Vector2({x:g}, {y:g})"


def col(r: float, g: float, b: float, a: float = 1.0) -> str:
    return f"Color({r}, {g}, {b}, {a})"


def rect_node(s: Scene, name: str, parent: str, x, y, w, h, color: str) -> None:
    s.node(
        name,
        "ColorRect",
        parent,
        offset_left=x,
        offset_top=y,
        offset_right=x + w,
        offset_bottom=y + h,
        color=color,
    )


def static_rect(s: Scene, name: str, parent: str, x, y, w, h) -> None:
    """An invisible solid rectangle with its top-left corner at (x, y)."""
    s.node(name, "StaticBody2D", parent)
    s.node(
        "Shape",
        "CollisionShape2D",
        f"{parent}/{name}",
        position=v(x + w / 2, y + h / 2),
        shape=s.rect(w, h),
    )


def _vec2_array(pts: tuple[tuple[float, float], ...]) -> str:
    coords = ", ".join(f"{px:g}, {py:g}" for px, py in pts)
    return f"PackedVector2Array({coords})"


def building(
    s: Scene,
    name: str,
    x,
    y,
    size,
    wall,
    roof,
    label="",
    door=True,
    texture: str = "",
    chimney_offsets: tuple[tuple[float, float], ...] = (),
    window_offsets: tuple[tuple[float, float], ...] = (),
) -> None:
    w, h = size
    props = {
        "position": v(x, y),
        "script": s.ext("Script", "res://scripts/world/building.gd"),
        "size": v(w, h),
        "wall_color": wall,
        "roof_color": roof,
        "label": f'"{label}"',
        "door": "true" if door else "false",
    }
    if texture:
        props["texture"] = s.ext("Texture2D", texture)
    if chimney_offsets:
        props["chimney_offsets"] = _vec2_array(chimney_offsets)
    if window_offsets:
        props["window_offsets"] = _vec2_array(window_offsets)
    s.node(name, "StaticBody2D", "Entities", **props)
    s.node(
        "Shape",
        "CollisionShape2D",
        f"Entities/{name}",
        position=v(0, -h / 2),
        shape=s.rect(w, h),
    )


def prop_sprite(
    s: Scene,
    name: str,
    x,
    y,
    texture: str,
    offset_y: float = -12,
    col_size: tuple[float, float] = (14, 8),
    col_offset_y: float = -4,
    hframes: int = 1,
    glow_texture: str = "",
) -> None:
    cw, ch = col_size
    body_props = {"position": v(x, y)}
    if hframes > 1 or glow_texture:
        body_props["script"] = s.ext("Script", "res://scripts/world/animated_prop.gd")
        if glow_texture:
            body_props["glow_texture"] = s.ext("Texture2D", glow_texture)
    s.node(name, "StaticBody2D", "Entities", **body_props)
    sp_props = {
        "scale": v(0.25, 0.25),
        "texture": s.ext("Texture2D", texture),
        "offset": v(0, offset_y * 4),
    }
    if hframes > 1:
        sp_props["hframes"] = str(hframes)
    s.node("Sprite2D", "Sprite2D", f"Entities/{name}", **sp_props)
    s.node(
        "Shape",
        "CollisionShape2D",
        f"Entities/{name}",
        position=v(0, col_offset_y),
        shape=s.rect(cw, ch),
    )


def sign(
    s: Scene, name: str, x, y, prompt: str, message: str, radius: float = 12
) -> None:
    interactable(
        s,
        name,
        x,
        y,
        "res://scripts/interactable.gd",
        radius,
        prompt=f'"{prompt}"',
        message=f'"{message}"',
    )


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


def interactable(
    s: Scene, name: str, x, y, script: str, radius: float, **props: str
) -> None:
    s.node(
        name,
        "Area2D",
        "Interactables",
        position=v(x, y),
        collision_layer="2",
        collision_mask="0",
        monitoring="false",
        script=s.ext("Script", script),
        **props,
    )
    s.node(
        "Reach",
        "CollisionShape2D",
        f"Interactables/{name}",
        shape=s._sub("CircleShape2D", f"radius = {radius:g}"),
    )


def pickup(
    s: Scene,
    name: str,
    x,
    y,
    prompt,
    message,
    color,
    item="",
    sets_flag="",
    requires=None,
    locked="",
    count=1,
    texture: str = "",
):
    props = {"prompt": f'"{prompt}"', "message": f'"{message}"'}
    if item:
        props["item"] = f'"{item}"'
    if count != 1:
        props["count"] = str(count)
    if sets_flag:
        props["sets_flag"] = f'"{sets_flag}"'
    if requires:
        props["requires"] = (
            "PackedStringArray(" + ", ".join(f'"{r}"' for r in requires) + ")"
        )
    if locked:
        props["locked_message"] = f'"{locked}"'
    interactable(s, name, x, y, "res://scripts/pickup.gd", 11, **props)
    if texture:
        s.node(
            "Sprite2D",
            "Sprite2D",
            f"Interactables/{name}",
            scale=v(0.25, 0.25),
            texture=s.ext("Texture2D", texture),
        )
    else:
        s.node(
            "Mark",
            "Polygon2D",
            f"Interactables/{name}",
            color=color,
            polygon="PackedVector2Array(0, -5, 4, 0, 0, 5, -4, 0)",
        )


def npc(
    s: Scene,
    name: str,
    x,
    y,
    display,
    dialogue,
    tint,
    row=0,
    sheet: str = "",
    behaviour: str = "stationary",
    wander_radius: float = 24.0,
    waypoints: tuple[tuple[float, float], ...] = (),
) -> None:
    props = {
        "position": v(x, y),
        "display_name": f'"{display}"',
        "dialogue_path": f'"res://data/dialogue/{dialogue}.json"',
        "facing_row": str(row),
        "behaviour": f'"{behaviour}"',
        "wander_radius": f"{wander_radius:g}",
    }
    if waypoints:
        coords = ", ".join(f"{wx:g}, {wy:g}" for wx, wy in waypoints)
        props["waypoints"] = f"PackedVector2Array({coords})"
    if sheet:
        props["sprite_sheet"] = s.ext("Texture2D", f"res://assets/npc/{sheet}.png")
    else:
        props["modulate"] = tint
    s.instance(name, "Entities", NPC_SCENE, **props)


def exit_zone(s: Scene, name: str, x, y, w, h, scene: str, spawn: str) -> None:
    s.node(
        name,
        "Area2D",
        "Zones",
        position=v(x, y),
        collision_layer="0",
        collision_mask="1",
        script=s.ext("Script", "res://scripts/scene_exit.gd"),
        target_scene=f'"{scene}"',
        target_spawn=f'"{spawn}"',
    )
    s.node("Shape", "CollisionShape2D", f"Zones/{name}", shape=s.rect(w, h))


def frame(
    s: Scene,
    size: tuple[int, int],
    root_name: str,
    ground: str,
    ground_texture: str = "",
    music_cue: str = "mus_wrackmouth",
    ambience_cues: tuple[str, ...] = ("amb_wind", "amb_gulls"),
) -> None:
    w, h = size
    amb_str = "PackedStringArray(" + ", ".join(f'"{c}"' for c in ambience_cues) + ")"
    s.node(
        root_name,
        "Node2D",
        None,
        y_sort_enabled="false",
        script=s.ext("Script", "res://scripts/world/area_scene.gd"),
        area_size=f"Vector2i({w}, {h})",
        music_cue=f'"{music_cue}"',
        ambience_cues=amb_str,
    )
    if ground_texture:
        s.node(
            "Ground",
            "Sprite2D",
            ".",
            scale=v(0.25, 0.25),
            texture=s.ext("Texture2D", ground_texture),
            centered="false",
        )
    else:
        s.node("Ground", "Node2D", ".")
        rect_node(s, "Grass", "Ground", 0, 0, w, h, ground)
    s.node("Bounds", "StaticBody2D", ".")


def finish(
    s: Scene, spawns: dict[str, tuple[float, float]], player: tuple[float, float]
) -> None:
    s.node("Spawns", "Node2D", ".")
    for name, (x, y) in spawns.items():
        s.node(name, "Marker2D", "Spawns", position=v(x, y))
    s.instance(
        "Player", "Entities", "res://scenes/player/player.tscn", position=v(*player)
    )
    s.instance("Hud", ".", "res://scenes/ui/hud.tscn")
    s.instance("DialogueBox", ".", "res://scenes/ui/dialogue_box.tscn")


def borders(s: Scene, w: int, h: int, gaps: dict[str, tuple[int, int]]) -> None:
    """Solid map edges. `gaps` maps a side to the (start, end) span left open for an exit."""
    t = 16

    def edge(side: str, fixed_x, fixed_y, length, horizontal):
        span = gaps.get(side)
        parts = [(0, length)] if span is None else [(0, span[0]), (span[1], length)]
        for i, (a, b) in enumerate(parts):
            if b <= a:
                continue
            if horizontal:
                static_rect(
                    s,
                    f"{side}{i}",
                    "Bounds",
                    a - t,
                    fixed_y,
                    b - a + (2 * t if len(parts) == 1 else t),
                    t,
                )
            else:
                static_rect(
                    s,
                    f"{side}{i}",
                    "Bounds",
                    fixed_x,
                    a - t,
                    t,
                    b - a + (2 * t if len(parts) == 1 else t),
                )

    edge("North", 0, -t, w, True)
    edge("South", 0, h, w, True)
    edge("West", -t, 0, h, False)
    edge("East", w, 0, h, False)


def wrackmouth() -> str:
    W, H = 640, 420
    s = Scene()
    frame(
        s,
        (W, H),
        "Wrackmouth",
        col(0.27, 0.4, 0.25),
        "res://assets/wrackmouth/ground.png",
        music_cue="mus_wrackmouth",
        ambience_cues=("amb_wind", "amb_gulls", "amb_fire"),
    )
    # North gate to the beach and the east road are the two ways out.
    borders(s, W, H, {"North": (296, 344), "East": (186, 238)})
    s.node("Entities", "Node2D", ".", y_sort_enabled="true")
    s.node("Interactables", "Node2D", ".")
    s.node("Zones", "Node2D", ".")

    hall = (col(0.5, 0.48, 0.44), col(0.24, 0.27, 0.34))
    building(
        s,
        "MayorHall",
        150,
        150,
        (104, 64),
        *hall,
        label="Mayor's Hall",
        texture="res://assets/wrackmouth/mayor_hall.png",
        chimney_offsets=((33.5, -100.0),),
        window_offsets=((-41.0, -31.0), (13.0, -53.0), (-12.0, -18.0), (1.0, -28.0)),
    )
    building(
        s,
        "Forge",
        500,
        175,
        (88, 52),
        col(0.4, 0.34, 0.3),
        col(0.3, 0.2, 0.18),
        label="Kell's Forge",
        texture="res://assets/wrackmouth/forge.png",
        chimney_offsets=((-23.5, -77.0),),
        window_offsets=((-18.0, -22.0), (14.0, -26.0)),
    )
    building(
        s,
        "SaltGull",
        330,
        345,
        (120, 66),
        col(0.46, 0.35, 0.26),
        col(0.23, 0.2, 0.2),
        label="The Salt Gull",
        texture="res://assets/wrackmouth/salt_gull.png",
        chimney_offsets=((40.8, -103.5),),
        window_offsets=((-24.0, -28.0), (16.0, -26.0), (28.0, -48.0)),
    )
    building(
        s,
        "HarrowHouse",
        80,
        290,
        (64, 44),
        col(0.44, 0.38, 0.32),
        col(0.26, 0.24, 0.28),
        texture="res://assets/wrackmouth/cottage_harrow.png",
        window_offsets=((12.0, -20.0),),
    )
    building(
        s,
        "RookCottage",
        205,
        300,
        (60, 42),
        col(0.47, 0.4, 0.33),
        col(0.3, 0.26, 0.24),
        texture="res://assets/wrackmouth/cottage_rook.png",
        chimney_offsets=((18.0, -65.0),),
        window_offsets=((-10.0, -20.0),),
    )
    building(
        s,
        "WeaverCottage",
        408,
        126,
        (64, 44),
        col(0.44, 0.38, 0.32),
        col(0.26, 0.24, 0.28),
        texture="res://assets/wrackmouth/cottage_weaver.png",
        chimney_offsets=((22.5, -69.0),),
        window_offsets=((-12.0, -20.0),),
    )
    building(
        s,
        "ShutteredHouse",
        560,
        330,
        (60, 42),
        col(0.34, 0.31, 0.3),
        col(0.2, 0.2, 0.22),
        texture="res://assets/wrackmouth/cottage_shuttered.png",
    )
    building(
        s,
        "LanternWatch",
        580,
        85,
        (40, 70),
        col(0.55, 0.54, 0.52),
        col(0.3, 0.3, 0.34),
        label="Lantern Watch",
        texture="res://assets/wrackmouth/lantern_watch.png",
        window_offsets=((-6.0, -58.0), (-6.0, -24.0)),
    )

    prop_sprite(
        s,
        "PlazaCampfire",
        320,
        210,
        "res://assets/props/campfire_lit_sheet.png",
        -10,
        col_size=(20, 10),
        col_offset_y=-4,
        hframes=4,
        glow_texture="res://assets/props/fire_glow.png",
    )
    prop_sprite(
        s,
        "PlazaSignpost",
        282,
        186,
        "res://assets/props/signpost.png",
        -13,
        col_size=(10, 7),
        col_offset_y=-3.5,
    )
    prop_sprite(
        s,
        "DeadTreeWest",
        38,
        125,
        "res://assets/props/dead_tree.png",
        -30,
        col_size=(14, 9),
        col_offset_y=-4.5,
    )
    prop_sprite(
        s,
        "DeadTreeCairn",
        136,
        382,
        "res://assets/props/dead_tree.png",
        -30,
        col_size=(14, 9),
        col_offset_y=-4.5,
    )
    prop_sprite(
        s,
        "DeadTreeEast",
        608,
        280,
        "res://assets/props/dead_tree.png",
        -30,
        col_size=(14, 9),
        col_offset_y=-4.5,
    )
    prop_sprite(
        s,
        "CairnHeadstone1",
        30,
        348,
        "res://assets/props/headstone_1.png",
        -11,
        col_size=(14, 8),
        col_offset_y=-4,
    )
    prop_sprite(
        s,
        "CairnHeadstone2",
        84,
        346,
        "res://assets/props/headstone_2.png",
        -10,
        col_size=(14, 8),
        col_offset_y=-4,
    )
    prop_sprite(
        s,
        "CairnPile",
        34,
        396,
        "res://assets/props/cairn_stones.png",
        -12,
        col_size=(24, 12),
        col_offset_y=-6,
    )

    npc(
        s,
        "GuardRorik",
        180,
        160,
        "Guard Rorik",
        "guard",
        col(0.7, 0.75, 0.85),
        sheet="guard",
        behaviour="stationary",
    )
    npc(
        s,
        "OrsaKell",
        500,
        187,
        "Orsa Kell",
        "orsa",
        col(0.9, 0.65, 0.5),
        sheet="orsa",
        behaviour="wander",
        wander_radius=16,
    )
    npc(
        s,
        "BramQuillon",
        300,
        360,
        "Bram Quillon",
        "bram",
        col(0.95, 0.85, 0.55),
        sheet="bram",
        behaviour="wander",
        wander_radius=18,
    )
    npc(
        s,
        "TeagueMarrow",
        580,
        98,
        "Teague Marrow",
        "teague",
        col(0.7, 0.75, 0.95),
        sheet="teague",
        behaviour="pace",
        waypoints=((556, 102), (604, 102)),
    )
    npc(
        s,
        "PellHarrow",
        95,
        305,
        "Pell Harrow",
        "pell",
        col(0.75, 0.7, 0.65),
        sheet="pell",
        behaviour="wander",
        wander_radius=22,
    )
    npc(
        s,
        "AnsaRook",
        205,
        314,
        "Ansa Rook",
        "ansa",
        col(0.85, 0.7, 0.85),
        sheet="ansa",
        behaviour="wander",
        wander_radius=20,
    )
    npc(
        s,
        "Wren",
        255,
        230,
        "Wren",
        "wren",
        col(1.0, 0.8, 0.8),
        sheet="wren",
        behaviour="wander",
        wander_radius=28,
    )

    sign(
        s,
        "PlazaSign",
        282,
        186,
        "Read",
        "North: Wreckers' Strand. East: Crossholm Road. West: Old Cairns. Below the planks: ALL SALVAGE WEIGHED AT THE HALL.",
        radius=15,
    )
    sign(
        s,
        "PlazaFire",
        320,
        208,
        "Warm hands",
        "Driftwood and peat burn low in the stone ring, throwing salt-scented sparks against the fog.",
        radius=18,
    )
    door(
        s,
        "DoorMayorHall",
        150,
        152,
        "mayor_hall",
        "Mayor's Hall",
        "res://scenes/interiors/mayor_hall.tscn",
        "from_town",
    )
    door(
        s,
        "DoorForge",
        474,
        182,
        "forge",
        "Kell's Forge",
        "res://scenes/interiors/forge.tscn",
        "from_town",
    )
    door(
        s,
        "DoorSaltGull",
        320,
        345,
        "salt_gull",
        "The Salt Gull",
        "res://scenes/interiors/salt_gull.tscn",
        "from_town",
    )
    door(
        s,
        "DoorHarrowHouse",
        80,
        292,
        "cottage_harrow",
        "Harrow Cottage",
        "res://scenes/interiors/cottage_harrow.tscn",
        "from_town",
    )
    door(
        s,
        "DoorRookCottage",
        205,
        302,
        "cottage_rook",
        "Rook Cottage",
        "res://scenes/interiors/cottage_rook.tscn",
        "from_town",
    )
    door(
        s,
        "DoorWeaverCottage",
        408,
        128,
        "cottage_weaver",
        "Weaver Cottage",
        "res://scenes/interiors/cottage_weaver.tscn",
        "from_town",
    )
    door(
        s,
        "DoorShutteredHouse",
        560,
        332,
        "cottage_shuttered",
        "Shuttered Cottage",
        "",
        "",
    )
    door(
        s,
        "DoorLanternWatch",
        580,
        105,
        "lantern_watch",
        "Lantern Watch",
        "res://scenes/interiors/lantern_watch.tscn",
        "from_town",
    )
    interactable(
        s,
        "InnBed",
        358,
        352,
        "res://scripts/rest_spot.gd",
        12,
        prompt='"Rent a bed (5 coin)"',
    )

    for i, (rx, ry) in enumerate(((86, 116), (86, 144), (212, 138)), start=1):
        pickup(
            s,
            f"RatHole{i}",
            rx,
            ry,
            "Block the hole",
            "You wedge a flat stone into the hole. Something scrabbles away behind it.",
            col(0.15, 0.1, 0.08),
            sets_flag=f"rathole_{i}",
            texture="res://assets/props/rathole.png",
        )
    for i, (x, y) in enumerate(((48, 368), (96, 392), (114, 358)), start=1):
        pickup(
            s,
            f"Moonherb{i}",
            x,
            y,
            "Gather",
            "Pale leaves that hold the dusk longer than the rest of the field. Moonherb.",
            col(0.6, 0.85, 0.95),
            item="moonherb",
            texture="res://assets/props/moonherb.png",
        )
    pickup(
        s,
        "OpenGrave",
        70,
        376,
        "Examine",
        "The grave has been dug open from below, not above. A hex-mark is burned into the cracked lid, fresh enough to smell. Among the spilled earth lies a scorched bone, and when you lift it, the mark is on it too.",
        col(0.9, 0.35, 0.2),
        item="hex_bone",
        sets_flag="saw_grave",
        requires=["stage:work_to_belong=cairns"],
        locked="Old cairns, wind-scoured. Gull bones and salt. The mayor sent you for herbs; the herbs grow close by.",
        texture="res://assets/props/open_grave.png",
    )

    exit_zone(
        s, "ToBeach", 320, 0, 48, 16, "res://scenes/world/beach.tscn", "from_town"
    )
    exit_zone(
        s,
        "ToRoad",
        W,
        212,
        16,
        52,
        "res://scenes/world/crossholm_road.tscn",
        "from_wrackmouth",
    )
    finish(
        s,
        {
            "from_beach": (320, 28),
            "from_road": (W - 28, 212),
            "from_mayor_hall": (150, 185),
            "from_forge": (474, 205),
            "from_salt_gull": (320, 370),
            "from_lantern_watch": (580, 130),
            "from_cottage_harrow": (80, 318),
            "from_cottage_rook": (205, 326),
            "from_cottage_weaver": (408, 152),
        },
        (320, 28),
    )
    return s.render()


def crossholm_road() -> str:
    W, H = 640, 360
    s = Scene()
    frame(
        s,
        (W, H),
        "CrossholmRoad",
        col(0.3, 0.39, 0.26),
        "res://assets/crossholm_road/ground.png",
        music_cue="mus_crossholm_road",
        ambience_cues=("amb_wind",),
    )
    borders(s, W, H, {"West": (176, 232)})
    s.node("Entities", "Node2D", ".", y_sort_enabled="true")
    s.node("Interactables", "Node2D", ".")
    s.node("Zones", "Node2D", ".")

    wall = col(0.47, 0.46, 0.45)
    roof = col(0.28, 0.28, 0.32)
    building(
        s,
        "WallNorth",
        600,
        170,
        (64, 170),
        wall,
        roof,
        label="Crossholm",
        door=False,
        texture="res://assets/crossholm_road/wall_north.png",
    )
    building(
        s,
        "WallSouth",
        600,
        360,
        (64, 146),
        wall,
        roof,
        door=False,
        texture="res://assets/crossholm_road/wall_south.png",
    )
    building(
        s,
        "Gate",
        600,
        214,
        (28, 44),
        col(0.3, 0.24, 0.18),
        col(0.2, 0.16, 0.12),
        label="Gate",
        door=False,
        texture="res://assets/crossholm_road/gate.png",
    )
    building(
        s,
        "BurnedFarm",
        340,
        74,
        (56, 36),
        col(0.2, 0.18, 0.16),
        col(0.15, 0.12, 0.12),
        door=False,
        texture="res://assets/crossholm_road/burned_farm.png",
    )
    building(
        s,
        "Cart",
        380,
        290,
        (46, 22),
        col(0.4, 0.3, 0.2),
        col(0.3, 0.22, 0.15),
        door=False,
        texture="res://assets/crossholm_road/cart.png",
    )
    prop_sprite(
        s,
        "RoadSignpost",
        60,
        174,
        "res://assets/props/signpost.png",
        -13,
        col_size=(10, 7),
        col_offset_y=-3.5,
    )
    prop_sprite(
        s,
        "DeadTreeRoad1",
        170,
        95,
        "res://assets/props/dead_tree.png",
        -30,
        col_size=(14, 9),
        col_offset_y=-4.5,
    )
    prop_sprite(
        s,
        "DeadTreeRoad2",
        485,
        110,
        "res://assets/props/dead_tree.png",
        -30,
        col_size=(14, 9),
        col_offset_y=-4.5,
    )
    npc(
        s,
        "DovCarrow",
        414,
        298,
        "Dov Carrow",
        "dov",
        col(0.85, 0.8, 0.6),
        2,
        sheet="dov",
        behaviour="stationary",
    )

    sign(
        s,
        "FarmSign",
        340,
        80,
        "Examine",
        "Charred roof-beams, still warm. Whatever came through here did not stop to take anything. The fields are scorched in a long, wide stripe.",
    )
    sign(
        s,
        "RoadSign",
        60,
        176,
        "Read",
        "Wrackmouth, back west. Crossholm, east. Travel by day.",
    )
    sign(
        s,
        "GateSign",
        560,
        176,
        "Read",
        "CROSSHOLM GARRISON. Gate closed at dusk. State your business.",
    )
    s.node(
        "GateZone",
        "Area2D",
        "Zones",
        position=v(560, 200),
        collision_layer="0",
        collision_mask="1",
        script=s.ext("Script", "res://scripts/flag_zone.gd"),
        flag='"reached_crossholm"',
        message='"Crossholm, at last: torches, spears and a gate that does not open. The captain will hear you out."',
    )
    s.node("Shape", "CollisionShape2D", "Zones/GateZone", shape=s.rect(24, 40))
    exit_zone(
        s,
        "ToWrackmouth",
        0,
        204,
        16,
        56,
        "res://scenes/world/wrackmouth.tscn",
        "from_road",
    )
    finish(s, {"from_wrackmouth": (30, 204)}, (30, 204))
    return s.render()


def main() -> None:
    out = ROOT / "scenes" / "world"
    (out / "wrackmouth.tscn").write_text(wrackmouth())
    (out / "crossholm_road.tscn").write_text(crossholm_road())
    print("wrote wrackmouth.tscn and crossholm_road.tscn")


if __name__ == "__main__":
    main()
