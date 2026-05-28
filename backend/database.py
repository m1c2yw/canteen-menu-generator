"""SQLite 数据库连接与建表"""
import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DB_DIR, 'canteen.db')


def get_db():
    """获取数据库连接（每请求一个连接）"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """创建所有表"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            cuisine TEXT NOT NULL,
            protein TEXT DEFAULT '',
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS weekly_menus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_key TEXT NOT NULL UNIQUE,
            repeat_rate REAL DEFAULT 0,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_id INTEGER NOT NULL REFERENCES weekly_menus(id),
            day_date TEXT NOT NULL,
            is_holiday INTEGER DEFAULT 0,
            dish_id INTEGER REFERENCES dishes(id),
            dish_name TEXT NOT NULL,
            category TEXT NOT NULL,
            cuisine TEXT NOT NULL,
            protein TEXT DEFAULT '',
            slot TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS dish_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_key TEXT NOT NULL,
            dish_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT DEFAULT '匿名',
            content TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'suggestion',
            status TEXT NOT NULL DEFAULT 'pending',
            reply TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS holidays (
            date TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_staples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weekday INTEGER NOT NULL,
            name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS daily_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            staple_id INTEGER NOT NULL REFERENCES daily_staples(id),
            quantity INTEGER NOT NULL DEFAULT 1,
            order_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_menu_items_menu ON menu_items(menu_id);
        CREATE INDEX IF NOT EXISTS idx_menu_items_date ON menu_items(day_date);
        CREATE INDEX IF NOT EXISTS idx_dish_history_week ON dish_history(week_key);
        CREATE INDEX IF NOT EXISTS idx_dishes_category ON dishes(category);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_dishes_name ON dishes(name);
        CREATE INDEX IF NOT EXISTS idx_feedbacks_status ON feedbacks(status);
    """)
    conn.commit()
    conn.close()
