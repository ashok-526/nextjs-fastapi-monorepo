from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router
from app.routers.social import router as social_router
from app.routers.posts import router as posts_router
from app.routers.feed import router as feed_router
from app.realtime.ws import router as ws_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers.settings import router as settings_router
from app.routers.admin import router as admin_router

app = FastAPI()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


settings = get_settings()

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

origins = []
if settings.WEB_ORIGIN:
    origins = [settings.WEB_ORIGIN]
elif settings.CORS_ORIGINS:
    origins = settings.CORS_ORIGINS

if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(social_router)
app.include_router(posts_router)
app.include_router(feed_router)
app.include_router(ws_router)
app.include_router(settings_router)
app.include_router(admin_router)
