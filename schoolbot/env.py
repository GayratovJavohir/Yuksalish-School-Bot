import os
from dotenv import load_dotenv

# .env faylni yuklaydi
load_dotenv()

# .env dagi qiymatlarni o'qib oladi
DJANGO_SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
