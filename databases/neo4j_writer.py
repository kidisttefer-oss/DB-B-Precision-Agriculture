"""
Writes the farm topology into Neo4j.
Fields, crop zones, sensors and irrigation units are nodes; the
relationships between them are what a graph database models best.
"""

import os
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=("neo4j", "camposense123"),
)


def save_registration(data):
    with driver.session() as session:
        session.run(
            """
            MERGE (f:Field {name: $field})
            MERGE (z:Zone {id: $zone_id})
            MERGE (s:Sensor {id: $sensor_id})
            MERGE (i:Irrigation {id: $irrigation_id})
            MERGE (f)-[:HAS_ZONE]->(z)
            MERGE (z)-[:HAS_SENSOR]->(s)
            MERGE (z)-[:WATERED_BY]->(i)
            """,
            field=data["field"],
            zone_id=data["zone_id"],
            sensor_id=data["sensor_id"],
            irrigation_id=data["irrigation_id"],
        )
