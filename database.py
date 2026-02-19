import psycopg2
import os
from contextlib import contextmanager

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                icon_emoji TEXT DEFAULT '📦'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                id SERIAL PRIMARY KEY,
                category_id INTEGER REFERENCES categories(id),
                brand_name TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                id SERIAL PRIMARY KEY,
                offer_id INTEGER REFERENCES offers(id),
                code_text TEXT NOT NULL,
                bonus_info TEXT,
                expires_at DATE,
                is_verified BOOLEAN DEFAULT TRUE
            )
        """)

def add_category(name, emoji):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories (name, icon_emoji) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
            (name, emoji)
        )

def add_offer(cat_id, brand, desc):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO offers (category_id, brand_name, description) VALUES (%s, %s, %s)",
            (cat_id, brand, desc)
        )

def add_promo_code(offer_id, code, bonus, expires):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO promo_codes (offer_id, code_text, bonus_info, expires_at) VALUES (%s, %s, %s, %s)",
            (offer_id, code, bonus, expires)
        )
