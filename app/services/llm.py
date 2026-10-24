from google import genai
from google.genai import types

from app.config import settings

client = genai.Client(api_key=settings.gemini_api_key)

SYSTEM_PROMPT = open("app/prompts/system_prompt.md", encoding="utf-8").read()

CONFIG=types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    max_output_tokens=500,
    temperature=0.3,
)

async def stream_reply(history : list[dict]):
    """history: [{"role": "user" | "model", "text": "..."}], oldest first."""
    contents = [
        types.Content(role=m["role"], parts=[types.Part(text=m["text"])])
        for m in history
    ]
    stream = await client.aio.models.generate_content_stream(
        model=settings.gemini_model,
        contents=contents,
        config=CONFIG,
    )

    async for chunk in stream:
        if chunk.text:
            yield chunk.text
    