import logging
from pathlib import Path

from google import genai
from google.genai import errors, types

from app.config import settings
from app.schemas import Message

client = genai.Client(api_key=settings.gemini_api_key)

logger = logging.getLogger(__name__)

RETRYABLE = {429, 500, 503, 504}
FALLBACK_TEXT = "\n\nSorry, something went wrong on my end. Please try again in a moment."

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.md"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

CONFIG=types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    max_output_tokens=500,
    temperature=0.3,
)

def to_contents(messages : list[Message]):
    return [
        types.Content(
            role="model" if m.role == "assistant" else "user",
            parts=[types.Part(text=m.content)],
        )
        for m in messages
    ]

async def stream_reply(messages : list[Message]):
    contents = to_contents(messages)
    for model in settings.gemini_models:
        started = False
        try:
            stream = await client.aio.models.generate_content_stream(
                model=model, contents=contents, config=CONFIG
            )
            async for chunk in stream:
                if chunk.text:
                    started = True
                    yield chunk.text
            return
        except errors.APIError as e:
            logger.warning("Model %s failed (%s)", model, e.code)
            if started or e.code not in RETRYABLE:
                break
        except Exception:
            logger.exception("Unexpected failure with %s", model)
            break
    yield FALLBACK_TEXT