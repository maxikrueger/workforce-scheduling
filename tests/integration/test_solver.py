"""
Integration-Tests für den Solver
Testet die End-to-End-Solver-Funktionalität
"""
import pytest
from services.schedule_service import SchedulerService
from core import Employee, EmployeeStatus, Schedule, Task


class TestSolverIntegration:
    """Integration-Tests für den gesamten Solver-Workflow"""

    @pytest.fixture
    def scheduler_service(self):
        """Erstellt eine SchedulerService-Instanz"""
        return SchedulerService()

    def test_simple_testcase_generation(self, scheduler_service):
        """Testet die Generierung eines einfachen Testfalls"""
        schedule = scheduler_service.generate_test_case('simple')

        assert schedule is not None
        assert isinstance(schedule, Schedule)
        assert len(schedule.employees) > 0
        assert len(schedule.tasks) > 0
        assert len(schedule.time_slots) > 0

    def test_solver_run_simple(self, scheduler_service):
        """Testet einen kompletten Solver-Run mit einfachem Testfall"""
        # Testfall generieren
        schedule = scheduler_service.generate_test_case('simple')

        # Solver ausführen
        solution = scheduler_service.run_scheduler(schedule, 'simple')

        # Validieren
        assert solution is not None
        assert solution.get_score() is not None

        # Prüfen ob Aufgaben zugewiesen wurden
        assigned_tasks = [t for t in solution.get_tasks()
                         if t.get_assigned_employee() is not None
                         and t.get_time_slot() is not None]

        assert len(assigned_tasks) > 0, "Mindestens eine Aufgabe sollte zugewiesen sein"

    @pytest.mark.slow
    def test_solver_run_complex(self, scheduler_service):
        """Testet Solver mit komplexem Testfall (dauert länger)"""
        schedule = scheduler_service.generate_test_case('complex')
        solution = scheduler_service.run_scheduler(schedule, 'complex')

        assert solution is not None
        assert solution.get_score() is not None

    def test_custom_time_limit(self, scheduler_service, sample_schedule):
        """Testet benutzerdefin iertes Zeitlimit"""
        # Sehr kurzes Zeitlimit (5 Sekunden)
        solution = scheduler_service.run_scheduler(
            sample_schedule,
            'simple',
            custom_time_limit=5
        )

        assert solution is not None
        # Solver sollte auch mit kurzem Zeitlimit eine Lösung finden
        assert solution.get_score() is not None


# Marker für langsame Tests (werden mit pytest -m "not slow" übersprungen)
pytest.mark.slow = pytest.mark.skipif(
    "not config.getoption('--run-slow')",
    reason="Nur mit --run-slow Flag ausführen"
)


class TestFeedbackOptimization:
    """Tests für die Berücksichtigung von Mitarbeiter-Feedback"""

    @pytest.mark.parametrize("rejected, expected", [("emp1", "emp2"), ("emp2", "emp1")])
    def test_negative_feedback_moves_task_to_other_employee(self, sample_timeslots, rejected, expected):
        """'Lieber nicht' führt dazu, dass die Aufgabe einem anderen Mitarbeiter zugewiesen wird"""
        schedule = Schedule()
        schedule.time_slots = sample_timeslots
        schedule.employees = [
            Employee("emp1", "Alice", {"python"}, EmployeeStatus.AVAILABLE),
            Employee("emp2", "Bob", {"python"}, EmployeeStatus.AVAILABLE),
        ]
        schedule.tasks = [Task("task1", 1, {"python"})]
        schedule.task_feedback = {("task1", rejected): -1}

        solution = SchedulerService().run_scheduler_with_feedback(schedule, "simple")

        task = solution.get_tasks()[0]
        assert task.get_assigned_employee().id == expected
