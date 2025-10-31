extends Node2D
class_name Particle


@export_subgroup("Nodes")
@export var sprite: Sprite2D

@export_subgroup("Variables")
@export var type: Util.ParticleType:
	set(new_type):
		type = new_type
		sprite.modulate = Util.PARTICLE_COLORS[type]


func _on_visible_on_screen_notifier_2d_screen_exited() -> void:
	queue_free()
