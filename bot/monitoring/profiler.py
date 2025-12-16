#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cProfile
import pstats
import io
import time
import psutil
import os
import asyncio
from functools import wraps
from pathlib import Path
from typing import Callable, Any, Optional

from src.logger import setup_logger
logger = setup_logger('profiler', log_file=os.path.join('logs', 'profiler.log'))

class Profiler:
    """Класс для профилирования производительности бота"""
    
    def __init__(self, output_dir: str = "profiles"):
        """
        Инициализация профилировщика
        
        Args:
            output_dir: Директория для сохранения результатов профилирования
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.profiler = cProfile.Profile()
        
    def profile_cpu(self, func: Callable) -> Callable:
        """
        Декоратор для профилирования CPU
        
        Args:
            func: Функция для профилирования
            
        Returns:
            Callable: Обёрнутая функция
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            profile_path = self.output_dir / f"{func.__name__}_cpu_profile.stats"
            
            # Запуск профилировщика
            self.profiler.enable()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
            finally:
                self.profiler.disable()
                
            # Сохранение результатов
            stats = pstats.Stats(self.profiler)
            stats.sort_stats('cumulative')
            stats.dump_stats(str(profile_path))
            
            # Логирование результатов
            s = io.StringIO()
            stats = pstats.Stats(self.profiler, stream=s)
            stats.sort_stats('cumulative')
            stats.print_stats(20)  # Топ 20 функций
            logger.info(f"CPU Profile for {func.__name__}:\n{s.getvalue()}")
            
            return result
            
        return wrapper
        
    def profile_memory(self, func: Callable) -> Callable:
        """
        Декоратор для профилирования памяти
        
        Args:
            func: Функция для профилирования
            
        Returns:
            Callable: Обёрнутая функция
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            process = psutil.Process()
            
            # Замер памяти до выполнения
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Выполнение функции
            start_time = time.time()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
            finally:
                end_time = time.time()
                
                # Замер памяти после выполнения
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                
                # Логирование результатов
                logger.info(
                    f"Memory Profile for {func.__name__}:\n"
                    f"Memory Before: {memory_before:.2f} MB\n"
                    f"Memory After: {memory_after:.2f} MB\n"
                    f"Memory Delta: {memory_after - memory_before:.2f} MB\n"
                    f"Execution Time: {end_time - start_time:.2f} seconds"
                )
            
            return result
            
        return wrapper

# Создание глобального экземпляра профилировщика
profiler = Profiler()

def profile(cpu: bool = True, memory: bool = True) -> Callable:
    """
    Комбинированный декоратор для профилирования CPU и памяти
    
    Args:
        cpu: Включить профилирование CPU
        memory: Включить профилирование памяти
        
    Returns:
        Callable: Декоратор
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            # Для async-функций
            if cpu:
                func = profiler.profile_cpu(func)
            if memory:
                func = profiler.profile_memory(func)
            return func
        else:
            # Для sync-функций
            def sync_wrapper(*args, **kwargs):
                profile_path = profiler.output_dir / f"{func.__name__}_cpu_profile.stats"
                profiler.profiler.enable()
                start_time = time.time()
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                try:
                    result = func(*args, **kwargs)
                finally:
                    profiler.profiler.disable()
                    end_time = time.time()
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    if cpu:
                        stats = pstats.Stats(profiler.profiler)
                        stats.sort_stats('cumulative')
                        stats.dump_stats(str(profile_path))
                        s = io.StringIO()
                        stats = pstats.Stats(profiler.profiler, stream=s)
                        stats.sort_stats('cumulative')
                        stats.print_stats(20)
                        logger.info(f"CPU Profile for {func.__name__}:\n{s.getvalue()}")
                    if memory:
                        logger.info(
                            f"Memory Profile for {func.__name__}:\n"
                            f"Memory Before: {memory_before:.2f} MB\n"
                            f"Memory After: {memory_after:.2f} MB\n"
                            f"Memory Delta: {memory_after - memory_before:.2f} MB\n"
                            f"Execution Time: {end_time - start_time:.2f} seconds"
                        )
                return result
            return sync_wrapper
    return decorator 