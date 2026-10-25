class_name RestSpot
extends Interactable
## A bed. Interacting opens the sleep menu: choose how long to sleep (1 to 24 hours). Any length refills
## health, stamina and mana and leaves the player Well Rested (+10% XP). The bed itself is free; a room
## at an inn is paid for at its door.


func interact(_player: Player) -> void:
	var area := AreaScene.of(self)
	if area != null:
		area.open_sleep_menu()
