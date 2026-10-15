import tkinter as tk
from tkinter import ttk

class StatsBuilder:
    """
    Klasse zum Erstellen der Statistikansicht
    Nutzt die DetailView-Komponente für die Darstellung
    """
    
    def create_stats_view(self, stats_frame, solution):
        """
        Erstellt die Statistikansicht mit allen Analysen
        
        Args:
            stats_frame: Der Frame aus DetailView.stats_frame, in dem die Statistik angezeigt wird
            solution: Das Schedule-Objekt mit der Lösung
        """
        # Bestehende Widgets löschen
        for widget in stats_frame.winfo_children():
            widget.destroy()
        
        if not solution:
            ttk.Label(stats_frame, text="Keine Statistik verfügbar.\nErstelle einen Zeitplan.").pack(pady=20)
            return
        
        # 1. Gesamtübersicht
        self._create_overview_section(stats_frame, solution)
        
        # 2. Ressourcenauslastung
        self._create_resource_section(stats_frame, solution)
        
        # 3. Skill-Analyse
        self._create_skill_section(stats_frame, solution)
        
        # 4. Aufgaben-Komplexitätsverteilung
        self._create_complexity_section(stats_frame, solution)
        
        # Score anzeigen
        score_label = ttk.Label(stats_frame, 
                                text=f"Optimierungsscore: {solution.get_score()}", 
                                font=('TkDefaultFont', 10, 'bold'))
        score_label.pack(anchor='w', padx=5, pady=5)
    
    def _create_overview_section(self, parent, solution):
        """Erstellt die Gesamtübersicht"""
        overview_frame = ttk.LabelFrame(parent, text="Gesamtübersicht")
        overview_frame.pack(fill='x', padx=5, pady=5)
        
        total_tasks = len(solution.get_tasks())
        assigned_tasks = [task for task in solution.get_tasks() 
                        if task.get_assigned_employee() and task.get_time_slot()]
        unassigned_tasks = [task for task in solution.get_tasks() 
                        if not task.get_assigned_employee() or not task.get_time_slot()]
        
        ttk.Label(overview_frame, text=f"Gesamtzahl Aufgaben: {total_tasks}").pack(anchor='w')
        ttk.Label(overview_frame, text=f"Zugewiesene Aufgaben: {len(assigned_tasks)}", 
                foreground='green').pack(anchor='w')
        ttk.Label(overview_frame, text=f"Nicht zugewiesene Aufgaben: {len(unassigned_tasks)}", 
                foreground='red').pack(anchor='w')
        
        # Unzugewiesene Aufgaben anzeigen, wenn vorhanden
        if unassigned_tasks:
            unassigned_frame = ttk.LabelFrame(parent, text="Nicht zugewiesene Aufgaben")
            unassigned_frame.pack(fill='x', padx=5, pady=5)
            
            for task in unassigned_tasks:
                ttk.Label(unassigned_frame, 
                        text=f"• {task.id} (Skills: {', '.join(task.required_skills)})", 
                        foreground='red').pack(anchor='w')
    
    def _create_resource_section(self, parent, solution):
        """Erstellt die Ressourcenauslastungsstatistik"""
        resource_frame = ttk.LabelFrame(parent, text="Ressourcenauslastung")
        resource_frame.pack(fill='x', padx=5, pady=5)
        
        # Arbeitszeit-Statistiken berechnen
        assigned_tasks = [task for task in solution.get_tasks() 
                         if task.get_assigned_employee() and task.get_time_slot()]
        
        # Sammle Arbeitszeiten pro Mitarbeiter
        employee_tasks = {}
        employee_total_hours = {}
        
        for task in assigned_tasks:
            emp = task.get_assigned_employee()
            if emp.id not in employee_tasks:
                employee_tasks[emp.id] = []
            employee_tasks[emp.id].append(task)
        
        # Berechne Gesamtstunden
        total_work_hours = 0
        for emp_id, tasks in employee_tasks.items():
            hours = sum(task.duration for task in tasks)
            employee_total_hours[emp_id] = hours
            total_work_hours += hours
        
        # Durchschnittliche Arbeitszeit
        avg_work_hours = total_work_hours / len(solution.get_employees()) if solution.get_employees() else 0
        
        ttk.Label(resource_frame, text=f"Gesamte Arbeitsstunden: {total_work_hours}").pack(anchor='w')
        ttk.Label(resource_frame, text=f"Durchschnittliche Arbeitsstunden pro Mitarbeiter: {avg_work_hours:.2f}").pack(anchor='w')
        
        # Mitarbeiter-Auslastung
        employee_utilization_frame = ttk.LabelFrame(parent, text="Mitarbeiter-Auslastung")
        employee_utilization_frame.pack(fill='x', padx=5, pady=5)
        
        for emp in solution.get_employees():
            tasks = employee_tasks.get(emp.id, [])
            hours = employee_total_hours.get(emp.id, 0)
            
            # Berechne Auslastungsgrad
            utilization_percentage = (hours / avg_work_hours * 100) if avg_work_hours > 0 else 0
            
            frame = ttk.Frame(employee_utilization_frame)
            frame.pack(fill='x', pady=2)
            
            ttk.Label(frame, text=f"{emp.name}: {len(tasks)} Aufgaben ({hours} Stunden)").pack(side='left')
            ttk.Label(frame, 
                    text=f"({utilization_percentage:.1f}% Auslastung)", 
                    foreground='blue' if tasks else 'gray').pack(side='left', padx=5)
    
    def _create_skill_section(self, parent, solution):
        """Erstellt die Skill-Analyse"""
        skill_frame = ttk.LabelFrame(parent, text="Skill-Analyse")
        skill_frame.pack(fill='x', padx=5, pady=5)
        
        # Sammle alle benötigten und vorhandenen Skills
        all_required_skills = set()
        matched_skills = {}
        
        assigned_tasks = [task for task in solution.get_tasks() 
                        if task.get_assigned_employee() and task.get_time_slot()]
        
        for task in assigned_tasks:
            all_required_skills.update(task.required_skills)
            emp = task.get_assigned_employee()
            
            for skill in task.required_skills:
                if emp.has_skill(skill):
                    matched_skills[skill] = matched_skills.get(skill, 0) + 1
        
        # Skill-Match-Rate
        skill_match_rate = len(matched_skills) / len(all_required_skills) * 100 if all_required_skills else 0
        
        ttk.Label(skill_frame, text=f"Benötigte Skills: {len(all_required_skills)}").pack(anchor='w')
        ttk.Label(skill_frame, 
                text=f"Skill-Match-Rate: {skill_match_rate:.1f}%", 
                foreground='green').pack(anchor='w')
        
        # Top gematchte Skills
        top_matched_skills = sorted(matched_skills.items(), key=lambda x: x[1], reverse=True)[:5]
        ttk.Label(skill_frame, text="Top gematchte Skills:").pack(anchor='w')
        for skill, count in top_matched_skills:
            ttk.Label(skill_frame, text=f"- {skill}: {count} Matches").pack(anchor='w')
    
    def _create_complexity_section(self, parent, solution):
        """Erstellt die Aufgaben-Komplexitätsverteilung"""
        complexity_frame = ttk.LabelFrame(parent, text="Aufgaben-Komplexität")
        complexity_frame.pack(fill='x', padx=5, pady=5)
        
        assigned_tasks = [task for task in solution.get_tasks() 
                        if task.get_assigned_employee() and task.get_time_slot()]
        
        # Kategorisiere Aufgaben nach Dauer
        task_complexity = {
            "Kurz (1h)": len([t for t in assigned_tasks if t.duration == 1]),
            "Mittel (2h)": len([t for t in assigned_tasks if t.duration == 2]),
            "Lang (3h)": len([t for t in assigned_tasks if t.duration == 3]),
            "Sehr lang (4h)": len([t for t in assigned_tasks if t.duration == 4])
        }
        
        for complexity, count in task_complexity.items():
            ttk.Label(complexity_frame, text=f"{complexity}: {count} Aufgaben").pack(anchor='w')