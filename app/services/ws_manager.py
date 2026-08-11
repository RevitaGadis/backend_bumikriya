import asyncio
import json
import logging
from typing import Dict, Optional, Set

from fastapi import WebSocket
from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import settings
from app.core.redis_mock import RedisMock

logger = logging.getLogger(__name__)

NOTIFICATION_CHANNEL = "notifications"


class ConnectionManager:
    """Tracks live WebSocket connections per user and broadcasts via Redis pub/sub."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._async_redis: Optional[AsyncRedis] = None
        self._redis_available: bool = False
        self._listener_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._loop = asyncio.get_running_loop()
        self.active_connections.setdefault(user_id, set()).add(websocket)
        await self._ensure_listener()

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        conns = self.active_connections.get(user_id)
        if conns:
            conns.discard(websocket)
            if not conns:
                self.active_connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, payload: dict) -> None:
        for ws in list(self.active_connections.get(user_id, set())):
            try:
                await ws.send_text(json.dumps(payload, ensure_ascii=False, default=str))
            except Exception:
                try:
                    self.active_connections.get(user_id, set()).discard(ws)
                except Exception:
                    pass

    def has_connection(self, user_id: str) -> bool:
        return bool(self.active_connections.get(user_id))

    async def _ensure_listener(self) -> None:
        if self._listener_task is not None:
            return
        try:
            self._async_redis = AsyncRedis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
            )
            await self._async_redis.ping()
            self._redis_available = True
            self._listener_task = asyncio.create_task(self._listen())
            logger.info("Notification pub/sub listener started.")
        except Exception:
            self._redis_available = False
            logger.warning(
                "Redis unavailable for WebSocket pub/sub (%s:%s). Falling back to in-process delivery.",
                settings.REDIS_HOST,
                settings.REDIS_PORT,
            )

    async def _listen(self) -> None:
        while True:
            try:
                pubsub = self._async_redis.pubsub()
                await pubsub.subscribe(NOTIFICATION_CHANNEL)
                async for message in pubsub.listen():
                    if message.get("type") != "message":
                        continue
                    try:
                        data = json.loads(message.get("data"))
                        user_id = data.get("user_id")
                        if user_id:
                            await self.send_to_user(user_id, data.get("payload", data))
                    except Exception:
                        continue
            except Exception:
                logger.warning("Notification pub/sub listener error, retrying in 3s...")
                await asyncio.sleep(3)


manager = ConnectionManager()


def _serialize_publish(user_id: str, payload: dict) -> str:
    return json.dumps({"user_id": user_id, "payload": payload}, ensure_ascii=False, default=str)


def publish_notification_sync(user_id: str, payload: dict) -> None:
    """Publish a notification so all app instances deliver it to the user in realtime.

    Uses Redis pub/sub when available; otherwise delivers directly to in-process
    WebSocket connections (e.g. the RedisMock fallback).
    """
    if manager._redis_available:
        try:
            client = SyncRedis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
            )
            client.publish(NOTIFICATION_CHANNEL, _serialize_publish(user_id, payload))
            client.close()
            return
        except Exception:
            pass

    # In-process fallback (no Redis / listener not running).
    if manager._loop is not None and manager.has_connection(user_id):
        try:
            asyncio.run_coroutine_threadsafe(
                manager.send_to_user(user_id, payload), manager._loop
            )
        except Exception:
            pass


def notify_user(
    user_id: str,
    title: str,
    message: Optional[str] = None,
    notification_type: str = "general",
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> None:
    """Build a realtime payload and push it to the user without touching the DB."""
    payload = {
        "event": "notification",
        "data": {
            "type": notification_type,
            "title": title,
            "message": message,
            "reference_type": reference_type,
            "reference_id": str(reference_id) if reference_id else None,
            "created_at": None,
        },
    }
    publish_notification_sync(user_id, payload)
