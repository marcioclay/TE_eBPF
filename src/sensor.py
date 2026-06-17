import paho.mqtt.client as mqtt
import time
import random

def on_connect(client, userdata, flags, rc):
    print(f"[✓] Sensor Legítimo conectado ao Broker (Status: {rc})")

client = mqtt.Client()
client.on_connect = on_connect

# Conecta no Gateway (10.0.0.1) na porta MQTT padrão
client.connect("10.0.0.1", 1883, keepalive=60)
client.loop_start()

print("[*] Iniciando envio de telemetria legítima...")
try:
    while True:
        temperatura = random.uniform(20.0, 26.0)
        client.publish("iot/sensor/temperatura", f"{temperatura:.2f}")
        time.sleep(5)  # Envia a cada 5 segundos (comportamento normal)
except KeyboardInterrupt:
    client.loop_stop()
