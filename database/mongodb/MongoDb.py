import os
from dotenv import load_dotenv
from typing import Any,cast

from pymongo import MongoClient

load_dotenv()
uri = os.getenv("MONGO_DB_URL")

mongoClient = cast(Any,MongoClient(uri))
