from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.models.chat import Chat, Message
from core.neural_network import get_ai_response
from uuid import UUID

async def create_chat(db: AsyncSession, user_id: Optional[UUID] = None) -> Chat:
    chat = Chat(
        user_id=user_id,
        is_anonymous=user_id is None
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat

async def get_chat(db: AsyncSession, chat_id: UUID, user_id: Optional[UUID] = None) -> Optional[Chat]:
    stmt = select(Chat).where(Chat.id == chat_id)
    if user_id is not None:
        stmt = stmt.where(Chat.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_chats(db: AsyncSession, user_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[Chat]:
    stmt = select(Chat)
    if user_id is not None:
        stmt = stmt.where(Chat.user_id == user_id)
    else:
        stmt = stmt.where(Chat.is_anonymous == True)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_chat_messages(db: AsyncSession, chat_id: UUID) -> List[Message]:
    stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.timestamp)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def add_message(db: AsyncSession, chat_id: UUID, content: str) -> Tuple[Message, Message]:
    # Сохраняем сообщение пользователя
    user_message = Message(
        chat_id=chat_id,
        content=content,
        is_assistant=False  # Явно указываем, что это сообщение пользователя
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    # Получаем историю сообщений для контекста
    chat_messages = await get_chat_messages(db, chat_id)
    
    # Формируем контекст для нейросети
    messages_for_ai = [
        {
            "role": "system",
            "content": "Ты - дружелюбный ассистент компании НейроПром. Отвечай на вопросы пользователей вежливо и по существу. Если тебя спрашивают о личном или о том как дела, отвечай искренне и дружелюбно."
        }
    ]
    
    # Добавляем историю сообщений с учетом их типа
    for msg in chat_messages:
        role = "assistant" if msg.is_assistant else "user"
        messages_for_ai.append({
            "role": role,
            "content": msg.content
        })

    # Получаем ответ от нейросети
    ai_response = await get_ai_response(messages_for_ai)

    # Сохраняем ответ нейросети
    ai_message = Message(
        chat_id=chat_id,
        content=ai_response,
        is_assistant=True  # Помечаем как сообщение ассистента
    )
    db.add(ai_message)
    await db.commit()
    await db.refresh(ai_message)

    return user_message, ai_message

async def delete_chat(db: AsyncSession, chat_id: UUID, user_id: Optional[UUID] = None) -> bool:
    chat = await get_chat(db, chat_id, user_id)
    if chat:
        await db.delete(chat)
        await db.commit()
        return True
    return False