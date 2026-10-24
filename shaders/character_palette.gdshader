shader_type canvas_item;

// Palette-swap shader for assets/hero/hero_sheet.png (96x128, 4x4 grid of 24x32 cells).
// Recolours hair, skin, and tunic while preserving dark outlines, eyes, and leather boots.
// The texture and the source_color uniforms arrive linearised, but the thresholds and luma divisors below are tuned on
// sRGB values, so the maths runs in sRGB (decoded here) and the result is written as sRGB. Without this the skin renders
// orange-red and the hair and tunic too dark.
uniform vec4 skin_color : source_color = vec4(0.855, 0.624, 0.490, 1.0);
uniform vec4 hair_color : source_color = vec4(0.290, 0.212, 0.165, 1.0);
uniform vec4 cloth_color : source_color = vec4(0.314, 0.306, 0.294, 1.0);

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	tex.rgb = pow(tex.rgb, vec3(1.0 / 2.2));
	vec3 skin = pow(skin_color.rgb, vec3(1.0 / 2.2));
	vec3 hair = pow(hair_color.rgb, vec3(1.0 / 2.2));
	vec3 cloth = pow(cloth_color.rgb, vec3(1.0 / 2.2));
	if (tex.a < 0.5) {
		COLOR = tex;
	} else {
		float mx = max(max(tex.r, tex.g), tex.b);
		float mn = min(min(tex.r, tex.g), tex.b);
		float chroma = mx - mn;
		float luma = dot(tex.rgb, vec3(0.299, 0.587, 0.114));

		vec2 sheet_px = UV * vec2(96.0, 128.0);
		float cell_x = mod(sheet_px.x, 24.0);
		float cell_y = mod(sheet_px.y, 32.0);
		int row = int(floor(sheet_px.y / 32.0));

		// Preserve dark outlines and eye box
		bool in_eye_box = (
			(row == 0 && cell_y >= 8.5 && cell_y <= 11.6 && cell_x >= 8.5 && cell_x <= 15.5 && (mn > 0.62 || mx < 0.37))
			|| (row == 2 && cell_y >= 8.0 && cell_y <= 11.4 && cell_x >= 6.5 && cell_x <= 11.4 && (mn > 0.62 || mx < 0.37))
			|| (row == 3 && cell_y >= 8.0 && cell_y <= 11.4 && cell_x >= 12.6 && cell_x <= 17.5 && (mn > 0.62 || mx < 0.37))
		);
		bool in_face_lower = (
			(row == 0 && cell_y >= 9.75 && cell_y <= 14.0 && cell_x >= 8.5 && cell_x <= 15.5)
			|| (row == 2 && cell_y >= 9.5 && cell_y <= 14.0 && cell_x <= 12.5)
			|| (row == 3 && cell_y >= 9.5 && cell_y <= 14.0 && cell_x >= 11.5)
		);

		if (mx >= 0.13 && !in_eye_box) {
			bool is_cloth = (cell_y >= 13.5 && cell_y <= 25.5 && chroma < 0.088);
			bool is_skin = (
				!is_cloth
				&& cell_y >= 6.5
				&& cell_y <= 25.0
				&& (
					(tex.r > 0.45 && (tex.r - tex.b) > 0.12)
					|| (in_face_lower && tex.r > 0.33 && (tex.r - tex.b) > 0.08)
				)
				&& !(row == 1 && cell_y < 14.2)
			);
			bool is_hair = (
				!is_cloth
				&& !is_skin
				&& !in_face_lower
				&& (cell_y <= 13.5 || (row == 1 && cell_y <= 14.5))
			);

			if (is_cloth) {
				tex.rgb = clamp(cloth * (luma / 0.28), 0.0, 1.0);
			} else if (is_skin) {
				tex.rgb = clamp(skin * (luma / 0.62), 0.0, 1.0);
			} else if (is_hair) {
				tex.rgb = clamp(hair * (luma / 0.22), 0.0, 1.0);
			}
		}
		COLOR = tex * COLOR;
	}
}
