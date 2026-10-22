shader_type canvas_item;

// Palette-swap shader for assets/hero/hero_sheet.png (96x128, 4x4 grid of 24x32 cells).
// Recolours hair, skin, and tunic while preserving dark outlines, eyes, and leather boots.
uniform vec4 skin_color : source_color = vec4(0.855, 0.624, 0.490, 1.0);
uniform vec4 hair_color : source_color = vec4(0.290, 0.212, 0.165, 1.0);
uniform vec4 cloth_color : source_color = vec4(0.314, 0.306, 0.294, 1.0);

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	if (tex.a < 0.5) {
		COLOR = tex;
	} else {
		float mx = max(max(tex.r, tex.g), tex.b);
		float mn = min(min(tex.r, tex.g), tex.b);
		float chroma = mx - mn;
		float luma = dot(tex.rgb, vec3(0.299, 0.587, 0.114));

		vec2 sheet_px = UV * vec2(96.0, 128.0);
		float cell_y = mod(sheet_px.y, 32.0);
		int row = int(floor(sheet_px.y / 32.0));

		// Preserve dark outlines and eyes (mx < 0.19)
		if (mx >= 0.19) {
			bool is_cloth = (cell_y >= 14.0 && cell_y <= 26.0 && chroma < 0.075);
			bool is_skin = (!is_cloth && cell_y >= 10.0 && cell_y <= 25.0 && tex.r > 0.48 && (tex.r - tex.b) > 0.12 && !(row == 1 && cell_y < 14.0));
			bool is_hair = (!is_cloth && !is_skin && (cell_y < 12.0 || (row == 1 && cell_y < 15.0) || (cell_y < 14.0 && mx < 0.45)));

			if (is_cloth) {
				tex.rgb = clamp(cloth_color.rgb * (luma / 0.28), 0.0, 1.0);
			} else if (is_skin) {
				tex.rgb = clamp(skin_color.rgb * (luma / 0.62), 0.0, 1.0);
			} else if (is_hair) {
				tex.rgb = clamp(hair_color.rgb * (luma / 0.22), 0.0, 1.0);
			}
		}
		COLOR = tex * COLOR;
	}
}
