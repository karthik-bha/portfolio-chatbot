from fastapi.testclient import TestClient

# pyrefly: ignore [missing-import]
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

import app.routes.chat as chat_module
from app.core.rate_limit import rate_limit_exceeded_handler
from main import app

client = TestClient(app)


def test_chat_streams_mocked_reply(monkeypatch):
    async def fake_stream(messages):
        yield "Hello "
        yield "there"

    monkeypatch.setattr(chat_module, "stream_reply", fake_stream)
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200
    assert r.text == "Hello there"

def test_chat_returns_503_when_llm_fails_before_stream(monkeypatch):
    async def failing_stream(messages):
        if False:
            yield "never"
        raise chat_module.LLMUnavailableError()

    monkeypatch.setattr(chat_module, "stream_reply", failing_stream)
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 503
    data = r.json()
    assert "The chatbot has reached its usage limit for now" in data["detail"]


def test_chat_handles_empty_stream(monkeypatch):
    async def empty_stream(messages):
        if False:
            yield "never"

    monkeypatch.setattr(chat_module, "stream_reply", empty_stream)
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200
    assert r.text == ""


def test_custom_rate_limit_handler():
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/chat",
        "headers": [],
        "app": app,
    }
    request = Request(scope)
    request.state.view_rate_limit = None

    exc = RateLimitExceeded.__new__(RateLimitExceeded)
    exc.detail = "5 per 1 minute"
    response = rate_limit_exceeded_handler(request, exc)
    assert response.status_code == 429
    assert b"The chatbot has reached its usage limit for now" in response.body


def test_chat_rejects_bad_payload():
    r = client.post("/chat", json={"messages": [{"role": "system", "content": "hi"}]})
    assert r.status_code == 422


def test_health():
    assert client.get("/health").status_code == 200