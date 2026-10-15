from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import sqlite3
import traceback

from database.db_base import DBBaseManager
from core import Employee, Task

class ScheduleRelationManager(DBBaseManager):
    """
    Manager-Klasse für die Verwaltung der Beziehungen zwischen Schedules, Mitarbeitern und Aufgaben.
    Verwaltet die Zugehörigkeit von Mitarbeitern und Aufgaben zu einem Zeitplan.
    """
    
    def save_schedule_employees(self, schedule_id: str, employees: List[Employee]) -> bool:
        """
        Speichert die Mitarbeiter-Zuordnungen für einen Zeitplan.
        
        Args:
            schedule_id: ID des Zeitplans
            employees: Liste der Mitarbeiter
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.isolation_level = None
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()
            
            # Bestehende Zuordnungen löschen
            cursor.execute('DELETE FROM schedule_employees WHERE schedule_id = ?', (schedule_id,))
            
            # Neue Zuordnungen speichern
            for employee in employees:
                # Eindeutige ID für die Zuordnung generieren
                relation_id = self.generate_id("se_rel")
                
                # Max/Min Stunden extrahieren, falls vorhanden
                max_daily_hours = getattr(employee, 'max_daily_hours', 8)
                min_daily_hours = getattr(employee, 'min_daily_hours', 4)
                
                cursor.execute('''
                INSERT INTO schedule_employees 
                (id, schedule_id, employee_id, status, max_daily_hours, min_daily_hours, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    relation_id,
                    schedule_id,
                    employee.id,
                    employee.status.value,
                    max_daily_hours,
                    min_daily_hours,
                    ""  # Keine Notizen standardmäßig
                ))
            
            conn.execute("COMMIT")
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Schedule-Employees: {str(e)}")
            traceback.print_exc()
            if conn:
                try:
                    conn.execute("ROLLBACK")
                except Exception as rollback_error:
                    print(f"Fehler beim Rollback: {rollback_error}")
            return False
        finally:
            if conn:
                conn.close()
    
    def save_schedule_tasks(self, schedule_id: str, tasks: List[Task]) -> bool:
        """
        Speichert die Aufgaben-Zuordnungen für einen Zeitplan.
        
        Args:
            schedule_id: ID des Zeitplans
            tasks: Liste der Aufgaben
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.isolation_level = None
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()
            
            # Bestehende Zuordnungen löschen
            cursor.execute('DELETE FROM schedule_tasks WHERE schedule_id = ?', (schedule_id,))
            
            # Neue Zuordnungen speichern
            for task in tasks:
                # Eindeutige ID für die Zuordnung generieren
                relation_id = self.generate_id("st_rel")
                
                # Priorität und Status extrahieren, falls vorhanden
                priority = getattr(task, 'priority', "medium")
                status = getattr(task, 'status', "open")
                
                cursor.execute('''
                INSERT INTO schedule_tasks 
                (id, schedule_id, task_id, priority, status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    relation_id,
                    schedule_id,
                    task.id,
                    priority,
                    status,
                    ""  # Keine Notizen standardmäßig
                ))
            
            conn.execute("COMMIT")
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Schedule-Tasks: {str(e)}")
            traceback.print_exc()
            if conn:
                try:
                    conn.execute("ROLLBACK")
                except Exception as rollback_error:
                    print(f"Fehler beim Rollback: {rollback_error}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_schedule_employees(self, schedule_id: str) -> List[Tuple]:
        """
        Gibt alle Mitarbeiter eines Zeitplans zurück.
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            Liste von Tupeln mit Mitarbeiter-Daten (relation_id, employee_id, name, status, max_daily_hours, min_daily_hours)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT se.id, se.employee_id, e.name, se.status, 
                       se.max_daily_hours, se.min_daily_hours
                FROM schedule_employees se
                JOIN employees e ON se.employee_id = e.id
                WHERE se.schedule_id = ?
                ORDER BY e.name
                ''', (schedule_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen der Schedule-Mitarbeiter: {e}")
            traceback.print_exc()
            return []
    
    def get_schedule_tasks(self, schedule_id: str) -> List[Tuple]:
        """
        Gibt alle Aufgaben eines Zeitplans zurück.
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            Liste von Tupeln mit Aufgaben-Daten (relation_id, task_id, name, duration, priority, status)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT st.id, st.task_id, t.name, t.duration, st.priority, st.status
                FROM schedule_tasks st
                JOIN tasks t ON st.task_id = t.id
                WHERE st.schedule_id = ?
                ORDER BY st.priority, t.name
                ''', (schedule_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen der Schedule-Aufgaben: {e}")
            traceback.print_exc()
            return []
    
    def load_schedule_employees(self, schedule_id: str, employee_manager) -> List[Employee]:
        """
        Lädt alle Mitarbeiter eines Zeitplans als vollständige Objekte.
        
        Args:
            schedule_id: ID des Zeitplans
            employee_manager: Eine Instanz des EmployeeManager für das Laden der vollständigen Mitarbeiter
            
        Returns:
            Liste von Employee-Objekten
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT employee_id
                FROM schedule_employees
                WHERE schedule_id = ?
                ''', (schedule_id,))
                
                employee_ids = [emp_id for (emp_id,) in cursor.fetchall()]
                
                # Mitarbeiter-Objekte laden
                employees = []
                for emp_id in employee_ids:
                    employee = employee_manager.load_employee(emp_id)
                    if employee:
                        employees.append(employee)
                
                return employees
        except Exception as e:
            print(f"Fehler beim Laden der Schedule-Mitarbeiter: {e}")
            traceback.print_exc()
            return []
    
    def load_schedule_tasks(self, schedule_id: str, task_manager) -> List[Task]:
        """
        Lädt alle Aufgaben eines Zeitplans als vollständige Objekte.
        
        Args:
            schedule_id: ID des Zeitplans
            task_manager: Eine Instanz des TaskManager für das Laden der vollständigen Aufgaben
            
        Returns:
            Liste von Task-Objekten
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT task_id
                FROM schedule_tasks
                WHERE schedule_id = ?
                ''', (schedule_id,))
                
                task_ids = [task_id for (task_id,) in cursor.fetchall()]
                
                # Aufgaben-Objekte laden
                tasks = []
                for task_id in task_ids:
                    task = task_manager.load_task(task_id)
                    if task:
                        tasks.append(task)
                
                return tasks
        except Exception as e:
            print(f"Fehler beim Laden der Schedule-Aufgaben: {e}")
            traceback.print_exc()
            return []
    
    def delete_schedule_relations(self, schedule_id: str) -> bool:
        """
        Löscht alle Mitarbeiter- und Aufgaben-Zuordnungen eines Zeitplans.
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.isolation_level = None
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()
            
            # Schedule-Mitarbeiter-Zuordnungen löschen
            cursor.execute('DELETE FROM schedule_employees WHERE schedule_id = ?', (schedule_id,))
            
            # Schedule-Aufgaben-Zuordnungen löschen
            cursor.execute('DELETE FROM schedule_tasks WHERE schedule_id = ?', (schedule_id,))
            
            conn.execute("COMMIT")
            return True
        except Exception as e:
            print(f"Fehler beim Löschen der Schedule-Zuordnungen: {e}")
            traceback.print_exc()
            if conn:
                try:
                    conn.execute("ROLLBACK")
                except Exception as rollback_error:
                    print(f"Fehler beim Rollback: {rollback_error}")
            return False
        finally:
            if conn:
                conn.close()