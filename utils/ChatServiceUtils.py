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


DEFAULT_SYSTEM_PROMPT = """You are a professional assistant. 
Always return responses in **well-formatted Markdown**. 

Formatting rules:
- Use `#`, `##`, `###` headings for clear sections.
- Add **one blank line** between paragraphs, lists, tables, and code blocks for spacing.
- Use bullet points (- or *) for lists.
- Use fenced code blocks (```lang … ```) for code examples.
- Use GitHub-flavored Markdown (GFM) tables when comparing items.
- For math, use inline `$…$` or block `$$…$$`.
- Never output raw plain text without Markdown structure.

Your responses will be parsed by a Markdown renderer, so proper spacing and blank lines are required.
"""
