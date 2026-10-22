extends Node
## Autoload. Holds what must survive scene changes (story state, the player's stats,
## display settings) and moves the player between scenes with a fade.

const STORY_PATH := "res://data/story.json"
const SETTINGS_PATH := "user://settings.cfg"
const THEME_PATH := "res://assets/ui/grim_theme.tres"
const FADE_SECONDS := 0.35

var state: GameState
var stats := Stats.new()
var fullscreen := false
var vsync := true

var _spawn := ""
var _changing := false
var _fade := ColorRect.new()


func _ready() -> void:
	reset()
	load_settings()
	var theme := load(THEME_PATH) as Theme
	if theme and get_tree() and get_tree().root:
		get_tree().root.theme = theme
	var layer := CanvasLayer.new()
	layer.layer = 100
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(_fade)
	add_child(layer)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F11 or (event.keycode == KEY_ENTER and event.alt_pressed):
			get_viewport().set_input_as_handled()
			toggle_fullscreen()


## Starts a fresh game: no flags, no items, no quests, full health.
func reset() -> void:
	state = GameState.new(StoryData.load_json(STORY_PATH))
	stats = Stats.new()
	_spawn = ""


func set_fullscreen(enabled: bool, path := SETTINGS_PATH) -> void:
	fullscreen = enabled
	_apply_display_settings()
	save_settings(path)


func toggle_fullscreen(path := SETTINGS_PATH) -> void:
	set_fullscreen(not fullscreen, path)


func set_vsync(enabled: bool, path := SETTINGS_PATH) -> void:
	vsync = enabled
	_apply_display_settings()
	save_settings(path)


func toggle_vsync(path := SETTINGS_PATH) -> void:
	set_vsync(not vsync, path)


func save_settings(path := SETTINGS_PATH) -> void:
	var cfg := ConfigFile.new()
	cfg.load(path)
	cfg.set_value("display", "fullscreen", fullscreen)
	cfg.set_value("display", "vsync", vsync)
	cfg.save(path)


func load_settings(path := SETTINGS_PATH) -> void:
	var cfg := ConfigFile.new()
	if cfg.load(path) == OK:
		fullscreen = bool(cfg.get_value("display", "fullscreen", false))
		vsync = bool(cfg.get_value("display", "vsync", true))
	else:
		fullscreen = false
		vsync = true
	_apply_display_settings()


func _apply_display_settings() -> void:
	if DisplayServer.get_name() == "headless":
		return
	var target_mode := (
		DisplayServer.WINDOW_MODE_FULLSCREEN
		if fullscreen
		else DisplayServer.WINDOW_MODE_WINDOWED
	)
	if DisplayServer.window_get_mode() != target_mode:
		DisplayServer.window_set_mode(target_mode)
	var target_vsync := (
		DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED
	)
	if DisplayServer.window_get_vsync_mode() != target_vsync:
		DisplayServer.window_set_vsync_mode(target_vsync)


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
