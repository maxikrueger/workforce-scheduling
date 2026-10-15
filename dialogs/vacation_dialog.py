import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Set
import uuid
from datetime import datetime, timedelta
from core import Employee, EmployeeStatus
from dialogs.skill_selection_dialog import SkillSelectionDialog
from tkcalendar import Calendar, DateEntry  # Zusätzliche Komponente für Kalenderfunktionen

class VacationDialog(tk.Toplevel):
    """Dialog zum Hinzufügen von Urlaubszeiten"""
    
    def __init__(self, parent, current_vacations=None):
        super().__init__(parent)
        self.title("Urlaubszeiten")
        self.transient(parent)
        self.resizable(False, False)
        self.geometry("450x400")
        
        # Bestehende Urlaubszeiten
        self.vacations = current_vacations or []
        self.result = None
        
        self.create_widgets()
        
        # Dialog modal machen
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.focus_set()
        
        # Warten, bis dieses Fenster zerstört wird
        parent.wait_window(self)
    
    def create_widgets(self):
        # Hauptframe
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Urlaubszeiten-Liste
        list_frame = ttk.LabelFrame(main_frame, text="Aktuelle Urlaubszeiten")
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Scrollbare Liste der Urlaubszeiten
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.vacation_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=8)
        self.vacation_list.pack(fill='both', expand=True, padx=5, pady=5)
        scrollbar.config(command=self.vacation_list.yview)
        
        # Bestehende Urlaubszeiten anzeigen
        self.update_vacation_list()
        
        # Eingabebereich für neue Urlaubszeit
        input_frame = ttk.LabelFrame(main_frame, text="Neue Urlaubszeit")
        input_frame.pack(fill='x', pady=(0, 10))
        
        # Start- und Enddatum
        date_frame = ttk.Frame(input_frame)
        date_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(date_frame, text="Von:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.start_date = DateEntry(date_frame, width=12, background='darkblue', 
                                  foreground='white', borderwidth=2, date_pattern='dd.MM.yyyy')
        self.start_date.grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(date_frame, text="Bis:").grid(row=0, column=2, sticky='w', padx=(10, 5))
        self.end_date = DateEntry(date_frame, width=12, background='darkblue', 
                                foreground='white', borderwidth=2, date_pattern='dd.MM.yyyy')
        self.end_date.grid(row=0, column=3, sticky='w', padx=5)
        
        # Buttons zum Hinzufügen/Entfernen
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Hinzufügen", command=self.add_vacation).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Entfernen", command=self.remove_vacation).pack(side='left')
        
        # OK und Abbrechen
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(action_frame, text="OK", command=self.on_ok).pack(side='right', padx=(5, 0))
        ttk.Button(action_frame, text="Abbrechen", command=self.on_cancel).pack(side='right')
    
    def update_vacation_list(self):
        """Aktualisiert die Liste der Urlaubszeiten"""
        self.vacation_list.delete(0, tk.END)
        for start_date, end_date in self.vacations:
            self.vacation_list.insert(tk.END, f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")
    
    def add_vacation(self):
        """Fügt eine neue Urlaubszeit hinzu"""
        start = self.start_date.get_date()
        end = self.end_date.get_date()
        
        # Validierung
        if start > end:
            messagebox.showerror("Fehler", "Das Startdatum muss vor dem Enddatum liegen.")
            return
        
        # Zur Liste hinzufügen und aktualisieren
        self.vacations.append((start, end))
        self.update_vacation_list()
    
    def remove_vacation(self):
        """Entfernt ausgewählte Urlaubszeiten"""
        selected = self.vacation_list.curselection()
        if not selected:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie einen Eintrag zum Entfernen aus.")
            return
        
        # Entfernen und Liste aktualisieren
        for index in reversed(selected):
            del self.vacations[index]
        
        self.update_vacation_list()
    
    def on_ok(self):
        """Schließt den Dialog und bestätigt die Änderungen"""
        self.result = self.vacations
        self.destroy()
    
    def on_cancel(self):
        """Bricht den Dialog ab"""
        self.result = None
        self.destroy()
