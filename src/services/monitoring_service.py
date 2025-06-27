import os
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from src.monitoring.monitor import SystemMonitor
from src.monitoring.error_monitor import ErrorMonitor
from src.monitoring.performance_monitor import PerformanceMonitor
from src.monitoring.cache_monitor import CacheMonitor
from pathlib import Path

logger = logging.getLogger(__name__)

class MonitoringService:
    """
    Сервис мониторинга и логирования для EatBot
    """
    def __init__(self, monitoring_file: Optional[Path] = None):
        self.system_monitor = SystemMonitor()
        self.error_monitor = ErrorMonitor()
        self.performance_monitor = PerformanceMonitor()
        self.cache_monitor = CacheMonitor()
        self.metrics_file = "monitoring/metrics.json"
        self.alerts_file = "monitoring/alerts.json"
        self.logs_dir = "logs/monitoring"
        self.monitoring_file = Path(monitoring_file) if monitoring_file else Path("monitoring/monitoring.json")
        self.metrics = {
            "requests": {
                "total": 0,
                "by_endpoint": {},
                "by_method": {},
                "by_status": {}
            },
            "errors": {
                "total": 0,
                "by_type": {},
                "by_endpoint": {},
                "details": []
            },
            "response_time": []
        }
        os.makedirs(self.monitoring_file.parent, exist_ok=True)
        if monitoring_file:
            if self.monitoring_file.exists():
                self._load_metrics()
            else:
                self.save_metrics()
        else:
            self._load_metrics()
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs("monitoring", exist_ok=True)

    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Логирование события в JSON-файл"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        try:
            log_path = os.path.join(self.logs_dir, f"{event_type}.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            logger.info(f"Событие {event_type} зафиксировано: {data}")
        except Exception as e:
            logger.error(f"Ошибка при логировании события: {e}")

    def record_metric(self, name: str, value: Any) -> None:
        """Запись метрики"""
        self.system_monitor.track_metric(name, value)
        self.log_event("metric", {"name": name, "value": value})

    def record_error(self, error_type: str, error_message: str) -> None:
        """Запись ошибки"""
        self.system_monitor.track_error(error_type, error_message)
        self.error_monitor.errors.setdefault(error_type, []).append({
            "timestamp": datetime.now().isoformat(),
            "message": error_message
        })
        self.log_event("error", {"type": error_type, "message": error_message})

    def record_alert(self, alert_type: str, message: str) -> None:
        """Запись алерта"""
        self.system_monitor.metrics[alert_type] = message
        alert_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message
        }
        try:
            with open(self.alerts_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert_entry, ensure_ascii=False) + "\n")
            logger.warning(f"ALERT: {alert_type} - {message}")
        except Exception as e:
            logger.error(f"Ошибка при записи алерта: {e}")

    def export_metrics(self) -> None:
        """Экспорт всех метрик в JSON-файл"""
        try:
            metrics = self.system_monitor.metrics
            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            logger.info("Метрики экспортированы в monitoring/metrics.json")
        except Exception as e:
            logger.error(f"Ошибка при экспорте метрик: {e}")

    def import_metrics(self) -> Optional[Dict[str, Any]]:
        """Импорт метрик из JSON-файла"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, "r", encoding="utf-8") as f:
                    metrics = json.load(f)
                logger.info("Метрики импортированы из monitoring/metrics.json")
                return metrics
        except Exception as e:
            logger.error(f"Ошибка при импорте метрик: {e}")
        return None

    def get_performance_report(self) -> Dict[str, Any]:
        """Получение отчёта о производительности"""
        return self.system_monitor.get_performance_report()

    def get_system_status(self) -> Dict[str, Any]:
        """Получение текущего состояния системы"""
        return self.system_monitor.metrics

    def get_error_stats(self) -> Dict[str, Any]:
        """Получение статистики ошибок"""
        return self.error_monitor.errors

    def get_cache_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        return self.cache_monitor.stats

    def get_performance_stats(self) -> Dict[str, Any]:
        """Получение статистики производительности"""
        return self.performance_monitor.get_performance_stats()

    def clear_metrics(self) -> None:
        """Очистка всех метрик"""
        self.system_monitor.clear_metrics()
        self.performance_monitor.query_times.clear()
        self.performance_monitor.memory_usage.clear()
        self.performance_monitor.cpu_usage.clear()
        self.performance_monitor.error_count.clear()
        self.cache_monitor.reset_stats()
        logger.info("Все метрики и статистика очищены")

    def log_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        self.metrics["requests"]["total"] += 1
        self.metrics["requests"]["by_endpoint"].setdefault(endpoint, 0)
        self.metrics["requests"]["by_endpoint"][endpoint] += 1
        self.metrics["requests"]["by_method"].setdefault(method, 0)
        self.metrics["requests"]["by_method"][method] += 1
        self.metrics["requests"]["by_status"].setdefault(str(status_code), 0)
        self.metrics["requests"]["by_status"][str(status_code)] += 1
        self.metrics["response_time"].append({
            "endpoint": endpoint,
            "time": response_time,
            "timestamp": datetime.now().isoformat()
        })
        self.save_metrics()

    def log_error(self, endpoint: str, error_type: str, error_message: str):
        self.metrics["errors"]["total"] += 1
        self.metrics["errors"]["by_type"].setdefault(error_type, 0)
        self.metrics["errors"]["by_type"][error_type] += 1
        self.metrics["errors"]["by_endpoint"].setdefault(endpoint, 0)
        self.metrics["errors"]["by_endpoint"][endpoint] += 1
        self.metrics["errors"]["details"].append({
            "endpoint": endpoint,
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })
        self.save_metrics()

    def get_metrics(self):
        return self.metrics

    def get_average_response_time(self):
        times = [item["time"] for item in self.metrics["response_time"]]
        if not times:
            return 0.0
        return round(sum(times) / len(times), 2)

    def get_error_rate(self):
        total_requests = self.metrics["requests"]["total"]
        total_errors = self.metrics["errors"]["total"]
        if total_requests == 0:
            return 0.0
        return round(total_errors / (total_requests + total_errors) * 100, 2) if (total_requests + total_errors) > 0 else 0.0

    def get_most_common_errors(self):
        error_counts = self.metrics["errors"]["by_type"]
        return [
            {"type": k, "count": v}
            for k, v in sorted(error_counts.items(), key=lambda x: -x[1])
        ]

    def get_endpoint_statistics(self):
        endpoints = set(self.metrics["requests"]["by_endpoint"].keys()) | set(self.metrics["errors"]["by_endpoint"].keys())
        stats = {}
        for endpoint in endpoints:
            stats[endpoint] = {
                "requests": self.metrics["requests"]["by_endpoint"].get(endpoint, 0),
                "errors": self.metrics["errors"]["by_endpoint"].get(endpoint, 0)
            }
        return stats

    def cleanup_old_metrics(self):
        # Оставляем только метрики за последние 30 дней
        cutoff = datetime.now() - timedelta(days=30)
        self.metrics["response_time"] = [
            item for item in self.metrics["response_time"]
            if datetime.fromisoformat(item["timestamp"]) > cutoff
        ]
        self.save_metrics()

    def save_metrics(self):
        try:
            with open(self.monitoring_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении метрик: {e}")

    def _load_metrics(self):
        if self.monitoring_file.exists():
            try:
                with open(self.monitoring_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Приведение к нужным типам
                    self.metrics = loaded
                    # Исправляем типы, если вдруг не dict
                    for k in ["by_endpoint", "by_method", "by_status"]:
                        if not isinstance(self.metrics["requests"][k], dict):
                            self.metrics["requests"][k] = dict(self.metrics["requests"][k])
                    for k in ["by_type", "by_endpoint"]:
                        if not isinstance(self.metrics["errors"][k], dict):
                            self.metrics["errors"][k] = dict(self.metrics["errors"][k])
                    if not isinstance(self.metrics["errors"]["details"], list):
                        self.metrics["errors"]["details"] = list(self.metrics["errors"]["details"])
                    if not isinstance(self.metrics["response_time"], list):
                        self.metrics["response_time"] = list(self.metrics["response_time"])
            except Exception as e:
                logger.error(f"Ошибка при загрузке метрик: {e}")

    def load_metrics(self):
        self._load_metrics()
        return self.metrics 