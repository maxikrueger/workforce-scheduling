import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class ScheduleLoaderDialog(tk.Toplevel):
    """Dialog zum Laden eines gespeicherten Zeitplans"""
    
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.title("Zeitplan laden")
        self.transient(parent)
        self.resizable(True, True)
        self.geometry("600x400")
        
        self.parent = parent
        self.db_manager = db_manager
        self.result = None
        
        self.create_widgets()
        
        # Dialog modal machen
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.focus_set()
        
        # Position neben dem Elternfenster
        self.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}")
        
        # Warten auf das Schließen des Fensters
        parent.wait_window(self)
    
    def create_widgets(self):
        """Erstellt die UI-Komponenten für den Dialog"""
        # Hauptcontainer
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Beschreibung
        ttk.Label(main_frame, text="Wählen Sie einen gespeicherten Zeitplan zum Laden:", 
                wraplength=550).pack(anchor='w', pady=(0, 10))
        
        # Tabelle mit Zeitplänen
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill='both', expand=True, pady=5)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame)
        y_scrollbar.pack(side='right', fill='y')
        
        # Treeview für die Tabelle
        columns = ("name", "start_date", "end_date", "status", "id")
        self.schedules_tree = ttk.Treeview(
            table_frame, 
            columns=columns,
            show="headings", 
            yscrollcommand=y_scrollbar.set,
            selectmode="browse"  # Nur eine Auswahl erlauben
        )
        
        # Spalten konfigurieren
        self.schedules_tree.heading("name", text="Name")
        self.schedules_tree.heading("start_date", text="Startdatum")
        self.schedules_tree.heading("end_date", text="Enddatum")
        self.schedules_tree.heading("status", text="Status")
        self.schedules_tree.heading("id", text="ID")
        
        self.schedules_tree.column("name", width=200)
        self.schedules_tree.column("start_date", width=100)
        self.schedules_tree.column("end_date", width=100)
        self.schedules_tree.column("status", width=100)
        self.schedules_tree.column("id", width=0, stretch=False)  # ID ausblenden
        
        # Anzeigespalten konfigurieren (ID ausblenden)
        self.schedules_tree["displaycolumns"] = ("name", "start_date", "end_date", "status")
        
        self.schedules_tree.pack(fill='both', expand=True)
        y_scrollbar.config(command=self.schedules_tree.yview)
        
        # Doppelklick-Event für sofortiges Laden
        self.schedules_tree.bind("<Double-1>", lambda e: self.on_load())
        
        # Laden der Zeitpläne
        self.load_schedules()
        
        # Button-Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Aktualisieren-Button
        ttk.Button(button_frame, text="Aktualisieren", 
                  command=self.load_schedules).pack(side='left')
        
        # Laden- und Abbrechen-Buttons
        self.load_button = ttk.Button(button_frame, text="Laden", 
                                    command=self.on_load, state="disabled")
        self.load_button.pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Abbrechen", 
                  command=self.on_cancel).pack(side='right')
        
        # Selektions-Event für Aktivierung des Laden-Buttons
        self.schedules_tree.bind("<<TreeviewSelect>>", self.on_select)
    
    def load_schedules(self):
        """Lädt die Zeitpläne aus der Datenbank"""
        # Bestehende Einträge löschen
        for item in self.schedules_tree.get_children():
            self.schedules_tree.delete(item)
        
        try:
            # Zeitpläne aus der Datenbank laden
            if self.db_manager:
                schedules = self.db_manager.get_all_schedules()
                
                if not schedules:
                    # Platzhalter anzeigen, wenn keine Zeitpläne vorhanden
                    self.schedules_tree.insert("", "end", values=(
                        "Keine Zeitpläne vorhanden", "", "", "", ""))
                    return
                
                # Zeitpläne sortieren (neueste zuerst)
                schedules = sorted(schedules, key=lambda s: s[2], reverse=True)
                
                # Zeitpläne anzeigen
                for schedule in schedules:
                    schedule_id, name, start_date_str, end_date_str, status, description = schedule
                    
                    # Datumsformatierung
                    try:
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
                        start_date_formatted = start_date.strftime('%d.%m.%Y')
                    except:
                        start_date_formatted = start_date_str
                    
                    try:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                        end_date_formatted = end_date.strftime('%d.%m.%Y')
                    except:
                        end_date_formatted = end_date_str
                    
                    # Eintrag hinzufügen
                    self.schedules_tree.insert("", "end", values=(
                        name, start_date_formatted, end_date_formatted, status, schedule_id))
            else:
                # Fehlermeldung anzeigen
                self.schedules_tree.insert("", "end", values=(
                    "Datenbankverbindung fehlt", "", "", "", ""))
        
        except Exception as e:
            # Fehlerbehandlung
            print(f"Fehler beim Laden der Zeitpläne: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fehlermeldung anzeigen
            self.schedules_tree.insert("", "end", values=(
                f"Fehler: {str(e)}", "", "", "", ""))
    
    def on_select(self, event):
        """Reagiert auf Auswahl in der Tabelle"""
        selected = self.schedules_tree.selection()
        self.load_button.config(state="normal" if selected else "disabled")
    
    def on_load(self):
        """Lädt den ausgewählten Zeitplan"""
        selected = self.schedules_tree.selection()
        if not selected:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie einen Zeitplan zum Laden aus.")
            return
        
        # ID des ausgewählten Zeitplans
        schedule_id = self.schedules_tree.item(selected[0], "values")[4]
        
        # Prüfen, ob es eine echte ID ist (falls Platzhalter ausgewählt)
        if not schedule_id:
            messagebox.showinfo("Hinweis", "Kein gültiger Zeitplan ausgewählt.")
            return
        
        # Ergebnis setzen und Dialog schließen
        self.result = schedule_id
        self.destroy()
    
    def on_cancel(self):
        """Bricht den Dialog ab"""
        self.result = None
        self.destroy()