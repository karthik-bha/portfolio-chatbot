from unittest.mock import AsyncMock

# pyrefly: ignore [missing-import]
import pytest

# pyrefly: ignore [missing-import]
from google.genai import errors

from app.schemas import Message
from app.services.llm import FALLBACK_TEXT, LLMUnavailableError, stream_reply


class MockChunk:
    def __init__(self, text: str):
        self.text = text


class AsyncStreamMock:
    def __init__(self, chunks: list[str], error_after: Exception | None = None):
        self.chunks = chunks
        self.error_after = error_after

    def __aiter__(self):
        self._iter = iter(self.chunks)
        return self

    async def __anext__(self):
        try:
            val = next(self._iter)
            return MockChunk(val)
        except StopIteration:
            if self.error_after:
                err = self.error_after
                self.error_after = None
                raise err
            raise StopAsyncIteration


@pytest.mark.anyio
async def test_stream_reply_success(monkeypatch):
    from app.services import llm

    fake_stream = AsyncStreamMock(["Hello ", "world!"])
    mock_gen = AsyncMock(return_value=fake_stream)
    monkeypatch.setattr(llm.client.aio.models, "generate_content_stream", mock_gen)

    chunks = [c async for c in stream_reply([Message(role="user", content="hi")])]
    assert chunks == ["Hello ", "world!"]


@pytest.mark.anyio
async def test_stream_reply_raises_when_all_fail_before_stream(monkeypatch):
    from app.services import llm

    api_err = errors.APIError(429, "Resource exhausted")
    mock_gen = AsyncMock(side_effect=api_err)
    monkeypatch.setattr(llm.client.aio.models, "generate_content_stream", mock_gen)

    with pytest.raises(LLMUnavailableError) as exc_info:
        _ = [c async for c in stream_reply([Message(role="user", content="hi")])]

    assert "reached its usage limit" in str(exc_info.value)
    assert exc_info.value.status_code == 503


@pytest.mark.anyio
async def test_stream_reply_yields_fallback_when_fails_mid_stream(monkeypatch):
    from app.services import llm

    api_err = errors.APIError(500, "Internal error")
    fake_stream = AsyncStreamMock(["First chunk"], error_after=api_err)
    mock_gen = AsyncMock(return_value=fake_stream)
    monkeypatch.setattr(llm.client.aio.models, "generate_content_stream", mock_gen)

    chunks = [c async for c in stream_reply([Message(role="user", content="hi")])]
    assert chunks == ["First chunk", FALLBACK_TEXT]
