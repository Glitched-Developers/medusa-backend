import json
import uvicorn

from fastapi import FastAPI
from api import get_schedule

app = FastAPI()


if __name__ == "__main__":
    schedule = get_schedule()
    print(json.dumps(schedule, ensure_ascii=False, indent=4))