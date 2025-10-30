# PROCESO
Elegimos hacer el proceso de cultivo de tomates en un huerto, con sensor de CO2(ppm), Humedad(%) y Temperatura(°C)

# PRODUCTOR:
La simulación la hicimos en Godot, lo cual nos permitio hacerlo en 2D, pero es obvio que Godot no esta conectado directamente a algún broker
por lo que se siguio la siguiente logica:
* Godot por el servidor 127.0.0.1:5050 (el puerto puede cambiar si uno lo quiere) hace un POST en HTTPRequest, así mandamos el json
que tiene la siguiente estructura "{"co2":120,"humedad":124,"temperatura":18.7018909454346}" al puerto y de ese podremos usarlo para 
pasarlo a nuestro broker elegido (ActiveMQ classic)
* Desde nuestro script conexion.py nos conectamos a la mismo servidor HTTP que Godot para obtener los json, y igualmente nos conectamos al 