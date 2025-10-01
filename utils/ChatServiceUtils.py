import os
from dotenv import load_dotenv


load_dotenv()


NVIDIA_URL = os.getenv("NVIDIA_URL", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")


def GetNvidiaURL():
    return NVIDIA_URL

def GetNvidiaAPIKey():
    return NVIDIA_API_KEY