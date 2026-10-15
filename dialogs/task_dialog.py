import tkinter as tk
from tkinter import ttk, messagebox
import uuid
from typing import Dict, List, Set, Optional, Callable
from datetime import timedelta

from core import Task, Employee, TimeSlot
from dialogs.skill_selection_dialog import SkillSelectionDialog

class TaskDialog(tk.Toplevel):
    """Dialog zum Erstellen oder Bearbeiten einer Aufgabe"""
    
    def __init__(self, parent, available_skills: Dict[str, List[str]], 
                task: Task = None, title="Aufgabe erstellen", 
                on_update: Optional[Callable[[Task], None]] = None,
                db_manager=None,
                available_employees: List[Employee] = None,
                available_timeslots: List[TimeSlot] = None):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.resizable(True, True)
        self.geometry("700x600")
        
        self.available_skills = available_skills
        self.task = task
        self.result = None
        self.on_update = on_update
        self.db_manager = db_manager  # Datenbankmanager hinzufügen
        
        # Zuweisungs-relevante Attribute
        self.available_employees = available_employees or []
        self.available_timeslots = available_timeslots or []
        
        # Aktuelle Zuweisungen
        self.assigned_employee = task.get_assigned_employee() if task and hasattr(task, 'get_assigned_employee') else None
        self.assigned_timeslot = task.get_time_slot() if task and hasattr(task, 'get_time_slot') else None
        
        # Unterstützung für Bearbeitungsmodus
        self.is_edit_mode = task is not None
        
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
        # Hauptcontainer mit Padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Notebook für Tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True, pady=10)
        
        # Tab 1: Aufgabeninformationen
        info_tab = ttk.Frame(notebook, padding=10)
        notebook.add(info_tab, text="Aufgabeninfo")
        self.setup_info_tab(info_tab)
        
        # Tab 2: Fähigkeiten
        skills_tab = ttk.Frame(notebook, padding=10)
        notebook.add(skills_tab, text="Benötigte Fähigkeiten")
        self.setup_skills_tab(skills_tab)
        
        # Tab 3: Zuweisungen
        assignments_tab = ttk.Frame(notebook, padding=10)
        notebook.add(assignments_tab, text="Zuweisungen")
        self.setup_assignments_tab(assignments_tab)
        
        # Tab 4: Datenbank (immer anzeigen, unabhängig vom Bearbeitungsmodus)
        db_tab = ttk.Frame(notebook, padding=10)
        notebook.add(db_tab, text="Datenbank")
        self.setup_database_tab(db_tab)
        
        # Button-Frame am unteren Rand
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Speichern- und Schließen-Buttons
        ttk.Button(button_frame, text="Speichern", command=self.on_save).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.on_cancel).pack(side='right')
    
    def setup_info_tab(self, parent):
        # Container mit Grid-Layout
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill='both', expand=True)
        
        # ID 
        ttk.Label(grid_frame, text="ID:").grid(row=0, column=0, sticky='w', pady=5)
        self.id_var = tk.StringVar(
            value=self.task.id if self.task else f"Task_{uuid.uuid4().hex[:8]}")
        ttk.Entry(grid_frame, textvariable=self.id_var, width=30).grid(
            row=0, column=1, sticky='ew', pady=5)
        
        # Name
        ttk.Label(grid_frame, text="Name/Beschreibung:").grid(row=1, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar(value=getattr(self.task, 'name', "") if self.task else "")
        ttk.Entry(grid_frame, textvariable=self.name_var, width=30).grid(
            row=1, column=1, sticky='ew', pady=5)
        
        # Dauer
        ttk.Label(grid_frame, text="Dauer (Stunden):").grid(row=2, column=0, sticky='w', pady=5)
        self.duration_var = tk.StringVar(value=str(self.task.duration) if self.task else "1")
        
        duration_frame = ttk.Frame(grid_frame)
        duration_frame.grid(row=2, column=1, sticky='w', pady=5)
        
        ttk.Spinbox(duration_frame, from_=1, to=8, 
                   textvariable=self.duration_var, width=5).pack(side='left')
        
        # Priorität
        ttk.Label(grid_frame, text="Priorität:").grid(row=3, column=0, sticky='w', pady=5)
        self.priority_var = tk.StringVar(value=getattr(self.task, 'priority', "medium") if self.task else "medium")
        priority_combo = ttk.Combobox(grid_frame, textvariable=self.priority_var, state="readonly", width=10)
        priority_combo['values'] = ["high", "medium", "low"]
        priority_combo.grid(row=3, column=1, sticky='w', pady=5)
        
        # Status
        ttk.Label(grid_frame, text="Status:").grid(row=4, column=0, sticky='w', pady=5)
        self.status_var = tk.StringVar(value=getattr(self.task, 'status', "open") if self.task else "open")
        status_combo = ttk.Combobox(grid_frame, textvariable=self.status_var, state="readonly", width=15)
        status_combo['values'] = ["open", "in_progress", "completed", "cancelled", "blocked"]
        status_combo.grid(row=4, column=1, sticky='w', pady=5)
        
        # Notizen
        ttk.Label(grid_frame, text="Notizen:").grid(row=5, column=0, sticky='nw', pady=5)
        self.notes_var = tk.StringVar(value=getattr(self.task, 'notes', "") if self.task else "")
        notes_entry = ttk.Entry(grid_frame, textvariable=self.notes_var, width=30)
        notes_entry.grid(row=5, column=1, sticky='ew', pady=5)
    
    def setup_skills_tab(self, parent):
        # Beschreibungstext
        ttk.Label(parent, text="Wählen Sie die für diese Aufgabe benötigten Fähigkeiten:").pack(
            anchor='w', pady=(0, 10))
        
        # Notebook für Kategorien
        skills_notebook = ttk.Notebook(parent)
        skills_notebook.pack(fill='both', expand=True, pady=5)
        
        # Kopie der vorhandenen Fähigkeiten erstellen
        self.required_skills = self.task.required_skills.copy() if self.task and hasattr(self.task, 'required_skills') else set()
        
        # Checkbutton-Variablen
        self.skill_vars = {}
        
        # Tabs für jede Kategorie erstellen
        for category, skills in self.available_skills.items():
            # Tab für Kategorie
            tab = ttk.Frame(skills_notebook, padding=5)
            skills_notebook.add(tab, text=category.capitalize())
            
            # Checkbuttons für jede Fähigkeit
            for skill in skills:
                skill_var = tk.BooleanVar(value=skill in self.required_skills)
                self.skill_vars[skill] = skill_var
                
                ttk.Checkbutton(
                    tab,
                    text=skill,
                    variable=skill_var,
                    command=lambda s=skill, v=skill_var: self.on_skill_changed(s, v)
                ).pack(anchor='w', pady=2)
        
        # Button zum schnellen Auswählen von Fähigkeiten
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(
            button_frame, 
            text="Dialog zur Fähigkeitsauswahl öffnen", 
            command=self.open_skill_selection_dialog
        ).pack(side='left')
        
        # Ausgewählte Fähigkeiten anzeigen
        self.selected_skills_var = tk.StringVar()
        self.update_selected_skills_text()
        ttk.Label(parent, textvariable=self.selected_skills_var, wraplength=600).pack(
            anchor='w', pady=10)
    
    def setup_assignments_tab(self, parent):
        """Richtet den Tab für Zuweisungen ein"""
        # Container mit Grid-Layout
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill='both', expand=True)
        
        # Mitarbeiter-Zuweisung
        ttk.Label(grid_frame, text="Mitarbeiter zuweisen:", font=('TkDefaultFont', 10, 'bold')).grid(
            row=0, column=0, sticky='w', pady=(0, 5))
        
        # ComboBox für Mitarbeiter
        self.employee_var = tk.StringVar(value="")
        employee_combo = ttk.Combobox(grid_frame, textvariable=self.employee_var, state="readonly", width=30)
        
        # Mitarbeiter zur Liste hinzufügen
        employee_options = ["Nicht zugewiesen"]
        self.employee_mapping = {"Nicht zugewiesen": None}
        
        for emp in self.available_employees:
            display_name = f"{emp.name} ({', '.join(sorted(emp.skills)[:2])})"
            employee_options.append(display_name)
            self.employee_mapping[display_name] = emp
        
        employee_combo['values'] = employee_options
        
        # Aktuellen Mitarbeiter auswählen
        if self.assigned_employee:
            for display_name, emp in self.employee_mapping.items():
                if emp and emp.id == self.assigned_employee.id:
                    self.employee_var.set(display_name)
                    break
        else:
            self.employee_var.set("Nicht zugewiesen")
        
        employee_combo.grid(row=0, column=1, sticky='w', pady=(0, 5))
        
        # Zeitslot-Zuweisung
        ttk.Label(grid_frame, text="Zeitslot zuweisen:", font=('TkDefaultFont', 10, 'bold')).grid(
            row=1, column=0, sticky='w', pady=5)
        
        # ComboBox für Zeitslots
        self.timeslot_var = tk.StringVar(value="")
        timeslot_combo = ttk.Combobox(grid_frame, textvariable=self.timeslot_var, state="readonly", width=30)
        
        # Zeitslots zur Liste hinzufügen
        timeslot_options = ["Nicht zugewiesen"]
        self.timeslot_mapping = {"Nicht zugewiesen": None}
        
        # Sortiere Zeitslots chronologisch
        sorted_timeslots = sorted(self.available_timeslots, key=lambda s: s.start_time) if self.available_timeslots else []
        
        for slot in sorted_timeslots:
            display_time = slot.start_time.strftime("%d.%m.%Y %H:%M")
            timeslot_options.append(display_time)
            self.timeslot_mapping[display_time] = slot
        
        timeslot_combo['values'] = timeslot_options
        
        # Aktuellen Zeitslot auswählen
        if self.assigned_timeslot:
            current_slot_time = self.assigned_timeslot.start_time.strftime("%d.%m.%Y %H:%M")
            
            # Prüfen, ob der aktuelle Zeitslot in den verfügbaren Optionen vorhanden ist
            if current_slot_time in self.timeslot_mapping.keys():
                self.timeslot_var.set(current_slot_time)
            else:
                # Falls nicht verfügbar, füge ihn trotzdem hinzu (mit Kennzeichnung)
                display_time = f"{current_slot_time} (aktuell)"
                timeslot_options.append(display_time)
                self.timeslot_mapping[display_time] = self.assigned_timeslot
                timeslot_combo['values'] = timeslot_options
                self.timeslot_var.set(display_time)
        else:
            self.timeslot_var.set("Nicht zugewiesen")
        
        timeslot_combo.grid(row=1, column=1, sticky='w', pady=5)
        
        # Aktuelle Zuweisung anzeigen (redundant aber nützlich für Übersicht)
        info_frame = ttk.LabelFrame(grid_frame, text="Aktuelle Zuweisung")
        info_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=15)
        
        emp_text = "Nicht zugewiesen"
        if self.assigned_employee:
            emp_text = f"{self.assigned_employee.name}"
        
        time_text = "Nicht zugewiesen"
        if self.assigned_timeslot:
            time_text = f"{self.assigned_timeslot.start_time.strftime('%d.%m.%Y %H:%M')}"
            
            # Endzeit berechnen
            end_time = self.assigned_timeslot.start_time + timedelta(hours=self.task.duration) if self.task else None
           
            if end_time:
                time_text += f" - {end_time.strftime('%H:%M')}"
        
        ttk.Label(info_frame, text=f"Mitarbeiter: {emp_text}").pack(anchor='w', padx=10, pady=2)
        ttk.Label(info_frame, text=f"Zeitslot: {time_text}").pack(anchor='w', padx=10, pady=2)
        
        # Hinweis zur Verwendung
        ttk.Label(grid_frame, text="Hinweis: Änderungen an den Zuweisungen können den Optimierungs-Score beeinflussen.", 
                 wraplength=400, font=('TkDefaultFont', 9, 'italic')).grid(
            row=3, column=0, columnspan=2, sticky='w', pady=(20, 0))
    
    def setup_database_tab(self, parent):
        """Richtet den Datenbank-Tab ein - unabhängig vom Edit-Modus und immer sichtbar"""
        # Beschreibungstext
        ttk.Label(parent, text="Datenbankoperationen für Aufgaben:", 
                wraplength=500).pack(anchor='w', pady=(0, 10))
        
        # Button-Frame
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=10)
        
        # Überprüfen, ob ein Datenbankmanager verfügbar ist
        if self.db_manager:
            # Speichern-Button
            save_button = ttk.Button(button_frame, text="In Datenbank speichern", 
                                  command=self.save_to_database)
            save_button.pack(side='left', padx=5)
            
            # Laden-Button
            load_button = ttk.Button(button_frame, text="Bestehende Aufgaben laden", 
                                  command=self.load_from_database)
            load_button.pack(side='left', padx=5)
        else:
            # Hinweis, wenn kein Datenbankmanager verfügbar ist
            ttk.Label(parent, text="Kein Datenbankmanager verfügbar. Datenbank-Funktionen sind deaktiviert.", 
                    foreground="gray").pack(pady=10)
        
        # Erläuterungstext für den Anwender
        info_text = """
Mit diesen Funktionen können Sie Aufgaben in der Datenbank speichern und später wiederverwenden.
- 'In Datenbank speichern': Speichert die aktuelle Aufgabe dauerhaft in der Datenbank
- 'Bestehende Aufgaben laden': Lädt eine vorhandene Aufgabe aus der Datenbank
        """
        ttk.Label(parent, text=info_text, justify='left', wraplength=500).pack(anchor='w', pady=10)
        
        # Status-Anzeige
        self.db_status_var = tk.StringVar()
        status_label = ttk.Label(parent, textvariable=self.db_status_var, wraplength=500)
        status_label.pack(anchor='w', pady=10)
    
    def on_skill_changed(self, skill, var):
        """Behandelt Änderungen an den benötigten Fähigkeiten"""
        if var.get():
            self.required_skills.add(skill)
        else:
            self.required_skills.discard(skill)
        
        self.update_selected_skills_text()
    
    def update_selected_skills_text(self):
        """Aktualisiert den Text der ausgewählten Fähigkeiten"""
        if not self.required_skills:
            self.selected_skills_var.set("Keine Fähigkeiten ausgewählt")
        else:
            self.selected_skills_var.set(f"Ausgewählte Fähigkeiten: {', '.join(sorted(self.required_skills))}")
    
    def open_skill_selection_dialog(self):
        """Öffnet den Dialog zur Auswahl von Fähigkeiten"""
        dialog = SkillSelectionDialog(self, self.available_skills, self.required_skills)
        if dialog.result is not None:
            self.required_skills = dialog.result
            
            # Checkboxen aktualisieren
            for skill, var in self.skill_vars.items():
                var.set(skill in self.required_skills)
            
            self.update_selected_skills_text()
    
    def save_to_database(self):
        """Speichert die aktuelle Aufgabe in der Datenbank"""
        if not self.db_manager:
            messagebox.showerror("Fehler", "Kein Datenbankmanager verfügbar.")
            return
        
        # Aufgabe erstellen
        task = self.create_task_object()
        if not task:
            return
        
        try:
            # Task in der Datenbank speichern
            success = self.db_manager.save_task(task)
            
            if success:
                messagebox.showinfo("Erfolg", f"Aufgabe '{task.name}' wurde in der Datenbank gespeichert.")
                # Status aktualisieren
                if hasattr(self, 'db_status_var'):
                    self.db_status_var.set(f"Aufgabe '{task.name}' erfolgreich gespeichert.")
            else:
                messagebox.showerror("Fehler", "Aufgabe konnte nicht gespeichert werden.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
    
    def load_from_database(self):
        """Lädt bestehende Aufgaben aus der Datenbank"""
        if not self.db_manager:
            messagebox.showerror("Fehler", "Kein Datenbankmanager verfügbar.")
            return
        
        try:
            # Alle Aufgaben-IDs laden
            all_tasks_data = self.db_manager.get_all_tasks()
            if not all_tasks_data:
                messagebox.showinfo("Information", "Keine Aufgaben in der Datenbank gefunden.")
                return
            
            # Dialog zur Auswahl der Aufgabe erstellen
            select_window = tk.Toplevel(self)
            select_window.title("Aufgabe auswählen")
            select_window.transient(self)
            select_window.grab_set()
            select_window.geometry("500x300")
            
            # Listbox mit Scrollbar
            list_frame = ttk.Frame(select_window, padding=10)
            list_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side='right', fill='y')
            
            task_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
            task_listbox.pack(fill='both', expand=True, padx=5, pady=5)
            scrollbar.config(command=task_listbox.yview)
            
            # Aufgaben zur Listbox hinzufügen
            task_mapping = {}
            for task_data in all_tasks_data:
                task_id, name, duration, deadline, status, priority, notes = task_data
                display_text = f"{name} (ID: {task_id}, Dauer: {duration//60}h, Status: {status})"
                task_listbox.insert(tk.END, display_text)
                task_mapping[display_text] = task_id
            
            # Button-Frame
            button_frame = ttk.Frame(select_window, padding=10)
            button_frame.pack(fill='x')
            
            def on_task_selected():
                selection = task_listbox.curselection()
                if not selection:
                    messagebox.showinfo("Hinweis", "Bitte wählen Sie eine Aufgabe aus.")
                    return
                
                selected_text = task_listbox.get(selection[0])
                selected_id = task_mapping[selected_text]
                
                # Aufgabe laden
                loaded_task = self.db_manager.load_task(selected_id)
                if loaded_task:
                    # Dialog schließen
                    select_window.destroy()
                    
                    # Felder mit den geladenen Daten aktualisieren
                    self.id_var.set(loaded_task.id)
                    self.name_var.set(getattr(loaded_task, 'name', loaded_task.id))
                    self.duration_var.set(str(loaded_task.duration))
                    self.status_var.set(getattr(loaded_task, 'status', "open"))
                    self.priority_var.set(getattr(loaded_task, 'priority', "medium"))
                    self.notes_var.set(getattr(loaded_task, 'notes', ""))
                    self.required_skills = loaded_task.required_skills
                    
                    # GUI-Updates nach dem Laden
                    self.update_selected_skills_text()
                    # Checkboxen aktualisieren
                    for skill, var in self.skill_vars.items():
                        var.set(skill in self.required_skills)
                    
                    # Optional: Datenbankstatus aktualisieren
                    if hasattr(self, 'db_status_var'):
                        self.db_status_var.set(f"Aufgabe '{loaded_task.name}' erfolgreich geladen.")
                    
                    # Aktualisierte Aufgabe speichern
                    self.task = loaded_task
                else:
                    messagebox.showerror("Fehler", f"Aufgabe konnte nicht geladen werden.")
            
            ttk.Button(button_frame, text="Auswählen", 
                      command=on_task_selected).pack(side='right', padx=(5, 0))
            ttk.Button(button_frame, text="Abbrechen", 
                      command=select_window.destroy).pack(side='right')
            
            # Doppelklick-Binding
            task_listbox.bind("<Double-1>", lambda e: on_task_selected())
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Aufgaben: {str(e)}")

    def create_task_object(self) -> Optional[Task]:
        """Erstellt ein Task-Objekt aus den aktuellen Werten"""
        # Überprüfen, ob eine ID eingegeben wurde
        task_id = self.id_var.get().strip()
        if not task_id:
            messagebox.showerror("Fehler", "Bitte geben Sie eine ID ein.")
            return None
        
        # Name überprüfen
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Fehler", "Bitte geben Sie einen Namen/Beschreibung ein.")
            return None
        
        # Dauer ermitteln und prüfen
        try:
            duration = int(self.duration_var.get())
            if duration < 1:
                raise ValueError("Dauer muss mindestens 1 Stunde betragen.")
        except ValueError as e:
            messagebox.showerror("Fehler", f"Ungültige Dauer: {str(e)}")
            return None
        
        # Prüfen, ob Fähigkeiten ausgewählt wurden
        if not self.required_skills:
            if not messagebox.askyesno("Warnung", 
                                    "Es wurden keine Fähigkeiten ausgewählt. Fortfahren?"):
                return None
        
        # Aufgabe erstellen
        task = Task(task_id, duration, self.required_skills)
        
        # Zusätzliche Attribute setzen
        task.name = name
        task.status = self.status_var.get()
        task.priority = self.priority_var.get()
        task.notes = self.notes_var.get()
        
        return task
        
    def on_save(self):
        """Verarbeitet den Klick auf den 'Speichern'-Button"""
        try:
            # Dauer überprüfen
            duration_text = self.duration_var.get().strip()
            if not duration_text:
                messagebox.showerror("Fehler", "Bitte geben Sie eine Dauer ein.")
                return
            
            duration = int(duration_text)
            if duration < 1:
                messagebox.showerror("Fehler", "Die Dauer muss mindestens 1 Stunde betragen.")
                return
            
            # Prüfen, ob Fähigkeiten ausgewählt wurden
            if not self.required_skills:
                if not messagebox.askyesno("Warnung", "Es wurden keine Fähigkeiten ausgewählt. Fortfahren?"):
                    return
        
            # Zuweisungen ermitteln
            selected_employee = self.employee_mapping.get(self.employee_var.get())
            selected_timeslot = self.timeslot_mapping.get(self.timeslot_var.get())
            
            # Aktualisierte Task-Instanz erstellen
            updated_task = Task(self.id_var.get(), duration, self.required_skills)
            
            # Zusätzliche Attribute setzen
            updated_task.name = self.name_var.get()
            updated_task.status = self.status_var.get()
            updated_task.priority = self.priority_var.get()
            updated_task.notes = self.notes_var.get()
            
            # Zuweisungen setzen
            if hasattr(updated_task, 'set_assigned_employee'):
                updated_task.set_assigned_employee(selected_employee)
            
            if hasattr(updated_task, 'set_time_slot'):
                updated_task.set_time_slot(selected_timeslot)
            
            # Callback aufrufen, wenn vorhanden
            if self.on_update:
                self.on_update(updated_task)
            
            messagebox.showinfo("Erfolg", "Aufgabendaten wurden aktualisiert.")
            self.result = updated_task
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Fehler", "Bitte geben Sie eine gültige Dauer ein.")
    
    def on_cancel(self):
        """Schließt den Dialog ohne zu speichern"""
        self.result = None
        self.destroy()