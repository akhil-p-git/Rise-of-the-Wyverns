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
    s.node(name, "StaticBody2D", "Entities", **props)
    s.node(
        "Shape",
        "CollisionShape2D",
        f"Entities/{name}",
        position=v(0, -h / 2),
        shape=s.rect(w, h),
    )


def prop_sprite(s: Scene, name: str, x, y, texture: str, offset_y: float = -12) -> None:
    s.node(
        name,
        "Sprite2D",
        "Entities",
        position=v(x, y),
        texture=s.ext("Texture2D", texture),
        offset=v(0, offset_y),
    )


def sign(s: Scene, name: str, x, y, prompt: str, message: str) -> None:
    interactable(
        s,
        name,
        x,
        y,
        "res://scripts/interactable.gd",
        10,
        prompt=f'"{prompt}"',
        message=f'"{message}"',
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
    s: Scene, name: str, x, y, display, dialogue, tint, row=0, sheet: str = ""
) -> None:
    props = {
        "position": v(x, y),
        "display_name": f'"{display}"',
        "dialogue_path": f'"res://data/dialogue/{dialogue}.json"',
        "facing_row": str(row),
    }
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
    )

    prop_sprite(
        s, "PlazaCampfire", 320, 210, "res://assets/props/campfire_lit.png", -10
    )
    prop_sprite(s, "PlazaSignpost", 282, 186, "res://assets/props/signpost.png", -13)
    prop_sprite(s, "DeadTreeWest", 38, 125, "res://assets/props/dead_tree.png", -30)
    prop_sprite(s, "DeadTreeCairn", 136, 382, "res://assets/props/dead_tree.png", -30)
    prop_sprite(s, "DeadTreeEast", 608, 280, "res://assets/props/dead_tree.png", -30)

    npc(
        s,
        "MayorTolle",
        150,
        162,
        "Mayor Tolle",
        "mayor",
        col(0.55, 0.85, 0.6),
        sheet="mayor",
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
    )
    npc(s, "Wren", 255, 230, "Wren", "wren", col(1.0, 0.8, 0.8), sheet="wren")

    sign(
        s,
        "HallSign",
        120,
        160,
        "Read",
        "Wrackmouth Hall. Salvage claims are filed here. Walk-ins are not welcome after dark.",
    )
    sign(
        s,
        "ForgeSign",
        470,
        187,
        "Read",
        "KELL. Bone and iron. Mended, forged, weighed. No credit.",
    )
    sign(s, "InnSign", 275, 352, "Read", "THE SALT GULL. Beds, stew, no questions.")
    sign(
        s,
        "ShutterSign",
        560,
        340,
        "Examine",
        "Shuttered. The salvager family left a week before the autumn wrecks stopped.",
    )
    sign(
        s,
        "HarrowSign",
        80,
        300,
        "Examine",
        "Nets drying on the wall. Pell Harrow's house.",
    )
    sign(
        s,
        "RookSign",
        205,
        310,
        "Examine",
        "A lantern burns in the window all night. The widow Rook's.",
    )
    sign(
        s,
        "WatchSign",
        560,
        95,
        "Read",
        "LANTERN WATCH. Keepers log every light and every shape in the fog.",
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

    for i, x in enumerate((115, 150, 185), start=1):
        pickup(
            s,
            f"RatHole{i}",
            x,
            82,
            "Block the hole",
            "You wedge a flat stone into the hole. Something scrabbles away behind it.",
            col(0.15, 0.1, 0.08),
            sets_flag=f"rathole_{i}",
            texture="res://assets/props/rathole.png",
        )
    for i, (x, y) in enumerate(((44, 372), (92, 392), (112, 360)), start=1):
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
    finish(s, {"from_beach": (320, 28), "from_road": (W - 28, 212)}, (320, 28))
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
    prop_sprite(s, "RoadSignpost", 60, 174, "res://assets/props/signpost.png", -13)
    prop_sprite(s, "DeadTreeRoad1", 170, 95, "res://assets/props/dead_tree.png", -30)
    prop_sprite(s, "DeadTreeRoad2", 485, 110, "res://assets/props/dead_tree.png", -30)
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
