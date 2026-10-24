class_name Stats
extends RefCounted
## Health, stamina and mana for any actor. Pure logic: no nodes, so it can be unit tested.

signal changed(stat: StringName)
signal died

const STAMINA_REGEN_DELAY := 1.0

var max_health: float
var max_stamina: float
var max_mana: float
var health: float
var stamina: float
var mana: float
var stamina_regen := 15.0
var mana_regen := 3.0

var _since_stamina_use := STAMINA_REGEN_DELAY


func _init(health_max := 100.0, stamina_max := 100.0, mana_max := 50.0) -> void:
	max_health = health_max
	max_stamina = stamina_max
	max_mana = mana_max
	health = max_health
	stamina = max_stamina
	mana = max_mana


func damage(amount: float) -> void:
	if health <= 0.0:
		return
	health = maxf(health - amount, 0.0)
	changed.emit(&"health")
	if health == 0.0:
		died.emit()


func heal(amount: float) -> void:
	if health <= 0.0:
		return
	health = minf(health + amount, max_health)
	changed.emit(&"health")


## Refills health, stamina and mana, as after a night's rest. A dead actor stays dead.
func restore_all() -> void:
	if health <= 0.0:
		return
	health = max_health
	stamina = max_stamina
	mana = max_mana
	_since_stamina_use = STAMINA_REGEN_DELAY
	changed.emit(&"health")
	changed.emit(&"stamina")
	changed.emit(&"mana")


## Spends up to `amount` of stamina. Returns false when there is none left to spend.
func use_stamina(amount: float) -> bool:
	if stamina <= 0.0:
		return false
	stamina = maxf(stamina - amount, 0.0)
	_since_stamina_use = 0.0
	changed.emit(&"stamina")
	return true


## Spends `cost` mana only if the whole cost is available.
func spend_mana(cost: float) -> bool:
	if mana < cost:
		return false
	mana -= cost
	changed.emit(&"mana")
	return true


func tick(delta: float) -> void:
	_since_stamina_use += delta
	if _since_stamina_use >= STAMINA_REGEN_DELAY and stamina < max_stamina:
		stamina = minf(stamina + stamina_regen * delta, max_stamina)
		changed.emit(&"stamina")
	if mana < max_mana:
		mana = minf(mana + mana_regen * delta, max_mana)
		changed.emit(&"mana")
