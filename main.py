import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardBuilder
import config
import database as db

# Настройка логов
logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# 🎯 Старт
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

# ℹ️ О боте
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

# 🔧 АДМИН: Добавить категорию
# Команда: /add_cat Название 📦
@dp.message(Command("add_cat"))
async def admin_add_cat(message: types.Message):
    if message.from_user.id != config.ADMIN_ID: return
    try:
        parts = message.text.split(maxsplit=2)
        name = parts[1]
        emoji = parts[2] if len(parts) > 2 else "📦"
        db.add_category(name, emoji)
        await message.reply(f"✅ Категория '{name}' создана")
    except:
        await message.reply("❌ Ошибка. Формат: /add_cat Название 📦")

# 🔧 АДМИН: Добавить офер (бренд)
# Команда: /add_offer cat_id|Название Бренда|Описание
@dp.message(Command("add_offer"))
async def admin_add_offer(message: types.Message):
    if message.from_user.id != config.ADMIN_ID: return
    try:
        parts = message.text.split(maxsplit=1)[1].split("|")
        cat_id = int(parts[0])
        brand = parts[1]
        desc = parts[2] if len(parts) > 2 else ""
        db.add_offer(cat_id, brand, desc)
        await message.reply(f"✅ Бренд '{brand}' добавлен")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# 🔧 АДМИН: Добавить промокод
# Команда: /add_code offer_id|CODE123|Бонус|2024-12-31
@dp.message(Command("add_code"))
async def admin_add_code(message: types.Message):
    if message.from_user.id != config.ADMIN_ID: return
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

# 🚀 Запуск
async def main():
    db.init_db()
    logging.info("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())