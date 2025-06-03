# Yuksalish School Bot

## Features
- Daily reminders via Celery
- Redis-backed task queue
- Telegram integration

## Setup
```bash
pip install -r requirements.txt
celery -A schoolbot worker -P eventlet
celery -A schoolbot beat