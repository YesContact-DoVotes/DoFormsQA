import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger("WebSocketManager")


class ConnectionManager:
    def __init__(self):
        # Maps session_id -> list of active WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.global_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, session_id: int):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket client connected to session {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: int):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket client disconnected from session {session_id}")

    async def broadcast_to_session(self, session_id: int, message: Dict[str, Any]):
        if session_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    disconnected.append(connection)
            for dead in disconnected:
                if dead in self.active_connections[session_id]:
                    self.active_connections[session_id].remove(dead)


ws_manager = ConnectionManager()
