from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hmac
import string
import os
from bson.binary import Binary
from app.models import (
    GenerateApiKeyResponseModel,
    HandleContextKeyGenerationRequestModel,
)
from app.services.EmailService import EmailService
from database import mongoClient
from app.implementations import ApiKeyControllerServiceImpl, HandleKeyInterfaceImpl
from app.schemas import ApiKeySchema,ContextSchema
from uuid import uuid4


class HandleKeyInterface(HandleKeyInterfaceImpl):

    def __init__(self) -> None:
        self.prefix: str = "folioapi-"

    def GenerateSalt(self) -> bytes:
        return os.urandom(16)

    def DeriveKeyHash(self, key: str, salt: bytes) -> str:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=backend,
        )
        derivedKey = kdf.derive(key.encode("utf-8"))
        return derivedKey.hex()

    def GenerateKey(self, length: int = 64) -> GenerateApiKeyResponseModel:
        randomBytes = os.urandom(length)
        characters = string.ascii_letters + string.digits
        randomString = "".join(characters[b % len(characters)] for b in randomBytes)
        key = self.prefix + randomString

        return GenerateApiKeyResponseModel(
            key=key,
            hash=self.DeriveKeyHash(key, self.GenerateSalt()),
            salt=self.GenerateSalt(),
        )

    def ValidateKey(self, key: str, storedHash: str, storedSalt: bytes) -> bool:
        if not key.startswith(self.prefix):
            return False
        provided_hash = self.DeriveKeyHash(key, storedSalt)
        return hmac.compare_digest(provided_hash.encode(), storedHash.encode())


class ApiKeyControllerService(ApiKeyControllerServiceImpl):

    def __init__(self) -> None:
        self.handleKeyInterface = HandleKeyInterface()
        self.emailService = EmailService()
        self.db = mongoClient["aifolio"]

    def HandleContextKeyGeneration(
        self, request: HandleContextKeyGenerationRequestModel
    ) -> None:
        generatedKey = self.handleKeyInterface.GenerateKey()

        tempApiSchema = ApiKeySchema(
            id=str(uuid4()),
            chatId=request.chatId,
            key=generatedKey.key,
            hash=generatedKey.hash,
            salt=Binary(generatedKey.salt),
        )

        apiKeyCollection = self.db["contextKeys"]
        apiKeyCollection.update_one(
            {"chatId": tempApiSchema.chatId},
            {"$set": tempApiSchema.model_dump()},
            upsert=True,
        )
        contextSchema = ContextSchema(
            id=str(uuid4()), chatId=request.chatId, context=request.context, description=request.description
        )

        contextCollection = self.db["contextData"]
        contextCollection.update_one(
            {"chatId": contextSchema.chatId},
            {"$set": contextSchema.model_dump()},
            upsert=True,
        )

        title = "AiFolio API Key: Ready for Your Chatbot Integration!"
        subject = (
            f"AiFolio API Key Generated for '{request.description}' – Check Your Setup"
        )
        body = f"""Dear User,

Congratulations! Your AiFolio API key has been successfully generated for the chat "{request.description}". This key enables a lightweight, context-aware chatbot (<20k tokens) on your website—perfect for interactive queries from recruiters, customers, or visitors.

**Your API Key:**
{generatedKey.key}

**Quick Integration Steps:**
1. Copy the key above.
2. Add it to your AiFolio frontend component: `<AiFolio apiKey="{generatedKey.key}" />`.
3. Embed the component where needed (e.g., portfolio page).
4. Test with sample queries—your uploaded context is now live!

Your data is private and secure—we don't log or share it. If you need updates, upload new content and regenerate.

Questions? Reply to this email or chat with us.

Best regards,
AiFolio Team
"""
        self.emailService.SendMail(
            toEmail=request.chatId, title=title, subject=subject, body=body
        )
