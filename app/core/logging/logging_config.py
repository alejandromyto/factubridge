"""
app/core/logging_config.py

Configuración de logging estructurado con JSON.
"""

import logging
import sys
from typing import Any, Dict

from pythonjsonlogger.json import JsonFormatter


class CustomJsonFormatter(JsonFormatter):
    """Formateador JSON con campos adicionales para trazabilidad."""

    def add_fields(
        self,
        log_data: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_data, record, message_dict)

        # Campos estándar
        log_data["timestamp"] = self.formatTime(record)
        log_data["level"] = record.levelname
        log_data["logger"] = record.name
        log_data["module"] = record.module
        log_data["function"] = record.funcName

        # Contexto adicional (safe para mypy)
        lote_id = getattr(record, "lote_id", None)
        if lote_id is not None:
            log_data["lote_id"] = lote_id

        registro_id = getattr(record, "registro_id", None)
        if registro_id is not None:
            log_data["registro_id"] = registro_id

        instalacion_id = getattr(record, "instalacion_id", None)
        if instalacion_id is not None:
            log_data["instalacion_id"] = instalacion_id


def setup_logging(log_level: str = "INFO", use_json: bool = True) -> None:
    """
    Configura el sistema de logging.

    Args:
        log_level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Si True, usa JSON. Si False, texto legible (desarrollo)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Limpiar handlers existentes
    root_logger.handlers.clear()

    # Handler a stdout
    handler = logging.StreamHandler(sys.stdout)

    formatter: logging.Formatter

    if use_json:
        # JSON para producción
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    else:
        # Texto para desarrollo local
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Silenciar logs verbosos de librerías
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
