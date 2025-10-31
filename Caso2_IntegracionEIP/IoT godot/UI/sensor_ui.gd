extends Control


@export_subgroup("Nodes")
@export var value_label: Label
@export var unit_label: Label

@export_subgroup("Variables")
@export var thermostat: Thermostat
@export var sensor: Sensor
@export var unit: String


func _ready() -> void:
	unit_label.text = unit


func _process(delta: float) -> void:
	value_label.text = str(sensor.reading) if sensor else str(roundi(thermostat.temperature))
