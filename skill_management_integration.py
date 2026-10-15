from tkinter import ttk
import uuid
from dialogs.skill_management_dialog import SkillManagementDialog

def add_skill_management_to_app(app):
    """
    Fügt die Skill-Management-Funktionalität zur SchedulingApp hinzu
    
    Diese Funktion integriert die Skill-Management-Funktionalität und übergibt
    den Callback direkt an die Toolbar für den Fähigkeiten-Button.
    """
    
    # Methode hinzufügen, um die Skills zu verwalten
    def manage_skills(self):
        """Öffnet den Dialog zur Verwaltung der verfügbaren Fähigkeiten"""
        dialog = SkillManagementDialog(self.root, self.available_skills, self.update_available_skills)
    
    def update_available_skills(self, updated_skills):
        """Aktualisiert die verfügbaren Skills in der Anwendung und der Datenbank"""
        self.available_skills = updated_skills
        
        # In der Datenbank speichern
        try:
            # Existierende Skills laden
            existing_skills = {name: id for id, name in self.db_manager.get_all_skills()}
            
            # Für jede Kategorie und Skill
            for category, skills in updated_skills.items():
                for skill in skills:
                    # Prüfen, ob Skill bereits existiert
                    if skill not in existing_skills:
                        # Neuen Skill anlegen
                        skill_id = f"skill_{uuid.uuid4().hex[:8]}"
                        self.db_manager.add_skill(skill_id, skill)
        except Exception as e:
            print(f"Fehler beim Speichern der Skills: {e}")
        
        # DetailView über die Änderung informieren
        if hasattr(self, 'detail_view'):
            self.detail_view.available_skills = updated_skills
    
    # Methoden an die Klasse anhängen
    app.manage_skills = manage_skills.__get__(app, type(app))
    app.update_available_skills = update_available_skills.__get__(app, type(app))