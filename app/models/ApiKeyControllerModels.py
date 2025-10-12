from pydantic import BaseModel


class GenerateApiKeyResponseModel(BaseModel):
    key: str
    hash: str
    salt: bytes


class UpdateApiKeyRequestModel(BaseModel):
    id: str
    method: str


class GenerateApiKeyRequestModel(BaseModel):
    pdfFileIds: list[str] | None = None
    csvFileIds: list[str] | None = None
    txtFileIds: list[str] | None = None
    ytVideoFileIds: list[str] | None = None
    keyId: str | None = None
    name: str
    type:str = "SINGLE"


class HandleFileProcessingRequestModel(BaseModel):
    id: str
