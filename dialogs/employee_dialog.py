import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Callable, Set, Optional
import uuid

from core import Employee, EmployeeStatus, Task
from dialogs.skill_selection_dialog import SkillSelectionDialog
from dialogs.vacation_dialog import VacationDialog
from dialogs.workinghour_dialog import WorkingHoursDialog
#from db_manager import DatabaseManager

class EmployeeDialog(tk.Toplevel):
    """
    Vereinheitlichter Dialog zum Erstellen, Bearbeiten und Anzeigen von Mitarbeitern.
    Kombiniert die Funktionalität von EmployeeDialog und EmployeeDetailDialog.
    """
    
    def __init__(self, parent, available_skills: Dict[str, List[str]], 
                 employee: Optional[Employee] = None, 
                 assigned_tasks: Optional[List[Task]] = None,
                 on_update: Callable[[Employee], None] = None, 
                 title=None,
                 db_manager=None):  # Add direct database manager parameter
        """
        Initialisiert den Dialog.
        
        Args:
            parent: Parent-Widget
            available_skills: Dictionary mit verfügbaren Fähigkeiten nach Kategorien
            employee: Optional - Existierender Mitarbeiter zum Bearbeiten
            assigned_tasks: Optional - Liste der zugewiesenen Aufgaben für diesen Mitarbeiter
            on_update: Optional - Callback-Funktion, die nach dem Speichern aufgerufen wird
            title: Optional - Titel des Dialogfensters
            db_manager: Optional - Direkter Zugriff auf den Datenbankmanager
        """
        super().__init__(parent)
        
        # Bestimmt Modus und Titel
        self.is_edit_mode = employee is not None
        if title:
            self.title(title)
        else:
            self.title(f"Mitarbeiter {'bearbeiten' if self.is_edit_mode else 'erstellen'}")
        
        # Parameter speichern
        self.parent = parent
        self.available_skills = available_skills
        self.employee = employee
        self.assigned_tasks = assigned_tasks or []
        self.on_update = on_update
        self.result = None
        self.db_manager = db_manager # Store the database manager directly
        
        # Fenstereinstellungen
        self.transient(parent)
        self.resizable(True, True)
        self.geometry("800x600")
        
        # Daten initialisieren 
        self.id = employee.id if employee else f"emp_{uuid.uuid4().hex[:8]}"
        self.skills = employee.skills.copy() if employee and hasattr(employee, 'skills') else set()
        self.preferred_skills = employee.preferred_skills.copy() if employee and hasattr(employee, 'preferred_skills') else set()
        self.working_hours = getattr(employee, 'working_hours', {}) if employee else {}
        self.vacations = getattr(employee, 'vacations', []) if employee else []
        
        # UI erstellen
        self.create_widgets()
        
        # Dialog mittig zum Parent positionieren
        self.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}")
        
        # Dialog modal machen
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.focus_set()
        
        # Warten, bis dieses Fenster zerstört wird (nur wenn nicht direkt aufgerufen)
        if not getattr(self, "_skip_wait", False):
            parent.wait_window(self)

    
    def create_widgets(self):
        """Erstellt alle UI-Elemente des Dialogs"""
        # Hauptcontainer mit Padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Notebook für Tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True, pady=10)
        
        # Tab 1: Allgemeine Informationen
        general_tab = ttk.Frame(notebook, padding=10)
        notebook.add(general_tab, text="Allgemein")
        self.create_general_tab(general_tab)
        
        # Tab 2: Fähigkeiten
        skills_tab = ttk.Frame(notebook, padding=10)
        notebook.add(skills_tab, text="Fähigkeiten")
        self.create_skills_tab(skills_tab)
        
        # Tab 3: Arbeitszeiten
        time_tab = ttk.Frame(notebook, padding=10)
        notebook.add(time_tab, text="Arbeitszeiten")
        self.create_time_tab(time_tab)
        
        # Tab 4: Urlaub
        vacation_tab = ttk.Frame(notebook, padding=10)
        notebook.add(vacation_tab, text="Urlaub")
        self.create_vacation_tab(vacation_tab)
        
        # Tab 5: Zugewiesene Aufgaben (nur im Bearbeitungsmodus mit zugewiesenen Aufgaben)
        if self.is_edit_mode and self.assigned_tasks:
            tasks_tab = ttk.Frame(notebook, padding=10)
            notebook.add(tasks_tab, text="Aufgaben")
            self.create_tasks_tab(tasks_tab)
        
        # Button-Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        # OK und Abbrechen-Buttons
        ttk.Button(button_frame, text="Speichern", command=self.on_save).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.on_cancel).pack(side='right')
    
    def create_general_tab(self, parent):
        """Erstellt den Tab für allgemeine Informationen"""
        # Container mit Grid-Layout
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill='both', expand=True)
        
        # ID (nicht änderbar)
        ttk.Label(grid_frame, text="ID:", font=('TkDefaultFont', 10, 'bold')).grid(
            row=0, column=0, sticky='w', pady=(0, 10))
        ttk.Label(grid_frame, text=self.id).grid(
            row=0, column=1, sticky='w', pady=(0, 10))
        
        # Name
        ttk.Label(grid_frame, text="Name:", font=('TkDefaultFont', 10, 'bold')).grid(
            row=1, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar(value=self.employee.name if self.employee else "")
        ttk.Entry(grid_frame, textvariable=self.name_var, width=30).grid(
            row=1, column=1, sticky='w', pady=5)
        
        # Status
        ttk.Label(grid_frame, text="Status:", font=('TkDefaultFont', 10, 'bold')).grid(
            row=2, column=0, sticky='w', pady=5)
        self.status_var = tk.StringVar(
            value=self.employee.status.value if self.employee else EmployeeStatus.AVAILABLE.value)
        status_combo = ttk.Combobox(grid_frame, textvariable=self.status_var, state="readonly", width=15)
        status_combo['values'] = [status.value for status in EmployeeStatus]
        status_combo.grid(row=2, column=1, sticky='w', pady=5)
        
        # Maximale Arbeitsstunden pro Tag
        ttk.Label(grid_frame, text="Max. Arbeitsstunden/Tag:", font=('TkDefaultFont', 10, 'bold')).grid(
            row=3, column=0, sticky='w', pady=5)
        self.max_hours_var = tk.StringVar(value=getattr(self.employee, 'max_daily_hours', 8) if self.employee else 8)
        ttk.Spinbox(grid_frame, from_=4, to=12, textvariable=self.max_hours_var, width=5).grid(
            row=3, column=1, sticky='w', pady=5)
        
        # Minimale Ruhezeit zwischen Schichten
        ttk.Label(grid_frame, text="Min. Ruhezeit (Stunden):", font=('TkDefaultFont', 10, 'bold')).grid(
            row=4, column=0, sticky='w', pady=5)
        self.min_rest_var = tk.StringVar(value=getattr(self.employee, 'min_rest_hours', 11) if self.employee else 11)
        ttk.Spinbox(grid_frame, from_=8, to=16, textvariable=self.min_rest_var, width=5).grid(
            row=4, column=1, sticky='w', pady=5)
        
        # Zusammenfassung der zugewiesenen Aufgaben (nur im Bearbeitungsmodus)
        if self.is_edit_mode:
            ttk.Label(grid_frame, text="Zugewiesene Aufgaben:", font=('TkDefaultFont', 10, 'bold')).grid(
                row=5, column=0, sticky='w', pady=5)
            
            tasks_text = f"{len(self.assigned_tasks)} Aufgabe(n) zugewiesen" if self.assigned_tasks else "Keine Aufgaben zugewiesen"
            ttk.Label(grid_frame, text=tasks_text).grid(
                row=5, column=1, sticky='w', pady=5)
    
    def create_skills_tab(self, parent):
        """Erstellt den Tab für Fähigkeiten"""
        # Fähigkeiten
        ttk.Label(parent, text="Fähigkeiten:").grid(row=0, column=0, sticky='w', pady=5)
        
        skills_frame = ttk.Frame(parent)
        skills_frame.grid(row=0, column=1, sticky='ew', pady=5)
        
        self.skills_var = tk.StringVar()
        self.update_skills_text()
        
        ttk.Label(skills_frame, textvariable=self.skills_var, wraplength=400).pack(
            side='left', fill='x', expand=True)
        
        ttk.Button(skills_frame, text="Bearbeiten", command=self.edit_skills).pack(side='right')
        
        # Bevorzugte Fähigkeiten
        ttk.Label(parent, text="Bevorzugte Fähigkeiten:").grid(row=1, column=0, sticky='w', pady=5)
        
        preferred_skills_frame = ttk.Frame(parent)
        preferred_skills_frame.grid(row=1, column=1, sticky='ew', pady=5)
        
        self.preferred_skills_var = tk.StringVar()
        self.update_preferred_skills_text()
        
        ttk.Label(preferred_skills_frame, textvariable=self.preferred_skills_var, wraplength=400).pack(
            side='left', fill='x', expand=True)
        
        ttk.Button(preferred_skills_frame, text="Bearbeiten", command=self.edit_preferred_skills).pack(side='right')
    
    def create_time_tab(self, parent):
        """Erstellt den Tab für Arbeitszeiten"""
        # Erklärungstext
        ttk.Label(parent, text="Bevorzugte Arbeitszeiten des Mitarbeiters:", 
                wraplength=500).pack(anchor='w', pady=(0, 10))
        
        # Zusammenfassung der aktuellen Einstellungen
        self.working_hours_var = tk.StringVar()
        self.update_working_hours_text()
        
        summary_frame = ttk.LabelFrame(parent, text="Aktuelle Einstellungen")
        summary_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(summary_frame, textvariable=self.working_hours_var, 
                wraplength=500).pack(anchor='w', padx=10, pady=10)
        
        # Button zum Bearbeiten
        ttk.Button(parent, text="Arbeitszeiten bearbeiten", 
                  command=self.edit_working_hours).pack(anchor='w')
    
    def create_vacation_tab(self, parent):
        """Erstellt den Tab für Urlaub"""
        # Erklärungstext
        ttk.Label(parent, text="Urlaubszeiten des Mitarbeiters:", 
                wraplength=500).pack(anchor='w', pady=(0, 10))
        
        # Liste der Urlaubszeiten
        list_frame = ttk.LabelFrame(parent, text="Eingetragene Urlaubszeiten")
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.vacation_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10)
        self.vacation_list.pack(fill='both', expand=True, padx=5, pady=5)
        scrollbar.config(command=self.vacation_list.yview)
        
        # Bestehende Urlaubszeiten anzeigen
        self.update_vacation_list()
        
        # Button zum Bearbeiten
        ttk.Button(parent, text="Urlaubszeiten bearbeiten", 
                  command=self.edit_vacations).pack(anchor='w')
    
    def create_tasks_tab(self, parent):
        """Erstellt den Tab für zugewiesene Aufgaben"""
        # Beschreibungstext
        ttk.Label(parent, text="Dem Mitarbeiter zugewiesene Aufgaben:", 
                wraplength=600).pack(anchor='w', pady=(0, 10))
        
        # Scrollbarer Bereich für die Aufgabenliste
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview für Aufgabenliste
        columns = ("id", "time", "duration", "skills")
        self.tasks_tree = ttk.Treeview(frame, columns=columns, 
                                      show="headings", yscrollcommand=scrollbar.set)
        
        self.tasks_tree.heading("id", text="Aufgabe")
        self.tasks_tree.heading("time", text="Zeit")
        self.tasks_tree.heading("duration", text="Dauer (h)")
        self.tasks_tree.heading("skills", text="Benötigte Fähigkeiten")
        
        self.tasks_tree.column("id", width=100)
        self.tasks_tree.column("time", width=150)
        self.tasks_tree.column("duration", width=70, anchor="center")
        self.tasks_tree.column("skills", width=250)
        
        self.tasks_tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.tasks_tree.yview)
        
        # Aufgaben hinzufügen, wenn vorhanden
        if self.assigned_tasks:
            for task in self.assigned_tasks:
                time_text = "Nicht geplant"
                if hasattr(task, 'get_time_slot') and task.get_time_slot():
                    time_slot = task.get_time_slot()
                    time_text = time_slot.start_time.strftime("%d.%m.%Y %H:%M")
                
                # Skills formatieren
                skills_text = ", ".join(sorted(task.required_skills))
                
                self.tasks_tree.insert("", "end", values=(
                    task.id,
                    time_text,
                    task.duration,
                    skills_text[:40] + "..." if len(skills_text) > 40 else skills_text
                ))
        else:
            # Platzhaltereintrag
            self.tasks_tree.insert("", "end", values=("Keine Aufgaben", "", "", ""))
    
    def update_skills_text(self):
        """Aktualisiert den Text der Fähigkeiten"""
        if not self.skills:
            self.skills_var.set("Keine Fähigkeiten ausgewählt")
        else:
            skills_text = ", ".join(sorted(self.skills))
            if len(skills_text) > 50:
                self.skills_var.set(f"{skills_text[:47]}...")
            else:
                self.skills_var.set(skills_text)
    
    def update_preferred_skills_text(self):
        """Aktualisiert den Text der bevorzugten Fähigkeiten"""
        if not self.preferred_skills:
            self.preferred_skills_var.set("Keine bevorzugten Fähigkeiten ausgewählt")
        else:
            skills_text = ", ".join(sorted(self.preferred_skills))
            if len(skills_text) > 50:
                self.preferred_skills_var.set(f"{skills_text[:47]}...")
            else:
                self.preferred_skills_var.set(skills_text)
    
    def update_working_hours_text(self):
        """Aktualisiert den Text der Arbeitszeiten"""
        if not self.working_hours:
            self.working_hours_var.set("Keine spezifischen Arbeitszeiten festgelegt.")
            return
            
        weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        summary = []
        
        for day_idx, day_name in enumerate(weekdays):
            day_prefs = self.working_hours.get(day_idx)
            if day_prefs and day_prefs.get("preferred"):
                start = day_prefs.get("start", "08:00")
                end = day_prefs.get("end", "17:00")
                summary.append(f"{day_name}: {start} - {end}")
        
        if not summary:
            self.working_hours_var.set("Keine bevorzugten Arbeitszeiten festgelegt.")
        else:
            self.working_hours_var.set("\n".join(summary))
    
    def update_vacation_list(self):
        """Aktualisiert die Liste der Urlaubszeiten"""
        self.vacation_list.delete(0, tk.END)
        
        if not self.vacations:
            self.vacation_list.insert(tk.END, "Keine Urlaubszeiten eingetragen")
            return
            
        for start_date, end_date in self.vacations:
            # Formatierung für Anzeige
            start_str = start_date.strftime("%d.%m.%Y")
            end_str = end_date.strftime("%d.%m.%Y")
            self.vacation_list.insert(tk.END, f"{start_str} - {end_str}")
    
    def edit_skills(self):
        """Öffnet den Dialog zur Auswahl von Fähigkeiten"""
        dialog = SkillSelectionDialog(self, self.available_skills, self.skills)
        if dialog.result is not None:
            self.skills = dialog.result
            # Bevorzugte Fähigkeiten dürfen nur aus den vorhandenen Fähigkeiten gewählt werden
            self.preferred_skills = self.preferred_skills.intersection(self.skills)
            self.update_skills_text()
            self.update_preferred_skills_text()
    
    def edit_preferred_skills(self):
        """Öffnet den Dialog zur Auswahl von bevorzugten Fähigkeiten"""
        # Nur die vorhandenen Fähigkeiten des Mitarbeiters zur Auswahl anbieten
        available_preferred = {}
        for category, skills in self.available_skills.items():
            category_skills = [skill for skill in skills if skill in self.skills]
            if category_skills:
                available_preferred[category] = category_skills
        
        dialog = SkillSelectionDialog(self, available_preferred, self.preferred_skills, 
                                     title="Bevorzugte Fähigkeiten auswählen")
        if dialog.result is not None:
            self.preferred_skills = dialog.result
            self.update_preferred_skills_text()
    
    def edit_working_hours(self):
        """Öffnet den Dialog zur Bearbeitung der Arbeitszeiten"""
        dialog = WorkingHoursDialog(self, self.working_hours)
        if dialog.result is not None:
            self.working_hours = dialog.result
            self.update_working_hours_text()
    
    def edit_vacations(self):
        """Öffnet den Dialog zur Bearbeitung der Urlaubszeiten"""
        dialog = VacationDialog(self, self.vacations)
        if dialog.result is not None:
            self.vacations = dialog.result
            self.update_vacation_list()
    
    



    def on_save(self):
        """Verarbeitet den Klick auf den 'Speichern'-Button"""
        # Überprüfen, ob ein Name eingegeben wurde
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Fehler", "Bitte geben Sie einen Namen ein.")
            return
        
        # Status ermitteln
        status_value = self.status_var.get()
        status = next((s for s in EmployeeStatus if s.value == status_value), EmployeeStatus.AVAILABLE)
        
        try:
            # Maximale Arbeitsstunden validieren
            max_hours = int(self.max_hours_var.get())
            if max_hours < 4 or max_hours > 12:
                messagebox.showerror("Fehler", "Die maximalen Arbeitsstunden pro Tag müssen zwischen 4 und 12 liegen.")
                return
                
            # Minimale Ruhezeit validieren
            min_rest = int(self.min_rest_var.get())
            if min_rest < 8 or min_rest > 16:
                messagebox.showerror("Fehler", "Die minimale Ruhezeit muss zwischen 8 und 16 Stunden liegen.")
                return
        except ValueError:
            messagebox.showerror("Fehler", "Bitte geben Sie gültige Zahlenwerte ein.")
            return
        
        # Employee-Objekt erstellen oder aktualisieren
        employee = Employee(self.id, name, self.skills, status, self.preferred_skills)
        
        # Zusätzliche Attribute hinzufügen
        employee.max_daily_hours = max_hours
        employee.min_rest_hours = min_rest
        employee.working_hours = self.working_hours
        employee.vacations = self.vacations
        
        # In der Datenbank speichern, wenn möglich
        save_success = False
        is_new_employee = not self.is_edit_mode
        
        try:
            if self.db_manager and hasattr(self.db_manager, 'save_employee'):
                # Direkt über den übergebenen db_manager speichern - keine Skill-ID-Abfragen mehr
                save_success = self.db_manager.save_employee(employee)
                if save_success:
                    messagebox.showinfo("Erfolg", "Mitarbeiterdaten wurden gespeichert.")
            else:
                # Wenn kein db_manager übergeben wurde, ist das OK - dann nur
                # für die lokale Verwendung ein Employee-Objekt erstellen
                save_success = True
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern des Mitarbeiters: {str(e)}")
        
        # Callback aufrufen, wenn vorhanden
        if self.on_update:
            self.on_update(employee)
        
        # Erfolgsmeldung anzeigen (nur wenn noch nicht angezeigt)
        if is_new_employee and save_success and not self.db_manager:
            messagebox.showinfo("Mitarbeiter erstellt", 
                            f"Der Mitarbeiter '{employee.name}' wurde erfolgreich erstellt.")
        elif save_success and not self.db_manager:
            messagebox.showinfo("Änderungen gespeichert", 
                            f"Die Änderungen für Mitarbeiter '{employee.name}' wurden erfolgreich gespeichert.")
        
        # Ergebnis speichern und Dialog schließen
        self.result = employee
        self.destroy()





    # Die alte get_skill_id-Methode wird nun nicht mehr direktiv verwendet, 
    # aber falls sie noch in anderem Code aufgerufen wird, hier eine saubere Version:
    def get_skill_id(self, skill_name):
        """
        Findet die ID eines Skills (nur für Legacy-Support - wird in on_save nicht mehr verwendet)
        HINWEIS: Diese Methode sollte nicht mehr direkt verwendet werden
        """
        try:
            # Nur den übergebenen DB-Manager verwenden - keine App-Referenzen suchen
            if self.db_manager and hasattr(self.db_manager, 'get_all_skills'):
                # Suche nach dem Skill in der Datenbank
                all_skills = self.db_manager.get_all_skills()
                
                for skill_id, name in all_skills:
                    if name.lower() == skill_name.lower():
                        return skill_id
                
                # Wenn nicht gefunden, wird None zurückgegeben
                # Kein direktes Erstellen hier mehr - das übernimmt save_employee
                return None
            return None
        except Exception as e:
            print(f"Fehler beim Abrufen des Skills: {str(e)}")
            return None








   










    def find_app_with_db_manager(self):
        """Helper method to find the application with a database manager"""
        # Look in parent hierarchy
        current = self.parent
        while current:
            if hasattr(current, 'db_manager'):
                return current
            elif hasattr(current, 'master'):
                current = current.master
            else:
                break
        
        # Try toplevel as a fallback
        top = self.winfo_toplevel()
        if hasattr(top, 'db_manager'):
            return top
            
        # Look for scheduling_app instance in toplevel children
        if hasattr(top, 'children'):
            for widget in top.winfo_children():
                if hasattr(widget, 'db_manager'):
                    return widget
            
        return None

    def on_cancel(self):
        """Verarbeitet den Klick auf den 'Abbrechen'-Button"""
        # Bei Abbruch keine Ergebnisse zurückgeben
        self.result = None
        self.destroy()