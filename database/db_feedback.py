from datetime import datetime
import traceback
from typing import Dict, List, Tuple
from database.db_base import DBBaseManager


class FeedbackManager(DBBaseManager):
    """Manager-Klasse für alle Feedback-bezogenen Datenbankoperationen"""
    
    def __init__(self, db_name: str = "workforce_scheduling.db"):
        """
        Initialisiert den FeedbackManager
        
        Args:
            db_name: Name der Datenbankdatei
        """
        super().__init__(db_name)
        self.create_tables()
    
    def create_tables(self):
        """Erstellt die benötigten Tabellen, falls sie noch nicht existieren"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tabelle für Feedback erstellen
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule_item_feedback (
                    id TEXT PRIMARY KEY,
                    schedule_id TEXT NOT NULL,
                    employee_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    rating INTEGER CHECK(rating IN (-1, 0)),
                    comment TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    iteration INTEGER DEFAULT 1,
                    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
                ''')
                
                # Indizes für schnelle Abfragen
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feedback_employee 
                ON schedule_item_feedback(employee_id)
                ''')
                
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feedback_schedule 
                ON schedule_item_feedback(schedule_id)
                ''')
                
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feedback_task 
                ON schedule_item_feedback(task_id)
                ''')
                
                cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feedback_iteration 
                ON schedule_item_feedback(iteration)
                ''')
        
        except Exception as e:
            print(f"Fehler beim Erstellen der Feedback-Tabellen: {e}")
            traceback.print_exc()
    
    
    def save_task_feedback(self, schedule_id: str, employee_id: str, 
                          task_id: str, rating: int, comment: str = "", 
                          iteration: int = 1) -> bool:
        """
        Speichert Feedback zu einer konkreten Aufgabenzuweisung
        
        Args:
            schedule_id: ID des Zeitplans
            employee_id: ID des Mitarbeiters
            task_id: ID der Aufgabe
            rating: Bewertung (1-5)
            comment: Optionaler Kommentar
            iteration: Iteration des Schedules
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prüfen, ob bereits Feedback existiert
                cursor.execute(
                    '''SELECT id FROM schedule_item_feedback 
                       WHERE schedule_id = ? AND employee_id = ? AND task_id = ? AND iteration = ?''', 
                    (schedule_id, employee_id, task_id, iteration)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Vorhandenes Feedback aktualisieren
                    cursor.execute('''
                    UPDATE schedule_item_feedback 
                    SET rating = ?, comment = ?, created_at = ?
                    WHERE schedule_id = ? AND employee_id = ? AND task_id = ? AND iteration = ?
                    ''', (rating, comment, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                         schedule_id, employee_id, task_id, iteration))
                else:
                    # Neues Feedback anlegen
                    feedback_id = self.generate_id("feedback")
                    cursor.execute('''
                    INSERT INTO schedule_item_feedback 
                    (id, schedule_id, employee_id, task_id, rating, comment, created_at, iteration)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        feedback_id, 
                        schedule_id, 
                        employee_id, 
                        task_id,
                        rating, 
                        comment, 
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                        iteration
                    ))
                return True
        except Exception as e:
            print(f"Fehler beim Speichern des Aufgaben-Feedbacks: {e}")
            traceback.print_exc()
            return False
    
    def get_task_feedback(self, schedule_id: str, task_id: str, iteration: int = None) -> List[Tuple]:
        """
        Gibt Feedback für eine bestimmte Aufgabe zurück
        
        Args:
            schedule_id: ID des Zeitplans
            task_id: ID der Aufgabe
            iteration: Optionale Iteration (falls None, wird das neueste Feedback verwendet)
            
        Returns:
            Liste von Feedback-Tupeln (id, employee_id, employee_name, rating, comment, created_at)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if iteration is not None:
                    # Feedback für eine spezifische Iteration
                    cursor.execute('''
                    SELECT f.id, f.employee_id, e.name, f.rating, f.comment, f.created_at
                    FROM schedule_item_feedback f
                    JOIN employees e ON f.employee_id = e.id
                    WHERE f.schedule_id = ? AND f.task_id = ? AND f.iteration = ?
                    ''', (schedule_id, task_id, iteration))
                else:
                    # Neuestes Feedback pro Mitarbeiter für diese Aufgabe
                    cursor.execute('''
                    SELECT f.id, f.employee_id, e.name, f.rating, f.comment, f.created_at
                    FROM schedule_item_feedback f
                    JOIN employees e ON f.employee_id = e.id
                    JOIN (
                        SELECT employee_id, MAX(created_at) as max_date
                        FROM schedule_item_feedback
                        WHERE schedule_id = ? AND task_id = ?
                        GROUP BY employee_id
                    ) latest ON f.employee_id = latest.employee_id AND f.created_at = latest.max_date
                    WHERE f.schedule_id = ? AND f.task_id = ?
                    ''', (schedule_id, task_id, schedule_id, task_id))
                
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen des Aufgaben-Feedbacks: {e}")
            traceback.print_exc()
            return []
    
    def get_employee_feedback(self, schedule_id: str, employee_id: str, iteration: int = None) -> List[Tuple]:
        """
        Gibt Feedback eines bestimmten Mitarbeiters für einen Zeitplan zurück
        
        Args:
            schedule_id: ID des Zeitplans
            employee_id: ID des Mitarbeiters
            iteration: Optionale Iteration (falls None, wird das neueste Feedback verwendet)
            
        Returns:
            Liste von Feedback-Tupeln (id, task_id, rating, comment, created_at)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if iteration is not None:
                    # Feedback für eine spezifische Iteration
                    cursor.execute('''
                    SELECT id, task_id, rating, comment, created_at
                    FROM schedule_item_feedback
                    WHERE schedule_id = ? AND employee_id = ? AND iteration = ?
                    ''', (schedule_id, employee_id, iteration))
                else:
                    # Neuestes Feedback für diesen Mitarbeiter
                    cursor.execute('''
                    SELECT id, task_id, rating, comment, created_at
                    FROM schedule_item_feedback
                    WHERE schedule_id = ? AND employee_id = ?
                    AND created_at = (
                        SELECT MAX(created_at) FROM schedule_item_feedback
                        WHERE schedule_id = ? AND employee_id = ? AND task_id = schedule_item_feedback.task_id
                    )
                    ''', (schedule_id, employee_id, schedule_id, employee_id))
                
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen des Mitarbeiter-Feedbacks: {e}")
            traceback.print_exc()
            return []
    
    def get_schedule_feedback(self, schedule_id: str, iteration: int = None) -> List[Tuple]:
        """
        Gibt Feedback für einen bestimmten Zeitplan zurück
        
        Args:
            schedule_id: ID des Zeitplans
            iteration: Optionale Iteration (falls None, wird das gesamte Feedback verwendet)
            
        Returns:
            Liste von Feedback-Tupeln (id, task_id, employee_id, employee_name, rating, comment)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if iteration is not None:
                    # Feedback für eine spezifische Iteration
                    cursor.execute('''
                    SELECT f.id, f.task_id, f.employee_id, e.name, f.rating, f.comment
                    FROM schedule_item_feedback f
                    JOIN employees e ON f.employee_id = e.id
                    WHERE f.schedule_id = ? AND f.iteration = ?
                    ORDER BY f.task_id, e.name
                    ''', (schedule_id, iteration))
                else:
                    # Gesamtes Feedback, nach Task und Mitarbeiter gruppiert
                    cursor.execute('''
                    SELECT f.id, f.task_id, f.employee_id, e.name, f.rating, f.comment
                    FROM schedule_item_feedback f
                    JOIN employees e ON f.employee_id = e.id
                    WHERE f.schedule_id = ?
                    ORDER BY f.task_id, e.name, f.created_at DESC
                    ''', (schedule_id,))
                
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen des Zeitplan-Feedbacks: {e}")
            traceback.print_exc()
            return []
    
    def get_task_feedback_for_schedule(self, schedule_id: str, iteration: int = None) -> Dict:
        """
        Holt Feedback für alle Aufgaben eines Schedules in einem optimierungs-freundlichen Format
        
        Args:
            schedule_id: ID des Zeitplans
            iteration: Optionale Iteration (falls None, wird das neueste Feedback verwendet)
            
        Returns:
            Dictionary {(task_id, employee_id): rating}
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if iteration is not None:
                    # Feedback für eine spezifische Iteration
                    cursor.execute('''
                    SELECT task_id, employee_id, rating 
                    FROM schedule_item_feedback
                    WHERE schedule_id = ? AND iteration = ?
                    ''', (schedule_id, iteration))
                else:
                    # Neuestes Feedback pro Aufgabe-Mitarbeiter-Kombination
                    cursor.execute('''
                    SELECT f.task_id, f.employee_id, f.rating
                    FROM schedule_item_feedback f
                    JOIN (
                        SELECT task_id, employee_id, MAX(created_at) as max_date
                        FROM schedule_item_feedback
                        WHERE schedule_id = ?
                        GROUP BY task_id, employee_id
                    ) latest 
                    ON f.task_id = latest.task_id 
                    AND f.employee_id = latest.employee_id 
                    AND f.created_at = latest.max_date
                    WHERE f.schedule_id = ?
                    ''', (schedule_id, schedule_id))
                
                result = {}
                for task_id, employee_id, rating in cursor.fetchall():
                    result[(task_id, employee_id)] = rating
                
                return result
        except Exception as e:
            print(f"Fehler beim Abrufen des Aufgaben-Feedbacks für den Zeitplan: {e}")
            traceback.print_exc()
            return {}
    
    def get_feedback_summary(self, schedule_id: str, iteration: int = None) -> Dict:
        """
        Erstellt eine Zusammenfassung des Feedbacks für einen Zeitplan
        
        Args:
            schedule_id: ID des Zeitplans
            iteration: Optionale Iteration (falls None, wird das gesamte Feedback verwendet)
            
        Returns:
            Dictionary mit verschiedenen Feedback-Metriken
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Parameter für die Abfragen
                params = (schedule_id,)
                iteration_filter = ""
                
                if iteration is not None:
                    iteration_filter = "AND iteration = ?"
                    params = (schedule_id, iteration)
                
                # Durchschnittsbewertung
                cursor.execute(f'''
                SELECT AVG(rating) FROM schedule_item_feedback
                WHERE schedule_id = ? {iteration_filter}
                ''', params)
                avg_rating = cursor.fetchone()[0] or 0
                
                # Anzahl der Bewertungen
                cursor.execute(f'''
                SELECT COUNT(*) FROM schedule_item_feedback
                WHERE schedule_id = ? {iteration_filter}
                ''', params)
                rating_count = cursor.fetchone()[0] or 0
                
                # Verteilung der Bewertungen
                cursor.execute(f'''
                SELECT rating, COUNT(*) FROM schedule_item_feedback
                WHERE schedule_id = ? {iteration_filter}
                GROUP BY rating
                ORDER BY rating
                ''', params)
                rating_distribution = {rating: count for rating, count in cursor.fetchall()}
                
                # Mitarbeiter mit Top-Bewertungen
                cursor.execute(f'''
                SELECT e.id, e.name, AVG(f.rating) as avg_rating, COUNT(*) as count
                FROM schedule_item_feedback f
                JOIN employees e ON f.employee_id = e.id
                WHERE f.schedule_id = ? {iteration_filter}
                GROUP BY e.id, e.name
                ORDER BY avg_rating DESC
                LIMIT 5
                ''', params)
                top_employees = [(emp_id, name, avg, count) for emp_id, name, avg, count in cursor.fetchall()]
                
                # Aufgaben mit Top-Bewertungen
                cursor.execute(f'''
                SELECT task_id, AVG(rating) as avg_rating, COUNT(*) as count
                FROM schedule_item_feedback
                WHERE schedule_id = ? {iteration_filter}
                GROUP BY task_id
                ORDER BY avg_rating DESC
                LIMIT 5
                ''', params)
                top_tasks = [(task_id, avg, count) for task_id, avg, count in cursor.fetchall()]
                
                return {
                    "average_rating": avg_rating,
                    "rating_count": rating_count,
                    "rating_distribution": rating_distribution,
                    "top_employees": top_employees,
                    "top_tasks": top_tasks,
                    "schedule_id": schedule_id,
                    "iteration": iteration
                }
        except Exception as e:
            print(f"Fehler beim Erstellen der Feedback-Zusammenfassung: {e}")
            traceback.print_exc()
            return {}
    
    def get_schedule_iterations(self, schedule_id: str) -> List[int]:
        """
        Gibt alle vorhandenen Iterationen eines Zeitplans zurück
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            Liste von Iterationsnummern
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT DISTINCT iteration FROM schedule_item_feedback
                WHERE schedule_id = ?
                ORDER BY iteration
                ''', (schedule_id,))
                
                return [iteration for (iteration,) in cursor.fetchall()]
        except Exception as e:
            print(f"Fehler beim Abrufen der Schedule-Iterationen: {e}")
            traceback.print_exc()
            return []
    
    def delete_schedule_feedback(self, schedule_id: str) -> bool:
        """
        Löscht das gesamte Feedback für einen Zeitplan
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM schedule_item_feedback WHERE schedule_id = ?', (schedule_id,))
                return True
        except Exception as e:
            print(f"Fehler beim Löschen des Zeitplan-Feedbacks: {e}")
            traceback.print_exc()
            return False