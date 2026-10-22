class_name Player
extends CharacterBody2D
## Top-down player: 8-direction walk, stamina-limited sprint, and interaction with the nearest Interactable.

signal prompt_changed(text: String)

const WALK_SPEED := 80.0
const SPRINT_SPEED := 130.0
const ACCELERATION := 700.0
const FRICTION := 900.0
const SPRINT_STAMINA_PER_SEC := 25.0
const WALK_FRAME_TIME := 0.14
const STEP_BOB := 1.0
const MOVING_SPEED := 5.0
const INTERACT_REACH := 14.0

## Shared with the `Game` autoload so health, stamina and mana carry between scenes.
var stats: Stats = Game.stats
## False while a conversation is open: no walking, no interacting.
var input_enabled := true
var facing := Vector2.DOWN
## Scales walk and sprint speed; the arrival scene lowers it so the survivor staggers ashore.
var speed_scale := 1.0
var surface_resolver: Callable

var _walk_time := 0.0
var _prev_step_col := 0
var _prompt := ""

@onready var _sprite: Sprite2D = $Sprite2D
@onready var _sprite_rest_y := _sprite.offset.y
@onready var _interact_area: Area2D = $InteractArea


func _ready() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	add_to_group("player")
	if _sprite.texture and _sprite.texture.resource_path == "res://assets/hero/hero_sheet.png" and Game.character:
		_sprite.material = Game.character.make_material()


func _physics_process(delta: float) -> void:
	var input := Vector2.ZERO
	if input_enabled:
		input = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var sprinting := (
		Input.is_action_pressed("sprint")
		and input != Vector2.ZERO
		and stats.use_stamina(SPRINT_STAMINA_PER_SEC * delta)
	)
	var target := input * (SPRINT_SPEED if sprinting else WALK_SPEED) * speed_scale
	velocity = velocity.move_toward(target, (ACCELERATION if input != Vector2.ZERO else FRICTION) * delta)
	move_and_slide()
	stats.tick(delta)

	if input != Vector2.ZERO:
		facing = input.normalized()
		_interact_area.position = facing * INTERACT_REACH
	_animate(delta)
	_update_prompt()


func _unhandled_input(event: InputEvent) -> void:
	if input_enabled and event.is_action_pressed("interact"):
		var target := _nearest_interactable()
		if target:
			get_viewport().set_input_as_handled()
			target.interact(self)


func _nearest_interactable() -> Interactable:
	var best: Interactable = null
	var best_dist := INF
	for area in _interact_area.get_overlapping_areas():
		if area is Interactable:
			var d := global_position.distance_squared_to(area.global_position)
			if d < best_dist:
				best = area
				best_dist = d
	return best


func _update_prompt() -> void:
	var target := _nearest_interactable()
	var text := "" if target == null else target.prompt
	if text != _prompt:
		_prompt = text
		prompt_changed.emit(text)


func _animate(delta: float) -> void:
	var row := _facing_row()
	var speed := velocity.length()
	if speed < MOVING_SPEED:
		_walk_time = 0.0
		_prev_step_col = 0
		_sprite.frame_coords = Vector2i(0, row)
		_sprite.offset.y = _sprite_rest_y
		return
	# Stride cadence follows actual speed, so ramping up and stopping both look natural.
	_walk_time += delta * speed / WALK_SPEED
	var column := int(_walk_time / WALK_FRAME_TIME) % 4
	if column % 2 == 1 and column != _prev_step_col:
		var cue: String = surface_resolver.call(global_position) if surface_resolver.is_valid() else "step_gravel"
		Audio.play_sfx(cue, global_position, randf_range(0.92, 1.08))
	_prev_step_col = column
	# hero_sheet.png rows: down, up, left, right. Columns: idle, stride, idle, stride.
	_sprite.frame_coords = Vector2i(column, row)
	_sprite.offset.y = _sprite_rest_y - (STEP_BOB if column % 2 == 1 else 0.0)


func _facing_row() -> int:
	if absf(facing.x) > absf(facing.y):
		return 2 if facing.x < 0.0 else 3
	return 1 if facing.y < 0.0 else 0
