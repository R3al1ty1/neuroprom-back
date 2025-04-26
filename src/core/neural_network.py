from typing import List
import httpx
import logging
from core.settings import settings

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_ai_response(messages: List[dict]) -> str:
    """
    Получает ответ от нейросети через OpenRouter API.
    
    :param messages: Список сообщений с их ролями
    :return: Ответ от нейросети
    """
    try:
        logger.info(f"Отправляем запрос к API с сообщениями: {messages}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.ai.url,
                headers={
                    "Authorization": f"Bearer {settings.ai.api_key}",
                    "HTTP-Referer": "https://neuroprom.com",
                    "X-Title": "NeuroProm Chat",  # Используем только ASCII символы
                    "Content-Type": "application/json"
                },
                json={
                    "messages": messages,
                    "model": settings.ai.model,
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Получен успешный ответ от API")
                return result["choices"][0]["message"]["content"]
            else:
                error_content = await response.aread()
                logger.error(f"Ошибка API: status_code={response.status_code}, response={error_content}")
                return f"Извините, произошла ошибка при обработке запроса. Код ошибки: {response.status_code}"
                
    except Exception as e:
        logger.error(f"Ошибка при работе с API: {str(e)}", exc_info=True)
        return f"Извините, произошла ошибка при обработке вашего запроса: {str(e)}"
