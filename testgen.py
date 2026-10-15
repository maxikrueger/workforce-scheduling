from datetime import datetime, timedelta
import random
import uuid
from typing import List, Set, Dict, Optional

# Import der Klassen aus der Core-Datei
from core import TimeSlot, Employee, Task, Schedule, EmployeeStatus

# Liste von Fähigkeiten nach Kategorien
SKILLS = {
    'frontend': ['javascript', 'html', 'css', 'react', 'angular', 'vue'],
#'backend': ['python', 'java', 'nodejs', 'spring', 'django'],
 #   'database': ['sql', 'mongodb', 'postgresql'],
  #  'devops': ['docker', 'kubernetes', 'aws']
}

# Liste von Vornamen und Nachnamen für die Generierung von Mitarbeiternamen
FIRST_NAMES = ["Anna", "Max", "Sophie", "Tim", "Laura", "Felix", "Sarah", "Lukas", "Lisa", "Paul",
               "Emma", "Noah", "Mia", "Liam", "Emilia", "Ben", "Hannah", "Jonas", "Lena", "Finn"]
LAST_NAMES = ["Schmidt", "Müller", "Weber", "Schneider", "Fischer", "Meyer", "Wagner", "Becker", "Hoffmann", "Koch",
              "Schulz", "Schäfer", "Bauer", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann"]

def generate_random_name() -> str:
    """Generiert einen zufälligen Namen aus den Namenslisten"""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def generate_skill_set(skill_count: int) -> Set[str]:
    """Generiert eine Menge von Fähigkeiten mit genau der angegebenen Anzahl"""
    # Flache Liste aller Fähigkeiten erstellen
    all_skills = [skill for category in SKILLS.values() for skill in category]
    
    # Zufällige Anzahl von Fähigkeiten auswählen
    skill_count = min(skill_count, len(all_skills))
    
    # Zufällige Fähigkeiten auswählen
    return set(random.sample(all_skills, skill_count))

def generate_time_slots(start_date: datetime, days: int, 
                      start_hour: int = 8, end_hour: int = 17) -> List[TimeSlot]:
    """Generiert Zeitslots für mehrere Tage"""
    slots = []
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        # Wochenenden überspringen
        if current_date.weekday() >= 5:  # 5 = Samstag, 6 = Sonntag
            continue
            
        for hour in range(start_hour, end_hour):
            slot_id = f"slot_{day}_{hour}"
            slot_time = current_date.replace(hour=hour, minute=0)
            slots.append(TimeSlot(slot_id, slot_time))
    
    return slots

def generate_employees(count: int) -> List[Employee]:
    """
    Generiert eine Liste von Mitarbeitern mit verschiedenen Fähigkeiten und Präferenzen
    
    Verbesserte Version mit mehr Fähigkeiten pro Mitarbeiter für bessere Zuordnungsmöglichkeiten
    und definiertem Arbeitszeiten-Dictionary.
    """
    employees = []
    
    # Flache Liste aller Fähigkeiten erstellen
    all_skills = [skill for category in SKILLS.values() for skill in category]
    
    for i in range(count):
        # Eindeutige ID generieren
        emp_id = f"emp_{i+1}"
        
        # Namen generieren
        name = generate_random_name()
        
        # Fähigkeiten je nach Erfahrungslevel generieren
        if i < count // 4:  # Top 25% sind Senior (5-8 Fähigkeiten)
            skills_count = random.randint(5, 8)
        elif i < count // 2:  # Nächste 25% sind Fortgeschrittene (3-5 Fähigkeiten)
            skills_count = random.randint(3, 5)
        else:  # Rest sind Junior (1-3 Fähigkeiten)
            skills_count = random.randint(1, 3)
        
        # Fähigkeiten auswählen
        skills = generate_skill_set(skills_count)
        
        # Bevorzugte Fähigkeiten aus den vorhandenen Fähigkeiten wählen
        # Zwischen 1 und 2 bevorzugte Fähigkeiten, aber nicht mehr als die Hälfte
        pref_count = min(2, len(skills) // 2 + 1)
        preferred_skills = set(random.sample(list(skills), pref_count))
        
        # Status setzen (die meisten sind verfügbar)
        status = EmployeeStatus.AVAILABLE
        if random.random() < 0.05:  # 5% sind beschäftigt
            status = EmployeeStatus.BUSY
        elif random.random() < 0.03:  # 3% sind abwesend
            status = EmployeeStatus.OFF
        
        # Arbeitszeiten-Dictionary erstellen
        working_hours = {}
        for day in range(5):  # 0-4 (Montag-Freitag)
            # Typische Arbeitszeiten
            if random.random() < 0.7:  # 70% Standard 8-17 Uhr
                start = "08:00"
                end = "17:00"
            elif random.random() < 0.5:  # Hälfte der übrigen früh 7-16 Uhr
                start = "07:00"
                end = "16:00"
            else:  # Rest spät 9-18 Uhr
                start = "09:00"
                end = "18:00"
            
            working_hours[day] = {
                "start": start,
                "end": end,
                "preferred": True  # Alle Wochentage sind bevorzugt
            }
        
        # Wochenende (optional, nur 10% arbeiten am Samstag)
        if random.random() < 0.1:
            working_hours[5] = {  # Samstag
                "start": "09:00",
                "end": "14:00",
                "preferred": False  # Nicht bevorzugt
            }
        
        # Mitarbeiter erstellen
        employees.append(Employee(
            emp_id, 
            name, 
            skills, 
            status, 
            preferred_skills, 
            working_hours
        ))
    
    return employees

def generate_tasks(count: int) -> List[Task]:
    """
    Generiert eine Liste von Aufgaben mit jeweils genau einer Fähigkeitsanforderung
    
    Jede Aufgabe erfordert genau eine Fähigkeit, wobei die Fähigkeiten aus allen
    verfügbaren Kategorien gleichmäßig verteilt werden.
    """
    tasks = []
    
    # Flache Liste aller Fähigkeiten erstellen
    all_skills = [skill for category in SKILLS.values() for skill in category]
    
    for i in range(count):
        # Eindeutige ID generieren
        task_id = f"Task_{i+1}"
        
        # Dauer generieren (1-4 Stunden)
        duration = random.randint(1, 4)
        
        # Genau eine zufällige Fähigkeit auswählen
        required_skill = random.choice(all_skills)
        required_skills = {required_skill}
        
        # Name für die Aufgabe generieren (basierend auf Fähigkeit)
        task_name = f"{required_skill.capitalize()}-Aufgabe {i+1}"
        
        # Aufgabe erstellen
        task = Task(task_id, duration, required_skills)
        task.name = task_name
        
        # Priorität zufällig setzen
        priorities = ["high", "medium", "low"]
        priority_weights = [0.2, 0.5, 0.3]  # 20% hoch, 50% mittel, 30% niedrig
        task.priority = random.choices(priorities, weights=priority_weights)[0]
        
        tasks.append(task)
    
    return tasks

def generate_test_case(complexity: str = "medium") -> Schedule:
    """
    Generiert einen Testfall mit unterschiedlicher Komplexität
    
    Args:
        complexity: "simple", "medium", "complex" oder "very_complex"
        
    Returns:
        Schedule: Ein generiertes Schedule-Objekt mit passender Menge an Aufgaben
                 für eine hohe Auslastung
    """
    # Parameter basierend auf Komplexität festlegen
    if complexity == "simple":
        employee_count = 2
        days = 1
        # Aufgabenanzahl wird später berechnet
    elif complexity == "medium":
        employee_count = 4
        days = 2
    elif complexity == "complex":
        employee_count = 5
        days = 7
    elif complexity == "very_complex":
        employee_count = 6
        days = 10
    else:
        # Standard ist medium
        employee_count = 4
        days = 2
    
    # Schedule erstellen
    schedule = Schedule()
    schedule.name = f"Testfall {complexity} - {datetime.now().strftime('%d.%m.%Y')}"
    
    # Zeitslots generieren (ab heute)
    start_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    schedule.time_slots = generate_time_slots(start_date, days)
    
    # Mitarbeiter generieren
    schedule.employees = generate_employees(employee_count)
    
    # Anzahl der Arbeitstage berechnen (ohne Wochenenden)
    workdays = sum(1 for day in range(days) if (start_date + timedelta(days=day)).weekday() < 5)
    
    # Berechnung der verfügbaren Arbeitsstunden: 
    # Mitarbeiter × Arbeitstage × 8 Stunden × Auslastungsfaktor (0.85 für 85% Auslastung)
    auslastungsfaktor = 0.85
    available_hours = employee_count * workdays * 8 * auslastungsfaktor
    
    # Durchschnittliche Aufgabendauer (2.5 Stunden)
    avg_task_duration = 2.5
    
    # Berechne Aufgabenanzahl für die gewünschte Auslastung
    task_count = int(available_hours / avg_task_duration)
    
    # Mindestanzahl an Aufgaben sicherstellen
    min_tasks = {
        "simple": 10,
        "medium": 20,
        "complex": 40,
        "very_complex": 70
    }
    
    task_count = max(task_count, min_tasks.get(complexity, 20))
    
    # Ausgabe für Debug-Zwecke
    print(f"Komplexität: {complexity}")
    print(f"Mitarbeiter: {employee_count}")
    print(f"Arbeitstage: {workdays} (von {days} Tagen)")
    print(f"Verfügbare Arbeitsstunden: {available_hours:.1f}")
    print(f"Benötigte Aufgaben für {auslastungsfaktor*100:.0f}% Auslastung: {task_count}")
    
    # Aufgaben generieren
    schedule.tasks = generate_tasks(task_count)
    
    return schedule

# Test der Funktion
if __name__ == "__main__":
    # Einen komplexen Testfall generieren
    test_schedule = generate_test_case("complex")
    
    print(f"\nGenerierter Zeitplan:")
    print(f"- Name: {test_schedule.name}")
    print(f"- {len(test_schedule.time_slots)} Zeitslots")
    print(f"- {len(test_schedule.employees)} Mitarbeiter")
    print(f"- {len(test_schedule.tasks)} Aufgaben")
    
    # Gesamte Aufgabendauer berechnen
    total_duration = sum(task.duration for task in test_schedule.tasks)
    print(f"- Gesamte Aufgabendauer: {total_duration} Stunden")
    
    # Verfügbare Fähigkeiten berechnen
    all_employee_skills = set()
    for employee in test_schedule.employees:
        all_employee_skills.update(employee.skills)
    
    # Benötigte Fähigkeiten prüfen
    required_skills = set()
    for task in test_schedule.tasks:
        required_skills.update(task.required_skills)
    
    print(f"- Verfügbare Fähigkeiten: {len(all_employee_skills)}")
    print(f"- Benötigte Fähigkeiten: {len(required_skills)}")
    
    # Prüfen, ob alle Aufgaben erfüllbar sind
    missing_skills = required_skills - all_employee_skills
    if missing_skills:
        print(f"Warnung: Folgende Fähigkeiten werden benötigt, aber von keinem Mitarbeiter beherrscht:")
        for skill in missing_skills:
            print(f"  - {skill}")
    else:
        print("Alle benötigten Fähigkeiten können erfüllt werden.")