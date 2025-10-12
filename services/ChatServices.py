import json
from typing import Any, cast
from fastapi.responses import StreamingResponse
import openai
from openai import AsyncOpenAI, OpenAIError
from implementations.ChatServicesImpl import ChatServicesImpl
from models import (
    ChatChoiceMessageModel,
    ChatChoiceModel,
    ChatDataModel,
    ChatRequestModel,
    ChatResponseModel,
    ChatUsageModel,
)
from cerebras.cloud.sdk import AsyncCerebras

from enums import (
    ChatResponseStatusEnum,
)

from utils import GetNvidiaBaseUrl, GetNvidiaApiKey, GetCerebrasApiKey
from app.ChatState import (
    ChatUsedTool,
    ChatEvent,
    ChatContent,
    ChatReasoning,
    ChatCompletionTokens,
    ChatPromptTokens,
    ChatTotalTokens,
    ReasoningTokens,
)


openAiClient = AsyncOpenAI(base_url="", api_key="")
cerebrasClient = AsyncCerebras(api_key="")


class ChatServices(ChatServicesImpl):

    async def OpenaiChat(self, modelParams: ChatRequestModel) -> Any:
        client = openAiClient if modelParams.method == "openai" else cerebrasClient
        if modelParams.method == "openai":
            openAiClient.base_url = GetNvidiaBaseUrl()
            openAiClient.api_key = GetNvidiaApiKey()
        elif modelParams.method == "cerebras":
            cerebrasClient.api_key = GetCerebrasApiKey()

        clientParams: dict[Any, Any] = {
            "messages": cast(Any, modelParams.messages),
            "model": modelParams.model.value[0],
            "max_tokens": modelParams.maxCompletionTokens,
            "stream": modelParams.stream,
            "temperature": modelParams.temperature,
            "top_p": modelParams.topP,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "response_format": cast(
                Any,
                (
                    None
                    if modelParams.responseFormat is None
                    else {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "schema",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {"response": modelParams.responseFormat},
                                "required": ["response"],
                                "additionalProperties": False,
                            },
                        },
                    }
                ),
            ),
            "stream_options": {"include_usage": True},
        }
        if modelParams.tools:
            clientParams["tools"] = cast(Any, modelParams.tools)
            clientParams["tool_choice"] = "auto"

        createCall = cast(Any, client.chat.completions.create(**clientParams))

        chatCompletion: Any = await createCall

        return chatCompletion

    async def Chat(
        self, modelParams: ChatRequestModel
    ) -> ChatResponseModel | StreamingResponse:

        try:

            chatCompletion = await self.OpenaiChat(modelParams)

            if modelParams.stream:

                async def eventGenerator():
                    startedReasoning = False
                    reasoningStartToken: Any = ""
                    reasoningEndToken: Any = ""
                    reasoningStartIndex = 0
                    try:
                        async for chunk in chatCompletion:
                            if getattr(chunk, "choices", None):
                                delta = getattr(chunk.choices[0], "delta", None)
                                if delta:
                                    content = getattr(delta, "content", None)
                                    reasoningContent = getattr(
                                        delta, "reasoning_content", None
                                    )
                                    reasoning = getattr(delta, "reasoning", None)
                                    toolCalls = getattr(delta, "tool_calls", None)
                                    toolName = None

                                    if startedReasoning:
                                        reasoningEndToken = reasoningEndToken + content
                                        if "</think>" in reasoningEndToken:
                                            startedReasoning = False
                                            reasoningStartToken = ""

                                        reasoningContent = content
                                        content = None

                                    if reasoningStartIndex < 5 and content:
                                        reasoningStartToken = (
                                            reasoningStartToken + content
                                        )
                                        if "<think>" in reasoningStartToken:
                                            startedReasoning = True
                                            reasoningStartIndex = 5
                                        else:
                                            reasoningStartIndex += 1

                                    if toolCalls and len(toolCalls) > 0:
                                        toolFunction = getattr(
                                            toolCalls[0], "function", None
                                        )
                                        toolName = getattr(toolFunction, "name", None)

                                    else:
                                        toolName = None

                                    if content:
                                        ChatContent[modelParams.messageId] += content
                                        yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"

                                    if reasoning:
                                        ChatReasoning[
                                            modelParams.messageId
                                        ] += reasoning
                                        yield f"data: {json.dumps({'type': 'reasoning', 'data': reasoning})}\n\n"

                                    if toolName:
                                        ChatUsedTool[modelParams.messageId] = toolName
                                        yield f"data: {json.dumps({'type': 'tool_name', 'data': toolName})}\n\n"

                                    if reasoningContent:
                                        ChatReasoning[
                                            modelParams.messageId
                                        ] += reasoningContent
                                        yield f"data: {json.dumps({'type': 'reasoning', 'data': reasoningContent})}\n\n"
                            if getattr(chunk, "usage", None):

                                usage = chunk.usage
                                ChatCompletionTokens[modelParams.messageId] = (
                                    usage.completion_tokens
                                )
                                ChatPromptTokens[modelParams.messageId] = (
                                    usage.prompt_tokens
                                )
                                ChatTotalTokens[modelParams.messageId] = (
                                    usage.total_tokens
                                )
                                ReasoningTokens[modelParams.messageId] = (
                                    usage.reasoning_tokens
                                    if getattr(usage, "reasoning_tokens", None)
                                    else 0
                                )

                                yield f"data: {json.dumps({'type': 'usage', 'data': {'completionTokens': usage.completion_tokens, 'promptTokens': usage.prompt_tokens, 'totalTokens': usage.total_tokens , 'reasoningTokens': usage.reasoning_tokens}})}\n\n"

                    except Exception as e:
                        yield f"event: error\ndata: {str(e)}\n\n"
                    finally:
                        if modelParams.messageId:
                            ChatEvent[modelParams.messageId].set()

                return StreamingResponse(
                    eventGenerator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                    },
                )

            choices: list[ChatChoiceModel] = []
            for ch in chatCompletion.choices:
                choices.append(
                    ChatChoiceModel(
                        index=ch.index,
                        message=ChatChoiceMessageModel(
                            role=ch.message.role,
                            content=ch.message.content,
                        ),
                    )
                )

            LLMData = ChatDataModel(
                id=chatCompletion.id,
                choices=choices,
                created=chatCompletion.created,
                model=chatCompletion.model,
                usage=ChatUsageModel(
                    promptTokens=chatCompletion.usage.prompt_tokens,
                    completionTokens=chatCompletion.usage.completion_tokens,
                    totalTokens=chatCompletion.usage.total_tokens,
                ),
            )

            return ChatResponseModel(
                status=ChatResponseStatusEnum.SUCCESS,
                content=LLMData.choices[0].message.content,
            )

        except openai.APIConnectionError as e:
            print(e)
            return ChatResponseModel(status=ChatResponseStatusEnum.REQUEST_TIMEOUT)

        except openai.RateLimitError as e:
            print(e)
            return ChatResponseModel(status=ChatResponseStatusEnum.RATE_LIMIT)

        except openai.BadRequestError as e:
            print(e)
            return ChatResponseModel(status=ChatResponseStatusEnum.BAD_REQUEST)

        except openai.AuthenticationError as e:
            print(e)
            return ChatResponseModel(status=ChatResponseStatusEnum.UNAUTHORIZED)

        except openai.InternalServerError as e:
            print(e)
            return ChatResponseModel(status=ChatResponseStatusEnum.SERVER_ERROR)
        except OpenAIError as e:
            print(e)
            return ChatResponseModel(status=ChatResponseStatusEnum.SERVER_ERROR)
