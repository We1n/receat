"""
Сервис для анализа нутриентов по рецепту.
Использует существующие сервисы и модели проекта.
"""
from typing import List, Dict, Any, Optional, Tuple
import logging
from src.services.product_service import ProductService

logger = logging.getLogger(__name__)

class NutrientAnalysisService:
    """
    Сервис для анализа нутриентов по рецепту.
    """
    def __init__(self):
        self.product_service = ProductService()

    def analyze_recipe(self, recipe_text: str) -> Dict[str, Any]:
        """
        Анализирует рецепт: парсит ингредиенты, сопоставляет с продуктами, считает нутриенты.
        Args:
            recipe_text: текст рецепта (или список ингредиентов)
        Returns:
            dict: результат анализа (итоговые нутриенты, найденные/ненайденные ингредиенты, советы)
        """
        try:
            import re
            lines = recipe_text.strip().split('\n')
            products = []
            info_lines = []
            errors = []
            for line in lines:
                if not line.strip():
                    continue
                match = re.match(r'^(.*?)\s+([\d.,]+)\s*(г|гр)?\.?', line.strip(), re.IGNORECASE)
                if match:
                    name = match.group(1).strip().lower()
                    weight_str = match.group(2).replace(',', '.')
                    try:
                        weight = float(weight_str)
                        products.append({'name': name, 'weight': weight})
                    except ValueError:
                        errors.append(f"❌ Не удалось распознать вес: '{line}'")
                else:
                    name = line.strip().lower()
                    if name:
                        products.append({'name': name, 'weight': 100})
                        info_lines.append(f"ℹ️ Для продукта '{name}' будет рассчитано по умолчанию для 100 г.")
                    else:
                        errors.append(f"❌ Не удалось распознать строку: '{line}'")

            if errors:
                return {
                    "success": False,
                    "error": "\n".join(errors),
                    "advice": "Проверьте формат: 'название продукта вес' (например, 'овсянка 50г')."
                }

            if not products:
                return {
                    "success": False,
                    "error": "Не удалось найти ни одного продукта. Проверьте формат ввода и попробуйте снова."
                }

            total_nutrients = {
                "calories": 0.0,
                "protein": 0.0,
                "fat": 0.0,
                "carbs": 0.0,
                "fiber": 0.0,
                "sugar": 0.0,
                "sodium": 0.0,
                "cholesterol": 0.0
            }
            total_weight = 0.0
            found_products = []
            not_found_products = []
            details = []

            for item in products:
                name = item["name"]
                weight = float(item["weight"])
                matches = self.product_service.search_products(name)
                if matches:
                    product = matches[0]
                    nutrients = self.product_service.calculate_nutrients(product, weight)
                    for k in total_nutrients:
                        total_nutrients[k] += nutrients.get(k, 0)
                    total_weight += weight
                    found_products.append(name)
                    details.append(
                        f"  - {product['emoji'] if 'emoji' in product else ''}{product['name'].capitalize()} ({int(weight)}г): "
                        f"{nutrients.get('calories', 0):.1f} ккал, Б:{nutrients.get('protein', 0):.1f} Ж:{nutrients.get('fat', 0):.1f} У:{nutrients.get('carbs', 0):.1f}"
                    )
                else:
                    not_found_products.append(name)

            result = {
                "success": True,
                "total_nutrients": total_nutrients,
                "total_weight": total_weight,
                "details": details,
                "not_found": not_found_products,
                "info": info_lines
            }
            return result
        except Exception as e:
            logger.error(f"Ошибка анализа рецепта: {e}")
            return {
                "success": False,
                "error": str(e),
                "advice": "Произошла ошибка при анализе рецепта. Попробуйте ещё раз или обратитесь к администратору."
            } 