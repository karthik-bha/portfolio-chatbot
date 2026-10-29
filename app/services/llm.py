import logging
from pathlib import Path

from google import genai

# pyrefly: ignore [missing-import]
from google.genai import errors, types

from app.config import settings
from app.schemas import Message

client = genai.Client(api_key=settings.gemini_api_key)

logger = logging.getLogger(__name__)

RETRYABLE = {429, 500, 503, 504}
RATE_LIMIT_MESSAGE = (
    "The chatbot has reached its usage limit for now. "
    "Please try again later, or reach Karthik through the Contact page."
)
FALLBACK_TEXT = (
    "\n\nThe chatbot has reached its usage limit for now. "
    "Please try again later, or reach Karthik through the Contact page."
)


class LLMUnavailableError(Exception):
    """Raised when all models fail before any content is yielded."""

    def __init__(
        self,
        message: str = RATE_LIMIT_MESSAGE,
        status_code: int = 503,
        last_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.last_error = last_error


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.md"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    max_output_tokens=500,
    temperature=0.3,
)


def to_contents(messages: list[Message]):
    return [
        types.Content(
            role="model" if m.role == "assistant" else "user",
            parts=[types.Part(text=m.content)],
        )
        for m in messages
    ]


async def stream_reply(messages: list[Message]):
    contents = to_contents(messages)
    started = False
    last_err: Exception | None = None
    for model in settings.gemini_models:
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
            last_err = e
            if started or e.code not in RETRYABLE:
                break
        except Exception as e:
            logger.exception("Unexpected failure with %s", model)
            last_err = e
            break

    if started:
        yield FALLBACK_TEXT
    else:
        raise LLMUnavailableError(last_error=last_err)