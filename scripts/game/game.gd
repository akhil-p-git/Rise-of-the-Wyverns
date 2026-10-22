extends Node
## Autoload. Holds what must survive scene changes (story state, the player's stats) and
## moves the player between scenes with a fade.

const STORY_PATH := "res://data/story.json"
const FADE_SECONDS := 0.35

var state: GameState
var stats := Stats.new()

var _spawn := ""
var _changing := false
var _fade := ColorRect.new()


func _ready() -> void:
	reset()
	var layer := CanvasLayer.new()
	layer.layer = 100
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_fade)
	add_child(layer)


## Starts a fresh game: no flags, no items, no quests, full health.
func reset() -> void:
	state = GameState.new(StoryData.load_json(STORY_PATH))
	stats = Stats.new()
	_spawn = ""


## Fades out, loads the scene, and fades in; the new scene calls `take_spawn()` to find its
## entry point.
func go_to(scene_path: String, spawn := "") -> void:
	if _changing:
		return
	_changing = true
	_spawn = spawn
	await _fade_to(1.0)
	get_tree().change_scene_to_file(scene_path)
	await get_tree().process_frame
	await get_tree().process_frame
	await _fade_to(0.0)
	_changing = false


## The spawn marker name the previous scene asked for; empty when none. Read once.
func take_spawn() -> String:
	var spawn := _spawn
	_spawn = ""
	return spawn


## Fades to black and back, calling `midway` while the screen is dark.
func blackout(midway: Callable) -> void:
	await _fade_to(1.0)
	midway.call()
	await get_tree().create_timer(0.4).timeout
	await _fade_to(0.0)


func _fade_to(alpha: float) -> void:
	var tween := create_tween()
	tween.tween_property(_fade, "color:a", alpha, FADE_SECONDS)
	await tween.finished
