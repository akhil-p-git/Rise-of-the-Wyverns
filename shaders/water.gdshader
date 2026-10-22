shader_type canvas_item;
// Moves the water in whole art pixels so it keeps the pixel-art look. The mask is 0 on
// land and rises with distance from the shore; open water moves more than the shoreline.

uniform sampler2D water_mask : filter_nearest;
uniform vec2 art_size = vec2(320.0, 180.0);
uniform float swell_pixels : hint_range(0.0, 4.0, 0.1) = 1.6;
uniform float speed : hint_range(0.0, 4.0, 0.1) = 1.0;
uniform float glint_amount : hint_range(0.0, 0.3, 0.01) = 0.06;

void fragment() {
	float m = texture(water_mask, UV).r;
	vec2 p = UV * art_size;
	float t = TIME * speed;
	vec2 wave = vec2(
		sin(p.y * 0.35 + t * 1.3 + sin(p.x * 0.05 + t * 0.4) * 2.0),
		sin(p.x * 0.22 + p.y * 0.12 - t * 0.9)
	);
	// Land samples itself; water moves by at most swell_pixels, snapped to the pixel grid.
	vec2 offset = floor(wave * swell_pixels * m + 0.5) / art_size;
	vec4 col = texture(TEXTURE, UV + offset);
	// Thin glints that drift across open water.
	float glint = step(0.975, sin(p.x * 0.45 + p.y * 0.3 - t * 1.4) * sin(p.y * 0.8 + t * 0.5)) * step(0.35, m);
	COLOR = vec4(col.rgb + glint * glint_amount, col.a);
}
