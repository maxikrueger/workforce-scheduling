from tkinter import messagebox, ttk
import tkinter as tk

class Toolbar:
    """Modulare Klasse für die Toolbar mit zweizeiligem Layout für bessere Übersicht"""
    
    def __init__(self, parent, on_generate_test, on_run_scheduler, on_generate_fixed_test=None,
                  on_save_schedule=None, on_load_schedule=None,
                  on_collect_feedback=None, on_optimize_with_feedback=None,
                  on_manage_skills=None):
        
        # Hauptframe für die Toolbar
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill='x', pady=5)
        
        # Container für beide Zeilen
        self.rows_container = ttk.Frame(self.frame)
        self.rows_container.pack(side='left', fill='x', expand=True)
        
        # Erste Zeile der Buttons
        self.button_frame_row1 = ttk.Frame(self.rows_container)
        self.button_frame_row1.pack(fill='x', pady=(0, 3))
        
        # Zweite Zeile der Buttons
        self.button_frame_row2 = ttk.Frame(self.rows_container)
        self.button_frame_row2.pack(fill='x')
        
        # Für Kompatibilität mit bestehendem Code - der Haupt-Button-Frame ist nun die erste Zeile
        self.button_frame = self.button_frame_row1
        
        
        # Button: Testfall generieren
        ttk.Button(self.button_frame_row1, text="Testfall generieren", 
                  command=on_generate_test).pack(side='left', padx=5)
        
        # Button: Zeitplan berechnen
        ttk.Button(self.button_frame_row1, text="Zeitplan berechnen", 
                  command=on_run_scheduler).pack(side='left', padx=5)
        
        # Button: Zeitplan speichern
        ttk.Button(self.button_frame_row1, text="Zeitplan speichern", 
                  command=on_save_schedule).pack(side='left', padx=5)
        
        # Button: Zeitplan laden
        ttk.Button(self.button_frame_row1, text="Zeitplan laden", 
                  command=on_load_schedule).pack(side='left', padx=5)
        
        
        # Button: Feedback sammeln
        ttk.Button(self.button_frame_row2, text="Feedback sammeln", 
                command=on_collect_feedback).pack(side='left', padx=5)

        # Button: Mit Feedback optimieren
        ttk.Button(self.button_frame_row2, text="Mit Feedback optimieren", 
                command=on_optimize_with_feedback).pack(side='left', padx=5)
        
        
        # Button: Fähigkeiten verwalten
        if on_manage_skills:
            ttk.Button(self.button_frame_row2, text="Fähigkeiten verwalten", 
                      command=on_manage_skills).pack(side='left', padx=5)
        
        # Komplexitätsauswahl in die zweite Zeile verschieben
        complexity_frame = ttk.Frame(self.button_frame_row2)
        complexity_frame.pack(side='left', padx=20)
        
        ttk.Label(complexity_frame, text="Komplexität:").pack(side='left')
        self.complexity_var = tk.StringVar(value="complex")
        complexity_options = ttk.Combobox(complexity_frame, textvariable=self.complexity_var, 
                                         width=12, state="readonly")
        complexity_options['values'] = ("simple", "medium", "complex", "very_complex")
        complexity_options.pack(side='left', padx=5)
        
        # Status-Anzeige bleibt im Hauptframe
        self.status_var = tk.StringVar(value="Bereit")
        status_label = ttk.Label(self.frame, textvariable=self.status_var)
        status_label.pack(side='right', padx=10)
        ttk.Label(self.frame, text="Status:").pack(side='right')