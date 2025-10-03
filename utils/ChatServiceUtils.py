import os
from dotenv import load_dotenv


load_dotenv()


CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
NVIDIA_URL = os.getenv("NVIDIA_URL", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")


def GetCerebrasAPIKey():
    return CEREBRAS_API_KEY


def GetNvidiaURL():
    return NVIDIA_URL


def GetNvidiaAPIKey():
    return NVIDIA_API_KEY
