extends Area2D
class_name Sensor


@export_subgroup("Variables")
@export var type: Util.ParticleType

var reading: int = 0


func _on_body_entered(body: Node2D) -> void:
	if body is Particle:
		if not body.type == type:
			return
		
		body.queue_free()
		reading += 1
