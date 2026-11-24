from contextlib import contextmanager
from datetime import date, timedelta
import os
from pathlib import Path
import sqlite3

DB_PATH = Path(os.getenv(
    "STUDY_PLANNER_DB", Path(__file__).with_name("planner.db")
))
PRIORITIES = ("Низький", "Середній", "Високий")


@contextmanager
def connection():
    database = sqlite3.connect(DB_PATH, timeout=15)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    try:
        with database:
            yield database
    finally:
        database.close()


def init_db():
    schema = Path(__file__).with_name("schema.sql").read_text(
        encoding="utf-8"
    )
    with connection() as database:
        database.executescript(schema)
        database.execute("BEGIN IMMEDIATE")
        version = database.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            names = ["Інформаційні технології", "Python", "Англійська мова"]
            database.executemany(
                "INSERT INTO subjects(name) VALUES (?)",
                [(name,) for name in names],
            )
            ids = {
                row["name"]: row["id"] for row in database.execute(
                    "SELECT id, name FROM subjects"
                )
            }
            today = date.today()
            demo = [
                (names[0], "Підготувати лабораторну роботу №6", 2, "Високий", 0),
                (names[0], "Перевірити публікацію Streamlit", 3, "Середній", 0),
                (names[0], "Повторити REST API", -2, "Середній", 1),
                (names[1], "Розв’язати задачі зі списками", -1, "Високий", 0),
                (names[1], "Повторити роботу з файлами", 4, "Низький", 0),
                (names[1], "Практика SQL-запитів", 5, "Середній", 0),
                (names[2], "Вивчити 20 нових слів", 1, "Середній", 0),
                (names[2], "Прочитати текст про технології", -3, "Низький", 1),
            ]
            database.executemany(
                """INSERT INTO tasks
                (subject_id, title, due_date, priority, done)
                VALUES (?, ?, ?, ?, ?)""",
                [
                    (ids[name], title, (today + timedelta(days=days)).isoformat(),
                     priority, done)
                    for name, title, days, priority, done in demo
                ],
            )
            database.execute("PRAGMA user_version = 1")


def subjects():
    with connection() as database:
        return [dict(row) for row in database.execute(
            "SELECT id, name FROM subjects ORDER BY name"
        )]


def tasks():
    with connection() as database:
        return [dict(row) for row in database.execute(
            """SELECT t.id, t.subject_id, s.name AS subject, t.title,
            t.due_date, t.priority, t.done
            FROM tasks t JOIN subjects s ON s.id = t.subject_id
            ORDER BY t.done, t.due_date, t.id"""
        )]


def save_subject(name, subject_id=None):
    name = name.strip()
    if not 2 <= len(name) <= 60:
        raise ValueError("Назва предмета має містити від 2 до 60 символів.")
    try:
        with connection() as database:
            if subject_id is None:
                database.execute("INSERT INTO subjects(name) VALUES (?)", (name,))
            else:
                cursor = database.execute(
                    "UPDATE subjects SET name = ? WHERE id = ?", (name, subject_id)
                )
                if not cursor.rowcount:
                    raise ValueError("Предмет уже видалено. Оновіть сторінку.")
    except sqlite3.IntegrityError:
        raise ValueError("Предмет із такою назвою вже існує.") from None


def delete_subject(subject_id):
    try:
        with connection() as database:
            cursor = database.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
            if not cursor.rowcount:
                raise ValueError("Предмет уже видалено.")
    except sqlite3.IntegrityError:
        raise ValueError("Спочатку видаліть або перенесіть завдання цього предмета.") from None


def save_task(subject_id, title, due_date, priority, done=False, task_id=None):
    title = title.strip()
    if not 2 <= len(title) <= 120:
        raise ValueError("Назва завдання має містити від 2 до 120 символів.")
    due_date = date.fromisoformat(str(due_date)).isoformat()
    if priority not in PRIORITIES:
        raise ValueError("Невідомий пріоритет.")
    values = (subject_id, title, due_date, priority, int(bool(done)))
    try:
        with connection() as database:
            if task_id is None:
                database.execute(
                    """INSERT INTO tasks
                    (subject_id, title, due_date, priority, done) VALUES (?, ?, ?, ?, ?)""",
                    values,
                )
            else:
                cursor = database.execute(
                    """UPDATE tasks SET subject_id=?, title=?, due_date=?,
                    priority=?, done=? WHERE id=?""", (*values, task_id)
                )
                if not cursor.rowcount:
                    raise ValueError("Завдання вже видалено. Оновіть сторінку.")
    except sqlite3.IntegrityError:
        raise ValueError("Вибраний предмет уже видалено. Оновіть сторінку.") from None


def delete_task(task_id):
    with connection() as database:
        cursor = database.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if not cursor.rowcount:
            raise ValueError("Завдання вже видалено.")
