class_name AreaScene
extends Node2D
## Composition root for an explorable area (a town, a stretch of road). It wires the player,
## camera, HUD, audio and conversations together; the scene tree owns the layout.

@export var area_size := Vector2i(640, 360)
@export var music_cue := "mus_wrackmouth"
@export var ambience_cues: PackedStringArray = ["amb_wind", "amb_gulls"]
@export var is_outdoor := true
## Which schedule place this scene is: "town" for Wrackmouth, the building id for an interior, "" for the rest.
@export var place_id := ""

@onready var _player: Player = $Entities/Player
@onready var _hud: Hud = $Hud
@onready var _dialogue: DialogueBox = $DialogueBox

## Indoor ambient at full day (daylight through the windows) and at night (hearths and candles only).
const INDOOR_DAY := Color(1.0, 0.96, 0.88, 1.0)
const INDOOR_NIGHT := Color(0.5, 0.46, 0.58, 1.0)

var _day_night_mod: CanvasModulate = null
var _indoor_mod: CanvasModulate = null


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

	if is_outdoor:
		var mod := get_node_or_null("DayNightModulate") as CanvasModulate
		if mod == null:
			mod = CanvasModulate.new()
			mod.name = "DayNightModulate"
			add_child(mod)
		_day_night_mod = mod
		if TimeSystem:
			_day_night_mod.color = TimeSystem.get_ambient_color()

	if not is_outdoor:
		_indoor_mod = get_node_or_null("WarmIndoorLight") as CanvasModulate
		_update_indoor_light()

	for node in $Interactables.get_children():
		if node is Interactable:
			node.interacted.connect(_hud.show_message)
	for node in $Entities.get_children():
		if node is Npc:
			node.dialogue_requested.connect(_dialogue.open.bind(_player))
	for node in $Zones.get_children():
		if node is FlagZone:
			node.triggered.connect(_hud.show_message)


func _process(_delta: float) -> void:
	if is_outdoor and _day_night_mod != null and TimeSystem:
		_day_night_mod.color = TimeSystem.get_ambient_color()
	elif _indoor_mod != null:
		_update_indoor_light()


## Opens the sleep menu (a bed was used).
func open_sleep_menu() -> void:
	_hud.open_sleep()


## The AreaScene that contains `node`, or null.
static func of(node: Node) -> AreaScene:
	var n := node.get_parent()
	while n != null and not n is AreaScene:
		n = n.get_parent()
	return n as AreaScene


## The ambient tint currently applied to this area's world.
func ambient_color() -> Color:
	if is_outdoor:
		return TimeSystem.get_ambient_color()
	return INDOOR_DAY.lerp(INDOOR_NIGHT, TimeSystem.get_night_factor())


## Multiplier that cancels the ambient tint, for light sprites (window glow, flames) that must keep their own
## colour in the dark instead of being darkened with the walls around them.
func light_compensation() -> Color:
	var amb := ambient_color()
	return Color(1.0 / amb.r, 1.0 / amb.g, 1.0 / amb.b, 1.0)


func _update_indoor_light() -> void:
	if _indoor_mod != null:
		_indoor_mod.color = ambient_color()


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
