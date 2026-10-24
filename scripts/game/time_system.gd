class_name TimeSystemComponent
extends Node
## Global day/night cycle controller.
## Tracks a 24-hour clock. 10:00 PM (22:00) to 6:00 AM (06:00) is night.
## All town buildings lock after 10 PM, except the Inn (The Salt Gull), which never locks.
## Buildings unlock at 6 AM.

signal hour_passed(hour: int)
signal day_phase_changed(is_night: bool)

const MINUTES_PER_DAY := 1440.0
# 1 real second = 2 game minutes; full 24h day = 12 real minutes (720 seconds).
const TIME_SCALE := 120.0

## Building ids exempt from the night lock (the inn) and ids that never open (the abandoned cottage).
const ALWAYS_OPEN: Array[String] = ["salt_gull"]
const NAILED_SHUT: Array[String] = ["cottage_shuttered"]

var current_minute: float = 8.0 * 60.0 # Starts at 8:00 AM
var _last_hour: int = 8
var _was_night: bool = false
var paused: bool = false


func _ready() -> void:
	_last_hour = get_hour()
	_was_night = is_night()


func _process(delta: float) -> void:
	if paused:
		return
	advance_seconds(delta)


func advance_seconds(delta: float) -> void:
	current_minute = fposmod(current_minute + delta * (TIME_SCALE / 60.0), MINUTES_PER_DAY)
	var h := get_hour()
	if h != _last_hour:
		_last_hour = h
		hour_passed.emit(h)
	var night := is_night()
	if night != _was_night:
		_was_night = night
		day_phase_changed.emit(night)


func set_time(hour: int, minute: int = 0) -> void:
	current_minute = float((hour % 24) * 60 + (minute % 60))
	_last_hour = get_hour()
	_was_night = is_night()
	day_phase_changed.emit(_was_night)


func get_hour() -> int:
	return int(current_minute / 60.0) % 24


func get_minute() -> int:
	return int(current_minute) % 60


func is_night() -> bool:
	var h := get_hour()
	return h >= 22 or h < 6


func is_day() -> bool:
	return not is_night()


func get_time_string() -> String:
	var h := get_hour()
	var m := get_minute()
	var period := "AM" if h < 12 else "PM"
	var disp_h := h % 12
	if disp_h == 0:
		disp_h = 12
	return "%d:%02d %s" % [disp_h, m, period]


func get_status_string() -> String:
	var t_str := get_time_string()
	if is_night():
		return "%s · Night (Town Locked)" % t_str
	return "%s · Day" % t_str


func is_building_locked(building_id: String) -> bool:
	if building_id in ALWAYS_OPEN:
		return false
	if building_id in NAILED_SHUT:
		return true
	return is_night()


func get_ambient_color() -> Color:
	var h := current_minute / 60.0
	if h < 4.5:
		return Color(0.42, 0.44, 0.58, 1.0) # Night
	elif h < 6.0:
		var t := (h - 4.5) / 1.5
		return Color(0.42, 0.44, 0.58, 1.0).lerp(Color(0.88, 0.82, 0.78, 1.0), t) # Dawn
	elif h < 8.0:
		var t := (h - 6.0) / 2.0
		return Color(0.88, 0.82, 0.78, 1.0).lerp(Color(1.0, 1.0, 1.0, 1.0), t) # Morning
	elif h < 18.0:
		return Color(1.0, 1.0, 1.0, 1.0) # Daylight
	elif h < 20.5:
		var t := (h - 18.0) / 2.5
		return Color(1.0, 1.0, 1.0, 1.0).lerp(Color(0.94, 0.76, 0.64, 1.0), t) # Sunset
	elif h < 22.0:
		var t := (h - 20.5) / 1.5
		return Color(0.94, 0.76, 0.64, 1.0).lerp(Color(0.52, 0.48, 0.62, 1.0), t) # Dusk
	else:
		var t := (h - 22.0) / 2.0
		return Color(0.52, 0.48, 0.62, 1.0).lerp(Color(0.42, 0.44, 0.58, 1.0), t) # Night
