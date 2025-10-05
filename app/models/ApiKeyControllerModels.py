from pydantic import BaseModel



class GenerateApiKeyResponseModel(BaseModel):
    key:str
    hash:str
    salt:bytes


class HandleContextKeyGenerationRequestModel(BaseModel):
    chatId: str
    context:str
    description:str












# from your_module import HandleKeyInterface  # Replace with actual import

# # Instantiate
# hki = HandleKeyInterface()

# # Generate a secure key and salt
# generated_key: str = hki.GenerateKey(length=64)
# stored_salt: bytes = hki.GenerateSalt()
# stored_hash: str = hki.DeriveKeyHash(generated_key, stored_salt)

# # In production: Store generated_key (temporarily, if needed), stored_hash, and stored_salt in DB
# print(f"Generated Key: {generated_key}")
# print(f"Stored Salt (hex): {stored_salt.hex()}")
# print(f"Stored Hash: {stored_hash}")

# # Validate (True for match)
# is_valid: bool = hki.ValidateApiKey(generated_key, stored_hash, stored_salt)
# print(f"Valid: {is_valid}")

# # Validate invalid (False)
# invalid_key: str = "invalid"
# is_invalid: bool = hki.ValidateApiKey(invalid_key, stored_hash, stored_salt)
# print(f"Invalid: {is_invalid}")