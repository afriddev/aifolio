import os
from dotenv import load_dotenv
from typing import Any, cast

from pymongo import MongoClient

load_dotenv()
uri = os.getenv("MONGO_DB_URL")

mongoClient = cast(Any, MongoClient(uri))


# Aifolio Database
aifolioDb = mongoClient["aifolio"]
# Aifolio collections
dataFilesCollection = aifolioDb["dataFiles"]
apiKeysCollection = aifolioDb["apiKeys"]
singleApiKeyDataCollection = aifolioDb["singleApiKeyData"]
chatMessagesCollection = aifolioDb["chatMessages"]
chatsCollection = aifolioDb["chats"]
chatFilesCollection = aifolioDb["chatFiles"]