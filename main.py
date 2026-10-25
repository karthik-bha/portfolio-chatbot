from fastapi import FastAPI
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins, 
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"]
)

app.include_router(health_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    return {"message": "Hello, World!"}
