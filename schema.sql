CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE CHECK(length(trim(name)) BETWEEN 2 AND 60)
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
    title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 2 AND 120),
    due_date TEXT NOT NULL,
    priority TEXT NOT NULL CHECK(priority IN ('Низький','Середній','Високий')),
    done INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0,1))
);
