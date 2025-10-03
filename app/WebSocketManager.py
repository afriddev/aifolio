from typing import Dict
from fastapi import WebSocket
from abc import ABC, abstractmethod


class WebSocketManagerImpl(ABC):
    @abstractmethod
    async def connect(self, websocket: WebSocket, email: str):
        pass

    @abstractmethod
    def disconnect(self, email: str):
        pass

    @abstractmethod
    async def sendToUser(self, email: str, message: str):
        pass


class WebSocketManager(WebSocketManagerImpl):
    def __init__(self):
        self.active: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, email: str):
        await websocket.accept()
        self.active[email] = websocket
        # print(f"✅ {email} connected")

    def disconnect(self, email: str):
        if email in self.active:
            del self.active[email]

    async def sendToUser(self, email: str, message: str):
        if email in self.active:
            await self.active[email].send_text(message)


webSocket = WebSocketManager()
