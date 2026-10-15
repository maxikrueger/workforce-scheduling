import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Set
import uuid
from datetime import datetime, timedelta
from core import Employee, EmployeeStatus
from dialogs.skill_selection_dialog import SkillSelectionDialog
from tkcalendar import Calendar, DateEntry



class WorkingHoursDialog(tk.Toplevel):
    """Dialog zum Festlegen bevorzugter Arbeitszeiten"""
    
    def __init__(self, parent, current_preferences=None):
        super().__init__(parent)
        self.title("Bevorzugte Arbeitszeiten")
        self.transient(parent)
        self.resizable(False, False)
        self.geometry("500x450")
        
        self.weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        # Format: {0: {"start": "08:00", "end": "16:00", "preferred": True}, ...}
        self.preferences = current_preferences or {}
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
        
        # Erklärung
        ttk.Label(main_frame, text="Legen Sie Ihre bevorzugten Arbeitszeiten für jeden Wochentag fest:", 
                 wraplength=450).pack(anchor='w', pady=(0, 10))
        
        # Frame für die Wochentagseinstellungen
        days_frame = ttk.Frame(main_frame)
        days_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Überschriften
        ttk.Label(days_frame, text="Wochentag", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(days_frame, text="Von", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(days_frame, text="Bis", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(days_frame, text="Bevorzugt", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=3, padx=5, pady=5)
        
        # Eingabefelder für jeden Wochentag
        self.time_vars = {}
        
        for i, day in enumerate(self.weekdays):
            # Wochentag-Label
            ttk.Label(days_frame, text=day).grid(row=i+1, column=0, padx=5, pady=5, sticky='w')
            
            # Standardwerte oder vorhandene Werte
            default_pref = self.preferences.get(i, {"start": "08:00", "end": "17:00", "preferred": i < 5})
            
            # Start- und Endzeit
            start_var = tk.StringVar(value=default_pref["start"])
            start_cb = ttk.Combobox(days_frame, textvariable=start_var, width=8, state="readonly")
            start_cb['values'] = [f"{h:02d}:00" for h in range(24)]
            start_cb.grid(row=i+1, column=1, padx=5, pady=2)
            
            end_var = tk.StringVar(value=default_pref["end"])
            end_cb = ttk.Combobox(days_frame, textvariable=end_var, width=8, state="readonly")
            end_cb['values'] = [f"{h:02d}:00" for h in range(24)]
            end_cb.grid(row=i+1, column=2, padx=5, pady=2)
            
            # Bevorzugt-Checkbox
            pref_var = tk.BooleanVar(value=default_pref["preferred"])
            ttk.Checkbutton(days_frame, variable=pref_var).grid(row=i+1, column=3, padx=15, pady=2)
            
            # Variablen speichern
            self.time_vars[i] = {
                "start": start_var,
                "end": end_var,
                "preferred": pref_var
            }
        
        # OK und Abbrechen
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(action_frame, text="OK", command=self.on_ok).pack(side='right', padx=(5, 0))
        ttk.Button(action_frame, text="Abbrechen", command=self.on_cancel).pack(side='right')
    
    def validate_times(self):
        """Überprüft, ob die Zeiten gültig sind"""
        for day, vars in self.time_vars.items():
            start = vars["start"].get()
            end = vars["end"].get()
            
            if start >= end and vars["preferred"].get():
                messagebox.showerror("Fehler", 
                                   f"Bei {self.weekdays[day]} muss die Endzeit nach der Startzeit liegen.")
                return False
        
        return True
    
    def on_ok(self):
        """Schließt den Dialog und bestätigt die Änderungen"""
        if not self.validate_times():
            return
        
        # Einstellungen sammeln
        result = {}
        for day, vars in self.time_vars.items():
            result[day] = {
                "start": vars["start"].get(),
                "end": vars["end"].get(),
                "preferred": vars["preferred"].get()
            }
        
        self.result = result
        self.destroy()
    
    def on_cancel(self):
        """Bricht den Dialog ab"""
        self.result = None
        self.destroy()
