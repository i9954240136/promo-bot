import os
from dotenv import load_dotenv

load_dotenv()

# 🔐 ВСТАВЬТЕ СЮДА ВАШ НОВЫЙ ТОКЕН (в кавычках)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8544537463:AAFs2rNEHBNoYiJS45yulmhSXkMF0DYjewI")

# Ссылка на веб-приложение (замените после Шага 3)
# Пока оставьте заглушку, мы вернемся к этому позже
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://google.com") 

# Ваш Telegram ID для доступа к админке (узнайте у @userinfobot)
ADMIN_ID = 123456789  

# База данных

DATABASE_NAME = "promo.db"

# Для Render
import os
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://google.com")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
