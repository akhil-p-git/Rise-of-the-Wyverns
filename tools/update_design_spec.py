"""Automatically generates and updates `docs/DESIGN_SPEC.md` and verifies `ASSETS.md`
by scanning live assets, sprite sheets, modular building parts, terrain tiles, UI item
icons, and scene configurations in the project.

Invoked automatically by `tools/build_all_art.py` and `tools/gen_town_scenes.py`.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def _scan_pngs(rel_dir: str) -> list[tuple[str, int, int]]:
    d = ROOT / rel_dir
    if not d.exists():
        return []
    out: list[tuple[str, int, int]] = []
    for p in sorted(d.rglob("*.png")):
        try:
            with Image.open(p) as im:
                w, h = im.size
            out.append((p.relative_to(ROOT).as_posix(), w, h))
        except OSError as exc:
            print(f"skipped {p}: {exc}")
    return out


def update_design_spec() -> None:
    categories = [
        ("Hero & Combat Sheets", "assets/hero"),
        ("NPC Sprite Sheets", "assets/npc"),
        ("Modular Building Parts & Smoke/Glow", "assets/buildings"),
        ("Interior Floors, Walls & Furniture", "assets/interiors"),
        ("Seamless 4x Terrain Tiles", "assets/terrain"),
        ("Wrackmouth Ground & Buildings", "assets/wrackmouth"),
        ("Crossholm Road Ground & Structures", "assets/crossholm_road"),
        ("Beach Ground & Props", "assets/beach"),
        ("World, Cemetery & Quest Props", "assets/props"),
        ("Inventory Item Icons", "assets/ui/items"),
    ]

    table_sections: list[str] = []
    total_pngs = 0
    for title, folder in categories:
        rows = _scan_pngs(folder)
        total_pngs += len(rows)
        lines = [
            f"### {title} (`{folder}/` — {len(rows)} assets)",
            "",
            "| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |",
            "| --- | --- | --- |",
        ]
        for rel, w, h in rows:
            lines.append(f"| `{rel}` | `{w}×{h}` px | `{w / 4.0:g}×{h / 4.0:g}` wu |")
        lines.append("")
        table_sections.append("\n".join(lines))

    spec_md = f"""# Rise of the Wyverns — Visual, Audio & Gameplay Design Specification

> **Auto-Updated Specification**: This document is automatically maintained by `tools/update_design_spec.py` whenever `tools/build_all_art.py` or `tools/gen_town_scenes.py` runs. Follow all principles below for every new area, character, prop, UI screen, and combat mechanic.

---

## 1. Resolution & 4× Native Pixel-Grid Architecture
- **Base Viewport & Camera**:
  - Viewport size (`project.godot`): `640×360` (`window/stretch/mode = "canvas_items"`, `default_texture_filter = 0` Nearest).
  - Player `Camera2D` uses `zoom = Vector2(2, 2)`, displaying a **`320×180` world-unit (`wu`) region** across the entire screen (`1280×720` windowed = `4 screen pixels per 1 world unit`; `1920×1080` fullscreen = `6 screen pixels per 1 world unit`).
- **Universal 4× Texture Density (`1 wu = 4×4 texture pixels`, `scale = Vector2(0.25, 0.25)`)**:
  - **Every character, NPC, building, prop, and ground map** MUST be authored and saved at **4× world density** and rendered at `scale = Vector2(0.25, 0.25)` so `1 texture pixel = 1 screen pixel` at 720p with zero Lanczos/bilinear blur and zero blocky `1×->4×` nearest-neighbor stretching.
  - **Ground Maps**:
    - `Beach` (`320×180` wu): `1280×720` px (`assets/beach/ground.png`).
    - `Wrackmouth` (`640×420` wu): `2560×1680` px (`assets/wrackmouth/ground.png`).
    - `Crossholm Road` (`640×360` wu): `2560×1440` px (`assets/crossholm_road/ground.png`).
  - **Never cut out low-res source landmarks onto ground maps**: All terrain (grass, organic Voronoi cobblestones, ornate plaza rings, and polygonal road rubble) is synthesized at native `1px` texel scale from `assets/terrain/`, and all gravestones, cairns, rat holes, and herbs are placed as native 4× prop sprites.

---

## 2. Character & NPC Walk-Cycle Stabilization Rules
- **Sprite Sheet Grid**: `384×512` px (`4 columns × 4 rows`, `96×128` px per cell, rendered at `scale = Vector2(0.25, 0.25)` = `24×32` wu).
  - Row `0`: Down | Row `1`: Up | Row `2`: Left | Row `3`: Right.
  - Col `0`: Idle | Col `1`: Stride A | Col `2`: Idle | Col `3`: Stride B.
- **Zero Vertical Bobbing & Zero Ankle Sway**:
  - `STEP_BOB := 0.0` in both `scripts/player/player.gd` and `scripts/npc.gd`.
  - **Head, Hair & Upper Torso (`y = 0..202` in `256×256` source space)** are 100% locked to the centered `Idle` frame across all 4 columns so characters never rock or sway while walking.
  - **Front/Back Walk (`Row 0, 1`)**: Split lower legs at the centerline (`x = 128`) and lift alternating boots purely vertically (`dy = -10`, **`dx = 0`**) so ankles never sway left and right.
  - **Side Walk (`Row 2, 3`)**: Never `FLIP_LEFT_RIGHT` a side-facing boot! Both boots always point in the direction of travel and scissor forward/back by `±8px` under the hips.

---

## 3. Modular Buildings, Moving Chimney Smoke & Soft Window Glow
- **Modular Building Parts (`assets/buildings/parts/`)**:
  - Reusable 4× components (`chimney_stone.png`, `window_amber.png`, `window_dormer.png`, `door_timber.png`) are combined to construct village houses (`cottage_harrow.png`, `cottage_rook.png`, `cottage_weaver.png`, `cottage_shuttered.png`, `mayor_hall.png`, `forge.png`, `salt_gull.png`).
- **Animated Chimney Smoke (`chimney_smoke_sheet.png`)**:
  - Static painted smoke wisps are stripped from roof PNGs. Instead, `Building` (`scripts/world/building.gd`) spawns a 6-frame animated smoke sprite (`hframes = 6`) at each `@export var chimney_offsets` point that curls upward and sways gently.
- **Soft, Warm Additive Window & Hearth Glow (`window_glow.png`, `fire_glow.png`)**:
  - Lit windows (`window_offsets` on `Building`) and the central fireplace (`AnimatedProp` on `PlazaCampfire` using 4-frame `campfire_lit_sheet.png`) attach additive (`CanvasItemMaterial.BLEND_MODE_ADD`) radial amber glow sprites that softly pulse in brightness.
- **Realistic Prop & Foundation Collisions**:
  - Every freestanding prop (`PlazaCampfire`, `PlazaSignpost`, `RoadSignpost`, `DeadTree*`, `CairnHeadstone*`, `CairnPile`, `Driftwood`, `CampfireUnlit`) is a `StaticBody2D` under `Entities` (`y_sort_enabled = true`) with a base-level `CollisionShape2D` so players and NPCs collide realistically with post/stone bases while Y-sorting behind upper flames, signs, and branches.
  - Wall-mounted or foundation-level interactables (such as `RatHole1..3`) are placed along building foundation bases, never overlapping upper roof shingles.

---

## 4. Unarmed Brawler Combat & Thematic Satchel Inventory
- **Combat Controls & Stamina (`scripts/player/player.gd`)**:
  - **Normal Attack (`Left Click` tap `< 0.28s`)**: Quick jab using `assets/hero/hero_punch_sheet.png` (`col 0 -> 1`), zero stamina cost.
  - **Power Attack (`Hold Left Click >= 0.28s`)**: Coils in wind-up stance (`col 2`) and unleashes a lunging haymaker (`col 3`) with a golden shockwave arc, spending `POWER_ATTACK_STAMINA := 20.0` via `stats.use_stamina()` (falls back to normal jab if winded).
  - **Blocking (`Hold Right Click`)**: Switches to `assets/hero/hero_block_sheet.png` showing **both wrapped forearms and fists raised in a 2-hands-up high guard** in all 4 directions, scaling movement speed by `BLOCK_SPEED_SCALE := 0.45`.
  - Both combat sheets preserve full compatibility with `shaders/character_palette.gdshader`.
- **Salt-Stained Satchel Inventory (`scenes/ui/inventory_panel.tscn`, `scripts/ui/inventory_panel.gd`)**:
  - Toggled via `I` or `Tab`. Displays customized character portrait, combat stance summary, live coin purse, and `64×64` pixel-art icons (`assets/ui/items/<id>.png`) with lore descriptions for all carried items.

---

## 5. Day/Night Cycle, House Interiors & Persistent Loot
- **Day/Night Cycle & Locking Rules (`scripts/game/time_system.gd`)**:
  - Global `TimeSystem` tracks a 24-hour clock. `10:00 PM (22:00)` to `6:00 AM (06:00)` is night.
  - Outdoor scenes feature smooth `CanvasModulate` transitions (crisp daylight, amber sunset, deep Nordic blue-tinted night).
  - All town houses lock after 10:00 PM, changing door prompts to `"Locked"` with nighttime lore dialogue.
  - **The Inn (`The Salt Gull`) is EXEMPT**: remains unlocked and welcoming 24/7.
  - All buildings unlock at 6:00 AM.
  - Abandoned / shuttered cottage remains permanently nailed shut.
- **House Interiors (`scenes/interiors/*.tscn`, `scripts/world/area_scene.gd`)**:
  - Full walkable interiors for all 8 town buildings (Mayor\'s Hall, Kell\'s Forge, The Salt Gull, Lantern Watch Tower, Harrow Cottage, Rook Cottage, Weaver Cottage, Venn\'s Goods) plus the Salt Gull\'s rentable room.
  - Warm indoor lighting (`WarmIndoorLight`), crackling hearth ambience (`amb_fire`), timber/stone floors, and furniture.
  - Doorways lead seamlessly back outside to Wrackmouth in front of each respective house via `Spawns/from_<building_id>`.
- **Persistent Loot Containers (`scripts/world/loot_container.gd`)**:
  - Chests, cupboards, tool bins, and larders provide lore items, salvage, and coin.
  - Container states persist via story flags (`looted_<id>`), preventing duplicate looting.
- **Inn room and sleep (`scripts/world/room_rental_door.gd`, `scripts/rest_spot.gd`, `Game.sleep_in_bed`)**: the door in the Salt Gull costs 5 coin and rents the room for 24 game hours (`TimeSystem.elapsed_minutes` is the absolute clock; the innkeeper\'s debt flag `inn_free` waives it). Using the room\'s bed opens the same hour picker as `T` in sleep mode (1 to 24 hours): any length passes that time, refills every vital and grants Well Rested for 8 hours after waking, so `Game.xp_multiplier()` is 1.1 while it lasts. Every future XP award must multiply by `Game.xp_multiplier()`. Waiting with `T` never grants Well Rested.
- **Merchant (`trader_shop`)**: Osric Venn keeps Venn\'s Goods and gives the side quest Elin\'s Locket. Buying and selling are not built yet.
- **Waiting (`T`, `scripts/ui/wait_panel.gd`)**: pick 1 to 24 hours; `TimeSystem.wait_hours` advances the clock hour by hour (doors and schedules react on each hour) and `Stats.restore_all` refills health, stamina and mana. The HUD clock shows the hour only and refreshes on `hour_passed`.
- **Town Schedules (`data/schedules.json`, `scripts/world/npc_schedule.gd`, `scripts/npc.gd`)**:
  - A slot is `{{from, to, at}}` where `at` is `town` or a building id; slots wrap midnight and each scheduled NPC must cover all 24 hours exactly once (tested).
  - An NPC is active only in the scene its slot names, at the position and behaviour that scene authored for it. `AreaScene.place_id` names the scene (`town` for Wrackmouth, the building id for an interior). NPCs with no entry are always present.
  - On `hour_passed` a leaving NPC walks to the door and vanishes; an arriving one appears at the door and walks to its post. Travel gives up and snaps to its target after a timeout, so a blocked path never strands anyone.
  - To schedule a new NPC: add its slots, give each place a scene node with the same `npc_id` (the generators derive `npc_id` from the dialogue file name), and add the NPC to the tests.
- **Kids (`behaviour = "play"`)**: run at `RUN_SPEED`, pick a random spot inside their play radius or run at another kid half the time (tag). Sheets `assets/npc/kid_a..d.png` come from `tools/build_kid_sheets.py` (one base child, four recolours).
- **Interior furnishing rules (`tools/gen_interior_scenes.py`, `tools/build_interior_art.py`)**:
  - Rooms are sized so the 320x180 camera sees most of one (cottages 240x170). Props are bottom-aligned sprites at `scale = 0.5` with a small footprint collision at the feet; rugs sit at `z_index = -1`, the floor and wall header at `-2`.
  - Every hearth is an unlit stone sprite plus an `AnimatedProp` fire (`hearth_fire_sheet.png`, `z_index = 1`) and halo; candles and hearths use `AreaScene.light_compensation()` so their glow keeps its colour while the room tint darkens at night.
  - Windows add a `DayLight` floor shaft that fades with `TimeSystem.get_night_factor()`; indoor ambient lerps between `INDOOR_DAY` and `INDOOR_NIGHT`.

---

## 6. Audio Architecture (`tools/gen_sfx.py`, `scripts/game/audio.gd`)
- **Zero Pure Sine-Wave Chirps**: All ambience (`amb_gulls`, `amb_wind`, `amb_waves`, `amb_fire`) and UI cues (`ui_hover`, `ui_confirm`, `ui_back`, `dialogue_blip`) use filtered organic noise, wood/parchment taps, and multi-harmonic damped acoustic lute plucks.
- **No Auto-Focus Hover Blips**: `audio.gd` connects button hover sounds only to `mouse_entered`, never `focus_entered`.
- **Multi-Bar Dark-Fantasy Music**: 16-second modal compositions combining bowed cello/fifth pads, plucked medieval lute arpeggios, solo viola/flute phrases, and cathedral reverb.

---

## 7. Live Auto-Generated Asset Inventory ({total_pngs} PNG Assets Verified)

{chr(10).join(table_sections)}
"""
    spec_path = ROOT / "docs" / "DESIGN_SPEC.md"
    spec_path.write_text(spec_md)
    print(f"updated {spec_path.relative_to(ROOT)} ({total_pngs} PNG assets cataloged)")


if __name__ == "__main__":
    update_design_spec()
