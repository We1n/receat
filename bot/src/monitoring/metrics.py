"""
Модуль для сбора и анализа метрик системы.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import logging
from src.config import Config
import json
import os

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Класс для сбора и анализа метрик"""
    
    def __init__(self, max_history: int = 1000):
        """
        Инициализация коллектора метрик
        
        Args:
            max_history: Максимальное количество записей в истории
        """
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.current_metrics: Dict[str, Any] = {}
        self.start_time = time.time()
        logger.info("Инициализирован MetricsCollector")
    
    def record_metric(self, name: str, value: Any, tags: Optional[Dict[str, str]] = None):
        """
        Запись метрики
        
        Args:
            name: Название метрики
            value: Значение метрики
            tags: Теги метрики
        """
        metric = {
            'name': name,
            'value': value,
            'tags': tags or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.current_metrics[name] = metric
        self.metrics_history.append(metric)
        logger.debug(f"Записана метрика {name}: {value}")
    
    def get_metric(self, name: str) -> Optional[Any]:
        """
        Получение значения метрики
        
        Args:
            name: Название метрики
            
        Returns:
            Значение метрики или None
        """
        return self.current_metrics.get(name, {}).get('value')
    
    def get_metrics_by_tags(self, tags: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Получение метрик по тегам
        
        Args:
            tags: Словарь тегов
            
        Returns:
            Список метрик
        """
        return [
            metric for metric in self.metrics_history
            if all(metric['tags'].get(k) == v for k, v in tags.items())
        ]
    
    def get_metrics_history(self, name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получение истории метрик
        
        Args:
            name: Название метрики
            limit: Ограничение количества записей
            
        Returns:
            Список метрик
        """
        history = [
            metric for metric in self.metrics_history
            if metric['name'] == name
        ]
        
        if limit:
            return history[-limit:]
        return history
    
    def calculate_statistics(self, name: str) -> Dict[str, float]:
        """
        Расчет статистики по метрике
        
        Args:
            name: Название метрики
            
        Returns:
            Словарь со статистикой
        """
        values = [
            metric['value'] for metric in self.metrics_history
            if metric['name'] == name and isinstance(metric['value'], (int, float))
        ]
        
        if not values:
            return {}
            
        return {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(values)
        }
    
    def save_metrics(self, filepath: str):
        """
        Сохранение метрик в файл
        
        Args:
            filepath: Путь к файлу
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(list(self.metrics_history), f, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении метрик: {e}")
            
    def load_metrics(self, filepath: str):
        """
        Загрузка метрик из файла
        
        Args:
            filepath: Путь к файлу
        """
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    metrics = json.load(f)
                    self.metrics_history = deque(metrics, maxlen=self.max_history)
        except Exception as e:
            logger.error(f"Ошибка при загрузке метрик: {e}")
            
    def clear_metrics(self):
        """Очистка метрик"""
        self.metrics_history.clear()
        self.current_metrics.clear()
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Получение метрик производительности
        
        Returns:
            Словарь с метриками производительности
        """
        return {
            'uptime': time.time() - self.start_time,
            'metrics_count': len(self.metrics_history),
            'current_metrics': self.current_metrics
        }
        
    def analyze_performance(self) -> Dict[str, Any]:
        """
        Анализ производительности
        
        Returns:
            Словарь с результатами анализа
        """
        analysis = {
            'metrics_count': len(self.metrics_history),
            'uptime': time.time() - self.start_time,
            'performance_issues': []
        }
        
        # Анализируем метрики на наличие проблем
        for metric in self.metrics_history:
            if isinstance(metric['value'], (int, float)):
                # Проверяем аномальные значения
                if metric['value'] < 0 or metric['value'] > 1000:
                    analysis['performance_issues'].append({
                        'metric': metric['name'],
                        'value': metric['value'],
                        'timestamp': metric['timestamp'],
                        'issue': 'Аномальное значение'
                    })
                    
        return analysis
        
    def get_metric_trends(self, name: str, window: int = 10) -> Dict[str, Any]:
        """
        Анализ трендов метрики
        
        Args:
            name: Название метрики
            window: Размер окна для анализа
            
        Returns:
            Словарь с трендами
        """
        values = [
            metric['value'] for metric in self.metrics_history
            if metric['name'] == name and isinstance(metric['value'], (int, float))
        ]
        
        if not values or len(values) < window:
            return {}
            
        recent_values = values[-window:]
        previous_values = values[-window-1:-1]
        
        if not previous_values:
            return {}
            
        # Рассчитываем тренд
        recent_avg = sum(recent_values) / len(recent_values)
        previous_avg = sum(previous_values) / len(previous_values)
        
        trend = (recent_avg - previous_avg) / previous_avg * 100 if previous_avg != 0 else 0
        
        return {
            'trend': trend,
            'recent_avg': recent_avg,
            'previous_avg': previous_avg,
            'direction': 'up' if trend > 0 else 'down' if trend < 0 else 'stable'
        }
        
    def get_metric_correlations(self, metric1: str, metric2: str) -> Dict[str, float]:
        """
        Расчет корреляции между метриками
        
        Args:
            metric1: Название первой метрики
            metric2: Название второй метрики
            
        Returns:
            Словарь с коэффициентами корреляции
        """
        values1 = [
            metric['value'] for metric in self.metrics_history
            if metric['name'] == metric1 and isinstance(metric['value'], (int, float))
        ]
        
        values2 = [
            metric['value'] for metric in self.metrics_history
            if metric['name'] == metric2 and isinstance(metric['value'], (int, float))
        ]
        
        if not values1 or not values2 or len(values1) != len(values2):
            return {}
            
        # Рассчитываем корреляцию
        n = len(values1)
        mean1 = sum(values1) / n
        mean2 = sum(values2) / n
        
        covariance = sum((x - mean1) * (y - mean2) for x, y in zip(values1, values2)) / n
        std1 = (sum((x - mean1) ** 2 for x in values1) / n) ** 0.5
        std2 = (sum((y - mean2) ** 2 for y in values2) / n) ** 0.5
        
        if std1 == 0 or std2 == 0:
            return {}
            
        correlation = covariance / (std1 * std2)
        
        return {
            'correlation': correlation,
            'strength': 'strong' if abs(correlation) > 0.7 else 'moderate' if abs(correlation) > 0.3 else 'weak',
            'direction': 'positive' if correlation > 0 else 'negative' if correlation < 0 else 'none'
        }
    
    def record_call(self, name: str, duration: float, status: str) -> None:
        """
        Запись метрики вызова
        
        Args:
            name: Название вызова
            duration: Длительность в секундах
            status: Статус вызова
        """
        self.record_metric(
            'call_duration',
            duration,
            {'name': name, 'status': status}
        )
        self.record_metric(
            'calls_total',
            1,
            {'name': name, 'status': status}
        )
    
    def record_db_operation(self, operation: str, duration: float, status: str) -> None:
        """
        Запись метрики операции с БД
        
        Args:
            operation: Тип операции
            duration: Длительность операции в секундах
            status: Статус операции
        """
        self.record_metric(
            'db_operation_duration',
            duration,
            {'operation': operation, 'status': status}
        )
        self.record_metric(
            'db_operations_total',
            1,
            {'operation': operation, 'status': status}
        )
    
    def record_cache_operation(self, operation: str, hit: bool) -> None:
        """
        Запись метрики операции с кэшем
        
        Args:
            operation: Тип операции
            hit: Попадание в кэш
        """
        self.record_metric(
            'cache_operations_total',
            1,
            {'operation': operation, 'hit': str(hit)}
        )
    
    def record_user_action(self, action: str, user_id: int) -> None:
        """
        Запись метрики действия пользователя
        
        Args:
            action: Тип действия
            user_id: ID пользователя
        """
        self.record_metric(
            'user_actions_total',
            1,
            {'action': action, 'user_id': str(user_id)}
        )
    
    def get_system_uptime(self) -> float:
        """
        Получение времени работы системы
        
        Returns:
            float: Время работы в секундах
        """
        return time.time() - self.start_time 