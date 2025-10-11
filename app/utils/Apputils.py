from app.implementations import AppUtilsImpl
import tiktoken
from fastapi.responses import StreamingResponse
import json


class AppUtils(AppUtilsImpl):

    def CountTokens(self, text: str) -> int:
        return len(tiktoken.get_encoding("cl100k_base").encode(text))

    async def StreamErrorMessage(self, error: str) -> StreamingResponse:
        async def streamError(error: str):
            yield f"data: {json.dumps({'type': 'content', 'data': error})}\n\n"

        return StreamingResponse(
            streamError(error),
        )
