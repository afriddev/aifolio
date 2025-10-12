import os
from typing import Any, cast
from dotenv import load_dotenv

load_dotenv()


C_KEY = cast(Any, os.getenv("C_KEY"))
C_KEY1 = cast(Any, os.getenv("C_KEY1"))
C_KEY2 = cast(Any, os.getenv("C_KEY2"))
C_KEY3 = cast(Any, os.getenv("C_KEY3"))
C_KEY4 = cast(Any, os.getenv("C_KEY4"))
N_KEY = cast(Any, os.getenv("N_KEY"))
N_KEY1 = cast(Any, os.getenv("N_KEY1"))
N_URL = cast(Any, os.getenv("N_URL"))
G_URL = cast(Any, os.getenv("G_URL"))
G_KEY = cast(Any, os.getenv("G_KEY"))


def GetCKey() -> str:
    return C_KEY


def GetCKey1() -> str:
    return C_KEY1


def GetCKey2() -> str:
    return C_KEY2


def GetCKey3() -> str:
    return C_KEY3


def GetCKey4() -> str:
    return C_KEY4


def GetNKey() -> str:
    return N_KEY


def GetNKey1() -> str:
    return N_KEY1


def GetNUrl() -> str:
    return N_URL

def GetGroqApiKey() -> str:
    return G_KEY


def GetGroqBaseUrl() -> str:
    return G_URL
