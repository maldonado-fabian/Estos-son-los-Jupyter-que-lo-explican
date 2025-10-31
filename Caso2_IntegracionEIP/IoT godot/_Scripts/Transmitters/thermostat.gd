extends Node2D
class_name Thermostat


const MIN_CRIT: float = 10.0
const MAX_CRIT: float = 35.0

const MIN_DAY: float = 22.0
const MAX_DAY: float = 26.0

const MIN_NIGHT: float = 16.0
const MAX_NIGHT: float = 18.0

@export var period: float = 1.0

var temperature: float
var time_passed: float = 0.0


func _process(delta: float) -> void:
	time_passed += delta
	if time_passed >= period:
		time_passed -= period
		emit()


func emit() -> void:
	var delta: float = Global.rng.randf()
	temperature = Global.rng.randf_range(MIN_CRIT - delta, MAX_CRIT + delta)
	# Reemplazar la línea anterior por una forma más compleja y realista de emitir la temperatura
