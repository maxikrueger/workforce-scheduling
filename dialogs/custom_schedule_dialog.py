import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
import uuid
import traceback

from database.db_manager import DatabaseManager
from dialogs.employee_selection_dialog import EmployeeSelectorDialog
from dialogs.task_selection_dialog import TaskSelectorDialog

from core import TimeSlot, Employee, Task, Schedule, EmployeeStatus
from dialogs.employee_dialog import EmployeeDialog
from dialogs.task_dialog import TaskDialog
from dialogs.timeslot_range_dialog import TimeSlotRangeDialog


class CustomScheduleDialog(tk.Toplevel):
    """Dialog zum Erstellen eines benutzerdefinierten Zeitplans"""
    
    def __init__(self, parent, available_skills: Dict[str, List[str]] = None):
        super().__init__(parent)
        self.title("Benutzerdefinierten Zeitplan erstellen")
        self.geometry("800x600")
        self.transient(parent)
        self.resizable(True, True)
        
        # Wenn keine verfügbaren Fähigkeiten übergeben wurden, Standardwerte nutzen
        if available_skills is None:
            self.available_skills = {
                'frontend': ['javascript', 'html', 'css', 'react', 'angular', 'vue'],
                'backend': ['python', 'java', 'nodejs', 'spring', 'django'],
                'database': ['sql', 'mongodb', 'postgresql'],
                'devops': ['docker', 'kubernetes', 'aws']
            }
        else:
            self.available_skills = available_skills
        
        # Initialisiere Schedule
        self.schedule = Schedule()
        self.schedule.time_slots = []
        self.schedule.employees = []
        self.schedule.tasks = []
        self.parent = parent
        
        # Initialisiere Datenbankmanager
        try:
            if hasattr(parent, 'db_manager') and parent.db_manager:
                self.db_manager = parent.db_manager
            else:
                self.db_manager = DatabaseManager()  # Direkter Zugriff auf den Datenbankmanager
        except Exception as e:
            print(f"Fehler beim Initialisieren des DatabaseManagers: {str(e)}")
            self.db_manager = None
        
        self.result = None
        
        self.create_widgets()
        
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
        
        # Notebook für die verschiedenen Abschnitte
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True, pady=10)
        
        # Tab 1: Zeitslots
        self.timeslots_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.timeslots_tab, text="Zeitslots")
        self.setup_timeslots_tab()
        
        # Tab 2: Mitarbeiter
        self.employees_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.employees_tab, text="Mitarbeiter")
        self.setup_employees_tab()
        
        # Tab 3: Aufgaben
        self.tasks_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.tasks_tab, text="Aufgaben")
        self.setup_tasks_tab()
        
        # Tab 4: Zusammenfassung
        self.summary_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.summary_tab, text="Zusammenfassung")
        self.setup_summary_tab()
        
        # Button-Frame am unteren Rand
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Erstellen- und Abbrechen-Buttons
        ttk.Button(button_frame, text="Zeitplan erstellen", command=self.on_create).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.on_cancel).pack(side='right')
    
    def setup_timeslots_tab(self):
        """Richtet den Tab für Zeitslots ein"""
        # Beschreibungstext
        ttk.Label(self.timeslots_tab, text="Konfigurieren Sie die Zeitslots für den Einsatzplan:", 
                wraplength=700).pack(anchor='w', pady=(0, 10))
        
        # Button zum Konfigurieren der Zeitslots
        button_frame = ttk.Frame(self.timeslots_tab)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Zeitslots konfigurieren", 
                  command=self.configure_timeslots).pack(side='left')
        
        # Frame für die Zusammenfassung
        summary_frame = ttk.LabelFrame(self.timeslots_tab, text="Aktuelle Zeitslot-Konfiguration")
        summary_frame.pack(fill='x', pady=10, padx=5)
        
        self.timeslots_summary_var = tk.StringVar(value="Keine Zeitslots konfiguriert")
        ttk.Label(summary_frame, textvariable=self.timeslots_summary_var, wraplength=700).pack(
            anchor='w', pady=10, padx=10)
        
        # Frame für die Liste der Zeitslots
        list_frame = ttk.LabelFrame(self.timeslots_tab, text="Zeitslots")
        list_frame.pack(fill='both', expand=True, pady=10)
        
        # Scrollbar und Listbox für Zeitslots
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.timeslots_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                          selectmode='extended', height=10)
        self.timeslots_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        scrollbar.config(command=self.timeslots_listbox.yview)
    
    def setup_employees_tab(self):
        """Richtet den Tab für Mitarbeiter ein"""
        # Beschreibungstext
        ttk.Label(self.employees_tab, text="Fügen Sie Mitarbeiter mit ihren Fähigkeiten hinzu:", 
                wraplength=700).pack(anchor='w', pady=(0, 10))
        
        # Buttons für Mitarbeiter
        button_frame = ttk.Frame(self.employees_tab)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Mitarbeiter hinzufügen", 
                  command=self.add_employee).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Bestehende Mitarbeiter laden", 
              command=self.load_existing_employees).pack(side='left', padx=5)
    
        ttk.Button(button_frame, text="Mitarbeiter bearbeiten", 
                  command=self.edit_employee).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Mitarbeiter entfernen", 
                  command=self.remove_employee).pack(side='left', padx=5)
        
        # Frame für Mitarbeiterliste mit Scrollbars
        list_frame = ttk.Frame(self.employees_tab)
        list_frame.pack(fill='both', expand=True, pady=10)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(list_frame)
        y_scrollbar.pack(side='right', fill='y')
        
        x_scrollbar = ttk.Scrollbar(list_frame, orient='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')
        
        # Treeview für Mitarbeiterliste
        self.employees_tree = ttk.Treeview(
            list_frame, 
            columns=("name", "skills", "status", "id"),
            show="headings",
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        # Spalten konfigurieren
        self.employees_tree.heading("name", text="Name")
        self.employees_tree.heading("skills", text="Fähigkeiten")
        self.employees_tree.heading("status", text="Status")
        self.employees_tree.heading("id", text="ID")
        
        self.employees_tree.column("name", width=150)
        self.employees_tree.column("skills", width=400)
        self.employees_tree.column("status", width=100)
        self.employees_tree.column("id", width=0, stretch=False)  # Versteckte Spalte für ID
        
        # Anzeige-Spalten konfigurieren (ID ausblenden)
        self.employees_tree["displaycolumns"] = ("name", "skills", "status")
        
        self.employees_tree.pack(fill='both', expand=True)
        
        # Scrollbars mit Treeview verbinden
        y_scrollbar.config(command=self.employees_tree.yview)
        x_scrollbar.config(command=self.employees_tree.xview)
        
        # Doppelklick-Binding für Bearbeiten
        self.employees_tree.bind("<Double-1>", lambda e: self.edit_employee())
    
    def load_existing_employees(self):
        """Lädt bestehende Mitarbeiter aus der Datenbank"""
        if not self.db_manager or not hasattr(self.db_manager, 'get_all_employees'):
            messagebox.showwarning("Warnung", "Datenbank-Verbindung nicht verfügbar.")
            return
        
        # Direkt den übergebenen Datenbankmanager verwenden
        try:
            # IDs aller Mitarbeiter laden
            employee_records = self.db_manager.get_all_employees()
            
            if not employee_records:
                messagebox.showinfo("Information", "Keine Mitarbeiter in der Datenbank gefunden.")
                return
                
            # Mitarbeiter laden
            employees = []
            for emp_record in employee_records:
                emp_id = emp_record[0]  # ID aus dem Datensatz
                employee = self.db_manager.load_employee(emp_id)
                if employee:
                    # Das Employee-Objekt direkt verwenden
                    employees.append(employee)
            
            if not employees:
                messagebox.showinfo("Information", "Keine Mitarbeiter in der Datenbank gefunden.")
                return
        
            # Dialog zum Auswählen der Mitarbeiter anzeigen
            dialog = EmployeeSelectorDialog(self, employees)
            
            if dialog.result:
                # Ausgewählte Mitarbeiter zum Schedule hinzufügen
                for employee in dialog.result:
                    # Prüfen, ob der Mitarbeiter bereits im Schedule ist
                    if not any(e.id == employee.id for e in self.schedule.employees):
                        self.schedule.employees.append(employee)
                
                # Anzeige aktualisieren
                self.update_employee_display()

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Mitarbeiter: {str(e)}")
            traceback.print_exc()
            return
    
    def load_existing_tasks(self):
        """Lädt bestehende Aufgaben aus der Datenbank"""
        if not self.db_manager or not hasattr(self.db_manager, 'get_all_tasks'):
            messagebox.showwarning("Warnung", "Datenbank-Verbindung nicht verfügbar.")
            return
        
        # Direkt den übergebenen Datenbankmanager verwenden
        try:
            # IDs aller Aufgaben laden
            task_records = self.db_manager.get_all_tasks()
            
            if not task_records:
                messagebox.showinfo("Information", "Keine Aufgaben in der Datenbank gefunden.")
                return
                
            # Aufgaben laden
            tasks = []
            for task_record in task_records:
                task_id = task_record[0]  # ID aus dem Datensatz
                task = self.db_manager.load_task(task_id)
                if task:
                    # Das Task-Objekt direkt verwenden
                    tasks.append(task)
            
            if not tasks:
                messagebox.showinfo("Information", "Keine Aufgaben in der Datenbank gefunden.")
                return
            
            # Dialog zum Auswählen der Aufgaben anzeigen
            dialog = TaskSelectorDialog(self, tasks)
            
            if dialog.result:
                # Ausgewählte Aufgaben zum Schedule hinzufügen
                for task in dialog.result:
                    # Prüfen, ob die Aufgabe bereits im Schedule ist
                    if not any(t.id == task.id for t in self.schedule.tasks):
                        self.schedule.tasks.append(task)
                
                # Anzeige aktualisieren
                self.update_task_display()

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Aufgaben: {str(e)}")
            traceback.print_exc()
            return
    
    def setup_tasks_tab(self):
        """Richtet den Tab für Aufgaben ein"""
        # Beschreibungstext
        ttk.Label(self.tasks_tab, text="Fügen Sie Aufgaben mit benötigten Fähigkeiten hinzu:", 
                wraplength=700).pack(anchor='w', pady=(0, 10))
        
        # Buttons für Aufgaben
        button_frame = ttk.Frame(self.tasks_tab)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Aufgabe hinzufügen", 
                  command=self.add_task).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="Bestehende Aufgaben laden", 
                  command=self.load_existing_tasks).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Aufgabe bearbeiten", 
                  command=self.edit_task).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Aufgabe entfernen", 
                  command=self.remove_task).pack(side='left', padx=5)
        
        # Frame für Aufgabenliste mit Scrollbars
        list_frame = ttk.Frame(self.tasks_tab)
        list_frame.pack(fill='both', expand=True, pady=10)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(list_frame)
        y_scrollbar.pack(side='right', fill='y')
        
        x_scrollbar = ttk.Scrollbar(list_frame, orient='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')
        
        # Treeview für Aufgabenliste
        self.tasks_tree = ttk.Treeview(
            list_frame, 
            columns=("id", "duration", "skills"),
            show="headings",
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        # Spalten konfigurieren
        self.tasks_tree.heading("id", text="ID")
        self.tasks_tree.heading("duration", text="Dauer (h)")
        self.tasks_tree.heading("skills", text="Benötigte Fähigkeiten")
        
        self.tasks_tree.column("id", width=150)
        self.tasks_tree.column("duration", width=70, anchor='center')
        self.tasks_tree.column("skills", width=430)
        
        self.tasks_tree.pack(fill='both', expand=True)
        
        # Scrollbars mit Treeview verbinden
        y_scrollbar.config(command=self.tasks_tree.yview)
        x_scrollbar.config(command=self.tasks_tree.xview)
        
        # Doppelklick-Binding für Bearbeiten
        self.tasks_tree.bind("<Double-1>", lambda e: self.edit_task())
    
    def setup_summary_tab(self):
        """Richtet den Tab für die Zusammenfassung ein"""
        # Scrollbarer Bereich für die Zusammenfassung
        summary_frame = ttk.Frame(self.summary_tab)
        summary_frame.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(summary_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Text-Widget für die Zusammenfassung
        self.summary_text = tk.Text(summary_frame, yscrollcommand=scrollbar.set, 
                                  wrap='word', state='disabled', 
                                  width=80, height=25)
        self.summary_text.pack(fill='both', expand=True, padx=5, pady=5)
        scrollbar.config(command=self.summary_text.yview)
        
        # Button zum Aktualisieren der Zusammenfassung
        ttk.Button(self.summary_tab, text="Zusammenfassung aktualisieren", 
                  command=self.update_summary).pack(pady=10)
        
        # Initiale Zusammenfassung anzeigen
        self.update_summary()
    
    def configure_timeslots(self):
        """Öffnet den Dialog zur Konfiguration der Zeitslots"""
        dialog = TimeSlotRangeDialog(self, db_manager=self.db_manager)
        
        if dialog.result:
            # Zeitslots direkt aus dem Dialog-Ergebnis übernehmen
            self.schedule.time_slots = dialog.result.get("time_slots", [])
            
            # Zusätzlich den Namen setzen, falls vorhanden
            self.schedule.name = dialog.result.get("name", self.schedule.name)
            
            # Listbox aktualisieren
            self.update_timeslot_display()
            
            # Zusammenfassung aktualisieren
            self.update_timeslot_summary()
    
    def update_timeslot_display(self):
        """Aktualisiert die Anzeige der Zeitslots in der Listbox"""
        # Listbox leeren
        self.timeslots_listbox.delete(0, tk.END)
        
        # Slots sortieren und anzeigen
        sorted_slots = sorted(self.schedule.time_slots, key=lambda s: s.start_time)
        
        for slot in sorted_slots:
            display_text = f"{slot.start_time.strftime('%d.%m.%Y %H:%M')} - {slot.id}"
            self.timeslots_listbox.insert(tk.END, display_text)
    
    def update_timeslot_summary(self):
        """Aktualisiert die Zusammenfassung der Zeitslots"""
        if not self.schedule.time_slots:
            self.timeslots_summary_var.set("Keine Zeitslots konfiguriert")
            return
        
        # Nach Tagen gruppieren
        slots_by_day = {}
        for slot in self.schedule.time_slots:
            day_key = slot.start_time.strftime('%Y-%m-%d')
            if day_key not in slots_by_day:
                slots_by_day[day_key] = []
            slots_by_day[day_key].append(slot)
        
        # Erster und letzter Tag
        first_slot = min(self.schedule.time_slots, key=lambda s: s.start_time)
        last_slot = max(self.schedule.time_slots, key=lambda s: s.start_time)
        
        # Zusammenfassung erstellen
        summary = (
            f"Zeitraum: {first_slot.start_time.strftime('%d.%m.%Y')} bis "
            f"{last_slot.start_time.strftime('%d.%m.%Y')}\n"
            f"Anzahl Tage: {len(slots_by_day)}\n"
            f"Gesamtzahl Zeitslots: {len(self.schedule.time_slots)}"
        )
        
        self.timeslots_summary_var.set(summary)
    
    def add_employee(self):
        """Öffnet den Dialog zum Hinzufügen eines Mitarbeiters"""
        dialog = EmployeeDialog(
            self, 
            self.available_skills,
            db_manager=self.db_manager  
        )
        
        if dialog.result:
            # Mitarbeiter zur Liste hinzufügen
            self.schedule.employees.append(dialog.result)
            
            # Anzeige aktualisieren
            self.update_employee_display()

    def edit_employee(self):
        """Öffnet den Dialog zum Bearbeiten eines ausgewählten Mitarbeiters"""
        selected_items = self.employees_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Hinweis", "Bitte wählen Sie einen Mitarbeiter zum Bearbeiten aus.")
            return
        
        # Nur den ersten ausgewählten Eintrag bearbeiten
        selected_id = selected_items[0]
        
        # Mitarbeiter-ID aus dem Tree-Item ermitteln
        employee_id = self.employees_tree.item(selected_id, "values")[3]  # ID ist in der 4. Spalte (versteckt)
        
        # Mitarbeiter finden
        employee = next((e for e in self.schedule.employees if e.id == employee_id), None)
        
        if employee:
            dialog = EmployeeDialog(
                self, 
                self.available_skills, 
                employee=employee, 
                title="Mitarbeiter bearbeiten",
                db_manager=self.db_manager 
            )
            
            if dialog.result:
                # Mitarbeiter in der Liste ersetzen
                for i, emp in enumerate(self.schedule.employees):
                    if emp.id == employee_id:
                        self.schedule.employees[i] = dialog.result
                        break
                
                # Anzeige aktualisieren
                self.update_employee_display()
        
    def remove_employee(self):
        """Entfernt ausgewählte Mitarbeiter aus der Liste"""
        selected_items = self.employees_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Hinweis", "Bitte wählen Sie mindestens einen Mitarbeiter zum Entfernen aus.")
            return
        
        # Bestätigung
        if not messagebox.askyesno("Mitarbeiter entfernen", 
                               f"Möchten Sie {len(selected_items)} Mitarbeiter wirklich entfernen?"):
            return
        
        # Mitarbeiter-IDs sammeln
        employee_ids = []
        for item_id in selected_items:
            employee_id = self.employees_tree.item(item_id, "values")[3]  # ID ist in der 4. Spalte (versteckt)
            employee_ids.append(employee_id)
        
        # Mitarbeiter entfernen
        self.schedule.employees = [e for e in self.schedule.employees if e.id not in employee_ids]
        
        # Anzeige aktualisieren
        self.update_employee_display()
    
    def update_employee_display(self):
        """Aktualisiert die Anzeige der Mitarbeiter im Treeview"""
        # Bestehende Einträge löschen
        for item in self.employees_tree.get_children():
            self.employees_tree.delete(item)
        
        # Mitarbeiter anzeigen
        for employee in self.schedule.employees:
            # Status übersetzen
            status_text = employee.status.value
            if status_text == "available":
                status_text = "Verfügbar"
            elif status_text == "busy":
                status_text = "Beschäftigt"
            elif status_text == "off":
                status_text = "Abwesend"
            
            # Skills formatieren
            skills_text = ", ".join(sorted(employee.skills))
            
            # Mitarbeiter zum Treeview hinzufügen
            self.employees_tree.insert("", "end", values=(
                employee.name,
                skills_text,
                status_text,
                employee.id  # ID in der 4. Spalte (versteckt)
            ))
    
    def add_task(self):
        """Öffnet den Dialog zum Hinzufügen einer Aufgabe"""
        dialog = TaskDialog(self, self.available_skills, db_manager=self.db_manager)
        
        if dialog.result:
            # Aufgabe zur Liste hinzufügen
            self.schedule.tasks.append(dialog.result)
            
            # Anzeige aktualisieren
            self.update_task_display()
    
    def edit_task(self):
        """Öffnet den Dialog zum Bearbeiten einer ausgewählten Aufgabe"""
        selected_items = self.tasks_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Hinweis", "Bitte wählen Sie eine Aufgabe zum Bearbeiten aus.")
            return
        
        # Nur den ersten ausgewählten Eintrag bearbeiten
        selected_id = selected_items[0]
        
        # Aufgaben-ID aus dem Tree-Item ermitteln
        task_id = self.tasks_tree.item(selected_id, "values")[0]
        
        # Aufgabe finden
        task = next((t for t in self.schedule.tasks if t.id == task_id), None)
        
        if task:
            dialog = TaskDialog(self, self.available_skills, task, 
                              title="Aufgabe bearbeiten")
            
            if dialog.result:
                # Aufgabe in der Liste ersetzen
                for i, t in enumerate(self.schedule.tasks):
                    if t.id == task_id:
                        self.schedule.tasks[i] = dialog.result
                        break
                
                # Anzeige aktualisieren
                self.update_task_display()
    
    def remove_task(self):
        """Entfernt ausgewählte Aufgaben aus der Liste"""
        selected_items = self.tasks_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Hinweis", "Bitte wählen Sie mindestens eine Aufgabe zum Entfernen aus.")
            return
        
        # Bestätigung
        if not messagebox.askyesno("Aufgabe entfernen", 
                               f"Möchten Sie {len(selected_items)} Aufgabe(n) wirklich entfernen?"):
            return
        
        # Aufgaben-IDs sammeln
        task_ids = []
        for item_id in selected_items:
            task_id = self.tasks_tree.item(item_id, "values")[0]
            task_ids.append(task_id)
        
        # Aufgaben entfernen
        self.schedule.tasks = [t for t in self.schedule.tasks if t.id not in task_ids]
        
        # Anzeige aktualisieren
        self.update_task_display()
    
    def update_task_display(self):
        """Aktualisiert die Anzeige der Aufgaben im Treeview"""
        # Bestehende Einträge löschen
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        # Aufgaben anzeigen
        for task in self.schedule.tasks:
            # Skills formatieren
            skills_text = ", ".join(sorted(task.required_skills))
            
            # Aufgabe zum Treeview hinzufügen
            self.tasks_tree.insert("", "end", values=(
                task.id,
                task.duration,
                skills_text
            ))
    
    def update_summary(self):
        """Aktualisiert die Zusammenfassung aller Daten"""
        # Text-Widget für die Bearbeitung aktivieren und leeren
        self.summary_text.config(state='normal')
        self.summary_text.delete(1.0, tk.END)
        
        # Zeitslots
        self.summary_text.insert(tk.END, "ZEITSLOTS\n", "heading")
        self.summary_text.insert(tk.END, "========\n\n")
        
        if self.schedule.time_slots:
            # Nach Tagen gruppieren
            slots_by_day = {}
            for slot in sorted(self.schedule.time_slots, key=lambda s: s.start_time):
                day_key = slot.start_time.strftime('%Y-%m-%d')
                if day_key not in slots_by_day:
                    slots_by_day[day_key] = []
                slots_by_day[day_key].append(slot)
            
            # Zusammenfassung pro Tag
            for day, slots in slots_by_day.items():
                day_display = slots[0].start_time.strftime('%A, %d.%m.%Y')
                self.summary_text.insert(tk.END, f"{day_display}:\n", "subheading")
                
                for slot in slots:
                    time_display = slot.start_time.strftime('%H:%M')
                    self.summary_text.insert(tk.END, f"  - {time_display} Uhr (ID: {slot.id})\n")
                
                self.summary_text.insert(tk.END, "\n")
        else:
            self.summary_text.insert(tk.END, "Keine Zeitslots konfiguriert.\n\n")
        
       # Mitarbeiter
        self.summary_text.insert(tk.END, "MITARBEITER\n", "heading")
        self.summary_text.insert(tk.END, "===========\n\n")
        
        if self.schedule.employees:
            for employee in self.schedule.employees:
                # Status übersetzen
                status_text = employee.status.value
                if status_text == "available":
                    status_text = "Verfügbar"
                elif status_text == "busy":
                    status_text = "Beschäftigt"
                elif status_text == "off":
                    status_text = "Abwesend"
                
                self.summary_text.insert(tk.END, f"{employee.name} ({status_text}):\n", "subheading")
                
                # Skills anzeigen
                if employee.skills:
                    skills_text = ", ".join(sorted(employee.skills))
                    self.summary_text.insert(tk.END, f"  Fähigkeiten: {skills_text}\n")
                else:
                    self.summary_text.insert(tk.END, "  Keine Fähigkeiten definiert.\n")
                
                self.summary_text.insert(tk.END, f"  ID: {employee.id}\n\n")
        else:
            self.summary_text.insert(tk.END, "Keine Mitarbeiter definiert.\n\n")
        
        # Aufgaben
        self.summary_text.insert(tk.END, "AUFGABEN\n", "heading")
        self.summary_text.insert(tk.END, "========\n\n")
        
        if self.schedule.tasks:
            for task in self.schedule.tasks:
                self.summary_text.insert(tk.END, f"{task.id}:\n", "subheading")
                self.summary_text.insert(tk.END, f"  Dauer: {task.duration} Stunde(n)\n")
                
                # Benötigte Fähigkeiten anzeigen
                if task.required_skills:
                    skills_text = ", ".join(sorted(task.required_skills))
                    self.summary_text.insert(tk.END, f"  Benötigte Fähigkeiten: {skills_text}\n\n")
                else:
                    self.summary_text.insert(tk.END, "  Keine Fähigkeiten definiert.\n\n")
        else:
            self.summary_text.insert(tk.END, "Keine Aufgaben definiert.\n\n")
        
        # Text-Widget wieder deaktivieren
        self.summary_text.config(state='disabled')
        
        # Text-Tags für Formatierung
        self.summary_text.tag_configure("heading", font=('TkDefaultFont', 12, 'bold'))
        self.summary_text.tag_configure("subheading", font=('TkDefaultFont', 10, 'bold'))

    def validate_schedule(self) -> Tuple[bool, str]:
        """Validiert den Zeitplan und gibt Fehlermeldung zurück"""
        # Prüfen, ob Zeitslots definiert wurden
        if not self.schedule.time_slots:
            return False, "Es wurden keine Zeitslots konfiguriert."
        
        # Prüfen, ob Mitarbeiter definiert wurden
        if not self.schedule.employees:
            return False, "Es wurden keine Mitarbeiter definiert."
        
        # Prüfen, ob Aufgaben definiert wurden
        if not self.schedule.tasks:
            return False, "Es wurden keine Aufgaben definiert."
        
        return True, ""

    def on_create(self):
        """Verarbeitet den Klick auf den 'Zeitplan erstellen'-Button"""
        # Zeitplan validieren
        valid, error_msg = self.validate_schedule()
        
        if not valid:
            messagebox.showerror("Fehler", error_msg)
            return
        
        # Ergebnis setzen und Dialog schließen
        self.result = self.schedule
        
        # Wenn ein Datenbankmanager verfügbar ist, Zeitplan speichern
      #  if self.db_manager:
       #     try:
        #        # Standardname generieren, falls nicht vorhanden
         #       schedule_name = self.schedule.name or f"Benutzerdefinierter Zeitplan {datetime.now().strftime('%d.%m.%Y')}"
                
                # In Datenbank speichern
              #  schedule_id = self.db_manager.save_schedule(
               #     self.schedule, 
                #    name=schedule_name, 
                 #   description="Manuell erstellter Zeitplan"
                #)
                
                #if schedule_id:
                 #   messagebox.showinfo("Erfolg", f"Zeitplan '{schedule_name}' wurde gespeichert.")
                    
                    # Combobox im Hauptfenster aktualisieren
 #                  try:
  #                      # Überprüfen, ob die refresh_schedule_combo Methode existiert
   #                     if hasattr(self.parent, 'refresh_schedule_combo') and callable(self.parent.refresh_schedule_combo):
    #                        self.parent.refresh_schedule_combo()
     #                   else:
      ###                      print("Info: refresh_schedule_combo nicht gefunden im Elternobjekt.")
         ##           except Exception as e:
           #             print(f"Warnung: Fehler beim Aktualisieren der Schedule-Combobox: {str(e)}")
            #            traceback.print_exc()
             #   else:
              #      messagebox.showwarning("Warnung", "Zeitplan konnte nicht in der Datenbank gespeichert werden.")
            
      #      except Exception as e:
       #         messagebox.showerror("Fehler", f"Fehler beim Speichern des Zeitplans: {str(e)}")
        #        traceback.print_exc()
        
        self.destroy()

    def on_cancel(self):
        """Verarbeitet den Klick auf den 'Abbrechen'-Button"""
        # Bestätigung, wenn Änderungen vorgenommen wurden
        if (self.schedule.time_slots or self.schedule.employees or self.schedule.tasks):
            if not messagebox.askyesno("Abbrechen", 
                                    "Möchten Sie wirklich abbrechen? Alle nicht gespeicherten Änderungen gehen verloren."):
                return
                
        # Bei Abbruch keine Ergebnisse zurückgeben
        self.result = None
        self.destroy()