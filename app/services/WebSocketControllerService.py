from app.implementations import WebSocketControllerImpl
from database import mongoClient
from app.models import HandleLikeRequestModel


class WebSocketControllerService(WebSocketControllerImpl):

    def __init__(self):
        self.db = mongoClient["aifolio"]

    def HandleLikeChatMessage(self, request: HandleLikeRequestModel):
        try:
            print(request)
            chatMessageCollection = self.db["chatMessages"]
            chatMessageCollection.update_one(
                {"chatId": request.chatId, "id": request.messageId},
                {"$set": {"liked": request.liked, "disLiked": request.disLiked}},
            )
        except Exception as e:
            print(f"Exception in HandleLikeChatMessage: {e}")

    def HandleDislikeChatMessage(self, request: HandleLikeRequestModel):
        try:
            print(request)
            
            chatMessageCollection = self.db["chatMessages"]
            chatMessageCollection.update_one(
                {"chatId": request.chatId, "id": request.messageId},
                {"$set": {"disLiked": request.disLiked, "liked": request.liked}},
            )
        except Exception as e:
            print(f"Exception in HandleDislikeChatMessage: {e}")
