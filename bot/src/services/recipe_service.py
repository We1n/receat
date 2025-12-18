from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging
import json
from pathlib import Path
from src.utils.error_handler import ErrorHandler, NotFoundError, ValidationError
from src.cache import (
    cache_result,
    invalidate_cache,
)
from src.cache.constants import CACHE_KEYS, CACHE_TTL, CACHE_PREFIXES
import shutil
from src.services.price_service import PriceService
from src.exceptions.base import AppError
import asyncio
import uuid

logger = logging.getLogger(__name__)

class RecipeService:
    """
    Сервис для работы с рецептами.
    Теперь self.recipes — словарь с ключами по id (UUID), а не по имени.
    Все методы работают по id.
    При инициализации происходит миграция старых данных (ключи-имена) в ключи-id.
    
    Attributes:
        recipes_file (Path): Путь к файлу с рецептами
        recipes (Dict[str, Dict]): Словарь с рецептами
        price_service (PriceService): Сервис для работы с ценами
    """
    
    def __init__(
        self,
        recipes_file: Union[str, Path] = "data/recipes.json",
        price_service: Optional[PriceService] = None
    ):
        """
        Инициализация сервиса.
        
        Args:
            recipes_file: Путь к файлу с рецептами
            price_service: Сервис для работы с ценами
        """
        self.recipes_file = Path(recipes_file)
        self.recipes: Dict[str, Dict] = self._load_recipes()
        self.price_service = price_service or PriceService()
        self.data_dir = Path("data")
        self.tags_file = self.data_dir / "tags.json"
        
        # Загружаем данные
        self._load_data()
    
    def _load_data(self) -> None:
        """
        Загрузка данных из JSON-файлов
        """
        try:
            # Загружаем теги
            if self.tags_file.exists():
                with open(self.tags_file, "r", encoding="utf-8") as f:
                    self.tags = json.load(f).get("tags", [])
            else:
                self.tags = []
            
            logger.info("✅ Данные успешно загружены")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки данных: {e}")
            self.tags = []
    
    def _load_recipes(self) -> Dict[str, Dict]:
        """
        Загрузка рецептов из файла.
        
        Returns:
            Dict: Словарь с рецептами
        """
        if not self.recipes_file.exists():
            return {}
        try:
            with open(self.recipes_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {}
        except Exception as e:
            logger.error(f"Ошибка загрузки рецептов: {e}")
            return {}
        # Миграция: если ключи — имена, преобразуем в id
        migrated = {}
        for key, recipe in data.items():
            rid = str(recipe.get("id") or uuid.uuid4())
            recipe["id"] = rid
            migrated[rid] = recipe
        # Если были изменения — сохраняем
        if set(migrated.keys()) != set(data.keys()):
            with open(self.recipes_file, "w", encoding="utf-8") as f:
                json.dump(migrated, f, ensure_ascii=False, indent=2)
        return migrated
            
    def _save_recipes(self) -> None:
        """
        Сохранение рецептов в файл.
        """
        with open(self.recipes_file, "w", encoding="utf-8") as f:
            json.dump(self.recipes, f, ensure_ascii=False, indent=2)
            
    def get_recipe(self, recipe_id: str) -> Optional[Dict]:
        """
        Получение рецепта.
        
        Args:
            recipe_id: ID рецепта
            
        Returns:
            Optional[Dict]: Данные рецепта или None, если рецепт не найден
        """
        return self.recipes.get(str(recipe_id))
        
    def get_all_recipes(self) -> List[Dict[str, Any]]:
        """
        Получение всех рецептов.
        
        Returns:
            List[Dict[str, Any]]: Список всех рецептов
        """
        return list(self.recipes.values())
        
    def add_recipe(self, recipe_name: str, recipe_data: Dict) -> None:
        """
        Добавление рецепта.
        
        Args:
            recipe_name: Название рецепта
            recipe_data: Данные рецепта
        """
        recipe_id = str(recipe_data.get("id") or uuid.uuid4())
        recipe_data["id"] = recipe_id
        recipe_data["name"] = recipe_name
        recipe_data["created_at"] = datetime.now().isoformat()
        recipe_data["updated_at"] = recipe_data["created_at"]
        self.recipes[recipe_id] = recipe_data
        self._save_recipes()
        
    def update_recipe(self, recipe_id: str, recipe_data: Dict) -> None:
        """
        Обновление рецепта.
        
        Args:
            recipe_id: ID рецепта
            recipe_data: Новые данные рецепта
        """
        if recipe_id in self.recipes:
            recipe_data["updated_at"] = datetime.now().isoformat()
            self.recipes[recipe_id].update(recipe_data)
            self._save_recipes()
            
    def delete_recipe(self, recipe_id: str) -> bool:
        """
        Удаление рецепта.
        
        Args:
            recipe_id: ID рецепта
            
        Returns:
            bool: True, если рецепт удален, иначе False
        """
        if recipe_id in self.recipes:
            del self.recipes[recipe_id]
            self._save_recipes()
            logger.info(f"✅ Рецепт с id '{recipe_id}' удалён")
            return True
        logger.warning(f"[delete_recipe] Рецепт с id '{recipe_id}' не найден для удаления")
        return False
        
    def search_recipes(self, query: str) -> Dict[str, Dict]:
        """
        Поиск рецептов по части имени или описанию (без учёта регистра)
        Возвращает dict: id -> рецепт
        """
        query = query.strip().lower()
        return {
            rid: data
            for rid, data in self.recipes.items()
            if query in data.get('name', '').lower() or query in data.get('description', '').lower()
        }
        
    def calculate_cost(self, recipe_id: str) -> Optional[float]:
        """
        Расчет стоимости рецепта.
        
        Args:
            recipe_id: ID рецепта
            
        Returns:
            Optional[float]: Стоимость рецепта или None, если рецепт не найден
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return None
            
        total_cost = 0.0
        for ingredient in recipe.get("ingredients", []):
            ingredient_name = ingredient.get("name", "").lower()
            amount = ingredient.get("amount", 0)
            unit = ingredient.get("unit", "")
            
            # Получаем лучшую цену ингредиента (с учетом всех магазинов)
            price_data = self.price_service.get_price(ingredient_name)
            if price_data and price_data.get("price") is not None:
                price = price_data["price"]
                # Конвертируем единицы измерения если нужно
                if unit == "кг" and ingredient.get("unit", "") == "г":
                    amount /= 1000
                elif unit == "л" and ingredient.get("unit", "") == "мл":
                    amount /= 1000
                total_cost += price * amount
                
        return total_cost
        
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['recipes'],
        ttl=CACHE_TTL['recipes'],
        prefix=CACHE_PREFIXES['recipes']
    )
    async def get_recipes(self) -> List[Dict[str, Any]]:
        """
        Получает список всех рецептов
        
        Returns:
            list: Список рецептов
        """
        return list(self.recipes.values())
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['recipe'],
        ttl=CACHE_TTL['recipe'],
        prefix=CACHE_PREFIXES['recipe']
    )
    async def get_recipe_by_name(self, recipe_name: str) -> Optional[Dict[str, Any]]:
        """
        Получение рецепта по названию
        
        Args:
            recipe_name: Название рецепта
            
        Returns:
            Optional[Dict[str, Any]]: Рецепт или None
        """
        return self.get_recipe(recipe_name)
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['search'],
        ttl=CACHE_TTL['search'],
        prefix=CACHE_PREFIXES['search']
    )
    async def search_recipes_by_name(self, query: str) -> Dict[str, Any]:
        """
        Поиск рецептов по названию
        
        Args:
            query: Поисковый запрос
            
        Returns:
            dict: Словарь с найденными рецептами
        """
        return self.search_recipes(query)
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['recipes_by_difficulty'],
        ttl=CACHE_TTL['recipes_by_difficulty'],
        prefix=CACHE_PREFIXES['recipes_by_difficulty']
    )
    async def get_recipes_by_difficulty(self, difficulty: str) -> List[Dict[str, Any]]:
        """
        Получает рецепты по сложности
        
        Args:
            difficulty: Сложность рецепта
            
        Returns:
            list: Список рецептов
        """
        return [recipe for recipe in self.recipes.values() if recipe.get("difficulty") == difficulty]
    
    @ErrorHandler.handle_errors
    @invalidate_cache(
        key_template=CACHE_KEYS['recipes'],
        prefix=CACHE_PREFIXES['recipes']
    )
    async def create_recipe(self, recipe_data: Dict[str, Any]) -> int:
        """
        Создание нового рецепта
        
        Args:
            recipe_data: Данные рецепта
            
        Returns:
            int: ID созданного рецепта
            
        Raises:
            ValidationError: При ошибке валидации
        """
        # Валидация данных
        self._validate_recipe_data(recipe_data)
        
        # Генерируем уникальный ID
        recipe_id = max([r["id"] for r in self.recipes.values()], default=0) + 1
        
        # Создаем рецепт
        recipe = {
            "id": recipe_id,
            "name": recipe_data["name"],
            "ingredients": recipe_data["ingredients"],
            "instructions": recipe_data["instructions"],
            "cooking_time": recipe_data.get("cooking_time", 30),
            "difficulty": recipe_data.get("difficulty", "Средняя"),
            "portions": recipe_data.get("portions", 2),
            "nutrients": recipe_data.get("nutrients", {"calories": 0, "proteins": 0, "fats": 0, "carbs": 0}),
            "tags": recipe_data.get("tags", []),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Добавляем рецепт
        self.recipes[recipe["id"]] = recipe
        
        # Сохраняем данные
        self._save_recipes()
        
        logger.info(f"✅ Создан новый рецепт с ID {recipe_id}")
        
        return recipe_id

    def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить рецепт по ID
        Args:
            recipe_id: ID рецепта (строка или число)
        Returns:
            Optional[Dict[str, Any]]: Рецепт или None если не найден
        """
        return self.recipes.get(str(recipe_id))

    def delete_recipe_by_id(self, recipe_id: str) -> bool:
        """
        Удаляет рецепт по его ID (строка или число).
        Args:
            recipe_id: ID рецепта
        Returns:
            bool: True если успешно удалён, иначе False
        """
        logger.debug(f"[delete_recipe_by_id] Пытаемся удалить по ID: {recipe_id}")
        if recipe_id in self.recipes:
            del self.recipes[recipe_id]
            self._save_recipes()
            logger.info(f"✅ Рецепт с id '{recipe_id}' удалён")
            return True
        logger.warning(f"[delete_recipe_by_id] Рецепт с ID {recipe_id} не найден")
        return False

    def _validate_recipe_data(self, data: Dict[str, Any]) -> None:
        """
        Валидация данных рецепта
        
        Args:
            data: Данные рецепта
            
        Raises:
            ValidationError: При неверных данных
        """
        required_fields = ['name', 'ingredients', 'instructions']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Отсутствует обязательное поле: {field}")
        
        if not isinstance(data['ingredients'], list):
            raise ValidationError("Поле ingredients должно быть списком")
        
        for ingredient in data['ingredients']:
            if not all(k in ingredient for k in ['name', 'amount', 'unit']):
                raise ValidationError("Каждый ингредиент должен содержать name, amount и unit")
