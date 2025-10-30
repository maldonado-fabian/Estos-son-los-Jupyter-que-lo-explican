#Tenemos 5 consumers: ConsumerCO2, ConsumerHumedad, ConsumerTemperatura, ConsumerBD, ConsumerLogger
import stomp
import json
import time
import sqlite3
import threading
from datetime import datetime
#--------------------- ACTIVEMQ STOMP----------------------
ACTIVEMQ_HOST = '127.0.0.1'
ACTIVEMQ_PORT = 61613
ACTIVEMQ_USER = 'admin'
ACTIVEMQ_PASS = 'admin'
#colas de entrada mq's
QUEUE_TODOS_DATOS = '/queue/mqTodosDatos'
QUEUE_ALERTA_CO2 = '/queue/mqAlertaCO2'
QUEUE_ALERTA_HUMEDAD = '/queue/mqAlertaHumedad'
QUEUE_ALERTA_TEMPERATURA = '/queue/mqAlertaTemperatura'
QUEUE_LOGGER = '/queue/mqLogger'

DB_NAME='sensores_huerto.db'
LOG_ALERTAS = 'alertas.log'
LOG_ERRORES = 'errores.log'

#BASE DE DATOS(SQLite):
class DatabaseManager:
    def __init__(self,db_name):
        self.db_name=db_name
        self.crear_tabla()
    def crear_tabla(self):
        conn=sqlite3.connect(self.db_name)
        cursor= conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensores_godot (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    co2 REAL NOT NULL,
                    humedad REAL NOT NULL,
                    temperatura REAL NOT NULL,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')
        conn.commit()
        conn.close()
        print("Tabla creada o ya existente.")

    #Insertar los datos en la BD
    def insertar_datos(self, datos):
        conn=sqlite3.connect(self.db_name)
        cursor= conn.cursor()
        cursor.execute('''
            INSERT INTO sensores_godot (fecha, timestamp, co2, humedad, temperatura)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datos.get('fecha', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                datos.get('timestamp', time.time()),
                float(datos.get('temperatura', 0)),
                float(datos.get('humedad', 0)),
                float(datos.get('co2', 0))))
        conn.commit()
        lectura_id=cursor.lastrowid
        conn.close()
        print("Datos insertados en la base de datos.")
        return lectura_id

#------------------------CONSUMER BD (guardamos todos los datos)----------
class ConsumerBD(stomp.ConnectionListener):
    def __init__(self, db_manager):
        self.db= db_manager
        self.count = 0
    def on_message(self,frame):
        try:
            datos= json.loads(frame.body)
            lectura_id= self.db.insertar_datos(datos)
            self.count += 1
            print(f"Mensaje #{self.count} insertado en BD con ID {lectura_id}")
        except Exception as e:
            print(f" Error BD:  {e}")
#-------------------------CONSUMER ALERTAS CO2, HUMEDAD Y TEMPERATURA--------------
class ConsumerAlertas(stomp.ConnectionListener):
    def __init__(self, tipo):
        self.tipo = tipo
        self.count = 0
        self.ultima_alerta_time = 0
    def on_message(self,frame):
        try:
            alerta=json.loads(frame.body)
            tiempo_actual=time.time()
            if tiempo_actual-self.ultima_alerta_time<30: #aggregator, para noa hacer spam
                print(f"Alerta {self.tipo} ignorada para evitar spam.")
                return
            
            self.ultima_alerta_time=tiempo_actual
            self.count += 1
            emojis_alerta={
                'CO2': '🚨',
                'Humedad': '💧',
                'Temperatura': '🌡️'
            }
            emoji=emojis_alerta.get(self.tipo,'⚠️')
            print(f"{emoji} Alerta {self.tipo} #{self.count}: {alerta}")

            with open(LOG_ALERTAS, 'a',encoding='utf-8') as f:
                f.write(f"[{alerta.get('fecha')}] {self.tipo} - "
                    f"Valor: {alerta.get('valor')} - "
                    f"{alerta.get('mensaje')}\n")
                
        except Exception as e:
            print(f" Error Alerta {self.tipo}:  {e}")

#-------------------------CONSUMER LOGGER (errores de validacion)--------------
class ConsumerLogger(stomp.ConnectionListener):
    def __init__(self):
        self.count = 0
    def on_message(self, frame):
        try:
            error=json.loads(frame.body)
            self.count += 1

            tipo=error.get('tipo','Desconocido')
            timestamp=error.get('timestamp', time.time())
            fecha=datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[Logger] #{self.count} - Tipo: {tipo} - Fecha: {fecha}")

            with open(LOG_ERRORES,'a',encoding='utf-8') as f:
                f.write(f"\n[{fecha}] {tipo}\n")
                if tipo == 'validacion':
                    f.write(f"Errores: {error.get('errores', [])}\n")
                elif tipo == 'error_sistema':
                    f.write(f"Error: {error.get('error', 'Sin detalles')}\n")

        except Exception as e:
            print(f" Error Logger:  {e}")

def main():
    print(f"Conectando a ActiveMQ para consumidores: {ACTIVEMQ_HOST}:{ACTIVEMQ_PORT}...")

    db_manager=DatabaseManager(DB_NAME)
    conn=stomp.Connection12([(ACTIVEMQ_HOST, ACTIVEMQ_PORT)], heartbeats=(10000,0))
    #listeners
    listener_bd=ConsumerBD(db_manager)
    listener_co2=ConsumerAlertas('CO2')
    listener_humedad=ConsumerAlertas('Humedad') 
    listener_temperatura=ConsumerAlertas('Temperatura')
    listener_logger=ConsumerLogger()

    conn.set_listener('bd', listener_bd)
    conn.set_listener('co2', listener_co2)
    conn.set_listener('humedad', listener_humedad)
    conn.set_listener('temperatura', listener_temperatura)
    conn.set_listener('logger', listener_logger)
    #conectar
    conn.connect(ACTIVEMQ_USER, ACTIVEMQ_PASS, wait=True)
    print("Conectado a ActiveMQ.\n")
    #suscribirse a las colas
    conn.subscribe(destination=QUEUE_TODOS_DATOS, id=1, ack='auto')
    conn.subscribe(destination=QUEUE_ALERTA_CO2, id=2, ack='auto')
    conn.subscribe(destination=QUEUE_ALERTA_HUMEDAD, id=3, ack='auto')
    conn.subscribe(destination=QUEUE_ALERTA_TEMPERATURA, id=4, ack='auto')
    conn.subscribe(destination=QUEUE_LOGGER, id=5, ack='auto')
    print("Suscrito a las colas de consumidores.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Deteniendo consumidores...")
    finally:
        conn.disconnect()
        print("Desconectado de ActiveMQ.")
        print(f"   Lecturas en BD: {listener_bd.count}")
        print(f"   Alertas CO2: {listener_co2.count}")
        print(f"   Alertas Humedad: {listener_humedad.count}")
        print(f"   Alertas Temperatura: {listener_temperatura.count}")
        print(f"   Logs de errores: {listener_logger.count}")

if __name__ == "__main__":
    main()