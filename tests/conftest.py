"""
Pytest Configuration und Fixtures für Workforce Scheduling Tests
"""
import pytest
from datetime import datetime, timedelta
from core import Employee, Task, TimeSlot, Schedule, EmployeeStatus


@pytest.fixture
def sample_timeslots():
    """Erstellt Beispiel-Zeitslots für Tests"""
    base_time = datetime(2026, 3, 17, 8, 0)  # Montag, 8:00 Uhr
    return [
        TimeSlot(f"slot_{i}", base_time + timedelta(hours=i))
        for i in range(8)  # 8:00 - 16:00
    ]


@pytest.fixture
def sample_employees():
    """Erstellt Beispiel-Mitarbeiter für Tests"""
    return [
        Employee("emp1", "Alice", {"python", "java"}, EmployeeStatus.AVAILABLE),
        Employee("emp2", "Bob", {"python", "javascript"}, EmployeeStatus.AVAILABLE),
        Employee("emp3", "Charlie", {"java", "sql"}, EmployeeStatus.AVAILABLE),
    ]


@pytest.fixture
def sample_tasks():
    """Erstellt Beispiel-Aufgaben für Tests"""
    return [
        Task("task1", 2, {"python"}),  # 2 Stunden, benötigt Python
        Task("task2", 1, {"javascript"}),  # 1 Stunde, benötigt JavaScript
        Task("task3", 3, {"java", "sql"}),  # 3 Stunden, benötigt Java und SQL
    ]


@pytest.fixture
def sample_schedule(sample_timeslots, sample_employees, sample_tasks):
    """Erstellt einen vollständigen Beispiel-Schedule für Tests"""
    schedule = Schedule()
    schedule.time_slots = sample_timeslots
    schedule.employees = sample_employees
    schedule.tasks = sample_tasks
    return schedule


@pytest.fixture
def simple_employee():
    """Einzelner Mitarbeiter für einfache Tests"""
    return Employee(
        "emp_simple",
        "Test User",
        {"python", "testing"},
        EmployeeStatus.AVAILABLE
    )


@pytest.fixture
def simple_task():
    """Einzelne Aufgabe für einfache Tests"""
    return Task("task_simple", 2, {"python"})


@pytest.fixture
def timeslot_morning():
    """Zeitslot am Morgen (9:00 Uhr)"""
    return TimeSlot("morning", datetime(2026, 3, 17, 9, 0))


@pytest.fixture
def timeslot_afternoon():
    """Zeitslot am Nachmittag (14:00 Uhr)"""
    return TimeSlot("afternoon", datetime(2026, 3, 17, 14, 0))


@pytest.fixture
def timeslot_late():
    """Zeitslot außerhalb der Arbeitszeit (18:00 Uhr)"""
    return TimeSlot("late", datetime(2026, 3, 17, 18, 0))
