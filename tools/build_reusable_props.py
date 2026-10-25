"""Generates reusable Godot PackedScene (.tscn) prop assets in scenes/interiors/props/:
- wall_torch.tscn
- hearth.tscn
- bed_wood.tscn
- bed_inn.tscn
- bed_kid.tscn
- candle_stand.tscn
- table_food.tscn
- table_wood.tscn
- chair_wood.tscn
- stool.tscn
- bench.tscn
- cupboard.tscn
- chest.tscn
- cauldron.tscn
- shelf_unit.tscn
- weapon_rack.tscn
- tool_rack.tscn

Run: python3 tools/build_reusable_props.py
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PROPS_DIR = ROOT / "scenes" / "interiors" / "props"
PROPS_DIR.mkdir(parents=True, exist_ok=True)
FURN = ROOT / "assets" / "interiors" / "furniture"


def img_size(name: str) -> tuple[int, int]:
    with Image.open(FURN / f"{name}.png") as im:
        return im.size


def gen_static_prop(
    filename: str,
    node_name: str,
    tex_name: str,
    cw: float,
    ch: float,
    scale: float = 0.5,
) -> None:
    _, h = img_size(tex_name)
    offset_y = -h / 2.0
    col_y = -ch / 2.0
    content = f"""[gd_scene format=3]

[ext_resource type="Texture2D" path="res://assets/interiors/furniture/{tex_name}.png" id="1_tex"]

[sub_resource type="RectangleShape2D" id="shape"]
size = Vector2({cw:g}, {ch:g})

[node name="{node_name}" type="StaticBody2D"]

[node name="Sprite2D" type="Sprite2D" parent="."]
scale = Vector2({scale:g}, {scale:g})
texture = ExtResource("1_tex")
offset = Vector2(0, {offset_y:g})

[node name="Shape" type="CollisionShape2D" parent="."]
position = Vector2(0, {col_y:g})
shape = SubResource("shape")
"""
    (PROPS_DIR / filename).write_text(content)


def gen_wall_torch() -> None:
    content = """[gd_scene format=3]

[ext_resource type="Script" path="res://scripts/world/animated_prop.gd" id="1_anim"]
[ext_resource type="Texture2D" path="res://assets/interiors/furniture/torch_wall.png" id="2_bracket"]
[ext_resource type="Texture2D" path="res://assets/interiors/furniture/torch_flame_sheet.png" id="3_flame"]
[ext_resource type="Texture2D" path="res://assets/interiors/furniture/torch_glow.png" id="4_glow"]

[node name="WallTorch" type="Node2D"]

[node name="Bracket" type="Sprite2D" parent="."]
z_index = -1
scale = Vector2(0.5, 0.5)
texture = ExtResource("2_bracket")
offset = Vector2(0, -22)

[node name="Flame" type="StaticBody2D" parent="."]
position = Vector2(0, -10)
script = ExtResource("1_anim")
fps = 7.0
glow_texture = ExtResource("4_glow")
glow_scale = Vector2(0.5, 0.5)
glow_offset = Vector2(0, -6)
z_index = 1

[node name="Sprite2D" type="Sprite2D" parent="Flame"]
scale = Vector2(0.5, 0.5)
texture = ExtResource("3_flame")
offset = Vector2(0, -16)
hframes = 4
"""
    (PROPS_DIR / "wall_torch.tscn").write_text(content)


def gen_hearth() -> None:
    w, h = img_size("hearth")
    cw, ch = 44.0, 10.0
    fire_y = -(h - 78) * 0.5 + 0.5
    content = f"""[gd_scene format=3]

[ext_resource type="Texture2D" path="res://assets/interiors/furniture/hearth.png" id="1_hearth"]
[ext_resource type="Script" path="res://scripts/world/animated_prop.gd" id="2_anim"]
[ext_resource type="Texture2D" path="res://assets/interiors/furniture/hearth_fire_sheet.png" id="3_fire"]
[ext_resource type="Texture2D" path="res://assets/interiors/furniture/hearth_glow.png" id="4_glow"]

[sub_resource type="RectangleShape2D" id="shape"]
size = Vector2({cw:g}, {ch:g})

[node name="Hearth" type="StaticBody2D"]

[node name="Sprite2D" type="Sprite2D" parent="."]
scale = Vector2(0.5, 0.5)
texture = ExtResource("1_hearth")
offset = Vector2(0, -{h / 2.0:g})

[node name="Shape" type="CollisionShape2D" parent="."]
position = Vector2(0, -{ch / 2.0:g})
shape = SubResource("shape")

[node name="HearthFire" type="StaticBody2D" parent="."]
position = Vector2(0, {fire_y:g})
script = ExtResource("2_anim")
fps = 7.0
glow_texture = ExtResource("4_glow")
glow_scale = Vector2(0.55, 0.4)
glow_offset = Vector2(0, -10)
z_index = 1

[node name="Sprite2D" type="Sprite2D" parent="HearthFire"]
scale = Vector2(0.5, 0.5)
texture = ExtResource("3_fire")
offset = Vector2(0, -20)
hframes = 4
"""
    (PROPS_DIR / "hearth.tscn").write_text(content)


def gen_candle_stand() -> None:
    content = """[gd_scene format=3]

[ext_resource type="Script" path="res://scripts/world/animated_prop.gd" id="1_anim"]
[ext_resource type="Texture2D" path="res://assets/interiors/furniture/candle_stand.png" id="2_stand"]
[ext_resource type="Texture2D" path="res://assets/interiors/furniture/candle_glow.png" id="3_glow"]

[sub_resource type="RectangleShape2D" id="shape"]
size = Vector2(6, 5)

[node name="CandleStand" type="StaticBody2D"]
script = ExtResource("1_anim")
fps = 1.0
glow_texture = ExtResource("3_glow")
glow_scale = Vector2(0.55, 0.55)
glow_offset = Vector2(0, -17)

[node name="Sprite2D" type="Sprite2D" parent="."]
scale = Vector2(0.5, 0.5)
texture = ExtResource("2_stand")
offset = Vector2(0, -20)

[node name="Shape" type="CollisionShape2D" parent="."]
position = Vector2(0, -2.5)
shape = SubResource("shape")
"""
    (PROPS_DIR / "candle_stand.tscn").write_text(content)


def main() -> None:
    gen_wall_torch()
    gen_hearth()
    gen_candle_stand()
    gen_static_prop("bed_wood.tscn", "BedWood", "bed_wood", 36.0, 14.0)
    gen_static_prop("bed_inn.tscn", "BedInn", "bed_inn", 36.0, 14.0)
    gen_static_prop("bed_kid.tscn", "BedKid", "bed_kid", 28.0, 12.0)
    gen_static_prop("table_wood.tscn", "TableWood", "table_wood", 48.0, 10.0)
    gen_static_prop("table_food.tscn", "TableFood", "table_food", 48.0, 10.0)
    gen_static_prop("chair_wood.tscn", "ChairWood", "chair_wood", 18.0, 8.0)
    gen_static_prop("stool.tscn", "Stool", "stool", 10.0, 6.0)
    gen_static_prop("bench.tscn", "Bench", "bench", 44.0, 8.0)
    gen_static_prop("cupboard.tscn", "Cupboard", "cupboard", 32.0, 10.0)
    gen_static_prop("chest.tscn", "Chest", "chest", 26.0, 9.0)
    gen_static_prop("cauldron.tscn", "Cauldron", "cauldron", 16.0, 8.0)
    gen_static_prop("shelf_unit.tscn", "ShelfUnit", "shelf_unit", 26.0, 8.0)
    gen_static_prop("weapon_rack.tscn", "WeaponRack", "weapon_rack", 30.0, 8.0)
    gen_static_prop("tool_rack.tscn", "ToolRack", "tool_rack", 32.0, 8.0)
    print(f"Generated 17 reusable prop PackedScenes in {PROPS_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
