from datetime import date
import sqlite3

import pandas as pd
import streamlit as st

import db

st.set_page_config(page_title="Планувальник навчання", layout="wide")
db.init_db()
st.sidebar.title("Навчальний план")
page = st.sidebar.radio("Сторінка", ["Завдання", "Предмети", "Про автора"])
st.sidebar.caption("Мазур Олександр · Варіант 13")
st.sidebar.caption(
    "Демонстраційна SQLite-база спільна для відвідувачів. "
    "Після перезапуску хмари зміни можуть скинутися."
)


def submit_action(action, *args, **kwargs):
    try:
        action(*args, **kwargs)
        st.session_state.notice = "Зміни збережено."
        st.rerun()
    except (ValueError, sqlite3.Error) as error:
        st.error(str(error))


if "notice" in st.session_state:
    st.success(st.session_state.pop("notice"))

if page == "Завдання":
    st.title("Планувальник навчання")
    st.write("Плануйте навчальні завдання, відстежуйте дедлайни та прогрес.")
    rows = db.tasks()
    total = len(rows)
    finished = sum(row["done"] for row in rows)
    overdue = sum(
        not row["done"] and row["due_date"] < date.today().isoformat()
        for row in rows
    )
    columns = st.columns(3)
    columns[0].metric("Усього завдань", total)
    columns[1].metric("Виконано", finished)
    columns[2].metric("Прострочено", overdue)
    listing, adding, editing = st.tabs(["Список", "Додати", "Редагувати"])
    options = {row["id"]: row["name"] for row in db.subjects()}

    with listing:
        left, middle, right = st.columns([2, 1, 1])
        query = left.text_input("Пошук у назві")
        subject_filter = middle.selectbox(
            "Предмет", [None, *options], format_func=lambda item: options.get(item, "Усі")
        )
        state_filter = right.selectbox("Статус", ["Усі", "До виконання", "Виконані"])
        filtered = [
            row for row in rows
            if query.strip().casefold() in row["title"].casefold()
            and (subject_filter is None or row["subject_id"] == subject_filter)
            and (state_filter == "Усі" or bool(row["done"]) == (state_filter == "Виконані"))
        ]
        st.caption(f"Знайдено завдань — {len(filtered)}")
        if filtered:
            frame = pd.DataFrame(filtered).rename(columns={
                "id": "ID", "subject": "Предмет", "title": "Завдання",
                "due_date": "Термін", "priority": "Пріоритет", "done": "Виконано",
            }).drop(columns=["subject_id"])
            frame["Виконано"] = frame["Виконано"].astype(bool)
            st.dataframe(frame, hide_index=True, width="stretch")
            st.bar_chart(frame.groupby("Предмет").size().rename("Завдань"))
        else:
            st.info("За цими умовами завдань не знайдено.")

    with adding:
        if options:
            with st.form("add_task", clear_on_submit=True):
                subject_id = st.selectbox("Предмет завдання", list(options), format_func=options.get)
                title = st.text_input("Назва завдання", max_chars=120)
                due = st.date_input("Термін виконання", value=date.today())
                priority = st.selectbox("Пріоритет", db.PRIORITIES, index=1)
                if st.form_submit_button("Додати завдання"):
                    submit_action(db.save_task, subject_id, title, due, priority)
        else:
            st.info("Спочатку додайте предмет на сторінці «Предмети».")

    with editing:
        task_options = {row["id"]: row for row in rows}
        if task_options and options:
            chosen = st.selectbox(
                "Оберіть завдання", list(task_options),
                format_func=lambda key: f"{key} · {task_options[key]['title']}",
            )
            current = task_options[chosen]
            with st.form(f"edit_task_{chosen}"):
                edit_title = st.text_input("Нова назва", value=current["title"], max_chars=120)
                subject_ids = list(options)
                edit_subject = st.selectbox(
                    "Змінити предмет", subject_ids,
                    index=subject_ids.index(current["subject_id"]), format_func=options.get,
                )
                edit_due = st.date_input("Новий термін", value=date.fromisoformat(current["due_date"]))
                edit_priority = st.selectbox(
                    "Новий пріоритет", db.PRIORITIES,
                    index=db.PRIORITIES.index(current["priority"]),
                )
                done = st.checkbox("Виконано", value=bool(current["done"]))
                if st.form_submit_button("Зберегти завдання"):
                    submit_action(
                        db.save_task, edit_subject, edit_title, edit_due,
                        edit_priority, done=done, task_id=chosen,
                    )
            confirm = st.checkbox("Підтверджую видалення завдання")
            if st.button("Видалити завдання", disabled=not confirm):
                submit_action(db.delete_task, chosen)
        else:
            st.info("Завдань для редагування ще немає.")

elif page == "Предмети":
    st.title("Навчальні предмети")
    rows = db.subjects()
    if rows:
        st.dataframe(
            pd.DataFrame(rows).rename(columns={"id": "ID", "name": "Предмет"}),
            hide_index=True, width="stretch",
        )
    with st.form("add_subject", clear_on_submit=True):
        name = st.text_input("Назва предмета", max_chars=60)
        if st.form_submit_button("Додати предмет"):
            submit_action(db.save_subject, name)
    options = {row["id"]: row["name"] for row in rows}
    if options:
        chosen = st.selectbox("Оберіть предмет", list(options), format_func=options.get)
        with st.form(f"edit_subject_{chosen}"):
            new_name = st.text_input("Нова назва предмета", value=options[chosen], max_chars=60)
            if st.form_submit_button("Зберегти предмет"):
                submit_action(db.save_subject, new_name, subject_id=chosen)
        confirm = st.checkbox("Підтверджую видалення предмета")
        if st.button("Видалити предмет", disabled=not confirm):
            submit_action(db.delete_subject, chosen)

else:
    st.title("Про автора")
    st.write("**Мазур Олександр**")
    st.write("Дисципліна — Інформаційні технології")
    st.write("Лабораторна робота №6 · Варіант 13")
    st.write(
        "Планувальник допомагає студенту організувати завдання з різних предметів, "
        "контролювати терміни та відмічати виконання."
    )
    st.write(
        "Створено три сторінки та дві пов’язані таблиці SQLite — subjects і tasks. "
        "Структуру бази даних можна відтворити файлом schema.sql."
    )
