#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import codecs
import psutil  # Для проверки PID
import logging

# Исправление для Windows event loop - ДОЛЖНО БЫТЬ В САМОМ НАЧАЛЕ
if sys.platform == 'win32':
    # Дополнительная настройка для Windows
    import asyncio
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.logger import setup_logger
logger = setup_logger('bot', log_file=os.path.join('logs', 'bot.log'))

from telegram import Update
from telegram.ext import Application, ContextTypes

from src.config import Config
from src.services.data_service import DataService
# LEGACY: Удалены импорты старых обработчиков
# from src.ui.handlers.collaborative_handlers import setup_collaborative_handlers
# from src.ui.handlers.product_handlers import register_product_handlers
# from src.ui.handlers.nutrient_handlers import register_nutrient_handlers
from src.ui.handlers.text_message_handler import register_text_message_handlers
from src.ui.handlers.command_handlers import CommandHandlers
from src.ui.handlers.main_callback_router import callback_router, handle_callback
from src.ui.handlers.navigation_handler import navigation_handler
from src.ui.handlers.recipe_handlers import recipe_handler
from src.ui.handlers.product_handlers import product_handler
from src.ui.handlers.main_handler import main_handler
from src.ui.handlers.conversation_handlers import create_recipe_conversation_handler
from src.monitoring.alerting import send_critical_alert_admin
# from src.monitoring.monitor import SystemMonitor # Temporarily disabled for debugging

# --- Lock file mechanism to prevent multiple instances ---
LOCK_FILE = Path("bot.lock")

def cleanup_lock_file():
    """Safely removes the lock file."""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            logger.info("Lock file removed.")
    except Exception as e:
        logger.error(f"Error removing lock file: {e}")

async def setup_handlers(application: Application) -> None:
    """Настройка всех обработчиков"""
    logger.info("Настройка обработчиков...")
    
    # Initialize services and handlers
    data_service = DataService()
    command_handlers = CommandHandlers()

    # Регистрируем обработчик навигации в роутере
    callback_router.register_handler("nav", navigation_handler)
    logger.info("Обработчик навигации зарегистрирован")
    
    # Регистрируем обработчик главного меню в роутере
    callback_router.register_handler("main", main_handler)
    logger.info("Обработчик главного меню зарегистрирован")
    
    # Регистрируем обработчик рецептов в роутере
    callback_router.register_handler("recipes", recipe_handler)
    logger.info("Обработчик рецептов зарегистрирован")

    # Регистрируем обработчик продуктов в роутере
    callback_router.register_handler("products", product_handler)
    logger.info("Обработчик продуктов зарегистрирован")

    # LEGACY: Удалена регистрация старых обработчиков
    # setup_collaborative_handlers(application, data_service, callback_handler)
    # register_product_handlers(application)
    # register_nutrient_handlers(application)
    
    # Регистрируем обработчики текстовых сообщений
    register_text_message_handlers(application)
    command_handlers.register_handlers(application)
    
    # Регистрируем новый ConversationHandler для рецептов
    recipe_conv_handler = create_recipe_conversation_handler()
    application.add_handler(recipe_conv_handler)
    logger.info("ConversationHandler для рецептов зарегистрирован")
    
    # Регистрируем единый обработчик колбэков
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(handle_callback))
    logger.info("Единый роутер колбэков зарегистрирован")
    
    logger.info("Обработчики настроены успешно")

async def main() -> None:
    """Main function to setup and run the bot."""
    Config.create_dirs()
    if not Config.BOT_TOKEN:
        logger.critical("Bot token not found! Cannot start.")
        return

    # Initialize bot
    application = Application.builder().token(Config.BOT_TOKEN).build()
    # Setup handlers
    await setup_handlers(application)

    # Global error handler
    async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        error = context.error
        logger.error(f"Global error: {error}", exc_info=True)
        # await send_critical_alert_admin(f'Global error: {error}', error)

    application.add_error_handler(global_error_handler)
    logger.info("Bot starting polling...")
    
    try:
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
    except RuntimeError as e:
        if "event loop" in str(e).lower():
            logger.info("Event loop error detected, trying alternative approach...")
            # Альтернативный подход
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            logger.info("Бот запущен в альтернативном режиме")
            # Ждем бесконечно
            while True:
                await asyncio.sleep(1)
        else:
            raise
    except Exception as e:
        logger.critical(f"Error during polling: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    # Load .env file
    if find_dotenv():
        load_dotenv(find_dotenv())
        logger.info(".env file found and loaded.")
    else:
        logger.warning(".env file not found.")

    # Handle lock file to ensure single instance (PID-aware)
    if LOCK_FILE.exists():
        try:
            with LOCK_FILE.open("r") as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                logger.warning(f"Lock file found. Another instance (PID {pid}) may be running. Exiting.")
                sys.exit(0)
            else:
                logger.warning(f"Stale lock file found (PID {pid} not running). Removing lock file.")
                cleanup_lock_file()
        except Exception as e:
            logger.warning(f"Error reading lock file: {e}. Removing lock file.")
            cleanup_lock_file()

    try:
        with LOCK_FILE.open("w") as f:
            f.write(str(os.getpid()))
        logger.info(f"Lock file created with PID {os.getpid()}.")
        # Упрощенный запуск для всех платформ
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
    except Exception as e:
        logger.critical(f"A critical error occurred in the main execution block: {e}", exc_info=True)
    finally:
        cleanup_lock_file()

# Add FileHandler for root-logger
fh = logging.FileHandler('logs/bot.log', encoding='utf-8')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logging.getLogger().addHandler(fh)
