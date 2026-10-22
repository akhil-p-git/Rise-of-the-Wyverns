class_name StoryData
extends RefCounted
## Loads the JSON that holds the story: data/story.json (items, quests) and data/dialogue/*.json.


static func load_json(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Cannot open %s: %s" % [path, error_string(FileAccess.get_open_error())])
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not parsed is Dictionary:
		push_error("%s is not a JSON object" % path)
		return {}
	return parsed
