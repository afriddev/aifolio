from app.implementations import WebSocketControllerImpl
from database import chatMessagesCollection
from app.models import HandleLikeRequestModel


class WebSocketControllerService(WebSocketControllerImpl):

    def HandleLikeChatMessage(self, request: HandleLikeRequestModel):
        try:
            print(request)
            chatMessagesCollection.update_one(
                {"chatId": request.chatId, "id": request.messageId},
                {"$set": {"liked": request.liked, "disLiked": request.disLiked}},
            )
        except Exception as e:
            print(f"Exception in HandleLikeChatMessage: {e}")

    def HandleDislikeChatMessage(self, request: HandleLikeRequestModel):
        try:
            chatMessagesCollection.update_one(
                {"chatId": request.chatId, "id": request.messageId},
                {"$set": {"disLiked": request.disLiked, "liked": request.liked}},
            )
        except Exception as e:
            print(f"Exception in HandleDislikeChatMessage: {e}")
