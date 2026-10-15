from typing import List, Tuple, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json
import sqlite3
import traceback

from database.db_base import DBBaseManager
from core import Schedule

class ScheduleBaseManager(DBBaseManager):
    """
    Manager-Klasse für grundlegende Schedule-Operationen (ohne Abhängigkeiten).
    Verwaltet nur die Basisdaten des Schedules in der schedules-Tabelle.
    """

    def save_schedule_base(self, schedule: Schedule, name: str = "", description: str = "") -> Optional[str]:
        """
        Speichert die Basisdaten eines Schedule-Objekts in der Datenbank.
        Kümmert sich NUR um die Speicherung der Daten in der schedules-Tabelle,
        ohne Zeitslots, Aufgaben oder Mitarbeiter.
        
        Args:
            schedule: Das zu speichernde Schedule-Objekt
            name: Name für den Zeitplan (falls nicht vorhanden)
            description: Beschreibung des Zeitplans
            
        Returns:
            ID des gespeicherten Schedules oder None bei Fehler
        """
        conn = None
        try:
            # ID generieren oder vorhandene ID verwenden
            schedule_id = getattr(schedule, 'id', self.generate_id("sch"))
            
            # Zeiten für Start- und Enddatum bestimmen
            # Priorität: 1. Aus Zeitslots, 2. Aus Objekt-Attributen, 3. Aktuelles Datum
            sorted_slots = sorted(schedule.time_slots, key=lambda s: s.start_time) if schedule.time_slots else []
            
            start_date = sorted_slots[0].start_time.strftime('%Y-%m-%d %H:%M:%S') if sorted_slots else \
                        getattr(schedule, 'start_date', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
            
            end_date = sorted_slots[-1].start_time.strftime('%Y-%m-%d %H:%M:%S') if sorted_slots else \
                    getattr(schedule, 'end_date', datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Werte aus Objekt oder Parameter extrahieren, mit Fallback
            schedule_name = getattr(schedule, 'name', '') or name or f"Schedule {datetime.now().strftime('%d.%m.%Y')}"
            schedule_description = getattr(schedule, 'description', '') or description or ''
            
            # Status bestimmen oder Default verwenden
            status = getattr(schedule, 'status', "draft")
            valid_statuses = ['planned', 'assigned', 'in_progress', 'completed', 'cancelled', 'draft']
            if status not in valid_statuses:
                status = 'draft'  # Standardwert, wenn ungültiger Status
            
            # Verbindung zur Datenbank herstellen
            conn = self.get_connection()
            conn.execute("PRAGMA busy_timeout = 5000")  # 5 Sekunden warten bei Locks
            conn.isolation_level = None
            conn.execute("BEGIN IMMEDIATE TRANSACTION")  # Sofort sperren, nicht warten
            conn.execute("PRAGMA foreign_keys = ON")
            
            cursor = conn.cursor()
            
            # Aktueller Zeitstempel
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Prüfen, ob Schedule bereits existiert
            cursor.execute('SELECT id FROM schedules WHERE id = ?', (schedule_id,))
            existing_schedule = cursor.fetchone()
            
            if not existing_schedule:
                # Neuen Schedule erstellen
                cursor.execute('''
                INSERT INTO schedules 
                (id, name, start_date, end_date, status, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    schedule_id, 
                    schedule_name, 
                    start_date, 
                    end_date, 
                    status, 
                    schedule_description,
                    current_time,
                    current_time
                ))
            else:
                # Bestehenden Schedule aktualisieren
                cursor.execute('''
                UPDATE schedules 
                SET name = ?, start_date = ?, end_date = ?, status = ?, description = ?, updated_at = ?
                WHERE id = ?
                ''', (
                    schedule_name, 
                    start_date, 
                    end_date, 
                    status, 
                    schedule_description, 
                    current_time,
                    schedule_id
                ))
            
            conn.execute("COMMIT")
            return schedule_id
        
        except sqlite3.IntegrityError as e:
            print(f"Integrity Error beim Speichern des Schedule-Basis: {str(e)}")
            if conn:
                conn.execute("ROLLBACK")
            return None
        
        except Exception as e:
            print(f"Fehler beim Speichern des Schedule-Basis: {str(e)}")
            traceback.print_exc()
            if conn:
                try:
                    conn.execute("ROLLBACK")
                except Exception as rollback_error:
                    print(f"Fehler beim Rollback: {rollback_error}")
            return None
        
        finally:
            if conn:
                conn.close()

    def load_schedule_base(self, schedule_id: str) -> Optional[Schedule]:
        """
        Lädt nur die Basisdaten eines Zeitplans aus der Datenbank.
        Lädt KEINE Zeitslots, Mitarbeiter oder Aufgaben.
        
        Args:
            schedule_id: ID des zu ladenden Zeitplans
            
        Returns:
            Schedule-Objekt mit Basisdaten oder None bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Schedule-Basisdaten laden
                cursor.execute('''
                SELECT id, name, start_date, end_date, status, description
                FROM schedules WHERE id = ?
                ''', (schedule_id,))
                
                schedule_data = cursor.fetchone()
                if not schedule_data:
                    print(f"Kein Schedule mit ID {schedule_id} gefunden.")
                    return None
                
                schedule_id, name, start_date_str, end_date_str, status, description = schedule_data
                
                # Schedule-Objekt erstellen
                schedule = Schedule()
                schedule.id = schedule_id
                schedule.name = name
                schedule.status = status
                schedule.description = description
                
                # Leere Listen für Zeitslots, Aufgaben und Mitarbeiter
                schedule.time_slots = []
                schedule.tasks = []
                schedule.employees = []
                
                # Optional: Start- und Enddatum als Attribute setzen
                if start_date_str:
                    try:
                        schedule.start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        print(f"Ungültiges Startdatum-Format: {start_date_str}")
                
                if end_date_str:
                    try:
                        schedule.end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        print(f"Ungültiges Enddatum-Format: {end_date_str}")
                
                return schedule
                
        except Exception as e:
            print(f"Fehler beim Laden des Schedule-Basis: {str(e)}")
            traceback.print_exc()
            return None

    def get_all_schedules(self) -> List[Tuple]:
        """
        Gibt alle Zeitpläne als Basisdaten zurück.
        
        Returns:
            Liste von Tupeln mit Schedule-Daten (id, name, start_date, end_date, status, description)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, name, start_date, end_date, status, description
                FROM schedules
                ORDER BY created_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen aller Zeitpläne: {e}")
            return []

    def update_schedule_status(self, schedule_id: str, status: str) -> bool:
        """
        Aktualisiert den Status eines Zeitplans.
        
        Args:
            schedule_id: ID des Zeitplans
            status: Neuer Status
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE schedules SET status = ?, updated_at = ? WHERE id = ?', 
                            (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), schedule_id))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Schedule-Status: {e}")
            return False

    def delete_schedule_base(self, schedule_id: str) -> bool:
        """
        Löscht einen Zeitplan aus der Datenbank.
        Hinweis: Durch Foreign Key Constraints werden dadurch auch alle abhängigen Daten gelöscht.
        
        Args:
            schedule_id: ID des zu löschenden Zeitplans
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        conn = None
        try:
            conn = self.get_connection()
            conn.isolation_level = None
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()
            
            # Schedule löschen
            cursor.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
            result = cursor.rowcount > 0
            
            conn.execute("COMMIT")
            return result
        except Exception as e:
            print(f"Fehler beim Löschen des Zeitplans: {e}")
            if conn:
                try:
                    conn.execute("ROLLBACK")
                except Exception as rollback_error:
                    print(f"Fehler beim Rollback: {rollback_error}")
            return False
        finally:
            if conn:
                conn.close()