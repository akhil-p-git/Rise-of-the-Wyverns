# Rise of the Wyverns

Original 2D top-down fantasy RPG in Godot 4.7 (GDScript), meant to be sold. Game title: Rise of the Wyverns (chosen 2026-10-20; the repo folder is still `new-country-rpg`). Design notes and plan: `~/.claude/plans/well-i-d-like-to-curried-scone.md`. Never reuse Skyrim names, lore or assets.

## Commands
- Run the tests: `tools/run_tests.sh` (copies the project to a temp dir, imports it, runs `tests/run_tests.gd` headless with `--fixed-fps 60`; exit code 1 on any failure). Safe while the editor has the project open.
- The main scene is the opening cutscene `scenes/intro/intro.tscn` (scripted with tweens in `scripts/intro/intro.gd`, Space, Enter or Escape skips after 1.5 s); it hands off to the starting beach, `scenes/world/beach.tscn`, with `play_arrival = true` (fade in, reduced speed for a few seconds). Open `beach.tscn` directly to skip the intro (320x180 art grid, shown through a 2x camera zoom in a 640x360 window). All art is authored at 4x texture density (1 game pixel = 4x4 texture pixels, sprites at `scale = 0.25`); see `docs/DESIGN_SPEC.md` for sheet and ground sizes.
- Hero sheet from 12 source views: `uv run --no-project --with pillow --with numpy python tools/build_hero_sheet.py --src-dir DIR --out assets/hero/hero_sheet.png` (see the script's docstring for file names). Reference-image edits in FLUX keep a character consistent across directions and walk frames.
- Controls in the test room: WASD or arrows to move, Shift to sprint, E to interact. Input actions live in `project.godot`; add new ones through the editor or the `execute_editor_script` tool, not by hand-editing the file while the editor is open.
- Screenshot a scene at an hour of day (the editor API's screenshot routes only capture the editor window): `tools/screenshot_scene.sh res://scenes/world/wrackmouth.tscn 23 out.png [wait]`. Runs on a temp copy of the project, needs a display.
- Import and check the project headless: `godot --headless --path . --import --quit` (do not run while the editor has the project open; it shares `.godot/`).
- Regenerate placeholder art: `uv run --no-project --with pillow --with numpy python tools/gen_test_art.py`.
- Turn a large image into pixel art: `uv run --no-project --with pillow --with numpy python tools/pixelize.py in.png out.png --width 48 --colors 12 --remove-bg 120 --preview 8`.
- Local image model (outside this repo): `cd ~/work/Dev/tools/imgen && uv run python generate.py "<prompt>" --out out/x.png --size 512` (FLUX.2 klein 4B, layer-by-layer offload; about 15 s at 512px on the RTX 4060, 8 GB).

## Driving the open Godot editor
The addon in `addons/godot_mcp_enhanced` serves JSON over `POST http://127.0.0.1:3571/api/...` (for example `/api/project/info`, `/api/scene/open`, `/api/node/add`, `/api/editor/screenshot` returning a base64 PNG, `/api/qa/reimport_all`, `/api/editor/execute_script` with `{"code": "..."}`). Read `addons/godot_mcp_enhanced/plugin.gd` for the route list and parameter names. The `godot-mcp` MCP server is registered but its tools did not load into Claude Code sessions started before it was added; restart the session to use them.

## Rules
- Story, world, factions, skills and character creation are decided in `docs/lore.md`; follow it and do not invent lore it marks (open). The third resource bar is `mana` (never "Magicka").
- Raw Gemini images live in `assets/source/gemini/{hero,intro,beach,creatures,ui}` (JPEG, ignored by Godot). Build game assets from them with `tools/pixelize.py` and `tools/build_hero_sheet.py` (its input names match `hero/`) (31 raw files, about 45 MB, git-ignored on purpose: keep a copy outside the repo).
- Every asset goes in `ASSETS.md` with source and license before use.
- AI-generated art is concept or placeholder only; it may not be copyrightable and Steam requires disclosure.
- Editor-only addons are removed from exports.
