from abc import ABC, abstractmethod


class ChatServicesImpl(ABC):

    @abstractmethod
    def chat(self, prompt: str) -> str:
        pass
