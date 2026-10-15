from tkinter import ttk
import tkinter as tk
import optapy
from optapy.score import HardSoftScore
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
from collections import defaultdict

from core import Task, Employee, TimeSlot, Schedule
from core import has_required_skills, check_time_overlap, is_within_working_hours, extends_beyond_working_hours

class ConstraintAnalyzer:
    """
    Klasse zur detaillierten Analyse von Constraint-Verletzungen.
    Gibt für jede harte Constraint die Anzahl der Verstöße und betroffene Elemente zurück.
    
    Diese verbesserte Version umfasst:
    - Umfassende Analyse aller Hard-Constraints
    - Detaillierte Informationen zu jeder Verletzung
    - Zusätzliche Prüfungen für Ruhezeiten, Arbeitsbelastung und Effizienz
    - Erweiterte Fehlerbeschreibungen für bessere Lösungsfindung
    """
    
    def __init__(self, solution: Schedule):
        """
        Initialisiert den ConstraintAnalyzer mit einer Lösung
        
        Args:
            solution: Ein Schedule-Objekt, typischerweise vom Solver zurückgegeben
        """
        self.solution = solution
        self.tasks = solution.get_tasks()
        self.employees = solution.get_employees()
        self.time_slots = solution.get_time_slots()
        
        # Score der Lösung
        self.score = solution.get_score()
        
        # Constraint-Verletzungen speichern
        self.violations = {}
        self.violation_details = defaultdict(list)
    
    def analyze(self) -> Tuple[Dict, Dict[str, List]]:
        """
        Führt eine vollständige Analyse aller Constraint-Verletzungen durch
        
        Returns:
            Tuple mit zwei Dictionaries:
            - Anzahl der Verstöße pro Constraint
            - Details zu den Verstößen (betroffene Aufgaben, Mitarbeiter, etc.)
        """
        # Hard Constraints prüfen - erweitert für vollständige Abdeckung
        self._check_missing_skills()
        self._check_task_overlaps()
        self._check_employee_availability()
        self._check_working_hours()
        self._check_extends_beyond_hours()
        
        # Weitere spezifische Einschränkungen (neu)
    #    self._check_rest_periods()
        self._check_max_daily_hours()
    #    self._check_consecutive_tasks()
        
        return self.violations, self.violation_details
    
    def _check_missing_skills(self):
        """Prüft fehlende Fähigkeiten"""
        violations = 0
        for task in self.tasks:
            if task.get_assigned_employee() is not None:
                employee = task.get_assigned_employee()
                if not has_required_skills(employee, task.required_skills):
                    violations += 1
                    missing_skills = [
                        skill for skill in task.required_skills 
                        if not employee.has_skill(skill)
                    ]
                    self.violation_details["Fehlende Fähigkeiten"].append({
                        "task_id": task.id,
                        "employee": employee.name,
                        "required_skills": list(task.required_skills),
                        "employee_skills": list(employee.skills),
                        "missing_skills": missing_skills
                    })
        
        self.violations["Fehlende Fähigkeiten"] = violations
    
    def _check_task_overlaps(self):
        """Prüft überlappende Aufgaben"""
        violations = 0
        processed_pairs = set()
        
        for i, task1 in enumerate(self.tasks):
            for j, task2 in enumerate(self.tasks):
                # Nur unterschiedliche Aufgaben prüfen und Duplikate vermeiden
                if i >= j or (task1.id, task2.id) in processed_pairs or (task2.id, task1.id) in processed_pairs:
                    continue
                
                processed_pairs.add((task1.id, task2.id))
                
                # Prüfen, ob gleicher Mitarbeiter und Überlappung
                if (task1.get_assigned_employee() is not None and 
                    task2.get_assigned_employee() is not None and
                    task1.get_assigned_employee().id == task2.get_assigned_employee().id and
                    check_time_overlap(task1, task2)):
                    
                    violations += 1
                    
                    # Start- und Endzeiten für Anzeige formatieren
                    if task1.get_time_slot() and task2.get_time_slot():
                        task1_start = task1.get_time_slot().start_time
                        task1_end = task1_start + timedelta(hours=task1.duration)
                        task2_start = task2.get_time_slot().start_time
                        task2_end = task2_start + timedelta(hours=task2.duration)
                        
                        self.violation_details["Aufgabenüberlappung"].append({
                            "employee": task1.get_assigned_employee().name,
                            "task1": task1.id,
                            "task1_time": f"{task1_start.strftime('%d.%m.%Y %H:%M')} - {task1_end.strftime('%H:%M')}",
                            "task2": task2.id,
                            "task2_time": f"{task2_start.strftime('%d.%m.%Y %H:%M')} - {task2_end.strftime('%H:%M')}",
                            "overlap_minutes": self._calculate_overlap_minutes(task1_start, task1_end, task2_start, task2_end)
                        })
        
        self.violations["Aufgabenüberlappung"] = violations
    
    def _calculate_overlap_minutes(self, start1, end1, start2, end2):
        """Berechnet die Überlappungszeit in Minuten"""
        latest_start = max(start1, start2)
        earliest_end = min(end1, end2)
        overlap_seconds = (earliest_end - latest_start).total_seconds()
        return max(0, int(overlap_seconds / 60))
    
    def _check_employee_availability(self):
        """Prüft, ob zugewiesene Mitarbeiter verfügbar sind"""
        violations = 0
        for task in self.tasks:
            if task.get_assigned_employee() is not None:
                employee = task.get_assigned_employee()
                if not employee.is_available():
                    violations += 1
                    self.violation_details["Mitarbeiter nicht verfügbar"].append({
                        "task_id": task.id,
                        "employee": employee.name,
                        "status": employee.status.value,
                        "time": task.get_time_slot().start_time.strftime('%d.%m.%Y %H:%M') if task.get_time_slot() else "Unbekannt"
                    })
        
        self.violations["Mitarbeiter nicht verfügbar"] = violations
    
    def _check_working_hours(self):
        """Prüft, ob Aufgaben innerhalb der Arbeitszeit (8-18 Uhr) starten"""
        violations = 0
        for task in self.tasks:
            if task.get_time_slot() is not None and not is_within_working_hours(task):
                violations += 1
                start_time = task.get_time_slot().start_time
                self.violation_details["Außerhalb der Arbeitszeit"].append({
                    "task_id": task.id,
                    "start_time": start_time.strftime('%d.%m.%Y %H:%M'),
                    "hour": start_time.hour,
                    "employee": task.get_assigned_employee().name if task.get_assigned_employee() else "Nicht zugewiesen"
                })
                
        self.violations["Außerhalb der Arbeitszeit"] = violations
    
    def _check_extends_beyond_hours(self):
        """Prüft, ob Aufgaben über 18 Uhr hinausgehen"""
        violations = 0
        for task in self.tasks:
            if task.get_time_slot() is not None and extends_beyond_working_hours(task):
                violations += 1
                
                start_time = task.get_time_slot().start_time
                end_time = start_time + timedelta(hours=task.duration)
                
                self.violation_details["Endet nach Arbeitsende"].append({
                    "task_id": task.id,
                    "start_time": start_time.strftime('%d.%m.%Y %H:%M'),
                    "end_time": end_time.strftime('%d.%m.%Y %H:%M'),
                    "duration": task.duration,
                    "employee": task.get_assigned_employee().name if task.get_assigned_employee() else "Nicht zugewiesen"
                })
                
        self.violations["Endet nach Arbeitsende"] = violations
    
    def _check_rest_periods(self):
        """Prüft, ob die Mindest-Ruhezeiten zwischen den Aufgaben eingehalten werden"""
        violations = 0
        min_rest_hours = 11  # Standard-Mindest-Ruhezeit in Stunden
        
        # Aufgaben nach Mitarbeiter gruppieren
        employee_tasks = defaultdict(list)
        for task in self.tasks:
            if task.get_assigned_employee() is not None and task.get_time_slot() is not None:
                employee_tasks[task.get_assigned_employee().id].append(task)
        
        # Für jeden Mitarbeiter die Aufgaben nach Zeit sortieren und Ruhezeiten prüfen
        for emp_id, tasks in employee_tasks.items():
            sorted_tasks = sorted(tasks, key=lambda t: t.get_time_slot().start_time)
            
            # Jede aufeinanderfolgende Aufgabe prüfen
            for i in range(len(sorted_tasks) - 1):
                task1 = sorted_tasks[i]
                task2 = sorted_tasks[i + 1]
                
                # Endzeit der ersten Aufgabe
                task1_end = task1.get_time_slot().start_time + timedelta(hours=task1.duration)
                # Startzeit der zweiten Aufgabe
                task2_start = task2.get_time_slot().start_time
                
                # Ruhezeit in Stunden berechnen
                if task1_end < task2_start:
                    rest_hours = (task2_start - task1_end).total_seconds() / 3600
                    
                    # Wenn Ruhezeit unter dem Minimum liegt
                    if rest_hours < min_rest_hours:
                        violations += 1
                        self.violation_details["Unzureichende Ruhezeit"].append({
                            "employee": task1.get_assigned_employee().name,
                            "task1": task1.id,
                            "task1_end": task1_end.strftime('%d.%m.%Y %H:%M'),
                            "task2": task2.id,
                            "task2_start": task2_start.strftime('%d.%m.%Y %H:%M'),
                            "rest_hours": round(rest_hours, 2),
                            "minimum": min_rest_hours
                        })
        
        self.violations["Unzureichende Ruhezeit"] = violations
    
    def _check_max_daily_hours(self):
        """Prüft, ob die maximale tägliche Arbeitszeit eingehalten wird"""
        violations = 0
        max_daily_hours = 10  # Standard maximale Arbeitszeit pro Tag
        
        # Aufgaben nach Mitarbeiter und Tag gruppieren
        employee_day_tasks = defaultdict(lambda: defaultdict(list))
        
        for task in self.tasks:
            if task.get_assigned_employee() is not None and task.get_time_slot() is not None:
                emp_id = task.get_assigned_employee().id
                day_key = task.get_time_slot().start_time.strftime('%Y-%m-%d')
                employee_day_tasks[emp_id][day_key].append(task)
        
        # Für jeden Mitarbeiter und Tag die Gesamtarbeitszeit berechnen
        for emp_id, days in employee_day_tasks.items():
            employee = next((e for e in self.employees if e.id == emp_id), None)
            if not employee:
                continue
                
            # Individuelle maximale tägliche Arbeitszeit ermitteln (falls vorhanden)
            individual_max = getattr(employee, 'max_daily_hours', max_daily_hours)
            
            for day, tasks in days.items():
                total_hours = sum(task.duration for task in tasks)
                
                if total_hours > individual_max:
                    violations += 1
                    self.violation_details["Maximale Tagesarbeitszeit überschritten"].append({
                        "employee": employee.name,
                        "date": day,
                        "total_hours": total_hours,
                        "max_allowed": individual_max,
                        "excess_hours": total_hours - individual_max,
                        "task_count": len(tasks)
                    })
        
        self.violations["Maximale Tagesarbeitszeit überschritten"] = violations
    
    def _check_consecutive_tasks(self):
        """Prüft, ob es Lücken zwischen aufeinanderfolgenden Aufgaben eines Mitarbeiters am selben Tag gibt"""
        violations = 0
        
        # Aufgaben nach Mitarbeiter und Tag gruppieren
        employee_day_tasks = defaultdict(lambda: defaultdict(list))
        
        for task in self.tasks:
            if task.get_assigned_employee() is not None and task.get_time_slot() is not None:
                emp_id = task.get_assigned_employee().id
                day_key = task.get_time_slot().start_time.strftime('%Y-%m-%d')
                employee_day_tasks[emp_id][day_key].append(task)
        
        # Für jeden Mitarbeiter und Tag die Aufgaben sortieren und prüfen
        for emp_id, days in employee_day_tasks.items():
            employee = next((e for e in self.employees if e.id == emp_id), None)
            if not employee:
                continue
                
            for day, tasks in days.items():
                if len(tasks) <= 1:
                    continue
                    
                # Aufgaben nach Startzeit sortieren
                sorted_tasks = sorted(tasks, key=lambda t: t.get_time_slot().start_time)
                
                # Prüfen auf Lücken zwischen den Aufgaben
                for i in range(len(sorted_tasks) - 1):
                    task1 = sorted_tasks[i]
                    task2 = sorted_tasks[i + 1]
                    
                    # Ende der ersten Aufgabe
                    task1_end = task1.get_time_slot().start_time + timedelta(hours=task1.duration)
                    # Start der nächsten Aufgabe
                    task2_start = task2.get_time_slot().start_time
                    
                    # Lücke berechnen (in Minuten)
                    if task1_end < task2_start:
                        gap_minutes = (task2_start - task1_end).total_seconds() / 60
                        
                        # Wenn die Lücke mehr als 15 Minuten und weniger als 30 Minuten beträgt,
                        # könnte dies eine ineffiziente Planung sein
                        if 15 < gap_minutes < 30:
                            violations += 1
                            self.violation_details["Ineffiziente Zeitlücken"].append({
                                "employee": employee.name,
                                "date": day,
                                "task1": task1.id,
                                "task1_end": task1_end.strftime('%H:%M'),
                                "task2": task2.id,
                                "task2_start": task2_start.strftime('%H:%M'),
                                "gap_minutes": int(gap_minutes)
                            })
        
        self.violations["Ineffiziente Zeitlücken"] = violations
    
    def get_summary(self) -> str:
        """
        Gibt eine formatierte Zusammenfassung der Constraint-Verletzungen zurück
        
        Returns:
            Formatierter String mit der Zusammenfassung
        """
        total_violations = sum(self.violations.values())
        
        summary = []
        summary.append(f"Gesamtscore: {self.score}")
        summary.append(f"Gesamt Hard Constraint Verletzungen: {total_violations}")
        summary.append("")
        
        # Constraints nach Anzahl der Verletzungen sortieren (wichtigste zuerst)
        sorted_constraints = sorted(self.violations.items(), key=lambda x: x[1], reverse=True)
        
        for constraint, count in sorted_constraints:
            if count > 0:
                summary.append(f"{constraint}: {count} Verletzung(en)")
                
                # Details für jede Verletzung
                for i, detail in enumerate(self.violation_details[constraint][:5], 1):  # Begrenze auf 5 Beispiele
                    # Formatierte Ausgabe der Details mit besserer Lesbarkeit
                    formatted_detail = self._format_violation_detail(constraint, detail)
                    summary.append(f"  {i}. {formatted_detail}")
                
                # Zeige an, wenn es weitere Verstöße gibt
                if len(self.violation_details[constraint]) > 5:
                    summary.append(f"  ... und {len(self.violation_details[constraint]) - 5} weitere")
                
                
                
                summary.append("")
        
        if total_violations == 0:
            summary.append("Keine Hard Constraint Verletzungen gefunden!")
            summary.append("Der Zeitplan ist aus Sicht der Hard Constraints optimal.")
        
        return "\n".join(summary)
    
    def _format_violation_detail(self, constraint_type: str, detail: Dict) -> str:
        """
        Formatiert die Details einer Constraint-Verletzung für bessere Lesbarkeit
        
        Args:
            constraint_type: Art der Constraint
            detail: Detailinformationen zur Verletzung
            
        Returns:
            Formatierter String für die Anzeige
        """
        if constraint_type == "Fehlende Fähigkeiten":
            return (f"Mitarbeiter {detail.get('employee')} fehlen für Aufgabe {detail.get('task_id')} "
                   f"die Fähigkeiten: {', '.join(detail.get('missing_skills', []))}")
        
        elif constraint_type == "Aufgabenüberlappung":
            return (f"Mitarbeiter {detail.get('employee')} hat überlappende Aufgaben: "
                   f"{detail.get('task1')} ({detail.get('task1_time')}) und "
                   f"{detail.get('task2')} ({detail.get('task2_time')}), "
                   f"Überlappung: {detail.get('overlap_minutes', 0)} Minuten")
        
        elif constraint_type == "Mitarbeiter nicht verfügbar":
            return (f"Mitarbeiter {detail.get('employee')} ist nicht verfügbar (Status: {detail.get('status')}), "
                   f"hat aber Aufgabe {detail.get('task_id')} um {detail.get('time')} zugewiesen")
        
        elif constraint_type == "Außerhalb der Arbeitszeit":
            return (f"Aufgabe {detail.get('task_id')} beginnt um {detail.get('start_time')} "
                   f"(Stunde {detail.get('hour')}), was außerhalb der Arbeitszeit (8-16 Uhr) liegt")
        
        elif constraint_type == "Endet nach Arbeitsende":
            return (f"Aufgabe {detail.get('task_id')} ({detail.get('duration')} Stunden) "
                   f"beginnt um {detail.get('start_time')} und endet um {detail.get('end_time')}, "
                   f"was nach dem Arbeitsende (16 Uhr) liegt")
        
        elif constraint_type == "Unzureichende Ruhezeit":
            return (f"Mitarbeiter {detail.get('employee')} hat zwischen Aufgaben {detail.get('task1')} "
                   f"(Ende: {detail.get('task1_end')}) und {detail.get('task2')} "
                   f"(Start: {detail.get('task2_start')}) nur {detail.get('rest_hours')} Stunden Ruhezeit "
                   f"(Minimum: {detail.get('minimum')} Stunden)")
        
        elif constraint_type == "Maximale Tagesarbeitszeit überschritten":
            return (f"Mitarbeiter {detail.get('employee')} hat am {detail.get('date')} "
                   f"{detail.get('total_hours')} Arbeitsstunden "
                   f"({detail.get('excess_hours')} Stunden über dem Maximum von {detail.get('max_allowed')})")
        
        elif constraint_type == "Ineffiziente Zeitlücken":
            return (f"Mitarbeiter {detail.get('employee')} hat am {detail.get('date')} eine ineffiziente Lücke "
                   f"von {detail.get('gap_minutes')} Minuten zwischen Aufgaben {detail.get('task1')} "
                   f"(Ende: {detail.get('task1_end')}) und {detail.get('task2')} (Start: {detail.get('task2_start')})")
        
        else:
            # Fallback für nicht speziell formatierte Constraints
            return ", ".join(f"{k}={v}" for k, v in detail.items())
    
    