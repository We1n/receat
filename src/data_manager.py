"""
Модуль для работы с данными в JSON-формате
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime

logger = logging.getLogger(__name__)

from src.config.config import Config
from src.validators.schemas import RecipeDTO, ValidationErrorResponse
from src.validators.input_handler import InputHandler
from src.search import RecipeSearcher

class DataManager:
    """Класс для управления данными в JSON-формате"""
    
    def __init__(self) -> None:
        """Инициализация менеджера данных"""
        self.data_dir = Path("src/data")
        self.recipes_file = self.data_dir / "recipes.json"
        self.users_file = self.data_dir / "users.json"
        
        # Новая система валидации
        self.input_handler = InputHandler()
        
        # Поисковик
        self.searcher = RecipeSearcher()
        
        # Кэш для данных
        self._cache: Dict[str, Any] = {
            "recipes": None,
            "users": None,
            "last_update": None
        }
        
        # Создаем директорию, если она не существует
        self.data_dir.mkdir(exist_ok=True)
        
        # Инициализируем файлы, если они не существуют
        self._init_files()
        
        # Загружаем данные и строим индексы
        self._load_all_data()
    
    def _init_files(self) -> None:
        """Инициализация JSON-файлов"""
        if not self.recipes_file.exists():
            self._save_json(self.recipes_file, {"recipes": []})
        
        if not self.users_file.exists():
            self._save_json(self.users_file, {"users": {}})
    
    def _load_all_data(self) -> None:
        """Загрузка всех данных и построение индексов"""
        try:
            # Загружаем данные
            self._cache["recipes"] = self._load_json(self.recipes_file)
            self._cache["users"] = self._load_json(self.users_file)
            self._cache["last_update"] = time.time()
            
            logger.info("Данные успешно загружены и индексы построены")
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {e}")
            # В случае ошибки используем пустые структуры
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
    
    def get_recipes(self) -> List[Dict[str, Any]]:
        """Получение списка рецептов"""
        if not self._check_cache("recipes"):
            self._update_cache("recipes")
        
        recipes: List[Dict[str, Any]] = self._cache["recipes"].get("recipes", [])
        
        return recipes
    
    def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Получение рецепта по ID"""
        if not self._check_cache("recipes"):
            self._update_cache("recipes")
        
        recipes: List[Dict[str, Any]] = self._cache["recipes"].get("recipes", [])
        for recipe in recipes:
            if recipe.get("id") == recipe_id:
                return recipe
        return None
    
    def add_recipe(self, recipe: Dict[str, Any]) -> Tuple[bool, Optional[List[Dict[str, str]]]]:
        """
        Добавление нового рецепта
        
        Args:
            recipe: Словарь с данными рецепта
            
        Returns:
            Tuple[bool, Optional[List[Dict[str, str]]]]: (результат операции, список ошибок валидации)
        """
        # Валидируем рецепт через новую систему
        validation_result = self.input_handler.validate_input(
            data=recipe,
            schema_name="RecipeDTO",
            user_message="Ошибка валидации рецепта"
        )
        
        # Проверяем, является ли результат ошибкой валидации
        if isinstance(validation_result, ValidationErrorResponse):
            return False, [validation_result.errors]
        
        recipes = self._cache["recipes"].get("recipes", [])
        
        # Генерация нового ID
        new_id = 1
        if recipes:
            new_id = max(recipe.get("id", 0) for recipe in recipes) + 1
        
        recipe["id"] = new_id
        recipes.append(recipe)
        
        self._cache["recipes"]["recipes"] = recipes
        success = self._save_json(self.recipes_file, self._cache["recipes"])
        
        return success, None
    
    def update_recipe(self, recipe_id: int, updated_recipe: Dict[str, Any]) -> Tuple[bool, Optional[List[Dict[str, str]]]]:
        """
        Обновление существующего рецепта
        
        Args:
            recipe_id: ID рецепта
            updated_recipe: Словарь с обновленными данными рецепта
            
        Returns:
            Tuple[bool, Optional[List[Dict[str, str]]]]: (результат операции, список ошибок валидации)
        """
        # Валидируем рецепт через новую систему
        validation_result = self.input_handler.validate_input(
            data=updated_recipe,
            schema_name="RecipeDTO",
            user_message="Ошибка валидации рецепта"
        )
        
        # Проверяем, является ли результат ошибкой валидации
        if isinstance(validation_result, ValidationErrorResponse):
            return False, [validation_result.errors]
        
        recipes = self._cache["recipes"].get("recipes", [])
        
        for i, recipe in enumerate(recipes):
            if recipe.get("id") == recipe_id:
                # Сохраняем ID
                updated_recipe["id"] = recipe_id
                recipes[i] = updated_recipe
                
                self._cache["recipes"]["recipes"] = recipes
                success = self._save_json(self.recipes_file, self._cache["recipes"])
                
                return success, None
        
        return False, None
    
    def delete_recipe(self, recipe_id: int) -> bool:
        """Удаление рецепта по ID"""
        recipes = self._cache["recipes"].get("recipes", [])
        
        for i, recipe in enumerate(recipes):
            if recipe.get("id") == recipe_id:
                del recipes[i]
                
                self._cache["recipes"]["recipes"] = recipes
                return self._save_json(self.recipes_file, self._cache["recipes"])
        
        return False
    
    def get_random_recipe(self) -> Optional[Dict]:
        """Получение случайного рецепта"""
        import random
        
        recipes = self.get_recipes()
        if not recipes:
            return None
        
        return random.choice(recipes)
    
    def get_available_ingredients(self) -> List[str]:
        """Получение списка доступных ингредиентов"""
        ingredients: List[str] = self._cache["recipes"].get("user_preferences", {}).get("available_ingredients", [])
        return ingredients
    
    def update_available_ingredients(self, ingredients: List[str]) -> bool:
        """Обновление списка доступных ингредиентов"""
        if "user_preferences" not in self._cache["recipes"]:
            self._cache["recipes"]["user_preferences"] = {}
        
        self._cache["recipes"]["user_preferences"]["available_ingredients"] = ingredients
        return self._save_json(self.recipes_file, self._cache["recipes"])
    
    def filter_recipes_by_available_ingredients(self, min_match_percentage: float = 0.7) -> List[Dict]:
        """Фильтрация рецептов по доступным ингредиентам"""
        available = set(self.get_available_ingredients())
        recipes = self.get_recipes()
        filtered_recipes = []
        
        for recipe in recipes:
            ingredients = [ing.get("name") for ing in recipe.get("ingredients", [])]
            if not ingredients:
                continue
            
            # Подсчет совпадающих ингредиентов
            matching = sum(1 for ing in ingredients if ing in available)
            match_percentage = matching / len(ingredients)
            
            if match_percentage >= min_match_percentage:
                filtered_recipe = recipe.copy()
                filtered_recipe["match_percentage"] = match_percentage
                filtered_recipes.append(filtered_recipe)
        
        # Сортировка по проценту совпадения (от большего к меньшему)
        return sorted(filtered_recipes, key=lambda x: x.get("match_percentage", 0), reverse=True)
    
    def calculate_calories_for_portions(self, recipe_id: int, portions: float) -> Optional[float]:
        """Расчет калорий для указанного количества порций"""
        recipe = self.get_recipe_by_id(recipe_id)
        if not recipe:
            return None
        
        calories_per_portion: float = float(recipe.get("calories", 0))
        return calories_per_portion * portions
    
    def adjust_ingredients_for_portions(self, recipe_id: int, portions: float) -> Optional[List[Dict]]:
        """Корректировка количества ингредиентов для указанного числа порций"""
        recipe = self.get_recipe_by_id(recipe_id)
        if not recipe:
            return None
        
        # Предполагаем, что ингредиенты указаны для одной порции
        adjusted_ingredients = []
        for ingredient in recipe.get("ingredients", []):
            adjusted = ingredient.copy()
            adjusted["amount"] = ingredient.get("amount", 0) * portions
            adjusted_ingredients.append(adjusted)
        
        return adjusted_ingredients

    def find_recipes_by_ingredients(self, available_ingredients: List[str]) -> List[Dict[str, Any]]:
        """
        Поиск рецептов по доступным ингредиентам
        
        Args:
            available_ingredients: Список доступных ингредиентов
            
        Returns:
            List[Dict[str, Any]]: Список результатов поиска
        """
        if not self._check_cache("recipes"):
            self._update_cache("recipes")
        
        recipes: List[Dict[str, Any]] = self._cache["recipes"].get("recipes", [])
        results = self.searcher.find_recipes_by_ingredients(recipes, available_ingredients)
        return results
    
    def find_recipes_by_name(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Поиск рецептов по названию
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            List[Dict[str, Any]]: Список результатов поиска
        """
        if not self._check_cache("recipes"):
            self._update_cache("recipes")
        
        recipes: List[Dict[str, Any]] = self._cache["recipes"].get("recipes", [])
        results = self.searcher.find_recipes_by_name(recipes, query, limit)
        return [{"recipe": r[0], "match_percentage": r[1]} for r in results]
    
    def find_recipes_by_difficulty(self, difficulty: str, exact_match: bool = False) -> List[Dict[str, Any]]:
        """
        Поиск рецептов по сложности
        
        Args:
            difficulty: Сложность рецепта (легкий, средний, сложный)
            exact_match: Требовать точное совпадение
            
        Returns:
            List[Dict[str, Any]]: Список результатов поиска
        """
        if not self._check_cache("recipes"):
            self._update_cache("recipes")
        
        recipes: List[Dict[str, Any]] = self._cache["recipes"].get("recipes", [])
        results = self.searcher.find_recipes_by_difficulty(recipes, difficulty, exact_match)
        return [{"recipe": r, "match_percentage": 100.0} for r in results]
    
    def find_recipes_by_cooking_time(
        self,
        max_time: int,
        min_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск рецептов по времени приготовления
        
        Args:
            max_time: Максимальное время приготовления в минутах
            min_time: Минимальное время приготовления в минутах
            
        Returns:
            List[Dict[str, Any]]: Список результатов поиска
        """
        if not self._check_cache("recipes"):
            self._update_cache("recipes")
        
        recipes: List[Dict[str, Any]] = self._cache["recipes"].get("recipes", [])
        results = self.searcher.find_recipes_by_cooking_time(recipes, max_time, min_time)
        return [{"recipe": r, "match_percentage": 100.0} for r in results]
    
    def find_recipes_by_multiple_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Поиск рецептов по нескольким критериям
        
        Args:
            criteria: Словарь с критериями поиска:
                - ingredients: List[str] - список ингредиентов
                - tags: List[str] - список тегов
                - difficulty: str - сложность
                - max_time: int - максимальное время
                - min_time: int - минимальное время
                - name: str - название
                
        Returns:
            List[Dict[str, Any]]: Список результатов поиска
        """
        if not self._check_cache("recipes"):
            self._update_cache("recipes")
        
        recipes: List[Dict[str, Any]] = self._cache["recipes"].get("recipes", [])
        results = self.searcher.find_recipes_by_multiple_criteria(recipes, criteria)
        return [{"recipe": r, "match_percentage": 100.0} for r in results]
