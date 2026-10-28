import asyncio
import json
import os
import signal

import firebase_admin
from firebase_admin import credentials
from redis.asyncio import Redis

from database import engine
from tasks.mail_poller import poll_mail_batch


def init_firebase() -> None:
    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    raw_creds = os.getenv("FIREBASE_SERVICE_ACCOUNT") or os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS_JSON"
    )
    if raw_creds:
        try:
            cred_dict = json.loads(raw_creds)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return
        except Exception as exc:
            raise RuntimeError(
                "Failed to parse Firebase credentials from environment variable."
            ) from exc

    try:
        firebase_admin.initialize_app()
    except Exception as exc:
        raise RuntimeError(
            "Firebase is not initialized. Provide FIREBASE_SERVICE_ACCOUNT env var "
            "or set GOOGLE_APPLICATION_CREDENTIALS to a mounted JSON file path."
        ) from exc


async def main() -> None:
    init_firebase()

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signum, stop.set)

    redis = Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
    )
    interval = int(os.getenv("MAIL_POLL_INTERVAL_SEC", "900"))

    try:
        while not stop.is_set():
            await poll_mail_batch(engine, redis)
            try:
                await asyncio.wait_for(stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass
    finally:
        await redis.aclose()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
