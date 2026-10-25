# Rise of the Wyverns — Visual, Audio & Gameplay Design Specification

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
  - Full walkable interiors for all 8 town buildings (Mayor's Hall, Kell's Forge, The Salt Gull, Lantern Watch Tower, Harrow Cottage, Rook Cottage, Weaver Cottage, Venn's Goods) plus the Salt Gull's rentable room.
  - Warm indoor lighting (`WarmIndoorLight`), crackling hearth ambience (`amb_fire`), timber/stone floors, and furniture.
  - Doorways lead seamlessly back outside to Wrackmouth in front of each respective house via `Spawns/from_<building_id>`.
- **Persistent Loot Containers (`scripts/world/loot_container.gd`)**:
  - Chests, cupboards, tool bins, and larders provide lore items, salvage, and coin.
  - Container states persist via story flags (`looted_<id>`), preventing duplicate looting.
- **Inn room and sleep (`scripts/world/room_rental_door.gd`, `scripts/rest_spot.gd`, `Game.sleep_in_bed`)**: the door in the Salt Gull costs 5 coin and rents the room for 24 game hours (`TimeSystem.elapsed_minutes` is the absolute clock; the innkeeper's debt flag `inn_free` waives it). Using the room's bed opens the same hour picker as `T` in sleep mode (1 to 24 hours): any length passes that time, refills every vital and grants Well Rested for 8 hours after waking, so `Game.xp_multiplier()` is 1.1 while it lasts. Every future XP award must multiply by `Game.xp_multiplier()`. Waiting with `T` never grants Well Rested.
- **Coin notices (`scripts/ui/hud.gd`)**: the HUD never lists the coin total (the satchel does). A gain shows a brief "Gained N coin" popup that adds up while it is still up; spending or taking other items shows nothing. A future shop screen should handle its own purchases and sales without that popup.
- **NPC pacing (`scripts/npc.gd`)**: adults stand still 4 to 9 seconds between strolls and between waypoint legs (`IDLE_PAUSE_MIN`/`IDLE_PAUSE_MAX`); kids rest 1 to 3 seconds (`PLAY_PAUSE_*`). Tested over two minutes of play.
- **Merchant (`trader_shop`)**: Osric Venn keeps Venn's Goods and gives the side quest Elin's Locket. Buying and selling are not built yet.
- **Waiting (`T`, `scripts/ui/wait_panel.gd`)**: pick 1 to 24 hours; `TimeSystem.wait_hours` advances the clock hour by hour (doors and schedules react on each hour) and `Stats.restore_all` refills health, stamina and mana. The HUD clock shows the hour only and refreshes on `hour_passed`.
- **Town Schedules (`data/schedules.json`, `scripts/world/npc_schedule.gd`, `scripts/npc.gd`)**:
  - A slot is `{from, to, at}` where `at` is `town` or a building id; slots wrap midnight and each scheduled NPC must cover all 24 hours exactly once (tested).
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

## 7. Live Auto-Generated Asset Inventory (115 PNG Assets Verified)

### Hero & Combat Sheets (`assets/hero/` — 3 assets)

| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |
| --- | --- | --- |
| `assets/hero/hero_block_sheet.png` | `384×512` px | `96×128` wu |
| `assets/hero/hero_punch_sheet.png` | `384×512` px | `96×128` wu |
| `assets/hero/hero_sheet.png` | `384×512` px | `96×128` wu |

### NPC Sprite Sheets (`assets/npc/` — 15 assets)

| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |
| --- | --- | --- |
| `assets/npc/ansa.png` | `384×512` px | `96×128` wu |
| `assets/npc/bram.png` | `384×512` px | `96×128` wu |
| `assets/npc/dov.png` | `384×512` px | `96×128` wu |
| `assets/npc/guard.png` | `384×512` px | `96×128` wu |
| `assets/npc/kid_a.png` | `384×512` px | `96×128` wu |
| `assets/npc/kid_b.png` | `384×512` px | `96×128` wu |
| `assets/npc/kid_c.png` | `384×512` px | `96×128` wu |
| `assets/npc/kid_d.png` | `384×512` px | `96×128` wu |
| `assets/npc/mayor.png` | `384×512` px | `96×128` wu |
| `assets/npc/merchant.png` | `384×512` px | `96×128` wu |
| `assets/npc/orsa.png` | `384×512` px | `96×128` wu |
| `assets/npc/pell.png` | `384×512` px | `96×128` wu |
| `assets/npc/teague.png` | `384×512` px | `96×128` wu |
| `assets/npc/wizard.png` | `384×512` px | `96×128` wu |
| `assets/npc/wren.png` | `384×512` px | `96×128` wu |

### Modular Building Parts & Smoke/Glow (`assets/buildings/` — 6 assets)

| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |
| --- | --- | --- |
| `assets/buildings/parts/chimney_smoke_sheet.png` | `384×128` px | `96×32` wu |
| `assets/buildings/parts/chimney_stone.png` | `42×84` px | `10.5×21` wu |
| `assets/buildings/parts/door_timber.png` | `82×130` px | `20.5×32.5` wu |
| `assets/buildings/parts/window_amber.png` | `40×68` px | `10×17` wu |
| `assets/buildings/parts/window_dormer.png` | `66×76` px | `16.5×19` wu |
| `assets/buildings/parts/window_glow.png` | `128×128` px | `32×32` wu |

### Interior Floors, Walls & Furniture (`assets/interiors/` — 41 assets)

| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |
| --- | --- | --- |
| `assets/interiors/floor_stone.png` | `128×128` px | `32×32` wu |
| `assets/interiors/floor_wood.png` | `128×128` px | `32×32` wu |
| `assets/interiors/furniture/anvil.png` | `56×64` px | `14×16` wu |
| `assets/interiors/furniture/banner.png` | `32×80` px | `8×20` wu |
| `assets/interiors/furniture/barrels.png` | `80×64` px | `20×16` wu |
| `assets/interiors/furniture/bed_kid.png` | `64×84` px | `16×21` wu |
| `assets/interiors/furniture/bed_wood.png` | `88×104` px | `22×26` wu |
| `assets/interiors/furniture/bench.png` | `96×32` px | `24×8` wu |
| `assets/interiors/furniture/bottle_shelf.png` | `128×64` px | `32×16` wu |
| `assets/interiors/furniture/candle_glow.png` | `64×64` px | `16×16` wu |
| `assets/interiors/furniture/candle_stand.png` | `16×40` px | `4×10` wu |
| `assets/interiors/furniture/cauldron.png` | `40×44` px | `10×11` wu |
| `assets/interiors/furniture/chair_wood.png` | `48×64` px | `12×16` wu |
| `assets/interiors/furniture/chest.png` | `64×52` px | `16×13` wu |
| `assets/interiors/furniture/coal_bin.png` | `48×40` px | `12×10` wu |
| `assets/interiors/furniture/counter_bar.png` | `144×56` px | `36×14` wu |
| `assets/interiors/furniture/cupboard.png` | `80×112` px | `20×28` wu |
| `assets/interiors/furniture/desk_scrolls.png` | `112×60` px | `28×15` wu |
| `assets/interiors/furniture/fur_rug.png` | `112×72` px | `28×18` wu |
| `assets/interiors/furniture/grindstone.png` | `48×56` px | `12×14` wu |
| `assets/interiors/furniture/hearth.png` | `96×88` px | `24×22` wu |
| `assets/interiors/furniture/hearth_fire_sheet.png` | `176×40` px | `44×10` wu |
| `assets/interiors/furniture/hearth_glow.png` | `192×192` px | `48×48` wu |
| `assets/interiors/furniture/herb_bunches.png` | `56×40` px | `14×10` wu |
| `assets/interiors/furniture/light_shaft.png` | `64×88` px | `16×22` wu |
| `assets/interiors/furniture/loom.png` | `88×80` px | `22×20` wu |
| `assets/interiors/furniture/net_rack.png` | `88×80` px | `22×20` wu |
| `assets/interiors/furniture/room_door.png` | `40×56` px | `10×14` wu |
| `assets/interiors/furniture/rug_woven.png` | `128×72` px | `32×18` wu |
| `assets/interiors/furniture/sacks.png` | `64×52` px | `16×13` wu |
| `assets/interiors/furniture/shelf_unit.png` | `64×96` px | `16×24` wu |
| `assets/interiors/furniture/spinning_wheel.png` | `56×64` px | `14×16` wu |
| `assets/interiors/furniture/stool.png` | `24×28` px | `6×7` wu |
| `assets/interiors/furniture/table_food.png` | `112×64` px | `28×16` wu |
| `assets/interiors/furniture/table_wood.png` | `112×64` px | `28×16` wu |
| `assets/interiors/furniture/tool_rack.png` | `72×72` px | `18×18` wu |
| `assets/interiors/furniture/trough.png` | `64×36` px | `16×9` wu |
| `assets/interiors/furniture/weapon_rack.png` | `72×80` px | `18×20` wu |
| `assets/interiors/furniture/window_wall.png` | `40×52` px | `10×13` wu |
| `assets/interiors/wall_stone.png` | `512×96` px | `128×24` wu |
| `assets/interiors/wall_timber.png` | `512×96` px | `128×24` wu |

### Seamless 4x Terrain Tiles (`assets/terrain/` — 3 assets)

| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |
| --- | --- | --- |
| `assets/terrain/cobble_tile.png` | `256×256` px | `64×64` wu |
| `assets/terrain/dirt_rubble_tile.png` | `256×256` px | `64×64` wu |
| `assets/terrain/grass_tile.png` | `256×256` px | `64×64` wu |

### Wrackmouth Ground & Buildings (`assets/wrackmouth/` — 10 assets)

| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |
| --- | --- | --- |
| `assets/wrackmouth/cottage_harrow.png` | `296×265` px | `74×66.25` wu |
| `assets/wrackmouth/cottage_rook.png` | `272×279` px | `68×69.75` wu |
| `assets/wrackmouth/cottage_shuttered.png` | `272×271` px | `68×67.75` wu |
| `assets/wrackmouth/cottage_weaver.png` | `296×281` px | `74×70.25` wu |
| `assets/wrackmouth/forge.png` | `384×339` px | `96×84.75` wu |
| `assets/wrackmouth/ground.png` | `2560×1680` px | `640×420` wu |
| `assets/wrackmouth/lantern_watch.png` | `216×352` px | `54×88` wu |
| `assets/wrackmouth/mayor_hall.png` | `464×462` px | `116×115.5` wu |
| `assets/wrackmouth/salt_gull.png` | `496×439` px | `124×109.75` wu |
| `assets/wrackmouth/shop_trader.png` | `272×279` px | `68×69.75` wu |

### Crossholm Road Ground & Structures (`assets/crossholm_road/` — 6 assets)

| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |
| --- | --- | --- |
| `assets/crossholm_road/burned_farm.png` | `272×271` px | `68×67.75` wu |
| `assets/crossholm_road/cart.png` | `224×228` px | `56×57` wu |
| `assets/crossholm_road/gate.png` | `192×256` px | `48×64` wu |
| `assets/crossholm_road/ground.png` | `2560×1440` px | `640×360` wu |
| `assets/crossholm_road/wall_north.png` | `192×680` px | `48×170` wu |
| `assets/crossholm_road/wall_south.png` | `192×584` px | `48×146` wu |

### Beach Ground & Props (`assets/beach/` — 5 assets)

| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |
| --- | --- | --- |
| `assets/beach/crate.png` | `160×132` px | `40×33` wu |
| `assets/beach/ground.png` | `1280×720` px | `320×180` wu |
| `assets/beach/water_mask.png` | `320×180` px | `80×45` wu |
| `assets/beach/wreck.png` | `384×345` px | `96×86.25` wu |
| `assets/beach/wyvern_skeleton.png` | `272×254` px | `68×63.5` wu |

### World, Cemetery & Quest Props (`assets/props/` — 15 assets)

| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |
| --- | --- | --- |
| `assets/props/cairn_stones.png` | `128×112` px | `32×28` wu |
| `assets/props/campfire_lit.png` | `96×85` px | `24×21.25` wu |
| `assets/props/campfire_lit_sheet.png` | `384×85` px | `96×21.25` wu |
| `assets/props/campfire_unlit.png` | `96×85` px | `24×21.25` wu |
| `assets/props/dead_tree.png` | `208×260` px | `52×65` wu |
| `assets/props/driftwood.png` | `168×139` px | `42×34.75` wu |
| `assets/props/fire_glow.png` | `128×128` px | `32×32` wu |
| `assets/props/headstone_1.png` | `80×104` px | `20×26` wu |
| `assets/props/headstone_2.png` | `76×96` px | `19×24` wu |
| `assets/props/iron_scrap.png` | `80×64` px | `20×16` wu |
| `assets/props/moonherb.png` | `72×72` px | `18×18` wu |
| `assets/props/open_grave.png` | `128×96` px | `32×24` wu |
| `assets/props/plaza_circle.png` | `520×552` px | `130×138` wu |
| `assets/props/rathole.png` | `72×56` px | `18×14` wu |
| `assets/props/signpost.png` | `72×105` px | `18×26.25` wu |

### Inventory Item Icons (`assets/ui/items/` — 11 assets)

| Asset Path | Pixel Dimensions (`4x` Native) | World Footprint (`@ 0.25` scale) |
| --- | --- | --- |
| `assets/ui/items/carters_tally.png` | `64×64` px | `16×16` wu |
| `assets/ui/items/coin.png` | `64×64` px | `16×16` wu |
| `assets/ui/items/hex_bone.png` | `64×64` px | `16×16` wu |
| `assets/ui/items/iron_daggers.png` | `64×64` px | `16×16` wu |
| `assets/ui/items/iron_scrap.png` | `64×64` px | `16×16` wu |
| `assets/ui/items/iron_sword_shield.png` | `64×64` px | `16×16` wu |
| `assets/ui/items/mayor_letter.png` | `64×64` px | `16×16` wu |
| `assets/ui/items/moonherb.png` | `64×64` px | `16×16` wu |
| `assets/ui/items/salvage_crate.png` | `64×64` px | `16×16` wu |
| `assets/ui/items/staff.png` | `64×64` px | `16×16` wu |
| `assets/ui/items/two_handed_sword.png` | `64×64` px | `16×16` wu |

