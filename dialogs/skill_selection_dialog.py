import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Set

class SkillSelectionDialog(tk.Toplevel):
    """Dialog zum Auswählen von Fähigkeiten aus einer Liste"""
    
    def __init__(self, parent, available_skills: Dict[str, List[str]], 
                initial_skills: Set[str] = None, title="Fähigkeiten auswählen"):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        
        self.available_skills = available_skills
        self.selected_skills = set() if initial_skills is None else initial_skills.copy()
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
        
        # Anweisungstext
        ttk.Label(main_frame, text="Wählen Sie Fähigkeiten aus:").pack(anchor='w', pady=(0, 10))
        
        # Notebook für Kategorien
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True, pady=10)
        
        # Tabs für jede Kategorie
        self.checkbutton_vars = {}
        
        for category, skills in self.available_skills.items():
            # Tab für Kategorie
            tab = ttk.Frame(notebook, padding=10)
            notebook.add(tab, text=category.capitalize())
            
            # Checkbuttons für jede Fähigkeit
            for skill in skills:
                var = tk.BooleanVar(value=skill in self.selected_skills)
                self.checkbutton_vars[skill] = var
                
                ttk.Checkbutton(tab, text=skill, variable=var).pack(anchor='w', pady=2)
        
        # Button-Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        # OK und Abbrechen-Buttons
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.on_cancel).pack(side='right')
        
        # Ausgewählte Fähigkeiten anzeigen
        self.selection_var = tk.StringVar()
        self.update_selection_text()
        ttk.Label(main_frame, textvariable=self.selection_var, wraplength=300).pack(
            fill='x', pady=(10, 0), anchor='w')
    
    def update_selection_text(self):
        """Aktualisiert den Text der ausgewählten Fähigkeiten"""
        if not self.selected_skills:
            self.selection_var.set("Keine Fähigkeiten ausgewählt")
        else:
            self.selection_var.set(f"Ausgewählt: {', '.join(sorted(self.selected_skills))}")
    
    def on_ok(self):
        """Verarbeitet den OK-Button-Klick"""
        # Ausgewählte Fähigkeiten sammeln
        self.selected_skills = {skill for skill, var in self.checkbutton_vars.items() if var.get()}
        
        # Ergebnis setzen und Dialog schließen
        self.result = self.selected_skills
        self.destroy()
    
    def on_cancel(self):
        """Verarbeitet den Abbrechen-Button-Klick"""
        self.result = None
        self.destroy()