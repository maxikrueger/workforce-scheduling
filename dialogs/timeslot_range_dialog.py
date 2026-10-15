import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional

from core import TimeSlot, Schedule

class TimeSlotRangeDialog(tk.Toplevel):
    """Dialog zur Konfiguration eines Zeitslot-Bereichs mit Datenbankunterstützung"""
    
    def __init__(self, parent, title="Zeitslots konfigurieren", db_manager=None):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        
        # Standardwerte
        self.start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.days = 5
        self.start_hour = 8
        self.end_hour = 17
        
        # Datenbank-Manager
        self.db_manager = db_manager
        
        self.result = None
        
        self.create_widgets()
        
        # Position neben dem Elternfenster
        self.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}")
        
        # Dialog modal machen
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.focus_set()
        
        # Warten, bis dieses Fenster zerstört wird
        parent.wait_window(self)
    
    def create_widgets(self):
        """Erstellt alle Widgets für den Dialog"""
        # Hauptcontainer mit Padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Startdatum
        ttk.Label(main_frame, text="Startdatum:").grid(row=0, column=0, sticky='w', pady=5)
        
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=0, column=1, sticky='w', pady=5)
        
        # Tag
        self.day_var = tk.StringVar(value=str(self.start_date.day))
        ttk.Spinbox(date_frame, from_=1, to=31, textvariable=self.day_var, width=3).pack(side='left')
        ttk.Label(date_frame, text=".").pack(side='left')
        
        # Monat
        self.month_var = tk.StringVar(value=str(self.start_date.month))
        ttk.Spinbox(date_frame, from_=1, to=12, textvariable=self.month_var, width=3).pack(side='left')
        ttk.Label(date_frame, text=".").pack(side='left')
        
        # Jahr
        self.year_var = tk.StringVar(value=str(self.start_date.year))
        ttk.Spinbox(date_frame, from_=2023, to=2030, textvariable=self.year_var, width=5).pack(side='left')
        
        # Anzahl der Tage
        ttk.Label(main_frame, text="Anzahl der Arbeitstage:").grid(row=1, column=0, sticky='w', pady=5)
        self.days_var = tk.StringVar(value=str(self.days))
        ttk.Spinbox(main_frame, from_=1, to=60, textvariable=self.days_var, width=5).grid(
            row=1, column=1, sticky='w', pady=5)
        
        # Tägliche Arbeitszeit
        ttk.Label(main_frame, text="Tägliche Arbeitszeit:").grid(row=2, column=0, sticky='w', pady=5)
        
        hours_frame = ttk.Frame(main_frame)
        hours_frame.grid(row=2, column=1, sticky='w', pady=5)
        
        # Startstunde
        self.start_hour_var = tk.StringVar(value=str(self.start_hour))
        ttk.Spinbox(hours_frame, from_=0, to=23, textvariable=self.start_hour_var, width=3).pack(side='left')
        ttk.Label(hours_frame, text="bis").pack(side='left', padx=5)
        
        # Endstunde
        self.end_hour_var = tk.StringVar(value=str(self.end_hour))
        ttk.Spinbox(hours_frame, from_=1, to=24, textvariable=self.end_hour_var, width=3).pack(side='left')
        ttk.Label(hours_frame, text="Uhr").pack(side='left')
        
        # Zeitslot-Name oder Beschreibung
        ttk.Label(main_frame, text="Zeitplan-Name:").grid(row=3, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar(value=f"Zeitplan {datetime.now().strftime('%d.%m.%Y')}")
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(
            row=3, column=1, sticky='w', pady=5)
        
        # Wochenenden überspringen
        ttk.Label(main_frame, text="Wochenenden:").grid(row=4, column=0, sticky='w', pady=5)
        self.skip_weekends_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Überspringen", variable=self.skip_weekends_var).grid(
            row=4, column=1, sticky='w', pady=5)
        
        # In Datenbank speichern
        ttk.Label(main_frame, text="Datenbank:").grid(row=5, column=0, sticky='w', pady=5)
        self.save_to_db_var = tk.BooleanVar(value=True if self.db_manager else False)
        save_db_check = ttk.Checkbutton(main_frame, text="In Datenbank speichern", 
                                      variable=self.save_to_db_var)
        save_db_check.grid(row=5, column=1, sticky='w', pady=5)
        
        # Deaktivieren, wenn kein DB-Manager vorhanden
        if not self.db_manager:
            save_db_check.config(state='disabled')
            ttk.Label(main_frame, text="(Kein Datenbank-Manager verfügbar)", 
                     foreground='gray').grid(row=5, column=1, sticky='w', padx=(180, 0), pady=5)
        
        # Zusammenfassung
        summary_frame = ttk.LabelFrame(main_frame, text="Zusammenfassung")
        summary_frame.grid(row=6, column=0, columnspan=2, sticky='ew', pady=10)
        
        self.summary_var = tk.StringVar()
        ttk.Label(summary_frame, textvariable=self.summary_var, wraplength=500).pack(pady=5)
        
        # Button zum Aktualisieren der Zusammenfassung
        ttk.Button(summary_frame, text="Vorschau aktualisieren", 
                  command=self.update_summary).pack(pady=5)
        
        # Initiale Zusammenfassung anzeigen
        self.update_summary()
        
        # Button-Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, sticky='e', pady=(15, 0))
        
        # Zusätzlicher Button zum Laden aus der Datenbank
        if self.db_manager:
            ttk.Button(button_frame, text="Aus DB laden", 
                      command=self.load_from_database).pack(side='left', padx=(0, 5))
        
        # OK und Abbrechen-Buttons
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.on_cancel).pack(side='right')
    
    def validate_input(self) -> Tuple[bool, str]:
        """Validiert die Eingabewerte und gibt Fehlermeldung zurück"""
        try:
            # Datum prüfen
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            
            try:
                start_date = datetime(year, month, day)
            except ValueError:
                return False, f"Ungültiges Datum: {day}.{month}.{year}"
            
            # Tagesanzahl prüfen
            days = int(self.days_var.get())
            if days < 1 or days > 60:
                return False, "Anzahl der Tage muss zwischen 1 und 60 liegen."
            
            # Uhrzeiten prüfen
            start_hour = int(self.start_hour_var.get())
            end_hour = int(self.end_hour_var.get())
            
            if start_hour < 0 or start_hour > 23:
                return False, "Startstunde muss zwischen 0 und 23 liegen."
            
            if end_hour < 1 or end_hour > 24:
                return False, "Endstunde muss zwischen 1 und 24 liegen."
            
            if start_hour >= end_hour:
                return False, "Endstunde muss größer als Startstunde sein."
            
            # Name prüfen
            name = self.name_var.get().strip()
            if not name:
                return False, "Bitte geben Sie einen Namen für den Zeitplan ein."
            
            return True, ""
            
        except ValueError:
            return False, "Bitte geben Sie gültige Zahlen ein."
    
    def update_summary(self):
        """Aktualisiert die Zusammenfassungsanzeige"""
        valid, error_msg = self.validate_input()
        
        if not valid:
            self.summary_var.set(f"Eingabefehler: {error_msg}")
            return
        
        # Eingabewerte holen
        year = int(self.year_var.get())
        month = int(self.month_var.get())
        day = int(self.day_var.get())
        days = int(self.days_var.get())
        start_hour = int(self.start_hour_var.get())
        end_hour = int(self.end_hour_var.get())
        skip_weekends = self.skip_weekends_var.get()
        
        # Start- und Enddatum berechnen
        start_date = datetime(year, month, day)
        
        # Anzahl der Zeitslots berechnen
        total_slots = 0
        current_date = start_date
        days_processed = 0
        
        while days_processed < days:
            # Wochenenden überspringen, wenn gewünscht
            if skip_weekends and current_date.weekday() >= 5:  # 5=Samstag, 6=Sonntag
                current_date += timedelta(days=1)
                continue
                
            # Für diesen Tag Zeitslots zählen
            total_slots += (end_hour - start_hour)
            
            # Nächster Tag
            current_date += timedelta(days=1)
            days_processed += 1
        
        # Enddatum berechnen
        if skip_weekends:
            # Wir müssen die übersprungenen Wochenendtage berücksichtigen
            end_date = start_date
            days_processed = 0
            
            while days_processed < days:
                end_date += timedelta(days=1)
                if end_date.weekday() < 5:  # Nur Arbeitstage zählen
                    days_processed += 1
            
            # Wir gehen einen Tag zurück, da die Schleife einen Tag zu weit geht
            end_date -= timedelta(days=1)
        else:
            # Einfacher Fall: Enddatum ist Startdatum + Anzahl der Tage - 1
            end_date = start_date + timedelta(days=days-1)
        
        # Zusätzliche Datenbank-Informationen
        db_info = "\nZeitslots werden " + ("in der Datenbank gespeichert." if self.save_to_db_var.get() else "nicht gespeichert.")
        
        # Zusammenfassung formatieren
        self.summary_var.set(
            f"Zeitraum: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n"
            f"Arbeitszeit: {start_hour}:00 - {end_hour}:00 Uhr\n"
            f"Gesamtzahl Zeitslots: {total_slots}\n"
            f"Zeitplan-Name: {self.name_var.get()}{db_info}"
        )
    
    def generate_time_slots(self) -> List[TimeSlot]:
        """
        Generiert Zeitslots basierend auf den Eingabewerten
        
        Returns:
            List[TimeSlot]: Liste der generierten TimeSlot-Objekte
        """
        # Eingabewerte holen
        year = int(self.year_var.get())
        month = int(self.month_var.get())
        day = int(self.day_var.get())
        days = int(self.days_var.get())
        start_hour = int(self.start_hour_var.get())
        end_hour = int(self.end_hour_var.get())
        skip_weekends = self.skip_weekends_var.get()
        
        # Start-Datum
        start_date = datetime(year, month, day)
        
        # Zeitslots generieren
        time_slots = []
        current_date = start_date
        days_processed = 0
        
        # Eindeutige ID für den Zeitplan generieren
        schedule_id = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        while days_processed < days:
            # Wochenenden überspringen, wenn gewünscht
            if skip_weekends and current_date.weekday() >= 5:  # 5=Samstag, 6=Sonntag
                current_date += timedelta(days=1)
                continue
            
            # Zeitslots für diesen Tag erstellen
            for hour in range(start_hour, end_hour):
                slot_id = f"slot_{schedule_id}_{current_date.strftime('%Y%m%d')}_{hour}"
                slot_time = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                time_slots.append(TimeSlot(slot_id, slot_time))
            
            # Nächster Tag
            current_date += timedelta(days=1)
            days_processed += 1
        
        return time_slots
    
    def save_time_slots_to_database(self, time_slots: List[TimeSlot]) -> Optional[str]:
        """
        Speichert die Zeitslots in der Datenbank mit Hilfe des ScheduleManagers
        
        Args:
            time_slots: Liste von TimeSlot-Objekten
            
        Returns:
            Schedule-ID bei Erfolg, None bei Fehler
        """
        if not self.db_manager:
            messagebox.showerror("Fehler", "Kein Datenbankmanager verfügbar.")
            return None
        
        try:
            # Neues Schedule-Objekt erstellen
            schedule = Schedule()
            schedule.time_slots = time_slots
            
            # Name und zusätzliche Informationen setzen
            schedule.name = self.name_var.get().strip()
            
     #       # In der Datenbank speichern
      #      schedule_id = self.db_manager.save_schedule(
       #         schedule, 
        #        name=schedule.name, 
         #       description=f"Generiert am {datetime.now().strftime('%d.%m.%Y %H:%M')}"
          #  )
            
       #     if schedule_id:
        #        messagebox.showinfo("Erfolg", f"Zeitplan '{schedule.name}' wurde gespeichert.")
         #       return schedule_id
          #  else:
           #     messagebox.showerror("Fehler", "Fehler beim Speichern des Zeitplans.")
            #    return None
        
        except Exception as e:
            messagebox.showerror("Datenbankfehler", f"Fehler beim Speichern: {str(e)}")
            return None
    
    def load_from_database(self):
        """Lädt vorhandene Zeitpläne aus der Datenbank"""
        if not self.db_manager:
            messagebox.showwarning("Hinweis", "Kein Datenbank-Manager verfügbar.")
            return
        
        try:
            # Alle Zeitpläne aus der Datenbank laden
            schedules = self.db_manager.get_all_schedules()
            
            if not schedules:
                messagebox.showinfo("Information", "Keine Zeitpläne in der Datenbank gefunden.")
                return
            
            # Dialog zur Auswahl des Zeitplans erstellen
            select_window = tk.Toplevel(self)
            select_window.title("Zeitplan auswählen")
            select_window.transient(self)
            select_window.grab_set()
            select_window.geometry("500x300")
            
            # Listbox mit Scrollbar
            list_frame = ttk.Frame(select_window, padding=10)
            list_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side='right', fill='y')
            
            schedule_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
            schedule_listbox.pack(fill='both', expand=True, padx=5, pady=5)
            scrollbar.config(command=schedule_listbox.yview)
            
            # Zeitpläne zur Listbox hinzufügen
            schedule_mapping = {}
            for schedule_data in schedules:
                schedule_id, name, start_date_str, end_date_str, status, description = schedule_data
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
                display_text = f"{name} ({start_date.strftime('%d.%m.%Y')}, {status})"
                schedule_listbox.insert(tk.END, display_text)
                schedule_mapping[display_text] = schedule_id
            
            # Button-Frame
            button_frame = ttk.Frame(select_window, padding=10)
            button_frame.pack(fill='x')
            
            def on_schedule_selected():
                selection = schedule_listbox.curselection()
                if not selection:
                    messagebox.showinfo("Hinweis", "Bitte wählen Sie einen Zeitplan aus.")
                    return
                
                selected_text = schedule_listbox.get(selection[0])
                selected_id = schedule_mapping[selected_text]
                
                # Zeitslots für den ausgewählten Zeitplan laden
                loaded_schedule = self.db_manager.load_schedule(selected_id, load_employees=False, load_tasks=False)
                
                if loaded_schedule and loaded_schedule.time_slots:
                    # Dialog schließen
                    select_window.destroy()
                    
                    # Ersten Zeitslot als Referenz für Voreinstellungen nutzen
                    first_slot = loaded_schedule.time_slots[0]
                    
                    # Eingabefelder aktualisieren
                    self.day_var.set(str(first_slot.start_time.day))
                    self.month_var.set(str(first_slot.start_time.month))
                    self.year_var.set(str(first_slot.start_time.year))
                    
                    # Tage zählen
                    unique_dates = set(slot.start_time.date() for slot in loaded_schedule.time_slots)
                    self.days_var.set(str(len(unique_dates)))
                    
                    # Start- und Endstunde ermitteln
                    hours = set(slot.start_time.hour for slot in loaded_schedule.time_slots)
                    self.start_hour_var.set(str(min(hours) if hours else 8))
                    self.end_hour_var.set(str(max(hours) + 1 if hours else 17))
                    
                    # Name setzen
                    self.name_var.set(loaded_schedule.name or f"Zeitplan {first_slot.start_time.strftime('%d.%m.%Y')}")
                    
                    # Zusammenfassung aktualisieren
                    self.update_summary()
                    
                    messagebox.showinfo("Erfolg", f"Zeitplan '{loaded_schedule.name}' wurde geladen.")
                else:
                    messagebox.showerror("Fehler", "Keine Zeitslots im ausgewählten Zeitplan.")
            
            ttk.Button(button_frame, text="Auswählen", 
                      command=on_schedule_selected).pack(side='right', padx=(5, 0))
            ttk.Button(button_frame, text="Abbrechen", 
                      command=select_window.destroy).pack(side='right')
            
            # Doppelklick-Binding
            schedule_listbox.bind("<Double-1>", lambda e: on_schedule_selected())
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Zeitpläne: {str(e)}")
    
    def on_ok(self):
        """Verarbeitet den Klick auf den 'OK'-Button"""
        valid, error_msg = self.validate_input()
        
        if not valid:
            messagebox.showerror("Fehler", error_msg)
            return
        
        # Zeitslots generieren
        time_slots = self.generate_time_slots()
        
        # In der Datenbank speichern, wenn gewünscht
      #  schedule_id = None
       # if self.save_to_db_var.get() and self.db_manager:
        #    schedule_id = self.save_time_slots_to_database(time_slots)
        
        # Ergebnis als Dictionary zurückgeben
        self.result = {
            "start_date": datetime(
                int(self.year_var.get()), 
                int(self.month_var.get()), 
                int(self.day_var.get())
            ),
            "days": int(self.days_var.get()),
            "start_hour": int(self.start_hour_var.get()),
            "end_hour": int(self.end_hour_var.get()),
            "skip_weekends": self.skip_weekends_var.get(),
            "time_slots": time_slots,
      #      "schedule_id": schedule_id,
            "name": self.name_var.get().strip()
        }
        
        self.destroy()
    
    def on_cancel(self):
        """Verarbeitet den Abbrechen-Button-Klick"""
        self.result = None
        self.destroy()