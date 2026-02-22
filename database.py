import sqlite3
from datetime import datetime, timedelta

DB_NAME = 'promo_bot.db'

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица категорий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon_emoji TEXT DEFAULT '📦',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица оферов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            brand_name TEXT NOT NULL,
            description TEXT,
            additional_info TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # Таблица промокодов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER,
            code_text TEXT,
            bonus_info TEXT,
            barcode TEXT,
            barcode_type TEXT DEFAULT 'EAN13',
            expires_at TIMESTAMP,
            is_verified BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (offer_id) REFERENCES offers(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

# === ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ===
def add_user(user_id, username=None, first_name=None, last_name=None, language_code=None):
    """Добавляет или обновляет пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Пробуем обновить существующего
        cursor.execute('''
            UPDATE users 
            SET username=?, first_name=?, last_name=?, language_code=?, last_seen=?
            WHERE user_id=?
        ''', (username, first_name, last_name, language_code, datetime.now(), user_id))
        
        # Если не обновился - добавляем нового
        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, language_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, language_code))
        
        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")
    finally:
        conn.close()

def update_user_last_seen(user_id):
    """Обновляет время последнего посещения"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users 
        SET last_seen = ?
        WHERE user_id = ?
    ''', (datetime.now(), user_id))
    
    conn.commit()
    conn.close()

def get_total_users():
    """Возвращает общее количество пользователей"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users')
    result = cursor.fetchone()[0]
    
    conn.close()
    return result

def get_active_users(days=7):
    """Возвращает количество активных пользователей за N дней"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_seen > ?
    ''', (datetime.now() - timedelta(days=days),))
    
    result = cursor.fetchone()[0]
    conn.close()
    return result

def get_new_users(days=1):
    """Возвращает количество новых пользователей за N дней"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE created_at > ?
    ''', (datetime.now() - timedelta(days=days),))
    
    result = cursor.fetchone()[0]
    conn.close()
    return result

# === СУЩЕСТВУЮЩИЕ ФУНКЦИИ ===
def add_category(name, emoji='📦'):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO categories (name, icon_emoji) VALUES (?, ?)', (name, emoji))
    conn.commit()
    conn.close()

def add_offer(category_id, brand_name, description='', additional_info=''):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO offers (category_id, brand_name, description, additional_info)
        VALUES (?, ?, ?, ?)
    ''', (category_id, brand_name, description, additional_info))
    conn.commit()
    conn.close()

def add_promo_code(offer_id, code_text, bonus_info='', expires_at=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO promo_codes (offer_id, code_text, bonus_info, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (offer_id, code_text, bonus_info, expires_at))
    conn.commit()
    conn.close()

def get_categories():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories ORDER BY name')
    result = cursor.fetchall()
    conn.close()
    return result

def get_offers(category_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if category_id:
        cursor.execute('SELECT * FROM offers WHERE category_id = ? AND is_active = TRUE', (category_id,))
    else:
        cursor.execute('SELECT * FROM offers WHERE is_active = TRUE')
    
    result = cursor.fetchall()
    conn.close()
    return result

def get_promo_codes(offer_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM promo_codes 
        WHERE offer_id = ? AND is_verified = TRUE
    ''', (offer_id,))
    result = cursor.fetchall()
    conn.close()
    return result
