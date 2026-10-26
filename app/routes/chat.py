from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.config import settings
from app.core.rate_limit import limiter
from app.schemas import ChatRequest
from app.services.llm import stream_reply

router = APIRouter()

@router.post("/chat")
@limiter.limit(settings.rate_limit)
async def chat(request: Request, req : ChatRequest):
    return StreamingResponse(stream_reply(req.messages), media_type="text/event-stream")