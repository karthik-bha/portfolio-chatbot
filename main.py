from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# pyrefly: ignore [missing-import]
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

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
