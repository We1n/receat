"""
Модуль мониторинга ошибок.
Содержит классы и функции для отслеживания и обработки ошибок.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass
from src.utils.cache import cache
from telegram import Bot
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

@dataclass
class MonitorConfig:
    """Конфигурация для мониторинга ошибок"""
    alert_threshold: int = 5  # Количество ошибок для оповещения
    alert_window: int = 300  # Окно времени в секундах
    alert_cooldown: int = 3600  # Задержка между оповещениями в секундах
    cache_ttl: int = 300  # 5 минут
    log_level: str = "WARNING"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class ErrorMonitor:
    """Класс для мониторинга ошибок."""
    
    def __init__(self, bot: Optional[Bot] = None, config: Optional[MonitorConfig] = None):
        """
        Инициализация монитора ошибок.
        
        Args:
            bot: Экземпляр бота для отправки алертов
            config: Конфигурация монитора
        """
        self.errors: Dict[str, List[Dict[str, Any]]] = {}
        self.bot = bot
        self.config = config or MonitorConfig()
        self.alert_threshold = self.config.alert_threshold
        
        # Создаем директорию для логов
        self.logs_dir = os.path.join("logs", "monitoring")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Настраиваем логирование
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format=self.config.log_format,
            handlers=[
                logging.FileHandler(os.path.join(self.logs_dir, "monitoring.log")),
                logging.StreamHandler()
            ]
        )
        
        logger.info("Инициализирован ErrorMonitor")
    
    def record_error(self, error_type: str, error_message: str, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> None:
        """
        Запись ошибки.
        
        Args:
            error_type: Тип ошибки
            error_message: Сообщение об ошибке
            context: Контекст бота
        """
        if error_type not in self.errors:
            self.errors[error_type] = []
            
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'message': error_message,
            'context': str(context) if context else None
        }
        
        self.errors[error_type].append(error_data)
        logger.error(f"Ошибка {error_type}: {error_message}")
        
        # Проверяем количество ошибок для отправки алерта
        if len(self.errors[error_type]) >= self.alert_threshold:
            self._send_alert(error_type)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Получение статистики ошибок.
        
        Returns:
            Словарь со статистикой ошибок
        """
        stats = {
            'total_errors': sum(len(errors) for errors in self.errors.values()),
            'error_types': {
                error_type: len(errors)
                for error_type, errors in self.errors.items()
            },
            'recent_errors': {
                error_type: errors[-5:]  # Последние 5 ошибок каждого типа
                for error_type, errors in self.errors.items()
            }
        }
        return stats
    
    def clear_errors(self) -> None:
        """Очистка всех ошибок."""
        self.errors.clear()
        logger.info("История ошибок очищена")
    
    def export_errors(self, filepath: str) -> None:
        """
        Экспорт ошибок в файл.
        
        Args:
            filepath: Путь к файлу для экспорта
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, ensure_ascii=False, indent=2)
            logger.info(f"Ошибки экспортированы в {filepath}")
        except Exception as e:
            logger.error(f"Ошибка при экспорте: {e}")
    
    def _send_alert(self, error_type: str) -> None:
        """
        Отправка алерта об ошибках.
        
        Args:
            error_type: Тип ошибки
        """
        if not self.bot:
            return
            
        error_count = len(self.errors[error_type])
        recent_errors = self.errors[error_type][-self.alert_threshold:]
        
        message = (
            f"🚨 Внимание! Обнаружено {error_count} ошибок типа {error_type}\n\n"
            f"Последние ошибки:\n"
        )
        
        for error in recent_errors:
            message += f"- {error['message']} ({error['timestamp']})\n"
            
        try:
            # Отправляем алерт администраторам
            # TODO: Добавить список администраторов
            pass
        except Exception as e:
            logger.error(f"Ошибка при отправке алерта: {e}")

# Создаем глобальный экземпляр монитора ошибок
error_monitor = ErrorMonitor() 