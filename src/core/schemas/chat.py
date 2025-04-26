from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional
from .message import MessageResponse

class ChatBase(BaseModel):
    is_anonymous: bool = False

class ChatCreate(ChatBase):
    user_id: Optional[UUID] = None

class ChatResponse(ChatBase):
    id: UUID
    created_at: datetime
    user_id: Optional[UUID] = None
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True