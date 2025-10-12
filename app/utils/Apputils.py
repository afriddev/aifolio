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






SEARCH_RAG_QUERY  = """
WITH q AS (
  SELECT $1::vector AS query
),
top_chunks AS (
  SELECT
    c.id                  AS chunk_id,
    c.text                AS chunk_text,
    NULL::text            AS question_text,
    1.0 - (c.embedding <#> q.query) AS score
  FROM q
  CROSS JOIN LATERAL (
    SELECT *
    FROM public.chunks
    WHERE embedding IS NOT NULL
    ORDER BY embedding <#> q.query
    LIMIT $2
  ) c
),
top_questions AS (
  SELECT
    cq.chunk_id,
    ch.text               AS chunk_text,
    cq.text               AS question_text,
    1.0 - (cq.embedding <#> q.query) AS score
  FROM q
  CROSS JOIN LATERAL (
    SELECT *
    FROM public.questions
    WHERE embedding IS NOT NULL
    ORDER BY embedding <#> q.query
    LIMIT $2
  ) cq
  JOIN public.chunks ch ON ch.id = cq.chunk_id
),
all_matches AS (
  SELECT * FROM top_chunks
  UNION ALL
  SELECT * FROM top_questions
)
SELECT
  chunk_id,
  chunk_text,
  question_text,
  score
FROM all_matches
ORDER BY score DESC
LIMIT $2;

"""