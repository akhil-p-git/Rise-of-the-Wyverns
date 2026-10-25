class_name BuildingDoor
extends Interactable
## Doorway to enter or exit a building. Handles day/night locking rules.
## Locked after 10 PM (22:00) until 6 AM (06:00), except the Inn (The Salt Gull), which never locks.

@export var building_id := ""
@export var building_name := ""
@export_file("*.tscn") var target_scene := ""
@export var target_spawn := ""
@export var is_exit := false


func _ready() -> void:
	_update_state()
	if Engine.is_editor_hint():
		return
	if TimeSystem:
		TimeSystem.day_phase_changed.connect(func(_is_night: bool) -> void: _update_state())


func _update_state() -> void:
	if is_exit:
		prompt = "Exit to " + building_name
		return
	if is_locked():
		prompt = "Locked"
	else:
		prompt = "Enter " + building_name if not building_name.is_empty() else "Enter"


func is_locked() -> bool:
	if is_exit:
		return false
	if TimeSystem:
		return TimeSystem.is_building_locked(building_id)
	return false


func interact(_player: Player) -> void:
	if is_locked():
		Audio.play_sfx("ui_back")
		var msg := ""
		if "shutter" in building_id.to_lower():
			msg = "The door is nailed shut with rusted iron spikes. No one answers from within."
		else:
			msg = "Barred for the night. Wrackmouth shutters its homes from 10:00 PM until 6:00 AM."
		interacted.emit(msg)
		return

	if not target_scene.is_empty():
		Audio.play_sfx("scene_exit")
		Game.go_to(target_scene, target_spawn)
