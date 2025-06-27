"""
Модуль логирования для EatTGBot.

Этот модуль предоставляет расширенную систему логирования с поддержкой:
- Ротации логов
- Структурированного логирования в JSON
- Контекстного логирования
- Разных уровней логирования для компонентов
- Логирования SQL-запросов

Пример использования:
    from src.logger import setup_logger, log_with_context
    
    # Инициализация логгеров
    logger = setup_logger(__name__)
    
    # Логирование с контекстом
    log_with_context(
        logger,
        'info',
        'User started conversation',
        user_id=123,
        chat_id=456,
        action='start'
    )
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
import os
from datetime import datetime
import json
from src.config import Config

class ContextFilter(logging.Filter):
    """
    Фильтр для добавления контекстной информации в логи.
    
    Этот фильтр добавляет поле 'context' в запись лога, если оно отсутствует.
    Контекстная информация может включать user_id, chat_id, action и другие данные.
    """
    def filter(self, record):
        if not hasattr(record, 'context'):
            record.context = {}
        return True

class JSONFormatter(logging.Formatter):
    """
    Форматтер для структурированного логирования в JSON.
    
    Преобразует запись лога в JSON-строку со следующими полями:
    - timestamp: время создания записи
    - level: уровень логирования
    - logger: имя логгера
    - message: сообщение
    - context: контекстная информация
    - exception: информация об исключении (если есть)
    """
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'context': getattr(record, 'context', {}),
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)

def setup_logger(name: str, log_file: Optional[str] = None, force_utf8: bool = True) -> logging.Logger:
    """
    Настройка логгера
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу лога
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Хендлер для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.encoding = 'utf-8'
    if force_utf8:
        # Принудительно устанавливаем кодировку UTF-8 для всех обработчиков
        # Это особенно важно для Windows, где стандартная кодировка (cp1251) не поддерживает многие символы
        for handler in logging.root.handlers:
            if isinstance(handler, (logging.FileHandler, logging.StreamHandler)):
                handler.setFormatter(formatter)
                handler.encoding = 'utf-8'

    logger.addHandler(console_handler)
    
    # Хендлер для записи в файл
    if log_file:
        # Убедимся, что кодировка для файла также установлена
        file_encoding = 'utf-8' if force_utf8 else None
        max_bytes = getattr(Config, 'LOG_MAX_BYTES', 10*1024*1024)
        backup_count = getattr(Config, 'LOG_MAX_FILES', 5)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=file_encoding
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_with_context(logger, level, message, **context):
    """
    Вспомогательная функция для логирования с контекстом.
    
    Args:
        logger: Логгер для записи
        level (str): Уровень логирования ('debug', 'info', 'warning', 'error', 'critical')
        message (str): Сообщение для логирования
        **context: Контекстная информация (user_id, chat_id, action и т.д.)
    """
    extra = {'context': context}
    if level == 'debug':
        logger.debug(message, extra=extra)
    elif level == 'info':
        logger.info(message, extra=extra)
    elif level == 'warning':
        logger.warning(message, extra=extra)
    elif level == 'error':
        logger.error(message, extra=extra)
    elif level == 'critical':
        logger.critical(message, extra=extra)
