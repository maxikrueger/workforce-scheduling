import tkinter as tk
from tkinter import ttk

from ui.calendar_view import CalendarView
from ui.detail_view import DetailView

class MainView:
    """Hauptansicht der Anwendung, die alle UI-Komponenten zusammenfasst"""
    
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        
        # Hauptframe
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Horizontaler Teiler
        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=5)
        
        # Unterer Bereich mit Kalender und Detail-Ansicht als PanedWindow
        self.bottom_pane = ttk.PanedWindow(self.main_frame, orient='horizontal')
        self.bottom_pane.pack(fill='both', expand=True)
        
        # Frame für die Kalender-Ansicht (linke Seite)
        calendar_frame = ttk.Frame(self.bottom_pane)
        
        # Frame für die Detail-Ansicht (rechte Seite)
        detail_frame = ttk.Frame(self.bottom_pane)
        
        # Zuerst die Frames zum PanedWindow hinzufügen
        self.bottom_pane.add(calendar_frame, weight=2)  # Kalender bekommt mehr Platz
        self.bottom_pane.add(detail_frame, weight=1)  # Details bekommen weniger Platz
        
        # Dann die Views in den entsprechenden Frames initialisieren
        self.calendar_view = CalendarView(calendar_frame)
        self.detail_view = DetailView(detail_frame, controller.db_manager)
        