from abc import ABC, abstractmethod
from typing import Any, cast
from cachetools import TTLCache

cacheStore = cast(
    Any, TTLCache(maxsize=float("inf"), ttl=2 * 24 * 60 * 60)
)  # 2 days in seconds


class CacheServiceImpl(ABC):
    @abstractmethod
    def GetKeyDetails(self, key: str) -> str | None:
        pass

    def SetKeyDetails(self, key: str, value: str) -> None:
        pass


class CacheService(CacheServiceImpl):
    def SetKeyDetails(self, key: str, value: str) -> None:
        cacheStore[key] = value

    def GetKeyDetails(self, key: str) -> str | None:
        return cacheStore.get(key, None)

cacheService  = CacheService()