from abc import ABC, abstractmethod


class AppUtilsImpl(ABC):
    
    @abstractmethod
    def CountTokens(self, text: str) -> int:
        pass
