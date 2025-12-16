"""
Модуль для улучшенного поиска рецептов
"""

from typing import List, Dict, Any, Tuple, Set, Optional
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class RecipeSearcher:
    """Класс для улучшенного поиска рецептов"""
    
    def __init__(self, min_similarity: int = 80) -> None:
        """
        Инициализация поисковика
        
        Args:
            min_similarity: Минимальный порог схожести (0-100)
        """
        self.min_similarity = min_similarity
    
    def find_similar_ingredients(self, ingredient: str, available_ingredients: List[str]) -> List[Tuple[str, int]]:
        """
        Поиск похожих ингредиентов
        
        Args:
            ingredient: Искомый ингредиент
            available_ingredients: Список доступных ингредиентов
            
        Returns:
            List[Tuple[str, int]]: Список кортежей (ингредиент, схожесть)
        """
        # Используем process.extract для поиска похожих строк
        matches = process.extract(
            ingredient.lower(),
            [i.lower() for i in available_ingredients],
            scorer=fuzz.token_sort_ratio,
            limit=3
        )
        
        # Фильтруем результаты по минимальной схожести
        return [(match[0], match[1]) for match in matches if match[1] >= self.min_similarity]
    
    def find_recipes_by_ingredients(
        self,
        recipes: List[Dict[str, Any]],
        available_ingredients: List[str],
        min_match_percentage: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Поиск рецептов по доступным ингредиентам с учетом нечеткого сравнения
        
        Args:
            recipes: Список рецептов
            available_ingredients: Список доступных ингредиентов
            min_match_percentage: Минимальный процент совпадения ингредиентов
            
        Returns:
            List[Dict]: Список рецептов с информацией о совпадениях
        """
        result: List[Dict[str, Any]] = []
        
        for recipe in recipes:
            recipe_ingredients = recipe.get("ingredients", [])
            if not recipe_ingredients:
                continue
            
            # Собираем все ингредиенты рецепта
            recipe_ingredient_names = [ing.get("name", "").lower() for ing in recipe_ingredients]
            
            # Счетчики для подсчета совпадений
            exact_matches: Set[str] = set()
            fuzzy_matches: Set[str] = set()
            missing_ingredients: List[Dict[str, Any]] = []
            
            # Проверяем каждый ингредиент рецепта
            for ingredient_dict in recipe_ingredients:
                ingredient_name = ingredient_dict.get("name", "").lower()
                
                # Проверяем точное совпадение
                if ingredient_name in [i.lower() for i in available_ingredients]:
                    exact_matches.add(ingredient_name)
                    continue
                
                # Ищем похожие ингредиенты
                similar_ingredients = self.find_similar_ingredients(ingredient_name, available_ingredients)
                if similar_ingredients:
                    fuzzy_matches.add(ingredient_name)
                    continue
                
                # Если нет совпадений, добавляем в список недостающих
                missing_ingredients.append(ingredient_dict)
            
            # Вычисляем процент совпадения
            total_ingredients = len(recipe_ingredients)
            match_percentage = (len(exact_matches) + len(fuzzy_matches)) / total_ingredients
            
            # Добавляем рецепт в результат, если процент совпадения достаточный
            if match_percentage >= min_match_percentage:
                result.append({
                    "recipe": recipe,
                    "exact_matches": list(exact_matches),
                    "fuzzy_matches": list(fuzzy_matches),
                    "missing_ingredients": missing_ingredients,
                    "match_percentage": match_percentage * 100
                })
        
        # Сортируем результаты по проценту совпадения
        result.sort(key=lambda x: x["match_percentage"], reverse=True)
        return result
    
    def find_recipes_by_name(
        self,
        recipes: List[Dict[str, Any]],
        query: str,
        limit: int = 5
    ) -> List[Tuple[Dict[str, Any], int]]:
        """
        Поиск рецептов по названию с учетом нечеткого сравнения
        
        Args:
            recipes: Список рецептов
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            List[Tuple[Dict, int]]: Список кортежей (рецепт, схожесть)
        """
        # Получаем названия рецептов
        recipe_names = [recipe.get("name", "") for recipe in recipes]
        
        # Ищем похожие названия
        matches = process.extract(
            query.lower(),
            [name.lower() for name in recipe_names],
            scorer=fuzz.token_sort_ratio,
            limit=limit
        )
        
        # Формируем результат
        result = []
        for match in matches:
            if match[1] >= self.min_similarity:
                recipe_index = recipe_names.index(match[0])
                result.append((recipes[recipe_index], match[1]))
        
        return result
    
    def find_recipes_by_difficulty(
        self,
        recipes: List[Dict[str, Any]],
        difficulty: str,
        exact_match: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Поиск рецептов по сложности
        
        Args:
            recipes: Список рецептов
            difficulty: Сложность рецепта (легкий, средний, сложный)
            exact_match: Требовать точное совпадение
            
        Returns:
            List[Dict]: Список рецептов
        """
        result: List[Dict[str, Any]] = []
        difficulty = difficulty.lower()
        
        for recipe in recipes:
            recipe_difficulty = recipe.get("difficulty", "").lower()
            
            if exact_match:
                if recipe_difficulty == difficulty:
                    result.append(recipe)
            else:
                # Используем нечеткое сравнение для сложности
                similarity = fuzz.ratio(recipe_difficulty, difficulty)
                if similarity >= self.min_similarity:
                    result.append(recipe)
        
        return result
    
    def find_recipes_by_cooking_time(
        self,
        recipes: List[Dict[str, Any]],
        max_time: int,
        min_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск рецептов по времени приготовления
        
        Args:
            recipes: Список рецептов
            max_time: Максимальное время приготовления в минутах
            min_time: Минимальное время приготовления в минутах
            
        Returns:
            List[Dict]: Список рецептов
        """
        result: List[Dict[str, Any]] = []
        
        for recipe in recipes:
            cooking_time = recipe.get("cooking_time", 0)
            
            if min_time is not None:
                if min_time <= cooking_time <= max_time:
                    result.append(recipe)
            else:
                if cooking_time <= max_time:
                    result.append(recipe)
        
        return result
    
    def find_recipes_by_multiple_criteria(
        self,
        recipes: List[Dict[str, Any]],
        criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Поиск рецептов по нескольким критериям
        
        Args:
            recipes: Список рецептов
            criteria: Словарь с критериями поиска:
                - ingredients: List[str] - список ингредиентов
                - difficulty: str - сложность
                - max_time: int - максимальное время
                - min_time: int - минимальное время
                - name: str - название
                
        Returns:
            List[Dict]: Список рецептов
        """
        filtered_recipes = recipes.copy()
        
        # Поиск по ингредиентам
        if "ingredients" in criteria:
            filtered_recipes = self.find_recipes_by_ingredients(
                filtered_recipes,
                criteria["ingredients"]
            )
            filtered_recipes = [r["recipe"] for r in filtered_recipes]
        
        # Поиск по сложности
        if "difficulty" in criteria:
            filtered_recipes = self.find_recipes_by_difficulty(
                filtered_recipes,
                criteria["difficulty"]
            )
        
        # Поиск по времени
        if "max_time" in criteria:
            filtered_recipes = self.find_recipes_by_cooking_time(
                filtered_recipes,
                criteria["max_time"],
                criteria.get("min_time")
            )
        
        # Поиск по названию
        if "name" in criteria:
            name_matches = self.find_recipes_by_name(
                filtered_recipes,
                criteria["name"]
            )
            filtered_recipes = [r[0] for r in name_matches]
        
        return filtered_recipes 