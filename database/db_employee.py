from typing import List, Tuple, Dict, Any, Optional, Set, Union
from datetime import datetime
import json
from database.db_base import DBBaseManager
from core import Employee, EmployeeStatus

class EmployeeManager(DBBaseManager):
    """Manager-Klasse für alle Mitarbeiter-bezogenen Datenbankoperationen"""
    
    def save_employee(self, employee: Employee) -> bool:
        """
        Speichert ein Employee-Objekt in der Datenbank.
        
        Args:
            employee: Das zu speichernde Employee-Objekt
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.isolation_level = None  # Für explizite Transaktionskontrolle
            
            # Explizite Transaktion starten
            conn.execute("BEGIN TRANSACTION")
            
            cursor = conn.cursor()
            
            # Prüfen, ob der Mitarbeiter bereits existiert
            cursor.execute('SELECT id FROM employees WHERE id = ?', (employee.id,))
            existing = cursor.fetchone()
            
            # Attribute mit Standardwerten abrufen
            max_weekly_hours = getattr(employee, 'max_weekly_hours', 40)
            min_daily_hours = getattr(employee, 'min_daily_hours', 4)
            max_daily_hours = getattr(employee, 'max_daily_hours', 10)
            
            # E-Mail generieren, falls nicht vorhanden
            email = getattr(employee, 'email', 
                        f"{employee.name.lower().replace(' ', '.')}@example.com")
            
            # Rolle festlegen (Standard: 'employee')
            role = getattr(employee, 'role', 'employee')
            
            if existing:
                # Update des bestehenden Mitarbeiters
                cursor.execute('''
                UPDATE employees 
                SET name = ?, email = ?, role = ?, status = ?, 
                    max_weekly_hours = ?, min_daily_hours = ?, max_daily_hours = ?
                WHERE id = ?
                ''', (
                    employee.name, 
                    email,
                    role,
                    employee.status.value,
                    max_weekly_hours,
                    min_daily_hours, 
                    max_daily_hours,
                    employee.id
                ))
            else:
                # Neuen Mitarbeiter anlegen
                cursor.execute('''
                INSERT INTO employees 
                (id, name, email, role, status, max_weekly_hours, min_daily_hours, max_daily_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee.id,
                    employee.name,
                    email,
                    role,
                    employee.status.value,
                    max_weekly_hours,
                    min_daily_hours,
                    max_daily_hours
                ))
            
            # Bestehende Skills löschen
            if existing:
                cursor.execute('DELETE FROM employee_skills WHERE employee_id = ?', (employee.id,))
            
            # Skills hinzufügen
            for skill in employee.skills:
                # Skill-ID finden oder erstellen
                cursor.execute('SELECT id FROM skills WHERE name = ?', (skill.lower(),))
                skill_result = cursor.fetchone()
                
                skill_id = None
                if skill_result:
                    skill_id = skill_result[0]
                else:
                    # Neuen Skill erstellen
                    skill_id = self.generate_id("skill")
                    cursor.execute('INSERT INTO skills (id, name) VALUES (?, ?)', 
                                (skill_id, skill.lower()))
                
                # Prüfen, ob bevorzugte Fähigkeit
                is_preferred = False
                if hasattr(employee, 'preferred_skills') and employee.preferred_skills:
                    is_preferred = skill in employee.preferred_skills
                
                # Skill-Zuordnung speichern
                cursor.execute('''
                INSERT INTO employee_skills (employee_id, skill_id, is_preferred)
                VALUES (?, ?, ?)
                ''', (employee.id, skill_id, is_preferred))
            
            # Arbeitszeiten speichern, wenn vorhanden
            if hasattr(employee, 'working_hours') and employee.working_hours:
                # Bestehende Verfügbarkeiten löschen
                cursor.execute('DELETE FROM employee_availability WHERE employee_id = ?', (employee.id,))
                
                # Neue Verfügbarkeiten speichern
                for day_idx, hours in employee.working_hours.items():
                    if hours.get("preferred", False):
                        cursor.execute('''
                        INSERT INTO employee_availability 
                        (employee_id, day_of_week, start_time, end_time, is_preferred)
                        VALUES (?, ?, ?, ?, ?)
                        ''', (
                            employee.id,
                            day_idx,
                            hours.get("start", "08:00"),
                            hours.get("end", "17:00"),
                            True
                        ))
            
            # Urlaubszeiten speichern, wenn vorhanden
            if hasattr(employee, 'vacations') and employee.vacations:
                # Bestehende Urlaubszeiten löschen
                cursor.execute('DELETE FROM employee_vacations WHERE employee_id = ?', (employee.id,))
                
                # Neue Urlaubszeiten speichern
                for start_date, end_date in employee.vacations:
                    vacation_id = self.generate_id("vac")
                    cursor.execute('''
                    INSERT INTO employee_vacations 
                    (id, employee_id, start_date, end_date, type)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        vacation_id,
                        employee.id,
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d'),
                        'vacation'
                    ))
            
            # Transaktion abschließen
            conn.execute("COMMIT")
            
            return True
        except Exception as e:
            print(f"Fehler beim Speichern des Mitarbeiters: {str(e)}")
            # Bei Fehler: Transaktion zurückrollen
            if conn:
                try:
                    conn.execute("ROLLBACK")
                except Exception as rollback_error:
                    print(f"Fehler beim Rollback: {rollback_error}")
            return False
        finally:
            # Verbindung schließen
            if conn:
                conn.close()
    
    def load_employee(self, employee_id: str) -> Optional[Employee]:
        """
        Lädt einen Mitarbeiter aus der Datenbank.
        
        Args:
            employee_id: ID des zu ladenden Mitarbeiters
            
        Returns:
            Employee-Objekt oder None bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Mitarbeiter-Basisdaten laden
                cursor.execute('''
                SELECT id, name, role, status, max_weekly_hours, min_daily_hours, max_daily_hours
                FROM employees WHERE id = ?
                ''', (employee_id,))
                
                employee_data = cursor.fetchone()
                if not employee_data:
                    return None
                
                emp_id, name, role, status_str, max_weekly, min_daily, max_daily = employee_data
                
                # Status in Enum konvertieren
                status = EmployeeStatus.AVAILABLE  # Standard
                for status_enum in EmployeeStatus:
                    if status_enum.value == status_str:
                        status = status_enum
                        break
                
                # Skills laden
                cursor.execute('''
                SELECT s.name, es.is_preferred
                FROM skills s
                JOIN employee_skills es ON s.id = es.skill_id
                WHERE es.employee_id = ?
                ''', (employee_id,))
                
                skills = set()
                preferred_skills = set()
                
                for skill_name, is_preferred in cursor.fetchall():
                    skills.add(skill_name)
                    if is_preferred:
                        preferred_skills.add(skill_name)
                
                # Mitarbeiter-Objekt erstellen
                employee = Employee(emp_id, name, skills, status, preferred_skills)
                
                # Zusätzliche Attribute setzen
                employee.max_weekly_hours = max_weekly
                employee.min_daily_hours = min_daily
                employee.max_daily_hours = max_daily
                employee.role = role
                
                # Arbeitszeiten laden
                cursor.execute('''
                SELECT day_of_week, start_time, end_time, is_preferred
                FROM employee_availability
                WHERE employee_id = ?
                ''', (employee_id,))
                
                working_hours = {}
                for day, start, end, is_preferred in cursor.fetchall():
                    working_hours[day] = {
                        "start": start,
                        "end": end,
                        "preferred": bool(is_preferred)
                    }
                
                employee.working_hours = working_hours
                
                # Urlaubszeiten laden
                cursor.execute('''
                SELECT start_date, end_date
                FROM employee_vacations
                WHERE employee_id = ?
                ''', (employee_id,))
                
                vacations = []
                for start_date_str, end_date_str in cursor.fetchall():
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    vacations.append((start_date, end_date))
                
                employee.vacations = vacations
                
                return employee
        except Exception as e:
            print(f"Fehler beim Laden des Mitarbeiters: {e}")
            return None
    
    def get_all_employees(self) -> List[Tuple]:
        """
        Gibt alle Mitarbeiter als Basisdaten zurück.
        
        Returns:
            Liste von Tupeln mit Mitarbeiterdaten
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, name, email, role, status, max_weekly_hours, min_daily_hours, max_daily_hours
                FROM employees
                ORDER BY name
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen aller Mitarbeiter: {e}")
            return []
    
    def load_all_employees(self) -> List[Employee]:
        """
        Lädt alle Mitarbeiter als vollständige Objekte.
        
        Returns:
            Liste von Employee-Objekten
        """
        employees = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM employees ORDER BY name')
                
                for (employee_id,) in cursor.fetchall():
                    employee = self.load_employee(employee_id)
                    if employee:
                        employees.append(employee)
                
            return employees
        except Exception as e:
            print(f"Fehler beim Laden aller Mitarbeiter: {e}")
            return []
    
    def delete_employee(self, employee_id: str) -> bool:
        """
        Löscht einen Mitarbeiter aus der Datenbank.
        
        Args:
            employee_id: ID des zu löschenden Mitarbeiters
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Löschen des Mitarbeiters: {e}")
            return False
    
    def get_employee_skills(self, employee_id: str) -> List[Tuple[str, str, bool]]:
        """
        Gibt alle Skills eines Mitarbeiters zurück.
        
        Args:
            employee_id: ID des Mitarbeiters
            
        Returns:
            Liste von Tupeln (skill_id, skill_name, is_preferred)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT s.id, s.name, es.is_preferred
                FROM skills s
                JOIN employee_skills es ON s.id = es.skill_id
                WHERE es.employee_id = ?
                ''', (employee_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen der Mitarbeiter-Skills: {e}")
            return []
    
    def get_employee_vacations(self, employee_id: str) -> List[Tuple]:
        """
        Gibt alle Urlaubszeiten eines Mitarbeiters zurück.
        
        Args:
            employee_id: ID des Mitarbeiters
            
        Returns:
            Liste von Tupeln mit Urlaubsdaten
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, start_date, end_date, type, notes
                FROM employee_vacations
                WHERE employee_id = ?
                ORDER BY start_date
                ''', (employee_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen der Urlaubszeiten: {e}")
            return []
        