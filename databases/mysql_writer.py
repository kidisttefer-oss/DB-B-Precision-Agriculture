"""
Writes structured sensor readings into MySQL.
Fixed schema (soil_moisture, temperature, light_lux) -> relational table.
"""

import os
import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user="root",
        password="camposense",
        database="camposense",
    )


def save_reading(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO readings (zone_id, sensor_id, soil_moisture, temperature, light_lux)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            data["zone_id"],
            data["sensor_id"],
            data["soil_moisture"],
            data["temperature"],
            data["light_lux"],
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()
