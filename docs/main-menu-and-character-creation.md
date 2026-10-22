# Main Menu and Character Creation

Status: decided 2026-10-22 (linked from `docs/lore.md`).

## Flow

`Main Menu` (`scenes/menu/main_menu.tscn`) -> `New Game` -> `Character Creation` (`scenes/menu/character_creation.tscn`) -> `Intro Cutscene` (`scenes/intro/intro.tscn`) -> `Starting Beach` (`scenes/world/beach.tscn`).

Running `intro.tscn` or `beach.tscn` directly from the editor still works using a default `Character` instance on `Game.character`.

## Main Menu Spec

- **Title**: `"Rise of the Wyverns"` rendered as styled text using `assets/ui/grim_theme.tres` (final logo to be commissioned before commercial release).
- **Buttons**:
  - `Continue` — stays hidden (`visible = false`) until the save/load system exists.
  - `New Game` — transitions to `scenes/menu/character_creation.tscn`.
  - `Settings` — opens the Settings panel (Windowed / Fullscreen toggle and VSync toggle persisted in `user://settings.cfg`, plus audio bus volume sliders for Master, Music, SFX, Ambience, and UI when the audio system is active).
  - `Credits` — opens the Credits panel (`data/credits.json`).
  - `Quit` — exits the game (`get_tree().quit()`).
- **Navigation**: Full keyboard (Up/Down/W/S, Enter/Space), mouse, and gamepad navigation with visible focus states; `Esc` / `Back` closes sub-panels or returns to the previous step.

### Main Menu Layout (ASCII)

```text
+--------------------------------------------------------------------------+
|                                                                          |
|                         RISE OF THE WYVERNS                              |
|                     Ash and Salt on the Coast of Vessary                 |
|                                                                          |
|                            +----------------+                            |
|                            |    New Game    |                            |
|                            +----------------+                            |
|                            |    Settings    |                            |
|                            +----------------+                            |
|                            |    Credits     |                            |
|                            +----------------+                            |
|                            |      Quit      |                            |
|                            +----------------+                            |
|                                                                          |
|  [Settings Overlay when open:]                                           |
|  +--------------------------------------------------------------------+  |
|  |  SETTINGS                                                          |  |
|  |  Display Mode:   [ Windowed / Fullscreen ]                         |  |
|  |  Vertical Sync:  [ Enabled / Disabled ]                            |  |
|  |  Master / Music / SFX / Ambience / UI Volume Sliders               |  |
|  |                                                           [ Back ] |  |
|  +--------------------------------------------------------------------+  |
+--------------------------------------------------------------------------+
```

## Character Creation Spec

Ordered steps (`0..4`), with a persistent live hero preview on the left and step controls on the right. The player can go `Back` to any prior step (or back to the Main Menu from Step 0).

1. **Step 1 — Appearance**:
   - Live animated preview of `assets/hero/hero_sheet.png` walking at 6 FPS and turning through all 4 facing directions (Down, Left, Up, Right).
   - Recoloured via `shaders/character_palette.gdshader` without altering dark outlines (`max(r,g,b) < 0.19`), eyes, or leather boots:
     - **Skin Tone** (5 options): Pale Salt, Weathered Fair, Warm Ochre, Sun-Bronzed, Deep Umber.
     - **Hair Colour** (6 options): Dark Umber, Raven Black, Ash Blonde, Rust Auburn, Iron Grey, Bleached Bone.
     - **Clothing Colour** (5 options): Convict Slate, Salt Marsh Moss, Dried Blood, Deep Indigo, Tarnished Ochre.
   - Includes a `Randomise` button.
2. **Step 2 — Pronouns**:
   - Options: `she/her`, `he/him`, `they/them`.
   - Provides text tokens resolved in `DialogueRunner.text()` and `Hud.show_message()`:
     - `{they}`, `{them}`, `{their}`, `{theirs}`, `{themself}`
     - Verb-agreement helpers `{is_are}` (`is`/`is`/`are`), `{was_were}` (`was`/`was`/`were`), `{has_have}` (`has`/`has`/`have`), `{s}` (`s`/`s`/`""`), `{es}` (`es`/`es`/`""`).
     - Capitalised tokens (`{They}`, `{Them}`, `{Their}`, `{Theirs}`, `{Themself}`, `{Is_are}`, `{Was_were}`, `{Has_have}`) automatically capitalise at the start of a sentence or when written with an initial capital.
3. **Step 3 — Difficulty**:
   - Options stored as data with a damage-taken multiplier exposed via `Game.difficulty_damage_scale()`:
     - `Easy` (`0.75x` damage taken)
     - `Normal` (`1.0x` damage taken)
     - `Hard` (`1.5x` damage taken)
4. **Step 4 — Hardcore (Optional)**:
   - Toggle (`Off` / `On`) with the explicit warning: `"Death ends this life for good."`
   - Stored as `Character.hardcore: bool`; the permadeath save-deletion hook waits until the save/load system lands.
5. **Step 5 — Confirm Summary**:
   - Displays the chosen appearance names, pronouns, difficulty, and Hardcore state alongside the live walking preview.
   - `Begin` starts the game (`Game.reset()` while keeping `Game.character`, then transitions to `res://scenes/intro/intro.tscn`).

- **Convictions**: Cut. Every character starts with identical skill values; there is no conviction picker.
- **Name Field**: Omitted per default spec (open question for Akhil: should the player have a name?).

### Character Creation Layout (ASCII)

```text
+--------------------------------------------------------------------------+
|  THE SURVIVOR                                      Step N of 5: <Title>  |
|  +------------------------+  +----------------------------------------+  |
|  |                        |  |  [Step 1: Appearance]                  |  |
|  |     +------------+     |  |  Skin Tone:  [<] Weathered Fair   [>]  |  |
|  |     |            |     |  |  Hair:       [<] Dark Umber       [>]  |  |
|  |     |   [HERO]   |     |  |  Tunic:      [<] Convict Slate    [>]  |  |
|  |     |  (walking  |     |  |  [ Randomise ]                         |  |
|  |     |  & turning)|     |  |                                        |  |
|  |     +------------+     |  |  [Step 2: Pronouns]                    |  |
|  |                        |  |  ( ) she/her  ( ) he/him  (*) they/them|  |
|  |   Facing: South/West/  |  |                                        |  |
|  |           North/East   |  |  [Step 3: Difficulty]                  |  |
|  |                        |  |  ( ) Easy     (*) Normal  ( ) Hard     |  |
|  |                        |  |                                        |  |
|  |                        |  |  [Step 4: Hardcore]                    |  |
|  |                        |  |  [ ] Hardcore Mode                     |  |
|  |                        |  |  "Death ends this life for good."      |  |
|  |                        |  |                                        |  |
|  |                        |  |  [Step 5: Confirm]                     |  |
|  |                        |  |  Summary of choices                    |  |
|  +------------------------+  +----------------------------------------+  |
|  [ Back (Esc) ]                                       [ Next / Begin ]   |
+--------------------------------------------------------------------------+
```
