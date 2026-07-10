"""
Writes flexible documents into MongoDB.
Nutrient readings have varying fields (each probe reports a different
subset), and alerts have varying event data - both fit a document store.
"""

import os
from pymongo import MongoClient

client = MongoClient(f"mongodb://{os.getenv('MONGO_HOST', 'localhost')}:27017")
db = client["camposense"]

nutrients_collection = db["nutrients"]
alerts_collection = db["alerts"]


def save_nutrients(data):
    nutrients_collection.insert_one(data)


def save_alert(data):
    alerts_collection.insert_one(data)
