import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import traceback
import core

from toolbar import Toolbar
from database.db_manager import DatabaseManager
from ui.main_view import MainView
from ui.calendar_builder import CalendarBuilder
from ui.stats_builder import StatsBuilder
from dialogs.custom_schedule_dialog import CustomScheduleDialog
from constraint_ui_integration import integrate_constraint_analyzer
from skill_management_integration import add_skill_management_to_app
from config.constants import (
    MAIN_WINDOW_WIDTH,
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_TITLE,
    TASK_COLORS,
    DEFAULT_SKILL_CATEGORIES,
    STATUS_READY
)
from logger import setup_logger, get_error_tracker, log_error, log_performance
import time

# Import der Feedback-Komponenten
from dialogs.feedback_dialog import FeedbackDialog, EmployeeSelectionDialog

class SchedulingApp:
    """Hauptklasse der Anwendung"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(MAIN_WINDOW_TITLE)
        self.root.geometry(f"{MAIN_WINDOW_WIDTH}x{MAIN_WINDOW_HEIGHT}")

        # Logger und Error-Tracker
        self.logger = setup_logger("SchedulingApp")
        self.error_tracker = get_error_tracker()
        self.logger.info("Scheduling Application wird initialisiert...")

        # Initialisiere Schedule und Solution
        self.schedule = None
        self.solution = None

        # Initialisiere DatabaseManager
        try:
            self.db_manager = DatabaseManager()
            self.logger.info("DatabaseManager erfolgreich initialisiert")
        except Exception as e:
            self.error_tracker.track_error("DATABASE", e, "DatabaseManager-Initialisierung")
            raise

        # Hilfsservices erstellen
        self.db_service = DatabaseService(self.db_manager)
        self.scheduler_service = SchedulerService()
        self.calendar_builder = CalendarBuilder()
        self.stats_builder = StatsBuilder()

        # Verfügbare Fähigkeiten definieren (aus Konstanten)
        self.available_skills = DEFAULT_SKILL_CATEGORIES.copy()

        # Skills-Management-Funktionalität hinzufügen - vor der Toolbar
        add_skill_management_to_app(self)

        # Toolbar erstellen mit allen Callback-Methoden inklusive Skill-Management
        self.toolbar = Toolbar(
            root,
            on_generate_test=self.generate_test_case,
            on_run_scheduler=self.run_scheduler,
            on_generate_fixed_test=getattr(self, 'generate_custom_test_case', None),
            on_save_schedule=self.save_schedule,
            on_load_schedule=self.load_schedule_dialog,
            on_collect_feedback=self.on_collect_feedback,
            on_optimize_with_feedback=self.on_optimize_with_feedback,
            on_manage_skills=self.manage_skills  # Neuer Parameter für Skill-Management
        )

        # Hauptansicht erstellen
        self.main_view = MainView(root, self)

        # Farben für die Kalender-Einträge (je nach Aufgabendauer) - aus Konstanten
        self.task_colors = TASK_COLORS.copy()
        
        # Features integrieren, die vorher in main.py waren
        self._setup_custom_schedule()
        self._setup_skill_management()
        self._setup_constraint_analyzer()
        self.main_view.detail_view.app = self

    
    def _setup_custom_schedule(self):
        """Richtet die Funktion zum Erstellen eines benutzerdefinierten Zeitplans ein"""
        # Button für benutzerdefinierten Zeitplan zur Toolbar hinzufügen
        ttk.Button(
            self.toolbar.button_frame,
            text="Benutzerdefinierter Zeitplan",
            command=self.create_custom_schedule
        ).pack(side='left', padx=5)

    def _setup_constraint_analyzer(self):
        """Richtet den Constraint-Analyzer ein"""
        integrate_constraint_analyzer(self)

    def _setup_skill_management(self):
        """Richtet das Skill-Management ein"""
        add_skill_management_to_app(self)
    
    def create_custom_schedule(self):
        """Öffnet den Dialog zum Erstellen eines benutzerdefinierten Zeitplans"""
        # Dialog für benutzerdefinierten Zeitplan öffnen
        dialog = CustomScheduleDialog(self.root, self.available_skills)
        
        if dialog.result:
            # Benutzerdefinierten Zeitplan übernehmen
            self.schedule = dialog.result
            
            # UI-Updates
            self.main_view.detail_view.update_employee_list(self.schedule.employees)
            self.main_view.detail_view.update_task_list(self.schedule.tasks)
            
            # Zusammenfassung anzeigen
            messagebox.showinfo(
                "Zeitplan erstellt", 
                f"Benutzerdefinierter Zeitplan wurde erstellt mit:\n"
                f"- {len(self.schedule.time_slots)} Zeitslots\n"
                f"- {len(self.schedule.employees)} Mitarbeitern\n"
                f"- {len(self.schedule.tasks)} Aufgaben\n\n"
                f"Klicke auf 'Zeitplan berechnen' um den Einsatzplan zu erstellen."
            )
            
            # Status aktualisieren
            self.toolbar.status_var.set("Benutzerdefinierter Zeitplan erstellt")
    
    def generate_test_case(self):
        """Generiert einen Testfall"""
        # Status aktualisieren
        self.toolbar.status_var.set("Generiere Testfall...")
        self.root.update()
        
        # Testfall generieren über Service
        try:
            complexity = self.toolbar.complexity_var.get()
            self.schedule = self.scheduler_service.generate_test_case(complexity)
            
            # Status aktualisieren
            self.toolbar.status_var.set(f"Testfall generiert ({complexity})")
            
            # UI-Updates
            self.main_view.detail_view.update_employee_list(self.schedule.employees)
            self.main_view.detail_view.update_task_list(self.schedule.tasks)
            self.main_view.detail_view.available_skills = self.available_skills
            
            # Zusammenfassung anzeigen
            messagebox.showinfo(
                "Testfall generiert", 
                f"Testfall wurde generiert mit:\n"
                f"- {len(self.schedule.time_slots)} Zeitslots\n"
                f"- {len(self.schedule.employees)} Mitarbeitern\n"
                f"- {len(self.schedule.tasks)} Aufgaben\n\n"
                f"Klicke auf 'Zeitplan berechnen' um den Einsatzplan zu erstellen."
            )
        except Exception as e:
            # Fehlermeldung
            messagebox.showerror("Fehler", f"Fehler beim Generieren des Testfalls:\n{str(e)}")
            self.toolbar.status_var.set("Fehler bei der Testfall-Generierung")
    
    def run_scheduler(self):
        """Führt den OptaPy-Scheduler aus"""
        if not self.schedule:
            messagebox.showwarning("Hinweis", "Kein Zeitplan vorhanden. Bitte zuerst einen Testfall generieren.")
            return

        core.set_current_schedule(self.schedule)

        # Status aktualisieren
        self.toolbar.status_var.set("Berechne Einsatzplan...")
        self.root.update()

        try:
            # Performance-Messung starten
            start_time = time.time()

            # Solver ausführen über Service
            complexity = self.toolbar.complexity_var.get()
            self.logger.info(f"Starte Solver mit Komplexität: {complexity}")
            self.solution = self.scheduler_service.run_scheduler(self.schedule, complexity)

            # Performance loggen
            duration = time.time() - start_time
            log_performance(
                self.logger,
                "Solver-Run",
                duration,
                {
                    "complexity": complexity,
                    "tasks": len(self.schedule.tasks),
                    "employees": len(self.schedule.employees),
                    "score": str(self.solution.get_score())
                }
            )

            # Iteration auf 1 setzen (für späteres Feedback)
            self.solution.iteration = 1

            # Status aktualisieren
            self.toolbar.status_var.set(f"Einsatzplan erstellt! Score: {self.solution.get_score()}")
            self.logger.info(f"Solver erfolgreich abgeschlossen. Score: {self.solution.get_score()}")

            # UI aktualisieren
            self.update_calendar_view()
            self.update_task_list()
            self.update_stats_view()

        except Exception as e:
            # Error-Tracking
            self.error_tracker.track_error("SOLVER", e, "Scheduler-Ausführung")

            # Fehlermeldung
            messagebox.showerror("Scheduler-Fehler", f"Fehler bei der Berechnung:\n{str(e)}")
            self.toolbar.status_var.set("Fehler bei der Berechnung")
    
    def update_task_list(self):
        """Aktualisiert die Aufgabenliste in der Detail-Ansicht mit der berechneten Lösung"""
        # DetailView mit verfügbaren Skills aktualisieren
        self.main_view.detail_view.available_skills = self.available_skills
        
        if not self.solution:
            # Wenn keine Lösung vorhanden ist, leere Liste anzeigen
            self.main_view.detail_view.update_task_list([])
            return
        
        # Aufgabenliste über DetailView aktualisieren
        self.main_view.detail_view.update_task_list(
            self.solution.get_tasks(),  # Aufgaben aus der Lösung
            self.solution  # Optionale Lösung für zusätzliche Kontextinformationen
        )
    
    def update_calendar_view(self):
        """Aktualisiert die Kalender-Ansicht mit der berechneten Lösung"""
        # DetailView mit verfügbaren Skills aktualisieren
        if hasattr(self, 'main_view') and hasattr(self.main_view, 'detail_view'):
            self.main_view.detail_view.available_skills = self.available_skills
        
        if not hasattr(self, 'solution') or self.solution is None:
            # Wenn keine Lösung vorhanden ist, Platzhalter anzeigen
            if hasattr(self, 'main_view') and hasattr(self.main_view, 'calendar_view'):
                try:
                    self.main_view.calendar_view.clear()
                    # Sicherstellen, dass content existiert
                    if hasattr(self.main_view.calendar_view, 'content'):
                        # Immer ein neues Label erstellen
                        placeholder_label = ttk.Label(self.main_view.calendar_view.content, 
                                                    text="Kein Zeitplan verfügbar.\nGeneriere einen Testfall oder lade Daten.",
                                                    font=('TkDefaultFont', 12))
                        placeholder_label.pack(pady=50, padx=50)
                        # Referenz speichern
                        self.main_view.calendar_view.placeholder_label = placeholder_label
                except Exception as e:
                    print(f"Fehler beim Aktualisieren der Kalenderansicht: {str(e)}")
            return
        
        # Kalender-Ansicht über den CalendarBuilder aktualisieren
        try:
            if hasattr(self, 'calendar_builder') and hasattr(self, 'main_view'):
                self.calendar_builder.update_calendar(
                    self.main_view.calendar_view,
                    self.solution.get_time_slots(),
                    self.solution.get_employees(),
                    self.solution.get_tasks(),
                    self.task_colors,
                    self.root
                )
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Kalenderansicht: {str(e)}")
            traceback.print_exc()
    
    def update_stats_view(self):
        """Aktualisiert den Statistik-Tab mit umfassenden Analysen"""
        # Statistik über StatsBuilder erstellen
        self.stats_builder.create_stats_view(
            self.main_view.detail_view.stats_frame,
            self.solution
        )
    
    def update_schedule_details(self):
        """Aktualisiert die Detail-Ansicht basierend auf dem aktuellen Zeitplan"""
        if self.schedule:
            self.main_view.detail_view.update_employee_list(self.schedule.employees)
            self.main_view.detail_view.update_task_list(self.schedule.tasks, self.solution)
    
    def refresh_schedule_combo(self):
        """Aktualisiert die Combobox mit verfügbaren Zeitplänen aus der Datenbank"""
        self.db_service.refresh_schedule_combo(
            self.main_view.schedule_combo, 
            self.main_view.schedule_mapping
        )
    
    def load_selected_schedule(self):
        """Lädt den in der Combobox ausgewählten Zeitplan"""
        selected = self.main_view.schedule_combo.get()
        
        if not selected or selected in ["Zeitplan auswählen", "Keine Zeitpläne verfügbar", 
                                        "Fehler beim Laden", "Datenbankverbindung fehlt"]:
            return
        
        # Schedule laden über DatabaseService
        try:
            schedule_id = self.main_view.schedule_mapping.get(selected)
            if not schedule_id:
                messagebox.showerror("Fehler", "Ungültige Schedule-ID")
                return
            
            loaded_schedule = self.db_service.load_schedule(schedule_id)
            
            if loaded_schedule:
                self.on_schedule_loaded(loaded_schedule)
            else:
                messagebox.showerror("Fehler", "Fehler beim Laden des Zeitplans")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden des Zeitplans: {str(e)}")
            traceback.print_exc()
    
    def on_schedule_loaded(self, loaded_schedule):
        """Verarbeitet einen geladenen Zeitplan"""
        # Zeitplan setzen
        self.schedule = loaded_schedule
        
        # Lösung generieren
        self.solution = self.scheduler_service.init_solution(self.schedule)
        
        # UI aktualisieren
        self.main_view.detail_view.update_employee_list(self.schedule.employees)
        self.main_view.detail_view.update_task_list(self.schedule.tasks, self.solution)
        self.update_calendar_view()
        self.update_stats_view()
        
        # Status aktualisieren
        self.toolbar.status_var.set(f"Zeitplan '{loaded_schedule.name}' geladen")
    
    def save_employee(self, employee):
        """Speichert einen Mitarbeiter in der Datenbank"""
        return self.db_service.save_employee(employee)

    def load_all_employees(self):
        """Lädt alle Mitarbeiter aus der Datenbank"""
        return self.db_service.load_all_employees()
    
    def get_skill_id(self, skill_name):
        """Findet die ID eines Skills oder erstellt einen neuen Skill"""
        return self.db_service.get_skill_id(skill_name)

    def manage_skills(self):
        """Öffnet den Dialog zur Verwaltung der verfügbaren Fähigkeiten
        Diese Methode wird in skill_management_integration hinzugefügt, ist aber 
        hier für Vollständigkeit definiert."""
        pass
    
    

    def save_schedule(self):
        """Speichert den aktuellen Zeitplan in der Datenbank"""
        if not self.schedule:
            messagebox.showwarning("Hinweis", "Kein Zeitplan vorhanden. Bitte zuerst einen Testfall generieren.")
            return
        
        # Status aktualisieren
        self.toolbar.status_var.set("Speichere Zeitplan...")
        self.root.update()
        
        try:
            # Name für den Zeitplan holen
            default_name = f"Zeitplan vom {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            
            # Wenn die Lösung einen Namen oder eine Iteration hat, verwenden
            if self.solution:
                solution_name = getattr(self.solution, 'name', None)
                if solution_name:
                    default_name = solution_name
                # Iteration hinzufügen, falls vorhanden
                iteration = getattr(self.solution, 'iteration', None)
                if iteration and iteration > 1:
                    if "Iteration" not in default_name:
                        default_name = f"{default_name} (Iteration {iteration})"
            
            # Optional: Dialog zum Eingeben des Namens
            from tkinter import simpledialog
            schedule_name = simpledialog.askstring(
                "Zeitplan speichern", 
                "Name für den Zeitplan:",
                initialvalue=getattr(self.schedule, 'name', default_name)
            )
            
            if not schedule_name:  # Abgebrochen
                self.toolbar.status_var.set("Speichervorgang abgebrochen")
                return
            
            # Aktuellen Namen setzen
            self.schedule.name = schedule_name
            
            # In der Datenbank speichern
            schedule_id = self.db_service.save_schedule(
                self.schedule,
                name=schedule_name,
                description=f"Gespeichert am {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            
            if schedule_id:
                # Status aktualisieren
                self.toolbar.status_var.set(f"Zeitplan '{schedule_name}' gespeichert")
                
                
                
                # Erfolgsmeldung
                messagebox.showinfo("Erfolg", f"Zeitplan '{schedule_name}' wurde erfolgreich gespeichert.")
            else:
                # Fehlermeldung
                messagebox.showerror("Fehler", "Zeitplan konnte nicht gespeichert werden.")
                self.toolbar.status_var.set("Fehler beim Speichern")
        
        except Exception as e:
            # Bei Fehler
            messagebox.showerror("Fehler", f"Fehler beim Speichern des Zeitplans:\n{str(e)}")
            self.toolbar.status_var.set("Fehler beim Speichern")
            traceback.print_exc()

    def load_schedule_dialog(self):
        """Öffnet einen Dialog zum Laden eines gespeicherten Zeitplans"""
        if not self.db_manager:
            messagebox.showerror("Fehler", "Keine Datenbankverbindung verfügbar.")
            return
        
        # Status aktualisieren
        self.toolbar.status_var.set("Zeitplan auswählen...")
        
        # Dialog zum Auswählen eines Zeitplans öffnen
        from dialogs.schedule_load_dialog import ScheduleLoaderDialog
        dialog = ScheduleLoaderDialog(self.root, self.db_manager)
        
        if dialog.result:
            # Status aktualisieren
            self.toolbar.status_var.set("Lade Zeitplan...")
            self.root.update()
            
            try:
                # Zeitplan laden ohne zusätzliche Parameter
                loaded_schedule = self.db_service.load_schedule(dialog.result)
                
                # Debug-Ausgabe
                print(f"Geladene TimeSlots: {len(loaded_schedule.time_slots) if loaded_schedule and hasattr(loaded_schedule, 'time_slots') else 0}")
                print(f"Geladene Mitarbeiter: {len(loaded_schedule.employees) if loaded_schedule and hasattr(loaded_schedule, 'employees') else 0}")
                print(f"Geladene Aufgaben: {len(loaded_schedule.tasks) if loaded_schedule and hasattr(loaded_schedule, 'tasks') else 0}")
                
                if loaded_schedule and hasattr(loaded_schedule, 'employees') and hasattr(loaded_schedule, 'tasks'):
                    # Zeitplan übernehmen
                    self.schedule = loaded_schedule
                    
                    # Initiale Lösung generieren (Nur wenn Mitarbeiter und Aufgaben vorhanden)
                    if len(self.schedule.employees) > 0 and len(self.schedule.tasks) > 0:
                        self.solution = self.scheduler_service.init_solution(self.schedule)
                    else:
                        self.solution = None
                        print("Keine Lösung generiert: Mitarbeiter oder Aufgaben fehlen")
                    
                    # UI aktualisieren (immer)
                    self.main_view.detail_view.update_employee_list(self.schedule.employees)
                    self.main_view.detail_view.update_task_list(self.schedule.tasks, self.solution)
                    self.update_calendar_view()
                    self.update_stats_view()
                    
                    # Status aktualisieren
                    self.toolbar.status_var.set(f"Zeitplan '{loaded_schedule.name}' geladen")
                    
                    # Erfolgsmeldung
                    messagebox.showinfo("Erfolg", f"Zeitplan '{loaded_schedule.name}' wurde erfolgreich geladen.")
                else:
                    # Fehlermeldung
                    messagebox.showerror("Fehler", "Zeitplan konnte nicht vollständig geladen werden. Mitarbeiter oder Aufgaben fehlen.")
                    self.toolbar.status_var.set("Fehler beim Laden")
            
            except Exception as e:
                # Bei Fehler
                messagebox.showerror("Fehler", f"Fehler beim Laden des Zeitplans:\n{str(e)}")
                self.toolbar.status_var.set("Fehler beim Laden")
                traceback.print_exc()
        else:
            # Abgebrochen
            self.toolbar.status_var.set("Bereit")

    # === Neue Methoden für das Feedback-System ===
    
    def on_collect_feedback(self):
        """
        Sammelt Feedback von einem Mitarbeiter für den aktuellen Schedule.
        Öffnet einen Dialog zur Mitarbeiterauswahl und anschließend den Feedback-Dialog.
        """
        # Prüfen, ob ein Schedule und eine Lösung vorhanden sind
        if not self.schedule or not self.solution:
            messagebox.showinfo("Hinweis", "Bitte erstellen oder laden Sie zuerst einen Zeitplan.")
            return
        
        # Prüfen, ob Mitarbeiter vorhanden sind
        if not self.solution.employees:
            messagebox.showinfo("Hinweis", "Keine Mitarbeiter im aktuellen Zeitplan vorhanden.")
            return
        
        # Dialog zur Auswahl eines Mitarbeiters öffnen
        employee_dialog = EmployeeSelectionDialog(self.root, self.solution.employees)
        
        # Wenn kein Mitarbeiter ausgewählt wurde, abbrechen
        if not employee_dialog.result:
            return
        
        # Ausgewählten Mitarbeiter für Feedback verwenden
        employee = employee_dialog.result
        
        # Feedback-Manager initialisieren (wenn verfügbar)
        feedback_manager = None
        if hasattr(self.db_manager, 'feedback_manager'):
            feedback_manager = self.db_manager.feedback_manager
        
        # Feedback-Dialog öffnen
        feedback_dialog = FeedbackDialog(
            self.root, 
            employee, 
            self.solution, 
            feedback_manager
        )
        
        # Verarbeite das Feedback-Ergebnis
        if feedback_dialog.result:
            # Feedback zum Schedule hinzufügen (für spätere Optimierung)
            if not hasattr(self.solution, 'task_feedback'):
                self.solution.task_feedback = {}
            
            # Aufgabenbewertungen extrahieren und in eine Form bringen, die der
            # Scheduler verstehen kann (task_id, employee_id) -> rating
            task_ratings = feedback_dialog.result.get("task_ratings", {})
            
            # Feedback im Schedule speichern
            for key, rating in task_ratings.items():
                self.solution.task_feedback[key] = rating
            
            # Meldung anzeigen
            messagebox.showinfo(
                "Feedback gespeichert", 
                f"Das Feedback von {employee.name} wurde erfolgreich aufgezeichnet und wird bei "
                f"der nächsten Optimierung berücksichtigt."
            )
            
            # Status aktualisieren
            self.toolbar.status_var.set(f"Feedback für {len(task_ratings)} Aufgaben gesammelt")
    
    def on_optimize_with_feedback(self):
        """
        Optimiert den aktuellen Schedule unter Berücksichtigung des gesammelten Feedbacks.
        Erstellt eine neue Iteration des Schedules.
        """
        # Prüfen, ob ein Schedule und eine Lösung vorhanden sind
        if not self.schedule or not self.solution:
            messagebox.showinfo("Hinweis", "Bitte erstellen oder laden Sie zuerst einen Zeitplan.")
            return
        
        # Prüfen, ob Feedback vorhanden ist
        has_feedback = hasattr(self.solution, 'task_feedback') and bool(self.solution.task_feedback)
        
        if not has_feedback:
            if not messagebox.askyesno(
                "Kein Feedback gefunden", 
                "Es wurde kein Feedback für diesen Zeitplan gefunden. "
                "Möchten Sie trotzdem eine neue Iteration starten?"
            ):
                return
        
        # Aktuelle Iteration ermitteln
        current_iteration = getattr(self.solution, 'iteration', 1)
        next_iteration = current_iteration + 1
        
        # Neuen Namen mit Iterationsnummer
        old_name = getattr(self.solution, 'name', f"Zeitplan {datetime.now().strftime('%d.%m.%Y')}")
        new_name = f"{old_name} (Iteration {next_iteration})"
        
        # Status aktualisieren
        self.toolbar.status_var.set(f"Optimiere Schedule mit Feedback (Iteration {next_iteration})...")
        self.root.update()
        
        try:
            # Vorbereiten der nächsten Iteration
            # Den Scheduler aufrufen und Feedback anwenden
            optimized_solution = self.scheduler_service.run_scheduler_with_feedback(
                self.solution,  # Wir verwenden die aktuelle Lösung als Ausgangspunkt
                self.toolbar.complexity_var.get(),
                apply_feedback=True
            )
            
            # Iteration und Namen aktualisieren
            optimized_solution.iteration = next_iteration
            optimized_solution.name = new_name
            
            # Lösung übernehmen
            self.solution = optimized_solution
            
            # UI aktualisieren
            self.update_task_list()
            self.update_calendar_view()
            self.update_stats_view()
            
            # Status aktualisieren
            feedback_count = len(getattr(self.solution, 'task_feedback', {}))
            self.toolbar.status_var.set(
                f"Schedule optimiert mit {feedback_count} Feedback-Einträgen. Score: {self.solution.get_score()}"
            )
            
            # Meldung anzeigen
            messagebox.showinfo(
                "Optimierung abgeschlossen", 
                f"Der Zeitplan wurde basierend auf dem gesammelten Feedback optimiert.\n\n"
                f"Neue Iteration: {next_iteration}\n"
                f"Score: {self.solution.get_score()}\n\n"
                f"Möchten Sie weitere Feedback-Einträge sammeln und erneut optimieren?"
            )
            
            # Fragen, ob der optimierte Schedule gespeichert werden soll
            if messagebox.askyesno(
                "Schedule speichern",
                f"Möchten Sie die optimierte Version '{new_name}' speichern?"
            ):
                self.save_schedule()
        
        except Exception as e:
            # Fehlerbehandlung
            messagebox.showerror(
                "Fehler bei der Optimierung", 
                f"Bei der Optimierung mit Feedback ist ein Fehler aufgetreten:\n{str(e)}"
            )
            self.toolbar.status_var.set("Fehler bei der Optimierung mit Feedback")
            traceback.print_exc()

    



    def add_employee_to_schedule(self, employee):
        """Fügt einen Mitarbeiter zur aktuellen Schedule hinzu"""
        if not self.schedule:
            messagebox.showinfo("Hinweis", "Kein aktiver Zeitplan vorhanden.")
            return
        
        # Prüfen, ob der Mitarbeiter bereits existiert
        if any(e.id == employee.id for e in self.schedule.employees):
            if messagebox.askyesno("Mitarbeiter existiert bereits", 
                                f"Ein Mitarbeiter mit der ID {employee.id} existiert bereits. Möchten Sie die Daten aktualisieren?"):
                # Mitarbeiter ersetzen
                for i, emp in enumerate(self.schedule.employees):
                    if emp.id == employee.id:
                        self.schedule.employees[i] = employee
                        break
            else:
                return  # Abbrechen, wenn nicht überschrieben werden soll
        else:
            # Neuen Mitarbeiter hinzufügen
            self.schedule.employees.append(employee)
        
        # UI aktualisieren
        self.main_view.detail_view.update_employee_list(self.schedule.employees)
        
        # Erfolgsmeldung
        messagebox.showinfo("Erfolg", f"Mitarbeiter '{employee.name}' wurde zum Zeitplan hinzugefügt.")
        
        # Optionale Datenbankoperationen, falls gewünscht
        if self.db_manager and hasattr(self.db_manager, 'save_employee'):
            try:
                self.db_manager.save_employee(employee)
            except Exception as e:
                print(f"Warnung: Konnte Mitarbeiter nicht in der Datenbank speichern: {str(e)}")

    def remove_employees_from_schedule(self, employee_ids):
        """Entfernt Mitarbeiter aus der aktuellen Schedule"""
        if not self.schedule:
            messagebox.showinfo("Hinweis", "Kein aktiver Zeitplan vorhanden.")
            return
        
        # Mitarbeiter aus der Schedule entfernen
        self.schedule.employees = [e for e in self.schedule.employees if e.id not in employee_ids]
        
        # UI aktualisieren
        self.main_view.detail_view.update_employee_list(self.schedule.employees)
        
        # Auch aus der Lösung entfernen, wenn vorhanden
        if self.solution:
            removed_count = len(employee_ids)
            messagebox.showinfo("Erfolg", f"{removed_count} Mitarbeiter wurden aus dem Zeitplan entfernt.")
            
            # Hinweis, dass die Lösung neu berechnet werden sollte
            messagebox.showinfo("Hinweis", 
                            "Bitte berechnen Sie den Zeitplan neu, um die Änderungen in den Zuweisungen zu berücksichtigen.")

    def add_task_to_schedule(self, task):
        """Fügt eine Aufgabe zur aktuellen Schedule hinzu"""
        if not self.schedule:
            messagebox.showinfo("Hinweis", "Kein aktiver Zeitplan vorhanden.")
            return
        
        # Prüfen, ob die Aufgabe bereits existiert
        if any(t.id == task.id for t in self.schedule.tasks):
            if messagebox.askyesno("Aufgabe existiert bereits", 
                                f"Eine Aufgabe mit der ID {task.id} existiert bereits. Möchten Sie die Daten aktualisieren?"):
                # Aufgabe ersetzen
                for i, t in enumerate(self.schedule.tasks):
                    if t.id == task.id:
                        self.schedule.tasks[i] = task
                        break
            else:
                return  # Abbrechen, wenn nicht überschrieben werden soll
        else:
            # Neue Aufgabe hinzufügen
            self.schedule.tasks.append(task)
        
        # UI aktualisieren
        self.main_view.detail_view.update_task_list(self.schedule.tasks, self.solution)
        
        # Erfolgsmeldung
        messagebox.showinfo("Erfolg", f"Aufgabe '{task.id}' wurde zum Zeitplan hinzugefügt.")
        
        # Optionale Datenbankoperationen, falls gewünscht
        if self.db_manager and hasattr(self.db_manager, 'save_task'):
            try:
                self.db_manager.save_task(task)
            except Exception as e:
                print(f"Warnung: Konnte Aufgabe nicht in der Datenbank speichern: {str(e)}")

    def remove_tasks_from_schedule(self, task_ids):
        """Entfernt Aufgaben aus der aktuellen Schedule"""
        if not self.schedule:
            messagebox.showinfo("Hinweis", "Kein aktiver Zeitplan vorhanden.")
            return
        
        # Aufgaben aus der Schedule entfernen
        self.schedule.tasks = [t for t in self.schedule.tasks if t.id not in task_ids]
        
        # UI aktualisieren
        self.main_view.detail_view.update_task_list(self.schedule.tasks, self.solution)
        
        # Auch aus der Lösung entfernen, wenn vorhanden
        if self.solution:
            removed_count = len(task_ids)
            messagebox.showinfo("Erfolg", f"{removed_count} Aufgabe(n) wurden aus dem Zeitplan entfernt.")
            
            # Hinweis, dass die Lösung neu berechnet werden sollte
            messagebox.showinfo("Hinweis", 
                            "Bitte berechnen Sie den Zeitplan neu, um die Änderungen zu berücksichtigen.")


# Import der Services am Ende der Datei, um Zirkelbezüge zu vermeiden
from services.schedule_service import SchedulerService
from services.db_service import DatabaseService