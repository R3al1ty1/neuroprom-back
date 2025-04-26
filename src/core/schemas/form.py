from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, constr

class FormBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company: str | None = None
    description: str | None = None

class FormCreate(FormBase):
    pass

class FormResponse(FormBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True