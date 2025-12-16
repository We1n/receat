"""
Модуль мониторинга системы.
Содержит классы и функции для отслеживания состояния бота.
"""

from typing import Optional, Dict, Any
import logging
from telegram import Bot
from telegram.ext import ContextTypes
from .metrics import MetricsCollector

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Класс для мониторинга системы."""
    
    def __init__(self, bot: Optional[Bot] = None):
        """
        Инициализация монитора.
        
        Args:
            bot: Экземпляр бота для отправки алертов
        """
        self.metrics: Dict[str, Any] = {}
        self.bot = bot
        self.metrics_collector = MetricsCollector()
        
    def track_metric(self, name: str, value: Any) -> None:
        """
        Отслеживание метрики.
        
        Args:
            name: Название метрики
            value: Значение метрики
        """
        self.metrics[name] = value
        self.metrics_collector.record_metric(name, value)
        logger.debug(f"Метрика {name} обновлена: {value}")
        
    def get_metric(self, name: str) -> Optional[Any]:
        """
        Получение значения метрики.
        
        Args:
            name: Название метрики
            
        Returns:
            Значение метрики или None, если метрика не найдена
        """
        return self.metrics.get(name)
        
    def clear_metrics(self) -> None:
        """Очистка всех метрик."""
        self.metrics.clear()
        self.metrics_collector.clear_metrics()
        logger.debug("Метрики очищены")
    
    def track_command(self, command: str, duration: float, success: bool, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> None:
        """
        Отслеживание выполнения команды.
        
        Args:
            command: Название команды
            duration: Длительность выполнения
            success: Успешность выполнения
            context: Контекст бота
        """
        self.metrics_collector.record_metric(
            f"command_{command}",
            {"duration": duration, "success": success, "context": str(context)}
        )
    
    def track_callback(self, callback: str, duration: float, success: bool, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> None:
        """
        Отслеживание выполнения callback-запроса.
        
        Args:
            callback: Название callback
            duration: Длительность выполнения
            success: Успешность выполнения
            context: Контекст бота
        """
        self.metrics_collector.record_metric(
            f"callback_{callback}",
            {"duration": duration, "success": success, "context": str(context)}
        )
    
    def track_message(self, message_type: str, duration: float, success: bool, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> None:
        """
        Отслеживание обработки сообщения.
        
        Args:
            message_type: Тип сообщения
            duration: Длительность обработки
            success: Успешность обработки
            context: Контекст бота
        """
        self.metrics_collector.record_metric(
            f"message_{message_type}",
            {"duration": duration, "success": success, "context": str(context)}
        )
    
    def track_error(self, error_type: str, error_message: str, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> None:
        """
        Отслеживание ошибки.
        
        Args:
            error_type: Тип ошибки
            error_message: Сообщение об ошибке
            context: Контекст бота
        """
        self.metrics_collector.record_metric(
            f"error_{error_type}",
            {"message": error_message, "context": str(context)}
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Получение отчета о производительности.
        
        Returns:
            Словарь с отчетом о производительности
        """
        return self.metrics_collector.analyze_performance()

# Создаем глобальный экземпляр монитора системы
system_monitor = SystemMonitor() 