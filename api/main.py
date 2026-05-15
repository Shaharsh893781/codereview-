from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.middleware import RateLimitMiddleware
from api.routes_auth import router as auth_router
from api.routes_reviews import router as reviews_router
from database.init_db import init_db
from utils.config import get_settings


settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CodeReviewAI API",
    description="AI-powered automated code review platform for Python teams.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(RateLimitMiddleware)
app.include_router(auth_router)
app.include_router(reviews_router)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def auth_page():
    return FileResponse("frontend/index.html")


@app.get("/dashboard")
def dashboard():
    return FileResponse("frontend/dashboard.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name}
