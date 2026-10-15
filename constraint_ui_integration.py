import tkinter as tk
from tkinter import ttk, messagebox
from constraintanalyzer import ConstraintAnalyzer
from softconstraintanalyzer import SoftConstraintAnalyzer

def integrate_constraint_analyzer(app):
    """
    Integriert die detaillierte Constraint-Analyse in die Scheduling-App.
    
    Diese erweiterte Funktion:
    1. Fügt einen neuen Tab zur Detailansicht hinzu
    2. Erweitert die Methode zur Aktualisierung der Statistik
    4. Integriert Hard- und Soft-Constraint-Analysen
    5. Bietet detaillierte Analysemöglichkeiten mit Lösungsvorschlägen
    
    Args:
        app: Die SchedulingApp-Instanz
    """
    # Original update_stats_view-Methode speichern, um sie später aufzurufen
    original_update_stats = app.update_stats_view
    
    # Neue aktualisierte Methode, die die Constraint-Analyse beinhaltet
    def enhanced_update_stats(self):
        # Zuerst die originale Methode aufrufen
        original_update_stats()
        
        if not self.solution:
            return
        
        # Constraint-Analyse zum Statistik-Tab hinzufügen
        constraint_frame = ttk.LabelFrame(self.main_view.detail_view.stats_frame, text="Constraint-Analyse")
        constraint_frame.pack(fill='x', padx=5, pady=5)
        
        # Constraint-Analyzer erstellen und Analyse durchführen
        analyzer = ConstraintAnalyzer(self.solution)
        violations, details = analyzer.analyze()
        
        # Soft-Constraint-Analyzer für zusätzliche Analysen
        soft_analyzer = SoftConstraintAnalyzer(self.solution)
        soft_evaluations, soft_details = soft_analyzer.analyze()
        
        # Score und Gesamtverletzungen anzeigen
        total_violations = sum(violations.values())
        
        # Hard-Constraint-Analyse
        hard_frame = ttk.Frame(constraint_frame)
        hard_frame.pack(fill='x', pady=5)
        
        ttk.Label(hard_frame, 
                 text=f"Hard Constraint Verletzungen: {total_violations}",
                 foreground='red' if total_violations > 0 else 'green',
                 font=('TkDefaultFont', 10, 'bold')).pack(anchor='w')
        
        # Soft-Constraint-Analyse
        soft_frame = ttk.Frame(constraint_frame)
        soft_frame.pack(fill='x', pady=5)
        
        # Soft-Score extrahieren
        soft_score = soft_analyzer.get_soft_score()
        
        ttk.Label(soft_frame, 
                 text=f"Soft Constraint Score: {soft_score}",
                 foreground='blue',
                 font=('TkDefaultFont', 10, 'bold')).pack(anchor='w')
        
        
        # Buttons für detaillierte Analysen
        button_frame = ttk.Frame(constraint_frame)
        button_frame.pack(fill='x', pady=5)
        
        # Button für Hard-Constraint-Analyse
        ttk.Button(button_frame, 
                  text="Detaillierte Hard-Constraint-Analyse", 
                  command=lambda: show_detailed_analysis(self, analyzer)).pack(side='left', padx=5)
        
        # Button für Soft-Constraint-Analyse
        ttk.Button(button_frame, 
                  text="Detaillierte Soft-Constraint-Analyse", 
                  command=lambda: show_detailed_soft_analysis(self, soft_analyzer)).pack(side='left', padx=5)
    
    # Methode zum Anzeigen der detaillierten Hard-Constraint-Analyse
    def show_detailed_analysis(app, analyzer):
        """Zeigt die detaillierte Hard-Constraint-Analyse in einem separaten Fenster an"""
        # Fenster erstellen
        analysis_window = tk.Toplevel(app.root)
        analysis_window.title("Detaillierte Hard-Constraint-Analyse")
        analysis_window.geometry("800x600")
        analysis_window.transient(app.root)
        
        # Hauptframe mit Scrollbar
        main_frame = ttk.Frame(analysis_window, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Überschrift
        ttk.Label(main_frame, 
                 text="Detaillierte Analyse der Hard Constraint Verletzungen",
                 font=('TkDefaultFont', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        # Scrollbarer Textbereich
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill='both', expand=True)
        
        y_scrollbar = ttk.Scrollbar(text_frame)
        y_scrollbar.pack(side='right', fill='y')
        
        x_scrollbar = ttk.Scrollbar(text_frame, orient='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')
        
        # Text-Widget für die Analyse
        text_widget = tk.Text(text_frame, wrap='none', 
                             yscrollcommand=y_scrollbar.set,
                             xscrollcommand=x_scrollbar.set)
        text_widget.pack(fill='both', expand=True)
        
        y_scrollbar.config(command=text_widget.yview)
        x_scrollbar.config(command=text_widget.xview)
        
        # Analyse-Zusammenfassung einfügen
        text_widget.insert('1.0', analyzer.get_summary())
        
        # Text-Widget schreibgeschützt machen
        text_widget.config(state='disabled')
        
        # Schließen-Button
        ttk.Button(main_frame, text="Schließen", 
                  command=analysis_window.destroy).pack(pady=10)
        
        # Fenster modal machen
        analysis_window.grab_set()
        analysis_window.focus_set()










    # Funktion zur Anzeige einer Constraint-Analyse im Dialog
    def show_constraint_analysis():
        """Zeigt einen Dialog mit der Constraint-Analyse an"""
        if not app.solution:
            messagebox.showinfo("Hinweis", "Keine Lösung verfügbar. Bitte berechnen Sie zuerst einen Zeitplan.")
            return
        
        analyzer = ConstraintAnalyzer(app.solution)
        soft_analyzer = SoftConstraintAnalyzer(app.solution)
        
        # Fenster erstellen
        analysis_window = tk.Toplevel(app.root)
        analysis_window.title("Constraint-Analyse")
        analysis_window.geometry("800x600")
        analysis_window.transient(app.root)
        
        # Notebook für Hard und Soft Constraints
        analysis_notebook = ttk.Notebook(analysis_window)
        analysis_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab für Hard Constraints
        hard_tab = ttk.Frame(analysis_notebook)
        analysis_notebook.add(hard_tab, text="Hard Constraints")
        
        # Content für Hard Constraints
        hard_frame = ttk.Frame(hard_tab, padding=10)
        hard_frame.pack(fill='both', expand=True)
        
        # Text-Widget für Hard-Constraints
        hard_text = tk.Text(hard_frame, wrap='word', height=25, width=80)
        hard_text.pack(fill='both', expand=True)
        hard_text.insert('1.0', analyzer.get_summary())
        hard_text.config(state='disabled')
        
        # Tab für Soft Constraints
        soft_tab = ttk.Frame(analysis_notebook)
        analysis_notebook.add(soft_tab, text="Soft Constraints")
        
        # Content für Soft Constraints
        soft_frame = ttk.Frame(soft_tab, padding=10)
        soft_frame.pack(fill='both', expand=True)
        
        # Text-Widget für Soft-Constraints
        soft_text = tk.Text(soft_frame, wrap='word', height=25, width=80)
        soft_text.pack(fill='both', expand=True)
        soft_text.insert('1.0', soft_analyzer.get_summary())
        soft_text.config(state='disabled')
        
        # Schließen-Button
        ttk.Button(analysis_window, text="Schließen", 
                  command=analysis_window.destroy).pack(pady=10)
        
        # Fenster modal machen
        analysis_window.grab_set()
        analysis_window.focus_set()
    
    # Methode zum Anzeigen der detaillierten Soft-Constraint-Analyse
    def show_detailed_soft_analysis(app, analyzer):
        """Zeigt die detaillierte Soft-Constraint-Analyse in einem separaten Fenster an"""
        # Fenster erstellen
        analysis_window = tk.Toplevel(app.root)
        analysis_window.title("Detaillierte Soft-Constraint-Analyse")
        analysis_window.geometry("800x600")
        analysis_window.transient(app.root)
        
        # Hauptframe mit Scrollbar
        main_frame = ttk.Frame(analysis_window, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Überschrift
        ttk.Label(main_frame, 
                 text="Detaillierte Analyse der Soft Constraints und Optimierungspotenziale",
                 font=('TkDefaultFont', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        # Scrollbarer Textbereich
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill='both', expand=True)
        
        y_scrollbar = ttk.Scrollbar(text_frame)
        y_scrollbar.pack(side='right', fill='y')
        
        x_scrollbar = ttk.Scrollbar(text_frame, orient='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')
        
        # Text-Widget für die Analyse
        text_widget = tk.Text(text_frame, wrap='none', 
                             yscrollcommand=y_scrollbar.set,
                             xscrollcommand=x_scrollbar.set)
        text_widget.pack(fill='both', expand=True)
        
        y_scrollbar.config(command=text_widget.yview)
        x_scrollbar.config(command=text_widget.xview)
        
        # Analyse-Zusammenfassung einfügen
        text_widget.insert('1.0', analyzer.get_summary())
        
        # Text-Widget schreibgeschützt machen
        text_widget.config(state='disabled')
        
        # Schließen-Button
        ttk.Button(main_frame, text="Schließen", 
                  command=analysis_window.destroy).pack(pady=10)
        
        # Fenster modal machen
        analysis_window.grab_set()
        analysis_window.focus_set()

   
    
    # Die Methode an die App-Instanz binden
    app.update_stats_view = enhanced_update_stats.__get__(app, type(app))
    
