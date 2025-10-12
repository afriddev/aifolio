import random
from openai import AsyncOpenAI
from utils import GetNKey, GetNUrl, GetNKey1
from implementations import EmbeddingImpl
from models import (
    EmbeddingRequestModel,
    EmbeddingResponseModel,
    EmbeddingDataModel,
    EmbeddingUsageModel,
    RerankResponseModel,
    RerankRequestModel,
    RerankResultModel,
    FindTopKresultsFromVectorsResponseModel,
    FindTopKresultsFromVectorsRequestModel,
)
from typing import cast, Any

from langchain_nvidia_ai_endpoints import NVIDIARerank
from langchain_core.documents import Document
import numpy as np
import faiss


openAiClient = AsyncOpenAI(base_url=GetNUrl(), api_key=GetNKey())
rerankClient = NVIDIARerank(api_key=GetNKey(), model="")


class Embedding(EmbeddingImpl):

    async def Embed(self, request: EmbeddingRequestModel) -> EmbeddingResponseModel:
        try:
            nvidiaApiKeys = [GetNKey(), GetNKey1()]
            openAiClient.api_key = random.choice(nvidiaApiKeys)
            response = await openAiClient.embeddings.create(
                model=request.model,
                input=request.texts,
                encoding_format="float",
                extra_body={"input_type": request.type, "truncate": "NONE"},
            )

            return EmbeddingResponseModel(
                data=[
                    EmbeddingDataModel(embedding=data.embedding, index=i)
                    for i, data in enumerate(response.data)
                ],
                model=request.model,
                usage=EmbeddingUsageModel(
                    prompt_tokens=response.usage.prompt_tokens,
                    total_tokens=response.usage.total_tokens,
                ),
            )
        except Exception as e:
            print(f"Error occurred: {e}")
            return EmbeddingResponseModel(
                data=None,
                model=request.model,
                usage=None,
            )

    async def RerankDocs(self, request: RerankRequestModel) -> RerankResponseModel:

        try:
            rerankClient.model = request.model

            response = rerankClient.compress_documents(
                query=request.query,
                documents=[Document(page_content=doc) for doc in request.docs],
            )
            temp: list[RerankResultModel] = []
            for doc in response:
                temp.append(
                    RerankResultModel(
                        doc=doc.page_content,
                        score=cast(Any, doc).metadata.get("relevance_score"),
                    )
                )
            return RerankResponseModel(results=temp)
        except Exception as e:
            print(e)
            return RerankResponseModel(results=[])

    def FindTopKResultsFromVectors(
        self, request: FindTopKresultsFromVectorsRequestModel
    ) -> FindTopKresultsFromVectorsResponseModel:
        try:
            sourceVec = np.array(request.sourceVectors, dtype="float32")
            queryVec = np.array([request.queryVector], dtype="float32")
            dim = sourceVec.shape[1]
            faissIndex: Any = faiss.IndexFlatL2(dim)
            faissIndex.add(sourceVec)
            distance, indeces = faissIndex.search(queryVec, request.topK)
            return FindTopKresultsFromVectorsResponseModel(
                distances=distance[0], indeces=indeces[0]
            )

        except Exception as e:
            print(e)
            return FindTopKresultsFromVectorsResponseModel(distances=None, indeces=None)