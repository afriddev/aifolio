from typing import Dict
from fastapi import WebSocket
from abc import ABC, abstractmethod
import asyncio


class WebSocketManagerImpl(ABC):
    @abstractmethod
    async def connect(self, websocket: WebSocket, email: str):
        pass

    @abstractmethod
    async def disconnect(self, email: str):
        pass

    @abstractmethod
    async def sendToUser(self, email: str, message: str):
        pass


class WebSocketManager(WebSocketManagerImpl):
    def __init__(self):
        self.active: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, email: str):
        async with self.lock:
            await websocket.accept()
            self.active[email] = websocket
            print(f"✅ {email} connected")
    
    async def disconnect(self, email: str):
        async with self.lock:
            if email in self.active:
                del self.active[email]
    
    async def sendToUser(self, email: str, message: str):
        async with self.lock:
            if email in self.active:
                await self.active[email].send_text(message)
            else:
                print(f"⚠️ No active connection for {email}")


webSocket = WebSocketManager()
