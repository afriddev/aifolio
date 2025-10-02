import os
from dotenv import load_dotenv

from pymongo import AsyncMongoClient

load_dotenv()
uri = os.getenv("MONGO_DB_URL")

mongoClient = AsyncMongoClient(uri)
