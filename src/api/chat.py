# main.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from core.db_helper import db_helper
from core.schemas.chat import ChatResponse, ChatCreate
from core.schemas.message import MessageResponse, MessageCreate, ChatMessageResponse
from core.schemas.user import UserResponse
from .auth import get_current_user
import crud.chat as chat_crud

router = APIRouter()

@router.post("/chats/", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate = ChatCreate(),
    current_user: Optional[UserResponse] = Depends(get_current_user),
    db: AsyncSession = Depends(db_helper.session_getter)
):
    # Если пользователь не авторизован, всегда создаем анонимный чат
    if current_user is None:
        return await chat_crud.create_chat(db)
    
    # Для авторизованного пользователя учитываем его выбор (анонимный или персональный чат)
    return await chat_crud.create_chat(
        db, 
        current_user.id if not chat_data.is_anonymous else None
    )

@router.get("/chats/", response_model=List[ChatResponse])
async def list_chats(
    skip: int = 0,
    limit: int = 100,
    current_user: Optional[UserResponse] = Depends(get_current_user),
    db: AsyncSession = Depends(db_helper.session_getter)
):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неавторизованные пользователи не могут просматривать список чатов. Используйте конкретный chat_id для доступа к своему анонимному чату."
        )
    return await chat_crud.get_chats(db, current_user.id, skip=skip, limit=limit)

@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    current_user: Optional[UserResponse] = Depends(get_current_user),
    db: AsyncSession = Depends(db_helper.session_getter)
):
    chat = await chat_crud.get_chat(db, chat_id, current_user.id if current_user else None)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Проверяем доступ к чату
    if not chat.is_anonymous and (current_user is None or chat.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return chat

@router.post("/chats/{chat_id}/messages/", response_model=ChatMessageResponse)
async def add_message(
    chat_id: UUID,
    message: MessageCreate,
    current_user: Optional[UserResponse] = Depends(get_current_user),
    db: AsyncSession = Depends(db_helper.session_getter)
):
    chat = await chat_crud.get_chat(db, chat_id, current_user.id if current_user else None)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Проверяем доступ к чату
    if not chat.is_anonymous and (current_user is None or chat.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Получаем оба сообщения: пользователя и ассистента
    user_message, assistant_message = await chat_crud.add_message(db, chat_id, message.content)
    
    return ChatMessageResponse(
        user_message=user_message,
        assistant_message=assistant_message
    )


@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: UUID,
    current_user: Optional[UserResponse] = Depends(get_current_user),
    db: AsyncSession = Depends(db_helper.session_getter)
):
    chat = await chat_crud.get_chat(db, chat_id, current_user.id if current_user else None)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Проверяем доступ к чату
    if not chat.is_anonymous and (current_user is None or chat.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = await chat_crud.delete_chat(db, chat_id, current_user.id if current_user else None)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success"}
