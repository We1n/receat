"""
Универсальные функции для расчёта нутриентов по продуктам и рецептам.
"""
from typing import List, Dict, Any
from src.services.product_service import ProductService

def calculate_nutrients_from_text(text: str) -> Dict[str, Any]:
    """
    Универсальный калькулятор БЖУ: парсит текст, ищет продукты через ProductService, считает и форматирует результат.
    """
    product_service = ProductService()
    lines = text.strip().split('\n')
    products = []
    info_lines = []
    errors = []
    for line in lines:
        if not line.strip():
            continue
        import re
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
        return {"success": False, "error": "\n".join(errors)}

    if not products:
        return {"success": False, "error": "❌ Не удалось найти ни одного продукта. Проверьте формат ввода и попробуйте снова."}

    total = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    total_weight = 0.0
    results_by_product = []
    not_found_products = []

    for item in products:
        name = str(item["name"])
        weight = float(item["weight"])
        matches = product_service.search_products(name)
        if matches:
            product = matches[0]
            nutrients = product_service.calculate_nutrients(product, weight)
            total["calories"] += nutrients.get("calories", 0)
            total["protein"] += nutrients.get("protein", 0)
            total["fat"] += nutrients.get("fat", 0)
            total["carbs"] += nutrients.get("carbs", 0)
            total_weight += weight
            results_by_product.append(
                f"  - {product.get('emoji', '')}{product['name'].capitalize()} ({int(weight)}г): "
                f"{nutrients.get('calories', 0):.1f} ккал, Б:{nutrients.get('protein', 0):.1f} Ж:{nutrients.get('fat', 0):.1f} У:{nutrients.get('carbs', 0):.1f}"
            )
        else:
            not_found_products.append(name)

    return {
        "success": True,
        "info": info_lines,
        "results_by_product": results_by_product,
        "not_found": not_found_products,
        "total": total,
        "total_weight": total_weight
    } 