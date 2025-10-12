from models import QaCsvChunksResponseModel, ChatRequestModel, ChatMessageModel
from models import (
    ExtractQaFromChunkResponseModel,
    QaChunkModel,
    QaQuestionsModel,
    AllChunksWithQuestionsModel,
)
from services import DocServices, ChatServices
from typing import Any, Tuple
from enums import CerebrasChatModelEnum, ChatMessageRoleEnum
import json
from utils import EXTRACT_QUESTIONS_FROM_CHUNK_PROMPT, CLEAN_YT_CHUNK_PROMPT
from uuid import uuid4
import time
import re
import unicodedata
from langchain_text_splitters import RecursiveCharacterTextSplitter
import string
import secrets
from implementations import (
    RagServicesImpl,
    ChunkServicesImpl,
    ExtractInstanceServiceImpl,
)


class RagServices(RagServicesImpl):

    def __init__(self):
        self.ChunkServices = ChunkServices()
        self.ExtractInstanceService = ExtractInstanceService()

    async def ExtractQuestionAndAnswersFromPdfFile(
        self, file: str
    ) -> AllChunksWithQuestionsModel:
        chunks = self.ChunkServices.ExtractChunksFromPdf(file=file)
        allChunks: list[QaChunkModel] = []
        allChunkQuestions: list[QaQuestionsModel] = []

        for chunk in chunks:
            messages: list[ChatMessageModel] = [
                ChatMessageModel(
                    role=ChatMessageRoleEnum.SYSTEM,
                    content=EXTRACT_QUESTIONS_FROM_CHUNK_PROMPT,
                ),
                ChatMessageModel(role=ChatMessageRoleEnum.USER, content=chunk),
            ]

            chunkQaInfo = await self.ExtractInstanceService.ExtractQuestionsFromChunk(
                messages=messages, retryLimit=0
            )

            chunkId = uuid4()
            allChunks.append(QaChunkModel(id=chunkId, text=chunkQaInfo.chunk))
            allChunkQuestions.extend(
                [
                    QaQuestionsModel(id=uuid4(), chunkId=chunkId, text=q)
                    for q in chunkQaInfo.questions
                ]
            )
        return AllChunksWithQuestionsModel(
            chunks=allChunks, questions=allChunkQuestions
        )

    async def ExtractQuestionsAndAnswersFromCsvFile(
        self, file: str
    ) -> AllChunksWithQuestionsModel:
        qa = self.ChunkServices.ExtractQuestionsAndAnswersFromCsvFile(file=file)

        allAnswers: list[QaChunkModel] = []
        allQuestions: list[QaQuestionsModel] = []

        for index, _ in enumerate(qa.answers):
            tempChunkId = uuid4()
            allAnswers.append(QaChunkModel(id=tempChunkId, text=qa.answers[index]))
            allQuestions.append(
                QaQuestionsModel(
                    id=uuid4(),
                    chunkId=tempChunkId,
                    text=qa.questions[index],
                )
            )
        return AllChunksWithQuestionsModel(chunks=allAnswers, questions=allQuestions)

    async def ExtractQuestionAndAnswersFromYtVideo(
        self, videoId: str
    ) -> AllChunksWithQuestionsModel:

        chunks = self.ChunkServices.ExtractChunksFromYtVideo(
            chunkSec=400, videoId=videoId
        )

        tempAllChunks: list[QaChunkModel] = []
        tempAllChunkQuestions: list[QaQuestionsModel] = []

        for chunk in chunks:
            cleanedChunk = await self.ExtractInstanceService.CleanYoutubeChunk(
                retryLimit=0,
                messages=[
                    ChatMessageModel(
                        role=ChatMessageRoleEnum.SYSTEM,
                        content=CLEAN_YT_CHUNK_PROMPT,
                    ),
                    ChatMessageModel(
                        role=ChatMessageRoleEnum.USER,
                        content=chunk,
                    ),
                ],
            )
            messages: list[ChatMessageModel] = [
                ChatMessageModel(
                    role=ChatMessageRoleEnum.SYSTEM,
                    content=EXTRACT_QUESTIONS_FROM_CHUNK_PROMPT,
                ),
                ChatMessageModel(
                    role=ChatMessageRoleEnum.USER,
                    content=cleanedChunk,
                ),
            ]

            chunkRagInfo = await self.ExtractInstanceService.ExtractQuestionsFromChunk(
                messages=messages, retryLimit=0
            )

            chunkId = uuid4()

            tempAllChunks.append(QaChunkModel(id=chunkId, text=chunkRagInfo.chunk))
            tempAllChunkQuestions.extend(
                [
                    QaQuestionsModel(id=uuid4(), chunkId=chunkId, text=question)
                    for question in chunkRagInfo.questions
                ]
            )
        return AllChunksWithQuestionsModel(
            chunks=tempAllChunks, questions=tempAllChunkQuestions
        )


class ChunkServices(ChunkServicesImpl):
    def __init__(self):
        self.docUtils = DocServices()

    def GenerateShortId(self, length: int = 8) -> str:
        alphabet = string.ascii_lowercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def ExtractChunkFromPdfText(
        self, file: str, chunkSize: int, chunkOLSize: int | None = 0
    ) -> Tuple[list[str], list[str]]:
        _PAGE_RE = re.compile(r"\bpage\s+\d+\s+of\s+\d+\b", re.IGNORECASE)
        _IMAGE_RE = re.compile(r"\s*(<<IMAGE-\d+>>)\s*", re.IGNORECASE)
        _BULLET_LINE_RE = re.compile(r"^[\s•\-\*\u2022\uf0b7FÞ]+(?=\S)", re.MULTILINE)
        _SOFT_HYPHEN_RE = re.compile(r"\u00AD")
        _HYPHEN_BREAK_RE = re.compile(r"(\w)-\n(\w)")
        _MULTI_NL_RE = re.compile(r"\n{3,}")
        _WS_NL_RE = re.compile(r"[ \t]+\n")
        _WS_RUN_RE = re.compile(r"[ \t]{2,}")

        def _normalizeText(raw: str) -> str:
            t = unicodedata.normalize("NFKC", raw)
            t = _SOFT_HYPHEN_RE.sub("", t)
            t = _PAGE_RE.sub(" ", t)
            t = _BULLET_LINE_RE.sub("", t)
            t = _HYPHEN_BREAK_RE.sub(r"\1\2", t)
            t = _IMAGE_RE.sub(r" \1 ", t)
            t = _WS_NL_RE.sub("\n", t)
            t = _MULTI_NL_RE.sub("\n\n", t)
            t = _WS_RUN_RE.sub(" ", t)
            t = re.sub(r"\s+", " ", t)
            return t.strip()

        def _mergeTinyChunks(chunks: list[str], minChars: int) -> list[str]:
            merged: list[str] = []
            carry = ""
            for ch in chunks:
                chs = ch.strip()
                if not chs:
                    continue
                if _IMAGE_RE.fullmatch(chs) or len(chs) < minChars:
                    if merged:
                        merged[-1] = (merged[-1].rstrip() + " " + chs).strip()
                    else:
                        carry = (carry + " " + chs).strip()
                else:
                    if carry:
                        chs = (carry + " " + chs).strip()
                        carry = ""
                    merged.append(chs)
            if carry:
                if merged:
                    merged[-1] = (merged[-1].rstrip() + " " + carry).strip()
                else:
                    merged = [carry]
            return merged

        text, images,_ = self.docUtils.ExtractTextAndImagesFromPdf(file)
        text = _normalizeText(text)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunkSize,
            chunk_overlap=chunkOLSize or 0,
            separators=["\n\n", "\n", " "],
            is_separator_regex=False,
            length_function=len,
        )
        chunks = splitter.split_text(text)
        chunks = _mergeTinyChunks(chunks, minChars=max(200, chunkSize // 3))
        return (
            chunks,
            images,
        )

    def ExtractChunksFromPdf(self, file: str) -> list[str]:
        chunks, images = self.ExtractChunkFromPdfText(
            file=file, chunkOLSize=100, chunkSize=2000
        )
        processedChunk: list[str] = []

        for chunk in chunks:
            processedChunk.append(chunk)
            matchedIndex = re.findall(r"<<[Ii][Mm][Aa][Gg][Ee]-([0-9]+)>>", chunk)
            indeces = list(map(int, matchedIndex))
            if len(indeces) == 0:
                processedChunk.append(chunk)
            else:
                chunkText = chunk
                for index in indeces:
                    imageUrl = self.docUtils.UploadImageToFileServer(
                        base64Str=images[index - 1],
                        name=f"{self.GenerateShortId()}.png",
                    )
                    token = f"<<image-{index}>>"
                    chunkText = chunkText.replace(
                        token, f"![Image]({imageUrl})" if imageUrl is not None else ""
                    )
                processedChunk.append(chunkText)

        return processedChunk

    def ExtractQuestionsAndAnswersFromCsvFile(
        self, file: str
    ) -> QaCsvChunksResponseModel:
        text, _ = self.docUtils.ExtractTextFromCsv(docPath=file)
        return self.docUtils.ExtractQaFromText(text=text)

    def ExtractChunksFromYtVideo(self, videoId: str, chunkSec: int) -> list[str]:
        text = self.docUtils.ExtractChunksFromYtVideo(
            videoId=videoId, chunkSec=chunkSec
        )
        response: list[str] = [
            f"{item.chunkText} for this [video link]({item.chunkUrl})" for item in text
        ]
        return response


class ExtractInstanceService(ExtractInstanceServiceImpl):
    def __init__(self):
        self.retryLimit = 5
        self.chatServices = ChatServices()

    async def ExtractQuestionsFromChunk(
        self,
        messages: list[ChatMessageModel],
        retryLimit: int,
    ) -> ExtractQaFromChunkResponseModel:
        if retryLimit > self.retryLimit:
            raise Exception("Exception while extracting questions from chunk")

        cerebrasChatResponse: Any = await self.chatServices.Chat(
            modelParams=ChatRequestModel(
                topP=0.9,
                temperature=0.1,
                maxCompletionTokens=5000,
                model=CerebrasChatModelEnum.QWEN_235B_INSTRUCT,
                messages=messages,
                responseFormat={
                    "type": "object",
                    "properties": {
                        "questions": {"type": "array", "items": {"type": "string"}},
                        "chunk": {"type": "string"},
                    },
                    "required": ["chunk", "questions"],
                    "additionalProperties": False,
                },
                method="cerebras",
                stream=False,
            )
        )
        chatResponse: Any = {}
        try:

            chatResponse = json.loads(cerebrasChatResponse.content).get("response")

        except Exception as e:
            print(f"Error occurred while extracting questions from chunk: {e}")

            messages.append(
                ChatMessageModel(
                    role=ChatMessageRoleEnum.USER,
                    content="Please generate a valid json object",
                )
            )
            time.sleep(60)

            await self.ExtractQuestionsFromChunk(
                messages=messages, retryLimit=retryLimit + 1
            )

        return ExtractQaFromChunkResponseModel(
            chunk=chatResponse.get("chunk", ""),
            questions=chatResponse.get("questions", []),
        )

    async def CleanYoutubeChunk(
        self,
        messages: list[ChatMessageModel],
        retryLimit: int,
    ) -> str:
        if retryLimit > self.retryLimit:
            raise Exception("Exception while extracting questions from chunk")

        cerebrasChatResponse: Any = await self.chatServices.Chat(
            modelParams=ChatRequestModel(
                topP=0.9,
                temperature=0.1,
                maxCompletionTokens=3000,
                model=CerebrasChatModelEnum.QWEN_235B_INSTRUCT,
                messages=messages,
                responseFormat={
                    "type": "object",
                    "properties": {
                        "chunk": {"type": "string"},
                    },
                    "required": ["chunk"],
                    "additionalProperties": False,
                },
                method="cerebras",
                stream=False,
            )
        )
        chatResponse: Any = {}
        try:

            chatResponse = json.loads(cerebrasChatResponse.content).get("response")

        except Exception as e:
            print(f"Error occurred while cleaning YouTube chunk: {e}")
            messages.append(
                ChatMessageModel(
                    role=ChatMessageRoleEnum.USER,
                    content="Please generate a valid json object",
                )
            )
            time.sleep(60)

            await self.ExtractQuestionsFromChunk(
                messages=messages, retryLimit=retryLimit + 1
            )

        return chatResponse.get("chunk", "")
