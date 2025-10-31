extends Node

var http_request := HTTPRequest.new()
var intervalo_envio := 1.0
var tiempo := 0.0

@export var url := "http://127.0.0.1:5050/sensores"

func _ready():
	add_child(http_request)
	http_request.request_completed.connect(_on_request_completed)
	print("Cliente HTTP listo. Enviando a: ", url)

func _process(delta):
	tiempo += delta
	if tiempo >= intervalo_envio:
		tiempo = 0.0
		enviar_datos()

func enviar_datos():
	var data = {
		"temperatura": get_parent().get_node("Thermostat").temperature,
		"humedad": get_parent().get_node("Sensors/SensorHumidity").reading,
		"co2": get_parent().get_node("Sensors/SensorCO2").reading
	}
	
	var json_str = JSON.stringify(data)
	var headers = ["Content-Type: application/json"]
	
	var error = http_request.request(url, headers, HTTPClient.METHOD_POST, json_str)
	
	if error == OK:
		print("→ Enviando: ", json_str)
	else:
		print("Error al enviar: ", error)

func _on_request_completed(result, response_code, headers, body):
	if response_code == 200:
		var response = JSON.parse_string(body.get_string_from_utf8())
		print("Respuesta del servidor: ", response)
	else:
		print("Error HTTP: ", response_code)
