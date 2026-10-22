class_name GameState
extends RefCounted
## What the story remembers: flags, carried items and quest progress. Pure logic, no nodes,
## so it can be unit tested; the `Game` autoload owns the one live instance.
##
## Conditions (used by quests and dialogue) are strings, all of which must hold:
##   flag:name        a flag is set (or a derived flag's conditions all hold)
##   item:name>=n     at least n of an item (`item:name` means one)
##   started:quest    the quest has been started       active:quest   started and not done
##   done:quest       the quest is finished            stage:quest=id the quest is at that stage
## Prefix any of them with `!` to negate it.
##
## Actions (run by dialogue): flag:name, clear:name, start:quest, give:item[:n], take:item[:n].

signal flag_changed(flag: String)
signal inventory_changed(item: String)
signal quest_changed(quest_id: String)

var quests: QuestLog
var flags := {}
var items := {}

var _derived: Dictionary
var _item_names: Dictionary


func _init(story: Dictionary) -> void:
	quests = QuestLog.new(story.get("quests", {}))
	_derived = story.get("derived", {})
	_item_names = story.get("items", {})
	var w: WeakRef = weakref(self)
	quests.changed.connect(
		func(id: String) -> void:
			var s := w.get_ref() as GameState
			if s:
				s.quest_changed.emit(id)
	)


func has_flag(flag: String) -> bool:
	if flags.has(flag):
		return true
	return _derived.has(flag) and check(_derived[flag])


func set_flag(flag: String) -> void:
	if flags.has(flag):
		return
	flags[flag] = true
	flag_changed.emit(flag)
	_refresh_quests()


func clear_flag(flag: String) -> void:
	if flags.erase(flag):
		flag_changed.emit(flag)


func count(item: String) -> int:
	return items.get(item, 0)


func item_name(item: String) -> String:
	return _item_names.get(item, item.capitalize())


func give(item: String, n := 1) -> void:
	items[item] = count(item) + n
	inventory_changed.emit(item)
	_refresh_quests()


## Removes up to `n`; returns false (and removes nothing) if fewer are carried.
func take(item: String, n := 1) -> bool:
	if count(item) < n:
		return false
	items[item] = count(item) - n
	inventory_changed.emit(item)
	return true


func start_quest(id: String) -> void:
	if quests.start(id):
		_refresh_quests()


func check(conditions: Array) -> bool:
	for cond: String in conditions:
		var negate := cond.begins_with("!")
		if _holds(cond.trim_prefix("!")) == negate:
			return false
	return true


func apply(actions: Array) -> void:
	for action: String in actions:
		var parts := action.split(":")
		match parts[0]:
			"flag":
				set_flag(parts[1])
			"clear":
				clear_flag(parts[1])
			"start":
				start_quest(parts[1])
			"give":
				give(parts[1], int(parts[2]) if parts.size() > 2 else 1)
			"take":
				take(parts[1], int(parts[2]) if parts.size() > 2 else 1)
			_:
				push_error("Unknown action: " + action)


func objective(quest_id: String) -> String:
	return quests.objective(quest_id, check)


func _holds(cond: String) -> bool:
	var sep := cond.find(":")
	var kind := cond.substr(0, sep)
	var arg := cond.substr(sep + 1)
	match kind:
		"flag":
			return has_flag(arg)
		"item":
			var bits := arg.split(">=")
			return count(bits[0]) >= (int(bits[1]) if bits.size() > 1 else 1)
		"started":
			return quests.is_started(arg)
		"active":
			return quests.is_active(arg)
		"done":
			return quests.is_done(arg)
		"stage":
			var bits := arg.split("=")
			return quests.stage_id(bits[0]) == bits[1]
	push_error("Unknown condition: " + cond)
	return false


func _refresh_quests() -> void:
	quests.refresh(check)
