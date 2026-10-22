class_name Npc
extends Interactable
## A villager the player can talk to. The scene that owns it opens the dialogue.

signal dialogue_requested(npc: Npc)

@export var display_name := ""
@export_file("*.json") var dialogue_path := ""
@export var sprite_sheet: Texture2D
## Row of the hero sheet to show: 0 down, 1 up, 2 left, 3 right.
@export_range(0, 3) var facing_row := 0

@onready var _sprite: Sprite2D = $Sprite2D


func _ready() -> void:
	prompt = "Talk"
	if sprite_sheet != null:
		_sprite.texture = sprite_sheet
	if _sprite.texture != null:
		var cell_h := float(_sprite.texture.get_height()) / float(maxi(1, _sprite.vframes))
		_sprite.offset = Vector2(0.0, -cell_h / 2.0)
	_sprite.frame_coords = Vector2i(0, facing_row)


func interact(player: Player) -> void:
	face(player.global_position)
	dialogue_requested.emit(self)


func face(point: Vector2) -> void:
	var d := point - global_position
	var row := 0
	if absf(d.x) > absf(d.y):
		row = 2 if d.x < 0.0 else 3
	elif d.y < 0.0:
		row = 1
	_sprite.frame_coords = Vector2i(0, row)
