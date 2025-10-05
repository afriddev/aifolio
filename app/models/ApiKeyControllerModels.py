from pydantic import BaseModel



class GenerateApiKeyResponseModel(BaseModel):
    key:str
    hash:str
    salt:bytes


class HandleContextKeyGenerationRequestModel(BaseModel):
    chatId: str
    context:str
    description:str






