"""菜单生成算法 - 保证8周无重复 + 羊肉每月2次"""
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

# 每类每周大致用量（用于鲜池预检）
WEEKLY_NEED = {
    'chicken': 3, 'duck': 3, 'beef': 3, 'fish': 2, 'shrimp': 3,
    'lamb': 1, 'otherMeat': 10, 'vegetable': 15, 'soup': 5, 'noodle': 5,
}


def get_monday(d: date) -> date:
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
    cur = conn.execute("SELECT * FROM dishes WHERE enabled = 1 ORDER BY id")
    dishes = {}
    for row in cur.fetchall():
        cat = row['category']
        if cat not in dishes:
            dishes[cat] = []
        dishes[cat].append(dict(row))
    return dishes


def get_recent_dish_set(conn, reference_date: date, weeks: int = 8):
    """获取以 reference_date 为基准的前8周内出现过的菜品"""
    cutoff = reference_date - timedelta(weeks=weeks)
    cutoff_str = format_date(get_monday(cutoff))
    cur = conn.execute(
        "SELECT DISTINCT dish_name FROM dish_history WHERE week_key >= ?", (cutoff_str,)
    )
    return {row['dish_name'] for row in cur.fetchall()}


def get_holidays_from_db(conn):
    cur = conn.execute("SELECT date FROM holidays")
    return {row['date'] for row in cur.fetchall()}


def get_last_lamb_date(conn):
    cur = conn.execute(
        "SELECT MAX(day_date) as last_date FROM menu_items WHERE category = 'lamb'"
    )
    row = cur.fetchone()
    return row['last_date'] if row and row['last_date'] else None


def get_monthly_lamb_count(conn, year: int, month: int):
    """查询指定月份已出现的羊肉天数"""
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year+1}-01-01"
    else:
        end = f"{year}-{month+1:02d}-01"
    cur = conn.execute(
        "SELECT COUNT(DISTINCT day_date) FROM menu_items WHERE category='lamb' AND day_date >= ? AND day_date < ?",
        (start, end)
    )
    row = cur.fetchone()
    return row[0] if row else 0


def shuffle_pool(dishes: list, recent: set) -> tuple:
    """洗牌并返回 (pool, fresh_count)。鲜菜在前，近期已用菜在后"""
    fresh = [d for d in dishes if d['name'] not in recent]
    used = [d for d in dishes if d['name'] in recent]
    random.shuffle(fresh)
    random.shuffle(used)
    return fresh + used, len(fresh)


def pick_big_meat_keys(must_include_fish: bool, shrimp_used: int, week_used: dict):
    """
    选择当天大荤类型（2种），均衡各类别本周使用次数。
    鱼日强制出鱼，其余按使用次数均衡分配。
    """
    # 鱼日：鱼必选为第一道
    if must_include_fish:
        remaining = [k for k in BIG_MEAT_KEYS if k != 'fish']
        if shrimp_used >= 2:
            remaining = [k for k in remaining if k != 'shrimp']
        remaining.sort(key=lambda k: week_used.get(k, 0))
        min_use = week_used.get(remaining[0], 0)
        tied = [k for k in remaining if week_used.get(k, 0) == min_use]
        return ['fish', random.choice(tied)]

    # 非鱼日：从鸡鸭牛虾中选2种，均衡使用次数
    available = [k for k in BIG_MEAT_KEYS if k != 'fish']
    if shrimp_used >= 2:
        available = [k for k in available if k != 'shrimp']

    available.sort(key=lambda k: week_used.get(k, 0))
    min_use = week_used.get(available[0], 0)
    tied = [k for k in available if week_used.get(k, 0) == min_use]
    a = random.choice(tied)

    remaining = [k for k in available if k != a]
    if a == 'chicken':
        no_duck = [k for k in remaining if k != 'duck']
        remaining = no_duck if no_duck else remaining
    elif a == 'duck':
        no_chicken = [k for k in remaining if k != 'chicken']
        remaining = no_chicken if no_chicken else remaining

    remaining.sort(key=lambda k: week_used.get(k, 0))
    min_use2 = week_used.get(remaining[0], 0)
    tied2 = [k for k in remaining if week_used.get(k, 0) == min_use2]
    b = random.choice(tied2)

    return [a, b]


def is_similar(x: dict, y: dict) -> bool:
    return any(w in x['name'] and w in y['name'] for w in SIMILAR_WORDS)


def generate_weekly_menu(monday: date, force: bool = False):
    """生成一周菜单（周一至周五），保证8周不重复、羊肉每月2次"""
    conn = get_db()
    week_key = format_date(monday)

    if not force:
        cur = conn.execute("SELECT id FROM weekly_menus WHERE week_key = ?", (week_key,))
        if cur.fetchone():
            conn.close()
            return None

    if force:
        conn.execute("DELETE FROM menu_items WHERE menu_id IN (SELECT id FROM weekly_menus WHERE week_key = ?)", (week_key,))
        conn.execute("DELETE FROM dish_history WHERE week_key = ?", (week_key,))
        conn.execute("DELETE FROM weekly_menus WHERE week_key = ?", (week_key,))

    extra_holidays = get_holidays_from_db(conn)
    recent_set = get_recent_dish_set(conn, monday)
    all_dishes = load_dishes_by_category(conn)

    # 创建洗牌池，记录鲜池大小
    pools = {}
    fresh_counts = {}
    for cat, dishes in all_dishes.items():
        pool, fc = shuffle_pool(dishes, recent_set)
        pools[cat] = pool
        fresh_counts[cat] = fc

    # 预检：确保各类别鲜池足以覆盖本周需求
    for cat, need in WEEKLY_NEED.items():
        fc = fresh_counts.get(cat, 0)
        if fc < need and cat in pools:
            print(f"  ⚠ {cat} 鲜池仅 {fc} 道，本周需 {need} 道，可能产生重复")

    indices = {cat: 0 for cat in pools}

    # 收集工作日
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

    # ─── 羊肉调度：每月最多2次，间隔≥5个工作日 ───
    # 判断本周工作日在哪几个月
    workday_months = set(d.month for d in workdays)
    allow_lamb = False
    lamb_target_month = None
    last_lamb = get_last_lamb_date(conn)

    for m in sorted(workday_months):
        monthly_count = get_monthly_lamb_count(conn, monday.year, m)
        if monthly_count < 2:
            days_since = 999
            if last_lamb:
                days_since = (monday - date.fromisoformat(last_lamb)).days
            if days_since >= 7:  # 至少间隔一周
                allow_lamb = True
                lamb_target_month = m
                break

    # 在目标月份内随机选一个工作日作为羊肉日
    lamb_day_idx = -1
    if allow_lamb and lamb_target_month is not None:
        candidates = [i for i, d in enumerate(workdays) if d.month == lamb_target_month]
        if candidates:
            lamb_day_idx = random.choice(candidates)

    # ─── 鱼日：每周随机一个工作日 ───
    fish_day_idx = random.randint(0, len(workdays) - 1)

    # ─── 创建周菜单记录 ───
    conn.execute(
        "INSERT INTO weekly_menus (week_key, repeat_rate) VALUES (?, 0)",
        (week_key,)
    )
    menu_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    shrimp_count = 0
    big_meat_week_used = {}  # 本周各类大荤已用次数，用于均衡分配
    all_names = []
    day_results = []

    def pick_from_pool(cat: str) -> dict:
        """从分类池取菜，严格从鲜池中取（保证不重复）"""
        idx = indices.get(cat, 0)
        pool = pools.get(cat, [])
        fc = fresh_counts.get(cat, 0)

        if idx >= len(pool):
            # 池已完全耗尽（极端情况）
            raise RuntimeError(f"分类 {cat} 池耗尽！idx={idx}, pool_size={len(pool)}")

        if idx >= fc:
            # 鲜池耗尽，将进入近期已用菜品区域——记录警告
            print(f"  ⚠ {cat} 鲜池耗尽(idx={idx}, fresh={fc})，被迫使用近期菜品")

        dish = dict(pool[idx])
        indices[cat] = idx + 1
        return dish

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
            conn.execute(
                "INSERT INTO menu_items (menu_id, day_date, is_holiday, dish_name, category, cuisine, slot) VALUES (?,?,1,'','','','holiday')",
                (menu_id, date_str)
            )
            continue

        wd_idx = workdays.index(d)

        # ── 大荤（2道） ──
        big_keys = pick_big_meat_keys(wd_idx == fish_day_idx, shrimp_count, big_meat_week_used)
        for k in big_keys:
            if k == 'shrimp':
                shrimp_count += 1
            big_meat_week_used[k] = big_meat_week_used.get(k, 0) + 1

        big_meat_dishes = []
        for slot_idx, key in enumerate(big_keys):
            if key not in pools:
                continue
            dish = pick_from_pool(key)
            dish['meatType'] = key
            dish['category'] = key
            big_meat_dishes.append(dish)
            all_names.append(dish['name'])
            conn.execute(
                "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                (menu_id, date_str, dish.get('id'), dish['name'], key, dish['cuisine'], dish.get('protein', ''), f'bigMeat_{slot_idx}', slot_idx)
            )

        # ── 其他荤菜（2道，羊肉日则为1羊+1猪） ──
        other_meat_dishes = []
        if wd_idx == lamb_day_idx and 'lamb' in pools:
            lamb_dish = pick_from_pool('lamb')
            lamb_dish['meatType'] = 'lamb'
            lamb_dish['category'] = 'lamb'
            other_meat_dishes.append(lamb_dish)
            all_names.append(lamb_dish['name'])
            conn.execute(
                "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                (menu_id, date_str, lamb_dish.get('id'), lamb_dish['name'], 'lamb', lamb_dish['cuisine'], '', 'otherMeat_0', 0)
            )

            pork_dish = pick_from_pool('otherMeat')
            pork_dish['category'] = 'otherMeat'
            other_meat_dishes.append(pork_dish)
            all_names.append(pork_dish['name'])
            conn.execute(
                "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                (menu_id, date_str, pork_dish.get('id'), pork_dish['name'], 'otherMeat', pork_dish['cuisine'], pork_dish.get('protein', ''), 'otherMeat_1', 1)
            )
        else:
            for slot_idx in range(2):
                pork_dish = pick_from_pool('otherMeat')
                pork_dish['category'] = 'otherMeat'
                # 同天避免同类食材（排骨/猪蹄/扣肉等）
                if slot_idx == 1 and other_meat_dishes and is_similar(pork_dish, other_meat_dishes[0]):
                    for _ in range(5):
                        pork_dish = pick_from_pool('otherMeat')
                        pork_dish['category'] = 'otherMeat'
                        if not is_similar(pork_dish, other_meat_dishes[0]):
                            break
                other_meat_dishes.append(pork_dish)
                all_names.append(pork_dish['name'])
                conn.execute(
                    "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                    (menu_id, date_str, pork_dish.get('id'), pork_dish['name'], 'otherMeat', pork_dish['cuisine'], pork_dish.get('protein', ''), f'otherMeat_{slot_idx}', slot_idx)
                )

        # ── 素菜（3道） ──
        vegetable_dishes = []
        for v_idx in range(3):
            v_dish = pick_from_pool('vegetable')
            v_dish['category'] = 'vegetable'
            vegetable_dishes.append(v_dish)
            all_names.append(v_dish['name'])
            conn.execute(
                "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
                (menu_id, date_str, v_dish.get('id'), v_dish['name'], 'vegetable', v_dish['cuisine'], '', f'vegetable_{v_idx}', v_idx)
            )

        # ── 汤（1道） ──
        soup_dish = pick_from_pool('soup')
        soup_dish['category'] = 'soup'
        all_names.append(soup_dish['name'])
        conn.execute(
            "INSERT INTO menu_items (menu_id, day_date, dish_id, dish_name, category, cuisine, protein, slot, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
            (menu_id, date_str, soup_dish.get('id'), soup_dish['name'], 'soup', soup_dish['cuisine'], '', 'soup', 0)
        )

        # ── 面食/主食（1道） ──
        noodle_dish = pick_from_pool('noodle')
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

    # ── 写入冷却历史 ──
    for name in all_names:
        conn.execute(
            "INSERT OR IGNORE INTO dish_history (week_key, dish_name) VALUES (?, ?)",
            (week_key, name)
        )

    # ── 计算重复率 ──
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
