from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import traceback

from database.db_base import DBBaseManager
from database.db_schedule_base import ScheduleBaseManager
from database.db_timeslot import TimeSlotManager
from database.db_schedule_relation import ScheduleRelationManager
from database.db_assignments import AssignmentManager

from core import Schedule

class ScheduleOperationsManager(DBBaseManager):
    """
    Manager-Klasse für die Integration aller Schedule-bezogenen Operationen.
    Orchestriert das Zusammenspiel der verschiedenen spezialisierten Manager.
    """
    
    def __init__(self, db_name: str = "workforce_scheduling.db", 
                employee_manager=None, task_manager=None):
        """
        Initialisiert den ScheduleOperationsManager.
        
        Args:
            db_name: Name der Datenbankdatei
            employee_manager: Optionale Instanz eines EmployeeManager
            task_manager: Optionale Instanz eines TaskManager
        """
        super().__init__(db_name)
        
        # Spezialisierte Manager erstellen
        self.schedule_base_manager = ScheduleBaseManager(db_name)
        self.timeslot_manager = TimeSlotManager(db_name)
        self.schedule_relation_manager = ScheduleRelationManager(db_name)
        self.assignment_manager = AssignmentManager(db_name)
        
        # Referenzen auf externe Manager
        self.employee_manager = employee_manager
        self.task_manager = task_manager
    
    def save_schedule(self, schedule: Schedule, name: str = "", description: str = "") -> Optional[str]:
        """
        Speichert einen vollständigen Zeitplan mit allen Abhängigkeiten.
        
        Args:
            schedule: Das zu speichernde Schedule-Objekt
            name: Name für den Zeitplan (falls nicht vorhanden)
            description: Beschreibung des Zeitplans
            
        Returns:
            ID des gespeicherten Schedules oder None bei Fehler
        """
        try:
            # 1. Basis-Schedule speichern
            schedule_id = self.schedule_base_manager.save_schedule_base(schedule, name, description)
            if not schedule_id:
                print("Fehler: Konnte Schedule-Basisdaten nicht speichern")
                return None
            
            # ID im Objekt setzen, falls noch nicht geschehen
            if not hasattr(schedule, 'id') or not schedule.id:
                schedule.id = schedule_id
            
            # Mitarbeiter und Aufgaben selbst anlegen bzw. aktualisieren, damit die
            # Zuordnungstabellen gültige Fremdschlüssel haben (z. B. bei generierten Testfällen)
            if self.employee_manager:
                for employee in schedule.employees or []:
                    self.employee_manager.save_employee(employee)
            if self.task_manager:
                for task in schedule.tasks or []:
                    self.task_manager.save_task(task)

            # 2. TimeSlots speichern
            if schedule.time_slots and not self.timeslot_manager.save_time_slots(schedule_id, schedule.time_slots):
                print("Fehler bei Speicherung der TimeSlots")
                # Trotzdem fortsetzen, um wenigstens Teile zu speichern
            
            # 3. Mitarbeiter-Zuordnungen speichern
            if schedule.employees and not self.schedule_relation_manager.save_schedule_employees(schedule_id, schedule.employees):
                print("Fehler bei Speicherung der Mitarbeiter-Beziehungen")
                # Trotzdem fortsetzen
            
            # 4. Aufgaben-Zuordnungen speichern
            if schedule.tasks and not self.schedule_relation_manager.save_schedule_tasks(schedule_id, schedule.tasks):
                print("Fehler bei Speicherung der Aufgaben-Beziehungen")
                # Trotzdem fortsetzen
            
            # 5. Assignments (konkrete Zuweisungen) speichern
            if schedule.tasks:
                assignment_count = self.assignment_manager.save_assignments(schedule_id, schedule)
                print(f"Assignments gespeichert: {assignment_count}")
            
            return schedule_id
            
        except Exception as e:
            print(f"Fehler beim Speichern des kompletten Schedules: {str(e)}")
            traceback.print_exc()
            return None
    
    def load_schedule(self, schedule_id: str, load_employees: bool = True, load_tasks: bool = True) -> Optional[Schedule]:
        """
        Lädt einen vollständigen Zeitplan mit allen Abhängigkeiten.
        
        Args:
            schedule_id: ID des zu ladenden Zeitplans
            load_employees: Wenn True, werden Mitarbeiter-Objekte geladen
            load_tasks: Wenn True, werden Aufgaben-Objekte geladen
            
        Returns:
            Schedule-Objekt oder None bei Fehler
        """
        try:
            # 1. Basis-Schedule laden
            schedule = self.schedule_base_manager.load_schedule_base(schedule_id)
            if not schedule:
                print(f"Fehler: Konnte Schedule mit ID {schedule_id} nicht laden")
                return None
            
            # 2. TimeSlots laden
            time_slots = self.timeslot_manager.load_time_slots(schedule_id)
            schedule.time_slots = time_slots
            print(f"Geladene TimeSlots: {len(time_slots)}")
            
            # 3. Prüfen, ob die erforderlichen Manager verfügbar sind
            if (load_employees and not self.employee_manager) or (load_tasks and not self.task_manager):
                print("Warnung: Erforderliche Manager fehlen. Mitarbeiter und/oder Aufgaben können nicht geladen werden.")
                load_employees = load_employees and self.employee_manager is not None
                load_tasks = load_tasks and self.task_manager is not None
            
            # 4. Mitarbeiter laden
            if load_employees and self.employee_manager:
                employees = self.schedule_relation_manager.load_schedule_employees(
                    schedule_id, self.employee_manager
                )
                schedule.employees = employees
                print(f"Geladene Mitarbeiter: {len(employees)}")
            
            # 5. Aufgaben laden
            if load_tasks and self.task_manager:
                tasks = self.schedule_relation_manager.load_schedule_tasks(
                    schedule_id, self.task_manager
                )
                schedule.tasks = tasks
                print(f"Geladene Aufgaben: {len(tasks)}")
            
            # 6. Assignments (Zuweisungen) laden und anwenden
            if load_employees and load_tasks and schedule.employees and schedule.tasks:
                # Dictionaries für schnellen Zugriff erstellen
                tasks_dict = {task.id: task for task in schedule.tasks}
                employees_dict = {emp.id: emp for emp in schedule.employees}
                timeslots_dict = {slot.id: slot for slot in schedule.time_slots}
                
                # Assignments abfragen
                assignments = self.assignment_manager.get_assignments(schedule_id)
                
                # Assignments auf das Schedule-Objekt anwenden
                self.assignment_manager.apply_assignments_to_schedule(
                    schedule, assignments, tasks_dict, employees_dict, timeslots_dict
                )
                
                print(f"Angewendete Assignments: {len(assignments)}")
            
            return schedule
            
        except Exception as e:
            print(f"Fehler beim Laden des kompletten Schedules: {str(e)}")
            traceback.print_exc()
            return None
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Löscht einen Zeitplan und alle zugehörigen Daten.
        
        Args:
            schedule_id: ID des zu löschenden Zeitplans
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Alle Zuweisungen löschen
            self.assignment_manager.delete_assignments(schedule_id)
            
            # Schedule-Beziehungen löschen
            self.schedule_relation_manager.delete_schedule_relations(schedule_id)
            
            # TimeSlots löschen
            self.timeslot_manager.delete_time_slots(schedule_id)
            
            # Schedule-Basis löschen
            return self.schedule_base_manager.delete_schedule_base(schedule_id)
        except Exception as e:
            print(f"Fehler beim Löschen des Schedules: {str(e)}")
            traceback.print_exc()
            return False
    
    def load_all_schedules(self, load_details: bool = False) -> List[Schedule]:
        """
        Lädt alle Zeitpläne aus der Datenbank.
        
        Args:
            load_details: Wenn True, werden auch Mitarbeiter und Aufgaben geladen
            
        Returns:
            Liste von Schedule-Objekten
        """
        schedules = []
        try:
            # Alle Schedule-IDs laden
            schedule_data = self.schedule_base_manager.get_all_schedules()
            
            for schedule_id, *_ in schedule_data:
                # Jeden Schedule laden
                schedule = self.load_schedule(
                    schedule_id, 
                    load_employees=load_details, 
                    load_tasks=load_details
                )
                if schedule:
                    schedules.append(schedule)
            
            return schedules
        except Exception as e:
            print(f"Fehler beim Laden aller Schedules: {str(e)}")
            traceback.print_exc()
            return []
    
    def copy_schedule(self, schedule_id: str, new_name: str = "") -> Optional[str]:
        """
        Erstellt eine Kopie eines bestehenden Zeitplans.
        
        Args:
            schedule_id: ID des zu kopierenden Zeitplans
            new_name: Optionaler Name für den neuen Zeitplan
            
        Returns:
            ID des neuen Zeitplans oder None bei Fehler
        """
        try:
            # Originalen Zeitplan komplett laden
            original_schedule = self.load_schedule(schedule_id, True, True)
            if not original_schedule:
                print(f"Fehler: Konnte Schedule mit ID {schedule_id} nicht laden")
                return None
            
            # Name des neuen Zeitplans setzen
            if not new_name:
                new_name = f"Kopie von {original_schedule.name} ({datetime.now().strftime('%d.%m.%Y')})"
            
            # ID zurücksetzen für Neuanlage
            original_id = original_schedule.id
            original_schedule.id = None
            
            # Neue TimeSlot-IDs generieren
            for slot in original_schedule.time_slots:
                slot.id = self.generate_id("slot")
            
            # Zeitplan speichern (generiert neue IDs für Assignments)
            new_id = self.save_schedule(original_schedule, new_name)
            
            if new_id:
                print(f"Schedule erfolgreich kopiert: {original_id} -> {new_id}")
            
            return new_id
            
        except Exception as e:
            print(f"Fehler beim Kopieren des Schedules: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_schedule_summary(self, schedule_id: str) -> Dict[str, Any]:
        """
        Erstellt eine Zusammenfassung eines Zeitplans ohne alle Details zu laden.
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            Dictionary mit Zusammenfassungsdaten
        """
        try:
            # Basis-Daten laden
            schedule_data = next((s for s in self.schedule_base_manager.get_all_schedules() 
                                if s[0] == schedule_id), None)
            
            if not schedule_data:
                return {}
            
            # Daten aus dem Tupel extrahieren
            _, name, start_date, end_date, status, description = schedule_data
            
            # Anzahlen ermitteln
            timeslot_count = self.timeslot_manager.count_time_slots(schedule_id)
            assignment_count = self.assignment_manager.count_assignments(schedule_id)
            
            # Mitarbeiter- und Aufgaben-Anzahl aus den Relations ermitteln
            employee_data = self.schedule_relation_manager.get_schedule_employees(schedule_id)
            task_data = self.schedule_relation_manager.get_schedule_tasks(schedule_id)
            
            # Zusammenfassung erstellen
            return {
                "id": schedule_id,
                "name": name,
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
                "description": description,
                "timeslot_count": timeslot_count,
                "employee_count": len(employee_data),
                "task_count": len(task_data),
                "assignment_count": assignment_count
            }
            
        except Exception as e:
            print(f"Fehler beim Erstellen der Schedule-Zusammenfassung: {str(e)}")
            traceback.print_exc()
            return {}