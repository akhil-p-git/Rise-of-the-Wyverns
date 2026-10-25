class_name AnimatedProp
extends StaticBody2D
## Solid world prop with an animated sprite sheet (e.g. town fireplace) and optional
## pulsing additive light halo.

const GLOW_COLOR := Color(1.0, 0.85, 0.55, 1.0)

@export var fps := 8.0
@export var glow_texture: Texture2D
@export var glow_scale := Vector2(0.45, 0.36)
@export var glow_offset := Vector2(0.0, -8.0)

var _time := 0.0
var _sprite: Sprite2D
var _glow: Sprite2D
var _area: AreaScene


func _ready() -> void:
	_area = AreaScene.of(self)
	_sprite = get_node_or_null("Sprite2D") as Sprite2D
	if glow_texture != null:
		_glow = Sprite2D.new()
		_glow.name = "Glow"
		_glow.texture = glow_texture
		_glow.position = glow_offset
		_glow.scale = glow_scale
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		_glow.material = mat
		add_child(_glow)


func _process(delta: float) -> void:
	_time += delta
	if _sprite != null and _sprite.hframes > 1:
		var total := maxi(1, _sprite.hframes * _sprite.vframes)
		_sprite.frame = int(_time * fps) % total
	if _glow != null and _area != null:
		var pulse := 0.62 + 0.14 * sin(_time * 5.2) + 0.06 * cos(_time * 11.7)
		# Night darkens the scene (CanvasModulate), so the halo widens and brightens to light the ground.
		var night := TimeSystem.get_night_factor()
		_glow.modulate = GLOW_COLOR * _area.light_compensation()
		_glow.modulate.a = clampf(pulse * lerpf(0.8, 1.4, night), 0.42, 1.0)
		_glow.scale = glow_scale * (0.97 + 0.05 * sin(_time * 4.3)) * lerpf(1.0, 1.9, night)
