# services.py
import uuid
from datetime import datetime
from typing import Dict, List, Literal, Tuple, Optional, Any
from fastapi import HTTPException, status

from schemas import Message, MessageBase
# Импортируем заглушку нашей нейросети
from neural_network import model_predictor

# Простое хранилище чатов в памяти (СЛОВАРЬ)
# Ключ: chat_id (uuid.UUID), Значение: список сообщений [Message, ...]
# В реальном приложении замените на БД (Redis, MongoDB, PostgreSQL и т.д.)
chats_db: Dict[uuid.UUID, List[Message]] = {}

# --- Функции для работы с чатами ---

def create_new_chat() -> uuid.UUID:
    """Создает новый чат и возвращает его ID."""
    chat_id = uuid.uuid4()
    chats_db[chat_id] = [] # Инициализируем пустой историей
    print(f"Chat created: {chat_id}")
    return chat_id

def get_chat_history(chat_id: uuid.UUID) -> List[Message]:
    """Возвращает историю сообщений для указанного чата."""
    if chat_id not in chats_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chats_db[chat_id]

def add_message_to_chat(chat_id: uuid.UUID, role: Literal['user', 'assistant'], content: str) -> Message:
    """Добавляет сообщение в историю чата."""
    if chat_id not in chats_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found during message add")

    message = Message(role=role, content=content)
    chats_db[chat_id].append(message)
    print(f"Message added to chat {chat_id}: {role} - {content[:50]}...")
    return message

def delete_chat_data(chat_id: uuid.UUID):
    """Удаляет данные чата."""
    if chat_id not in chats_db:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    del chats_db[chat_id]
    print(f"Chat deleted: {chat_id}")

def get_all_chats() -> List[Dict[str, Any]]:
    """Возвращает список всех активных чатов и время последней активности."""
    chat_list = []
    for chat_id, messages in chats_db.items():
        last_activity = messages[-1].timestamp if messages else None # Нужна проверка на пустой список
        if last_activity: # Добавляем только если есть сообщения
             chat_list.append({"chat_id": chat_id, "last_activity": last_activity})
    # Сортируем по последней активности (самые новые сверху)
    chat_list.sort(key=lambda x: x["last_activity"], reverse=True)
    return chat_list


# --- Функция обработки сообщения и вызова НС ---

def process_user_message(chat_id: uuid.UUID, user_content: str) -> Tuple[Message, Message, Optional[Dict[str, Any]]]:
    """
    Обрабатывает сообщение пользователя, вызывает нейросеть и возвращает ответ.
    """
    # 1. Получаем текущую историю чата (для контекста нейросети)
    history = get_chat_history(chat_id) # Вызовет 404, если чат не найден

    # 2. Добавляем сообщение пользователя в историю
    user_message = add_message_to_chat(chat_id, role='user', content=user_content)

    # 3. Подготавливаем историю для модели (если она использует контекст)
    # Преобразуем наш формат Message в формат, ожидаемый моделью (если нужно)
    model_history = [{"role": msg.role, "content": msg.content} for msg in history]

    # 4. Вызываем нейросеть (заглушку)
    try:
        # Передаем ПОСЛЕДНЕЕ сообщение пользователя и ВСЮ историю до него
        prediction_result = model_predictor.predict(user_input=user_content, chat_history=model_history)
    except Exception as e:
        # Обработка ошибок от нейросети
        print(f"Error calling neural network for chat {chat_id}: {e}")
        # Формируем сообщение об ошибке для пользователя
        assistant_content = f"Извините, произошла ошибка при обработке вашего запроса: {e}"
        prediction_details = {"error": str(e)}
    else:
        # 5. Формируем ответ ассистента на основе предсказания
        # Логика формирования ответа зависит от того, что возвращает ваша модель
        pred_data = prediction_result.get("prediction")
        comment = prediction_result.get("comment", "")

        if pred_data:
             # Форматируем словарь свойств в строку
            properties_str = ", ".join([f"{key}: {value}" for key, value in pred_data.items()])
            assistant_content = f"Предсказанные свойства: {properties_str}. {comment}"
        else:
            assistant_content = comment if comment else "Не удалось получить предсказание."

        prediction_details = prediction_result # Сохраняем весь результат от НС

    # 6. Добавляем ответ ассистента в историю
    assistant_message = add_message_to_chat(chat_id, role='assistant', content=assistant_content)

    return user_message, assistant_message, prediction_details