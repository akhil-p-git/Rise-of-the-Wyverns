class_name QuestLog
extends RefCounted
## Quest progress. Each quest is an ordered list of stages; a stage is done when all of its
## `done_when` conditions hold. Pure logic: the caller supplies the condition check.

signal changed(quest_id: String)

var _defs: Dictionary
## quest id -> index of the current stage; stages.size() means the quest is finished.
var _stage := {}


func _init(defs: Dictionary) -> void:
	_defs = defs


func knows(id: String) -> bool:
	return _defs.has(id)


func title(id: String) -> String:
	return _defs[id].get("title", id)


func is_started(id: String) -> bool:
	return _stage.has(id)


func is_done(id: String) -> bool:
	return _stage.has(id) and _stage[id] >= _stages(id).size()


func is_active(id: String) -> bool:
	return is_started(id) and not is_done(id)


func start(id: String) -> bool:
	if not knows(id) or is_started(id):
		return false
	_stage[id] = 0
	changed.emit(id)
	return true


## Id of the current stage, or "" when the quest is not active.
func stage_id(id: String) -> String:
	if not is_active(id):
		return ""
	return _stages(id)[_stage[id]]["id"]


func active_ids() -> Array[String]:
	var out: Array[String] = []
	for id: String in _defs:
		if is_active(id):
			out.append(id)
	return out


## Advances every quest whose current stage is satisfied, repeatedly, so a stage that was
## already complete when it began is skipped straight away.
func refresh(check: Callable) -> void:
	for id: String in _stage.keys():
		var moved := false
		while is_active(id) and _satisfied(_stages(id)[_stage[id]], check) == _count(id):
			_stage[id] += 1
			moved = true
		if moved:
			changed.emit(id)


## "Gather moonherb (2/4)": the stage text, with progress when the stage has several parts.
func objective(id: String, check: Callable) -> String:
	if not is_active(id):
		return ""
	var stage: Dictionary = _stages(id)[_stage[id]]
	var total: int = stage.get("done_when", []).size()
	if total <= 1:
		return stage["text"]
	return "%s (%d/%d)" % [stage["text"], _satisfied(stage, check), total]


func _count(id: String) -> int:
	return _stages(id)[_stage[id]].get("done_when", []).size()


func _satisfied(stage: Dictionary, check: Callable) -> int:
	var n := 0
	for cond: String in stage.get("done_when", []):
		if check.call([cond]):
			n += 1
	return n


func _stages(id: String) -> Array:
	return _defs[id]["stages"]
