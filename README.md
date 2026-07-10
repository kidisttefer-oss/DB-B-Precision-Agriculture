# CampoSense

Precision agriculture monitoring system (project DB-B4).
IoT sensors on a Sicilian farm publish data over MQTT; a Python
subscriber routes each message, by topic, into the database that best
fits its shape: MySQL, MongoDB or Neo4j.

## Architecture

```
sensor_simulator.py                     subscriber.py
 (fake IoT sensors)                    (topic-based routing)
        |                                     |
        |  camposense/{zone}/structured       |--> MySQL    (fixed-schema readings)
        |  camposense/{zone}/flexible         |--> MongoDB  (nutrients, varying fields)
        +--> Mosquitto (MQTT broker) -------->|--> MongoDB  (irrigation/heat alerts)
           camposense/{zone}/alert            |--> Neo4j    (farm topology)
           camposense/{zone}/registration
                                                     |
                                       Flask API (api/server.py)
                                                     |
                                       Dashboard (dashboard/index.html)
```

## Requirements

- Docker + Docker Compose

## How to run

```bash
docker compose up --build
```

Wait ~30 seconds for all services to start. Then:

- Dashboard: open `dashboard/index.html` in a browser
- API: http://localhost:5000/api/readings
- Neo4j browser: http://localhost:7474 (user `neo4j`, password `camposense123`)

## Project structure

| Path | Purpose |
|---|---|
| `simulator/sensor_simulator.py` | Simulates soil sensors, publishes MQTT messages |
| `subscriber/subscriber.py` | Subscribes to all topics, routes messages by topic |
| `databases/mysql_writer.py` | Inserts structured readings into MySQL |
| `databases/mongo_writer.py` | Inserts nutrient docs and alerts into MongoDB |
| `databases/neo4j_writer.py` | Creates farm topology graph in Neo4j |
| `sql/schema.sql` | MySQL table + view + stored procedure |
| `api/server.py` | Flask API, one endpoint per database |
| `dashboard/` | Static dashboard polling the API every 5 s |
