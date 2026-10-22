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


func _draw() -> void:
	if texture != null:
		var tw := float(texture.get_width())
		var th := float(texture.get_height())
		draw_texture(texture, Vector2(-tw / 2.0, -th))
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
