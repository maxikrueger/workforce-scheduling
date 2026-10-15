"""
Unit-Tests für core.py - Domänenmodell und Basis-Funktionen
"""
import pytest
from datetime import datetime, timedelta
from core import (
    Employee,
    Task,
    TimeSlot,
    Schedule,
    EmployeeStatus,
    has_required_skills,
    check_time_overlap,
    is_within_working_hours,
    extends_beyond_working_hours
)


class TestEmployee:
    """Tests für die Employee-Klasse"""

    def test_employee_creation(self):
        """Testet das Erstellen eines Mitarbeiters"""
        emp = Employee("e1", "Test User", {"python", "java"})
        assert emp.id == "e1"
        assert emp.name == "Test User"
        assert emp.skills == {"python", "java"}
        assert emp.status == EmployeeStatus.AVAILABLE

    def test_has_skill(self, simple_employee):
        """Testet die has_skill Methode"""
        assert simple_employee.has_skill("python")
        assert simple_employee.has_skill("testing")
        assert not simple_employee.has_skill("java")

    def test_is_available(self):
        """Testet die is_available Methode"""
        emp_available = Employee("e1", "Available", {"python"}, EmployeeStatus.AVAILABLE)
        emp_busy = Employee("e2", "Busy", {"python"}, EmployeeStatus.BUSY)
        emp_off = Employee("e3", "Off", {"python"}, EmployeeStatus.OFF)

        assert emp_available.is_available()
        assert not emp_busy.is_available()
        assert not emp_off.is_available()


class TestTask:
    """Tests für die Task-Klasse"""

    def test_task_creation(self):
        """Testet das Erstellen einer Aufgabe"""
        task = Task("t1", 2, {"python", "sql"})
        assert task.id == "t1"
        assert task.duration == 2
        assert task.required_skills == {"python", "sql"}
        assert task.get_time_slot() is None
        assert task.get_assigned_employee() is None

    def test_task_assignment(self, simple_task, simple_employee, timeslot_morning):
        """Testet die Zuweisung von Mitarbeiter und Zeitslot"""
        simple_task.set_assigned_employee(simple_employee)
        simple_task.set_time_slot(timeslot_morning)

        assert simple_task.get_assigned_employee() == simple_employee
        assert simple_task.get_time_slot() == timeslot_morning


class TestTimeSlot:
    """Tests für die TimeSlot-Klasse"""

    def test_timeslot_creation(self):
        """Testet das Erstellen eines Zeitslots"""
        start_time = datetime(2026, 3, 17, 9, 0)
        slot = TimeSlot("slot1", start_time)
        assert slot.id == "slot1"
        assert slot.start_time == start_time


class TestSchedule:
    """Tests für die Schedule-Klasse"""

    def test_schedule_creation(self):
        """Testet das Erstellen eines Schedules"""
        schedule = Schedule()
        assert schedule.time_slots == []
        assert schedule.employees == []
        assert schedule.tasks == []
        assert schedule._score is None

    def test_schedule_with_data(self, sample_schedule):
        """Testet Schedule mit Beispieldaten"""
        assert len(sample_schedule.time_slots) == 8
        assert len(sample_schedule.employees) == 3
        assert len(sample_schedule.tasks) == 3


class TestConstraintHelpers:
    """Tests für Constraint-Hilfsfunktionen"""

    def test_has_required_skills_success(self):
        """Testet has_required_skills bei vorhandenen Skills"""
        emp = Employee("e1", "Dev", {"python", "java", "sql"})
        assert has_required_skills(emp, {"python"})
        assert has_required_skills(emp, {"python", "java"})
        assert has_required_skills(emp, {"python", "java", "sql"})

    def test_has_required_skills_failure(self):
        """Testet has_required_skills bei fehlenden Skills"""
        emp = Employee("e1", "Dev", {"python"})
        assert not has_required_skills(emp, {"java"})
        assert not has_required_skills(emp, {"python", "java"})

    def test_has_required_skills_empty(self):
        """Testet has_required_skills mit leeren Skills"""
        emp = Employee("e1", "Dev", {"python"})
        assert has_required_skills(emp, set())

    def test_check_time_overlap_overlapping(self):
        """Testet Überlappungserkennung bei sich überschneidenden Aufgaben"""
        task1 = Task("t1", 2, {"python"})  # 9:00-11:00
        task2 = Task("t2", 2, {"python"})  # 10:00-12:00

        task1.set_time_slot(TimeSlot("s1", datetime(2026, 3, 17, 9, 0)))
        task2.set_time_slot(TimeSlot("s2", datetime(2026, 3, 17, 10, 0)))

        assert check_time_overlap(task1, task2)

    def test_check_time_overlap_non_overlapping(self):
        """Testet Überlappungserkennung bei nicht überlappenden Aufgaben"""
        task1 = Task("t1", 2, {"python"})  # 9:00-11:00
        task2 = Task("t2", 2, {"python"})  # 11:00-13:00

        task1.set_time_slot(TimeSlot("s1", datetime(2026, 3, 17, 9, 0)))
        task2.set_time_slot(TimeSlot("s2", datetime(2026, 3, 17, 11, 0)))

        assert not check_time_overlap(task1, task2)

    def test_check_time_overlap_none_values(self):
        """Testet Überlappungserkennung mit None-Werten"""
        task1 = Task("t1", 2, {"python"})
        task2 = Task("t2", 2, {"python"})

        # Keine Zeitslots zugewiesen
        assert not check_time_overlap(task1, task2)

    def test_is_within_working_hours_valid(self):
        """Testet is_within_working_hours für gültige Zeiten"""
        task = Task("t1", 2, {"python"})

        # 8:00, 10:00, 14:00 - alle innerhalb 8-16 Uhr
        for hour in [8, 10, 14]:
            task.set_time_slot(TimeSlot("s1", datetime(2026, 3, 17, hour, 0)))
            assert is_within_working_hours(task)

    def test_is_within_working_hours_invalid(self):
        """Testet is_within_working_hours für ungültige Zeiten"""
        task = Task("t1", 2, {"python"})

        # 7:00, 16:00, 18:00 - außerhalb 8-16 Uhr
        for hour in [7, 16, 18]:
            task.set_time_slot(TimeSlot("s1", datetime(2026, 3, 17, hour, 0)))
            assert not is_within_working_hours(task)

    def test_extends_beyond_working_hours_yes(self):
        """Testet extends_beyond_working_hours für überschreitende Aufgaben"""
        task = Task("t1", 3, {"python"})  # 3 Stunden
        task.set_time_slot(TimeSlot("s1", datetime(2026, 3, 17, 14, 0)))  # 14:00-17:00

        # Endet um 17:00 -> über 16:00 hinaus
        assert extends_beyond_working_hours(task)

    def test_extends_beyond_working_hours_no(self):
        """Testet extends_beyond_working_hours für nicht überschreitende Aufgaben"""
        task = Task("t1", 2, {"python"})  # 2 Stunden
        task.set_time_slot(TimeSlot("s1", datetime(2026, 3, 17, 10, 0)))  # 10:00-12:00

        # Endet um 12:00 -> innerhalb 8-16 Uhr
        assert not extends_beyond_working_hours(task)
