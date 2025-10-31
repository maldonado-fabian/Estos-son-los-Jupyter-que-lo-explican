extends Node


enum ParticleType { HUMIDITY, CO2 }

const PARTICLE_COLORS: Dictionary[ParticleType, Color] = {
	ParticleType.HUMIDITY: Color.ROYAL_BLUE,
	ParticleType.CO2: Color.DIM_GRAY
}
