"""
Улучшенное логирование для бота
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
from telegram import Update, User, Message
from telegram.ext import ContextTypes

# Создаем директорию для логов
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Настраиваем форматирование логов
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Настраиваем файловый обработчик
file_handler = logging.FileHandler(
    log_dir / f"bot_{datetime.now().strftime('%Y%m%d')}.log",
    encoding='utf-8'
)
file_handler.setFormatter(formatter)

# Настраиваем консольный обработчик
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

class Logger:
    """Класс для улучшенного логирования"""
    
    def __init__(self, name: str):
        """
        Инициализация логгера
        
        Args:
            name: Имя логгера
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Добавляем обработчики
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_command(self, update: Update, command: str) -> None:
        """
        Логирование команды
        
        Args:
            update: Обновление от Telegram
            command: Команда
        """
        user = update.effective_user
        if not user:
            return
        
        user_id = user.id
        username = user.username or "Unknown"
        
        self.logger.info(
            f"👤 Команда: {command} | "
            f"Пользователь: {username} (ID: {user_id})"
        )
    
    def log_message(self, update: Update) -> None:
        """
        Логирование сообщения
        
        Args:
            update: Обновление от Telegram
        """
        user = update.effective_user
        message = update.message
        if not user or not message:
            return
        
        user_id = user.id
        username = user.username or "Unknown"
        text = message.text or ""
        
        self.logger.info(
            f"💬 Сообщение | "
            f"Пользователь: {username} (ID: {user_id}) | "
            f"Текст: {text}"
        )
    
    def log_callback(self, update: Update, callback_data: str) -> None:
        """
        Логирование callback
        
        Args:
            update: Обновление от Telegram
            callback_data: Данные callback
        """
        user = update.effective_user
        if not user:
            return
        
        user_id = user.id
        username = user.username or "Unknown"
        
        self.logger.info(
            f"🔘 Callback: {callback_data} | "
            f"Пользователь: {username} (ID: {user_id})"
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Логирование ошибки
        
        Args:
            error: Ошибка
            context: Контекст ошибки
        """
        error_data = {
            "error": str(error),
            "type": type(error).__name__,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        self.logger.error(
            f"❌ Ошибка: {error} | "
            f"Тип: {type(error).__name__} | "
            f"Контекст: {json.dumps(context or {}, ensure_ascii=False)}"
        )
        
        # Сохраняем ошибку в отдельный файл
        error_file = log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        with open(error_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(error_data, ensure_ascii=False) + "\n")
    
    def log_state_change(self, user_id: int, old_state: str, new_state: str) -> None:
        """
        Логирование изменения состояния
        
        Args:
            user_id: ID пользователя
            old_state: Старое состояние
            new_state: Новое состояние
        """
        self.logger.info(
            f"🔄 Изменение состояния | "
            f"Пользователь: {user_id} | "
            f"Старое состояние: {old_state} | "
            f"Новое состояние: {new_state}"
        )
    
    def log_action(self, action: str, user_id: int, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Логирование действия
        
        Args:
            action: Действие
            user_id: ID пользователя
            details: Детали действия
        """
        self.logger.info(
            f"⚡️ Действие: {action} | "
            f"Пользователь: {user_id} | "
            f"Детали: {json.dumps(details or {}, ensure_ascii=False)}"
        )
    
    def log_performance(self, operation: str, duration: float) -> None:
        """
        Логирование производительности
        
        Args:
            operation: Операция
            duration: Длительность в секундах
        """
        self.logger.info(
            f"⏱ Производительность | "
            f"Операция: {operation} | "
            f"Длительность: {duration:.2f} сек"
        )
    
    def log_data_change(self, data_type: str, action: str, details: Dict[str, Any]) -> None:
        """
        Логирование изменения данных
        
        Args:
            data_type: Тип данных
            action: Действие
            details: Детали изменения
        """
        self.logger.info(
            f"📝 Изменение данных | "
            f"Тип: {data_type} | "
            f"Действие: {action} | "
            f"Детали: {json.dumps(details, ensure_ascii=False)}"
        ) 