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
from app.implementations import ApiKeyServicesImpl, HandleKeyInterfaceImpl
from app.schemas import ApiKeySchema, ApiKeyDataSchema
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


class ApiKeyServices(ApiKeyServicesImpl):

    def __init__(self) -> None:
        self.handleKeyInterface = HandleKeyInterface()
        self.emailService = EmailService()
        self.db = mongoClient["aifolio"]

    def HandleContextKeyGeneration(
        self, request: HandleContextKeyGenerationRequestModel
    ) -> None:
        generatedKey = self.handleKeyInterface.GenerateKey()
        tempApiKeyId = str(uuid4())

        tempApiSchema = ApiKeySchema(
            id=tempApiKeyId,
            chatId=request.chatId,
            key=generatedKey.key,
            hash=generatedKey.hash,
            salt=Binary(generatedKey.salt),
            name=request.name,
        )

        apiKeyCollection = self.db["apiKeys"]
        apiKeyCollection.update_one(
            {"chatId": tempApiSchema.chatId},
            {"$set": tempApiSchema.model_dump()},
            upsert=True,
        )
        tempApiKeyDataSchema = ApiKeyDataSchema(
            id=str(uuid4()),
            apiKeyId=tempApiKeyId,
            chatId=request.chatId,
            data=request.context,
        )

        contextCollection = self.db["apiKeyData"]
        contextCollection.update_one(
            {"chatId": tempApiKeyDataSchema.chatId},
            {"$set": tempApiKeyDataSchema.model_dump()},
            upsert=True,
        )

        title = "AiFolio API Key: Ready for Your Chatbot Integration!"
        subject = f"AiFolio API Key Generated for '{request.name}' – Check Your Setup"

        masked = (
            (generatedKey.key[:4] + "…" + generatedKey.key[-4:])
            if len(generatedKey.key) > 10
            else generatedKey.key
        )
        from string import Template

        body = Template(
            """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>AiFolio API Key</title>
  <style>
    :root { color-scheme: light dark; }
    body { margin:0; padding:0; background:#f3f6fb; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; color:#0f172a; }
    .container { width:100%; max-width:680px; margin:28px auto; background:#fff; border-radius:12px; box-shadow:0 8px 24px rgba(16,24,40,0.06); overflow:hidden; border:1px solid rgba(15,23,42,0.04); }
    .header { padding:20px 24px; display:flex; align-items:center; gap:14px; background: linear-gradient(90deg,#0ea5a4 0%,#7c3aed 100%); color:#fff; }
    .logo-box { width:44px; height:44px; border-radius:8px; display:flex; align-items:center; justify-content:center; background:rgba(255,255,255,0.12); font-weight:700; color:rgba(255,255,255,0.95); }
    .brand { font-weight:700; font-size:16px; letter-spacing:0.2px; }
    .content { padding:24px; }
    h1 { margin:0 0 10px 0; font-size:18px; color:#08112a; }
    p { margin:0 0 12px 0; color:#374151; font-size:15px; }
    .key-card { margin:18px 0; padding:14px; background:#f8fafc; border-radius:10px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", "Helvetica Neue", monospace; font-size:14px; color:#0b1220; border:1px solid rgba(15,23,42,0.04); }
    /* Prevent clients breaking long keys — allow horizontal scroll instead */
    .key-pre { display:block; overflow-x:auto; white-space:nowrap; -webkit-overflow-scrolling:touch; padding-bottom:4px; }
    .meta { display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-top:8px; }
    .pill { background:#eef2ff; color:#3730a3; padding:6px 10px; border-radius:999px; font-size:13px; font-weight:600; }
    .instructions { margin-top:16px; color:#374151; font-size:15px; }
    ol { margin:8px 0 0 18px; }
    li { margin:8px 0; }
    .cta { display:inline-block; margin-top:14px; text-decoration:none; background:#0f172a; color:#fff; padding:10px 16px; border-radius:8px; font-weight:600; font-size:14px; }
    .note { margin-top:14px; font-size:13px; color:#6b7280; line-height:1.4; }
    .footer { padding:16px 24px; font-size:13px; color:#6b7280; background:#fbfdff; display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
    .small { font-size:13px; color:#9ca3af; }
    code.inline { background:transparent; font-family:inherit; font-size:inherit; color:inherit; }
    @media (max-width:480px) { .container{margin:12px;} .header{padding:14px;} .content{padding:16px;} }
  </style>
</head>
<body>
  <div class="container" role="article" aria-label="AiFolio API Key notification">
    <div class="header">
      <!-- simplified logo box (removed menu icon) -->
      <div class="logo-box" aria-hidden="true">AF</div>
      <div>
        <div class="brand">AiFolio</div>
        <div class="small" style="color:rgba(255,255,255,0.9);font-size:13px;margin-top:2px;">API key generated</div>
      </div>
    </div>

    <div class="content">
      <h1>API Key for “$description”</h1>
      <p>Hello,</p>
      <p>Your AiFolio API key is ready. Use it to integrate the lightweight chatbot (context ≤ 20k tokens) into your site or portfolio.</p>

      <div class="key-card" role="region" aria-label="API Key">
        <div style="font-size:13px;color:#6b7280;margin-bottom:6px;">API Key</div>
        <!-- horizontal scroll prevents word-wrapping into multiple visual lines -->
        <div class="key-pre"><strong>$key</strong></div>
      </div>

      <div class="meta" aria-hidden="false">
        <div class="pill">Preview: $masked_key</div>
        <div class="small">Safe to email to the account owner only. Consider rotating keys periodically.</div>
      </div>

      <div class="instructions" aria-hidden="false">
        <strong>Quick integration — 3 steps</strong>
        <ol>
          <li>Copy the API key above.</li>
          <li>Add it to your AiFolio component: <code class="inline">&lt;AiFolio apiKey="$key" /&gt;</code></li>
          <li>Embed the component on your page and test with sample queries.</li>
        </ol>

        <a href="https://your-docs.example.com/aifolio/setup" class="cta" target="_blank" rel="noopener noreferrer">View integration guide</a>

        <p class="note">If you need the key regenerated or want to update the context, upload the new documents and request a new key. We don't store or share your content beyond the purpose of this service.</p>
      </div>
    </div>

    <div class="footer" role="contentinfo">
      <div class="small">Need help? Reply to this email or visit AiFolio Docs.</div>
      <div class="small">AiFolio Team • &copy; $year</div>
    </div>
  </div>
</body>
</html>
"""
        ).substitute(
            description=request.name,
            key=generatedKey.key,
            masked_key=masked,
            year=2025,
        )

        print(
            self.emailService.SendMail(
                toEmail="afridayan01@gmail.com", title=title, subject=subject, body=body
            )
        )
