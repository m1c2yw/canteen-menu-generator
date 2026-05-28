"""菜单生成算法（从 index.html JS 逻辑移植）"""
import random
from datetime import date, timedelta
from database import get_db

BIG_MEAT_KEYS = ['chicken', 'duck', 'beef', 'fish', 'shrimp']
SIMILAR_WORDS = ['排骨', '猪蹄', '扣肉', '肉丸', '肘子']

# 2026 年中国法定节假日
HOLIDAYS_2026 = {
    '2026-01-01',
    '2026-02-16', '2026-02-17', '2026-02-18', '2026-02-19', '2026-02-20',
    '2026-04-06',
    '2026-05-01', '2026-05-04', '2026-05-05',
    '2026-06-19',
    '2026-09-25',
    '2026-10-01', '2026-10-02', '2026-10-05', '2026-10-06', '2026-10-07',
}


def get_monday(d: date) -> date:
    """获取 d 所在周的周一"""
    return d - timedelta(days=d.weekday())


def format_date(d: date) -> str:
    return d.isoformat()


def get_day_name(d: date) -> str:
    return ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][d.weekday()]


def is_holiday(d: date, extra_holidays: set) -> bool:
    return format_date(d) in HOLIDAYS_2026 or format_date(d) in extra_holidays


def is_workday(d: date, extra_holidays: set) -> bool:
    return d.weekday() < 5 and not is_holiday(d, extra_holidays)


def load_dishes_by_category(conn):
    """从数据库加载菜品，按分类组织"""
    cur = conn.execute("SELECT * FROM dishes WHERE enabled = 1 ORDER BY id")
    dishes = {}
    for row in cur.fetchall():
        cat = row['category']
        if cat not in dishes:
            dishes[cat] = []
        dishes[cat].append(dict(row))
    return dishes


def get_recent_dish_set(conn, weeks: int = 8):
    """获取最近 N 周内出现过的菜品名称集合"""
    cutoff = date.today() - timedelta(weeks=weeks)
    cutoff_str = format_date(get_monday(cutoff))
    cur = conn.execute(
        "SELECT DISTINCT dish_name FROM dish_history WHERE week_key >= ?", (cutoff_str,)
    )
    return {row['dish_name'] for row in cur.fetchall()}


def get_holidays_from_db(conn):
    """从数据库读取额外节假日"""
    cur = conn.execute("SELECT date FROM holidays")
    return {row['date'] for row in cur.fetchall()}


def get_last_lamb_date(conn):
    cur = conn.execute(
        "SELECT MAX(day_date) as last_date FROM menu_items WHERE category = 'lamb'"
    )
    row = cur.fetchone()
    return row['last_date'] if row and row['last_date'] else None


def shuffle_pool(dishes: list, recent: set) -> list:
    """洗牌，优先排列近期未出现的菜品"""
    fresh = [d for d in dishes if d['name'] not in recent]
    used = [d for d in dishes if d['name'] in recent]
    random.shuffle(fresh)
    random.shuffle(used)
    return fresh + used


def pick_big_meat_keys(must_include_fish: bool, shrimp_used: int):
    """
    选择当天大荤类型（2种）。
    - must_include_fish: 是否必须包含鱼（每周一次）
    - shrimp_used: 本周虾已使用次数（最多2次）
    """
    non_fish = [k for k in BIG_MEAT_KEYS if k != 'fish']
    if must_include_fish:
        candidates = [k for k in non_fish if not (k == 'shrimp' and shrimp_used >= 2)]
        other = random.choice(candidates)
        return ['fish', other]
    # 非鱼日：选2种，避免鸡鸭同在
    candidates = list(non_fish)
    if shrimp_used >= 2:
        candidates = [k for k in candidates if k != 'shrimp']
    random.shuffle(candidates)
    a, b = candidates[0], candidates[1]
    if (a == 'chicken' and b == 'duck') or (a == 'duck' and b == 'chicken'):
        return [a, candidates[2]]
    return [a, b]


def is_similar(x: dict, y: dict) -> bool:
    return any(w in x['name'] and w in y['name'] for w in SIMILAR_WORDS)


def generate_weekly_menu(monday: date, force: bool = False):
    """生成一周菜单（周一至周五）"""
    conn = get_db()
    week_key = format_date(monday)

    # 如果已存在且不强制重生成，直接返回
    if not force:
        cur = conn.execute("SELECT id FROM weekly_menus WHERE week_key = ?", (week_key,))
        if cur.fetchone():
            conn.close()
            return None  # 调用方自行查询已有菜单

    # 清理旧数据
    if force:
        conn.execute("DELETE FROM menu_items WHERE menu_id IN (SELECT id FROM weekly_menus WHERE week_key = ?)", (week_key,))
        conn.execute("DELETE FROM dish_history WHERE week_key = ?", (week_key,))
        conn.execute("DELETE FROM weekly_menus WHERE week_key = ?", (week_key,))

    extra_holidays = get_holidays_from_db(conn)
    recent_set = get_recent_dish_set(conn)
    all_dishes = load_dishes_by_category(conn)

    # 为每个分类创建洗牌后的池
    pools = {}
    for cat, dishes in all_dishes.items():
        pools[cat] = shuffle_pool(dishes, recent_set)

    indices = {cat: 0 for cat in pools}

    # 统计工作日数量
    workdays = []
    for i in range(7):
        d = monday + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        if not is_workday(d, extra_holidays):
            continue
        workdays.append(d)

    if not workdays:
        conn.close()
        return None

    # 鱼日：随机选一个工作日
    fish_day_idx = random.randint(0, len(workdays) - 1)

    # 羊：距上次 >= 14 天
    last_lamb = get_last_lamb_date(conn)
    allow_lamb = True
    if last_lamb:
        days_since = (monday - date.fromisoformat(last_lamb)).days
        allow_lamb = days_since >= 14
    lamb_day_idx = random.randint(0, len(workdays) - 1) if allow_lamb else -1

    # 创建周菜单记录
    conn.execute(
        "INSERT INTO weekly_menus (week_key, repeat_rate) VALUES (?, 0)",
        (week_key,)
    )
    menu_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    shrimp_count = 0
    all_names = []
    day_results = []

    for i in range(7):
        d = monday + timedelta(days=i)
        if d.weekday() >= 5:
            continue

        date_str = format_date(d)

        if not is_workday(d, extra_holidays):
            day_results.append({
                'date': date_str, 'day_name': get_day_name(d),
                'is_holiday': True, 'dishes': None,
            })
            # 持久化节假日记录
            conn.execute(
                "INSERT INTO menu_items (menu_id, day_date, is_holiday, dish_name, category, cuisine, slot) VALUES (?,?,1,'','','','holiday')",
                (menu_id, date_str)
            )
            continue

        # 确定当天在工作日列表中的索引
        wd_idx = workdays.index(d)

        # 大荤选择
        big_keys = pick_big_meat_keys(wd_idx == fish_day_idx, shrimp_count)
        for k in big_keys:
            if k == 'shrimp':
                shrimp_count += 1

        big_meat_dishes = []
        for slot_idx, key in enumerate(big_keys):
            if key not in pools or indices[key] >= len(pools[key]):
                continue
            dish = dict(pools[key][indices[key]])
            indices[key] += 1
            dish['meatType'] = key
            dish['category'] = key
            big_meat_dishes.append(dish)
            all_names.append(dish['name'])
            conn.execute(
                "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                (menu_id, date_str, dish.get('id'), dish['name'], key, dish['cuisine'], dish.get('protein', ''), f'bigMeat_{slot_idx}', slot_idx)
            )

        # 其他荤菜
        other_meat_dishes = []
        if wd_idx == lamb_day_idx and 'lamb' in pools and indices.get('lamb', 0) < len(pools.get('lamb', [])):
            lamb_dish = dict(pools['lamb'][indices.get('lamb', 0)])
            indices['lamb'] = indices.get('lamb', 0) + 1
            lamb_dish['meatType'] = 'lamb'
            lamb_dish['category'] = 'lamb'
            other_meat_dishes.append(lamb_dish)
            all_names.append(lamb_dish['name'])
            conn.execute(
                "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                (menu_id, date_str, lamb_dish.get('id'), lamb_dish['name'], 'lamb', lamb_dish['cuisine'], '', 'otherMeat_0', 0)
            )

            pork_dish = dict(pools['otherMeat'][indices['otherMeat']])
            indices['otherMeat'] += 1
            pork_dish['category'] = 'otherMeat'
            other_meat_dishes.append(pork_dish)
            all_names.append(pork_dish['name'])
            conn.execute(
                "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                (menu_id, date_str, pork_dish.get('id'), pork_dish['name'], 'otherMeat', pork_dish['cuisine'], pork_dish.get('protein', ''), 'otherMeat_1', 1)
            )
        else:
            for slot_idx in range(2):
                if indices['otherMeat'] >= len(pools.get('otherMeat', [])):
                    continue
                pork_dish = dict(pools['otherMeat'][indices['otherMeat']])
                indices['otherMeat'] += 1
                pork_dish['category'] = 'otherMeat'
                # 同天避免同类食材
                if slot_idx == 1 and other_meat_dishes and is_similar(pork_dish, other_meat_dishes[0]):
                    swaps = 0
                    while swaps < 5 and indices['otherMeat'] < len(pools.get('otherMeat', [])):
                        pork_dish = dict(pools['otherMeat'][indices['otherMeat']])
                        indices['otherMeat'] += 1
                        pork_dish['category'] = 'otherMeat'
                        if not is_similar(pork_dish, other_meat_dishes[0]):
                            break
                        swaps += 1
                other_meat_dishes.append(pork_dish)
                all_names.append(pork_dish['name'])
                conn.execute(
                    "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                    (menu_id, date_str, pork_dish.get('id'), pork_dish['name'], 'otherMeat', pork_dish['cuisine'], pork_dish.get('protein', ''), f'otherMeat_{slot_idx}', slot_idx)
                )

        # 素菜 3 道
        vegetable_dishes = []
        for v_idx in range(3):
            if indices['vegetable'] >= len(pools.get('vegetable', [])):
                continue
            v_dish = dict(pools['vegetable'][indices['vegetable']])
            indices['vegetable'] += 1
            v_dish['category'] = 'vegetable'
            vegetable_dishes.append(v_dish)
            all_names.append(v_dish['name'])
            conn.execute(
                "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                (menu_id, date_str, v_dish.get('id'), v_dish['name'], 'vegetable', v_dish['cuisine'], '', f'vegetable_{v_idx}', v_idx)
            )

        # 汤
        soup_dish = dict(pools['soup'][indices['soup']]) if indices['soup'] < len(pools.get('soup', [])) else {'name': '紫菜蛋花汤', 'cuisine': '家常', 'category': 'soup'}
        indices['soup'] += 1
        soup_dish['category'] = 'soup'
        all_names.append(soup_dish['name'])
        conn.execute(
            "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
            (menu_id, date_str, soup_dish.get('id'), soup_dish['name'], 'soup', soup_dish['cuisine'], '', 'soup', 0)
        )

        # 面食
        noodle_dish = dict(pools['noodle'][indices['noodle']]) if indices['noodle'] < len(pools.get('noodle', [])) else {'name': '蛋炒饭', 'cuisine': '家常', 'category': 'noodle'}
        indices['noodle'] += 1
        noodle_dish['category'] = 'noodle'
        all_names.append(noodle_dish['name'])
        conn.execute(
            "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
            (menu_id, date_str, noodle_dish.get('id'), noodle_dish['name'], 'noodle', noodle_dish['cuisine'], '', 'noodle', 0)
        )

        day_results.append({
            'date': date_str,
            'day_name': get_day_name(d),
            'is_holiday': False,
            'dishes': {
                'bigMeat': big_meat_dishes,
                'otherMeat': other_meat_dishes,
                'vegetables': vegetable_dishes,
                'soup': soup_dish,
                'noodle': noodle_dish,
            },
        })

    # 写入冷却历史
    for name in all_names:
        conn.execute(
            "INSERT OR IGNORE INTO dish_history (week_key, dish_name) VALUES (?, ?)",
            (week_key, name)
        )

    # 计算重复率
    repeats = sum(1 for n in all_names if n in recent_set)
    repeat_rate = round(repeats / len(all_names) * 100) if all_names else 0
    conn.execute("UPDATE weekly_menus SET repeat_rate = ? WHERE id = ?", (repeat_rate, menu_id))

    conn.commit()
    conn.close()

    return {
        'menu_id': menu_id,
        'week_key': week_key,
        'repeat_rate': repeat_rate,
        'generated_at': format_date(date.today()),
        'days': day_results,
    }
