class_name CharacterCreation
extends Control
## Five-step pre-intro character creation:
## 0: Appearance (skin, hair, clothing palette swap + randomise)
## 1: Pronouns (she/her, he/him, they/them)
## 2: Difficulty (Easy, Normal, Hard)
## 3: Hardcore (optional toggle + warning)
## 4: Confirm summary -> begins intro cutscene.

const MENU_SCENE := "res://scenes/menu/main_menu.tscn"
const INTRO_SCENE := "res://scenes/intro/intro.tscn"
const STEP_TITLES := [
	"Step 1 of 5 — Appearance",
	"Step 2 of 5 — Pronouns",
	"Step 3 of 5 — Difficulty",
	"Step 4 of 5 — Hardcore",
	"Step 5 of 5 — Confirm",
]
const FACING_ORDER := [0, 2, 1, 3]
const FACING_NAMES := ["South", "West", "North", "East"]

var character := Character.new()
var step_index := 0
var preview_material: ShaderMaterial

var _anim_time := 0.0
var _turn_time := 0.0
var _facing_idx := 0

@onready var _step_label: Label = $Margin/RootVBox/HeaderRow/StepLabel
@onready var _preview_sprite: Sprite2D = $Margin/RootVBox/BodyRow/PreviewPanel/Margin/VBox/SpriteStage/PreviewSprite
@onready var _facing_label: Label = $Margin/RootVBox/BodyRow/PreviewPanel/Margin/VBox/FacingLabel

@onready var _step_appearance: VBoxContainer = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance
@onready var _model_val: Label = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/ModelRow/Value
@onready var _model_prev: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/ModelRow/Prev
@onready var _model_next: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/ModelRow/Next
@onready var _skin_val: Label = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/SkinRow/Value
@onready var _hair_val: Label = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/HairRow/Value
@onready var _cloth_val: Label = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/ClothRow/Value
@onready var _skin_prev: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/SkinRow/Prev
@onready var _skin_next: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/SkinRow/Next
@onready var _hair_prev: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/HairRow/Prev
@onready var _hair_next: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/HairRow/Next
@onready var _cloth_prev: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/ClothRow/Prev
@onready var _cloth_next: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/ClothRow/Next
@onready var _random_btn: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepAppearance/RandomButton

@onready var _step_pronouns: VBoxContainer = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepPronouns
@onready var _btn_she: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepPronouns/SheButton
@onready var _btn_he: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepPronouns/HeButton
@onready var _btn_they: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepPronouns/TheyButton
@onready var _pronoun_sample: Label = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepPronouns/SampleLabel

@onready var _step_difficulty: VBoxContainer = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepDifficulty
@onready var _btn_easy: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepDifficulty/EasyButton
@onready var _btn_normal: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepDifficulty/NormalButton
@onready var _btn_hard: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepDifficulty/HardButton
@onready var _diff_desc: Label = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepDifficulty/DescLabel

@onready var _step_hardcore: VBoxContainer = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepHardcore
@onready var _hardcore_btn: Button = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepHardcore/ToggleButton
@onready var _hardcore_warn: Label = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepHardcore/WarningLabel

@onready var _step_confirm: VBoxContainer = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepConfirm
@onready var _summary_label: Label = $Margin/RootVBox/BodyRow/RightPanel/Margin/StepConfirm/SummaryLabel

@onready var _back_btn: Button = $Margin/RootVBox/FooterRow/BackButton
@onready var _next_btn: Button = $Margin/RootVBox/FooterRow/NextButton


func _ready() -> void:
	if Game.character:
		character = Game.character.duplicate() as Character
	preview_material = character.make_material()
	_preview_sprite.material = preview_material

	_model_prev.pressed.connect(func() -> void: _cycle_model(-1))
	_model_next.pressed.connect(func() -> void: _cycle_model(1))
	_skin_prev.pressed.connect(func() -> void: _cycle_skin(-1))
	_skin_next.pressed.connect(func() -> void: _cycle_skin(1))
	_hair_prev.pressed.connect(func() -> void: _cycle_hair(-1))
	_hair_next.pressed.connect(func() -> void: _cycle_hair(1))
	_cloth_prev.pressed.connect(func() -> void: _cycle_cloth(-1))
	_cloth_next.pressed.connect(func() -> void: _cycle_cloth(1))
	_random_btn.pressed.connect(_on_randomize)

	_btn_she.pressed.connect(func() -> void: _set_pronouns("she/her"))
	_btn_he.pressed.connect(func() -> void: _set_pronouns("he/him"))
	_btn_they.pressed.connect(func() -> void: _set_pronouns("they/them"))

	_btn_easy.pressed.connect(func() -> void: _set_difficulty("Easy"))
	_btn_normal.pressed.connect(func() -> void: _set_difficulty("Normal"))
	_btn_hard.pressed.connect(func() -> void: _set_difficulty("Hard"))

	_hardcore_btn.pressed.connect(_on_toggle_hardcore)

	_back_btn.pressed.connect(_on_back)
	_next_btn.pressed.connect(_on_next)

	Audio.play_music("mus_menu")
	Audio.play_ambience(["amb_wind", "amb_waves"])
	_refresh_ui()
	set_step(0)


func _process(delta: float) -> void:
	_anim_time += delta
	_turn_time += delta
	if _turn_time >= 1.4:
		_turn_time = 0.0
		_facing_idx = (_facing_idx + 1) % FACING_ORDER.size()
		_facing_label.text = "Facing: " + FACING_NAMES[_facing_idx]
	var col := int(_anim_time * 6.0) % 4
	var row: int = FACING_ORDER[_facing_idx]
	_preview_sprite.frame_coords = Vector2i(col, row)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		_on_back()


func set_step(idx: int) -> void:
	step_index = clampi(idx, 0, 4)
	_step_label.text = STEP_TITLES[step_index]
	_step_appearance.visible = (step_index == 0)
	_step_pronouns.visible = (step_index == 1)
	_step_difficulty.visible = (step_index == 2)
	_step_hardcore.visible = (step_index == 3)
	_step_confirm.visible = (step_index == 4)

	_back_btn.text = "Main Menu" if step_index == 0 else "Back"
	_next_btn.text = "Begin" if step_index == 4 else "Next"
	_refresh_ui()

	match step_index:
		0:
			_skin_next.grab_focus()
		1:
			_btn_they.grab_focus()
		2:
			_btn_normal.grab_focus()
		3:
			_hardcore_btn.grab_focus()
		4:
			_next_btn.grab_focus()


func _cycle_model(_delta: int = 1) -> void:
	character.body_type = "Male" if character.is_female() else "Female"
	if character.is_female() and character.pronouns == "he/him":
		character.pronouns = "she/her"
	elif not character.is_female() and character.pronouns == "she/her":
		character.pronouns = "he/him"
	_refresh_ui()


func _cycle_skin(delta: int) -> void:
	character.skin_index = posmod(character.skin_index + delta, Character.SKIN_TONES.size())
	_refresh_ui()


func _cycle_hair(delta: int) -> void:
	character.hair_index = posmod(character.hair_index + delta, Character.HAIR_COLOURS.size())
	_refresh_ui()


func _cycle_cloth(delta: int) -> void:
	character.cloth_index = posmod(character.cloth_index + delta, Character.CLOTHING_COLOURS.size())
	_refresh_ui()


func _on_randomize() -> void:
	character.randomize_appearance()
	_refresh_ui()


func _set_pronouns(p: String) -> void:
	character.pronouns = p
	_refresh_ui()


func _set_difficulty(d: String) -> void:
	character.difficulty = d
	_refresh_ui()


func _on_toggle_hardcore() -> void:
	character.hardcore = not character.hardcore
	_refresh_ui()


func _refresh_ui() -> void:
	character.apply_to_material(preview_material)
	_model_val.text = character.body_type
	var tex_path := "res://assets/hero/hero_female_sheet.png" if character.is_female() else "res://assets/hero/hero_sheet.png"
	if _preview_sprite.texture == null or _preview_sprite.texture.resource_path != tex_path:
		_preview_sprite.texture = load(tex_path) as Texture2D

	_skin_val.text = character.skin_name()
	_hair_val.text = character.hair_name()
	_cloth_val.text = character.cloth_name()

	_btn_she.text = ("* " if character.pronouns == "she/her" else "  ") + "she / her"
	_btn_he.text = ("* " if character.pronouns == "he/him" else "  ") + "he / him"
	_btn_they.text = ("* " if character.pronouns == "they/them" else "  ") + "they / them"
	_pronoun_sample.text = character.format_text(
		'"{they} pulled {themself} from the surf. {their} name is not on the manifest."'
	)

	_btn_easy.text = ("* " if character.difficulty == "Easy" else "  ") + "Easy (0.75x damage)"
	_btn_normal.text = ("* " if character.difficulty == "Normal" else "  ") + "Normal (1.0x damage)"
	_btn_hard.text = ("* " if character.difficulty == "Hard" else "  ") + "Hard (1.5x damage)"
	_diff_desc.text = "Damage taken multiplier: %.2fx" % character.damage_scale()

	_hardcore_btn.text = "Hardcore: ON" if character.hardcore else "Hardcore: OFF"
	_hardcore_warn.text = "Death ends this life for good."

	_summary_label.text = (
		"Model: %s\nSkin Tone: %s\nHair Colour: %s\nClothing: %s\nPronouns: %s\nDifficulty: %s (%.2fx)\nHardcore: %s"
		% [
			character.body_type,
			character.skin_name(),
			character.hair_name(),
			character.cloth_name(),
			character.pronouns,
			character.difficulty,
			character.damage_scale(),
			"Yes — death ends this life for good" if character.hardcore else "No",
		]
	)


func _on_back() -> void:
	if step_index > 0:
		set_step(step_index - 1)
	else:
		Game.go_to(MENU_SCENE)


func _on_next() -> void:
	if step_index < 4:
		set_step(step_index + 1)
	else:
		Game.character = character
		Game.reset()
		Game.go_to(INTRO_SCENE)
