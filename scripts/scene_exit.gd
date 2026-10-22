class_name SceneExit
extends Area2D
## Walking into this zone loads another scene, arriving at the named spawn marker there.

@export_file("*.tscn") var target_scene := ""
@export var target_spawn := ""


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if body is Player:
		Audio.play_sfx("scene_exit")
		Game.go_to(target_scene, target_spawn)
