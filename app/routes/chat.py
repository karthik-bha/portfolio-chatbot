from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import settings
from app.core.rate_limit import limiter
from app.schemas import ChatRequest
from app.services.llm import LLMUnavailableError, stream_reply

router = APIRouter()


async def with_first_chunk(
    first_chunk: str, stream: AsyncIterator[str]
) -> AsyncIterator[str]:
    yield first_chunk
    async for chunk in stream:
        yield chunk


@router.post("/chat")
@limiter.limit(settings.rate_limit)
async def chat(request: Request, req: ChatRequest):
    stream = stream_reply(req.messages)
    try:
        first_chunk = await anext(stream)
    except StopAsyncIteration:
        return StreamingResponse(iter(()), media_type="text/event-stream")
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return StreamingResponse(
        with_first_chunk(first_chunk, stream), media_type="text/event-stream"
    )