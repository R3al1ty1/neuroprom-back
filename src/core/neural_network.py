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
    :return: Ответ от нейросети или сообщение об ошибке
    """
    try:
        logger.info(f"Отправляем запрос к API с сообщениями: {messages}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.ai.url,
                headers={
                    "Authorization": f"Bearer {settings.ai.api_key}",
                    "HTTP-Referer": "https://neuroprom.com", # Убедитесь, что этот реферер разрешен в настройках OpenRouter, если там есть ограничения
                    "X-Title": "NeuroProm Chat",
                    "Content-Type": "application/json"
                },
                json={
                    "messages": messages,
                    "model": settings.ai.model,
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                timeout=30.0 # Увеличьте таймаут, если модель отвечает долго
            )

            # Логгируем статус и пытаемся прочитать тело ответа ДЛЯ ЛЮБОГО СТАТУСА
            try:
                response_body = response.json()
                logger.info(f"Статус ответа API: {response.status_code}. Тело ответа: {response_body}")
            except Exception as json_error:
                # Если не JSON, читаем как текст
                response_text = await response.aread() # Используем aread() для асинхронного чтения
                logger.error(f"Статус ответа API: {response.status_code}. Не удалось распарсить JSON: {json_error}. Тело ответа (текст): {response_text.decode(errors='ignore')}")
                return f"Извините, получен некорректный ответ от сервиса AI (статус {response.status_code})."


            if response.status_code == 200:
                # --- ИЗМЕНЕНИЕ НАЧИНАЕТСЯ ЗДЕСЬ ---
                # Проверяем наличие ключа 'choices' и что он не пустой
                if "choices" in response_body and response_body["choices"]:
                    # Дополнительная проверка на наличие 'message' и 'content'
                    try:
                        content = response_body["choices"][0]["message"]["content"]
                        logger.info("Успешно извлечен контент из ответа API.")
                        return content
                    except (KeyError, IndexError, TypeError) as e:
                        logger.error(f"Ошибка извлечения контента из ожидаемой структуры ответа: {e}. Ответ: {response_body}", exc_info=True)
                        return "Извините, структура ответа от сервиса AI неожиданная."
                # Если 'choices' нет, проверяем наличие ключа 'error' (частый формат ошибок)
                elif "error" in response_body:
                     error_message = response_body.get("error", {}).get("message", "Неизвестная ошибка в теле ответа")
                     logger.error(f"API вернул ошибку в теле ответа (статус 200): {response_body}")
                     return f"Сервис AI вернул ошибку: {error_message}"
                else:
                     # Если ни 'choices', ни 'error' нет
                     logger.error(f"Ответ API (статус 200) не содержит ключа 'choices' или 'error'. Ответ: {response_body}")
                     return "Извините, получен неожиданный формат ответа от сервиса AI."
                # --- ИЗМЕНЕНИЕ ЗАКАНЧИВАЕТСЯ ЗДЕСЬ ---
            else:
                # Логгирование уже произошло выше при попытке распарсить JSON
                error_detail = response_body.get("error", {}).get("message", "Детали не предоставлены") if isinstance(response_body, dict) else "Детали не являются словарем"
                return f"Извините, произошла ошибка при обработке запроса сервисом AI. Код: {response.status_code}. Детали: {error_detail}"

    except httpx.TimeoutException:
        logger.error("Ошибка: Превышен таймаут при запросе к API OpenRouter.", exc_info=True)
        return "Извините, сервис AI не ответил вовремя. Попробуйте еще раз позже."
    except httpx.RequestError as e:
        logger.error(f"Ошибка сети при запросе к API OpenRouter: {e}", exc_info=True)
        return f"Извините, произошла сетевая ошибка при обращении к сервису AI: {e}"
    except Exception as e:
        logger.error(f"Неожиданная ошибка при работе с API: {str(e)}", exc_info=True)
        return f"Извините, произошла внутренняя ошибка при обработке вашего запроса."