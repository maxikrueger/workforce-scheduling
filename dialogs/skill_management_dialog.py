import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional, Callable

class SkillManagementDialog(tk.Toplevel):
    """Dialog zur Verwaltung der verfügbaren Fähigkeiten (Skills)"""
    
    def __init__(self, parent, available_skills: Dict[str, List[str]], 
                 on_update: Callable[[Dict[str, List[str]]], None] = None):
        super().__init__(parent)
        self.title("Fähigkeiten verwalten")
        self.transient(parent)
        self.resizable(True, True)
        self.geometry("700x500")
        
        # Deep copy der verfügbaren Skills erstellen, damit wir sie bearbeiten können
        self.available_skills = {category: skills.copy() for category, skills in available_skills.items()}
        self.on_update = on_update
        
        self.create_widgets()
        
        # Dialog mittig zum Parent positionieren
        self.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}")
        
        # Dialog modal machen
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.focus_set()
    
    def create_widgets(self):
        """Erstellt die UI-Elemente des Dialogs"""
        # Hauptframe mit Padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Überschrift
        ttk.Label(main_frame, text="Verfügbare Fähigkeiten verwalten", font=('TkDefaultFont', 12, 'bold')).pack(
            anchor='w', pady=(0, 10))
        
        # Kategorien-Frame und Skills-Frame (zwei Spalten)
        columns_frame = ttk.Frame(main_frame)
        columns_frame.pack(fill='both', expand=True, pady=5)
        
        # Linke Spalte: Kategorien
        categories_frame = ttk.LabelFrame(columns_frame, text="Kategorien")
        categories_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Rechte Spalte: Skills für ausgewählte Kategorie
        skills_frame = ttk.LabelFrame(columns_frame, text="Fähigkeiten")
        skills_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Kategorien-Listbox mit Scrollbar
        categories_scroll = ttk.Scrollbar(categories_frame)
        categories_scroll.pack(side='right', fill='y')
        
        self.categories_listbox = tk.Listbox(categories_frame, selectmode='single', 
                                           yscrollcommand=categories_scroll.set)
        self.categories_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        categories_scroll.config(command=self.categories_listbox.yview)
        
        # Button-Frame für Kategorien
        cat_button_frame = ttk.Frame(categories_frame)
        cat_button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(cat_button_frame, text="Hinzufügen", command=self.add_category).pack(side='left', padx=(0, 2))
        ttk.Button(cat_button_frame, text="Umbenennen", command=self.rename_category).pack(side='left', padx=2)
        ttk.Button(cat_button_frame, text="Löschen", command=self.delete_category).pack(side='left', padx=2)
        
        # Skills-Listbox mit Scrollbar
        skills_scroll = ttk.Scrollbar(skills_frame)
        skills_scroll.pack(side='right', fill='y')
        
        self.skills_listbox = tk.Listbox(skills_frame, selectmode='single', 
                                       yscrollcommand=skills_scroll.set)
        self.skills_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        skills_scroll.config(command=self.skills_listbox.yview)
        
        # Button-Frame für Skills
        skill_button_frame = ttk.Frame(skills_frame)
        skill_button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(skill_button_frame, text="Hinzufügen", command=self.add_skill).pack(side='left', padx=(0, 2))
        ttk.Button(skill_button_frame, text="Umbenennen", command=self.rename_skill).pack(side='left', padx=2)
        ttk.Button(skill_button_frame, text="Löschen", command=self.delete_skill).pack(side='left', padx=2)
        
        # Button-Frame am unteren Rand
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Speichern- und Schließen-Buttons
        ttk.Button(button_frame, text="Speichern", command=self.save_changes).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.on_close).pack(side='right')
        
        # Event-Binding für Kategorie-Wechsel
        self.categories_listbox.bind('<<ListboxSelect>>', self.on_category_selected)
        
        # Initial Kategorien laden
        self.load_categories()
    
    def load_categories(self):
        """Lädt die verfügbaren Kategorien in die Listbox"""
        self.categories_listbox.delete(0, tk.END)
        
        # Sortierte Liste der Kategorien
        categories = sorted(self.available_skills.keys())
        
        for category in categories:
            self.categories_listbox.insert(tk.END, category)
        
        # Erste Kategorie auswählen, wenn vorhanden
        if categories:
            self.categories_listbox.selection_set(0)
            self.on_category_selected(None)
    
    def load_skills(self, category: str):
        """Lädt die Skills einer Kategorie in die Listbox"""
        self.skills_listbox.delete(0, tk.END)
        
        if category in self.available_skills:
            # Sortierte Liste der Skills
            skills = sorted(self.available_skills[category])
            
            for skill in skills:
                self.skills_listbox.insert(tk.END, skill)
    
    def on_category_selected(self, event):
        """Behandelt die Auswahl einer Kategorie"""
        selected_indices = self.categories_listbox.curselection()
        
        if selected_indices:
            selected_category = self.categories_listbox.get(selected_indices[0])
            self.load_skills(selected_category)
        else:
            self.skills_listbox.delete(0, tk.END)
    
    def add_category(self):
        """Fügt eine neue Kategorie hinzu"""
        new_category = simpledialog.askstring("Neue Kategorie", 
                                            "Name der neuen Kategorie:", parent=self)
        
        if new_category:
            # Doppelte Einträge vermeiden
            new_category = new_category.strip().lower()
            
            if not new_category:
                messagebox.showwarning("Warnung", "Der Name der Kategorie darf nicht leer sein.")
                return
            
            if new_category in self.available_skills:
                messagebox.showwarning("Warnung", f"Die Kategorie '{new_category}' existiert bereits.")
                return
            
            # Neue Kategorie mit leerer Skill-Liste hinzufügen
            self.available_skills[new_category] = []
            
            # Listen aktualisieren
            self.load_categories()
            
            # Neue Kategorie selektieren
            for i in range(self.categories_listbox.size()):
                if self.categories_listbox.get(i) == new_category:
                    self.categories_listbox.selection_set(i)
                    self.on_category_selected(None)
                    break
    
    def rename_category(self):
        """Benennt eine bestehende Kategorie um"""
        selected_indices = self.categories_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie eine Kategorie zum Umbenennen aus.")
            return
        
        old_name = self.categories_listbox.get(selected_indices[0])
        new_name = simpledialog.askstring("Kategorie umbenennen", 
                                        f"Neuer Name für '{old_name}':", parent=self)
        
        if new_name:
            # Doppelte Einträge vermeiden
            new_name = new_name.strip().lower()
            
            if not new_name:
                messagebox.showwarning("Warnung", "Der Name der Kategorie darf nicht leer sein.")
                return
            
            if new_name in self.available_skills:
                messagebox.showwarning("Warnung", f"Die Kategorie '{new_name}' existiert bereits.")
                return
            
            # Kategorie umbenennen
            self.available_skills[new_name] = self.available_skills.pop(old_name)
            
            # Listen aktualisieren
            self.load_categories()
            
            # Neue Kategorie selektieren
            for i in range(self.categories_listbox.size()):
                if self.categories_listbox.get(i) == new_name:
                    self.categories_listbox.selection_set(i)
                    self.on_category_selected(None)
                    break
    
    def delete_category(self):
        """Löscht eine Kategorie"""
        selected_indices = self.categories_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie eine Kategorie zum Löschen aus.")
            return
        
        category = self.categories_listbox.get(selected_indices[0])
        
        # Bestätigung einholen
        if messagebox.askyesno("Kategorie löschen", 
                             f"Möchten Sie die Kategorie '{category}' mit allen darin enthaltenen Fähigkeiten wirklich löschen?"):
            # Kategorie löschen
            del self.available_skills[category]
            
            # Listen aktualisieren
            self.load_categories()
    
    def add_skill(self):
        """Fügt eine neue Fähigkeit zur ausgewählten Kategorie hinzu"""
        selected_cat_indices = self.categories_listbox.curselection()
        
        if not selected_cat_indices:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie eine Kategorie aus.")
            return
        
        category = self.categories_listbox.get(selected_cat_indices[0])
        
        # Neuen Skill abfragen
        new_skill = simpledialog.askstring("Neue Fähigkeit", 
                                         f"Name der neuen Fähigkeit in '{category}':", parent=self)
        
        if new_skill:
            # Doppelte Einträge vermeiden
            new_skill = new_skill.strip().lower()
            
            if not new_skill:
                messagebox.showwarning("Warnung", "Der Name der Fähigkeit darf nicht leer sein.")
                return
            
            if new_skill in self.available_skills[category]:
                messagebox.showwarning("Warnung", f"Die Fähigkeit '{new_skill}' existiert bereits in dieser Kategorie.")
                return
            
            # Skill hinzufügen
            self.available_skills[category].append(new_skill)
            
            # Skills neu laden
            self.load_skills(category)
            
            # Neuen Skill selektieren
            for i in range(self.skills_listbox.size()):
                if self.skills_listbox.get(i) == new_skill:
                    self.skills_listbox.selection_set(i)
                    break
    
    def rename_skill(self):
        """Benennt eine bestehende Fähigkeit um"""
        selected_cat_indices = self.categories_listbox.curselection()
        selected_skill_indices = self.skills_listbox.curselection()
        
        if not selected_cat_indices or not selected_skill_indices:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie eine Kategorie und eine Fähigkeit zum Umbenennen aus.")
            return
        
        category = self.categories_listbox.get(selected_cat_indices[0])
        old_skill = self.skills_listbox.get(selected_skill_indices[0])
        
        # Neuen Namen abfragen
        new_skill = simpledialog.askstring("Fähigkeit umbenennen", 
                                         f"Neuer Name für '{old_skill}':", parent=self)
        
        if new_skill:
            # Doppelte Einträge vermeiden
            new_skill = new_skill.strip().lower()
            
            if not new_skill:
                messagebox.showwarning("Warnung", "Der Name der Fähigkeit darf nicht leer sein.")
                return
            
            if new_skill in self.available_skills[category]:
                messagebox.showwarning("Warnung", f"Die Fähigkeit '{new_skill}' existiert bereits in dieser Kategorie.")
                return
            
            # Skill umbenennen
            index = self.available_skills[category].index(old_skill)
            self.available_skills[category][index] = new_skill
            
            # Skills neu laden
            self.load_skills(category)
            
            # Neuen Skill selektieren
            for i in range(self.skills_listbox.size()):
                if self.skills_listbox.get(i) == new_skill:
                    self.skills_listbox.selection_set(i)
                    break
    
    def delete_skill(self):
        """Löscht eine Fähigkeit"""
        selected_cat_indices = self.categories_listbox.curselection()
        selected_skill_indices = self.skills_listbox.curselection()
        
        if not selected_cat_indices or not selected_skill_indices:
            messagebox.showinfo("Hinweis", "Bitte wählen Sie eine Kategorie und eine Fähigkeit zum Löschen aus.")
            return
        
        category = self.categories_listbox.get(selected_cat_indices[0])
        skill = self.skills_listbox.get(selected_skill_indices[0])
        
        # Bestätigung einholen
        if messagebox.askyesno("Fähigkeit löschen", 
                             f"Möchten Sie die Fähigkeit '{skill}' wirklich löschen?",
                             detail="Hinweis: Das Löschen einer Fähigkeit wirkt sich nur auf zukünftige Mitarbeiter und Aufgaben aus. Bestehende Zuordnungen bleiben unverändert."):
            # Skill löschen
            self.available_skills[category].remove(skill)
            
            # Skills neu laden
            self.load_skills(category)
    
    def save_changes(self):
        """Speichert die Änderungen und schließt den Dialog"""
        # Callback aufrufen, wenn vorhanden
        if self.on_update:
            self.on_update(self.available_skills)
        
        messagebox.showinfo("Erfolg", "Die Fähigkeiten wurden erfolgreich gespeichert.")
        self.destroy()
    
    def on_close(self):
        """Schließt den Dialog ohne zu speichern"""
        if messagebox.askyesno("Schließen", 
                             "Möchten Sie den Dialog wirklich schließen? Alle nicht gespeicherten Änderungen gehen verloren."):
            self.destroy()