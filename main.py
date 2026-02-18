import logging
import os
from flask import Flask, request
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import config
import database as db

# === Flask для health checks ===
flask_app = Flask(__name__)

@flask_app.route('/')
def hello():
    return "Bot is running! ✅"

@flask_app.route('/health')
def health():
    return "OK", 200

@flask_app.route('/webhook', methods=['POST'])
async def webhook_handler():
    # Для webhook через Flask (упрощённо)
    return "OK", 200

# === Настройка бота ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# === Хендлеры ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Открыть каталог", web_app=WebAppInfo(url=config.WEBAPP_URL))
    builder.button(text="ℹ️ О проекте", callback_data="about")
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Здесь собраны лучшие промокоды и скидки. "
        "Нажми кнопку ниже, чтобы открыть каталог 👇",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "about")
async def show_about(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "📱 <b>Promo Catalog Bot</b>\n\n"
        "• Удобный поиск по категориям\n"
        "• Только проверенные коды\n"
        "• Ежедневные обновления\n\n"
        "<i>Активируйте коды на сайтах партнёров</i>",
        parse_mode="HTML"
    )

@dp.message(Command("add_cat"))
async def admin_add_cat(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.reply(f"❌ Доступ запрещён. Ваш ID: {message.from_user.id}")
        return
    try:
        parts = message.text.split(maxsplit=2)
        name = parts[1]
        emoji = parts[2] if len(parts) > 2 else "📦"
        db.add_category(name, emoji)
        await message.reply(f"✅ Категория '{name}' создана")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("add_offer"))
async def admin_add_offer(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.reply(f"❌ Доступ запрещён. Ваш ID: {message.from_user.id}")
        return
    try:
        parts = message.text.split(maxsplit=1)[1].split("|")
        cat_id = int(parts[0])
        brand = parts[1]
        desc = parts[2] if len(parts) > 2 else ""
        db.add_offer(cat_id, brand, desc)
        await message.reply(f"✅ Бренд '{brand}' добавлен")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("add_code"))
async def admin_add_code(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.reply(f"❌ Доступ запрещён. Ваш ID: {message.from_user.id}")
        return
    try:
        parts = message.text.split(maxsplit=1)[1].split("|")
        offer_id = int(parts[0])
        code = parts[1]
        bonus = parts[2] if len(parts) > 2 else ""
        expires = parts[3] if len(parts) > 3 else None
        db.add_promo_code(offer_id, code, bonus, expires)
        await message.reply(f"✅ Промокод добавлен")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# === Запуск с webhook ===
async def on_startup(bot: Bot):
    webhook_url = f"{config.WEBAPP_URL.replace('github.io', 'onrender.com')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook установлен на {webhook_url}")

async def main():
    db.init_db()
    logger.info("База данных инициализирована")
    
    # Запускаем Flask
    from threading import Thread
    flask_thread = Thread(target=lambda: flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))), daemon=True)
    flask_thread.start()
    logger.info(f"Flask запущен на порту {os.environ.get('PORT', 8080)}")
    
    # Настройка webhook
    await on_startup(bot)
    
    # Создаём aiohttp приложение для webhook
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 8080)))
    await site.start()
    
    logger.info("Бот запущен в режиме webhook!")
    
    # Держим приложение запущенным
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
