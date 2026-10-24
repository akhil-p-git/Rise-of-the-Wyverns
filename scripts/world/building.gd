@tool
class_name Building
extends StaticBody2D
## Building with collision footprint `size` anchored at bottom-centre of the wall so it
## y-sorts by its feet. Draws `texture` when assigned, or falls back to a gray-box rectangle.

@export var texture: Texture2D:
	set(value):
		texture = value
		queue_redraw()
@export var size := Vector2(80, 48):
	set(value):
		size = value
		queue_redraw()
@export var wall_color := Color(0.42, 0.36, 0.3):
	set(value):
		wall_color = value
		queue_redraw()
@export var roof_color := Color(0.25, 0.27, 0.33):
	set(value):
		roof_color = value
		queue_redraw()
@export var door := true:
	set(value):
		door = value
		queue_redraw()
@export var label := "":
	set(value):
		label = value
		queue_redraw()
const GLOW_COLOR := Color(1.0, 0.88, 0.58, 1.0)

@export var chimney_offsets: PackedVector2Array = []
@export var window_offsets: PackedVector2Array = []

var _anim_time := 0.0
var _smoke_sprites: Array[Sprite2D] = []
var _glow_sprites: Array[Sprite2D] = []


func _ready() -> void:
	if Engine.is_editor_hint():
		return
	_setup_atmosphere()


func _setup_atmosphere() -> void:
	if not window_offsets.is_empty() and ResourceLoader.exists("res://assets/buildings/parts/window_glow.png"):
		var glow_tex := load("res://assets/buildings/parts/window_glow.png") as Texture2D
		var add_mat := CanvasItemMaterial.new()
		add_mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		for wpos in window_offsets:
			var g := Sprite2D.new()
			g.texture = glow_tex
			g.position = wpos
			g.scale = Vector2(0.24, 0.24)
			g.material = add_mat
			add_child(g)
			_glow_sprites.append(g)

	if not chimney_offsets.is_empty() and ResourceLoader.exists("res://assets/buildings/parts/chimney_smoke_sheet.png"):
		var smoke_tex := load("res://assets/buildings/parts/chimney_smoke_sheet.png") as Texture2D
		for cpos in chimney_offsets:
			var s := Sprite2D.new()
			s.texture = smoke_tex
			s.hframes = 6
			s.position = cpos
			s.scale = Vector2(0.25, 0.25)
			s.offset = Vector2(0.0, -50.0)
			s.modulate = Color(0.92, 0.94, 0.98, 0.82)
			add_child(s)
			_smoke_sprites.append(s)


func _process(delta: float) -> void:
	if Engine.is_editor_hint() or (_smoke_sprites.is_empty() and _glow_sprites.is_empty()):
		return
	_anim_time += delta
	for i in _smoke_sprites.size():
		var s := _smoke_sprites[i]
		s.frame = int((_anim_time * 5.5) + i * 2.0) % 6
		s.rotation = sin(_anim_time * 1.6 + i) * 0.04
	for i in _glow_sprites.size():
		var g := _glow_sprites[i]
		var flicker := 0.64 + 0.14 * sin(_anim_time * 2.8 + float(i) * 1.3) + 0.05 * cos(_anim_time * 6.5)
		# The CanvasModulate darkens everything at night, so the glow grows and brightens to read as light.
		var night := TimeSystem.get_night_factor()
		g.modulate = GLOW_COLOR * TimeSystem.get_light_compensation()
		g.modulate.a = clampf(flicker * lerpf(0.55, 1.35, night), 0.3, 1.0)
		g.scale = Vector2(0.24, 0.24) * lerpf(1.0, 1.7, night)


func _draw() -> void:
	if texture != null:
		var tw := float(texture.get_width()) * 0.25
		var th := float(texture.get_height()) * 0.25
		draw_texture_rect(texture, Rect2(-tw / 2.0, -th, tw, th), false)
		return
	var left := -size.x / 2.0
	var roof_h := size.y * 0.45
	var wall := Rect2(left, -size.y, size.x, size.y)
	draw_rect(wall, wall_color)
	draw_rect(Rect2(left, -size.y, size.x, roof_h), roof_color)
	draw_rect(Rect2(left - 2, -size.y - 3, size.x + 4, 4), roof_color.darkened(0.3))
	if door:
		draw_rect(Rect2(-5, -14, 10, 14), wall_color.darkened(0.55))
	draw_rect(wall, Color(0.05, 0.04, 0.07), false, 1.0)
	if not label.is_empty():
		var font := ThemeDB.fallback_font
		draw_string(
			font, Vector2(left, -size.y - 8), label, HORIZONTAL_ALIGNMENT_CENTER, size.x, 8, Color(0.96, 0.94, 0.88)
		)
