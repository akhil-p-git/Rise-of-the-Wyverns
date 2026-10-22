extends Node2D
## Opening cutscene: the prison ship runs onto the reef in a storm, then hands off to the beach.
## Space, Enter or Escape skips it, after a short grace period so a focusing click or a held key cannot.

const BEACH_SCENE := "res://scenes/world/beach.tscn"
const SHIP_START := Vector2(-70.0, 60.0)
const SHIP_IMPACT := Vector2(200.0, 84.0)
const SAIL_SECONDS := 6.5
const SKIP_GRACE_SECONDS := 1.5

var _finished := false
var _age := 0.0

@onready var _camera: Camera2D = $Camera2D
@onready var _ship: Node2D = $Ship
@onready var _broken: Sprite2D = $Wreckage/Broken
@onready var _debris: CPUParticles2D = $Wreckage/Debris
@onready var _flash: ColorRect = $Overlay/Flash
@onready var _fade: ColorRect = $Overlay/Fade
@onready var _caption: Label = $Overlay/Caption


func _ready() -> void:
	_ship.position = SHIP_START
	_play()


func _process(delta: float) -> void:
	_age += delta


func _unhandled_input(event: InputEvent) -> void:
	if _age >= SKIP_GRACE_SECONDS and (event.is_action_pressed("ui_accept") or event.is_action_pressed("ui_cancel")):
		skip()


func skip() -> void:
	if _finished:
		return
	_finished = true
	var beach: Node = load(BEACH_SCENE).instantiate()
	beach.play_arrival = true
	var tree := get_tree()
	tree.root.add_child(beach)
	tree.current_scene = beach
	queue_free()


func _play() -> void:
	create_tween().tween_property(_fade, "color:a", 0.0, 1.0)

	var sway := create_tween().set_loops()
	sway.tween_property(_ship, "rotation", 0.05, 1.1).set_trans(Tween.TRANS_SINE)
	sway.tween_property(_ship, "rotation", -0.05, 1.1).set_trans(Tween.TRANS_SINE)

	_lightning(2.5)
	_lightning(5.2)

	var sail := create_tween()
	sail.tween_property(_ship, "position", SHIP_IMPACT, SAIL_SECONDS).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	await sail.finished
	sway.kill()
	_impact()

	await _wait(3.2)
	_caption.modulate.a = 0.0
	create_tween().tween_property(_caption, "modulate:a", 1.0, 1.2)
	await _wait(3.0)
	var out := create_tween()
	out.tween_property(_fade, "color:a", 1.0, 1.2)
	await out.finished
	skip()


func _impact() -> void:
	_ship.hide()
	_broken.global_position = _ship.global_position
	_broken.rotation = _ship.rotation
	$Wreckage.show()
	_debris.global_position = _ship.global_position
	_debris.restart()
	_shake(5.0, 0.7)
	_flash.color.a = 0.9
	create_tween().tween_property(_flash, "color:a", 0.0, 0.5)

	var sink := create_tween().set_parallel()
	sink.tween_property(_broken, "position", _broken.position + Vector2(-8.0, 10.0), 3.0).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	sink.tween_property(_broken, "rotation", _broken.rotation - 0.12, 3.0)
	sink.tween_property($Wreckage, "modulate:a", 0.0, 2.2).set_delay(1.4)


func _lightning(delay: float) -> void:
	var bolt := create_tween()
	bolt.tween_interval(delay)
	bolt.tween_property(_flash, "color:a", 0.55, 0.05)
	bolt.tween_property(_flash, "color:a", 0.0, 0.12)
	bolt.tween_property(_flash, "color:a", 0.35, 0.04)
	bolt.tween_property(_flash, "color:a", 0.0, 0.4)


func _shake(strength: float, seconds: float) -> void:
	var shake := create_tween()
	shake.tween_method(
		func(t: float) -> void: _camera.offset = Vector2(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0)) * strength * (1.0 - t),
		0.0,
		1.0,
		seconds
	)
	shake.tween_callback(func() -> void: _camera.offset = Vector2.ZERO)


func _wait(seconds: float) -> void:
	var timer := create_tween()
	timer.tween_interval(seconds)
	await timer.finished
