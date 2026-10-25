# Rise of the Wyverns: lore, world and progression

Status: decided in the 2026-10-22 brainstorm unless marked (proposed) or (open). Source of truth for story, world, factions and character systems; code and art follow this file.

## Pitch

A 2D top-down fantasy RPG for people who love Skyrim and want it in 2D. You are a convict, the sole survivor of a prison ship wrecked off the coast of the kingdom of Vessary. An exiled court sorcerer, Malrec, is raising the long-dead wyverns to burn the kingdom down and seize the throne. You are not chosen and have no destiny: you are a survivor who earns a place, then has to break eight wyvern hexes before you can face Malrec.

Progression feels like Skyrim. Structure feels like Pokemon: eight great bosses, taken in any order, with side quests between, then the final villain.

Tone: mythic and somber.

## The kingdom of Vessary

A monarchy with a King and a royal court, the court that exiled Malrec.

- Look: slate coasts, salt marsh, fog, old stone. Deliberately not Skyrim's snowy Norse look.
- Capital: Highcrown (proposed name).
- History: the first kings won this land from the wyverns ages ago, and the crown still claims descent from those wyvern-slayers. Wyvern bones lie across the land as old trophies and landmarks. When Malrec raises the wyverns he is undoing the story that makes the King legitimate.
- You are a foreign convict, so the kingdom is new to you.
- The map is eight wyvern regions around the capital: sea caves, volcanic forges, glacier peaks, storm cliffs, poison marsh, barrow fields, night forest, quarry mountains.

## Wyverns

Wyverns are this world's ancient dragons. They ruled the skies before people came, and were worshipped and feared. They died out or were slain long ago, and their bones remain, like the skeleton on the starting beach.

Rules that keep them distinct from Skyrim's dragons:

- A man raises them, not a prophecy. They return because Malrec digs them up.
- Risen wyverns look undead: old bone, scorched sinew, fire burning inside the ribcage.
- They don't speak and there are no shouts. At most the eldest might carry Malrec's voice.
- No soul-absorbing. Common risen wyverns drop bone and scales for crafting. Each of the eight great wyverns is bound by one of Malrec's hexes, and breaking it frees a reward. Your power comes from undoing his work.
- Two legs and wing-arms, never four legs plus wings (see `docs/gemini-sprite-prompts.md`).

## Malrec, the villain

- Once a member of the King's royal court.
- Exiled for placing hexes on people.
- Has returned, raising wyverns to burn the kingdom down and take control.
- Hexes are his signature: every great wyvern is hex-bound, and his hex-marks appear on doors, graves and bones.
- Theme: his exile mirrors yours. You are an outsider who works to belong; he is an outsider who chose to burn it all down.
- (open) His exact court role, who he hexed, whether the King covered it up, and his title (for example "the Hexer").
- Search the name "Malrec" on Steam and in trademark databases before locking it.

## Story structure

1. Main menu and character creation (before the intro; see `docs/main-menu-and-character-creation.md`), then the shipwreck intro cutscene and the starting beach.
2. Wrackmouth, the peaceful first town. The mayor's chores teach the basics. The last chore reveals Malrec's hex-mark and the missing wyvern bones.
3. The mayor sends you to Crossholm with the news and the hex-marked bone.
4. The eight great wyverns, in any order, with towns, side quests, guild questlines and dungeons between them.
5. Malrec, once all eight hexes are broken.

### Scaling

All enemies, the wyverns included, scale to the player's level, like Skyrim. Suggested implementation: each region has a minimum and maximum level, and enemies spawn at the player's level clamped to that range.

## The towns

**Wrackmouth (first town).** A quiet fishing and salvage village above the beach, where nothing has happened in years. Villagers pick over wrecks and are wary of the one person who walked out of one. The mayor is tired and fair, and gives you work because the village is short of hands: work if you want to belong.

**Crossholm (second town, the hub).** A walled market town at a crossroads with a royal garrison. Roads lead out to the wyvern regions. It has the first shops, trainers and guild contacts. You arrive to smoke on the horizon: an outlying farm has just been burned by the first risen wyvern. Show the aftermath rather than staging a live attack, to avoid echoing Skyrim's opening.

### Tutorial chores (Wrackmouth)

> Superseded 2026-10-24: Mayor Tolle now gives a single quest, "The Rat Below" (kill the giant rat in the dungeon past the last houses), with a choice of one starting weapon (two iron daggers, iron sword and shield, two-handed sword, or a staff). The chores below are no longer in the game. The cairn grave, the hex-bone and the missing wyvern bones remain as an optional discovery (`saw_grave`) and are free to reuse when the main thread needs the reveal. The dungeon and its location are not yet designed.

| Chore | Teaches | Lore it plants |
| --- | --- | --- |
| 1. Fetch a crate of salvage from your own wreck for the Bone-wrights | Interaction, inventory | Salvage rights and the bone trade. You pass the wyvern bones on the beach. |
| 2. Clear rats from the mayor's cellar | Melee | Old stone carved with wyverns burning a city |
| 3. Carry a message to the Lantern Watch | Navigation | The keeper logs wing-shapes in the fog that "can't be" |
| 4. Forage herbs near the old cairns | One spell (light or detection) | The reveal |

The reveal: at the cairns your light shows a grave dug open, and Malrec's hex-sigil. Walking back along the shore, the wyvern bones from the first screen are gone, dragged toward the cliffs. This reuses the beach art as the payoff.

## The eight great wyverns (proposed roster, placeholder names)

Each gives a permanent Boon (passive) or a Breath (a spell on a cooldown, separate from skill spells).

| Wyvern | Region | Fight | Reward | Type |
| --- | --- | --- | --- | --- |
| Saltmaw | Sea caves and wreck graveyard | Floods the arena in waves; fight between tides | Deep Lungs: breathe underwater, swim fast, reach sunken areas | Boon |
| Cinderqueen | Volcanic forges | Lava pools spread; stay mobile | Cinder Breath: a fire cone | Breath |
| Rimewing | Glacier peaks | Freezes the floor so you slide; ice pillars as cover | Frostblood: frost resistance, no cold damage in the north | Boon |
| Thunderhide | Storm cliffs | Lightning strikes where it marks; dives from the clouds | Storm Step: lightning dash through enemies | Breath |
| Blightmother | Poison marsh | Spawns hatchlings, leaves poison clouds | Clean Blood: immunity to poison and disease | Boon |
| Hollowbone | Barrow fields | Raises skeletons; re-forms once unless you break its skull | Bone Servant: summon a skeletal ally | Breath |
| Duskwing | Night forest | Hides in darkness; your light reveals it | Shadowstep: brief invisibility and night vision | Breath |
| Graniteback | Quarry mountains | Armoured; open weak points with heavy blows | Stone Skin: permanent armour bonus | Boon |

## Factions

| Faction | Role | What they want | Your way in |
| --- | --- | --- | --- |
| The Free Company | Warrior guild | Mercenaries hiring out to burned towns. Honour-bound, practical. No secret curse. | A contract in Crossholm |
| The Hexwardens | Mage guild | A small order that breaks hexes. They knew Malrec at court and failed to stop him. An order, not a college. | Bring them a hex-mark to study |
| The Unwritten | Thief guild | Outcasts, smugglers and ex-convicts with no papers. A community, not a crime syndicate. | Your conviction opens their door |
| The Crown | Story | Wants Malrec stopped, and wants quiet about what he did at court | Through the garrison, mid-game |
| The Hexbound | Enemies | Malrec's followers, who took his hexes for power | Fought throughout |
| The Bone-wrights | Crafting | Buy wyvern bone and scales; teach Blacksmithing and Enchanting | Sell your first wyvern parts |
| The Lantern Watch | Coast and sky watch | Lighthouse keepers tracking wyvern sightings | Wrackmouth's message chore |

## Character

### Resource bars

Health, Stamina, Mana. No attributes. ("Magicka" is not used: it is an Elder Scrolls term and a Paradox game title. The code uses `mana`.)

### Levelling

- Skills run 1 to 100 and rise by use.
- Skill-ups raise character level (proposed: every 10 skill-ups).
- On level-up, add +10 to Health, Stamina or Mana.
- Then gain one perk point to spend in any skill's perk tree.

### Disciplines and skills (15)

Each skill has its own perk tree. Branches fill gaps that aren't skills of their own (lockpicking, athletics, illusion, detection). Branch lists are (proposed).

| Discipline | Skill | Covers | Perk branches (proposed) |
| --- | --- | --- | --- |
| Warrior | One-Handed | Swords, axes, maces, daggers | Blade; Axe and Mace; Dual Wield |
| Warrior | Two-Handed | Greatswords, warhammers, wyvern-bone glaives | Sweep; Stagger; Execution |
| Warrior | Block | Shields and parrying | Timed Parry; Shield Bash; Deflect Arrows |
| Warrior | Heavy Armour | Plate, mail, bone plate | Conditioning (sprint, carry weight); Juggernaut; Tower |
| Warrior | Blacksmithing | Forging, repair and improvement (includes Oblivion's Armorer) | Forge Tiers (iron, steel, bone, wyvern bone); Armorer; Salvage |
| Mage | Elemental | Fire, frost, lightning | Fire; Frost; Storm; Dual-Cast |
| Mage | Summoning | Spirits, beasts, bound weapons | Spirits; Beasts; Bound Arms; capstone: grave-song, Malrec's forbidden craft |
| Mage | Healing | Self and others, cures, repelling the dead | Restoration; Cure; Turn the Dead (strong against risen wyverns) |
| Mage | Mystic Arts | Mind, senses, utility | Illusion; Detection; Utility (telekinesis, water-breathing, shields) |
| Mage | Enchanting | Imbuing gear | Weapons; Armour; Soul Capture; Bone Runes |
| Thief | Sneak | Stealth, sneak attacks, pickpocketing | Shadow; Assassin; Pickpocket; Lockpicking |
| Thief | Charisma | Speech and barter | Persuade; Intimidate; Barter (incl. fencing) |
| Thief | Alchemy | Potions and poisons | Potions; Poisons; Forager (extra ingredients, cooking) |
| Thief | Archery | Bows and crossbows, aimed in 2D | Bows; Crossbows; Steady Aim; Trick Arrows |
| Thief | Light Armour | Leather, hide, scale | Agility (dodge-roll, move speed); Evasion; Unhindered |

### Character creation

Before the opening cutscene (see `docs/main-menu-and-character-creation.md`):
- Appearance (skin tone, hair colour, clothing colour via palette swap on the survivor sprite, with a randomise option).
- Pronouns (`she/her`, `he/him`, `they/them`).
- Difficulty (`Easy`, `Normal`, `Hard`).
- Optional Hardcore mode ("death ends this life for good").
- Convictions are cut: every character starts with identical skill values.

## Originality guardrails

The game is Skyrim-like on purpose. These keep it legally and visibly its own (not legal advice; the legal review still stands):

| Close to Skyrim | Our steer |
| --- | --- |
| Prisoner arrives, ancient dragons return | No execution scene, no rescue by attack; wyverns raised by a man, not prophecy; you are not chosen |
| Talking dragons, Shouts, Dragonborn soul-absorbing | Mute undead wyverns; rewards come from breaking Malrec's hexes |
| Warrior, mage and thief guilds | Own framing: sellswords with no curse, hex-breaking order not a college, outcast community not a syndicate |
| Town attacked by a dragon early | Show aftermath at Crossholm, not a live attack |
| Elder Scrolls words | Avoid Magicka, Jarl, Thane, Hold, the Reach, Septim, Nord, Alteration, Conjuration, Mysticism |
| Snowy Norse look | Slate coast, salt marsh, fog |

Before store assets: search "Rise of the Wyverns", "Vessary", "Malrec" and town names on Steam, Google and a trademark database.

## Still open

- Malrec's court role, who he hexed, and his title.
- Capital name (Highcrown proposed).
- Final names for the eight wyverns and their order of reveal.
- Perk branch details and skill-ups per level.
- Free Company, Hexwardens and Unwritten questlines.
