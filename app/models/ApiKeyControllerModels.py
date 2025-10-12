from pydantic import BaseModel


class GenerateApiKeyResponseModel(BaseModel):
    key: str
    hash: str
    salt: bytes


class UpdateApiKeyRequestModel(BaseModel):
    id: str
    method: str


class GenerateApiKeyRequestModel(BaseModel):
    name: str
    filesType: str = "SINGLE"
    methodType: str = "CONTEXT"
    pdfFileIds: list[str] | None = None
    csvFileIds: list[str] | None = None
    txtFileIds: list[str] | None = None
    ytVideoFileIds: list[str] | None = None
    keyId: str | None = None
    singleFileId: str | None = None


class HandleFileProcessingRequestModel(BaseModel):
    id: str
