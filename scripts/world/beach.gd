extends Node2D
## Starting area: the shipwreck beach. Composition root only; the scene tree owns the layout.

const AREA_SIZE := Vector2i(320, 180)
const ARRIVAL_POSITION := Vector2(125, 68)
const ARRIVAL_SPEED_SCALE := 0.35

## Set by the intro: fade in from black and stagger ashore instead of starting at full speed.
var play_arrival := false


func _ready() -> void:
	var player: Player = $Entities/Player
	player.surface_resolver = _surface_at
	Audio.play_music("mus_beach")
	Audio.play_ambience(["amb_waves", "amb_wind", "amb_gulls"])
	var camera: Camera2D = player.get_node("Camera2D")
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = AREA_SIZE.x
	camera.limit_bottom = AREA_SIZE.y
	$Hud.bind(player)
	for interactable in $Interactables.get_children():
		if interactable is Interactable:
			interactable.interacted.connect($Hud.show_message)
	var spawn := Game.take_spawn()
	if not spawn.is_empty():
		var marker := get_node_or_null("Spawns/" + spawn) as Marker2D
		if marker:
			player.global_position = marker.global_position
	if Game.state.has_flag("saw_grave"):
		$Decals/WyvernSkeleton.hide()
		$Interactables/SkeletonSign.message = (
			"Deep furrows in the wet sand leading toward the cliffs. The wyvern bones are gone."
		)
	if play_arrival:
		_arrive()


func _arrive() -> void:
	var player: Player = $Entities/Player
	player.global_position = ARRIVAL_POSITION
	player.speed_scale = ARRIVAL_SPEED_SCALE
	var fade: ColorRect = $Overlay/Fade
	fade.color.a = 1.0
	create_tween().tween_property(fade, "color:a", 0.0, 2.5)
	create_tween().tween_property(player, "speed_scale", 1.0, 4.0).set_delay(1.0)
	$Hud.show_message("Cold water. Salt. You are alive, and the rest of the ship is not.")


func _surface_at(pos: Vector2) -> String:
	if pos.x < 92.0 and pos.y < 110.0:
		return "step_planks"
	if pos.y < 86.0:
		return "step_wet_sand"
	if pos.y > 130.0 and pos.x >= 132.0 and pos.x <= 168.0:
		return "step_gravel"
	return "step_sand"
