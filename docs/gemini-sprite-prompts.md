# Gemini asset prompts

Already received and sorted into `assets/source/gemini/` (see `ASSETS.md`): the 12 hero views, intro ship, broken ship and storm sea, beach ground and props, rat, crab, UI frames. The sections below remain as the prompt record.

How to use: start one Gemini chat per asset group so the style stays consistent. Paste the STYLE block first in each prompt. One image per prompt. For anything with several views (the hero), generate the base image first, then upload it and use the REFERENCE prompts. Save files under the names given; the build tools expect them.

Cleanup afterwards:
- Sprites on magenta: `uv run --no-project --with pillow --with numpy python tools/pixelize.py IN.png OUT.png --block 8 --crop --colors 20 --remove-bg 160` (use `--block 4` for 1280-wide images).
- Hero sheet: put the 12 files from section 1 in one folder and run `tools/build_hero_sheet.py --src-dir DIR --out assets/hero/hero_sheet.png`.
- Log every file in `ASSETS.md` as AI-generated and check Gemini's terms for commercial use before shipping.

## STYLE (paste at the start of every prompt)

> 16-bit pixel art, large crisp square pixels of uniform size, hard edges, no anti-aliasing, no gradients, no blur, limited 16-colour palette, dark outlines, somber mythic mood with muted blue-grey and earth tones, top-down 3/4 view as in classic Zelda-like RPGs.

Sprite suffix (add to prompts marked "on magenta"): `Subject centered on a flat solid magenta (#ff00ff) background, no shadow or ground under it, whole subject visible, no text, no border.`

## 1. Hero (12 images, the survivor)

Base, save as `idle_down.png`:
`[STYLE] A ragged survivor in torn grey prisoner overalls with brown patches, short brown hair, bare forearms, worn brown boots, standing, seen from the front, full body. [sprite suffix]`

Then upload `idle_down.png` and send each of these (the reference prompt prefix is: `Same character, same clothes, same palette and same pixel size, ...`):
- `idle_up.png`: `... seen from behind, standing.`
- `idle_left.png`: `... in side view facing left, standing.`
- `idle_right.png`: `... in side view facing right, standing.`
- `walk_down_left.png`: `... front view, mid-stride walking, left foot forward, arms swinging.`
- `walk_down_right.png`: `... front view, mid-stride walking, right foot forward, arms swinging.`
- `walk_up_left.png` and `walk_up_right.png`: same two prompts, seen from behind.
- `walk_left_left.png` and `walk_left_right.png`: same two prompts, side view facing left.
- `walk_right_left.png` and `walk_right_right.png`: same two prompts, side view facing right.

Extras for later (one image each): lying face-down on wet sand, arms out; crouching with a hand reaching down; swinging a short club; falling backwards (death).

## 2. Opening cutscene (3 images)

- `ship.png` (square, on magenta): `[STYLE] A battered wooden sailing prison ship seen from directly above, bow pointing right, long narrow hull, torn dark sails on two masts, iron-barred hatches on the deck, rigging and ropes, small lanterns. [sprite suffix]`
- `ship_broken.png` (square, on magenta): `[STYLE] The same ship broken in two pieces, snapped masts, planks and barrels scattered around, seen from directly above, bow section on the right and stern section on the left. [sprite suffix]`
- `storm_sea.png` (16:9, widest option): `[STYLE] Overhead view of a dark stormy sea at night, big rolling swells with white foam crests, a jagged black rock reef with breaking white surf along the right edge of the image, open water over the left two thirds, no ship, no land, no text.`

## 3. Starting beach (1 ground, then props)

- `ground.png` (16:9): `[STYLE] Overhead view of a rocky shipwreck beach: grey-blue sea with white foam along the top, wet dark sand, dry pale sand, scattered dark rocks, two small tide pools with blue water, a winding pale sand path leading inland to the bottom edge where grass begins. No characters, no buildings, no text.`
- Props, each on magenta with the sprite suffix, saved by name:
  - `wreck.png`: a wrecked wooden ship hull broken in two, snapped mast, torn sail cloth, planks scattered, half buried in sand, seen from above, large.
  - `wyvern_skeleton.png`: a giant wyvern skeleton: two powerful hind legs, folded bat-like wing bones in place of forelegs, a long tail and a horned skull, half buried in sand, bleached bone, seen from above, large. (The first Gemini skeleton came out four-legged and dragon-like; regenerate it with this prompt.)
  - `crate.png`: a split-open wooden crate and a barrel washed ashore with rope.
  - `driftwood.png`: a weathered driftwood log with broken ship planks.
  - `tidepool.png`: a small natural tide pool with clear blue water, irregular dark rock edge, one orange starfish, seen from above (not a stone well).
  - `dead_tree.png`: a bare twisted dead tree with a few dry leaves, seen from above at 3/4 angle.
  - `campfire_unlit.png` and `campfire_lit.png`: a small stone ring campfire, unlit with charred logs, and lit with flames.
  - `signpost.png`: a wooden signpost with a blank plank face.

## 4. People and creatures (for the tutorial)

Use the same hero workflow (base image, then 3 more directions, then 2 walk frames per direction):
- `mayor`: a stern middle-aged woman in a long dark green coat with a brass chain of office, grey streaked hair tied back, standing, front view.
- `rat`: a giant cellar rat, front view; plus side view facing left and right.
- `crab` and `gull`: beach crab and sea gull, front and side views.

## 5. UI (optional, 16:9 or square, no magenta needed)

- `[STYLE] An ornate dark wooden frame with iron corner studs for a dialogue box, empty centre, wide, designed to be stretched as a 9-slice.`
- `[STYLE] Three horizontal status bar frames, empty, in dark iron, matching the dialogue frame.` (fills are drawn in code: red health, green stamina, blue mana)
