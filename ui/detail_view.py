import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import random
import traceback
from typing import List, Dict, Optional
from dialogs.employee_dialog import EmployeeDialog
from dialogs.task_dialog import TaskDialog


# Importiere die Core-Klassen
from core import (
    TimeSlot, Employee, Task, Schedule, EmployeeStatus,
    optapy, HardSoftScore, define_constraints
)

class DetailView:
    """Modulare Klasse für die Detail-Ansicht"""
    
    def __init__(self, parent, db_manager):

        self.db_manger = db_manager
        # Container für die Detail-Ansicht
        self.frame = ttk.LabelFrame(parent, text="Details")
        self.frame.pack(side='right', fill='both', expand=True)
        
        # Standardwert für verfügbare Skills
        self.available_skills = {
            'frontend': ['javascript', 'html', 'css', 'react', 'angular', 'vue'],
            'backend': ['python', 'java', 'nodejs', 'spring', 'django'],
            'database': ['sql', 'mongodb', 'postgresql'],
            'devops': ['docker', 'kubernetes', 'aws']
        }
        
        # Notebook für Tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Mitarbeiter
        self.employee_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.employee_tab, text="Mitarbeiter")
        self._setup_employee_tab()
        
        # Tab 2: Aufgaben
        self.task_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.task_tab, text="Aufgaben")
        self._setup_task_tab()
        
        # Tab 3: Statistik
        self.stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_tab, text="Statistik")
        self._setup_stats_tab()
        
        # Liste für aktuelle Mitarbeiter initialisieren
        self.current_employees = []
        # Liste für aktuelle Aufgaben initialisieren
        self.current_tasks = []
        # Aktuelle Lösung speichern (für Aufgabenzuweisungen)
        self.current_solution = None
        # Zugriff auf das Schedule-Objekt
        self.schedule = None

    def _setup_employee_tab(self):
        """Richtet den Mitarbeiter-Tab ein"""
        # Hauptframe für den Mitarbeiter-Tab
        main_frame = ttk.Frame(self.employee_tab)
        main_frame.pack(fill='both', expand=True)
        
        # Button-Leiste am oberen Rand hinzufügen
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(0, 5))
        
        # Button zum Öffnen des Mitarbeiter-Detail-Dialogs
        self.view_employee_button = ttk.Button(
            button_frame, 
            text="Mitarbeiter Details anzeigen", 
            command=self.show_employee_details
        )
        self.view_employee_button.pack(side='left', padx=(0, 5))
        
        # Neue Buttons für Erstellen/Hinzufügen/Entfernen
        self.create_employee_button = ttk.Button(
            button_frame,
            text="Mitarbeiter erstellen",
            command=self.create_employee
        )
        self.create_employee_button.pack(side='left', padx=5)
        
        self.add_employee_button = ttk.Button(
            button_frame,
            text="Mitarbeiter laden",
            command=self.add_new_employee
        )
        self.add_employee_button.pack(side='left', padx=5)
        
        self.remove_employee_button = ttk.Button(
            button_frame,
            text="Mitarbeiter entfernen",
            command=self.remove_selected_employees
        )
        self.remove_employee_button.pack(side='left', padx=5)
        
        # Scrollbarer Bereich für die Mitarbeiterliste
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview für Mitarbeiterliste
        self.employee_tree = ttk.Treeview(list_frame, columns=("name", "skills", "status"), 
                                        show="headings", yscrollcommand=scrollbar.set)
        
        self.employee_tree.heading("name", text="Name")
        self.employee_tree.heading("skills", text="Fähigkeiten")
        self.employee_tree.heading("status", text="Status")
        
        self.employee_tree.column("name", width=150)
        self.employee_tree.column("skills", width=250)
        self.employee_tree.column("status", width=100)
        
        self.employee_tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.employee_tree.yview)
        
        # Platzhaltereintrag
        self.employee_tree.insert("", "end", values=("Keine Daten", "", ""))
        
        # Doppelklick-Event binden
        self.employee_tree.bind("<Double-1>", self.on_employee_double_click)

    def _setup_task_tab(self):
        """Richtet den Aufgaben-Tab ein"""
        # Hauptframe für den Aufgaben-Tab
        main_frame = ttk.Frame(self.task_tab)
        main_frame.pack(fill='both', expand=True)
        
        # Button-Leiste am oberen Rand hinzufügen
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(0, 5))
        
        # Button zum Öffnen des Aufgaben-Detail-Dialogs
        self.edit_task_button = ttk.Button(
            button_frame, 
            text="Aufgabe bearbeiten", 
            command=self.show_task_details
        )
        self.edit_task_button.pack(side='left', padx=(0, 5))
        
        # Neue Buttons für Erstellen/Hinzufügen/Entfernen
        self.create_task_button = ttk.Button(
            button_frame,
            text="Aufgabe erstellen",
            command=self.create_task
        )
        self.create_task_button.pack(side='left', padx=5)
        
        self.add_task_button = ttk.Button(
            button_frame,
            text="Aufgabe laden",
            command=self.add_new_task
        )
        self.add_task_button.pack(side='left', padx=5)
        
        self.remove_task_button = ttk.Button(
            button_frame,
            text="Aufgabe entfernen",
            command=self.remove_selected_tasks
        )
        self.remove_task_button.pack(side='left', padx=5)
        
        # Scrollbarer Bereich für die Aufgabenliste
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview für Aufgabenliste
        self.task_tree = ttk.Treeview(list_frame, columns=("id", "duration", "skills", "assigned"), 
                                     show="headings", yscrollcommand=scrollbar.set)
        
        self.task_tree.heading("id", text="Aufgabe")
        self.task_tree.heading("duration", text="Dauer (h)")
        self.task_tree.heading("skills", text="Benötigte Fähigkeiten")
        self.task_tree.heading("assigned", text="Zugewiesen")
        
        self.task_tree.column("id", width=100)
        self.task_tree.column("duration", width=70, anchor="center")
        self.task_tree.column("skills", width=200)
        self.task_tree.column("assigned", width=130)
        
        self.task_tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.task_tree.yview)
        
        # Platzhaltereintrag
        self.task_tree.insert("", "end", values=("Keine Daten", "", "", ""))
        
        # Doppelklick-Event binden
        self.task_tree.bind("<Double-1>", self.on_task_double_click)
    
    def _setup_stats_tab(self):
        """Richtet den Statistik-Tab mit vertikaler Scrollbar ein"""
        # Erstelle einen Rahmen für den gesamten Statistik-Tab
        main_frame = ttk.Frame(self.stats_tab)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Überschrift
        ttk.Label(main_frame, text="Zeitplan-Statistik", font=('TkDefaultFont', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        # Erstelle ein scrollbares Frame für die Statistik-Inhalte
        # Canvas und Scrollbar für vertikales Scrollen
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        
        # Packe Canvas und Scrollbar
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Konfiguriere das Canvas mit der Scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Erstelle ein Frame innerhalb des Canvas für die Statistikinhalte
        self.stats_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.stats_frame, anchor="nw", width=canvas.winfo_reqwidth())
        
        # Platzhalter
        ttk.Label(self.stats_frame, text="Keine Statistik verfügbar.\nErstelle einen Zeitplan.").pack(pady=20)
        
        # Mausrad-Bindung für vertikales Scrollen
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def create_employee(self):
        """Öffnet den Dialog zum Erstellen eines neuen Mitarbeiters"""
        # Den EmployeeDialog verwenden, um einen neuen Mitarbeiter zu erstellen
        dialog = EmployeeDialog(
            self.employee_tab,
            self.available_skills,
            db_manager=self.db_manger
        )
        
        if dialog.result:
            # Füge den neuen Mitarbeiter zur aktuellen Liste hinzu
            if hasattr(self, 'current_employees'):
                self.current_employees.append(dialog.result)
                self.update_employee_list(self.current_employees)
                
                # App-Referenz holen und den Mitarbeiter zum Schedule hinzufügen, falls möglich
                app = self._get_app_reference()
                if app and hasattr(app, 'schedule') and app.schedule:
                    # Füge Mitarbeiter zum Schedule hinzu, falls eine Methode dafür existiert
                    if hasattr(app, 'add_employee_to_schedule'):
                        app.add_employee_to_schedule(dialog.result)
                    elif hasattr(app.schedule, 'employees'):
                        # Direkt zum Schedule hinzufügen, wenn keine spezielle Methode existiert
                        app.schedule.employees.append(dialog.result)
    
    def create_task(self):
        """Öffnet den Dialog zum Erstellen einer neuen Aufgabe"""
        # Den TaskDialog verwenden, um eine neue Aufgabe zu erstellen
        dialog = TaskDialog(
            self.task_tab,
            self.available_skills,
            db_manager=self.db_manger
        )
        
        if dialog.result:
            # Füge die neue Aufgabe zur aktuellen Liste hinzu
            if hasattr(self, 'current_tasks'):
                self.current_tasks.append(dialog.result)
                self.update_task_list(self.current_tasks, self.current_solution)
                
                # App-Referenz holen und die Aufgabe zum Schedule hinzufügen, falls möglich
                app = self._get_app_reference()
                if app and hasattr(app, 'schedule') and app.schedule:
                    # Füge Aufgabe zum Schedule hinzu, falls eine Methode dafür existiert
                    if hasattr(app, 'add_task_to_schedule'):
                        app.add_task_to_schedule(dialog.result)
                    elif hasattr(app.schedule, 'tasks'):
                        # Direkt zum Schedule hinzufügen, wenn keine spezielle Methode existiert
                        app.schedule.tasks.append(dialog.result)
    
    def show_task_details(self):
        """Öffnet den Aufgaben-Detail-Dialog für die ausgewählte Aufgabe"""
        # Ausgewähltes Item holen
        selected_item = self.task_tree.selection()
        
        if not selected_item:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie eine Aufgabe aus der Liste aus.")
            return
        
        # Daten aus dem ausgewählten Item extrahieren
        item_data = self.task_tree.item(selected_item[0], "values")
        task_id = item_data[0]  # ID ist die erste Spalte
        
        # Die ausgewählte Aufgabe finden
        task = None
        if self.current_solution:
            # Wenn wir eine Lösung haben, aus der Lösung holen
            task = next((t for t in self.current_solution.get_tasks() if t.id == task_id), None)
        
        if not task and self.current_tasks:
            # Alternativ aus der Aufgabenliste holen
            task = next((t for t in self.current_tasks if t.id == task_id), None)
        
        if task:
            # Verfügbare Zeitslots und Mitarbeiter für die Zuweisungen
            available_timeslots = []
            available_employees = []
            
            if self.current_solution:
                # Wenn Lösung vorhanden, daraus die Daten holen
                available_timeslots = self.current_solution.get_time_slots()
                available_employees = self.current_solution.get_employees()
            elif hasattr(self, 'schedule') and self.schedule:
                # Alternativ aus dem Schedule holen, falls vorhanden
                available_timeslots = self.schedule.time_slots
                available_employees = self.schedule.employees
            else:
                # Fallback: Aktuelle Listen verwenden
                available_employees = self.current_employees
            
            TaskDialog(
                parent=self.task_tab, 
                available_skills=self.available_skills,
                task=task,
                title=f"Aufgabendetails: {task.id}",
                on_update=self.update_task,
                db_manager=self.db_manger,
                available_employees=available_employees,
                available_timeslots=available_timeslots
            )
        else:
            messagebox.showwarning("Fehler", "Die ausgewählte Aufgabe konnte nicht gefunden werden.")
    
    def on_task_double_click(self, event):
        """Behandelt Doppelklick auf eine Aufgabe"""
        # Die gleiche Funktion aufrufen wie beim Button-Klick
        self.show_task_details()
    
    def update_task(self, updated_task):
        """Aktualisiert eine Aufgabe in der Liste und aktualisiert die Anzeige"""
        # Aktualisieren in der aktuellen Aufgabenliste
        for i, task in enumerate(self.current_tasks):
            if task.id == updated_task.id:
                self.current_tasks[i] = updated_task
                break
        
        # Auch in der Lösung aktualisieren, falls vorhanden
        if self.current_solution:
            solution_tasks = self.current_solution.get_tasks()
            for i, task in enumerate(solution_tasks):
                if task.id == updated_task.id:
                    solution_tasks[i] = updated_task
                    break
        
        # Anzeige aktualisieren
        self.update_task_list(self.current_tasks, self.current_solution)
    
    def show_employee_details(self):
        """Öffnet den Mitarbeiter-Detail-Dialog für den ausgewählten Mitarbeiter"""
        # Ausgewähltes Item holen
        selected_item = self.employee_tree.selection()
        
        if not selected_item:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie einen Mitarbeiter aus der Liste aus.")
            return
        
        # Daten aus dem ausgewählten Item extrahieren
        item_data = self.employee_tree.item(selected_item[0], "values")
        
        # Mitarbeiter-ID sollte die versteckte Spalte sein
        if len(item_data) >= 5:  # Wir erwarten mindestens 5 Spalten (name, skills, preferred, status, id)
            employee_id = item_data[4]  # ID ist in index 4 (die fünfte Spalte)
            
            # Den ausgewählten Mitarbeiter finden
            employee = next((e for e in self.current_employees if e.id == employee_id), None)
            
            if employee:
                # Zugewiesene Aufgaben für diesen Mitarbeiter ermitteln
                assigned_tasks = []
                
                if self.current_solution:
                    # Wenn wir eine Lösung haben, prüfen wir alle Aufgaben
                    for task in self.current_solution.get_tasks():
                        if hasattr(task, 'get_assigned_employee') and task.get_assigned_employee():
                            if task.get_assigned_employee().id == employee_id:
                                assigned_tasks.append(task)
                else:
                    # Alternativ prüfen wir die aktuellen Aufgaben
                    for task in self.current_tasks:
                        if hasattr(task, 'get_assigned_employee') and task.get_assigned_employee():
                            if task.get_assigned_employee().id == employee_id:
                                assigned_tasks.append(task)
                
                # Den Mitarbeiter-Detail-Dialog öffnen
                EmployeeDialog(
                    self.employee_tab, 
                    self.available_skills,
                    employee=employee,
                    assigned_tasks=assigned_tasks,
                    on_update=self.update_employee,
                    title=f"Mitarbeiterdetails: {employee.name}",
                    db_manager=self.db_manger
                )
            else:
                messagebox.showwarning("Fehler", "Der ausgewählte Mitarbeiter konnte nicht gefunden werden.")
        else:
            messagebox.showwarning("Fehler", "Unvollständige Mitarbeiterdaten.")

    def on_employee_double_click(self, event):
        """Behandelt Doppelklick auf einen Mitarbeiter"""
        # Die gleiche Funktion aufrufen wie beim Button-Klick
        self.show_employee_details()

    def update_employee(self, updated_employee):
        """Aktualisiert einen Mitarbeiter in der Liste und aktualisiert die Anzeige"""
        if hasattr(self, 'current_employees'):
            # Den alten Mitarbeiter durch den aktualisierten ersetzen
            for i, emp in enumerate(self.current_employees):
                if emp.id == updated_employee.id:
                    self.current_employees[i] = updated_employee
                    break
            
            # Anzeige aktualisieren
            self.update_employee_list(self.current_employees)

    def update_employee_list(self, employees=None):
        """Aktualisiert die Mitarbeiterliste im Treeview"""
        # Bestehende Einträge löschen
        for item in self.employee_tree.get_children():
            self.employee_tree.delete(item)
        
        if not employees:
            self.employee_tree.insert("", "end", values=("Keine Daten", "", ""))
            return
        
        # Aktuelle Mitarbeiterliste speichern
        self.current_employees = employees
        
        # Spalten anpassen, um Platz für bevorzugte Fähigkeiten zu schaffen
        self.employee_tree["columns"] = ("name", "skills", "preferred", "status", "id")
        self.employee_tree.heading("name", text="Name")
        self.employee_tree.heading("skills", text="Fähigkeiten")
        self.employee_tree.heading("preferred", text="Bevorzugte")
        self.employee_tree.heading("status", text="Status")
        
        # ID-Spalte verstecken
        self.employee_tree["displaycolumns"] = ("name", "skills", "preferred", "status")
        
        self.employee_tree.column("name", width=120)
        self.employee_tree.column("skills", width=200)
        self.employee_tree.column("preferred", width=200)
        self.employee_tree.column("status", width=80)
        
        # Mitarbeiter hinzufügen
        for employee in employees:
            # Status-Text formatieren
            status_text = employee.status.value
            if status_text == "available":
                status_text = "Verfügbar"
            elif status_text == "busy":
                status_text = "Beschäftigt"
            elif status_text == "off":
                status_text = "Abwesend"
            
            # Skills formatieren
            skills_text = ", ".join(sorted(employee.skills))
            if len(skills_text) > 40:
                skills_text = skills_text[:37] + "..."
            
            # Bevorzugte Skills formatieren
            if hasattr(employee, 'preferred_skills') and employee.preferred_skills:
                preferred_text = ", ".join(sorted(employee.preferred_skills))
                if len(preferred_text) > 40:
                    preferred_text = preferred_text[:37] + "..."
            else:
                preferred_text = "Keine"
            
            # Mitarbeiter zur Tabelle hinzufügen
            self.employee_tree.insert("", "end", values=(
                employee.name, 
                skills_text, 
                preferred_text,
                status_text,
                employee.id  # ID-Spalte (versteckt)
            ))

    def clear_stats(self):
        """Leert die Statistik-Anzeige"""
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # Platzhalter
        ttk.Label(self.stats_frame, text="Keine Statistik verfügbar.\nErstelle einen Zeitplan.").pack(pady=20)
    
    def update_task_list(self, tasks=None, solution=None):
        """Aktualisiert die Aufgabenliste im Treeview"""
        # Lösung speichern für Aufgabenzuweisungen
        if solution:
            self.current_solution = solution
            
        # Schedule-Referenz speichern, falls in Lösung vorhanden
        if hasattr(solution, 'schedule'):
            self.schedule = solution.schedule
        
        # Bestehende Einträge löschen
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        if not tasks:
            self.task_tree.insert("", "end", values=("Keine Daten", "", "", "", ""))
            self.current_tasks = []
            return
        
        # Erweitere Spalten, um Name/Bezeichnung anzuzeigen
        self.task_tree["columns"] = ("id", "name", "duration", "skills", "assigned")
        self.task_tree.heading("id", text="ID")
        self.task_tree.heading("name", text="Bezeichnung")
        self.task_tree.heading("duration", text="Dauer (h)")
        self.task_tree.heading("skills", text="Benötigte Fähigkeiten")
        self.task_tree.heading("assigned", text="Zugewiesen")
        
        # Aktuelle Aufgabenliste speichern
        self.current_tasks = tasks
        
        # Aufgaben hinzufügen
        for task in tasks:
            # Zugewiesenen Mitarbeiter ermitteln (wenn vorhanden)
            assigned_text = "Nicht zugewiesen"
            if hasattr(task, 'get_assigned_employee') and task.get_assigned_employee():
                assigned_text = task.get_assigned_employee().name
            
            # Skills formatieren
            skills_text = ", ".join(task.required_skills)
            
            # Task-Name ermitteln
            task_name = getattr(task, 'name', task.id) if hasattr(task, 'name') else task.id
            
            # Aufgabe zur Tabelle hinzufügen
            self.task_tree.insert("", "end", values=(
                task.id,
                task_name,
                task.duration,
                skills_text[:40] + "..." if len(skills_text) > 40 else skills_text,
                assigned_text
            ))

    # Neue Methoden zum Hinzufügen und Entfernen von Mitarbeitern/Aufgaben
    def add_new_employee(self):
        """Lädt und wählt einen bestehenden Mitarbeiter aus der Datenbank für den aktuellen Zeitplan"""
        # App-Referenz holen
        app = self._get_app_reference()
        
        if not app or not hasattr(app, 'schedule') or not app.schedule:
            messagebox.showinfo("Hinweis", "Bitte erstellen oder laden Sie zuerst einen Zeitplan.")
            return
        
        # Prüfen, ob ein Datenbankmanager verfügbar ist
        if not self.db_manger or not hasattr(self.db_manger, 'get_all_employees'):
            messagebox.showwarning("Warnung", "Datenbank-Verbindung nicht verfügbar.")
            return
        
        try:
            # IDs aller Mitarbeiter laden
            employee_records = self.db_manger.get_all_employees()
            
            if not employee_records:
                messagebox.showinfo("Information", "Keine Mitarbeiter in der Datenbank gefunden.")
                return
                
            # Mitarbeiter laden
            employees = []
            for emp_record in employee_records:
                emp_id = emp_record[0]  # ID aus dem Datensatz
                employee = self.db_manger.load_employee(emp_id)
                if employee:
                    # Das Employee-Objekt direkt verwenden
                    employees.append(employee)
            
            if not employees:
                messagebox.showinfo("Information", "Keine Mitarbeiter in der Datenbank gefunden.")
                return
        
            # Dialog zur Auswahl der Mitarbeiter anzeigen
            from dialogs.employee_selection_dialog import EmployeeSelectorDialog
            dialog = EmployeeSelectorDialog(self.employee_tab, employees)
            
            if dialog.result:
                # Ausgewählte Mitarbeiter zum Schedule hinzufügen
                for employee in dialog.result:
                    # Prüfen, ob der Mitarbeiter bereits im Schedule ist
                    if not any(e.id == employee.id for e in app.schedule.employees):
                        app.schedule.employees.append(employee)
                
                # Anzeige aktualisieren
                self.update_employee_list(app.schedule.employees)

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Mitarbeiter: {str(e)}")
            traceback.print_exc()



    def remove_selected_employees(self):
        """Entfernt ausgewählte Mitarbeiter aus der Schedule"""
        selected_items = self.employee_tree.selection()
        
        if not selected_items:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie mindestens einen Mitarbeiter zum Entfernen aus.")
            return
        
        # Bestätigung einholen
        if not messagebox.askyesno("Mitarbeiter entfernen",
                              f"Möchten Sie {len(selected_items)} Mitarbeiter wirklich aus dem Zeitplan entfernen?"):
            return
        
        # Mitarbeiter-IDs sammeln
        employee_ids = []
        for item_id in selected_items:
            values = self.employee_tree.item(item_id, "values")
            if len(values) >= 5:  # Wir erwarten mindestens 5 Werte mit der ID am Ende
                employee_id = values[4]  # ID ist an Position 4
                employee_ids.append(employee_id)
        
        # App-Referenz holen
        app = self._get_app_reference()
        if app and hasattr(app, 'remove_employees_from_schedule'):
            app.remove_employees_from_schedule(employee_ids)
        else:
            # Direkte Entfernung, wenn keine App-Referenz gefunden
            if hasattr(self, 'current_employees'):
                self.current_employees = [e for e in self.current_employees if e.id not in employee_ids]
                self.update_employee_list(self.current_employees)

    def add_new_task(self):
        """Öffnet den Dialog zum Hinzufügen einer neuen Aufgabe zur aktuellen Schedule"""
        # App-Referenz holen
        app = self._get_app_reference()
        
        if not app or not hasattr(app, 'schedule') or not app.schedule:
            messagebox.showinfo("Hinweis", "Bitte erstellen oder laden Sie zuerst einen Zeitplan.")
            return
        
        # Den TaskDialog verwenden
        dialog = TaskDialog(
            self.task_tab,
            self.available_skills,
            db_manager=self.db_manger
        )
        
        if dialog.result:
            if app and hasattr(app, 'add_task_to_schedule'):
                app.add_task_to_schedule(dialog.result)
            else:
                # Fallback: Direkt zur aktuellen Liste hinzufügen
                if hasattr(self, 'current_tasks'):
                    self.current_tasks.append(dialog.result)
                    self.update_task_list(self.current_tasks, getattr(self, 'current_solution', None))
                else:
                    messagebox.showinfo("Fehler", "Konnte Aufgabe nicht hinzufügen: Keine Referenz zur Hauptanwendung gefunden.")

    def remove_selected_tasks(self):
        """Entfernt ausgewählte Aufgaben aus der Schedule"""
        selected_items = self.task_tree.selection()
        
        if not selected_items:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie mindestens eine Aufgabe zum Entfernen aus.")
            return
        
        # Bestätigung einholen
        if not messagebox.askyesno("Aufgaben entfernen",
                              f"Möchten Sie {len(selected_items)} Aufgabe(n) wirklich aus dem Zeitplan entfernen?"):
            return
        
        # Aufgaben-IDs sammeln
        task_ids = []
        for item_id in selected_items:
            values = self.task_tree.item(item_id, "values")
            if values:
                task_id = values[0]  # ID ist die erste Spalte
                task_ids.append(task_id)
        
        # App-Referenz holen
        app = self._get_app_reference()
        if app and hasattr(app, 'remove_tasks_from_schedule'):
            app.remove_tasks_from_schedule(task_ids)
        else:
            # Direkte Entfernung, wenn keine App-Referenz gefunden
            if hasattr(self, 'current_tasks'):
                self.current_tasks = [t for t in self.current_tasks if t.id not in task_ids]
                self.update_task_list(self.current_tasks, getattr(self, 'current_solution', None))
    
    def _get_app_reference(self):
        """Verbesserte Hilfsmethode, um eine Referenz auf die Hauptanwendung zu erhalten"""
        # Versuche direkter Zugriff auf die DB-Manager-Instanz
        if hasattr(self, 'db_manger') and hasattr(self.db_manger, '_app'):
            return self.db_manger._app
            
        # Versuche über eine eingebaute Link-Variable
        if hasattr(self, 'app'):
            return self.app
            
        # Versuche über die Widget-Hierarchie
        parent = self.frame.master
        while parent:
            # Prüfen auf typische Attribute der Hauptanwendung
            if hasattr(parent, 'schedule') and hasattr(parent, 'solution'):
                return parent
            # Spezifische Prüfung auf die SchedulingApp-Klasse
            if hasattr(parent, '__class__') and parent.__class__.__name__ == 'SchedulingApp':
                return parent
            # Versuche über das MainView-Objekt
            if hasattr(parent, 'controller'):
                return parent.controller
            # Navigiere weiter hoch in der Hierarchie
            if hasattr(parent, 'master'):
                parent = parent.master
            else:
                break
        return None