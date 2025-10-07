from pydantic import BaseModel



class GenerateApiKeyResponseModel(BaseModel):
    key:str
    hash:str
    salt:bytes


class HandleContextKeyGenerationRequestModel(BaseModel):
    keyId:str
    keyDetails:GenerateApiKeyResponseModel
    chatId: str
    context:str
    name:str

class UpdateApiKeyRequestModel(BaseModel):
    id:str
    method:str




