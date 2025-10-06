from pydantic import BaseModel



class HandleLikeRequestModel(BaseModel):
    chatId:str
    messageId:str
    liked:bool = False
    disLiked:bool = False
    