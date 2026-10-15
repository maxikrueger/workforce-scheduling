import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import random
from typing import List, Dict, Optional

class CalendarView:
    """
    Modulare Klasse für die Kalender-Ansicht mit optimiertem horizontalem und vertikalem Scrollen,
    fixierter Kopfzeile und verbesserter visueller Darstellung
    """
    
    def __init__(self, parent):
        # Container für den Kalender mit Scrollbalken
        self.frame = ttk.LabelFrame(parent, text="Einsatzplan")
        self.frame.pack(side='left', fill='both', expand=True)
        
        # Vertikale Scrollbar
        self.v_scrollbar = ttk.Scrollbar(self.frame, orient='vertical')
        self.v_scrollbar.pack(side='right', fill='y')
        
        # Horizontale Scrollbar
        self.h_scrollbar = ttk.Scrollbar(self.frame, orient='horizontal')
        self.h_scrollbar.pack(side='bottom', fill='x')
        
        # Canvas für den scrollbaren Inhalt mit Hintergrundfarbe für bessere Sichtbarkeit
        self.canvas = tk.Canvas(self.frame, 
                               yscrollcommand=self.v_scrollbar.set,
                               xscrollcommand=self.h_scrollbar.set,
                               background="#f8f8f8")  # Leicht grauer Hintergrund
        self.canvas.pack(fill='both', expand=True)
        
        # Scrollbars mit Canvas verbinden
        self.v_scrollbar.config(command=self.canvas.yview)
        self.h_scrollbar.config(command=self.canvas.xview)
        
        # Frame im Canvas für den eigentlichen Kalender
        self.content = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.content, anchor='nw')
        
        # Platzhalter-Text
        self.placeholder_label = ttk.Label(self.content, 
                                         text="Kein Zeitplan verfügbar.\nGeneriere einen Testfall oder lade Daten.",
                                         font=('TkDefaultFont', 12))
        self.placeholder_label.pack(pady=50, padx=50)
        
        # Canvas-Scrollregion aktualisieren
        self.content.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        
        # Mausrad-Bindung für vertikales Scrollen
        self.canvas.bind("<MouseWheel>", self._on_vertical_mousewheel)
        # Mausrad-Bindung für horizontales Scrollen (mit Shift)
        self.canvas.bind("<Shift-MouseWheel>", self._on_horizontal_mousewheel)
        
        # Zusätzlich: Control + Mausrad für horizontales Scrollen (Alternative zu Shift)
        self.canvas.bind("<Control-MouseWheel>", self._on_horizontal_mousewheel)
        
        # Event für Größenänderung, um Scrollregion anzupassen
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Verhindern, dass das Canvas die Frames einschränkt
        self.canvas.config(width=800)  # Größere Anfangsbreite, wird durch Scrollregion dynamisch
    
    def _on_vertical_mousewheel(self, event):
        """Behandelt Mausrad-Events für vertikales Scrollen"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_horizontal_mousewheel(self, event):
        """Behandelt Mausrad-Events für horizontales Scrollen mit Modifier-Taste"""
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_canvas_configure(self, event):
        """Behandelt Größenänderungen des Canvas"""
        # Scrollregion aktualisieren, wenn das Canvas resized wird
        self.content.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            # Header-Bereich berücksichtigen
            self.canvas.config(scrollregion=(bbox[0], 0, bbox[2], bbox[3]))
    
    def clear(self):
        """Leert die Kalenderansicht"""
        # Alle Canvas-Fensterelemente entfernen (header und content)
        for window_id in self.canvas.find_withtag("window"):
            self.canvas.delete(window_id)
            
        # Alle Widgets im Content-Frame zerstören
        for widget in self.content.winfo_children():
            widget.destroy()
            
        # Stellen Sie sicher, dass placeholder_label als None gesetzt wird, nachdem es zerstört wurde
        self.placeholder_label = None
        
        # Neues Frame für den Inhalt erstellen
        self.content = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.content, anchor='nw')
        
        # Canvas-Scrollregion aktualisieren
        self.content.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox('all'))