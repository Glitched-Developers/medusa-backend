import json
from typing import Any

from firebase_admin import messaging
from sqlalchemy import delete, select

from database import user_devices
from notifications.types import NotificationType


class NotificationService:
    @staticmethod
    async def send_to_user(db_engine, user_id: str, title: str, body: str, event_type: NotificationType | str, payload_data: dict[str, Any] | None = None) -> None:
        async with db_engine.connect() as conn:
            tokens = (await conn.execute(select(user_devices.c.fcm_token).where(user_devices.c.user_id == user_id))).scalars().all()
        if not tokens:
            return
        message = messaging.MulticastMessage(notification=messaging.Notification(title=title, body=body), data={"event_type": str(event_type), **{k: str(v) for k, v in (payload_data or {}).items()}}, tokens=list(tokens))
        result = messaging.send_each_for_multicast(message)
        dead = [token for token, item in zip(tokens, result.responses) if getattr(getattr(item, "exception", None), "code", None) in {"UNREGISTERED", "NOT_FOUND", "INVALID_ARGUMENT"}]
        if dead:
            async with db_engine.begin() as conn:
                await conn.execute(delete(user_devices).where(user_devices.c.fcm_token.in_(dead)))
