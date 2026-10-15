import os
import logging
import traceback
from typing import Optional, Any
import appdirs
from database.db_constants import DatabaseConstants
from config.constants import LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT


def setup_logger(name: Optional[str] = None, level: str = LOG_LEVEL) -> logging.Logger:
    """
    Richtet einen Logger mit File- und Console-Handler ein

    Args:
        name: Name des Loggers (None = Root-Logger)
        level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Konfigurierter Logger
    """
    log_dir = os.path.join(appdirs.user_log_dir(DatabaseConstants.APP_NAME, DatabaseConstants.APP_AUTHOR))
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'workforce_scheduling.log')

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Verhindere doppelte Handler
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Handler für Datei
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)  # Alle Logs in Datei

    # Handler für Console (nur WARNING+)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_error(logger: logging.Logger, error: Exception, context: str = "") -> None:
    """
    Loggt einen Fehler mit vollständigem Traceback

    Args:
        logger: Logger-Instanz
        error: Exception-Objekt
        context: Zusätzlicher Kontext (z.B. "Solver-Ausführung")
    """
    error_msg = f"{context}: {str(error)}" if context else str(error)
    logger.error(error_msg, exc_info=True)
    logger.debug(f"Traceback: {traceback.format_exc()}")


def log_performance(logger: logging.Logger, operation: str, duration_seconds: float, details: Optional[dict] = None) -> None:
    """
    Loggt Performance-Metriken

    Args:
        logger: Logger-Instanz
        operation: Name der Operation (z.B. "Solver-Run")
        duration_seconds: Dauer in Sekunden
        details: Zusätzliche Details (z.B. {"tasks": 20, "employees": 10})
    """
    msg = f"Performance [{operation}]: {duration_seconds:.2f}s"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        msg += f" ({detail_str})"
    logger.info(msg)


def log_constraint_violation(logger: logging.Logger, constraint_name: str, details: dict) -> None:
    """
    Loggt Constraint-Verletzungen

    Args:
        logger: Logger-Instanz
        constraint_name: Name des verletzten Constraints
        details: Details zur Verletzung
    """
    detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
    logger.warning(f"Constraint-Verletzung [{constraint_name}]: {detail_str}")


class ErrorTracker:
    """
    Zentrale Klasse für Error-Tracking über die gesamte Anwendung
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or setup_logger()
        self.error_counts = {}

    def track_error(self, error_type: str, error: Exception, context: str = "") -> None:
        """
        Trackt einen Fehler und zählt Vorkommen

        Args:
            error_type: Kategorie des Fehlers (z.B. "SOLVER", "DATABASE", "UI")
            error: Exception-Objekt
            context: Zusätzlicher Kontext
        """
        # Zähler erhöhen
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Loggen
        full_context = f"[{error_type}] {context}" if context else f"[{error_type}]"
        log_error(self.logger, error, full_context)

    def get_error_summary(self) -> dict:
        """Gibt eine Zusammenfassung aller Fehler zurück"""
        return self.error_counts.copy()

    def reset(self) -> None:
        """Setzt alle Error-Counter zurück"""
        self.error_counts.clear()


# Globaler Error-Tracker (Singleton)
_global_error_tracker: Optional[ErrorTracker] = None


def get_error_tracker() -> ErrorTracker:
    """Gibt den globalen Error-Tracker zurück"""
    global _global_error_tracker
    if _global_error_tracker is None:
        _global_error_tracker = ErrorTracker()
    return _global_error_tracker