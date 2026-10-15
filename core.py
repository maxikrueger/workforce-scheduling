import optapy
from datetime import datetime, timedelta
from typing import Optional, Set, List, Dict
from optapy import (
    problem_fact,
    planning_entity,
    planning_solution,
    planning_variable,
    constraint_provider,
    problem_fact_collection_property,
    planning_entity_collection_property,
    planning_score)

from optapy.types import Constraint, ConstraintFactory
from optapy.score import HardSoftScore
from optapy.constraint import Joiners, ConstraintCollectors
from enum import Enum


# Einfache Enums für Status
class EmployeeStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFF = "off"

# Zeitslots (Problemfakten)
@problem_fact
class TimeSlot:
    def __init__(self, id: str, start_time: datetime):
        self.id = id
        self.start_time = start_time

# Mitarbeiter (Problemfakten)
@problem_fact
class Employee:
    def __init__(self, id: str, name: str, skills: Set[str], status: EmployeeStatus = EmployeeStatus.AVAILABLE, 
                 preferred_skills: Set[str] = None, working_hours: Dict = None):
        self.id = id
        self.name = name
        self.skills = skills
        self.status = status
        # Initialize preferred skills (default to empty set if None)
        self.preferred_skills = preferred_skills if preferred_skills is not None else set()
        # Initialize working hours (default to empty dict if None)
        self.working_hours = working_hours if working_hours is not None else {}

    def has_skill(self, skill: str) -> bool:
        return skill in self.skills

    def is_available(self) -> bool:
        return self.status == EmployeeStatus.AVAILABLE
        
    def prefers_skill(self, skill: str) -> bool:
        """Checks if the given skill is one of the employee's preferred skills"""
        return skill in self.preferred_skills

# Aufgaben (Planungsentitäten)
@planning_entity
class Task:
    def __init__(self, id: str, duration: int, required_skills: Set[str]):
        self.id = id
        self.duration = duration
        self.required_skills = required_skills
        self._time_slot = None
        self._assigned_employee = None
        self.status = None
        self.feedback_score = 0
        self.employee_feedback = {}  # {employee_id: Bewertung}, -1 = "Lieber nicht", 0 = "Find ich gut"
    
    @planning_variable(TimeSlot, ["timeSlotRange"])
    def get_time_slot(self):
        return self._time_slot
    
    def set_time_slot(self, time_slot):
        self._time_slot = time_slot

    @planning_variable(Employee, ["employeeRange"])
    def get_assigned_employee(self):
        return self._assigned_employee
    
    def set_assigned_employee(self, employee):
        self._assigned_employee = employee


    def set_feedback_score(self, score: int):
        """Setzt den Feedback-Score für diese Aufgabe"""
        self.feedback_score = score
    
    def get_feedback_score(self) -> int:
        """Gibt den gespeicherten Feedback-Score zurück"""
        return self.feedback_score

    def get_feedback_impact(self) -> int:
        """
        Bewertet die aktuelle Zuweisung anhand des Feedbacks des zugewiesenen Mitarbeiters:
        -2 bei "Lieber nicht", +2 bei "Find ich gut", 0 ohne Feedback
        """
        employee = self._assigned_employee
        if employee is None:
            return 0
        rating = self.employee_feedback.get(employee.id)
        if rating == -1:
            return -2
        if rating == 0:
            return 2
        return 0

# Zeitplan (Planungslösung)
@planning_solution
class Schedule:
    def __init__(self):
        self.time_slots = []
        self.employees = []
        self.tasks = []
        self._score = None
        self.name = f"Zeitplan {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        self.iteration = 1  # Aktuelle Iteration des Schedules
        self.task_feedback = {}  # Dict: {(task_id, employee_id): rating}
    
    @problem_fact_collection_property(TimeSlot)
    @optapy.value_range_provider(range_id="timeSlotRange")
    def get_time_slots(self):
        return self.time_slots

    @problem_fact_collection_property(Employee)
    @optapy.value_range_provider(range_id="employeeRange")
    def get_employees(self):
        return self.employees
    
    @planning_entity_collection_property(Task)
    def get_tasks(self):
        return self.tasks
    
    @planning_score(HardSoftScore)
    def get_score(self):
        return self._score
    
    def set_score(self, score):
        self._score = score


# Hilfsfunktionen für Constraints mit Exception Handling
def end_time_of_task(task) -> Optional[datetime]:
    """
    Berechnet die Endzeit einer Aufgabe basierend auf Startzeit und Dauer
    Gibt None zurück, wenn task oder time_slot None ist
    """
    try:
        if task is None or task.get_time_slot() is None:
            return None
        
        # Sicherere Variante mit timedelta statt hour replacement
        return task.get_time_slot().start_time + timedelta(hours=task.duration)
    except Exception:
        # Fehlerfall abfangen und None zurückgeben
        return None

def check_time_overlap(task1, task2) -> bool:
    """
    Prüft, ob zwei Aufgaben zeitlich überlappen
    Gibt False zurück, wenn einer der Parameter ungültig ist
    """
    try:
        # Prüfen ob alle nötigen Daten vorhanden sind
        if (task1 is None or task2 is None or 
            task1.get_time_slot() is None or task2.get_time_slot() is None):
            return False
        
        task1_start = task1.get_time_slot().start_time
        task1_end = task1_start + timedelta(hours=task1.duration)
        
        task2_start = task2.get_time_slot().start_time
        task2_end = task2_start + timedelta(hours=task2.duration)
        
        # Klassische Überlappungsformel
        return task1_start < task2_end and task2_start < task1_end
    except Exception:
        # Im Zweifelsfall keine Überlappung zurückgeben
        return False

def has_required_skills(employee, required_skills) -> bool:
    """
    Prüft, ob ein Mitarbeiter alle benötigten Fähigkeiten hat
    """
    try:
        if employee is None or required_skills is None:
            return False
        
        return all(employee.has_skill(skill) for skill in required_skills)
    except Exception:
        return False

def count_matching_skills(employee, required_skills) -> int:
    """
    Zählt die Anzahl der übereinstimmenden Fähigkeiten
    """
    try:
        if employee is None or required_skills is None:
            return 0
        
        return sum(1 for skill in required_skills if employee.has_skill(skill))
    except Exception:
        return 0

def safe_check_working_hours(task):
    """
    Sichere Implementierung zur Prüfung der bevorzugten Arbeitszeiten.
    Diese Funktion vermeidet alle möglichen AttributeErrors.
    
    Args:
        task: Die zu prüfende Aufgabe
        
    Returns:
        1 wenn die Aufgabe in bevorzugten Arbeitszeiten liegt, sonst 0
    """
    try:
        # Safety checks
        if not task:
            return 0
            
        employee = task.get_assigned_employee()
        if not employee:
            return 0
            
        time_slot = task.get_time_slot()
        if not time_slot:
            return 0
        
        # Prüfen, ob working_hours existiert und ein dict ist
        if not hasattr(employee, 'working_hours') or not isinstance(employee.working_hours, dict):
            # Fallback zu einer Standard-Präferenz (9-15 Uhr)
            hour = time_slot.start_time.hour
            return 1 if 9 <= hour < 15 else 0
        
        # Day of week ermitteln (0=Montag, 6=Sonntag)
        day_of_week = time_slot.start_time.weekday()
        
        # Prüfen, ob es Präferenzen für diesen Tag gibt
        if day_of_week not in employee.working_hours:
            return 0
        
        # Präferenzen für diesen Tag abrufen
        day_prefs = employee.working_hours[day_of_week]
        
        # Wenn es keine dict ist oder 'preferred' nicht True ist, zurück zu 0
        if not isinstance(day_prefs, dict) or not day_prefs.get('preferred', False):
            return 0
        
        # Start- und Endzeiten extrahieren
        start_str = day_prefs.get('start', '08:00')
        end_str = day_prefs.get('end', '17:00')
        
        # Konvertiere Zeiten in Stunden
        try:
            start_hour = int(start_str.split(':')[0])
            end_hour = int(end_str.split(':')[0])
            task_hour = time_slot.start_time.hour
            
            # Prüfen, ob die Aufgabe in den bevorzugten Stunden beginnt
            if start_hour <= task_hour < end_hour:
                return 1
        except (ValueError, IndexError):
            # Fallback bei Problemen mit den Zeitformaten
            pass
        
        return 0
    except Exception:
        # Bei unerwarteten Fehlern, keine Belohnung
        return 0

# Global variable to store the current schedule during constraint evaluation
_CURRENT_SCHEDULE = None


def calculate_assignment_satisfaction(task, solution):
    """
    Berechnet den Zufriedenheitswert basierend auf dem Feedback zur konkreten Aufgabe.
    
    Bei negativem Feedback (-1 für "Lieber nicht") wird eine negative Bewertung zurückgegeben,
    um diese Aufgabenzuweisung zu vermeiden.
    
    Bei positivem Feedback (0 für "Find ich gut") wird eine positive Bewertung zurückgegeben,
    um diese Aufgabenzuweisung zu bevorzugen.
    
    Args:
        task: Die zu bewertende Aufgabe
        solution: Die aktuelle Lösungsinstanz mit dem Feedback
        
    Returns:
        int: Ein Wert zwischen -2 und 2, abhängig vom Feedback
    """
    try:
        employee = task.get_assigned_employee()
        if not employee:
            return 0
        
        # Prüfen, ob task_feedback im solution existiert
        if not hasattr(solution, 'task_feedback'):
            return 0
        
        # Schlüssel für die Aufgabe-Mitarbeiter-Kombination
        key = (task.id, employee.id)
        
        # Feedback abrufen (gibt None zurück, wenn nicht vorhanden)
        feedback = solution.task_feedback.get(key)
        
        if feedback is None:
            # Kein Feedback vorhanden, neutral bewerten
            return 0
        
        # Feedback bewerten: 
        # -1 ("Lieber nicht") -> -2 (starke Bestrafung)
        # 0 ("Find ich gut") -> 2 (starke Belohnung)
        if feedback == -1:
            return -2  # Negative Bewertung stärker gewichten
        elif feedback == 0:
            return 2   # Positive Bewertung belohnen
        
        # Sollte nicht vorkommen, aber zur Sicherheit
        return 0
        
    except Exception as e:
        print(f"Error in calculate_assignment_satisfaction: {e}")
        return 0

@constraint_provider
def define_constraints(constraint_factory: ConstraintFactory):
    return [
        # Existierende Constraints beibehalten
        # 1. Mitarbeiter muss benötigte Fähigkeiten haben
        constraint_factory.forEach(Task)\
            .filter(lambda task: 
                task.get_assigned_employee() is not None and 
                not has_required_skills(task.get_assigned_employee(), task.required_skills)
            )\
            .penalize("Fehlende Fähigkeiten", HardSoftScore.ONE_HARD),
            
        # 2. Keine überlappenden Aufgaben für einen Mitarbeiter
        constraint_factory.forEach(Task)\
            .join(Task,
                # Gleicher Mitarbeiter
                Joiners.equal(lambda t: t.get_assigned_employee()),
                # Unterschiedliche Aufgaben
                Joiners.lessThan(lambda t: t.id))\
            .filter(lambda task1, task2: 
                # Sicherstellen, dass alle Werte vorhanden sind
                task1.get_assigned_employee() is not None and
                check_time_overlap(task1, task2)
            )\
            .penalize("Aufgabenüberlappung", HardSoftScore.ONE_HARD),
            
        # 3. Mitarbeiter muss verfügbar sein
        constraint_factory.forEach(Task)\
            .filter(lambda task: 
                task.get_assigned_employee() is not None and
                not task.get_assigned_employee().is_available()
            )\
            .penalize("Mitarbeiter nicht verfügbar", HardSoftScore.ONE_HARD),
            
        # 4. Aufgaben nur zwischen 8:00 und 16:00 Uhr
        constraint_factory.forEach(Task)\
            .filter(lambda task: 
                task.get_time_slot() is not None and 
                not is_within_working_hours(task)
            )\
            .penalize("Außerhalb der Arbeitszeit", HardSoftScore.ONE_HARD),
        
        # 5. Aufgaben dürfen nicht über 16:00 Uhr hinausgehen
        constraint_factory.forEach(Task)\
            .filter(lambda task: 
                task.get_time_slot() is not None and 
                extends_beyond_working_hours(task)
            )\
            .penalize("Endet nach Arbeitsende", HardSoftScore.ONE_HARD),
            
        # Weiche Einschränkungen (besser wenn erfüllt)
        # 1. Belohne Fähigkeitsübereinstimmungen
        constraint_factory.forEach(Task)\
            .filter(lambda task: task.get_assigned_employee() is not None)\
            .reward("Fähigkeitsübereinstimmung", HardSoftScore.ONE_SOFT,
                    lambda task: count_matching_skills(task.get_assigned_employee(), task.required_skills)),
                    
        # 2. Belohne Übereinstimmungen mit bevorzugten Fähigkeiten der Mitarbeiter
        constraint_factory.forEach(Task)\
            .filter(lambda task: 
                task.get_assigned_employee() is not None and
                hasattr(task.get_assigned_employee(), 'preferred_skills') and
                task.get_assigned_employee().preferred_skills is not None
            )\
            .reward("Bevorzugte Fähigkeiten", HardSoftScore.ONE_SOFT,
                    lambda task: sum(1 for skill in task.required_skills 
                                    if task.get_assigned_employee().prefers_skill(skill))),
        
        # 3. Belohne Aufgaben in bevorzugten Arbeitszeiten
        constraint_factory.forEach(Task)\
            .filter(lambda task: 
                task.get_assigned_employee() is not None and
                task.get_time_slot() is not None
            )\
            .reward("Einfache Arbeitszeiten", HardSoftScore.ONE_SOFT,
                    lambda task: 1 if 9 <= task.get_time_slot().start_time.hour < 15 else 0),


        # 4. Berücksichtige Mitarbeiter-Feedback aus der vorherigen Iteration
        constraint_factory.forEach(Task)\
            .filter(lambda task: task.get_feedback_impact() != 0)\
            .impact("Mitarbeiter-Feedback", HardSoftScore.ONE_SOFT,
                    lambda task: task.get_feedback_impact()),
    ]


def set_current_schedule(schedule):
    """
    Setzt das aktuelle Schedule-Objekt für die Constraint-Auswertung
    
    Args:
        schedule: Das Schedule-Objekt, das während der Constraint-Auswertung verwendet werden soll
    """
    global _CURRENT_SCHEDULE
    _CURRENT_SCHEDULE = schedule

def get_current_schedule():
    """
    Gibt das aktuelle Schedule-Objekt zurück, das während der Constraint-Auswertung verwendet wird
    
    Returns:
        Das aktuelle Schedule-Objekt oder None, wenn keines gesetzt ist
    """
    global _CURRENT_SCHEDULE
    return _CURRENT_SCHEDULE

# Hilfsfunktionen für die Constraints
def is_within_working_hours(task):
    """
    Prüft, ob eine Aufgabe innerhalb der Arbeitszeit (8-18 Uhr) beginnt
    """
    try:
        if task.get_time_slot() is None:
            return True  # Ignoriere nicht zugewiesene Aufgaben
        
        start_hour = task.get_time_slot().start_time.hour
        return 8 <= start_hour < 16
    except Exception:
        return False

def extends_beyond_working_hours(task):
    """
    Prüft, ob eine Aufgabe über 16 Uhr hinausgeht
    """
    try:
        if task.get_time_slot() is None:
            return False  # Ignoriere nicht zugewiesene Aufgaben
        
        start_time = task.get_time_slot().start_time
        end_time = start_time + timedelta(hours=task.duration)
        
        # Aufgabe endet nach 16 Uhr
        return end_time > start_time.replace(hour=16, minute=0, second=0, microsecond=0)
    except Exception:
        return False


# Hauptfunktion zum Testen
def main():
    # Erstelle Zeitplan
    schedule = Schedule()
    
    # Füge Zeitslots hinzu (8:00 - 12:00 Uhr)
    schedule.time_slots = [
        TimeSlot(f"slot_{i}", 
                datetime(2024, 2, 17, 8 + i, 0))
        for i in range(5)
    ]
    
    # Setup working hours for employees (Monday = 0)
    alice_working_hours = {
        0: {"start": "08:00", "end": "17:00", "preferred": True},  # Monday
        1: {"start": "08:00", "end": "17:00", "preferred": True},  # Tuesday
        2: {"start": "09:00", "end": "16:00", "preferred": True},  # Wednesday
        3: {"start": "08:00", "end": "17:00", "preferred": True},  # Thursday
        4: {"start": "08:00", "end": "14:00", "preferred": True}   # Friday
    }
    
    bob_working_hours = {
        0: {"start": "10:00", "end": "18:00", "preferred": True},  # Monday
        1: {"start": "10:00", "end": "18:00", "preferred": True},  # Tuesday
        2: {"start": "10:00", "end": "18:00", "preferred": True},  # Wednesday
        3: {"start": "10:00", "end": "18:00", "preferred": True},  # Thursday
        4: {"start": "08:00", "end": "13:00", "preferred": True}   # Friday
    }
    
    # Füge Mitarbeiter mit ihren Fähigkeiten hinzu
    schedule.employees = [
        Employee("emp1", "Alice", {"python", "java", "sql"}, working_hours=alice_working_hours),
        Employee("emp2", "Bob", {"python", "javascript"}, working_hours=bob_working_hours),
        Employee("emp3", "Charlie", {"java", "sql"})  # No working hours preference
    ]
    
    # Füge Aufgaben mit benötigten Fähigkeiten hinzu
    schedule.tasks = [
        Task("Task1", 2, {"python"}),
        Task("Task2", 1, {"javascript"}),
        Task("Task3", 1, {"java", "sql"})
    ]
    
    # Beispiel-Feedback hinzufügen
    schedule.task_feedback = {
        ("Task1", "emp1"): 0,  # "Find ich gut" für Alice+Task1
        ("Task2", "emp2"): -1   # "Lieber nicht" für Bob+Task2
    }
    
    # Aktuelles Schedule setzen für Constraints
    set_current_schedule(schedule)
    
    # Solver-Konfiguration
    solver_config = optapy.config.solver.SolverConfig()
    solver_config.withEntityClasses(Task)
    solver_config.withSolutionClass(Schedule)
    solver_config.withConstraintProviderClass(define_constraints)
    
    # Zeitlimit setzen
    solver_config.withTerminationConfig(
        optapy.config.solver.termination.TerminationConfig()
        .withSecondsSpentLimit(10)
    )
    
    # Solver erstellen und Problem lösen
    solver_factory = optapy.solver_factory_create(solver_config)
    solver = solver_factory.buildSolver()
    solution = solver.solve(schedule)
    
    # Lösung ausgeben
    print("\nGefundene Lösung:")
    for task in solution.get_tasks():
        slot = task.get_time_slot()
        employee = task.get_assigned_employee()
        if slot and employee:
            task_hour = slot.start_time.hour
            working_hours_result = safe_check_working_hours(task)
            is_preferred = "in bevorzugter Zeit" if working_hours_result == 1 else "nicht in bevorzugter Zeit"
            
            # Prüfen, ob Feedback vorhanden ist
            feedback_key = (task.id, employee.id)
            feedback = solution.task_feedback.get(feedback_key, "Kein Feedback")
            feedback_text = ""
            if feedback == 0:
                feedback_text = "(Mitarbeiter findet die Zuweisung gut)"
            elif feedback == -1:
                feedback_text = "(Mitarbeiter möchte diese Aufgabe lieber nicht)"
            
            print(f"{task.id} -> Zeit: {slot.start_time.strftime('%H:%M')}, "
                  f"Mitarbeiter: {employee.name}, "
                  f"Benötigte Fähigkeiten: {', '.join(task.required_skills)}, "
                  f"{is_preferred} {feedback_text}")
        else:
            print(f"{task.id} -> Nicht zugewiesen")

# Ausführen, wenn direkt gestartet
if __name__ == "__main__":
    main()