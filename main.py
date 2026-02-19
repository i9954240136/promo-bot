import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import config
import database as db

# === Настройка логирования ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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

# === Health check endpoint ===
async def health_handler(request):
    return web.json_response({
        "status": "ok", 
        "message": "Bot is running! ✅",
        "service": "promo-bot"
    })

# === Запуск ===
async def on_startup(bot: Bot):
    # Формируем правильный webhook URL из WEBAPP_URL
    webapp_url = os.environ.get('WEBAPP_URL', '')
    
    # Если WEBAPP_URL содержит github.io, заменяем на onrender.com
    if 'github.io' in webapp_url:
        # Извлекаем имя пользователя и репозиторий
        parts = webapp_url.rstrip('/').split('/')
        if len(parts) >= 2:
            username = parts[-2] if 'github.io' in parts[-2] else parts[-1]
            repo = parts[-1] if 'github.io' not in parts[-1] else 'promo-bot'
            webhook_base = f"https://{username.replace('.github.io', '')}-{'promo-bot'}.onrender.com"
        else:
            webhook_base = "https://promo-bot-ex86.onrender.com"
    else:
        # Используем напрямую, если уже есть Render URL
        webhook_base = os.environ.get('SERVICE_URL', 'https://promo-bot-ex86.onrender.com')
    
    webhook_url = f"{webhook_base}/webhook"
    
    try:
        await bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook установлен на {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")

async def main():
    try:
        # Инициализация БД
        logger.info("🔄 Инициализация базы данных...")
        db.init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise
    
    # Создаём aiohttp приложение
    app = web.Application()
    
    # Добавляем health check endpoints
    app.router.add_get('/', health_handler)
    app.router.add_get('/health', health_handler)
    
    # Настраиваем webhook
    await on_startup(bot)
    
    # Регистрируем webhook handler от aiogram
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Получаем порт от Render
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Запуск сервера на порту {port}...")
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"✅ Бот запущен в режиме webhook!")
    logger.info(f"📍 Health check: http://0.0.0.0:{port}/health")
    logger.info(f"📍 Webhook: http://0.0.0.0:{port}/webhook")
    
    # Держим приложение запущенным
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("🛑 Бот остановлен")

if __name__ == "__main__":
    logger.info("🎬 Запуск promo-bot...")
    asyncio.run(main())
