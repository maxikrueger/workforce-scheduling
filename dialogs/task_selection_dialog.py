# task_selector_dialog.py
import tkinter as tk
from tkinter import ttk


class TaskSelectorDialog(tk.Toplevel):
    """Dialog zum Auswählen bestehender Aufgaben aus der Datenbank"""
    
    def __init__(self, parent, tasks, title="Aufgaben auswählen"):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.resizable(True, True)
        self.geometry("700x400")  # Etwas breiter für die zusätzliche Spalte
        
        self.tasks = tasks
        self.selected_tasks = []
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
        # Hauptcontainer mit Padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Beschreibung
        ttk.Label(main_frame, text="Wählen Sie Aufgaben aus der Datenbank aus:", 
                wraplength=500).pack(anchor='w', pady=(0, 10))
        
        # Frame für Aufgabenliste
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview für Aufgabenliste mit zusätzlicher Name-Spalte
        self.task_tree = ttk.Treeview(
            list_frame, 
            columns=("id", "name", "duration", "skills"),
            show="headings", 
            yscrollcommand=scrollbar.set,
            selectmode="extended"  # Mehrfachauswahl erlauben
        )
        
        # Spalten konfigurieren
        self.task_tree.heading("id", text="ID")
        self.task_tree.heading("name", text="Bezeichnung")
        self.task_tree.heading("duration", text="Dauer (h)")
        self.task_tree.heading("skills", text="Benötigte Fähigkeiten")
        
        self.task_tree.column("id", width=100)
        self.task_tree.column("name", width=150)
        self.task_tree.column("duration", width=80, anchor='center')
        self.task_tree.column("skills", width=350)
        
        self.task_tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.task_tree.yview)
        
        # Aufgaben zur Treeview hinzufügen
        for task in self.tasks:
            # Skills formatieren
            skills_text = ", ".join(sorted(task.required_skills))
            if len(skills_text) > 40:
                skills_text = skills_text[:37] + "..."
            
            # Aufgabenname ermitteln (falls vorhanden)
            task_name = getattr(task, 'name', task.id) if hasattr(task, 'name') else task.id
            
            # Eintrag zur Liste hinzufügen
            self.task_tree.insert("", "end", values=(
                task.id, 
                task_name,
                task.duration, 
                skills_text
            ), tags=(task.id,))
        
        # Optionale Suchfunktion
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill='x', pady=5)
        
        ttk.Label(search_frame, text="Suche:").pack(side='left')
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=5)
        
        ttk.Button(search_frame, text="Suchen", 
                  command=self.search_tasks).pack(side='left')
        
        # Button-Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Auswählen-Button (deaktiviert bei keiner Auswahl)
        self.select_button = ttk.Button(button_frame, text="Auswählen", 
                                      command=self.on_select, state="disabled")
        self.select_button.pack(side='right', padx=(5, 0))
        
        ttk.Button(button_frame, text="Abbrechen", 
                  command=self.on_cancel).pack(side='right')
        
        # Binding für Auswahländerungen
        self.task_tree.bind("<<TreeviewSelect>>", self.on_selection_change)
        
        # Doppelklick-Binding für schnelle Auswahl
        self.task_tree.bind("<Double-1>", lambda e: self.on_select())
    
    def on_selection_change(self, event):
        """Aktualisiert den Zustand des Auswählen-Buttons"""
        selected = self.task_tree.selection()
        self.select_button.config(state="normal" if selected else "disabled")
    
    def search_tasks(self):
        """Filtert die Aufgabenliste basierend auf dem Suchtext"""
        search_text = self.search_var.get().lower()
        
        # Alle Einträge entfernen
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Gefilterte Aufgaben hinzufügen
        for task in self.tasks:
            # Name für die Suche vorbereiten
            task_name = getattr(task, 'name', task.id) if hasattr(task, 'name') else task.id
            
            # Suche in ID, Name und Skills
            if (search_text in task.id.lower() or 
                search_text in task_name.lower() or 
                any(search_text in skill.lower() for skill in task.required_skills)):
                
                # Skills formatieren
                skills_text = ", ".join(sorted(task.required_skills))
                if len(skills_text) > 40:
                    skills_text = skills_text[:37] + "..."
                
                # Eintrag zur Liste hinzufügen
                self.task_tree.insert("", "end", values=(
                    task.id, 
                    task_name,
                    task.duration, 
                    skills_text
                ), tags=(task.id,))
    
    def on_select(self):
        """Verarbeitet den Klick auf den 'Auswählen'-Button"""
        selected_items = self.task_tree.selection()
        
        if not selected_items:
            return
        
        # Ausgewählte Aufgaben sammeln
        selected_tasks = []
        for item in selected_items:
            # ID vom Tag bekommen
            for task in self.tasks:
                if task.id in self.task_tree.item(item, "tags"):
                    selected_tasks.append(task)
                    break
        
        self.result = selected_tasks
        self.destroy()
    
    def on_cancel(self):
        """Verarbeitet den Klick auf den 'Abbrechen'-Button"""
        self.result = None
        self.destroy()