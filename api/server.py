"""
Small API the dashboard calls. Each endpoint reads from exactly one
database, so the dashboard can show all three updating live, side by side.
"""

import os

from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
from pymongo import MongoClient
from neo4j import GraphDatabase

app = Flask(__name__)
CORS(app)


def get_mysql_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user="root",
        password="camposense",
        database="camposense",
    )


mongo_client = MongoClient(f"mongodb://{os.getenv('MONGO_HOST', 'localhost')}:27017")
nutrients_collection = mongo_client["camposense"]["nutrients"]
alerts_collection = mongo_client["camposense"]["alerts"]

neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=("neo4j", "camposense123"),
)


# ---- MySQL: structured soil/temperature/light readings ----
@app.route("/api/readings")
def get_readings():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM readings ORDER BY recorded_at DESC LIMIT 20")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    for row in rows:
        row["recorded_at"] = row["recorded_at"].isoformat()
    return jsonify(rows)


# ---- MySQL: averages per crop zone (uses the SQL view) ----
@app.route("/api/averages")
def get_averages():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM zone_averages")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)


# ---- MongoDB: flexible nutrient readings ----
@app.route("/api/nutrients")
def get_nutrients():
    docs = list(nutrients_collection.find().sort("_id", -1).limit(10))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return jsonify(docs)


# ---- MongoDB: irrigation / heat alerts ----
@app.route("/api/alerts")
def get_alerts():
    docs = list(alerts_collection.find().sort("_id", -1).limit(10))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return jsonify(docs)


# ---- Neo4j: field -> zone -> sensor/irrigation topology ----
@app.route("/api/topology")
def get_topology():
    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (f:Field)-[:HAS_ZONE]->(z:Zone)-[:HAS_SENSOR]->(s:Sensor)
            MATCH (z)-[:WATERED_BY]->(i:Irrigation)
            RETURN f.name AS field, z.id AS zone_id, s.id AS sensor_id, i.id AS irrigation_id
            """
        )
        data = [
            {
                "field": r["field"],
                "zone_id": r["zone_id"],
                "sensor_id": r["sensor_id"],
                "irrigation_id": r["irrigation_id"],
            }
            for r in result
        ]
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

