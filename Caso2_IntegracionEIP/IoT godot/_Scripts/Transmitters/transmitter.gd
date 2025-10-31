extends Node2D
class_name Transmitter


@export_subgroup("Nodes")
@export var preloader: ResourcePreloader

@export_subgroup("Variables")
@export var type: Util.ParticleType
@export var power: float = 10.0
@export var emissions: int = 1


func _process(delta: float) -> void:
	if Input.is_key_pressed(Key.KEY_SPACE):
		emit()


func emit() -> void:
	for i: int in range(emissions):
		var instance: PackedScene = preloader.get_resource("particle")
		if not instance:
			return
		
		var particle: Particle = instance.instantiate()
		particle.type = type
		
		var angle: float = Global.rng.randf_range(0, 2 * PI)
		var direction: Vector2 = Vector2(cos(angle), -sin(angle))
		var force: Vector2 = direction * power
		particle.apply_central_impulse(force)
		
		add_child(particle)
