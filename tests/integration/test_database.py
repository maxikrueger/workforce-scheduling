"""
Integrationstests für die SQLite-Persistenz (DatabaseManager)
"""
import pytest

from database.db_manager import DatabaseManager


@pytest.fixture
def db_manager(tmp_path, monkeypatch):
    """DatabaseManager mit Datenbank in einem temporären Home-Verzeichnis"""
    monkeypatch.setenv("HOME", str(tmp_path))
    return DatabaseManager()


@pytest.fixture
def assigned_schedule(sample_schedule):
    """Schedule mit festen Zuweisungen, ohne den Solver zu starten"""
    slots = sample_schedule.time_slots
    emp1, emp2, emp3 = sample_schedule.employees
    task1, task2, task3 = sample_schedule.tasks
    task1.set_assigned_employee(emp1)
    task1.set_time_slot(slots[0])
    task2.set_assigned_employee(emp2)
    task2.set_time_slot(slots[1])
    task3.set_assigned_employee(emp3)
    task3.set_time_slot(slots[2])
    return sample_schedule


class TestDatabaseManager:
    """Tests für Speichern und Laden kompletter Zeitpläne"""

    def test_save_and_load_schedule_roundtrip(self, db_manager, assigned_schedule):
        """Ein gespeicherter Zeitplan wird mit allen Zuweisungen wieder geladen"""
        schedule_id = db_manager.save_schedule(assigned_schedule, name="Testplan")
        assert schedule_id

        loaded = db_manager.load_schedule(schedule_id)

        assert len(loaded.employees) == 3
        assert len(loaded.tasks) == 3
        assert len(loaded.time_slots) == 8

        assignments = {
            t.id: (t.get_assigned_employee().id, t.get_time_slot().id)
            for t in loaded.tasks
        }
        assert assignments == {
            "task1": ("emp1", "slot_0"),
            "task2": ("emp2", "slot_1"),
            "task3": ("emp3", "slot_2"),
        }

    def test_employee_skills_are_persisted(self, db_manager, sample_employees):
        """Skills eines Mitarbeiters bleiben beim Speichern erhalten"""
        assert db_manager.save_employee(sample_employees[0])

        loaded = db_manager.load_employee("emp1")

        assert loaded.name == "Alice"
        assert loaded.skills == {"python", "java"}

    def test_feedback_is_stored_per_iteration(self, db_manager, assigned_schedule):
        """Feedback zu einer Zuweisung wird pro Iteration abgelegt"""
        schedule_id = db_manager.save_schedule(assigned_schedule, name="Testplan")

        saved = db_manager.feedback_manager.save_task_feedback(
            schedule_id, "emp1", "task1", rating=-1, comment="lieber nicht", iteration=1
        )

        assert saved
        feedback = db_manager.feedback_manager.get_task_feedback_for_schedule(schedule_id, 1)
        assert feedback == {("task1", "emp1"): -1}
