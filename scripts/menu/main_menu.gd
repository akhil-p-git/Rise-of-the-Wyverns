class_name MainMenu
extends Control
## Title screen: New Game -> Character Creation, Settings (window mode, vsync, audio buses),
## Credits, and Quit. Continue stays hidden until save/load lands.

const CREATION_SCENE := "res://scenes/menu/character_creation.tscn"
const CREDITS_PATH := "res://data/credits.json"

@onready var _main_box: VBoxContainer = $Center/MainBox
@onready var _continue_btn: Button = $Center/MainBox/Buttons/ContinueButton
@onready var _new_game_btn: Button = $Center/MainBox/Buttons/NewGameButton
@onready var _settings_btn: Button = $Center/MainBox/Buttons/SettingsButton
@onready var _credits_btn: Button = $Center/MainBox/Buttons/CreditsButton
@onready var _quit_btn: Button = $Center/MainBox/Buttons/QuitButton

@onready var _settings_panel: PanelContainer = $Center/SettingsPanel
@onready var _fullscreen_btn: Button = $Center/SettingsPanel/Margin/VBox/FullscreenRow/FullscreenButton
@onready var _vsync_btn: Button = $Center/SettingsPanel/Margin/VBox/VsyncRow/VsyncButton
@onready var _audio_box: VBoxContainer = $Center/SettingsPanel/Margin/VBox/AudioBox
@onready var _settings_back_btn: Button = $Center/SettingsPanel/Margin/VBox/BackButton

@onready var _credits_panel: PanelContainer = $Center/CreditsPanel
@onready var _credits_label: Label = $Center/CreditsPanel/Margin/VBox/CreditsText
@onready var _credits_back_btn: Button = $Center/CreditsPanel/Margin/VBox/BackButton

var _bus_sliders := {}


func _ready() -> void:
	_continue_btn.hide()
	_settings_panel.hide()
	_credits_panel.hide()

	_new_game_btn.pressed.connect(_on_new_game)
	_settings_btn.pressed.connect(_open_settings)
	_credits_btn.pressed.connect(_open_credits)
	_quit_btn.pressed.connect(func() -> void: get_tree().quit())

	_fullscreen_btn.pressed.connect(_on_toggle_fullscreen)
	_vsync_btn.pressed.connect(_on_toggle_vsync)
	_settings_back_btn.pressed.connect(_close_subpanels)
	_credits_back_btn.pressed.connect(_close_subpanels)

	_build_audio_sliders()
	_refresh_settings_labels()
	_load_credits_text()
	_new_game_btn.grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if _settings_panel.visible or _credits_panel.visible:
			get_viewport().set_input_as_handled()
			_close_subpanels()


func _on_new_game() -> void:
	Game.go_to(CREATION_SCENE)


func _open_settings() -> void:
	_refresh_settings_labels()
	_main_box.hide()
	_credits_panel.hide()
	_settings_panel.show()
	_fullscreen_btn.grab_focus()


func _open_credits() -> void:
	_load_credits_text()
	_main_box.hide()
	_settings_panel.hide()
	_credits_panel.show()
	_credits_back_btn.grab_focus()


func _close_subpanels() -> void:
	var from_credits := _credits_panel.visible
	_settings_panel.hide()
	_credits_panel.hide()
	_main_box.show()
	if from_credits:
		_credits_btn.grab_focus()
	else:
		_settings_btn.grab_focus()


func _on_toggle_fullscreen() -> void:
	Game.toggle_fullscreen()
	_refresh_settings_labels()


func _on_toggle_vsync() -> void:
	Game.toggle_vsync()
	_refresh_settings_labels()


func _refresh_settings_labels() -> void:
	_fullscreen_btn.text = "Fullscreen" if Game.fullscreen else "Windowed"
	_vsync_btn.text = "Enabled" if Game.vsync else "Disabled"
	var audio := get_node_or_null("/root/Audio")
	if audio:
		for bus_name: String in _bus_sliders:
			var slider: HSlider = _bus_sliders[bus_name]
			slider.set_value_no_signal(audio.get_bus_volume(bus_name))


func _build_audio_sliders() -> void:
	var audio := get_node_or_null("/root/Audio")
	if audio == null:
		return
	for child in _audio_box.get_children():
		child.queue_free()
	_bus_sliders.clear()
	for bus_name: String in ["Master", "Music", "SFX", "Ambience", "UI"]:
		var row := HBoxContainer.new()
		var lbl := Label.new()
		lbl.text = bus_name
		lbl.custom_minimum_size = Vector2(80, 0)
		var slider := HSlider.new()
		slider.min_value = 0.0
		slider.max_value = 1.0
		slider.step = 0.05
		slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		slider.custom_minimum_size = Vector2(120, 16)
		slider.value = audio.get_bus_volume(bus_name)
		slider.value_changed.connect(func(v: float) -> void: audio.set_bus_volume(bus_name, v))
		row.add_child(lbl)
		row.add_child(slider)
		_audio_box.add_child(row)
		_bus_sliders[bus_name] = slider


func _load_credits_text() -> void:
	if not FileAccess.file_exists(CREDITS_PATH):
		_credits_label.text = (
			"Rise of the Wyverns\n"
			+ "Font: Noto Serif Display (The Noto Project Authors, SIL OFL 1.1)\n"
			+ "Audio & Additional Credits: see ASSETS.md"
		)
		return
	var data := StoryData.load_json(CREDITS_PATH)
	var lines: Array[String] = ["Rise of the Wyverns — Credits"]
	for entry: Dictionary in data.get("entries", []):
		lines.append(
			"%s: %s (%s)"
			% [entry.get("role", "Asset"), entry.get("author", "Unknown"), entry.get("license", "")]
		)
	_credits_label.text = "\n".join(lines)
