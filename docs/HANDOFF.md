# Handoff: Rise of the Wyverns (as of 2026-10-21)

Original 2D top-down fantasy RPG in Godot 4.7.2 (GDScript, GL Compatibility), meant to be sold. Skyrim-inspired but must stay original: no Bethesda names, lore or assets. Read `CLAUDE.md` (commands, rules), `docs/lore.md` (decided story and systems), `ASSETS.md` (asset ledger), `docs/ai-art-licensing.md` and `docs/gemini-sprite-prompts.md`.

## How to run and verify

- Game: open the project in Godot 4.7; main scene is `scenes/intro/intro.tscn` (shipwreck cutscene, then the beach).
- Tests: `tools/run_tests.sh` (headless copy of the project; runs `res://tests/run_tests.tscn` so autoloads exist and fails non-zero on any compile/script error or test failure). Currently **251 passed, 0 failed**.
- Python tools: `uvx ruff check tools/ && uvx ruff format --check tools/`.
- The Godot editor can be driven over HTTP on 127.0.0.1:3571 (addon `addons/godot_mcp_enhanced`, routes in its `plugin.gd`). Do not hand-edit `project.godot` while the editor is open.

## Done and checked

- Movement (acceleration, speed-driven animation, physics interpolation for a 160 Hz display), animated water shader, shipwreck intro, starting beach, Wrackmouth village, and Crossholm road with 16-bit dark-fantasy pixel art (`tools/build_all_art.py`), readable HUD text.
- Mana replaces "Magicka" everywhere (`scripts/stats.gd:26`, `scenes/ui/hud.tscn`, `tests/run_tests.gd:67`).
- Full story logic and first town verified:
  - `scripts/game/`: `game_state.gd`, `quest_log.gd`, `dialogue_runner.gd`, `story_data.gd`, `game.gd` (autoload `Game`).
  - `data/story.json` and `data/dialogue/*.json` for eight NPCs (`mayor`, `orsa`, `bram`, `teague`, `pell`, `ansa`, `wren`, `dov`), cross-referenced in `tests/run_tests.gd:261-318`.
  - `scenes/world/beach.tscn`, `scenes/world/wrackmouth.tscn` and `scenes/world/crossholm_road.tscn` connected end-to-end.

## Status of prior known issues

1. **Test harness broken by autoload (`FIXED`)**: `tools/run_tests.sh:21-35` now runs `res://tests/run_tests.tscn` (`tests/run_tests.gd:1`, `extends Node`) so the `Game` autoload (`project.godot:19`) registers before script compilation, and checks both import and run logs for `SCRIPT ERROR`, `Failed to load`, `Parse Error`, and `Compile Error`.
2. **Beach not connected to town (`FIXED`)**:
   - South exit to `res://scenes/world/wrackmouth.tscn` (`target_spawn = "from_beach"`): `scenes/world/beach.tscn:243-250`.
   - `Spawns/from_town` marker: `scenes/world/beach.tscn:256-257` and `scripts/world/beach.gd:23-27`.
   - Crate pickup (`salvage_crate`, requires `started:work_to_belong`): `scenes/world/beach.tscn:178-189`.
   - Three `iron_scrap` pickups: `scenes/world/beach.tscn:193-240`.
   - Wyvern skeleton hidden when `saw_grave` is set: `scripts/world/beach.gd:28-32`.
3. **Chore 2 (clear rats) and Chore 4 spell lesson (`STILL OPEN`)**: Chore 2 uses three rat holes (`tools/gen_town_scenes.py:213-223`, `data/story.json:12`) because combat is not yet implemented; Chore 4's spell lesson (`docs/lore.md:70`) awaits the magic system.
4. **Unit tests for `GameState`, `QuestLog`, `DialogueRunner` and JSON cross-references (`FIXED`)**: Implemented in `tests/run_tests.gd:206-346` (`test_logic_and_data()`).
5. **Town gray-box art & 4-legged wyvern skeleton (`FIXED`, UI frames still open)**:
   - Wyvern skeleton regenerated with two hind legs and bat-like wing-arms (`assets/beach/wyvern_skeleton.png`, `tools/build_all_art.py:92-99`).
   - Town grounds, 12 buildings/structures, 9 environmental props, hero and 8 NPC sprite sheets generated and hooked up via `scripts/world/building.gd:9`, `scripts/npc.gd:13`, and `tools/gen_town_scenes.py`.
   - `assets/source/gemini/ui` frames still have baked-in checkerboards and are unused.
6. **Placeholder NPC and inn names (`STILL OPEN`)**: Maren Tolle, Orsa Kell, Bram Quillon, Teague Marrow, Pell Harrow, Ansa Rook, Wren, Dov Carrow, and The Salt Gull (`data/dialogue/*.json`, `tools/gen_town_scenes.py:181-208`) still need final review/trademark check.

## Constraints to keep

- Original IP: avoid Elder Scrolls words (see the guardrail table in `docs/lore.md`).
- Gemini output: Google claims no ownership and gives no explicit commercial grant or indemnity; Steam requires AI disclosure; pure AI output may not be copyrightable. Commission hero, logo and key art before a paid release. Log every asset in `ASSETS.md`.
- Do not decide the lore items marked `(open)` in `docs/lore.md` without asking.
