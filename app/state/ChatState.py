import asyncio
from collections import defaultdict

chatDetectedTools = defaultdict(lambda: None)
chatCompletionEvents = defaultdict(lambda: asyncio.Event())