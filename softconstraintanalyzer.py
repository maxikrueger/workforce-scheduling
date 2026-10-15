from tkinter import ttk
import tkinter as tk
import optapy
from optapy.score import HardSoftScore
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set, Tuple
from collections import defaultdict

from core import Task, Employee, TimeSlot, Schedule
from core import has_required_skills, check_time_overlap, is_within_working_hours, extends_beyond_working_hours
from core import safe_check_working_hours, count_matching_skills

class SoftConstraintAnalyzer:
    """
    Verbesserte Klasse zur detaillierten Analyse von Soft-Constraint-Beiträgen und -Optimierungen.
    Bewertet Soft-Constraints und gibt Optimierungsvorschläge zurück.
    
    Diese Version behebt Probleme mit:
    - Der korrekten Extrahierung des Soft-Scores
    - Gewichtung der Arbeitsbelastung
    - Erkennung bevorzugter Arbeitszeiten
    - Integration von Feedback-Bewertungen
    """
    
    def __init__(self, solution: Schedule):
        """
        Initialisiert den SoftConstraintAnalyzer mit einer Lösung
        
        Args:
            solution: Ein Schedule-Objekt, typischerweise vom Solver zurückgegeben
        """
        self.solution = solution
        self.tasks = solution.get_tasks()
        self.employees = solution.get_employees()
        self.time_slots = solution.get_time_slots()
        
        # Score der Lösung
        self.score = solution.get_score()
        
        # Soft-Score direkt extrahieren
        self.soft_score = self.get_soft_score()
        
        # Constraint-Bewertungen speichern
        self.soft_evaluations = {}
        self.soft_details = defaultdict(list)
        


    def analyze(self) -> Tuple[Dict, Dict[str, Any]]:
        """
        Führt eine vollständige Analyse aller Soft-Constraints durch
        
        Returns:
            Tuple mit zwei Elementen:
            - Dictionary mit Punktzahlen pro Soft-Constraint
            - Dictionary mit Details zu den Constraints
        """
        try:
            # Soft Constraints prüfen
            self._evaluate_skill_matching()
            self._evaluate_preferred_skills()
            self._evaluate_working_hours()
          #  self._evaluate_employee_workload()
            self._evaluate_feedback_satisfaction()
            
            
            return self.soft_evaluations, self.soft_details
        except Exception as e:
            print(f"Fehler während der Soft-Constraint-Analyse: {e}")
            # Leere Ergebnisse zurückgeben bei Fehler
            return {}, {}
    
    def _evaluate_skill_matching(self):
        """Bewertet Fähigkeitsübereinstimmungen"""
        total_score = 0
        matches = []
        mismatches = []
        
        for task in self.tasks:
            if task.get_assigned_employee() is not None:
                employee = task.get_assigned_employee()
                matched_skills = count_matching_skills(employee, task.required_skills)
                required_skills_count = len(task.required_skills)
                
                # Jede Fähigkeitsübereinstimmung gibt einen Punkt
                total_score += matched_skills
                
                # Details für besonders gute Übereinstimmungen oder fehlende Skills
                if matched_skills == required_skills_count:
                    matches.append({
                        "task_id": task.id,
                        "employee": employee.name,
                        "skills": list(task.required_skills),
                        "score": matched_skills
                    })
                else:
                    missing_skills = [
                        skill for skill in task.required_skills 
                        if not employee.has_skill(skill)
                    ]
                    mismatches.append({
                        "task_id": task.id,
                        "employee": employee.name,
                        "matched_skills": matched_skills,
                        "total_skills": required_skills_count,
                        "missing_skills": missing_skills
                    })
        
        self.soft_evaluations["Fähigkeitsübereinstimmung"] = total_score
        self.soft_details["Fähigkeitsübereinstimmung"] = {
            "perfect_matches": matches,
            "partial_matches": mismatches,
            "total_score": total_score
        }
    
    def _evaluate_preferred_skills(self):
        """Bewertet bevorzugte Fähigkeiten der Mitarbeiter"""
        total_score = 0
        preferred_matches = []
        
        for task in self.tasks:
            if task.get_assigned_employee() is not None:
                employee = task.get_assigned_employee()
                
                # Prüfen, ob der Mitarbeiter bevorzugte Fähigkeiten hat
                if hasattr(employee, 'preferred_skills') and employee.preferred_skills:
                    # Zählen der übereinstimmenden bevorzugten Fähigkeiten
                    preferred_count = sum(1 for skill in task.required_skills 
                                        if skill in employee.preferred_skills)
                    total_score += preferred_count
                    
                    if preferred_count > 0:
                        preferred_matches.append({
                            "task_id": task.id,
                            "employee": employee.name,
                            "preferred_skills": [s for s in task.required_skills if s in employee.preferred_skills],
                            "score": preferred_count
                        })
        
        self.soft_evaluations["Bevorzugte Fähigkeiten"] = total_score
        self.soft_details["Bevorzugte Fähigkeiten"] = {
            "preferred_matches": preferred_matches,
            "total_score": total_score
        }
    
    def _evaluate_working_hours(self):
        """
        Bewertet die Einhaltung bevorzugter Arbeitszeiten
        Verbesserte Version mit korrekter Prüfung der Arbeitszeiten
        """
        total_score = 0
        preferred_times = []
        non_preferred_times = []
        
        for task in self.tasks:
            if task.get_assigned_employee() is not None and task.get_time_slot() is not None:
                employee = task.get_assigned_employee()
                time_slot = task.get_time_slot()
                
                # Verbesserte Prüfung bevorzugter Arbeitszeiten
                is_preferred = self._check_preferred_working_time(employee, time_slot)
                
                # Score erhöhen für bevorzugte Zeiten
                total_score += is_preferred
                
                # Details für die Auswertung
                task_info = {
                    "task_id": task.id,
                    "employee": employee.name,
                    "time": time_slot.start_time.strftime('%d.%m.%Y %H:%M'),
                    "day_of_week": time_slot.start_time.weekday(),
                    "hour": time_slot.start_time.hour
                }
                
                if is_preferred:
                    preferred_times.append(task_info)
                else:
                    non_preferred_times.append(task_info)
        
        self.soft_evaluations["Bevorzugte Arbeitszeiten"] = total_score
        self.soft_details["Bevorzugte Arbeitszeiten"] = {
            "preferred_times": preferred_times,
            "non_preferred_times": non_preferred_times,
            "total_score": total_score
        }
    
    def _check_preferred_working_time(self, employee, time_slot) -> int:
        """
        Verbesserte Implementierung zur Prüfung bevorzugter Arbeitszeiten
        
        Args:
            employee: Der zu prüfende Mitarbeiter
            time_slot: Der zu prüfende Zeitslot
            
        Returns:
            1 wenn die Zeit in den bevorzugten Arbeitszeiten liegt, sonst 0
        """
        try:
            # Ohne working_hours sind Standard-Arbeitszeiten bevorzugt (9-15 Uhr)
            if not hasattr(employee, 'working_hours') or not employee.working_hours:
                hour = time_slot.start_time.hour
                return 1 if 9 <= hour < 15 else 0
                
            # Wochentag (0=Montag, 6=Sonntag)
            day_of_week = time_slot.start_time.weekday()
            
            # Prüfen, ob Präferenz für diesen Tag existiert
            day_prefs = employee.working_hours.get(day_of_week)
            if not day_prefs or not day_prefs.get("preferred", False):
                # Als Fallback Standard-Arbeitszeiten verwenden
                hour = time_slot.start_time.hour
                return 1 if 9 <= hour < 15 else 0
            
            # Start- und Endzeiten aus den Präferenzen extrahieren
            start_str = day_prefs.get("start", "08:00")
            end_str = day_prefs.get("end", "17:00")
            
            # Stunden extrahieren
            start_hour = int(start_str.split(":")[0])
            end_hour = int(end_str.split(":")[0])
            task_hour = time_slot.start_time.hour
            
            # Prüfen, ob die Aufgabe innerhalb des bevorzugten Zeitfensters liegt
            if start_hour <= task_hour < end_hour:
                return 1
                
            return 0
        except Exception:
            # Bei Fehlern konservativ sein
            hour = time_slot.start_time.hour
            return 1 if 9 <= hour < 15 else 0
    
    def _evaluate_employee_workload(self):
        """
        Bewertet die Ausgewogenheit der Arbeitsbelastung der Mitarbeiter
        Verbesserte Version mit angemessener Skalierung
        """
        # Arbeitsbelastung pro Mitarbeiter berechnen
        workload = {}
        for task in self.tasks:
            if task.get_assigned_employee() is not None:
                emp_id = task.get_assigned_employee().id
                if emp_id not in workload:
                    workload[emp_id] = 0
                workload[emp_id] += task.duration
        
        # Durchschnittliche Arbeitsbelastung berechnen
        if not workload:
            self.soft_evaluations["Ausgewogene Arbeitsbelastung"] = 0
            self.soft_details["Ausgewogene Arbeitsbelastung"] = {
                "workloads": [],
                "average_workload": 0,
                "total_score": 0
            }
            return
            
        avg_workload = sum(workload.values()) / len(workload)
        
        # Abweichungen vom Durchschnitt berechnen
        deviations = []
        total_deviation = 0
        
        for emp_id, hours in workload.items():
            employee = next((e for e in self.employees if e.id == emp_id), None)
            if employee:
                deviation = abs(hours - avg_workload)
                total_deviation += deviation
                
                deviations.append({
                    "employee": employee.name,
                    "hours": hours,
                    "deviation": deviation,
                    "relative_deviation": deviation / avg_workload if avg_workload > 0 else 0
                })
        
        # VERBESSERT: Skalierung der Abweichung für angemessene Gewichtung
        # Berechne einen Ungleichgewichts-Faktor: je größer die Abweichung, desto größer der Abzug,
        # aber skaliert und begrenzt, um extreme Ausreißer zu vermeiden
        employee_count = len(workload)
        avg_deviation = total_deviation / employee_count if employee_count > 0 else 0
        
        # Skalierter Score - negative Punkte für Ungleichgewichte, aber mit vernünftiger Skalierung
        # Limitiere den maximalen Abzug auf die Anzahl der Mitarbeiter * 2
        max_penalty = employee_count * 2
        scaled_penalty = min(avg_deviation, max_penalty)
        deviation_score = -int(scaled_penalty)
        
        self.soft_evaluations["Ausgewogene Arbeitsbelastung"] = deviation_score
        self.soft_details["Ausgewogene Arbeitsbelastung"] = {
            "workloads": sorted(deviations, key=lambda x: x["deviation"], reverse=True),
            "average_workload": avg_workload,
            "average_deviation": avg_deviation,
            "total_deviation": total_deviation,
            "employee_count": employee_count,
            "total_score": deviation_score
        }
    
    def _evaluate_feedback_satisfaction(self):
        """
        Bewertet die Berücksichtigung des Mitarbeiter-Feedbacks
        Verbesserte Version mit korrekter Integration von direkten Feedback-Scores
        """
        total_score = 0
        considered_feedback = []
        ignored_feedback = []
        
        # Prüfen, ob Feedback vorhanden ist
        if not hasattr(self.solution, 'task_feedback') or not self.solution.task_feedback:
            self.soft_evaluations["Feedback-Berücksichtigung"] = 0
            self.soft_details["Feedback-Berücksichtigung"] = {
                "considered_feedback": [],
                "ignored_feedback": [],
                "total_score": 0,
                "has_feedback": False
            }
            return
        
        # Jede Aufgabe mit Feedback prüfen
        for (task_id, emp_id), rating in self.solution.task_feedback.items():
            # Die zugehörige Task finden
            task = next((t for t in self.tasks if t.id == task_id), None)
            if not task:
                continue
                
            # Die aktuelle Zuweisung prüfen
            current_emp = task.get_assigned_employee()
            if not current_emp:
                continue
            
            # Auswertung verbessern: Konsistenz mit den Constraint-Definitionen herstellen
            # Bewertung ist positiv, wenn:
            # - Positives Feedback (0/"Find ich gut") und der Mitarbeiter ist zugewiesen
            # - Negatives Feedback (-1/"Lieber nicht") und der Mitarbeiter ist NICHT zugewiesen
            is_positive_feedback = rating == 0
            is_correctly_assigned = (current_emp.id == emp_id) if is_positive_feedback else (current_emp.id != emp_id)
            
            # Score ermitteln: +2 für richtiges Assignment, -2 für falsches Assignment
            score_contribution = 0 if is_correctly_assigned else -1
            total_score += score_contribution
            
            # Details sammeln
            feedback_detail = {
                "task_id": task_id,
                "feedback_employee": next((e.name for e in self.employees if e.id == emp_id), "Unbekannt"),
                "assigned_employee": current_emp.name,
                "rating": "Positiv" if is_positive_feedback else "Negativ",
                "is_considered": is_correctly_assigned,
                "score": score_contribution
            }
            
            if is_correctly_assigned:
                considered_feedback.append(feedback_detail)
            else:
                ignored_feedback.append(feedback_detail)
        
        self.soft_evaluations["Feedback-Berücksichtigung"] = total_score
        self.soft_details["Feedback-Berücksichtigung"] = {
            "considered_feedback": considered_feedback,
            "ignored_feedback": ignored_feedback,
            "total_score": total_score,
            "has_feedback": True
        }
    
                       
    def get_soft_score(self) -> int:
        """
        Gibt den Soft-Score der Lösung zurück
        Robuste Implementierung für OptaPy-Objekte
        """
        try:
            if self.score is None:
                return 0
                
            # Für OptaPy Score-Objekte: direkt auf das Java-Objekt zugreifen
            # Das Java-Objekt verwenden - HardSoftScore in OptaPy hat keine Python-Methode soft_score(),
            # sondern verwendet das zugrundeliegende Java-Objekt
            if hasattr(self.score, 'toString'):
                # Java-Objekt als String darstellen
                score_str = str(self.score)
                # String im Format "-10hard/43soft" parsen
                if '/' in score_str:
                    parts = score_str.split('/')
                    if len(parts) == 2 and 'soft' in parts[1]:
                        return int(parts[1].replace('soft', ''))
            
            # Wenn wir bereits einen String haben, direkt parsen
            elif isinstance(self.score, str):
                if '/' in self.score:
                    parts = self.score.split('/')
                    if len(parts) == 2 and 'soft' in parts[1]:
                        return int(parts[1].replace('soft', ''))
                        
            # Fallback
            return 0
        except Exception as e:
            print(f"Fehler bei der Extraktion des Soft-Scores: {e}")
            return 0
    
    def get_summary(self) -> str:
        """
        Gibt eine formatierte Zusammenfassung der Soft-Constraint-Analyse zurück
        
        Returns:
            Formatierter String mit der Zusammenfassung
        """
        # Evaluierung sicherstellen, falls diese noch nicht durchgeführt wurde
        if not self.soft_evaluations:
            self.analyze()
        
        summary = []
        
        # Gesamtscore und Soft-Score
        summary.append(f"Gesamtscore: {self.score}")
        summary.append(f"Soft-Score: {self.soft_score}")
        summary.append("")
        
        # Beiträge der einzelnen Soft-Constraints
        summary.append("Beiträge der Soft-Constraints:")
        for constraint, score in self.soft_evaluations.items():
            summary.append(f"  {constraint}: {score} Punkte")
        summary.append("")
        
        # Details zur Fähigkeitsübereinstimmung
        if "Fähigkeitsübereinstimmung" in self.soft_details:
            skill_details = self.soft_details["Fähigkeitsübereinstimmung"]
            summary.append("Fähigkeitsübereinstimmungen:")
            summary.append(f"  Perfekte Übereinstimmungen: {len(skill_details.get('perfect_matches', []))}")
            summary.append(f"  Teilweise Übereinstimmungen: {len(skill_details.get('partial_matches', []))}")
            
            # Top 3 schlechteste Übereinstimmungen
            partial_matches = skill_details.get("partial_matches", [])
            if partial_matches:
                summary.append("  Top 3 verbesserungswürdige Zuweisungen:")
                worst_matches = sorted(partial_matches, key=lambda x: x.get("matched_skills", 0))[:3]
                for i, match in enumerate(worst_matches, 1):
                    missing = match.get("missing_skills", [])
                    missing_str = ", ".join(missing)
                    summary.append(f"    {i}. Aufgabe {match.get('task_id', '')} ({match.get('employee', '')}): Fehlende Skills: {missing_str}")
            summary.append("")
        
        # Details zu bevorzugten Arbeitszeiten
        if "Bevorzugte Arbeitszeiten" in self.soft_details:
            time_details = self.soft_details["Bevorzugte Arbeitszeiten"]
            preferred = time_details.get("preferred_times", [])
            non_preferred = time_details.get("non_preferred_times", [])
            summary.append("Arbeitszeiten:")
            summary.append(f"  Aufgaben in bevorzugten Zeiten: {len(preferred)}")
            summary.append(f"  Aufgaben außerhalb bevorzugter Zeiten: {len(non_preferred)}")
            summary.append("")
        
        # Details zur Arbeitsbelastung
        if "Ausgewogene Arbeitsbelastung" in self.soft_details:
            workload_details = self.soft_details["Ausgewogene Arbeitsbelastung"]
            workloads = workload_details.get("workloads", [])
            avg = workload_details.get("average_workload", 0)
            summary.append("Arbeitsbelastung:")
            summary.append(f"  Durchschnitt: {avg:.2f} Stunden")
            
            if workloads:
                # Top 3 Mitarbeiter mit höchster Abweichung
                top_deviations = sorted(workloads, key=lambda x: x.get("deviation", 0), reverse=True)[:3]
                summary.append("  Größte Abweichungen:")
                for i, entry in enumerate(top_deviations, 1):
                    hours = entry.get("hours", 0)
                    dev = entry.get("deviation", 0)
                    summary.append(f"    {i}. {entry.get('employee', '')}: {hours} Stunden ({dev:.2f} Abweichung)")
            summary.append("")
        
        # Details zur Feedback-Berücksichtigung
#        if "Feedback-Berücksichtigung" in self.soft_details:
 #           feedback_details = self.soft_details["Feedback-Berücksichtigung"]
  #          if feedback_details.get("has_feedback", False):
   #             considered = feedback_details.get("considered_feedback", [])
    #            ignored = feedback_details.get("ignored_feedback", [])
     #           summary.append("Feedback-Berücksichtigung:")
      ##          summary.append(f"  Berücksichtigtes Feedback: {len(considered)}")
        #        summary.append(f"  Ignoriertes Feedback: {len(ignored)}")
         #       
          #      if ignored:
           #         summary.append("  Nicht berücksichtigtes Feedback:")
            ##        for i, entry in enumerate(ignored[:3], 1):
              #          summary.append(f"    {i}. Aufgabe {entry.get('task_id', '')}: {entry.get('rating', '')} von {entry.get('feedback_employee', '')}")
            #summary.append("")
        
       
        return "\n".join(summary)