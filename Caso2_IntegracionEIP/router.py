import stomp
import json
import time
import sys

ACTIVEMQ_HOST = '127.0.0.1'
ACTIVEMQ_PORT = 61613
ACTIVEMQ_USER = 'admin'
ACTIVEMQ_PASS = 'admin'

# Cola de principal
QUEUE_INPUT = '/queue/sensores_huerto'

#colas de salida mq's
QUEUE_TODOS_DATOS = '/queue/mqTodosDatos'
QUEUE_CO2 = '/queue/mqCO2'
QUEUE_HUMEDAD = '/queue/mqHumedad'
QUEUE_TEMPERATURA = '/queue/mqTemperatura'
QUEUE_LOGGER = '/queue/mqLogger'
QUEUE_ALERTA_CO2 = '/queue/mqAlertaCO2'
QUEUE_ALERTA_HUMEDAD = '/queue/mqAlertaHumedad'
QUEUE_ALERTA_TEMPERATURA = '/queue/mqAlertaTemperatura'

# Rangos óptimos para tomates
RANGOS_OPTIMOS = {
    'co2': {'min': 700, 'max': 1000},
    'humedad': {'min': 40, 'max': 90},
    'temperatura': {'min': 6, 'max': 45}
}
#Listener de Stomp.ipynb
class RouterListener(stomp.ConnectionListener):
    def __init__(self, conn):
        self.conn = conn
        self.mensaje_count = 0
    
    def on_error(self, frame):
        print(f'Error recibido: {frame.body}')
    
    def on_message(self, frame):
        self.mensaje_count += 1
        
        try:
            # Decodificar mensaje
            datos = json.loads(frame.body)
            
            print(f"\n{'='*60}")
            print(f"📨 Mensaje #{self.mensaje_count} recibido del router")
            print(f"Datos: {datos}")
            print(f"{'='*60}")
            
            #1) validar si los datos son validos, si no se envia a logger
            if not self.validar_datos(datos):
                error_msg = {
                    'tipo': 'validacion',
                    'datos': datos,
                    'timestamp': time.time()
                }
                self.conn.send(destination=QUEUE_LOGGER, body=json.dumps(error_msg))
                print("✗ Datos inválidos, enviado a mqLogger")
                return
            
            # 2. ENVIAR A mqTodosDatos (sin filtrar ya que son datos historicos)
            self.conn.send(destination=QUEUE_TODOS_DATOS, body=json.dumps(datos))
            print(f"✓ Enviado a mqTodosDatos")
            
            # 3. CONTENT-BASED ROUTER: CO2, Humedad y Temperatura
            if 'co2' in datos:
                msg_co2 = {
                    'co2': datos['co2'],
                    'timestamp': datos.get('timestamp'),
                    'fecha': datos.get('fecha')
                }
                self.conn.send(destination=QUEUE_CO2, body=json.dumps(msg_co2))
                print(f"✓ CO2 enviado a mqCO2")
                
                # Aplicar filtro CO2 para ver si esta en fuera de rango normal 
                self.aplicar_filtro_co2(datos)
            
            if 'humedad' in datos:
                msg_humedad = {
                    'humedad': datos['humedad'],
                    'timestamp': datos.get('timestamp'),
                    'fecha': datos.get('fecha')
                }
                self.conn.send(destination=QUEUE_HUMEDAD, body=json.dumps(msg_humedad))
                print(f"✓ Humedad enviada a mqHumedad")
                
                # Aplicar filtro Humedad
                self.aplicar_filtro_humedad(datos)
            
            if 'temperatura' in datos:
                msg_temp = {
                    'temperatura': datos['temperatura'],
                    'timestamp': datos.get('timestamp'),
                    'fecha': datos.get('fecha')
                }
                self.conn.send(destination=QUEUE_TEMPERATURA, body=json.dumps(msg_temp))
                print(f"✓ Temperatura enviada a mqTemperatura")
                
                # Aplicar filtro Temperatura
                self.aplicar_filtro_temperatura(datos)
            
            print(f"{'='*60}\n")
            
        except json.JSONDecodeError as e:
            print(f"✗ Error decodificando JSON: {e}")
        except Exception as e:
            print(f"✗ Error procesando mensaje: {e}")
    
    def validar_datos(self, datos):
        """Valida que los datos sean correctos"""
        campos_requeridos = ['co2','humedad', 'temperatura']
        
        for campo in campos_requeridos:
            if campo not in datos:
                print(f"  ✗ Falta campo: {campo}")
                return False
            
            valor = datos[campo]
            if valor is None:
                print(f"  ✗ {campo} es None")
                return False
            
            try:
                valor_float = float(valor)
                if valor_float < 0:
                    print(f"  ✗ {campo} es negativo: {valor_float}")
                    return False
            except (ValueError, TypeError):
                print(f"  ✗ {campo} no es número: {valor}")
                return False
        
        return True
    
    def aplicar_filtro_co2(self, datos):
        """Message Filter: CO2 [value<700 or value>1000]"""
        co2 = float(datos['co2'])
        
        if co2 < RANGOS_OPTIMOS['co2']['min'] or co2 > RANGOS_OPTIMOS['co2']['max']:
            alerta = {
                'tipo': 'alerta_co2',
                'valor': co2,
                'mensaje': f"⚠️  CO2 fuera de rango: {co2} ppm (óptimo: 700-1000)",
                'timestamp': datos.get('timestamp'),
                'fecha': datos.get('fecha')
            }
            self.conn.send(destination=QUEUE_ALERTA_CO2, body=json.dumps(alerta))
            print(f"  ⚠️  ALERTA CO2 enviada: {co2} ppm")
    
    def aplicar_filtro_humedad(self, datos):
        """Message Filter: Humedad [value<40 or value>90]"""
        humedad = float(datos['humedad'])
        
        if humedad < RANGOS_OPTIMOS['humedad']['min'] or humedad > RANGOS_OPTIMOS['humedad']['max']:
            alerta = {
                'tipo': 'alerta_humedad',
                'valor': humedad,
                'mensaje': f"⚠️  Humedad fuera de rango: {humedad}% (óptimo: 40-90)",
                'timestamp': datos.get('timestamp'),
                'fecha': datos.get('fecha')
            }
            self.conn.send(destination=QUEUE_ALERTA_HUMEDAD, body=json.dumps(alerta))
            print(f"  ⚠️  ALERTA HUMEDAD enviada: {humedad}%")
    
    def aplicar_filtro_temperatura(self, datos):
        """Message Filter: Temperatura [value<6 or value>45]"""
        temperatura = float(datos['temperatura'])
        
        if temperatura < RANGOS_OPTIMOS['temperatura']['min'] or temperatura > RANGOS_OPTIMOS['temperatura']['max']:
            alerta = {
                'tipo': 'alerta_temperatura',
                'valor': temperatura,
                'mensaje': f"⚠️  Temperatura fuera de rango: {temperatura}°C (óptimo: 6-45)",
                'timestamp': datos.get('timestamp'),
                'fecha': datos.get('fecha')
            }
            self.conn.send(destination=QUEUE_ALERTA_TEMPERATURA, body=json.dumps(alerta))
            print(f"  ⚠️  ALERTA TEMPERATURA enviada: {temperatura}°C")

def main():
    print("=" * 60)
    print("🔀 ROUTER - Content-Based Router (Patrón EIP)")
    print("=" * 60)
    print(f"Conectando a ActiveMQ: {ACTIVEMQ_HOST}:{ACTIVEMQ_PORT}")
    print(f"Escuchando cola: {QUEUE_INPUT}")
    print("=" * 60)
    print("\nPresiona Ctrl+C para detener\n")
    
    # Crear conexión
    conn = stomp.Connection12([(ACTIVEMQ_HOST, ACTIVEMQ_PORT)], heartbeats=(10000, 0))
    
    # Crear y registrar el listener
    listener = RouterListener(conn)
    conn.set_listener('', listener)
    
    # Conectar
    conn.connect(ACTIVEMQ_USER, ACTIVEMQ_PASS, wait=True)
    print("✓ Conectado a ActiveMQ\n")
    
    # Suscribirse a la cola de entrada
    conn.subscribe(destination=QUEUE_INPUT,id=1,ack='auto')
    print(f"✓ Suscrito a {QUEUE_INPUT}\n")
    print("Esperando mensajes para enrutar...\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo router...")
    finally:
        conn.disconnect()
        print("✓ Desconectado de ActiveMQ")
        print(f"\n📊 Total de mensajes enrutados: {listener.mensaje_count}")

if __name__ == '__main__':
    main()