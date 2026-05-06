import os
import sqlite3
from datetime import datetime
from pathlib import Path

import json
import urllib.error
import urllib.request
from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "instance" / "school.db"


SUBJECTS = [
    {"title": "Математика", "age": "6–18 лет", "format": "индивидуально / мини-группы", "goal": "школьная база, контрольные, ОГЭ и ЕГЭ"},
    {"title": "Русский язык", "age": "7–18 лет", "format": "онлайн-занятия", "goal": "грамотность, сочинения, экзамены"},
    {"title": "Английский язык", "age": "6–18 лет", "format": "разговорная практика", "goal": "школьная программа и уверенная коммуникация"},
    {"title": "Физика", "age": "10–18 лет", "format": "разбор задач", "goal": "понимание законов, ОГЭ/ЕГЭ"},
    {"title": "Химия", "age": "12–18 лет", "format": "теория + практика", "goal": "систематизация тем и подготовка к экзаменам"},
    {"title": "Биология", "age": "10–18 лет", "format": "визуальные конспекты", "goal": "закрытие пробелов и экзамены"},
    {"title": "История", "age": "10–18 лет", "format": "карты, даты, причинно-следственные связи", "goal": "контрольные, ОГЭ/ЕГЭ"},
    {"title": "Обществознание", "age": "13–18 лет", "format": "кейсы и практика заданий", "goal": "подготовка к ОГЭ/ЕГЭ"},
    {"title": "Информатика", "age": "10–18 лет", "format": "практика за компьютером", "goal": "алгоритмы, Python, экзамены"},
]

AGE_TRACKS = [
    {"range": "6–9 лет", "title": "Мягкая адаптация и база", "text": "Помогаем привыкнуть к учебному ритму, развиваем интерес к предметам и закрепляем фундаментальные навыки."},
    {"range": "10–14 лет", "title": "Школьная программа без пробелов", "text": "Разбираем сложные темы, готовим к контрольным и формируем устойчивую привычку учиться."},
    {"range": "15–18 лет", "title": "Экзамены и поступление", "text": "Строим индивидуальную траекторию подготовки к ОГЭ/ЕГЭ, профориентации и выбору дальнейшего пути."},
]

FORMATS = [
    "Индивидуальные занятия с персональным планом",
    "Мини-группы для совместной практики",
    "Подготовка к контрольным и самостоятельным работам",
    "Сопровождение по школьной программе",
    "Интенсивы перед экзаменами и важными темами",
]

TARIFFS = [
    {"name": "Пробное занятие", "lessons": "1 встреча", "details": "диагностика уровня, цели и рекомендации по плану"},
    {"name": "Старт", "lessons": "4 занятия", "details": "быстро закрыть конкретную тему или подготовиться к контрольной"},
    {"name": "Прогресс", "lessons": "8 занятий", "details": "системная работа по предмету и регулярная обратная связь"},
    {"name": "Экзамены", "lessons": "индивидуальный план", "details": "ОГЭ/ЕГЭ, пробники, стратегия выполнения заданий"},
]

FAQ = [
    {"question": "Как проходит занятие?", "answer": "Урок проводится онлайн: преподаватель объясняет тему, разбирает задания и фиксирует домашнюю практику."},
    {"question": "Что нужно для обучения?", "answer": "Нужны стабильный интернет, компьютер или планшет, тетрадь и готовность задавать вопросы."},
    {"question": "Можно ли перенести урок?", "answer": "Да, перенос согласуется заранее с администратором и преподавателем."},
    {"question": "Как записаться?", "answer": "Оставьте заявку на сайте или напишите в Telegram — администратор уточнит предмет, возраст и удобное время."},
    {"question": "Как работает связь через Telegram?", "answer": "Telegram используется для быстрой коммуникации, подтверждения заявок и уведомлений о занятиях."},
]


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["DATABASE"] = str(DATABASE)

    @app.before_request
    def before_request():
        g.db = get_db(app.config["DATABASE"])

    @app.teardown_request
    def teardown_request(exception=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            subjects=SUBJECTS,
            age_tracks=AGE_TRACKS,
            formats=FORMATS,
            tariffs=TARIFFS,
            faq=FAQ[:4],
        )

    @app.route("/about")
    def about():
        return render_template("about.html", age_tracks=AGE_TRACKS)

    @app.route("/subjects")
    def subjects():
        return render_template("subjects.html", subjects=SUBJECTS)

    @app.route("/formats")
    def formats():
        return render_template("formats.html", formats=FORMATS, tariffs=TARIFFS)

    @app.route("/faq")
    def faq():
        return render_template("faq.html", faq=FAQ)

    @app.route("/privacy")
    def privacy():
        return render_template("privacy.html")

    @app.route("/apply", methods=["POST"])
    def apply():
        data = {
            "parent_name": request.form.get("parent_name", "").strip(),
            "contact": request.form.get("contact", "").strip(),
            "child_age": request.form.get("child_age", "").strip(),
            "subject": request.form.get("subject", "").strip(),
            "goal": request.form.get("goal", "").strip(),
        }

        missing = [key for key in ("parent_name", "contact", "child_age") if not data[key]]
        if missing:
            flash("Пожалуйста, заполните имя, контакт и возраст ребёнка.", "error")
            return redirect(url_for("index", _anchor="signup"))

        save_application(g.db, data)
        send_telegram_notification(data)
        flash("Заявка принята! Администратор свяжется с вами в Telegram или по указанному контакту.", "success")
        return redirect(url_for("index", _anchor="signup"))

    return app


def get_db(database_path):
    Path(database_path).parent.mkdir(exist_ok=True)
    db = sqlite3.connect(database_path)
    db.row_factory = sqlite3.Row
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_name TEXT NOT NULL,
            contact TEXT NOT NULL,
            child_age TEXT NOT NULL,
            subject TEXT,
            goal TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    return db


def save_application(db, data):
    db.execute(
        """
        INSERT INTO applications (parent_name, contact, child_age, subject, goal, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data["parent_name"],
            data["contact"],
            data["child_age"],
            data["subject"],
            data["goal"],
            datetime.utcnow().isoformat(timespec="seconds"),
        ),
    )
    db.commit()


def send_telegram_notification(data):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    message = (
        "Новая заявка онлайн-школы «Самый умный»\n"
        f"Имя: {data['parent_name']}\n"
        f"Контакт: {data['contact']}\n"
        f"Возраст ребёнка: {data['child_age']}\n"
        f"Предмет: {data['subject'] or 'не указан'}\n"
        f"Цель: {data['goal'] or 'не указана'}"
    )
    payload = json.dumps({"chat_id": chat_id, "text": message}).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5):
            pass
    except urllib.error.URLError:
        # Заявка уже сохранена в базе; временная ошибка Telegram не должна мешать пользователю.
        pass


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
