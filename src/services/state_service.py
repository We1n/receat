"""
Единый сервис управления состояниями пользователей (FSM).
"""
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
import logging
from src.config.states import States

logger = logging.getLogger(__name__)

class UserStateService:
    """
    Сервис для управления состояниями пользователей (FSM).
    Хранит состояния в data/user_states.json.
    """
    def __init__(self, state_file: str = "data/user_states.json", timeout: int = 300):
        self.state_file = state_file
        self.timeout = timeout
        self.state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.state_file):
            return {}
        with open(self.state_file, encoding="utf-8") as f:
            return json.load(f)

    def _save_state(self) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def get_state(self, user_id: int) -> Optional[States]:
        user = self.state.get(str(user_id))
        if not user:
            return None
        state = user.get("state")
        if isinstance(state, str):
            try:
                return States[state]
            except Exception:
                return None
        return state

    def set_state(self, user_id: int, state: States, data: Optional[Dict[str, Any]] = None) -> None:
        self.state[str(user_id)] = {
            "state": state.name,
            "data": data or {},
            "updated_at": datetime.now().isoformat()
        }
        self._save_state()
        logger.info(f"Установлено состояние {state} для пользователя {user_id}")

    def clear_state(self, user_id: Optional[int] = None) -> None:
        if user_id is None:
            self.state = {}
        else:
            self.state.pop(str(user_id), None)
        self._save_state()
        logger.info(f"Очищено состояние пользователя {user_id}")

    def get_state_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        user = self.state.get(str(user_id))
        if not user:
            return None
        return user.get("data") 