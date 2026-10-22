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
	test_stats()
	test_settings_and_theme()
	test_audio()
	await test_character_and_menus()
	test_logic_and_data()
	await test_town_scenes()
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
	check(crate_sign != null and crate_sign.get("item") == "salvage_crate", "beach crate is salvage_crate pickup")
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
	var state := GameState.new(story)

	# Flags and derived flags
	check(not state.has_flag("rathole_1"), "flag initially unset")
	state.set_flag("rathole_1")
	check(state.has_flag("rathole_1"), "flag set")
	check(not state.has_flag("rats_cleared"), "derived flag false when partial")
	state.apply(["flag:rathole_2", "flag:rathole_3"])
	check(state.has_flag("rats_cleared"), "derived flag true when all parts hold")
	state.apply(["clear:rathole_3"])
	check(not state.has_flag("rats_cleared"), "derived flag false after clearing component")
	state.set_flag("rathole_3")

	# Items
	eq(state.count("coin"), 0, "coin starts at 0")
	state.apply(["give:coin:15"])
	eq(state.count("coin"), 15, "give adds item count")
	check(not state.take("coin", 20), "take refuses when short")
	eq(state.count("coin"), 15, "refused take leaves count intact")
	check(state.take("coin", 5), "take succeeds when enough")
	eq(state.count("coin"), 10, "take subtracts count")

	# QuestLog progression
	state.apply(["start:work_to_belong"])
	check(state.quests.is_active("work_to_belong"), "work_to_belong is active")
	eq(state.quests.stage_id("work_to_belong"), "chores", "starts at chores stage")
	check(state.objective("work_to_belong").ends_with("(1/3)"), "chores objective tracks 1/3")
	state.apply(["flag:chore_crate", "flag:chore_message"])
	eq(state.quests.stage_id("work_to_belong"), "cairns", "advances to cairns stage")
	state.apply(["give:moonherb:3", "flag:saw_grave"])
	eq(state.quests.stage_id("work_to_belong"), "report", "advances to report stage")
	state.apply(["flag:reported_mayor"])
	eq(state.quests.stage_id("work_to_belong"), "road", "advances to road stage")
	state.apply(["flag:reached_crossholm"])
	check(state.quests.is_done("work_to_belong"), "work_to_belong completes")

	# DialogueRunner
	var mayor_tree := StoryData.load_json("res://data/dialogue/mayor.json")
	var fresh_state := GameState.new(story)
	var runner := DialogueRunner.new()
	check(runner.begin(mayor_tree, fresh_state), "mayor dialogue begins on fresh state")
	eq(runner.node_id, "first", "fresh state enters 'first' node")
	eq(runner.choices().size(), 3, "first node offers 3 choices")
	runner.advance(0) # "I can work." -> "accept"
	eq(runner.node_id, "accept", "choice 0 advances to accept")
	check(fresh_state.quests.is_active("work_to_belong"), "accept node starts work_to_belong")
	eq(fresh_state.count("mayor_letter"), 1, "accept node gives mayor_letter")
	runner.advance()
	eq(runner.node_id, "accept_end", "advances to accept_end")
	runner.advance()
	check(runner.finished, "dialogue finishes after accept_end")

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

	var dialogue_files := ["ansa", "bram", "dov", "mayor", "orsa", "pell", "teague", "wren"]
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
	var mayor: Npc = wm.get_node("Entities/MayorTolle")
	var orsa: Npc = wm.get_node("Entities/OrsaKell")
	var teague: Npc = wm.get_node("Entities/TeagueMarrow")
	var wren: Npc = wm.get_node("Entities/Wren")
	var player: Player = wm.get_node("Entities/Player")
	check(mayor.sprite_sheet != null, "MayorTolle has custom NPC sprite sheet")

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
	var mayor_stayed_put := true
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
		if mayor.global_position.distance_to(mayor.home_position) > 0.001:
			mayor_stayed_put = false
		if teague.global_position.distance_to(teague.waypoints[0]) <= 2.0:
			reached_wp0 = true
		if teague.global_position.distance_to(teague.waypoints[1]) <= 2.0:
			reached_wp1 = true

	var avg_ms := float(total_usec) / 3000.0 / 1000.0
	print("NPC physics benchmark (7 NPCs in Wrackmouth): %.4f ms/frame" % avg_ms)
	check(avg_ms < 0.2, "all Wrackmouth NPCs under 0.2 ms/frame (got %.4f ms)" % avg_ms)
	check(stayed_in_radius, "wander NPC stays inside wander_radius over 3000 frames")
	check(never_overlapped_wall, "wander NPC never overlaps a wall over 3000 frames")
	check(mayor_stayed_put, "stationary NPC does not move over 3000 frames")
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
