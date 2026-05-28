"""菜单查询接口（公开）"""
from datetime import date
from fastapi import APIRouter, HTTPException, Query
from database import get_db
from generator import get_monday, format_date, get_day_name, is_holiday, get_holidays_from_db

router = APIRouter(prefix="/api/menus", tags=["menus"])


def build_menu_response(menu_row, items):
    """将数据库记录组合为前端格式"""
    days_map = {}
    for item in items:
        day_date = item['day_date']
        if day_date not in days_map:
            d = date.fromisoformat(day_date)
            days_map[day_date] = {
                'date': day_date,
                'day_name': get_day_name(d),
                'is_holiday': bool(item['is_holiday']),
                'dishes': None,
            }

        if item['is_holiday']:
            continue

        entry = days_map[day_date]
        if entry['dishes'] is None:
            entry['dishes'] = {
                'bigMeat': [],
                'otherMeat': [],
                'vegetables': [],
                'soup': None,
                'noodle': None,
            }

        dish_data = {
            'id': item['id'],
            'dish_id': item['dish_id'],
            'name': item['dish_name'],
            'category': item['category'],
            'cuisine': item['cuisine'],
            'protein': item.get('protein', ''),
        }

        slot = item['slot']
        if slot.startswith('bigMeat'):
            dish_data['meatType'] = item['category']
            entry['dishes']['bigMeat'].append(dish_data)
        elif slot.startswith('otherMeat'):
            if item['category'] == 'lamb':
                dish_data['meatType'] = 'lamb'
            entry['dishes']['otherMeat'].append(dish_data)
        elif slot.startswith('vegetable'):
            entry['dishes']['vegetables'].append(dish_data)
        elif slot == 'soup':
            entry['dishes']['soup'] = dish_data
        elif slot == 'noodle':
            entry['dishes']['noodle'] = dish_data

    days = list(days_map.values())
    days.sort(key=lambda x: x['date'])
    return days


@router.get("/current")
def get_current_menu():
    monday = get_monday(date.today())
    week_key = format_date(monday)
    return get_menu_by_week(week_key)


@router.get("")
def get_menu_by_week(week_key: str = Query(...)):
    conn = get_db()
    cur = conn.execute("SELECT * FROM weekly_menus WHERE week_key = ?", (week_key,))
    menu = cur.fetchone()
    if not menu:
        conn.close()
        # 尝试自动生成
        from generator import generate_weekly_menu
        monday = date.fromisoformat(week_key)
        result = generate_weekly_menu(monday)
        if result:
            return result
        raise HTTPException(status_code=404, detail="该周无菜单数据")

    cur = conn.execute(
        "SELECT * FROM menu_items WHERE menu_id = ? ORDER BY day_date, sort_order",
        (menu['id'],)
    )
    items = [dict(row) for row in cur.fetchall()]
    conn.close()

    days = build_menu_response(menu, items)
    return {
        'menu_id': menu['id'],
        'week_key': menu['week_key'],
        'repeat_rate': menu['repeat_rate'],
        'generated_at': menu['generated_at'],
        'days': days,
    }
