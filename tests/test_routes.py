from fastapi.testclient import TestClient
from main import app
import app.routes.chat as chat_module

client = TestClient(app)


def test_chat_streams_mocked_reply(monkeypatch):
    async def fake_stream(messages):
        yield "Hello "
        yield "there"

    monkeypatch.setattr(chat_module, "stream_reply", fake_stream)
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200
    assert r.text == "Hello there"

def test_chat_rejects_bad_payload():
    r = client.post("/chat", json={"messages": [{"role": "system", "content": "hi"}]})
    assert r.status_code == 422

def test_health():
    assert client.get("/health").status_code == 200