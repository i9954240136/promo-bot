import os
from datetime import datetime, timedelta
from supabase import create_client, Client

# Инициализация Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://yfvvsbcvrwvahmceutvi.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    """Инициализация базы данных (таблицы уже созданы в Supabase)"""
    print("✅ Supabase подключён")

# === ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ===
def add_user(user_id, username=None, first_name=None, last_name=None, language_code=None):
    """Добавляет или обновляет пользователя"""
    try:
        # Проверяем, существует ли пользователь
        response = supabase.table('users').select('id').eq('user_id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            # Обновляем существующего
            supabase.table('users').update({
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'language_code': language_code,
                'last_seen': datetime.now().isoformat()
            }).eq('user_id', user_id).execute()
        else:
            # Добавляем нового
            supabase.table('users').insert({
                'user_id': user_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'language_code': language_code,
                'created_at': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat()
            }).execute()
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")

def update_user_last_seen(user_id):
    """Обновляет время последнего посещения"""
    try:
        supabase.table('users').update({
            'last_seen': datetime.now().isoformat()
        }).eq('user_id', user_id).execute()
    except Exception as e:
        print(f"❌ Ошибка обновления last_seen: {e}")

def get_total_users():
    """Возвращает общее количество пользователей"""
    try:
        response = supabase.table('users').select('id', count='exact').execute()
        return response.count
    except Exception as e:
        print(f"❌ Ошибка получения пользователей: {e}")
        return 0

def get_active_users(days=7):
    """Возвращает количество активных пользователей за N дней"""
    try:
        date_from = (datetime.now() - timedelta(days=days)).isoformat()
        response = supabase.table('users').select('id', count='exact').gte('last_seen', date_from).execute()
        return response.count
    except Exception as e:
        print(f"❌ Ошибка получения активных: {e}")
        return 0

def get_new_users(days=1):
    """Возвращает количество новых пользователей за N дней"""
    try:
        date_from = (datetime.now() - timedelta(days=days)).isoformat()
        response = supabase.table('users').select('id', count='exact').gte('created_at', date_from).execute()
        return response.count
    except Exception as e:
        print(f"❌ Ошибка получения новых: {e}")
        return 0

def get_recent_users(limit=20):
    """Возвращает последних пользователей"""
    try:
        response = supabase.table('users').select('*').order('created_at', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"❌ Ошибка получения списка: {e}")
        return []

# === СУЩЕСТВУЮЩИЕ ФУНКЦИИ (оставьте как есть) ===
def add_category(name, emoji='📦'):
    try:
        supabase.table('categories').insert({'name': name, 'icon_emoji': emoji}).execute()
    except Exception as e:
        print(f"❌ Ошибка добавления категории: {e}")

def add_offer(category_id, brand_name, description='', additional_info=''):
    try:
        supabase.table('offers').insert({
            'category_id': category_id,
            'brand_name': brand_name,
            'description': description,
            'additional_info': additional_info
        }).execute()
    except Exception as e:
        print(f"❌ Ошибка добавления офера: {e}")

def add_promo_code(offer_id, code_text, bonus_info='', expires_at=None):
    try:
        supabase.table('promo_codes').insert({
            'offer_id': offer_id,
            'code_text': code_text,
            'bonus_info': bonus_info,
            'expires_at': expires_at
        }).execute()
    except Exception as e:
        print(f"❌ Ошибка добавления промокода: {e}")

def get_categories():
    try:
        response = supabase.table('categories').select('*').order('name').execute()
        return response.data
    except Exception as e:
        print(f"❌ Ошибка получения категорий: {e}")
        return []

def get_offers(category_id=None):
    try:
        query = supabase.table('offers').select('*').eq('is_active', True)
        if category_id:
            query = query.eq('category_id', category_id)
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"❌ Ошибка получения оферов: {e}")
        return []

def get_promo_codes(offer_id):
    try:
        response = supabase.table('promo_codes').select('*').eq('offer_id', offer_id).eq('is_verified', True).execute()
        return response.data
    except Exception as e:
        print(f"❌ Ошибка получения промокодов: {e}")
        return []
