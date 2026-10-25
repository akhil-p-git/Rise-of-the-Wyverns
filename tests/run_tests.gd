extends Node
## Headless tests. Run through tools/run_tests.sh (it uses a throwaway copy of the project).
## Exits 1 when any check fails; a bare assert() would hang the runner instead.

var passed := 0
var failed := 0
var root: Window:
	get:
		return get_tree().root


func _ready() -> void:
	await get_tree().process_frame
	# Tests set the clock themselves; real time must not push NPCs onto their evening schedule mid-run.
	TimeSystem.paused = true
	TimeSystem.set_time(12, 0)
	test_stats()
	test_settings_and_theme()
	test_audio()
	await test_character_and_menus()
	test_logic_and_data()
	await test_town_scenes()
	await test_day_night_and_interiors()
	await test_schedules()
	await test_inn_and_merchant()
	await test_room()
	await test_beach()
	await test_intro()
	Audio.stop_all()
	await get_tree().process_frame
	print("Results: %d passed, %d failed" % [passed, failed])
	get_tree().quit(1 if failed > 0 else 0)


func check(ok: bool, label: String) -> void:
	if ok:
		passed += 1
	else:
		failed += 1
		push_error("FAIL %s" % label)


func eq(actual: Variant, expected: Variant, label: String) -> void:
	if actual == expected:
		passed += 1
	else:
		failed += 1
		push_error("FAIL %s: expected %s, got %s" % [label, expected, actual])


func test_stats() -> void:
	var s := Stats.new()
	var died_count := [0]
	s.died.connect(func() -> void: died_count[0] += 1)
	s.damage(30.0)
	eq(s.health, 70.0, "damage reduces health")
	s.heal(500.0)
	eq(s.health, 100.0, "heal clamps to max")
	s.damage(500.0)
	eq(s.health, 0.0, "damage clamps at zero")
	s.damage(10.0)
	eq(died_count[0], 1, "died emitted once")
	s.heal(50.0)
	eq(s.health, 0.0, "dead actors are not healed")
	s.restore_all()
	eq(s.health, 0.0, "restore_all does not revive the dead")

	var r := Stats.new()
	r.damage(60.0)
	r.use_stamina(80.0)
	r.spend_mana(40.0)
	r.restore_all()
	eq([r.health, r.stamina, r.mana], [r.max_health, r.max_stamina, r.max_mana], "restore_all refills every vital")

	var t := Stats.new()
	check(t.use_stamina(40.0), "use_stamina spends when available")
	eq(t.stamina, 60.0, "stamina after spend")
	t.tick(0.5)
	eq(t.stamina, 60.0, "no regen inside the delay")
	t.tick(0.6)
	check(t.stamina > 60.0, "regen after the delay")
	t.use_stamina(1000.0)
	eq(t.stamina, 0.0, "use_stamina clamps at zero")
	check(not t.use_stamina(1.0), "use_stamina refuses at zero")

	var m := Stats.new()
	check(not m.spend_mana(60.0), "spend_mana refuses when short")
	eq(m.mana, 50.0, "refused spend leaves mana alone")
	check(m.spend_mana(20.0), "spend_mana succeeds")
	eq(m.mana, 30.0, "mana after spend")
	m.tick(1.0)
	check(m.mana > 30.0, "mana regenerates")


func test_settings_and_theme() -> void:
	var cfg_path := "user://test_settings.cfg"
	Game.set_fullscreen(true, cfg_path)
	Game.set_vsync(false, cfg_path)
	Game.fullscreen = false
	Game.vsync = true
	Game.load_settings(cfg_path)
	eq(Game.fullscreen, true, "fullscreen setting round-trips through ConfigFile")
	eq(Game.vsync, false, "vsync setting round-trips through ConfigFile")
	Game.toggle_fullscreen(cfg_path)
	Game.toggle_vsync(cfg_path)
	eq(Game.fullscreen, false, "toggle_fullscreen flips fullscreen back to false")
	eq(Game.vsync, true, "toggle_vsync flips vsync back to true")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(cfg_path))

	var theme := load("res://assets/ui/grim_theme.tres") as Theme
	check(theme != null, "grim_theme.tres loads as Theme")
	if theme:
		check(theme.default_font != null, "grim_theme has default_font")
		for state_name: String in ["normal", "hover", "focus", "pressed", "disabled"]:
			check(theme.has_stylebox(state_name, "Button"), "grim_theme Button has %s stylebox" % state_name)
		for slider_style: String in ["slider", "grabber_area", "grabber_area_highlight"]:
			check(theme.has_stylebox(slider_style, "HSlider"), "grim_theme HSlider has %s stylebox" % slider_style)
		check(theme.has_stylebox("panel", "PanelContainer"), "grim_theme PanelContainer has panel stylebox")


func test_audio() -> void:
	check(Audio != null, "Audio autoload is registered")
	for bus_name: String in ["Master", "Music", "SFX", "Ambience", "UI"]:
		check(AudioServer.get_bus_index(bus_name) != -1, "Audio bus '%s' exists" % bus_name)

	var audio_json := StoryData.load_json("res://data/audio.json")
	var cues: Dictionary = audio_json.get("cues", {})
	check(not cues.is_empty(), "data/audio.json has cues")
	for cue_id: String in cues:
		var p: String = cues[cue_id].get("path", "")
		check(FileAccess.file_exists(p), "audio cue '%s' file exists at %s" % [cue_id, p])

	var expected_cues := [
		"mus_menu", "mus_storm", "mus_beach", "mus_wrackmouth", "mus_crossholm_road",
		"amb_waves", "amb_wind", "amb_rain", "amb_gulls", "amb_fire",
		"ui_hover", "ui_confirm", "ui_back", "dialogue_blip",
		"step_sand", "step_wet_sand", "step_gravel", "step_planks", "step_stone",
		"pickup", "rest_fire", "scene_exit", "thunder",
	]
	for req_id: String in expected_cues:
		check(cues.has(req_id), "cue '%s' used in scenes/code exists in data/audio.json" % req_id)

	# Missing cue warns once and never crashes
	Audio.play_sfx("nonexistent_test_cue")
	Audio.play_sfx("nonexistent_test_cue")
	check(Audio.warned_missing.has("nonexistent_test_cue"), "missing cue recorded once without crashing")

	# Bus volumes round-trip through settings ConfigFile
	var cfg_path := "user://test_audio_settings.cfg"
	var sample_vols := {"Master": 0.75, "Music": 0.40, "SFX": 0.65, "Ambience": 0.50, "UI": 0.80}
	for bname: String in sample_vols:
		Audio.set_bus_volume(bname, sample_vols[bname], cfg_path)
	for bname: String in sample_vols:
		Audio.set_bus_volume(bname, 0.10, "user://dummy_ignored.cfg")
	Audio.load_volumes(cfg_path)
	for bname: String in sample_vols:
		check(absf(Audio.get_bus_volume(bname) - sample_vols[bname]) < 0.001, "bus '%s' volume round-trips" % bname)
	DirAccess.remove_absolute(ProjectSettings.globalize_path(cfg_path))
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://dummy_ignored.cfg"))


func test_character_and_menus() -> void:
	var c := Character.new()
	check(Character.SKIN_TONES.size() >= 5, "at least 5 skin tones")
	check(Character.HAIR_COLOURS.size() >= 6, "at least 6 hair colours")
	check(Character.CLOTHING_COLOURS.size() >= 4, "at least 4 clothing colours")
	eq(c.pronouns, "they/them", "default pronouns they/them")
	eq(c.difficulty, "Normal", "default difficulty Normal")
	eq(c.hardcore, false, "default hardcore false")

	# Pronoun sets & sentence-start capitalisation
	var tpl := "{they} staggered ashore. Carry {them} to {their} bed; the pack is {theirs}, and {they} steadied {themself}."
	c.pronouns = "she/her"
	eq(
		c.format_text(tpl),
		"She staggered ashore. Carry her to her bed; the pack is hers, and she steadied herself.",
		"she/her pronouns and sentence-start capitalisation"
	)
	c.pronouns = "he/him"
	eq(
		c.format_text(tpl),
		"He staggered ashore. Carry him to his bed; the pack is his, and he steadied himself.",
		"he/him pronouns and sentence-start capitalisation"
	)
	c.pronouns = "they/them"
	eq(
		c.format_text(tpl),
		"They staggered ashore. Carry them to their bed; the pack is theirs, and they steadied themself.",
		"they/them pronouns and sentence-start capitalisation"
	)

	# DialogueRunner pronoun resolution
	var p_tree := {
		"entries": [{"if": [], "node": "n1"}],
		"nodes": {"n1": {"speaker": "Test", "text": "{they} {is_are} here."}},
	}
	var p_runner := DialogueRunner.new()
	c.pronouns = "she/her"
	p_runner.begin(p_tree, Game.state, c)
	eq(p_runner.text(), "She is here.", "DialogueRunner resolves she/her tokens")
	c.pronouns = "they/them"
	p_runner.begin(p_tree, Game.state, c)
	eq(p_runner.text(), "They are here.", "DialogueRunner resolves they/them tokens")

	# Difficulty damage scale
	var prev_char := Game.character
	Game.character = c
	c.difficulty = "Easy"
	eq(Game.difficulty_damage_scale(), 0.75, "Easy difficulty scale is 0.75")
	c.difficulty = "Normal"
	eq(Game.difficulty_damage_scale(), 1.0, "Normal difficulty scale is 1.0")
	c.difficulty = "Hard"
	eq(Game.difficulty_damage_scale(), 1.5, "Hard difficulty scale is 1.5")

	# Palette shader material parameters
	c.skin_index = 3
	c.hair_index = 4
	c.cloth_index = 2
	var mat := c.make_material()
	check(mat != null and mat.shader != null, "Character creates ShaderMaterial")
	eq(mat.get_shader_parameter("skin_color"), c.skin_color(), "shader skin_color matches character")
	eq(mat.get_shader_parameter("hair_color"), c.hair_color(), "shader hair_color matches character")
	eq(mat.get_shader_parameter("cloth_color"), c.cloth_color(), "shader cloth_color matches character")
	Game.character = prev_char

	# Scene chain resolution and headless instantiation
	check(ResourceLoader.exists("res://scenes/menu/main_menu.tscn"), "main_menu.tscn exists")
	check(ResourceLoader.exists(MainMenu.CREATION_SCENE), "MainMenu -> CharacterCreation target exists")
	check(ResourceLoader.exists(CharacterCreation.INTRO_SCENE), "CharacterCreation -> Intro target exists")
	check(ResourceLoader.exists("res://scenes/world/beach.tscn"), "Intro -> Beach target exists")

	var menu: MainMenu = load("res://scenes/menu/main_menu.tscn").instantiate()
	root.add_child(menu)
	await physics_frames(2)
	check(menu != null, "main_menu.tscn instantiates headless")
	check(not menu.get_node("Center/MainBox/Buttons/ContinueButton").visible, "Continue stays hidden")
	menu.queue_free()
	await get_tree().process_frame

	var cc: CharacterCreation = load("res://scenes/menu/character_creation.tscn").instantiate()
	root.add_child(cc)
	await physics_frames(2)
	check(cc != null, "character_creation.tscn instantiates headless")
	for step_i in 5:
		cc.set_step(step_i)
		eq(cc.step_index, step_i, "character_creation switches to step %d" % step_i)
	cc.queue_free()
	await get_tree().process_frame


func physics_frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func process_frame_wait() -> void:
	await get_tree().process_frame


func hold(actions: Array, frames: int) -> void:
	for a in actions:
		Input.action_press(a)
	await physics_frames(frames)
	for a in actions:
		Input.action_release(a)


func place(player: Player, pos: Vector2) -> void:
	player.global_position = pos
	player.velocity = Vector2.ZERO
	await physics_frames(2)


func test_room() -> void:
	var room: Node = load("res://scenes/world/test_room.tscn").instantiate()
	root.add_child(room)
	await physics_frames(3)
	var player: Player = room.get_node("Player")

	await place(player, Vector2(300, 200))
	var start := player.global_position
	await hold(["move_right"], 30)
	check(player.global_position.x > start.x + 20.0, "walking right moves the player")
	check(absf(player.global_position.y - start.y) < 1.0, "walking right does not drift vertically")

	await place(player, Vector2(300, 200))
	await hold(["move_right", "move_down"], 30)
	var diagonal := player.global_position - Vector2(300, 200)
	check(diagonal.x > 15.0 and diagonal.y > 15.0, "diagonal movement moves on both axes")
	check(diagonal.length() < 50.0, "diagonal speed is normalized")

	await place(player, Vector2(300, 200))
	player.stats.stamina = 100.0
	await hold(["move_right", "sprint"], 30)
	check(player.stats.stamina < 100.0, "sprinting drains stamina")
	check(player.global_position.x - 300.0 > 40.0, "sprinting is faster than walking")

	player.stats.stamina = 0.0
	await place(player, Vector2(300, 200))
	await hold(["move_right", "sprint"], 30)
	check(player.global_position.x - 300.0 < 45.0, "no sprint without stamina")

	await place(player, Vector2(630, 200))
	await hold(["move_right"], 60)
	check(player.global_position.x < 636.0, "the east wall stops the player")

	# Tree1's collider is centred at y=117 and the player's body circle sits 3px above its origin,
	# so start at y=120 to hit the trunk head-on; an off-centre approach slides around it instead.
	await place(player, Vector2(40, 120))
	await hold(["move_right"], 60)
	var tree_x := player.global_position.x
	check(tree_x < 50.5, "a tree trunk blocks the player (x=%s)" % tree_x)
	check(tree_x > 35.0, "the player reached the tree (x=%s)" % tree_x)

	var messages: Array[String] = []
	room.get_node("Sign").interacted.connect(func(text: String) -> void: messages.append(text))
	var prompts: Array[String] = []
	player.prompt_changed.connect(func(text: String) -> void: prompts.append(text))
	await place(player, Vector2(340, 185))
	await physics_frames(3)
	check(prompts.size() > 0 and prompts[-1] == "Read", "the prompt appears near the sign")
	var press := InputEventAction.new()
	press.action = "interact"
	press.pressed = true
	Input.parse_input_event(press)
	await physics_frames(2)
	eq(messages.size(), 1, "interact triggers the sign once")
	check(messages.size() > 0 and messages[0].begins_with("Harbor road"), "sign message text")
	await place(player, Vector2(200, 300))
	await physics_frames(3)
	check(prompts[-1] == "", "the prompt clears when walking away")

	player.stats.damage(30.0)
	var health_bar: ProgressBar = room.get_node("Hud/Bars/Health")
	eq(health_bar.value, 70.0, "HUD health bar follows stats")

	# Combat punches and blocking
	var attack_events: Array[bool] = []
	player.attacked.connect(func(is_power: bool) -> void: attack_events.append(is_power))

	player.perform_normal_attack()
	check(player.is_attacking, "perform_normal_attack sets is_attacking")
	eq(player.last_attack_was_power, false, "perform_normal_attack sets last_attack_was_power to false")
	eq(attack_events.size(), 1, "attacked signal emitted once")
	eq(attack_events[-1], false, "attacked signal passes is_power=false")
	await physics_frames(18)
	check(not player.is_attacking, "normal attack finishes after duration")

	player.stats.stamina = 100.0
	var power_ok := player.perform_power_attack()
	check(power_ok, "perform_power_attack succeeds with full stamina")
	check(player.is_attacking, "perform_power_attack sets is_attacking")
	eq(player.last_attack_was_power, true, "perform_power_attack sets last_attack_was_power to true")
	eq(player.stats.stamina, 80.0, "power attack spends 20 stamina")
	eq(attack_events.size(), 2, "attacked signal emitted twice")
	eq(attack_events[-1], true, "attacked signal passes is_power=true")
	await physics_frames(25)
	check(not player.is_attacking, "power attack finishes after duration")

	# Blocking (high guard)
	Input.action_press("block")
	await physics_frames(2)
	check(player.is_blocking, "pressing block sets player.is_blocking")
	Input.action_release("block")
	await physics_frames(2)
	check(not player.is_blocking, "releasing block clears player.is_blocking")

	# Inventory satchel UI
	var hud: Hud = room.get_node("Hud")
	check(hud.inventory != null, "HUD has InventoryPanel")
	check(not hud.inventory.is_open(), "inventory starts closed")

	Game.state.apply(["give:moonherb:3", "give:coin:12"])
	hud.inventory.open()
	check(hud.inventory.is_open(), "inventory.open() opens inventory")
	await physics_frames(2)
	check(hud.inventory.item_row_count() >= 1, "inventory displays carried items")

	hud.inventory.select_item("moonherb")
	check(hud.inventory._selected_item == "moonherb", "item selection updates _selected_item")

	hud.inventory.close()
	check(not hud.inventory.is_open(), "inventory.close() closes inventory")

	hud.inventory.toggle()
	check(hud.inventory.is_open(), "inventory.toggle() toggles to open")
	hud.inventory.toggle()
	check(not hud.inventory.is_open(), "inventory.toggle() toggles to closed")

	# Waiting (T): opens the menu, skips the clock, refills every vital
	TimeSystem.set_time(20, 0)
	Game.stats.damage(50.0)
	Game.stats.use_stamina(60.0)
	Game.stats.spend_mana(30.0)
	var wait_event := InputEventAction.new()
	wait_event.action = "wait"
	wait_event.pressed = true
	hud._unhandled_input(wait_event)
	check(hud.wait_panel.is_open(), "pressing wait opens the wait panel")
	check(not player.input_enabled, "the wait panel freezes the player")
	hud.wait_panel.adjust(5)
	eq(hud.wait_panel.hours, 6, "wait panel adjusts hours")
	hud.wait_panel.adjust(100)
	eq(hud.wait_panel.hours, WaitPanel.MAX_HOURS, "wait panel caps at 24 hours")
	hud.wait_panel.adjust(-100)
	eq(hud.wait_panel.hours, WaitPanel.MIN_HOURS, "wait panel floors at 1 hour")
	hud.wait_panel.adjust(5)
	hud.wait_panel.confirm()
	check(not hud.wait_panel.is_open(), "confirming closes the wait panel")
	check(player.input_enabled, "the player can move again after waiting")
	eq(TimeSystem.get_hour(), 2, "waiting 6 hours from 8 PM lands at 2 AM")
	eq(
		[Game.stats.health, Game.stats.stamina, Game.stats.mana],
		[Game.stats.max_health, Game.stats.max_stamina, Game.stats.max_mana],
		"waiting regenerates all vitals"
	)
	hud._unhandled_input(wait_event)
	hud.wait_panel.cancel()
	check(player.input_enabled and TimeSystem.get_hour() == 2, "cancelling the wait changes nothing")
	TimeSystem.set_time(12, 0)

	room.queue_free()
	await get_tree().process_frame


func test_beach() -> void:
	var beach: Node = load("res://scenes/world/beach.tscn").instantiate()
	root.add_child(beach)
	await physics_frames(3)
	var player: Player = beach.get_node("Entities/Player")

	await place(player, Vector2(150, 80))
	await hold(["move_up"], 60)
	check(player.global_position.y > 58.0, "the sea stops the player (y=%s)" % player.global_position.y)

	await place(player, Vector2(138, 130))
	await hold(["move_up"], 60)
	check(player.global_position.y > 112.0, "the crate blocks the player (y=%s)" % player.global_position.y)

	await place(player, Vector2(64, 150))
	await hold(["move_up"], 60)
	check(player.global_position.y > 134.0, "the tide pool blocks the player (y=%s)" % player.global_position.y)

	var to_town: Area2D = beach.get_node_or_null("Zones/ToTown")
	check(to_town != null and to_town.target_scene == "res://scenes/world/wrackmouth.tscn", "beach has exit to Wrackmouth")
	check(beach.get_node_or_null("Spawns/from_town") is Marker2D, "beach has Spawns/from_town marker")
	var crate_sign: Node = beach.get_node_or_null("Interactables/CrateSign")
	check(crate_sign != null and not crate_sign is Pickup, "beach crate is an examine point, not a pickup")
	check(beach.get_node_or_null("Interactables/IronScrap1") != null and beach.get_node("Interactables/IronScrap1").get("item") == "iron_scrap", "beach has IronScrap1 pickup")
	check(beach.get_node_or_null("Interactables/IronScrap2") != null and beach.get_node("Interactables/IronScrap2").get("item") == "iron_scrap", "beach has IronScrap2 pickup")
	check(beach.get_node_or_null("Interactables/IronScrap3") != null and beach.get_node("Interactables/IronScrap3").get("item") == "iron_scrap", "beach has IronScrap3 pickup")
	if to_town:
		to_town.monitoring = false
	await place(player, Vector2(150, 140))
	await hold(["move_down"], 60)
	check(player.global_position.y > 165.0, "the path south is open (y=%s)" % player.global_position.y)

	var prompts: Array[String] = []
	player.prompt_changed.connect(func(text: String) -> void: prompts.append(text))
	await place(player, Vector2(194, 102))
	await physics_frames(3)
	check(prompts.size() > 0 and prompts[-1] == "Examine", "the prompt appears at the wyvern bones")

	beach.queue_free()
	await get_tree().process_frame


func test_logic_and_data() -> void:
	var story := StoryData.load_json("res://data/story.json")
	check(not story.is_empty(), "story.json loads")

	# Flags and derived flags (generic mechanics, on a small fixture rather than the shipped story)
	var fixture := {
		"items": {"coin": "Coin", "herb": "Herb"},
		"derived": {"all_chores": ["flag:chore_a", "flag:chore_b", "flag:chore_c"]},
		"quests": {
			"errands": {
				"title": "Errands",
				"stages": [
					{"id": "chores", "text": "Do the chores", "done_when": ["flag:chore_a", "flag:chore_b", "flag:chore_c"]},
					{"id": "gather", "text": "Gather herbs", "done_when": ["item:herb>=3"]},
					{"id": "report", "text": "Report back", "done_when": ["flag:reported"]},
				],
			},
		},
	}
	var state := GameState.new(fixture)
	check(not state.has_flag("chore_a"), "flag initially unset")
	state.set_flag("chore_a")
	check(state.has_flag("chore_a"), "flag set")
	check(not state.has_flag("all_chores"), "derived flag false when partial")
	state.apply(["flag:chore_b", "flag:chore_c"])
	check(state.has_flag("all_chores"), "derived flag true when all parts hold")
	state.apply(["clear:chore_c"])
	check(not state.has_flag("all_chores"), "derived flag false after clearing component")
	state.set_flag("chore_c")

	# Items
	eq(state.count("coin"), 0, "coin starts at 0")
	state.apply(["give:coin:15"])
	eq(state.count("coin"), 15, "give adds item count")
	check(not state.take("coin", 20), "take refuses when short")
	eq(state.count("coin"), 15, "refused take leaves count intact")
	check(state.take("coin", 5), "take succeeds when enough")
	eq(state.count("coin"), 10, "take subtracts count")

	# QuestLog progression
	state.apply(["start:errands"])
	check(state.quests.is_active("errands"), "errands is active")
	eq(state.quests.stage_id("errands"), "gather", "chores already done, so it starts at the gather stage")
	state.apply(["give:herb:2"])
	check(state.objective("errands").ends_with("Gather herbs"), "single-part objective has no progress suffix")
	state.apply(["give:herb:1"])
	eq(state.quests.stage_id("errands"), "report", "advances to report stage")
	state.apply(["flag:reported"])
	check(state.quests.is_done("errands"), "errands completes")

	var multi := GameState.new(fixture)
	multi.apply(["start:errands", "flag:chore_a"])
	check(multi.objective("errands").ends_with("(1/3)"), "a three-part stage tracks 1/3")

	# DialogueRunner: the mayor gives one quest, then the weapon choice
	var mayor_tree := StoryData.load_json("res://data/dialogue/mayor.json")
	var fresh_state := GameState.new(story)
	var runner := DialogueRunner.new()
	check(runner.begin(mayor_tree, fresh_state), "mayor dialogue begins on fresh state")
	eq(runner.node_id, "first", "fresh state enters 'first' node")
	eq(runner.choices().size(), 3, "first node offers 3 choices")
	runner.advance(0) # "I can work." -> "accept"
	eq(runner.node_id, "accept", "choice 0 advances to accept")
	check(fresh_state.quests.is_active("giant_rat"), "accept node starts giant_rat")
	eq(fresh_state.quests.stage_id("giant_rat"), "hunt", "the quest starts at the hunt stage")
	runner.advance()
	eq(runner.node_id, "weapons", "accepting leads straight to the weapon choice")
	eq(runner.choices().size(), 4, "the mayor offers four weapons")
	runner.advance(2) # the two-handed sword
	eq(fresh_state.count("two_handed_sword"), 1, "the chosen weapon is given")
	check(fresh_state.has_flag("weapon_chosen"), "choosing a weapon sets weapon_chosen")
	eq(runner.node_id, "armed", "the mayor sends the player off")
	runner.advance()
	check(runner.finished, "dialogue finishes after armed")
	# Only one weapon: talking again just reminds the player of the hunt
	runner.begin(mayor_tree, fresh_state)
	eq(runner.node_id, "hunt_reminder", "after choosing, the mayor only repeats the task")
	eq(fresh_state.count("iron_daggers") + fresh_state.count("staff") + fresh_state.count("iron_sword_shield"), 0, "no second weapon is given")
	# Walking away from the choice offers it again
	var undecided := GameState.new(story)
	undecided.apply(["start:giant_rat"])
	runner.begin(mayor_tree, undecided)
	eq(runner.node_id, "weapons", "leaving without choosing re-offers the weapons")
	# Each weapon is a real item
	for weapon: String in ["iron_daggers", "iron_sword_shield", "two_handed_sword", "staff"]:
		check(story["items"].has(weapon) and InventoryPanel.ITEM_DESCRIPTIONS.has(weapon), "%s is a named, described item" % weapon)
	# Reporting the kill pays and finishes the quest
	fresh_state.apply(["flag:giant_rat_slain"])
	eq(fresh_state.quests.stage_id("giant_rat"), "report", "killing the rat moves the quest to the report stage")
	runner.begin(mayor_tree, fresh_state)
	eq(runner.node_id, "report", "the mayor takes the report")
	eq(fresh_state.count("coin"), 25, "the report pays 25 coin")
	check(fresh_state.quests.is_done("giant_rat"), "The Rat Below is complete")
	runner.begin(mayor_tree, fresh_state)
	eq(runner.node_id, "after", "afterwards the mayor has only thanks")

	# Tam: the whistle can be handed over without ever taking his quest
	var early := GameState.new(story)
	early.apply(["give:bone_whistle"])
	var tam_tree := StoryData.load_json("res://data/dialogue/tam.json")
	runner.begin(tam_tree, early)
	eq(runner.node_id, "early", "Tam notices a whistle the player already holds")
	runner.advance(0) # "Oh, you mean this whistle?"
	eq(runner.node_id, "early_return", "the player can hand it over right away")
	eq(early.count("bone_whistle"), 0, "the whistle goes back to Tam")
	eq(early.count("coin"), 10, "Tam pays 10 coin")
	check(early.quests.is_done("tams_whistle"), "Tam's Whistle completes without a separate step")
	var declined := GameState.new(story)
	declined.apply(["give:bone_whistle"])
	runner.begin(tam_tree, declined)
	runner.advance(1) # "It's just a shell."
	check(runner.finished and declined.count("bone_whistle") == 1, "the player can keep the whistle")

	# Cross-reference validation across data/story.json and data/dialogue/*.json
	var items_dict: Dictionary = story.get("items", {})
	var quests_dict: Dictionary = story.get("quests", {})
	var stage_ids_by_quest := {}
	for qid: String in quests_dict:
		var sids := {}
		for st: Dictionary in quests_dict[qid].get("stages", []):
			sids[st["id"]] = true
		stage_ids_by_quest[qid] = sids

	for dflag: String in story.get("derived", {}):
		for cond: String in story["derived"][dflag]:
			_validate_cond(cond, "story.derived." + dflag, items_dict, quests_dict, stage_ids_by_quest)
	for qid: String in quests_dict:
		for st: Dictionary in quests_dict[qid].get("stages", []):
			for cond: String in st.get("done_when", []):
				_validate_cond(cond, "story.quests.%s.%s" % [qid, st["id"]], items_dict, quests_dict, stage_ids_by_quest)

	var dialogue_files := ["ansa", "bram", "chancellor", "dov", "guard", "isa", "mayor", "orsa", "osric", "pell", "tam", "teague", "wizard", "wren"]
	for dlg_name: String in dialogue_files:
		var path := "res://data/dialogue/%s.json" % dlg_name
		var tree := StoryData.load_json(path)
		var nodes: Dictionary = tree.get("nodes", {})
		check(not nodes.is_empty(), "%s has nodes" % path)
		for entry: Dictionary in tree.get("entries", []):
			check(nodes.has(entry.get("node", "")), "%s entry node '%s' exists" % [path, entry.get("node", "")])
			for cond: String in entry.get("if", []):
				_validate_cond(cond, path + ":entry", items_dict, quests_dict, stage_ids_by_quest)
		for nid: String in nodes:
			var n: Dictionary = nodes[nid]
			if n.has("next"):
				check(nodes.has(n["next"]), "%s node '%s' next '%s' exists" % [path, nid, n["next"]])
			for act: String in n.get("do", []):
				_validate_action(act, "%s:%s" % [path, nid], items_dict, quests_dict)
			for ch: Dictionary in n.get("choices", []):
				if ch.has("next"):
					check(nodes.has(ch["next"]), "%s choice next '%s' exists" % [path, ch["next"]])
				for cond: String in ch.get("if", []):
					_validate_cond(cond, "%s:%s:choice" % [path, nid], items_dict, quests_dict, stage_ids_by_quest)
				for act: String in ch.get("do", []):
					_validate_action(act, "%s:%s:choice" % [path, nid], items_dict, quests_dict)


func _validate_cond(cond: String, ctx: String, items_dict: Dictionary, quests_dict: Dictionary, stage_ids_by_quest: Dictionary) -> void:
	var raw := cond.trim_prefix("!")
	var sep := raw.find(":")
	check(sep > 0, "%s: condition '%s' has prefix" % [ctx, cond])
	var kind := raw.substr(0, sep)
	var arg := raw.substr(sep + 1)
	match kind:
		"flag":
			check(not arg.is_empty(), "%s: flag name non-empty" % ctx)
		"item":
			var bits := arg.split(">=")
			check(items_dict.has(bits[0]), "%s: item '%s' exists in story.json" % [ctx, bits[0]])
		"started", "active", "done":
			check(quests_dict.has(arg), "%s: quest '%s' exists in story.json" % [ctx, arg])
		"stage":
			var bits := arg.split("=")
			check(bits.size() == 2 and quests_dict.has(bits[0]) and stage_ids_by_quest[bits[0]].has(bits[1]), "%s: stage '%s' resolves" % [ctx, arg])
		_:
			check(false, "%s: unknown condition kind '%s'" % [ctx, kind])


func _validate_action(act: String, ctx: String, items_dict: Dictionary, quests_dict: Dictionary) -> void:
	var parts := act.split(":")
	match parts[0]:
		"flag", "clear":
			check(parts.size() == 2 and not parts[1].is_empty(), "%s: action '%s' valid" % [ctx, act])
		"start":
			check(parts.size() == 2 and quests_dict.has(parts[1]), "%s: start quest '%s' exists" % [ctx, act])
		"give", "take":
			check(parts.size() >= 2 and items_dict.has(parts[1]), "%s: item '%s' exists in action '%s'" % [ctx, parts[1], act])
		_:
			check(false, "%s: unknown action '%s'" % [ctx, act])


func test_town_scenes() -> void:
	var wm: Node = load("res://scenes/world/wrackmouth.tscn").instantiate()
	root.add_child(wm)
	await physics_frames(2)
	check(wm != null, "wrackmouth.tscn instantiates")
	check(wm.get_node_or_null("Ground") is Sprite2D, "wrackmouth has Sprite2D ground")
	check(wm.get_node("Entities/MayorHall").texture != null, "MayorHall has building texture")
	var guard: Npc = wm.get_node("Entities/GuardRorik")
	var orsa: Npc = wm.get_node("Entities/OrsaKell")
	var teague: Npc = wm.get_node("Entities/TeagueMarrow")
	var wren: Npc = wm.get_node("Entities/Wren")
	var player: Player = wm.get_node("Entities/Player")
	check(guard.sprite_sheet != null, "GuardRorik has custom NPC sprite sheet")
	check(wm.get_node_or_null("Entities/MayorTolle") == null, "Mayor Tolle is inside Mayor's Hall, not outside on street")

	# Seed all NPCs deterministically
	var all_npcs: Array[Npc] = []
	for child in wm.get_node("Entities").get_children():
		if child is Npc:
			var n := child as Npc
			n.set_seed(12345 + all_npcs.size() * 97)
			all_npcs.append(n)

	# Place Orsa close to Forge wall so wander must avoid wall collisions over 3000 frames
	var dt := 1.0 / 60.0
	var stayed_in_radius := true
	var never_overlapped_wall := true
	var guard_stayed_put := true
	var reached_wp0 := false
	var reached_wp1 := false

	var total_usec := 0
	for frame_i in 3000:
		var t0 := Time.get_ticks_usec()
		for n: Npc in all_npcs:
			n._physics_process(dt)
		total_usec += Time.get_ticks_usec() - t0

		if orsa.global_position.distance_to(orsa.home_position) > orsa.wander_radius + 0.01:
			stayed_in_radius = false
		if orsa._is_blocked(orsa.global_position):
			never_overlapped_wall = false
		if guard.global_position.distance_to(guard.home_position) > 0.001:
			guard_stayed_put = false
		if teague.global_position.distance_to(teague.waypoints[0]) <= 2.0:
			reached_wp0 = true
		if teague.global_position.distance_to(teague.waypoints[1]) <= 2.0:
			reached_wp1 = true

	var avg_ms := float(total_usec) / 3000.0 / 1000.0
	print("NPC physics benchmark (7 NPCs in Wrackmouth): %.4f ms/frame" % avg_ms)
	check(avg_ms < 0.2, "all Wrackmouth NPCs under 0.2 ms/frame (got %.4f ms)" % avg_ms)
	check(stayed_in_radius, "wander NPC stays inside wander_radius over 3000 frames")
	check(never_overlapped_wall, "wander NPC never overlaps a wall over 3000 frames")
	check(guard_stayed_put, "stationary NPC does not move over 3000 frames")
	check(reached_wp0 and reached_wp1, "pace NPC reaches each waypoint")

	# Interaction test: stops NPC, faces player, resumes after end_interaction
	player.global_position = wren.global_position + Vector2(-18.0, 0.0)
	wren.interact(player)
	check(wren.interacting, "interacting sets NPC interacting=true")
	eq(wren.facing_row, 2, "NPC turns left (row 2) to face player on the left")
	var pos_during := wren.global_position
	for i in 120:
		wren._physics_process(dt)
	eq(wren.global_position, pos_during, "NPC does not move while interacting")
	if wm.get_node("DialogueBox").is_open():
		wm.get_node("DialogueBox")._close()
	else:
		wren.end_interaction()
	check(not wren.interacting, "NPC resumes after dialogue closes")
	var moved_after := false
	for i in 300:
		wren._physics_process(dt)
		if wren.global_position.distance_to(pos_during) > 1.0:
			moved_after = true
			break
	check(moved_after, "wander NPC moves again after interaction ends")

	# Verify realistic prop collisions for PlazaSignpost (282, 186) and PlazaCampfire (320, 210)
	await place(player, Vector2(262, 185))
	await hold(["move_right"], 45)
	check(player.global_position.x < 276.0, "PlazaSignpost blocks the player (x=%s)" % player.global_position.x)
	check(player.global_position.x > 268.0, "player reaches PlazaSignpost collider (x=%s)" % player.global_position.x)

	await place(player, Vector2(296, 209))
	await hold(["move_right"], 45)
	check(player.global_position.x < 308.0, "PlazaCampfire blocks the player (x=%s)" % player.global_position.x)
	check(player.global_position.x > 300.0, "player reaches PlazaCampfire collider (x=%s)" % player.global_position.x)

	wm.queue_free()
	await get_tree().process_frame

	var cr: Node = load("res://scenes/world/crossholm_road.tscn").instantiate()
	root.add_child(cr)
	await physics_frames(2)
	check(cr != null, "crossholm_road.tscn instantiates")
	check(cr.get_node_or_null("Ground") is Sprite2D, "crossholm_road has Sprite2D ground")
	check(cr.get_node("Entities/Gate").texture != null, "Crossholm Gate has building texture")
	cr.queue_free()
	await get_tree().process_frame


func test_intro() -> void:
	var intro: Node = load("res://scenes/intro/intro.tscn").instantiate()
	root.add_child(intro)
	await physics_frames(3)
	intro.skip()
	await physics_frames(3)
	var beach: Node = root.get_node_or_null("Beach")
	check(beach != null, "skipping the intro hands off to the beach")
	check(not is_instance_valid(intro), "the intro frees itself after the handoff")
	if beach != null:
		var player: Player = beach.get_node("Entities/Player")
		check(beach.play_arrival, "the beach knows it is the arrival")
		check(player.speed_scale < 1.0, "the survivor staggers ashore at reduced speed")
		beach.queue_free()
		await get_tree().process_frame


func test_day_night_and_interiors() -> void:
	# 1. TimeSystem Day/Night Cycle & Locking rules
	check(TimeSystem != null, "TimeSystem autoload is registered")
	TimeSystem.set_time(12, 0)
	eq(TimeSystem.get_hour(), 12, "TimeSystem sets hour to 12")
	eq(TimeSystem.get_minute(), 0, "TimeSystem sets minute to 0")
	check(TimeSystem.is_day(), "12:00 PM is day")
	check(not TimeSystem.is_night(), "12:00 PM is not night")
	check(not TimeSystem.is_building_locked("mayor_hall"), "Mayor's Hall unlocked at noon")
	check(not TimeSystem.is_building_locked("forge"), "Forge unlocked at noon")
	check(not TimeSystem.is_building_locked("salt_gull"), "Salt Gull unlocked at noon")
	check(TimeSystem.is_building_locked("cottage_shuttered"), "Shuttered cottage always locked")

	# 10:00 PM (22:00) lock time
	TimeSystem.set_time(22, 15)
	eq(TimeSystem.get_hour(), 22, "TimeSystem sets hour to 22")
	check(TimeSystem.is_night(), "10:15 PM is night")
	check(not TimeSystem.is_day(), "10:15 PM is not day")
	check(TimeSystem.is_building_locked("mayor_hall"), "Mayor's Hall locked at 10:15 PM")
	check(TimeSystem.is_building_locked("forge"), "Forge locked at 10:15 PM")
	check(TimeSystem.is_building_locked("cottage_harrow"), "Harrow Cottage locked at 10:15 PM")
	# Salt Gull Inn is EXEMPT: stays unlocked!
	check(not TimeSystem.is_building_locked("salt_gull"), "Salt Gull Inn remains UNLOCKED at night (22:15)")

	# 6:00 AM unlock time
	TimeSystem.set_time(6, 0)
	eq(TimeSystem.get_hour(), 6, "TimeSystem sets hour to 6")
	check(TimeSystem.is_day(), "6:00 AM unlocks town (is_day=true)")
	check(not TimeSystem.is_night(), "6:00 AM is not night")
	check(not TimeSystem.is_building_locked("mayor_hall"), "Mayor's Hall unlocked at 6:00 AM")

	# The HUD clock shows whole hours
	TimeSystem.set_time(15, 45)
	eq(TimeSystem.get_time_string(), "3 PM", "clock shows the hour only")
	TimeSystem.set_time(0, 0)
	eq(TimeSystem.get_time_string(), "12 AM", "midnight reads 12 AM")
	TimeSystem.set_time(12, 0)
	eq(TimeSystem.get_night_factor(), 0.0, "no night at noon")
	TimeSystem.set_time(0, 0)
	eq(TimeSystem.get_night_factor(), 1.0, "full night at midnight")
	TimeSystem.set_time(19, 30)
	check(TimeSystem.get_night_factor() > 0.0 and TimeSystem.get_night_factor() < 1.0, "dusk eases into night")

	# Waiting skips whole hours, emitting each one and the night/day switches
	var seen_hours: Array[int] = []
	var on_hour := func(h: int) -> void: seen_hours.append(h)
	TimeSystem.hour_passed.connect(on_hour)
	TimeSystem.set_time(21, 0)
	seen_hours.clear()
	TimeSystem.wait_hours(2)
	TimeSystem.hour_passed.disconnect(on_hour)
	eq(seen_hours, [22, 23], "wait_hours emits every hour it crosses")
	check(TimeSystem.is_night(), "waiting from 9 PM for 2 hours reaches night")

	# Ambient lighting color
	TimeSystem.set_time(12, 0)
	var day_col: Color = TimeSystem.get_ambient_color()
	eq(day_col, Color(1.0, 1.0, 1.0, 1.0), "Noon ambient color is white")
	TimeSystem.set_time(1, 0)
	var night_col: Color = TimeSystem.get_ambient_color()
	check(night_col.r < 0.6 and night_col.b > night_col.r, "Night ambient color is dark blue-tinted")

	# 2. Door interactable in town
	var wm: Node = load("res://scenes/world/wrackmouth.tscn").instantiate()
	root.add_child(wm)
	await physics_frames(2)
	var door_hall: BuildingDoor = wm.get_node("Interactables/DoorMayorHall")
	var door_inn: BuildingDoor = wm.get_node("Interactables/DoorSaltGull")
	check(door_hall != null, "Wrackmouth has DoorMayorHall")
	check(door_inn != null, "Wrackmouth has DoorSaltGull")

	TimeSystem.set_time(12, 0)
	door_hall._update_state()
	door_inn._update_state()
	check(not door_hall.is_locked(), "DoorMayorHall unlocked at noon")
	eq(door_hall.prompt, "Enter Mayor's Hall", "Door prompt shows Enter at noon")

	TimeSystem.set_time(23, 0)
	door_hall._update_state()
	door_inn._update_state()
	check(door_hall.is_locked(), "DoorMayorHall locked at 11 PM")
	eq(door_hall.prompt, "Locked", "Door prompt shows Locked at night")
	check(not door_inn.is_locked(), "DoorSaltGull stays unlocked at 11 PM")
	eq(door_inn.prompt, "Enter The Salt Gull", "DoorSaltGull prompt shows Enter at night")

	wm.queue_free()
	await get_tree().process_frame

	# 3. All 7 interior scenes instantiate headless with correct structure
	var interior_paths := [
		"res://scenes/interiors/mayor_hall.tscn",
		"res://scenes/interiors/forge.tscn",
		"res://scenes/interiors/salt_gull.tscn",
		"res://scenes/interiors/lantern_watch.tscn",
		"res://scenes/interiors/cottage_harrow.tscn",
		"res://scenes/interiors/cottage_rook.tscn",
		"res://scenes/interiors/cottage_weaver.tscn",
		"res://scenes/interiors/salt_gull_room.tscn",
		"res://scenes/interiors/trader_shop.tscn",
	]
	for ipath in interior_paths:
		var scene: AreaScene = load(ipath).instantiate()
		root.add_child(scene)
		await physics_frames(2)
		check(scene != null, "%s instantiates" % ipath)
		check(not scene.is_outdoor, "%s is indoor scene (is_outdoor=false)" % ipath)
		check(scene.get_node_or_null("Spawns/from_town") is Marker2D, "%s has Spawns/from_town" % ipath)
		var exit_door: BuildingDoor = scene.get_node_or_null("Interactables/DoorExit")
		check(exit_door != null and exit_door.is_exit, "%s has exit door back to town" % ipath)
		var entities: Node2D = scene.get_node_or_null("Entities")
		if entities:
			for child in entities.get_children():
				if child is Npc:
					check(not child.display_name.is_empty(), "%s in %s has display_name" % [child.name, ipath])
					check(not child.dialogue_path.is_empty(), "%s in %s has dialogue_path" % [child.name, ipath])
					check(ResourceLoader.exists(child.dialogue_path), "%s in %s dialogue file exists" % [child.name, ipath])
		scene.queue_free()
		await get_tree().process_frame

	# 4. Court NPCs & LootContainer functionality in Mayor's Hall
	var mh: AreaScene = load("res://scenes/interiors/mayor_hall.tscn").instantiate()
	root.add_child(mh)
	await physics_frames(2)
	var p: Player = mh.get_node("Entities/Player")
	var mayor: Npc = mh.get_node("Entities/MayorTolle")
	check(mayor != null, "Mayor Tolle is inside Mayor's Hall")
	eq(mayor.display_name, "Mayor Maren Tolle", "Mayor Tolle display_name is Mayor Maren Tolle")
	eq(mayor.dialogue_path, "res://data/dialogue/mayor.json", "Mayor Tolle dialogue_path is mayor.json")
	check(ResourceLoader.exists(mayor.dialogue_path), "Mayor Tolle dialogue file exists")

	check(mh.get_node("Entities/ChancellorAlden") != null, "Chancellor Alden is inside Mayor's Hall")
	check(mh.get_node("Entities/GuardVance") != null, "Royal Guard Vance is inside Mayor's Hall")

	# Mayor Tolle is reachable from the central aisle and gives tasks
	await place(p, Vector2(170, 138))
	await hold(["move_up"], 8)
	eq(p._nearest_interactable(), mayor, "Mayor Tolle is reachable and nearest interactable from central aisle")

	# Dialogue opens and gives task to player
	var dlg: DialogueBox = mh.get_node("DialogueBox")
	check(dlg != null, "Mayor's Hall has DialogueBox")
	mayor.interact(p)
	check(dlg.is_open(), "interacting with Mayor Tolle opens DialogueBox")
	dlg._choose(0) # "I can work." -> accept node: starts giant_rat
	check(Game.state.quests.is_active("giant_rat"), "Mayor Tolle dialogue starts the giant_rat quest")
	dlg._close()
	check(not dlg.is_open(), "DialogueBox closes cleanly")

	var chest: LootContainer = mh.get_node("Interactables/MayorChest")
	check(chest != null, "Mayor's Hall has MayorChest loot container")
	check(not chest.is_looted(), "chest starts unlooted")
	eq(chest.prompt, "Search Council Strongbox", "chest prompt shows Search Council Strongbox")

	var prev_coins: int = Game.state.count("coin")
	chest.interact(p)
	check(chest.is_looted(), "interacting loots chest and sets flag")
	eq(Game.state.count("coin"), prev_coins + 18, "looting chest adds 18 coins")
	eq(chest.prompt, "", "looted chest has empty prompt")

	# Re-interacting does not add more loot
	chest.interact(p)
	eq(Game.state.count("coin"), prev_coins + 18, "looted chest cannot be re-looted")

	# 5. Entering and leaving Mayor's Hall without getting stuck
	# In Mayor's Hall, the player at the from_town marker can move freely
	await place(p, mh.get_node("Spawns/from_town").global_position)
	var hall_start := p.global_position
	await hold(["move_up"], 15)
	check(p.global_position.y < hall_start.y - 10.0, "player moves freely inside Mayor's Hall doorway")

	mh.queue_free()
	await get_tree().process_frame

	# In Wrackmouth, player at from_mayor_hall (150, 185) can move freely in all directions
	var wm_exit: Node = load("res://scenes/world/wrackmouth.tscn").instantiate()
	root.add_child(wm_exit)
	await physics_frames(2)
	var wm_p: Player = wm_exit.get_node("Entities/Player")
	var wm_marker: Marker2D = wm_exit.get_node("Spawns/from_mayor_hall")
	check(wm_marker != null, "wrackmouth has Spawns/from_mayor_hall")
	await place(wm_p, wm_marker.global_position)
	var exit_pos := wm_p.global_position
	await hold(["move_down"], 15)
	check(wm_p.global_position.y > exit_pos.y + 10.0, "player moves down after exiting Mayor's Hall")
	await place(wm_p, wm_marker.global_position)
	await hold(["move_left"], 15)
	check(wm_p.global_position.x < exit_pos.x - 10.0, "player moves left after exiting Mayor's Hall")
	await place(wm_p, wm_marker.global_position)
	await hold(["move_right"], 15)
	check(wm_p.global_position.x > exit_pos.x + 10.0, "player moves right after exiting Mayor's Hall")

	wm_exit.queue_free()
	await get_tree().process_frame


func test_schedules() -> void:
	# Data: every scheduled NPC covers 24 hours once and names real places with a matching NPC node there.
	for id: String in NpcSchedule.npc_ids():
		check(NpcSchedule.covers_whole_day(id), "%s schedule covers every hour exactly once" % id)
	eq(NpcSchedule.place_at("orsa", 12), "town", "Orsa is in the yard at noon")
	eq(NpcSchedule.place_at("orsa", 23), "forge", "Orsa sleeps at the forge (slot wraps midnight)")
	eq(NpcSchedule.place_at("orsa", 8), "forge", "Orsa is still at the forge at 8 AM")
	eq(NpcSchedule.place_at("nobody", 12), "", "unscheduled NPCs have no place")

	var town: Node = load("res://scenes/world/wrackmouth.tscn").instantiate()
	root.add_child(town)
	var interior_npcs := {}
	for id: String in NpcSchedule.npc_ids():
		var places := {}
		for hour in 24:
			places[NpcSchedule.place_at(id, hour)] = true
		for place: String in places:
			var scene: Node = town if place == "town" else load("res://scenes/interiors/%s.tscn" % place).instantiate()
			var found := false
			for npc: Node in scene.find_children("*", "Npc", true, false):
				found = found or npc.npc_id == id
			check(found, "%s has an NPC node in %s" % [id, place])
			if scene != town:
				scene.free()
	town.free()
	interior_npcs.clear()

	# Town at noon: the kids and Orsa are out, Bram is in the inn.
	TimeSystem.set_time(12, 0)
	town = load("res://scenes/world/wrackmouth.tscn").instantiate()
	root.add_child(town)
	await physics_frames(2)
	var orsa: Npc = town.get_node("Entities/OrsaKell")
	var bram: Npc = town.get_node("Entities/BramQuillon")
	var tam: Npc = town.get_node("Entities/Tam")
	check(orsa.present and tam.present, "Orsa and Tam are in town at noon")
	check(not bram.present, "Bram is inside the inn at noon")
	check(bram.collision_layer == 0 and not bram.visible, "an absent NPC is hidden and cannot be talked to")

	# Kids run: Tam covers ground and stays inside his play radius
	var start := tam.global_position
	var farthest := 0.0
	var inside := true
	for i in 900:
		tam._physics_process(1.0 / 60.0)
		farthest = maxf(farthest, tam.global_position.distance_to(start))
		inside = inside and tam.global_position.distance_to(tam.home_position) <= tam.wander_radius + 0.5
	check(farthest > 15.0, "Tam runs around (moved %.1f)" % farthest)
	check(inside, "Tam stays inside his play radius")

	# 17:00: Orsa heads for the inn (via her door), then vanishes from town
	TimeSystem.set_time(16, 0)
	TimeSystem.set_time(17, 0)
	check(orsa._travelling and orsa._travel_leaving, "Orsa starts walking away at 17:00")
	for i in 1800:
		orsa._physics_process(1.0 / 60.0)
		if not orsa.present:
			break
	check(not orsa.present, "Orsa leaves the town scene once she reaches the door")

	# 19:00: kids go home; 8 AM Bram comes out of the inn and walks to his post
	TimeSystem.set_time(18, 0)
	TimeSystem.set_time(19, 0)
	for i in 1800:
		tam._physics_process(1.0 / 60.0)
		if not tam.present:
			break
	check(not tam.present, "Tam goes home at 19:00")
	TimeSystem.set_time(7, 0)
	TimeSystem.set_time(8, 0)
	check(bram.present and bram._travelling, "Bram steps out of the inn at 8 AM")
	var door := bram.global_position
	for i in 1800:
		bram._physics_process(1.0 / 60.0)
		if not bram._travelling:
			break
	check(not bram._travelling, "Bram finishes walking to his post")
	check(bram.global_position.distance_to(bram.home_position) < 3.0, "Bram ends at his post (door was %s)" % door)
	town.free()

	# Loading an interior mid-day: occupants appear only if the schedule says so
	TimeSystem.set_time(12, 0)
	var forge: Node = load("res://scenes/interiors/forge.tscn").instantiate()
	root.add_child(forge)
	await physics_frames(2)
	check(not forge.get_node("Entities/OrsaKell").present, "Orsa is not in the forge at noon")
	TimeSystem.set_time(21, 0)
	check(forge.get_node("Entities/OrsaKell").present, "Orsa walks back into the forge at 21:00")
	forge.free()

	# Tam's quest: ask, find the whistle on the beach, return it for coin
	Game.reset()
	var runner := DialogueRunner.new()
	var tree: Dictionary = StoryData.load_json("res://data/dialogue/tam.json")
	runner.begin(tree, Game.state)
	eq(runner.node_id, "intro", "Tam opens with his problem")
	runner.advance(0)
	check(Game.state.quests.is_active("tams_whistle"), "accepting starts Tam's Whistle")
	var beach: Node = load("res://scenes/world/beach.tscn").instantiate()
	root.add_child(beach)
	await physics_frames(2)
	var whistle: Pickup = beach.get_node("Interactables/TamsWhistle")
	whistle.interact(beach.get_node("Entities/Player"))
	check(Game.state.count("bone_whistle") == 1, "the whistle is on the beach and can be taken")
	beach.free()
	runner.begin(tree, Game.state)
	eq(runner.node_id, "return", "Tam thanks the player once they hold the whistle")
	check(Game.state.count("bone_whistle") == 0 and Game.state.count("coin") == 10, "the whistle is traded for 10 coin")
	check(Game.state.quests.is_done("tams_whistle"), "Tam's Whistle is complete")
	Game.reset()
	TimeSystem.set_time(12, 0)


func test_inn_and_merchant() -> void:
	Game.reset()
	TimeSystem.set_time(12, 0)

	# Town: the shop exists, the old outdoor bed is gone
	var town: Node = load("res://scenes/world/wrackmouth.tscn").instantiate()
	root.add_child(town)
	await physics_frames(2)
	var shop_door: BuildingDoor = town.get_node("Interactables/DoorTraderShop")
	check(shop_door != null and shop_door.building_id == "trader_shop", "Wrackmouth has the trader's shop door")
	check(town.get_node_or_null("Spawns/from_trader_shop") is Marker2D, "the town has a from_trader_shop spawn")
	check(town.get_node_or_null("Interactables/InnBed") == null, "the outdoor bed is replaced by the inn room")
	shop_door._update_state()
	eq(shop_door.prompt, "Enter Venn's Goods", "the shop is open at noon")
	TimeSystem.set_time(23, 0)
	shop_door._update_state()
	eq(shop_door.prompt, "Locked", "the shop is shut at night like the houses")
	TimeSystem.set_time(12, 0)
	town.free()

	# Inn: renting the room costs 5 coin and lasts 24 hours
	var inn: Node = load("res://scenes/interiors/salt_gull.tscn").instantiate()
	root.add_child(inn)
	await physics_frames(2)
	var room_door: RoomRentalDoor = inn.get_node("Interactables/RoomDoor")
	check(inn.get_node_or_null("Spawns/from_salt_gull_room") is Marker2D, "the inn has a spawn for coming back from the room")
	room_door.target_scene = ""  # stay in this scene for the test
	eq(room_door.prompt, "Rent a room (5 coin)", "an unrented room shows its price")
	Game.state.apply(["give:coin:3"])
	room_door.interact(null)
	check(not Game.is_room_rented() and Game.state.count("coin") == 3, "too little coin: no room, no charge")
	Game.state.apply(["give:coin:10"])
	room_door.interact(null)
	check(Game.is_room_rented(), "paying rents the room")
	eq(Game.state.count("coin"), 8, "the room costs exactly 5 coin")
	eq(room_door.prompt, "Enter your room", "a rented room is entered for free")
	room_door.interact(null)
	eq(Game.state.count("coin"), 8, "re-entering a rented room is free")
	TimeSystem.wait_hours(23)
	check(Game.is_room_rented(), "the room is still yours after 23 hours")
	TimeSystem.wait_hours(1)
	check(not Game.is_room_rented(), "the rental ends after 24 hours")
	Game.state.apply(["flag:inn_free"])
	room_door.interact(null)
	eq(Game.state.count("coin"), 8, "the innkeeper's debt covers the room")
	inn.free()

	# Sleeping: any length refills vitals and grants +10% XP for eight hours after waking
	Game.reset()
	TimeSystem.set_time(22, 0)
	Game.stats.damage(60.0)
	Game.stats.use_stamina(50.0)
	eq(Game.xp_multiplier(), 1.0, "no XP bonus before sleeping")
	Game.sleep_in_bed(8)
	eq(TimeSystem.get_hour(), 6, "sleeping 8 hours from 10 PM wakes at 6 AM")
	eq(Game.stats.health, Game.stats.max_health, "sleep restores health")
	check(Game.is_well_rested(), "sleeping makes the player Well Rested")
	check(is_equal_approx(Game.xp_multiplier(), 1.1), "Well Rested gives +10% XP")
	TimeSystem.wait_hours(7)
	check(Game.is_well_rested(), "still rested after 7 hours")
	TimeSystem.wait_hours(1)
	check(not Game.is_well_rested() and Game.xp_multiplier() == 1.0, "the bonus ends after 8 hours")
	for nap: int in [1, 2, 12, 23, 24]:
		Game.reset()
		TimeSystem.set_time(12, 0)
		Game.sleep_in_bed(nap)
		check(Game.is_well_rested(), "sleeping %d hour(s) grants the bonus" % nap)
		TimeSystem.wait_hours(7)
		check(Game.is_well_rested(), "the bonus after a %d-hour sleep lasts 8 hours (7 in)" % nap)
		TimeSystem.wait_hours(1)
		check(not Game.is_well_rested(), "the bonus after a %d-hour sleep ends at 8 hours" % nap)
	# Resting by waiting (T) does not count as sleeping in a bed
	Game.reset()
	TimeSystem.wait_hours(8)
	Game.stats.restore_all()
	check(not Game.is_well_rested(), "only a bed grants Well Rested")

	# The room scene: a bed that sleeps, and an exit back into the inn
	var room: Node = load("res://scenes/interiors/salt_gull_room.tscn").instantiate()
	root.add_child(room)
	await physics_frames(2)
	var bedstead: RestSpot = room.get_node("Interactables/Bedstead")
	check(bedstead != null, "the room has a bed to sleep in")
	var room_hud: Hud = room.get_node("Hud")
	var room_player: Player = room.get_node("Entities/Player")
	TimeSystem.set_time(14, 0)
	Game.stats.damage(40.0)
	bedstead.interact(room_player)
	check(room_hud.wait_panel.is_open() and room_hud.wait_panel.sleeping, "using the bed opens the sleep menu")
	check(not room_player.input_enabled, "the sleep menu freezes the player")
	eq(room_hud.wait_panel._wait_btn.text, "Sleep", "the confirm button reads Sleep")
	room_hud.wait_panel.cancel()
	check(not Game.is_well_rested() and TimeSystem.get_hour() == 14 and room_player.input_enabled, "cancelling sleep changes nothing")
	bedstead.interact(room_player)
	room_hud.wait_panel.adjust(2)  # 3 hours
	await room_hud.wait_panel.confirm()
	eq(TimeSystem.get_hour(), 17, "sleeping 3 hours from 2 PM wakes at 5 PM")
	check(Game.is_well_rested(), "a 3-hour sleep still grants Well Rested")
	eq(Game.stats.health, Game.stats.max_health, "the sleep refilled health")
	check(room_player.input_enabled, "the player can move again after sleeping")
	check(room_hud._rested_label.text.begins_with("Well Rested"), "the HUD shows the Well Rested bonus")
	Game.reset()
	TimeSystem.set_time(12, 0)
	var back: BuildingDoor = room.get_node("Interactables/DoorExit")
	eq(back.target_scene, "res://scenes/interiors/salt_gull.tscn", "the room's door leads back into the inn")
	eq(back.prompt, "Exit to the Salt Gull", "the exit names where it leads")
	room.free()

	# The merchant's quest: ask, can't finish without the locket, pays 40 coin
	var shop: Node = load("res://scenes/interiors/trader_shop.tscn").instantiate()
	root.add_child(shop)
	await physics_frames(2)
	check(shop.get_node("Entities/OsricVenn") is Npc, "Osric Venn keeps the shop")
	shop.free()
	Game.reset()
	var tree: Dictionary = StoryData.load_json("res://data/dialogue/osric.json")
	var runner := DialogueRunner.new()
	runner.begin(tree, Game.state)
	eq(runner.node_id, "intro", "Osric opens with his grief")
	runner.advance(0) # "What happened to her?"
	eq(runner.node_id, "story", "he tells the story")
	runner.advance()
	eq(runner.node_id, "ask", "then he asks for the locket")
	runner.advance(0) # "I'll find it."
	check(Game.state.quests.is_active("elins_locket"), "accepting starts Elin's Locket")
	eq(Game.state.quests.stage_id("elins_locket"), "find", "the quest starts at the find stage")
	runner.advance()
	runner.begin(tree, Game.state)
	eq(runner.node_id, "reminder", "without the locket Osric only reminds the player")
	Game.state.apply(["give:silver_locket"])
	eq(Game.state.quests.stage_id("elins_locket"), "return", "holding the locket moves the quest on")
	runner.begin(tree, Game.state)
	eq(runner.node_id, "return", "Osric takes the locket")
	check(Game.state.count("silver_locket") == 0 and Game.state.count("coin") == 40, "the locket is traded for 40 coin")
	check(Game.state.quests.is_done("elins_locket"), "Elin's Locket is complete")

	# Weapon icons exist for the four starting weapons
	for weapon: String in ["iron_daggers", "iron_sword_shield", "two_handed_sword", "staff"]:
		check(ResourceLoader.exists("res://assets/ui/items/%s.png" % weapon), "%s has an inventory icon" % weapon)
	Game.reset()
	TimeSystem.set_time(12, 0)
