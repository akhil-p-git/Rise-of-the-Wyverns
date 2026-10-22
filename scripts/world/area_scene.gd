class_name AreaScene
extends Node2D
## Composition root for an explorable area (a town, a stretch of road). It wires the player,
## camera, HUD, audio and conversations together; the scene tree owns the layout.

@export var area_size := Vector2i(640, 360)
@export var music_cue := "mus_wrackmouth"
@export var ambience_cues: PackedStringArray = ["amb_wind", "amb_gulls"]

@onready var _player: Player = $Entities/Player
@onready var _hud: Hud = $Hud
@onready var _dialogue: DialogueBox = $DialogueBox


func _ready() -> void:
	var camera: Camera2D = _player.get_node("Camera2D")
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = area_size.x
	camera.limit_bottom = area_size.y
	_player.surface_resolver = _surface_at
	Audio.play_music(music_cue)
	Audio.play_ambience(Array(ambience_cues))
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


func _surface_at(pos: Vector2) -> String:
	if name == "Wrackmouth":
		if pos.x >= 260.0 and pos.x <= 380.0 and pos.y >= 165.0 and pos.y <= 255.0:
			return "step_stone"
		if pos.x < 140.0 and pos.y > 330.0:
			return "step_stone"
		return "step_gravel"
	return "step_gravel"
