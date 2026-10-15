import tkinter as tk
from tkinter import ttk, messagebox
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from core import Employee, Task, Schedule

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from core import Employee, Task, Schedule


import tkinter as tk
from tkinter import ttk, messagebox
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from core import Employee, Task, Schedule

class FeedbackDialog(tk.Toplevel):
    """Dialog zur Abgabe von Feedback zu einem Zeitplan"""
    
    def __init__(self, parent, employee: Employee, schedule: Schedule, feedback_manager=None):
        """
        Initialisiert den Feedback-Dialog
        
        Args:
            parent: Eltern-Widget
            employee: Der Mitarbeiter, der Feedback gibt
            schedule: Der zu bewertende Zeitplan
            feedback_manager: Optional - Datenbankmanager für Feedback
        """
        super().__init__(parent)
        self.title(f"Feedback für {schedule.name}")
        self.transient(parent)
        self.resizable(True, True)
        self.geometry("800x600")
        
        self.employee = employee
        self.schedule = schedule
        self.feedback_manager = feedback_manager
        self.result = None
        
        # Aufgaben für diesen Mitarbeiter sammeln
        self.assigned_tasks = self._get_assigned_tasks()
        
        # Dictionary zum Speichern der Bewertungen
        # Format: {task_id: rating_value}
        # Standardisierte Rating Werte: 0 = Zustimmung, -1 = Ablehnung
        self.task_ratings = {}
        
        # Dictionary zum Verfolgen des Bewertungsstatus
        # Format: {task_id: "rated"/"unrated"}
        self.rating_status = {task.id: "unrated" for task in self.assigned_tasks}
        
        self.create_widgets()
        
        # Dialog modal machen
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.focus_set()
        
        # Warten auf das Schließen des Fensters
        parent.wait_window(self)
    
    def _get_assigned_tasks(self) -> List[Task]:
        """
        Sammelt alle Aufgaben, die dem Mitarbeiter zugewiesen sind
        
        Returns:
            Liste der zugewiesenen Aufgaben
        """
        assigned_tasks = []
        
        for task in self.schedule.tasks:
            # Verschiedene Methoden zur Überprüfung der Zuweisung
            if hasattr(task, 'get_assigned_employee'):
                assigned_employee = task.get_assigned_employee()
                if assigned_employee and assigned_employee.id == self.employee.id:
                    # Überprüfen, ob die Aufgabe bereits bewertet wurde
                    if task.status != "bewertet":
                        assigned_tasks.append(task)
            elif hasattr(task, '_assigned_employee'):
                # Fallback für alternative Implementierungen
                if task._assigned_employee and task._assigned_employee.id == self.employee.id:
                    # Überprüfen, ob die Aufgabe bereits bewertet wurde
                    if task.status != "bewertet":
                        assigned_tasks.append(task)
        
        return assigned_tasks
    
    def create_widgets(self):
        """Erstellt die UI-Elemente"""
        # Hauptframe mit Padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Überschrift und Einleitung
        ttk.Label(main_frame, text=f"Bewertung für Zeitplan: {self.schedule.name}", 
                 font=('TkDefaultFont', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        ttk.Label(main_frame, text=f"Mitarbeiter: {self.employee.name}", 
                 font=('TkDefaultFont', 10)).pack(anchor='w', pady=(0, 5))
        
        ttk.Label(main_frame, text="Bitte bewerten Sie Ihre Aufgabenzuweisungen:", 
                 wraplength=650).pack(anchor='w', pady=(0, 10))
        
        # Bewertungsbuttons oberhalb der Aufgabenliste
        rating_buttons_frame = ttk.Frame(main_frame)
        rating_buttons_frame.pack(fill='x', pady=(0, 5))
        
        # Anleitung für die Bewertung
        ttk.Label(rating_buttons_frame, 
                 text="Aufgabe auswählen und dann bewerten:").pack(side='left', padx=(0, 10))
        
        # Zustimmung-Button
        self.agree_button = ttk.Button(
            rating_buttons_frame, 
            text="Find ich gut",
            command=lambda: self.rate_selected_task(0),  # 0 für Zustimmung (standardisiert)
            state="disabled"
        )
        self.agree_button.pack(side='left', padx=5)
        
        # Widerspruch-Button
        self.disagree_button = ttk.Button(
            rating_buttons_frame, 
            text="Lieber nicht",
            command=lambda: self.rate_selected_task(-1),  # -1 für Ablehnung (standardisiert)
            state="disabled"
        )
        self.disagree_button.pack(side='left', padx=5)
        
        # Scrollbarer Bereich für die Aufgabenliste
        task_frame = ttk.Frame(main_frame)
        task_frame.pack(fill='both', expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(task_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview für Aufgabenliste
        columns = ("id", "time", "duration", "skills", "rating", "status")
        self.tasks_tree = ttk.Treeview(task_frame, columns=columns, 
                                      show="headings", yscrollcommand=scrollbar.set,
                                      selectmode="browse")  # Nur einen Eintrag auswählen
        
        self.tasks_tree.heading("id", text="Aufgabe")
        self.tasks_tree.heading("time", text="Zeit")
        self.tasks_tree.heading("duration", text="Dauer (h)")
        self.tasks_tree.heading("skills", text="Benötigte Fähigkeiten")
        self.tasks_tree.heading("rating", text="Bewertung")
        self.tasks_tree.heading("status", text="Status")
        
        self.tasks_tree.column("id", width=100)
        self.tasks_tree.column("time", width=150)
        self.tasks_tree.column("duration", width=70, anchor="center")
        self.tasks_tree.column("skills", width=200)
        self.tasks_tree.column("rating", width=80)
        self.tasks_tree.column("status", width=80)
        
        self.tasks_tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.tasks_tree.yview)
        
        # Event-Binding für Auswahl
        self.tasks_tree.bind("<<TreeviewSelect>>", self.on_task_selected)
        
        # Aufgaben hinzufügen
        if self.assigned_tasks:
            for task in self.assigned_tasks:
                # Zeitinformationen
                time_text = "Nicht geplant"
                if hasattr(task, 'get_time_slot') and task.get_time_slot():
                    time_slot = task.get_time_slot()
                    start_time = time_slot.start_time
                    end_time = start_time + timedelta(hours=task.duration)
                    time_text = f"{start_time.strftime('%d.%m.%Y %H:%M')} - {end_time.strftime('%H:%M')}"
                
                # Skills formatieren
                skills_text = ", ".join(sorted(task.required_skills))
                if len(skills_text) > 40:
                    skills_text = skills_text[:37] + "..."
                
                # Initiale Bewertung ist "Nicht bewertet"
                rating_text = "Nicht bewertet"
                status_text = "Unbewertet"
                
                # Aufgabe zur Treeview hinzufügen
                self.tasks_tree.insert("", "end", values=(
                    task.id,
                    time_text,
                    task.duration,
                    skills_text,
                    rating_text,
                    status_text
                ), tags=(task.id,))
        else:
            # Platzhaltereintrag
            self.tasks_tree.insert("", "end", values=("Keine Aufgaben", "", "", "", "Keine", "N/A"))
        
        # Legende für die Bewertung
        legend_frame = ttk.LabelFrame(main_frame, text="Bewertungsskala")
        legend_frame.pack(fill='x', pady=(5, 10))
        
        ttk.Label(legend_frame, text="'Find ich gut' = Zustimmung (0), 'Lieber nicht' = Ablehnung (-1)").pack(
            anchor='w', padx=5, pady=5)
        
        # Gesamtkommentar
        comment_frame = ttk.LabelFrame(main_frame, text="Kommentar (optional)")
        comment_frame.pack(fill='x', pady=10)
        
        self.comment_text = tk.Text(comment_frame, wrap='word', height=3)
        self.comment_text.pack(fill='x', padx=5, pady=5)
        
        # Button-Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Status-Anzeige
        self.status_var = tk.StringVar(value="0 von {} Aufgaben bewertet".format(len(self.assigned_tasks)))
        status_label = ttk.Label(button_frame, textvariable=self.status_var)
        status_label.pack(side='left')
        
        # Speichern- und Abbrechen-Buttons
        ttk.Button(button_frame, text="Feedback senden", 
                  command=self.on_submit).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Abbrechen", 
                  command=self.on_cancel).pack(side='right')
    
    def on_task_selected(self, event):
        """Behandelt die Auswahl einer Aufgabe in der Treeview"""
        selected_items = self.tasks_tree.selection()
        
        if not selected_items:
            # Keine Auswahl - Buttons deaktivieren
            self.agree_button.config(state="disabled")
            self.disagree_button.config(state="disabled")
            return
        
        # Ausgewählte Aufgabe
        selected_item = selected_items[0]
        values = self.tasks_tree.item(selected_item, "values")
        task_id = values[0]  # ID ist in der ersten Spalte
        status = values[5]   # Status ist in der letzten Spalte
        
        # Buttons aktivieren, wenn die Aufgabe noch nicht bewertet wurde
        button_state = "normal" if status != "Bewertet" else "disabled"
        self.agree_button.config(state=button_state)
        self.disagree_button.config(state=button_state)
    
    def rate_selected_task(self, rating: int):
        """
        Bewertet die aktuell ausgewählte Aufgabe.
        Standardisierter Ansatz: 0 = Zustimmung, -1 = Ablehnung
        """
        selected_items = self.tasks_tree.selection()
        
        if not selected_items:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie eine Aufgabe aus.")
            return
        
        # Ausgewählte Aufgabe
        selected_item = selected_items[0]
        values = self.tasks_tree.item(selected_item, "values")
        task_id = values[0]  # ID ist in der ersten Spalte
        
        # Find the actual task object
        task = next((t for t in self.assigned_tasks if t.id == task_id), None)
        if task:
            # Task status aktualisieren
            task.status = "bewertet"
            
            # Feedback-Score direkt im Task-Objekt setzen
            if hasattr(task, 'set_feedback_score'):
                task.set_feedback_score(rating)  # Direkter Wert ohne Umrechnung
            elif hasattr(task, 'feedback_score'):
                task.feedback_score = rating  # Direkter Wert ohne Umrechnung
        
        # Rating in Dictionary speichern
        self.task_ratings[(task_id, self.employee.id)] = rating
        
        # Status aktualisieren
        self.rating_status[task_id] = "rated"
        
        # Anzeige aktualisieren
        rating_text = self._get_rating_text(rating)
        self.tasks_tree.item(selected_item, values=(
            values[0],  # ID
            values[1],  # Zeit
            values[2],  # Dauer
            values[3],  # Skills
            rating_text,  # Bewertung
            "Bewertet"   # Status
        ))
        
        # Buttons deaktivieren
        self.agree_button.config(state="disabled")
        self.disagree_button.config(state="disabled")
        
        # Status-Anzeige aktualisieren
        rated_count = sum(1 for status in self.rating_status.values() if status == "rated")
        self.status_var.set(f"{rated_count} von {len(self.assigned_tasks)} Aufgaben bewertet")
        
        # Wenn Feedback-Manager verfügbar ist, sofort in der Datenbank speichern
        if self.feedback_manager and hasattr(self.feedback_manager, 'save_task_feedback'):
            try:
                # Iteration des Schedules ermitteln
                iteration = getattr(self.schedule, 'iteration', 1)
                
                # Kommentar aus dem Textfeld holen (Optional)
                comment = self.comment_text.get("1.0", "end-1c").strip()
                
                # In der Datenbank speichern - standardisierte Werte verwenden
                success = self.feedback_manager.save_task_feedback(
                    self.schedule.id,
                    self.employee.id,
                    task_id,
                    rating,  # Standardisierter Wert: 0 oder -1
                    comment,
                    iteration
                )
                
                if not success:
                    print(f"Warnung: Feedback für Aufgabe {task_id} konnte nicht gespeichert werden")
            except Exception as e:
                print(f"Fehler beim Speichern des Feedbacks für Aufgabe {task_id}: {str(e)}")
    
    def _get_rating_text(self, rating: int) -> str:
        """Gibt den Text für einen Bewertungswert zurück"""
        if rating == -1:
            return "Lieber nicht"
        elif rating == 0:
            return "Find ich gut"
        else:
            return "Nicht bewertet"
    
    def on_submit(self):
        """Verarbeitet das Absenden des Feedbacks"""
        # Prüfen, ob alle Aufgaben bewertet wurden
        unrated_tasks = [task_id for task_id, status in self.rating_status.items() if status != "rated"]
        if unrated_tasks and len(self.assigned_tasks) > 0:
            if not messagebox.askyesno("Unvollständige Bewertung", 
                                      f"Es wurden {len(unrated_tasks)} von {len(self.assigned_tasks)} Aufgaben nicht bewertet.\n\nMöchten Sie das Feedback trotzdem absenden?"):
                return
        
        # Ergebnis zurückgeben - das direkte Speichern in der Datenbank wurde bereits erledigt
        self.result = {
            "employee_id": self.employee.id,
            "task_ratings": self.task_ratings,
            "comment": self.comment_text.get("1.0", "end-1c").strip()
        }
        
        messagebox.showinfo("Erfolg", "Vielen Dank für Ihr Feedback!")
        self.destroy()
    
    def on_cancel(self):
        """Schließt den Dialog ohne zu speichern"""
        if sum(1 for status in self.rating_status.values() if status == "rated") > 0:
            if not messagebox.askyesno("Abbrechen", "Sie haben bereits Bewertungen abgegeben. Möchten Sie wirklich abbrechen?"):
                return
        
        self.result = None
        self.destroy()









class EmployeeSelectionDialog(tk.Toplevel):
    """Einfacher Dialog zur Auswahl eines Mitarbeiters"""
    
    def __init__(self, parent, employees, title="Mitarbeiter auswählen"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x300")
        self.transient(parent)
        self.resizable(False, False)
        
        self.employees = employees
        self.result = None
        
        self._create_widgets()
        
        # Dialog modal machen
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.focus_set()
        
        # Warten, bis dieses Fenster zerstört wird
        parent.wait_window(self)
    
    def _create_widgets(self):
        """Erstellt die UI-Elemente"""
        # Hauptframe
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Überschrift
        ttk.Label(main_frame, 
                  text="Wählen Sie einen Mitarbeiter", 
                  font=('TkDefaultFont', 12, 'bold')
        ).pack(anchor='w', pady=(0, 10))
        
        # Suchfeld
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(search_frame, text="Suche:").pack(side='left')
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, 
                                 textvariable=self.search_var, 
                                 width=30)
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<KeyRelease>', self._filter_employees)
        
        # Mitarbeiterliste
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.employee_listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            font=('TkDefaultFont', 10)
        )
        self.employee_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.employee_listbox.yview)
        
        # Dopppelklick-Binding für schnelle Auswahl
        self.employee_listbox.bind('<Double-1>', lambda e: self.on_select())
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        self.select_button = ttk.Button(
            button_frame, 
            text="Auswählen", 
            command=self.on_select, 
            state='disabled'
        )
        self.select_button.pack(side='right', padx=(5, 0))
        
        ttk.Button(
            button_frame, 
            text="Abbrechen", 
            command=self.on_cancel
        ).pack(side='right')
        
        # Mitarbeiter zur Liste hinzufügen
        self._populate_employee_list()
        
        # Selektions-Event
        self.employee_listbox.bind('<<ListboxSelect>>', self._on_selection_change)
    
    def _populate_employee_list(self):
        """Füllt die Mitarbeiterliste"""
        self.employee_listbox.delete(0, tk.END)
        self.employee_mapping = {}
        
        for employee in self.employees:
            # Formatiere Mitarbeiter-Anzeige
            display_text = f"{employee.name} ({', '.join(sorted(employee.skills)[:2])})"
            self.employee_listbox.insert(tk.END, display_text)
            # Mapping zwischen Listbox-Index und Employee-Objekt
            self.employee_mapping[self.employee_listbox.size() - 1] = employee
    
    def _filter_employees(self, event=None):
        """Filtert die Mitarbeiterliste basierend auf der Suche"""
        search_term = self.search_var.get().lower()
        
        # Lösche alte Liste
        self.employee_listbox.delete(0, tk.END)
        self.employee_mapping.clear()
        
        for employee in self.employees:
            # Suche in Name und Skills
            search_text = f"{employee.name.lower()} {' '.join(employee.skills).lower()}"
            
            if search_term in search_text:
                display_text = f"{employee.name} ({', '.join(sorted(employee.skills)[:2])})"
                self.employee_listbox.insert(tk.END, display_text)
                self.employee_mapping[self.employee_listbox.size() - 1] = employee
    
    def _on_selection_change(self, event):
        """Aktiviert/Deaktiviert den Auswählen-Button"""
        selection = self.employee_listbox.curselection()
        
        if selection:
            self.select_button.config(state='normal')
        else:
            self.select_button.config(state='disabled')
    
    def on_select(self):
        """Verarbeitet die Auswahl eines Mitarbeiters"""
        selection = self.employee_listbox.curselection()
        
        if not selection:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie einen Mitarbeiter.")
            return
        
        # Den ersten (und einzigen) ausgewählten Index nehmen
        index = selection[0]
        
        # Mitarbeiter-Objekt aus dem Mapping holen
        selected_employee = self.employee_mapping.get(index)
        
        if selected_employee:
            self.result = selected_employee
            self.destroy()
        else:
            messagebox.showerror("Fehler", "Fehler bei der Mitarbeiterauswahl.")
    
    def on_cancel(self):
        """Schließt den Dialog ohne Auswahl"""
        self.result = None
        self.destroy()