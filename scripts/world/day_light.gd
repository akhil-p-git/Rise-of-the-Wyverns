class_name DayLight
extends Sprite2D
## Additive window light on an interior floor that fades with the day: full at noon, gone at night.

@export var strength := 0.5


func _ready() -> void:
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	material = mat
	_update()


func _process(_delta: float) -> void:
	_update()


func _update() -> void:
	modulate.a = strength * (1.0 - TimeSystem.get_night_factor())
