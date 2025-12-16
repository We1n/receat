"""
Модуль для работы с JSON-данными
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class JSONManager:
    """Класс для управления данными в JSON-формате"""
    
    def __init__(self) -> None:
        """Инициализация менеджера JSON-данных"""
        self.data_dir = Path("data")
        self.recipes_file = self.data_dir / "recipes.json"
        self.users_file = self.data_dir / "user_states.json"
        # Кэш для данных
        self._cache: Dict[str, Any] = {
            "recipes": None,
            "users": None,
            "last_update": None
        }
        self.data_dir.mkdir(exist_ok=True)
        self._init_files()
        self._load_all_data()
    
    def _init_files(self) -> None:
        """Инициализация JSON-файлов"""
        if not self.recipes_file.exists():
            self._save_json(self.recipes_file, {"recipes": []})
        if not self.users_file.exists():
            self._save_json(self.users_file, {"users": {}})
    
    def _load_all_data(self) -> None:
        """Загрузка всех данных"""
        try:
            self._cache["recipes"] = self._load_json(self.recipes_file)
            self._cache["users"] = self._load_json(self.users_file)
            self._cache["last_update"] = time.time()
            logger.info("Данные успешно загружены")
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {e}")
            self._cache["recipes"] = {"recipes": []}
            self._cache["users"] = {"users": {}}
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Загрузка данных из JSON-файла"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
                return data
        except Exception as e:
            logger.error(f"Ошибка загрузки данных из {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: Path, data: Dict) -> bool:
        """Сохранение данных в JSON-файл"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения данных в {file_path}: {e}")
            return False
    
    def _check_cache(self, cache_key: str, max_age: int = 300) -> bool:
        """
        Проверка актуальности кэша
        
        Args:
            cache_key: Ключ кэша
            max_age: Максимальный возраст кэша в секундах (по умолчанию 5 минут)
            
        Returns:
            bool: True если кэш актуален, False если нужно обновить
        """
        if self._cache[cache_key] is None:
            return False
        
        if self._cache["last_update"] is None:
            return False
        
        current_time: float = time.time()
        last_update: float = self._cache["last_update"]
        return current_time - last_update <= max_age
    
    def _update_cache(self, cache_key: str) -> None:
        """
        Обновление кэша
        
        Args:
            cache_key: Ключ кэша для обновления
        """
        try:
            if cache_key == "recipes":
                self._cache["recipes"] = self._load_json(self.recipes_file)
            elif cache_key == "users":
                self._cache["users"] = self._load_json(self.users_file)
            
            self._cache["last_update"] = time.time()
            
            logger.info(f"Кэш {cache_key} успешно обновлен")
        except Exception as e:
            logger.error(f"Ошибка при обновлении кэша {cache_key}: {e}")
    
    # Удалены все методы для работы со списками покупок 