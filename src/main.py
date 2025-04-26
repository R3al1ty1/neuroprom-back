import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api import router as api_router
from core.settings import settings
from core.db_helper import db_helper


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Приложение запускается...")
    yield
    print("🛑 Приложение выключается...")
    db_helper.dispose()


app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    title="Neuroprom API",
    version="1.0.0"
)

origins = [
    "https://app.neuroprom.com",
    "https://neuroprom.com",
    "http://127.0.0.1:5000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"]
)

app.include_router(
    api_router,
    prefix="/api",
    tags=["api"]
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.run.host,
        port=settings.run.port
    )