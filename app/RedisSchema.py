from pydantic import BaseModel


# Pass keyId you will get key details
class ApiKeySchema(BaseModel):
    id: str
    key: str
    hash: str
    salt: str
    status: str


# Pass apikey you will get keyId
class KeyDetailsSchema(BaseModel):
    id: str


# passs keyId you will get all data
class ApiKeyDataSchema(BaseModel):
    id: str
    keyId: str
    data: str
