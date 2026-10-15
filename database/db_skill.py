from typing import List, Tuple, Dict, Any, Optional
from database.db_base import DBBaseManager

class SkillManager(DBBaseManager):
    """Manager-Klasse für alle Skill-bezogenen Datenbankoperationen"""
    
    def get_or_create_skill_id(self, skill_name: str) -> str:
        """
        Gibt die ID eines Skills zurück oder erstellt einen neuen Skill.
        
        Args:
            skill_name: Name des Skills
            
        Returns:
            ID des Skills
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Nach bestehendem Skill suchen
                cursor.execute('SELECT id FROM skills WHERE name = ?', (skill_name.lower(),))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                
                # Wenn nicht gefunden, neuen Skill erstellen
                new_id = self.generate_id("skill")
                
                cursor.execute('INSERT INTO skills (id, name) VALUES (?, ?)', 
                               (new_id, skill_name.lower()))
                
                return new_id
        except Exception as e:
            print(f"Fehler beim Abrufen/Erstellen des Skills: {e}")
            return None
    
    def add_skill(self, name: str, id: str = None) -> str:
        """
        Fügt einen neuen Skill hinzu.
        
        Args:
            name: Name des Skills
            id: Optional - ID des Skills; wenn nicht angegeben, wird eine generiert
            
        Returns:
            ID des Skills
        """
        try:
            skill_id = id if id else self.generate_id("skill")
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO skills (id, name) VALUES (?, ?)',
                               (skill_id, name.lower()))
                return skill_id
        except Exception as e:
            print(f"Fehler beim Hinzufügen des Skills: {e}")
            return None
    
    def get_all_skills(self) -> List[Tuple[str, str]]:
        """
        Gibt alle verfügbaren Skills zurück.
        
        Returns:
            Liste von Tupeln (id, name)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, name FROM skills ORDER BY name')
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen der Skills: {e}")
            return []
    
    def get_skill(self, skill_id: str) -> Optional[Tuple[str, str]]:
        """
        Gibt einen Skill anhand seiner ID zurück.
        
        Args:
            skill_id: ID des Skills
            
        Returns:
            Tuple (id, name) oder None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, name FROM skills WHERE id = ?', (skill_id,))
                return cursor.fetchone()
        except Exception as e:
            print(f"Fehler beim Abrufen des Skills: {e}")
            return None
    
    def update_skill(self, skill_id: str, name: str) -> bool:
        """
        Aktualisiert einen Skill.
        
        Args:
            skill_id: ID des Skills
            name: Neuer Name des Skills
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE skills SET name = ? WHERE id = ?', (name.lower(), skill_id))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Skills: {e}")
            return False
    
    def delete_skill(self, skill_id: str) -> bool:
        """
        Löscht einen Skill anhand seiner ID.
        
        Args:
            skill_id: ID des Skills
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM skills WHERE id = ?', (skill_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Löschen des Skills: {e}")
            return False
    
    def get_skills_by_names(self, skill_names: List[str]) -> List[Tuple[str, str]]:
        """
        Gibt Skills anhand ihrer Namen zurück.
        
        Args:
            skill_names: Liste von Skill-Namen
            
        Returns:
            Liste von Tupeln (id, name)
        """
        if not skill_names:
            return []
            
        try:
            placeholders = ', '.join(['?'] * len(skill_names))
            query = f'SELECT id, name FROM skills WHERE name IN ({placeholders})'
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, [name.lower() for name in skill_names])
                return cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Abrufen der Skills: {e}")
            return []