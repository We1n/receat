import time
import psutil
import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Мониторинг производительности системы"""
    
    def __init__(self, history_size=1000):
        self.history_size = history_size
        self.query_times = deque(maxlen=history_size)
        self.memory_usage = deque(maxlen=history_size)
        self.cpu_usage = deque(maxlen=history_size)
        self.error_count = deque(maxlen=history_size)
        self.start_time = time.time()
        
        # Пороговые значения для алертов
        self.thresholds = {
            'query_time': 1.0,  # секунды
            'memory_usage': 0.8,  # 80% от доступной памяти
            'cpu_usage': 0.8,  # 80% от CPU
            'error_rate': 0.1  # 10% ошибок
        }
    
    def record_query_time(self, query: str, execution_time: float):
        """Запись времени выполнения запроса"""
        self.query_times.append({
            'timestamp': datetime.now(),
            'query': query,
            'execution_time': execution_time
        })
        
        if execution_time > self.thresholds['query_time']:
            logger.warning(
                "Медленный запрос: %s (%.2f сек)",
                query,
                execution_time
            )
    
    def record_memory_usage(self):
        """Запись использования памяти"""
        memory = psutil.Process().memory_percent()
        self.memory_usage.append({
            'timestamp': datetime.now(),
            'usage': memory
        })
        
        if memory > self.thresholds['memory_usage'] * 100:
            logger.warning(
                "Высокое использование памяти: %.1f%%",
                memory
            )
    
    def record_cpu_usage(self):
        """Запись использования CPU"""
        cpu = psutil.Process().cpu_percent()
        self.cpu_usage.append({
            'timestamp': datetime.now(),
            'usage': cpu
        })
        
        if cpu > self.thresholds['cpu_usage'] * 100:
            logger.warning(
                "Высокая нагрузка на CPU: %.1f%%",
                cpu
            )
    
    def record_error(self, error_type: str, error_message: str):
        """Запись ошибки"""
        self.error_count.append({
            'timestamp': datetime.now(),
            'type': error_type,
            'message': error_message
        })
    
    def get_performance_stats(self) -> Dict:
        """Получение статистики производительности"""
        return {
            'uptime': time.time() - self.start_time,
            'query_stats': self._get_query_stats(),
            'memory_stats': self._get_memory_stats(),
            'cpu_stats': self._get_cpu_stats(),
            'error_stats': self._get_error_stats()
        }
    
    def _get_query_stats(self) -> Dict:
        """Статистика по запросам"""
        if not self.query_times:
            return {}
        
        times = [q['execution_time'] for q in self.query_times]
        return {
            'avg_time': sum(times) / len(times),
            'max_time': max(times),
            'min_time': min(times),
            'total_queries': len(times)
        }
    
    def _get_memory_stats(self) -> Dict:
        """Статистика по памяти"""
        if not self.memory_usage:
            return {}
        
        usage = [m['usage'] for m in self.memory_usage]
        return {
            'avg_usage': sum(usage) / len(usage),
            'max_usage': max(usage),
            'current_usage': usage[-1]
        }
    
    def _get_cpu_stats(self) -> Dict:
        """Статистика по CPU"""
        if not self.cpu_usage:
            return {}
        
        usage = [c['usage'] for c in self.cpu_usage]
        return {
            'avg_usage': sum(usage) / len(usage),
            'max_usage': max(usage),
            'current_usage': usage[-1]
        }
    
    def _get_error_stats(self) -> Dict:
        """Статистика по ошибкам"""
        if not self.error_count:
            return {}
        
        error_types = {}
        for error in self.error_count:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_count),
            'error_types': error_types
        }
    
    def get_slow_queries(self, threshold: Optional[float] = None) -> List[Dict]:
        """Получение списка медленных запросов"""
        if threshold is None:
            threshold = self.thresholds['query_time']
        
        return [
            q for q in self.query_times
            if q['execution_time'] > threshold
        ]
    
    def get_error_summary(self) -> Dict:
        """Получение сводки по ошибкам"""
        if not self.error_count:
            return {}
        
        error_types = {}
        for error in self.error_count:
            error_type = error['type']
            if error_type not in error_types:
                error_types[error_type] = {
                    'count': 0,
                    'last_message': None
                }
            error_types[error_type]['count'] += 1
            error_types[error_type]['last_message'] = error['message']
        
        return error_types 