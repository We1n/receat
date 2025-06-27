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

logger = logging.getLogger(__name__)

class RecipeService:
    """
    Сервис для работы с рецептами.
    Обеспечивает полный функционал создания, редактирования, поиска и управления рецептами.
    
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
        self.categories_file = self.data_dir / "categories.json"
        self.tags_file = self.data_dir / "tags.json"
        
        # Загружаем данные
        self._load_data()
    
    def _load_data(self) -> None:
        """
        Загрузка данных из JSON-файлов
        """
        try:
            # Загружаем категории
            if self.categories_file.exists():
                with open(self.categories_file, "r", encoding="utf-8") as f:
                    self.categories = json.load(f).get("categories", [])
            else:
                self.categories = []
            
            # Загружаем теги
            if self.tags_file.exists():
                with open(self.tags_file, "r", encoding="utf-8") as f:
                    self.tags = json.load(f).get("tags", [])
            else:
                self.tags = []
            
            logger.info("✅ Данные успешно загружены")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки данных: {e}")
            self.categories = []
            self.tags = []
    
    def _load_recipes(self) -> Dict:
        """
        Загрузка рецептов из файла.
        
        Returns:
            Dict: Словарь с рецептами
        """
        try:
            if self.recipes_file.exists() and self.recipes_file.stat().st_size > 0:
                with open(self.recipes_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"[Загрузка рецептов] Тип данных: {type(data)}, Размер: {len(data) if isinstance(data, (dict, list)) else 'N/A'}")
                    if isinstance(data, dict) and len(data) > 0:
                        logger.info(f"[Загрузка рецептов] Пример ключа: {list(data.keys())[0]}, Пример рецепта: {list(data.values())[0]}")
                    if isinstance(data, dict):
                        return data
                    else:
                        logger.warning(
                            f"recipes.json содержит данные неверного типа ({type(data)}), ожидался dict. "
                            f"Файл будет проигнорирован, чтобы избежать сбоя."
                        )
                        return {}
            return {}
        except Exception as e:
            logger.error(f"Ошибка при загрузке рецептов: {e}")
            return {}
            
    def _save_recipes(self) -> None:
        """
        Сохранение рецептов в файл.
        """
        try:
            self.recipes_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.recipes_file, "w", encoding="utf-8") as f:
                json.dump(self.recipes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении рецептов: {e}")
            
    def get_recipe(self, recipe_name: str) -> Optional[Dict]:
        """
        Получение рецепта.
        
        Args:
            recipe_name: Название рецепта
            
        Returns:
            Optional[Dict]: Данные рецепта или None, если рецепт не найден
        """
        return self.recipes.get(recipe_name.lower())
        
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
        recipe_name = recipe_name.lower()
        recipe_data["created_at"] = datetime.now().isoformat()
        recipe_data["updated_at"] = recipe_data["created_at"]
        self.recipes[recipe_name] = recipe_data
        self._save_recipes()
        
    def update_recipe(self, recipe_name: str, recipe_data: Dict) -> None:
        """
        Обновление рецепта.
        
        Args:
            recipe_name: Название рецепта
            recipe_data: Новые данные рецепта
        """
        recipe_name = recipe_name.lower()
        if recipe_name in self.recipes:
            recipe_data["updated_at"] = datetime.now().isoformat()
            self.recipes[recipe_name].update(recipe_data)
            self._save_recipes()
            
    def delete_recipe(self, recipe_name: str) -> bool:
        """
        Удаление рецепта.
        
        Args:
            recipe_name: Название рецепта
            
        Returns:
            bool: True, если рецепт удален, иначе False
        """
        logger.debug(f"[delete_recipe] Пытаемся удалить по имени: '{recipe_name}'. Ключи: {list(self.recipes.keys())}")
        if recipe_name and recipe_name.lower() in self.recipes:
            del self.recipes[recipe_name.lower()]
            self._save_recipes()
            logger.info(f"✅ Рецепт '{recipe_name}' удалён")
            return True
        logger.warning(f"[delete_recipe] Рецепт '{recipe_name}' не найден для удаления")
        return False
        
    def search_recipes(self, query: str) -> Dict:
        """
        Поиск рецептов по запросу.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Dict: Словарь с найденными рецептами
        """
        query = query.lower()
        return {
            name: data
            for name, data in self.recipes.items()
            if query in name or query in data.get("description", "").lower()
        }
        
    def calculate_cost(self, recipe_name: str) -> Optional[float]:
        """
        Расчет стоимости рецепта.
        
        Args:
            recipe_name: Название рецепта
            
        Returns:
            Optional[float]: Стоимость рецепта или None, если рецепт не найден
        """
        recipe = self.get_recipe(recipe_name)
        if not recipe:
            return None
            
        total_cost = 0.0
        for ingredient in recipe.get("ingredients", []):
            ingredient_name = ingredient.get("name", "").lower()
            amount = ingredient.get("amount", 0)
            unit = ingredient.get("unit", "")
            
            # Получаем цену ингредиента
            price_data = self.price_service.get_price(ingredient_name)
            if price_data:
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
        key_template=CACHE_KEYS['recipes_by_category'],
        ttl=CACHE_TTL['recipes_by_category'],
        prefix=CACHE_PREFIXES['recipes_by_category']
    )
    async def get_recipes_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """
        Получает рецепты по категории
        
        Args:
            category_id: ID категории
            
        Returns:
            list: Список рецептов
        """
        return [recipe for recipe in self.recipes.values() if recipe["category_id"] == category_id]
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['recipes_by_ingredients'],
        ttl=CACHE_TTL['recipes_by_ingredients'],
        prefix=CACHE_PREFIXES['recipes_by_ingredients']
    )
    async def get_recipes_by_ingredients(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        """
        Получает рецепты по ингредиентам
        
        Args:
            ingredients: Список ингредиентов
            
        Returns:
            list: Список рецептов
        """
        results = []
        ingredients = [i.lower() for i in ingredients]
        
        for recipe in self.recipes.values():
            recipe_ingredients = [i["name"].lower() for i in recipe["ingredients"]]
            if all(i in recipe_ingredients for i in ingredients):
                results.append(recipe)
        
        return results
    
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
            "category": recipe_data.get("category", "общее"),
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
        self.recipes[recipe["name"].lower()] = recipe
        
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
        logger.debug(f"[get_recipe_by_id] Ищем рецепт по ID: {recipe_id}. Все ID: {[r.get('id') for r in self.recipes.values()]}")
        try:
            recipe_id_int = int(recipe_id)
            for recipe in self.recipes.values():
                if recipe.get("id") == recipe_id_int:
                    logger.debug(f"[get_recipe_by_id] Найден рецепт: {recipe}")
                    return recipe
            logger.warning(f"[get_recipe_by_id] Рецепт с ID {recipe_id} не найден")
            return None
        except (ValueError, TypeError):
            logger.error(f"[get_recipe_by_id] Неверный формат ID рецепта: {recipe_id}")
            return None
    
    @ErrorHandler.handle_errors
    async def update_recipe_by_name(self, recipe_name: str, data: Dict[str, Any]) -> bool:
        """
        Обновление рецепта
        
        Args:
            recipe_name: Название рецепта
            data: Данные для обновления
            
        Returns:
            bool: True если успешно
            
        Raises:
            NotFoundError: Если рецепт не найден
            ValidationError: При ошибке валидации
        """
        if recipe_name.lower() in self.recipes:
            # Валидация данных
            self._validate_recipe_data(data)
            
            # Обновляем данные
            self.recipes[recipe_name.lower()].update(data)
            self.recipes[recipe_name.lower()]["updated_at"] = datetime.now().isoformat()
            
            # Сохраняем данные
            self._save_recipes()
            
            logger.info(f"✅ Рецепт {recipe_name.lower()} обновлен")
            
            return True
        else:
            raise NotFoundError(f"❌ Рецепт с названием {recipe_name} не найден")
    
    @ErrorHandler.handle_errors
    async def delete_recipe_by_name_async(self, recipe_name: str) -> bool:
        """
        Асинхронное удаление рецепта по имени (не блокирует event loop)
        Args:
            recipe_name: Название рецепта
        Returns:
            bool: True если успешно, иначе False
        """
        return await asyncio.to_thread(self.delete_recipe, recipe_name)
    
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

    def _favorites_file(self) -> Path:
        """Возвращает путь к файлу избранного"""
        return self.data_dir / "favorites.json"

    def _load_favorites(self) -> dict:
        """Загружает избранное из JSON"""
        path = self._favorites_file()
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки избранного: {e}")
            return {}

    def _save_favorites(self, favorites: dict) -> None:
        """Сохраняет избранное в JSON с резервным копированием"""
        path = self._favorites_file()
        backup_path = self.data_dir / "favorites_backup.json"
        try:
            if path.exists():
                shutil.copy(str(path), str(backup_path))
            with open(path, "w", encoding="utf-8") as f:
                json.dump(favorites, f, ensure_ascii=False, indent=2)
            logger.info("✅ Избранное успешно сохранено")
        except Exception as e:
            logger.error(f"Ошибка сохранения избранного: {e}")

    def get_favorite_recipes(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получить избранные рецепты пользователя
        Args:
            user_id: ID пользователя
        Returns:
            List[Dict[str, Any]]: Список рецептов
        """
        favorites = self._load_favorites()
        recipe_ids = favorites.get(str(user_id), [])
        result = [r for r in self.recipes.values() if r["id"] in recipe_ids]
        logger.info(f"Пользователь {user_id} запросил избранные рецепты: {recipe_ids}")
        return result

    def toggle_favorite(self, recipe_name: str, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Добавить/удалить рецепт из избранного пользователя
        Args:
            recipe_name: Название рецепта
            user_id: ID пользователя
        Returns:
            Optional[Dict[str, Any]]: Рецепт, если добавлен, иначе None
        """
        favorites = self._load_favorites()
        user_key = str(user_id)
        recipe = self.get_recipe(recipe_name)
        if not recipe:
            logger.warning(f"Рецепт {recipe_name} не найден для избранного пользователя {user_id}")
            return None
        user_favs = set(favorites.get(user_key, []))
        if recipe["id"] in user_favs:
            user_favs.remove(recipe["id"])
            logger.info(f"Рецепт {recipe_name} удалён из избранного пользователя {user_id}")
            result = None
        else:
            user_favs.add(recipe["id"])
            logger.info(f"Рецепт {recipe_name} добавлен в избранное пользователя {user_id}")
            result = recipe
        favorites[user_key] = list(user_favs)
        self._save_favorites(favorites)
        return result
    
    def create_category(self, category_data: dict) -> Dict[str, Any]:
        """
        Создать новую категорию
        Args:
            category_data: dict с полями name, description и др.
        Returns:
            Dict[str, Any]: созданная категория
        """
        try:
            # Генерируем уникальный ID
            category_id = max([c["id"] for c in self.categories], default=0) + 1
            category = {
                "id": category_id,
                "name": category_data.get("name", f"Категория {category_id}"),
                "description": category_data.get("description", "")
            }
            # Добавляем дополнительные поля, если есть
            for k, v in category_data.items():
                if k not in category:
                    category[k] = v
            self.categories.append(category)
            # Сохраняем с резервным копированием
            backup_path = self.data_dir / "categories_backup.json"
            if self.categories_file.exists():
                shutil.copy(str(self.categories_file), str(backup_path))
            with open(self.categories_file, "w", encoding="utf-8") as f:
                json.dump({"categories": self.categories, "last_update": datetime.now().isoformat()}, f, ensure_ascii=False, indent=4)
            logger.info(f"✅ Категория создана: {category}")
            return category
        except Exception as e:
            logger.error(f"❌ Ошибка создания категории: {e}")
            raise
    
    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['recipe_servings'],
        ttl=CACHE_TTL['recipe_servings'],
        prefix=CACHE_PREFIXES['recipe_servings']
    )
    async def calculate_servings(self, recipe_name: str, target_servings: int) -> Dict[str, Any]:
        """
        Расчет ингредиентов для заданного количества порций
        
        Args:
            recipe_name: Название рецепта
            target_servings: Целевое количество порций
            
        Returns:
            dict: Рецепт с пересчитанными ингредиентами
            
        Raises:
            NotFoundError: Если рецепт не найден
            ValidationError: При неверном количестве порций
        """
        recipe = self.get_recipe(recipe_name)
        if not recipe:
            raise NotFoundError(f"❌ Рецепт с названием {recipe_name} не найден")
        
        if target_servings <= 0:
            raise ValidationError("❌ Количество порций должно быть положительным числом")
        
        # Рассчитываем коэффициент
        original_servings = recipe.get("servings", 1)
        factor = target_servings / original_servings
        
        # Создаем копию рецепта
        adjusted_recipe = recipe.copy()
        
        # Пересчитываем ингредиенты
        adjusted_recipe["ingredients"] = [
            {
                **ingredient,
                "amount": round(ingredient["amount"] * factor, 2)
            }
            for ingredient in recipe["ingredients"]
        ]
        
        # Обновляем количество порций
        adjusted_recipe["servings"] = target_servings
        
        return adjusted_recipe

    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['recipe_time'],
        ttl=CACHE_TTL['recipe_time'],
        prefix=CACHE_PREFIXES['recipe_time']
    )
    async def calculate_cooking_time(self, recipe_name: str) -> Dict[str, Any]:
        """
        Расчет времени приготовления рецепта
        
        Args:
            recipe_name: Название рецепта
            
        Returns:
            dict: Информация о времени приготовления
            
        Raises:
            NotFoundError: Если рецепт не найден
        """
        recipe = self.get_recipe(recipe_name)
        if not recipe:
            raise NotFoundError(f"❌ Рецепт с названием {recipe_name} не найден")
        
        # Базовое время на подготовку ингредиентов (2 минуты на ингредиент)
        prep_time = len(recipe["ingredients"]) * 2
        
        # Время на каждый шаг приготовления (в среднем 5 минут)
        cooking_time = len(recipe["instructions"].split("\n")) * 5
        
        # Общее время
        total_time = prep_time + cooking_time
        
        return {
            "prep_time": prep_time,
            "cooking_time": cooking_time,
            "total_time": total_time,
            "formatted_time": f"{total_time // 60}ч {total_time % 60}м"
        }

    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['recipes_by_calories'],
        ttl=CACHE_TTL['recipes_by_calories'],
        prefix=CACHE_PREFIXES['recipes_by_calories']
    )
    async def get_recipes_by_calories(self, min_calories: Optional[float] = None, max_calories: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Получает рецепты по калорийности
        
        Args:
            min_calories: Минимальная калорийность
            max_calories: Максимальная калорийность
            
        Returns:
            list: Список рецептов
        """
        filtered_recipes = []
        
        for recipe in self.recipes.values():
            try:
                calories = recipe.get("calories", 0)
                
                if min_calories is not None and calories < min_calories:
                    continue
                if max_calories is not None and calories > max_calories:
                    continue
                    
                filtered_recipes.append(recipe)
            except Exception as e:
                logger.error(f"❌ Ошибка расчета калорий для рецепта {recipe['id']}: {e}")
                continue
        
        return filtered_recipes

    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['recipes_by_macros'],
        ttl=CACHE_TTL['recipes_by_macros'],
        prefix=CACHE_PREFIXES['recipes_by_macros']
    )
    async def get_recipes_by_macros(
        self,
        min_proteins: Optional[float] = None,
        max_proteins: Optional[float] = None,
        min_fats: Optional[float] = None,
        max_fats: Optional[float] = None,
        min_carbs: Optional[float] = None,
        max_carbs: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Получает рецепты по БЖУ
        
        Args:
            min_proteins: Минимальное количество белков
            max_proteins: Максимальное количество белков
            min_fats: Минимальное количество жиров
            max_fats: Максимальное количество жиров
            min_carbs: Минимальное количество углеводов
            max_carbs: Максимальное количество углеводов
            
        Returns:
            list: Список рецептов
        """
        filtered_recipes = []
        
        for recipe in self.recipes.values():
            try:
                nutrients = recipe.get("nutrients", {})
                
                # Проверяем белки
                proteins = nutrients.get("proteins", 0)
                if min_proteins is not None and proteins < min_proteins:
                    continue
                if max_proteins is not None and proteins > max_proteins:
                    continue
                
                # Проверяем жиры
                fats = nutrients.get("fats", 0)
                if min_fats is not None and fats < min_fats:
                    continue
                if max_fats is not None and fats > max_fats:
                    continue
                
                # Проверяем углеводы
                carbs = nutrients.get("carbs", 0)
                if min_carbs is not None and carbs < min_carbs:
                    continue
                if max_carbs is not None and carbs > max_carbs:
                    continue
                
                filtered_recipes.append(recipe)
            except Exception as e:
                logger.error(f"❌ Ошибка расчета БЖУ для рецепта {recipe['id']}: {e}")
                continue
        
        return filtered_recipes

    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['recipe_substitutes'],
        ttl=CACHE_TTL['recipe_substitutes'],
        prefix=CACHE_PREFIXES['recipe_substitutes']
    )
    async def get_ingredient_substitutes(self, ingredient_name: str) -> List[Dict[str, Any]]:
        """
        Получает список возможных замен для ингредиента
        Args:
            ingredient_name: Название ингредиента
        Returns:
            list: Список возможных замен
        """
        try:
            substitutes_path = self.data_dir / "substitutes.json"
            if not substitutes_path.exists():
                logger.warning(f"Файл заменителей не найден: {substitutes_path}")
                return []
            with open(substitutes_path, "r", encoding="utf-8") as f:
                substitutes_db = json.load(f)
            return substitutes_db.get(ingredient_name.lower(), [])
        except Exception as e:
            logger.error(f"Ошибка при загрузке заменителей: {e}")
            return []

    @ErrorHandler.handle_errors
    @cache_result(
        key_template=CACHE_KEYS['recipe_with_substitutes'],
        ttl=CACHE_TTL['recipe_with_substitutes'],
        prefix=CACHE_PREFIXES['recipe_with_substitutes']
    )
    async def get_recipe_with_substitutes(self, recipe_name: str, substitutions: Dict[str, str]) -> Dict[str, Any]:
        """
        Получает рецепт с замененными ингредиентами
        
        Args:
            recipe_name: Название рецепта
            substitutions: Словарь замен (старый ингредиент -> новый ингредиент)
            
        Returns:
            dict: Рецепт с замененными ингредиентами
            
        Raises:
            NotFoundError: Если рецепт не найден
        """
        recipe = self.get_recipe(recipe_name)
        if not recipe:
            raise NotFoundError(f"❌ Рецепт с названием {recipe_name} не найден")
        
        # Создаем копию рецепта
        modified_recipe = recipe.copy()
        
        # Заменяем ингредиенты
        for ingredient in modified_recipe["ingredients"]:
            old_name = ingredient["name"].lower()
            if old_name in substitutions:
                new_name = substitutions[old_name]
                substitutes = await self.get_ingredient_substitutes(old_name)
                
                # Ищем информацию о замене
                substitute_info = next((s for s in substitutes if s["name"].lower() == new_name.lower()), None)
                if substitute_info:
                    ingredient["name"] = new_name
                    ingredient["amount"] = round(ingredient["amount"] * substitute_info["ratio"], 2)
                    ingredient["notes"] = substitute_info.get("notes", "")
        
        return modified_recipe

    def delete_recipe_by_id(self, recipe_id: str) -> bool:
        """
        Удаляет рецепт по его ID (строка или число).
        Args:
            recipe_id: ID рецепта
        Returns:
            bool: True если успешно удалён, иначе False
        """
        logger.debug(f"[delete_recipe_by_id] Пытаемся удалить по ID: {recipe_id}")
        recipe = self.get_recipe_by_id(recipe_id)
        if not recipe:
            logger.warning(f"[delete_recipe_by_id] Рецепт с ID {recipe_id} не найден")
            return False
        recipe_name = recipe.get('name')
        if not recipe_name:
            logger.warning(f"[delete_recipe_by_id] У рецепта с ID {recipe_id} нет имени")
            return False
        return self.delete_recipe(recipe_name)

    # Удаляем дублирующиеся асинхронные методы, так как уже есть синхронные версии
