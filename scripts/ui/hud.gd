class_name Hud
extends CanvasLayer
## Stat bars, the interact prompt, and a short message line.

const MESSAGE_SECONDS := 4.0

@onready var _health: ProgressBar = $Bars/Health
@onready var _stamina: ProgressBar = $Bars/Stamina
@onready var _mana: ProgressBar = $Bars/Mana
@onready var _prompt: Label = $Prompt
@onready var _message: Label = $Message
@onready var _message_timer: Timer = $MessageTimer
@onready var _tracker: Label = $Tracker


func _ready() -> void:
	_message_timer.timeout.connect(func() -> void: _message.text = "")
	Game.state.quest_changed.connect(_refresh_tracker.unbind(1))
	Game.state.flag_changed.connect(_refresh_tracker.unbind(1))
	Game.state.inventory_changed.connect(_refresh_tracker.unbind(1))
	_refresh_tracker()


func bind(player: Player) -> void:
	var stats := player.stats
	stats.changed.connect(_on_stats_changed.bind(stats))
	player.prompt_changed.connect(_on_prompt_changed)
	_refresh(stats)


func _on_stats_changed(_stat: StringName, stats: Stats) -> void:
	_refresh(stats)


func show_message(text: String) -> void:
	_message.text = text
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
