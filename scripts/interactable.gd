class_name Interactable
extends Area2D
## Something the player can use with the interact key (signs now; doors, NPCs, containers later).

signal interacted(message: String)

@export var prompt := "Read"
@export_multiline var message := ""


func interact(_player: Player) -> void:
	interacted.emit(message)
