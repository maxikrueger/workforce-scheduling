-- Skills Tabelle
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Employees Tabelle
CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin', 'manager', 'employee')),
    status TEXT CHECK(status IN ('available', 'busy', 'off')),    
    max_weekly_hours INTEGER DEFAULT 40,
    min_daily_hours INTEGER DEFAULT 4,
    max_daily_hours INTEGER DEFAULT 10
);

-- Employee Skills Tabelle
CREATE TABLE IF NOT EXISTS employee_skills (
    employee_id TEXT,
    skill_id TEXT,
    is_preferred BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (employee_id, skill_id)
);

-- Employee Availability Tabelle
CREATE TABLE IF NOT EXISTS employee_availability (
    employee_id TEXT,
    day_of_week INTEGER CHECK(day_of_week BETWEEN 0 AND 6),
    start_time TEXT,
    end_time TEXT,
    is_preferred BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    PRIMARY KEY (employee_id, day_of_week, start_time, end_time)
);

-- Tasks Tabelle
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    duration INTEGER NOT NULL,  -- in minutes
    deadline TEXT,
    status TEXT CHECK(status IN ('open', 'in_progress', 'completed', 'cancelled', 'blocked')),
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')),
    notes TEXT
);

-- Task Required Skills Tabelle
CREATE TABLE IF NOT EXISTS task_required_skills (
    task_id TEXT,
    skill_id TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, skill_id)
);

-- Task Dependencies Tabelle
CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id TEXT,
    dependent_task_id TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (dependent_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, dependent_task_id)
);

-- Schedules Tabelle (überarbeitet)
CREATE TABLE IF NOT EXISTS schedules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Schedule Employees Tabelle (neu)
CREATE TABLE IF NOT EXISTS schedule_employees (
    id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    status TEXT, 
    max_daily_hours INTEGER,
    min_daily_hours INTEGER,
    notes TEXT,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE (schedule_id, employee_id)
);

-- Schedule Tasks Tabelle 
CREATE TABLE IF NOT EXISTS schedule_tasks (
    id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')),
    deadline TEXT,
    status, 
    notes TEXT,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE (schedule_id, task_id)
);

-- Feedback Tabelle für Schedules
CREATE TABLE IF NOT EXISTS schedule_item_feedback (
    id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    task_id TEXT NOT NULL,      -- Bezieht sich auf eine konkrete Aufgabenzuweisung
    rating INTEGER CHECK(rating IN (-1, 0)),  -- -1 = "Lieber nicht", 0 = "Find ich gut"
    comment TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    iteration INTEGER DEFAULT 1, -- Speichert die Iteration des Schedules
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    UNIQUE (schedule_id, employee_id, task_id, iteration)
);


-- TimeSlots Tabelle 
CREATE TABLE IF NOT EXISTS timeslots (
    id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE
);

-- Assignments Tabelle (überarbeitet)
CREATE TABLE IF NOT EXISTS assignments (
    id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    timeslot_id TEXT NOT NULL,
    status TEXT CHECK(status IN ('planned', 'confirmed', 'in_progress', 'completed', 'cancelled')) DEFAULT 'planned',
    actual_start_time TEXT,
    actual_end_time TEXT,
    notes TEXT,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (timeslot_id) REFERENCES timeslots(id) ON DELETE CASCADE
);

-- Assignment Breaks Tabelle
CREATE TABLE IF NOT EXISTS assignment_breaks (
    assignment_id TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    PRIMARY KEY (assignment_id, start_time, end_time)
);

-- Employee Vacations Tabelle (neu)
CREATE TABLE IF NOT EXISTS employee_vacations (
    id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    type TEXT CHECK(type IN ('vacation', 'sick_leave', 'personal', 'other')) DEFAULT 'vacation',
    notes TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Indices für häufige Abfragen
CREATE INDEX IF NOT EXISTS idx_employee_skills ON employee_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_task_skills ON task_required_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_timeslots_schedule ON timeslots(schedule_id);
CREATE INDEX IF NOT EXISTS idx_assignments_schedule ON assignments(schedule_id);
CREATE INDEX IF NOT EXISTS idx_assignments_employee ON assignments(employee_id);
CREATE INDEX IF NOT EXISTS idx_assignments_task ON assignments(task_id);
CREATE INDEX IF NOT EXISTS idx_assignments_timeslot ON assignments(timeslot_id);
CREATE INDEX IF NOT EXISTS idx_schedule_employees ON schedule_employees(schedule_id, employee_id);
CREATE INDEX IF NOT EXISTS idx_schedule_tasks ON schedule_tasks(schedule_id, task_id);
CREATE INDEX IF NOT EXISTS idx_employee_vacations ON employee_vacations(employee_id);
CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status);
CREATE INDEX IF NOT EXISTS idx_schedules_dates ON schedules(start_date, end_date);