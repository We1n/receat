import json
import uuid
from pathlib import Path

RECIPES_PATH = Path("data/recipes.json")
BACKUP_PATH = Path("data/recipes_backup.json")


def add_ids_to_recipes():
    if not RECIPES_PATH.exists():
        print(f"❌ Файл {RECIPES_PATH} не найден!")
        return

    # Делаем резервную копию
    BACKUP_PATH.write_bytes(RECIPES_PATH.read_bytes())
    print(f"✅ Резервная копия сохранена: {BACKUP_PATH}")

    with open(RECIPES_PATH, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    changed = 0
    for name, data in recipes.items():
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
            changed += 1
            print(f"Добавлен id для рецепта: {name}")

    if changed == 0:
        print("Все рецепты уже имеют id. Изменений не требуется.")
        return

    with open(RECIPES_PATH, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)
    print(f"✅ Обновлено {changed} рецептов. Все рецепты теперь имеют id!")

if __name__ == "__main__":
    add_ids_to_recipes() 