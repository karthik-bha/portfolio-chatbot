from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.config import settings

MAX_ASSISTANT_CHARS = 4000

class Message(BaseModel):
    role : Literal["user", "assistant"]
    content : str = Field(min_length=1)

    @model_validator(mode="after")
    def check_length(self):
        self.content = self.content.strip()
        if not self.content:
            raise ValueError("message is empty")
        limit = settings.max_message_chars if self.role == "user" else MAX_ASSISTANT_CHARS
        if len(self.content) > limit:
            raise ValueError(f"{self.role} message exceeds {limit} characters")
        return self

class ChatRequest(BaseModel):
    messages : list[Message] = Field(min_length=1)

    @model_validator(mode="after")
    def check_and_trim(self):
        if self.messages[-1].role!="user":
            raise ValueError("last message must be from user")
        self.messages = self.messages[-settings.max_history_turns:]
        while self.messages and self.messages[0].role!="user":
            self.messages = self.messages[1:]
        return self


