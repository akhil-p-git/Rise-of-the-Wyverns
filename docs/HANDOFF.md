# Handoff: Rise of the Wyverns (as of 2026-10-22)

Original 2D top-down fantasy RPG in Godot 4.7.2 (GDScript, GL Compatibility), meant to be sold. Skyrim-inspired but must stay original: no Bethesda names, lore or assets. Read `CLAUDE.md` (commands, rules), `docs/lore.md` (decided story and systems), `docs/main-menu-and-character-creation.md`, `docs/audio-shortlist.md`, `ASSETS.md` (asset ledger), `docs/ai-art-licensing.md` and `docs/gemini-sprite-prompts.md`.

## How to run and verify

- Game: open the project in Godot 4.7; main scene is `scenes/menu/main_menu.tscn` (`Main Menu -> New Game -> Character Creation -> Intro Cutscene -> Starting Beach`).
- Tests: `tools/run_tests.sh` (headless copy of the project; runs `res://tests/run_tests.tscn` so autoloads exist and fails non-zero on any compile/script error or test failure). Currently **365 passed, 0 failed**.
- Python tools: `uvx ruff check tools/ && uvx ruff format --check tools/`.
- The Godot editor can be driven over HTTP on 127.0.0.1:3571 (addon `addons/godot_mcp_enhanced`, routes in its `plugin.gd`). Do not hand-edit `project.godot` while the editor is open.

## Done and checked

- **Multi-resolution display & Grim UI Theme**:
  - `project.godot` uses `stretch/mode="canvas_items"` and `stretch/aspect="keep"` with a `640x360` base (`1280x720` default window override) and near-black letterbox/pillarbox bars (`Color(0.04, 0.035, 0.055, 1)`), preserving 160 Hz physics interpolation and native-resolution vector UI text.
  - Fullscreen/windowed (`F11` / `Alt+Enter` or Settings menu) and VSync toggles persist in `user://settings.cfg`.
  - `assets/ui/grim_theme.tres` + `scripts/ui/grim_palette.gd` using `assets/ui/NotoSerifDisplay-Medium.ttf` (`SIL Open Font License 1.1` in `assets/ui/OFL.txt`).
- **Main Menu & Character Creation**:
  - `scenes/menu/main_menu.tscn` (`scripts/menu/main_menu.gd`) and `scenes/menu/character_creation.tscn` (`scripts/menu/character_creation.gd`).
  - `scripts/game/character.gd` + `shaders/character_palette.gdshader` on `assets/hero/hero_sheet.png` (5 skin tones, 6 hair colours, 5 tunic colours, randomise button, pronoun token substitution `{they}`/`{them}`/`{their}`/`{theirs}`/`{themself}`, difficulty damage multiplier via `Game.difficulty_damage_scale()`, and optional Hardcore flag).
- **Audio System & Procedural Cues**:
  - `scripts/game/audio.gd` (`Audio` autoload) with 5 buses (`Master`, `Music`, `SFX`, `Ambience`, `UI`), `data/audio.json`, `data/credits.json`, `docs/audio-shortlist.md`, and `tools/gen_sfx.py` generating 23 normalized cues under `assets/audio/{music,ambience,sfx}`.
- **Living NPCs**:
  - `scripts/npc.gd` and `tools/gen_town_scenes.py` supporting `stationary`, `wander`, and `pace` behaviours, subtle grim-toned standing fidgets, obstacle/radius avoidance, and pausing during dialogue (`0.0055 ms/frame` for all 7 Wrackmouth NPCs).

## Status of prior known issues

1. **Test harness broken by autoload (`FIXED`)**: `tools/run_tests.sh:21-38` runs `res://tests/run_tests.tscn` (`tests/run_tests.gd:1`, `extends Node`) so `Game` and `Audio` autoloads register before script compilation, and fails non-zero on any `SCRIPT ERROR`, `Failed to load`, `Parse Error`, or `Compile Error`.
2. **Beach not connected to town (`FIXED`)**:
   - South exit to `res://scenes/world/wrackmouth.tscn` (`target_spawn = "from_beach"`): `scenes/world/beach.tscn:243-250`.
   - `Spawns/from_town` marker: `scenes/world/beach.tscn:256-257` and `scripts/world/beach.gd:26-30`.
   - Crate pickup (`salvage_crate`, requires `started:work_to_belong`): `scenes/world/beach.tscn:178-189`.
   - Three `iron_scrap` pickups: `scenes/world/beach.tscn:193-240`.
   - Wyvern skeleton hidden when `saw_grave` is set: `scripts/world/beach.gd:31-35`.
3. **Chore 2 (clear rats) and Chore 4 spell lesson (`STILL OPEN`)**: Chore 2 uses three rat holes (`tools/gen_town_scenes.py:582-593`, `data/story.json:12`) because combat is not yet implemented; Chore 4's spell lesson (`docs/lore.md:70`) awaits the magic system.
4. **Unit tests for `GameState`, `QuestLog`, `DialogueRunner` and JSON cross-references (`FIXED`)**: Implemented in `tests/run_tests.gd:336-475` (`test_logic_and_data()`).
5. **Town gray-box art & 4-legged wyvern skeleton (`FIXED`)**:
   - Wyvern skeleton regenerated with two hind legs and bat-like wing-arms (`assets/beach/wyvern_skeleton.png`, `tools/build_all_art.py:92-99`).
   - Town grounds, 12 buildings/structures, 9 environmental props, hero and 8 NPC sprite sheets generated and hooked up via `scripts/world/building.gd:9`, `scripts/npc.gd:14`, and `tools/gen_town_scenes.py`.
   - UI panels use `StyleBoxFlat` in `assets/ui/grim_theme.tres` instead of `assets/source/gemini/ui`.
6. **Placeholder NPC and inn names (`STILL OPEN`)**: Maren Tolle, Orsa Kell, Bram Quillon, Teague Marrow, Pell Harrow, Ansa Rook, Wren, Dov Carrow, and The Salt Gull (`data/dialogue/*.json`, `tools/gen_town_scenes.py:455-527`) still need final review/trademark check.

## Constraints to keep

- Original IP: avoid Elder Scrolls words (see the guardrail table in `docs/lore.md`).
- Gemini output: Google claims no ownership and gives no explicit commercial grant or indemnity; Steam requires AI disclosure; pure AI output may not be copyrightable. Commission hero, logo and key art before a paid release. Log every asset in `ASSETS.md`.
- Do not decide the lore items marked `(open)` in `docs/lore.md` without asking.
