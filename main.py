import asyncio

import uvicorn
from fastapi import FastAPI

from routes import router

app = FastAPI()
app.include_router(router)

async def main():
    """Функция для асинхронного запуска uvicorn."""
    config = uvicorn.Config("main:app", host="localhost", port=5000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
