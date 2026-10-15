import os
import sys
import appdirs

class DatabaseConstants:
    APP_NAME = "workforce_scheduling"
    APP_AUTHOR = "workforce_scheduling"
    DB_PATH = os.path.join(appdirs.user_data_dir(APP_NAME, APP_AUTHOR), "workforce_scheduling.db")
    
    @staticmethod
    def get_resource_path(relative_path):
        """Gibt den absoluten Pfad zur Ressource zurück"""
        # Sicherstellen, dass relative_path nicht None ist
        if relative_path is None:
            relative_path = ""
            
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller-Modus
            return os.path.join(sys._MEIPASS, relative_path)
        # Normaler Modus
        base_dir = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(os.path.dirname(base_dir), relative_path)