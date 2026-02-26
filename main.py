# === ИМПОРТЫ ===
import logging
import os
import asyncio
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import config
import database as db

# === Глобальные переменные ===
broadcast_message = None

# === Настройка логирования ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === Инициализация бота ===
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# === Хендлеры ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработка команды /start - сохраняет пользователя в базу"""
    try:
        db.add_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code
        )
        logger.info(f"✅ Новый пользователь: {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 Открыть каталог", web_app=WebAppInfo(url=config.WEBAPP_URL))
    builder.button(text="📞 Связь с автором", callback_data="contact_author")
    builder.adjust(1)  # Кнопки в 1 столбец
    
    await message.answer(
        "👋 Привет! Добро пожаловать в <b>Promo Bot</b>!\n\n"
        "🎁 Здесь вы найдёте лучшие промокоды и скидки от популярных брендов!\n\n"
        "📖 Нажмите «Открыть каталог», чтобы начать!",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"  # ← ВКЛЮЧАЕМ HTML-РАЗМЕТКУ
    )

@dp.callback_query(F.data == "contact_author")
async def contact_author(callback: types.CallbackQuery):
    """Обработка кнопки 'Связь с автором'"""
    # Сначала закрываем callback (без текста)
    await callback.answer()
    
    # Отправляем отдельное сообщение с контактом
    await callback.message.answer(
        "📬 Написать автору можно в личный Telegram:\n\n"
        "👤 @chevengur92\n\n"
        "✉️ Я всегда отвечаю в течение 24 часов!"
    )

@dp.message(Command("add_cat"))
async def admin_add_cat(message: types.Message):
    """Добавление категории (только для админа)"""
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
    """Добавление бренда (только для админа)"""
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
    """Добавление промокода (только для админа)"""
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

@dp.message(Command("stats"))
async def admin_stats(message: types.Message):
    """Показывает статистику пользователей (только для админа)"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    try:
        total_users = db.get_total_users()
        active_users = db.get_active_users(days=7)
        new_users = db.get_new_users(days=1)
        
        await message.reply(
            f"📊 **Статистика бота**\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"🟢 Активных за 7 дней: {active_users}\n"
            f"🆕 Новых за 24 часа: {new_users}\n\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# =====================================================
# 📢 РАССЫЛКА ПОЛЬЗОВАТЕЛЯМ
# =====================================================

@dp.message(Command("broadcast"))
async def admin_broadcast(message: types.Message):
    """
    Начало рассылки (только для админа)
    Использование: /broadcast Текст сообщения
    """
    if message.from_user.id != config.ADMIN_ID:
        await message.reply("❌ Доступ запрещён")
        return
    
    # Получаем текст сообщения после команды
    text = message.text.replace("/broadcast", "").strip()
    
    if not text:
        await message.reply(
            "❌ Введите текст рассылки!\n\n"
            "Пример: /broadcast 🎁 Новые промокоды уже в боте!"
        )
        return
    
    # Отправляем сообщение на подтверждение
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить", callback_data="broadcast_confirm")
    builder.button(text="❌ Отмена", callback_data="broadcast_cancel")
    builder.adjust(2)
    
    # Сохраняем текст в состоянии (через Redis или в памяти)
    # Для простоты используем глобальную переменную
    global broadcast_message
    broadcast_message = text
    
    await message.reply(
        f"📢 **Подтверждение рассылки**\n\n"
        f"📝 Текст:\n{text}\n\n"
        f"👥 Получателей: ~{db.get_total_users()}\n\n"
        f"Отправить?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "broadcast_confirm")
async def broadcast_confirm(callback: types.CallbackQuery):
    """Подтверждение и отправка рассылки"""
    global broadcast_message
    
    if not broadcast_message:
        await callback.answer("❌ Сообщение не найдено", show_alert=True)
        return
    
    await callback.answer("🚀 Начинаю рассылку...")
    await callback.message.edit_text("🚀 **Рассылка началась...**\n\nПодождите, это может занять несколько минут.")
    
    # Получаем всех пользователей
    users = db.get_all_users()  # Нужно добавить эту функцию в database.py
    
    total = len(users)
    sent = 0
    failed = 0
    
    # Отправляем каждому пользователю
    for user in users:
        try:
            await bot.send_message(
                chat_id=user['user_id'],
                text=broadcast_message,
                parse_mode="HTML"
            )
            sent += 1
            await asyncio.sleep(0.1)  # Пауза чтобы не заблокировали
        except Exception as e:
            failed += 1
            logger.error(f"❌ Не удалось отправить {user['user_id']}: {e}")
    
    # Сохраняем в базу
    db.add_broadcast(
        message=broadcast_message,
        sent_by=callback.from_user.id,
        total_sent=sent,
        total_failed=failed
    )
    
    await callback.message.edit_text(
        f"✅ **Рассылка завершена!**\n\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}\n"
        f"👥 Всего: {total}"
    )
    
    broadcast_message = None

@dp.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: types.CallbackQuery):
    """Отмена рассылки"""
    global broadcast_message
    broadcast_message = None
    await callback.answer("❌ Рассылка отменена", show_alert=True)
    await callback.message.delete()

@dp.message(Command("broadcast_stats"))
async def broadcast_stats(message: types.Message):
    """Статистика рассылок (только для админа)"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    try:
        stats = db.get_broadcast_stats()
        
        text = "📊 **Статистика рассылок**\n\n"
        for broadcast in stats[:10]:  # Последние 10
            text += f"📅 {broadcast['sent_at'][:10]}\n"
            text += f"📤 Отправлено: {broadcast['total_sent']}\n"
            text += f"❌ Ошибок: {broadcast['total_failed']}\n\n"
        
        await message.reply(text)
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(Command("analytics"))
async def show_analytics(message: types.Message):
    """Показывает аналитику из Supabase (только для админа)"""
    if message.from_user.id != config.ADMIN_ID:
        return
    
    try:
        data = db.get_analytics_summary(days=7)
        
        if not data:
            await message.reply("❌ Ошибка получения данных")
            return
        
        text = f"📊 **Аналитика за 7 дней**\n\n"
        text += f"👥 Активных пользователей: {data['active_users']}\n\n"
        
        if data['popular_brands']:
            text += "🔥 **Популярные бренды:**\n"
            for brand in data['popular_brands'][:5]:
                text += f"  • {brand['brand']}: {brand['views']} просмотров\n"
        
        await message.reply(text)
    except Exception as e:
        logger.error(f"❌ Ошибка аналитики: {e}")
        await message.reply(f"❌ Ошибка: {e}")

@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def handle_webapp_data(message: types.Message):
    """📱 Обработка данных от Mini App (резервный вариант)"""
    try:
        data = json.loads(message.web_app_data.data)
        logger.info(f"📥 Получены данные от Mini App: {data}")
        
        action = data.get('action')
        user_id = data.get('user_id')
        
        if user_id:
            db.update_user_last_seen(user_id)
            
            if action == 'app_opened':
                logger.info(f"📱 Mini App открыт: {user_id}")
            elif action == 'brand_viewed':
                brand = data.get('brand', 'Unknown')
                logger.info(f"👁 {user_id} просмотрел бренд: {brand}")
            elif action == 'promo_copied':
                logger.info(f"📋 {user_id} скопировал промокод")
    except Exception as e:
        logger.error(f"❌ Ошибка обработки WebApp данных: {e}")

# === Self-ping для предотвращения сна ===
async def self_ping():
    """Автоматический пинг каждые 5 минут"""
    import aiohttp
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'http://localhost:10000/webhook',
                    json={'test': 'ping'},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    logger.info(f"🔄 Self-ping: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Self-ping error: {e}")
        
        await asyncio.sleep(300)  # 5 минут

# === Запуск ===
async def on_startup(bot: Bot):
    """Настройка webhook при запуске"""
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'promo-bot-ex86.onrender.com')}/webhook"
    await bot.set_webhook(webhook_url)
    logger.info(f"🔗 Webhook: {webhook_url}")

async def main():
    """Основная функция запуска"""
    db.init_db()
    logger.info("✅ База данных готова")
    
    # Создаём приложение
    app = web.Application()
    
    await on_startup(bot)
    
    # Регистрируем webhook handler
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Используем порт от Render
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"🚀 Бот запущен на порту {port}")
    
    # Запускаем self-ping в фоне
    asyncio.create_task(self_ping())
    logger.info("✅ Self-ping запущен (каждые 5 минут)")
    
    # Бесконечный цикл для поддержания работы
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())





