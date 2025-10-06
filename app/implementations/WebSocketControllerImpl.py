from abc import ABC, abstractmethod
from app.models import HandleLikeRequestModel


class WebSocketRouterControllerImpl(ABC):
    @abstractmethod
    def RouteMessage(self, data: str):
        pass


class WebSocketControllerImpl(ABC):

    @abstractmethod
    def HandleLikeChatMessage(self, request: HandleLikeRequestModel):
        pass

    @abstractmethod
    def HandleDislikeChatMessage(self, request: HandleLikeRequestModel):
        pass
