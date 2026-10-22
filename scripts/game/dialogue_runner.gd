class_name DialogueRunner
extends RefCounted
## Walks one dialogue tree (see data/dialogue/*.json) against the game state. Pure logic.
##
## A tree has `entries` (the first whose `if` conditions hold picks the opening node) and
## `nodes`. A node has `speaker`, `text`, optional `do` actions run on entering it, and either
## `choices` (each with `text`, optional `if`, `do`, `next`) or a single `next`. A node with
## neither, or a choice with no `next`, ends the conversation.

var node_id := ""
var finished := true

var _tree: Dictionary
var _state: GameState


## Starts the tree. Returns false when no entry matches, so the caller can skip the talk.
func begin(tree: Dictionary, state: GameState) -> bool:
	_tree = tree
	_state = state
	for entry: Dictionary in tree.get("entries", []):
		if state.check(entry.get("if", [])):
			_enter(entry["node"])
			return true
	finished = true
	return false


func speaker() -> String:
	return _node().get("speaker", "")


func text() -> String:
	return _node().get("text", "")


## The choices the player can pick right now, in order. Empty means "press to continue".
func choices() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for choice: Dictionary in _node().get("choices", []):
		if _state.check(choice.get("if", [])):
			out.append(choice)
	return out


## Continues the conversation. `pick` indexes `choices()` when the node has any.
func advance(pick := 0) -> void:
	if finished:
		return
	var available := choices()
	var next := ""
	if available.is_empty():
		next = _node().get("next", "")
	else:
		var choice := available[clampi(pick, 0, available.size() - 1)]
		_state.apply(choice.get("do", []))
		next = choice.get("next", "")
	if next.is_empty():
		finished = true
	else:
		_enter(next)


func _enter(id: String) -> void:
	node_id = id
	finished = false
	_state.apply(_node().get("do", []))


func _node() -> Dictionary:
	return _tree["nodes"][node_id]
