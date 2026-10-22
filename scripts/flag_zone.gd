class_name FlagZone
extends Area2D
## Sets a story flag the first time the player walks in, and shows a message.

@export var flag := ""
@export_multiline var message := ""

signal triggered(message: String)


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if body is Player and not Game.state.has_flag(flag):
		Game.state.set_flag(flag)
		triggered.emit(message)
