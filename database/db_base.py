import sqlite3
import os
from typing import List, Tuple, Dict, Any, Optional, Union
import uuid
from database.db_constants import DatabaseConstants


class DBBaseManager:
    """Basisklasse für alle datenbankspezifischen Manager-Klassen"""
    
    def __init__(self, db_name: str = "workforce_scheduling.db"):
        """
        Initialisiert den Basis-Datenbankmanager
        
        Args:
            db_name: Name der Datenbankdatei
        """
        if db_name:
            self.db_name = db_name
        else:
            self.db_name = DatabaseConstants.DB_PATH

        # Sicherstellen, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(self.db_name), exist_ok=True)    
    
    
    def get_connection(self):
        """Erstellt und gibt eine Datenbankverbindung zurück"""
        conn = sqlite3.connect(self.db_name, timeout=10)
        # Aktiviere Foreign Key Constraints
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def execute_query(self, query: str, params: tuple = None) -> Any:
        """
        Führt eine SQL-Abfrage aus und gibt die Ergebnisse zurück.
        
        Args:
            query: SQL-Abfrage
            params: Parameter für die Abfrage (optional)
            
        Returns:
            Ergebnismenge oder None bei INSERT/UPDATE/DELETE
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Prüfen, ob es sich um eine SELECT-Abfrage handelt
                if query.strip().upper().startswith("SELECT"):
                    return cursor.fetchall()
                else:
                    return cursor.rowcount
        except Exception as e:
            print(f"Fehler bei der Ausführung der Abfrage: {e}")
            return None
    
    def generate_id(self, prefix: str = "id") -> str:
        """
        Generiert eine eindeutige ID mit Präfix
        
        Args:
            prefix: Präfix für die ID
            
        Returns:
            Eindeutige ID
        """
        return f"{prefix}_{uuid.uuid4().hex[:8]}"