class_name RoomRentalDoor
extends BuildingDoor
## The door to a room at an inn. Entering costs `rent_cost` coin and the room stays the player's for
## `Game.ROOM_RENT_HOURS` game hours; the innkeeper's debt (flag `inn_free`) covers it.

@export var rent_cost := 5


func _ready() -> void:
	super._ready()
	if not Engine.is_editor_hint():
		TimeSystem.hour_passed.connect(func(_hour: int) -> void: _update_state())


func _update_state() -> void:
	super._update_state()
	if is_exit or is_locked():
		return
	if Game.is_room_rented() or Game.state.has_flag("inn_free"):
		prompt = "Enter your room"
	else:
		prompt = "Rent a room (%d coin)" % rent_cost


func interact(player: Player) -> void:
	if not is_exit and not is_locked() and not Game.is_room_rented():
		var state := Game.state
		if not state.has_flag("inn_free"):
			if state.count("coin") < rent_cost:
				interacted.emit("A room costs %d coin. You have %d." % [rent_cost, state.count("coin")])
				return
			state.take("coin", rent_cost)
		Game.rent_room()
		interacted.emit("You pay for a room for the night.")
		_update_state()
	super.interact(player)
