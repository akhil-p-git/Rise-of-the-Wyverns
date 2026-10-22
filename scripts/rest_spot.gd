class_name RestSpot
extends Interactable
## A bed. Costs coin unless the innkeeper owes you; restores health, stamina and mana.

const FREE_FLAG := "inn_free"

@export var cost := 5


func interact(_player: Player) -> void:
	var state := Game.state
	var free := state.has_flag(FREE_FLAG)
	if not free and state.count("coin") < cost:
		interacted.emit("A bed costs %d coin. You have %d." % [cost, state.count("coin")])
		return
	if not free:
		state.take("coin", cost)
	Game.blackout(_restore)
	interacted.emit("You sleep without dreaming, which is a mercy.")


func _restore() -> void:
	var stats := Game.stats
	stats.health = stats.max_health
	stats.stamina = stats.max_stamina
	stats.mana = stats.max_mana
	for stat: StringName in [&"health", &"stamina", &"mana"]:
		stats.changed.emit(stat)
