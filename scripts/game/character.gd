class_name Character
extends Resource
## Player character configuration chosen before the intro cutscene:
## appearance palette indices, pronouns, difficulty, and optional Hardcore flag.

const SKIN_TONES := [
	{"name": "Pale Salt", "color": Color(0.91, 0.78, 0.69, 1.0)},
	{"name": "Weathered Fair", "color": Color(0.855, 0.624, 0.490, 1.0)},
	{"name": "Warm Ochre", "color": Color(0.74, 0.52, 0.36, 1.0)},
	{"name": "Sun-Bronzed", "color": Color(0.58, 0.39, 0.27, 1.0)},
	{"name": "Deep Umber", "color": Color(0.40, 0.27, 0.19, 1.0)},
]

const HAIR_COLOURS := [
	{"name": "Dark Umber", "color": Color(0.290, 0.212, 0.165, 1.0)},
	{"name": "Raven Black", "color": Color(0.14, 0.13, 0.16, 1.0)},
	{"name": "Ash Blonde", "color": Color(0.68, 0.59, 0.42, 1.0)},
	{"name": "Rust Auburn", "color": Color(0.54, 0.24, 0.16, 1.0)},
	{"name": "Iron Grey", "color": Color(0.46, 0.47, 0.49, 1.0)},
	{"name": "Bleached Bone", "color": Color(0.82, 0.79, 0.73, 1.0)},
]

const CLOTHING_COLOURS := [
	{"name": "Convict Slate", "color": Color(0.314, 0.306, 0.294, 1.0)},
	{"name": "Salt Marsh Moss", "color": Color(0.24, 0.34, 0.25, 1.0)},
	{"name": "Dried Blood", "color": Color(0.44, 0.17, 0.17, 1.0)},
	{"name": "Deep Indigo", "color": Color(0.21, 0.26, 0.38, 1.0)},
	{"name": "Tarnished Ochre", "color": Color(0.48, 0.38, 0.22, 1.0)},
]

const PRONOUN_SETS := {
	"she/her": {
		"they": "she",
		"them": "her",
		"their": "her",
		"theirs": "hers",
		"themself": "herself",
		"is_are": "is",
		"was_were": "was",
		"has_have": "has",
		"s": "s",
		"es": "es",
	},
	"he/him": {
		"they": "he",
		"them": "him",
		"their": "his",
		"theirs": "his",
		"themself": "himself",
		"is_are": "is",
		"was_were": "was",
		"has_have": "has",
		"s": "s",
		"es": "es",
	},
	"they/them": {
		"they": "they",
		"them": "them",
		"their": "their",
		"theirs": "theirs",
		"themself": "themself",
		"is_are": "are",
		"was_were": "were",
		"has_have": "have",
		"s": "",
		"es": "",
	},
}

const DIFFICULTY_SCALES := {
	"Easy": 0.75,
	"Normal": 1.0,
	"Hard": 1.5,
}

const PALETTE_SHADER := preload("res://shaders/character_palette.gdshader")

@export var skin_index := 1
@export var hair_index := 0
@export var cloth_index := 0
@export var pronouns := "they/them"
@export var difficulty := "Normal"
@export var hardcore := false


func skin_color() -> Color:
	return SKIN_TONES[posmod(skin_index, SKIN_TONES.size())]["color"]


func hair_color() -> Color:
	return HAIR_COLOURS[posmod(hair_index, HAIR_COLOURS.size())]["color"]


func cloth_color() -> Color:
	return CLOTHING_COLOURS[posmod(cloth_index, CLOTHING_COLOURS.size())]["color"]


func skin_name() -> String:
	return SKIN_TONES[posmod(skin_index, SKIN_TONES.size())]["name"]


func hair_name() -> String:
	return HAIR_COLOURS[posmod(hair_index, HAIR_COLOURS.size())]["name"]


func cloth_name() -> String:
	return CLOTHING_COLOURS[posmod(cloth_index, CLOTHING_COLOURS.size())]["name"]


func damage_scale() -> float:
	return float(DIFFICULTY_SCALES.get(difficulty, 1.0))


func apply_to_material(mat: ShaderMaterial) -> void:
	if mat == null:
		return
	if mat.shader == null:
		mat.shader = PALETTE_SHADER
	mat.set_shader_parameter("skin_color", skin_color())
	mat.set_shader_parameter("hair_color", hair_color())
	mat.set_shader_parameter("cloth_color", cloth_color())


func make_material() -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.shader = PALETTE_SHADER
	apply_to_material(mat)
	return mat


func randomize_appearance(rng: RandomNumberGenerator = null) -> void:
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	skin_index = rng.randi_range(0, SKIN_TONES.size() - 1)
	hair_index = rng.randi_range(0, HAIR_COLOURS.size() - 1)
	cloth_index = rng.randi_range(0, CLOTHING_COLOURS.size() - 1)


## Resolves pronoun tokens ({they}, {them}, {their}, {theirs}, {themself}, plus verb
## agreement helpers {is_are}, {was_were}, {has_have}, {s}, {es}) and capitalises them
## when written with an initial capital or placed at the start of a sentence.
func format_text(text: String) -> String:
	if not text.contains("{"):
		return text
	var table: Dictionary = PRONOUN_SETS.get(pronouns, PRONOUN_SETS["they/them"])
	var out := text
	for key: String in table:
		var val: String = table[key]
		var cap_val := val.substr(0, 1).to_upper() + val.substr(1) if not val.is_empty() else ""
		var cap_key := key.substr(0, 1).to_upper() + key.substr(1)
		out = out.replace("{%s}" % cap_key, cap_val)
		var token := "{%s}" % key
		var pos := out.find(token)
		while pos != -1:
			var rep := cap_val if _is_sentence_start(out, pos) else val
			out = out.substr(0, pos) + rep + out.substr(pos + token.length())
			pos = out.find(token, pos + rep.length())
	return out


static func _is_sentence_start(s: String, idx: int) -> bool:
	var i := idx - 1
	while i >= 0:
		var ch := s[i]
		if ch == " " or ch == "\t" or ch == "\"" or ch == "'" or ch == "“":
			i -= 1
			continue
		return ch == "." or ch == "!" or ch == "?" or ch == "\n"
	return true
