from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class ConnectMailRequest(BaseModel):
    user_id: str
    email: EmailStr
    password: str
    fcm_token: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_bsu_email(cls, value: EmailStr) -> EmailStr:
        if not str(value).lower().endswith("@bsuedu.ru"):
            raise ValueError("Email must end with @bsuedu.ru")
        return value


class DeviceTokenRequest(BaseModel):
    user_id: str
    fcm_token: str


class OperationStatusResponse(BaseModel):
    status: str = "ok"
    detail: str
