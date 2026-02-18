import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect("promo.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        # Категории
        conn.execute("""CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon_emoji TEXT DEFAULT "📦"
        )""")
        # Оферы (Бренды)
        conn.execute("""CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            brand_name TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )""")
        # Промокоды
        conn.execute("""CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER,
            code_text TEXT NOT NULL,
            bonus_info TEXT,
            expires_at DATE,
            is_verified INTEGER DEFAULT 1,
            FOREIGN KEY (offer_id) REFERENCES offers(id)
        )""")
        conn.commit()

def add_category(name, emoji):
    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO categories (name, icon_emoji) VALUES (?, ?)", (name, emoji))
        conn.commit()

def add_offer(cat_id, brand, desc):
    with get_db() as conn:
        conn.execute("INSERT INTO offers (category_id, brand_name, description) VALUES (?, ?, ?)", (cat_id, brand, desc))
        conn.commit()

def add_promo_code(offer_id, code, bonus, expires):
    with get_db() as conn:
        conn.execute("INSERT INTO promo_codes (offer_id, code_text, bonus_info, expires_at) VALUES (?, ?, ?, ?)", 
                     (offer_id, code, bonus, expires))
        conn.commit()

def get_categories():
    with get_db() as conn:
        return conn.execute("SELECT * FROM categories ORDER BY name").fetchall()

def get_offers(cat_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM offers WHERE category_id = ? AND is_active = 1", (cat_id,)).fetchall()

def get_codes(offer_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM promo_codes WHERE offer_id = ? AND is_verified = 1", (offer_id,)).fetchall()