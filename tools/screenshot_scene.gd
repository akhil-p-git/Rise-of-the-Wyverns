extends SceneTree
## Renders one scene to a PNG. Run through tools/screenshot_scene.sh, which supplies the project copy.
## Args after `--`: scene path, hour of day (0-23), output PNG, optional `wait` to open the T wait menu.

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	root.get_node("TimeSystem").set_time(int(args[1]), 0)
	root.get_node("TimeSystem").paused = true
	var scene: Node = (load(args[0]) as PackedScene).instantiate()
	root.add_child(scene)
	# Nodes get their _ready (and @onready vars) on the first frame when added from _initialize.
	await process_frame
	if args.size() > 3 and args[3] == "wait":
		scene.get_node("Hud").wait_panel.open()
	await create_timer(1.5).timeout
	await process_frame
	root.get_viewport().get_texture().get_image().save_png(args[2])
	quit()
