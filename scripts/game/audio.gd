extends Node
## Autoload `Audio`. Manages the five audio buses (Master, Music, SFX, Ambience, UI),
## crossfades music and ambience loops, ducks music under dialogue, and plays 1D/2D SFX
## looked up by cue ID in data/audio.json.

const AUDIO_DATA_PATH := "res://data/audio.json"
const BUS_NAMES := ["Master", "Music", "SFX", "Ambience", "UI"]
const DUCK_DB := -7.0

var cues := {}
var current_music_id := ""
var active_ambience_ids: Array[String] = []
var warned_missing := {}

var _bus_volumes := {
	"Master": 1.0,
	"Music": 0.85,
	"SFX": 0.90,
	"Ambience": 0.80,
	"UI": 0.85,
}
var _music_a: AudioStreamPlayer
var _music_b: AudioStreamPlayer
var _active_music: AudioStreamPlayer
var _music_base_db := 0.0
var _ducked := false
var _ambience_players := {}
var _stream_cache := {}


func _ready() -> void:
	_ensure_buses()
	var parsed := StoryData.load_json(AUDIO_DATA_PATH)
	cues = parsed.get("cues", {})

	_music_a = AudioStreamPlayer.new()
	_music_a.bus = &"Music"
	add_child(_music_a)

	_music_b = AudioStreamPlayer.new()
	_music_b.bus = &"Music"
	add_child(_music_b)
	_active_music = _music_a

	load_volumes()
	get_tree().node_added.connect(_on_node_added)


func _ensure_buses() -> void:
	for bus_name: String in BUS_NAMES:
		if AudioServer.get_bus_index(bus_name) == -1:
			var idx := AudioServer.bus_count
			AudioServer.add_bus(idx)
			AudioServer.set_bus_name(idx, bus_name)
			AudioServer.set_bus_send(idx, &"Master")


func set_bus_volume(bus_name: String, linear: float, path := Game.SETTINGS_PATH) -> void:
	var clamped := clampf(linear, 0.0, 1.0)
	_bus_volumes[bus_name] = clamped
	var idx := AudioServer.get_bus_index(bus_name)
	if idx != -1:
		AudioServer.set_bus_mute(idx, clamped <= 0.001)
		AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(clamped, 0.0001)))
	save_volumes(path)


func get_bus_volume(bus_name: String) -> float:
	return float(_bus_volumes.get(bus_name, 1.0))


func save_volumes(path := Game.SETTINGS_PATH) -> void:
	var cfg := ConfigFile.new()
	cfg.load(path)
	for bus_name: String in BUS_NAMES:
		cfg.set_value("audio", bus_name, float(_bus_volumes.get(bus_name, 1.0)))
	cfg.save(path)


func load_volumes(path := Game.SETTINGS_PATH) -> void:
	_ensure_buses()
	var cfg := ConfigFile.new()
	if cfg.load(path) == OK:
		for bus_name: String in BUS_NAMES:
			if cfg.has_section_key("audio", bus_name):
				_bus_volumes[bus_name] = clampf(float(cfg.get_value("audio", bus_name, 1.0)), 0.0, 1.0)
	for bus_name: String in BUS_NAMES:
		var v := float(_bus_volumes.get(bus_name, 1.0))
		var idx := AudioServer.get_bus_index(bus_name)
		if idx != -1:
			AudioServer.set_bus_mute(idx, v <= 0.001)
			AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(v, 0.0001)))


func play_music(id: String, fade := 0.8) -> void:
	if id.is_empty():
		stop_music(fade)
		return
	var entry := _get_cue(id)
	if entry.is_empty():
		return
	if current_music_id == id and _active_music and _active_music.playing:
		return
	var stream := _load_stream(entry)
	if stream == null:
		return
	current_music_id = id
	_music_base_db = float(entry.get("volume_db", 0.0))
	var target_db := _music_base_db + (DUCK_DB if _ducked else 0.0)

	var next_player := _music_b if _active_music == _music_a else _music_a
	var prev_player := _active_music
	_active_music = next_player

	next_player.stream = stream
	next_player.bus = StringName(entry.get("bus", "Music"))
	if fade <= 0.01:
		if prev_player and prev_player.playing:
			prev_player.stop()
		next_player.volume_db = target_db
		if DisplayServer.get_name() != "headless":
			next_player.play()
	else:
		next_player.volume_db = -40.0
		if DisplayServer.get_name() != "headless":
			next_player.play()
		var tw := create_tween().set_parallel()
		tw.tween_property(next_player, "volume_db", target_db, fade)
		if prev_player and prev_player.playing:
			tw.tween_property(prev_player, "volume_db", -40.0, fade)
			tw.chain().tween_callback(prev_player.stop)


func stop_music(fade := 0.8) -> void:
	current_music_id = ""
	if _active_music == null or not _active_music.playing:
		return
	var p := _active_music
	if fade <= 0.01:
		p.stop()
	else:
		var tw := create_tween()
		tw.tween_property(p, "volume_db", -40.0, fade)
		tw.tween_callback(p.stop)


func set_music_ducked(ducked: bool, fade := 0.25) -> void:
	_ducked = ducked
	if _active_music == null or not _active_music.playing:
		return
	var target_db := _music_base_db + (DUCK_DB if _ducked else 0.0)
	if fade <= 0.01:
		_active_music.volume_db = target_db
	else:
		create_tween().tween_property(_active_music, "volume_db", target_db, fade)


func play_ambience(ids: Array, fade := 0.8) -> void:
	var wanted: Array[String] = []
	for raw_id in ids:
		var id := String(raw_id)
		if not id.is_empty() and not _get_cue(id).is_empty():
			wanted.append(id)
	active_ambience_ids = wanted

	for existing_id: String in _ambience_players.keys():
		if not wanted.has(existing_id):
			var old_p: AudioStreamPlayer = _ambience_players[existing_id]
			_ambience_players.erase(existing_id)
			if is_instance_valid(old_p):
				if fade <= 0.01:
					old_p.queue_free()
				else:
					var tw := create_tween()
					tw.tween_property(old_p, "volume_db", -40.0, fade)
					tw.tween_callback(old_p.queue_free)

	for id: String in wanted:
		if _ambience_players.has(id):
			continue
		var entry := _get_cue(id)
		var stream := _load_stream(entry)
		if stream == null:
			continue
		var p := AudioStreamPlayer.new()
		p.stream = stream
		p.bus = StringName(entry.get("bus", "Ambience"))
		var target_db := float(entry.get("volume_db", 0.0))
		add_child(p)
		_ambience_players[id] = p
		if fade <= 0.01:
			p.volume_db = target_db
			if DisplayServer.get_name() != "headless":
				p.play()
		else:
			p.volume_db = -40.0
			if DisplayServer.get_name() != "headless":
				p.play()
			create_tween().tween_property(p, "volume_db", target_db, fade)


func play_sfx(id: String, position: Variant = null, pitch_scale := 1.0) -> void:
	var entry := _get_cue(id)
	if entry.is_empty():
		return
	var stream := _load_stream(entry)
	if stream == null or DisplayServer.get_name() == "headless":
		return
	var bus_name := StringName(entry.get("bus", "SFX"))
	var vol_db := float(entry.get("volume_db", 0.0))
	if position is Vector2:
		var p2d := AudioStreamPlayer2D.new()
		p2d.stream = stream
		p2d.bus = bus_name
		p2d.volume_db = vol_db
		p2d.pitch_scale = pitch_scale
		p2d.position = position
		p2d.max_distance = 260.0
		add_child(p2d)
		p2d.finished.connect(p2d.queue_free)
		p2d.play()
	else:
		var p := AudioStreamPlayer.new()
		p.stream = stream
		p.bus = bus_name
		p.volume_db = vol_db
		p.pitch_scale = pitch_scale
		add_child(p)
		p.finished.connect(p.queue_free)
		p.play()


func play_ui(id: String) -> void:
	play_sfx(id)


func _get_cue(id: String) -> Dictionary:
	if cues.has(id):
		return cues[id]
	if not warned_missing.has(id):
		warned_missing[id] = true
		push_warning("Missing audio cue: " + id)
	return {}


func _load_stream(entry: Dictionary) -> AudioStream:
	var path: String = entry.get("path", "")
	if path.is_empty():
		return null
	if _stream_cache.has(path):
		return _stream_cache[path]
	var stream := load(path) as AudioStream
	if stream is AudioStreamOggVorbis and bool(entry.get("loop", false)):
		stream.loop = true
	if stream != null:
		_stream_cache[path] = stream
	return stream


func stop_all() -> void:
	current_music_id = ""
	active_ambience_ids.clear()
	_ambience_players.clear()
	_stream_cache.clear()
	for child in get_children():
		if child is AudioStreamPlayer:
			child.stop()
			child.stream = null
		elif child is AudioStreamPlayer2D:
			child.stop()
			child.stream = null
			child.queue_free()


func _exit_tree() -> void:
	stop_all()


func _on_node_added(node: Node) -> void:
	if node is Button:
		var btn := node as Button
		btn.mouse_entered.connect(_on_btn_hover)
		btn.pressed.connect(_on_btn_confirm)


func _on_btn_hover() -> void:
	play_sfx("ui_hover")


func _on_btn_confirm() -> void:
	play_sfx("ui_confirm")
