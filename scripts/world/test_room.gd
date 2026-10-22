extends Node2D
## Gray-box room for Milestone 1: placeholder map, colliders, one sign, the player and the HUD.

const ROOM_SIZE := Vector2i(640, 360)


func _ready() -> void:
	var camera: Camera2D = $Player/Camera2D
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = ROOM_SIZE.x
	camera.limit_bottom = ROOM_SIZE.y
	$Hud.bind($Player)
	$Sign.interacted.connect($Hud.show_message)
