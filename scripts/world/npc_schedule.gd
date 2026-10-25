class_name NpcSchedule
extends RefCounted
## Where each villager is at each hour of the day, from `data/schedules.json`.
## A place is "town" or a building id (`mayor_hall`, `forge`, ...). An NPC without an entry is always
## wherever its scene authored it.

const PATH := "res://data/schedules.json"

static var _slots: Dictionary = {}
static var _loaded := false


## The place `npc_id` should be at `hour` (0-23), or "" when it has no schedule or no slot covers that hour.
static func place_at(npc_id: String, hour: int) -> String:
	_load()
	for slot: Dictionary in _slots.get(npc_id, []):
		if _covers(int(slot["from"]), int(slot["to"]), hour):
			return String(slot["at"])
	return ""


static func is_scheduled(npc_id: String) -> bool:
	_load()
	return _slots.has(npc_id)


static func npc_ids() -> Array:
	_load()
	return _slots.keys()


## True when the slots of `npc_id` cover all 24 hours exactly once.
static func covers_whole_day(npc_id: String) -> bool:
	_load()
	for hour in 24:
		var hits := 0
		for slot: Dictionary in _slots.get(npc_id, []):
			if _covers(int(slot["from"]), int(slot["to"]), hour):
				hits += 1
		if hits != 1:
			return false
	return true


static func reload() -> void:
	_loaded = false
	_load()


static func _covers(from_hour: int, to_hour: int, hour: int) -> bool:
	if from_hour < to_hour:
		return hour >= from_hour and hour < to_hour
	return hour >= from_hour or hour < to_hour


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	_slots = StoryData.load_json(PATH)
