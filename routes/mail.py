from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select, update

from api.zimbra import ZimbraClient
from cache import schedule_cache
from database import engine, user_devices, user_mail_accounts
from models.mail import ConnectMailRequest, DeviceTokenRequest, OperationStatusResponse
from utils.security import encrypt_password

router = APIRouter(prefix="/mail", tags=["Mail"])


async def _save_device(user_id: str, token: str) -> None:
    async with engine.begin() as conn:
        existing = await conn.scalar(select(user_devices.c.id).where(user_devices.c.fcm_token == token))
        if existing:
            await conn.execute(update(user_devices).where(user_devices.c.id == existing).values(user_id=user_id))
        else:
            await conn.execute(user_devices.insert().values(user_id=user_id, fcm_token=token))


@router.post("/connect", response_model=OperationStatusResponse)
async def connect_mail(request: ConnectMailRequest):
    client = ZimbraClient()
    try:
        token = await client.authenticate(str(request.email), request.password)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid Zimbra credentials")
        await client.enable_protocols(token)
        async with engine.begin() as conn:
            existing = await conn.scalar(select(user_mail_accounts.c.id).where(user_mail_accounts.c.user_id == request.user_id))
            values = {"email": str(request.email), "password_encrypted": encrypt_password(request.password), "is_active": True}
            if existing:
                await conn.execute(update(user_mail_accounts).where(user_mail_accounts.c.id == existing).values(**values))
            else:
                await conn.execute(user_mail_accounts.insert().values(user_id=request.user_id, **values))
        if request.fcm_token:
            await _save_device(request.user_id, request.fcm_token)
        for message in await client.get_unread_messages(str(request.email), token):
            msg_id = message.get("id") or message.get("mid")
            if msg_id:
                await schedule_cache._get_client().set(f"notified:{request.user_id}:{msg_id}", "1", ex=259200, nx=True)
        return OperationStatusResponse(detail="Mail account connected")
    finally:
        await client.close()


@router.post("/device/token", response_model=OperationStatusResponse)
async def register_device(request: DeviceTokenRequest):
    await _save_device(request.user_id, request.fcm_token)
    return OperationStatusResponse(detail="Device token registered")


@router.delete("/disconnect/{user_id}", response_model=OperationStatusResponse)
async def disconnect_mail(user_id: str):
    async with engine.begin() as conn:
        await conn.execute(delete(user_mail_accounts).where(user_mail_accounts.c.user_id == user_id))
    return OperationStatusResponse(detail="Mail account disconnected")
