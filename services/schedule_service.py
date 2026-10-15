import optapy
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging

from testgen import generate_test_case as testgen_generate_test_case
from core import Task, Schedule, define_constraints, HardSoftScore
from config.constants import (
    SOLVER_TIME_LIMIT_SIMPLE,
    SOLVER_TIME_LIMIT_MEDIUM,
    SOLVER_TIME_LIMIT_COMPLEX,
    SOLVER_TIME_LIMIT_VERY_COMPLEX
)
from logger import setup_logger, log_performance
import time

class SchedulerService:
    """Service-Klasse für Scheduling-Operationen"""

    def __init__(self):
        """Initialisiert den Scheduler-Service"""
        self.logger = setup_logger("SchedulerService")

        # Solver-Zeitlimits aus Konstanten (können überschrieben werden)
        self.time_limits = {
            'simple': SOLVER_TIME_LIMIT_SIMPLE,
            'medium': SOLVER_TIME_LIMIT_MEDIUM,
            'complex': SOLVER_TIME_LIMIT_COMPLEX,
            'very_complex': SOLVER_TIME_LIMIT_VERY_COMPLEX
        }

    def generate_test_case(self, complexity):
        """
        Generiert einen Testfall mit der angegebenen Komplexität

        Args:
            complexity: Komplexitätsstufe ("simple", "medium", "complex", "very_complex")

        Returns:
            Schedule: Ein generiertes Schedule-Objekt
        """
        self.logger.info(f"Generiere Testfall mit Komplexität: {complexity}")
        # Testfall generieren über das testgen-Modul
        return testgen_generate_test_case(complexity)
    
    def run_scheduler(self, schedule, complexity, custom_time_limit: Optional[int] = None):
        """
        Führt den OptaPy-Scheduler aus

        Args:
            schedule: Das Schedule-Objekt mit den zu optimierenden Daten
            complexity: Komplexitätsstufe für Zeitlimitbestimmung
            custom_time_limit: Optionales benutzerdefiniertes Zeitlimit in Sekunden

        Returns:
            Schedule: Das optimierte Schedule-Objekt
        """
        # Zeitlimit bestimmen
        if custom_time_limit:
            time_limit = custom_time_limit
            self.logger.info(f"Verwende benutzerdefiniertes Zeitlimit: {time_limit}s")
        else:
            time_limit = self.time_limits.get(complexity, SOLVER_TIME_LIMIT_MEDIUM)
            self.logger.info(f"Verwende Zeitlimit für '{complexity}': {time_limit}s")

        # Solver-Konfiguration
        solver_config = optapy.config.solver.SolverConfig()
        solver_config.withEntityClasses(Task)
        solver_config.withSolutionClass(Schedule)
        solver_config.withConstraintProviderClass(define_constraints)

        solver_config.withTerminationConfig(
            optapy.config.solver.termination.TerminationConfig()
            .withSecondsSpentLimit(time_limit)
        )

        # Solver erstellen und Problem lösen
        solver_factory = optapy.solver_factory_create(solver_config)
        solver = solver_factory.buildSolver()

        # Performance-Messung
        start_time = time.time()
        self.logger.info("Solver startet...")

        solution = solver.solve(schedule)

        # Performance loggen
        duration = time.time() - start_time
        log_performance(
            self.logger,
            f"Solver ({complexity})",
            duration,
            {
                "time_limit": time_limit,
                "tasks": len(schedule.tasks),
                "employees": len(schedule.employees)
            }
        )

        return solution
    
    def run_scheduler_with_feedback(self, schedule, complexity, apply_feedback=True):
        """
        Führt den Scheduler mit Berücksichtigung des Feedbacks aus
        
        Args:
            schedule: Das Schedule-Objekt
            complexity: Komplexitätsgrad für die Rechendauer
            apply_feedback: Ob Feedback in die Optimierung einfließen soll
            
        Returns:
            Schedule: Das optimierte Schedule-Objekt
        """
        # Prüfen, ob Feedback verwendet werden soll
        if apply_feedback:
            # Feedback aus der Datenbank laden, falls nicht bereits vorhanden
            if not hasattr(schedule, 'task_feedback') or not schedule.task_feedback:
                try:
                    # Datenbankmanager laden
                    from database.db_manager import DatabaseManager
                    db_manager = DatabaseManager()
                    feedback_manager = db_manager.feedback_manager
                    
                    # Aktuelle Iteration ermitteln
                    iteration = getattr(schedule, 'iteration', 1)
                    
                    # Feedback für die aktuelle Schedule-Iteration laden
                    task_feedback = feedback_manager.get_task_feedback_for_schedule(
                        schedule.id, iteration-1)  # Feedback der vorherigen Iteration
                    
                    # Feedback zum Schedule hinzufügen
                    schedule.task_feedback = task_feedback
                    
                    print(f"Feedback für {len(task_feedback)} Aufgaben geladen")
                except Exception as e:
                    print(f"Fehler beim Laden des Feedbacks: {e}")
                    schedule.task_feedback = {}
        else:
            # Kein Feedback verwenden
            schedule.task_feedback = {}
        
        # Feedback an die Aufgaben übergeben, damit der Solver es bewerten kann
        for task in schedule.tasks:
            task.employee_feedback = {
                employee_id: rating
                for (task_id, employee_id), rating in schedule.task_feedback.items()
                if task_id == task.id
            }
        
        # Solver-Konfiguration wie in run_scheduler
        solver_config = optapy.config.solver.SolverConfig()
        solver_config.withEntityClasses(Task)
        solver_config.withSolutionClass(Schedule)
        solver_config.withConstraintProviderClass(define_constraints)
        
        # Zeitlimit setzen (je nach Komplexität)
        time_limit = 10  # Standard: 10 Sekunden
        if complexity == "complex":
            time_limit = 20
        elif complexity == "very_complex":
            time_limit = 30
            
        solver_config.withTerminationConfig(
            optapy.config.solver.termination.TerminationConfig()
            .withSecondsSpentLimit(time_limit)
        )
        
        # Solver erstellen und Problem lösen
        solver_factory = optapy.solver_factory_create(solver_config)
        solver = solver_factory.buildSolver()
        
        # Lösen und Feedback-Iteration aktualisieren
        solution = solver.solve(schedule)
        solution.iteration = getattr(schedule, 'iteration', 1)
        
        return solution
    
    def init_solution(self, schedule, time_limit=10):
        """
        Initialisiert eine Lösung für einen geladenen Zeitplan
        mit einem kurzen Zeitlimit
        
        Args:
            schedule: Das Schedule-Objekt
            time_limit: Zeitlimit in Sekunden
            
        Returns:
            Schedule: Eine initiale Lösung oder das originale Schedule-Objekt bei Fehler
        """
        try:
            # Solver mit kurzem Zeitlimit
            solver_config = optapy.config.solver.SolverConfig()
            solver_config.withEntityClasses(Task)
            solver_config.withSolutionClass(Schedule)
            solver_config.withConstraintProviderClass(define_constraints)
            
            solver_config.withTerminationConfig(
                optapy.config.solver.termination.TerminationConfig()
                .withSecondsSpentLimit(time_limit)
            )
            
            # Solver erstellen und Problem lösen
            solver_factory = optapy.solver_factory_create(solver_config)
            solver = solver_factory.buildSolver()
            
            return solver.solve(schedule)
        except Exception:
            # Bei Fehler das originale Schedule-Objekt zurückgeben
            return schedule
    
    def collect_feedback(self, schedule, feedback_dict: Dict[Tuple[str, str], int]):
        """
        Sammelt Feedback für einen Schedule zur Verwendung in der nächsten Optimierung
        
        Args:
            schedule: Das Schedule-Objekt
            feedback_dict: Dictionary mit (task_id, employee_id) als Schlüssel und Bewertung (1-5) als Wert
            
        Returns:
            Schedule mit aktualisiertem Feedback
        """
        if not hasattr(schedule, 'task_feedback'):
            schedule.task_feedback = {}
        
        # Feedback zum Schedule hinzufügen
        for (task_id, employee_id), rating in feedback_dict.items():
            schedule.task_feedback[(task_id, employee_id)] = rating
        
        return schedule
    
    def evaluate_solution_quality(self, solution) -> Dict:
        """
        Evaluiert die Qualität einer Schedule-Lösung
        
        Args:
            solution: Das Schedule-Objekt
            
        Returns:
            Dictionary mit verschiedenen Qualitätsmetriken
        """
        if not solution:
            return {"error": "Keine Lösung vorhanden"}
            
        try:
            # Gesamtscore
            score = solution.get_score()
            
            # Zuweisungsstatistik
            total_tasks = len(solution.get_tasks())
            assigned_tasks = sum(1 for task in solution.get_tasks() 
                              if task.get_assigned_employee() is not None and 
                              task.get_time_slot() is not None)
            
            # Auslastungsstatistik
            employee_workload = {}
            for task in solution.get_tasks():
                if task.get_assigned_employee():
                    emp_id = task.get_assigned_employee().id
                    if emp_id not in employee_workload:
                        employee_workload[emp_id] = 0
                    employee_workload[emp_id] += task.duration
            
            avg_workload = sum(employee_workload.values()) / len(employee_workload) if employee_workload else 0
            
            # Workload-Ungleichgewicht (Standardabweichung)
            workload_deviation = 0
            if employee_workload:
                workload_deviation = (sum((load - avg_workload) ** 2 for load in employee_workload.values()) 
                                 / len(employee_workload)) ** 0.5
            
            # Feedback-basierte Metrik, falls vorhanden
            feedback_satisfaction = 0
            if hasattr(solution, 'task_feedback') and solution.task_feedback:
                feedback_values = list(solution.task_feedback.values())
                feedback_satisfaction = sum(feedback_values) / len(feedback_values) if feedback_values else 0
            
            return {
                "score": str(score),
                "total_tasks": total_tasks,
                "assigned_tasks": assigned_tasks,
                "assignment_rate": assigned_tasks / total_tasks if total_tasks > 0 else 0,
                "avg_workload": avg_workload,
                "workload_deviation": workload_deviation,
                "feedback_satisfaction": feedback_satisfaction,
                "iteration": getattr(solution, "iteration", 1)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def increment_schedule_iteration(self, schedule):
        """
        Erhöht die Iterationsnummer eines Schedules
        
        Args:
            schedule: Das Schedule-Objekt
            
        Returns:
            Schedule mit erhöhter Iteration
        """
        current_iteration = getattr(schedule, 'iteration', 1)
        schedule.iteration = current_iteration + 1
        return schedule
    
    def create_new_iteration(self, schedule, new_name=None):
        """
        Erstellt eine neue Iteration eines bestehenden Schedules
        
        Args:
            schedule: Das originale Schedule-Objekt
            new_name: Optionaler neuer Name für die Iteration
            
        Returns:
            Eine Kopie des Schedule-Objekts mit inkrementierter Iteration
        """
        # Kopie des Schedules erstellen
        new_schedule = Schedule()
        
        # Grundlegende Eigenschaften kopieren
        new_schedule.time_slots = schedule.time_slots.copy()
        new_schedule.employees = schedule.employees.copy()
        new_schedule.tasks = schedule.tasks.copy()
        
        # Feedback übernehmen
        if hasattr(schedule, 'task_feedback'):
            new_schedule.task_feedback = schedule.task_feedback.copy()
        
        # Iteration erhöhen
        current_iteration = getattr(schedule, 'iteration', 1)
        new_schedule.iteration = current_iteration + 1
        
        # Name setzen
        if new_name:
            new_schedule.name = new_name
        else:
            base_name = getattr(schedule, 'name', f"Zeitplan {datetime.now().strftime('%d.%m.%Y')}")
            new_schedule.name = f"{base_name} (Iteration {new_schedule.iteration})"
        
        return new_schedule

# Helper-Funktion für die Constraints (für externen Zugriff)
def calculate_assignment_satisfaction(task) -> int:
    """
    Berechnet den Zufriedenheitswert basierend auf dem Feedback zur konkreten Aufgabe
    
    Args:
        task: Die Aufgabe, für die der Zufriedenheitswert berechnet werden soll
        
    Returns:
        int: Zufriedenheitswert zwischen 0 und 4 (normalisierte Bewertung)
    """
    employee = task.get_assigned_employee()
    if not employee:
        return 0
    
    # Referenz zum Schedule-Objekt erhalten (über die aktuelle Solver-Instanz)
    from optapy import ConstraintInfo
    schedule = ConstraintInfo.GLOBAL_CONFIG.get_current_working_solution()
    
    if not schedule or not hasattr(schedule, 'task_feedback'):
        return 0
    
    # Schlüssel für die Aufgabe-Mitarbeiter-Kombination
    key = (task.id, employee.id)
    
    # Bewertung für diese spezifische Zuweisung verwenden (oder 3 als neutral)
    rating = schedule.task_feedback.get(key, 3)
    
    # Normalisieren auf 0-4 (1 wird zu 0, 5 wird zu 4)
    return rating - 1