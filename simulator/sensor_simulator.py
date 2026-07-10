"""
Simulates IoT sensors installed on a Sicilian farm, across two fields.

Publishes distinct kinds of messages every 5 seconds, deliberately
shaped to fit a different database each:

  camposense/{zone}/structured    -> soil moisture + temperature + light  -> MySQL
  camposense/{zone}/flexible      -> a random subset of nutrient readings -> MongoDB
  camposense/{zone}/alert         -> irrigation / heat alerts             -> MongoDB
  camposense/{zone}/registration  -> field/zone/sensor relationships      -> Neo4j
"""

import json
import os
import random
import time
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = 1883

# Two fields, each with crop zones - this hierarchy is what Neo4j will model
FIELDS = {
    "field-north": ["zone-lemons", "zone-olives"],
    "field-south": ["zone-vines"],
}

MOISTURE_THRESHOLD = 30   # percent - below this, irrigation is needed
TEMP_THRESHOLD = 38       # degrees C - Sicilian summer heat stress

client = mqtt.Client()
client.connect(BROKER, PORT)


def send_registration():
    """Sent once at startup - tells Neo4j the field/zone/sensor hierarchy."""
    for field, zones in FIELDS.items():
        for zone in zones:
            payload = {
                "field": field,
                "zone_id": zone,
                "sensor_id": f"{zone}-sensor",
                "irrigation_id": f"{zone}-drip",
            }
            client.publish(f"camposense/{zone}/registration", json.dumps(payload))


def make_structured_reading(zone):
    """Fixed schema every time -> fits a SQL table perfectly."""
    return {
        "zone_id": zone,
        "sensor_id": f"{zone}-sensor",
        "soil_moisture": round(random.uniform(15, 60), 1),
        "temperature": round(random.uniform(20, 42), 1),
        "light_lux": round(random.uniform(5000, 90000), 0),
    }


def make_flexible_reading(zone):
    """
    Different soil probes report different nutrients, so the set of
    fields is NOT fixed - this is exactly the kind of data a document
    database handles well and a rigid SQL table would struggle with.
    """
    possible_fields = {
        "nitrogen_ppm": lambda: round(random.uniform(10, 80), 0),
        "phosphorus_ppm": lambda: round(random.uniform(5, 50), 0),
        "potassium_ppm": lambda: round(random.uniform(50, 250), 0),
    }
    chosen_keys = random.sample(list(possible_fields.keys()), k=random.randint(1, 3))

    reading = {"zone_id": zone, "sensor_id": f"{zone}-sensor"}
    for key in chosen_keys:
        reading[key] = possible_fields[key]()
    return reading


def check_alert(zone, structured):
    if structured["soil_moisture"] < MOISTURE_THRESHOLD:
        return {
            "zone_id": zone,
            "alert_type": "irrigation_needed",
            "value": structured["soil_moisture"],
            "threshold": MOISTURE_THRESHOLD,
        }
    if structured["temperature"] > TEMP_THRESHOLD:
        return {
            "zone_id": zone,
            "alert_type": "heat_stress",
            "value": structured["temperature"],
            "threshold": TEMP_THRESHOLD,
        }
    return None


if __name__ == "__main__":
    all_zones = [zone for zones in FIELDS.values() for zone in zones]

    send_registration()
    print("Sensor simulator started. Publishing every 5 seconds...")

    while True:
        for zone in all_zones:
            structured = make_structured_reading(zone)
            client.publish(f"camposense/{zone}/structured", json.dumps(structured))
            print("Structured (-> MySQL):", structured)

            flexible = make_flexible_reading(zone)
            client.publish(f"camposense/{zone}/flexible", json.dumps(flexible))
            print("Flexible (-> MongoDB):", flexible)

            alert = check_alert(zone, structured)
            if alert:
                client.publish(f"camposense/{zone}/alert", json.dumps(alert))
                print("ALERT (-> MongoDB):", alert)

        time.sleep(5)
