from flask import Flask, request, jsonify
import json
import stomp

app = Flask(__name__)
#--------------------- ACTIVEMQ STOMP----------------------
#variables de conexion del StompProducer.ipynb
ACTIVEMQ_HOST = '127.0.0.1'
ACTIVEMQ_PORT = 61613
ACTIVEMQ_USER = 'admin'
ACTIVEMQ_PASS = 'admin'
ACTIVEMQ_QUEUE = '/queue/sensores_huerto'
print("Conectando a ActiveMQ...")
stomp_conn = stomp.Connection12([(ACTIVEMQ_HOST, ACTIVEMQ_PORT)], heartbeats=(10000, 0))
stomp_conn.connect(ACTIVEMQ_USER, ACTIVEMQ_PASS, wait=True)
print("Conectado a ActiveMQ")
#activemq = ActiveMQConnection()
#Aquí guardaremos los últimos datos
ultimos_datos = {}
#------------ ENPOINT FLASK PARA RECIBIR DATOS -------------
@app.route('/sensores', methods=['POST'])
def recibir_sensores():
    try:
        datos = request.get_json()
        print("Datos recibidos de godot:", datos)
        
        # Guardar los últimos datos
        ultimos_datos.update(datos)
        datos_str = json.dumps(datos)

        stomp_conn.send(destination=ACTIVEMQ_QUEUE, body=datos_str)
        print(f"enviado a ActiveMQ cola {ACTIVEMQ_QUEUE}")
        #respuesta a godot de que se envio al broker:
        return jsonify({"status":"recibido y enviado a ActiveMQ(broker)"}), 200
        # enviar_a_activemq(datos)
    except Exception as e:
        print(f"✗ Error: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 400

@app.route('/sensores', methods=['GET'])
def obtener_sensores():
    """Endpoint opcional para verificar los últimos datos"""
    return jsonify(ultimos_datos), 200

if __name__ == '__main__':
    print(f"Servidor HTTP iniciado en http://127.0.0.1:5050")
    app.run(host='127.0.0.1', port=5050, debug=True)