import asyncio
from collections import defaultdict
from typing import cast, Any

ChatUsedTool = cast(Any, defaultdict(lambda: None))
ChatContent = cast(Any, defaultdict(str))
ChatReasoning = cast(Any, defaultdict(str))

ChatCompletionTokens = cast(Any, defaultdict(int))
ChatPromptTokens = cast(Any, defaultdict(int))
ChatTotalTokens = cast(Any, defaultdict(int))
ReasoningTokens = cast(Any, defaultdict(int))


ChatEvent = cast(Any, defaultdict(lambda: asyncio.Event()))
