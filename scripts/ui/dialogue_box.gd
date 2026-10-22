class_name DialogueBox
extends CanvasLayer
## Conversation window. Opens an NPC's dialogue tree, types the text out, and lets the player
## continue (E or Space) or pick a choice (arrows and Space, or the number keys).

signal closed

const CHARS_PER_SECOND := 70.0

var _runner := DialogueRunner.new()
var _player: Player
var _opened_frame := -1
var _typing: Tween

@onready var _panel: Control = $Panel
@onready var _name: Label = $Panel/Margin/Box/Name
@onready var _text: Label = $Panel/Margin/Box/Text
@onready var _choices: VBoxContainer = $Panel/Margin/Box/Choices
@onready var _hint: Label = $Panel/Margin/Box/Hint


func _ready() -> void:
	_panel.hide()


func is_open() -> bool:
	return _panel.visible


## Starts the NPC's conversation. Does nothing if none of its entries match.
func open(npc: Npc, player: Player) -> void:
	if is_open() or not _runner.begin(StoryData.load_json(npc.dialogue_path), Game.state):
		return
	_player = player
	_player.input_enabled = false
	_opened_frame = Engine.get_process_frames()
	_panel.show()
	_show_node()


func _unhandled_input(event: InputEvent) -> void:
	if not is_open() or Engine.get_process_frames() == _opened_frame:
		return
	if event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		_close()
	elif event.is_action_pressed("interact"):
		get_viewport().set_input_as_handled()
		_confirm()
	elif event is InputEventKey and event.pressed and not event.echo:
		var number: int = event.keycode - KEY_1
		if number >= 0 and number < _choices.get_child_count() and _choices.visible:
			get_viewport().set_input_as_handled()
			_choose(number)


func _confirm() -> void:
	if _typing and _typing.is_running():
		_typing.kill()
		_text.visible_ratio = 1.0
		_finished_typing()
	elif _choices.visible:
		var focused := get_viewport().gui_get_focus_owner()
		if focused is Button:
			focused.pressed.emit()
	else:
		_choose(0)


func _choose(index: int) -> void:
	_runner.advance(index)
	if _runner.finished:
		_close()
	else:
		_show_node()


func _show_node() -> void:
	_name.text = _runner.speaker()
	_text.text = _runner.text()
	for child in _choices.get_children():
		child.queue_free()
	_choices.hide()
	_hint.hide()
	_text.visible_ratio = 0.0
	_typing = create_tween()
	_typing.tween_property(_text, "visible_ratio", 1.0, maxf(_text.text.length() / CHARS_PER_SECOND, 0.05))
	_typing.finished.connect(_finished_typing)


func _finished_typing() -> void:
	var options := _runner.choices()
	if options.is_empty():
		_hint.text = "E / Space: continue"
		_hint.show()
		return
	for i in options.size():
		var button := Button.new()
		button.text = "%d. %s" % [i + 1, options[i]["text"]]
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.flat = true
		button.pressed.connect(_choose.bind(i))
		_choices.add_child(button)
	_choices.show()
	_choices.get_child(0).grab_focus()


func _close() -> void:
	if _typing:
		_typing.kill()
	_panel.hide()
	_player.input_enabled = true
	closed.emit()
