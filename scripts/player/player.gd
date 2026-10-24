class_name Player
extends CharacterBody2D
## Top-down player: 8-direction walk, stamina-limited sprint, unarmed combat (normal punch on LMB,
## stamina-consuming power attack on hold LMB, 2-hands-up high guard block on RMB), and interaction.

signal prompt_changed(text: String)
signal attacked(is_power: bool)

const WALK_SPEED := 80.0
const SPRINT_SPEED := 130.0
const ACCELERATION := 700.0
const FRICTION := 900.0
const SPRINT_STAMINA_PER_SEC := 25.0
const WALK_FRAME_TIME := 0.14
const STEP_BOB := 0.0
const MOVING_SPEED := 5.0
const INTERACT_REACH := 14.0

const POWER_ATTACK_HOLD := 0.28
const POWER_ATTACK_AUTO_RELEASE := 0.55
const POWER_ATTACK_STAMINA := 20.0
const NORMAL_ATTACK_DURATION := 0.20
const POWER_ATTACK_DURATION := 0.32
const BLOCK_SPEED_SCALE := 0.45

## Shared with the `Game` autoload so health, stamina and mana carry between scenes.
var stats: Stats = Game.stats
## False while a conversation is open: no walking, no interacting.
var input_enabled := true
var facing := Vector2.DOWN:
	set(value):
		facing = value
		if _interact_area:
			_interact_area.position = facing * INTERACT_REACH
## Scales walk and sprint speed; the arrival scene lowers it so the survivor staggers ashore.
var speed_scale := 1.0
var surface_resolver: Callable

var is_blocking := false
var is_attacking := false
var last_attack_was_power := false

var _charging_attack := false
var _attack_hold_time := 0.0
var _attack_timer := 0.0
var _walk_time := 0.0
var _prev_step_col := 0
var _prompt := ""

var _walk_tex: Texture2D
var _punch_tex: Texture2D
var _block_tex: Texture2D

@onready var _sprite: Sprite2D = $Sprite2D
@onready var _sprite_rest_y := _sprite.offset.y
@onready var _interact_area: Area2D = $InteractArea


func _ready() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	add_to_group("player")
	_walk_tex = _sprite.texture
	if ResourceLoader.exists("res://assets/hero/hero_punch_sheet.png"):
		_punch_tex = load("res://assets/hero/hero_punch_sheet.png") as Texture2D
	if ResourceLoader.exists("res://assets/hero/hero_block_sheet.png"):
		_block_tex = load("res://assets/hero/hero_block_sheet.png") as Texture2D
	if _sprite.texture and _sprite.texture.resource_path == "res://assets/hero/hero_sheet.png" and Game.character:
		_sprite.material = Game.character.make_material()


func perform_normal_attack() -> void:
	is_blocking = false
	_charging_attack = false
	_attack_hold_time = 0.0
	is_attacking = true
	last_attack_was_power = false
	_attack_timer = NORMAL_ATTACK_DURATION
	velocity = facing * 32.0
	Audio.play_sfx("step_gravel", global_position, 1.35)
	_update_combat_sprite()
	attacked.emit(false)


func perform_power_attack() -> bool:
	if not stats.use_stamina(POWER_ATTACK_STAMINA):
		perform_normal_attack()
		return false
	is_blocking = false
	_charging_attack = false
	_attack_hold_time = 0.0
	is_attacking = true
	last_attack_was_power = true
	_attack_timer = POWER_ATTACK_DURATION
	velocity = facing * 95.0
	Audio.play_sfx("rest_fire", global_position, 1.25)
	_update_combat_sprite()
	attacked.emit(true)
	return true


func _physics_process(delta: float) -> void:
	var input := Vector2.ZERO
	if input_enabled:
		input = Input.get_vector("move_left", "move_right", "move_up", "move_down")

	# Update combat state machine (attack / power attack / 2-hands-up block)
	if is_attacking:
		_attack_timer -= delta
		if _attack_timer <= 0.0:
			is_attacking = false
	elif input_enabled:
		var want_block := Input.is_action_pressed("block")
		var want_attack := Input.is_action_pressed("attack")
		if want_block:
			_charging_attack = false
			_attack_hold_time = 0.0
			is_blocking = true
		else:
			is_blocking = false
			if want_attack:
				_charging_attack = true
				_attack_hold_time += delta
				if _attack_hold_time >= POWER_ATTACK_AUTO_RELEASE:
					perform_power_attack()
			elif _charging_attack:
				if _attack_hold_time >= POWER_ATTACK_HOLD:
					perform_power_attack()
				else:
					perform_normal_attack()
	else:
		is_blocking = false
		_charging_attack = false
		_attack_hold_time = 0.0

	var sprinting := (
		Input.is_action_pressed("sprint")
		and input != Vector2.ZERO
		and not is_blocking
		and not is_attacking
		and not _charging_attack
		and stats.use_stamina(SPRINT_STAMINA_PER_SEC * delta)
	)
	var move_mult := speed_scale
	if is_blocking or _charging_attack:
		move_mult *= BLOCK_SPEED_SCALE
	elif is_attacking:
		move_mult *= 0.25

	var target := input * (SPRINT_SPEED if sprinting else WALK_SPEED) * move_mult
	velocity = velocity.move_toward(target, (ACCELERATION if input != Vector2.ZERO else FRICTION) * delta)
	move_and_slide()
	stats.tick(delta)

	if input != Vector2.ZERO and not is_attacking:
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


func _update_combat_sprite() -> void:
	var row := _facing_row()
	if is_attacking and _punch_tex != null:
		_sprite.texture = _punch_tex
		var col := 3 if last_attack_was_power else 1
		if not last_attack_was_power and _attack_timer > NORMAL_ATTACK_DURATION * 0.65:
			col = 0
		_sprite.frame_coords = Vector2i(col, row)
		_sprite.offset.y = _sprite_rest_y
	elif _charging_attack and _attack_hold_time >= 0.08 and _punch_tex != null:
		_sprite.texture = _punch_tex
		_sprite.frame_coords = Vector2i(2, row)
		_sprite.offset.y = _sprite_rest_y
	elif is_blocking and _block_tex != null:
		_sprite.texture = _block_tex
		var bcol := int(_walk_time / (WALK_FRAME_TIME * 1.4)) % 4
		_sprite.frame_coords = Vector2i(bcol, row)
		_sprite.offset.y = _sprite_rest_y


func _animate(delta: float) -> void:
	if is_attacking or (_charging_attack and _attack_hold_time >= 0.08) or is_blocking:
		if is_blocking and velocity.length() >= MOVING_SPEED:
			_walk_time += delta * velocity.length() / WALK_SPEED
		_update_combat_sprite()
		return

	if _walk_tex != null and _sprite.texture != _walk_tex:
		_sprite.texture = _walk_tex

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
