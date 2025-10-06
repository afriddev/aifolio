from app.implementations import WebSocketRouterControllerImpl
from app.services import WebSocketControllerService
from app.models import HandleLikeRequestModel
import json
from typing import Any


class WebSocketRouterController(WebSocketRouterControllerImpl):
    def __init__(self):
        self.webSocketController = WebSocketControllerService()

    def RouteMessage(self, data: str):
        responseData: Any = json.loads(data)
        print(data)
        type = responseData.get("type")
        if (type == "like" or type == "disLike") and responseData is not None:
            request = HandleLikeRequestModel(
                chatId=responseData.get("chatId"),
                messageId=responseData.get("messageId"),
                liked=responseData.get("liked"),
                disLiked=responseData.get("disLiked"),
            )
            if type == "like":
                self.webSocketController.HandleLikeChatMessage(request=request)
            else:
                self.webSocketController.HandleDislikeChatMessage(request=request)
