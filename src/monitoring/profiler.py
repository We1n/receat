"""
Универсальный профилировщик для мониторинга производительности

Этот модуль предоставляет функционал для:
- Профилирования кода
- Мониторинга производительности
- Анализа использования ресурсов
- Оптимизации производительности
"""

import cProfile
import pstats
import io
import logging
import time
import functools
import os
from datetime import datetime
from typing import Callable, Any, Optional, Dict, List
import psutil
import line_profiler
import memory_profiler
from .performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

class Profiler:
    """Класс для профилирования кода"""
    
    def __init__(self, output_dir: str = "profiles", metrics: Any = None):
        """
        Инициализация профилировщика
        
        Args:
            output_dir: Директория для сохранения результатов профилирования
            metrics: Объект для интеграции с системой метрик
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.profiler = cProfile.Profile()
        self.stats = {}
        self.line_profiler = line_profiler.LineProfiler()
        self.metrics = metrics
        self.monitor = PerformanceMonitor()
        logger.info("Инициализирован универсальный профилировщик")
        
    def profile_recipe_search(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Профилирование поиска рецептов
        
        Args:
            query: Поисковый запрос
            filters: Фильтры поиска
            
        Returns:
            Результаты профилирования
        """
        @self.profile
        def search():
            # Здесь будет код поиска рецептов
            raise NotImplementedError("Профилирование поиска рецептов не реализовано")
            
        return search()
        
    def profile_ingredient_search(self, query: str) -> Dict[str, Any]:
        """
        Профилирование поиска ингредиентов
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Результаты профилирования
        """
        @self.profile
        def search():
            # Здесь будет код поиска ингредиентов
            raise NotImplementedError("Профилирование поиска ингредиентов не реализовано")
            
        return search()
        
    # def profile_shopping_list(self, user_id: int) -> Dict[str, Any]:
    #     """УДАЛЕНО: функционал не будет реализован"""
    #     return {}
        
    def profile_nutrient_calculation(self, ingredients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Профилирование расчета нутриентов
        
        Args:
            ingredients: Список ингредиентов
            
        Returns:
            Результаты профилирования
        """
        @self.profile
        def calculate():
            # Здесь будет код расчета нутриентов
            raise NotImplementedError("Профилирование расчёта нутриентов не реализовано")
            
        return calculate()

    def profile(self, func: Callable = None, *, save_to_file: bool = False) -> Callable:
        """
        Декоратор для профилирования функции с поддержкой опционального аргумента save_to_file
        """
        def decorator(inner_func):
            @functools.wraps(inner_func)
            def wrapper(*args, **kwargs):
                self.profiler.enable()
                start_time = time.time()
                try:
                    result = inner_func(*args, **kwargs)
                    return result
                except Exception as e:
                    # Сохраняем ошибку в статистике
                    if inner_func.__name__ not in self.stats:
                        self.stats[inner_func.__name__] = {'calls': 0}
                    self.stats[inner_func.__name__]['error'] = str(e)
                    raise
                finally:
                    self.profiler.disable()
                    end_time = time.time()
                    stats = pstats.Stats(self.profiler)
                    stats.sort_stats('cumulative')
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{inner_func.__name__}_{timestamp}.prof"
                    filepath = os.path.join(self.output_dir, filename)
                    if save_to_file:
                        stats.dump_stats(filepath)
                    # Сохраняем метрики
                    if inner_func.__name__ not in self.stats:
                        self.stats[inner_func.__name__] = {
                            'calls': 0
                        }
                    self.stats[inner_func.__name__]['calls'] = self.stats[inner_func.__name__].get('calls', 0) + 1
                    self.stats[inner_func.__name__].update({
                        'execution_time': end_time - start_time,
                        'profile_file': filepath if save_to_file else None,
                        'timestamp': timestamp
                    })
                    # Интеграция с системой метрик
                    if hasattr(self, 'metrics') and self.metrics is not None:
                        metric_name = f"{inner_func.__name__}_execution_time"
                        self.metrics.record_metric(metric_name, end_time - start_time)
                    logger.info(f"Профилирование {inner_func.__name__} завершено. Результаты сохранены в {filepath}")
            return wrapper
        if func is None:
            return decorator
        else:
            return decorator(func)

    def profile_line(self, func: Callable = None, *, show_memory: bool = False) -> Callable:
        """
        Декоратор для построчного профилирования с поддержкой опционального аргумента show_memory
        """
        def decorator(inner_func):
            @functools.wraps(inner_func)
            def wrapper(*args, **kwargs):
                wrapped = self.line_profiler(inner_func)
                result = wrapped(*args, **kwargs)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{inner_func.__name__}_line_{timestamp}.prof"
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'w') as f:
                    self.line_profiler.print_stats(stream=f)
                logger.info(f"Построчное профилирование {inner_func.__name__} завершено. Результаты сохранены в {filepath}")
                return result
            return wrapper
        if func is None:
            return decorator
        else:
            return decorator(func)

    def profile_memory(self, func: Callable) -> Callable:
        """
        Декоратор для профилирования использования памяти
        
        Args:
            func: Функция для профилирования
            
        Returns:
            Декорированная функция
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Измеряем память до и после выполнения функции
            mem_usage_before = memory_profiler.memory_usage(-1, interval=0.01, timeout=1)
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            mem_usage_after = memory_profiler.memory_usage(-1, interval=0.01, timeout=1)
            peak_memory = max(mem_usage_after) - min(mem_usage_before)
            
            # Сохраняем результаты
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{func.__name__}_memory_{timestamp}.txt"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w') as f:
                f.write(f"Memory usage before: {mem_usage_before}\n")
                f.write(f"Memory usage after: {mem_usage_after}\n")
                f.write(f"Peak memory usage: {peak_memory} MiB\n")
                f.write(f"Execution time: {end_time - start_time} sec\n")
            
            # Сохраняем в self.stats
            self.stats[f"{func.__name__}_memory"] = {
                'peak_memory': peak_memory,
                'memory_before': mem_usage_before,
                'memory_after': mem_usage_after,
                'execution_time': end_time - start_time,
                'profile_file': filepath,
                'timestamp': timestamp
            }
            logger.info(f"Профилирование памяти {func.__name__} завершено. Результаты сохранены в {filepath}")
            return result
        return wrapper

    def get_stats(self) -> dict:
        """
        Получение статистики профилирования
        
        Returns:
            Словарь со статистикой
        """
        return self.stats
    
    def analyze_profile(self, profile_file: str) -> dict:
        """
        Анализ результатов профилирования
        
        Args:
            profile_file: Путь к файлу с результатами профилирования
            
        Returns:
            Словарь с результатами анализа
        """
        stats = pstats.Stats(profile_file)
        
        # Получаем статистику
        stream = io.StringIO()
        stats.stream = stream
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Топ-20 самых затратных операций
        
        return {
            'top_operations': stream.getvalue(),
            'total_calls': stats.total_calls,
            'total_time': stats.total_tt
        }

    def get_memory_stats(self) -> dict:
        """
        Получение статистики использования памяти
        
        Returns:
            Словарь со статистикой
        """
        return {k: v for k, v in self.stats.items() if k.endswith('_memory')}

    def clear_stats(self):
        """Очистка статистики"""
        self.stats.clear()
        self.profiler = cProfile.Profile()
        self.line_profiler = line_profiler.LineProfiler()

    def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """
        Получение рекомендаций по оптимизации производительности
        
        Returns:
            Список рекомендаций
        """
        recommendations = []
        
        # Анализируем статистику
        for func_name, stats in self.stats.items():
            if 'execution_time' in stats:
                # Проверяем время выполнения
                if stats['execution_time'] > 1.0:  # Более 1 секунды
                    recommendations.append({
                        'type': 'execution_time',
                        'function': func_name,
                        'value': stats['execution_time'],
                        'recommendation': f'Функция {func_name} выполняется слишком долго. Рекомендуется оптимизировать.'
                    })
                
                # Проверяем использование памяти
                if func_name.endswith('_memory'):
                    memory_used = stats.get('memory_used', 0)
                    if memory_used > 100 * 1024 * 1024:  # Более 100 MB
                        recommendations.append({
                            'type': 'memory_usage',
                            'function': func_name,
                            'value': memory_used,
                            'recommendation': f'Функция {func_name} использует слишком много памяти. Рекомендуется оптимизировать.'
                        })
        
        return recommendations

    def get_line_stats(self) -> dict:
        """
        Получение статистики построчного профилирования
        
        Returns:
            Словарь с результатами построчного профилирования
        """
        stream = io.StringIO()
        self.line_profiler.print_stats(stream=stream)
        return {'line_profile_report': stream.getvalue()}

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Получение отчета о производительности
        
        Returns:
            Отчет о производительности
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'profiler_stats': self.get_stats(),
            'memory_stats': self.get_memory_stats(),
            'performance_stats': self.monitor.get_performance_stats(),
            'recommendations': self.get_performance_recommendations()
        } 