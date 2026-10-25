class_name RestSpot
extends Interactable
## A bed. Costs coin unless the innkeeper owes you (a rented room's bed costs nothing); sleeping passes
## the night, refills health, stamina and mana, and leaves the player Well Rested (+10% XP).

const FREE_FLAG := "inn_free"

@export var cost := 0


func interact(_player: Player) -> void:
	var state := Game.state
	var free := state.has_flag(FREE_FLAG) or cost == 0
	if not free and state.count("coin") < cost:
		interacted.emit("A bed costs %d coin. You have %d." % [cost, state.count("coin")])
		return
	if not free:
		state.take("coin", cost)
	Audio.play_sfx("rest_fire", global_position)
	Game.blackout(Game.sleep_in_bed)
	interacted.emit("You sleep without dreaming, which is a mercy. You wake well rested.")
