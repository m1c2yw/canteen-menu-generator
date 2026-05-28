"""种子数据：导入菜品、创建管理员、初始化节假日"""
import json
import os
from database import init_db, get_db
from auth import hash_password

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def seed_dishes():
    """从 dishes_data.json 导入菜品到数据库"""
    json_path = os.path.join(DATA_DIR, 'dishes_data.json')
    if not os.path.exists(json_path):
        print(f"错误：找不到 {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        dishes_data = json.load(f)

    conn = get_db()
    count = 0
    for category, dishes in dishes_data.items():
        for dish in dishes:
            protein = dish.get('protein', '')
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO dishes (name, category, cuisine, protein) VALUES (?,?,?,?)",
                    (dish['name'], category, dish['cuisine'], protein)
                )
                count += 1
            except Exception as e:
                print(f"跳过重复菜品: {dish['name']} - {e}")

    conn.commit()
    conn.close()
    print(f"已导入 {count} 道菜品")


def seed_admin(username: str = 'admin', password: str = 'admin123'):
    """创建默认管理员账号"""
    conn = get_db()
    cur = conn.execute("SELECT id FROM admins WHERE username = ?", (username,))
    if cur.fetchone():
        print(f"管理员 {username} 已存在，跳过")
    else:
        conn.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?,?)",
            (username, hash_password(password))
        )
        conn.commit()
        print(f"已创建管理员: {username} / {password}")
    conn.close()


def seed_holidays():
    """初始化 2026 年法定节假日"""
    holidays = [
        ('2026-01-01', '元旦'),
        ('2026-02-16', '春节（除夕）'),
        ('2026-02-17', '春节（初一）'),
        ('2026-02-18', '春节（初二）'),
        ('2026-02-19', '春节（初三）'),
        ('2026-02-20', '春节（初四）'),
        ('2026-04-06', '清明节'),
        ('2026-05-01', '劳动节'),
        ('2026-05-04', '劳动节'),
        ('2026-05-05', '劳动节'),
        ('2026-06-19', '端午节'),
        ('2026-09-25', '中秋节'),
        ('2026-10-01', '国庆节'),
        ('2026-10-02', '国庆节'),
        ('2026-10-05', '国庆节'),
        ('2026-10-06', '国庆节'),
        ('2026-10-07', '国庆节'),
    ]
    conn = get_db()
    count = 0
    for date_str, name in holidays:
        try:
            conn.execute("INSERT OR IGNORE INTO holidays (date, name) VALUES (?,?)", (date_str, name))
            count += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    print(f"已初始化 {count} 个节假日")


if __name__ == '__main__':
    print("初始化数据库...")
    init_db()
    print("导入菜品...")
    seed_dishes()
    print("创建管理员...")
    seed_admin()
    print("初始化节假日...")
    seed_holidays()
    print("初始化完成！")
