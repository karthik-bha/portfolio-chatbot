from fastapi import Request, Response
from fastapi.responses import JSONResponse

# pyrefly: ignore [missing-import]
from slowapi import Limiter

# pyrefly: ignore [missing-import]
from slowapi.errors import RateLimitExceeded

# pyrefly: ignore [missing-import]
from slowapi.util import get_remote_address

from app.services.llm import RATE_LIMIT_MESSAGE


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    response = JSONResponse(
        {
            "detail": RATE_LIMIT_MESSAGE,
            "error": f"Rate limit exceeded: {exc.detail}",
        },
        status_code=429,
    )
    response = request.app.state.limiter._inject_headers(
        response, request.state.view_rate_limit
    )
    return response