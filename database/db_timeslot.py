from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
import sqlite3
import traceback

from database.db_base import DBBaseManager
from core import TimeSlot

class TimeSlotManager(DBBaseManager):
    """
    Manager-Klasse für alle TimeSlot-bezogenen Datenbankoperationen.
    Verwaltet die Speicherung, das Laden und die Manipulation von Zeitslots.
    """
    
    def save_time_slots(self, schedule_id: str, time_slots: List[TimeSlot]) -> bool:
        """
        Speichert Zeitslots für einen Zeitplan.
        
        Args:
            schedule_id: ID des Zeitplans
            time_slots: Liste von TimeSlot-Objekten
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        conn = None
        try:
            conn = self.get_connection()
            # Konfiguration für Timeout bei Locks
            conn.execute("PRAGMA busy_timeout = 5000")  # 5 Sekunden warten bei Locks
            conn.isolation_level = None
            conn.execute("BEGIN IMMEDIATE TRANSACTION")  # Sofort sperren, nicht warten
            
            cursor = conn.cursor()
            
            # Bestehende Zeitslots entfernen
            cursor.execute('DELETE FROM timeslots WHERE schedule_id = ?', (schedule_id,))
            
            # Track IDs we've already processed to avoid duplicates
            processed_ids = set()
            
            # Zeitslots speichern
            for slot in time_slots:
                # Skip if we've already processed this ID
                if slot.id in processed_ids:
                    print(f"Überspringe doppelte Timeslot ID: {slot.id}")
                    continue
                    
                processed_ids.add(slot.id)
                
                # End-Zeit berechnen (1 Stunde nach Start, falls nicht anders angegeben)
                end_time = slot.start_time + timedelta(hours=1)
                if hasattr(slot, 'end_time'):
                    end_time = slot.end_time
                
                print(f"Speichere TimeSlot: {slot.id}, Zeit: {slot.start_time}")
                
                cursor.execute('''
                INSERT INTO timeslots 
                (id, schedule_id, start_time, end_time, is_available)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    slot.id,
                    schedule_id,
                    slot.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    1
                ))
            
            # Verify number of saved timeslots
            cursor.execute('SELECT COUNT(*) FROM timeslots WHERE schedule_id = ?', (schedule_id,))
            count = cursor.fetchone()[0]
            print(f"Erfolgreich {count} Zeitslots für Schedule {schedule_id} gespeichert")
            
            conn.execute("COMMIT")
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Zeitslots: {e}")
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
    
    def load_time_slots(self, schedule_id: str) -> List[TimeSlot]:
        """
        Lädt alle Zeitslots eines Zeitplans.
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            Liste von TimeSlot-Objekten
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Count timeslots for debug information
                cursor.execute('SELECT COUNT(*) FROM timeslots WHERE schedule_id = ?', (schedule_id,))
                count = cursor.fetchone()[0]
                print(f"Gefunden: {count} Zeitslots in der Datenbank für Schedule {schedule_id}")
                
                cursor.execute('''
                SELECT id, start_time, end_time
                FROM timeslots
                WHERE schedule_id = ?
                ORDER BY start_time
                ''', (schedule_id,))
                
                time_slots = []
                time_slots_data = cursor.fetchall()
                
                if not time_slots_data:
                    print(f"Keine TimeSlots für Schedule {schedule_id} gefunden.")
                    return []
                
                for slot_id, start_time_str, end_time_str in time_slots_data:
                    try:
                        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                        time_slot = TimeSlot(slot_id, start_time)
                        
                        # End-Zeit setzen, falls vorhanden
                        if end_time_str:
                            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                            time_slot.end_time = end_time
                        
                        time_slots.append(time_slot)
                    except ValueError as e:
                        print(f"Fehler beim Parsen des TimeSlot-Datums: {e}")
                
                return time_slots
        except Exception as e:
            print(f"Fehler beim Laden der Zeitslots: {e}")
            traceback.print_exc()
            return []
    
    def delete_time_slots(self, schedule_id: str) -> bool:
        """
        Löscht alle Zeitslots eines Zeitplans.
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM timeslots WHERE schedule_id = ?', (schedule_id,))
                return True
        except Exception as e:
            print(f"Fehler beim Löschen der Zeitslots: {e}")
            return False
    
    def copy_time_slots_from_schedule(self, source_schedule_id: str, target_schedule_id: str) -> bool:
        """
        Kopiert TimeSlots von einem Schedule zu einem anderen.
        
        Args:
            source_schedule_id: ID des Quell-Schedules
            target_schedule_id: ID des Ziel-Schedules
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Quell-TimeSlots laden
            source_slots = self.load_time_slots(source_schedule_id)
            
            if not source_slots:
                print(f"Keine TimeSlots im Quell-Schedule {source_schedule_id} gefunden.")
                return False
            
            # Neue IDs für die kopierten TimeSlots generieren
            copied_slots = []
            for slot in source_slots:
                new_id = self.generate_id("slot")
                copied_slot = TimeSlot(new_id, slot.start_time)
                if hasattr(slot, 'end_time'):
                    copied_slot.end_time = slot.end_time
                copied_slots.append(copied_slot)
            
            # In Ziel-Schedule speichern
            return self.save_time_slots(target_schedule_id, copied_slots)
        
        except Exception as e:
            print(f"Fehler beim Kopieren der TimeSlots: {e}")
            traceback.print_exc()
            return False
    
    def get_time_slot(self, slot_id: str) -> Optional[TimeSlot]:
        """
        Lädt einen einzelnen Zeitslot anhand seiner ID.
        
        Args:
            slot_id: ID des Zeitslots
            
        Returns:
            TimeSlot-Objekt oder None bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, start_time, end_time
                FROM timeslots
                WHERE id = ?
                ''', (slot_id,))
                
                slot_data = cursor.fetchone()
                if not slot_data:
                    return None
                
                slot_id, start_time_str, end_time_str = slot_data
                
                try:
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                    time_slot = TimeSlot(slot_id, start_time)
                    
                    # End-Zeit setzen, falls vorhanden
                    if end_time_str:
                        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                        time_slot.end_time = end_time
                    
                    return time_slot
                except ValueError as e:
                    print(f"Fehler beim Parsen des TimeSlot-Datums: {e}")
                    return None
                
        except Exception as e:
            print(f"Fehler beim Laden des Zeitslots: {e}")
            return None
    
    def count_time_slots(self, schedule_id: str) -> int:
        """
        Zählt die Anzahl der Zeitslots eines Zeitplans.
        
        Args:
            schedule_id: ID des Zeitplans
            
        Returns:
            Anzahl der Zeitslots
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM timeslots WHERE schedule_id = ?', (schedule_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Fehler beim Zählen der Zeitslots: {e}")
            return 0
    
    def get_time_slots_by_day(self, schedule_id: str, date: datetime) -> List[TimeSlot]:
        """
        Lädt alle Zeitslots eines Zeitplans für einen bestimmten Tag.
        
        Args:
            schedule_id: ID des Zeitplans
            date: Datum, für das die Zeitslots geladen werden sollen
            
        Returns:
            Liste von TimeSlot-Objekten
        """
        try:
            # Datum formatieren (nur Tag, ohne Zeit)
            date_str = date.strftime('%Y-%m-%d')
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT id, start_time, end_time
                FROM timeslots
                WHERE schedule_id = ? AND date(start_time) = ?
                ORDER BY start_time
                ''', (schedule_id, date_str))
                
                time_slots = []
                
                for slot_id, start_time_str, end_time_str in cursor.fetchall():
                    try:
                        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                        time_slot = TimeSlot(slot_id, start_time)
                        
                        # End-Zeit setzen, falls vorhanden
                        if end_time_str:
                            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                            time_slot.end_time = end_time
                        
                        time_slots.append(time_slot)
                    except ValueError as e:
                        print(f"Fehler beim Parsen des TimeSlot-Datums: {e}")
                
                return time_slots
        except Exception as e:
            print(f"Fehler beim Laden der Zeitslots nach Tag: {e}")
            return []