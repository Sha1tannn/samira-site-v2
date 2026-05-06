# Онлайн-школа «Самый умный»

Flask-приложение для дипломного проекта онлайн-школы: сайт представляет образовательные услуги, собирает заявки на обучение, сохраняет их в SQLite и при наличии настроек отправляет уведомление администратору через Telegram Bot API.

## Стек

- Frontend: HTML5, CSS3, JavaScript
- Backend: Python, Flask
- Database: SQLite
- Communication: Telegram Bot API
- Infrastructure-ready: Ubuntu Server, Docker, Nginx и Asterisk описываются как перспектива развития комплекса

## Запуск локально

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run
```

Сайт будет доступен по адресу `http://127.0.0.1:5000`.

## Telegram-интеграция

Для отправки заявок в Telegram задайте переменные окружения:

```bash
export TELEGRAM_BOT_TOKEN="token"
export TELEGRAM_CHAT_ID="chat_id"
```

Если переменные не заданы, заявки всё равно сохраняются в SQLite, а Telegram-уведомление пропускается.

## Страницы

- Главная
- О школе
- Предметы
- Форматы обучения и абонементы
- FAQ
- Политика обработки данных

## Docker

```bash
docker compose up --build
```

Пример `nginx.conf.example` показывает схему reverse proxy для Flask-приложения.
