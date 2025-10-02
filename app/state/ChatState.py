import asyncio
from collections import defaultdict

ChatUsedTool = defaultdict(lambda: None)
chatContent = defaultdict(str)
chatReasoning = defaultdict(str)
ChatEvent = defaultdict(lambda: asyncio.Event())