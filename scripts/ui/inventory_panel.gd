class_name InventoryPanel
extends Control
## Thematic dark-fantasy character satchel & inventory screen. Toggle with I or Tab.

signal closed

const ITEM_DESCRIPTIONS := {
	"coin": "Salt-tarnished silver and copper crown bits weighed at the Hall.",
	"salvage_crate": "Heavy iron ship-fittings and tarred rope salvaged from the surf for Orsa's forge.",
	"iron_scrap": "Bent hull-strapping, rivets, and chain links that still ring true on an anvil.",
	"moonherb": "Pale dusk-holding leaves gathered among the old cairns south-west of Wrackmouth.",
	"hex_bone": "A scorched bone dug from the cracked cairn. A fresh arcane hex-mark burns in its marrow.",
	"mayor_letter": "Mayor Tolle's sealed dispatch for Teague Marrow at Lantern Watch.",
	"carters_tally": "Dov Carrow's notched tally stick from the burned farmstead on the Crossholm road.",
}

@onready var _title_label: Label = $Panel/Margin/VBox/Header/Title
@onready var _coin_label: Label = $Panel/Margin/VBox/Header/CoinLabel
@onready var _items_box: VBoxContainer = $Panel/Margin/VBox/Body/ItemsScroll/ItemsList
@onready var _empty_label: Label = $Panel/Margin/VBox/Body/ItemsScroll/ItemsList/EmptyLabel
@onready var _detail_title: Label = $Panel/Margin/VBox/Body/DetailBox/DetailTitle
@onready var _detail_desc: Label = $Panel/Margin/VBox/Body/DetailBox/DetailDesc
@onready var _portrait: Sprite2D = $Panel/Margin/VBox/Body/DetailBox/PortraitFrame/PortraitSprite
@onready var _close_btn: Button = $Panel/Margin/VBox/Header/CloseButton

var _selected_item := ""


func _ready() -> void:
	visible = false
	_close_btn.pressed.connect(close)
	Game.state.inventory_changed.connect(func(_id: String) -> void:
		if visible:
			refresh()
	)
	refresh()


func is_open() -> bool:
	return visible


func toggle() -> void:
	if visible:
		close()
	else:
		open()


func open() -> void:
	refresh()
	visible = true
	Audio.play_ui("ui_confirm")


func close() -> void:
	if not visible:
		return
	visible = false
	Audio.play_ui("ui_back")
	closed.emit()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		var k := event as InputEventKey
		if k.physical_keycode == KEY_I or k.physical_keycode == KEY_TAB or k.keycode == KEY_I or k.keycode == KEY_TAB:
			get_viewport().set_input_as_handled()
			toggle()
		elif visible and (k.physical_keycode == KEY_ESCAPE or k.keycode == KEY_ESCAPE):
			get_viewport().set_input_as_handled()
			close()


func item_row_count() -> int:
	var n := 0
	for child in _items_box.get_children():
		if child != _empty_label and not child.is_queued_for_deletion():
			n += 1
	return n


func select_item(item_id: String) -> void:
	_select_item(item_id)


func refresh() -> void:
	if _title_label == null:
		return
	_title_label.text = "Castaway's Satchel"
	_coin_label.text = "Coin Purse: %d" % Game.state.count("coin")

	if _portrait != null and Game.character != null:
		_portrait.material = Game.character.make_material()

	for child in _items_box.get_children():
		if child != _empty_label:
			child.queue_free()

	var carried_ids: Array[String] = []
	for item_id: String in Game.state.items.keys():
		if Game.state.count(item_id) > 0:
			carried_ids.append(item_id)
	carried_ids.sort()

	_empty_label.visible = carried_ids.is_empty()
	if carried_ids.is_empty():
		_selected_item = ""
		_detail_title.text = "Empty Satchel"
		_detail_desc.text = "Nothing but salt-stiffened linen. Scour the wreck and the village for salvage."
		return

	if _selected_item.is_empty() or Game.state.count(_selected_item) <= 0:
		_selected_item = carried_ids[0]

	for item_id in carried_ids:
		var qty := Game.state.count(item_id)
		var btn := Button.new()
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.custom_minimum_size = Vector2(0, 28)
		var icon_path := "res://assets/ui/items/%s.png" % item_id
		if ResourceLoader.exists(icon_path):
			btn.icon = load(icon_path) as Texture2D
			btn.expand_icon = true
		var dname := Game.state.item_name(item_id)
		btn.text = "  %s   ×%d" % [dname, qty] if qty > 1 else "  %s" % dname
		btn.pressed.connect(_select_item.bind(item_id))
		btn.mouse_entered.connect(_select_item.bind(item_id))
		_items_box.add_child(btn)

	_select_item(_selected_item)


func _select_item(item_id: String) -> void:
	_selected_item = item_id
	var qty := Game.state.count(item_id)
	var dname := Game.state.item_name(item_id)
	_detail_title.text = "%s (×%d)" % [dname, qty] if qty > 1 else dname
	_detail_desc.text = ITEM_DESCRIPTIONS.get(
		item_id,
		"Carried in your salt-stained satchel."
	)
