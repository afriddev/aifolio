import redis
from abc import ABC, abstractmethod
from typing import Any

apiKeyServerConfig = redis.Redis(host="localhost", port=6000, db=0)
apiKeyDataServerConfig = redis.Redis(host="localhost", port=6000, db=1)
keyDetailsServerConfig = redis.Redis(host="localhost", port=6000, db=1)


class RedisCacheImpl(ABC):

    @abstractmethod
    def setKeyDetails(self, key: str, value: str):
        pass

    @abstractmethod
    def getKeyDetails(self, key: str) -> str | None:
        pass
    
    @abstractmethod
    def setApiKey(self, key: str, value: str):
        pass

    @abstractmethod
    def getApiKeyValue(self, key: str) -> str | None:
        pass

    @abstractmethod
    def setApiKeyData(self, key: str, value: str):
        pass
    

    @abstractmethod
    def getApiKeyDataValue(self, key: str) -> str | None:
        pass

    @abstractmethod
    def deleteApiKey(self, key: str):
        pass


    @abstractmethod
    def flushAll(self):
        pass


class RedisCache(RedisCacheImpl):
    def __init__(self):
        self.apiKeyServer: Any = apiKeyServerConfig
        self.apiKeyDataServer: Any = apiKeyDataServerConfig
        self.keyDetailsServer: Any = keyDetailsServerConfig

    def setKeyDetails(self, key: str, value: str):
        self.keyDetailsServer.set(key, value)

    def getKeyDetails(self, key: str) -> str | None:
        return self.keyDetailsServer.get(key)
    
    
    def setApiKey(self, key: str, value: str):
        self.apiKeyServer.set(key, value)

    def getApiKeyValue(self, key: str) -> str | None:
        return self.apiKeyServer.get(key)

    def setApiKeyData(self, key: str, value: str):
        self.apiKeyDataServer.set(key, value)

    def getApiKeyDataValue(self, key: str) -> str | None:
        return self.apiKeyDataServer.get(key)

    def deleteApiKey(self, key: str):
        self.apiKeyServer.delete(key)

    def deleteApiKeyData(self, key: str):
        self.apiKeyDataServer.delete(key)

    def flushAll(self):
        self.apiKeyServer.flushdb()
        self.apiKeyDataServer.flushdb()


redisClient = RedisCache()
