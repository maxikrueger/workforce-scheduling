import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from ui.calendar_view import CalendarView

class CalendarBuilder:
    """
    Klasse zum Erstellen des Kalendergitters
    Nutzt die CalendarView-Klasse für die UI-Komponenten
    Mit optimiertem Layout, fixierter Kopfzeile und erweiterten Arbeitszeiten
    """
    
    def __init__(self):
        """Initialisiert den CalendarBuilder mit lokalisierten Wochentagen"""
        # Deutsche Wochentage für Lokalisierung
        self.weekday_names = {
            0: "Montag",
            1: "Dienstag",
            2: "Mittwoch", 
            3: "Donnerstag", 
            4: "Freitag", 
            5: "Samstag", 
            6: "Sonntag"
        }
    
    def _get_german_weekday(self, weekday_number):
        """Gibt den deutschen Namen für einen Wochentag zurück"""
        return self.weekday_names.get(weekday_number, "Unbekannt")
    
    def update_calendar(self, calendar_view, time_slots, employees, tasks, task_colors, root):
        """
        Hauptmethode zur Aktualisierung der Kalender-Ansicht
        
        Args:
            calendar_view: CalendarView-Instanz
            time_slots: Liste von TimeSlot-Objekten
            employees: Liste von Employee-Objekten
            tasks: Liste von Task-Objekten
            task_colors: Dictionary mit Farben je nach Aufgabendauer
            root: Das Hauptfenster für Tooltips
        """
        # Bestehende Inhalte löschen
        calendar_view.clear()
        
        if not time_slots or not employees:
            # Falls keine Daten vorhanden, zeige Platzhalter an
            # Immer ein neues Label erstellen, um sicherzugehen, dass es funktioniert
            calendar_view.placeholder_label = ttk.Label(calendar_view.content, 
                                                    text="Kein Zeitplan verfügbar.\nGeneriere einen Testfall oder lade Daten.",
                                                    font=('TkDefaultFont', 12))
            calendar_view.placeholder_label.pack(pady=50, padx=50)
            return
        
        # Kalender-Grid erstellen
        self._create_calendar_grid(
            calendar_view.content,
            calendar_view.canvas,
            time_slots,
            employees,
            tasks,
            task_colors,
            root
        )
        
        # ScrollRegion anpassen, um Header-Bereich zu berücksichtigen
        calendar_view.content.update_idletasks()
        bbox = calendar_view.canvas.bbox("all")
        if bbox:
            # Header-Bereich soll nicht gescrollt werden, daher angepasstes ScrollRegion
            calendar_view.canvas.config(scrollregion=(bbox[0], 0, bbox[2], bbox[3]))
    
    
    


    def _create_calendar_grid(self, content_frame, canvas, time_slots, employees, tasks, task_colors, root):
        """Erstellt das Kalender-Grid mit Zeitslots und Aufgaben"""
        base_slot_height = 40  # Höhe eines einzelnen Zeitslots
        base_slot_width = 130  # Einheitliche Breite für alle Mitarbeiter-Spalten
        
        # Header-Zeile mit Zeit und Mitarbeiter-Namen
        # Zeit-Label in der ersten Spalte
        time_label = ttk.Label(content_frame, text="Zeit", font=('TkDefaultFont', 9, 'bold'))
        time_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        # Mitarbeiter als Spaltenbeschriftungen
        employee_cols = {}
        for i, employee in enumerate(employees):
            col_index = i + 1  # Einfache, fortlaufende Spaltennummerierung
            
            # Erstelle ein Frame für den Mitarbeiternamen
            ttk.Label(content_frame, text=employee.name, font=('TkDefaultFont', 9, 'bold')).grid(
                row=0, column=col_index, padx=5, pady=5, sticky='w')
            
            # Speichern der Spaltenposition für diesen Mitarbeiter
            employee_cols[employee.id] = col_index

        # Zeitslots sortieren und nach Tagen gruppieren
        sorted_slots = sorted(time_slots, key=lambda s: s.start_time)
        time_slots_by_day = self._group_slots_by_day(sorted_slots)
        
        # Grid für jeden Tag erstellen
        current_row = 1
        time_slot_rows = {}  # Speichert die Zeilenposition für jeden Zeitslot
        
        for day_key, slots in time_slots_by_day.items():
            # Tag-Header
            # Übersetze den Wochentag ins Deutsche
            day_date = slots[0].start_time
            weekday_german = self._get_german_weekday(day_date.weekday())
            day_display = f"{weekday_german}, {day_date.strftime('%d.%m.%Y')}"
            
            # Separator vor jedem Tag außer dem ersten
            if current_row > 1:
                separator = ttk.Separator(content_frame, orient='horizontal')
                # Berechne die tatsächliche Anzahl der Spalten (Mitarbeiter + Separatoren)
                total_columns = len(employees) * 2
                separator.grid(row=current_row, column=0, columnspan=total_columns + 1, 
                            sticky='ew', pady=10)  # Größerer Abstand zwischen Tagen (10 statt 5)
                current_row += 1
                
            # Tag-Header mit verbessertem Layout und Hintergrund
            day_header = ttk.Label(content_frame, text=day_display, 
                                font=('TkDefaultFont', 10, 'bold'),
                                background="#e0e0e0")  # Dunklerer Hintergrund für Tag-Header
            # Berechne die tatsächliche Anzahl der Spalten (Mitarbeiter + Separatoren)
            total_columns = len(employees) * 2
            day_header.grid(row=current_row, column=0, columnspan=total_columns + 1, 
                        padx=5, pady=10, sticky='w')  # Mehr Padding um Tag-Header (10 statt 5)
            current_row += 1
            
            # Erweiterte Arbeitszeiten: 8:00 bis 19:00 Uhr
            working_hours = range(8, 20)  # Von 8 bis 19 Uhr
            
            # Erstelle Zeilen für jede volle Stunde der erweiterten Arbeitszeit
            for hour in working_hours:
                # Erstelle ein Zeitstempel für die aktuelle Stunde dieses Tages
                current_date = slots[0].start_time.replace(hour=hour, minute=0)
                
                # Finde den passenden Slot für diese Stunde
                matching_slot = next((slot for slot in slots if slot.start_time.hour == hour), None)
                
                # Zeit-Label (zeigt immer die Stunde an, auch wenn kein Slot vorhanden ist)
                time_str = f"{hour:02d}:00"
                # Erstelle ein Frame für die Zeitbeschriftung mit fester Breite
                time_label_frame = ttk.Frame(content_frame, width=base_slot_width)
                time_label_frame.grid(row=current_row, column=0, padx=5, pady=2, sticky='w')
                time_label_frame.grid_propagate(False)  # Verhindert Größenänderung
                
                ttk.Label(time_label_frame, text=time_str).pack(anchor='w')
                
                if matching_slot:
                    # Wenn ein Slot für diese Stunde existiert, Zeile für diesen Slot speichern
                    time_slot_rows[matching_slot.id] = current_row
                
                # Leere Zellen für jeden Mitarbeiter
                # Berücksichtige nur die eigentlichen Mitarbeiterspalten, nicht die Separator-Spalten
                for i, _ in enumerate(employees):
                    col = i * 2 + 1  # Berechne den Spaltenindex basierend auf der Mitarbeiterposition
                    frame = ttk.Frame(content_frame, width=base_slot_width, height=base_slot_height)
                    frame.grid(row=current_row, column=col, padx=1, pady=1)
                    # Verhindern, dass die Zelle sich zusammenzieht
                    frame.grid_propagate(False)
                
                current_row += 1
            
        # Aufgaben in das Grid einfügen
        self._place_tasks_in_grid(
            content_frame, 
            tasks, 
            time_slot_rows, 
            employee_cols, 
            task_colors, 
            root,
            base_slot_height,
            base_slot_width
        )
    
    def _group_slots_by_day(self, time_slots):
        """Gruppiert Zeitslots nach Tagen"""
        time_slots_by_day = {}
        
        for slot in time_slots:
            day_key = slot.start_time.strftime("%Y-%m-%d")
            if day_key not in time_slots_by_day:
                time_slots_by_day[day_key] = []
            time_slots_by_day[day_key].append(slot)
            
        return time_slots_by_day
    
    def _place_tasks_in_grid(self, content_frame, tasks, time_slot_rows, employee_cols, task_colors, root, base_slot_height, base_slot_width):
        """Platziert Aufgaben im Grid"""
        for task in tasks:
            slot = task.get_time_slot()
            employee = task.get_assigned_employee()
            
            if slot and employee:
                # Finde die Zeile und Spalte für diese Aufgabe
                row = time_slot_rows.get(slot.id)
                col = employee_cols.get(employee.id)
                
                if row and col:
                    # Task in Grid einsetzen
                    self._create_task_cell(
                        content_frame,
                        task,
                        employee,
                        row,
                        col,
                        task_colors,
                        root,
                        base_slot_height,
                        base_slot_width
                    )
    
    def _create_task_cell(self, content_frame, task, employee, row, col, task_colors, root, base_slot_height, base_slot_width):
        """Erstellt eine Zelle für eine Aufgabe im Grid"""
        # Höhe basierend auf der Aufgabendauer berechnen
        task_height = base_slot_height * task.duration
        
        # Farbe je nach Aufgabendauer
        color = task_colors.get(task.duration, "#F5B7B1")  # Standard-Rot
        
        # Task-Frame mit fester Größe
        task_frame = ttk.Frame(content_frame)
        task_frame.grid(row=row, column=col, rowspan=task.duration, padx=1, pady=1, sticky='nsew')
        
        # Canvas für die Aufgabe mit fester Breite
        task_canvas = tk.Canvas(
            task_frame, 
            bg=color, 
            width=base_slot_width,
            height=task_height,
            highlightthickness=1, 
            highlightbackground="gray"
        )
        task_canvas.pack(fill='both', expand=True)
        
        # Aufgabenname zentriert anzeigen
        short_id = task.id if len(task.id) < 15 else task.id[:12] + "..."
        task_canvas.create_text(
            base_slot_width // 2,  # x-Position (Mitte)
            task_height // 2,      # y-Position (Mitte)
            text=short_id, 
            fill="black"
        )
        
        # Tooltip für mehr Details
        self._create_tooltip(task_canvas, task, employee, root)
    
    def _create_tooltip(self, widget, task, employee, root):
        """Erstellt einen detaillierten Tooltip für Aufgaben"""
        # Zeitslot-Informationen abrufen
        slot = task.get_time_slot()
        start_time = slot.start_time.strftime("%d.%m.%Y %H:%M")
        
        # Berechne die Endzeit basierend auf der Startzeit und der Aufgabendauer
        end_time = (slot.start_time + timedelta(hours=task.duration)).strftime("%H:%M")
        
        # Fähigkeiten formatieren
        skills_text = ", ".join(sorted(task.required_skills))
        
        tooltip_text = f"""
        Aufgabe: {task.id}
        Zeit: {start_time} - {end_time}
        Dauer: {task.duration} Stunde(n)
        Mitarbeiter: {employee.name}
        Benötigte Fähigkeiten: {skills_text}
        """
        
        def show_tooltip(event):
            x, y = event.x_root, event.y_root
            tooltip = tk.Toplevel(root)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{x+10}+{y+10}")
            
            label = ttk.Label(tooltip, text=tooltip_text, background="lightyellow", 
                            relief="solid", borderwidth=1, justify="left", padding=5)
            label.pack()
            
            def hide_tooltip(e):
                tooltip.destroy()
            
            widget.bind("<Leave>", hide_tooltip)
            tooltip.bind("<Leave>", hide_tooltip)
            
        widget.bind("<Enter>", show_tooltip)