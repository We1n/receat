import logging
import json
from pathlib import Path

class DataService:
    """
    Сервис для работы с данными пользователей (без покупок)
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("DataService инициализирован")
        self.user_states_file = Path("data/user_states.json")

    def get_user_data(self, user_id):
        """Получить данные пользователя по user_id из JSON-файла."""
        try:
            if self.user_states_file.exists():
                with open(self.user_states_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get(str(user_id), {})
            return {}
        except Exception as e:
            self.logger.error(f"Ошибка при чтении user_states.json: {e}")
            return {}

    def save_user_data(self, user_id, user_data):
        """Сохранить данные пользователя по user_id в JSON-файл."""
        try:
            all_data = {}
            if self.user_states_file.exists():
                with open(self.user_states_file, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            all_data[str(user_id)] = user_data
            with open(self.user_states_file, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Данные пользователя {user_id} успешно сохранены.")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении user_states.json: {e}")

    # Удалено всё, что связано с покупками 