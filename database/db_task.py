from typing import List, Tuple, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from database.db_base import DBBaseManager
from core import Task

class TaskManager(DBBaseManager):
    """Manager-Klasse für alle Aufgaben-bezogenen Datenbankoperationen"""
    
    def save_task(self, task: Task) -> bool:
        """
        Speichert ein Task-Objekt in der Datenbank.
        
        Args:
            task: Das zu speichernde Task-Objekt
            
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
            
            # Prüfen, ob die Aufgabe bereits existiert
            cursor.execute('SELECT id FROM tasks WHERE id = ?', (task.id,))
            existing = cursor.fetchone()
            
            # Deadline berechnen (z.B. Heute + Dauer + 1 Tag)
            deadline = (datetime.now() + timedelta(hours=task.duration, days=1)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Standardwerte für Status und Priorität
            status = getattr(task, 'status', 'open')
            priority = getattr(task, 'priority', 'medium')
            notes = getattr(task, 'notes', '')
            
            # Name ableiten, falls nicht vorhanden (Standard: ID)
            name = getattr(task, 'name', task.id)
            
            if existing:
                # Update der bestehenden Aufgabe
                cursor.execute('''
                UPDATE tasks 
                SET name = ?, duration = ?, deadline = ?, status = ?, priority = ?, notes = ?
                WHERE id = ?
                ''', (
                    name,
                    task.duration * 60,  # Umrechnung in Minuten
                    deadline,
                    status,
                    priority,
                    notes,
                    task.id
                ))
            else:
                # Neue Aufgabe anlegen
                cursor.execute('''
                INSERT INTO tasks 
                (id, name, duration, deadline, status, priority, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.id,
                    name,
                    task.duration * 60,  # Umrechnung in Minuten
                    deadline,
                    status,
                    priority,
                    notes
                ))
            
            # Bestehende Skills löschen
            if existing:
                cursor.execute('DELETE FROM task_required_skills WHERE task_id = ?', (task.id,))
            
            # Skills-Manager auf derselben Verbindung
            # Benötigte Skills hinzufügen
            for skill in task.required_skills:
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
                
                # Skill-Zuordnung speichern
                cursor.execute('''
                INSERT INTO task_required_skills (task_id, skill_id)
                VALUES (?, ?)
                ''', (task.id, skill_id))
            
            # Abhängigkeiten speichern, wenn vorhanden
            if hasattr(task, 'dependencies') and task.dependencies:
                # Bestehende Abhängigkeiten löschen
                cursor.execute('DELETE FROM task_dependencies WHERE task_id = ?', (task.id,))
                
                # Neue Abhängigkeiten speichern
                for dependent_task_id in task.dependencies:
                    cursor.execute('''
                    INSERT INTO task_dependencies (task_id, dependent_task_id)
                    VALUES (?, ?)
                    ''', (task.id, dependent_task_id))
            
            # Transaktion abschließen
            conn.execute("COMMIT")
            
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Aufgabe: {str(e)}")
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
    
    def load_task(self, task_id: str) -> Optional[Task]:
        """
        Lädt eine Aufgabe aus der Datenbank.
        
        Args:
            task_id: ID der zu ladenden Aufgabe
            
        Returns:
            Task-Objekt oder None bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Aufgaben-Basisdaten laden
                cursor.execute('''
                SELECT id, name, duration, deadline, status, priority, notes
                FROM tasks WHERE id = ?
                ''', (task_id,))
                
                task_data = cursor.fetchone()
                if not task_data:
                    return None
                
                task_id, name, duration_minutes, deadline, status, priority, notes = task_data
                
                # Benötigte Skills laden
                cursor.execute('''
                SELECT s.name
                FROM skills s
                JOIN task_required_skills trs ON s.id = trs.skill_id
                WHERE trs.task_id = ?
                ''', (task_id,))
                
                required_skills = set(skill_name for (skill_name,) in cursor.fetchall())
                
                # Task-Objekt erstellen
                task = Task(task_id, duration_minutes // 60, required_skills)  # Umrechnung von Minuten in Stunden
                
                # Zusätzliche Attribute setzen
                task.name = name
                task.status = status
                task.priority = priority
                task.notes = notes
                
                # Abhängigkeiten laden
                cursor.execute('''
                SELECT dependent_task_id
                FROM task_dependencies
                WHERE task_id = ?
                ''', (task_id,))
                
                dependencies = [dep_id for (dep_id,) in cursor.fetchall()]
                if dependencies:
                    task.dependencies = dependencies
                
                return task
        except Exception as e:
            print(f"Fehler beim Laden der Aufgabe: {e}")
            return None
    
    def get_all_tasks(self) -> List[Tuple]:
        """
        Gibt alle Aufgaben als Basisdaten zurück.
        
        Returns:
            Liste von Tupeln mit Aufgabendaten
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, name, duration, deadline, status, priority, notes
                FROM tasks
                ORDER BY deadline
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen aller Aufgaben: {e}")
            return []
    
    def load_all_tasks(self) -> List[Task]:
        """
        Lädt alle Aufgaben als vollständige Objekte.
        
        Returns:
            Liste von Task-Objekten
        """
        tasks = []
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM tasks')
                
                for (task_id,) in cursor.fetchall():
                    task = self.load_task(task_id)
                    if task:
                        tasks.append(task)
                
            return tasks
        except Exception as e:
            print(f"Fehler beim Laden aller Aufgaben: {e}")
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """
        Löscht eine Aufgabe aus der Datenbank.
        
        Args:
            task_id: ID der zu löschenden Aufgabe
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Löschen der Aufgabe: {e}")
            return False
    
    def get_task_skills(self, task_id: str) -> List[Tuple[str, str]]:
        """
        Gibt alle benötigten Skills einer Aufgabe zurück.
        
        Args:
            task_id: ID der Aufgabe
            
        Returns:
            Liste von Tupeln (skill_id, skill_name)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT s.id, s.name
                FROM skills s
                JOIN task_required_skills trs ON s.id = trs.skill_id
                WHERE trs.task_id = ?
                ''', (task_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen der Aufgaben-Skills: {e}")
            return []
    
    def get_tasks_by_skills(self, skill_ids: List[str]) -> List[Tuple]:
        """
        Gibt alle Aufgaben zurück, die bestimmte Skills erfordern.
        
        Args:
            skill_ids: Liste von Skill-IDs
            
        Returns:
            Liste von Tupeln mit Aufgabendaten
        """
        if not skill_ids:
            return []
            
        try:
            placeholders = ', '.join(['?'] * len(skill_ids))
            query = f'''
            SELECT DISTINCT t.id, t.name, t.duration, t.deadline, t.status, t.priority
            FROM tasks t
            JOIN task_required_skills trs ON t.id = trs.task_id
            WHERE trs.skill_id IN ({placeholders})
            ORDER BY t.deadline
            '''
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, skill_ids)
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen der Aufgaben nach Skills: {e}")
            return []
    
    def get_task_dependencies(self, task_id: str) -> List[str]:
        """
        Gibt alle Abhängigkeiten einer Aufgabe zurück.
        
        Args:
            task_id: ID der Aufgabe
            
        Returns:
            Liste von Task-IDs
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT dependent_task_id
                FROM task_dependencies
                WHERE task_id = ?
                ''', (task_id,))
                return [dep_id for (dep_id,) in cursor.fetchall()]
        except Exception as e:
            print(f"Fehler beim Abrufen der Aufgaben-Abhängigkeiten: {e}")
            return []