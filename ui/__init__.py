# ui/__init__.py
"""
UI-Komponenten für die Scheduling-App

Enthält Module für:
- main_view: Hauptansicht der Anwendung
- calendar_builder: Erstellung des Kalender-Grids
- stats_builder: Erstellung der Statistik-Ansicht
"""

from ui.main_view import MainView
from ui.calendar_builder import CalendarBuilder
from ui.stats_builder import StatsBuilder

__all__ = ['MainView', 'CalendarBuilder', 'StatsBuilder']