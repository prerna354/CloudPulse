import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: str) -> None:
        for connection in list(self._connections):
            try:
                await connection.send_text(message)
            except Exception:
                logger.info("Dropping dead websocket connection")
                self.disconnect(connection)


manager = ConnectionManager()
