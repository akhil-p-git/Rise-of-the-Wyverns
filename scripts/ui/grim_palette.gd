class_name GrimPalette
extends RefCounted
## Single source of truth for the grim UI color palette (ash, bone, tarnished gold,
## dried blood, near-black panels). Matches assets/ui/grim_theme.tres.

const NEAR_BLACK := Color(0.055, 0.05, 0.07, 0.94)
const PANEL_BG := Color(0.07, 0.065, 0.09, 0.94)
const BUTTON_BG := Color(0.09, 0.085, 0.11, 0.94)
const BUTTON_HOVER_BG := Color(0.15, 0.13, 0.16, 0.96)
const BUTTON_FOCUS_BG := Color(0.17, 0.14, 0.13, 0.96)
const BUTTON_PRESSED_BG := Color(0.32, 0.10, 0.11, 0.96)
const BUTTON_DISABLED_BG := Color(0.06, 0.06, 0.07, 0.60)

const BONE := Color(0.92, 0.89, 0.82, 1.0)
const ASH := Color(0.58, 0.56, 0.53, 1.0)
const ASH_DARK := Color(0.24, 0.23, 0.26, 1.0)
const TARNISHED_GOLD := Color(0.78, 0.64, 0.36, 1.0)
const DRIED_BLOOD := Color(0.62, 0.17, 0.17, 1.0)
const STAMINA_MOSS := Color(0.32, 0.56, 0.28, 1.0)
const MANA_SLATE := Color(0.26, 0.45, 0.72, 1.0)
const OUTLINE_DARK := Color(0.04, 0.035, 0.055, 1.0)
