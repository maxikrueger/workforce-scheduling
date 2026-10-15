import tkinter as tk
from tkinter import messagebox
import os
from database.db_constants import DatabaseConstants
from logger import setup_logger
from scheduling_app import SchedulingApp

def main():
    # Logger einrichten
    logger = setup_logger()
    logger.info("Anwendung gestartet")
    
    try:
        # Datenverzeichnis erstellen
        os.makedirs(os.path.dirname(DatabaseConstants.DB_PATH), exist_ok=True)
        
        # App starten
        root = tk.Tk()
        app = SchedulingApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Fehler: {e}", exc_info=True)
        messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    finally:
        logger.info("Anwendung beendet")

if __name__ == "__main__":
    main()