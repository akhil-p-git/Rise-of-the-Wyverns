class_name Hud
extends CanvasLayer
## Stat bars, the interact prompt, and a short message line.

const MESSAGE_SECONDS := 4.0
const InventoryPanelScript = preload("res://scripts/ui/inventory_panel.gd")

@onready var _health: ProgressBar = $Bars/Health
@onready var _stamina: ProgressBar = $Bars/Stamina
@onready var _mana: ProgressBar = $Bars/Mana
@onready var _prompt: Label = $Prompt
@onready var _message: Label = $Message
@onready var _message_timer: Timer = $MessageTimer
@onready var _tracker: Label = $Tracker
@onready var _time_label: Label = get_node_or_null("TimeLabel")
@onready var _rested_label: Label = get_node_or_null("RestedLabel")
@onready var inventory: InventoryPanelScript = $InventoryPanel
@onready var wait_panel: WaitPanel = $WaitPanel

var _player: Player


func _ready() -> void:
	_message_timer.timeout.connect(func() -> void: _message.text = "")
	Game.state.quest_changed.connect(_refresh_tracker.unbind(1))
	Game.state.flag_changed.connect(_refresh_tracker.unbind(1))
	Game.state.inventory_changed.connect(_refresh_tracker.unbind(1))
	_refresh_tracker()
	_update_time()
	Game.rested_changed.connect(_update_rested)
	TimeSystem.hour_passed.connect(_update_rested.unbind(1))
	_update_rested()
	TimeSystem.hour_passed.connect(_update_time.unbind(1))
	TimeSystem.day_phase_changed.connect(_update_time.unbind(1))
	wait_panel.waited.connect(_on_waited)


func _update_time() -> void:
	if _time_label != null and TimeSystem != null:
		_time_label.text = TimeSystem.get_status_string()


func _update_rested() -> void:
	if _rested_label != null:
		_rested_label.text = "Well Rested (+10% XP)" if Game.is_well_rested() else ""


func bind(player: Player) -> void:
	_player = player
	var stats := player.stats
	stats.changed.connect(_on_stats_changed.bind(stats))
	player.prompt_changed.connect(_on_prompt_changed)
	_refresh(stats)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("wait") and _can_wait():
		get_viewport().set_input_as_handled()
		_player.input_enabled = false
		wait_panel.open()


func _can_wait() -> bool:
	return _player != null and _player.input_enabled and not inventory.is_open() and not wait_panel.is_open()


func _on_waited(hours: int) -> void:
	_player.input_enabled = true
	if hours > 0:
		show_message("You wait %d hour%s, and wake rested. It is %s." % [hours, "" if hours == 1 else "s", TimeSystem.get_time_string()])


func _on_stats_changed(_stat: StringName, stats: Stats) -> void:
	_refresh(stats)


func show_message(text: String) -> void:
	_message.text = Game.format_text(text)
	_message_timer.start(MESSAGE_SECONDS)


## Active quests with their current objective, then the coin purse.
func _refresh_tracker() -> void:
	var lines: Array[String] = []
	for id in Game.state.quests.active_ids():
		lines.append("%s\n%s" % [Game.state.quests.title(id), Game.state.objective(id)])
	var coin := Game.state.count("coin")
	if coin > 0:
		lines.append("%d coin" % coin)
	_tracker.text = "\n\n".join(lines)


func _refresh(stats: Stats) -> void:
	_set_bar(_health, stats.health, stats.max_health)
	_set_bar(_stamina, stats.stamina, stats.max_stamina)
	_set_bar(_mana, stats.mana, stats.max_mana)


func _set_bar(bar: ProgressBar, value: float, max_value: float) -> void:
	bar.max_value = max_value
	bar.value = value


func _on_prompt_changed(text: String) -> void:
	_prompt.text = "" if text.is_empty() else "E: " + text
