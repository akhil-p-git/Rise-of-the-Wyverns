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
	test_logic_and_data()
	await test_town_scenes()
	await test_room()
	await test_beach()
	await test_intro()
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
	check(wm.get_node("Entities/MayorTolle").sprite_sheet != null, "MayorTolle has custom NPC sprite sheet")
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
