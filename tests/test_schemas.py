import pytest
from pydantic import ValidationError
from app.schemas import ChatRequest

def user(text): return {"role": "user", "content": text}
def bot(text): return {"role": "assistant", "content": text}

def make(*messages):
    # same path FastAPI uses: raw JSON-like data -> validated model
    return ChatRequest.model_validate({"messages": list(messages)})

def test_accepts_valid_request():
    req = make(user("hi"))
    assert len(req.messages) == 1

def test_rejects_system_role():
    with pytest.raises(ValidationError): # type: ignore
        make({"role": "system", "content": "hi"})

def test_rejects_empty_content():
    with pytest.raises(ValidationError):
        make(user("   "))

def test_last_message_must_be_user():
    with pytest.raises(ValidationError):
        make(user("hi"), bot("hello"))

def test_rejects_overlong_user_message():
    with pytest.raises(ValidationError):
        make(user("x" * 5000))

def test_trims_history_and_starts_with_user():
    msgs = [user("q") if i % 2 == 0 else bot("a") for i in range(21)]
    req = make(*msgs)
    assert len(req.messages) <= 6
    assert req.messages[0].role == "user"