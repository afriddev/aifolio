from pydantic import BaseModel


class GenerateApiKeyResponseModel(BaseModel):
    key: str
    hash: str
    salt: bytes


class UpdateApiKeyRequestModel(BaseModel):
    id: str
    method: str


class GenerateApiKeyRequestModel(BaseModel):
    fileId: str | None = None
    keyId: str | None = None
    name: str


class HandleFileProcessingRequestModel(BaseModel):
    id: str
