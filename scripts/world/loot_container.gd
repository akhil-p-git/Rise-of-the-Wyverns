class_name LootContainer
extends Interactable
## Persistent lootable chest, cupboard, dresser, or sack.

@export var container_id := ""
@export var container_name := "Chest"
@export var loot: Dictionary = {"coin": 5}


func _ready() -> void:
	_update_prompt()


func is_looted() -> bool:
	return Game.state.has_flag("looted_" + container_id) if Game and Game.state else false


func _update_prompt() -> void:
	if is_looted():
		prompt = ""
	else:
		prompt = "Search " + container_name


func interact(_player: Player) -> void:
	if is_looted():
		interacted.emit("The %s is empty." % container_name.to_lower())
		return

	var gained_lines: Array[String] = []
	for item_id: String in loot:
		var qty := int(loot[item_id])
		if qty > 0 and Game and Game.state:
			Game.state.give(item_id, qty)
			var iname := Game.state.item_name(item_id)
			if iname.is_empty():
				iname = item_id.capitalize()
			gained_lines.append("%d %s" % [qty, iname] if qty > 1 else iname)

	if Game and Game.state:
		Game.state.set_flag("looted_" + container_id)

	Audio.play_sfx("pickup")
	_update_prompt()

	var msg := "Found %s in the %s." % [", ".join(gained_lines), container_name.to_lower()]
	interacted.emit(msg)
