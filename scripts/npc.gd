class_name Npc
extends Interactable
## A villager the player can talk to. Supports three behaviours (`stationary`, `wander`, `pace`),
## subtle grim-toned standing fidgets, obstacle/radius avoidance, and pausing during dialogue.

signal dialogue_requested(npc: Npc)

const WALK_SPEED := 30.0
const WALK_FRAME_TIME := 0.18
const STEP_BOB := 0.0

@export var display_name := ""
@export_file("*.json") var dialogue_path := ""
@export var sprite_sheet: Texture2D
## Row of the sprite sheet to show: 0 down, 1 up, 2 left, 3 right.
@export_range(0, 3) var facing_row := 0
@export_enum("stationary", "wander", "pace") var behaviour := "stationary"
@export var wander_radius := 24.0
@export var waypoints: PackedVector2Array = []

var home_position := Vector2.ZERO
var interacting := false
var rng := RandomNumberGenerator.new()

var _moving := false
var _target := Vector2.ZERO
var _wait_timer := 2.0
var _fidget_timer := 2.5
var _walk_time := 0.0
var _wp_index := 0
var _wp_dir := 1
var _rest_offset_y := -64.0
var _base_scale := Vector2(0.25, 0.25)
var _query := PhysicsShapeQueryParameters2D.new()

@onready var _sprite: Sprite2D = $Sprite2D
@onready var _body: StaticBody2D = $Body
@onready var _body_shape: CollisionShape2D = $Body/Shape


func _ready() -> void:
	prompt = "Talk"
	home_position = global_position
	_base_scale = _sprite.scale
	if rng.seed == 0:
		rng.seed = hash(name) ^ int(home_position.x * 31.0 + home_position.y * 97.0)
	if sprite_sheet != null:
		_sprite.texture = sprite_sheet
	if _sprite.texture != null:
		var cell_h := float(_sprite.texture.get_height()) / float(maxi(1, _sprite.vframes))
		_rest_offset_y = -cell_h / 2.0
		_sprite.offset = Vector2(0.0, _rest_offset_y)
	_sprite.frame_coords = Vector2i(0, facing_row)

	_query.shape = _body_shape.shape
	_query.collision_mask = 1
	_query.collide_with_bodies = true
	_query.collide_with_areas = false
	_query.exclude = [_body.get_rid(), get_rid()]

	_wait_timer = rng.randf_range(0.8, 2.4)
	_fidget_timer = rng.randf_range(1.8, 3.8)


func set_seed(seed_val: int) -> void:
	rng = RandomNumberGenerator.new()
	rng.seed = seed_val
	_wait_timer = rng.randf_range(0.4, 1.2)
	_fidget_timer = rng.randf_range(1.5, 3.0)


func interact(player: Player) -> void:
	interacting = true
	_stop_movement()
	face(player.global_position)
	dialogue_requested.emit(self)


func end_interaction() -> void:
	interacting = false
	_wait_timer = rng.randf_range(1.5, 3.0)


func face(point: Vector2) -> void:
	var d := point - global_position
	if d.length_squared() < 0.001:
		return
	if absf(d.x) > absf(d.y):
		facing_row = 2 if d.x < 0.0 else 3
	else:
		facing_row = 1 if d.y < 0.0 else 0
	if _sprite:
		_sprite.frame_coords = Vector2i(0, facing_row)


func _physics_process(delta: float) -> void:
	if interacting or get_tree().paused or Game.is_changing_scene():
		return

	if _moving:
		_step_move(delta)
	else:
		_tick_idle(delta)


func _tick_idle(delta: float) -> void:
	_fidget_timer -= delta
	if _fidget_timer <= 0.0:
		_do_fidget()
		_fidget_timer = rng.randf_range(2.2, 4.5)

	if behaviour == "stationary":
		return

	_wait_timer -= delta
	if _wait_timer > 0.0:
		return

	if behaviour == "wander":
		var angle := rng.randf_range(0.0, TAU)
		var dist := rng.randf_range(6.0, maxf(6.0, wander_radius * 0.92))
		_target = home_position + Vector2.from_angle(angle) * dist
		_moving = true
	elif behaviour == "pace" and waypoints.size() >= 2:
		_target = waypoints[_wp_index]
		_moving = true


func _step_move(delta: float) -> void:
	var to_target := _target - global_position
	var dist := to_target.length()
	if dist <= 1.5:
		if behaviour == "pace" and waypoints.size() >= 2:
			global_position = _target
			if _wp_index + _wp_dir >= waypoints.size() or _wp_index + _wp_dir < 0:
				_wp_dir = -_wp_dir
			_wp_index = clampi(_wp_index + _wp_dir, 0, waypoints.size() - 1)
			_wait_timer = rng.randf_range(0.5, 1.2)
		else:
			_wait_timer = rng.randf_range(1.5, 5.0)
		_stop_movement()
		return

	var dir := to_target / dist
	var step := minf(dist, WALK_SPEED * delta)
	var next_pos := global_position + dir * step

	if behaviour == "wander" and next_pos.distance_to(home_position) > wander_radius:
		_stop_movement()
		_wait_timer = rng.randf_range(1.5, 5.0)
		return

	if _is_blocked(next_pos):
		_stop_movement()
		_wait_timer = rng.randf_range(1.5, 3.5)
		return

	face(next_pos)
	global_position = next_pos
	_walk_time += delta
	var col := int(_walk_time / WALK_FRAME_TIME) % 4
	_sprite.frame_coords = Vector2i(col, facing_row)
	_sprite.offset.y = _rest_offset_y - (STEP_BOB if col % 2 == 1 else 0.0)


func _is_blocked(pos: Vector2) -> bool:
	_query.transform = Transform2D(0.0, pos + _body_shape.position)
	var space := get_world_2d().direct_space_state
	return not space.intersect_shape(_query, 1).is_empty()


func _stop_movement() -> void:
	_moving = false
	_walk_time = 0.0
	if _sprite:
		_sprite.frame_coords = Vector2i(0, facing_row)
		_sprite.offset.y = _rest_offset_y
		_sprite.rotation = 0.0
		_sprite.scale = _base_scale


func _do_fidget() -> void:
	if _sprite == null:
		return
	var kind := rng.randi_range(0, 2)
	if kind == 0:
		# Subtle head turn / look around via direction frame
		var dirs := [0, 2, 3, 1]
		facing_row = dirs[rng.randi_range(0, dirs.size() - 1)]
		_sprite.frame_coords = Vector2i(0, facing_row)
	elif kind == 1:
		# Subtle weight shift wobble (2 degrees)
		var tw := create_tween()
		tw.tween_property(_sprite, "rotation", 0.035, 0.14)
		tw.tween_property(_sprite, "rotation", -0.025, 0.14)
		tw.tween_property(_sprite, "rotation", 0.0, 0.12)
	else:
		# Subtle breathing / shoulder shift
		var tw := create_tween()
		tw.tween_property(_sprite, "scale", _base_scale * Vector2(1.03, 0.97), 0.15)
		tw.tween_property(_sprite, "scale", _base_scale, 0.18)
