"""
Zentrale Konstanten für die Workforce Scheduling Application

Alle Hardcoded-Werte werden hier definiert für bessere Wartbarkeit
und einfachere Anpassung.
"""

# === Arbeitszeiten ===
WORKING_HOURS_START = 8  # Arbeitsbeginn (Uhr)
WORKING_HOURS_END = 16   # Arbeitsende (Uhr)

# === Arbeitszeitgesetz (ArbZG) Limits ===
MAX_DAILY_HOURS = 10           # Maximale Arbeitsstunden pro Tag
MIN_REST_HOURS = 11            # Mindest-Ruhezeit zwischen Schichten (§5 ArbZG)
MAX_CONSECUTIVE_DAYS = 5       # Max. aufeinanderfolgende Arbeitstage
DEFAULT_MAX_WEEKLY_HOURS = 40  # Standard Wochenstunden (Vollzeit)

# === Solver-Konfiguration ===
SOLVER_TIME_LIMIT_SIMPLE = 10      # Sekunden für einfache Probleme
SOLVER_TIME_LIMIT_MEDIUM = 20      # Sekunden für mittlere Komplexität
SOLVER_TIME_LIMIT_COMPLEX = 30     # Sekunden für komplexe Probleme
SOLVER_TIME_LIMIT_VERY_COMPLEX = 60  # Sekunden für sehr komplexe Probleme

# === Constraint-Gewichtungen ===
HARD_SCORE_WEIGHT = 1    # Gewichtung für Hard-Constraints
SOFT_SCORE_WEIGHT = 1    # Gewichtung für Soft-Constraints

# === UI-Farben für Aufgaben (nach Dauer) ===
TASK_COLORS = {
    1: "#AED6F1",  # Hellblau - 1 Stunde
    2: "#D5F5E3",  # Hellgrün - 2 Stunden
    3: "#FAD7A0",  # Hellorange - 3 Stunden
    4: "#D7BDE2"   # Helllila - 4+ Stunden
}

# === Datenbank ===
DB_NAME = "workforce_scheduling.db"
DB_TIMEOUT = 30  # Sekunden

# === Logging ===
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# === Zeitformat ===
DATE_FORMAT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = "%d.%m.%Y %H:%M"

# === Skill-Management ===
DEFAULT_SKILL_CATEGORIES = {
    'frontend': ['javascript', 'html', 'css', 'react', 'angular', 'vue'],
    'backend': ['python', 'java', 'nodejs', 'spring', 'django'],
    'database': ['sql', 'mongodb', 'postgresql'],
    'devops': ['docker', 'kubernetes', 'aws']
}

# === Feedback-System ===
FEEDBACK_RATING_DISLIKE = -1  # "Lieber nicht"
FEEDBACK_RATING_LIKE = 0      # "Find ich gut"

# === Testfall-Generierung ===
TESTCASE_CONFIG = {
    'simple': {
        'num_employees': 3,
        'num_tasks': 5,
        'num_timeslots': 8,
        'solver_time_limit': SOLVER_TIME_LIMIT_SIMPLE
    },
    'medium': {
        'num_employees': 5,
        'num_tasks': 10,
        'num_timeslots': 16,
        'solver_time_limit': SOLVER_TIME_LIMIT_MEDIUM
    },
    'complex': {
        'num_employees': 10,
        'num_tasks': 20,
        'num_timeslots': 32,
        'solver_time_limit': SOLVER_TIME_LIMIT_COMPLEX
    },
    'very_complex': {
        'num_employees': 15,
        'num_tasks': 30,
        'num_timeslots': 48,
        'solver_time_limit': SOLVER_TIME_LIMIT_VERY_COMPLEX
    }
}

# === UI-Konfiguration ===
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 700
MAIN_WINDOW_TITLE = "Mitarbeiter-Einsatzplanung"

# === Status-Messages ===
STATUS_READY = "Bereit"
STATUS_GENERATING_TESTCASE = "Generiere Testfall..."
STATUS_RUNNING_SOLVER = "Berechne Einsatzplan..."
STATUS_SAVING = "Speichere Zeitplan..."
STATUS_LOADING = "Lade Zeitplan..."
