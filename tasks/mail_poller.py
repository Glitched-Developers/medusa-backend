import asyncio
import logging

from sqlalchemy import select

from api.zimbra import ZimbraClient
from database import user_mail_accounts
from notifications import NotificationService, NotificationType
from utils.security import decrypt_password

logger = logging.getLogger(__name__)


async def poll_mail_batch(engine, redis_client) -> None:
    async with engine.connect() as conn:
        accounts = (await conn.execute(select(user_mail_accounts).where(user_mail_accounts.c.is_active.is_(True)))).mappings().all()
    semaphore = asyncio.Semaphore(5)

    async def process(account):
        async with semaphore:
            user_id = account["user_id"]
            client = ZimbraClient()
            try:
                token = await redis_client.get(f"zimbra:token:{user_id}")
                if not token:
                    token = await client.authenticate(account["email"], decrypt_password(account["password_encrypted"]))
                    if not token:
                        return
                    await redis_client.set(f"zimbra:token:{user_id}", token, ex=5400)
                for message in await client.get_unread_messages(account["email"], token):
                    msg_id = message.get("id") or message.get("mid")
                    if not msg_id:
                        continue
                    notification_key = f"notified:{user_id}:{msg_id}"
                    if await redis_client.exists(notification_key):
                        continue
                    try:
                        sender = message.get("su", "New mail")
                        await NotificationService.send_to_user(engine, user_id, "New mail", str(sender), NotificationType.MAIL, {"message_id": msg_id})
                    except Exception:
                        logger.exception("Failed to send mail notification for user %s", user_id)
                        continue
                    await redis_client.set(notification_key, "1", ex=259200, nx=True)
            finally:
                await client.close()

    await asyncio.gather(*(process(account) for account in accounts))
