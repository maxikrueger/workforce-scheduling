from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import sqlite3
import traceback

from database.db_base import DBBaseManager
from core import Schedule, Task, Employee, TimeSlot

class AssignmentManager(DBBaseManager):
    """
    Manager-Klasse für die Verwaltung von Assignments (Zuweisungen).
    Verwaltet die konkreten Zuweisungen von Aufgaben zu Mitarbeitern in bestimmten Zeitslots.
    """
    
    def save_assignments(self, schedule_id: str, schedule: Schedule) -> int:
        """
        Speichert die Zuweisungen zwischen Mitarbeitern, Aufgaben und Zeitslots.
        
        Args:
            schedule_id: ID des Zeitplans
            schedule: Das Schedule-Objekt mit den zugewiesenen Aufgaben
            
        Returns:
            Anzahl der gespeicherten Assignments
        """
        conn = None
        assignment_count = 0
        try:
            conn = self.get_connection()
            conn.isolation_level = None
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()
            
            # Bestehende Assignments löschen
            cursor.execute('DELETE FROM assignments WHERE schedule_id = ?', (schedule_id,))
            
            # Neue Assignments speichern
            for task in schedule.tasks:
                # Nur Aufgaben mit Zuweisung berücksichtigen
                if hasattr(task, 'get_assigned_employee') and hasattr(task, 'get_time_slot'):
                    employee = task.get_assigned_employee()
                    time_slot = task.get_time_slot()
                    
                    if employee is not None and time_slot is not None:
                        # Eindeutige ID für das Assignment generieren
                        assignment_id = self.generate_id("asgn")
                        
                        cursor.execute('''
                        INSERT INTO assignments 
                        (id, schedule_id, task_id, employee_id, timeslot_id, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            assignment_id,
                            schedule_id,
                            task.id,
                            employee.id,
                            time_slot.id,
                            "planned"  # Standardstatus
                        ))
                        assignment_count += 1
            
            conn.execute("COMMIT")
            return assignment_count
        except Exception as e:
            print(f"Fehler beim Speichern der Assignments: {str(e)}")
            traceback.print_exc()
            if conn:
                try:
                    conn.execute("ROLLBACK")
                except Exception as rollback_error:
                    print(f"Fehler beim Rollback: {rollback_error}")
            return 0
        finally:
            if conn:
                conn.close()
    
    def get_assignments(self, schedule_id: str) -> List[Tuple]:
        """
        Gibt alle Zuweisungen eines Zeitplans zurück.
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            Liste von Tupeln mit Assignment-Daten
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT a.id, a.task_id, a.employee_id, a.timeslot_id, a.status,
                       e.name as employee_name, t.name as task_name, 
                       ts.start_time, ts.end_time
                FROM assignments a
                JOIN employees e ON a.employee_id = e.id
                JOIN tasks t ON a.task_id = t.id
                JOIN timeslots ts ON a.timeslot_id = ts.id
                WHERE a.schedule_id = ?
                ORDER BY ts.start_time
                ''', (schedule_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen der Zuweisungen: {e}")
            traceback.print_exc()
            return []
    
    def apply_assignments_to_schedule(self, schedule: Schedule, assignments: List[Tuple],
                                    tasks_dict: Dict[str, Task], 
                                    employees_dict: Dict[str, Employee],
                                    timeslots_dict: Dict[str, TimeSlot]) -> None:
        """
        Wendet Zuweisungen auf ein Schedule-Objekt an (setzt die entsprechenden Beziehungen).
        
        Args:
            schedule: Das Schedule-Objekt, auf das die Zuweisungen angewendet werden sollen
            assignments: Liste von Assignment-Tupeln (task_id, employee_id, timeslot_id)
            tasks_dict: Dictionary zur Zuordnung von Task-IDs zu Task-Objekten
            employees_dict: Dictionary zur Zuordnung von Employee-IDs zu Employee-Objekten
            timeslots_dict: Dictionary zur Zuordnung von TimeSlot-IDs zu TimeSlot-Objekten
        """
        try:
            # Zuweisungen auf das Schedule-Objekt anwenden
            for assignment in assignments:
                task_id = assignment[1]  # task_id ist das zweite Element
                employee_id = assignment[2]  # employee_id ist das dritte Element
                timeslot_id = assignment[3]  # timeslot_id ist das vierte Element
                
                # Prüfen, ob alle benötigten Objekte vorhanden sind
                if (task_id in tasks_dict and 
                    employee_id in employees_dict and 
                    timeslot_id in timeslots_dict):
                    
                    task = tasks_dict[task_id]
                    employee = employees_dict[employee_id]
                    timeslot = timeslots_dict[timeslot_id]
                    
                    # Zuweisungen setzen, falls die Methoden vorhanden sind
                    if hasattr(task, 'set_assigned_employee'):
                        task.set_assigned_employee(employee)
                    
                    if hasattr(task, 'set_time_slot'):
                        task.set_time_slot(timeslot)
        except Exception as e:
            print(f"Fehler beim Anwenden der Zuweisungen: {e}")
            traceback.print_exc()
    
    def count_assignments(self, schedule_id: str) -> int:
        """
        Zählt die Anzahl der Zuweisungen eines Zeitplans.
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            Anzahl der Zuweisungen
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM assignments WHERE schedule_id = ?', (schedule_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Fehler beim Zählen der Zuweisungen: {e}")
            return 0
    
    def delete_assignments(self, schedule_id: str) -> bool:
        """
        Löscht alle Zuweisungen eines Zeitplans.
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM assignments WHERE schedule_id = ?', (schedule_id,))
                return True
        except Exception as e:
            print(f"Fehler beim Löschen der Zuweisungen: {e}")
            return False
    
    def update_assignment_status(self, assignment_id: str, status: str) -> bool:
        """
        Aktualisiert den Status einer Zuweisung.
        
        Args:
            assignment_id: ID der Zuweisung
            status: Neuer Status
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE assignments 
                SET status = ?
                WHERE id = ?
                ''', (status, assignment_id))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Assignment-Status: {e}")
            return False
    
    def get_employee_assignments(self, schedule_id: str, employee_id: str) -> List[Tuple]:
        """
        Gibt alle Zuweisungen eines Mitarbeiters für einen Zeitplan zurück.
        
        Args:
            schedule_id: ID des Zeitplans
            employee_id: ID des Mitarbeiters
            
        Returns:
            Liste von Tupeln mit Assignment-Daten
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT a.id, a.task_id, a.employee_id, a.timeslot_id, a.status,
                       t.name as task_name, ts.start_time
                FROM assignments a
                JOIN tasks t ON a.task_id = t.id
                JOIN timeslots ts ON a.timeslot_id = ts.id
                WHERE a.schedule_id = ? AND a.employee_id = ?
                ORDER BY ts.start_time
                ''', (schedule_id, employee_id))
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen der Mitarbeiter-Zuweisungen: {e}")
            return []
    
    def get_task_assignment(self, schedule_id: str, task_id: str) -> Optional[Tuple]:
        """
        Gibt die Zuweisung einer Aufgabe für einen Zeitplan zurück.
        
        Args:
            schedule_id: ID des Zeitplans
            task_id: ID der Aufgabe
            
        Returns:
            Tupel mit Assignment-Daten oder None, wenn keine Zuweisung existiert
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT a.id, a.employee_id, a.timeslot_id, a.status,
                       e.name as employee_name, ts.start_time
                FROM assignments a
                JOIN employees e ON a.employee_id = e.id
                JOIN timeslots ts ON a.timeslot_id = ts.id
                WHERE a.schedule_id = ? AND a.task_id = ?
                ''', (schedule_id, task_id))
                return cursor.fetchone()
        except Exception as e:
            print(f"Fehler beim Abrufen der Aufgaben-Zuweisung: {e}")
            return None