class_name Npc
extends Interactable
## A villager the player can talk to. Supports four behaviours (`stationary`, `wander`, `pace`, and `play` for
## kids who run about and chase each other), subtle grim-toned standing fidgets, obstacle/radius avoidance,
## pausing during dialogue, and a daily schedule (`npc_id` in `data/schedules.json`): the NPC walks to the door
## and leaves when its slot sends it elsewhere, and walks in from the door when its slot brings it here.

signal dialogue_requested(npc: Npc)

const WALK_SPEED := 30.0
const WALK_FRAME_TIME := 0.18
const STEP_BOB := 0.0
const RUN_SPEED := 62.0
const RUN_FRAME_TIME := 0.1
const TRAVEL_SPEED := 42.0
## A door sits flush against its wall, so a leaving NPC counts as arrived when this close.
const TRAVEL_ARRIVE_DISTANCE := 8.0
## Travel gives up and snaps to the target after this multiple of the straight-line walking time (plus a floor).
const TRAVEL_PATIENCE := 2.5
const TRAVEL_MIN_SECONDS := 3.0
## Directions tried, in order, when the straight line to a travel target is blocked.
const TRAVEL_DETOURS := [0.0, 0.7854, -0.7854, 1.5708, -1.5708]

@export var display_name := ""
@export_file("*.json") var dialogue_path := ""
@export var sprite_sheet: Texture2D
## Row of the sprite sheet to show: 0 down, 1 up, 2 left, 3 right.
@export_range(0, 3) var facing_row := 0
## Key into `data/schedules.json`; empty means the NPC is always where its scene put it.
@export var npc_id := ""
@export_enum("stationary", "wander", "pace", "play") var behaviour := "stationary"
@export var wander_radius := 24.0
@export var waypoints: PackedVector2Array = []

var home_position := Vector2.ZERO
var interacting := false
## False while the NPC is elsewhere on its schedule: hidden, not collidable, not talkable.
var present := true
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
var _area: AreaScene
var _travelling := false
var _travel_target := Vector2.ZERO
var _travel_leaving := false
var _travel_time := 0.0
var _travel_limit := 0.0

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

	if behaviour == "play":
		add_to_group("kids")
	_area = AreaScene.of(self)
	if not npc_id.is_empty() and _area != null:
		TimeSystem.hour_passed.connect(_on_hour_passed)
		if not _scheduled_here(TimeSystem.get_hour()):
			_set_present(false)


func set_seed(seed_val: int) -> void:
	rng = RandomNumberGenerator.new()
	rng.seed = seed_val
	_wait_timer = rng.randf_range(0.4, 1.2)
	_fidget_timer = rng.randf_range(1.5, 3.0)


func _scheduled_here(hour: int) -> bool:
	var place := NpcSchedule.place_at(npc_id, hour)
	return place.is_empty() or place == _area.place_id


func _on_hour_passed(hour: int) -> void:
	var here := _scheduled_here(hour)
	if here and not present:
		_arrive(NpcSchedule.place_at(npc_id, posmod(hour - 1, 24)))
	elif not here and present:
		_depart(NpcSchedule.place_at(npc_id, hour))


func _arrive(from_place: String) -> void:
	global_position = _door_position(from_place) + Vector2(0.0, -8.0)
	_set_present(true)
	_begin_travel(home_position, false)


func _depart(to_place: String) -> void:
	_begin_travel(_door_position(to_place), true)


## Where people go in and out for `building_id`: its door in town, or this interior's own exit.
func _door_position(building_id: String) -> Vector2:
	for node in _area.get_node("Interactables").get_children():
		if node is BuildingDoor and (node.is_exit or node.building_id == building_id):
			return node.global_position
	return home_position


func _begin_travel(target: Vector2, leaving: bool) -> void:
	_stop_movement()
	_travelling = true
	_travel_target = target
	_travel_leaving = leaving
	_travel_time = 0.0
	_travel_limit = global_position.distance_to(target) / TRAVEL_SPEED * TRAVEL_PATIENCE + TRAVEL_MIN_SECONDS


func _set_present(value: bool) -> void:
	present = value
	visible = value
	collision_layer = 2 if value else 0
	_body_shape.set_deferred("disabled", not value)
	if not value:
		_travelling = false
		_stop_movement()


func _step_travel(delta: float) -> void:
	_travel_time += delta
	var to_target := _travel_target - global_position
	var arrive := TRAVEL_ARRIVE_DISTANCE if _travel_leaving else 2.0
	if to_target.length() <= arrive or _travel_time >= _travel_limit:
		global_position = _travel_target
		_finish_travel()
		return
	var dir := to_target.normalized()
	for detour: float in TRAVEL_DETOURS:
		var step_dir: Vector2 = dir.rotated(detour)
		var next_pos := global_position + step_dir * minf(to_target.length(), TRAVEL_SPEED * delta)
		if not _is_blocked(next_pos):
			face(next_pos)
			global_position = next_pos
			_animate_walk(delta, WALK_FRAME_TIME)
			return


func _finish_travel() -> void:
	_travelling = false
	if _travel_leaving:
		_set_present(false)
	else:
		_stop_movement()
		_wait_timer = rng.randf_range(0.5, 1.5)


func _animate_walk(delta: float, frame_time: float) -> void:
	_walk_time += delta
	var col := int(_walk_time / frame_time) % 4
	_sprite.frame_coords = Vector2i(col, facing_row)
	_sprite.offset.y = _rest_offset_y - (STEP_BOB if col % 2 == 1 else 0.0)


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
	if not present or interacting or get_tree().paused or Game.is_changing_scene():
		return

	if _travelling:
		_step_travel(delta)
	elif _moving:
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
	elif behaviour == "play":
		_target = _pick_play_target()
		_moving = true


## Kids run to a random spot nearby, or run at another kid half as often to play tag.
func _pick_play_target() -> Vector2:
	var buddies := get_tree().get_nodes_in_group("kids").filter(
		func(n: Node) -> bool: return n != self and n is Npc and n.present and n.get_parent() == get_parent()
	)
	var spot: Vector2
	if not buddies.is_empty() and rng.randf() < 0.5:
		var buddy: Npc = buddies[rng.randi_range(0, buddies.size() - 1)]
		spot = buddy.global_position + Vector2.from_angle(rng.randf_range(0.0, TAU)) * 8.0
	else:
		spot = home_position + Vector2.from_angle(rng.randf_range(0.0, TAU)) * rng.randf_range(8.0, wander_radius)
	var offset := spot - home_position
	if offset.length() > wander_radius:
		spot = home_position + offset.normalized() * wander_radius
	return spot


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
		elif behaviour == "play":
			_wait_timer = rng.randf_range(0.2, 1.3)
		else:
			_wait_timer = rng.randf_range(1.5, 5.0)
		_stop_movement()
		return

	var playing := behaviour == "play"
	var dir := to_target / dist
	var step := minf(dist, (RUN_SPEED if playing else WALK_SPEED) * delta)
	var next_pos := global_position + dir * step

	if behaviour == "wander" and next_pos.distance_to(home_position) > wander_radius:
		_stop_movement()
		_wait_timer = rng.randf_range(1.5, 5.0)
		return

	if _is_blocked(next_pos):
		_stop_movement()
		_wait_timer = rng.randf_range(0.1, 0.4) if playing else rng.randf_range(1.5, 3.5)
		return

	face(next_pos)
	global_position = next_pos
	_animate_walk(delta, RUN_FRAME_TIME if playing else WALK_FRAME_TIME)


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
