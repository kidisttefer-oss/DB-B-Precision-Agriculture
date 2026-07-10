"""
Subscribes to all CampoSense topics and routes each message, by topic,
to the database that best fits its shape:

  camposense/{zone}/structured    -> MySQL   (fixed schema)
  camposense/{zone}/flexible      -> MongoDB (varying fields)
  camposense/{zone}/alert         -> MongoDB (varying event data)
  camposense/{zone}/registration  -> Neo4j   (relationships)
"""

import json
import os
import sys

import paho.mqtt.client as mqtt

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from databases.mysql_writer import save_reading
from databases.mongo_writer import save_nutrients, save_alert
from databases.neo4j_writer import save_registration

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = 1883
TOPIC = "camposense/#"


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker, result code:", rc)
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    message_type = msg.topic.split("/")[-1]

    if message_type == "structured":
        save_reading(data)
        print("Saved structured reading to MySQL:", data)
    elif message_type == "flexible":
        save_nutrients(data)
        print("Saved nutrient reading to MongoDB:", data)
    elif message_type == "alert":
        save_alert(data)
        print("Saved alert to MongoDB:", data)
    elif message_type == "registration":
        save_registration(data)
        print("Saved registration to Neo4j:", data)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

if __name__ == "__main__":
    client.connect(BROKER, PORT)
    print("Subscriber started, waiting for messages...")
    client.loop_forever()
