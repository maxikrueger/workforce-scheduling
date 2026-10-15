from tkinter import messagebox
from datetime import datetime
import traceback

class DatabaseService:
    """
    Service-Klasse als Fassade für Datenbankoperationen
    Verwendet die bestehenden Funktionen aus db_manager und weiteren DB-Klassen,
    ohne Funktionalität zu duplizieren
    """
    
    def __init__(self, db_manager):
        """
        Initialisiert den DatabaseService
        
        Args:
            db_manager: Eine Instanz des DatabaseManager
        """
        self.db_manager = db_manager
    
    def refresh_schedule_combo(self, combo, mapping_dict):
        """
        Aktualisiert die Combobox mit verfügbaren Zeitplänen aus der Datenbank
        
        Args:
            combo: Die Combobox-Widget-Instanz
            mapping_dict: Ein Dictionary für die Zuordnung von Anzeigetext zu ID
        """
        try:
            # Aktuelle Auswahl merken, falls vorhanden
            current_selection = combo.get()
            
            # Zeitpläne aus der Datenbank laden
            if self.db_manager:
                schedules = self.db_manager.get_all_schedules()  # Bestehende Funktion verwenden
                
                # Formatiere Zeitpläne für die Combobox
                schedule_options = []
                mapping_dict.clear()  # Dictionary leeren
                
                for schedule_data in schedules:
                    schedule_id, name, start_date_str, end_date_str, status, description = schedule_data
                    
                    if start_date_str:  # Prüfen auf None oder leere Strings
                        try:
                            start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
                            # Formatierung: Name (Datum, Status)
                            display_text = f"{name} ({start_date.strftime('%d.%m.%Y')}, {status})"
                        except (ValueError, TypeError):
                            # Fallback bei Problemen mit dem Datum
                            display_text = f"{name} (Status: {status})"
                    else:
                        display_text = f"{name} (Status: {status})"
                    
                    schedule_options.append(display_text)
                    mapping_dict[display_text] = schedule_id
                
                # Combobox aktualisieren
                combo['values'] = schedule_options
                
                # Wenn keine Optionen vorhanden sind, Standardtext anzeigen
                if not schedule_options:
                    combo.set("Keine Zeitpläne verfügbar")
                # Vorherige Auswahl wiederherstellen, wenn möglich
                elif current_selection and current_selection in schedule_options:
                    combo.set(current_selection)
                # Sonst Standardaufforderung anzeigen
                else:
                    combo.set("Zeitplan auswählen")
            else:
                # Falls kein Datenbankmanager verfügbar
                combo['values'] = []
                combo.set("Datenbankverbindung fehlt")
                mapping_dict.clear()
        
        except Exception as e:
            # Fehlerprotokollierung
            print(f"Fehler beim Aktualisieren der Zeitplan-Combobox: {str(e)}")
            traceback.print_exc()
            
            # UI trotzdem in einen definierten Zustand bringen
            combo['values'] = []
            combo.set("Fehler beim Laden")
    
    def load_schedule(self, schedule_id):
        """
        Lädt einen Zeitplan aus der Datenbank
        
        Args:
            schedule_id: ID des zu ladenden Zeitplans
                
        Returns:
            Schedule: Das geladene Schedule-Objekt oder None bei Fehler
        """
        try:
            # Direkt die bestehende Funktion des db_manager aufrufen
            # Hier fehlten die Parameter load_employees und load_tasks
            return self.db_manager.load_schedule(
                schedule_id, 
                load_employees=True, 
                load_tasks=True
            )
        except Exception as e:
            # Fehlerbehandlung
            print(f"Fehler beim Laden des Zeitplans: {str(e)}")
            traceback.print_exc()
            return None

    
    def save_schedule(self, schedule, name=None, description=None):
        """
        Speichert einen Zeitplan in der Datenbank
        
        Args:
            schedule: Das zu speichernde Schedule-Objekt
            name: Optionaler Name für den Zeitplan
            description: Optionale Beschreibung für den Zeitplan
            
        Returns:
            str: ID des gespeicherten Zeitplans oder None bei Fehler
        """
        try:
            # Direkte Weiterleitung an db_manager.save_schedule
            return self.db_manager.save_schedule(
                schedule,
                name=name or getattr(schedule, 'name', ''),
                description=description or getattr(schedule, 'description', '')
            )
        except Exception as e:
            print(f"Fehler beim Speichern des Zeitplans: {str(e)}")
            traceback.print_exc()
            return None
    
    # Diese Methode ist nur ein Wrapper für die bestehende Funktion - zum Vereinheitlichen der API
    def get_all_schedules(self):
        """Ruft alle Zeitpläne aus der Datenbank ab"""
        return self.db_manager.get_all_schedules()
    
    def get_schedule_tasks(self, schedule_id):
        """Ruft die Aufgaben eines Zeitplans ab"""
        return self.db_manager.get_schedule_tasks(schedule_id)
    
    def get_schedule_employees(self, schedule_id):
        """Ruft die Mitarbeiter eines Zeitplans ab"""
        return self.db_manager.get_schedule_employees(schedule_id)
    
    def delete_schedule(self, schedule_id):
        """Löscht einen Zeitplan aus der Datenbank"""
        return self.db_manager.delete_schedule(schedule_id)
    
    # Für lokale Funktionalität, bei der ein Exception-Handling sinnvoll ist
    def save_employee(self, employee):
        """Speichert einen Mitarbeiter und behandelt Exceptions"""
        try:
            return self.db_manager.save_employee(employee)
        except Exception as e:
            print(f"Fehler beim Speichern des Mitarbeiters: {str(e)}")
            traceback.print_exc()
            return False