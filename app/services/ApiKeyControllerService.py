from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hmac
import string
import os
from bson.binary import Binary
from app.models import GenerateApiKeyResponseModel

from app.implementations import ApiKeyControllerServiceImpl, HandleKeyInterfaceImpl


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
            backend=backend
        )
        derivedKey = kdf.derive(key.encode('utf-8'))
        return derivedKey.hex()

    def GenerateKey(self, length: int = 64) -> GenerateApiKeyResponseModel:
        randomBytes = os.urandom(length)
        characters = string.ascii_letters + string.digits
        randomString = ''.join(characters[b % len(characters)] for b in randomBytes)
        key = self.prefix + randomString

        return GenerateApiKeyResponseModel(key=key, hash=self.DeriveKeyHash(key, self.GenerateSalt()), salt=self.GenerateSalt())

    def ValidateKey(self, key: str, storedHash: str, storedSalt: bytes) -> bool:
        if not key.startswith(self.prefix):
            return False
        provided_hash = self.DeriveKeyHash(key, storedSalt)
        return hmac.compare_digest(provided_hash.encode(), storedHash.encode())



class ApiKeyControllerService(ApiKeyControllerServiceImpl):
    
