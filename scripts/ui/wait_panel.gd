class_name WaitPanel
extends Control
## "Wait" menu opened with T, or "Sleep" menu opened at a bed: pick 1-24 hours, confirm to skip the clock
## ahead and refill every vital. Sleeping also leaves the player Well Rested, whatever the length.

## Emitted when the menu closes: the hours waited, or 0 when cancelled.
signal waited(hours: int)

const MIN_HOURS := 1
const MAX_HOURS := 24

@onready var _title_label: Label = $Panel/Margin/VBox/TitleLabel
@onready var _hint_label: Label = $Panel/Margin/VBox/HintLabel
@onready var _now_label: Label = $Panel/Margin/VBox/NowLabel
@onready var _hours_label: Label = $Panel/Margin/VBox/Row/HoursLabel
@onready var _less_btn: Button = $Panel/Margin/VBox/Row/LessButton
@onready var _more_btn: Button = $Panel/Margin/VBox/Row/MoreButton
@onready var _wait_btn: Button = $Panel/Margin/VBox/Buttons/WaitButton
@onready var _cancel_btn: Button = $Panel/Margin/VBox/Buttons/CancelButton

var hours := MIN_HOURS
## True when opened at a bed: confirming sleeps (with the Well Rested bonus) instead of waiting.
var sleeping := false


func _ready() -> void:
	visible = false
	_less_btn.pressed.connect(adjust.bind(-1))
	_more_btn.pressed.connect(adjust.bind(1))
	_wait_btn.pressed.connect(confirm)
	_cancel_btn.pressed.connect(cancel)


func is_open() -> bool:
	return visible


func open(sleep := false) -> void:
	sleeping = sleep
	hours = MIN_HOURS
	_title_label.text = "Sleep" if sleep else "Wait"
	_wait_btn.text = "Sleep" if sleep else "Wait"
	_hint_label.text = "Arrows: hours  Enter: %s  Esc: cancel" % ("sleep" if sleep else "wait")
	_refresh()
	visible = true
	Audio.play_ui("ui_confirm")


func adjust(delta: int) -> void:
	hours = clampi(hours + delta, MIN_HOURS, MAX_HOURS)
	_refresh()


func confirm() -> void:
	if not visible:
		return
	visible = false
	var slept := hours
	if sleeping:
		Audio.play_sfx("rest_fire")
		await Game.blackout(Game.sleep_in_bed.bind(slept))
	else:
		TimeSystem.wait_hours(slept)
		Game.stats.restore_all()
		Audio.play_ui("ui_confirm")
	waited.emit(slept)


func cancel() -> void:
	if not visible:
		return
	visible = false
	Audio.play_ui("ui_back")
	waited.emit(0)


func _refresh() -> void:
	_now_label.text = "It is %s." % TimeSystem.get_time_string()
	_hours_label.text = "%d hour%s" % [hours, "" if hours == 1 else "s"]


func _unhandled_input(event: InputEvent) -> void:
	if not visible or not (event is InputEventKey) or not event.pressed:
		return
	var k := event as InputEventKey
	var key := k.physical_keycode
	if key == KEY_LEFT or key == KEY_A or key == KEY_DOWN or key == KEY_S:
		adjust(-1)
	elif key == KEY_RIGHT or key == KEY_D or key == KEY_UP or key == KEY_W:
		adjust(1)
	elif k.echo:
		return
	elif key == KEY_ENTER or key == KEY_KP_ENTER or key == KEY_SPACE:
		confirm()
	elif key == KEY_ESCAPE or key == KEY_T:
		cancel()
	else:
		return
	get_viewport().set_input_as_handled()
