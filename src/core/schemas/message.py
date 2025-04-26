from datetime import datetime
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class MessageBase(BaseModel):
    content: str
    is_assistant: bool = False

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    chat_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: Optional[MessageResponse] = None
