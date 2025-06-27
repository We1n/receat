from typing import List, Dict, Any
import re
from src.services.product_service import ProductService

async def calculate_from_text(text: str) -> str:
    """
    Унифицированный калькулятор БЖУ: парсит текст, ищет продукты через ProductService, считает и форматирует результат.
    """
    product_service = ProductService()
    lines = text.strip().split('\n')
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
        return "\n".join(errors) + "\n\nПроверьте формат: `название продукта вес` (например, `овсянка 50г`)."

    if not products:
        return "❌ Не удалось найти ни одного продукта. Проверьте формат ввода и попробуйте снова."

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

    if not results_by_product:
        return "Не удалось найти ни один из указанных продуктов в базе. Проверьте названия."

    result_lines = ["📊 *Результаты расчета БЖУ:*"]
    if info_lines:
        result_lines.extend(info_lines)
    result_lines.append("*Детализация по продуктам:*")
    result_lines.extend(results_by_product)
    result_lines.append("\n" + "─" * 20)
    result_lines.append(f"✅ *Итого ({int(total_weight)}г):*")
    result_lines.append(f"   Калории: *{total['calories']:.1f} ккал*")
    result_lines.append(f"   Белки: *{total['protein']:.1f} г*")
    result_lines.append(f"   Жиры: *{total['fat']:.1f} г*")
    result_lines.append(f"   Углеводы: *{total['carbs']:.1f} г*")

    if not_found_products:
        result_lines.append("\n" + "─" * 20)
        result_lines.append("⚠️ *Следующие продукты не найдены в базе:*")
        result_lines.extend([f"  - {name}" for name in not_found_products])
        result_lines.append("\n_Расчет произведен без учета этих продуктов._")

    return "\n".join(result_lines) 