import logging
import os
import sqlite3
import traceback
from typing import List, Tuple, Dict, Any, Optional

from core import Employee, Schedule, Task, TimeSlot
from database.db_base import DBBaseManager
from database.db_skill import SkillManager
from database.db_employee import EmployeeManager
from database.db_task import TaskManager
from database.db_schedule_base import ScheduleBaseManager
from database.db_timeslot import TimeSlotManager
from database.db_schedule_relation import ScheduleRelationManager
from database.db_assignments import AssignmentManager
from database.db_schedule_operations import ScheduleOperationsManager
from database.db_feedback import FeedbackManager

class DatabaseManager:
    """
    Zentrale Datenbank-Manager-Klasse, die alle spezialisierten Manager vereint.
    Dient als Schnittstelle für die Anwendung zu allen Datenbankoperationen.
    """
    
    def __init__(self, db_name: str = "workforce_scheduling.db"):
        """
        Initialisiert den DatabaseManager und erstellt die Datenbank-Tabellen.
        
        Args:
            db_name: Name der Datenbankdatei
        """
        self.logger = logging.getLogger(__name__)

        # Bestimme den Pfad für die Datenbankdatei
        base_path = os.path.join(os.path.expanduser("~"), ".workforce_scheduling")
        os.makedirs(base_path, exist_ok=True)
        self.db_name = os.path.join(base_path, db_name)
        
        # Bestimme den Pfad für die Schema-Datei
        # Wir verwenden mehrere mögliche Pfade und nehmen den ersten, der existiert
        possible_schema_paths = [
            # Relativ zum Arbeitsverzeichnis
            "database/db_schema.sql",
            # Im gleichen Verzeichnis wie diese Datei
            os.path.join(os.path.dirname(__file__), "db_schema.sql"),
            # Eine Ebene höher im Verzeichnis "database"
            os.path.join(os.path.dirname(__file__), "../database/db_schema.sql"),
            # Absoluter Pfad zum aktuellen Verzeichnis + db_schema.sql
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_schema.sql")
        ]
        
        self.schema_file = None
        for path in possible_schema_paths:
            if os.path.exists(path):
                self.schema_file = path
                break
        
        print(f"Datenbank: {self.db_name}")
        print(f"Schema: {self.schema_file}")
        
        # Initialisiere die spezialisierten Manager
        self.skill_manager = SkillManager(self.db_name)
        self.employee_manager = EmployeeManager(self.db_name)
        self.task_manager = TaskManager(self.db_name)
        
        # Neue spezialisierte Schedule-Manager
        self.schedule_base_manager = ScheduleBaseManager(self.db_name)
        self.timeslot_manager = TimeSlotManager(self.db_name)
        self.schedule_relation_manager = ScheduleRelationManager(self.db_name)
        self.assignment_manager = AssignmentManager(self.db_name)
        
        # Der übergeordnete Schedule-Operations-Manager bekommt Zugriff auf employee_manager und task_manager
        self.schedule_operations_manager = ScheduleOperationsManager(
            self.db_name, 
            employee_manager=self.employee_manager,
            task_manager=self.task_manager
        )
        
        # Erstelle Datenbank-Tabellen, falls nötig
        self.create_tables()

        # Feedback-Manager für die iterative Nachoptimierung
        self.feedback_manager = FeedbackManager(self.db_name)
    
    def create_tables(self):
        """Erstellt alle benötigten Tabellen aus der Schema-Datei"""
        connection = None
        try:
            # Zuerst sicherstellen, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(self.db_name), exist_ok=True)
            
            # Prüfe, ob die Schema-Datei existiert
            if not self.schema_file or not os.path.exists(self.schema_file):
                print(f"Warnung: Schema-Datei nicht gefunden. Tabellen werden nicht erstellt.")
                return
                
            # Lese SQL-Befehle aus der Datei
            with open(self.schema_file, 'r', encoding='utf-8') as file:
                sql_script = file.read()
            
            # Verbindung herstellen und Schema ausführen
            connection = sqlite3.connect(self.db_name)
            connection.executescript(sql_script)
            connection.commit()
            
            print(f"Datenbank-Schema wurde erfolgreich initialisiert: {self.db_name}")
        except Exception as e:
            print(f"Fehler beim Erstellen der Tabellen: {e}")
            traceback.print_exc()
            if connection:
                try:
                    connection.rollback()
                except:
                    pass
        finally:
            if connection:
                connection.close()


    
    def execute_query(self, query: str, params: tuple = None):
        """
        Führt eine SQL-Abfrage direkt aus.
        Delegiert an DBBaseManager.
        
        Args:
            query: SQL-Abfrage
            params: Parameter für die Abfrage (optional)
            
        Returns:
            Ergebnismenge oder None bei INSERT/UPDATE/DELETE
        """
        try:
            return self.skill_manager.execute_query(query, params)
        except Exception as e:
            self.logger.error(f"Fehler beim Ausführen der Abfrage: {e}")
            return None
    
    #
    # Skill-Methoden
    #
    
    def get_or_create_skill_id(self, skill_name: str) -> str:
        """Gibt die ID eines Skills zurück oder erstellt einen neuen Skill."""
        try:
            return self.skill_manager.get_or_create_skill_id(skill_name)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen/Erstellen des Skills: {e}")
            return None
    
    def add_skill(self, name: str, id: str = None) -> str:
        """Fügt einen neuen Skill hinzu."""
        try:
            return self.skill_manager.add_skill(name, id)
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen des Skills: {e}")
            return None
    
    def get_all_skills(self) -> List[Tuple[str, str]]:
        """Gibt alle verfügbaren Skills zurück."""
        try:
            return self.skill_manager.get_all_skills()
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Skills: {e}")
            return []
    
    def get_skill(self, skill_id: str) -> Optional[Tuple[str, str]]:
        """Gibt einen Skill anhand seiner ID zurück."""
        try:
            return self.skill_manager.get_skill(skill_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Skills: {e}")
            return None
    
    def update_skill(self, skill_id: str, name: str) -> bool:
        """Aktualisiert einen Skill."""
        try:
            return self.skill_manager.update_skill(skill_id, name)
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Skills: {e}")
            return False
    
    def delete_skill(self, skill_id: str) -> bool:
        """Löscht einen Skill anhand seiner ID."""
        try:
            return self.skill_manager.delete_skill(skill_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen des Skills: {e}")
            return False
    
    def get_skills_by_names(self, skill_names: List[str]) -> List[Tuple[str, str]]:
        """Gibt Skills anhand ihrer Namen zurück."""
        try:
            return self.skill_manager.get_skills_by_names(skill_names)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Skills: {e}")
            return []
    
    #
    # Employee-Methoden
    #
    
    def save_employee(self, employee: Employee) -> bool:
        """Speichert ein Employee-Objekt in der Datenbank."""
        try:
            return self.employee_manager.save_employee(employee)
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern des Mitarbeiters: {e}")
            return False
    
    def load_employee(self, employee_id: str) -> Optional[Employee]:
        """Lädt einen Mitarbeiter aus der Datenbank."""
        try:
            return self.employee_manager.load_employee(employee_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Laden des Mitarbeiters: {e}")
            return None
    
    def get_all_employees(self) -> List[Tuple]:
        """Gibt alle Mitarbeiter als Basisdaten zurück."""
        try:
            return self.employee_manager.get_all_employees()
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen aller Mitarbeiter: {e}")
            return []
    
    def load_all_employees(self) -> List[Employee]:
        """Lädt alle Mitarbeiter als vollständige Objekte."""
        try:
            return self.employee_manager.load_all_employees()
        except Exception as e:
            self.logger.error(f"Fehler beim Laden aller Mitarbeiter: {e}")
            return []
    
    def delete_employee(self, employee_id: str) -> bool:
        """Löscht einen Mitarbeiter aus der Datenbank."""
        try:
            return self.employee_manager.delete_employee(employee_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen des Mitarbeiters: {e}")
            return False
    
    def get_employee_skills(self, employee_id: str) -> List[Tuple[str, str, bool]]:
        """Gibt alle Skills eines Mitarbeiters zurück."""
        try:
            return self.employee_manager.get_employee_skills(employee_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Mitarbeiter-Skills: {e}")
            return []
    
    def get_employee_vacations(self, employee_id: str) -> List[Tuple]:
        """Gibt alle Urlaubszeiten eines Mitarbeiters zurück."""
        try:
            return self.employee_manager.get_employee_vacations(employee_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Urlaubszeiten: {e}")
            return []
    
    #
    # Task-Methoden
    #
    
    def save_task(self, task: Task) -> bool:
        """Speichert ein Task-Objekt in der Datenbank."""
        try:
            return self.task_manager.save_task(task)
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Aufgabe: {e}")
            return False
    
    def load_task(self, task_id: str) -> Optional[Task]:
        """Lädt eine Aufgabe aus der Datenbank."""
        try:
            return self.task_manager.load_task(task_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Aufgabe: {e}")
            return None
    
    def get_all_tasks(self) -> List[Tuple]:
        """Gibt alle Aufgaben als Basisdaten zurück."""
        try:
            return self.task_manager.get_all_tasks()
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen aller Aufgaben: {e}")
            return []
    
    def load_all_tasks(self) -> List[Task]:
        """Lädt alle Aufgaben als vollständige Objekte."""
        try:
            return self.task_manager.load_all_tasks()
        except Exception as e:
            self.logger.error(f"Fehler beim Laden aller Aufgaben: {e}")
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """Löscht eine Aufgabe aus der Datenbank."""
        try:
            return self.task_manager.delete_task(task_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen der Aufgabe: {e}")
            return False
    
    def get_task_skills(self, task_id: str) -> List[Tuple[str, str]]:
        """Gibt alle benötigten Skills einer Aufgabe zurück."""
        try:
            return self.task_manager.get_task_skills(task_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Aufgaben-Skills: {e}")
            return []
    
    def get_tasks_by_skills(self, skill_ids: List[str]) -> List[Tuple]:
        """Gibt alle Aufgaben zurück, die bestimmte Skills erfordern."""
        try:
            return self.task_manager.get_tasks_by_skills(skill_ids)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Aufgaben nach Skills: {e}")
            return []
    
    def get_task_dependencies(self, task_id: str) -> List[str]:
        """Gibt alle Abhängigkeiten einer Aufgabe zurück."""
        try:
            return self.task_manager.get_task_dependencies(task_id)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Aufgaben-Abhängigkeiten: {e}")
            return []
    
    #
    # Schedule-Methoden (delegiert an die spezialisierten Manager)
    #
    
    def save_schedule(self, schedule: Schedule, name: str = "", description: str = "") -> Optional[str]:
        """Speichert einen Zeitplan mit allen Abhängigkeiten in der Datenbank."""
        try:
            return self.schedule_operations_manager.save_schedule(schedule, name, description)
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern des kompletten Schedules: {e}")
            return None
    
    def load_schedule(self, schedule_id: str, load_employees: bool = True, load_tasks: bool = True) -> Optional[Schedule]:
        """Lädt einen Zeitplan aus der Datenbank."""
        try:
            return self.schedule_operations_manager.load_schedule(schedule_id, load_employees, load_tasks)
        except Exception as e:
            self.logger.error(f"Fehler beim Laden des kompletten Schedules: {e}")
            return None
    
    def get_all_schedules(self) -> List[Tuple]:
        """Gibt alle Zeitpläne als Basisdaten zurück."""
        try:
            return self.schedule_base_manager.get_all_schedules()
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen aller Zeitpläne: {e}")
            return []
    
    def load_all_schedules(self, load_details: bool = False) -> List[Schedule]:
        """Lädt alle Zeitpläne aus der Datenbank."""
        try:
            return self.schedule_operations_manager.load_all_schedules(load_details)
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen aller Zeitpläne: {e}")
            return []
        
    def delete_schedule(self, schedule_id: str) -> bool:
        """Löscht einen Zeitplan und alle zugehörigen Daten."""
        try:
            return self.schedule_operations_manager.delete_schedule(schedule_id)
        except Exception as e:
            logging.error(f"Fehler beim Löschen des Zeitplans {schedule_id}: {e}")
            return False
    
    def save_time_slots(self, schedule_id: str, time_slots: List[TimeSlot]) -> bool:
        """Speichert Zeitslots für einen Zeitplan."""
        try:
            return self.timeslot_manager.save_time_slots(schedule_id, time_slots)
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Zeitslots für Zeitplan {schedule_id}: {e}")
            return False
    
    def load_time_slots(self, schedule_id: str) -> List[TimeSlot]:
        """Lädt alle Zeitslots eines Zeitplans."""
        try:
            return self.timeslot_manager.load_time_slots(schedule_id)
        except Exception as e:
            logging.error(f"Fehler beim Laden der Zeitslots für Zeitplan {schedule_id}: {e}")
            return []
    
    def get_assignments(self, schedule_id: str) -> List[Tuple]:
        """Gibt alle Zuweisungen eines Zeitplans zurück."""
        try:
            return self.assignment_manager.get_assignments(schedule_id)
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Zuweisungen für Zeitplan {schedule_id}: {e}")
            return []
    
    def get_schedule_employees(self, schedule_id: str) -> List[Tuple]:
        """Gibt alle Mitarbeiter eines Zeitplans zurück."""
        try:
            return self.schedule_relation_manager.get_schedule_employees(schedule_id)
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Mitarbeiter für Zeitplan {schedule_id}: {e}")
            return []
    
    def get_schedule_tasks(self, schedule_id: str) -> List[Tuple]:
        """Gibt alle Aufgaben eines Zeitplans zurück."""
        try:
            return self.schedule_relation_manager.get_schedule_tasks(schedule_id)
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Aufgaben für Zeitplan {schedule_id}: {e}")
            return []
    
    def copy_schedule(self, schedule_id: str, new_name: str = "") -> Optional[str]:
        """Erstellt eine Kopie eines bestehenden Zeitplans."""
        try:
            return self.schedule_operations_manager.copy_schedule(schedule_id, new_name)
        except Exception as e:
            logging.error(f"Fehler beim Kopieren des Zeitplans {schedule_id}: {e}")
            return None
    
    def get_schedule_summary(self, schedule_id: str) -> Dict[str, Any]:
        """Erstellt eine Zusammenfassung eines Zeitplans."""
        try:
            return self.schedule_operations_manager.get_schedule_summary(schedule_id)
        except Exception as e:
            logging.error(f"Fehler beim Erstellen der Zusammenfassung für Zeitplan {schedule_id}: {e}")
            return {}
    
    def update_schedule_status(self, schedule_id: str, status: str) -> bool:
        """Aktualisiert den Status eines Zeitplans."""
        try:
            return self.schedule_base_manager.update_schedule_status(schedule_id, status)
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren des Status für Zeitplan {schedule_id}: {e}")
            return False
