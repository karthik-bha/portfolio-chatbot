from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.llm import stream_reply

router = APIRouter()

@router.post("/chat")
async def chat(req):
    return StreamingResponse(stream_reply(req.history), media_type="text/event-stream")