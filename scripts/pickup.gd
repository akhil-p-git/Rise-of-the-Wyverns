class_name Pickup
extends Interactable
## Something to take or use once: an item on the ground, a hole to block, a grave to examine.
## It remembers being used, so it stays gone when the scene is reloaded.

## Item given on use (may be empty when the point is the flag or the message).
@export var item := ""
@export var count := 1
@export var sets_flag := ""
## Conditions that must hold before it can be used (see GameState).
@export var requires: PackedStringArray = []
@export_multiline var locked_message := ""

var _key := ""


func _ready() -> void:
	_key = "taken:" + String(get_path())
	if Game.state.has_flag(_key):
		queue_free()


func interact(_player: Player) -> void:
	var state := Game.state
	if not state.check(Array(requires)):
		interacted.emit(locked_message)
		return
	if not item.is_empty():
		state.give(item, count)
	if not sets_flag.is_empty():
		state.set_flag(sets_flag)
	state.set_flag(_key)
	interacted.emit(message)
	queue_free()
