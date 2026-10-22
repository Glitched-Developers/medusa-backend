import asyncio
import os
import signal

import firebase_admin
from redis.asyncio import Redis

from database import engine
from tasks.mail_poller import poll_mail_batch


async def main() -> None:
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            firebase_admin.initialize_app()
        except Exception as exc:
            raise RuntimeError(
                "Firebase is not initialized. Set GOOGLE_APPLICATION_CREDENTIALS "
                "to a mounted Firebase service-account JSON file."
            ) from exc

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
