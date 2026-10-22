class_name AreaScene
extends Node2D
## Composition root for an explorable area (a town, a stretch of road). It wires the player,
## camera, HUD and conversations together; the scene tree owns the layout.

@export var area_size := Vector2i(640, 360)

@onready var _player: Player = $Entities/Player
@onready var _hud: Hud = $Hud
@onready var _dialogue: DialogueBox = $DialogueBox


func _ready() -> void:
	var camera: Camera2D = _player.get_node("Camera2D")
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = area_size.x
	camera.limit_bottom = area_size.y
	_hud.bind(_player)
	_place_player(Game.take_spawn())
	for node in $Interactables.get_children():
		if node is Interactable:
			node.interacted.connect(_hud.show_message)
	for node in $Entities.get_children():
		if node is Npc:
			node.dialogue_requested.connect(_dialogue.open.bind(_player))
	for node in $Zones.get_children():
		if node is FlagZone:
			node.triggered.connect(_hud.show_message)


func _place_player(spawn: String) -> void:
	var marker := get_node_or_null("Spawns/" + spawn) as Marker2D
	if marker:
		_player.global_position = marker.global_position
