import os
from datetime import datetime, timedelta
from supabase import create_client, Client

# Инициализация Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    """Инициализация базы данных"""
    print("✅ Supabase подключён")

def add_user(user_id, username=None, first_name=None, last_name=None, language_code=None):
    """Добавляет или обновляет пользователя"""
    try:
        # Проверяем, существует ли пользователь
        response = supabase.table('users').select('id').eq('user_id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            # Обновляем existing
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
    """Всего пользователей"""
    try:
        response = supabase.table('users').select('id', count='exact').execute()
        return response.count
    except:
        return 0

def get_active_users(days=7):
    """Активные за N дней"""
    try:
        date_from = (datetime.now() - timedelta(days=days)).isoformat()
        response = supabase.table('users').select('id', count='exact').gte('last_seen', date_from).execute()
        return response.count
    except:
        return 0

def get_new_users(days=1):
    """Новые за N дней"""
    try:
        date_from = (datetime.now() - timedelta(days=days)).isoformat()
        response = supabase.table('users').select('id', count='exact').gte('created_at', date_from).execute()
        return response.count
    except:
        return 0

# Остальные функции
def add_category(name, emoji='📦'):
    try:
        supabase.table('categories').insert({'name': name, 'icon_emoji': emoji}).execute()
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def add_offer(category_id, brand_name, description='', additional_info=''):
    try:
        supabase.table('offers').insert({
            'category_id': category_id,
            'brand_name': brand_name,
            'description': description,
            'additional_info': additional_info
        }).execute()
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def add_promo_code(offer_id, code_text, bonus_info='', expires_at=None):
    try:
        supabase.table('promo_codes').insert({
            'offer_id': offer_id,
            'code_text': code_text,
            'bonus_info': bonus_info,
            'expires_at': expires_at
        }).execute()
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def get_categories():
    try:
        response = supabase.table('categories').select('*').order('name').execute()
        return response.data
    except:
        return []

def get_offers(category_id=None):
    try:
        query = supabase.table('offers').select('*').eq('is_active', True)
        if category_id:
            query = query.eq('category_id', category_id)
        response = query.execute()
        return response.data
    except:
        return []

def get_promo_codes(offer_id):
    try:
        response = supabase.table('promo_codes').select('*').eq('offer_id', offer_id).eq('is_verified', True).execute()
        return response.data
    except:
        return []
