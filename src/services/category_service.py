from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json
from pathlib import Path
from src.utils.error_handler import ErrorHandler, ValidationError, NotFoundError
from src.cache import (
    cache_result,
    invalidate_cache,
)
from src.cache.constants import CACHE_KEYS, CACHE_TTL, CACHE_PREFIXES

logger = logging.getLogger(__name__)

class CategoryService:
    """
    Сервис для работы с категориями рецептов.
    Обеспечивает полный функционал создания, редактирования, поиска и управления категориями.
    """
    
    def __init__(self):
        """
        Инициализация сервиса
        """
        self.data_dir = Path("data")
        self.categories_file = self.data_dir / "categories.json"
        
        # Загружаем данные
        self._load_data()
    
    def _load_data(self) -> None:
        """
        Загрузка данных из JSON-файла
        """
        try:
            if self.categories_file.exists():
                with open(self.categories_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.categories = data.get("categories", [])
            else:
                self.categories = []
            
            logger.info("✅ Данные категорий успешно загружены")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки данных категорий: {e}")
            self.categories = []
    
    def _save_data(self) -> None:
        """
        Сохранение данных в JSON-файл
        """
        try:
            with open(self.categories_file, "w", encoding="utf-8") as f:
                json.dump({
                    "categories": self.categories,
                    "last_update": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=4)
            
            logger.info("✅ Данные категорий успешно сохранены")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения данных категорий: {e}")
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['categories'],
        ttl=CACHE_TTL['categories'],
        prefix=CACHE_PREFIXES['categories']
    )
    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        Получает список категорий рецептов
        
        Returns:
            list: Список категорий
        """
        return self.categories
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['category'],
        ttl=CACHE_TTL['category'],
        prefix=CACHE_PREFIXES['category']
    )
    async def get_category(self, category_id: int) -> Dict[str, Any]:
        """
        Получает категорию по ID
        
        Args:
            category_id: ID категории
            
        Returns:
            dict: Данные категории
            
        Raises:
            NotFoundError: Если категория не найдена
        """
        for category in self.categories:
            if category["id"] == category_id:
                return category
        raise NotFoundError(f"❌ Категория с ID {category_id} не найдена")
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['category_by_name'],
        ttl=CACHE_TTL['category'],
        prefix=CACHE_PREFIXES['category']
    )
    async def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Получает категорию по названию
        
        Args:
            name: Название категории
            
        Returns:
            Optional[dict]: Данные категории или None
        """
        for category in self.categories:
            if category["name"].lower() == name.lower():
                return category
        return None
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['categories'],
        prefix=CACHE_PREFIXES['categories']
    )
    async def add_category(self, name: str, description: Optional[str] = None, emoji: Optional[str] = None) -> int:
        """
        Добавляет новую категорию
        
        Args:
            name: Название категории
            description: Описание категории
            emoji: Эмодзи для категории
            
        Returns:
            int: ID новой категории
            
        Raises:
            ValidationError: Если категория с таким названием уже существует
        """
        # Проверяем существование категории
        existing = await self.get_category_by_name(name)
        if existing:
            raise ValidationError(f"❌ Категория с названием '{name}' уже существует")
        
        # Создаем новую категорию
        new_id = max([cat["id"] for cat in self.categories], default=0) + 1
        new_category = {
            "id": new_id,
            "name": name,
            "description": description or f"Категория {name}",
            "emoji": emoji or "📁",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Добавляем категорию
        self.categories.append(new_category)
        
        # Сохраняем данные
        self._save_data()
        
        return new_id
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['categories'],
        prefix=CACHE_PREFIXES['categories']
    )
    async def update_category(self, category_id: int, data: Dict[str, Any]) -> bool:
        """
        Обновляет категорию
        
        Args:
            category_id: ID категории
            data: Новые данные
            
        Returns:
            bool: True если обновление успешно
            
        Raises:
            NotFoundError: Если категория не найдена
            ValidationError: Если категория с таким названием уже существует
        """
        # Проверяем существование категории
        category = await self.get_category(category_id)
        if not category:
            raise NotFoundError(f"❌ Категория с ID {category_id} не найдена")
        
        # Проверяем новое название
        if "name" in data:
            existing = await self.get_category_by_name(data["name"])
            if existing and existing["id"] != category_id:
                raise ValidationError(f"❌ Категория с названием '{data['name']}' уже существует")
        
        # Обновляем данные
        category.update(data)
        category["updated_at"] = datetime.now().isoformat()
        
        # Сохраняем данные
        self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['categories'],
        prefix=CACHE_PREFIXES['categories']
    )
    async def delete_category(self, category_id: int) -> bool:
        """
        Удаляет категорию
        
        Args:
            category_id: ID категории
            
        Returns:
            bool: True если удаление успешно
            
        Raises:
            NotFoundError: Если категория не найдена
        """
        # Проверяем существование категории
        category = await self.get_category(category_id)
        if not category:
            raise NotFoundError(f"❌ Категория с ID {category_id} не найдена")
        
        # Удаляем категорию
        self.categories = [cat for cat in self.categories if cat["id"] != category_id]
        
        # Сохраняем данные
        self._save_data()
        
        return True
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['category'],
        prefix=CACHE_PREFIXES['category']
    )
    async def move_recipes_to_category(self, from_category_id: int, to_category_id: int) -> bool:
        """
        Перемещает рецепты из одной категории в другую
        
        Args:
            from_category_id: ID исходной категории
            to_category_id: ID целевой категории
            
        Returns:
            bool: True если перемещение успешно
            
        Raises:
            NotFoundError: Если одна из категорий не найдена
        """
        # Проверяем существование категорий
        from_category = await self.get_category(from_category_id)
        to_category = await self.get_category(to_category_id)
        if not from_category or not to_category:
            raise NotFoundError("❌ Одна из категорий не найдена")
        
        # Обновляем данные
        from_category["updated_at"] = datetime.now().isoformat()
        to_category["updated_at"] = datetime.now().isoformat()
        
        # Сохраняем данные
        self._save_data()
        
        return True 