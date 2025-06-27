import logging
import os
from typing import Optional
from telegram import Bot
from src.config import Config

logger = logging.getLogger("alerting")

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")


def log_critical_error(message: str, exc: Optional[Exception] = None):
    logger.critical(f"CRITICAL: {message}", exc_info=exc)
    # Можно расширить: отправлять уведомление админу
    if ADMIN_CHAT_ID and BOT_TOKEN:
        try:
            bot = Bot(token=BOT_TOKEN)
            text = f"❗️ Критическая ошибка:\n{message}"
            if exc:
                text += f"\n{exc}"
            # Убираем асинхронный вызов из синхронной функции
            logger.info(f"Алерт для админа: {text}")
        except Exception as e:
            logger.error(f"Ошибка при отправке алерта админу: {e}")

async def send_critical_alert_admin(message: str, exc: Optional[Exception] = None):
    """Отправить критическую ошибку админу через Telegram."""
    admin_id = getattr(Config, 'ADMIN_ID', None)
    bot_token = getattr(Config, 'BOT_TOKEN', None)
    if admin_id and bot_token:
        try:
            bot = Bot(token=bot_token)
            text = f"❗️ EatBot: Критическая ошибка!\n{message}"
            if exc:
                text += f"\n{exc}"
            from datetime import datetime
            text += f"\nВремя: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await bot.send_message(chat_id=admin_id, text=text)
            logger.info(f"Уведомление админу {admin_id} отправлено")
        except Exception as e:
            logger.error(f"Ошибка при отправке алерта админу: {e}")
    else:
        logger.error("Не задан ADMIN_ID или BOT_TOKEN для отправки алерта админу") 