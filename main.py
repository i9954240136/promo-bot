# === ИМПОРТЫ ===
import logging
import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import config
import database as db

# === Настройка логирования ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === Инициализация бота ===
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# === Хендлеры ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Открыть каталог", web_app=WebAppInfo(url=config.WEBAPP_URL))
    builder.button(text="ℹ️ О проекте", callback_data="about")
    
    await message.answer(
        f"👋 Привет! Бот работает!\n\nНажми кнопку ниже 👇",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "about")
async def show_about(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("📱 Promo Bot работает!")

@dp.message(Command("add_cat"))
async def admin_add_cat(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.reply(f"❌ Ваш ID: {message.from_user.id}")
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

# === Запуск ===
async def on_startup(bot: Bot):
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'promo-bot-ex86.onrender.com')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook: {webhook_url}")

async def main():
    db.init_db()
    logger.info("✅ БД готова")
    
    # Создаём основное приложение для бота
    bot_app = web.Application()
    
    await on_startup(bot)
    
    # Регистрируем webhook handler
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(bot_app, path="/webhook")
    setup_application(bot_app, dp, bot=bot)
    
    runner = web.AppRunner(bot_app)
    await runner.setup()
    
    # Основной порт для бота
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🚀 Бот запущен на порту {port}")
    
    # === ОТДЕЛЬНЫЙ СЕРВЕР ДЛЯ HEALTH CHECK ===
    async def handle_health(request):
        return web.json_response({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "promo-bot"
        })
    
    health_app = web.Application()
    health_app.router.add_get('/health', handle_health)
    health_app.router.add_get('/ping', handle_health)
    health_app.router.add_get('/', handle_health)
    
    health_runner = web.AppRunner(health_app)
    await health_runner.setup()
    
    # Health check на порту +1 (10001)
    health_port = port + 1
    health_site = web.TCPSite(health_runner, '0.0.0.0', health_port)
    await health_site.start()
    
    logger.info(f"✅ Health check на порту {health_port}")
    logger.info(f"✅ URL: http://0.0.0.0:{health_port}/health")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
