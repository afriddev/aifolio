from app.implementations import ChatbotControllerImpl

from database import redisClient
import json


class ChatbotControllerService(ChatbotControllerImpl):

    def __init__(self):
        self.redisClient = redisClient

    def GetApiKeyId(self, key: str) -> str | None:
        tempKeyData = self.redisClient.getApiKeyId(key)
        if tempKeyData is not None:
            tempKeyData = json.loads(tempKeyData)
            return tempKeyData["id"]
        return None

    def GetApiKeyStatus(self, keyId: str) -> str:
        tempKeyData = self.redisClient.getApiKeyValue(keyId)
        if tempKeyData is not None:
            tempKeyData = json.loads(tempKeyData)
            return tempKeyData["status"]
        return "NOT_FOUND"

    def GetApiKeyData(self, keyId: str) -> str:
        tempKeyData = self.redisClient.getApiKeyDataValue(keyId)
        if tempKeyData is not None:
            tempKeyData = json.loads(tempKeyData)
            return tempKeyData["data"]
        return "ERROR"
