"""
Модуль для мониторинга использования кэша
"""

import time
import logging
from typing import Dict, Any, List, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
from src.config import Config

logger = logging.getLogger(__name__)

class CacheMonitor:
    """Класс для мониторинга использования кэша"""
    
    def __init__(self):
        """Инициализация монитора кэша"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': 0,
            'max_size': Config.USER_CACHE_MAX_SIZE,
            'last_cleanup': time.time(),
            'cleanup_count': 0,
            'operations': defaultdict(int),
            'errors': defaultdict(int),
            'performance': {
                'response_times': deque(maxlen=1000),  # Храним последние 1000 операций
                'memory_usage': deque(maxlen=1000),
                'peak_memory': 0,
                'slow_operations': defaultdict(int)
            }
        }
        self.logger = logging.getLogger(__name__)
    
    def record_hit(self, cache_name: str) -> None:
        """
        Записывает успешное попадание в кэш
        
        Args:
            cache_name: Имя кэша
        """
        self.stats['hits'] += 1
        self.stats['operations'][f'{cache_name}_hit'] += 1
        self.logger.debug(f"Кэш-хит: {cache_name}")
    
    def record_miss(self, cache_name: str) -> None:
        """
        Записывает промах кэша
        
        Args:
            cache_name: Имя кэша
        """
        self.stats['misses'] += 1
        self.stats['operations'][f'{cache_name}_miss'] += 1
        self.logger.debug(f"Кэш-промах: {cache_name}")
    
    def record_eviction(self, cache_name: str) -> None:
        """
        Записывает вытеснение из кэша
        
        Args:
            cache_name: Имя кэша
        """
        self.stats['evictions'] += 1
        self.stats['operations'][f'{cache_name}_eviction'] += 1
        self.logger.debug(f"Вытеснение из кэша: {cache_name}")
    
    def record_cleanup(self, evicted_count: int) -> None:
        """
        Записывает очистку кэша
        
        Args:
            evicted_count: Количество вытесненных записей
        """
        self.stats['cleanup_count'] += 1
        self.stats['last_cleanup'] = time.time()
        self.stats['evictions'] += evicted_count
        self.logger.info(f"Очистка кэша: вытеснено {evicted_count} записей")
    
    def record_error(self, cache_name: str, error: Exception) -> None:
        """
        Записывает ошибку кэша
        
        Args:
            cache_name: Имя кэша
            error: Объект ошибки
        """
        error_type = type(error).__name__
        self.stats['errors'][f'{cache_name}_{error_type}'] += 1
        self.logger.error(f"Ошибка кэша {cache_name}: {str(error)}")
    
    def update_size(self, current_size: int) -> None:
        """
        Обновляет информацию о размере кэша
        
        Args:
            current_size: Текущий размер кэша
        """
        self.stats['size'] = current_size
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получает текущую статистику кэша
        
        Returns:
            Dict[str, Any]: Статистика кэша
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'evictions': self.stats['evictions'],
            'size': self.stats['size'],
            'max_size': self.stats['max_size'],
            'usage': f"{(self.stats['size'] / self.stats['max_size'] * 100):.2f}%",
            'cleanup_count': self.stats['cleanup_count'],
            'last_cleanup': datetime.fromtimestamp(self.stats['last_cleanup']).strftime('%Y-%m-%d %H:%M:%S'),
            'operations': dict(self.stats['operations']),
            'errors': dict(self.stats['errors'])
        }
    
    def get_operation_stats(self) -> Dict[str, int]:
        """
        Получает статистику операций кэша
        
        Returns:
            Dict[str, int]: Статистика операций
        """
        return dict(self.stats['operations'])
    
    def get_error_stats(self) -> Dict[str, int]:
        """
        Получает статистику ошибок кэша
        
        Returns:
            Dict[str, int]: Статистика ошибок
        """
        return dict(self.stats['errors'])
    
    def reset_stats(self) -> None:
        """Сбрасывает статистику кэша"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': 0,
            'max_size': Config.USER_CACHE_MAX_SIZE,
            'last_cleanup': time.time(),
            'cleanup_count': 0,
            'operations': defaultdict(int),
            'errors': defaultdict(int),
            'performance': {
                'response_times': deque(maxlen=1000),  # Храним последние 1000 операций
                'memory_usage': deque(maxlen=1000),
                'peak_memory': 0,
                'slow_operations': defaultdict(int)
            }
        }
        self.logger.info("Статистика кэша сброшена")
    
    def record_performance(self, operation: str, start_time: float, memory_usage: int) -> None:
        """
        Записывает метрики производительности
        
        Args:
            operation: Тип операции
            start_time: Время начала операции
            memory_usage: Использование памяти
        """
        response_time = time.time() - start_time
        self.stats['performance']['response_times'].append(response_time)
        self.stats['performance']['memory_usage'].append(memory_usage)
        
        # Обновляем пиковое использование памяти
        if memory_usage > self.stats['performance']['peak_memory']:
            self.stats['performance']['peak_memory'] = memory_usage
        
        # Отмечаем медленные операции (более 100мс)
        if response_time > 0.1:
            self.stats['performance']['slow_operations'][operation] += 1
            self.logger.warning(f"Медленная операция {operation}: {response_time:.3f}с")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Получает статистику производительности
        
        Returns:
            Dict[str, Any]: Статистика производительности
        """
        response_times = list(self.stats['performance']['response_times'])
        memory_usage = list(self.stats['performance']['memory_usage'])
        
        if not response_times:
            return {
                'avg_response_time': 0,
                'max_response_time': 0,
                'min_response_time': 0,
                'avg_memory_usage': 0,
                'peak_memory': 0,
                'slow_operations': {}
            }
        
        return {
            'avg_response_time': sum(response_times) / len(response_times),
            'max_response_time': max(response_times),
            'min_response_time': min(response_times),
            'avg_memory_usage': sum(memory_usage) / len(memory_usage),
            'peak_memory': self.stats['performance']['peak_memory'],
            'slow_operations': dict(self.stats['performance']['slow_operations'])
        }
    
    def get_recommendations(self) -> List[str]:
        """
        Получает рекомендации по оптимизации кэша
        
        Returns:
            List[str]: Список рекомендаций
        """
        recommendations = []
        perf_stats = self.get_performance_stats()
        
        # Проверяем эффективность кэша
        hit_rate = (self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) * 100) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
        if hit_rate < 50:
            recommendations.append(f"⚠️ Низкая эффективность кэша: {hit_rate:.1f}% попаданий")
        
        # Проверяем использование памяти
        memory_usage_percent = (self.stats['size'] / self.stats['max_size']) * 100
        if memory_usage_percent > 80:
            recommendations.append(f"⚠️ Высокое использование памяти: {memory_usage_percent:.1f}%")
        
        # Проверяем медленные операции
        if perf_stats['avg_response_time'] > 0.05:
            recommendations.append(f"⚠️ Высокое среднее время отклика: {perf_stats['avg_response_time']:.3f}с")
        
        # Проверяем частоту очистки
        if self.stats['cleanup_count'] > 100:
            recommendations.append("⚠️ Частые очистки кэша - возможно стоит увеличить TTL")
        
        return recommendations

# Создаем глобальный экземпляр монитора кэша
cache_monitor = CacheMonitor() 