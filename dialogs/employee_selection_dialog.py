# employee_selector_dialog.py
import tkinter as tk
from tkinter import ttk

class EmployeeSelectorDialog(tk.Toplevel):
    """Dialog zum Auswählen bestehender Mitarbeiter aus der Datenbank"""
    
    def __init__(self, parent, employees, title="Mitarbeiter auswählen"):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.resizable(True, True)
        self.geometry("600x400")
        
        self.employees = employees
        self.selected_employees = []
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
        ttk.Label(main_frame, text="Wählen Sie Mitarbeiter aus der Datenbank aus:", 
                wraplength=500).pack(anchor='w', pady=(0, 10))
        
        # Frame für Mitarbeiterliste
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview für Mitarbeiterliste
        self.employee_tree = ttk.Treeview(
            list_frame, 
            columns=("name", "skills", "status"),
            show="headings", 
            yscrollcommand=scrollbar.set,
            selectmode="extended"  # Mehrfachauswahl erlauben
        )
        
        # Spalten konfigurieren
        self.employee_tree.heading("name", text="Name")
        self.employee_tree.heading("skills", text="Fähigkeiten")
        self.employee_tree.heading("status", text="Status")
        
        self.employee_tree.column("name", width=150)
        self.employee_tree.column("skills", width=300)
        self.employee_tree.column("status", width=100)
        
        self.employee_tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.employee_tree.yview)
        
        # Mitarbeiter zur Treeview hinzufügen
        for employee in self.employees:
            # Skills formatieren
            skills_text = ", ".join(sorted(employee.skills))
            if len(skills_text) > 40:
                skills_text = skills_text[:37] + "..."
            
            # Status-Text formatieren
            status_text = employee.status.value
            if status_text == "available":
                status_text = "Verfügbar"
            elif status_text == "busy":
                status_text = "Beschäftigt"
            elif status_text == "off":
                status_text = "Abwesend"
            
            # Eintrag zur Liste hinzufügen
            self.employee_tree.insert("", "end", values=(
                employee.name, 
                skills_text, 
                status_text
            ), tags=(employee.id,))
        
        # Optionale Suchfunktion
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill='x', pady=5)
        
        ttk.Label(search_frame, text="Suche:").pack(side='left')
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=5)
        
        ttk.Button(search_frame, text="Suchen", 
                  command=self.search_employees).pack(side='left')
        
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
        self.employee_tree.bind("<<TreeviewSelect>>", self.on_selection_change)
        
        # Doppelklick-Binding für schnelle Auswahl
        self.employee_tree.bind("<Double-1>", lambda e: self.on_select())
    
    def on_selection_change(self, event):
        """Aktualisiert den Zustand des Auswählen-Buttons"""
        selected = self.employee_tree.selection()
        self.select_button.config(state="normal" if selected else "disabled")
    
    def search_employees(self):
        """Filtert die Mitarbeiterliste basierend auf dem Suchtext"""
        search_text = self.search_var.get().lower()
        
        # Alle Einträge entfernen
        for item in self.employee_tree.get_children():
            self.employee_tree.delete(item)
        
        # Gefilterte Mitarbeiter hinzufügen
        for employee in self.employees:
            if (search_text in employee.name.lower() or 
                any(search_text in skill.lower() for skill in employee.skills)):
                
                # Skills formatieren
                skills_text = ", ".join(sorted(employee.skills))
                if len(skills_text) > 40:
                    skills_text = skills_text[:37] + "..."
                
                # Status-Text formatieren
                status_text = employee.status.value
                if status_text == "available":
                    status_text = "Verfügbar"
                elif status_text == "busy":
                    status_text = "Beschäftigt"
                elif status_text == "off":
                    status_text = "Abwesend"
                
                # Eintrag zur Liste hinzufügen
                self.employee_tree.insert("", "end", values=(
                    employee.name, 
                    skills_text, 
                    status_text
                ), tags=(employee.id,))
    
    def on_select(self):
        """Verarbeitet den Klick auf den 'Auswählen'-Button"""
        selected_items = self.employee_tree.selection()
        
        if not selected_items:
            return
        
        # Ausgewählte Mitarbeiter sammeln
        selected_employees = []
        for item in selected_items:
            # ID vom Tag bekommen
            for employee in self.employees:
                if employee.id in self.employee_tree.item(item, "tags"):
                    selected_employees.append(employee)
                    break
        
        self.result = selected_employees
        self.destroy()
    
    def on_cancel(self):
        """Verarbeitet den Klick auf den 'Abbrechen'-Button"""
        self.result = None
        self.destroy()